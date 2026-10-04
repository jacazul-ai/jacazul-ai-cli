package project

import (
	"encoding/json"
	"errors"
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
)

// AnchoredPersona reads the persona anchored for the project in
// JACAZUL_HOME/.task/<PROJECT_ID>/persona.json, the file jacazul-persona
// writes. No file yields "". The persisted configuration file
// (project.json) is a separate feature, not implemented, so it is not read.
func AnchoredPersona(home, id string) (string, error) {
	path := filepath.Join(home, ".task", id, "persona.json")
	data, err := os.ReadFile(path)
	if errors.Is(err, fs.ErrNotExist) {
		return "", nil
	}
	if err != nil {
		return "", err
	}
	var anchor struct {
		AnchoredPersona string `json:"anchored_persona"`
	}
	if err := json.Unmarshal(data, &anchor); err != nil {
		return "", fmt.Errorf("%s: %w", path, err)
	}
	return anchor.AnchoredPersona, nil
}
