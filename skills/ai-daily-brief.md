# ai-daily-brief

生成每日晨报数据底稿。

## 命令

```bash
zero run ai-daily-brief
```

## 产物

- `_brief/daily-YYYY-MM-DD.md`
- 包含 VRSK sections、VRSK 任务、infosec 战略举措、infosec 问题收集表

## 依赖

- PowerShell 7 (`pwsh`)
- `lark-cli` 已登录
- `tools/ai-workflow/config.ps1` 中的配置

## 注意

- 脚本只产出数据底稿
- 分析、优先级排序、报告成文由 AI 二次加工
- 对人沟通统一交飞书侧 hermes Agent
