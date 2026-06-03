# 🐊 jacazul-copilot.ps1: Copilot CLI native launcher for Windows

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

# Export all context variables
$env:PROJECT_ID = $env:PROJECT_ID
$env:CONTEXT_REAL_PATH = (Get-Location).Path
$env:CONTEXT_SYSTEM_USER = $env:USERNAME
$env:CONTEXT_GIT_USER = (git config --global user.name 2>$null)
if (!$env:CONTEXT_GIT_USER) { $env:CONTEXT_GIT_USER = $env:USERNAME }
$env:CONTEXT_GIT_EMAIL = (git config --global user.email 2>$null)
if (!$env:CONTEXT_GIT_EMAIL) { $env:CONTEXT_GIT_EMAIL = "not-configured" }
$env:COPILOT_CUSTOM_INSTRUCTIONS_DIRS = "$(Join-Path $env:USERPROFILE '.copilot');$(Join-Path $env:USERPROFILE '.github\instructions')"

# Add workflow scripts to PATH
$SkillsScripts = Join-Path $env:PROJECT_ROOT "skills\taskwarrior-expert\scripts"
$PathArray = $env:PATH -split [IO.Path]::PathSeparator
if (!($PathArray -contains $SkillsScripts)) {
    $env:PATH = "$env:PATH;${SkillsScripts}"
}

# Base Onboard Prompt for Jacazul (Copilot)
$ONBOARD_PROMPT = "The anchored persona for this session is Jacazul (Jacaré Azul). Activate 'jacazul-engine', 'taskwarrior-expert', and 'git-expert' skills immediately. Perform tactical discovery via 'tw-flow ponder'. IMPORTANT: Closely follow all banners, tips, warnings, and errors emitted by tw-flow and ponder as behavioral guidance. CACHE PROTOCOL: When any command returns [cached], REPRODUCE the last full output for the user — never hide info behind the signal. Use --force ONLY when the user asks or you have concrete reason to suspect stale cache."

# Run arguments logic
$FINAL_ARGS = @()
if ($RESUME) {
    $FINAL_ARGS = $CLEAN_ARGS
} else {
    if ($CLEAN_ARGS.Count -eq 0) {
        $FINAL_ARGS = @("--agent", "jacazul", "-i", $ONBOARD_PROMPT)
    } else {
        $userPrompt = $CLEAN_ARGS -join " "
        $FINAL_ARGS = @("--agent", "jacazul", "-i", $ONBOARD_PROMPT, $userPrompt)
    }
}

# Find real copilot binary (avoid local wrapper)
$REAL_COPILOT = $null
$copilotBins = Get-Command copilot -All -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source
foreach ($bin in $copilotBins) {
    if ($bin -notmatch "scripts\\copilot") {
        $REAL_COPILOT = $bin
        break
    }
}
if (!$REAL_COPILOT) {
    $REAL_COPILOT = "gh.exe copilot"
}

if ($env:DEBUG) {
    Write-Output "🐊 jacazul-copilot: Starting direct execution via [$REAL_COPILOT]"
}

# DRY RUN
if ($env:DRY) {
    Write-Output "✅ Dry run complete. Copilot bootstrap verified for project [$env:PROJECT_ID]."
    Write-Output "🐊 Arguments for copilot: $FINAL_ARGS"
    exit 0
}

# Execute copilot
if ($REAL_COPILOT -match " ") {
    $parts = $REAL_COPILOT -split " "
    $cmd = $parts[0]
    $extraArgs = $parts[1..($parts.Length-1)]
    & $cmd $extraArgs $FINAL_ARGS
} else {
    & $REAL_COPILOT $FINAL_ARGS
}

# Exit banner: only shown if an independent session file exists
$FOCUS_FILE = Join-Path $env:JACAZUL_HOME ".task\$env:PROJECT_ID\focus-$env:JACAZUL_SESSION_ID.json"
if (Test-Path $FOCUS_FILE) {
    Write-Output ""
    Write-Output "+-- 🐊 Jacazul Session --------------------------------------+"
    Write-Output "|  To resume: jacazul-copilot --jacazul-session $env:JACAZUL_SESSION_ID      |"
    Write-Output "+------------------------------------------------------------+"
}
