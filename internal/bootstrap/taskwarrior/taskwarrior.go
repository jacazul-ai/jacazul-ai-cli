// Package taskwarrior ports scripts/bootstrap/taskwarrior one to one,
// known issues included, while the flow engine replaces Taskwarrior.
//
// Transitional: this package leaves at the flow cutoff, which also
// migrates the Taskwarrior data into the flow database.
package taskwarrior

import (
	"bufio"
	"errors"
	"fmt"
	"io"
	"io/fs"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"strings"
	"time"
)

// Templates are the .taskrc templates UDAs are synced from.
type Templates struct {
	Caged, Unhinged string
}

// Input is what Bootstrap reads.
type Input struct {
	ProjectID   string
	Home        string // JACAZUL_HOME
	Mode        string // JACAZUL_MODE
	TaskRC      string // inherited TASKRC, possibly empty
	SessionID   string
	FocusPlan   string // JACAZUL_FOCUS_PLAN
	FocusTask   string // JACAZUL_FOCUS_TASK
	RealTask    string // JACAZUL_REAL_TASK
	TaskVersion string // JACAZUL_TASK_VERSION
	Debug       bool
	Templates   Templates
	Out         io.Writer
}

// Result is what the launcher exports.
type Result struct {
	TaskData string // TASKDATA
	TaskRC   string // TASKRC, empty when none applies
}

var dataLocation = regexp.MustCompile(`(?m)^data\.location=.*$`)

// Bootstrap prepares Taskwarrior for the project and reports what to
// export. Without a project it does nothing.
func Bootstrap(in Input) (Result, error) {
	if in.ProjectID == "" {
		return Result{}, nil
	}
	res := Result{
		TaskData: filepath.Join(in.Home, ".task", in.ProjectID),
		TaskRC:   in.TaskRC,
	}
	location := "data.location=" + filepath.Join(in.Home, ".task")

	if in.Mode == "UNHINGED" {
		res.TaskRC = filepath.Join(in.Home, ".taskrc")
		if _, err := os.Stat(res.TaskRC); errors.Is(err, fs.ErrNotExist) {
			fmt.Fprintf(in.Out, "🐊 Initializing Unhinged Taskwarrior config at %s...\n", res.TaskRC)
			if err := os.MkdirAll(in.Home, 0o755); err != nil {
				return res, err
			}
			rc := dataLocation.ReplaceAllLiteralString(in.Templates.Unhinged, location)
			if err := os.WriteFile(res.TaskRC, []byte(rc), 0o644); err != nil {
				return res, err
			}
		} else {
			if err := syncUDAs(res.TaskRC, in.Templates.Unhinged, "🐊 Injecting missing UDA from project: ", in); err != nil {
				return res, err
			}
			if err := ensureLocation(res.TaskRC, location); err != nil {
				return res, err
			}
		}
	}

	if in.Mode != "UNHINGED" && res.TaskRC != "" && isFile(res.TaskRC) {
		if err := syncUDAs(res.TaskRC, in.Templates.Caged, "🐊 Injecting missing UDA: ", in); err != nil {
			return res, err
		}
	}

	if _, err := os.Stat(res.TaskData); errors.Is(err, fs.ErrNotExist) {
		fmt.Fprintf(in.Out, "🐊 Creating task data directory: %s\n", res.TaskData)
		if err := os.MkdirAll(res.TaskData, 0o755); err != nil {
			return res, err
		}
	}

	if in.TaskVersion == "3" && isFile(filepath.Join(res.TaskData, "pending.data")) &&
		!isFile(filepath.Join(res.TaskData, "taskchampion.sqlite3")) {
		if err := migrate(in, res.TaskData); err != nil {
			return res, err
		}
	}

	if in.FocusPlan != "" && in.SessionID != "" {
		if err := seedFocus(in, res.TaskData); err != nil {
			return res, err
		}
	}

	if in.SessionID != "" {
		if err := purgeCaches(in); err != nil {
			return res, err
		}
	}

	if in.Debug {
		fmt.Fprintf(in.Out, "🐊 Task Data: %s\n", res.TaskData)
		if res.TaskRC != "" {
			fmt.Fprintf(in.Out, "🐊 Task RC: %s\n", res.TaskRC)
		}
		if in.SessionID != "" {
			fmt.Fprintf(in.Out, "🐊 Session ID: %s\n", in.SessionID)
		}
	}
	return res, nil
}

