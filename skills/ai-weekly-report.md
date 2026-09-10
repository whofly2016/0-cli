# ai-weekly-report

生成周报数据底稿。

## 命令

```bash
zero run ai-weekly-report
```

## 产物

- `_brief/weekly-YYYY-MM-DD.md`
- 包含 VRSK 全量任务、战略专项、战略举措、年度执行、实现与整改记录表

## 依赖

- PowerShell 7 (`pwsh`)
- `lark-cli` 已登录
- `tools/ai-workflow/config.ps1` 中的配置

## 注意

- 数据底稿由 AI 按 CAO 视角加工
- 加工后上传飞书云文档并由 hermes 播报
