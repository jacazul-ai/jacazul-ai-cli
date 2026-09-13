"""py-mode: print the Python mode (legacy, greenfield, migration) of a
tree and the evidence behind it."""

import argparse
import sys
from pathlib import Path

from jacazul.pyexpert.archaeology import resolve_mode, scan


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="py-mode",
        description=(
            "Archaeology scan: classify a Python tree as legacy, "
            "greenfield or migration."
        ),
    )
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument(
        "--scan-only",
        action="store_true",
        help="ignore JACAZUL_PY_MODE and [tool.jacazul] overrides",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.path)
    if not root.is_dir():
        print(
            f"❌ {root} is not a directory.\n"
            "   ACTION: pass the project root (the directory holding "
            "pyproject.toml or setup.py).",
            file=sys.stderr,
        )
        return 2

    report = scan(root)
    if args.scan_only:
        mode, source = report.mode, "scan"
    else:
        mode, source = resolve_mode(root)

    print(f"🐊 PY_MODE: {mode} (source: {source})")
    for item in report.evidence:
        print(f"  - {item}")
    if source != "scan" and mode != report.mode:
        print(f"ℹ scan would say {report.mode}; override from {source} wins.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
