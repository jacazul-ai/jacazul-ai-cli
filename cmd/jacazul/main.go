package main

import (
	"os"
	"runtime/debug"

	"github.com/jacazul-ai/launcher/internal/cli"
)

func getVersion() string {
	if info, ok := debug.ReadBuildInfo(); ok && info.Main.Version != "" {
		return info.Main.Version
	}
	return "dev"
}

func main() {
	os.Exit(cli.Run(os.Args[1:], os.Stdout, os.Stderr, getVersion()))
}
