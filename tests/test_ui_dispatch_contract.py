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

    def test_pi_bootstrap_activates_ui_dispatch_skill(self):
        content = (PROJECT_ROOT / "scripts" / "jacazul-pi").read_text()

        self.assertIn("- jacazul-ui\n", content)
        self.assertIn("JACAZUL_HOST", content)
        self.assertIn("jacazul.nvim", content)


if __name__ == "__main__":
    unittest.main()
