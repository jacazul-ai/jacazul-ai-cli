"""Content guards for the six core subjects compared against upstream.

Each of these subjects already had a local reference when the upstream
comparison began, so the risk is not an empty file — it is a reference
that looks complete while missing the conventions a Go reviewer would
actually cite. These guards pin what the depth comparison added.
"""

import pathlib
import unittest


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
REFERENCES = PROJECT_ROOT / "skills" / "go-expert" / "references"


def _read(name):
    return (REFERENCES / name).read_text(encoding="utf-8")


class TestGoExpertCoreSubjects(unittest.TestCase):
    def _covers(self, name, markers):
        content = _read(name).lower()
        for marker in markers:
            self.assertTrue(
                marker.lower() in content,
                f"{name} no longer covers {marker!r}",
            )

    def test_naming_covers_the_conventions_a_reviewer_cites(self):
        self._covers(
            "naming.md",
            (
                "MixedCaps",
                "stutter",
                "receiver",
                "acronym",
                "Err",
                "Must",
            ),
        )

    def test_naming_keeps_the_anti_java_material(self):
        """The depth comparison must enrich, never displace."""
        self._covers("naming.md", ("IThing", "BaseThing", "premature"))


if __name__ == "__main__":
    unittest.main()
