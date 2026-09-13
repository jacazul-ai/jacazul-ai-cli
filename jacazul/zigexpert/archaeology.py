"""Era scan for Zig trees.

Reads the markers listed in skills/zig-expert/VERSIONS.md and names the
newest era the code targets, the oldest marker still present, and the
declared floor from build.zig.zon. No Zig toolchain is required.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

_SKIP_DIRS = {".git", ".zig-cache", "zig-cache", "zig-out", "vendor"}
_SAMPLE_LIMIT = 300

# Ordered oldest to newest. An "until" marker names the newest era in
# which the construct was still current (an upper bound on the tree's
# target); a "since" marker names the first era where it exists (a lower
# bound). A lower bound above the upper bound means a migration.
_ERAS = ("0.10", "0.11", "0.12", "0.13", "0.14", "0.15", "0.16")
_SINCE = {"0.16"}

_MARKERS: list[tuple[str, str, re.Pattern[str]]] = [
    (
        "0.10",
        "two-argument cast builtin (@intCast(T, x))",
        re.compile(
            r"@(?:intCast|ptrCast|truncate|bitCast|floatCast)"
            r"\s*\(\s*[\w.*\[\]]+\s*,"
        ),
    ),
    (
        "0.10",
        "pre-0.11 cast name (@boolToInt, @intToFloat, ...)",
        re.compile(
            r"@(?:boolToInt|intToFloat|floatToInt|intToPtr|ptrToInt"
            r"|enumToInt|intToEnum)\b"
        ),
    ),
    (
        "0.10",
        "for loop with implicit index capture",
        # A `0..` range operand inside the parentheses is the 0.11+ form.
        re.compile(r"\bfor\s*\((?:(?!\.\.)[^)])*\)\s*\|\s*\w+\s*,\s*\w+\s*\|"),
    ),
    (
        "0.10",
        "std.build.Builder / setBuildMode",
        re.compile(
            r"std\.build\.Builder|\.setBuildMode\(|standardReleaseOptions\("
        ),
    ),
    (
        "0.11",
        "std.os POSIX call (moved to std.posix in 0.12)",
        re.compile(
            r"\bstd\.os\.(?:abort|exit|write|read|open|close|getenv"
            r"|linux|windows)\b"
        ),
    ),
    (
        "0.11",
        "three-argument @fieldParentPtr",
        re.compile(r"@fieldParentPtr\s*\(\s*[\w.]+\s*,\s*\""),
    ),
    ("0.11", "@fabs / @errSetCast", re.compile(r"@(?:fabs|errSetCast)\b")),
    (
        "0.12",
        ".{ .path = } / LazyPath.relative in build.zig",
        re.compile(r"\.\{\s*\.path\s*=|LazyPath\.relative\("),
    ),
    (
        "0.12",
        "std.ChildProcess / std.rand / ComptimeStringMap",
        re.compile(
            r"\bstd\.ChildProcess\b|\bstd\.rand\.|\bComptimeStringMap\b"
        ),
    ),
    (
        "0.13",
        "std.heap.GeneralPurposeAllocator",
        re.compile(r"GeneralPurposeAllocator\s*\("),
    ),
    (
        "0.13",
        "callconv(.C) / @setCold / @export without &",
        re.compile(r"callconv\(\.C\)|@setCold\(|@export\(\s*[A-Za-z_]"),
    ),
    (
        "0.13",
        "capitalized std.builtin.Type field (.Int, .Struct)",
        re.compile(r"\.(?:Int|Struct|Pointer|Enum|Union|Fn|Optional)\s*=>"),
    ),
    (
        "0.13",
        "addExecutable with root_source_file (no root_module)",
        re.compile(r"addExecutable\s*\(\s*\.\{[^}]*root_source_file"),
    ),
    ("0.14", "usingnamespace", re.compile(r"\busingnamespace\b")),
    (
        "0.14",
        "managed ArrayList (.init(allocator) / append(x))",
        re.compile(r"ArrayList\s*\([^)]*\)\s*\.init\s*\("),
    ),
    (
        "0.14",
        "std.io.getStdOut / BufferedWriter",
        re.compile(
            r"std\.io\.getStd(?:Out|Err|In)\(|BufferedWriter\b"
            r"|std\.io\.bufferedWriter\("
        ),
    ),
    ("0.14", "std.BoundedArray", re.compile(r"\bstd\.BoundedArray\b")),
    (
        "0.15",
        "std.fs.cwd / std.fs.File (moved to std.Io in 0.16)",
        re.compile(r"\bstd\.fs\.(?:cwd\(|File\b|Dir\b|openFileAbsolute)"),
    ),
    (
        "0.15",
        "std.Thread.Mutex (moved to std.Io.Mutex in 0.16)",
        re.compile(r"\bstd\.Thread\.(?:Mutex|Condition|RwLock|Semaphore)\b"),
    ),
    (
        "0.15",
        "@Type(...) (split into @Int/@Struct in 0.16)",
        re.compile(r"@Type\s*\("),
    ),
    (
        "0.15",
        "pub fn main() without std.process.Init",
        re.compile(r"pub\s+fn\s+main\s*\(\s*\)"),
    ),
    ("0.15", "std.io namespace", re.compile(r"\bstd\.io\.")),
    ("0.15", "@cImport (deprecated in 0.16)", re.compile(r"@cImport\s*\(")),
    (
        "0.16",
        "main(init: std.process.Init)",
        re.compile(r"pub\s+fn\s+main\s*\(\s*\w+\s*:\s*std\.process\.Init"),
    ),
    (
        "0.16",
        "std.Io interface (Io.Dir, Io.File, Io.Mutex, Io.Group)",
        re.compile(
            r"\bstd\.Io\.(?:Dir|File|Mutex|Group|Future|Batch|Writer|Reader)\b"
            r"|\bIo\.(?:Group|File|Dir|Mutex)\b"
        ),
    ),
    (
        "0.16",
        "type builtins (@Int, @Struct, ...)",
        re.compile(r"@(?:Int|Struct|Union|Enum|Pointer|Fn|Tuple)\s*\("),
    ),
    ("0.16", "b.addTranslateC", re.compile(r"addTranslateC\s*\(")),
]

_FLOOR = re.compile(r"\.minimum_zig_version\s*=\s*\"([^\"]+)\"")
_ZON_NAME_STRING = re.compile(r"\.name\s*=\s*\"")
_ZON_FINGERPRINT = re.compile(r"\.fingerprint\s*=")


@dataclass
class Report:
    era: str | None
    oldest: str | None
    floor: str | None
    migration: bool
    evidence: list[str] = field(default_factory=list)


def scan(root: str | os.PathLike[str]) -> Report:
    base = Path(root)
    evidence: list[str] = []
    hits: dict[str, int] = {}

    floor = _floor(base, evidence)

    for path in _iter_sources(base):
        text = path.read_text(encoding="utf-8", errors="replace")
        for era, label, pattern in _MARKERS:
            count = len(pattern.findall(text))
            if count:
                hits[era] = hits.get(era, 0) + count
                evidence.append(f"{era}: {label} x{count} ({path.name})")

    if not hits:
        evidence.append("no evidence: no era markers found in sources")
        return Report(
            era=None,
            oldest=None,
            floor=floor,
            migration=False,
            evidence=evidence,
        )

    until = [era for era in _ERAS if era in hits and era not in _SINCE]
    since = [era for era in _ERAS if era in hits and era in _SINCE]
    upper = until[0] if until else None
    lower = since[-1] if since else None

    if upper and lower and _ERAS.index(lower) > _ERAS.index(upper):
        evidence.append(
            f"mixed markers: constructs current until {upper} next to "
            f"constructs that exist since {lower}: migration in progress"
        )
        return Report(
            era=lower,
            oldest=upper,
            floor=floor,
            migration=True,
            evidence=evidence,
        )
    era = upper or lower
    return Report(
        era=era, oldest=era, floor=floor, migration=False, evidence=evidence
    )


def _floor(base: Path, evidence: list[str]) -> str | None:
    zon = base / "build.zig.zon"
    if not zon.is_file():
        return None
    text = zon.read_text(encoding="utf-8", errors="replace")
    match = _FLOOR.search(text)
    floor = match.group(1) if match else None
    if floor:
        evidence.append(f"floor {floor} from build.zig.zon")
    if _ZON_NAME_STRING.search(text) and not _ZON_FINGERPRINT.search(text):
        evidence.append(
            "0.13: build.zig.zon with string .name and no .fingerprint"
        )
    return floor


def _iter_sources(base: Path):
    count = 0
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
        for name in filenames:
            if not name.endswith(".zig"):
                continue
            yield Path(dirpath, name)
            count += 1
            if count >= _SAMPLE_LIMIT:
                return
