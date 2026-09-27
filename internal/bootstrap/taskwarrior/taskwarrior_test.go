package taskwarrior

import (
	"bytes"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// TestMain lets the test binary stand in for the task executable: with
// FAKE_TASK_MARKER set it records TASKDATA and its arguments and exits.
func TestMain(m *testing.M) {
	if marker := os.Getenv("FAKE_TASK_MARKER"); marker != "" {
		line := os.Getenv("TASKDATA") + " " + strings.Join(os.Args[1:], " ") + "\n"
		if err := os.WriteFile(marker, []byte(line), 0o644); err != nil {
			os.Exit(1)
		}
		os.Exit(0)
	}
	os.Exit(m.Run())
}

const template = "data.location=/root/.task\nconfirmation=no\nuda.ticket.type=string\nuda.backlog.type=numeric\n"

func run(t *testing.T, in Input) (Result, string) {
	t.Helper()
	var out bytes.Buffer
	in.Out = &out
	if in.Templates == (Templates{}) {
		in.Templates = Templates{Caged: template, Unhinged: template}
	}
	res, err := Bootstrap(in)
	if err != nil {
		t.Fatal(err)
	}
	return res, out.String()
}

func read(t *testing.T, path string) string {
	t.Helper()
	data, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	return string(data)
}

func write(t *testing.T, path, content string) {
	t.Helper()
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(path, []byte(content), 0o644); err != nil {
		t.Fatal(err)
	}
}

func TestNoProjectDoesNothing(t *testing.T) {
	home := t.TempDir()
	res, out := run(t, Input{Home: home, Debug: true})
	if res != (Result{}) || out != "" {
		t.Fatalf("got %+v and output %q, want nothing", res, out)
	}
}

func TestCreatesTheTaskDataDirectory(t *testing.T) {
	home := t.TempDir()
	res, out := run(t, Input{Home: home, ProjectID: "org_app", Mode: "COUNSELOR"})
	want := filepath.Join(home, ".task", "org_app")
	if res.TaskData != want {
		t.Fatalf("TaskData = %q, want %q", res.TaskData, want)
	}
	if info, err := os.Stat(want); err != nil || !info.IsDir() {
		t.Fatalf("task data directory missing: %v", err)
	}
	if out != "🐊 Creating task data directory: "+want+"\n" {
		t.Fatalf("output %q", out)
	}
}

func TestUnhingedInitializesItsTaskRC(t *testing.T) {
	home := t.TempDir()
	res, out := run(t, Input{Home: home, ProjectID: "org_app", Mode: "UNHINGED"})
	rc := filepath.Join(home, ".taskrc")
	if res.TaskRC != rc {
		t.Fatalf("TaskRC = %q, want %q", res.TaskRC, rc)
	}
	if !strings.Contains(out, "🐊 Initializing Unhinged Taskwarrior config at "+rc+"...") {
		t.Fatalf("output %q", out)
	}
	if got := read(t, rc); !strings.HasPrefix(got, "data.location="+home+"/.task\n") {
		t.Fatalf("taskrc starts %q, want data.location under home", got)
	}
}

func TestUnhingedSyncsMissingUDAsAndDataLocation(t *testing.T) {
	home := t.TempDir()
	rc := filepath.Join(home, ".taskrc")
	write(t, rc, "data.location=/elsewhere\nuda.ticket.type=string\n")

	_, out := run(t, Input{Home: home, ProjectID: "org_app", Mode: "UNHINGED", Debug: true})
	got := read(t, rc)
	if !strings.Contains(got, "data.location="+home+"/.task\n") {
		t.Fatalf("data.location not corrected: %q", got)
	}
	if strings.Count(got, "uda.ticket.type") != 1 || !strings.HasSuffix(got, "uda.backlog.type=numeric\n") {
		t.Fatalf("UDAs not synced once: %q", got)
	}
	if !strings.Contains(out, "🐊 Injecting missing UDA from project: uda.backlog.type=numeric\n") {
		t.Fatalf("output %q", out)
	}
}

func TestCounselorSyncsUDAsIntoAnInheritedTaskRC(t *testing.T) {
	home := t.TempDir()
	rc := filepath.Join(t.TempDir(), "mine.taskrc")
	write(t, rc, "uda.ticket.type=string\n")

	res, out := run(t, Input{Home: home, ProjectID: "org_app", Mode: "COUNSELOR", TaskRC: rc, Debug: true})
	if res.TaskRC != rc {
		t.Fatalf("TaskRC = %q, want the inherited %q", res.TaskRC, rc)
	}
	if got := read(t, rc); got != "uda.ticket.type=string\nuda.backlog.type=numeric\n" {
		t.Fatalf("taskrc %q", got)
	}
	if !strings.Contains(out, "🐊 Injecting missing UDA: uda.backlog.type=numeric\n") {
		t.Fatalf("output %q", out)
	}
}

func TestFocusSeedWritesTheSessionFile(t *testing.T) {
	home := t.TempDir()
	run(t, Input{Home: home, ProjectID: "org_app", SessionID: "abcd1234", FocusPlan: "plan-a", FocusTask: "uuid-1"})
	got := read(t, filepath.Join(home, ".task", "org_app", "focus-abcd1234.json"))
	want := "{\n  \"focused_plan\": \"plan-a\",\n  \"focused_task_uuid\": \"uuid-1\",\n  \"task_track\": [],\n  \"plans_of_interest\": []\n}\n"
	if got != want {
		t.Fatalf("focus file %q", got)
	}
}

func TestCachePurgeKeepsGlobalAndTheCurrentSession(t *testing.T) {
	home := t.TempDir()
	cache := filepath.Join(home, "cache", "tw-flow", "org_app")
	for _, d := range []string{"global", "abcd1234", "other001"} {
		if err := os.MkdirAll(filepath.Join(cache, d), 0o755); err != nil {
			t.Fatal(err)
		}
	}
	run(t, Input{Home: home, ProjectID: "org_app", SessionID: "abcd1234"})
	for d, want := range map[string]bool{"global": true, "abcd1234": true, "other001": false} {
		_, err := os.Stat(filepath.Join(cache, d))
		if (err == nil) != want {
			t.Errorf("%s present = %v, want %v", d, err == nil, want)
		}
	}
}

func TestDebugReportsDataRCAndSession(t *testing.T) {
	home := t.TempDir()
	_, out := run(t, Input{Home: home, ProjectID: "org_app", Mode: "UNHINGED", SessionID: "abcd1234", Debug: true})
	for _, line := range []string{
		"🐊 Task Data: " + filepath.Join(home, ".task", "org_app") + "\n",
		"🐊 Task RC: " + filepath.Join(home, ".taskrc") + "\n",
		"🐊 Session ID: abcd1234\n",
	} {
		if !strings.HasSuffix(out, line) && !strings.Contains(out, line) {
			t.Errorf("output lacks %q", line)
		}
	}
}

func TestMigratesVersionTwoDataUnderVersionThree(t *testing.T) {
	home := t.TempDir()
	data := filepath.Join(home, ".task", "org_app")
	write(t, filepath.Join(data, "pending.data"), "legacy\n")
	marker := filepath.Join(t.TempDir(), "args")
	t.Setenv("FAKE_TASK_MARKER", marker)

	_, out := run(t, Input{Home: home, ProjectID: "org_app", RealTask: os.Args[0], TaskVersion: "3"})
	if got := read(t, marker); got != data+" import-v2 rc.hooks=0\n" {
		t.Fatalf("task ran with %q", got)
	}
	backups, _ := filepath.Glob(filepath.Join(home, ".task-backups", "migration-*", "pending.data"))
	if len(backups) != 1 {
		t.Fatalf("backups %v, want one copy of pending.data", backups)
	}
	if !strings.Contains(out, "✅ Migration successful.") {
		t.Fatalf("output %q", out)
	}
}
