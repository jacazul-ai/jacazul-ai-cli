package onboard

import (
	"os"
	"path/filepath"
	"testing"
)

// The references were produced by scripts/bootstrap/onboard for these
// values; the Go render must match them byte for byte.
func TestRenderMatchesTheBashBootstrap(t *testing.T) {
	cases := []struct {
		persona string
		vars    Vars
	}{
		{"jacazul", Vars{
			PersonaDisplay: "Jacazul (Jacaré Azul)", PersonaSignature: "🐊 Jacazul",
			ResponseSignature: "🐊 Jacazul",
			TaskSignature:     "— Jacazul (unspecified; harness: claude; session: abcd1234)",
			Mode:              "COUNSELOR", ChatLang: "pt-br", DataLang: "en",
		}},
		{"arnalbam", Vars{
			PersonaDisplay: "Arnalbam", PersonaSignature: "{💪} Arnalbam",
			ResponseSignature: "{💪} Arnalbam",
			TaskSignature:     "— Arnalbam (unspecified; harness: claude; session: abcd1234)",
			Mode:              "COUNSELOR", ChatLang: "pt-br", DataLang: "en",
		}},
	}
	for _, c := range cases {
		t.Run(c.persona, func(t *testing.T) {
			want, err := os.ReadFile(filepath.Join("..", "..", "..", "testdata", "parity", "onboard", c.persona+".txt"))
			if err != nil {
				t.Fatal(err)
			}
			got, err := Prompt(c.persona, c.vars)
			if err != nil {
				t.Fatal(err)
			}
			if got != string(want) {
				t.Fatalf("prompt differs from the Bash reference\n--- got ---\n%s\n--- want ---\n%s", got, want)
			}
		})
	}
}

func TestUnknownPersonaIsAnError(t *testing.T) {
	if _, err := Prompt("nobody", Vars{}); err == nil {
		t.Fatal("want an error for a persona without a voice")
	}
}

func TestRenderExecutesNothing(t *testing.T) {
	got := Render("a $(id) `id` $UNKNOWN $JACAZUL_MODE", Vars{Mode: "COUNSELOR"})
	if got != "a $(id) `id`  COUNSELOR" {
		t.Fatalf("got %q", got)
	}
}
