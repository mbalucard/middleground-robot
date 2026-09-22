"""
企微工具审批流程编排
    - issue_review_card: 写入草稿并发审批卡
    - consume_judge_stream_and_reply: interrupts_judge 恢复并回复
    - cancel_pending_interrupt_if_any: 新消息时自动取消审批
    - handle_template_card_event: 处理审批卡片点击
"""

from __future__ import annotations

from api.qw_api_robot.api_client import ApiClientError, stream_interrupts_judge
from api.qw_api_robot.general_tools import get_or_create_api_thread_id
from api.qw_api_robot.interrupt_card import (
    build_result_card,
    build_review_card,
    make_task_id,
)
from api.qw_api_robot.interrupt_draft import (
    apply_button_decision,
    build_draft,
    clear_draft,
    current_tool_name,
    decides_for_api,
    fill_all_reject,
    get_draft,
    is_draft_expired,
    mark_event_seen,
    set_draft,
)
from api.qw_api_robot.qw_respond import (
    respond_template_card,
    respond_update_template_card,
    send_markdown,
    send_template_card,
)
from api.qw_api_robot.stream_agent import (
    _interrupt_event_from_api,
    format_agent_chunk,
)
from utils.logger_manager import LoggerManager

logger = LoggerManager.get_logger(name="interrupt_flow")

GROUP_INTERRUPT_REPLY = "当前为群聊，无工具审批权限"
INTERRUPT_STREAM_HINT = "请审批工具调用"
EXPIRED_CARD_REPLY = "该审批已过期，请重新发起请求"


async def issue_review_card(
    ws,
    *,
    userid: str,
    message_id: str,
    tools: list[dict],
    passive_req_id: str | None = None,
) -> None:
    """
    写入草稿并发出首张/恢复后审批卡
    Args:
        ws: websocket
        userid(str): 企微 userid
        message_id(str): API message_id
        tools(list): 待审工具
        passive_req_id(str): 若有则被动发卡，否则 aibot_send_msg, default=None
    """
    if not tools:
        logger.error(f"interrupt 无 tools userid={userid} message_id={message_id}")
        return
    task_id = make_task_id(message_id, 0)
    draft = build_draft(message_id=message_id, tools=tools, task_id=task_id)
    await set_draft(userid, draft)
    card = build_review_card(
        tool_name=str(tools[0].get("name") or "工具"),
        task_id=task_id,
        show_all_buttons=len(tools) >= 2,
        index=0,
        total=len(tools),
    )
    if passive_req_id:
        resp = await respond_template_card(ws, passive_req_id, card)
    else:
        resp = await send_template_card(ws, userid, card)
    if resp.get("errcode", 0) != 0:
        logger.error(f"审批卡发送失败 userid={userid} resp={resp}")


async def consume_judge_stream_and_reply(
    ws,
    *,
    userid: str,
    thread_id: str,
    message_id: str,
    decides: list[str],
    is_all_decides: bool,
) -> None:
    """
    调用 interrupts_judge/stream，markdown 回复；若再 interrupt 则主动推卡
    Args:
        ws: websocket
        userid(str): 企微 userid
        thread_id(str): API thread_id
        message_id(str): API message_id
        decides(list): 决策列表
        is_all_decides(bool): 是否全部一致决策
    """
    await send_markdown(ws, userid, "继续处理中…")
    fragments: list[str] = []
    try:
        async for event in stream_interrupts_judge(
            user_id=userid,
            thread_id=thread_id,
            message_id=message_id,
            decides=decides,
            is_all_decides=is_all_decides,
        ):
            if not event.get("success", True):
                await send_markdown(
                    ws,
                    userid,
                    str(event.get("message") or "中断恢复失败，请稍后重试"),
                )
                return
            data_type = event.get("data_type")
            if data_type == "end":
                break
            if data_type == "error":
                await send_markdown(
                    ws,
                    userid,
                    str(event.get("message") or "中断恢复失败，请稍后重试"),
                )
                return
            if data_type == "interrupt":
                irq = _interrupt_event_from_api(event)
                tools = irq.get("tools") or []
                mid = str(irq.get("message_id") or message_id)
                await issue_review_card(
                    ws,
                    userid=userid,
                    message_id=mid,
                    tools=tools,
                    passive_req_id=None,
                )
                return
            if data_type == "tool":
                continue
            if data_type == "agent":
                fragments.extend(format_agent_chunk(event.get("data")))
                continue
    except ApiClientError as e:
        await send_markdown(ws, userid, e.user_message)
        return
    except Exception as e:
        logger.exception(f"interrupts_judge 失败: {e}")
        await send_markdown(ws, userid, "中断恢复失败，请稍后重试")
        return

    text = "\n\n".join(fragments).strip() if fragments else "（无内容）"
    await send_markdown(ws, userid, text)


