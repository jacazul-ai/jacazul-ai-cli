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

# Every skill directory present upstream at UPSTREAM_PIN. The pin and this
# inventory move together: advancing one without the other claims a
# comparison that did not happen.
UPSTREAM_SKILLS = (
    "golang-benchmark",
    "golang-cli",
    "golang-code-style",
    "golang-concurrency",
    "golang-context",
    "golang-continuous-integration",
    "golang-data-structures",
    "golang-database",
    "golang-dependency-injection",
    "golang-dependency-management",
    "golang-design-patterns",
    "golang-documentation",
    "golang-error-handling",
    "golang-google-wire",
    "golang-gopls",
    "golang-graphql",
    "golang-grpc",
    "golang-how-to",
    "golang-lint",
    "golang-modernize",
    "golang-naming",
    "golang-observability",
    "golang-performance",
    "golang-pkg-go-dev",
    "golang-popular-libraries",
    "golang-project-layout",
    "golang-refactoring",
    "golang-safety",
    "golang-samber-do",
    "golang-samber-hot",
    "golang-samber-lo",
    "golang-samber-mo",
    "golang-samber-oops",
    "golang-samber-ro",
    "golang-samber-slog",
    "golang-security",
    "golang-spf13-cobra",
    "golang-spf13-viper",
    "golang-stay-updated",
    "golang-stretchr-testify",
    "golang-structs-interfaces",
    "golang-swagger",
    "golang-testing",
    "golang-troubleshooting",
    "golang-uber-dig",
    "golang-uber-fx",
)

DE_PARA_HEADING = "## Upstream parity de-para"


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

    def _de_para(self):
        start = self.docs.index(DE_PARA_HEADING) + len(DE_PARA_HEADING)
        rest = self.docs[start:]
        end = rest.find("\n## ")
        return rest if end == -1 else rest[:end]

    def test_every_upstream_skill_has_a_verdict(self):
        """A skill in no table is invisible, not merely uncompared.

        The de-para reads as a complete map, and its own safeguard only
        covers absence from the Adapted table. A skill named nowhere
        escapes both.
        """
        section = self._de_para()
        missing = [n for n in UPSTREAM_SKILLS if n not in section]

        self.assertEqual(
            missing,
            [],
            "these upstream skills carry no verdict anywhere in the "
            f"de-para, so nothing records that they were considered: "
            f"{missing}",
        )

    def test_the_inventory_is_not_silently_stale(self):
        """Duplicates here would mask a skill that is actually absent."""
        self.assertEqual(
            len(UPSTREAM_SKILLS),
            len(set(UPSTREAM_SKILLS)),
            "the upstream inventory contains a duplicate entry",
        )


if __name__ == "__main__":
    unittest.main()
