"""Compile and run the rust-expert playbook examples on the installed
toolchain. Skipped when rustc is absent."""

import pathlib
import shutil
import subprocess
import tempfile
import unittest

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
EXAMPLES = PROJECT_ROOT / "skills" / "rust-expert" / "examples"
PLAYBOOK = PROJECT_ROOT / "skills" / "rust-expert" / "PLAYBOOK.md"


@unittest.skipUnless(shutil.which("rustc"), "rustc not installed")
class TestRustExamplesCompile(unittest.TestCase):
    def test_every_example_compiles_and_runs(self):
        examples = sorted(EXAMPLES.glob("*.rs"))
        self.assertTrue(examples, "no examples found")
        out_dir = pathlib.Path(tempfile.mkdtemp(prefix="jacazul_rustex_"))
        for example in examples:
            with self.subTest(example=example.name):
                binary = out_dir / example.stem
                build = subprocess.run(
                    [
                        "rustc",
                        "--edition",
                        "2024",
                        "-o",
                        str(binary),
                        str(example),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                self.assertEqual(
                    build.returncode,
                    0,
                    msg=f"{example.name}:\n{build.stderr}",
                )
                run = subprocess.run(
                    [str(binary)],
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                self.assertEqual(run.returncode, 0, msg=run.stderr)
                self.assertIn("ok", run.stdout)


class TestPlaybookExamplesMirrorFiles(unittest.TestCase):
    def test_playbook_code_blocks_match_example_files(self):
        playbook = PLAYBOOK.read_text(encoding="utf-8")
        for example in sorted(EXAMPLES.glob("*.rs")):
            with self.subTest(example=example.name):
                body = example.read_text(encoding="utf-8").strip()
                self.assertIn(
                    body,
                    playbook,
                    msg=f"{example.name} differs from its playbook block",
                )


if __name__ == "__main__":
    unittest.main()
