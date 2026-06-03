# [Jacazul] Python Bootstrap (PowerShell Version)

$VENV_DIR = Join-Path $env:USERPROFILE ".jacazul-ai\.venv"
$REQUIREMENTS_FILE = Join-Path $env:PROJECT_ROOT "templates\python\requirements.txt"

# 0. Kill existing shell VENV if it points to legacy paths
Remove-Item env:VIRTUAL_ENV -ErrorAction SilentlyContinue

$VENV_BIN = Join-Path $VENV_DIR "Scripts"
$PythonExe = Join-Path $VENV_BIN "python.exe"

# 1. Ensure the venv directory exists and is valid
$RECREATE_VENV = $false
if (!(Test-Path $VENV_DIR)) {
    $RECREATE_VENV = $true
} else {
    & $PythonExe --version >$null 2>&1
    if ($LastExitCode -ne 0) {
        Write-Output "[WARNING] Python venv at $VENV_DIR is invalid or broken. Recreating..."
        $RECREATE_VENV = $true
    }
}

if ($RECREATE_VENV) {
    Write-Output "[Jacazul] Initializing persistent Python venv at $VENV_DIR..."
    if (Test-Path $VENV_DIR) {
        Remove-Item -Path $VENV_DIR -Recurse -Force -ErrorAction SilentlyContinue
    }
    
    $parentDir = Split-Path $VENV_DIR -Parent
    if (!(Test-Path $parentDir)) {
        New-Item -ItemType Directory -Path $parentDir -Force | Out-Null
    }
    
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        & uv venv "$VENV_DIR"
    } else {
        & python -m venv "$VENV_DIR"
    }
}

# 2. Activate the venv
# 2.1 Enforce Sentinel Precedence
# Ensure the project's scripts directory is at the front of the PATH
# Also ensure the venv's Scripts is in the PATH for entry points.
$env:VIRTUAL_ENV = $VENV_DIR
$PathParts = $env:PATH -split [IO.Path]::PathSeparator
$ScriptsDir = Join-Path $env:PROJECT_ROOT "scripts"

$NewPathParts = @()
$NewPathParts += $ScriptsDir
$NewPathParts += $VENV_BIN
foreach ($part in $PathParts) {
    if ($part -ne $ScriptsDir -and $part -ne $VENV_BIN) {
        $NewPathParts += $part
    }
}
$env:PATH = $NewPathParts -join [IO.Path]::PathSeparator

# 3. Sync dependencies if requirements.txt exists
if (Test-Path $REQUIREMENTS_FILE) {
    if ($env:DEBUG) {
        Write-Output "[Jacazul] Syncing Python dependencies..."
        if (Get-Command uv -ErrorAction SilentlyContinue) {
            & uv pip install -r "$REQUIREMENTS_FILE"
        } else {
            & (Join-Path $VENV_BIN "pip.exe") install -r "$REQUIREMENTS_FILE"
        }
    }
}

# 4. Install Jacazul local package (editable)
if (Test-Path (Join-Path $env:PROJECT_ROOT "pyproject.toml")) {
    if ($env:DEBUG) {
        Write-Output "[Jacazul] Installing Jacazul package in editable mode..."
    }
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        if ($env:DEBUG) {
            & uv pip install -e "$env:PROJECT_ROOT"
        } else {
            & uv pip install -e "$env:PROJECT_ROOT" >$null 2>&1
        }
    } else {
        $pipBin = Join-Path $VENV_BIN "pip.exe"
        if ($env:DEBUG) {
            & $pipBin install -e "$env:PROJECT_ROOT"
        } else {
            & $pipBin install -e "$env:PROJECT_ROOT" >$null 2>&1
        }
    }
}

if ($env:DEBUG) {
    Write-Output "[OK] Jacazul: Python environment ready ($VENV_DIR)."
}