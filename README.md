# middleground-robot

`middleground-robot` 是一个企业微信智能机器人服务。项目通过 WebSocket 长连接接收企微 AI Bot 回调消息，使用 DeepAgents / LangGraph 组织智能体执行，支持流式回复、工具调用、会话缓存，以及基于 PostgreSQL 的持久化记忆与执行状态存储。

当前默认智能体名称为 `Dawn`。

## 项目现状概览

当前代码已经实现的核心能力：

- 企业微信 AI Bot WebSocket 订阅、心跳保活、消息回调处理
- 文本消息的流式回复
- 单聊纯图片挂起（`image`：下载解密写入 Redis，最多 5 张 / 10 分钟；固定话术等待下一问，不立刻描述内容）
- 挂起图追问：同用户同 `thread_id` 的后续 `text` 或 `mixed` 会带上挂起图（`mixed` 再合并本次附图）交由 MiniMax-M3 文字回复，答完清空
- 基于 DeepAgents 的工具调用型 Agent
- Redis 维护 `thread_id`、消息中间态、工具调用中间态与纯图挂起队列
- PostgreSQL 持久化问答记录、工具调用记录，以及 LangGraph checkpoint/store
- 支持联网搜索、当前时间、店铺信息查询、销售数据查询
- 通过 `/memories/` 提供跨会话长期记忆能力

当前明确的限制：

- 群聊纯图片（`image`）企微通常不回调；请用 @机器人 + 图文（`mixed`）或单聊发图
- 纯图挂起满 5 张后拒绝再追加纯图；发 `mixed` 仍可与挂起图合并作答
- 不支持机器人回复图片；文件、语音、视频等仍返回“暂不支持”
- 运行依赖较多，至少需要企业微信、PostgreSQL、Redis，以及模型相关密钥
- 销售/店铺类工具还依赖额外的 MySQL 数据源配置

## 技术栈

