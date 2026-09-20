"""Content guards for the adapted safety and code-style material.

Upstream ships a `golang-safety` skill defined by a property rather than a
subject. This project dissolves that material into the reference that owns
each subject, and creates `numbers.md` for the one cluster that had no
owner. These tests fail when a topic drifts back out of its owner, and when
an upstream rule this project deliberately rejected reappears.
"""

import pathlib
import unittest


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILL_DIR = PROJECT_ROOT / "skills" / "go-expert"
REFERENCES = SKILL_DIR / "references"


def _read(name):
    return (REFERENCES / name).read_text(encoding="utf-8")


class TestGoExpertSafetyStyle(unittest.TestCase):
    def test_numbers_reference_owns_numeric_correctness(self):
        """Numeric range, precision, and division had no local owner."""
        content = _read("numbers.md")

        for marker in (
            "math.MaxInt32",
            "epsilon",
            "divide by zero",
            "NaN",
        ):
            self.assertIn(marker, content, f"numbers.md lost {marker!r}")

    def test_nil_traps_land_in_their_owning_references(self):
        errors = _read("errors.md")
        self.assertIn("typed nil", errors.lower())

        structs = _read("structs-interfaces.md")
        self.assertIn("nil receiver", structs.lower())

        collections = _read("data-structures.md")
        self.assertIn("nil map", collections.lower())

    def test_aliasing_traps_live_in_data_structures(self):
        content = _read("data-structures.md")

        for marker in (
            "a[:len(a):len(a)]",
            "slices.Clone",
            "slices.DeleteFunc",
        ):
            self.assertIn(
                marker,
                content,
                f"data-structures.md lost {marker!r}",
            )

    def test_defer_in_a_loop_lands_in_resources(self):
        content = _read("resources.md").lower()
        self.assertIn("defer", content)
        self.assertIn("loop", content)

    def test_parameter_passing_lands_in_values(self):
        content = _read("values.md")
        self.assertIn("parameter", content.lower())
        self.assertIn("128", content)

    def test_code_style_covers_the_imported_clarity_rules(self):
        content = _read("code-style.md")

        for marker in (
            "composite literal",
            "named boolean",
            "switch",
            "naked return",
        ):
            self.assertIn(
                marker,
                content.lower(),
                f"code-style.md lost {marker!r}",
            )

    def test_rejected_upstream_rules_never_reappear(self):
        """Three upstream rules conflict with local policy and stay out."""
        rejected = {
            "one function, one job": (
                "contradicts SKILL.md: function scope is contract, not size"
            ),
            "samber/lo": (
                "the skill is standard-library-oriented; no third-party "
                "collection dependency"
            ),
            "sub-agent": (
                "cascading activation is forbidden by the Horizontal Skill "
                "Architecture mandate"
            ),
        }

        paths = [
            SKILL_DIR / "SKILL.md",
            SKILL_DIR / "CODE-REVIEW.md",
            *sorted(REFERENCES.glob("*.md")),
        ]
        for path in paths:
            content = path.read_text(encoding="utf-8").lower()
            for phrase, reason in rejected.items():
                self.assertNotIn(
                    phrase,
                    content,
                    f"{path.name} reintroduced {phrase!r}: {reason}",
                )


if __name__ == "__main__":
    unittest.main()
