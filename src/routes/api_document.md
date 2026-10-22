# Robot API 接口文档

基于 DeepAgents 的机器人 HTTP API。服务入口见 `src/fastapi_main.py`。

- 默认地址：`http://<host>:8010`
- 请求体：`Content-Type: application/json`
- 流式响应：`Content-Type: application/x-ndjson`（每行一条 JSON，以 `\n` 结尾）
- OpenAPI：服务启动后可访问 `/docs`、`/redoc`、`/openapi.json`

调用智能体前，先用会话接口创建 `thread_id`。智能体运行会生成 `message_id`（`m-{uuid}`），中断恢复时必须带回同一 `message_id`。

## 通用约定

### 模型标签 `model_label`

| 值 | 说明 |
| --- | --- |
| `deepseek` | 默认 支持图片输入 |
| `minimax_m3` | 支持图片（`provider=anthropic`） |
| `aihubmix_minimax_m27` | 纯文本 |
| `aihubmix_minimax_m3` | 支持图片（`provider=anthropic`） |

带图时允许的组合：

| `provider` | 允许的 `model_label` |
| --- | --- |
| `openai` | `deepseek` |
| `anthropic` | `minimax_m3`、`aihubmix_minimax_m3` |

### 请求头

| 名称 | 适用接口 | 说明 |
| --- | --- | --- |
| `Authorization` | `POST /agent/run_agent/invoke`、`POST /agent/run_agent/stream` | 可选。仅当值以 `Bearer ` 开头时，整段头值会作为模型 `api_key` 传入 |

### 消息对象

智能体消息由 `agent_message_to_dict` 转换，`type` 决定字段。

**HumanMessage**

```json
{
  "type": "HumanMessage",
  "content": "用户问题或图文 content",
  "id": "消息 id",
  "additional_kwargs": {},
  "response_metadata": {}
}
```

**AIMessage**

```json
{
  "type": "AIMessage",
  "content": "文本；列表 content 会拼成字符串，仅有 thinking 时前缀为 thinking: ",
  "additional_kwargs": {},
  "response_metadata": {},
  "id": "消息 id",
  "tool_calls": [],
  "invalid_tool_calls": [],
  "usage_metadata": null
}
```

**ToolMessage**

```json
{
  "type": "ToolMessage",
  "content": "工具返回",
  "name": "工具名",
  "id": "消息 id",
  "tool_call_id": "对应 tool_call id"
}
```

**Interrupt**

```json
{
  "type": "Interrupt",
  "content": {
    "action_requests": [],
    "review_configs": []
  },
  "id": "中断 id"
}
```

无中断时，短期记忆接口里的 `data` 可能是空对象 `{}`。

### 错误形态

业务失败（线程不存在、图文校验失败、中断恢复失败）多数仍返回 HTTP 200，用 `success: false` 表示。参数缺失走 FastAPI 校验或 `HTTPException`。

| HTTP | 场景 | 响应体 |
| --- | --- | --- |
| 400 | 业务必填缺失（如删除时 `thread_id` / `key` 为空） | `{"detail": "错误说明"}` |
| 422 | JSON 缺必填字段或类型不符 | FastAPI `detail` 数组 |
| 500 | 数据库、记忆存储或智能体执行异常 | `{"detail": "错误说明"}` |

业务失败的统一结构（同步接口）：

```json
{
  "success": false,
  "agent_args": {},
  "total": 0,
  "data": [],
  "data_type": "error",
  "message": "错误说明"
}
```

会话线程不存在时，`message` 可能是：`用户会话线程不存在`、`用户会话线程已归档`、`会话线程已删除`、`会话线程不唯一`。

---

## 根路径

### `GET /`

服务探活。

**响应**

```json
{"message": "我是Dawn机器人根目录!"}
```

---

## Agent `/agent`

### `GET /agent/`

路由探活。

**响应**

```json
{"message": "这里是Agent交互路由"}
```

### `POST /agent/run_agent/invoke`

同步运行一轮智能体。服务端生成 `message_id`。成功后后台落库，不影响本次响应。

**请求体**

