// Package environment resolves the runtime values every harness shares,
// mirroring scripts/bootstrap/environment.
package environment

import (
	"cmp"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

// Global is the session used when none is given. The launcher owns the
// session: no process mints its own.
const Global = "global"

// fallbackTasks are checked when no task binary is on PATH.
var fallbackTasks = []string{"/usr/bin/task", "/usr/local/bin/task", "/opt/homebrew/bin/task"}

// Input is what Resolve reads.
type Input struct {
	// Getenv reads the caller's environment.
	Getenv func(string) string
	// ProjectID scopes the task data.
	ProjectID string
	// HomeFlag is --home; it wins over JACAZUL_HOME.
	HomeFlag string
	// SessionFlag is --session; it wins over JACAZUL_SESSION.
	SessionFlag string
	// SkipDirs are PATH entries holding the Jacazul task wrapper, which
	// must not be taken for the real task binary.
	SkipDirs []string
}

// Env holds the resolved runtime values.
type Env struct {
	Home        string // JACAZUL_HOME
	TaskData    string // TASKDATA
	SessionID   string // JACAZUL_SESSION
	Mode        string // JACAZUL_MODE
	RealTask    string // JACAZUL_REAL_TASK, empty when none is found
	TaskVersion string // JACAZUL_TASK_VERSION, the major version
}

// Home is JACAZUL_HOME: --home, then the environment, then ~/.jacazul-ai.
func Home(flag string, getenv func(string) string) string {
	return cmp.Or(flag, getenv("JACAZUL_HOME"), filepath.Join(getenv("HOME"), ".jacazul-ai"))
}

// Session is JACAZUL_SESSION: --session, then the environment, then
// Global. JACAZUL_SESSION_ID, the name tw-flow reads, is honored after
// JACAZUL_SESSION until the tw-flow cutoff.
func Session(flag string, getenv func(string) string) string {
	return cmp.Or(flag, getenv("JACAZUL_SESSION"), getenv("JACAZUL_SESSION_ID"), Global)
}

// Resolve computes the shared runtime values: each one from its flag, then
// its environment variable, then the computed default.
func Resolve(in Input) Env {
	env := Env{
		Home:      Home(in.HomeFlag, in.Getenv),
		SessionID: Session(in.SessionFlag, in.Getenv),
		Mode:      in.Getenv("JACAZUL_MODE"),
	}
	if in.ProjectID != "" {
		env.TaskData = filepath.Join(env.Home, ".task", in.ProjectID)
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
