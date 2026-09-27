// Package persona embeds the persona voice specifications, the source the
// hatch renders them from, so the launcher can inject the active voice
// without a checkout.
package persona

import "embed"

// Voices holds persona_<id>.md for every built-in persona.
//
//go:embed persona_*.md
var Voices embed.FS
