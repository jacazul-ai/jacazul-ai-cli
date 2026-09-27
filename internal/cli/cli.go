// Package cli holds the jacazul launcher commands. Each harness gets its
// own command file; Run parses the arguments and dispatches.
package cli

import (
	"errors"
	"fmt"
	"io"

	"github.com/jessevdk/go-flags"
)

// Options are the flags accepted before the harness name.
type Options struct {
	Version bool `short:"v" long:"version" description:"Print the launcher version and exit"`
}

// Run executes the launcher with args (without the program name) and
// returns the process exit code.
func Run(args []string, stdout, stderr io.Writer, version string) int {
	var opts Options
	parser := flags.NewParser(&opts, flags.HelpFlag)
	parser.Name = "jacazul"
	parser.Usage = "[Options] <harness> [args...]"

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

	if len(rest) == 0 {
		fmt.Fprintln(stderr, "no harness given")
	} else {
		fmt.Fprintf(stderr, "unknown harness %q\n", rest[0])
	}
	parser.WriteHelp(stderr)
	return 1
}