- Python `>=3.14`
- [deepagents](https://github.com/langchain-ai/deepagents)
- LangGraph / LangChain
- PostgreSQL
- Redis
- WebSocket（`websockets`）
- Tavily Search
- pandas / SQLAlchemy / psycopg / aiomysql

## 目录结构

```text
middleground-robot/
├── src/
│   └── qw_robot_main.py          # 主入口，建立企微 WS 连接并消费消息
├── api/qw_robot/
│   ├── message_processing.py     # 消息回调、流式响应、心跳
│   ├── media_handler.py          # 企微图片下载与 AES 解密
│   ├── pending_images.py         # 纯图 Redis 挂起队列
│   ├── session_manager.py        # Redis 中间态与 Postgres 落库
│   ├── data_models.py            # 问答/工具调用表定义与建表
│   ├── data_interaction.py       # 数据写入逻辑
│   └── general_tools.py          # req_id、thread_id、send_json、WS 应答分发
├── robot/
│   ├── agents/
│   │   ├── main_agent.py         # Agent 构建入口
│   │   ├── agent_invoke.py       # 同步调用、流式调用、中断恢复
│   │   ├── agent_backend.py      # Agent 后端组合
│   │   ├── model_middleware.py   # 模型选择中间件
│   │   ├── model_context.py      # Agent 运行上下文
│   │   └── models.py             # DeepSeek / MiniMax 模型初始化
│   ├── tools/
│   │   ├── ordinary_tool.py      # 联网搜索、当前时间
│   │   ├── sale_tools.py         # 销售数据查询
│   │   ├── shop_info_tools.py    # 企业/门店/店铺信息查询
│   │   ├── memory_device.py      # Postgres checkpoint/store 资源
│   │   └── message_tool.py       # 消息整理工具
│   └── workspace/                # Agent 工作目录（本地记忆、skills 等）
├── configs/
│   ├── api_config.py             # 企微配置
│   ├── model_config.py           # 模型与搜索配置
│   ├── service_config.py         # Redis / Postgres / MySQL / 日志配置
│   └── general_config.py         # 项目路径等通用配置
├── data/sql/                     # 销售与店铺查询 SQL
├── utils/                        # DB、Redis、日志等基础设施
├── main.py                       # 简单占位脚本
├── pyproject.toml                # 依赖声明
└── setup.py                      # 可编辑安装入口
```

## 运行流程

```text
企业微信消息
    ↓
WebSocket 回调
    ↓
handle_msg_callback()
    ├─ 校验消息类型
    ├─ 从 Redis 分配/续期 thread_id
    ├─ 记录消息中间态
    └─ 创建流式回复气泡
            ↓
       stream_agent()
            ├─ 调用 DeepAgent
            ├─ 逐步产出文本/工具调用状态
            ├─ 工具调用结果暂存 Redis
            └─ 完成后写入 PostgreSQL
                    ↓
             企微侧 finish=true 收尾
```

## Agent 与工具

`robot/agents/main_agent.py` 中会构建主智能体，并挂载以下能力：

- 系统提示词，定义机器人身份 `Dawn`
- summarization middleware
- 模型选择 middleware
- 工具列表：
  - `internet_search`
  - `get_current_date`
  - `get_shop_sale_data`
  - `list_shops_with_sales`
  - `get_shop_info`

说明：

- 当前代码里 `build_agent()` 默认使用 `manual` 模式的模型中间件
- `Context.model` 可指定 `deepseek`、`minimax` 或 `minimax_m3`（有图消息会走 `minimax_m3`）
- `DynamicModelSelectionMiddleware` 已实现，但当前默认未启用

## 存储设计

### Redis

主要用于短期状态管理：

- 用户会话 `thread_id`
- 消息处理中间态
- 工具调用处理中间态

典型 Key：

- `message:{user_id}+{message_id}`
- `tool_calls:{message_id}+{tool_call_id}`

### PostgreSQL

业务表：

- `qw_robot_messages`
- `qw_robot_tool_calls`

另外，LangGraph 还会通过 `AsyncPostgresSaver` 和 `AsyncPostgresStore` 自动维护 checkpoint/store 相关表，用于会话状态与长期记忆。

### `/memories/` 长期记忆

Agent 系统提示中要求把用户长期事实写入 `/memories/user_profile.md`。这部分能力依赖 Agent backend 与 Postgres store，目的是让机器人在跨会话时仍能记住用户信息。

## 环境变量

在项目根目录创建 `.env`。

### 企业微信

```bash
QYWX_BOT_URL=
QYWX_BOT_ID=
QYWX_BOT_SECRET=
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
REDIS_DB=3
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

### 2. 准备工作目录

如果本地还没有 Agent 工作目录，可以先创建：

```bash
mkdir -p robot/workspace/skills
```

### 3. 启动机器人主程序

```bash
python -m src.qw_robot_main
```

或：

```bash
python src/qw_robot_main.py
```

启动后会执行：

1. 初始化 `qw_robot_messages` 与 `qw_robot_tool_calls`
2. 连接企业微信 WebSocket
3. 执行 `aibot_subscribe`
4. 启动心跳协程
5. 接收文本消息并流式回复

## 本地调试

调试 Agent 构建：

```bash
python -m robot.agents.main_agent
```

调试流式 Agent 调用：

```bash
python -m robot.agents.agent_invoke
```

说明：这两个调试入口同样依赖模型配置与 PostgreSQL 连接。

## 依赖摘要

`pyproject.toml` 当前声明的主要依赖包括：

- `deepagents`
- `langgraph-checkpoint-postgres`
- `langchain-deepseek`
- `redis`
- `psycopg[binary]`
- `sqlalchemy`
- `pandas`
- `aiomysql`
- `tavily-python`

## 注意事项

- 正式入口是 `src/qw_robot_main.py`，根目录 `main.py` 只是打印 Python 版本的占位脚本
- `model_config.py` 中部分环境变量会在导入阶段直接校验，缺失时会抛错
- 如果只想验证企微接入链路但不使用销售类工具，仍建议补齐 MySQL 配置，避免后续工具初始化时出错
- 日志默认写入 `logfile/app.log`

## 后续可补充

如果准备继续完善这个项目，建议优先补这几项：

- 增加 `.env.example`
- 在 `README.md` 中补一张部署架构图
- 明确企微回调协议版本和接入前置条件
- 为主要工具和消息链路补充测试用例
