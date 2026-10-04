package claude

import (
	"bytes"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/jacazul-ai/launcher/internal/testutil"
	tmpl "github.com/jacazul-ai/launcher/templates/claude"
)

// The claude default reference was captured from the Bash launcher in a
// fresh HOME; Bootstrap must print its Claude lines and leave the same
// settings.json when run against this checkout.
func TestFreshHomeMatchesTheBashReference(t *testing.T) {
	data, err := os.ReadFile(filepath.Join(testutil.RepoRoot(t), "testdata", "parity", "claude", "default.txt"))
	if err != nil {
		t.Fatal(err)
	}
	ref := string(data)
	root := testutil.Checkout(t)
	home := t.TempDir()
	var out bytes.Buffer
	err = Bootstrap(Input{
		ConfigDir: ConfigDir("", filepath.Join(home, ".jacazul-ai")),
		Root:      root,
		Template:  tmpl.Settings,
		Debug:     true,
		Out:       &out,
	})
	if err != nil {
		t.Fatal(err)
	}
	normalize := strings.NewReplacer(home, "<HOME>", root, "<ROOT>").Replace

	stdout := section(ref, "stdout")
	first := strings.Index(stdout, "🐊 Creating Claude directory")
	last := strings.Index(stdout, "✅ Jacazul: Claude configuration verified.\n")
	if first < 0 || last < 0 {
		t.Fatal("reference lacks the Claude bootstrap lines")
	}
	want := stdout[first : last+len("✅ Jacazul: Claude configuration verified.\n")]
	if got := normalize(out.String()); got != want {
		t.Errorf("output differs from the Bash reference\n--- got ---\n%s\n--- want ---\n%s", got, want)
	}

	settings, err := os.ReadFile(filepath.Join(home, ".jacazul-ai", "agents", "claude", "settings.json"))
	if err != nil {
		t.Fatal(err)
	}
	want = section(ref, ".jacazul-ai/agents/claude/settings.json")
	if got := normalize(string(settings)); strings.TrimSpace(got) != strings.TrimSpace(want) {
		t.Errorf("settings differ from the Bash reference\n--- got ---\n%s\n--- want ---\n%s", got, want)
	}
}

// section returns the body of a "## name" section of a reference.
func section(ref, name string) string {
	_, body, ok := strings.Cut(ref, "## "+name+"\n")
	if !ok {
		return ""
	}
	if end := strings.Index(body, "\n## "); end >= 0 {
		body = body[:end+1]
	}
	return body
}
