"""Archaeology scan: classify a Python tree as legacy, greenfield or
migration from the markers it leaves on disk.

The scan is a pure function over the filesystem. Override resolution
(environment, then ``[tool.jacazul] py_mode``) lives in ``resolve_mode``.
"""

from __future__ import annotations

import os
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

MODES = ("legacy", "greenfield", "migration")
ENV_MODE = "JACAZUL_PY_MODE"

_SKIP_DIRS = {
    ".git",
    ".hg",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".tox",
    ".mypy_cache",
    ".ruff_cache",
    "build",
    "dist",
    "site-packages",
}
_SAMPLE_LIMIT = 200

_PY2_PRINT = re.compile(r"^\s*print\s+[^(\s]", re.MULTILINE)
_PY2_FUTURE = re.compile(
    r"^\s*from\s+__future__\s+import\s+.*\b(print_function|unicode_literals)"
    r"\b",
    re.MULTILINE,
)
_PY2_SHIMS = re.compile(
    r"^\s*(import\s+six|from\s+six\b|import\s+future\b)", re.MULTILINE
)
_DEF = re.compile(
    r"^\s*(?:async\s+)?def\s+\w+\s*\(([^)]*)\)\s*(->)?", re.MULTILINE
)
_FSTRING = re.compile(r"\bf['\"]")
_PATHLIB = re.compile(
    r"^\s*(from\s+pathlib\s+import|import\s+pathlib)", re.MULTILINE
)
_OSPATH = re.compile(r"\bos\.path\.")
_DATACLASS = re.compile(r"@dataclass\b|from\s+dataclasses\s+import")
_ASYNC = re.compile(r"^\s*async\s+def\b", re.MULTILINE)
_PCT_FORMAT = re.compile(r"['\"]\s*%\s*\(")
_VERSION = re.compile(r"(\d+)\.(\d+)")


@dataclass
class Report:
    """Result of an archaeology scan."""

    mode: str
    evidence: list[str] = field(default_factory=list)
    floor: tuple[int, int] | None = None
    packaging: str = "none"
    legacy_code: int = 0
    modern_code: int = 0
    annotated_ratio: float | None = None


def scan(root: str | os.PathLike[str]) -> Report:
    """Classify ``root`` by interpreter floor, packaging, code era, test
    runner and formatting markers."""
    base = Path(root)
    evidence: list[str] = []

    floor = _interpreter_floor(base, evidence)
    packaging = _packaging(base, evidence)
    legacy_code, modern_code, ratio = _code_era(base, evidence)
    modern_tests = _test_runner(base, evidence)
    _formatting_config(base, evidence)

    has_markers = bool(evidence)
    mode = _classify(
        floor, packaging, legacy_code, modern_code, ratio, modern_tests
    )
    if not has_markers:
        evidence.append(
            "no evidence: empty or unmarked tree, defaulting to greenfield"
        )
    return Report(
        mode=mode,
        evidence=evidence,
        floor=floor,
        packaging=packaging,
        legacy_code=legacy_code,
        modern_code=modern_code,
        annotated_ratio=ratio,
    )


def resolve_mode(
    root: str | os.PathLike[str], env: dict[str, str] | None = None
) -> tuple[str, str]:
    """Return ``(mode, source)`` honoring the override chain.

    ``source`` is ``env``, ``pyproject`` or ``scan``.
    """
    env = os.environ if env is None else env
    candidate = env.get(ENV_MODE, "").strip().lower()
    if candidate in MODES:
        return candidate, "env"

    declared = _declared_mode(Path(root))
    if declared in MODES:
        return declared, "pyproject"

    return scan(root).mode, "scan"


def _declared_mode(base: Path) -> str | None:
    data = _load_pyproject(base)
    tool = data.get("tool", {}) if data else {}
    jacazul = tool.get("jacazul", {}) if isinstance(tool, dict) else {}
    value = jacazul.get("py_mode") if isinstance(jacazul, dict) else None
    return value.strip().lower() if isinstance(value, str) else None


def _load_pyproject(base: Path) -> dict:
    path = base / "pyproject.toml"
    if not path.is_file():
        return {}
    try:
        with path.open("rb") as handle:
            return tomllib.load(handle)
    except (tomllib.TOMLDecodeError, OSError):
        return {}


def _parse_floor(spec: str) -> tuple[int, int] | None:
    match = _VERSION.search(spec)
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


def _interpreter_floor(
    base: Path, evidence: list[str]
) -> tuple[int, int] | None:
    data = _load_pyproject(base)
    project = data.get("project", {}) if data else {}
    spec = (
        project.get("requires-python") if isinstance(project, dict) else None
    )
    if isinstance(spec, str):
        floor = _parse_floor(spec)
        if floor:
            evidence.append(
                f"floor {floor[0]}.{floor[1]} from requires-python"
            )
            return floor

    version_file = base / ".python-version"
    if version_file.is_file():
        floor = _parse_floor(version_file.read_text(encoding="utf-8"))
        if floor:
            evidence.append(
                f"floor {floor[0]}.{floor[1]} from .python-version"
            )
            return floor

    setup_py = base / "setup.py"
    if setup_py.is_file():
        text = setup_py.read_text(encoding="utf-8", errors="replace")
        match = re.search(r"python_requires\s*=\s*['\"]([^'\"]+)", text)
        if match:
            floor = _parse_floor(match.group(1))
            if floor:
                evidence.append(
                    f"floor {floor[0]}.{floor[1]} "
                    "from setup.py python_requires"
                )
                return floor

    ruff = data.get("tool", {}).get("ruff", {}) if data else {}
    target = ruff.get("target-version") if isinstance(ruff, dict) else None
    if isinstance(target, str):
        match = re.match(r"py(\d)(\d+)", target)
        if match:
            floor = int(match.group(1)), int(match.group(2))
            evidence.append(
                f"floor {floor[0]}.{floor[1]} from tool.ruff.target-version"
            )
            return floor
    return None


