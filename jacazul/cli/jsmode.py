"""js-mode: print the JavaScript/TypeScript mode of a tree and the
evidence behind it."""

import argparse
import sys
from pathlib import Path

from jacazul.jsexpert.archaeology import resolve_mode, scan


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="js-mode",
        description=(
            "Archaeology scan: classify a JavaScript/TypeScript tree as "
            "legacy, greenfield or migration."
        ),
    )
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument(
        "--scan-only",
        action="store_true",
        help="ignore JACAZUL_JS_TS_MODE and package.json overrides",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.path)
    if not root.is_dir():
        print(
            f"❌ {root} is not a directory.\n"
            "   ACTION: pass the project root (the directory holding "
            "package.json).",
            file=sys.stderr,
        )
        return 2

    report = scan(root)
    if args.scan_only:
        mode, source = report.mode, "scan"
    else:
        mode, source = resolve_mode(root)

    print(f"🐊 JS_TS_MODE: {mode} (source: {source})")
    for item in report.evidence:
        print(f"  - {item}")
    if source != "scan" and mode != report.mode:
        print(f"ℹ scan would say {report.mode}; override from {source} wins.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
