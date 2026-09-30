// Package environment resolves the runtime values every harness shares,
// mirroring scripts/bootstrap/environment.
package environment

import (
	"crypto/rand"
	"encoding/hex"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

// fallbackTasks are checked when no task binary is on PATH.
var fallbackTasks = []string{"/usr/bin/task", "/usr/local/bin/task", "/opt/homebrew/bin/task"}

// Input is what Resolve reads.
type Input struct {
	// Getenv reads the caller's environment.
	Getenv func(string) string
	// ProjectID scopes the task data.
	ProjectID string
	// SessionFlag is --session; it wins over JACAZUL_SESSION_ID.
	SessionFlag string
	// SkipDirs are PATH entries holding the Jacazul task wrapper, which
	// must not be taken for the real task binary.
	SkipDirs []string
}

// Env holds the resolved runtime values.
type Env struct {
	Home        string // JACAZUL_HOME
	TaskData    string // TASKDATA
	SessionID   string // JACAZUL_SESSION_ID
	Mode        string // JACAZUL_MODE
	RealTask    string // JACAZUL_REAL_TASK, empty when none is found
	TaskVersion string // JACAZUL_TASK_VERSION, the major version
}

// Resolve computes the shared runtime values. A preset JACAZUL_HOME wins
// over the default under HOME.
func Resolve(in Input) Env {
	env := Env{
		Home:      in.Getenv("JACAZUL_HOME"),
		SessionID: in.SessionFlag,
		Mode:      in.Getenv("JACAZUL_MODE"),
	}
	if env.Home == "" {
		env.Home = filepath.Join(in.Getenv("HOME"), ".jacazul-ai")
	}
	if in.ProjectID != "" {
		env.TaskData = filepath.Join(env.Home, ".task", in.ProjectID)
	}
	if env.SessionID == "" {
		env.SessionID = in.Getenv("JACAZUL_SESSION_ID")
	}
	if env.SessionID == "" {
		env.SessionID = newSessionID()
	}
	if env.Mode == "" {
		env.Mode = "COUNSELOR"
	}
	env.RealTask = realTask(in.Getenv("PATH"), in.SkipDirs)
	if env.RealTask != "" {
		env.TaskVersion = taskMajor(env.RealTask)
	}
	return env
}

func newSessionID() string {
	b := make([]byte, 4)
	// crypto/rand.Read never returns an error on supported platforms.
	_, _ = rand.Read(b)
	return hex.EncodeToString(b)
}

func realTask(path string, skip []string) string {
	for _, dir := range filepath.SplitList(path) {
		if dir == "" || contains(skip, dir) {
			continue
		}
		candidate := filepath.Join(dir, "task")
		if isExecutable(candidate) {
			return candidate
		}
	}
	for _, candidate := range fallbackTasks {
		if isExecutable(candidate) {
			return candidate
		}
	}
	return ""
}

func taskMajor(task string) string {
	out, err := exec.Command(task, "--version").Output()
	if err != nil {
		return ""
	}
	first, _, _ := strings.Cut(strings.TrimSpace(string(out)), "\n")
	major, _, _ := strings.Cut(first, ".")
	return major
}

func isExecutable(path string) bool {
	info, err := os.Stat(path)
	return err == nil && !info.IsDir() && info.Mode()&0o111 != 0
}

func contains(list []string, s string) bool {
	for _, item := range list {
		if filepath.Clean(item) == filepath.Clean(s) {
			return true
		}
	}
	return false
}
