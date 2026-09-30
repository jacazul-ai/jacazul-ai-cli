package cli

import (
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/jacazul-ai/launcher/internal/bootstrap/environment"
	"github.com/jacazul-ai/launcher/internal/bootstrap/project"
	"github.com/jacazul-ai/launcher/internal/session"
)

// runFlow holds the workflow commands the launcher answers natively.
// Everything else stays with tw-flow until the flow engine is embedded.
func runFlow(args []string, stdout, stderr io.Writer) int {
	if len(args) == 2 && args[0] == "session" && args[1] == "list" {
		return sessionList(stdout, stderr)
	}
	fmt.Fprintf(stderr, "❌ jacazul flow: only 'session list' is native for now; run 'tw-flow %s'\n", strings.Join(args, " "))
	return 1
}

// sessionList prints the project's independent session lanes like
// tw-flow session list, plus whether a handoff note waits for each.
func sessionList(stdout, stderr io.Writer) int {
	dir := os.Getenv("TASKDATA")
	if dir == "" {
		cwd, err := os.Getwd()
		if err != nil {
			fmt.Fprintf(stderr, "❌ jacazul flow: %v\n", err)
			return 1
		}
		id, err := project.Resolve(cwd)
		if err != nil {
			fmt.Fprintf(stderr, "❌ jacazul flow: %v\n", err)
			return 1
		}
		dir = filepath.Join(environment.Home(os.Getenv), ".task", id.ID)
	}
	sessions, err := session.List(dir, time.Now())
	if err != nil {
		fmt.Fprintf(stderr, "❌ jacazul flow: %v\n", err)
		return 1
	}
	if len(sessions) == 0 {
		fmt.Fprintln(stdout, "ℹ No independent sessions found.")
		return 0
	}

	current := os.Getenv("JACAZUL_SESSION_ID")
	fmt.Fprintln(stdout, "SESSION ID   PLAN                           TASK       AGE     STATUS  NOTE")
	fmt.Fprintln(stdout, strings.Repeat("-", 78))
	for _, s := range sessions {
		marker := " "
		if s.ID == current {
			marker = "*"
		}
		line := fmt.Sprintf("%s %s  %-30s %-10s %-7s %-7s %s",
			s.ID, marker, s.Plan, s.Task, session.FormatAge(s.Age), s.Status, s.Note)
		fmt.Fprintln(stdout, strings.TrimRight(line, " "))
	}
	return 0
}
