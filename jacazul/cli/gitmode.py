"""git-mode: name the integration workflow a repository uses."""

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from jacazul.gitexpert.probe import detect


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="git-mode",
        description=(
            "Workflow scan: linear (rebase and fast-forward), merge (merge "
            "commits integrate topics) or unknown, with layout, reference "
            "branch, upstream, convention, signing and hooks."
        ),
    )
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--json", action="store_true", help="JSON output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
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

    if args.json:
        print(json.dumps(asdict(report), indent=2))
        return 0

    hint = (
        " (ask before rewriting history)" if report.mode == "unknown" else ""
    )
    print(f"🐊 GIT_MODE: {report.mode} (source: {report.source}){hint}")
    trees = (
        f" ({report.worktrees} worktrees)" if report.layout != "plain" else ""
    )
    print(f"  layout: {report.layout}{trees}")
    if report.reference:
        print(
            f"  reference: {report.reference} "
            f"(source: {report.reference_source})"
        )
    else:
        print("  reference: unknown (pin it or ask)")
    if not report.branch:
        print("  branch: detached HEAD")
    elif report.upstream:
        print(
            f"  branch: {report.branch} -> {report.upstream} "
            f"(ahead {report.ahead}, behind {report.behind})"
        )
    else:
        print(f"  branch: {report.branch} (no upstream: unpublished)")
    print(
        f"  convention: {report.conventional}/{report.recent} recent titles "
        "are Conventional Commits"
    )
    print(f"  signing: {report.signing}")
    print(f"  hooks: {report.hooks}")
    for item in report.evidence:
        print(f"  - {item}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
