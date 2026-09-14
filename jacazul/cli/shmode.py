"""sh-mode: name the shell dialect a tree targets (portable, bash, mixed)."""

import argparse
import os
import sys
from pathlib import Path

from jacazul.shexpert.archaeology import ENV_MODE, MODES, scan


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sh-mode",
        description=(
            "Dialect scan: portable (POSIX sh), bash, or mixed (bashisms "
            "under #!/bin/sh or features above the minimum bash)."
        ),
    )
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument(
        "--files",
        action="store_true",
        help="list every script and its dialect",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.path)
    if not root.is_dir():
        print(f"❌ {root} is not a directory.", file=sys.stderr)
        return 2

    report = scan(root)
    override = os.environ.get(ENV_MODE, "").strip().lower()
    mode = override if override in MODES else report.mode
    source = "env" if override in MODES else "scan"

    if mode is None:
        print("🐊 SH_MODE: unknown (no shell scripts)")
    else:
        print(f"🐊 SH_MODE: {mode} (source: {source}, {report.files} scripts)")
    for item in report.evidence:
        print(f"  - {item}")
    if args.files:
        for info in report.infos:
            need = f" bash>={info.min_bash}" if info.min_bash else ""
            print(f"  {info.dialect:<8} {info.declared:<5}{need}  {info.path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
