"""zig-era: name the Zig era a tree was written for, from its markers."""

import argparse
import sys
from pathlib import Path

from jacazul.zigexpert.archaeology import scan


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="zig-era",
        description=(
            "Era scan: name the newest Zig release a tree targets and the "
            "oldest marker still present."
        ),
    )
    parser.add_argument("path", nargs="?", default=".")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.path)
    if not root.is_dir():
        print(
            f"❌ {root} is not a directory.\n"
            "   ACTION: pass the project root (the directory holding "
            "build.zig).",
            file=sys.stderr,
        )
        return 2

    report = scan(root)
    if report.era is None:
        print("🐊 ZIG_ERA: unknown (no markers)")
    else:
        print(f"🐊 ZIG_ERA: {report.era}")
    if report.floor:
        print(f"   floor: {report.floor} (build.zig.zon)")
    if report.migration:
        print(
            f"   migration: oldest marker {report.oldest}, newest "
            f"{report.era}; walk VERSIONS.md between them"
        )
    for item in report.evidence:
        print(f"  - {item}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
