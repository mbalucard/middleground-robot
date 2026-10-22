---
name: internet-search
description: 查询公开网页。用户要搜网上的资料、新闻、最新情况，或给出网址要看页面内容时使用。门店、库存、商品、零售不要用本技能。
allowed-tools: internet_search fetch_internet_content
---

# 网页搜索与抓取

用 `internet_search` 搜公开网页，用 `fetch_internet_content` 抓取某一次结果里的链接或用户给出的网址。先按用户意图选工具，再调用。不要凭记忆编造标题、日期、数字或页面内容。

门店、仓库、库存、商品、区域、零售走对应的 ERP skill。不要改用网页搜索。

## 先选工具

| 用户要的 | 工具 |
| --- | --- |
| 网上的资料、新闻、最新情况，还没有具体网址 | `internet_search` |
| 已经有网址，或这次搜索的 `need_content` 是 `false`、要看某一条正文 | `fetch_internet_content` |

用户直接给了网址：先抓取。页面不够回答时，再按下面的次数规则搜索。

时效问题（今天、最近、今年、某日之后）先调用 `get_current_date`，用返回字符串开头的日期。不要沿用本轮更早的日期。

## 搜索次数

每个问题里，自己主动调用 `internet_search` 最多 2 次。

| 第几次 | count | 什么时候搜 |
| --- | --- | --- |
| 第 1 次 | `3` | 需要上网时 |
| 第 2 次 | `5` | 第 1 次的结果不能回答，或没有匹配 |
| 用户要求再搜 | `10` | 用户针对同一问题明确说再搜、重新搜、换一批 |

用户要求再搜时：

- 第 2 次还没发生：这一次就是第 2 次，`count=10`。不要先用 `5` 再搜一遍。
- 第 2 次已经用 `5` 搜过：可以应要求再搜一次，`count=10`，然后停止。
- 用户没要求：不要使用 `10`。两次之后不要自己再搜。

`count` 只用 `3`、`5`、`10`。不要传更大的数。`count` 大于 5 的那次，`need_content` 必须是 `false`。

同一次调用返回的 `data` 是这一次的结果集。同一条 `query` 再搜一次，结果可能不同。这次搜索的 `need_content` 是 `false` 时，要看某一条的正文，用该条的 `url` 抓取，不要为了正文把同一查询再搜一遍。这次已经是 `need_content=true` 时，正文就在 `content` 里，用户再追问细节也不要抓取。

## 搜索参数

| 参数 | 取值 |
| --- | --- |
| `query` | 必填。1～128 个字符，不能全是空白。问题较长时收成短搜索词 |
| `count` | 第 1 次 `3`，第 2 次 `5`。用户要求再搜同一问题时这一次用 `10` |
| `need_content` | 默认 `false`。用户一开始就要求细节、原文、具体内容，且这次 `count` 不超过 5 时，才传 `true`。`count` 大于 5 时必须是 `false` |
| `ori_question` | 可选。`query` 是改写后的短搜索词，且用户原话不超过 128 字时，可以把原话传上。`query` 已经是原话，或原话超过 128 字时，不传 |

`need_content=false` 时，每条的 `content` 是空字符串。用 `summary` 组织回答。要展开某一条，抓取该条 `url`。

用户从一开始就要细节，且这次 `count` 是 `3` 或 `5` 时，可以传 `need_content=true`。正文在该条的 `content`。这次已经拿过正文，之后用户再追问细节，直接用已有的 `content` 回答，不要对同一条再调用 `fetch_internet_content`。两者内容相同。

`count` 大于 5 时，`need_content` 必须是 `false`。一次带回多条正文，上下文会超长。用户要某一条的细节时，再抓取那一条的 `url`。

## 搜索语法

`query` 里的操作符会原样生效。用户限定了站点、语言或日期时再用。第一次不要堆很多操作符。

