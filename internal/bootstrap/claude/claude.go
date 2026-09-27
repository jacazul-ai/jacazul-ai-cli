// Package claude prepares the Claude Code config directory, mirroring
// scripts/bootstrap/claude: settings.json from the template, the skill
// links honoring HOSTS and the status line extension.
package claude

import (
	"bufio"
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"io/fs"
	"os"
	"path/filepath"
	"slices"
	"strings"
)

// statusLine is the extension whose path the status line points at.
const statusLine = "jacazul-line.sh"

// Input is what Bootstrap reads.
type Input struct {
	ConfigDir string // CLAUDE_CONFIG_DIR
	// Root is the checkout holding skills/ and extensions/claude/.
	Root string
	// Template is the settings.json template.
	Template string
	Debug    bool
	Out      io.Writer
}

// ConfigDir is a preset CLAUDE_CONFIG_DIR, else the directory under
// JACAZUL_HOME.
func ConfigDir(preset, home string) string {
	if preset != "" {
		return preset
	}
	return filepath.Join(home, "agents", "claude")
}

// Bootstrap creates the config directory, merges the template's
// permissions into settings.json, links the skills and the extension and
// points the status line at it. User entries and a user-owned status line
// are never touched.
func Bootstrap(in Input) error {
	if !exists(in.ConfigDir) {
		fmt.Fprintf(in.Out, "🐊 Creating Claude directory at %s...\n", in.ConfigDir)
		if err := os.MkdirAll(in.ConfigDir, 0o755); err != nil {
			return err
		}
	}

	settingsFile := filepath.Join(in.ConfigDir, "settings.json")
	current, err := os.ReadFile(settingsFile)
	if errors.Is(err, fs.ErrNotExist) {
		fmt.Fprintln(in.Out, "🐊 Initializing Claude settings.json from template...")
		if err := os.WriteFile(settingsFile, []byte(in.Template), 0o644); err != nil {
			return err
		}
		current = []byte(in.Template)
	} else if err != nil {
		return err
	}
	settings, err := parseObject(current)
	if err != nil {
		return fmt.Errorf("%s is not a JSON object (%w); fix or remove it and launch again", settingsFile, err)
	}
	if err := mergeAllow(&settings, in.Template); err != nil {
		return fmt.Errorf("%s: %w; fix permissions.allow and launch again", settingsFile, err)
	}
	if in.Debug {
		fmt.Fprintln(in.Out, "✅ Jacazul: Claude settings.json verified (SessionStart hook active).")
	}

	skillsDir := filepath.Join(in.ConfigDir, "skills")
	if !exists(skillsDir) {
		if in.Debug {
			fmt.Fprintf(in.Out, "🐊 Creating Claude skills directory at %s...\n", skillsDir)
		}
		if err := os.MkdirAll(skillsDir, 0o755); err != nil {
			return err
		}
	}
	entries, err := os.ReadDir(filepath.Join(in.Root, "skills"))
	if err != nil && !errors.Is(err, fs.ErrNotExist) {
		return err
	}
	for _, entry := range entries {
		name := entry.Name()
		source := filepath.Join(in.Root, "skills", name)
		target := filepath.Join(skillsDir, name)
		if !isDir(source) || !isFile(filepath.Join(source, "SKILL.md")) {
			continue
		}
		hosted, err := hostedByClaude(source)
		if err != nil {
			return err
		}
		if !hosted {
			if isLink(target) {
				if err := os.Remove(target); err != nil {
					return err
				}
				fmt.Fprintf(in.Out, "🐊 Unlinking skill not hosted by claude: %s\n", name)
			}
			continue
		}
		if err := ensureLink(in, "skill", "Linking global Claude skill", source, target); err != nil {
			return err
		}
	}

	extensionsDir := filepath.Join(in.ConfigDir, "extensions")
	if !exists(extensionsDir) {
		if in.Debug {
			fmt.Fprintf(in.Out, "🐊 Creating Claude extensions directory at %s...\n", extensionsDir)
		}
		if err := os.MkdirAll(extensionsDir, 0o755); err != nil {
			return err
		}
	}
	line := filepath.Join(extensionsDir, statusLine)
	if source := filepath.Join(in.Root, "extensions", "claude", statusLine); isFile(source) {
		if err := ensureLink(in, "extension", "Linking Claude extension", source, line); err != nil {
			return err
		}
	}

	if isFile(line) {
		if err := pointStatusLine(&settings, line); err != nil {
			return err
		}
	}
	if err := writeIfChanged(settingsFile, current, settings); err != nil {
		return err
	}
	if in.Debug {
		fmt.Fprintln(in.Out, "✅ Jacazul: Claude configuration verified.")
	}
	return nil
}

// hostedByClaude reports whether a skill serves claude: a skill without a
// HOSTS file serves every harness, otherwise one line must read claude.
func hostedByClaude(skill string) (bool, error) {
	f, err := os.Open(filepath.Join(skill, "HOSTS"))
	if errors.Is(err, fs.ErrNotExist) {
		return true, nil
	}
	if err != nil {
		return false, err
	}
	defer f.Close()
	scanner := bufio.NewScanner(f)
	for scanner.Scan() {
		if scanner.Text() == "claude" {
			return true, nil
		}
	}
	return false, scanner.Err()
}

