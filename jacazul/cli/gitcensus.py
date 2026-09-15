"""git-census: count commit message and history families over a range."""

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from jacazul.gitexpert.probe import census, default_range, detect


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="git-census",
        description=(
            "Commit census: security (AI attribution), policy (title, body, "
            "footer, internal IDs) and history (leftover fixups, merges "
            "under linear mode) families with counts and example commits."
        ),
    )
    parser.add_argument("path", nargs="?", help="repository or worktree")
    parser.add_argument(
        "--range",
        dest="rng",
        help="commit range (default: upstream..HEAD, else reference..HEAD)",
    )
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--all", action="store_true", help="include zero rows")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.path:
        print(
            "❌ git-census needs an explicit path.\n"
            "   ACTION: pass the repository or worktree to check.",
            file=sys.stderr,
        )
        return 2
    root = Path(args.path)
    if not root.is_dir():
        print(f"❌ {root} is not a directory.", file=sys.stderr)
        return 2

    report = detect(root)
    if report is None:
        print(
            f"❌ {root} is not inside a Git repository.\n"
            "   ACTION: pass a path inside the repository or one of its "
            "worktrees.",
            file=sys.stderr,
        )
        return 2

    rng = args.rng or default_range(root, report)
    if rng is None:
        print(
            "❌ No default range: HEAD is on the reference branch (or no "
            "reference is known) and has no upstream.\n"
            "   ACTION: pass --range <base>..<tip> for the commits to check.",
            file=sys.stderr,
        )
        return 2
    try:
        rows = census(root, rng, mode=report.mode)
    except ValueError as exc:
        print(
            f"❌ Cannot read the range {rng}: {exc}\n"
            "   ACTION: pass a valid --range <base>..<tip>.",
            file=sys.stderr,
        )
        return 2

    shown = rows if args.all else [r for r in rows if r.count]
    total = sum(r.count for r in rows)

    if args.json:
        print(
            json.dumps(
                {
                    "range": rng,
                    "mode": report.mode,
                    "rows": [asdict(r) for r in shown],
                    "total": total,
                },
                indent=2,
            )
        )
        return 0

    print(f"🐊 git-census: {rng} (mode: {report.mode})")
    print(f"{'kind':<9} {'count':>6}  label")
    for r in shown:
        examples = f"  [{', '.join(r.examples)}]" if r.examples else ""
        print(f"{r.kind:<9} {r.count:>6}  {r.label}{examples}")
    print(f"total: {total} across {len(shown)} families")
    return 0


if __name__ == "__main__":
    sys.exit(main())
