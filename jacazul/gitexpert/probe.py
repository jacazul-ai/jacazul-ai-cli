"""Workflow probe and commit census for Git repositories.

The axis for Git is the integration style a project uses, not the age of
its history: ``linear`` (topic branches rebased and fast-forwarded),
``merge`` (merge commits integrate topics) or ``unknown``. The style comes
from the project pin (the ``## Git Workflow`` section of ``AGENTS.md``),
then the operator pin (local ``git-expert.*`` config), then a scan of the
reference branch. The census counts message and history families over a
commit range. Nothing here writes to the repository.
"""

from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

MODES = ("linear", "merge")
PIN_KEYS = ("integration", "reference")
CONFIG_SECTION = "git-expert"
PROJECT_FILE = "AGENTS.md"
SCAN_DEPTH = 200
MIN_LINEAR = 10
RECENT_TITLES = 50
TITLE_MAX = 50
BODY_MAX = 72
EXAMPLES = 5

CONVENTIONAL = re.compile(
    r"^(?:feat|fix|refactor|perf|test|docs|style|build|ci|chore|revert)"
    r"(?:\([^)\s]+\))?!?: \S"
)

_SECTION = re.compile(r"^##\s+Git Workflow\s*$", re.IGNORECASE)
_HEADING = re.compile(r"^#{1,2}\s")
_PIN_LINE = re.compile(
    r"^\s*[-*]\s*(integration|reference)\s*:\s*`?([\w./-]+)`?\s*$",
    re.IGNORECASE,
)

_AI_NAMES = (
    r"(?:copilot|claude|anthropic|openai|chatgpt|codex|gemini|cursor|devin"
    r"|aider|codeium|windsurf|tabnine|jules|gpt-?\d)"
)
_AI_TRAILERS = (
    re.compile(rf"^co-authored-by:.*\b{_AI_NAMES}", re.IGNORECASE),
    re.compile(rf"^(?:assisted|generated)-by:.*\b{_AI_NAMES}", re.I),
    re.compile(r"^claude-session:", re.IGNORECASE),
    re.compile(r"generated (?:with|by) \[?claude", re.IGNORECASE),
)
_FIXUP = re.compile(r"^(?:fixup|squash|amend)! ")
_TICKET = re.compile(r"^(?:refs|fixes|closes|resolves):\s*(.+)$", re.I)
_TRAILER = re.compile(r"^[A-Za-z][\w-]*: \S")
_UUID = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
    re.IGNORECASE,
)
_HEX = re.compile(r"(?<![#\w-])[0-9a-f]{7,40}(?![\w-])", re.IGNORECASE)

# (key, kind, label) in report order.
FAMILIES: tuple[tuple[str, str, str], ...] = (
    ("ai", "security", "AI attribution trailer"),
    ("title_long", "policy", f"title over {TITLE_MAX} characters"),
    ("not_conventional", "policy", "title not in Conventional Commits form"),
    ("no_blank", "policy", "missing blank line after title"),
    ("body_wide", "policy", f"body line over {BODY_MAX} characters"),
    ("literal", "policy", "literal \\n in title (collapsed message)"),
    ("footer", "policy", "ticket footer not the last line"),
    ("internal", "policy", "internal workflow ID in footer"),
    ("leftover", "history", "leftover fixup!/squash!/amend! commit"),
    ("merge", "history", "merge commit under linear mode"),
)


@dataclass
class Report:
    mode: str  # linear | merge | unknown
    source: str  # project | config | scan
    layout: str  # plain | worktrees | bare
    worktrees: int
    reference: str | None
    reference_source: str | None
    branch: str | None
    upstream: str | None
    ahead: int | None
    behind: int | None
    conventional: int
    recent: int
    signing: str
    hooks: str
    evidence: list[str] = field(default_factory=list)


@dataclass
class Row:
    label: str
    kind: str
    count: int
    examples: list[str] = field(default_factory=list)


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(cwd), *args], capture_output=True, text=True
    )


def _out(cwd: Path, *args: str) -> str | None:
    result = _git(cwd, *args)
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def _project_pin(top: Path) -> dict[str, str]:
    try:
        lines = (top / PROJECT_FILE).read_text(encoding="utf-8").splitlines()
    except OSError:
        return {}
    pin: dict[str, str] = {}
    inside = False
    for line in lines:
        if _SECTION.match(line):
            inside = True
            continue
        if not inside:
            continue
        if _HEADING.match(line):
            break
        match = _PIN_LINE.match(line)
        if match:
            pin.setdefault(match.group(1).lower(), match.group(2))
    return pin


