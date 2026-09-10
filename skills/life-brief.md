# life-brief

人生简报：把公司和个人飞书的任务、日程合并成一份 Markdown 报告。

## 用法

```bash
# 今日简报（默认 company + life）
zero run life-brief

# 写入文件
zero run life-brief --out _brief/life-2026-09-10.md

# 7 天视图
zero run life-brief --days 7 --out _brief/life-week-2026-09-10.md

# 只看公司
zero run life-brief --profiles company --out _brief/life-company-2026-09-10.md

# 只看个人
zero run life-brief --profiles life --out _brief/life-life-2026-09-10.md

# 拉取全部任务页（默认只取 40 条）
zero run life-brief --page-all --out _brief/life-2026-09-10.md

# JSON 输出（给其他工具）
zero run life-brief --json

# 关闭实体标注（不读 life-entities.json）
zero run life-brief --no-entities
```

## 输出结构

```markdown
# 人生简报（2026-09-10，1 天）

## company（profile: company）
### 任务（未完成 N 项）
- 🔴 逾期 xxx (due: 2026-09-09T08:00:00+08:00)
- ⬜ 待办 yyy (due: 2026-09-10T18:00:00+08:00)

### 日程（N 项）
- 09:00 - 10:00 周会

## life（profile: life）
### 任务（未完成 N 项）
...

### 日程（N 项）
...
```

## 实体解析（别名消歧）

`life-brief` 会自动读取 `0_docs/life-entities.json`，在每条任务后面标注涉及的人/公司/项目，例如：

```markdown
- ⬜ 邮件回原线程附双章扫描件... 〈李慧婕·财务、云天·乙方〉 (due: 2026-09-16)
```

这用到了本体（ontology）思想：不同名字对应同一个对象。

维护 `life-entities.json`：

```json
{
  "entities": [
    {
      "id": "li-huijie",
      "type": "person",
      "canonical": "李慧婕",
      "aliases": ["财务", "财务老师"],
      "role": "财务",
      "org": "Optix"
    }
  ]
}
```

## 实现

- 调用 `lark-cli --profile company task +get-my-tasks --json`
- 调用 `lark-cli --profile life task +get-my-tasks --json`
- 调用 `lark-cli --profile company calendar +agenda --json`
- 调用 `lark-cli --profile life calendar +agenda --json`
- 合并后按逾期、待完成、日程分组输出
- 自动过滤 `due_at` 年份 < 2000 的无效日期
- 读取 `0_docs/life-entities.json` 进行实体标注

## 依赖

- `lark-cli` 已安装并登录
- `company` 和 `life` profile 有效

## 每日定时任务（可选）

安装每日 09:00 自动运行：

```powershell
# 需管理员权限
pwsh -File tools/0-cli/scripts/install-life-brief-task.ps1 -Time 09:00
```

删除任务：

```powershell
Unregister-ScheduledTask -TaskName "LifeBrief-Daily" -Confirm:$false
```
