# middleground-robot

`middleground-robot` 是一个企业微信智能机器人服务。通过 WebSocket 长连接接收企微 AI Bot 回调，使用 DeepAgents / LangGraph 组织智能体执行，支持流式回复、工具调用、MCP 扩展、会话缓存，以及基于 PostgreSQL 的持久化记忆与执行状态存储。

当前默认智能体名称为 `Dawn`。

## 项目现状概览

已实现的核心能力：

- 企业微信 AI Bot WebSocket 订阅、心跳保活、消息与事件回调处理
- 文本消息流式回复；进入会话时发送欢迎语
- 单聊纯图片挂起（`image`：下载解密写入 Redis，最多 5 张 / 10 分钟；固定话术等待下一问）
- 挂起图追问：同用户同 `thread_id` 的后续 `text` 或 `mixed` 会带上挂起图（`mixed` 再合并本次附图）交由识图模型文字回复，答完清空（默认 DeepSeek Vision）
- 单聊消息忙锁：同一会话处理中时拒绝新请求，避免并发打断
- 基于 DeepAgents 的工具调用型 Agent（含 summarization / 模型选择中间件）
- Redis 维护 `thread_id`、消息中间态、工具调用中间态、纯图挂起队列与忙锁
- PostgreSQL 持久化问答记录、工具调用记录，以及 LangGraph checkpoint/store
- 内置工具：联网搜索、当前时间、店铺信息、销售数据查询
- MCP 工具：企业微信通讯录、企业微信会议（streamable HTTP）
- 通过 `/memories/` 提供跨会话长期记忆

当前限制：

- 群聊纯图片（`image`）企微通常不回调；请用 @机器人 + 图文（`mixed`）或单聊发图
- 纯图挂起满 5 张后拒绝再追加纯图；发 `mixed` 仍可与挂起图合并作答
- 不支持机器人回复图片；文件、语音、视频等仍返回“暂不支持”
- 运行依赖企业微信、PostgreSQL、Redis，以及模型相关密钥
- 销售/店铺类工具依赖额外的 MySQL 数据源；MCP 工具依赖对应服务 URL

## 技术栈

