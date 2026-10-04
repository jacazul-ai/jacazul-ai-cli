package environment

import (
	"fmt"
	"os"
	"path/filepath"
	"testing"
)

// TestMain lets the test binary stand in for the task executable: with
// FAKE_TASK_VERSION set it prints that version and exits.
func TestMain(m *testing.M) {
	if v := os.Getenv("FAKE_TASK_VERSION"); v != "" {
		fmt.Println(v)
		os.Exit(0)
	}
	os.Exit(m.Run())
}

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

func TestHomeFlagBeatsThePresetValue(t *testing.T) {
	env := Resolve(Input{
		Getenv:    lookup(map[string]string{"HOME": "/u", "JACAZUL_HOME": "/custom"}),
		HomeFlag:  "/flag",
		ProjectID: "org_app",
	})
	if env.Home != "/flag" || env.TaskData != "/flag/.task/org_app" {
		t.Fatalf("got Home %q, TaskData %q, want them under the flag", env.Home, env.TaskData)
	}
}

func TestSessionPrecedence(t *testing.T) {
	for _, tc := range []struct {
		name string
		flag string
		vars map[string]string
		want string
	}{
		{"flag beats the environment", "fromflag", map[string]string{"JACAZUL_SESSION": "fromenv"}, "fromflag"},
		{"environment", "", map[string]string{"JACAZUL_SESSION": "fromenv"}, "fromenv"},
		{"JACAZUL_SESSION beats the legacy name", "", map[string]string{"JACAZUL_SESSION": "fromenv", "JACAZUL_SESSION_ID": "legacy"}, "fromenv"},
		{"legacy name until the tw-flow cutoff", "", map[string]string{"JACAZUL_SESSION_ID": "legacy"}, "legacy"},
		{"default is global", "", nil, Global},
	} {
		t.Run(tc.name, func(t *testing.T) {
			env := Resolve(Input{Getenv: lookup(tc.vars), SessionFlag: tc.flag})
			if env.SessionID != tc.want {
				t.Fatalf("SessionID = %q, want %q", env.SessionID, tc.want)
			}
		})
	}
}

// The launcher owns the session: without one given, every process lands
// on the same global session instead of minting its own.
func TestNoSessionIsGeneratedPerProcess(t *testing.T) {
	a := Resolve(Input{Getenv: lookup(nil)}).SessionID
	b := Resolve(Input{Getenv: lookup(nil)}).SessionID
	if a != b {
		t.Fatalf("two processes got sessions %q and %q", a, b)
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

// writeTask links a "task" in dir to the test binary.
func writeTask(t *testing.T, dir string) string {
	t.Helper()
	if err := os.MkdirAll(dir, 0o755); err != nil {
		t.Fatal(err)
	}
	self, err := os.Executable()
	if err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(dir, "task")
	if err := os.Symlink(self, path); err != nil {
		t.Fatal(err)
	}
	return path
}

func TestRealTaskSkipsTheWrapperDirectory(t *testing.T) {
	root := t.TempDir()
	wrapper := filepath.Join(root, "repo", "scripts")
	writeTask(t, wrapper)
	real := writeTask(t, filepath.Join(root, "bin"))
	t.Setenv("FAKE_TASK_VERSION", "3.4.1")

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