def _config_pin(root: Path) -> dict[str, str]:
    pin: dict[str, str] = {}
    for key in PIN_KEYS:
        value = _out(root, "config", "--get", f"{CONFIG_SECTION}.{key}")
        if value:
            pin[key] = value
    return pin


def resolve_ref(root: Path, name: str) -> str | None:
    """Return a revision for a branch name: local first, then origin."""
    for ref, rev in (
        (f"refs/heads/{name}", name),
        (f"refs/remotes/origin/{name}", f"origin/{name}"),
    ):
        if _out(root, "rev-parse", "--verify", "--quiet", ref) is not None:
            return rev
    return None


def _reference(
    root: Path, pins: tuple[tuple[str, dict[str, str]], ...]
) -> tuple[str | None, str | None]:
    for source, pin in pins:
        if pin.get("reference"):
            return pin["reference"], source
    head = _out(
        root, "symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD"
    )
    if head:
        return head.split("/", 1)[-1], "origin/HEAD"
    default = _out(root, "config", "--get", "init.defaultBranch")
    for name, source in (
        (default, "init.defaultBranch"),
        ("main", "branch"),
        ("master", "branch"),
    ):
        if name and resolve_ref(root, name):
            return name, source
    return None, None


def _scan(root: Path, reference: str | None, evidence: list[str]) -> str:
    if _out(root, "config", "--get-regexp", r"^gitflow\."):
        evidence.append("gitflow.* config present: merge-based git-flow")
        return "merge"
    target = (resolve_ref(root, reference) if reference else None) or "HEAD"
    listing = _out(
        root,
        "rev-list",
        "--first-parent",
        f"--max-count={SCAN_DEPTH}",
        "--parents",
        target,
    )
    lines = (listing or "").splitlines()
    merges = sum(1 for line in lines if len(line.split()) > 2)
    if merges:
        evidence.append(
            f"{merges} merge commits in the last {len(lines)} "
            f"first-parent commits of {target}"
        )
        return "merge"
    if len(lines) >= MIN_LINEAR:
        evidence.append(
            f"no merge commits in the last {len(lines)} "
            f"first-parent commits of {target}"
        )
        return "linear"
    evidence.append(
        f"only {len(lines)} commits on {target}: not enough history to infer"
    )
    return "unknown"


def _worktree_count(root: Path) -> int:
    listing = _out(root, "worktree", "list", "--porcelain") or ""
    blocks = [block for block in listing.split("\n\n") if block.strip()]
    return sum(1 for block in blocks if "bare" not in block.splitlines())


def _hooks(root: Path, common: Path) -> str:
    custom = _out(root, "config", "--get", "core.hooksPath")
    if custom:
        return f"core.hooksPath={custom}"
    try:
        names = sorted(
            path.name
            for path in (common / "hooks").iterdir()
            if path.is_file()
            and not path.name.endswith(".sample")
            and os.access(path, os.X_OK)
        )
    except OSError:
        names = []
    return ", ".join(names) if names else "none"


