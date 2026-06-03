# [Jacazul] Hatch Bootstrap (PowerShell Version)

$HATCH_BIN = Join-Path $env:USERPROFILE ".jacazul-ai\.venv\Scripts\jacazul-hatch.exe"

if (Test-Path $HATCH_BIN) {
    & "$HATCH_BIN" --client gemini
    & "$HATCH_BIN" --client copilot
    & "$HATCH_BIN" --client opencode
    & "$HATCH_BIN" --client claude
} else {
    Write-Output "[WARNING] Hatch entry point not found at $HATCH_BIN. Falling back to direct script..."
    $HATCH_ENGINE = Join-Path $env:PROJECT_ROOT "jacazul\cli\hatch.py"
    if (Test-Path $HATCH_ENGINE) {
        $python = Join-Path $env:USERPROFILE ".jacazul-ai\.venv\Scripts\python.exe"
        & "$python" "$HATCH_ENGINE" --client gemini
        & "$python" "$HATCH_ENGINE" --client copilot
        & "$python" "$HATCH_ENGINE" --client opencode
        & "$python" "$HATCH_ENGINE" --client claude
    } else {
        Write-Error "[ERROR] Hatch engine not found."
    }
}