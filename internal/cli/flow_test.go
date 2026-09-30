package cli

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestFlowSessionListReadsTheProjectLanes(t *testing.T) {
	l := setup(t)
	t.Setenv("JACAZUL_SESSION_ID", "bbbbbbbb")
	id := filepath.Base(filepath.Dir(l.project)) + "_" + filepath.Base(l.project)
	dir := filepath.Join(l.home, ".jacazul-ai", ".task", id)
	if err := os.MkdirAll(dir, 0o755); err != nil {
		t.Fatal(err)
	}
	for name, content := range map[string]string{
		"focus-bbbbbbbb.json":      `{"focused_plan": "jacazul-launcher", "focused_task_uuid": "454bc8a1-4a64"}`,
		"session-note-bbbbbbbb.md": "",
	} {
		if err := os.WriteFile(filepath.Join(dir, name), []byte(content), 0o644); err != nil {
			t.Fatal(err)
		}
	}

	code, stdout, stderr := run(t, "flow", "session", "list")
	if code != 0 {
		t.Fatalf("exit %d, stderr %q", code, stderr)
	}
	lines := strings.Split(strings.TrimSuffix(stdout, "\n"), "\n")
	if len(lines) != 3 {
		t.Fatalf("want header, rule and one lane:\n%s", stdout)
	}
	if !strings.HasPrefix(lines[0], "SESSION ID   PLAN") || !strings.HasSuffix(lines[0], "NOTE") {
		t.Errorf("header %q", lines[0])
	}
	fields := strings.Fields(lines[2])
	want := []string{"bbbbbbbb", "*", "jacazul-launcher", "454bc8a1"}
	for i, w := range want {
		if i >= len(fields) || fields[i] != w {
			t.Fatalf("lane %q, want it to start with %q", lines[2], want)
		}
	}
	if !strings.HasSuffix(lines[2], "active  note") {
		t.Errorf("lane %q lacks status and note", lines[2])
	}
}

func TestFlowSessionListHonorsTaskData(t *testing.T) {
	setup(t)
	dir := t.TempDir()
	t.Setenv("TASKDATA", dir)
	if err := os.WriteFile(filepath.Join(dir, "focus-cccccccc.json"), []byte("{}"), 0o644); err != nil {
		t.Fatal(err)
	}
	_, stdout, _ := run(t, "flow", "session", "list")
	if !strings.Contains(stdout, "cccccccc    -") {
		t.Errorf("TASKDATA lane missing:\n%s", stdout)
	}
}

func TestFlowSessionListWithoutLanes(t *testing.T) {
	setup(t)
	code, stdout, _ := run(t, "flow", "session", "list")
	if code != 0 || stdout != "ℹ No independent sessions found.\n" {
		t.Fatalf("exit %d, stdout %q", code, stdout)
	}
}

func TestFlowOtherCommandsPointToTwFlow(t *testing.T) {
	setup(t)
	code, _, stderr := run(t, "flow", "status")
	if code != 1 || !strings.Contains(stderr, "tw-flow status") {
		t.Fatalf("exit %d, stderr %q", code, stderr)
	}
}