def _packaging(base: Path, evidence: list[str]) -> str:
    data = _load_pyproject(base)
    has_project = bool(data) and isinstance(data.get("project"), dict)
    has_lock = any(
        (base / name).is_file() for name in ("uv.lock", "poetry.lock")
    )
    has_setup = (base / "setup.py").is_file() or (base / "setup.cfg").is_file()
    has_requirements = (base / "requirements.txt").is_file()

    if has_project or has_lock:
        evidence.append("modern packaging: pyproject [project] or lockfile")
        if has_setup:
            evidence.append("setup.py or setup.cfg still present")
        return "modern"
    if has_setup or has_requirements:
        evidence.append("legacy packaging: setup.py/setup.cfg/requirements")
        return "legacy"
    return "none"


def _iter_sources(base: Path):
    count = 0
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
        for name in filenames:
            if not name.endswith(".py"):
                continue
            yield Path(dirpath, name)
            count += 1
            if count >= _SAMPLE_LIMIT:
                return


def _code_era(
    base: Path, evidence: list[str]
) -> tuple[int, int, float | None]:
    legacy = 0
    modern = 0
    defs = 0
    annotated = 0
    legacy_hits: dict[str, int] = {}
    modern_hits: dict[str, int] = {}

    for path in _iter_sources(base):
        text = path.read_text(encoding="utf-8", errors="replace")
        for label, pattern in (
            ("py2 print statement", _PY2_PRINT),
            ("__future__ print/unicode import", _PY2_FUTURE),
            ("six/future shim", _PY2_SHIMS),
            ("os.path string surgery", _OSPATH),
            ("% formatting", _PCT_FORMAT),
        ):
            hits = len(pattern.findall(text))
            if hits:
                legacy_hits[label] = legacy_hits.get(label, 0) + hits
        for label, pattern in (
            ("f-strings", _FSTRING),
            ("pathlib", _PATHLIB),
            ("dataclasses", _DATACLASS),
            ("async def", _ASYNC),
        ):
            hits = len(pattern.findall(text))
            if hits:
                modern_hits[label] = modern_hits.get(label, 0) + hits
        for match in _DEF.finditer(text):
            defs += 1
            params, arrow = match.group(1), match.group(2)
            if arrow or ":" in params:
                annotated += 1

    hard_legacy = sum(
        legacy_hits.get(k, 0)
        for k in (
            "py2 print statement",
            "__future__ print/unicode import",
            "six/future shim",
        )
    )
    soft_legacy = sum(
        legacy_hits.get(k, 0)
        for k in ("os.path string surgery", "% formatting")
    )
    legacy = hard_legacy * 10 + soft_legacy
    modern = sum(modern_hits.values())
    ratio = annotated / defs if defs else None

    for label, hits in legacy_hits.items():
        evidence.append(f"legacy code: {label} x{hits}")
    for label, hits in modern_hits.items():
        evidence.append(f"modern code: {label} x{hits}")
    if ratio is not None:
        evidence.append(f"annotated defs: {annotated}/{defs}")
    return legacy, modern, ratio


def _test_runner(base: Path, evidence: list[str]) -> bool:
    data = _load_pyproject(base)
    has_pytest_cfg = bool(data) and "pytest" in data.get("tool", {})
    has_conftest = any(True for _ in base.rglob("conftest.py"))
    if has_pytest_cfg or has_conftest:
        evidence.append("test runner: pytest markers")
        return True
    return False


def _formatting_config(base: Path, evidence: list[str]) -> None:
    data = _load_pyproject(base)
    tool = data.get("tool", {}) if data else {}
    found = [name for name in ("ruff", "black") if name in tool]
    for name in ("setup.cfg", "tox.ini", ".flake8"):
        path = base / name
        if path.is_file() and re.search(
            r"^\[(flake8|pycodestyle)\]",
            path.read_text(encoding="utf-8", errors="replace"),
            re.MULTILINE,
        ):
            found.append(name)
    if (base / ".editorconfig").is_file():
        found.append(".editorconfig")
    if found:
        evidence.append("formatting config: " + ", ".join(found))


def _classify(
    floor: tuple[int, int] | None,
    packaging: str,
    legacy_code: int,
    modern_code: int,
    ratio: float | None,
    modern_tests: bool,
) -> str:
    hard_legacy = legacy_code >= 10
    old_floor = floor is not None and floor < (3, 8)
    if hard_legacy or old_floor:
        if packaging == "modern" and not old_floor:
            return "migration"
        return "legacy"

    modern_floor = floor is not None and floor >= (3, 10)
    typed = ratio is not None and ratio >= 0.5
    legacy_style = legacy_code > modern_code and legacy_code > 0

    if packaging == "modern":
        if legacy_style or (ratio is not None and ratio < 0.5):
            return "migration"
        return "greenfield"
    if packaging == "legacy":
        if modern_code > 0 or typed or modern_tests or modern_floor:
            return "migration"
        return "legacy"
    if legacy_style:
        return "legacy"
    return "greenfield"
