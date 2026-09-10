from __future__ import annotations

import shlex
import subprocess
import sys

from . import registry

WORKSPACE_ROOT = registry.WORKSPACE_ROOT


def run(name: str, args: list[str], dry_run: bool = False) -> int:
    entry = registry.find(name)
    if not entry:
        print(f"unknown tool: {name}", file=sys.stderr)
        return 1

    status = entry.get("status", "")
    if status in ("documented", "docs-only"):
        print(f"{name} is documented only; not a runnable CLI", file=sys.stderr)
        return 1

    template = entry.get("invoke_template", "")
    if not template:
        print(f"{name}: missing invoke_template", file=sys.stderr)
        return 1

    args_str = " ".join(shlex.quote(a) for a in args)
    if "{args}" in template:
        cmd = template.replace("{args}", args_str)
    else:
        cmd = f"{template} {args_str}" if args else template

    print(f"[zero] {cmd}")
    if dry_run:
        print("[zero] dry-run: not executing")
        return 0
    return subprocess.run(cmd, shell=True, cwd=WORKSPACE_ROOT).returncode