// ensureLink points target at source. A correct link stays, a wrong one
// is replaced, and anything that is not a link belongs to the user.
func ensureLink(in Input, kind, linking, source, target string) error {
	name := filepath.Base(target)
	info, err := os.Lstat(target)
	switch {
	case errors.Is(err, fs.ErrNotExist):
		if in.Debug {
			fmt.Fprintf(in.Out, "🐊 %s: %s\n", linking, name)
		}
	case err != nil:
		return err
	case info.Mode()&fs.ModeSymlink == 0:
		fmt.Fprintf(in.Out, "⚠️  Claude %s %s is not a link; leaving %s untouched.\n", kind, name, target)
		return nil
	case resolve(target) == resolve(source):
		return nil
	default:
		if in.Debug {
			fmt.Fprintf(in.Out, "⚠️  Claude %s %s points to wrong location. Re-linking...\n", kind, name)
		}
		if err := os.Remove(target); err != nil {
			return err
		}
	}
	return os.Symlink(source, target)
}

// resolve follows every link like readlink -f; a broken link resolves to
// itself, so it never matches its source.
func resolve(path string) string {
	if real, err := filepath.EvalSymlinks(path); err == nil {
		return real
	}
	return path
}

// mergeAllow adds the template's permissions.allow to the settings as a
// sorted set, the result of jq's unique.
func mergeAllow(settings *object, template string) error {
	tmpl, err := parseObject([]byte(template))
	if err != nil {
		return fmt.Errorf("settings template: %w", err)
	}
	tmplPerms, err := permissionsOf(tmpl)
	if err != nil {
		return fmt.Errorf("settings template: %w", err)
	}
	adds, err := allowOf(tmplPerms)
	if err != nil {
		return fmt.Errorf("settings template: %w", err)
	}
	perms, err := permissionsOf(*settings)
	if err != nil {
		return err
	}
	allow, err := allowOf(perms)
	if err != nil {
		return err
	}
	allow = append(allow, adds...)
	slices.Sort(allow)
	allow = slices.Compact(allow)
	raw, err := marshal(allow)
	if err != nil {
		return err
	}
	perms.set("allow", raw)
	if raw, err = perms.marshal(); err != nil {
		return err
	}
	settings.set("permissions", raw)
	return nil
}

// permissionsOf returns the permissions object, empty when unset.
func permissionsOf(settings object) (object, error) {
	raw, ok := settings.get("permissions")
	if !ok || isNull(raw) {
		return object{}, nil
	}
	perms, err := parseObject(raw)
	if err != nil {
		return nil, fmt.Errorf("permissions: %w", err)
	}
	return perms, nil
}

func allowOf(perms object) ([]string, error) {
	raw, ok := perms.get("allow")
	if !ok || isNull(raw) {
		return nil, nil
	}
	var allow []string
	if err := json.Unmarshal(raw, &allow); err != nil {
		return nil, fmt.Errorf("permissions.allow is not a list of strings: %w", err)
	}
	return allow, nil
}

// pointStatusLine sets the status line to the extension when it is unset
// or still points at a Jacazul-owned entrypoint.
func pointStatusLine(settings *object, line string) error {
	raw, ok := settings.get("statusLine")
	if ok && !isNull(raw) && !ownedStatusLine(raw) {
		return nil
	}
	value, err := marshal(struct {
		Type    string `json:"type"`
		Command string `json:"command"`
	}{"command", line})
	if err != nil {
		return err
	}
	settings.set("statusLine", value)
	return nil
}

func ownedStatusLine(raw json.RawMessage) bool {
	var command string
	if json.Unmarshal(raw, &command) != nil {
		var line struct {
			Command any `json:"command"`
		}
		if json.Unmarshal(raw, &line) != nil {
			return false
		}
		command, _ = line.Command.(string)
	}
	return strings.HasSuffix(command, "/"+statusLine)
}

// writeIfChanged replaces the settings file atomically, keeping its mode,
// when the rendered settings differ from what was read.
func writeIfChanged(path string, current []byte, settings object) error {
	data, err := settings.marshal()
	if err != nil {
		return err
	}
	var out bytes.Buffer
	if err := json.Indent(&out, data, "", "  "); err != nil {
		return err
	}
	out.WriteByte('\n')
	if bytes.Equal(out.Bytes(), current) {
		return nil
	}
	info, err := os.Stat(path)
	if err != nil {
		return err
	}
	tmp, err := os.CreateTemp(filepath.Dir(path), ".settings-*.json")
	if err != nil {
		return err
	}
	defer os.Remove(tmp.Name())
	if _, err := tmp.Write(out.Bytes()); err != nil {
		tmp.Close()
		return err
	}
	if err := tmp.Close(); err != nil {
		return err
	}
	if err := os.Chmod(tmp.Name(), info.Mode().Perm()); err != nil {
		return err
	}
	return os.Rename(tmp.Name(), path)
}

func exists(path string) bool {
	_, err := os.Stat(path)
	return err == nil
}

func isDir(path string) bool {
	info, err := os.Stat(path)
	return err == nil && info.IsDir()
}

func isFile(path string) bool {
	info, err := os.Stat(path)
	return err == nil && info.Mode().IsRegular()
}

func isLink(path string) bool {
	info, err := os.Lstat(path)
	return err == nil && info.Mode()&fs.ModeSymlink != 0
}
