package cli

import (
	"bytes"
	"strings"
	"testing"
)

func run(t *testing.T, args ...string) (int, string, string) {
	t.Helper()
	var stdout, stderr bytes.Buffer
	code := Run(args, &stdout, &stderr, "v1.2.3")
	return code, stdout.String(), stderr.String()
}

func TestVersionFlagPrintsVersion(t *testing.T) {
	for _, flag := range []string{"-v", "--version"} {
		code, stdout, stderr := run(t, flag)
		if code != 0 {
			t.Fatalf("%s: exit %d, stderr %q", flag, code, stderr)
		}
		if stdout != "v1.2.3\n" {
			t.Fatalf("%s: stdout %q, want the version", flag, stdout)
		}
	}
}

func TestHelpGoesToStdoutAndSucceeds(t *testing.T) {
	code, stdout, _ := run(t, "--help")
	if code != 0 {
		t.Fatalf("exit %d, want 0", code)
	}
	if !strings.Contains(stdout, "Usage:") {
		t.Fatalf("stdout %q has no usage", stdout)
	}
}

func TestNoHarnessFailsWithHelpOnStderr(t *testing.T) {
	code, stdout, stderr := run(t)
	if code != 1 {
		t.Fatalf("exit %d, want 1", code)
	}
	if stdout != "" {
		t.Fatalf("stdout %q, want nothing", stdout)
	}
	if !strings.Contains(stderr, "Usage:") {
		t.Fatalf("stderr %q has no usage", stderr)
	}
}

func TestUnknownFlagFailsWithTheError(t *testing.T) {
	code, _, stderr := run(t, "--bogus")
	if code != 1 {
		t.Fatalf("exit %d, want 1", code)
	}
	if !strings.Contains(stderr, "bogus") {
		t.Fatalf("stderr %q does not name the flag", stderr)
	}
}
