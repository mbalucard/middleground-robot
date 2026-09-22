# middleground-robot

`middleground-robot` 是一个企业微信智能机器人与 Agent HTTP API 服务。企微侧通过 WebSocket 长连接收消息，再经 HTTP 调用本仓库 FastAPI，由 DeepAgents / LangGraph 执行智能体；支持流式回复、工具调用、MCP 扩展、图文理解，以及基于 PostgreSQL 的会话与长期记忆。

当前默认智能体名称为 `Dawn`。

## 项目现状概览

架构为双进程：

1. **FastAPI**（默认 `8010`）：Agent / 会话 / 记忆 HTTP 接口，负责模型调用与业务落库
2. **企微适配进程**（`qw_main`）：WebSocket 订阅企微，媒体下载与挂起图，再调用 FastAPI

已实现的核心能力：

- 企业微信 AI Bot WebSocket 订阅、心跳保活、消息与事件回调处理
- 文本消息流式回复；进入会话时发送欢迎语
- 单聊纯图片挂起（`image`：下载解密写入 Redis，最多 5 张 / 10 分钟；固定话术等待下一问）
- 挂起图追问：同用户同 API `thread_id` 的后续 `text` 或 `mixed` 会带上挂起图交由识图模型文字回复（默认 DeepSeek Vision / `provider=openai`）
- 单聊消息忙锁：同一会话处理中时拒绝新请求，避免并发打断
- FastAPI：`/agent` 同步与流式调用、中断恢复路由；`/session` 会话线程；`/memory` 长期记忆与会话详情
- 基于 DeepAgents 的工具调用型 Agent（含 summarization / 模型选择中间件）
- Redis：企微侧 API `thread_id` 映射、纯图挂起队列、忙锁；API 侧中断会话等
- PostgreSQL：`user_threads` / `user_thread_messages` / `message_tool_calls`，以及 LangGraph checkpoint/store
- 内置工具：联网搜索、当前时间、店铺信息、销售数据查询
- MCP 工具：企业微信通讯录、企业微信会议（streamable HTTP）
- 通过 `/memories/`（Agent 工作区约定）与 `/memory` HTTP 路由提供跨会话长期记忆

当前限制：

- 群聊纯图片（`image`）企微通常不回调；请用 @机器人 + 图文（`mixed`）或单聊发图
- 纯图挂起满 5 张后拒绝再追加纯图；发 `mixed` 仍可与挂起图合并作答（合计超过 API 上限 10 张会在企微侧提示）
- 不支持机器人回复图片；文件、语音、视频等仍返回“暂不支持”
- 企微侧工具 interrupt：单聊出按钮审批卡（同意/拒绝；多工具含全部同意/拒绝）；群聊仅提示无审批权限；审批中再发文本/图文会自动拒绝原审批；恢复结果经 `aibot_send_msg` markdown 推送
- 运行依赖企业微信、PostgreSQL、Redis、FastAPI 进程，以及模型相关密钥
- 销售/店铺类工具依赖额外的 MySQL 数据源；MCP 工具依赖对应服务 URL

## 技术栈

