"""Archaeology scan for JavaScript and TypeScript trees.

Classifies a tree as legacy, greenfield or migration from the markers it
leaves on disk. Pure function over the filesystem; the override chain
(environment, then ``package.json`` ``jacazul.mode``) lives in
``resolve_mode``. No Node toolchain is required.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

MODES = ("legacy", "greenfield", "migration")
ENV_MODE = "JACAZUL_JS_TS_MODE"

_SKIP_DIRS = {
    ".git",
    "node_modules",
    "dist",
    "build",
    "out",
    "coverage",
    ".next",
    ".nuxt",
    ".svelte-kit",
    "vendor",
    "bower_components",
}
_SOURCE_SUFFIXES = {
    ".js",
    ".mjs",
    ".cjs",
    ".jsx",
    ".ts",
    ".mts",
    ".cts",
    ".tsx",
}
_SAMPLE_LIMIT = 300

_LEGACY_DEPS = {
    "jquery": "jquery",
    "grunt": "grunt",
    "gulp": "gulp",
    "bower": "bower",
    "karma": "karma",
    "testee": "testee",
    "steal": "steal (StealJS)",
    "can": "canjs",
    "backbone": "backbone",
    "requirejs": "requirejs",
    "browserify": "browserify",
    "coffee-script": "coffeescript",
    "coffeescript": "coffeescript",
    "phantomjs-prebuilt": "phantomjs",
    "babel-core": "babel 6",
}
_MODERN_DEPS = {
    "typescript": "typescript",
    "vite": "vite",
    "esbuild": "esbuild",
    "vitest": "vitest",
    "prettier": "prettier",
    "@biomejs/biome": "biome",
    "tsx": "tsx",
    "rollup": "rollup",
    "playwright": "playwright",
    "@playwright/test": "playwright",
    "turbo": "turborepo",
}

_REQUIRE = re.compile(r"\brequire\s*\(\s*['\"]", re.MULTILINE)
_MODULE_EXPORTS = re.compile(r"\bmodule\.exports\b|\bexports\.\w+\s*=")
_IMPORT = re.compile(
    r"^\s*import\s+[\w{*\s,]+\s+from\s+['\"]|^\s*import\s+['\"]", re.MULTILINE
)
_EXPORT = re.compile(
    r"^\s*export\s+(default|const|let|function|class|\{|\*)", re.MULTILINE
)
_VAR = re.compile(r"^\s*var\s+\w", re.MULTILINE)
_LET_CONST = re.compile(r"^\s*(let|const)\s+\w", re.MULTILINE)
_PROTOTYPE = re.compile(r"\.prototype\.\w+\s*=")
_ASYNC = re.compile(r"\basync\s+(function|\(|\w+\s*=>|\w+\s*\()")
_JQUERY_CALL = re.compile(r"(?<![\w$])\$\s*\(")


@dataclass
class Report:
    """Result of an archaeology scan."""

    mode: str
    evidence: list[str] = field(default_factory=list)
    legacy_score: int = 0
    modern_score: int = 0
    typed: bool = False
    esm: bool | None = None


def scan(root: str | os.PathLike[str]) -> Report:
    base = Path(root)
    evidence: list[str] = []
    pkg = _load_package_json(base)

    legacy = 0
    modern = 0

    legacy_tooling, modern_tooling = _tooling(base, pkg, evidence)
    legacy += legacy_tooling
    modern += modern_tooling

    typed, strict = _typing(base, pkg, evidence)
    if typed:
        modern += 2 if strict else 1

    esm_declared = pkg.get("type") == "module"
    if esm_declared:
        evidence.append("package.json type=module")
        modern += 1

    cjs, esm, var_count, modern_syntax, legacy_syntax = _code_era(
        base, evidence
    )
    if cjs and not esm:
        legacy += 2
    if esm and not cjs:
        modern += 2
    legacy += legacy_syntax
    modern += modern_syntax

    mode = _classify(
        legacy, modern, cjs, esm, typed, legacy_tooling, modern_tooling
    )
    if not evidence:
        evidence.append(
            "no evidence: empty or unmarked tree, defaulting to greenfield"
        )
    return Report(
        mode=mode,
        evidence=evidence,
        legacy_score=legacy,
        modern_score=modern,
        typed=typed,
        esm=(esm > 0) if (esm or cjs) else None,
    )


def resolve_mode(
    root: str | os.PathLike[str], env: dict[str, str] | None = None
) -> tuple[str, str]:
    """Return ``(mode, source)`` honoring the override chain."""
    env = os.environ if env is None else env
    candidate = env.get(ENV_MODE, "").strip().lower()
    if candidate in MODES:
        return candidate, "env"

    pkg = _load_package_json(Path(root))
    jacazul = pkg.get("jacazul")
    declared = jacazul.get("mode") if isinstance(jacazul, dict) else None
    if isinstance(declared, str) and declared.strip().lower() in MODES:
        return declared.strip().lower(), "package.json"

    return scan(root).mode, "scan"


def _load_package_json(base: Path) -> dict:
    path = base / "package.json"
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def _all_deps(pkg: dict) -> dict[str, str]:
    deps: dict[str, str] = {}
    for key in ("dependencies", "devDependencies", "peerDependencies"):
        section = pkg.get(key)
        if isinstance(section, dict):
            deps.update({k: str(v) for k, v in section.items()})
    return deps


def _tooling(base: Path, pkg: dict, evidence: list[str]) -> tuple[int, int]:
    legacy = 0
    modern = 0
    deps = _all_deps(pkg)

    for name, label in _LEGACY_DEPS.items():
        if name in deps:
            evidence.append(f"legacy tooling: {label}")
            legacy += 2
    if "webpack" in deps:
        major = _major(deps["webpack"])
        if major is not None and major <= 4:
            evidence.append(f"legacy tooling: webpack {major}")
            legacy += 2
        else:
            evidence.append("tooling: webpack 5+")
    for name, label in _MODERN_DEPS.items():
        if name in deps:
            evidence.append(f"modern tooling: {label}")
            modern += 2

    if (base / "bower.json").is_file():
        evidence.append("legacy tooling: bower.json")
        legacy += 3
    for name in ("Gruntfile.js", "gulpfile.js", "karma.conf.js"):
        if (base / name).is_file():
            evidence.append(f"legacy tooling: {name}")
            legacy += 2

    if any(
        (base / name).is_file()
        for name in (
            "eslint.config.js",
            "eslint.config.mjs",
            "eslint.config.cjs",
            "eslint.config.ts",
        )
    ):
        evidence.append("modern tooling: eslint flat config")
        modern += 1
    elif any(base.glob(".eslintrc*")):
        evidence.append("tooling: legacy .eslintrc config")
        legacy += 1

    if (base / "pnpm-lock.yaml").is_file():
        evidence.append("lockfile: pnpm")
        modern += 1
    elif (base / "bun.lock").is_file() or (base / "bun.lockb").is_file():
        evidence.append("lockfile: bun")
        modern += 1
    elif (base / "yarn.lock").is_file():
        evidence.append("lockfile: yarn")
    elif (base / "package-lock.json").is_file():
        version = _lockfile_version(base / "package-lock.json")
        if version is not None and version <= 1:
            evidence.append("lockfile: package-lock v1 (npm 6 era)")
            legacy += 1
        else:
            evidence.append("lockfile: package-lock v2+")

    engines = pkg.get("engines", {})
    node = engines.get("node") if isinstance(engines, dict) else None
    if isinstance(node, str):
        major = _major(node)
        if major is not None:
            evidence.append(f"node floor {major} from engines.node")
            if major < 14:
                legacy += 2
            elif major >= 18:
                modern += 1
    if isinstance(pkg.get("packageManager"), str):
        evidence.append("packageManager pinned")
        modern += 1
    return legacy, modern


def _typing(base: Path, pkg: dict, evidence: list[str]) -> tuple[bool, bool]:
    path = base / "tsconfig.json"
    if not path.is_file():
        return False, False
    strict = False
    try:
        text = path.read_text(encoding="utf-8")
        text = re.sub(r"//[^\n]*|/\*.*?\*/", "", text, flags=re.DOTALL)
        data = json.loads(text)
        options = (
            data.get("compilerOptions", {}) if isinstance(data, dict) else {}
        )
        strict = (
            bool(options.get("strict")) if isinstance(options, dict) else False
        )
    except (json.JSONDecodeError, OSError):
        pass
    evidence.append(
        "typescript: tsconfig.json" + (" strict" if strict else " non-strict")
    )
    return True, strict


def _iter_sources(base: Path):
    count = 0
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
        for name in filenames:
            if Path(name).suffix not in _SOURCE_SUFFIXES:
                continue
            if name.endswith(".min.js"):
                continue
            yield Path(dirpath, name)
            count += 1
            if count >= _SAMPLE_LIMIT:
                return


def _code_era(base: Path, evidence: list[str]):
    cjs = 0
    esm = 0
    var_count = 0
    let_const = 0
    prototype = 0
    async_count = 0
    jquery = 0
    ts_files = 0
    js_files = 0

    for path in _iter_sources(base):
        if path.suffix in {".ts", ".tsx", ".mts", ".cts"}:
            ts_files += 1
        else:
            js_files += 1
        text = path.read_text(encoding="utf-8", errors="replace")
        cjs += len(_REQUIRE.findall(text)) + len(_MODULE_EXPORTS.findall(text))
        esm += len(_IMPORT.findall(text)) + len(_EXPORT.findall(text))
        var_count += len(_VAR.findall(text))
        let_const += len(_LET_CONST.findall(text))
        prototype += len(_PROTOTYPE.findall(text))
        async_count += len(_ASYNC.findall(text))
        jquery += len(_JQUERY_CALL.findall(text))

    if cjs:
        evidence.append(f"module system: CommonJS markers x{cjs}")
    if esm:
        evidence.append(f"module system: ESM markers x{esm}")
    if var_count:
        evidence.append(f"legacy code: var declarations x{var_count}")
    if prototype:
        evidence.append(f"legacy code: prototype assignments x{prototype}")
    if jquery:
        evidence.append(f"legacy code: jQuery calls x{jquery}")
    if async_count:
        evidence.append(f"modern code: async functions x{async_count}")
    if ts_files or js_files:
        evidence.append(f"sources: {ts_files} ts, {js_files} js")

    legacy_syntax = 0
    modern_syntax = 0
    if var_count > let_const and var_count > 0:
        legacy_syntax += 2
    if prototype:
        legacy_syntax += 1
    if jquery:
        legacy_syntax += 1
    if async_count:
        modern_syntax += 1
    if ts_files and ts_files >= js_files:
        modern_syntax += 1
    return cjs, esm, var_count, modern_syntax, legacy_syntax


def _classify(
    legacy: int,
    modern: int,
    cjs: int,
    esm: int,
    typed: bool,
    legacy_tooling: int,
    modern_tooling: int,
) -> str:
    if legacy == 0 and modern == 0:
        return "greenfield"
    if legacy_tooling >= 2 and modern_tooling >= 2:
        return "migration"
    if legacy >= 2 and modern >= 2:
        return "migration"
    if legacy > modern:
        return "legacy"
    if cjs and esm:
        return "migration"
    return "greenfield"


def _major(spec: str) -> int | None:
    match = re.search(r"(\d+)", spec)
    return int(match.group(1)) if match else None


def _lockfile_version(path: Path) -> int | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    value = data.get("lockfileVersion") if isinstance(data, dict) else None
    return int(value) if isinstance(value, int) else None
