#!/usr/bin/env python3
"""
life-brief: unified daily/weekly brief from company and personal Feishu.

Merges lark-cli tasks + calendar agenda into a single Markdown report.
"""

import argparse
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


def load_entities(path: Path | None):
    """Load entity registry → {alias: entity} lookup. Returns {} if absent."""
    if path is None:
        path = DEFAULT_ENTITIES_PATH
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    lookup = {}
    for ent in data.get("entities", []):
        for name in [ent.get("canonical", "")] + ent.get("aliases", []):
            if name:
                lookup[name] = ent
    return lookup


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


def fmt_task(t, entity_lookup=None):
    summary = t.get("summary", "(no summary)")
    summary = annotate(summary, entity_lookup or {})
    due = t.get("due_at", "")
    completed = t.get("completed", False)
    status = "✅" if completed else "⬜"
    if not completed and _is_valid_due(due):
        due_date = _due_date(due)
        if due_date < datetime.now().strftime("%Y-%m-%d"):
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


def generate_report(date, days, profiles, page_all=False, entity_lookup=None):
    lines = [f"# 人生简报（{date}，{days} 天）", ""]
    for name, profile in profiles.items():
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
                lines.append(fmt_task(t, entity_lookup))
            for t in upcoming[:10]:
                lines.append(fmt_task(t, entity_lookup))
            for t in no_due[:5]:
                lines.append(fmt_task(t, entity_lookup))

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
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate a unified life/work brief")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--days", type=int, default=1, help="Days to cover")
    parser.add_argument("--profiles", default="company,life")
    parser.add_argument("--out", type=Path, help="Output file (default: stdout)")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--page-all", action="store_true", help="Fetch all task pages")
    parser.add_argument(
        "--entities",
        type=Path,
        default=DEFAULT_ENTITIES_PATH,
        help="Entity/alias registry JSON",
    )
    parser.add_argument(
        "--no-entities", action="store_true", help="Disable entity annotation"
    )
    args = parser.parse_args()

    profiles = {name: PROFILES.get(name, name) for name in args.profiles.split(",")}
    entity_lookup = {} if args.no_entities else load_entities(args.entities)

    if args.json:
        result = {}
        for name, profile in profiles.items():
            result[name] = {
                "tasks": collect_tasks(profile, args.page_all),
                "agenda": collect_agenda(
                    profile,
                    f"{args.date}T00:00:00+08:00",
                    f"{args.date}T23:59:59+08:00",
                ),
            }
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    report = generate_report(args.date, args.days, profiles, args.page_all, entity_lookup)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(report, encoding="utf-8")
        print(f"written: {args.out}")
    else:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        print(report)


if __name__ == "__main__":
    main()
