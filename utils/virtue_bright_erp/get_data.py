"""
获取ERP数据
    - 分批并发拉取分页工具的全部数据
"""

from typing import Any, Optional
import asyncio


async def fetch_all_pages(
        tool,
        args: dict,
        *,
        batch_size: int = 20,
        max_pages: Optional[int] = None,
        verbose: bool = False,) -> dict[str, Any]:
    """
    分批并发拉取分页工具的全部数据
    Args:
        tool: 带 ainvoke 的 LangChain tool（如 get_goods_info）
        args(dict): 调用参数（含 runtime 及业务过滤条件；current 会被覆盖）
        batch_size(int): 每批并发页数, default=20
        max_pages(Optional[int]): 最多拉几页（调试用）, default=None 表示全部
        verbose(bool): 是否打印进度, default=True
    Returns:
        dict: {status, data, page_info, errors, ...首屏其它字段如 total_summary}
    """
    base_args = {**args, "current": 1}
    first = await tool.ainvoke(base_args)

    if first.get("status") != "success":
        return first

    data_list = list(first.get("data") or [])
    page_info = dict(first.get("page_info") or {})
    total_pages = page_info.get("pages") or 1
    if max_pages is not None:
        total_pages = min(total_pages, max_pages)

    errors: list[dict] = []

    async def fetch_page(page: int):
        page_args = {**args, "current": page}
        result = await tool.ainvoke(page_args)
        if result.get("status") != "success":
            raise RuntimeError(
                f"page={page}: {result.get('message') or result}")
        return page, (result.get("data") or [])

    for batch_start in range(2, total_pages + 1, batch_size):
        batch_end = min(batch_start + batch_size, total_pages + 1)
        if verbose:
            print(f"正在拉取 {batch_start}-{batch_end - 1} / {total_pages} 页...")

        batch_results = await asyncio.gather(
            *(fetch_page(p) for p in range(batch_start, batch_end)),
            return_exceptions=True,
        )

        ok = []
        for page, result in zip(range(batch_start, batch_end), batch_results):
            if isinstance(result, Exception):
                errors.append({"page": page, "error": str(result)})
                if verbose:
                    print(f"第 {page} 页失败: {result}")
            else:
                ok.append(result)

        for _, items in sorted(ok, key=lambda x: x[0]):
            data_list.extend(items)

    # 保留首屏里除 data/page_info 外的字段（如 total_summary）
    result = {
        **{k: v for k, v in first.items() if k not in ("data", "page_info")},
        "status": "success" if not errors else "partial",
        "data": data_list,
        "page_info": {
            **page_info,
            "current": total_pages,
            "fetched": len(data_list),
        },
        "errors": errors,
    }
    if verbose:
        print(f"完成: {len(data_list)} 条, 失败 {len(errors)} 页")
    return result
