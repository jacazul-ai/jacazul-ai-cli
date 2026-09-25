import pathlib
import unittest


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]


class TestUiDispatchContract(unittest.TestCase):
    def test_skill_requires_immediate_alert_routing(self):
        content = (
            PROJECT_ROOT / "skills" / "jacazul-ui" / "SKILL.md"
        ).read_text()

        self.assertIn("call `jacazul_alert` immediately", content)
        self.assertIn("me manda um alert", content)

    def test_pi_extension_reinforces_immediate_alert_routing(self):
        content = (
            PROJECT_ROOT / "extensions" / "pi" / "jacazul-ui.ts"
        ).read_text()

        self.assertIn("call jacazul_alert immediately", content)
        self.assertIn("Never use tmux", content)
        self.assertIn("running inside jacazul.nvim", content)

    def test_pi_loads_ui_skill_only_with_a_host_ui(self):
        content = (PROJECT_ROOT / "scripts" / "jacazul-pi").read_text()
        block = content.split("## 🛑 MANDATORY: SKILL ACTIVATION", 1)[1]
        first_list = block.split("\n\n", 1)[0]

        # Terminal sessions have no host UI, so the skill is conditional.
        self.assertNotIn("- jacazul-ui", first_list)
        self.assertIn('export JACAZUL_UI="1"', content)
        self.assertIn("jacazul.nvim", content)
        self.assertIn("Load jacazul-ui in the first turn", content)
        # The extension owns the Neovim host guidance; no second copy.
        self.assertNotIn("## Active host", content)

    def test_pi_extension_guidance_needs_a_host_ui(self):
        content = (
            PROJECT_ROOT / "extensions" / "pi" / "jacazul-ui.ts"
        ).read_text()

        self.assertIn('process.env.JACAZUL_UI === "1"', content)
        self.assertIn("if (!HAS_HOST_UI)", content)
        # The alert contract jacazul.nvim relies on stays unchanged.
        self.assertIn('name: "jacazul_alert"', content)
        self.assertIn("ctx.ui.notify(input.message", content)

    def test_ui_skill_is_limited_to_pi(self):
        skill_dir = PROJECT_ROOT / "skills" / "jacazul-ui"
        hosts = (skill_dir / "HOSTS").read_text().split()
        description = (skill_dir / "SKILL.md").read_text().split("\n")[2]

        self.assertEqual(hosts, ["pi"])
        self.assertIn("jacazul_alert", description)
        self.assertIn("pi", description)
        for harness in ("claude", "gemini", "copilot", "opencode"):
            bootstrap = (
                PROJECT_ROOT / "scripts" / "bootstrap" / harness
            ).read_text()
            self.assertIn('"$skill_dir/HOSTS"', bootstrap, harness)


if __name__ == "__main__":
    unittest.main()
