package main

import (
	"fmt"
	"os"

	"github.com/jacazul-ai/jacazul-ai-cli/internal/cli"
)

func main() {
	app := cli.New()
	if err := app.Run(os.Args[1:]); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
