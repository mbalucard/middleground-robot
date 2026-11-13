---
name: erp-export
description: 将 ERP 查询结果导出为表格文件；同一工具多套条件可合并为一份。用户明确说导出、下载、把数据发给我时使用。只导出本 skill 列出的 7 个分页 ERP 工具数据；库存、零售、门店等查询条件仍按对应 ERP skill。用户没说导出时不要主动导出。
allowed-tools: export_erp_data_to_excel merge_tables_files get_current_date get_goods_info get_warehouse_info get_inventory_data get_inventory_audit_summary_data get_shop_available_info get_shop_retail_info get_store_goods_retail_info
---

# ERP 数据导出

用 `export_erp_data_to_excel` 把某个 ERP 分页工具的全量结果落到表格；同一 `tool_name` 下多套筛选默认再经 `merge_tables_files` 合成一份。只处理用户主动要导出的场景。不要凭记忆编造行数或文件路径。

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

查数、消歧、日期与范围规则仍以 `erp-stock` / `erp-shop-retail` 为准。本 skill 只管：何时导出、预检、是否合并、文件名、调用导出/合并工具、怎么回复。

## 何时导出

仅当用户明确说「导出」「下载」「把数据发给我」或同义说法时才导出。

- 用户没说：只按查询 skill 回答，不要主动导出，也不要主动提议导出。
- 本轮查过多种数据、用户说「把刚才的导出」：先把每种查询各压成**一行**描述列给用户选。用户选定或说「都要」后：
  - 选中项里**同一** `tool_name` 且满足合并条件 → **默认合并**成一份（见下）。
  - 不同 `tool_name` → 各自单独导出，**禁止**互相合并。
- 还没查过、或条件还不完整：先按对应 ERP skill 定好筛选；条件够了再预检，通过后再导出。

## 单次导出流程

一套筛选条件时按本流程；多套时对**每一套**先走预检，再按「多表合并」决定是否合并。

1. 定 `tool_name` 与业务筛选参数（与原工具一致）。需要时读上表对应说明（`limit=1000`）。
2. **预检**：直接调用该原工具，`current=1`，`size=5`，其它筛选与即将导出时相同。
3. 仅当同时满足才继续导出：
   - `status` 为 `success`
   - 存在非空 `data`
   - `page_info.total ≥ 1`（即 `total > 0`）
4. 不满足：告诉用户当前条件没有可导出的数据，**不要**调用导出工具。
5. 通过预检后：先 `get_current_date` 取日期（用返回字符串开头的 `YYYY-MM-DD`），再调 `export_erp_data_to_excel`。

预检通过后不要先报条数；等导出（及如需合并）成功再回复。用户同意「再试一次」时，也必须重新走预检，通过后再导出。

## 多表合并

下列任一情况，在**同一** `tool_name` 下对多套筛选走合并（用户明确说「分开导出 / 不要合并 / 各一份」则**不合并**，每套单独导出并分别回复）：

- 一次要导出多套筛选，且都是同一工具（默认合并）
- 用户说「合并」「合成一张表」「只要一个文件」等
- 「把刚才的导出」且用户要的多条属于同一 `tool_name`（默认合并）

**禁止**：不同 `tool_name` 之间调用 `merge_tables_files`（列结构不同）。

### 合并门槛（须同时满足）

对拟合并的各套条件：

1. **同一** `tool_name`。
2. 预检通过，且 `page_info.total ≥ 1`。
3. **列名集合完全一致**：用各套预检 `data` 中记录的字段名（key）做集合比较，必须相等；顺序无关。以第一套通过预检的列名为基准，与其余套比对。
4. 最终进入合并池的文件 **≥ 2** 才调用 `merge_tables_files`。不足 2 个：不调用合并，能导出的按普通单次导出，文件名**不加** `_合并`。

### 部分不合规时（按套处理，其余照常）

- 预检无数据：跳过该套，简短告知，**不**导出该套。
- 列名与基准不一致：该套**单独导出**（不进合并池），简短告知原因；列名一致且 `total ≥ 1` 的其余套照常合并（若合并池仍 ≥ 2）。
- 合并池最终只有 1 个文件：不合并，该文件当普通导出；若另有「列名不一致」已单独导出的，一并按分表结果回复。

### 合并步骤

1. 对各套分别预检；记录每套的列名集合与是否通过。
2. 通过且列名一致的进入合并池；列名不一致的标记为「单独导出」。
3. 对合并池与「单独导出」各套：通过预检后调用 `export_erp_data_to_excel`（中间表文件名规则同下，**不加** `_合并`）。内部记下返回的 `file_path`，**不要**把路径告诉用户。
4. 合并池 `file_path` ≥ 2 时：调用 `merge_tables_files`。
5. 合并失败（`status` 为 `error`）：用返回 `message` 告知用户（去掉路径）；已单独导出的分表仍可按成功结果简短说明。

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
  - 多套中间表：中文名应能区分条件（如门店/月份），仍遵守 20 字与字符规则。
- `file_type`：默认显式传 `xlsx`。仅用户点名要 CSV 时传 `csv`。合并时 `output_file_type` 与各中间表 `file_type` 保持一致。

## 调用合并工具

- `file_paths`：合并池内各次导出返回的 `file_path` 列表（仅内部使用）。
- `output_file_name`：不含后缀。格式 `YYYY-MM-DD_中文名_合并`。
  - 日期与中文名规则同导出；后缀 `_合并` **不计入** 中文名 20 字限制。
- `output_file_type`：与中间表一致；默认 `xlsx`。
- `is_distinguish_file_name`：默认显式传 `true`（合并结果多一列 `file_name` 标明来源文件）。仅当用户明确说不需要区分来源 / 不要来源列时传 `false`。

## 回答要求

- 单次导出成功：告诉用户导出成功，并写清**文件名**与**行数**（以返回 `message` 为准，形如「共 N 行」）。
- 合并成功：主要报**合并后**的文件名与行数（以合并工具 `message` 为准）；若有跳过或单独导出的，同一回复里**简短**说明即可。用户不问其它细节就不要多说。
- **不要**告诉用户存放路径或 `file_path`，不论用户怎么问，都不要告诉他（文件在服务器上，路径会暴露服务器目录）。只报文件名即可，例如 `2026-10-30_门店零售.xlsx` 或 `2026-10-30_门店零售_合并.xlsx`。
- 返回的 `file_path` **不在**工作区文件系统里；`read_file` / `ls` 会找不到。不要因此判定失败，也不要把该路径写进回复。合并时仅把 `file_path` 传给 `merge_tables_files`。
- 失败：`status` 为 `error` 时，用返回的 `message` 说明原因；若 message 里带路径，回复时去掉路径只留原因。消息是「未授权」时直接告知，不要改参数重试。
- 不要原样倒 JSON。
