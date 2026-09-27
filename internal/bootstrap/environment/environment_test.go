package environment

import (
	"os"
	"path/filepath"
	"regexp"
	"testing"
)

func lookup(vars map[string]string) func(string) string {
	return func(key string) string { return vars[key] }
}

func TestHomeHonorsAPresetValue(t *testing.T) {
	env := Resolve(Input{
		Getenv:    lookup(map[string]string{"HOME": "/u", "JACAZUL_HOME": "/custom"}),
		ProjectID: "org_app",
	})
	if env.Home != "/custom" {
		t.Fatalf("Home = %q, want the preset /custom", env.Home)
	}
	if env.TaskData != "/custom/.task/org_app" {
		t.Fatalf("TaskData = %q, want it under the preset home", env.TaskData)
	}
}

func TestHomeDefaultsUnderTheUserHome(t *testing.T) {
	env := Resolve(Input{Getenv: lookup(map[string]string{"HOME": "/u"}), ProjectID: "org_app"})
	if env.Home != "/u/.jacazul-ai" || env.TaskData != "/u/.jacazul-ai/.task/org_app" {
		t.Fatalf("got Home %q, TaskData %q", env.Home, env.TaskData)
	}
}

func TestSessionFlagBeatsTheEnvironment(t *testing.T) {
	env := Resolve(Input{
		Getenv:      lookup(map[string]string{"JACAZUL_SESSION_ID": "fromenv1"}),
		SessionFlag: "fromflag",
	})
	if env.SessionID != "fromflag" {
		t.Fatalf("SessionID = %q, want the flag", env.SessionID)
	}
}

func TestSessionFromTheEnvironment(t *testing.T) {
	env := Resolve(Input{Getenv: lookup(map[string]string{"JACAZUL_SESSION_ID": "fromenv1"})})
	if env.SessionID != "fromenv1" {
		t.Fatalf("SessionID = %q, want the inherited one", env.SessionID)
	}
}

func TestNewSessionIsEightHexCharacters(t *testing.T) {
	a := Resolve(Input{Getenv: lookup(nil)}).SessionID
	b := Resolve(Input{Getenv: lookup(nil)}).SessionID
	if !regexp.MustCompile(`^[0-9a-f]{8}$`).MatchString(a) {
		t.Fatalf("SessionID = %q, want 8 hex characters", a)
	}
	if a == b {
		t.Fatalf("two new sessions share the ID %q", a)
	}
}

func TestModeDefaultsToCounselor(t *testing.T) {
	if got := Resolve(Input{Getenv: lookup(nil)}).Mode; got != "COUNSELOR" {
		t.Fatalf("Mode = %q, want COUNSELOR", got)
	}
	got := Resolve(Input{Getenv: lookup(map[string]string{"JACAZUL_MODE": "UNHINGED"})}).Mode
	if got != "UNHINGED" {
		t.Fatalf("Mode = %q, want the variable", got)
	}
}

// writeTask creates an executable fake task that reports version.
func writeTask(t *testing.T, dir, version string) string {
	t.Helper()
	if err := os.MkdirAll(dir, 0o755); err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(dir, "task")
	script := "#!/bin/sh\necho " + version + "\n"
	if err := os.WriteFile(path, []byte(script), 0o755); err != nil {
		t.Fatal(err)
	}
	return path
}

func TestRealTaskSkipsTheWrapperDirectory(t *testing.T) {
	root := t.TempDir()
	wrapper := filepath.Join(root, "repo", "scripts")
	writeTask(t, wrapper, "0.0.0")
	real := writeTask(t, filepath.Join(root, "bin"), "3.4.1")

	env := Resolve(Input{
		Getenv:   lookup(map[string]string{"PATH": wrapper + string(os.PathListSeparator) + filepath.Dir(real)}),
		SkipDirs: []string{wrapper},
	})
	if env.RealTask != real {
		t.Fatalf("RealTask = %q, want %q", env.RealTask, real)
	}
	if env.TaskVersion != "3" {
		t.Fatalf("TaskVersion = %q, want the major 3", env.TaskVersion)
	}
}