| 字段 | 类型 | 必填 | 默认 | 说明 |
| --- | --- | --- | --- | --- |
| `user_id` | string | 是 | | 用户 ID |
| `query` | string | 是 | | 用户问题。有图时不能为空，不支持只传图片 |
| `thread_id` | string | 是 | | 已创建且未删除的会话线程 |
| `model_label` | string | 否 | `deepseek` | 见模型标签 |
| `is_message_all` | bool | 否 | `false` | `true` 返回本轮从最后一条用户消息起的全部消息；`false` 只返回本轮最后一条 |
| `images` | array | 否 | `[]` | 最多 10 张，单张 ≤ 10MB，格式 jpeg / png / gif / webp |
| `provider` | string | 有图时必填 | `null` | `openai` 或 `anthropic` |

`images` 单项：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `data` | string | 是 | 纯 base64，或 `data:image/...;base64,...` |
| `media_type` | string | 否 | 如 `image/jpeg`。传入时必须与文件头一致 |

**请求示例**

```json
{
  "user_id": "user01",
  "query": "帮我查一下今天的订单",
  "thread_id": "t-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "model_label": "deepseek",
  "is_message_all": false,
  "images": [],
  "provider": null
}
```

**成功响应**

若本轮触发人工审批中断，`data` 末尾会追加一条 `Interrupt`。`agent_args.message_id` 用于后续恢复。

```json
{
  "success": true,
  "agent_args": {
    "user_id": "user01",
    "thread_id": "t-...",
    "message_id": "m-...",
    "model_label": "deepseek"
  },
  "total": 1,
  "data": [],
  "data_type": "agent_message",
  "message": "成功获取智能体消息"
}
```

**图文失败 `message` 示例**

- `图文问答时 query 不能为空（不支持仅传图片）`
- `单次最多上传 10 张图片，当前 N 张`
- `有图时必须传入 provider（openai 或 anthropic）`
- `模型 {model_label} 不支持图片输入；请使用：...`
- `provider=... 与 model_label=... 不匹配；该 provider 仅允许：...`
- `图片 base64 无效，请传入合法的 JPEG/PNG/GIF/WEBP base64`
- `第 N 张图片 data 为空`
- `第 N 张图片：图片过大或格式不支持（请发 jpeg/png/gif/webp，≤10MB）`
- `第 N 张图片 media_type 与文件内容不符（声明=...，实际=...）`

### `POST /agent/run_agent/interrupts_judge/invoke`

对上一轮挂起的工具审批做决策，并同步继续运行。不读取 `Authorization`，沿用中断时保存的 `api_key` 与 `model_label`。

**请求体**

| 字段 | 类型 | 必填 | 默认 | 说明 |
| --- | --- | --- | --- | --- |
| `user_id` | string | 是 | | 用户 ID |
| `thread_id` | string | 是 | | 会话线程 |
| `message_id` | string | 否 | `""` | 触发中断那次运行返回的消息 ID。对不上则恢复失败 |
| `decides` | string[] | 是 | | 每项为 `approve`、`edit`、`reject`、`respond` |
| `is_all_decides` | bool | 否 | `false` | 见下方决策规则 |
| `is_message_all` | bool | 否 | `false` | 同 invoke |

**决策规则**

- `is_all_decides` 为 `false`：`decides` 长度必须等于当前中断里的动作条数，按顺序一一对应。
- `is_all_decides` 为 `true`：`decides` 只能有 1 项，且只能是 `approve` 或 `reject`，应用到全部待审批动作。

**请求示例**

```json
{
  "user_id": "user01",
  "thread_id": "t-...",
  "message_id": "m-...",
  "decides": ["approve"],
  "is_all_decides": true,
  "is_message_all": false
}
```

**成功响应** 与 invoke 相同，`data_type` 为 `agent_message`。`agent_args` 不含 `model_label`。

**失败**（无中断、已过期，或决策条数 / 取值不合法）：

```json
{
  "success": false,
  "agent_args": {
    "user_id": "user01",
    "thread_id": "t-...",
    "message_id": "m-..."
  },
  "total": 0,
  "data": [],
  "data_type": "error",
  "message": "中断恢复失败：无有效中断信息或决策参数不合法"
}
```

### `POST /agent/run_agent/stream`

流式运行一轮智能体。请求体与 invoke 相同。`is_message_all` 对流式无效，每个节点单独成行。

**响应** `application/x-ndjson`

中间行：

