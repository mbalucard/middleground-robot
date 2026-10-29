# TOOLS.md - Your Tools

这里是你记录工具使用经验的地方。
当你使用工具犯错的时候，请记录下来，这样未来的你就不会重蹈覆辙。这是你精心整理，提炼过的工具使用记录。

## export_erp_data_to_excel

- 参数：`tool_name`（要调用的 ERP 工具名）、`tool_args`（该工具的参数）、`file_name`（不带后缀，工具会自己补）、`file_type`（`csv` / `xlsx`）。
- 返回的 `file_path` 形如 `/temp/xxx.csv`，这个路径**不在我的文件系统里**，`read_file`/`ls` 会报 not found。不要因此判定导出失败；以返回的 `status=success` 和 `message` 为准，把文件名和路径直接给用户。
- 导出前把 `size` 调到足够大（如 50/200），避免只导出第一页；因为分页默认 10 条。
