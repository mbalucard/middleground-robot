# middleground-robot

企业微信智能机器人服务：通过 WebSocket 长连接接收企微消息，基于 [DeepAgents](https://github.com/langchain-ai/deepagents) / LangGraph 构建名为 **Dawn** 的 AI 助手，支持流式回复、工具调用与跨会话长期记忆。

## 功能概览

- 企业微信 AI Bot WebSocket 订阅、心跳保活、欢迎语与流式文本回复
- DeepAgent 智能体（DeepSeek / MiniMax），可手动或按消息量自动切换模型
- 内置工具：联网搜索（Tavily）、获取当前时间
- PostgreSQL：对话/工具调用落库 + LangGraph Checkpoint / Store（短期状态与长期记忆）
- Redis：会话 `thread_id` 管理、消息与工具调用的短时缓存
- 按 `user_id` 隔离的 `/memories/` 长期记忆目录

## 技术栈

| 类别 | 选型 |
| ------ | ------ |
| 语言 / 包管理 | Python ≥ 3.14，[uv](https://github.com/astral-sh/uv) |
| Agent | deepagents、LangGraph、LangChain |
| 模型 | DeepSeek、MiniMax |
| 存储 | PostgreSQL（SQLAlchemy / psycopg）、Redis |
| 接入 | 企业微信 WebSocket（`websockets`） |
| 搜索 | Tavily |

## 项目结构

```text
middleground-robot/
├── src/
│   └── qw_robot_main.py      # 主入口：企微 WS 连接与消息循环
├── api/qw_robot/               # 企微侧 API 与会话
│   ├── message_processing.py # 消息回调、流式回复、心跳
│   ├── session_manager.py    # Redis 缓存 → Postgres 落库
│   ├── data_models.py        # 表模型与 init_db
│   ├── data_interaction.py   # 消息 / 工具调用写入
│   └── general_tools.py      # req_id、thread_id、send_json 等
├── robot/
│   ├── agents/               # 智能体构建与调用
│   │   ├── main_agent.py     # create_deep_agent
│   │   ├── agent_invoke.py   # invoke / stream / 中断恢复
│   │   ├── models.py         # 模型实例
│   │   ├── model_middleware.py
│   │   ├── model_context.py
│   │   └── agent_backend.py  # 文件系统 + Store 组合后端
│   └── tools/                # 工具与记忆资源
│       ├── ordinary_tool.py  # 搜索、日期
│       ├── memory_device.py  # Postgres checkpointer / store
│       └── message_tool.py   # 消息解析与历史修剪
├── configs/                  # 环境变量驱动的配置
├── utils/                    # DB / Redis / 日志
├── main.py                   # 占位（打印 Python 版本）
├── pyproject.toml
└── setup.py                  # 可编辑安装：uv pip install -e .
```

运行时还会使用（默认被 `.gitignore` 忽略，需本地准备）：

- `.env`：密钥与连接信息
- `logfile/`：滚动日志
- `robot/workspace/`：Agent 工作区（`AGENTS.md`、`skills/` 等）

## 架构与数据流

```text
企微用户消息
    │
    ▼
WebSocket (aibot_subscribe / aibot_msg_callback)
    │
    ▼
message_processing.handle_msg_callback
    │  · Redis 分配 / 续期 thread_id
    │  · 创建流式气泡「正在思考...」
    ▼
stream_agent (DeepAgent + Postgres checkpointer/store)
    │  · 工具调用过程写入 Redis → Postgres
    │  · 增量内容通过 aibot_respond_msg (msgtype=stream) 推送
    ▼
finish=true 结束流式气泡；问答落库 qw_robot_messages
```

长期记忆：`CompositeBackend` 将默认文件操作落到 `robot/workspace/`，`/memories/` 路由到 Postgres `StoreBackend`，按 `user_id` 命名空间隔离。

## 环境要求

- Python **≥ 3.14**（见 `.python-version`）
- PostgreSQL（对话表 + LangGraph checkpoint/store）
- Redis（会话与消息缓存）
- 企业微信 AI 机器人 WebSocket 地址、Bot ID、Secret
- DeepSeek / MiniMax / Tavily API Key

## 快速开始

### 1. 安装依赖

```bash
# 建议使用 uv
uv sync
uv pip install -e .
```

### 2. 配置环境变量

在项目根目录创建 `.env`（勿提交）。主要变量如下：

```bash
# 企业微信机器人
QYWX_BOT_URL=
QYWX_BOT_ID=
QYWX_BOT_SECRET=

# DeepSeek
DEEPSEEK_BASE_URL_OPENAI=
DEEPSEEK_BASE_URL_ANTHROPIC=
DEEPSEEK_API_KEY=

# MiniMax
MINIMAX_ANTHROPIC_URL=
MINIMAX_KEY=

# Tavily 搜索
TAVILY_API_KEY=

# PostgreSQL
PS_USER=
PS_PASSWORD=
PS_HOST=
PS_PORT=
PS_DATABASE=

# Redis（可选，有默认值）
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=3
SESSION_TIMEOUT=300
REDIS_TTL=3600
```

### 3. 准备工作区（可选但推荐）

```bash
mkdir -p robot/workspace/skills
# 可在 robot/workspace/AGENTS.md 中编写 Agent 记忆/指令
```

### 4. 启动服务

```bash
python -m src.qw_robot_main
# 或
python src/qw_robot_main.py
```

启动后会：

1. `init_db()` 创建表 `qw_robot_messages`、`qw_robot_tool_calls`
2. 连接企微 WebSocket 并 `aibot_subscribe`
3. 后台心跳（默认 30s）
4. 收到文本消息后流式调用 Agent 并回复

本地单独调试 Agent（不连企微）：

```bash
python -m robot.agents.main_agent
# 或
python -m robot.agents.agent_invoke
```

## 核心模块说明

### 配置 (`configs/`)

| 模块 | 作用 |
| ------ | ------ |
| `api_config.py` | 企微 Bot URL / ID / Secret |
| `model_config.py` | DeepSeek、MiniMax、Tavily |
| `service_config.py` | Postgres、Redis、日志路径、API Host/Port |
| `general_config.py` | 项目根路径等 |

### Agent (`robot/agents/`)

- **`build_agent`**：`create_deep_agent`，挂载 summarization 中间件、模型选择中间件、工具与系统提示
- **`stream_agent`**：面向企微的异步流式输出，并同步写入工具调用与最终回答
- **模型中间件**：`manual`（按 `context.model`）或 `auto`（消息数 > 10 切 MiniMax）

### 会话与存储

- Redis Key 示例：`message:{user_id}+{message_id}`、`tool_calls:{message_id}+{tool_call_id}`；用户 `thread_id` 按 userid 哈希缓存
- 问答与工具调用在流式结束后写入 Postgres

## 数据库表

| 表名 | 说明 |
|------|------|
| `qw_robot_messages` | 对话记录（question / answer / thread_id / user_id 等） |
| `qw_robot_tool_calls` | 工具调用记录（name / input / output） |

另有 LangGraph 通过 `AsyncPostgresSaver` / `AsyncPostgresStore` 自动维护的 checkpoint 与 store 表。

## 当前能力边界

- 企微侧目前仅处理 **文本** 消息；图片/文件等会回复「暂不支持」
- `main.py` 仅为版本探测占位，正式入口是 `src/qw_robot_main.py`
- `robot/tools/general_tool.py` 目前为空文件，可扩展自定义工具

## 开发说明

```bash
# 可编辑安装后，按包路径导入
uv pip install -e .

# 日志默认写入 logfile/app.log（目录自动创建，已被 gitignore）
```

依赖声明见 `pyproject.toml`；锁定版本见 `uv.lock`。
