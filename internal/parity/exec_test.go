package parity

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"slices"
	"strings"
	"testing"
)

// The DRY references stop before the harness. The exec references
// (testdata/parity/capture --exec) hold what the Bash launcher handed to
// claude, observed by testdata/parity/fake-claude: its arguments and its
// environment. The Go launcher must hand over the same.

// ignoredEnv depends on the machine's Taskwarrior install, not on the launcher.
var ignoredEnv = map[string]bool{
	"JACAZUL_REAL_TASK":    true,
	"JACAZUL_TASK_VERSION": true,
}

// bashOnlyEnv are variables the Go launcher does not export, on purpose.
// Only the Bash scripts that set them read them.
var bashOnlyEnv = map[string]string{
	"CURRENT_DIR":               "scratch value of the Bash project identity",
	"PARENT_DIR":                "scratch value of the Bash project identity",
	"JACAZUL_PROJECT_ANCHOR":    "read only by scripts/bootstrap/project-identity",
	"JACAZUL_PERSONA_SPEC_FILE": "the Go launcher renders the voice from embedded templates",
}

// goOnlyEnv are variables only the Go launcher exports.
var goOnlyEnv = map[string]string{}

// goResumeArgs is where the Go launcher differs from the Bash one on
// --resume: the argument reaches claude and the session prompt stays, while
// the Bash launcher swallowed both (see goResume in claude_test.go).
const goResumeArgs = "--append-system-prompt\n[ONBOARD_PROMPT]\n--resume\n"

// The capture normalizes these lines the same way; see testdata/parity/capture.
var envNormalize = []struct {
	re *regexp.Regexp
	to string
}{
	{regexp.MustCompile(`(?m)^(CONTEXT_REAL_PATH)=.*$`), "${1}=<PROJECT>"},
	{regexp.MustCompile(`(?m)^(JACAZUL_PROJECT_ANCHOR)=.*$`), "${1}=<ANCHOR>"},
	{regexp.MustCompile(`(?m)^(USER|CONTEXT_GIT_USER|CONTEXT_SYSTEM_USER)=.*$`), "${1}=<USER>"},
}

var sessionEnv = regexp.MustCompile(`(?m)^JACAZUL_SESSION_ID=([0-9a-f]{8})$`)

func TestParityClaudeExecMatchesTheBashLauncher(t *testing.T) {
	bin, root := buildLauncher(t)
	fake, err := os.ReadFile(filepath.Join(parityDir, "fake-claude"))
	if err != nil {
		t.Fatal(err)
	}

	for _, s := range parityScenarios(t) {
		if s.harness != "claude" {
			continue
		}
		t.Run(s.name, func(t *testing.T) {
			ref := readReference(t, filepath.Join(parityDir, "claude", s.name+".exec.txt"))
			home := t.TempDir()
			// The project directory is named like this repository so the
			// project ID matches the reference on any clone.
			project := filepath.Join(t.TempDir(), "jacazul-ai", "jacazul-ai-cli")
			claude := filepath.Join(home, ".local", "bin", "claude")
			// The capture gives each HOME its own venv; the launcher exports
			// VIRTUAL_ENV when one exists.
			venv := filepath.Join(home, ".jacazul-ai", ".venv")
			for _, dir := range []string{project, filepath.Dir(claude), venv} {
				if err := os.MkdirAll(dir, 0o755); err != nil {
					t.Fatal(err)
				}
			}
			if err := os.WriteFile(claude, fake, 0o755); err != nil {
				t.Fatal(err)
			}
			recorded := filepath.Join(home, "claude.out")

			cmd := exec.Command(bin, launcherArgs(s.args)...)
			cmd.Dir = project
			cmd.Env = []string{
				"HOME=" + home, "USER=" + os.Getenv("USER"), "LANG=C.UTF-8", "TERM=dumb",
				"PATH=/usr/local/bin:/usr/bin:/bin", "FAKE_CLAUDE_OUT=" + recorded,
			}
			out, err := cmd.CombinedOutput()
			code := 0
			if exitErr, ok := err.(*exec.ExitError); ok {
				code = exitErr.ExitCode()
			} else if err != nil {
				t.Fatal(err)
			}
			if want := strings.TrimSpace(ref["exit"]); fmt.Sprint(code) != want {
				t.Fatalf("exit %d, want %s; output:\n%s", code, want, out)
			}

			got := readReference(t, recorded)
			normalize := func(section string) string {
				for _, n := range envNormalize {
					section = n.re.ReplaceAllString(section, n.to)
				}
				section = strings.NewReplacer(home, "<HOME>", root, "<ROOT>", project, "<PROJECT>").Replace(section)
				if !strings.Contains(s.args, "--jacazul-session") {
					if m := sessionEnv.FindStringSubmatch(section); m != nil {
						section = strings.ReplaceAll(section, m[1], "<SESSION>")
					}
				}
				return section
			}

			wantArgs := ref["args"]
			if s.name == "resume" {
				wantArgs = goResumeArgs
			}
			if gotArgs := normalize(got["args"]); gotArgs != wantArgs {
				t.Errorf("arguments differ\n--- got ---\n%s\n--- want ---\n%s", gotArgs, wantArgs)
			}
			for _, d := range envDiff(envMap(ref["env"]), envMap(normalize(got["env"]))) {
				t.Error(d)
			}
		})
	}
}

// envMap reads sorted KEY=value lines.
func envMap(section string) map[string]string {
	env := map[string]string{}
	for _, line := range strings.Split(section, "\n") {
		if key, value, ok := strings.Cut(line, "="); ok {
			env[key] = value
		}
	}
	return env
}

// envDiff lists how got differs from want, apart from the machine-bound and
// accepted differences above.
func envDiff(want, got map[string]string) []string {
	var diffs []string
	for key, w := range want {
		g, ok := got[key]
		switch {
		case ignoredEnv[key]:
		case bashOnlyEnv[key] != "" && !ok:
		case !ok:
			diffs = append(diffs, fmt.Sprintf("%s is missing, the Bash launcher exports %q", key, w))
		case g != w:
			diffs = append(diffs, fmt.Sprintf("%s=%q, the Bash launcher exports %q", key, g, w))
		}
	}
	for key, g := range got {
		if _, ok := want[key]; !ok && !ignoredEnv[key] && goOnlyEnv[key] == "" {
			diffs = append(diffs, fmt.Sprintf("%s=%q is exported only by the Go launcher", key, g))
		}
	}
	slices.Sort(diffs)
	return diffs
}
