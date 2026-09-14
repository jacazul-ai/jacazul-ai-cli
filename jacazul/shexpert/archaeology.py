"""Dialect scan and pitfall census for shell scripts.

The axis for shell is the dialect a script targets, not its age: POSIX
``sh``, ``bash`` (with a minimum version implied by the features used), or
``mixed`` when bashisms sit under a ``#!/bin/sh`` shebang or a feature
exceeds the declared minimum. The census counts pitfall families by kind
(security, correctness, portability, maintenance). No shellcheck needed;
``bash -n`` / ``sh -n`` run only when asked and available.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

MODES = ("portable", "bash", "mixed")
ENV_MODE = "JACAZUL_SH_MODE"

_SKIP_DIRS = {
    ".git",
    "node_modules",
    "vendor",
    ".venv",
    "venv",
    "dist",
    "build",
    "__pycache__",
}
_SUFFIXES = {".sh", ".bash", ".zsh", ".ksh"}
_SAMPLE_LIMIT = 2000
_SHEBANG = re.compile(r"^#!\s*(\S+)(?:\s+(\S+))?")

# (label, regex) constructs that POSIX sh does not have.
BASHISMS: tuple[tuple[str, re.Pattern[str]], ...] = tuple(
    (label, re.compile(rx, re.MULTILINE))
    for label, rx in (
        ("[[ ]] test", r"(?<![\w\"'])\[\[\s"),
        ("(( )) arithmetic command", r"(?<![$\w])\(\(\s*[^)]"),
        ("array assignment name=( )", r"^\s*\w+=\("),
        ("array expansion ${arr[@]}", r"\$\{\w+\[[@*0-9]"),
        ("local", r"^\s*local\s"),
        ("function keyword", r"^\s*function\s+\w"),
        ("process substitution <( )", r"[<>]\("),
        ("${var//pattern} substitution", r"\$\{\w+//"),
        ("${var^^} / ${var,,} case conversion", r"\$\{\w+(?:\^\^|,,)\}"),
        ("$'...' ANSI-C quoting", r"\$'"),
        ("read -a", r"\bread\s+-[a-z]*a"),
        ("echo -e", r"\becho\s+-[a-z]*e"),
        ("source (POSIX uses .)", r"^\s*source\s"),
        ("declare / typeset", r"^\s*(?:declare|typeset)\s"),
        ("let", r"^\s*let\s"),
        ("select loop", r"^\s*select\s+\w+\s+in\b"),
        ("=~ regex match", r"=~"),
        ("$RANDOM", r"\$RANDOM\b"),
        ("${!var} indirect expansion", r"\$\{!\w"),
        ("&> redirection", r"&>"),
        ("|& pipe", r"\|&"),
        ("pushd / popd", r"^\s*(?:pushd|popd)\b"),
        ("printf %q", r"printf\s+['\"]?[^'\"]*%q"),
        ("mapfile / readarray", r"^\s*(?:mapfile|readarray)\b"),
        ("declare -A associative array", r"^\s*declare\s+-[a-zA-Z]*A"),
        ("${var@Q} transformation", r"\$\{\w+@[QEPAaKkU]\}"),
        ("coproc", r"^\s*coproc\b"),
    )
)

# Minimum bash version implied by a construct.
VERSION_GATES: tuple[tuple[str, str, re.Pattern[str]], ...] = tuple(
    (label, version, re.compile(rx, re.MULTILINE))
    for label, version, rx in (
        ("mapfile / readarray", "4.0", r"^\s*(?:mapfile|readarray)\b"),
        ("declare -A", "4.0", r"^\s*declare\s+-[a-zA-Z]*A"),
        ("case ;;& fallthrough", "4.0", r";;&"),
        ("coproc", "4.0", r"^\s*coproc\b"),
        ("${var^^} / ${var,,}", "4.0", r"\$\{\w+(?:\^\^|,,)\}"),
        ("|& pipe", "4.0", r"\|&"),
        ("test -v var", "4.2", r"\[\[?\s+-v\s"),
        ("declare -n nameref", "4.3", r"^\s*declare\s+-[a-zA-Z]*n"),
        ("negative array index", "4.3", r"\$\{\w+\[-\d+\]\}"),
        ("${var@Q}", "4.4", r"\$\{\w+@[QEPA]\}"),
        (
            "EPOCHSECONDS / EPOCHREALTIME",
            "5.0",
            r"\$\{?EPOCH(?:SECONDS|REALTIME)",
        ),
        ("${var@U} / ${var@L}", "5.1", r"\$\{\w+@[ULu]\}"),
    )
)

ZSHISMS: tuple[tuple[str, re.Pattern[str]], ...] = tuple(
    (label, re.compile(rx, re.MULTILINE))
    for label, rx in (
        ("setopt", r"^\s*setopt\s"),
        ("autoload", r"^\s*autoload\s"),
        ("${(f)var} parameter flags", r"\$\{\([a-zA-Z@]+\)\w"),
    )
)


@dataclass
class Pitfall:
    label: str
    kind: str  # security | correctness | portability | maintenance
    pattern: re.Pattern[str] | None
    file_check: str | None = None  # name of a file-level check


def _p(
    label: str, kind: str, rx: str | None, file_check: str | None = None
) -> Pitfall:
    return Pitfall(
        label, kind, re.compile(rx, re.MULTILINE) if rx else None, file_check
    )


PITFALLS: tuple[Pitfall, ...] = (
    _p("eval on a string", "security", r"^\s*eval\s"),
    _p(
        "curl | sh / wget | bash",
        "security",
        r"\b(?:curl|wget)\b[^|\n]*\|\s*(?:sudo\s+)?(?:ba|z)?sh\b",
    ),
    _p("sudo inside the script", "security", r"^\s*sudo\s"),
    _p(
        "rm -rf on a variable without :? guard",
        "security",
        r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*\s+[\"']?\$(?!\{\w+:\?)\{?\w+",
    ),
    _p(
        "unquoted expansion as argument (heuristic)",
        "security",
        r"(?<=\s)\$\{?[A-Za-z_]\w*\}?(?=\s*(?:$|[;|&>]|\s))",
        file_check="unquoted_outside_tests",
    ),
    _p("cd without || exit / && check", "correctness", r"^\s*cd\s+[^|&;\n]+$"),
    _p(
        "parsing ls output",
        "correctness",
        r"\$\(\s*ls\b|`\s*ls\b|\bin\s+\$\(ls\b",
    ),
    _p("if [ $? ...] instead of if command", "correctness", r"\[\s+\$\?\s"),
    _p("read without -r", "correctness", r"^\s*read\s+(?!-[a-z]*r)(?!-)\w"),
    _p(
        "== inside [ ] (POSIX test uses =)",
        "correctness",
        r"\[\s[^]\n]*[^=!]==[^=]",
    ),
    _p(
        "set -e with pipelines and no pipefail",
        "correctness",
        None,
        file_check="errexit_no_pipefail",
    ),
    _p("echo -e / echo -n (not portable)", "portability", r"\becho\s+-[en]\b"),
    _p("which instead of command -v", "portability", r"\bwhich\s+\w"),
    _p("sed -i (GNU and BSD differ)", "portability", r"\bsed\s+-i\b"),
    _p(
        "readlink -f (GNU only on macOS < 12.3)",
        "portability",
        r"\breadlink\s+-f\b",
    ),
    _p("backticks instead of $( )", "portability", r"`[^`\n]+`"),
    _p(
        "hardcoded #!/bin/bash (use /usr/bin/env bash)",
        "portability",
        r"^#!\s*/bin/bash",
    ),
    _p(
        "mktemp without trap cleanup",
        "maintenance",
        None,
        file_check="mktemp_no_trap",
    ),
    _p("expr instead of $(( ))", "maintenance", r"\bexpr\s"),
    _p(
        "cat | grep (useless use of cat)",
        "maintenance",
        r"\bcat\s+\S+\s*\|\s*grep\b",
    ),
    _p("let instead of $(( ))", "maintenance", r"^\s*let\s"),
)

_ERREXIT = re.compile(r"^\s*set\s+-[a-zA-Z]*e|^\s*set\s+-o\s+errexit", re.M)
_PIPEFAIL = re.compile(r"pipefail")
_PIPE = re.compile(r"[^|]\|[^|&]")
_MKTEMP = re.compile(r"\bmktemp\b")
_TRAP = re.compile(r"^\s*trap\s", re.M)


@dataclass
class FileInfo:
    path: Path
    declared: str  # sh | bash | zsh | none
    dialect: str  # portable | bash | zsh | mixed
    bashisms: list[str] = field(default_factory=list)
    zshisms: list[str] = field(default_factory=list)
    version_gates: list[str] = field(default_factory=list)
    min_bash: str | None = None


@dataclass
class Report:
    mode: str | None
    files: int
    evidence: list[str] = field(default_factory=list)
    infos: list[FileInfo] = field(default_factory=list)


@dataclass
class Row:
    label: str
    kind: str
    count: int
    files: int


def _declared(text: str) -> str:
    match = _SHEBANG.match(text)
    if not match:
        return "none"
    interp = match.group(1)
    arg = match.group(2) or ""
    name = Path(interp).name if not interp.endswith("env") else Path(arg).name
    if name in {"sh", "dash", "ash"}:
        return "sh"
    if name == "bash":
        return "bash"
    if name == "zsh":
        return "zsh"
    if name == "ksh":
        return "sh"
    return "none"


def _is_shell(path: Path) -> bool:
    if path.suffix in _SUFFIXES:
        return True
    if path.suffix:
        return False
    try:
        with path.open("rb") as handle:
            head = handle.read(80)
    except OSError:
        return False
    return head.startswith(b"#!") and (b"sh" in head.split(b"\n", 1)[0])


def _iter_scripts(base: Path):
    count = 0
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
        for name in filenames:
            path = Path(dirpath, name)
            if path.is_symlink() or not _is_shell(path):
                continue
            yield path
            count += 1
            if count >= _SAMPLE_LIMIT:
                return


def _strip_comments(text: str) -> str:
    lines = []
    for i, line in enumerate(text.splitlines()):
        if i == 0 and line.startswith("#!"):
            lines.append(line)
            continue
        stripped = line.lstrip()
        lines.append("" if stripped.startswith("#") else line)
    return "\n".join(lines) + "\n"


def scan_file(path: str | os.PathLike[str]) -> FileInfo:
    p = Path(path)
    raw = p.read_text(encoding="utf-8", errors="replace")
    text = _strip_comments(raw)
    declared = _declared(raw)

    bashisms = [label for label, rx in BASHISMS if rx.search(text)]
    zshisms = [label for label, rx in ZSHISMS if rx.search(text)]
    gates = [
        (label, ver) for label, ver, rx in VERSION_GATES if rx.search(text)
    ]
    min_bash = max((ver for _, ver in gates), key=_vkey) if gates else None

    if declared == "sh":
        dialect = "mixed" if bashisms else "portable"
    elif declared == "bash":
        dialect = "mixed" if zshisms else "bash"
    elif declared == "zsh":
        dialect = "zsh"
    else:
        dialect = "bash" if bashisms else "portable"

    return FileInfo(
        path=p,
        declared=declared,
        dialect=dialect,
        bashisms=bashisms,
        zshisms=zshisms,
        version_gates=[f"{label} (bash {ver})" for label, ver in gates],
        min_bash=min_bash,
    )


def _vkey(version: str) -> tuple[int, int]:
    major, minor = version.split(".")
    return int(major), int(minor)


def scan(root: str | os.PathLike[str]) -> Report:
    base = Path(root)
    infos = [scan_file(path) for path in _iter_scripts(base)]
    evidence: list[str] = []
    if not infos:
        evidence.append("no shell scripts found (by suffix or shebang)")
        return Report(mode=None, files=0, evidence=evidence)

    by_dialect: dict[str, int] = {}
    for info in infos:
        by_dialect[info.dialect] = by_dialect.get(info.dialect, 0) + 1
    for dialect in ("portable", "bash", "zsh", "mixed"):
        if dialect in by_dialect:
            evidence.append(f"{dialect}: {by_dialect[dialect]} files")

    for info in infos:
        rel = (
            info.path.relative_to(base)
            if info.path.is_relative_to(base)
            else info.path
        )
        if info.dialect == "mixed":
            what = ", ".join(info.bashisms[:4] or info.zshisms[:4])
            evidence.append(
                f"mixed: {rel} declares {info.declared} but uses {what}"
            )
        if info.min_bash:
            evidence.append(
                f"{rel}: needs bash {info.min_bash} ({info.version_gates[0]})"
            )

    if "mixed" in by_dialect:
        mode = "mixed"
    elif set(by_dialect) <= {"portable"}:
        mode = "portable"
    else:
        mode = "bash"
    return Report(mode=mode, files=len(infos), evidence=evidence, infos=infos)


_SAFE_SPANS = re.compile(r"\[\[.*?\]\]|\(\(.*?\)\)|\$\(\(.*?\)\)", re.S)
_UNQUOTED = re.compile(
    r"(?<=\s)\$\{?[A-Za-z_]\w*\}?(?=\s*(?:$|[;|&>]|\s))", re.M
)


def _file_check(name: str, text: str) -> int:
    if name == "unquoted_outside_tests":
        # [[ ]] and (( )) do not word-split; blank them before counting.
        return len(_UNQUOTED.findall(_SAFE_SPANS.sub(" ", text)))
    if name == "errexit_no_pipefail":
        return int(
            bool(_ERREXIT.search(text))
            and bool(_PIPE.search(text))
            and not _PIPEFAIL.search(text)
        )
    if name == "mktemp_no_trap":
        return int(bool(_MKTEMP.search(text)) and not _TRAP.search(text))
    return 0


def census(root: str | os.PathLike[str]) -> list[Row]:
    counts: dict[str, int] = {}
    files: dict[str, int] = {}
    for path in _iter_scripts(Path(root)):
        text = _strip_comments(
            path.read_text(encoding="utf-8", errors="replace")
        )
        for pit in PITFALLS:
            if pit.file_check:
                hits = _file_check(pit.file_check, text)
            else:
                hits = len(pit.pattern.findall(text))
            if hits:
                counts[pit.label] = counts.get(pit.label, 0) + hits
                files[pit.label] = files.get(pit.label, 0) + 1
    return [
        Row(p.label, p.kind, counts.get(p.label, 0), files.get(p.label, 0))
        for p in PITFALLS
    ]


def lint(root: str | os.PathLike[str]) -> list[str]:
    """Parse every script with the interpreter its shebang declares."""
    failures: list[str] = []
    dash = shutil.which("dash")
    bash = shutil.which("bash")
    sh = shutil.which("sh")
    for info in scan(root).infos:
        if info.declared == "sh":
            binary = dash or sh
        elif info.declared == "zsh":
            binary = shutil.which("zsh")
        else:
            binary = bash
        if not binary:
            continue
        res = subprocess.run(
            [binary, "-n", str(info.path)], capture_output=True, text=True
        )
        if res.returncode != 0:
            first = (res.stderr or res.stdout).strip().splitlines()
            failures.append(
                first[0] if first else f"{info.path}: parse failed"
            )
    return failures
