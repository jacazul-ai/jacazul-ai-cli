// Package onboard renders the session prompt the launcher hands to the
// harness, mirroring scripts/bootstrap/onboard: prompts/onboard.md with
// its variables substituted, followed by the active persona's voice.
package onboard

import (
	"fmt"
	"regexp"
	"strings"

	voices "github.com/jacazul-ai/launcher/jacazul/hatch/templates/persona"
	"github.com/jacazul-ai/launcher/prompts"
)

// Vars are the values the template refers to.
type Vars struct {
	PersonaDisplay    string // $JACAZUL_PERSONA_DISPLAY
	PersonaSignature  string // $JACAZUL_PERSONA_SIGNATURE
	ResponseSignature string // $JACAZUL_RESPONSE_SIGNATURE
	TaskSignature     string // $JACAZUL_TASK_SIGNATURE
	Mode              string // $JACAZUL_MODE
	ChatLang          string // $JACAZUL_CHAT_LANG
	DataLang          string // $JACAZUL_DATA_LANG
}

var variable = regexp.MustCompile(`\$\{?([A-Za-z_][A-Za-z0-9_]*)\}?`)

// Prompt renders the embedded template for persona and appends its voice.
func Prompt(persona string, vars Vars) (string, error) {
	voice, err := voices.Voices.ReadFile("persona_" + persona + ".md")
	if err != nil {
		return "", fmt.Errorf("no voice for persona %q: %w", persona, err)
	}
	return Render(prompts.Onboard, vars) + "\n\n" + strings.TrimRight(string(voice), "\n"), nil
}

// Render substitutes $NAME and ${NAME} in tmpl. Unknown names become
// empty, as in the shell; nothing in the template is ever executed, unlike
// the Bash bootstrap's eval.
func Render(tmpl string, vars Vars) string {
	values := map[string]string{
		"JACAZUL_PERSONA_DISPLAY":    vars.PersonaDisplay,
		"JACAZUL_PERSONA_SIGNATURE":  vars.PersonaSignature,
		"JACAZUL_RESPONSE_SIGNATURE": vars.ResponseSignature,
		"JACAZUL_TASK_SIGNATURE":     vars.TaskSignature,
		"JACAZUL_MODE":               vars.Mode,
		"JACAZUL_CHAT_LANG":          vars.ChatLang,
		"JACAZUL_DATA_LANG":          vars.DataLang,
	}
	out := variable.ReplaceAllStringFunc(tmpl, func(m string) string {
		return values[variable.FindStringSubmatch(m)[1]]
	})
	return strings.TrimRight(out, "\n")
}
