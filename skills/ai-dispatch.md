# ai-dispatch

扫描各项目 `_inbox/` 当日任务卡，派发到 codex exec 无人值守执行。

## 命令

```bash
# 默认：今天、所有默认项目、20 分钟超时
zero run ai-dispatch

# 指定日期和项目
zero run ai-dispatch -Date 2026-06-12 -Projects 1_optix,infosec -TimeoutMin 30
```

## 参数

- `-Date <yyyy-MM-dd>`：任务卡日期，默认今天
- `-Projects <string[]>`：扫描项目，默认 `1_optix,patents,infosec,tools`
- `-Sandbox <string>`：codex sandbox，默认 `workspace-write`
- `-TimeoutMin <int>`：单卡超时分钟，默认 20

## 产物

- `_brief/runs/<Date>/dispatch-summary.txt`
- 各卡日志 `_brief/runs/<Date>/<project>--<slug>.log`

## 注意

- 卡片含 `## Result` 段即视为已完成，跳过
- 超时后会 kill 进程并记录 TIMEOUT
