"""Structural guards for the go-expert hub-and-references layout.

The skill is split into a thin hub (SKILL.md) plus one reference per owned
topic. These tests fail when a link rots, a reference is orphaned, or the
progressive-disclosure rules in docs/skill-methodology.md are violated.
"""

import pathlib
import re
import unittest


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILL_DIR = PROJECT_ROOT / "skills" / "go-expert"
SKILL = SKILL_DIR / "SKILL.md"
REFERENCES = SKILL_DIR / "references"

MARKDOWN_LINK = re.compile(r"\]\(([^)\s]+)\)")


def _markdown_files():
    return [
        SKILL,
        SKILL_DIR / "CODE-REVIEW.md",
        *sorted(REFERENCES.glob("*.md")),
    ]


def _strip_code_fences(text):
    """Generic calls like AsType[T](x) read as links to the regex."""
    out, fenced = [], False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if not fenced:
            out.append(line)
    return "\n".join(out)


def _link_targets(path):
    """Relative link targets in a file, with anchors and URLs removed."""
    prose = _strip_code_fences(path.read_text(encoding="utf-8"))
    for target in MARKDOWN_LINK.findall(prose):
        if target.startswith(("http://", "https://", "#")):
            continue
        yield target.split("#", 1)[0]


class TestGoExpertStructure(unittest.TestCase):
    def test_every_relative_link_resolves(self):
        for path in _markdown_files():
            for target in _link_targets(path):
                if not target:
                    continue
                resolved = (path.parent / target).resolve()
                self.assertTrue(
                    resolved.exists(),
                    f"{path.name} links to missing target {target}",
                )

    def test_hub_routes_to_every_reference(self):
        routed = {
            target.split("/")[-1]
            for target in _link_targets(SKILL)
            if target.startswith("references/")
        }
        on_disk = {path.name for path in REFERENCES.glob("*.md")}

        self.assertEqual(
            on_disk - routed,
            set(),
            "reference files exist but the hub routing table never names them",
        )
        self.assertEqual(
            routed - on_disk,
            set(),
            "the hub routes to reference files that do not exist",
        )

    def test_references_stay_one_level_deep(self):
        nested = [p for p in REFERENCES.rglob("*") if p.is_dir()]
        self.assertEqual(
            nested,
            [],
            "nested reference directories get partially read and silently "
            "truncated; keep references one level deep",
        )

    def test_playbook_is_not_resurrected(self):
        self.assertFalse(
            (SKILL_DIR / "PLAYBOOK.md").exists(),
            "go-expert uses references/ instead of PLAYBOOK.md; see "
            "docs/skill-methodology.md",
        )
        for path in _markdown_files():
            self.assertNotIn(
                "PLAYBOOK.md",
                path.read_text(encoding="utf-8"),
                f"{path.name} still points at the dissolved PLAYBOOK.md",
            )

    def test_no_bare_at_mention_of_a_skill(self):
        """A bare @name force-loads the target skill in some harnesses."""
        bare_at = re.compile(r"(?<![\w`/])@[a-z][a-z0-9-]*\b")
        for path in _markdown_files():
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.lstrip().startswith(("go install", "//")):
                    continue
                self.assertIsNone(
                    bare_at.search(line),
                    f"{path.name}: cite skills in backticks, not as @mentions "
                    f"-> {line.strip()!r}",
                )

    def test_hub_stays_thinner_than_its_references(self):
        """The hub routes; depth belongs in references paid only when read."""
        hub = SKILL.stat().st_size
        refs = sum(p.stat().st_size for p in REFERENCES.glob("*.md"))
        self.assertLess(
            hub, refs, "the hub has absorbed reference-level depth"
        )


if __name__ == "__main__":
    unittest.main()
