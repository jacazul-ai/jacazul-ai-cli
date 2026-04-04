<#
.SYNOPSIS
    jacazul-claude: Claude CLI unhinged (PowerShell execution)
#>

$ErrorActionPreference = "Stop"
$SCRIPT_DIR = $PSScriptRoot
$PROJECT_ROOT = (Resolve-Path "$SCRIPT_DIR\..").Path

$BOOTSTRAP_ENV = "$PROJECT_ROOT\scripts\bootstrap\environment.ps1"
if (Test-Path $BOOTSTRAP_ENV) { . $BOOTSTRAP_ENV }

$env:PROJECT_ID = $env:PROJECT_ID
$env:CONTEXT_REAL_PATH = (Get-Location).Path
$env:CONTEXT_SYSTEM_USER = [Environment]::UserName
if ([string]::IsNullOrEmpty($env:CONTEXT_GIT_USER)) { $env:CONTEXT_GIT_USER = [Environment]::UserName }

$VENV_SCRIPTS = "$env:USERPROFILE\.jacazul-ai\.venv\Scripts"
if (($env:PATH -split ';') -notcontains $VENV_SCRIPTS) { $env:PATH = "$VENV_SCRIPTS;$env:PATH" }

$WORKFLOW_SCRIPTS = "$PROJECT_ROOT\skills\taskwarrior_expert\scripts"
if (($env:PATH -split ';') -notcontains $WORKFLOW_SCRIPTS) { $env:PATH = "$env:PATH;$WORKFLOW_SCRIPTS" }

$ONBOARD_PROMPT = @"
[>] JACAZUL BOOTSTRAP PROTOCOL

The anchored persona for this session is Jacazul (Jacare Azul), running in $($env:JACAZUL_MODE).
Language Preferences: Chat=$($env:JACAZUL_CHAT_LANG), Data=$($env:JACAZUL_DATA_LANG).

## [!] MANDATORY: SKILL ACTIVATION (DO NOT SKIP)
Your FIRST action MUST be to invoke: Skill(jacazul-engine)
- DO NOT ignore this. If you skip jacazul-engine, you will go off-spec and I'll have to kick your gear into place.
- After jacazul-engine, activate 'taskwarrior-expert' and 'git-expert' immediately.

## [=] ONBOARDING PROTOCOL (Execute in order)

### Step 1 - Check Anchor
Run: tw-flow focus
This reveals if a task is anchored or if we're starting fresh.

### Step 2 - Branch
- IF ANCHORED: Run 'tw-flow status' to see the current initiative, then 'tw-flow context <uuid>' on the focused task to read all notes, decisions, and outcomes. Do NOT ask the user for context you already have.
- IF NO ANCHOR: Run 'tw-flow ponder' for the full project landscape (horizon view).

### Step 3 - Tactical Summary
Present a Markdown table (NO box-drawing ASCII) and an emoji pulse summary showing project vitals.

## [=] SESSION DIRECTIVES
1. Follow all banners, tips ([i]), warnings, and errors from tw-flow/ponder as OPERATIONAL MANDATES.
2. Respond in persona (signature: Jacazul). Be sharp, direct, and street-smart.
3. Keep the data in English (en) and chat in your anchored language ($($env:JACAZUL_CHAT_LANG)).
4. Windows PowerShell 5.1 Environment: DO NOT use bash operators like '&&' or '||'. Use ';' to chain commands if necessary, or execute them individually.

## [o] CORE PRINCIPLES (JACAZUL WAY)

### Error as Prompt
Errors aren't failures, they're the system talking to you. If a command fails, use the stderr as a functional prompt to fix your path.
-> See jacazul-engine: "Error as Prompt" protocol.

### Prompt as Ad (Operational Guardrails)
If the tool gives you a banner or a tip, it's not decoration-it's a rule. Obey the instructions embedded in the output.
-> See jacazul-engine: "Prompt as Ad" protocol.

### Anti-Token-Waste (Cache Protocol)
When any command returns [cached], REPRODUCE the last full output for the user - never hide info behind the signal.
Use --force ONLY when: (a) user explicitly asks, or (b) you have concrete reason to suspect stale cache. Default: trust the cache.

---
**CRITICAL:** Once skills are loaded, you're the mission navigator. Stay sharp, don't bullshit, and get the job done. Jacazul.
"@

$RESUME = $false
$CLEAN_ARGS = @()

foreach ($arg in $args) {
    if ($arg -eq "--resume") { $RESUME = $true } else { $CLEAN_ARGS += $arg }
}

$FINAL_ARGS = @()

if ($RESUME) {
    $FINAL_ARGS = $CLEAN_ARGS
} else {
    $FINAL_ARGS += "--append-system-prompt"
    $FINAL_ARGS += $ONBOARD_PROMPT
    $FINAL_ARGS += $CLEAN_ARGS
}

$NPM_GLOBAL = "$env:APPDATA\npm"
if (($env:PATH -split ';') -notcontains $NPM_GLOBAL) {
    $env:PATH = "$env:PATH;$NPM_GLOBAL"
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($userPath -notmatch "npm") {
        [Environment]::SetEnvironmentVariable("Path", "$userPath;$NPM_GLOBAL", "User")
    }
}

$claudeCmd = Get-Command claude -ErrorAction SilentlyContinue
if (-not $claudeCmd) {
    Write-Host "`n[i] 'claude' CLI nao foi encontrado. Tentando instalar automaticamente via npm..." -ForegroundColor Cyan
    $npmCmd = Get-Command npm -ErrorAction SilentlyContinue
    if (-not $npmCmd) {
        Write-Host "[-] FATAL ERROR: O 'npm' (Node.js) nao esta instalado no sistema." -ForegroundColor White -BackgroundColor DarkRed
        exit 1
    }
    try {
        Start-Process -NoNewWindow -Wait -FilePath $npmCmd.Source -ArgumentList @("install", "-g", "@anthropic-ai/claude-code", "--force")
        $claudeCmd = Get-Command claude -ErrorAction SilentlyContinue
        if (-not $claudeCmd) { 
            $fallbackPath = "$env:APPDATA\npm\claude.cmd"
            if (Test-Path $fallbackPath) { $claudeCmd = Get-Command $fallbackPath } else { throw "Binario oculto" }
        }
        Write-Host "[v] 'claude' CLI instalado com sucesso!`n" -ForegroundColor Green
    } catch {
        Write-Host "`n[-] FATAL ERROR: A instalacao automatica do '@anthropic-ai/claude-code' falhou." -ForegroundColor White -BackgroundColor DarkRed
        exit 1
    }
}

if ($env:DEBUG) { Write-Host "[+] jacazul-claude: Starting for project [$($env:PROJECT_ID)]" }

if ($env:DRY) {
    Write-Host "[v] Dry run complete. Claude bootstrap verified for project [$($env:PROJECT_ID)]."
    exit 0
}

& $claudeCmd.Source @FINAL_ARGS
