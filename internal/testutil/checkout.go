// Package testutil holds what the launcher tests share.
package testutil

import (
	"os"
	"path/filepath"
	"testing"
)

// RepoRoot returns this repository's root, found from the test's working
// directory by its go.mod.
func RepoRoot(t testing.TB) string {
	t.Helper()
	dir, err := os.Getwd()
	if err != nil {
		t.Fatal(err)
	}
	for {
		if _, err := os.Stat(filepath.Join(dir, "go.mod")); err == nil {
			return dir
		}
		parent := filepath.Dir(dir)
		if parent == dir {
			t.Fatal("no go.mod above the test's working directory")
		}
		dir = parent
	}
}

// Checkout returns a source tree for the launcher to read, built in a
// temporary directory from this repository's scripts, extensions and skills.
// The jacazul-engine skill is always a stub: the hatch generates it and git
// ignores it, so a clean clone (CI) has none and a developer's tree has the
// real one. The stub makes the tests give the same result in both.
func Checkout(t testing.TB) string {
	t.Helper()
	repo := RepoRoot(t)
	root := t.TempDir()
	for _, dir := range []string{"scripts", "extensions"} {
		link(t, filepath.Join(repo, dir), filepath.Join(root, dir))
	}

	entries, err := os.ReadDir(filepath.Join(repo, "skills"))
	if err != nil {
		t.Fatal(err)
	}
	skills := filepath.Join(root, "skills")
	engine := filepath.Join(skills, "jacazul-engine")
	if err := os.MkdirAll(engine, 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(engine, "SKILL.md"), []byte("# jacazul-engine\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	for _, entry := range entries {
		if !entry.IsDir() || entry.Name() == "jacazul-engine" {
			continue
		}
		link(t, filepath.Join(repo, "skills", entry.Name()), filepath.Join(skills, entry.Name()))
	}
	return root
}

func link(t testing.TB, source, target string) {
	t.Helper()
	if err := os.Symlink(source, target); err != nil {
		t.Fatal(err)
	}
}
