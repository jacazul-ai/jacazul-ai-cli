// Package language resolves the chat and data languages, mirroring
// scripts/bootstrap/language.
package language

import (
	"encoding/json"
	"os"
)

// Pair is a chat and data language. An empty field is unset.
type Pair struct {
	Chat string `json:"chat"`
	Data string `json:"data"`
}

var defaults = Pair{Chat: "pt-br", Data: "en"}

// Resolve picks each language from, in order: the JACAZUL_CHAT_LANG and
// JACAZUL_DATA_LANG variables, the project's setting, the global file
// (JACAZUL_HOME/language.json) and the defaults. A missing or unreadable
// global file counts as unset.
func Resolve(getenv func(string) string, project Pair, globalPath string) Pair {
	var global Pair
	if data, err := os.ReadFile(globalPath); err == nil {
		_ = json.Unmarshal(data, &global)
	}
	return Pair{
		Chat: first(getenv("JACAZUL_CHAT_LANG"), project.Chat, global.Chat, defaults.Chat),
		Data: first(getenv("JACAZUL_DATA_LANG"), project.Data, global.Data, defaults.Data),
	}
}

func first(values ...string) string {
	for _, v := range values {
		if v != "" {
			return v
		}
	}
	return ""
}
