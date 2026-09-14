"""sh-census: count shell pitfall families by kind across a tree."""

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from jacazul.shexpert.archaeology import census, lint


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sh-census",
        description=(
            "Pitfall census for shell scripts: security, correctness, "
            "portability and maintenance families with counts and files."
        ),
    )
    parser.add_argument("path", nargs="?", help="project root")
    parser.add_argument(
        "--lint",
        action="store_true",
        help="also parse every script with the shell its shebang declares",
    )
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--all", action="store_true", help="include zero rows")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.path:
        print(
            "❌ sh-census needs an explicit path.\n"
            "   ACTION: pass the directory holding the scripts.",
            file=sys.stderr,
        )
        return 2
    root = Path(args.path)
    if not root.is_dir():
        print(f"❌ {root} is not a directory.", file=sys.stderr)
        return 2

    rows = census(root)
    shown = rows if args.all else [r for r in rows if r.count]
    failures = lint(root) if args.lint else []
    total = sum(r.count for r in rows)

    if args.json:
        print(
            json.dumps(
                {
                    "rows": [asdict(r) for r in shown],
                    "total": total,
                    "lint_failures": failures,
                },
                indent=2,
            )
        )
        return 0

    print("🐊 sh-census: pitfall families")
    print(f"{'kind':<12} {'count':>6} {'files':>6}  label")
    for r in shown:
        print(f"{r.kind:<12} {r.count:>6} {r.files:>6}  {r.label}")
    print(f"total: {total} across {len(shown)} families")
    if args.lint:
        if failures:
            print(f"\n❌ parse: {len(failures)} scripts fail with their shell")
            for line in failures[:50]:
                print(f"  - {line}")
        else:
            print("\n✅ parse: every script parses with its declared shell")
    return 0


if __name__ == "__main__":
    sys.exit(main())
