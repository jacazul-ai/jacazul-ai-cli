import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

from jacazul.zigexpert.archaeology import scan

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]


def _write(root, relpath, content=""):
    path = pathlib.Path(root, relpath)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


class TestZigEraScan(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="jacazul_zigera_")

    def test_two_argument_casts_and_old_for_loops_are_pre_0_11(self):
        _write(
            self.root,
            "src/main.zig",
            "pub fn main() void {\n"
            "    const x: u16 = 300;\n"
            "    const y = @intCast(u8, x);\n"
            "    for (items) |item, i| { _ = item; _ = i; }\n"
            "    _ = y;\n"
            "}\n",
        )

        report = scan(self.root)

        self.assertEqual(report.era, "0.10")
        self.assertTrue(any("two-argument" in e for e in report.evidence))

    def test_gpa_and_managed_arraylist_are_0_14(self):
        _write(
            self.root,
            "src/main.zig",
            'const std = @import("std");\n'
            "pub fn main() !void {\n"
            "    var gpa = std.heap.GeneralPurposeAllocator(.{}){};\n"
            "    var list = std.ArrayList(u8).init(gpa.allocator());\n"
            "    try list.append(1);\n"
            "}\n",
        )

        report = scan(self.root)

        self.assertEqual(report.era, "0.13")

    def test_writergate_era_without_io_is_0_15(self):
        _write(
            self.root,
            "build.zig.zon",
            '.{ .name = .app, .version = "0.0.0", .fingerprint = 0x1,\n'
            '   .minimum_zig_version = "0.15.1", .paths = .{""} }\n',
        )
        _write(
            self.root,
            "src/main.zig",
            'const std = @import("std");\n'
            "pub fn main() !void {\n"
            "    var buf: [64]u8 = undefined;\n"
            "    var w = std.fs.File.stdout().writer(&buf);\n"
            '    try w.interface.print("{f}", .{x});\n'
            "    try w.interface.flush();\n"
            "}\n",
        )

        report = scan(self.root)

        self.assertEqual(report.era, "0.15")
        self.assertEqual(report.floor, "0.15.1")

    def test_init_main_and_io_are_0_16(self):
        _write(
            self.root,
            "src/main.zig",
            'const std = @import("std");\n'
            "pub fn main(init: std.process.Init) !void {\n"
            "    const io = init.io;\n"
            "    var group: std.Io.Group = .init;\n"
            "    defer group.cancel(io);\n"
            "}\n",
        )

        report = scan(self.root)

        self.assertEqual(report.era, "0.16")

    def test_mixed_markers_report_migration(self):
        _write(
            self.root,
            "src/old.zig",
            'const std = @import("std");\n'
            "var gpa = std.heap.GeneralPurposeAllocator(.{}){};\n",
        )
        _write(
            self.root,
            "src/new.zig",
            'const std = @import("std");\n'
            "pub fn main(init: std.process.Init) !void { _ = init.io; }\n",
        )

        report = scan(self.root)

        self.assertEqual(report.era, "0.16")
        self.assertEqual(report.oldest, "0.13")
        self.assertTrue(report.migration)

    def test_empty_tree_has_no_evidence(self):
        report = scan(self.root)

        self.assertIsNone(report.era)
        self.assertTrue(any("no evidence" in e for e in report.evidence))


class TestZigEraCli(unittest.TestCase):
    def test_prints_era_and_evidence(self):
        root = tempfile.mkdtemp(prefix="jacazul_zigera_cli_")
        _write(root, "src/a.zig", 'const p = @fieldParentPtr(T, "f", ptr);\n')
        env = os.environ.copy()
        env["PYTHONPATH"] = str(PROJECT_ROOT)

        result = subprocess.run(
            [sys.executable, "-m", "jacazul.cli.zigera", root],
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("ZIG_ERA: 0.11", result.stdout)


if __name__ == "__main__":
    unittest.main()
