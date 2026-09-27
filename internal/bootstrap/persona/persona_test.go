package persona

import "testing"

func lookup(vars map[string]string) func(string) string {
	return func(key string) string { return vars[key] }
}

func TestKnownPersonaFromTheProject(t *testing.T) {
	p := Resolve(Input{Getenv: lookup(nil), Project: "arnalbam", Harness: "claude", SessionID: "0989a06c"})
	if p.ID != "arnalbam" || p.Name != "Arnalbam" || p.Signature != "{💪} Arnalbam" {
		t.Fatalf("got %+v", p)
	}
	if p.ResponseSignature != p.Signature {
		t.Fatalf("ResponseSignature = %q, want the persona signature", p.ResponseSignature)
	}
}

func TestEnvironmentBeatsTheProject(t *testing.T) {
	p := Resolve(Input{Getenv: lookup(map[string]string{"JACAZUL_PERSONA": "atena"}), Project: "codama"})
	if p.ID != "atena" {
		t.Fatalf("ID = %q, want the environment's atena", p.ID)
	}
}

func TestUnknownPersonaFallsBackToJacazul(t *testing.T) {
	p := Resolve(Input{Getenv: lookup(nil), Project: "nobody"})
	if p.ID != "jacazul" || p.Display != "Jacazul (Jacaré Azul)" || p.Signature != "🐊 Jacazul" {
		t.Fatalf("got %+v", p)
	}
	if !p.Invalid {
		t.Fatal("Invalid = false, want true so --debug can warn")
	}
}

func TestTaskSignatureCarriesModelHarnessAndShortSession(t *testing.T) {
	p := Resolve(Input{
		Getenv:    lookup(map[string]string{"CLAUDE_MODEL": "claude-opus-5-5"}),
		Project:   "codama",
		Harness:   "claude",
		SessionID: "0989a06cffff",
	})
	want := "— Codama (claude-opus-5-5; harness: claude; session: 0989a06c)"
	if p.TaskSignature != want {
		t.Fatalf("TaskSignature = %q, want %q", p.TaskSignature, want)
	}
}

func TestModelFallsThroughUnknownValues(t *testing.T) {
	cases := []struct {
		env  map[string]string
		want string
	}{
		{map[string]string{"JACAZUL_MODEL": "Unknown", "PI_MODEL": "gpt-x"}, "gpt-x"},
		{map[string]string{"ANTHROPIC_MODEL": "none", "MODEL": "m"}, "m"},
		{nil, "unspecified"},
	}
	for _, c := range cases {
		if got := Resolve(Input{Getenv: lookup(c.env)}).Model; got != c.want {
			t.Errorf("env %v: Model = %q, want %q", c.env, got, c.want)
		}
	}
}

func TestHarnessAndSessionDefaults(t *testing.T) {
	p := Resolve(Input{Getenv: lookup(nil)})
	if p.Harness != "unknown" || p.SessionShort != "global" {
		t.Fatalf("got harness %q, session %q", p.Harness, p.SessionShort)
	}
}
