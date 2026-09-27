// Package persona resolves the active persona and the signatures derived
// from it, mirroring scripts/bootstrap/persona.
package persona

import (
	"fmt"
	"strings"
)

type identity struct {
	display, name, signature string
}

var known = map[string]identity{
	"jacazul":  {"Jacazul (Jacaré Azul)", "Jacazul", "🐊 Jacazul"},
	"codama":   {"Codama", "Codama", "{🔷} Codama"},
	"arnalbam": {"Arnalbam", "Arnalbam", "{💪} Arnalbam"},
	"atena":    {"Atena", "Atena", "{🦉} Atena"},
}

// Input is what Resolve reads.
type Input struct {
	Getenv    func(string) string
	Project   string // persona from project.json or the legacy anchor
	Harness   string
	SessionID string
}

// Persona holds the values exported as JACAZUL_PERSONA and friends.
type Persona struct {
	ID                string
	Display           string
	Name              string
	Signature         string
	Model             string
	Harness           string
	SessionShort      string
	ResponseSignature string
	TaskSignature     string
	// Invalid reports that the requested persona was unknown and
	// Jacazul was used instead.
	Invalid bool
}

// Resolve picks the persona from JACAZUL_PERSONA, then the project, then
// Jacazul. The model falls through JACAZUL_MODEL, PI_MODEL, CLAUDE_MODEL,
// ANTHROPIC_MODEL and MODEL, skipping empty or unknown values.
func Resolve(in Input) Persona {
	id := in.Getenv("JACAZUL_PERSONA")
	if id == "" {
		id = in.Project
	}
	p := Persona{ID: "jacazul"}
	if id != "" {
		if _, ok := known[id]; ok {
			p.ID = id
		} else {
			p.Invalid = true
		}
	}
	who := known[p.ID]
	p.Display, p.Name, p.Signature = who.display, who.name, who.signature

	p.Model = "unspecified"
	for _, key := range []string{"JACAZUL_MODEL", "PI_MODEL", "CLAUDE_MODEL", "ANTHROPIC_MODEL", "MODEL"} {
		if v := in.Getenv(key); !unknownModel(v) {
			p.Model = v
			break
		}
	}

	p.Harness = in.Harness
	if p.Harness == "" {
		p.Harness = "unknown"
	}
	p.SessionShort = in.SessionID
	if p.SessionShort == "" {
		p.SessionShort = "global"
	}
	if len(p.SessionShort) > 8 {
		p.SessionShort = p.SessionShort[:8]
	}

	p.ResponseSignature = p.Signature
	p.TaskSignature = fmt.Sprintf("— %s (%s; harness: %s; session: %s)", p.Name, p.Model, p.Harness, p.SessionShort)
	return p
}

func unknownModel(v string) bool {
	switch strings.ToLower(v) {
	case "", "unspecified", "unknown", "none", "null":
		return true
	}
	return false
}
