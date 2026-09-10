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

# 百岁人生规划：仅用本地资料，不调用飞书
zero run life-brief --offline --days 7 --out _brief/life-100-plan-2026-09-10.md

# 离线结构化数据；明确标记 remote_status=not_fetched
zero run life-brief --offline --json --out _brief/life-local.json

# 紧凑模式：跳过百岁规划和来源，只看可执行部分
zero run life-brief --compact --out _brief/life-compact.md

# 只看某个生活领域（如 health / work / finance）
zero run life-brief --area health --out _brief/life-health.md

# 过滤事件时间范围
zero run life-brief --since 2026-09-01 --until 2026-09-10 --out _brief/life-range.md

# 周/月复盘模板：已完成、逾期、过程、健康、目标、复盘问题
zero run life-brief --review --days 7 --out _brief/life-review-2026-09-10.md
```

## 百岁人生规划与数据含义

读取工作区根 `life-management.json` 的 `century_plan`，展示百岁规划假设、候选生活章节、健康基线缺口、90 天候选行动和复盘问题。完整方案见工作区的 `notes/life-100-year-plan.md`。

- 100 岁是用户选择的规划假设，不是寿命预测；出生日期未知时不计算年龄或剩余时间。
- `proposed` / `draft` 目标与已采纳目标分开计数，生活设想不自动创建任务或预约。
- 健康数据只有带有效观察日期与来源、且不晚于简报日期，才计入“有记录”数量；这是资料完整度，不是健康评分，也不保证旧数据仍有效。
- `--offline` 不调用 `lark-cli`，不把未查询的远程任务/日程显示为 0；普通模式保持原有飞书采集路径。
- `--date` 用于任务逾期与过程日期比较；过期计划显示“待核实”，不自动标为已完成。`--days` 同时用于 Markdown 和在线 JSON 的日程范围。
- `--events` 可指定事件日志。离线 JSON 包含本地规划、实体、事件和未获取远程数据标记；在线 JSON 保持 profile 顶层结构。
- 数据格式错误会报告错误，不能将损坏的管理文件静默当作无数据。健康来源至少每年及状态明显变化时复核；这些规则本身不代表定时任务已启用。

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
