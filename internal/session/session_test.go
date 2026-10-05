package session

import (
	"os"
	"path/filepath"
	"testing"
	"time"
)

var now = time.Date(2026, 9, 27, 12, 0, 0, 0, time.UTC)

func focus(t *testing.T, dir, id, content string, age time.Duration) {
	t.Helper()
	path := filepath.Join(dir, "focus-"+id+".json")
	if err := os.WriteFile(path, []byte(content), 0o644); err != nil {
		t.Fatal(err)
	}
	mtime := now.Add(-age)
	if err := os.Chtimes(path, mtime, mtime); err != nil {
		t.Fatal(err)
	}
}

func TestListReadsLanesNewestFirst(t *testing.T) {
	dir := t.TempDir()
	focus(t, dir, "aaaaaaaa", `{"focused_plan": "old", "focused_task_uuid": null}`, 9*time.Hour)
	focus(t, dir, "bbbbbbbb", `{"focused_plan": "launcher", "focused_task_uuid": "454bc8a1-4a64-448d"}`, 30*time.Second)
	focus(t, dir, "cccccccc", `not json`, 3*time.Hour)
	if err := os.WriteFile(filepath.Join(dir, "focus.json"), []byte("{}"), 0o644); err != nil {
		t.Fatal(err)
	}
	for id, note := range map[string]string{"aaaaaaaa": "# note\n", "bbbbbbbb": "# note\nacknowledged: 2026-09-27\n"} {
		if err := os.WriteFile(filepath.Join(dir, "session-note-"+id+".md"), []byte(note), 0o644); err != nil {
			t.Fatal(err)
		}
	}

	got, err := List(dir, now)
	if err != nil {
		t.Fatal(err)
	}
	want := []Session{
		{ID: "bbbbbbbb", Plan: "launcher", Task: "454bc8a1", Age: 30 * time.Second, Status: Active, Handoff: HandoffRead},
		{ID: "cccccccc", Plan: "?", Task: "?", Age: 3 * time.Hour, Status: Idle},
		{ID: "aaaaaaaa", Plan: "old", Task: "-", Age: 9 * time.Hour, Status: Orphan, Handoff: HandoffUnread},
	}
	if len(got) != len(want) {
		t.Fatalf("got %d sessions: %+v", len(got), got)
	}
	for i := range want {
		if got[i] != want[i] {
			t.Errorf("session %d: got %+v, want %+v", i, got[i], want[i])
		}
	}
}

func TestListWithoutDirectoryIsEmpty(t *testing.T) {
	got, err := List(filepath.Join(t.TempDir(), "missing"), now)
	if err != nil || len(got) != 0 {
		t.Fatalf("got %v, %v", got, err)
	}
}

func TestStatusThresholds(t *testing.T) {
	for age, want := range map[time.Duration]Status{
		0:                         Active,
		2*time.Hour - time.Second: Active,
		2 * time.Hour:             Idle,
		8*time.Hour - time.Second: Idle,
		8 * time.Hour:             Orphan,
	} {
		if got := statusOf(age); got != want {
			t.Errorf("age %s: got %s, want %s", age, got, want)
		}
	}
}

func TestFormatAge(t *testing.T) {
	for age, want := range map[time.Duration]string{
		59 * time.Second:                "59s",
		60 * time.Second:                "1m",
		59*time.Minute + 59*time.Second: "59m",
		3 * time.Hour:                   "3h",
		47 * time.Hour:                  "1d",
	} {
		if got := FormatAge(age); got != want {
			t.Errorf("%s: got %q, want %q", age, got, want)
		}
	}
}
