<#
.SYNOPSIS
    Jacazul Bootstrap - Environment Check (PowerShell)
    This script is the SOLE entry point for runtime configuration (Dynamics).
#>

# 1. Run-once Guard
if ($env:JACAZUL_ENV_INITIALIZED) {
    return
}

$PROJECT_ROOT = (Resolve-Path "$PSScriptRoot\..\..").Path

# 2. Dynamic Detection of Real Taskwarrior Binary
if ([string]::IsNullOrEmpty($env:JACAZUL_REAL_TASK)) {
    # 0. Check for local compiled binary first
    $localTaskPath = Join-Path $PROJECT_ROOT "bin\tw\task.exe"
    if (Test-Path $localTaskPath) {
        $taskPath = $localTaskPath
    }

    if (-not $taskPath) {
        # Check for direct path like scoop installs or global path first
        $taskPath = Get-Command task.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -First 1
    }
    
    if (-not $taskPath) {
        # Fallback common Windows paths
        $commonPaths = @(
            "$env:ProgramFiles\taskwarrior\task.exe",
            "$env:USERPROFILE\scoop\shims\task.exe",
            "C:\ProgramData\chocolatey\bin\task.exe"
        )
        foreach ($p in $commonPaths) {
            if (Test-Path $p) {
                $taskPath = $p
                break
            }
        }
    }
    
    if ($taskPath -and ($taskPath -notmatch "scripts\\task")) {
        $env:JACAZUL_REAL_TASK = $taskPath
    } else {
        Write-Host "`n[i] O nucleo de tarefas 'task.exe' (Taskwarrior) nao foi encontrado nativamente." -ForegroundColor Cyan
        Write-Host "[!] Nenhuma build local ou instalacao global encontrada." -ForegroundColor Red
        [Environment]::Exit(1)
    }
}

# 2.1 Taskwarrior/OS Detection
if ([string]::IsNullOrEmpty($env:JACAZUL_TASK_VERSION) -and $env:JACAZUL_REAL_TASK) {
    try {
        $taskVerOutput = & $env:JACAZUL_REAL_TASK --version | Select-Object -First 1
        $env:JACAZUL_TASK_VERSION = ($taskVerOutput -split '\.')[0]
    } catch {
        # Ignore
    }
}
$env:JACAZUL_HOST_OS = "windows"

# 2.2 Administrative Alias
if ($env:JACAZUL_REAL_TASK) {
    Set-Alias -Name rtask -Value $env:JACAZUL_REAL_TASK -Scope Global -ErrorAction SilentlyContinue
}

# 3. Project Identity Calculation
if ([string]::IsNullOrEmpty($env:PROJECT_ID)) {
    $parentDir = (Get-Item $PROJECT_ROOT).Parent.Name
    $currentDir = (Get-Item $PROJECT_ROOT).Name
    $env:PROJECT_ID = "${parentDir}_${currentDir}"
}

# 4. Session Identity
if ([string]::IsNullOrEmpty($env:JACAZUL_SESSION_ID)) {
    $env:JACAZUL_SESSION_ID = [guid]::NewGuid().ToString().Substring(0,8)
}

# 5. Mode Configuration
if ([string]::IsNullOrEmpty($env:JACAZUL_MODE)) {
    $env:JACAZUL_MODE = "COUNSELOR"
}

# 4. Component Bootstraps (Dynamics)

# 4.0 Language (Idiom)
$BOOTSTRAP_LANG = "$PROJECT_ROOT\scripts\bootstrap\language.ps1"
if (Test-Path $BOOTSTRAP_LANG) { . $BOOTSTRAP_LANG }

# 4.1 Python VENV (Foundation)
$BOOTSTRAP_PYTHON = "$PROJECT_ROOT\scripts\bootstrap\python.ps1"
if (Test-Path $BOOTSTRAP_PYTHON) { . $BOOTSTRAP_PYTHON }

# 4.1.1 Health Check (Critical Binaries - AFTER Python bootstrap)
$TW_FLOW_BIN = "$env:USERPROFILE\.jacazul-ai\.venv\Scripts\tw-flow.exe"
if (!(Test-Path $TW_FLOW_BIN)) {
    $TW_FLOW_BIN = "$PROJECT_ROOT\skills\taskwarrior_expert\scripts\tw-flow.exe"
}

if (!(Test-Path $TW_FLOW_BIN)) {
    # If we are in the middle of a configuration, don't exit yet, but warn
    if (!$env:JACAZUL_CONFIGURING) {
        Write-Host "`n❌ CRITICAL ERROR: tw-flow não encontrado ou executável." -ForegroundColor White -BackgroundColor DarkRed
        Write-Host "   A estrutura do workspace pode estar corrompida." -ForegroundColor Yellow
        Write-Host "   Solução: Execute 'scripts\configure.ps1' para corrigi-la.`n" -ForegroundColor Yellow
        [Environment]::Exit(1)
    }
}

# 4.2 JIT Prompt Hatching (The Forge)
$BOOTSTRAP_HATCH = "$PROJECT_ROOT\scripts\bootstrap\hatch.ps1"
if (Test-Path $BOOTSTRAP_HATCH) { & $BOOTSTRAP_HATCH }

# 4.3 Taskwarrior
$BOOTSTRAP_TW = "$PROJECT_ROOT\scripts\bootstrap\taskwarrior.ps1"
if (Test-Path $BOOTSTRAP_TW) { . $BOOTSTRAP_TW }

# 4.4 GitHub
$BOOTSTRAP_GITHUB = "$PROJECT_ROOT\scripts\bootstrap\github.ps1"
if (Test-Path $BOOTSTRAP_GITHUB) { . $BOOTSTRAP_GITHUB }

# 4.5 Gemini
$BOOTSTRAP_GEMINI = "$PROJECT_ROOT\scripts\bootstrap\gemini.ps1"
if (Test-Path $BOOTSTRAP_GEMINI) { . $BOOTSTRAP_GEMINI "$env:USERPROFILE\.gemini" }

# 4.6 Claude
$BOOTSTRAP_CLAUDE = "$PROJECT_ROOT\scripts\bootstrap\claude.ps1"
if (Test-Path $BOOTSTRAP_CLAUDE) { . $BOOTSTRAP_CLAUDE "$env:USERPROFILE\.claude" }

# 5. Finalize Initialization
$env:JACAZUL_ENV_INITIALIZED = "true"

# Initial feedback - ONLY if DEBUG is set
if ($env:DEBUG) {
    Write-Host "🐊 Jacazul Runtime Initialized | Mode: $($env:JACAZUL_MODE) | Binary: $($env:JACAZUL_REAL_TASK)"
}
