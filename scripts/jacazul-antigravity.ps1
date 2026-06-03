# [Jacazul] jacazul-antigravity.ps1: Antigravity CLI native launcher for Windows

if (!$env:PROJECT_ROOT) {
    $scriptDir = Split-Path $MyInvocation.MyCommand.Path -Parent
    if (!$scriptDir) { $scriptDir = $PSScriptRoot }
    $env:PROJECT_ROOT = (Resolve-Path (Join-Path $scriptDir "..\")).Path
}

# 1. Session Restore: parse --jacazul-session BEFORE bootstrap
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
    Write-Error "[ERROR] Jacazul runtime environment not found at $BOOTSTRAP_ENV"
    exit 1
}

# Export all context variables
$env:CONTEXT_REAL_PATH = (Get-Location).Path
$env:CONTEXT_SYSTEM_USER = $env:USERNAME
if (!$env:CONTEXT_GIT_USER) { $env:CONTEXT_GIT_USER = $env:USERNAME }
$env:GEMINI_INSTRUCTIONS_DIR = Join-Path $env:PROJECT_ROOT "templates\context\instructions"

# Add workflow scripts to PATH
$SkillsScripts = Join-Path $env:PROJECT_ROOT "skills\taskwarrior-expert\scripts"
$PathArray = $env:PATH -split [IO.Path]::PathSeparator
if (!($PathArray -contains $SkillsScripts)) {
    $env:PATH = "$env:PATH;${SkillsScripts}"
}

# Antigravity Bootstrap (settings + skill links)
$BOOTSTRAP_ANTIGRAVITY = Join-Path $env:PROJECT_ROOT "scripts\bootstrap\antigravity.ps1"
if (Test-Path $BOOTSTRAP_ANTIGRAVITY) {
    . $BOOTSTRAP_ANTIGRAVITY
} else {
    if ($env:DEBUG) { Write-Output "[WARNING] Antigravity bootstrap script not found at $BOOTSTRAP_ANTIGRAVITY." }
}

$ONBOARD_TEMPLATE = Join-Path $env:PROJECT_ROOT "prompts\onboard.md"

# Load and Process Onboard Prompt
$ONBOARD_TEXT_FALLBACK = "🚀 JACAZUL BOOTSTRAP PROTOCOL"
if (Test-Path $ONBOARD_TEMPLATE) {
    $onboardContent = Get-Content -Raw -Path $ONBOARD_TEMPLATE
    $onboardContent = $onboardContent -replace '\$\{JACAZUL_MODE\}', $env:JACAZUL_MODE
    $onboardContent = $onboardContent -replace '\$JACAZUL_MODE', $env:JACAZUL_MODE
    $onboardContent = $onboardContent -replace '\$\{JACAZUL_CHAT_LANG\}', $env:JACAZUL_CHAT_LANG
    $onboardContent = $onboardContent -replace '\$JACAZUL_CHAT_LANG', $env:JACAZUL_CHAT_LANG
    $onboardContent = $onboardContent -replace '\$\{JACAZUL_DATA_LANG\}', $env:JACAZUL_DATA_LANG
    $onboardContent = $onboardContent -replace '\$JACAZUL_DATA_LANG', $env:JACAZUL_DATA_LANG
    $ONBOARD_TEXT_FALLBACK = $onboardContent
}

# Check if agy is installed
$AGY_BIN = (Get-Command agy -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source)
if (!$AGY_BIN) {
    $AGY_BIN = Join-Path $env:LOCALAPPDATA "agy\bin\agy.exe"
    if (!(Test-Path $AGY_BIN)) {
        $AGY_BIN = "agy.exe"
    }
}

if ($env:DEBUG) {
    Write-Output "[Jacazul] jacazul-antigravity: Starting for project [$env:PROJECT_ID]"
}

# Run arguments logic
$FINAL_ARGS = @()
if ($RESUME) {
    $FINAL_ARGS = $CLEAN_ARGS
} else {
    if ($CLEAN_ARGS.Count -eq 0) {
        $FINAL_ARGS = @("-i", $ONBOARD_TEXT_FALLBACK)
    } else {
        $userPrompt = $CLEAN_ARGS -join " "
        $FINAL_ARGS = @("-i", $ONBOARD_TEXT_FALLBACK, $userPrompt)
    }
}

if ($AGY_BIN -eq "agy.exe" -and !(Get-Command agy -ErrorAction SilentlyContinue)) {
    Write-Error "[ERROR] agy command not found in PATH."
    exit 1
}

# DRY RUN
if ($env:DRY) {
    Write-Output "[OK] Dry run complete. Antigravity bootstrap verified for project [$env:PROJECT_ID]."
    Write-Output "[Jacazul] Arguments for agy: $FINAL_ARGS"
    exit 0
}

if (!$env:DRY) {
    Write-Output "[Jacazul] Active Session: Mode=$env:JACAZUL_MODE | Lang=$env:JACAZUL_CHAT_LANG"
}

& $AGY_BIN $FINAL_ARGS

# Exit banner
$FOCUS_FILE = Join-Path $env:JACAZUL_HOME ".task\$env:PROJECT_ID\focus-$env:JACAZUL_SESSION_ID.json"
if (Test-Path $FOCUS_FILE) {
    Write-Output ""
    Write-Output "+-- [Jacazul] Session --------------------------------------+"
    Write-Output "|  To resume: jacazul-antigravity --jacazul-session $env:JACAZUL_SESSION_ID      |"
    Write-Output "+------------------------------------------------------------+"
}