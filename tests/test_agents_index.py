import re
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENTS = PROJECT_ROOT / "AGENTS.md"
# Repository mandates no skill carries; they must survive any slimming.
MANDATES = (
    "scripts/configure",
    "Silent by Default",
    "DRY=true",
    "MUST NOT invoke the raw `task` binary",
    "`rtask`",
    "NEVER edit generated files directly",
    "jacazul-hatch --target <target>",
    "docs/skill-methodology.md",
    "`OUTCOME:` annotation",
    "base system primitives",
    "load on demand",
    "`uuid description [plan-name]`",
    "Terminei a tarefa <uuid> <desc> [<plan>]",
    "vaccinating",
    "`make test`",
    "tests/test_suite_contract.py",
    "Implementation → Test → Docs",
    "jacazul-ai/jacazul-ai-sandbox",
    "`jacazul-broker`",
)
# Rules the engine hub owns; AGENTS.md names where they live instead.
POINTERS = (
    '"Context Orientation"',
    '"Persona Protocol"',
    '"Core Principles"',
    "docs/README.md",
)
GIT_WORKFLOW = """## Git Workflow

Pinned for `git-expert` and `git-mode`: topic work is rebased onto the
reference branch and fast-forwarded, so history stays linear.

- integration: linear
- reference: master
"""


class AgentsIndexTest(unittest.TestCase):
    """AGENTS.md keeps repository mandates and points at the rest."""

    def setUp(self):
        raw = AGENTS.read_text(encoding="utf-8")
        self.raw = raw
        self.text = " ".join(raw.split())

    def test_keeps_every_repository_mandate(self):
        for mandate in MANDATES:
            self.assertIn(" ".join(mandate.split()), self.text, mandate)

    def test_points_at_what_the_engine_owns(self):
        for pointer in POINTERS:
            self.assertIn(pointer, self.text, pointer)
        self.assertNotIn("Jacazul/Codana", self.text)
        self.assertNotIn("### 2. Documentation Map", self.raw)

    def test_git_workflow_stays_verbatim(self):
        # git-mode parses this block.
        self.assertIn(GIT_WORKFLOW, self.raw)

    def test_stays_lean(self):
        self.assertLess(len(self.raw.encode("utf-8")), 10_000)

    def test_docs_index_owns_the_documentation_map(self):
        docs_index = (PROJECT_ROOT / "docs" / "README.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("## 🗺️ Documentation Map", docs_index)
        self.assertIn("| `docs/ARCHITECTURE.md` | Contributors |", docs_index)
        self.assertIn("Trigger → Action", docs_index)

    def test_engine_uses_the_same_task_reference_format(self):
        templates = PROJECT_ROOT / "jacazul" / "hatch" / "templates"
        logic = (templates / "core" / "logic.md").read_text(encoding="utf-8")
        self.assertIn("`uuid description [plan-name]`", logic)
        self.assertIsNone(re.search(r"fa145ef2 - Task description", logic))


if __name__ == "__main__":
    unittest.main()
