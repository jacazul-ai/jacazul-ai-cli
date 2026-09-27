// Package prompts embeds the session prompt templates the launcher renders.
package prompts

import _ "embed"

// Onboard is the session prompt template: the bootstrap protocol with the
// persona, mode, signature and language variables to substitute.
//
//go:embed onboard.md
var Onboard string
