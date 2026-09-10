# ai-infosec-status

拉取信息安全多维表格关键子表现状。

## 命令

```bash
zero run ai-infosec-status
```

## 产物

- `_brief/infosec-status-YYYY-MM-DD.md`
- 包含问题收集表、实现与整改记录表、验收记录与结果表、终端部署追踪

## 依赖

- PowerShell 7 (`pwsh`)
- `lark-cli` 已登录
- infosec Base Token 已在 `tools/ai-workflow/config.ps1` 配置
