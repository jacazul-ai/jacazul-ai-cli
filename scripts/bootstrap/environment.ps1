# [Jacazul] Bootstrap - Environment Check (PowerShell Version)
# This script is the SOLE entry point for runtime configuration (Dynamics).

# 1. Dynamic project context refresh
$PROJECT_ID_LIB = Join-Path $env:PROJECT_ROOT "scripts\bootstrap\project-identity.ps1"
if (Test-Path $PROJECT_ID_LIB) {
    . $PROJECT_ID_LIB
    Export-JacazulProjectIdentity (Get-Location).Path
} elseif (!$env:PROJECT_ID) {
    $parentDir = Split-Path (Split-Path (Get-Location).Path -Parent) -Leaf
    $currentDir = Split-Path (Get-Location).Path -Leaf
    $env:PROJECT_ID = "${parentDir}_${currentDir}"
}

if ($env:PROJECT_ID) {
    $env:JACAZUL_HOME = Join-Path $env:USERPROFILE ".jacazul-ai"
    $env:TASKDATA = Join-Path $env:JACAZUL_HOME ".task\$env:PROJECT_ID"
}

# 2. Run-once Guard
if ($env:JACAZUL_ENV_INITIALIZED) {
    return
}

# 3. Dynamic Detection of Real Taskwarrior Binary
if (!$env:JACAZUL_REAL_TASK) {
    $taskBins = Get-Command task -All -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source
    foreach ($bin in $taskBins) {
        if ($bin -notmatch "scripts\\task") {
            $env:JACAZUL_REAL_TASK = $bin
            break
        }
    }
    if (!$env:JACAZUL_REAL_TASK) {
        $env:JACAZUL_REAL_TASK = "task.exe"
    }
}

# 3.1 Taskwarrior/OS Detection
if (!$env:JACAZUL_TASK_VERSION) {
    if ($env:JACAZUL_REAL_TASK) {
        $verOut = & "$env:JACAZUL_REAL_TASK" --version 2>$null
        if ($LastExitCode -eq 0 -and $verOut) {
            $verStr = [string]$verOut
            $env:JACAZUL_TASK_VERSION = $verStr.Split('.')[0].Trim()
        }
    }
    if (!$env:JACAZUL_TASK_VERSION) {
        $env:JACAZUL_TASK_VERSION = "3"
    }
    $env:JACAZUL_HOST_OS = "windows"
}

# 4. Session Identity
if (!$env:JACAZUL_SESSION_ID) {
    $uuid = [guid]::NewGuid().ToString().Replace("-", "")
    $env:JACAZUL_SESSION_ID = $uuid.Substring(0, 8)
}

# 5. Mode Configuration
if (!$env:JACAZUL_MODE) {
    $env:JACAZUL_MODE = "COUNSELOR"
}

# 6. Component Bootstraps
$BOOTSTRAP_LANG = Join-Path $env:PROJECT_ROOT "scripts\bootstrap\language.ps1"
if (Test-Path $BOOTSTRAP_LANG) {
    . $BOOTSTRAP_LANG
}

# 6.1 Python VENV
$BOOTSTRAP_PYTHON = Join-Path $env:PROJECT_ROOT "scripts\bootstrap\python.ps1"
if (Test-Path $BOOTSTRAP_PYTHON) {
    . $BOOTSTRAP_PYTHON
}

# 6.2 JIT Prompt Hatching
$BOOTSTRAP_HATCH = Join-Path $env:PROJECT_ROOT "scripts\bootstrap\hatch.ps1"
if (Test-Path $BOOTSTRAP_HATCH) {
    . $BOOTSTRAP_HATCH
}

# 6.3 Taskwarrior
$BOOTSTRAP_TW = Join-Path $env:PROJECT_ROOT "scripts\bootstrap\taskwarrior.ps1"
if (Test-Path $BOOTSTRAP_TW) {
    . $BOOTSTRAP_TW
}

# 7. Finalize Initialization
$env:JACAZUL_ENV_INITIALIZED = "true"

if ($env:DEBUG) {
    Write-Output "[Jacazul] Jacazul Runtime Initialized | Mode: $env:JACAZUL_MODE | Binary: $env:JACAZUL_REAL_TASK"
}