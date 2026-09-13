"""Compile and run the zig-expert playbook examples on the installed Zig.

This is the per-release refresh gate: when the toolchain moves, these
examples are the first thing that breaks. Skipped when zig is absent.
"""

import pathlib
import shutil
import subprocess
import unittest

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
EXAMPLES = PROJECT_ROOT / "skills" / "zig-expert" / "examples"
VERSIONS = PROJECT_ROOT / "skills" / "zig-expert" / "VERSIONS.md"
PLAYBOOK = PROJECT_ROOT / "skills" / "zig-expert" / "PLAYBOOK.md"


@unittest.skipUnless(shutil.which("zig"), "zig toolchain not installed")
class TestZigExamplesCompile(unittest.TestCase):
    def test_every_example_passes_zig_test(self):
        examples = sorted(EXAMPLES.glob("*.zig"))
        self.assertTrue(examples, "no examples found")
        for example in examples:
            with self.subTest(example=example.name):
                result = subprocess.run(
                    ["zig", "test", str(example)],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                self.assertEqual(
                    result.returncode,
                    0,
                    msg=f"{example.name}:\n{result.stderr}",
                )

    def test_installed_version_is_on_the_ladder(self):
        version = subprocess.run(
            ["zig", "version"], capture_output=True, text=True, timeout=30
        ).stdout.strip()
        minor = ".".join(version.split(".")[:2])
        ladder = VERSIONS.read_text(encoding="utf-8")
        self.assertIn(
            f"## {minor}",
            ladder,
            msg=(
                f"zig {version} installed but VERSIONS.md has no '## {minor}'"
                " section: run the refresh procedure"
            ),
        )


class TestPlaybookExamplesMirrorFiles(unittest.TestCase):
    def test_playbook_code_blocks_match_example_files(self):
        playbook = PLAYBOOK.read_text(encoding="utf-8")
        for example in sorted(EXAMPLES.glob("*.zig")):
            with self.subTest(example=example.name):
                body = example.read_text(encoding="utf-8").strip()
                self.assertIn(
                    body,
                    playbook,
                    msg=f"{example.name} differs from its playbook block",
                )


if __name__ == "__main__":
    unittest.main()
