package language

import (
	"os"
	"path/filepath"
	"testing"
)

func lookup(vars map[string]string) func(string) string {
	return func(key string) string { return vars[key] }
}

func globalFile(t *testing.T, content string) string {
	t.Helper()
	path := filepath.Join(t.TempDir(), "language.json")
	if err := os.WriteFile(path, []byte(content), 0o644); err != nil {
		t.Fatal(err)
	}
	return path
}

func TestDefaultsWithoutAnySource(t *testing.T) {
	got := Resolve(lookup(nil), Pair{}, filepath.Join(t.TempDir(), "missing.json"))
	if got != (Pair{Chat: "pt-br", Data: "en"}) {
		t.Fatalf("got %+v, want pt-br/en", got)
	}
}

func TestGlobalFileBeatsDefaults(t *testing.T) {
	got := Resolve(lookup(nil), Pair{}, globalFile(t, `{"chat": "es", "data": "es"}`))
	if got != (Pair{Chat: "es", Data: "es"}) {
		t.Fatalf("got %+v, want the global file", got)
	}
}

func TestProjectBeatsTheGlobalFile(t *testing.T) {
	got := Resolve(lookup(nil), Pair{Chat: "en"}, globalFile(t, `{"chat": "es", "data": "es"}`))
	if got != (Pair{Chat: "en", Data: "es"}) {
		t.Fatalf("got %+v, want chat from the project and data from the global file", got)
	}
}

func TestEnvironmentBeatsEverything(t *testing.T) {
	env := lookup(map[string]string{"JACAZUL_CHAT_LANG": "fr", "JACAZUL_DATA_LANG": "de"})
	got := Resolve(env, Pair{Chat: "en", Data: "en"}, globalFile(t, `{"chat": "es", "data": "es"}`))
	if got != (Pair{Chat: "fr", Data: "de"}) {
		t.Fatalf("got %+v, want the environment", got)
	}
}
