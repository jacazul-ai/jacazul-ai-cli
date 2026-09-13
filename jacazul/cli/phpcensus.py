"""php-census: count removed and deprecated PHP constructs by the version
that breaks them, or the constructs newer than a production floor."""

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from jacazul.phpexpert.archaeology import census, lint


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="php-census",
        description=(
            "Migration progress bar: counts of constructs that a newer PHP "
            "removes or deprecates, grouped by breaking version. With "
            "--floor, counts the constructs newer than that floor instead "
            "(the bridge check while production stays behind)."
        ),
    )
    parser.add_argument("path", nargs="?", help="project root")
    parser.add_argument(
        "--floor",
        help="production floor (e.g. 5.6): report syntax newer than it",
    )
    parser.add_argument(
        "--lint",
        metavar="PHP",
        nargs="?",
        const="php",
        help="also run `php -l` over the tree with this binary",
    )
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument(
        "--all", action="store_true", help="include rows with zero hits"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.path:
        print(
            "❌ php-census needs an explicit path.\n"
            "   ACTION: pass the project root you are migrating.",
            file=sys.stderr,
        )
        return 2
    root = Path(args.path)
    if not root.is_dir():
        print(f"❌ {root} is not a directory.", file=sys.stderr)
        return 2

    rows = census(root, floor=args.floor)
    shown = rows if args.all else [r for r in rows if r.count]
    failures = lint(root, args.lint) if args.lint else []
    total = sum(r.count for r in rows)

    if args.json:
        print(
            json.dumps(
                {
                    "floor": args.floor,
                    "rows": [asdict(r) for r in shown],
                    "total": total,
                    "lint_failures": failures,
                },
                indent=2,
            )
        )
        return 0

    if args.floor:
        print(f"🐊 php-census: constructs newer than floor {args.floor}")
    else:
        print("🐊 php-census: constructs a newer PHP removes or deprecates")
    print(f"{'breaks':<7} {'kind':<11} {'count':>6} {'files':>6}  label")
    for r in shown:
        print(
            f"{r.breaks:<7} {r.kind:<11} {r.count:>6} {r.files:>6}  {r.label}"
        )
    print(f"total: {total} across {len(shown)} construct families")
    if args.lint:
        if failures:
            print(
                f"\n❌ php -l ({args.lint}): {len(failures)} files "
                "fail to parse"
            )
            for line in failures[:50]:
                print(f"  - {line}")
        else:
            print(f"\n✅ php -l ({args.lint}): every file parses")
    if args.floor and total:
        print(
            "\n💡 PROMPT: these constructs will not run on the production "
            f"floor {args.floor}. Rewrite them in the bridge subset or "
            "flip production first."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
