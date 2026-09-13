"""js-check: run the checks a JavaScript/TypeScript tree declares, with
the house indentation preference and the legacy guard.

The command plan is built from what the tree declares (package manager
from the lockfile, tsc when tsconfig.json exists, eslint and prettier
when configured). ``--dry-run`` prints the plan without running it, so
the planner is testable without Node.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

from jacazul.jsexpert.archaeology import resolve_mode
from jacazul.jsexpert.formatting import (
    HOUSE_INDENT,
    ignore_formatting,
    resolve_indent,
)

_ESLINT_CONFIGS = (
    "eslint.config.js",
    "eslint.config.mjs",
    "eslint.config.cjs",
    "eslint.config.ts",
    ".eslintrc",
    ".eslintrc.js",
    ".eslintrc.cjs",
    ".eslintrc.json",
    ".eslintrc.yml",
    ".eslintrc.yaml",
)
_PRETTIER_CONFIGS = (
    ".prettierrc",
    ".prettierrc.json",
    ".prettierrc.yaml",
    ".prettierrc.yml",
    ".prettierrc.toml",
    ".prettierrc.js",
    ".prettierrc.cjs",
    ".prettierrc.mjs",
    "prettier.config.js",
    "prettier.config.cjs",
    "prettier.config.mjs",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="js-check",
        description=(
            "Run the checks a JS/TS tree declares; never invents gates."
        ),
    )
    parser.add_argument("path", nargs="?", help="project root to check")
    parser.add_argument(
        "--check", action="store_true", help="validate only; never write"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="print the plan and exit"
    )
    parser.add_argument(
        "--run-scripts",
        action="store_true",
        help="also run the project's own lint and test scripts",
    )
    parser.add_argument("--indent", type=int, help="override indent size")
    parser.add_argument(
        "--mode",
        choices=("legacy", "greenfield", "migration"),
        help="override the resolved mode",
    )
    return parser


def package_manager(root: Path) -> str:
    if (root / "pnpm-lock.yaml").is_file():
        return "pnpm"
    if (root / "bun.lock").is_file() or (root / "bun.lockb").is_file():
        return "bun"
    if (root / "yarn.lock").is_file():
        return "yarn"
    return "npm"


def _exec_prefix(manager: str) -> list[str]:
    if manager == "npm":
        return ["npx", "--no-install"]
    if manager == "bun":
        return ["bunx"]
    return [manager, "exec"]


def _scripts(root: Path) -> dict:
    path = root / "package.json"
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    scripts = data.get("scripts") if isinstance(data, dict) else None
    return scripts if isinstance(scripts, dict) else {}


def build_plan(root: Path, write: bool, run_scripts: bool) -> list[list[str]]:
    manager = package_manager(root)
    prefix = _exec_prefix(manager)
    plan: list[list[str]] = []

    if (root / "tsconfig.json").is_file():
        plan.append([*prefix, "tsc", "--noEmit"])
    if any((root / name).is_file() for name in _PRETTIER_CONFIGS):
        action = "--write" if write else "--check"
        plan.append([*prefix, "prettier", action, "."])
    if any((root / name).is_file() for name in _ESLINT_CONFIGS):
        cmd = [*prefix, "eslint", "."]
        if write:
            cmd.append("--fix")
        plan.append(cmd)
    if run_scripts:
        scripts = _scripts(root)
        for name in ("lint", "test"):
            if name in scripts:
                plan.append([manager, "run", name])
    return plan


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.path:
        print(
            "❌ js-check needs an explicit path.\n"
            "   ACTION: pass the project root you are working in.",
            file=sys.stderr,
        )
        return 2

    root = Path(args.path)
    if not root.is_dir():
        print(f"❌ {root} is not a directory.", file=sys.stderr)
        return 2

    mode, mode_source = (
        (args.mode, "flag") if args.mode else resolve_mode(root)
    )
    style, size, indent_source = resolve_indent(root, flag=args.indent)
    write = not args.check and not ignore_formatting(mode, root)

    print(
        f"🐊 js-check: mode {mode} ({mode_source}), indent {style} {size} "
        f"({indent_source}, house preference {HOUSE_INDENT[0]} "
        f"{HOUSE_INDENT[1]}), {'writing' if write else 'check-only'}"
    )
    if not write and not args.check:
        print(
            "ℹ Formatting guard active (JACAZUL_JS_TS_IGNORE_FORMATTING or "
            "legacy tree without formatter config). Nothing is written."
        )
    if mode == "greenfield" and indent_source == "default":
        print(
            "ℹ Greenfield tree with no declared indentation. ACTION: "
            "declare tabWidth in .prettierrc or indent_size in "
            ".editorconfig so the preference is explicit."
        )

    plan = build_plan(root, write, args.run_scripts)
    if not plan:
        print(
            "ℹ Nothing declared to run (no tsconfig, prettier or eslint "
            "config). Not inventing a gate."
        )
        return 0

    for cmd in plan:
        print("  $ " + " ".join(cmd))
    if args.dry_run:
        return 0

    failed = False
    for cmd in plan:
        try:
            res = subprocess.run(cmd, cwd=root, text=True)
        except FileNotFoundError:
            print(
                f"💡 PROMPT: {cmd[0]} is not installed. Install the "
                "project's package manager or skip with --dry-run.",
                file=sys.stderr,
            )
            return 1
        if res.returncode != 0:
            failed = True
            print(
                f"💡 PROMPT: '{' '.join(cmd)}' failed. Read its output "
                "above and fix the reported files.",
                file=sys.stderr,
            )
    if failed:
        print("\n❌ JS/TS validation failed.", file=sys.stderr)
        return 1
    print("\n✅ JS/TS validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