// syncUDAs appends every uda.* line of template whose key the file lacks.
func syncUDAs(path, template, message string, in Input) error {
	data, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	present := string(data)
	var missing []string
	scanner := bufio.NewScanner(strings.NewReader(template))
	for scanner.Scan() {
		line := scanner.Text()
		if !strings.HasPrefix(line, "uda.") {
			continue
		}
		key, _, _ := strings.Cut(line, "=")
		if hasKey(present, key) {
			continue
		}
		if in.Debug {
			fmt.Fprintf(in.Out, "%s%s\n", message, line)
		}
		missing = append(missing, line)
	}
	if len(missing) == 0 {
		return nil
	}
	f, err := os.OpenFile(path, os.O_APPEND|os.O_WRONLY, 0)
	if err != nil {
		return err
	}
	defer f.Close()
	_, err = f.WriteString(strings.Join(missing, "\n") + "\n")
	return err
}

func hasKey(content, key string) bool {
	for _, line := range strings.Split(content, "\n") {
		if strings.HasPrefix(line, key+"=") {
			return true
		}
	}
	return false
}

// ensureLocation rewrites data.location lines unless the file already
// names the Jacazul task directory.
func ensureLocation(path, location string) error {
	data, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	if strings.Contains(string(data), location) {
		return nil
	}
	return os.WriteFile(path, []byte(dataLocation.ReplaceAllLiteralString(string(data), location)), 0o644)
}

func migrate(in Input, taskData string) error {
	fmt.Fprintln(in.Out, "⚠️  Detected Taskwarrior 2.x data in version 3 environment.")
	fmt.Fprintln(in.Out, "🐊 Migrating database to SQLite (task import-v2)...")
	backup := filepath.Join(in.Home, ".task-backups", "migration-"+time.Now().Format("20060102-150405"))
	if err := os.MkdirAll(backup, 0o755); err != nil {
		return err
	}
	legacy, err := filepath.Glob(filepath.Join(taskData, "*.data"))
	if err != nil {
		return err
	}
	for _, src := range legacy {
		data, err := os.ReadFile(src)
		if err != nil {
			return err
		}
		if err := os.WriteFile(filepath.Join(backup, filepath.Base(src)), data, 0o644); err != nil {
			return err
		}
	}
	cmd := exec.Command(in.RealTask, "import-v2", "rc.hooks=0")
	cmd.Env = append(os.Environ(), "TASKDATA="+taskData)
	cmd.Stdout, cmd.Stderr = in.Out, in.Out
	if cmd.Run() == nil {
		fmt.Fprintln(in.Out, "✅ Migration successful.")
	} else {
		fmt.Fprintln(in.Out, "❌ Migration failed! Please check logs.")
	}
	return nil
}

func seedFocus(in Input, taskData string) error {
	path := filepath.Join(taskData, "focus-"+in.SessionID+".json")
	if isFile(path) {
		return nil
	}
	if in.Debug {
		fmt.Fprintf(in.Out, "🐊 Creating independent session focus: %s\n", path)
	}
	if err := os.MkdirAll(taskData, 0o755); err != nil {
		return err
	}
	content := fmt.Sprintf("{\n  \"focused_plan\": %q,\n  \"focused_task_uuid\": %q,\n  \"task_track\": [],\n  \"plans_of_interest\": []\n}\n",
		in.FocusPlan, in.FocusTask)
	return os.WriteFile(path, []byte(content), 0o644)
}

// purgeCaches removes every tw-flow session cache of the project except
// global and the current session. Known issue kept for parity: it also
// removes caches of other live sessions.
func purgeCaches(in Input) error {
	dir := filepath.Join(in.Home, "cache", "tw-flow", in.ProjectID)
	entries, err := os.ReadDir(dir)
	if errors.Is(err, fs.ErrNotExist) {
		return nil
	}
	if err != nil {
		return err
	}
	for _, e := range entries {
		if !e.IsDir() || e.Name() == "global" || e.Name() == in.SessionID {
			continue
		}
		if err := os.RemoveAll(filepath.Join(dir, e.Name())); err != nil {
			return err
		}
	}
	return nil
}

func isFile(path string) bool {
	info, err := os.Stat(path)
	return err == nil && !info.IsDir()
}
