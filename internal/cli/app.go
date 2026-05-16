package cli

import (
	"fmt"

	flags "github.com/jessevdk/go-flags"
)

type App struct {
	parser *flags.Parser
	opts   *Options
}

type Options struct {
	Version bool           `long:"version" description:"Show version information"`
	Status  StatusCommand  `command:"status" description:"Show focused plan status"`
	Inis    InisCommand    `command:"inis" description:"List available plans"`
	Tree    TreeCommand    `command:"tree" description:"Show plan tree"`
	Roadmap RoadmapCommand `command:"roadmap" description:"Show roadmap data"`
}

type StatusCommand struct{}

type InisCommand struct{}

type TreeCommand struct {
	Args struct {
		Plan string `positional-arg-name:"plan" description:"Plan name" required:"true"`
	} `positional-args:"yes"`
}

type RoadmapCommand struct{}

func New() *App {
	opts := &Options{}
	parser := flags.NewParser(opts, flags.HelpFlag|flags.PassDoubleDash)
	parser.Name = "tw-flow"
	parser.ShortDescription = "tw-flow Go rewrite bootstrap"
	parser.LongDescription = "Initial Go bootstrap for the tw-flow rewrite."

	return &App{parser: parser, opts: opts}
}

func (a *App) Run(args []string) error {
	_, err := a.parser.ParseArgs(args)
	if err != nil {
		if fe, ok := err.(*flags.Error); ok && fe.Type == flags.ErrHelp {
			return nil
		}
		return err
	}

	if a.opts.Version {
		fmt.Println("tw-flow (go bootstrap)")
		return nil
	}

	return nil
}

func (c *StatusCommand) Execute(args []string) error {
	fmt.Println("status: not implemented yet")
	return nil
}

func (c *InisCommand) Execute(args []string) error {
	fmt.Println("inis: not implemented yet")
	return nil
}

func (c *TreeCommand) Execute(args []string) error {
	fmt.Printf("tree: not implemented yet for plan %q\n", c.Args.Plan)
	return nil
}

func (c *RoadmapCommand) Execute(args []string) error {
	fmt.Println("roadmap: not implemented yet")
	return nil
}

func X(a *string, b *string, c *string) {
}
