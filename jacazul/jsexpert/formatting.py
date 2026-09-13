"""Indentation protocol and ignore guard for JavaScript/TypeScript trees.

Indent resolution order: explicit flag, ``JACAZUL_JS_TS_INDENT``, project
configuration (``.editorconfig``, ``.prettierrc*``, ``prettier`` key in
``package.json``), then the explicit house preference of 4 spaces.
"""

from __future__ import annotations

import configparser
import json
import os
from pathlib import Path

HOUSE_INDENT = ("space", 4)
ENV_INDENT = "JACAZUL_JS_TS_INDENT"
ENV_IGNORE = "JACAZUL_JS_TS_IGNORE_FORMATTING"
_TRUTHY = {"1", "true", "yes", "on"}
_PRETTIER_FILES = (
    ".prettierrc",
    ".prettierrc.json",
    ".prettierrc.yaml",
    ".prettierrc.yml",
    ".prettierrc.toml",
    ".prettierrc.js",
    ".prettierrc.cjs",
    ".prettierrc.mjs",
    "prettier.config.js",
    "prettier.config.cjs",
    "prettier.config.mjs",
)
_BIOME_FILES = ("biome.json", "biome.jsonc")


def resolve_indent(
    root: str | os.PathLike[str],
    flag: int | None,
    env: dict[str, str] | None = None,
) -> tuple[str, int, str]:
    """Return ``(style, size, source)``; style is ``space`` or ``tab``."""
    env = os.environ if env is None else env
    if flag is not None:
        return "space", int(flag), "flag"

    raw = env.get(ENV_INDENT, "").strip().lower()
    if raw == "tab":
        return "tab", 4, "env"
    if raw.isdigit():
        return "space", int(raw), "env"

    base = Path(root)
    for resolver in (_editorconfig, _prettierrc, _package_json_prettier):
        found = resolver(base)
        if found is not None:
            return found
    return HOUSE_INDENT[0], HOUSE_INDENT[1], "default"


def has_formatter_config(root: str | os.PathLike[str]) -> bool:
    base = Path(root)
    if any((base / name).is_file() for name in _PRETTIER_FILES):
        return True
    if any((base / name).is_file() for name in _BIOME_FILES):
        return True
    pkg = _load_package_json(base)
    return isinstance(pkg.get("prettier"), (dict, str))


def ignore_formatting(
    mode: str,
    root: str | os.PathLike[str],
    env: dict[str, str] | None = None,
) -> bool:
    env = os.environ if env is None else env
    if env.get(ENV_IGNORE, "").strip().lower() in _TRUTHY:
        return True
    return mode == "legacy" and not has_formatter_config(root)


def _load_package_json(base: Path) -> dict:
    path = base / "package.json"
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def _from_prettier_options(
    options: dict, source: str
) -> tuple[str, int, str] | None:
    use_tabs = options.get("useTabs")
    width = options.get("tabWidth")
    if use_tabs is True:
        return "tab", int(width) if isinstance(width, int) else 4, source
    if isinstance(width, int):
        return "space", width, source
    return None


def _prettierrc(base: Path) -> tuple[str, int, str] | None:
    for name in (".prettierrc", ".prettierrc.json"):
        path = base / name
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if isinstance(data, dict):
            found = _from_prettier_options(data, name)
            if found:
                return found
    return None


def _package_json_prettier(base: Path) -> tuple[str, int, str] | None:
    options = _load_package_json(base).get("prettier")
    if isinstance(options, dict):
        return _from_prettier_options(options, "package.json")
    return None


def _editorconfig(base: Path) -> tuple[str, int, str] | None:
    path = base / ".editorconfig"
    if not path.is_file():
        return None
    parser = configparser.ConfigParser(strict=False)
    try:
        parser.read_string(
            "[__preamble__]\n" + path.read_text(encoding="utf-8")
        )
    except (configparser.Error, OSError):
        return None
    for section in parser.sections():
        if section == "__preamble__":
            continue
        if not _section_covers_js(section):
            continue
        style = parser.get(section, "indent_style", fallback="").strip()
        size = parser.get(section, "indent_size", fallback="").strip()
        if style == "tab":
            return "tab", int(size) if size.isdigit() else 4, ".editorconfig"
        if size.isdigit():
            return "space", int(size), ".editorconfig"
    return None


def _section_covers_js(section: str) -> bool:
    if section == "*":
        return True
    body = section.strip("[]")
    if "{" in body:
        start = body.index("{") + 1
        end = body.rindex("}")
        inner = body[start:end]
        return any(
            part.strip() in {"js", "ts", "jsx", "tsx", "mjs", "cjs"}
            for part in inner.split(",")
        )
    return body in {"*.js", "*.ts", "*.jsx", "*.tsx", "*.mjs", "*.cjs"}