- Python `>=3.14`
- [deepagents](https://github.com/langchain-ai/deepagents)
- LangGraph / LangChain
- FastAPI / uvicorn / httpx
- PostgreSQL / Redis
- WebSocket（`websockets`）
- Tavily Search
- MCP（`langchain-mcp-adapters`）
- pandas / SQLAlchemy / psycopg / aiomysql / pycryptodome

## 目录结构

```text
middleground-robot/
├── src/
│   ├── fastapi_main.py           # FastAPI 入口（Agent / Session / Memory）
│   ├── qw_main.py                # 企微 WS 入口（适配层，HTTP 调 API）
│   └── routes/
│       ├── agent_interactive.py  # /agent 调用与流式、中断恢复
│       ├── session_management.py # /session 会话线程
│       └── memory_management.py  # /memory 长期记忆与会话详情
├── api/qw_api_robot/
│   ├── message_processing.py     # 消息回调、流式响应、图文流程、心跳、审批卡
│   ├── api_client.py             # HTTP 调 FastAPI（session / agent stream / interrupts_judge）
│   ├── stream_agent.py           # NDJSON → 企微展示事件（text / interrupt）
│   ├── interrupt_draft.py        # 审批草稿（挂 qw_api_thread Hash）
│   ├── interrupt_card.py         # 审批卡片结构
│   ├── media_handler.py          # 企微图片下载与 AES 解密
│   ├── pending_images.py         # 纯图 Redis 挂起队列
│   ├── mes_busy.py               # 单聊消息忙锁
│   └── general_tools.py          # req_id、API thread 缓存、WS 收发分发
├── robot/
│   ├── agents/                   # Agent 构建、调用与模型层
│   │   ├── main_agent.py         # Agent 构建入口
│   │   ├── agent_invoke.py       # 同步/流式调用、中断恢复
│   │   ├── agent_backend.py      # Filesystem + Store 组合后端
│   │   ├── model_middleware.py   # 模型选择中间件
│   │   ├── model_context.py      # Agent 运行上下文
│   │   └── models.py             # DeepSeek / MiniMax 模型初始化
│   ├── agent_tools/              # Agent 可调用的工具
│   │   ├── ordinary_tool.py      # 联网搜索、当前时间
│   │   ├── sale_tools.py         # 销售数据查询
│   │   ├── shop_info_tools.py    # 企业/门店/店铺信息查询
│   │   └── mcp_server_tools.py   # MCP 工具加载
│   ├── tools/                    # 运行用组件（非工具挂载）
│   │   ├── message_content.py    # 多模态 content 拼装与剥图
│   │   ├── message_tool.py       # 消息整理工具
│   │   └── memory_device.py      # Postgres checkpoint/store 资源
│   └── workspace/                # Agent 工作目录
│       ├── AGENTS.md
│       ├── sys_message.md
│       └── me/                   # 身份 / 性格 / 长期记忆约定
├── configs/
│   ├── api_config.py             # 企微与 APIConfig.url
│   ├── model_config.py           # 模型与搜索配置
│   ├── service_config.py         # Redis / Postgres / MySQL / 日志配置
│   ├── mcp_configs.py            # MCP 服务地址
│   └── general_config.py         # 项目路径等通用配置
├── utils/                        # DB、Redis、日志、api_utils 等
├── data/sql/                     # 销售与店铺查询 SQL
├── main.py                       # 简单占位脚本
├── pyproject.toml
└── setup.py
```

## 运行流程

```text
企业微信消息 / 事件
    ↓
qw_main（WebSocket）
    ↓
cmd 分流
   ├─ aibot_event_callback（如 enter_chat 欢迎语）
   └─ aibot_msg_callback → handle_msg_callback()
            ├─ Redis 获取/创建 API thread_id（未命中则 POST /session/.../create）
            ├─ 单聊抢占忙锁
            ├─ image → 挂起队列，返回就绪话术
            ├─ text / mixed → 合并挂起图则带 images 调 API，否则纯文本调 API
            └─ POST /agent/run_agent/stream → 解析 NDJSON → 企微流式刷新
               └─ 若 data_type=interrupt（单聊）→ finish stream → 被动 template_card 审批
                  └─ template_card_event → update 卡 → 凑齐后 POST interrupts_judge/stream
                     → aibot_send_msg markdown 回结果（再 interrupt 则主动推下一张卡）

FastAPI（fastapi_main）
    ├─ 校验会话 / 图文
    ├─ run_agent_astream（落库由 BackgroundTasks 写入业务表）
    └─ LangGraph checkpoint / store
```

## Agent 与工具

`robot/` 下按职责拆分：

- `agents/`：Agent 构建、调用、模型与中间件
- `agent_tools/`：挂载到 Agent 的可调用工具（本地工具 + MCP）
- `tools/`：运行期辅助组件（多模态 content、消息解析、Postgres 资源等）

`robot/agents/main_agent.py` 中 `build_agent()` 会挂载：

- 系统提示：`robot/workspace/sys_message.md`（身份见 `me/IDENTITY.md`，名称为 `Dawn`）
- summarization middleware、模型选择 middleware（默认 `manual`）
- 本地工具：`internet_search`、`get_current_date`、`get_shop_sale_data`、`list_shops_with_sales`、`get_shop_info`
- MCP 工具：启动时通过 `QwMcp.get_tools()` 从配置的 MCP 服务动态加载

说明：

- `Context.model` / `model_label` 可指定：`deepseek`、`minimax_m27`、`minimax_m3`、`aihubmix_minimax_m27`、`aihubmix_minimax_m3`
- `deepseek` 对应实际模型名 `deepseek-flash`；有图时需搭配 `provider=openai`
- `DynamicModelSelectionMiddleware` 已实现，当前默认未启用

### 识图 provider（`openai` / `anthropic`）

多模态 content 拼装在 `robot/tools/message_content.py`；API 校验见 `utils/api_utils/vision_request.py`。企微侧默认 `provider="openai"`、`model_label=deepseek`。

| `provider` | content 协议 | `model_label` | 实际模型 |
|---|---|---|---|
| `openai` | OpenAI `image_url` + `data:` URL | `deepseek` | deepseek-flash |
| `anthropic` | Anthropic `image` + `source.base64` | `minimax_m3` / `aihubmix_minimax_m3` | MiniMax-M3 |

注意：这里的 `anthropic` **不是** DeepSeek 的 Anthropic 兼容端点，而是「Anthropic 风格多模态 content + MiniMax-M3」。纯图 Redis 挂起只存 `{media_type, data}`，与协议无关。

### FastAPI 图文（`/agent/run_agent/invoke` · `/stream`）

一次 JSON 提交文字 + 图（`images[].data` 为 base64 或 data URL，JPEG/PNG/GIF/WEBP，最多 10 张）。有图时 `provider` 必填，且须与上表白名单一致；业务库 `query` 存为 `[图片] {原文}`，不落原图。

### 非 vision 回合剥图

同 `thread_id` 识图后，checkpoint 里仍保留带图的 HumanMessage。后续纯文本默认走 `deepseek` 时，`ConfigurableModelMiddleware` 通过 `strip_images_from_messages` 在**本次请求视图**中剥掉图片块并补提示——不写回 checkpoint。追问图中细节依赖此前 vision 助手的文字回复。

## 存储设计

### Redis

企微适配侧：

- `qw_api_thread:{userid}`：缓存当前 API `thread_id`（TTL 约 600 秒，过期后重新 create）；Hash 字段 `interrupt_draft` 存工具审批草稿（逻辑过期 `expires_at` 600 秒）
- `pending_images:{userid}:{thread_id}`：纯图挂起
- `mes_busy:{userid}:{thread_id}`：单聊忙锁

API 侧另有中断会话等 Key（由 `SessionRedis` 管理）。

### PostgreSQL

业务表（由 FastAPI 写入）：

- `user_threads`
- `user_thread_messages`
- `message_tool_calls`

LangGraph 通过 `AsyncPostgresSaver` / `AsyncPostgresStore` 维护 checkpoint 与 store，用于会话状态与 `/memories/` 长期记忆。

### `/memories/` 长期记忆

系统提示要求将用户长期事实写入 `/memories/user_profile.md`，并按日记录 `/memories/YYYY-MM-DD.md`。该路径由 `StoreBackend` 按 `user_id` 隔离，落在 Postgres store。HTTP 侧也可通过 `/memory/long_term_info/*` 读写。

## 环境变量

通过环境变量配置（可用 dotenv 在启动时加载）。必填项在 `configs/model_config.py` 导入阶段会校验。

### 企业微信

```bash
QYWX_BOT_URL=
QYWX_BOT_ID=
QYWX_BOT_SECRET=
```

### MCP（可选，缺省则对应服务不可用）

```bash
QYWX_MCP_TOOL_USER_URL=
QYWX_MCP_TOOL_MEETING_URL=
```

### DeepSeek

```bash
DEEPSEEK_BASE_URL_OPENAI=
DEEPSEEK_BASE_URL_ANTHROPIC=
DEEPSEEK_API_KEY=
```

### MiniMax

```bash
MINIMAX_ANTHROPIC_URL=
MINIMAX_KEY=
```

### Tavily

```bash
TAVILY_API_KEY=
```

### PostgreSQL

```bash
PS_USER=
PS_PASSWORD=
PS_HOST=
PS_PORT=
PS_DATABASE=
```

### Redis

```bash
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0
SESSION_TIMEOUT=300
REDIS_TTL=3600
```

### 销售查询 MySQL 数据源

```bash
DemingMySQLUser=
DemingMySQLPassword=
DemingMySQLHost=
DemingMySQLPort=
```

企微调 API 的基址在 `configs/api_config.py` 的 `APIConfig.url`（默认 `http://127.0.0.1:8010`）。本地调用使用 `httpx` 时需 `trust_env=False`，避免系统代理截走本机请求。

## 安装与启动

### 1. 安装依赖

推荐使用 `uv`：

```bash
uv sync
uv pip install -e .
```

### 2. 启动（两个进程）

先启动 FastAPI，等到日志出现 `Application startup complete`：

```bash
uv run src/fastapi_main.py
```

再启动企微适配进程：

```bash
uv run src/qw_main.py
```

说明：

1. FastAPI 初始化 Redis、Postgres、Agent（含 MCP），监听 `0.0.0.0:8010`
2. `qw_main` 连接企微 WebSocket，执行 `aibot_subscribe`，启动心跳，收消息后 HTTP 调 API
3. 勿同时再跑旧的企微直连入口（若仓库中仍保留）

## 本地调试

调试 Agent 构建：

```bash
uv run python -m robot.agents.main_agent
```

该入口依赖模型配置与 PostgreSQL。

## 依赖摘要

`pyproject.toml` 主要依赖：

- `deepagents`
- `fastapi` / `httpx`
- `langgraph-checkpoint-postgres`
- `langchain-deepseek`
- `langchain-mcp-adapters`
- `redis`
- `psycopg[binary]`
- `sqlalchemy`
- `pandas`
- `aiomysql`
- `tavily-python`
- `pycryptodome`

## 注意事项

- 正式企微入口是 `src/qw_main.py`，Agent HTTP 入口是 `src/fastapi_main.py`；根目录 `main.py` 只是占位脚本
- `model_config.py` 中部分环境变量会在导入阶段直接校验，缺失时抛错
- 若只验证企微接入、不用销售类工具，仍建议补齐 MySQL 配置，避免工具初始化出错
- MCP URL 未配置时，对应 MCP 工具可能加载失败，需保证服务可用或调整启动逻辑
- 单聊忙锁 TTL 为 300 秒；纯图挂起最多 5 张、TTL 10 分钟；企微侧 API `thread_id` 映射约 600 秒
