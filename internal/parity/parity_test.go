// Package parity is temporary: it holds the Go launcher to what each Bash
// launcher does, and leaves at the Python and Bash cutoff together with
// testdata/parity.
package parity

import (
	"bufio"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"testing"
)

// parityDir holds what each Bash launcher does under DRY=true DEBUG=true,
// recorded by testdata/parity/capture. The Go launcher is held to it.
var parityDir = filepath.Join("..", "..", "testdata", "parity")

type parityScenario struct {
	harness, name, env, args string
}

func parityScenarios(t *testing.T) []parityScenario {
	t.Helper()
	f, err := os.Open(filepath.Join(parityDir, "scenarios.tsv"))
	if err != nil {
		t.Fatal(err)
	}
	defer f.Close()

	var scenarios []parityScenario
	scanner := bufio.NewScanner(f)
	for scanner.Scan() {
		line := scanner.Text()
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		fields := strings.Split(line, "\t")
		if len(fields) != 4 {
			t.Fatalf("scenarios.tsv: want 4 tab-separated fields, got %d in %q", len(fields), line)
		}
		scenarios = append(scenarios, parityScenario{fields[0], fields[1], fields[2], fields[3]})
	}
	if err := scanner.Err(); err != nil {
		t.Fatal(err)
	}
	return scenarios
}

func TestParityEveryScenarioHasAReference(t *testing.T) {
	for _, s := range parityScenarios(t) {
		ref := filepath.Join(parityDir, s.harness, s.name+".txt")
		data, err := os.ReadFile(ref)
		if err != nil {
			t.Errorf("%s/%s: %v (run testdata/parity/capture %s)", s.harness, s.name, err, s.harness)
			continue
		}
		for _, section := range []string{"\n## exit\n", "\n## stdout\n"} {
			if !strings.Contains(string(data), section) {
				t.Errorf("%s/%s: missing section %q", s.harness, s.name, strings.TrimSpace(section))
			}
		}
	}
}

// A reference that names a path on the capturing machine fails on every
// other clone; the capture must normalize it.
func TestParityReferencesHoldNoMachinePaths(t *testing.T) {
	machinePath := regexp.MustCompile(`/(?:home|tmp|Users)/`)
	refs, err := filepath.Glob(filepath.Join(parityDir, "*", "*.txt"))
	if err != nil {
		t.Fatal(err)
	}
	for _, ref := range refs {
		data, err := os.ReadFile(ref)
		if err != nil {
			t.Fatal(err)
		}
		for i, line := range strings.Split(string(data), "\n") {
			if machinePath.MatchString(line) {
				t.Errorf("%s:%d: machine path %q", ref, i+1, line)
			}
		}
	}
}
