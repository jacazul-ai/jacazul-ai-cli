#!/home/fpiraz/.jacazul-ai/.venv/bin/python
import os
import shutil
import subprocess
import tempfile
import unittest

from jacazul.cli.hatch import build_parser
from jacazul.hatch.engine import hatch_prompt
from jacazul.hatch.persona import PersonaManager


class TestHatchEngine(unittest.TestCase):
    def setUp(self):
        self.test_root = tempfile.mkdtemp()
        self.script_dir = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )
        # We need to mock the PROJECT_ROOT logic in hatch.py or set environment
        os.environ["PROJECT_ID"] = "test_project"

        # hatch.py uses script_dir for loader, so we just check outputs
        self.manager = PersonaManager(data_dir=self.test_root)

    def tearDown(self):
        shutil.rmtree(self.test_root)

    def test_cli_accepts_hatch_targets(self):
        parser = build_parser()

        for target in ("pi", "openai", "all"):
            args = parser.parse_args(["--target", target])
            self.assertEqual(args.target, target)

        legacy_args = parser.parse_args(["--client", "pi"])
        self.assertEqual(legacy_args.target, "pi")

    def test_all_hatches_shared_engine_and_real_adapters(self):
        legacy_agent = os.path.join(
            self.test_root,
            "agents",
            "arnalbam-opencode.md",
        )
        os.makedirs(os.path.dirname(legacy_agent), exist_ok=True)
        with open(legacy_agent, "w", encoding="utf-8") as agent_file:
            agent_file.write("legacy generated artifact")

        hatch_prompt(
            "all",
            persona_override="arnalbam",
            output_root=self.test_root,
        )

        skill_path = os.path.join(
            self.test_root,
            "skills",
            "jacazul-engine",
            "SKILL.md",
        )
        self.assertTrue(os.path.isfile(skill_path))

        copilot_agent = os.path.join(
            self.test_root,
            "agents",
            "arnalbam-copilot.md",
        )
        self.assertTrue(os.path.isfile(copilot_agent))

        opencode_agent = os.path.join(
            self.test_root,
            "agents",
            "jacazul-opencode.md",
        )
        self.assertTrue(os.path.isfile(opencode_agent))
        with open(opencode_agent, encoding="utf-8") as agent_file:
            self.assertIn("{💪} Arnalbam", agent_file.read())
        self.assertFalse(
            os.path.exists(
                os.path.join(self.test_root, "agents", "arnalbam-opencode.md")
            )
        )

        for target in ("pi", "openai"):
            agent_path = os.path.join(
                self.test_root,
                "agents",
                f"arnalbam-{target}.md",
            )
            self.assertFalse(os.path.exists(agent_path))

    def test_hatch_renders_broker_safety_contract(self):
        hatch_prompt(
            "pi",
            persona_override="jacazul",
            output_root=self.test_root,
        )

        skill_path = os.path.join(
            self.test_root,
            "skills",
            "jacazul-engine",
            "SKILL.md",
        )
        with open(skill_path, encoding="utf-8") as skill_file:
            rendered_skill = skill_file.read()

        self.assertIn("never raw `gh`", rendered_skill)
        self.assertIn("Explicit ticket format", rendered_skill)
        self.assertIn("do not bypass the vault", rendered_skill)

    def test_bootstrap_uses_runtime_target_once(self):
        fake_bin = os.path.join(
            self.test_root,
            ".jacazul-ai",
            ".venv",
            "bin",
            "jacazul-hatch",
        )
        capture_path = os.path.join(self.test_root, "hatch-args")
        os.makedirs(os.path.dirname(fake_bin), exist_ok=True)
        with open(fake_bin, "w", encoding="utf-8") as fake_hatch:
            fake_hatch.write(
                f"#!/bin/sh\nprintf '%s\\n' \"$@\" > '{capture_path}'\n"
            )
        os.chmod(fake_bin, 0o700)

        env = os.environ.copy()
        env["HOME"] = self.test_root
        env["JACAZUL_HARNESS"] = "pi"
        subprocess.run(
            ["bash", os.path.join(self.script_dir, "scripts/bootstrap/hatch")],
            check=True,
            env=env,
            capture_output=True,
            text=True,
        )

        with open(capture_path, encoding="utf-8") as capture:
            self.assertEqual(capture.read().splitlines(), ["--target", "pi"])

    def test_hatch_gemini_parity(self):
        # This is more of an integration test
        # We check if artifacts are created in the right place
        # The actual hatch.py uses root_dir = script_dir/../..
        # For testing purposes, we'll just run it and check if it crashes
        try:
            hatch_prompt("gemini", persona_override="jacazul")
            hatch_prompt("copilot", persona_override="codana")
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"Hatching failed: {e}")

    def test_hatch_includes_active_persona_authority(self):
        hatch_prompt("gemini", persona_override="arnalbam")

        skill_path = os.path.join(
            self.script_dir,
            "skills",
            "jacazul-engine",
            "SKILL.md",
        )
        with open(skill_path, encoding="utf-8") as skill_file:
            rendered_skill = skill_file.read()

        self.assertIn("## Active Persona Authority", rendered_skill)
        self.assertIn("JACAZUL_PERSONA", rendered_skill)
        self.assertIn("never blend their voices", rendered_skill)

    def test_hatch_includes_handoff_visibility_contract(self):
        hatch_prompt("gemini", persona_override="arnalbam")

        skill_path = os.path.join(
            self.script_dir,
            "skills",
            "jacazul-engine",
            "SKILL.md",
        )
        with open(skill_path, encoding="utf-8") as skill_file:
            rendered_skill = skill_file.read()

        self.assertIn("## HANDOFF VISIBILITY CONTRACT", rendered_skill)
        self.assertIn("focused plan and task", rendered_skill)
        self.assertIn("Never say only `context loaded`", rendered_skill)


if __name__ == "__main__":
    unittest.main()
