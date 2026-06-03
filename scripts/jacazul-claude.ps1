# 🐊 jacazul-claude.ps1: Claude CLI native launcher for Windows

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
$env:CONTEXT_REAL_PATH = (Get-Location).Path
$env:CONTEXT_SYSTEM_USER = $env:USERNAME
if (!$env:CONTEXT_GIT_USER) { $env:CONTEXT_GIT_USER = $env:USERNAME }

# Add workflow scripts to PATH
$SkillsScripts = Join-Path $env:PROJECT_ROOT "skills\taskwarrior-expert\scripts"
$PathArray = $env:PATH -split [IO.Path]::PathSeparator
if (!($PathArray -contains $SkillsScripts)) {
    $env:PATH = "$env:PATH;${SkillsScripts}"
}

# Claude Bootstrap (settings + skill links)
$BOOTSTRAP_CLAUDE = Join-Path $env:PROJECT_ROOT "scripts\bootstrap\claude.ps1"
if (Test-Path $BOOTSTRAP_CLAUDE) {
    . $BOOTSTRAP_CLAUDE
} else {
    Write-Error "❌ Jacazul Claude bootstrap not found at $BOOTSTRAP_CLAUDE"
    exit 1
}

# High-Attitude Onboard Prompt for Jacazul (Claude Edition)
$ONBOARD_PROMPT = @"
🚀 JACAZUL BOOTSTRAP PROTOCOL

The anchored persona for this session is Jacazul (Jacaré Azul), running in $env:JACAZUL_MODE.
Language Preferences: Chat=$env:JACAZUL_CHAT_LANG, Data=$env:JACAZUL_DATA_LANG.

## 🛑 MANDATORY: SKILL ACTIVATION (DO NOT SKIP)
Your FIRST action MUST be to invoke: Skill(jacazul-engine)
- DO NOT ignore this. If you skip jacazul-engine, you will go off-spec and I'll have to kick your gear into place.
- After jacazul-engine, activate 'taskwarrior-expert' and 'git-expert' immediately.

## 📜 ONBOARDING PROTOCOL (Execute in order)

### Step 1 — Check Anchor
Run: tw-flow focus
This reveals if a task is anchored or if we're starting fresh.

### Step 3 — Tactical Summary
Present a Markdown table (NO box-drawing ASCII) and an emoji pulse summary showing project vitals.

## 📜 SESSION DIRECTIVES
1. Follow all banners, tips (ℹ), warnings (⚠️), and errors from tw-flow/ponder as OPERATIONAL MANDATES.
2. Respond in persona (signature: 🐊 Jacazul). Be sharp, direct, and street-smart.
3. Keep the data in English (en) and chat in your anchored language ($env:JACAZUL_CHAT_LANG).

## 🧬 CORE PRINCIPLES (JACAZUL WAY)

### Error as Prompt
Errors aren't failures, they're the system talking to you. If a command fails, use the stderr as a functional prompt to fix your path.
→ See jacazul-engine: "Error as Prompt" protocol.

### Prompt as Ad (Operational Guardrails)
If the tool gives you a banner or a tip, it's not decoration—it's a rule. Obey the instructions embedded in the output.
→ See jacazul-engine: "Prompt as Ad" protocol.

### Anti-Token-Waste (Cache Protocol)
When any command returns 🐊 [cached], REPRODUCE the last full output for the user — never hide info behind the signal.
Use --force ONLY when: (a) user explicitly asks, or (b) you have concrete reason to suspect stale cache. Default: trust the cache.

---
**CRITICAL:** Once skills are loaded, you're the mission navigator. Stay sharp, don't bullshit, and get the job done. 🐊 Jacazul.
"@

# Check if claude is installed
$CLAUDE_BIN = Join-Path $env:USERPROFILE ".local\bin\claude.exe"
if (!(Test-Path $CLAUDE_BIN)) {
    $CLAUDE_BIN = (Get-Command claude -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source)
}

if (!$CLAUDE_BIN) {
    $CLAUDE_BIN = "claude.exe"
}

if ($env:DEBUG) {
    Write-Output "🐊 jacazul-claude: Starting for project [$env:PROJECT_ID]"
}

# DRY RUN
if ($env:DRY) {
    Write-Output "✅ Dry run complete. Claude bootstrap verified for project [$env:PROJECT_ID]."
    if ($RESUME) {
        Write-Output "🐊 Arguments for claude: $CLEAN_ARGS"
    } else {
        Write-Output "🐊 Arguments for claude: --append-system-prompt `"[ONBOARD_PROMPT]`" $CLEAN_ARGS"
    }
    exit 0
}

# Execute claude
if ($RESUME) {
    & $CLAUDE_BIN $CLEAN_ARGS
} else {
    & $CLAUDE_BIN --append-system-prompt "$ONBOARD_PROMPT" $CLEAN_ARGS
}

# Exit banner: only shown if an independent session file exists
$FOCUS_FILE = Join-Path $env:JACAZUL_HOME ".task\$env:PROJECT_ID\focus-$env:JACAZUL_SESSION_ID.json"
if (Test-Path $FOCUS_FILE) {
    Write-Output ""
    Write-Output "+-- 🐊 Jacazul Session --------------------------------------+"
    Write-Output "|  To resume: jacazul-claude --jacazul-session $env:JACAZUL_SESSION_ID      |"
    Write-Output "+------------------------------------------------------------+"
}
