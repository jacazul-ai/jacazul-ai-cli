package project

import (
	"os"
	"path/filepath"
	"testing"
)

func writeFile(t *testing.T, path, content string) {
	t.Helper()
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(path, []byte(content), 0o644); err != nil {
		t.Fatal(err)
	}
}

func TestAnchoredPersonaReadsTheLegacyPersonaFile(t *testing.T) {
	home := t.TempDir()
	writeFile(t, filepath.Join(home, ".task", "org_app", "persona.json"),
		`{"anchored_persona": "codama"}`)

	got, err := AnchoredPersona(home, "org_app")
	if err != nil {
		t.Fatal(err)
	}
	if got != "codama" {
		t.Fatalf("AnchoredPersona = %q, want codama", got)
	}
}

// The configuration file is a separate feature, not implemented: the
// launcher must not read a project.json.
func TestAnchoredPersonaIgnoresProjectJSON(t *testing.T) {
	home := t.TempDir()
	writeFile(t, filepath.Join(home, "projects", "org_app", "project.json"), `{"persona": "atena"}`)

	got, err := AnchoredPersona(home, "org_app")
	if err != nil {
		t.Fatal(err)
	}
	if got != "" {
		t.Fatalf("AnchoredPersona = %q from project.json, want nothing", got)
	}
}

func TestAnchoredPersonaWithoutAFileIsEmpty(t *testing.T) {
	got, err := AnchoredPersona(t.TempDir(), "org_app")
	if err != nil || got != "" {
		t.Fatalf("got %q, %v, want an empty persona", got, err)
	}
}

func TestAnchoredPersonaRejectsBrokenJSON(t *testing.T) {
	home := t.TempDir()
	writeFile(t, filepath.Join(home, ".task", "org_app", "persona.json"), `{"anchored_persona":`)

	if _, err := AnchoredPersona(home, "org_app"); err == nil {
		t.Fatal("want an error for a broken persona.json")
	}
}
