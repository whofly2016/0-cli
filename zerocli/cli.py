from __future__ import annotations

import json
import sys
import subprocess

import click

from . import __version__, registry, runner


@click.group()
@click.version_option(version=__version__, prog_name="zero")
def cli():
    """Local CLI-Anything hub for the 0_docs workspace."""


@cli.command("list")
@click.option("--category", help="Filter by category")
@click.option("--status", help="Filter by status")
@click.option("--json", "json_flag", is_flag=True, help="Output JSON")
def list_cmd(category: str | None, status: str | None, json_flag: bool):
    """List registered local CLIs."""
    entries = registry.entries()
    if category:
        cat = category.lower()
        entries = [e for e in entries if e.get("category", "").lower() == cat]
    if status:
        st = status.lower()
        entries = [e for e in entries if e.get("status", "").lower() == st]
    if json_flag:
        click.echo(json.dumps(entries, ensure_ascii=False, indent=2))
        return
    for e in entries:
        click.echo(
            f"{e['name']:20} "
            f"{e.get('display_name', ''):25} "
            f"[{e.get('category', '')}] "
            f"{e.get('status', '')}"
        )


@cli.command()
@click.argument("keyword")
@click.option("--category", help="Filter by category")
@click.option("--status", help="Filter by status")
@click.option("--skill", is_flag=True, help="Also search SKILL.md content")
@click.option("--json", "json_flag", is_flag=True, help="Output JSON")
def search(keyword: str, category: str | None, status: str | None, skill: bool, json_flag: bool):
    """Search registry by name, display_name, description, category or skill."""
    kw = keyword.lower()
    cat = category.lower() if category else None
    st = status.lower() if status else None
    results = []
    for e in registry.entries():
        hay = " ".join([str(e.get(k, "")) for k in ("name", "display_name", "description", "category")])
        match = kw in hay.lower()
        if skill and not match:
            path = registry.skill_path(e)
            if path and path.exists():
                match = kw in path.read_text(encoding="utf-8").lower()
        if match and cat and e.get("category", "").lower() != cat:
            match = False
        if match and st and e.get("status", "").lower() != st:
            match = False
        if match:
            results.append(e)
    if json_flag:
        click.echo(json.dumps(results, ensure_ascii=False, indent=2))
        return
    for e in results:
        click.echo(f"{e['name']:20} {e.get('display_name', '')}")


@cli.command()
@click.argument("name")
def skill(name: str):
    """Display the SKILL.md for a tool."""
    entry = registry.find(name)
    if not entry:
        click.echo(f"unknown tool: {name}", err=True)
        sys.exit(1)
    path = registry.skill_path(entry)
    if not path or not path.exists():
        click.echo(f"no skill doc for {name}", err=True)
        sys.exit(1)
    click.echo(path.read_text(encoding="utf-8"))


@cli.command()
@click.argument("name")
@click.option("--json", "json_flag", is_flag=True, help="Output JSON")
def info(name: str, json_flag: bool):
    """Show detailed registry info for a tool."""
    entry = registry.find(name)
    if not entry:
        click.echo(f"unknown tool: {name}", err=True)
        sys.exit(1)
    if json_flag:
        click.echo(json.dumps(entry, ensure_ascii=False, indent=2))
        return
    for k, v in entry.items():
        click.echo(f"{k}: {v}")


@cli.command()
@click.argument("name")
def install(name: str):
    """Run the install_cmd for a registered tool."""
    entry = registry.find(name)
    if not entry:
        click.echo(f"unknown tool: {name}", err=True)
        sys.exit(1)
    cmd = entry.get("install_cmd")
    if not cmd:
        click.echo(f"{name}: no install_cmd", err=True)
        sys.exit(1)
    click.echo(f"[zero] {cmd}")
    sys.exit(subprocess.run(cmd, shell=True, cwd=runner.WORKSPACE_ROOT).returncode)


@cli.command(
    context_settings=dict(ignore_unknown_options=True, allow_extra_args=True),
)
@click.argument("name")
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
@click.option("--dry-run", is_flag=True, help="Print the command without executing")
def run(name: str, args: tuple[str, ...], dry_run: bool):
    """Run a registered local CLI with optional arguments."""
    sys.exit(runner.run(name, list(args), dry_run=dry_run))


@cli.command()
@click.option("--json", "json_flag", is_flag=True, help="Output JSON")
def scan(json_flag: bool):
    """Scan workspace for cli-anything-registry.json files."""
    found = registry.scan()
    if json_flag:
        click.echo(json.dumps(found, ensure_ascii=False, indent=2))
        return
    for item in found:
        click.echo(f"{item.get('name')} ({item.get('version')}) - {item.get('_path')}")


@cli.command(
    context_settings=dict(ignore_unknown_options=True, allow_extra_args=True),
)
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
@click.option("--dry-run", is_flag=True, help="Print the command without executing")
def brief(args: tuple[str, ...], dry_run: bool):
    """Generate life/work brief (shortcut for 'zero run life-brief')."""
    sys.exit(runner.run("life-brief", list(args), dry_run=dry_run))


@cli.command()
@click.option("--json", "json_flag", is_flag=True, help="Output JSON")
def doctor(json_flag: bool):
    """Validate the local registry."""
    issues = registry.validate()
    ok = not issues
    if json_flag:
        click.echo(json.dumps({"ok": ok, "issues": issues}, ensure_ascii=False, indent=2))
        sys.exit(0 if ok else 1)
    if ok:
        click.echo("registry OK")
        return
    for issue in issues:
        click.echo(f"issue: {issue}", err=True)
    sys.exit(1)


def main():
    cli()
