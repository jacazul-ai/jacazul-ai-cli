// Package cli holds the jacazul launcher commands. Each harness gets its
// own command file; Run parses the arguments and dispatches.
package cli

import (
	"errors"
	"fmt"
	"io"

	"github.com/jessevdk/go-flags"
)

// Options are the flags accepted before the harness name. Everything after
// the harness name belongs to the harness.
type Options struct {
	Version bool   `short:"v" long:"version" description:"Print the launcher version and exit"`
	Dry     bool   `long:"dry" description:"Run every bootstrap step but do not start the harness (also DRY)"`
	Debug   bool   `long:"debug" description:"Print what each bootstrap step verifies (also DEBUG)"`
	Session string `long:"session" value-name:"ID" description:"Continue the Jacazul session ID instead of starting one"`
	// LegacySession is the Bash launchers' name for --session, kept until
	// the cutoff.
	LegacySession string `long:"jacazul-session" value-name:"ID" hidden:"true"`
}

// Run executes the launcher with args (without the program name) and
// returns the process exit code.
func Run(args []string, stdout, stderr io.Writer, version string) int {
	var opts Options
	parser := flags.NewParser(&opts, flags.HelpFlag|flags.PassAfterNonOption)
	parser.Name = "jacazul"
	parser.Usage = "[Options] <harness> [args...]\n\nHarnesses:\n  claude    Claude Code"

	rest, err := parser.ParseArgs(args)
	if opts.Version {
		fmt.Fprintln(stdout, version)
		return 0
	}
	if err != nil {
		var flagsErr *flags.Error
		if errors.As(err, &flagsErr) && flagsErr.Type == flags.ErrHelp {
			parser.WriteHelp(stdout)
			return 0
		}
		fmt.Fprintln(stderr, err)
		parser.WriteHelp(stderr)
		return 1
	}

	if len(rest) > 0 && rest[0] == "claude" {
		return runClaude(opts, rest[1:], stdout, stderr)
	}
	if len(rest) == 0 {
		fmt.Fprintln(stderr, "no harness given")
	} else {
		fmt.Fprintf(stderr, "unknown harness %q\n", rest[0])
	}
	parser.WriteHelp(stderr)
	return 1
}
