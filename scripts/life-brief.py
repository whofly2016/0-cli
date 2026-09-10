#!/usr/bin/env python3
"""
life-brief: unified daily/weekly brief from company and personal Feishu.

Merges lark-cli tasks + calendar agenda into a single Markdown report.
"""

import argparse
import difflib
import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

PROFILES = {
    "company": "company",
    "life": "life",
}

# Default location of the local entity registry (people / vendors / projects).
# Lives at the workspace root; never committed to a public repo.
WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ENTITIES_PATH = WORKSPACE_ROOT / "life-entities.json"
DEFAULT_EVENTS_PATH = WORKSPACE_ROOT / "life-events.jsonl"
DEFAULT_MANAGEMENT_PATH = WORKSPACE_ROOT / "life-management.json"


def _read_json(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def load_entities(path: Path | None):
    """Load entity registry → {alias: entity} lookup. Returns {} if absent."""
    data = _read_json(path or DEFAULT_ENTITIES_PATH)
    if data is None:
        return {}
    lookup = {}
    for ent in data.get("entities", []):
        for name in [ent.get("canonical", "")] + ent.get("aliases", []):
            if name:
                lookup[name] = ent
    return lookup


def load_entities_by_id(path: Path | None):
    """Load entity registry → {id: entity}. Returns {} if absent."""
    data = _read_json(path or DEFAULT_ENTITIES_PATH)
    if data is None:
        return {}
    return {ent.get("id"): ent for ent in data.get("entities", []) if ent.get("id")}


def load_events(path: Path | None):
    """Load JSONL event log. Returns []."""
    path = path or DEFAULT_EVENTS_PATH
    if not path.exists():
        return []
    events = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except Exception:
            continue
    return events


def load_management(path: Path | None):
    """Load the life-management control layer. Returns {} if absent."""
    path = path or DEFAULT_MANAGEMENT_PATH
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        raise ValueError(f"无法读取人生管理文件 {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"人生管理文件必须是 JSON 对象: {path}")
    return data


def _calendar_date(value):
    """Return an ISO date or None; never invent dates for unknown records."""
    if not isinstance(value, str):
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        return None


def _open_processes(entities):
    closed = {"done", "completed", "cancelled", "canceled", "archived"}
    return {
        pid: proc for pid, proc in entities.items()
        if proc.get("type") == "process" and proc.get("status") not in closed
    }


def century_section(management, report_date, days=1):
    """Render proposals and recorded evidence without predicting health or lifespan."""
    plan = management.get("century_plan") or {}
    if not plan:
        return []
    horizon = plan.get("planning_horizon") or {}
    target_age = horizon.get("age_years")
    lines = ["## 百岁人生规划", ""]
    if target_age is not None:
        lines.append(f"**规划上限**：{target_age} 岁（规划假设，不是寿命预测）。")
    birth = _calendar_date(plan.get("date_of_birth"))
    if birth and birth <= report_date:
        born = datetime.strptime(birth, "%Y-%m-%d")
        today = datetime.strptime(report_date, "%Y-%m-%d")
        age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
        lines.append(f"**当前年龄**：{age} 周岁（按已记录出生日期和简报日期计算）。")
        if isinstance(target_age, (int, float)) and age >= target_age:
            lines.append("已达到当前规划上限，可延长规划；这不表示生命到期。")
    else:
        lines.append("**当前年龄**：未知；出生日期未记录、无效或晚于简报日期，不计算剩余时间。")

    design = plan.get("life_design") or {}
    if design.get("ordinary_day"):
        lines.extend(["", f"**生活设想（候选）**：{design['ordinary_day']}"])
    scenarios = design.get("age_scenarios") or []
    if scenarios:
        lines.extend(["", "| 年龄参照 | 可调整的生活章节 |", "|---|---|"])
        for stage in scenarios:
            lines.append(f"| {stage.get('label', '')} | {stage.get('theme', '')}：{stage.get('scene', '')} |")
        lines.append("")
        lines.append("年龄仅作想象坐标，不是固定的婚育、退休或能力时间表。")

    health = plan.get("health_plan") or {}
    baseline = health.get("baseline") or []
    recorded = [
        item for item in baseline
        if item.get("value") is not None and item.get("source")
        and _calendar_date(item.get("observed_on"))
        and _calendar_date(item["observed_on"]) <= report_date
    ]
    lines.extend([
        "", "### 健康维护", "",
        f"**有日期与来源的基线记录**：{len(recorded)}/{len(baseline)} 项；这是信息完整度，不是健康评分，旧记录也不代表当前状态。",
    ])
    missing = [item.get("name", item.get("id", "未知项")) for item in baseline if item not in recorded]
    if missing:
        lines.append(f"**待补充资料**：{'、'.join(missing)}。")
    references = health.get("references") or []
    if references:
        lines.extend(["", "以下是一般参考，尚未按你的年龄、疾病或运动限制个体化：", ""])
        for reference in references:
            refs = " ".join(f"[{sid}]" for sid in reference.get("source_ids", []))
            lines.append(f"- {reference.get('text', '')} {refs}")

    candidates = [g for g in management.get("goals", []) if g.get("status") in {"proposed", "draft"}]
    if candidates:
        lines.extend(["", "### 90 天候选行动（未自动成为承诺）", ""])
        for goal in candidates:
            lines.append(f"- **{goal.get('title', goal.get('id', '候选目标'))}**：{goal.get('next_action', '待定义')}")
        lines.append("")
        lines.append("90 天从实际开始试行时起算；此处没有创建外部任务或预约。")

    questions = plan.get("review_questions") or []
    if questions:
        lines.extend(["", "### 生活复盘", ""])
        lines.extend(f"- {q}" for q in (questions if days >= 7 else questions[:2]))
    lines.append("")
    return lines


def century_sources(management):
    sources = (management.get("century_plan") or {}).get("sources") or []
    if not sources:
        return []
    checked_on = ((management.get("century_plan") or {}).get("health_plan") or {}).get("sources_checked_on")
    lines = ["## 健康参考来源", "", f"一般指南不代表个人寿命预测；最近核对：{checked_on or '未知'}。", ""]
    for source in sources:
        lines.append(f"[{source['id']}]: {source['url']} \"{source.get('publisher', '')} — {source.get('title', '')}\"")
    lines.append("")
    return lines


def annotate(text: str, entity_lookup: dict) -> str:
    """Append resolved entity tags like 〈李慧婕·财务, 云天·乙方〉."""
    if not entity_lookup or not text:
        return text
    found = []
    seen_ids = set()
    # Match longer aliases first so "云天科技" wins over "云天"
    for alias in sorted(entity_lookup.keys(), key=len, reverse=True):
        if alias and alias in text:
            ent = entity_lookup[alias]
            if ent.get("id") in seen_ids:
                continue
            seen_ids.add(ent.get("id"))
            role = ent.get("role") or ent.get("type") or ""
            found.append(f"{ent.get('canonical')}·{role}" if role else ent.get("canonical"))
    if found:
        return f"{text} 〈{'、'.join(found)}〉"
    return text


def run_lark(args, profile):
    """Run lark-cli with a profile and return JSON data."""
    cmd = f"lark-cli --profile {profile} {' '.join(args)} --json"
    result = subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8", shell=True
    )
    if result.returncode != 0:
        return {"error": result.stderr}
    try:
        # lark-cli 1.0.65 may emit raw control chars inside JSON strings.
        return json.loads(result.stdout, strict=False)
    except json.JSONDecodeError:
        return {"error": "invalid json output"}


def collect_tasks(profile, page_all=False):
    args = ["task", "+get-my-tasks"]
    if page_all:
        args.append("--page-all")
    else:
        args.extend(["--page-limit", "40"])
    data = run_lark(args, profile)
    if "error" in data:
        return {"error": data["error"], "items": []}
    items = data.get("data", {}).get("items", [])
    return {"items": items}


def collect_agenda(profile, start, end):
    args = ["calendar", "+agenda", "--start", start, "--end", end]
    data = run_lark(args, profile)
    if "error" in data:
        return {"error": data["error"], "items": []}
    return {"items": data.get("data", [])}


def _is_valid_due(due: str) -> bool:
    if not due:
        return False
    try:
        year = int(due[:4])
    except Exception:
        return False
    return year >= 2000


def _due_date(due: str) -> str:
    return due.split("T")[0] if _is_valid_due(due) else ""


def fmt_task(t, entity_lookup=None, report_date=None):
    report_date = report_date or datetime.now().strftime("%Y-%m-%d")
    summary = t.get("summary", "(no summary)")
    summary = annotate(summary, entity_lookup or {})
    due = t.get("due_at", "")
    completed = t.get("completed", False)
    status = "✅" if completed else "⬜"
    if not completed and _is_valid_due(due):
        due_date = _due_date(due)
        if due_date < report_date:
            status = "🔴"
    due_display = _due_date(due) if _is_valid_due(due) else "(无截止日期)"
    return f"- {status} {summary} (due: {due_display})"


def fmt_event(e):
    start = e.get("start_time", "")
    end = e.get("end_time", "")
    summary = e.get("summary", "(no title)")
    if start:
        try:
            st = datetime.fromisoformat(start.replace("Z", "+00:00"))
            start = st.strftime("%H:%M")
        except Exception:
            pass
    if end:
        try:
            et = datetime.fromisoformat(end.replace("Z", "+00:00"))
            end = et.strftime("%H:%M")
        except Exception:
            pass
    return f"- {start} - {end} {summary}"


def process_section(entities, events, report_date=None, management=None, area=None):
    """Render 'in-progress processes' from entity registry + event log."""
    report_date = report_date or datetime.now().strftime("%Y-%m-%d")
    processes = _open_processes(entities)
    if not processes:
        return []
    if area and management:
        portfolio = management.get("portfolio", [])
        allowed = {x.get("process") for x in portfolio if x.get("area") == area}
        processes = {pid: p for pid, p in processes.items() if pid in allowed}
        if not processes:
            return []
    lines = ["## 已登记且未关闭的过程", ""]
    for pid, proc in sorted(
        processes.items(), key=lambda x: x[1].get("canonical", "")
    ):
        stage = proc.get("current_stage") or "未知"
        goal = proc.get("goal") or ""
        lines.append(f"### {proc.get('canonical', '未命名')}（当前：{stage}）")
        if goal:
            lines.append(f"**目标**：{goal}")
        next_events = [
            e for e in events if e.get("object") == pid and e.get("state") == "planned"
        ]
        next_events.sort(key=lambda x: str(x.get("when", "")))
        if next_events:
            nxt = next_events[0]
            where = nxt.get("where", "")
            when = nxt.get("when", "")
            detail = nxt.get("brief") or nxt.get("detail", "")
            label = "计划已过期，待核实" if str(when)[:10] < report_date else "下一计划事件"
            lines.append(f"**{label}**：{when} @{where} → {nxt.get('action')}：{detail}")
        else:
            lines.append("**下一步**：未记录计划事件（不表示没有行动）。")
        lines.append("")
    return lines


def management_section(management, entities, events, report_date=None, area=None):
    """Render a compact portfolio/control view above raw task lists."""
    if not management:
        return []
    report_date = report_date or datetime.now().strftime("%Y-%m-%d")

    areas = {a.get("id"): a for a in management.get("areas", []) if a.get("id")}
    portfolio = management.get("portfolio", [])
    goals = management.get("goals", [])
    north_star = management.get("north_star", {})
    lines = ["## 人生管理视图", ""]

    if north_star.get("statement"):
        label = "长期方向（候选）" if north_star.get("status") in {"proposed", "draft"} else "长期方向"
        lines.append(f"**{label}**：{north_star['statement']}")
    else:
        lines.append("**长期方向**：待定义")
    adopted = sum(g.get("status") in {"active", "adopted", "in_progress"} for g in goals)
    proposed = sum(g.get("status") in {"proposed", "draft"} for g in goals)
    lines.append(f"**已采纳且未完成目标**：{adopted} 个；**候选目标**：{proposed} 个。")
    lines.append("")

    active_by_area = {}
    unmapped = []
    for pid, proc in _open_processes(entities).items():
        mapping = next((x for x in portfolio if x.get("process") == pid), None)
        if not mapping:
            unmapped.append(proc.get("canonical", pid))
            continue
        if area and mapping.get("area") != area:
            continue
        active_by_area.setdefault(mapping.get("area"), []).append(proc)

    for area_id, procs in active_by_area.items():
        area_obj = areas.get(area_id, {"name": area_id})
        stale = 0
        no_next = 0
        for proc in procs:
            pid = proc.get("id")
            planned = [e for e in events if e.get("object") == pid and e.get("state") == "planned"]
            if not planned:
                no_next += 1
            lifespan = proc.get("lifespan") or {}
            if lifespan.get("to") and lifespan.get("to") < report_date:
                stale += 1
        flags = []
        if no_next:
            flags.append(f"{no_next} 个未记录计划事件")
        if stale:
            flags.append(f"{stale} 个结束日期已过，状态待核实")
        suffix = f"；⚠️ {'，'.join(flags)}" if flags else ""
        names = "、".join(p.get("canonical", p.get("id", "")) for p in procs)
        lines.append(f"- **{area_obj.get('name', area_id)}**：{len(procs)} 个已登记过程（{names}）{suffix}")

    unassessed = [a.get("name") for a in areas.values() if a.get("status") == "unassessed"]
    if unassessed:
        lines.append(f"- **尚未建立基线的领域**：{'、'.join(unassessed)}")
    if unmapped and not area:
        lines.append(f"- **未归属领域的过程**：{'、'.join(unmapped)}")
    lines.append("")
    return lines


def generate_review(
    date, days, profiles, page_all=False, entity_lookup=None, entities=None, events=None,
    management=None, offline=False, area=None
):
    """Generate a weekly/monthly review template."""
    entities = entities or {}
    events = events or []
    management = management or {}
    lines = [f"# 人生复盘（{date}，{days} 天）", ""]

    # Completed items from events
    completed_events = [e for e in events if e.get("state") == "completed"]
    if completed_events:
        lines.extend(["## 已完成事项", ""])
        for e in completed_events[:20]:
            when = e.get("when", "")
            action = e.get("action", "")
            obj = e.get("object", "")
            detail = e.get("brief") or e.get("detail", "")
            lines.append(f"- {when} {action} {obj}：{detail}")
        lines.append("")

    # Overdue tasks
    if not offline:
        lines.extend(["## 逾期任务", ""])
        for name, profile in profiles.items():
            tasks_result = collect_tasks(profile, page_all)
            if "error" not in tasks_result:
                tasks = tasks_result["items"]
                overdue = [
                    t for t in tasks
                    if not t.get("completed")
                    and _is_valid_due(t.get("due_at", ""))
                    and _due_date(t["due_at"]) < date
                ]
                for t in overdue[:10]:
                    lines.append(f"- 🔴 {t.get('summary')} (due: {_due_date(t.get('due_at', ''))}) [{name}]")
        lines.append("")

    # Process status
    processes = _open_processes(entities)
    if processes:
        lines.extend(["## 进行中过程", ""])
        for pid, proc in sorted(processes.items(), key=lambda x: x[1].get("canonical", "")):
            stage = proc.get("current_stage") or "未知"
            goal = proc.get("goal") or ""
            lines.append(f"### {proc.get('canonical', '未命名')}（当前：{stage}）")
            if goal:
                lines.append(f"**目标**：{goal}")
            next_events = [e for e in events if e.get("object") == pid and e.get("state") == "planned"]
            next_events.sort(key=lambda x: str(x.get("when", "")))
            if next_events:
                nxt = next_events[0]
                lines.append(f"**下一步**：{nxt.get('when')} @{nxt.get('where', '')} → {nxt.get('action')}")
            else:
                lines.append("**下一步**：未记录计划事件")
            lines.append("")

    # Health baseline
    health = (management.get("century_plan") or {}).get("health_plan") or {}
    baseline = health.get("baseline") or []
    if baseline:
        lines.extend(["## 健康基线", ""])
        recorded = [
            item for item in baseline
            if item.get("value") is not None and item.get("source")
            and _calendar_date(item.get("observed_on"))
            and _calendar_date(item["observed_on"]) <= date
        ]
        lines.append(f"**有记录**：{len(recorded)}/{len(baseline)} 项")
        missing = [item.get("name", item.get("id", "未知项")) for item in baseline if item not in recorded]
        if missing:
            lines.append(f"**待补充**：{'、'.join(missing)}")
        lines.append("")

    # Goals
    goals = management.get("goals", [])
    if goals:
        lines.extend(["## 目标进展", ""])
        for goal in goals:
            status = goal.get("status", "unknown")
            title = goal.get("title", goal.get("id", "未命名"))
            next_action = goal.get("next_action", "")
            lines.append(f"- **{title}** [{status}]：{next_action}")
        lines.append("")

    # Review questions
    questions = (management.get("century_plan") or {}).get("review_questions") or []
    if not questions:
        questions = [
            "本周/月最重要的进展是什么？",
            "哪些过程需要调整优先级？",
            "健康基线有哪些需要补充或更新？",
            "下周/月最想完成的一件事是什么？",
        ]
    lines.extend(["## 复盘问题", ""])
    lines.extend(f"- {q}" for q in questions)
    lines.append("")

    return "\n".join(lines)


def generate_report(
    date, days, profiles, page_all=False, entity_lookup=None, entities=None, events=None,
    management=None, offline=False, compact=False, area=None
):
    entities = entities or {}
    events = events or []
    management = management or {}
    lines = [f"# 人生简报（{date}，{days} 天）", ""]
    if offline:
        lines.extend(["离线模式：只读取本地规划、实体与事件；未获取飞书任务或日程。", ""])
    if not compact:
        lines.extend(century_section(management, date, days))

    mgmt_lines = management_section(management, entities, events, date, area=area)
    if mgmt_lines:
        lines.extend(mgmt_lines)

    # Spacetime process view: ordered processes and next events.
    proc_lines = process_section(entities, events, date, management=management, area=area)
    if proc_lines:
        lines.extend(proc_lines)

    for name, profile in ({} if offline else profiles).items():
        lines.append(f"## {name}（profile: {profile}）")

        tasks_result = collect_tasks(profile, page_all)
        if "error" in tasks_result:
            lines.append(f"### 任务\n- ⚠️ 获取失败: {tasks_result['error'][:200]}")
        else:
            tasks = tasks_result["items"]
            active = [t for t in tasks if not t.get("completed")]
            overdue = [
                t
                for t in active
                if _is_valid_due(t.get("due_at", ""))
                and _due_date(t["due_at"]) < date
            ]
            upcoming = [
                t
                for t in active
                if _is_valid_due(t.get("due_at", ""))
                and _due_date(t["due_at"]) >= date
            ]
            no_due = [t for t in active if not _is_valid_due(t.get("due_at", ""))]

            lines.append(f"### 任务（未完成 {len(active)} 项）")
            for t in overdue[:10]:
                lines.append(fmt_task(t, entity_lookup, date))
            for t in upcoming[:10]:
                lines.append(fmt_task(t, entity_lookup, date))
            for t in no_due[:5]:
                lines.append(fmt_task(t, entity_lookup, date))

        start = f"{date}T00:00:00+08:00"
        end_date = (datetime.strptime(date, "%Y-%m-%d") + timedelta(days=days)).strftime(
            "%Y-%m-%d"
        )
        end = f"{end_date}T00:00:00+08:00"
        agenda_result = collect_agenda(profile, start, end)
        if "error" in agenda_result:
            lines.append(f"### 日程\n- ⚠️ 获取失败: {agenda_result['error'][:200]}")
        else:
            events = agenda_result["items"]
            lines.append(f"### 日程（{len(events)} 项）")
            for e in events[:10]:
                lines.append(fmt_event(e))
        lines.append("")
    if not compact:
        lines.extend(century_sources(management))
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate a unified life/work brief")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--days", type=int, default=1, help="Days to cover")
    parser.add_argument("--profiles", default="company,life")
    parser.add_argument("--out", type=Path, help="Output file (default: stdout)")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--page-all", action="store_true", help="Fetch all task pages")
    parser.add_argument("--offline", action="store_true", help="Use local planning data only; do not call Lark")
    parser.add_argument("--compact", action="store_true", help="Skip century plan and sources; show only actionable sections")
    parser.add_argument("--review", action="store_true", help="Generate weekly/monthly review template")
    parser.add_argument("--diff", type=Path, help="Compare generated report with a previous brief file")
    parser.add_argument("--area", help="Filter management/process sections by life area id")
    parser.add_argument("--since", help="Only include events on/after this date (YYYY-MM-DD)")
    parser.add_argument("--until", help="Only include events on/before this date (YYYY-MM-DD)")
    parser.add_argument("--events", type=Path, default=DEFAULT_EVENTS_PATH, help="Local event log JSONL")
    parser.add_argument(
        "--entities",
        type=Path,
        default=DEFAULT_ENTITIES_PATH,
        help="Entity/alias registry JSON",
    )
    parser.add_argument(
        "--no-entities", action="store_true", help="Disable entity annotation"
    )
    parser.add_argument(
        "--management",
        type=Path,
        default=DEFAULT_MANAGEMENT_PATH,
        help="Life-management control layer JSON",
    )
    args = parser.parse_args()
    if not _calendar_date(args.date):
        parser.error("--date 必须是有效的 YYYY-MM-DD 日期")
    if args.days < 1:
        parser.error("--days 必须大于 0")
    if args.since and not _calendar_date(args.since):
        parser.error("--since 必须是有效的 YYYY-MM-DD 日期")
    if args.until and not _calendar_date(args.until):
        parser.error("--until 必须是有效的 YYYY-MM-DD 日期")

    profiles = {name.strip(): PROFILES.get(name.strip(), name.strip()) for name in args.profiles.split(",") if name.strip()}
    entity_lookup = {} if args.no_entities else load_entities(args.entities)
    entities = {} if args.no_entities else load_entities_by_id(args.entities)
    events = load_events(args.events)
    if args.since:
        events = [e for e in events if str(e.get("when", ""))[:10] >= args.since]
    if args.until:
        events = [e for e in events if str(e.get("when", ""))[:10] <= args.until]
    try:
        management = load_management(args.management)
    except ValueError as exc:
        parser.error(str(exc))

    if args.json:
        if args.offline:
            result = {
                "date": args.date, "days": args.days, "offline": True,
                "management": management, "entities": entities, "events": events,
                "remote_status": "not_fetched",
            }
        else:
            end_date = (datetime.strptime(args.date, "%Y-%m-%d") + timedelta(days=args.days)).strftime("%Y-%m-%d")
            result = {}
            for name, profile in profiles.items():
                result[name] = {
                    "tasks": collect_tasks(profile, args.page_all),
                    "agenda": collect_agenda(profile, f"{args.date}T00:00:00+08:00", f"{end_date}T00:00:00+08:00"),
                }
        report = json.dumps(result, ensure_ascii=False, indent=2)
    else:
        if args.review:
            report = generate_review(
                args.date, args.days, profiles, args.page_all, entity_lookup,
                entities, events, management, offline=args.offline, area=args.area,
            )
        else:
            report = generate_report(
                args.date, args.days, profiles, args.page_all, entity_lookup,
                entities, events, management, offline=args.offline,
                compact=args.compact, area=args.area,
            )
    if args.diff:
        if not args.diff.exists():
            parser.error(f"--diff 文件不存在: {args.diff}")
        previous = args.diff.read_text(encoding="utf-8")
        diff = difflib.unified_diff(
            previous.splitlines(keepends=True),
            report.splitlines(keepends=True),
            fromfile=str(args.diff),
            tofile="current",
        )
        report = "".join(diff)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(report, encoding="utf-8")
        print(f"written: {args.out}")
    else:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        print(report)


if __name__ == "__main__":
    main()
