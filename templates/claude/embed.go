// Package claude embeds the Claude Code settings template the launcher
// installs and merges permissions from.
package claude

import _ "embed"

// Settings is the settings.json template.
//
//go:embed settings.json
var Settings string
