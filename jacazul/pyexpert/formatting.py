"""Formatting protocol: resolve line length and the ignore guard.

Resolution order for line length: explicit flag, ``JACAZUL_PY_LINE_LENGTH``,
project configuration (``[tool.ruff]``, ``[tool.black]``,
``[flake8]``/``[pycodestyle]`` in setup.cfg/tox.ini/.flake8,
``.editorconfig``), then the house default of 79.
"""

from __future__ import annotations

import configparser
import os
import tomllib
from pathlib import Path

HOUSE_LINE_LENGTH = 79
ENV_LINE_LENGTH = "JACAZUL_PY_LINE_LENGTH"
ENV_IGNORE = "JACAZUL_PY_IGNORE_FORMATTING"
_TRUTHY = {"1", "true", "yes", "on"}


def resolve_line_length(
    root: str | os.PathLike[str],
    flag: int | None,
    env: dict[str, str] | None = None,
) -> tuple[int, str]:
    """Return ``(line_length, source)``."""
    env = os.environ if env is None else env
    if flag is not None:
        return int(flag), "flag"

    raw = env.get(ENV_LINE_LENGTH, "").strip()
    if raw.isdigit():
        return int(raw), "env"

    base = Path(root)
    from_project = _project_line_length(base)
    if from_project is not None:
        return from_project

    return HOUSE_LINE_LENGTH, "default"


def has_formatter_config(root: str | os.PathLike[str]) -> bool:
    """True when the tree declares a formatter or style configuration."""
    return _project_line_length(Path(root)) is not None or _has_tool(
        Path(root), ("ruff", "black")
    )


def ignore_formatting(
    mode: str,
    root: str | os.PathLike[str],
    env: dict[str, str] | None = None,
) -> bool:
    """True when py-check must skip every writing phase."""
    env = os.environ if env is None else env
    if env.get(ENV_IGNORE, "").strip().lower() in _TRUTHY:
        return True
    return mode == "legacy" and not has_formatter_config(root)


def _load_pyproject(base: Path) -> dict:
    path = base / "pyproject.toml"
    if not path.is_file():
        return {}
    try:
        with path.open("rb") as handle:
            return tomllib.load(handle)
    except (tomllib.TOMLDecodeError, OSError):
        return {}


def _has_tool(base: Path, names: tuple[str, ...]) -> bool:
    tool = _load_pyproject(base).get("tool", {})
    return isinstance(tool, dict) and any(name in tool for name in names)


def _project_line_length(base: Path) -> tuple[int, str] | None:
    tool = _load_pyproject(base).get("tool", {})
    if isinstance(tool, dict):
        for name in ("ruff", "black"):
            section = tool.get(name)
            if isinstance(section, dict):
                value = section.get("line-length")
                if isinstance(value, int):
                    return value, "pyproject.toml"

    for name in ("setup.cfg", "tox.ini", ".flake8"):
        value = _ini_line_length(base / name)
        if value is not None:
            return value, name

    value = _editorconfig_line_length(base / ".editorconfig")
    if value is not None:
        return value, ".editorconfig"
    return None


def _ini_line_length(path: Path) -> int | None:
    if not path.is_file():
        return None
    parser = configparser.ConfigParser()
    try:
        parser.read(path, encoding="utf-8")
    except configparser.Error:
        return None
    for section in ("flake8", "pycodestyle"):
        if parser.has_section(section):
            for key in ("max-line-length", "max_line_length"):
                raw = parser.get(section, key, fallback="").strip()
                if raw.isdigit():
                    return int(raw)
    return None


def _editorconfig_line_length(path: Path) -> int | None:
    if not path.is_file():
        return None
    parser = configparser.ConfigParser(strict=False)
    try:
        # .editorconfig allows top-level keys (root = true) before any
        # section; give them a synthetic section so configparser accepts it.
        parser.read_string(
            "[__preamble__]\n" + path.read_text(encoding="utf-8")
        )
    except (configparser.Error, OSError):
        return None
    for section in ("*.py", "*.{py}", "*"):
        if parser.has_section(section):
            raw = parser.get(section, "max_line_length", fallback="").strip()
            if raw.isdigit():
                return int(raw)
    return None
