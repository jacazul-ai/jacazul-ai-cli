package parity

import (
	"bytes"
	"fmt"
	"io/fs"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"slices"
	"strings"
	"testing"

	"github.com/jacazul-ai/launcher/internal/testutil"
)

// bashOnly are stdout lines the Go launcher drops on purpose: it neither
// syncs the Python venv nor runs the Python hatch on every launch.
var bashOnly = []*regexp.Regexp{
	regexp.MustCompile(`^🐊 Syncing Python dependencies via 'uv'\.\.\.$`),
	regexp.MustCompile(`^🐊 Installing Jacazul package in editable mode\.\.\.$`),
	regexp.MustCompile(`^✅ Jacazul: Python environment ready \(.*\)\.$`),
	regexp.MustCompile(`^✓ Hatched Engine Skill: `),
}

// sessionID is random unless a scenario fixes it; both sides are normalized.
var sessionID = regexp.MustCompile(`(Session ID: )[0-9a-f]{8}\b`)

// taskBinary differs per machine; the reference was captured with one.
var taskBinary = regexp.MustCompile(`(?m)(Runtime Initialized \| Mode: \w+ \| Binary: ).*$`)

// goResume is where the Go launcher differs from the Bash one on
// --resume: it passes the argument to claude and keeps the session
// prompt, while the Bash launcher swallowed both (see "Open decisions" in
// docs/proposals/go-launcher.md).
const goResume = `🐊 Arguments for claude: --append-system-prompt "[ONBOARD_PROMPT]" --resume`

// goTaskData is printed by the Go launcher only: in Bash the hatch created
// the task data directory silently before the Taskwarrior bootstrap ran.
const goTaskData = "🐊 Creating task data directory: <HOME>/.jacazul-ai/.task/jacazul-ai_jacazul-ai-cli"

func TestParityClaudeMatchesTheBashLauncher(t *testing.T) {
	repo := testutil.RepoRoot(t)
	// The binary finds its checkout from its own path, so it is built into
	// a checkout whose skills, extensions and scripts are this one's.
	root := testutil.Checkout(t)
	bin := filepath.Join(root, "bin", "jacazul")
	build := exec.Command("go", "build", "-o", bin, "./cmd/jacazul")
	build.Dir = repo
	if out, err := build.CombinedOutput(); err != nil {
		t.Fatalf("go build: %v\n%s", err, out)
	}

	for _, s := range parityScenarios(t) {
		if s.harness != "claude" {
			continue
		}
		t.Run(s.name, func(t *testing.T) {
			ref := readReference(t, filepath.Join(parityDir, "claude", s.name+".txt"))
			home := t.TempDir()
			// The project directory is named like this repository so the
			// project ID matches the reference on any clone.
			project := filepath.Join(t.TempDir(), "jacazul-ai", "jacazul-ai-cli")
			fakeClaude := filepath.Join(home, ".local", "bin", "claude")
			for _, dir := range []string{project, filepath.Dir(fakeClaude)} {
				if err := os.MkdirAll(dir, 0o755); err != nil {
					t.Fatal(err)
				}
			}
			if err := os.WriteFile(fakeClaude, nil, 0o755); err != nil {
				t.Fatal(err)
			}

			cmd := exec.Command(bin, launcherArgs(s.args)...)
			cmd.Dir = project
			cmd.Env = []string{
				"HOME=" + home, "USER=" + os.Getenv("USER"), "LANG=C.UTF-8", "TERM=dumb",
				"PATH=/usr/local/bin:/usr/bin:/bin",
			}
			var stdout, stderr bytes.Buffer
			cmd.Stdout, cmd.Stderr = &stdout, &stderr
			code := 0
			if err := cmd.Run(); err != nil {
				exitErr, ok := err.(*exec.ExitError)
				if !ok {
					t.Fatal(err)
				}
				code = exitErr.ExitCode()
			}

			normalize := func(s string) string {
				s = strings.NewReplacer(home, "<HOME>", root, "<ROOT>").Replace(s)
				s = sessionID.ReplaceAllString(s, "${1}<SESSION>")
				return taskBinary.ReplaceAllString(s, "${1}<TASK>")
			}

			if want := strings.TrimSpace(ref["exit"]); fmt.Sprint(code) != want {
				t.Errorf("exit %d, want %s; stderr:\n%s", code, want, stderr.String())
			}
			want := normalize(withoutBashOnly(ref["stdout"]))
			want = strings.Replace(want, "🐊 Task Data: ", goTaskData+"\n🐊 Task Data: ", 1)
			if s.name == "resume" {
				want = strings.Replace(want, "🐊 Arguments for claude: \n", goResume+"\n", 1)
			}
			if got := normalize(stdout.String()); got != want {
				t.Errorf("stdout differs\n--- got ---\n%s\n--- want ---\n%s", got, want)
			}
			if got := normalize(stderr.String()); got != ref["stderr"] {
				t.Errorf("stderr differs\n--- got ---\n%s\n--- want ---\n%s", got, ref["stderr"])
			}
			if got := normalize(homeTree(t, home)); got != ref["home"] {
				t.Errorf("HOME tree differs\n--- got ---\n%s\n--- want ---\n%s", got, ref["home"])
			}
			settings := ".jacazul-ai/agents/claude/settings.json"
			data, err := os.ReadFile(filepath.Join(home, settings))
			if err != nil {
				t.Fatal(err)
			}
			if got := normalize(string(data)); strings.TrimSpace(got) != strings.TrimSpace(ref[settings]) {
				t.Errorf("settings.json differs\n--- got ---\n%s\n--- want ---\n%s", got, ref[settings])
			}
		})
	}
}

