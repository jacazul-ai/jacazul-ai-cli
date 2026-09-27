// Package project resolves which Jacazul project a directory belongs to.
package project

import (
	"os/exec"
	"path/filepath"
	"strings"
)

// Identity is the canonical project of a directory.
type Identity struct {
	// Anchor is the project root: the git top level, or for a linked
	// worktree the directory holding the shared .git or .bare.
	Anchor string
	// ID scopes per-project state: "<parent>_<anchor>" by directory name.
	ID string
}

// Resolve returns the project identity of dir. Outside a git work tree,
// or without git installed, dir itself is the anchor.
func Resolve(dir string) (Identity, error) {
	abs, err := filepath.Abs(dir)
	if err != nil {
		return Identity{}, err
	}
	if real, err := filepath.EvalSymlinks(abs); err == nil {
		abs = real
	}

	anchor := abs
	if top := gitPath(abs, "--show-toplevel"); top != "" {
		anchor = top
		gitDir := gitPath(abs, "--path-format=absolute", "--git-dir")
		common := gitPath(abs, "--path-format=absolute", "--git-common-dir")
		if gitDir != "" && common != "" && gitDir != common {
			if base := filepath.Base(common); base == ".git" || base == ".bare" {
				anchor = filepath.Dir(common)
			}
		}
	}

	return Identity{
		Anchor: anchor,
		ID:     filepath.Base(filepath.Dir(anchor)) + "_" + filepath.Base(anchor),
	}, nil
}

// gitPath runs git rev-parse in dir and returns its output, or "" when dir
// is not in a work tree or git is unavailable.
func gitPath(dir string, args ...string) string {
	out, err := exec.Command("git", append([]string{"-C", dir, "rev-parse"}, args...)...).Output()
	if err != nil {
		return ""
	}
	return strings.TrimSpace(string(out))
}
