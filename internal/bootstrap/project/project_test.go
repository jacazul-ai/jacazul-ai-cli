package project

import (
	"os"
	"os/exec"
	"path/filepath"
	"testing"
)

func git(t *testing.T, dir string, args ...string) {
	t.Helper()
	cmd := exec.Command("git", append([]string{"-C", dir}, args...)...)
	cmd.Env = append(os.Environ(),
		"GIT_CONFIG_GLOBAL="+os.DevNull,
		"GIT_CONFIG_NOSYSTEM=1",
		"GIT_AUTHOR_NAME=t", "GIT_AUTHOR_EMAIL=t@example.invalid",
		"GIT_COMMITTER_NAME=t", "GIT_COMMITTER_EMAIL=t@example.invalid",
	)
	if out, err := cmd.CombinedOutput(); err != nil {
		t.Fatalf("git %v: %v\n%s", args, err, out)
	}
}

// root returns a temp dir with symlinks resolved, as pwd -P would.
func root(t *testing.T) string {
	t.Helper()
	dir, err := filepath.EvalSymlinks(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	return dir
}

func TestResolveOutsideGitUsesTheDirectory(t *testing.T) {
	dir := filepath.Join(root(t), "clients", "acme")
	if err := os.MkdirAll(dir, 0o755); err != nil {
		t.Fatal(err)
	}
	t.Setenv("GIT_CEILING_DIRECTORIES", filepath.Dir(dir))

	id, err := Resolve(dir)
	if err != nil {
		t.Fatal(err)
	}
	if id.Anchor != dir || id.ID != "clients_acme" {
		t.Fatalf("got %+v, want anchor %s and ID clients_acme", id, dir)
	}
}

func TestResolveRegularRepoUsesTheTopLevel(t *testing.T) {
	repo := filepath.Join(root(t), "org", "app")
	sub := filepath.Join(repo, "internal", "pkg")
	if err := os.MkdirAll(sub, 0o755); err != nil {
		t.Fatal(err)
	}
	git(t, repo, "init", "-q")

	id, err := Resolve(sub)
	if err != nil {
		t.Fatal(err)
	}
	if id.Anchor != repo || id.ID != "org_app" {
		t.Fatalf("got %+v, want anchor %s and ID org_app", id, repo)
	}
}

func TestResolveLinkedWorktreeUsesTheCommonDirParent(t *testing.T) {
	for _, common := range []string{".bare", ".git"} {
		t.Run(common, func(t *testing.T) {
			project := filepath.Join(root(t), "org", "app")
			main := filepath.Join(project, "main")
			if err := os.MkdirAll(main, 0o755); err != nil {
				t.Fatal(err)
			}
			git(t, project, "init", "-q", "--bare", common)
			git(t, filepath.Join(project, common), "worktree", "add", "-q", "--orphan", "-b", "main", main)

			id, err := Resolve(main)
			if err != nil {
				t.Fatal(err)
			}
			if id.Anchor != project || id.ID != "org_app" {
				t.Fatalf("got %+v, want anchor %s and ID org_app", id, project)
			}
		})
	}
}