// launcherArgs turns a Bash launcher argument list into the Go command:
// --jacazul-session becomes jacazul's --session, everything else to the harness.
func launcherArgs(args string) []string {
	out := []string{"--dry", "--debug"}
	var harness []string
	fields := strings.Fields(args)
	if args == "-" {
		fields = nil
	}
	for i := 0; i < len(fields); i++ {
		if fields[i] == "--jacazul-session" && i+1 < len(fields) {
			out = append(out, "--session", fields[i+1])
			i++
			continue
		}
		harness = append(harness, fields[i])
	}
	return append(append(out, "claude"), harness...)
}

// readReference splits a reference into its "## name" sections.
func readReference(t *testing.T, path string) map[string]string {
	t.Helper()
	data, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	sections := map[string]string{}
	var name string
	for _, line := range strings.SplitAfter(string(data), "\n") {
		if strings.HasPrefix(line, "## ") {
			name = strings.TrimSpace(strings.TrimPrefix(line, "## "))
			sections[name] = ""
			continue
		}
		if name != "" {
			sections[name] += line
		}
	}
	// A blank line separates sections in the reference.
	for k, v := range sections {
		sections[k] = strings.TrimSuffix(v, "\n")
	}
	return sections
}

func withoutBashOnly(stdout string) string {
	var kept []string
	for _, line := range strings.SplitAfter(stdout, "\n") {
		if !slices.ContainsFunc(bashOnly, func(re *regexp.Regexp) bool {
			return re.MatchString(strings.TrimSuffix(line, "\n"))
		}) {
			kept = append(kept, line)
		}
	}
	return strings.Join(kept, "")
}

// homeTree lists home like the capture's find -printf '%y %p %l', sorted
// bytewise, without the venv.
func homeTree(t *testing.T, home string) string {
	t.Helper()
	var lines []string
	err := filepath.WalkDir(home, func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		rel, _ := filepath.Rel(home, path)
		rel = "./" + rel
		if rel == "./." {
			rel = "."
		}
		switch {
		case rel == "./.jacazul-ai/.venv" || rel == "./.local":
			return filepath.SkipDir
		case d.Type()&fs.ModeSymlink != 0:
			target, err := os.Readlink(path)
			if err != nil {
				return err
			}
			lines = append(lines, "l "+rel+" "+target)
		case d.IsDir():
			lines = append(lines, "d "+rel)
		default:
			lines = append(lines, "f "+rel)
		}
		return nil
	})
	if err != nil {
		t.Fatal(err)
	}
	slices.Sort(lines)
	return strings.Join(lines, "\n") + "\n"
}
