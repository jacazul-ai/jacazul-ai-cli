package project

import (
	"encoding/json"
	"errors"
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
)

// Language is the chat and data language pair.
type Language struct {
	Chat string `json:"chat"`
	Data string `json:"data"`
}

// Config is the stable per-project configuration stored in
// JACAZUL_HOME/projects/<PROJECT_ID>/project.json. Empty fields mean the
// project sets nothing and callers fall back to their defaults.
type Config struct {
	Persona  string   `json:"persona"`
	Language Language `json:"language"`
}

// LoadConfig reads the project's project.json. When it is absent, the
// persona anchored in the legacy .task/<PROJECT_ID>/persona.json is used.
// No file at all yields the zero Config.
func LoadConfig(home, id string) (Config, error) {
	var cfg Config
	path := filepath.Join(home, "projects", id, "project.json")
	found, err := readJSON(path, &cfg)
	if err != nil || found {
		return cfg, err
	}

	var legacy struct {
		AnchoredPersona string `json:"anchored_persona"`
	}
	legacyPath := filepath.Join(home, ".task", id, "persona.json")
	if _, err := readJSON(legacyPath, &legacy); err != nil {
		return Config{}, err
	}
	cfg.Persona = legacy.AnchoredPersona
	return cfg, nil
}

// readJSON decodes path into v and reports whether the file existed.
func readJSON(path string, v any) (bool, error) {
	data, err := os.ReadFile(path)
	if errors.Is(err, fs.ErrNotExist) {
		return false, nil
	}
	if err != nil {
		return false, err
	}
	if err := json.Unmarshal(data, v); err != nil {
		return true, fmt.Errorf("%s: %w", path, err)
	}
	return true, nil
}
