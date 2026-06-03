# [Jacazul] jacazul-gemini.ps1: Gemini CLI native launcher for Windows

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

# 3. System Prompt Governance
$GEMINI_BIN = (Get-Command gemini -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source)
if (!$GEMINI_BIN) {
    $GEMINI_BIN = "gemini"
}

$GEMINI_VERSION = "unknown"
if ($GEMINI_BIN -ne "gemini" -or (Get-Command gemini -ErrorAction SilentlyContinue)) {
    $geminiVerOut = & $GEMINI_BIN --version 2>$null
    if ($LastExitCode -eq 0 -and $geminiVerOut) {
        $GEMINI_VERSION = $geminiVerOut.Trim()
    }
}

$DUMPS_DIR = Join-Path $env:PROJECT_ROOT ".gemini\system_dumps"
$VERSION_DUMP = Join-Path $DUMPS_DIR "system_$GEMINI_VERSION.md"
$ACTIVE_PROMPT = Join-Path $env:PROJECT_ROOT ".gemini\active-system.md"
$ONBOARD_TEMPLATE = Join-Path $env:PROJECT_ROOT "prompts\onboard.md"
$CAPABILITIES_TEMPLATE = Join-Path $env:PROJECT_ROOT "prompts\gemini_capabilities.md"

if (!(Test-Path $VERSION_DUMP)) {
    if ($env:DEBUG) {
        Write-Output "[Jacazul] Version dump missing for $GEMINI_VERSION. Performing auto-dump..."
    }
    New-Item -ItemType Directory -Path $DUMPS_DIR -Force | Out-Null
    
    $env:GEMINI_WRITE_SYSTEM_MD = $VERSION_DUMP
    & $GEMINI_BIN skills list > $null 2>&1
    Remove-Item env:GEMINI_WRITE_SYSTEM_MD -ErrorAction SilentlyContinue
}

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

# Prompt Injection Strategy
$ONBOARD_PROMPT_ACTIVE = $true
if (Test-Path $VERSION_DUMP) {
    if ($env:DEBUG) {
        Write-Output "[Jacazul] Generating active system prompt override..."
    }
    $dumpContent = Get-Content -Raw -Path $VERSION_DUMP
    $capabilities = ""
    if (Test-Path $CAPABILITIES_TEMPLATE) {
        $capabilities = Get-Content -Raw -Path $CAPABILITIES_TEMPLATE
    }
    
    $fullSystemPrompt = "$dumpContent`r`n`r`n---`r`n`r`n$ONBOARD_TEXT_FALLBACK`r`n`r`n$capabilities"
    $fullSystemPrompt | Set-Content $ACTIVE_PROMPT -Force
    # Normalize paths with forward slashes for Node.js compatibility on Windows
    $env:GEMINI_SYSTEM_MD = $ACTIVE_PROMPT -replace '\\', '/'
    $ONBOARD_PROMPT_ACTIVE = $false
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

if ($GEMINI_BIN -eq "gemini" -and !(Get-Command gemini -ErrorAction SilentlyContinue)) {
    Write-Error "[ERROR] gemini command not found in PATH."
    exit 1
}

if ($env:DEBUG) {
    Write-Output "[Jacazul] jacazul-gemini: Starting for project [$env:PROJECT_ID]"
}

# DRY RUN
if ($env:DRY) {
    Write-Output "[OK] Dry run complete. Gemini bootstrap verified for project [$env:PROJECT_ID]."
    Write-Output "[Jacazul] Arguments for gemini: $FINAL_ARGS"
    exit 0
}

if (!$env:DRY) {
    Write-Output "[Jacazul] Active Session: Mode=$env:JACAZUL_MODE | Lang=$env:JACAZUL_CHAT_LANG"
    Write-Output "[Jacazul] System Prompt: $env:GEMINI_SYSTEM_MD"
}

& $GEMINI_BIN $FINAL_ARGS

# Exit banner
$FOCUS_FILE = Join-Path $env:JACAZUL_HOME ".task\$env:PROJECT_ID\focus-$env:JACAZUL_SESSION_ID.json"
if (Test-Path $FOCUS_FILE) {
    Write-Output ""
    Write-Output "+-- [Jacazul] Session --------------------------------------+"
    Write-Output "|  To resume: jacazul-gemini --jacazul-session $env:JACAZUL_SESSION_ID      |"
    Write-Output "+------------------------------------------------------------+"
}
