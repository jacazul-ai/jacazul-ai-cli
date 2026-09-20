"""Content guards for the adapted production cluster.

Upstream ships four production skills: benchmark, performance,
troubleshooting and observability. Benchmark and performance are subjects
with no local owner and become references. Troubleshooting is a bug
catalogue defined by a property, so its residue dissolves into owners.
Observability is infrastructure rather than Go, and stays out.

These tests fail when a new reference loses its subject, when dissolved
residue drifts out of its owner, or when the vendor boundary is crossed.
"""

import pathlib
import unittest


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILL_DIR = PROJECT_ROOT / "skills" / "go-expert"
REFERENCES = SKILL_DIR / "references"


def _read(name):
    return (REFERENCES / name).read_text(encoding="utf-8")


def _all_skill_files():
    return [
        SKILL_DIR / "SKILL.md",
        SKILL_DIR / "CODE-REVIEW.md",
        *sorted(REFERENCES.glob("*.md")),
    ]


class TestGoExpertProduction(unittest.TestCase):
    def test_benchmarks_reference_owns_measurement(self):
        content = _read("benchmarks.md")

        for marker in (
            "testing.B",
            "b.Loop()",
            "ReportAllocs",
            "-benchmem",
            "benchstat",
        ):
            self.assertIn(marker, content, f"benchmarks.md lost {marker!r}")

    def test_profiling_reference_owns_the_diagnostic_tools(self):
        content = _read("profiling.md")

        for marker in (
            "pprof",
            "go tool trace",
            "-race",
            "GODEBUG",
        ):
            self.assertIn(marker, content, f"profiling.md lost {marker!r}")

    def test_performance_reference_gates_on_measurement(self):
        """An optimization catalogue without the gate teaches guessing."""
        content = _read("performance.md")

        for marker in (
            "sync.Pool",
            "escape analysis",
            "inlin",
            "measure",
        ):
            self.assertIn(
                marker,
                content.lower() if marker.islower() else content,
                f"performance.md lost {marker!r}",
            )

        self.assertIn("benchmarks.md", content, "performance.md must route")

    def test_runtime_reference_gains_the_gc_knobs(self):
        content = _read("runtime.md")

        for marker in ("GOGC", "GOMEMLIMIT", "GOMAXPROCS", "PGO"):
            self.assertIn(marker, content, f"runtime.md lost {marker!r}")

    def test_dissolved_bug_catalogue_lands_in_owners(self):
        cases = {
            "code-style.md": "shadow",
            "resources.md": "os.Exit",
            "concurrency.md": "closed channel",
            "data-structures.md": "rune",
            "values.md": "Equal",
            "structs-interfaces.md": "iota",
        }
        for name, marker in cases.items():
            self.assertIn(
                marker.lower(),
                _read(name).lower(),
                f"{name} lost the dissolved topic {marker!r}",
            )

    def test_vendor_observability_stays_out(self):
        """Infrastructure is not the Go language; the boundary holds."""
        vendors = (
            "prometheus",
            "opentelemetry",
            "grafana",
            "pyroscope",
            "datadog",
            "jaeger",
        )
        for path in _all_skill_files():
            content = path.read_text(encoding="utf-8").lower()
            for vendor in vendors:
                self.assertNotIn(
                    vendor,
                    content,
                    f"{path.name} crossed the vendor boundary with "
                    f"{vendor!r}; instrumentation belongs to the project, "
                    f"not to the language expert",
                )


if __name__ == "__main__":
    unittest.main()
