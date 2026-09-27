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

func TestLoadConfigReadsProjectJSON(t *testing.T) {
	home := t.TempDir()
	writeFile(t, filepath.Join(home, "projects", "org_app", "project.json"),
		`{"persona": "atena", "language": {"chat": "en", "data": "en"}}`)

	cfg, err := LoadConfig(home, "org_app")
	if err != nil {
		t.Fatal(err)
	}
	if cfg.Persona != "atena" || cfg.Language.Chat != "en" || cfg.Language.Data != "en" {
		t.Fatalf("got %+v", cfg)
	}
}

func TestLoadConfigFallsBackToTheLegacyPersonaFile(t *testing.T) {
	home := t.TempDir()
	writeFile(t, filepath.Join(home, ".task", "org_app", "persona.json"),
		`{"anchored_persona": "codama"}`)

	cfg, err := LoadConfig(home, "org_app")
	if err != nil {
		t.Fatal(err)
	}
	if cfg.Persona != "codama" {
		t.Fatalf("Persona = %q, want the legacy anchor codama", cfg.Persona)
	}
}

func TestLoadConfigWithoutFilesIsEmpty(t *testing.T) {
	cfg, err := LoadConfig(t.TempDir(), "org_app")
	if err != nil {
		t.Fatal(err)
	}
	if cfg != (Config{}) {
		t.Fatalf("got %+v, want the zero Config", cfg)
	}
}

func TestLoadConfigRejectsBrokenJSON(t *testing.T) {
	home := t.TempDir()
	writeFile(t, filepath.Join(home, "projects", "org_app", "project.json"), `{"persona":`)

	if _, err := LoadConfig(home, "org_app"); err == nil {
		t.Fatal("want an error for a broken project.json")
	}
}
