# [Jacazul] jacazul-github.ps1: GitHub Token Manager for Jacazul

$VENV_DIR = Join-Path $env:USERPROFILE ".jacazul-ai\.venv"
$VENV_PYTHON = Join-Path $VENV_DIR "Scripts\python.exe"

if (!(Test-Path $VENV_PYTHON)) {
    Write-Error "❌ ERROR: Jacazul Python runtime not found at $VENV_PYTHON"
    Write-Error "   Action: Run scripts/configure.ps1 from the jacazul-ai-cli repository."
    exit 1
}

# Execute python module and pass all arguments
& $VENV_PYTHON -m jacazul.cli.github $args