| 操作符 | 示例 | 作用 |
| --- | --- | --- |
| `site:` | `DeepSeek site:github.com` | 只留指定站点。多个站点用 `OR` 连接：`DeepSeek site:github.com OR site:huggingface.co` |
| `-site:` | `DeepSeek -site:example.com` | 排除站点。多个用空格分隔 |
| `-` | `DeepSeek -广告` | 排除关键词。多个用空格分隔 |
| `-"..."` | `DeepSeek -"release notes"` | 排除短语 |
| `"..."` | `DeepSeek "精确短语"` | 精确匹配短语 |
| `lang:` | `DeepSeek lang:zh,en` | 限定语言，多种用逗号分隔 |
| `after:` | `DeepSeek after:2025-01-01` | 只留该日期之后发布的网页。也可用年份 |
| `before:` | `DeepSeek before:2026-06-01` | 只留该日期之前发布的网页。也可用年份 |

相对日期先用 `get_current_date` 算出具体日期，再写入 `after:` 或 `before:`。

## 怎么读结果

成功时 `status` 为 `success`。`data` 是列表，每条字段：

| 字段 | 含义 |
| --- | --- |
| `rerank_score` | 0～3。大于等于 1.5 是优质结果 |
| `authority` | 0～4，`-1` 表示未知。大于等于 3 是高权威 |
| `title` | 标题 |
| `url` | 链接 |
| `snippet` | 短摘要，约 100～200 字 |
| `summary` | 长摘要，约 600～800 字。回答时以这个为准 |
| `content` | 网页正文。`need_content` 为 `false` 或正文缺失时是空字符串 |
| `site_name` | 站点名，可能为空 |
| `date` | 发布时间，上海时间，形如 `YYYY-MM-DD HH:MM:SS 星期几`。没有发布时间时是 `null` 或没有该字段 |

选用顺序：

1. 先用 `rerank_score` 大于等于 1.5 的结果。
2. 这些里面再优先 `authority` 大于等于 3 的。
3. 仍然接近时，用 `date` 更新的那条。
4. 没有任何一条达到 1.5：用分数最高的那条，并在回答里说明相关度一般。

`need_content=true` 时，用该条的 `content` 回答，不要再抓取这条 `url`。`need_content=false` 时，抓取到的正文优先于该条的 `summary` 和 `snippet`。多条说法冲突时并列写上，各自带发布日期。

抓取成功时 `status` 为 `success`。`data.title` 是页面标题，缺失时是空字符串。`data.content` 是 Markdown 正文。用正文回答，不要把整篇 Markdown 原样贴给用户。

只抓取 `need_content=false` 那次结果里的 `url`，或用户给出的网址。`need_content=true` 的结果不要再抓。一次抓一到两条真正要用的链接。网址必须是带主机名的 `http` 或 `https`，长度不超过 8192，不能带用户名或密码。

## 回答要求

- 用中文短列表或几句话，不要原样倒 JSON。
- 事实带上发布日期，只到日，取 `date` 里的 `YYYY-MM-DD`。`date` 为空时说明发布时间未知。
- 标题、链接、站点名，用户问到才给。
- 名称、数字、日期以工具结果为准。
- `status` 为 `error`，且 `message` 是 `{"results": []}` 或其中 `results` 为空数组时，说明没有匹配。这次占用一次搜索次数。还可以按次数规则改 `query` 再搜。不要说系统故障。
- `status` 为 `error` 且 `message` 里有 `error` 时，用 `error.message` 说明原因。403 告诉用户页面被拒绝。404 告诉用户抓不到正文。429 告诉用户请求过多，不要立刻重试。401 告诉用户搜索服务鉴权失败。402 告诉用户余额不足。其它 4xx 在不改参数的情况下不要重试。

## 只做其中一步

- 用户只要网上的结论：搜索，用 `summary` 回答。不要把每条都抓下来。
- 用户已经给了网址：只抓取。抓取内容不够时再搜索。
- 用户要某一条的细节，而这次搜索是 `need_content=false`、`content` 为空：只抓取这条 `url`，不要为了正文再搜一遍。
- 这次搜索已经是 `need_content=true`：用户追问细节时用已有的 `content`，不要再抓取。
