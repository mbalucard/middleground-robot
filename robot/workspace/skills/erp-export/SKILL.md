---
name: erp-export
description: 将 ERP 查询结果导出为表格文件。用户明确说导出、下载、把数据发给我时使用。只导出本 skill 列出的 7 个分页 ERP 工具数据；库存、零售、门店等查询条件仍按对应 ERP skill。用户没说导出时不要主动导出。
allowed-tools: export_erp_data_to_excel get_current_date get_goods_info get_warehouse_info get_inventory_data get_inventory_audit_summary_data get_shop_available_info get_shop_retail_info get_store_goods_retail_info
---

# ERP 数据导出

用 `export_erp_data_to_excel` 把某个 ERP 分页工具的全量结果落到表格。只处理用户主动要导出的场景。不要凭记忆编造行数或文件路径。

本 skill **只能**导出下列 7 个工具的数据（均带 `size` / `page_info`）。`get_region_tree_info` 无分页，**不要**导出。其它非 ERP 工具也不要走本导出工具。

| 可导出工具 | 筛选条件说明（需要时再读） |
| --- | --- |
| `get_goods_info` | `/skills/erp-stock/goods.md` |
| `get_warehouse_info` | `/skills/erp-stock/warehouse.md` |
| `get_inventory_data` | `/skills/erp-stock/inventory.md` |
| `get_inventory_audit_summary_data` | `/skills/erp-stock/inventory_audit.md` |
| `get_shop_available_info` | `/skills/erp-shop-retail/shop.md` |
| `get_shop_retail_info` | `/skills/erp-shop-retail/shop_retail.md` |
| `get_store_goods_retail_info` | `/skills/erp-shop-retail/goods_retail.md` |

查数、消歧、日期与范围规则仍以 `erp-stock` / `erp-shop-retail` 为准。本 skill 只管：何时导出、预检、文件名、调用导出工具、怎么回复。

## 何时导出

仅当用户明确说「导出」「下载」「把数据发给我」或同义说法时才导出。

- 用户没说：只按查询 skill 回答，不要主动导出，也不要主动提议导出。
- 本轮查过多种数据、用户说「把刚才的导出」：先把每种查询各压成**一行**描述列给用户选，选定后再走预检与导出。例如：`2026年7月直营门店销售汇总数据`。
- 还没查过、或条件还不完整：先按对应 ERP skill 定好筛选；条件够了再预检，通过后再导出。

## 流程

1. 定 `tool_name` 与业务筛选参数（与原工具一致）。需要时读上表对应说明（`limit=1000`）。
2. **预检**：直接调用该原工具，`current=1`，`size=5`，其它筛选与即将导出时相同。
3. 仅当同时满足才继续导出：
   - `status` 为 `success`
   - 存在非空 `data`
   - `page_info.total > 0`
4. 不满足：告诉用户当前条件没有可导出的数据，**不要**调用导出工具。
5. 通过预检后：先 `get_current_date` 取日期（用返回字符串开头的 `YYYY-MM-DD`），再调 `export_erp_data_to_excel`。

预检通过后不要先报条数；等导出成功再回复。用户同意「再试一次」时，也必须重新走预检，通过后再导出。

## 调用导出工具

`tool_args` 与原工具参数一致，并遵守：

- `current`：固定传 `1`（导出内部会从第一页拉全量；传其它页码也无效，但仍传 `1`，避免多余麻烦）。
- `size`：默认 `100`；用户要求更大时再加大，**最大 `1000`**。不要省略，须显式传入。
- 不要把查询 skill 里常用的展示用 `size=1` / `size=10` 原样带进导出。

其它参数：

- `tool_name`：上表七个之一，与原工具名完全一致。
- `file_name`：不含后缀。格式 `YYYY-MM-DD_中文名`。
  - 日期必须来自本次 `get_current_date`，不要沿用更早记忆。
  - 中文名自由起、尽量短，**不含日期部分最长 20 个字符**；特殊字符只允许 `_` 与 `-`。
- `file_type`：默认显式传 `xlsx`。仅用户点名要 CSV 时传 `csv`。

## 回答要求

- 成功：`status` 为 `success` 时，告诉用户导出成功，并写清**文件名**与**行数**（以返回 `message` 为准，形如「共 N 行」）。用户不问其它细节就不要多说。
- 返回的 `file_path` 形如 `/temp/xxx.xlsx`，**不在**工作区文件系统里；`read_file` / `ls` 会找不到。不要因此判定失败。
- 失败：`status` 为 `error` 时，用返回的 `message` 说明原因。消息是「未授权」时直接告知，不要改参数重试。
- 不要原样倒 JSON。
