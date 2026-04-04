# 🐊 Jacazul Hatch Bootstrap (PowerShell)
# Centralized JIT Prompt Forge trigger for the current session.

$HATCH_BIN = "$env:USERPROFILE\.jacazul-ai\.venv\Scripts\jacazul-hatch.exe"

if (Test-Path $HATCH_BIN) {
    if ($env:DEBUG) { Write-Host "🐊 Hatching all clients..." -ForegroundColor Cyan }
    & $HATCH_BIN --client gemini
    & $HATCH_BIN --client copilot
    & $HATCH_BIN --client opencode
    & $HATCH_BIN --client claude
} else {
    Write-Warning "Hatch entry point not found at $HATCH_BIN."
}
