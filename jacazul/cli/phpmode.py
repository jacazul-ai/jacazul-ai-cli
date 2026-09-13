"""php-mode: name the PHP mode (legacy, greenfield, migration) of a tree."""

import argparse
import sys
from pathlib import Path

from jacazul.phpexpert.archaeology import resolve_mode, scan


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="php-mode",
        description=(
            "Archaeology scan: classify a PHP tree as legacy, greenfield "
            "or migration and flag syntax above the declared floor."
        ),
    )
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument(
        "--scan-only",
        action="store_true",
        help="ignore JACAZUL_PHP_MODE and composer.json overrides",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.path)
    if not root.is_dir():
        print(
            f"❌ {root} is not a directory.\n"
            "   ACTION: pass the project root (the directory holding "
            "composer.json or index.php).",
            file=sys.stderr,
        )
        return 2

    report = scan(root)
    if args.scan_only:
        mode, source = report.mode, "scan"
    else:
        mode, source = resolve_mode(root)

    print(f"🐊 PHP_MODE: {mode} (source: {source})")
    if report.floor:
        print(f"   floor: {report.floor}")
    for item in report.evidence:
        print(f"  - {item}")
    if source != "scan" and mode != report.mode:
        print(f"ℹ scan would say {report.mode}; override from {source} wins.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
