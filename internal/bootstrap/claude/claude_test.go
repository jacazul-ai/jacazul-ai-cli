package claude

import (
	"bytes"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

const template = `{
  "permissions": {
    "allow": [
      "Skill(tw)",
      "Bash(tw-flow:*)"
    ]
  },
  "attribution": {
    "commit": ""
  }
}
`

// checkout builds a source tree with the given skills, each hosted by the
// harnesses listed after the colon (none means every harness), plus the
// status line extension.
func checkout(t *testing.T, skills ...string) string {
	t.Helper()
	root := t.TempDir()
	for _, s := range skills {
		name, hosts, _ := strings.Cut(s, ":")
		write(t, filepath.Join(root, "skills", name, "SKILL.md"), "# "+name+"\n")
		if hosts != "" {
			write(t, filepath.Join(root, "skills", name, "HOSTS"), strings.ReplaceAll(hosts, ",", "\n")+"\n")
		}
	}
	write(t, filepath.Join(root, "extensions", "claude", "jacazul-line.sh"), "#!/bin/bash\n")
	return root
}

func run(t *testing.T, in Input) string {
	t.Helper()
	var out bytes.Buffer
	in.Out = &out
	if in.Template == "" {
		in.Template = template
	}
	if err := Bootstrap(in); err != nil {
		t.Fatal(err)
	}
	return out.String()
}

func read(t *testing.T, path string) string {
	t.Helper()
	data, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	return string(data)
}

func write(t *testing.T, path, content string) {
	t.Helper()
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(path, []byte(content), 0o644); err != nil {
		t.Fatal(err)
	}
}

func link(t *testing.T, target, path string) {
	t.Helper()
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.Symlink(target, path); err != nil {
		t.Fatal(err)
	}
}

func readlink(t *testing.T, path string) string {
	t.Helper()
	target, err := os.Readlink(path)
	if err != nil {
		t.Fatal(err)
	}
	return target
}

func TestConfigDir(t *testing.T) {
	if got := ConfigDir("/custom", "/j"); got != "/custom" {
		t.Errorf("preset CLAUDE_CONFIG_DIR: got %q", got)
	}
	if got := ConfigDir("", "/j"); got != "/j/agents/claude" {
		t.Errorf("default: got %q", got)
	}
}

func TestFreshConfigDebug(t *testing.T) {
	root := checkout(t, "b-skill", "a-skill", "pi-only:pi", "both:pi,claude")
	write(t, filepath.Join(root, "skills", "no-skill-md", "README.md"), "")
	write(t, filepath.Join(root, "skills", "loose-file"), "")
	dir := filepath.Join(t.TempDir(), "agents", "claude")

	out := run(t, Input{ConfigDir: dir, Root: root, Debug: true})

	want := "🐊 Creating Claude directory at " + dir + "...\n" +
		"🐊 Initializing Claude settings.json from template...\n" +
		"✅ Jacazul: Claude settings.json verified (SessionStart hook active).\n" +
		"🐊 Creating Claude skills directory at " + dir + "/skills...\n" +
		"🐊 Linking global Claude skill: a-skill\n" +
		"🐊 Linking global Claude skill: b-skill\n" +
		"🐊 Linking global Claude skill: both\n" +
		"🐊 Creating Claude extensions directory at " + dir + "/extensions...\n" +
		"🐊 Linking Claude extension: jacazul-line.sh\n" +
		"✅ Jacazul: Claude configuration verified.\n"
	if out != want {
		t.Errorf("output:\n%s\nwant:\n%s", out, want)
	}
	for _, name := range []string{"a-skill", "b-skill", "both"} {
		if got := readlink(t, filepath.Join(dir, "skills", name)); got != filepath.Join(root, "skills", name) {
			t.Errorf("skill %s links to %q", name, got)
		}
	}
	for _, name := range []string{"pi-only", "no-skill-md", "loose-file"} {
		if _, err := os.Lstat(filepath.Join(dir, "skills", name)); !os.IsNotExist(err) {
			t.Errorf("skill %s should not be linked: %v", name, err)
		}
	}
	line := filepath.Join(dir, "extensions", "jacazul-line.sh")
	if got := readlink(t, line); got != filepath.Join(root, "extensions", "claude", "jacazul-line.sh") {
		t.Errorf("extension links to %q", got)
	}

	wantSettings := `{
  "permissions": {
    "allow": [
      "Bash(tw-flow:*)",
      "Skill(tw)"
    ]
  },
  "attribution": {
    "commit": ""
  },
  "statusLine": {
    "type": "command",
    "command": "` + line + `"
  }
}
`
	if got := read(t, filepath.Join(dir, "settings.json")); got != wantSettings {
		t.Errorf("settings:\n%s\nwant:\n%s", got, wantSettings)
	}
}

func TestFreshConfigQuiet(t *testing.T) {
	dir := filepath.Join(t.TempDir(), "claude")
	out := run(t, Input{ConfigDir: dir, Root: checkout(t, "a-skill")})
	want := "🐊 Creating Claude directory at " + dir + "...\n" +
		"🐊 Initializing Claude settings.json from template...\n"
	if out != want {
		t.Errorf("output:\n%s\nwant:\n%s", out, want)
	}
}

func TestSecondRunIsSilent(t *testing.T) {
	dir := filepath.Join(t.TempDir(), "claude")
	in := Input{ConfigDir: dir, Root: checkout(t, "a-skill")}
	run(t, in)
	before := read(t, filepath.Join(dir, "settings.json"))
	if out := run(t, in); out != "" {
		t.Errorf("second run printed:\n%s", out)
	}
	if after := read(t, filepath.Join(dir, "settings.json")); after != before {
		t.Errorf("second run changed settings:\n%s", after)
	}
}

func TestExistingSettingsKeepUserState(t *testing.T) {
	dir := t.TempDir()
	settings := filepath.Join(dir, "settings.json")
	write(t, settings, `{"model": "opus", "permissions": {"deny": ["Bash(rm:*)"], "allow": ["Zed(x)", "Skill(tw)"]},
  "statusLine": {"type": "command", "command": "~/my-line.sh"}, "note": "<a&b>"}`)

	run(t, Input{ConfigDir: dir, Root: checkout(t)})

	want := `{
  "model": "opus",
  "permissions": {
    "deny": [
      "Bash(rm:*)"
    ],
    "allow": [
      "Bash(tw-flow:*)",
      "Skill(tw)",
      "Zed(x)"
    ]
  },
  "statusLine": {
    "type": "command",
    "command": "~/my-line.sh"
  },
  "note": "<a&b>"
}
`
	if got := read(t, settings); got != want {
		t.Errorf("settings:\n%s\nwant:\n%s", got, want)
	}
}

func TestOwnedStatusLineIsRewrittenInPlace(t *testing.T) {
	for name, value := range map[string]string{
		"null":   `null`,
		"string": `"/old/checkout/extensions/claude/jacazul-line.sh"`,
		"object": `{"type": "command", "command": "/old/agents/claude/extensions/jacazul-line.sh", "padding": 1}`,
	} {
		t.Run(name, func(t *testing.T) {
			dir := t.TempDir()
			settings := filepath.Join(dir, "settings.json")
			write(t, settings, `{"statusLine": `+value+`, "model": "opus"}`)

			run(t, Input{ConfigDir: dir, Root: checkout(t)})

			want := `{
  "statusLine": {
    "type": "command",
    "command": "` + filepath.Join(dir, "extensions", "jacazul-line.sh") + `"
  },
  "model": "opus",
  "permissions": {
    "allow": [
      "Bash(tw-flow:*)",
      "Skill(tw)"
    ]
  }
}
`
			if got := read(t, settings); got != want {
				t.Errorf("settings:\n%s\nwant:\n%s", got, want)
			}
		})
	}
}

func TestNoStatusLineWithoutExtension(t *testing.T) {
	root := checkout(t)
	if err := os.Remove(filepath.Join(root, "extensions", "claude", "jacazul-line.sh")); err != nil {
		t.Fatal(err)
	}
	dir := t.TempDir()
	run(t, Input{ConfigDir: dir, Root: root})
	if got := read(t, filepath.Join(dir, "settings.json")); strings.Contains(got, "statusLine") {
		t.Errorf("statusLine set without the extension:\n%s", got)
	}
}

func TestInvalidSettingsFail(t *testing.T) {
	dir := t.TempDir()
	settings := filepath.Join(dir, "settings.json")
	write(t, settings, `{"permissions": `)
	err := Bootstrap(Input{ConfigDir: dir, Root: checkout(t), Template: template, Out: &bytes.Buffer{}})
	if err == nil || !strings.Contains(err.Error(), settings) {
		t.Fatalf("want an error naming %s, got %v", settings, err)
	}
	if got := read(t, settings); got != `{"permissions": ` {
		t.Errorf("invalid settings were rewritten: %q", got)
	}
}

func TestLinksAreRepaired(t *testing.T) {
	root := checkout(t, "good", "moved", "pi-only:pi")
	dir := t.TempDir()
	skills := filepath.Join(dir, "skills")
	link(t, filepath.Join(root, "skills", "good"), filepath.Join(skills, "good"))
	link(t, "/old/checkout/skills/moved", filepath.Join(skills, "moved"))
	link(t, filepath.Join(root, "skills", "pi-only"), filepath.Join(skills, "pi-only"))
	link(t, "/old/checkout/extensions/claude/jacazul-line.sh", filepath.Join(dir, "extensions", "jacazul-line.sh"))

	out := run(t, Input{ConfigDir: dir, Root: root, Debug: true})

	for _, line := range []string{
		"⚠️  Claude skill moved points to wrong location. Re-linking...\n",
		"🐊 Unlinking skill not hosted by claude: pi-only\n",
		"⚠️  Claude extension jacazul-line.sh points to wrong location. Re-linking...\n",
	} {
		if !strings.Contains(out, line) {
			t.Errorf("output lacks %q:\n%s", line, out)
		}
	}
	if strings.Contains(out, "skill: good") || strings.Contains(out, "skill good") {
		t.Errorf("a correct link was touched:\n%s", out)
	}
	if got := readlink(t, filepath.Join(skills, "moved")); got != filepath.Join(root, "skills", "moved") {
		t.Errorf("moved links to %q", got)
	}
	if _, err := os.Lstat(filepath.Join(skills, "pi-only")); !os.IsNotExist(err) {
		t.Errorf("pi-only link kept: %v", err)
	}
}

func TestUnhostedSkillMessageIsNotDebugOnly(t *testing.T) {
	root := checkout(t, "pi-only:pi")
	dir := t.TempDir()
	link(t, filepath.Join(root, "skills", "pi-only"), filepath.Join(dir, "skills", "pi-only"))
	write(t, filepath.Join(dir, "settings.json"), template)
	if out := run(t, Input{ConfigDir: dir, Root: root}); out != "🐊 Unlinking skill not hosted by claude: pi-only\n" {
		t.Errorf("output: %q", out)
	}
}

func TestUserDirectoryIsLeftAlone(t *testing.T) {
	root := checkout(t, "mine")
	dir := t.TempDir()
	own := filepath.Join(dir, "skills", "mine", "SKILL.md")
	write(t, own, "# user skill\n")
	write(t, filepath.Join(dir, "settings.json"), template)

	out := run(t, Input{ConfigDir: dir, Root: root})

	if want := "⚠️  Claude skill mine is not a link; leaving " + filepath.Dir(own) + " untouched.\n"; out != want {
		t.Errorf("output: %q, want %q", out, want)
	}
	if got := read(t, own); got != "# user skill\n" {
		t.Errorf("user skill changed: %q", got)
	}
	entries, err := os.ReadDir(filepath.Dir(own))
	if err != nil {
		t.Fatal(err)
	}
	if len(entries) != 1 {
		t.Errorf("a link was created inside the user directory: %v", entries)
	}
}