def detect(path: str | os.PathLike[str]) -> Report | None:
    """Resolve the workflow of the repository holding ``path``."""
    root = Path(path)
    common_dir = _out(
        root, "rev-parse", "--path-format=absolute", "--git-common-dir"
    )
    if common_dir is None:
        return None
    common = Path(common_dir)
    top = _out(root, "rev-parse", "--show-toplevel")
    evidence: list[str] = []

    bare = _out(root, "config", "--bool", "core.bare") == "true"
    worktrees = _worktree_count(root)
    if bare:
        layout = "bare"
    elif worktrees > 1:
        layout = "worktrees"
    else:
        layout = "plain"
    if layout != "plain":
        evidence.append(
            f"stash stack is shared by {worktrees} worktrees: "
            "prefer WIP commits, apply stash entries by hash"
        )
    if (
        bare
        and _out(root, "config", "--get", "remote.origin.url")
        and not _out(root, "config", "--get-all", "remote.origin.fetch")
    ):
        evidence.append(
            "remote.origin.fetch is not set: a bare clone has no "
            "remote-tracking branches until it is configured"
        )

    pins = (
        ("project", _project_pin(Path(top)) if top else {}),
        ("config", _config_pin(root)),
    )
    mode = source = None
    for name, pin in pins:
        value = pin.get("integration", "").strip().lower()
        if not value:
            continue
        if value in MODES:
            mode, source = value, name
            where = (
                f"the Git Workflow section of {PROJECT_FILE}"
                if name == "project"
                else f"git config {CONFIG_SECTION}.integration"
            )
            evidence.append(f"pinned by {where}")
            break
        evidence.append(
            f"{name} pin integration={value!r} ignored "
            "(expected linear or merge)"
        )

    reference, reference_source = _reference(root, pins)
    if mode is None:
        mode, source = _scan(root, reference, evidence), "scan"

    branch = _out(root, "symbolic-ref", "--quiet", "--short", "HEAD")
    upstream = ahead = behind = None
    if branch:
        upstream = _out(
            root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"
        )
    if upstream:
        counts = _out(
            root, "rev-list", "--left-right", "--count", "HEAD...@{u}"
        )
        if counts:
            ahead, behind = (int(value) for value in counts.split())

    titles = _out(
        root, "log", f"-{RECENT_TITLES}", "--no-merges", "--format=%s"
    )
    titles_list = (titles or "").splitlines()
    conventional = sum(1 for title in titles_list if CONVENTIONAL.match(title))

    gpgsign = _out(root, "config", "--bool", "commit.gpgsign") == "true"
    signing_format = _out(root, "config", "--get", "gpg.format") or "openpgp"

    return Report(
        mode=mode,
        source=source,
        layout=layout,
        worktrees=worktrees,
        reference=reference,
        reference_source=reference_source,
        branch=branch,
        upstream=upstream,
        ahead=ahead,
        behind=behind,
        conventional=conventional,
        recent=len(titles_list),
        signing=f"on ({signing_format})" if gpgsign else "off",
        hooks=_hooks(root, common),
        evidence=evidence,
    )


def default_range(path: str | os.PathLike[str], report: Report) -> str | None:
    """Range to census when none is given, or None when it is ambiguous."""
    if report.upstream:
        return f"{report.upstream}..HEAD"
    if report.reference and report.branch != report.reference:
        base = resolve_ref(Path(path), report.reference)
        if base:
            return f"{base}..HEAD"
    return None


def _commits(root: Path, rng: str):
    result = _git(root, "log", "--format=%H%x00%P%x00%B%x1e", rng, "--")
    if result.returncode != 0:
        raise ValueError(result.stderr.strip() or f"git log {rng} failed")
    for record in result.stdout.split("\x1e"):
        record = record.lstrip("\n")
        if not record:
            continue
        sha, parents, message = record.split("\x00", 2)
        yield sha, parents.split(), message


def _too_wide(line: str) -> bool:
    return (
        len(line) > BODY_MAX
        and "://" not in line
        and not line.startswith(("    ", "\t"))
        and not _TRAILER.match(line)
    )


def _internal_id(root: Path, value: str) -> bool:
    if _UUID.search(value):
        return True
    for token in _HEX.findall(value):
        spec = f"{token}^{{commit}}"
        if _out(root, "rev-parse", "--verify", "--quiet", spec) is None:
            return True
    return False


def _hits(root: Path, parents: list[str], message: str, mode: str) -> set:
    lines = message.rstrip("\n").split("\n")
    title = lines[0]
    hits: set[str] = set()
    if any(rx.search(line) for line in lines for rx in _AI_TRAILERS):
        hits.add("ai")
    if len(parents) > 1:
        if mode == "linear":
            hits.add("merge")
        return hits
    if _FIXUP.match(title):
        hits.add("leftover")
        return hits

    if len(title) > TITLE_MAX:
        hits.add("title_long")
    if "\\n" in title:
        hits.add("literal")
    if not CONVENTIONAL.match(title):
        hits.add("not_conventional")
    if len(lines) > 1 and lines[1].strip():
        hits.add("no_blank")
    if any(_too_wide(line) for line in lines[1:]):
        hits.add("body_wide")

    tickets = [line for line in lines if _TICKET.match(line)]
    if tickets:
        last = next(line for line in reversed(lines) if line.strip())
        if not _TICKET.match(last):
            hits.add("footer")
        if any(_internal_id(root, line) for line in tickets):
            hits.add("internal")
    return hits


def census(
    path: str | os.PathLike[str], rng: str, mode: str = "unknown"
) -> list[Row]:
    """Count message and history families over the commits in ``rng``."""
    root = Path(path)
    rows = {key: Row(label, kind, 0) for key, kind, label in FAMILIES}
    for sha, parents, message in _commits(root, rng):
        for key in _hits(root, parents, message, mode):
            row = rows[key]
            row.count += 1
            if len(row.examples) < EXAMPLES:
                row.examples.append(sha[:8])
    return [rows[key] for key, _, _ in FAMILIES]
