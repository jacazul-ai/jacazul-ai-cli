# 🐊 Jacazul Python Bootstrap (PowerShell)
# Manages the persistent Python venv using 'uv' or 'pip'.

$JACAZUL_DIR = "$env:USERPROFILE\.jacazul-ai"
$VENV_DIR = "$JACAZUL_DIR\.venv"
$VENV_SCRIPTS = "$VENV_DIR\Scripts"
$REQUIREMENTS_FILE = "$PROJECT_ROOT\templates\python\requirements.txt"

# 1. Ensure the venv directory exists and is valid
$RECREATE_VENV = $false
if (!(Test-Path $VENV_DIR)) {
    $RECREATE_VENV = $true
} elseif (!(Test-Path "$VENV_SCRIPTS\python.exe")) {
    Write-Host "⚠️  Python venv at $VENV_DIR is invalid or broken. Recreating..." -ForegroundColor Yellow
    $RECREATE_VENV = $true
}

if ($RECREATE_VENV) {
    Write-Host "🐊 Initializing persistent Python venv at $VENV_DIR..." -ForegroundColor Cyan
    if (Test-Path $VENV_DIR) { Remove-Item -Path $VENV_DIR -Recurse -Force }
    if (!(Test-Path $JACAZUL_DIR)) { New-Item -ItemType Directory -Force -Path $JACAZUL_DIR | Out-Null }
    
    $uvPath = Get-Command uv -ErrorAction SilentlyContinue
    if ($uvPath) {
        & $uvPath.Source venv $VENV_DIR
    } else {
        & python -m venv $VENV_DIR
    }
}

# 2. Activate the venv for the current session
if (!(Test-Path $VENV_SCRIPTS)) {
    Write-Error "❌ Fatal Error: VENV Scripts folder not found at $VENV_SCRIPTS"
    return
}

$env:VIRTUAL_ENV = $VENV_DIR
if (($env:PATH -split ';') -notcontains $VENV_SCRIPTS) {
    $env:PATH = "$VENV_SCRIPTS;$env:PATH"
}

# 3. Sync dependencies if requirements.txt exists and we are in DEBUG
if (Test-Path $REQUIREMENTS_FILE) {
    if ($env:DEBUG) {
        Write-Host "🐊 Syncing Python dependencies..." -ForegroundColor Cyan
        $pipPath = "$VENV_SCRIPTS\pip.exe"
        & $pipPath install -r $REQUIREMENTS_FILE
    }
}

# 4. Install Jacazul local package (editable)
# This ensures all entry points (tw-flow, jacazul-broker, etc.) are available in the venv.
if (Test-Path "$PROJECT_ROOT\pyproject.toml") {
    $pipPath = "$VENV_SCRIPTS\pip.exe"
    if ($env:DEBUG) {
        Write-Host "🐊 Installing Jacazul package in editable mode..." -ForegroundColor Cyan
        & $pipPath install -e "$PROJECT_ROOT"
    } else {
        & $pipPath install -e "$PROJECT_ROOT" | Out-Null
    }
}

# Log status in DEBUG mode
if ($env:DEBUG) {
    Write-Host "✅ Jacazul: Python environment ready ($VENV_DIR)." -ForegroundColor Green
}
