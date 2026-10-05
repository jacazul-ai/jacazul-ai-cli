// Package session reads the Jacazul session lanes, the focus-<id>.json
// files the workflow engine keeps under TASKDATA, as tw-flow session list
// does. It only reads: sessions stay owned by the workflow engine.
package session

import (
	"cmp"
	"encoding/json"
	"errors"
	"io/fs"
	"os"
	"path/filepath"
	"slices"
	"strconv"
	"strings"
	"time"
)

// Status is how recently a lane was used; the workflow engine touches the
// lane's file on every command.
type Status string

const (
	Active Status = "active" // used within 2 hours
	Idle   Status = "idle"   // used within 8 hours
	Orphan Status = "orphan" // older, a candidate for tw-flow session purge
)

// Handoff is the state of a lane's handoff note.
type Handoff string

const (
	NoHandoff     Handoff = ""
	HandoffUnread Handoff = "unread" // written by tw-flow session dump, not read yet
	HandoffRead   Handoff = "read"   // acknowledged with tw-flow session ack
)

// Session is one independent lane.
type Session struct {
	ID      string
	Plan    string // "-" when unset, "?" when the file is unreadable
	Task    string // short UUID, with the same placeholders as Plan
	Age     time.Duration
	Status  Status
	Handoff Handoff
}

// List returns the lanes in dir, most recently used first. A missing dir
// has no lanes.
func List(dir string, now time.Time) ([]Session, error) {
	paths, err := filepath.Glob(filepath.Join(dir, "focus-*.json"))
	if err != nil {
		return nil, err
	}
	sessions := make([]Session, 0, len(paths))
	for _, path := range paths {
		info, err := os.Stat(path)
		if errors.Is(err, fs.ErrNotExist) {
			continue
		}
		if err != nil {
			return nil, err
		}
		id := strings.TrimSuffix(strings.TrimPrefix(filepath.Base(path), "focus-"), ".json")
		age := now.Sub(info.ModTime())
		s := Session{ID: id, Plan: "?", Task: "?", Age: age, Status: statusOf(age)}

		var lane struct {
			Plan string `json:"focused_plan"`
			Task string `json:"focused_task_uuid"`
		}
		if data, err := os.ReadFile(path); err == nil && json.Unmarshal(data, &lane) == nil {
			s.Plan = cmp.Or(lane.Plan, "-")
			s.Task = cmp.Or(shortUUID(lane.Task), "-")
		}
		if note, err := os.ReadFile(filepath.Join(dir, "session-note-"+id+".md")); err == nil {
			s.Handoff = HandoffUnread
			if strings.Contains(string(note), "acknowledged:") {
				s.Handoff = HandoffRead
			}
		}
		sessions = append(sessions, s)
	}
	slices.SortStableFunc(sessions, func(a, b Session) int { return cmp.Compare(a.Age, b.Age) })
	return sessions, nil
}

func statusOf(age time.Duration) Status {
	switch {
	case age < 2*time.Hour:
		return Active
	case age < 8*time.Hour:
		return Idle
	default:
		return Orphan
	}
}

// FormatAge renders an age in its largest whole unit: 59s, 3m, 5h, 2d.
func FormatAge(age time.Duration) string {
	switch {
	case age < time.Minute:
		return strconv.Itoa(int(age/time.Second)) + "s"
	case age < time.Hour:
		return strconv.Itoa(int(age/time.Minute)) + "m"
	case age < 24*time.Hour:
		return strconv.Itoa(int(age/time.Hour)) + "h"
	default:
		return strconv.Itoa(int(age/(24*time.Hour))) + "d"
	}
}

func shortUUID(uuid string) string {
	if len(uuid) > 8 {
		return uuid[:8]
	}
	return uuid
}