```json
{
  "success": true,
  "agent_args": {
    "user_id": "user01",
    "thread_id": "t-...",
    "message_id": "m-...",
    "model_label": "deepseek"
  },
  "order": {"num": 1, "is_end": false},
  "data": {},
  "data_type": "agent",
  "message": "智能体消息"
}
```

| `data_type` | `message` | `data` |
| --- | --- | --- |
| `agent` | 智能体消息 | AIMessage |
| `tool` | 工具消息 | ToolMessage |
| `interrupt` | 中断消息 | Interrupt |
| `unknown` | 未知消息 | `null` |
| `end` | 流式输出结束 | `null`，且 `order.is_end` 为 `true` |
| `error` | 错误说明 | `[]` 或空；图文失败、线程不存在时整段流只有这一行，且没有 `order` |

结束行：

```json
{
  "success": true,
  "agent_args": {},
  "order": {"num": 2, "is_end": true},
  "data": null,
  "data_type": "end",
  "message": "流式输出结束"
}
```

### `POST /agent/run_agent/interrupts_judge/stream`

流式恢复中断。请求体与同步恢复相同。`is_message_all` 对流式无效。

正常分片与 stream 相同，`agent_args` 不含 `model_label`。

恢复失败时只输出一行后结束，不再跟 `end` 行：

```json
{
  "success": false,
  "agent_args": {},
  "order": {"num": 1, "is_end": true},
  "data": null,
  "data_type": "error",
  "message": "中断恢复失败：无有效中断信息或决策参数不合法"
}
```

线程不存在时的错误行与同步接口相同（含 `total`，无 `order`）。

---

## Session `/session`

### `GET /session/`

路由探活。

**响应**

```json
{"message": "这里是Session管理路由"}
```

### `POST /session/session_thread/create`

为用户创建会话线程。`thread_id` 由服务端生成，格式 `t-{uuid}`。请求里的 `thread_id` 会被忽略。

**请求体**

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `user_id` | string | 是 | 用户 ID |
| `thread_id` | string | 否 | 本接口不使用 |

**请求示例**

```json
{"user_id": "user01"}
```

**成功**

```json
{
  "success": true,
  "data": {"user_id": "user01", "thread_id": "t-..."},
  "message": "成功创建会话线程"
}
```

**失败**

```json
{
  "success": false,
  "data": {},
  "message": "创建会话线程失败"
}
```

### `POST /session/session_thread/user_thread_list`

查询该用户未删除的会话，按创建时间倒序。

**请求体** 同创建接口，只需 `user_id`。

**成功**

```json
{
  "success": true,
  "data": [
    {"user_id": "user01", "thread_id": "t-...", "is_active": 1}
  ],
  "total": 1,
  "message": "成功获取用户会话线程列表"
}
```

`is_active`：`1` 可用，`0` 已归档。列表只含 `is_deleted = 0` 的记录。

**无数据**

```json
{
  "success": false,
  "data": [],
  "total": 0,
  "message": "未找到用户会话线程"
}
```

### `POST /session/session_thread/delete`

软删除会话，并清除该线程的 checkpoint。

**请求体**

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `user_id` | string | 是 | 用户 ID |
| `thread_id` | string | 是 | 要删除的线程。空字符串返回 HTTP 400 |

**请求示例**

```json
{"user_id": "user01", "thread_id": "t-..."}
```

**成功**

```json
{"success": true, "message": "成功删除会话"}
```

**失败**

```json
{"success": false, "message": "删除会话线程失败"}
```

**HTTP 400**

```json
{"detail": "删除会话线程失败，thread_id不能为空"}
```

---

## Memory `/memory`

长期记忆的 `key` 在写入和删除前会格式化：空格换成下划线，并套上 `/{key}.md`。例如传入 `2026-08-30`，实际键为 `/2026-08-30.md`。读取接口返回的是存储中的原始键，删除时请传格式化前的同一段文本，或自行去掉已有的前导 `/` 与结尾 `.md` 后再传，避免被重复包裹。

### `GET /memory/`

路由探活。

**响应**

```json
{"message": "这里是memory管理路由"}
```

### `POST /memory/long_term_info/read`

读取该用户全部长期记忆。`key`、`content` 可省略。

**请求体**

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `user_id` | string | 是 | 用户 ID |
| `key` | string | 否 | 本接口不使用 |
| `content` | string | 否 | 本接口不使用 |

