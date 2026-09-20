"""Guards for the upstream provenance record.

The go-expert skill adapts material from an MIT-licensed upstream project.
Attribution and the reviewed pin are the kind of content that quietly
disappears in a later edit, so they are asserted rather than trusted.
"""

import pathlib
import unittest


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
DOCS = PROJECT_ROOT / "docs" / "go-expert.md"

UPSTREAM_PIN = "19a0626ae8565d27a7b7bdf59d8d99d94d7e284c"
UPSTREAM_DOI = "10.5281/zenodo.21605229"


class TestGoExpertProvenance(unittest.TestCase):
    def setUp(self):
        self.docs = DOCS.read_text(encoding="utf-8")

    def _present(self, marker, haystack=None):
        """assertIn would dump the whole document into the failure."""
        hay = self.docs if haystack is None else haystack
        self.assertTrue(
            marker in hay,
            f"docs/go-expert.md no longer contains {marker!r}",
        )

    def test_the_reviewed_pin_is_recorded_in_full(self):
        """A short hash is ambiguous once upstream grows."""
        self._present(UPSTREAM_PIN)

    def test_the_licence_and_copyright_are_attributed(self):
        for marker in ("MIT", "Samuel Berthe", "cc-skills-golang"):
            self._present(marker)

    def test_the_requested_citation_is_present(self):
        """Upstream asks to be cited through its CITATION.cff."""
        self._present(UPSTREAM_DOI)

    def test_re_evaluation_has_a_trigger_and_a_rule(self):
        for marker in ("re-evaluat", "advance the pin"):
            self._present(marker, self.docs.lower())


if __name__ == "__main__":
    unittest.main()
