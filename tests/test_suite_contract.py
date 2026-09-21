"""Guards for how the test suite itself is invoked.

The repository had no canonical invocation: no Makefile target, no
pyproject configuration, no CI. Callers improvised
`unittest discover -s tests`, which drops the repository root from the
package path and matches only one of the two file-naming conventions
present here. The result was 84 tests that never ran, and the failures
they would have reported staying invisible.

These tests pin the invocation and, more importantly, fail the moment a
new test file would be skipped by it.
"""

import fnmatch
import pathlib
import re
import unittest


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
MAKEFILE = PROJECT_ROOT / "Makefile"
TESTS_DIR = PROJECT_ROOT / "tests"

TEST_TARGET = re.compile(
    r"^test:.*?\n((?:\t.*\n)+)", re.MULTILINE | re.DOTALL
)
PATTERN_FLAG = re.compile(r"-p\s+'([^']+)'")


class TestSuiteContract(unittest.TestCase):
    def setUp(self):
        self.makefile = MAKEFILE.read_text(encoding="utf-8")
        match = TEST_TARGET.search(self.makefile)
        self.assertIsNotNone(
            match,
            "the Makefile must define a `test` target so the suite has one "
            "invocation instead of an improvised one per caller",
        )
        self.recipe = match.group(1)

    def test_the_target_keeps_the_repository_root_as_top_level(self):
        """Without -t . the relative imports in tests/ fail to resolve."""
        self.assertIn(
            "-t .",
            self.recipe,
            "`-t .` is what makes `from .base import ...` work under "
            "discover; dropping it turns those modules into errors",
        )

    def test_the_target_declares_an_explicit_pattern(self):
        self.assertIsNotNone(
            PATTERN_FLAG.search(self.recipe),
            "the default pattern `test*.py` matches only one of the two "
            "naming conventions used in tests/; declare one explicitly",
        )

    def test_no_test_module_is_dark(self):
        """A file holding tests that the pattern skips is worse than none."""
        pattern = PATTERN_FLAG.search(self.recipe).group(1)

        dark = []
        for path in sorted(TESTS_DIR.glob("*.py")):
            source = path.read_text(encoding="utf-8")
            if "def test_" not in source:
                continue
            if not fnmatch.fnmatch(path.name, pattern):
                dark.append(path.name)

        self.assertEqual(
            dark,
            [],
            f"these files define tests that `{pattern}` never collects, so "
            f"they silently do not run: {dark}",
        )


if __name__ == "__main__":
    unittest.main()
