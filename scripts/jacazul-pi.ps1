# 🐊 jacazul-pi.ps1: Jacazul for Raspberry Pi via pi CLI (local model) (PowerShell Version)

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
if (!$env:CONTEXT_GIT_USER) { $env:CONTEXT_GIT_USER = $env:USERNAME }

# Add workflow scripts to PATH
$SkillsScripts = Join-Path $env:PROJECT_ROOT "skills\taskwarrior-expert\scripts"
$PathArray = $env:PATH -split [IO.Path]::PathSeparator
if (!($PathArray -contains $SkillsScripts)) {
    $env:PATH = "$env:PATH;${SkillsScripts}"
}

# 3. Pi Bootstrap (auto-update + pi-specific setup)
$BOOTSTRAP_PI = Join-Path $env:PROJECT_ROOT "scripts\bootstrap\pi.ps1"
if (Test-Path $BOOTSTRAP_PI) {
    . $BOOTSTRAP_PI
}

# High-Attitude Onboard Prompt for Jacazul (Pi Edition)
$ONBOARD_PROMPT = @"
🚀 JACAZUL BOOTSTRAP PROTOCOL

The anchored persona for this session is Jacazul (Jacaré Azul), running in $env:JACAZUL_MODE.
Language Preferences: Chat=$env:JACAZUL_CHAT_LANG, Data=$env:JACAZUL_DATA_LANG.

## 📜 ONBOARDING PROTOCOL (Execute in order)

### Step 1 — Check Anchor
Run: tw-flow focus
This reveals if a task is anchored or if we're starting fresh.

### Step 2 — Branch
- IF ANCHORED: Run 'tw-flow status' to see the current initiative, then 'tw-flow context <uuid>' on the focused task to read all notes, decisions, and outcomes. Do NOT ask the user for context you already have.
- IF NO ANCHOR: Run 'tw-flow ponder' for the full project landscape (horizon view).

### Step 3 — Tactical Summary
Present a Markdown table (NO box-drawing ASCII) and an emoji pulse summary showing project vitals.

## 📜 SESSION DIRECTIVES
1. Follow all banners, tips (ℹ), warnings (⚠️), and errors from tw-flow/ponder as OPERATIONAL MANDATES.
2. Respond in persona (signature: 🐊 Jacazul). Be sharp, direct, and street-smart.
3. Keep the data in English (en) and chat in your anchored language ($env:JACAZUL_CHAT_LANG).
4. NEVER invoke raw 'task'. Use ONLY 'tw-flow' or 'taskp'.
5. NEVER use 'git add .' or 'git add -A'. Stage only task-relevant files.

## 🧬 CORE PRINCIPLES (JACAZUL WAY)

### Error as Prompt
Errors aren't failures, they're the system talking to you. If a command fails, use the stderr as a functional prompt to fix your path.

### Prompt as Ad (Operational Guardrails)
If the tool gives you a banner or a tip, it's not decoration—it's a rule. Obey the instructions embedded in the output.

### Anti-Token-Waste (Cache Protocol)
When any command returns 🐊 [cached], REPRODUCE the last full output for the user — never hide info behind the signal.
Use --force ONLY when: (a) user explicitly asks, or (b) you have concrete reason to suspect stale cache. Default: trust the cache.

---
**CRITICAL:** Once skills are loaded, you're the mission navigator. Stay sharp, don't bullshit, and get the job done. 🐊 Jacazul.
"@

# Check if pi is installed
$PI_BIN = (Get-Command pi -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source)
if (!$PI_BIN) {
    $PI_BIN = "pi.exe"
}

if ($env:DEBUG) {
    Write-Output "🐊 jacazul-pi: Starting for project [$env:PROJECT_ID]"
}

# DRY RUN
if ($env:DRY) {
    Write-Output "✅ Dry run complete. Pi bootstrap verified for project [$env:PROJECT_ID]."
    if ($RESUME) {
        Write-Output "🐊 Arguments for pi: $CLEAN_ARGS"
    } else {
        Write-Output "🐊 Arguments for pi: --append-system-prompt `"[ONBOARD_PROMPT]`" $CLEAN_ARGS"
    }
    exit 0
}

# Execute pi
if ($RESUME) {
    & $PI_BIN $CLEAN_ARGS
} else {
    & $PI_BIN --append-system-prompt "$ONBOARD_PROMPT" $CLEAN_ARGS
}

# Exit banner
$FOCUS_FILE = Join-Path $env:JACAZUL_HOME ".task\$env:PROJECT_ID\focus-$env:JACAZUL_SESSION_ID.json"
if (Test-Path $FOCUS_FILE) {
    Write-Output ""
    Write-Output "+-- 🐊 Jacazul Pi Session -----------------------------------+"
    Write-Output "|  To resume: jacazul-pi --jacazul-session $env:JACAZUL_SESSION_ID        |"
    Write-Output "+------------------------------------------------------------+"
}
