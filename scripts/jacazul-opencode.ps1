# 🐊 jacazul-opencode.ps1: Opencode CLI native launcher for Windows

if (!$env:PROJECT_ROOT) {
    $scriptDir = Split-Path $MyInvocation.MyCommand.Path -Parent
    if (!$scriptDir) { $scriptDir = $PSScriptRoot }
    $env:PROJECT_ROOT = (Resolve-Path (Join-Path $scriptDir "..\")).Path
}

# 1. Session Restore: parse --jacazul-session BEFORE bootstrap sources
$RESUME = $false
$JACAZUL_SESSION_ID = $null
$CLEAN_ARGS = @()

for ($i = 0; $i -lt $args.Count; $i++) {
    if ($args[$i] -eq "--jacazul-session") {
        $env:JACAZUL_SESSION_ID = $args[$i+1]
        $i++
    } elseif ($args[$i] -eq "--resume") {
        $RESUME = $true
    } else {
        $CLEAN_ARGS += $args[$i]
    }
}

# 2. Runtime Bootstrap (Dynamics)
$BOOTSTRAP_ENV = Join-Path $env:PROJECT_ROOT "scripts\bootstrap\environment.ps1"
if (Test-Path $BOOTSTRAP_ENV) {
    . $BOOTSTRAP_ENV
} else {
    Write-Error "❌ Jacazul runtime environment not found at $BOOTSTRAP_ENV"
    exit 1
}

# Export context for TUI
$env:PROJECT_ID = $env:PROJECT_ID
$env:CONTEXT_REAL_PATH = (Get-Location).Path
$env:CONTEXT_SYSTEM_USER = $env:USERNAME

# Add workflow scripts to PATH
$SkillsScripts = Join-Path $env:PROJECT_ROOT "skills\taskwarrior-expert\scripts"
$PathArray = $env:PATH -split [IO.Path]::PathSeparator
if (!($PathArray -contains $SkillsScripts)) {
    $env:PATH = "$env:PATH;${SkillsScripts}"
}

# Verification: Opencode installation
$OPENCODE_BIN = (Get-Command opencode -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source)
if (!$OPENCODE_BIN) {
    $localPath = Join-Path $env:USERPROFILE ".opencode\bin\opencode.exe"
    if (Test-Path $localPath) {
        $OPENCODE_BIN = $localPath
    } else {
        $OPENCODE_BIN = "opencode.exe"
    }
}

if ($env:DEBUG) {
    Write-Output "🐊 jacazul-opencode: Starting for project [$env:PROJECT_ID]"
}

# DRY RUN
if ($env:DRY) {
    Write-Output "✅ Dry run complete. Opencode bootstrap verified for project [$env:PROJECT_ID]."
    exit 0
}

# Prepare arguments
$ARGS_STRING = $CLEAN_ARGS -join " "
$FINAL_ARGS = $CLEAN_ARGS
if (!($ARGS_STRING -match "--agent")) {
    $FINAL_ARGS = @("--agent", "jacazul") + $CLEAN_ARGS
}

& $OPENCODE_BIN $FINAL_ARGS

# Exit banner
$FOCUS_FILE = Join-Path $env:JACAZUL_HOME ".task\$env:PROJECT_ID\focus-$env:JACAZUL_SESSION_ID.json"
if (Test-Path $FOCUS_FILE) {
    Write-Output ""
    Write-Output "+-- 🐊 Jacazul Session --------------------------------------+"
    Write-Output "|  To resume: jacazul-opencode --jacazul-session $env:JACAZUL_SESSION_ID      |"
    Write-Output "+------------------------------------------------------------+"
}
