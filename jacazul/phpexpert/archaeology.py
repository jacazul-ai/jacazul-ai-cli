"""Archaeology scan and construct census for PHP trees.

One marker table drives both the mode scan (legacy, greenfield, migration)
and the census (counts by the PHP version that breaks each construct).
Every marker carries the version that removes, deprecates or introduces
it, so the same table answers "what breaks on the target" and "what is
newer than the production floor". No PHP binary is required; ``php -l``
is used only when asked and available.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

MODES = ("legacy", "greenfield", "migration")
ENV_MODE = "JACAZUL_PHP_MODE"

_SKIP_DIRS = {".git", "vendor", "node_modules", ".idea", "cache", ".cache"}
_SUFFIXES = {".php", ".inc", ".phtml"}
_SAMPLE_LIMIT = 4000


@dataclass(frozen=True)
class Marker:
    label: str
    breaks: str  # PHP version that removes, deprecates or introduces it
    kind: str  # removed | deprecated | modern
    pattern: re.Pattern[str]


def _m(label: str, breaks: str, kind: str, regex: str) -> Marker:
    return Marker(label, breaks, kind, re.compile(regex, re.MULTILINE))


MARKERS: tuple[Marker, ...] = (
    # --- removed in 5.4 / 7.0 ---
    _m(
        "$HTTP_*_VARS superglobals",
        "5.4",
        "removed",
        r"\$HTTP_(?:GET|POST|COOKIE|SERVER|ENV|SESSION|POST_FILES)_VARS\b",
    ),
    _m(
        "register_globals / session_register()",
        "5.4",
        "removed",
        r"\bsession_(?:register|unregister|is_registered)\s*\("
        r"|register_globals",
    ),
    _m("mysql_* extension", "7.0", "removed", r"\bmysql_[a-z_]+\s*\("),
    _m(
        "ereg* / split() / spliti()",
        "7.0",
        "removed",
        r"\b(?:ereg|eregi|ereg_replace|eregi_replace|split|spliti)\s*\(",
    ),
    _m("mssql_* extension", "7.0", "removed", r"\bmssql_[a-z_]+\s*\("),
    _m(
        "&new by-reference construction", "7.0", "removed", r"=\s*&\s*new\s+\w"
    ),
    _m(
        "call_user_method()",
        "7.0",
        "removed",
        r"\bcall_user_method(?:_array)?\s*\(",
    ),
    _m(
        "set_magic_quotes_runtime()",
        "7.0",
        "removed",
        r"\bset_magic_quotes_runtime\s*\(",
    ),
    _m(
        "preg_replace /e modifier",
        "7.0",
        "removed",
        r"preg_replace\s*\(\s*['\"][^'\"]*['\"]\s*[a-z]*e[a-z]*['\"]",
    ),
    _m("ASP-style <% tags", "7.0", "removed", r"<%(?!%)"),
    # --- removed in 8.0 ---
    _m("each()", "8.0", "removed", r"(?<![\w>$])each\s*\("),
    _m("create_function()", "8.0", "removed", r"\bcreate_function\s*\("),
    _m(
        "PHP 4 constructor (method named after its class)",
        "8.0",
        "removed",
        r"__PHP4_CTOR__",
    ),
    _m("__autoload()", "8.0", "removed", r"\bfunction\s+__autoload\s*\("),
    _m("money_format()", "8.0", "removed", r"\bmoney_format\s*\("),
    _m(
        "get_magic_quotes_gpc() / _runtime()",
        "8.0",
        "removed",
        r"\bget_magic_quotes_(?:gpc|runtime)\s*\(",
    ),
    _m("$str{0} curly string offset", "8.0", "removed", r"\$\w+\{\s*\d+\s*\}"),
    _m("(unset) cast", "8.0", "removed", r"\(\s*unset\s*\)"),
    _m(
        "implode() with reversed argument order",
        "8.0",
        "removed",
        r"\bimplode\s*\(\s*\$\w+\s*,\s*['\"]",
    ),
    # --- deprecated in 8.1 ---
    _m(
        "strftime() / gmstrftime()",
        "8.1",
        "deprecated",
        r"\b(?:gm)?strftime\s*\(",
    ),
    _m(
        "FILTER_SANITIZE_STRING",
        "8.1",
        "deprecated",
        r"\bFILTER_SANITIZE_STRING\b",
    ),
    _m(
        "date_sunrise() / date_sunset()",
        "8.1",
        "deprecated",
        r"\bdate_sun(?:rise|set)\s*\(",
    ),
    # --- deprecated in 8.2 ---
    _m(
        "${var} string interpolation",
        "8.2",
        "deprecated",
        r"\$\{[A-Za-z_][\w\[\]'\"]*\}",
    ),
    _m(
        "utf8_encode() / utf8_decode()",
        "8.2",
        "deprecated",
        r"\butf8_(?:en|de)code\s*\(",
    ),
    _m(
        "dynamic property writes ($this->x = ...) to review",
        "8.2",
        "deprecated",
        r"__DYNAMIC_PROP__",
    ),
    # --- deprecated in 8.3 / 8.4 ---
    _m(
        "get_class() / get_parent_class() without argument",
        "8.3",
        "deprecated",
        r"\bget_(?:parent_)?class\s*\(\s*\)",
    ),
    _m(
        "implicitly nullable parameter (Type $x = null)",
        "8.4",
        "deprecated",
        r"\b(?!\?)[A-Z]\w*\s+\$\w+\s*=\s*null\b",
    ),
    _m("E_STRICT", "8.4", "deprecated", r"\bE_STRICT\b"),
    _m(
        "mysqli_ping() / session_set_save_handler() old shape",
        "8.4",
        "deprecated",
        r"\bmysqli_ping\s*\(",
    ),
    # --- modern constructs (version that introduced them) ---
    _m("?? null coalescing", "7.0", "modern", r"\?\?(?!=)"),
    _m(
        "scalar / return type declarations",
        "7.0",
        "modern",
        r"\)\s*:\s*\??(?:int|string|bool|float|array|void|self|static|\\?[A-Z]\w*)\b",
    ),
    _m(
        "[$a, $b] = short list destructuring",
        "7.1",
        "modern",
        r"^\s*\[\s*\$\w+(?:\s*,\s*\$\w+)*\s*\]\s*=",
    ),
    _m("nullable ?Type", "7.1", "modern", r"[\(,]\s*\?[A-Z\\]\w*\s+\$"),
    _m(
        "typed properties",
        "7.4",
        "modern",
        r"\b(?:public|protected|private)\s+(?:readonly\s+)?\??(?:int|string|bool|float|array|[A-Z\\]\w*)\s+\$",
    ),
    _m("fn() arrow functions", "7.4", "modern", r"\bfn\s*\("),
    _m("??= null coalescing assignment", "7.4", "modern", r"\?\?="),
    _m("match expression", "8.0", "modern", r"\bmatch\s*\("),
    _m("?-> nullsafe operator", "8.0", "modern", r"\?->"),
    _m("#[Attribute]", "8.0", "modern", r"^\s*#\[\w"),
    _m(
        "constructor property promotion",
        "8.0",
        "modern",
        r"__construct\s*\([^)]*\b(?:public|protected|private)\s+",
    ),
    _m("enum", "8.1", "modern", r"^\s*(?:final\s+)?enum\s+\w+"),
    _m("readonly", "8.1", "modern", r"\breadonly\s+"),
    _m(
        "declare(strict_types=1)",
        "7.0",
        "modern",
        r"declare\s*\(\s*strict_types\s*=\s*1",
    ),
    _m("namespace", "5.3", "modern", r"^\s*namespace\s+[\w\\]+\s*;"),
)

_CLASS = re.compile(r"\bclass\s+(\w+)\b[^{]*\{")
_DYNAMIC = re.compile(r"\$this->\w+\s*=[^=]")
_DECLARED_PROP = re.compile(
    r"^\s*(?:public|protected|private|var)\s+(?:static\s+)?(?:readonly\s+)?"
    r"(?:\??[\w\\]+\s+)?\$(\w+)",
    re.MULTILINE,
)
_FLOOR = re.compile(r"(\d+)\.(\d+)")


@dataclass
class Row:
    label: str
    breaks: str
    kind: str
    count: int
    files: int


@dataclass
class Report:
    mode: str
    floor: str | None
    evidence: list[str] = field(default_factory=list)
    above_floor: list[str] = field(default_factory=list)
    rows: list[Row] = field(default_factory=list)


def _version_key(v: str) -> tuple[int, int]:
    match = _FLOOR.search(v)
    return (int(match.group(1)), int(match.group(2))) if match else (0, 0)


def _iter_sources(base: Path):
    count = 0
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
        for name in filenames:
            if Path(name).suffix not in _SUFFIXES:
                continue
            yield Path(dirpath, name)
            count += 1
            if count >= _SAMPLE_LIMIT:
                return


def _php4_ctors(text: str) -> int:
    hits = 0
    for cls in _CLASS.findall(text):
        if re.search(r"\bfunction\s+" + re.escape(cls) + r"\s*\(", text, re.I):
            hits += 1
    return hits


def _dynamic_props(text: str) -> int:
    writes = {
        m.group(0).split("->")[1].split("=")[0].strip()
        for m in _DYNAMIC.finditer(text)
    }
    declared = set(_DECLARED_PROP.findall(text))
    return len(writes - declared)


def census(
    root: str | os.PathLike[str], floor: str | None = None
) -> list[Row]:
    """Count every marker across the tree.

    With ``floor`` set, return only modern constructs newer than the floor
    (the bridge check); otherwise return removed and deprecated constructs.
    """
    base = Path(root)
    counts: dict[str, int] = {}
    files: dict[str, int] = {}
    for path in _iter_sources(base):
        text = path.read_text(encoding="utf-8", errors="replace")
        for marker in MARKERS:
            if marker.pattern.pattern == "__PHP4_CTOR__":
                hits = _php4_ctors(text)
            elif marker.pattern.pattern == "__DYNAMIC_PROP__":
                hits = _dynamic_props(text)
            else:
                hits = len(marker.pattern.findall(text))
            if hits:
                counts[marker.label] = counts.get(marker.label, 0) + hits
                files[marker.label] = files.get(marker.label, 0) + 1

    rows: list[Row] = []
    for marker in MARKERS:
        if floor is not None:
            if marker.kind != "modern":
                continue
            if _version_key(marker.breaks) <= _version_key(floor):
                continue
        elif marker.kind == "modern":
            continue
        rows.append(
            Row(
                label=marker.label,
                breaks=marker.breaks,
                kind=marker.kind,
                count=counts.get(marker.label, 0),
                files=files.get(marker.label, 0),
            )
        )
    rows.sort(key=lambda r: (_version_key(r.breaks), r.label))
    return rows


def _composer(base: Path) -> dict:
    path = base / "composer.json"
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def _declared_floor(base: Path, evidence: list[str]) -> str | None:
    data = _composer(base)
    require = data.get("require", {})
    spec = require.get("php") if isinstance(require, dict) else None
    if isinstance(spec, str):
        match = _FLOOR.search(spec)
        if match:
            floor = f"{match.group(1)}.{match.group(2)}"
            evidence.append(f"floor {floor} from composer.json require.php")
            return floor
    config = data.get("config", {})
    platform = config.get("platform", {}) if isinstance(config, dict) else {}
    spec = platform.get("php") if isinstance(platform, dict) else None
    if isinstance(spec, str):
        match = _FLOOR.search(spec)
        if match:
            floor = f"{match.group(1)}.{match.group(2)}"
            evidence.append(f"floor {floor} from composer.json platform.php")
            return floor
    version_file = base / ".php-version"
    if version_file.is_file():
        match = _FLOOR.search(version_file.read_text(encoding="utf-8"))
        if match:
            floor = f"{match.group(1)}.{match.group(2)}"
            evidence.append(f"floor {floor} from .php-version")
            return floor
    return None


def _ecosystem(base: Path, evidence: list[str]) -> None:
    if (base / "wp-config.php").is_file() or (base / "wp-content").is_dir():
        evidence.append("ecosystem: WordPress present (evidence only)")
    if (base / "artisan").is_file():
        evidence.append("ecosystem: Laravel present (evidence only)")
    if (base / "symfony.lock").is_file():
        evidence.append("ecosystem: Symfony present (evidence only)")
    data = _composer(base)
    if data:
        evidence.append("packaging: composer.json present")
        autoload = data.get("autoload", {})
        if isinstance(autoload, dict) and "psr-4" in autoload:
            evidence.append("packaging: PSR-4 autoload")
    else:
        evidence.append("packaging: no composer.json")


def scan(root: str | os.PathLike[str]) -> Report:
    base = Path(root)
    evidence: list[str] = []
    floor = _declared_floor(base, evidence)
    _ecosystem(base, evidence)

    legacy_rows = [r for r in census(base) if r.count]
    modern_rows = [r for r in _modern_rows(base) if r.count]

    for row in legacy_rows:
        evidence.append(
            f"{row.kind} in {row.breaks}: {row.label} x{row.count} "
            f"({row.files} files)"
        )
    for row in modern_rows:
        evidence.append(f"modern since {row.breaks}: {row.label} x{row.count}")

    above: list[str] = []
    if floor:
        for row in modern_rows:
            if _version_key(row.breaks) > _version_key(floor):
                above.append(f"{row.label} needs {row.breaks}")
        if above:
            evidence.append(
                f"syntax above declared floor {floor}: " + "; ".join(above)
            )

    removed = [r for r in legacy_rows if r.kind == "removed"]
    deprecated = [r for r in legacy_rows if r.kind == "deprecated"]
    floor_key = _version_key(floor) if floor else None
    modern_floor = floor_key is not None and floor_key >= (8, 0)

    if removed:
        mode = "migration" if (modern_rows or modern_floor) else "legacy"
    elif modern_rows and (modern_floor or not deprecated):
        mode = "greenfield" if not deprecated else "migration"
    elif deprecated:
        mode = "legacy"
    else:
        mode = "greenfield"
        if not modern_rows and not floor:
            evidence.append(
                "no evidence: no era markers found, defaulting to greenfield"
            )

    return Report(
        mode=mode,
        floor=floor,
        evidence=evidence,
        above_floor=above,
        rows=legacy_rows,
    )


def _modern_rows(base: Path) -> list[Row]:
    counts: dict[str, int] = {}
    files: dict[str, int] = {}
    for path in _iter_sources(base):
        text = path.read_text(encoding="utf-8", errors="replace")
        for marker in MARKERS:
            if marker.kind != "modern":
                continue
            hits = len(marker.pattern.findall(text))
            if hits:
                counts[marker.label] = counts.get(marker.label, 0) + hits
                files[marker.label] = files.get(marker.label, 0) + 1
    rows = [
        Row(
            m.label,
            m.breaks,
            m.kind,
            counts.get(m.label, 0),
            files.get(m.label, 0),
        )
        for m in MARKERS
        if m.kind == "modern"
    ]
    rows.sort(key=lambda r: (_version_key(r.breaks), r.label))
    return rows


def resolve_mode(
    root: str | os.PathLike[str], env: dict[str, str] | None = None
) -> tuple[str, str]:
    env = os.environ if env is None else env
    candidate = env.get(ENV_MODE, "").strip().lower()
    if candidate in MODES:
        return candidate, "env"
    extra = _composer(Path(root)).get("extra", {})
    jacazul = extra.get("jacazul", {}) if isinstance(extra, dict) else {}
    declared = jacazul.get("mode") if isinstance(jacazul, dict) else None
    if isinstance(declared, str) and declared.strip().lower() in MODES:
        return declared.strip().lower(), "composer.json"
    return scan(root).mode, "scan"


def lint(root: str | os.PathLike[str], php: str = "php") -> list[str]:
    """Run ``php -l`` over the tree with the given binary; return the
    failing lines. Empty list when php is missing or everything parses."""
    binary = shutil.which(php)
    if not binary:
        return [f"php binary not found: {php}"]
    failures: list[str] = []
    for path in _iter_sources(Path(root)):
        res = subprocess.run(
            [binary, "-l", str(path)], capture_output=True, text=True
        )
        if res.returncode != 0:
            line = (res.stderr or res.stdout).strip().splitlines()
            failures.append(line[0] if line else f"{path}: lint failed")
    return failures
