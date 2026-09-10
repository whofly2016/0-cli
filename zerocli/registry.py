from __future__ import annotations

import json
from pathlib import Path
from typing import Any

HUB_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = HUB_ROOT.parent.parent
REGISTRY_PATH = HUB_ROOT / "local_registry.json"

REQUIRED_FIELDS = ("name", "display_name", "version", "category", "skill_md")


def load() -> dict[str, Any]:
    if not REGISTRY_PATH.exists():
        return {"meta": {}, "entries": []}
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def entries() -> list[dict[str, Any]]:
    return load().get("entries", [])


def find(name: str) -> dict[str, Any] | None:
    for e in entries():
        if e.get("name") == name:
            return e
    return None


def skill_path(entry: dict[str, Any]) -> Path | None:
    path = entry.get("skill_md")
    if not path:
        return None
    return WORKSPACE_ROOT / path


def skill_md_path(entry: dict) -> Path | None:
    """Resolve the skill markdown path for an entry."""
    skill_md = entry.get("skill_md")
    if not skill_md:
        return None
    path = WORKSPACE_ROOT / skill_md
    return path if path.exists() else None


def scan() -> list[dict]:
    """Scan workspace for cli-anything-registry.json files."""
    found = []
    for path in WORKSPACE_ROOT.rglob("cli-anything-registry.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            data["_path"] = str(path.relative_to(WORKSPACE_ROOT))
            found.append(data)
        except Exception:
            continue
    return found


def validate() -> list[str]:
    issues = []
    data = load()
    if not isinstance(data, dict):
        issues.append("registry must be a JSON object")
        return issues
    if "entries" not in data:
        issues.append("registry missing 'entries'")
    if not isinstance(data.get("entries"), list):
        issues.append("'entries' must be a list")
        return issues

    seen = set()
    for i, e in enumerate(data["entries"]):
        if not isinstance(e, dict):
            issues.append(f"entry #{i} is not an object")
            continue
        name = e.get("name")
        if not name:
            issues.append(f"entry #{i} missing 'name'")
            continue
        if name in seen:
            issues.append(f"duplicate entry: {name}")
        seen.add(name)

        for field in REQUIRED_FIELDS:
            if field not in e:
                issues.append(f"{name}: missing '{field}'")

        if e.get("status") != "documented" and not e.get("invoke_template"):
            issues.append(f"{name}: non-documented entries require 'invoke_template'")

        skill = skill_path(e)
        if skill and not skill.exists():
            issues.append(f"{name}: skill_md not found: {skill}")

    return issues