async def cancel_pending_interrupt_if_any(
    ws,
    *,
    userid: str,
    thread_id: str,
) -> bool:
    """
    若有 pending 审批草稿：全部 reject 并 resume，更新卡为已取消
    Args:
        ws: websocket
        userid(str): 企微 userid
        thread_id(str): API thread_id
    Returns:
        True 表示曾存在并已取消
    """
    draft = await get_draft(userid)
    if not draft or draft.get("status") != "pending":
        return False
    if is_draft_expired(draft):
        await clear_draft(userid)
        return False

    message_id = str(draft.get("message_id") or "")
    new_draft, is_all = fill_all_reject(draft)
    decides = decides_for_api(new_draft, is_all)
    await clear_draft(userid)

    await send_markdown(ws, userid, "已取消当前工具审批，开始处理新消息。")

    if message_id and decides:
        try:
            async for event in stream_interrupts_judge(
                user_id=userid,
                thread_id=thread_id,
                message_id=message_id,
                decides=decides,
                is_all_decides=is_all,
            ):
                # 自动拒绝后不展示恢复内容，仅消费流避免挂起
                if event.get("data_type") in ("end", "error", "interrupt"):
                    break
        except Exception as e:
            logger.exception(f"自动拒绝 interrupts_judge 失败: {e}")
    return True


async def handle_template_card_event(ws, msg: dict) -> None:
    """
    处理模板卡片按钮事件：更新卡、串行下一张或 interrupts_judge
    Args:
        ws: websocket连接
        msg(dict): aibot_event_callback 帧
    """
    headers = msg.get("headers") or {}
    body = msg.get("body") or {}
    callback_req_id = headers.get("req_id") or ""
    from_info = body.get("from") or {}
    userid = from_info.get("userid") or ""
    event = (body.get("event") or {})
    card_event = event.get("template_card_event") or {}
    event_key = card_event.get("event_key") or card_event.get("eventkey") or ""
    task_id = card_event.get("task_id") or ""
    msgid = body.get("msgid") or ""

    logger.info(
        f"template_card_event userid={userid} task_id={task_id} "
        f"event_key={event_key}"
    )

    if not userid or not callback_req_id:
        logger.error("template_card_event 缺少 userid 或 req_id")
        return

    draft = await get_draft(userid)
    if not draft or is_draft_expired(draft):
        await clear_draft(userid)
        try:
            await respond_update_template_card(
                ws,
                callback_req_id,
                build_result_card(
                    task_id=task_id or "expired",
                    title="审批已过期",
                    desc=EXPIRED_CARD_REPLY,
                ),
                userids=[userid],
            )
        except Exception as e:
            logger.warning(f"过期卡更新失败: {e}")
        await send_markdown(ws, userid, EXPIRED_CARD_REPLY)
        return

    if draft.get("status") != "pending":
        await respond_update_template_card(
            ws,
            callback_req_id,
            build_result_card(
                task_id=task_id or str(draft.get("current_task_id") or "done"),
                title="审批已结束",
                desc="该审批已处理完毕",
            ),
            userids=[userid],
        )
        return

    current_task = str(draft.get("current_task_id") or "")
    if task_id and current_task and task_id != current_task:
        logger.warning(
            f"task_id 不匹配 expect={current_task} got={task_id}"
        )
        return

    event_token = (
        f"{msgid}:{task_id}:{event_key}" if msgid else f"{task_id}:{event_key}"
    )
    if not mark_event_seen(draft, event_token):
        logger.info(f"幂等跳过 event_token={event_token}")
        return
    await set_draft(userid, draft)

    try:
        new_draft, done, is_all_decides = apply_button_decision(draft, event_key)
    except ValueError as e:
        logger.warning(f"无效按钮: {e}")
        await set_draft(userid, draft)
        return

    label = {
        "irq_approve": "已同意",
        "irq_reject": "已拒绝",
        "irq_approve_all": "已全部同意",
        "irq_reject_all": "已全部拒绝",
    }.get(event_key, "已处理")

    # 5s 内先 update
    await respond_update_template_card(
        ws,
        callback_req_id,
        build_result_card(
            task_id=task_id or current_task,
            title=label,
            desc=f"{current_tool_name(draft)} — {label}",
        ),
        userids=[userid],
    )

    if not done:
        tools = new_draft.get("tools") or []
        index = int(new_draft.get("index") or 0)
        next_task = make_task_id(str(new_draft.get("message_id") or "m"), index)
        new_draft["current_task_id"] = next_task
        card_ids = list(new_draft.get("card_task_ids") or [])
        card_ids.append(next_task)
        new_draft["card_task_ids"] = card_ids
        await set_draft(userid, new_draft)
        tool_name = "工具"
        if 0 <= index < len(tools):
            tool_name = str((tools[index] or {}).get("name") or "工具")
        card = build_review_card(
            tool_name=tool_name,
            task_id=next_task,
            show_all_buttons=len(tools) >= 2,
            index=index,
            total=len(tools),
        )
        await send_template_card(ws, userid, card)
        return

    # 已凑齐：清草稿后 judge（先 clear 避免并发）
    message_id = str(new_draft.get("message_id") or "")
    decides = decides_for_api(new_draft, is_all_decides)
    await clear_draft(userid)

    try:
        thread_id = await get_or_create_api_thread_id(userid)
    except Exception as e:
        logger.exception(f"获取 thread_id 失败: {e}")
        await send_markdown(ws, userid, "恢复失败：无法获取会话，请稍后重试")
        return

    await consume_judge_stream_and_reply(
        ws,
        userid=userid,
        thread_id=thread_id,
        message_id=message_id,
        decides=decides,
        is_all_decides=is_all_decides,
    )