**响应** 无记录时仍为 `success: true`，`total` 为 0。

```json
{
  "success": true,
  "user_id": "user01",
  "data": [
    {
      "user_id": "user01",
      "key": "/2026-08-30.md",
      "content": "记忆正文",
      "created_at": "创建时间",
      "modified_at": "修改时间",
      "encoding": "utf-8"
    }
  ],
  "data_type": "long_term_info",
  "total": 1,
  "message": "成功获取用户长期记忆"
}
```

无记录时 `message` 为 `未找到用户长期记忆`。

### `POST /memory/long_term_info/write`

按格式化后的 key 创建或覆盖一条长期记忆。已存在则保留原 `created_at`，并更新 `modified_at`。

**请求体**

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `user_id` | string | 是 | 用户 ID |
| `key` | string | 是 | 记忆键，不能为空 |
| `content` | string | 是 | 记忆正文，不能为空 |

**请求示例**

```json
{
  "user_id": "user01",
  "key": "2026-08-30",
  "content": "今天苏州下大雨"
}
```

**成功**

```json
{"success": true, "message": "成功创建用户长期记忆"}
```

已存在同 key 时 `message` 为 `成功更新用户长期记忆`。

**HTTP 400**

```json
{"detail": "写入长期记忆信息失败，key或content不能为空"}
```

### `POST /memory/long_term_info/delete`

删除一条长期记忆。`content` 可省略。

**请求体**

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `user_id` | string | 是 | 用户 ID |
| `key` | string | 是 | 与写入时相同的原始键 |

**成功**

```json
{"success": true, "message": "成功删除用户长期记忆"}
```

**HTTP 400**

```json
{"detail": "删除长期记忆信息失败，key不能为空"}
```

### `POST /memory/user_session_thread/details`

读取该线程 checkpoint 中的消息列表（短期记忆）。

**请求体**

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `user_id` | string | 是 | 用户 ID |
| `thread_id` | string | 是 | 会话线程，不能为空 |

**响应** 无消息时仍为 `success: true`。

```json
{
  "success": true,
  "agent_args": {"user_id": "user01", "thread_id": "t-..."},
  "total": 2,
  "data": [],
  "data_type": "thread_details",
  "message": "成功获取用户会话详情"
}
```

`data` 为 HumanMessage / AIMessage / ToolMessage 列表。无消息时 `message` 为 `未找到用户会话详情`。

**HTTP 400**

```json
{"detail": "获取用户会话详情失败，thread_id不能为空"}
```

### `POST /memory/user_session_thread/interrupt`

读取该线程当前挂起的中断。用于展示待审批工具，再调用中断恢复接口。

**请求体** 同会话详情。

**响应**

```json
{
  "success": true,
  "agent_args": {"user_id": "user01", "thread_id": "t-..."},
  "data": {
    "type": "Interrupt",
    "content": {},
    "id": "中断 id"
  },
  "data_type": "interrupt",
  "message": "成功获取会话中断信息"
}
```

无中断时 `data` 为 `{}`，`message` 为 `未找到会话中断信息`。

**HTTP 400**

```json
{"detail": "获取会话中断信息失败，thread_id不能为空"}
```

---

## 接口一览

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/` | 根路径探活 |
| GET | `/agent/` | Agent 路由探活 |
| POST | `/agent/run_agent/invoke` | 同步运行智能体 |
| POST | `/agent/run_agent/interrupts_judge/invoke` | 同步恢复中断 |
| POST | `/agent/run_agent/stream` | 流式运行智能体 |
| POST | `/agent/run_agent/interrupts_judge/stream` | 流式恢复中断 |
| GET | `/session/` | Session 路由探活 |
| POST | `/session/session_thread/create` | 创建会话线程 |
| POST | `/session/session_thread/user_thread_list` | 会话列表 |
| POST | `/session/session_thread/delete` | 删除会话线程 |
| GET | `/memory/` | Memory 路由探活 |
| POST | `/memory/long_term_info/read` | 读取长期记忆 |
| POST | `/memory/long_term_info/write` | 写入长期记忆 |
| POST | `/memory/long_term_info/delete` | 删除长期记忆 |
| POST | `/memory/user_session_thread/details` | 会话消息详情 |
| POST | `/memory/user_session_thread/interrupt` | 当前中断信息 |