- Python `>=3.14`
- [deepagents](https://github.com/langchain-ai/deepagents)
- LangGraph / LangChain
- PostgreSQL / Redis
- WebSocket（`websockets`）
- Tavily Search
- MCP（`langchain-mcp-adapters`）
- pandas / SQLAlchemy / psycopg / aiomysql / pycryptodome

## 目录结构

```text
middleground-robot/
├── src/
│   └── qw_robot_main.py          # 主入口：企微 WS、订阅、心跳、消息分发
├── api/qw_robot/
│   ├── message_processing.py     # 消息回调、流式响应、识图流程、心跳
│   ├── media_handler.py          # 企微图片下载与 AES 解密
│   ├── pending_images.py         # 纯图 Redis 挂起队列
│   ├── mes_busy.py               # 单聊消息忙锁
│   ├── session_manager.py        # Redis 中间态与 Postgres 落库
│   ├── data_models.py            # 问答/工具调用表定义与建表
│   ├── data_interaction.py       # 数据写入逻辑
│   └── general_tools.py          # req_id、thread_id、send_json、WS 应答分发
├── robot/
│   ├── agents/
│   │   ├── main_agent.py         # Agent 构建入口
│   │   ├── agent_invoke.py       # 同步/流式调用、中断恢复
│   │   ├── agent_backend.py      # Filesystem + Store 组合后端
│   │   ├── model_middleware.py   # 模型选择中间件
│   │   ├── model_context.py      # Agent 运行上下文
│   │   ├── message_content.py    # 多模态 content 拼装与剥图
│   │   └── models.py             # DeepSeek / MiniMax 模型初始化
│   ├── tools/
│   │   ├── ordinary_tool.py      # 联网搜索、当前时间
│   │   ├── sale_tools.py         # 销售数据查询
│   │   ├── shop_info_tools.py    # 企业/门店/店铺信息查询
│   │   ├── mcp_server_tools.py   # MCP 工具加载
│   │   ├── memory_device.py      # Postgres checkpoint/store 资源
│   │   └── message_tool.py       # 消息整理工具
│   └── workspace/                # Agent 工作目录
│       ├── AGENTS.md             # 工作区说明与记忆约定
│       ├── sys_message.md        # 系统提示（持久化记忆规则）
│       └── me/                   # 身份 / 性格 / 长期记忆
├── configs/
│   ├── api_config.py             # 企微配置
│   ├── model_config.py           # 模型与搜索配置
│   ├── service_config.py         # Redis / Postgres / MySQL / 日志配置
│   ├── mcp_configs.py            # MCP 服务地址
│   └── general_config.py         # 项目路径等通用配置
├── data/sql/                     # 销售与店铺查询 SQL
├── utils/                        # DB、Redis、日志、时间等基础设施
├── main.py                       # 简单占位脚本
├── pyproject.toml                # 依赖声明
└── setup.py                      # 可编辑安装入口
```

## 运行流程

```text
企业微信消息 / 事件
    ↓
WebSocket 回调
    ↓
cmd 分流
    ├─ aibot_event_callback（如 enter_chat 欢迎语）
    └─ aibot_msg_callback → handle_msg_callback()
            ├─ 校验消息类型（text / image / mixed / 其它）
            ├─ 从 Redis 分配/续期 thread_id
            ├─ 单聊抢占忙锁（失败则提示任务进行中）
            ├─ image → 挂起队列，返回就绪话术
            ├─ text / mixed → 合并挂起图则走识图，否则走普通 Agent
            └─ 流式回复，结束后写 Redis/Postgres，释放忙锁
```

## Agent 与工具

`robot/agents/main_agent.py` 中 `build_agent()` 会挂载：

- 系统提示：`robot/workspace/sys_message.md`（身份见 `me/IDENTITY.md`，名称为 `Dawn`）
- summarization middleware、模型选择 middleware（默认 `manual`）
- 本地工具：
  - `internet_search`
  - `get_current_date`
  - `get_shop_sale_data`
  - `list_shops_with_sales`
  - `get_shop_info`
- MCP 工具：启动时通过 `QwMcp.get_tools()` 从配置的 MCP 服务动态加载

说明：

- `Context.model` 可指定 `deepseek`、`minimax`、`minimax_m3` 或 `deepseek_vision`
- 有图消息默认走 `deepseek_vision`；可切到 `minimax_m3`
- `DynamicModelSelectionMiddleware` 已实现，当前默认未启用

### 识图 provider（`openai` / `anthropic`）

多模态 content 拼装与 provider → 模型映射在 `robot/agents/message_content.py`。企微侧 `_handle_vision_flow` 默认：

```python
provider: Literal["openai", "anthropic"] = "openai"
```

| `provider` | content 协议 | `Context.model` | 实际模型 |
|---|---|---|---|
| `openai`（默认） | OpenAI `image_url` + `data:` URL | `deepseek_vision` | `deepseek-v4-flash-vision-exp` |
| `anthropic` | Anthropic `image` + `source.base64` | `minimax_m3` | MiniMax-M3 |

注意：这里的 `anthropic` **不是** DeepSeek 的 Anthropic 兼容端点，而是「Anthropic 风格多模态 content + MiniMax-M3」。切换识图后端时，改 `_handle_vision_flow` 的 `provider` 即可；纯图 Redis 挂起只存 `{media_type, data}`，与协议无关。

### 非 vision 回合剥图

同 `thread_id` 识图后，checkpoint 里仍保留带图的 HumanMessage。后续纯文本默认走 `deepseek` 时，`ConfigurableModelMiddleware` 通过 `strip_images_from_messages` 在**本次请求视图**中剥掉图片块并补提示——不写回 checkpoint。追问图中细节依赖此前 vision 助手的文字回复。

## 存储设计

### Redis

短期状态：

- 用户会话 `thread_id`（默认 TTL 见 `SESSION_TIMEOUT`，约 300 秒并带抖动）
- 消息处理中间态、工具调用中间态
- 纯图挂起队列、单聊忙锁

典型 Key：

- `message:{user_id}+{message_id}`
- `tool_calls:{message_id}+{tool_call_id}`
- `pending_images:{userid}:{thread_id}`
- `mes_busy:{userid}:{thread_id}`

### PostgreSQL

业务表：

- `qw_robot_messages`
- `qw_robot_tool_calls`

LangGraph 通过 `AsyncPostgresSaver` / `AsyncPostgresStore` 维护 checkpoint 与 store，用于会话状态与 `/memories/` 长期记忆。

### `/memories/` 长期记忆

系统提示要求将用户长期事实写入 `/memories/user_profile.md`，并按日记录 `/memories/YYYY-MM-DD.md`。该路径由 `StoreBackend` 按 `user_id` 隔离，落在 Postgres store。

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

## 安装与启动

### 1. 安装依赖

推荐使用 `uv`：

```bash
uv sync
uv pip install -e .
```

### 2. 启动机器人主程序

```bash
python -m src.qw_robot_main
```

或：

```bash
python src/qw_robot_main.py
```

启动后会：

1. 初始化 `qw_robot_messages` 与 `qw_robot_tool_calls`
2. 连接企业微信 WebSocket，执行 `aibot_subscribe`
3. 启动心跳协程
4. 构建 Agent（含 MCP 工具加载）
5. 接收消息并流式回复

## 本地调试

调试 Agent 构建：

```bash
python -m robot.agents.main_agent
```

调试流式 Agent 调用：

```bash
python -m robot.agents.agent_invoke
```

说明：这两个入口同样依赖模型配置与 PostgreSQL。

## 依赖摘要

`pyproject.toml` 主要依赖：

- `deepagents`
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
- `httpx`

## 注意事项

- 正式入口是 `src/qw_robot_main.py`，根目录 `main.py` 只是打印 Python 版本的占位脚本
- `model_config.py` 中部分环境变量会在导入阶段直接校验，缺失时抛错
- 若只验证企微接入、不用销售类工具，仍建议补齐 MySQL 配置，避免工具初始化出错
- MCP URL 未配置时，对应 MCP 工具可能加载失败，需保证服务可用或调整启动逻辑
- 单聊忙锁 TTL 为 300 秒；纯图挂起最多 5 张、TTL 10 分钟
