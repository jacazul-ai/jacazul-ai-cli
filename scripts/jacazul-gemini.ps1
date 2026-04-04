<#
.SYNOPSIS
    jacazul-gemini: Gemini CLI unhinged (PowerShell execution)
#>

$ErrorActionPreference = "Stop"
$SCRIPT_DIR = $PSScriptRoot
$PROJECT_ROOT = (Resolve-Path "$SCRIPT_DIR\..").Path

# -----------------------------------------------------------------------------
# Runtime Bootstrap (Dynamics)
# -----------------------------------------------------------------------------
$BOOTSTRAP_ENV = "$PROJECT_ROOT\scripts\bootstrap\environment.ps1"
if (Test-Path $BOOTSTRAP_ENV) {
    . $BOOTSTRAP_ENV
} else {
    Write-Error "? Jacazul runtime environment not found at $BOOTSTRAP_ENV"
    exit 1
}

# Export context variables to Environment
$env:PROJECT_ID = $env:PROJECT_ID
$env:CONTEXT_REAL_PATH = (Get-Location).Path
$env:CONTEXT_SYSTEM_USER = [Environment]::UserName

if ([string]::IsNullOrEmpty($env:CONTEXT_GIT_USER)) {
    $env:CONTEXT_GIT_USER = [Environment]::UserName
}

$env:GEMINI_INSTRUCTIONS_DIR = "$PROJECT_ROOT\templates\context\instructions"

# Add virtual environment to PATH (FIRST priority)
$VENV_SCRIPTS = "$env:USERPROFILE\.jacazul-ai\.venv\Scripts"
if (Test-Path $VENV_SCRIPTS) {
    if (($env:PATH -split ';') -notcontains $VENV_SCRIPTS) {
        $env:PATH = "$VENV_SCRIPTS;$env:PATH"
    }
}

# DO NOT add $PROJECT_ROOT\skills\taskwarrior_expert\scripts to PATH on Windows.
# On Windows, we rely on the .exe wrappers in the venv or the .cmd wrappers in ~/bin.
# Adding the bash folder causes PowerShell to try to execute extensionless bash scripts.

# High-Attitude Onboard Prompt for Jacazul (Gemini Edition)
$ONBOARD_PROMPT = @"
[>] JACAZUL BOOTSTRAP PROTOCOL

The anchored persona for this session is Jacazul (Jacar? Azul), running in $($env:JACAZUL_MODE).
Language Preferences: Chat=$($env:JACAZUL_CHAT_LANG), Data=$($env:JACAZUL_DATA_LANG).

## [!] MANDATORY: SKILL ACTIVATION (DO NOT SKIP)
Your FIRST action MUST be to invoke: Skill(jacazul-engine)
- DO NOT ignore this. If you skip jacazul-engine, you will go off-spec and I'll have to kick your gear into place.
- After jacazul-engine, activate 'taskwarrior-expert' and 'git-expert' immediately.

## [=] ONBOARDING PROTOCOL (Execute in order)

### Step 1 ? Check Anchor
Run: tw-flow focus
This reveals if a task is anchored or if we're starting fresh.

### Step 2 ? Branch
- IF ANCHORED: Run 'tw-flow status' to see the current initiative, then 'tw-flow context <uuid>' on the focused task to read all notes, decisions, and outcomes. Do NOT ask the user for context you already have.
- IF NO ANCHOR: Run 'tw-flow ponder' for the full project landscape (horizon view).

### Step 3 ? Tactical Summary
Present a Markdown table (NO box-drawing ASCII) and an emoji pulse summary showing project vitals.

## [=] SESSION DIRECTIVES
1. Follow all banners, tips (?), warnings (??), and errors from tw-flow/ponder as OPERATIONAL MANDATES.
2. Respond in persona (signature:  Jacazul). Be sharp, direct, and street-smart.
3. Keep the data in English (en) and chat in your anchored language ($($env:JACAZUL_CHAT_LANG)).
4. Windows PowerShell 5.1 Environment: DO NOT use bash operators like '&&' or '||'. Use ';' to chain commands if necessary, or execute them individually.

## [o] CORE PRINCIPLES (JACAZUL WAY)

### Error as Prompt
Errors aren't failures, they're the system talking to you. If a command fails, use the stderr as a functional prompt to fix your path.
? See jacazul-engine: "Error as Prompt" protocol.

### Prompt as Ad (Operational Guardrails)
If the tool gives you a banner or a tip, it's not decoration?it's a rule. Obey the instructions embedded in the output.
? See jacazul-engine: "Prompt as Ad" protocol.

### Anti-Token-Waste (Cache Protocol)
When any command returns  [cached], REPRODUCE the last full output for the user ? never hide info behind the signal.
Use --force ONLY when: (a) user explicitly asks, or (b) you have concrete reason to suspect stale cache. Default: trust the cache.

---
**CRITICAL:** Once skills are loaded, you're the mission navigator. Stay sharp, don't bullshit, and get the job done.  Jacazul.
"@

# Parse arguments for --resume
$RESUME = $false
$CLEAN_ARGS = @()

foreach ($arg in $args) {
    if ($arg -eq "--resume") {
        $RESUME = $true
    } else {
        $CLEAN_ARGS += $arg
    }
}

$FINAL_ARGS = @()

# If resume is true, don't use the onboard prompt
if ($RESUME) {
    $FINAL_ARGS = $CLEAN_ARGS
} else {
    if ($CLEAN_ARGS.Count -eq 0) {
        $FINAL_ARGS += "-i"
        $FINAL_ARGS += $ONBOARD_PROMPT
    } else {
        $FINAL_ARGS += "-i"
        $FINAL_ARGS += $ONBOARD_PROMPT
        # Note: $CLEAN_ARGS could be multiple parts of a prompt
        $USER_PROMPT = $CLEAN_ARGS -join " "
        $FINAL_ARGS += $USER_PROMPT
    }
}

$NPM_GLOBAL = "$env:APPDATA\npm"
if (($env:PATH -split ';') -notcontains $NPM_GLOBAL) {
    $env:PATH = "$env:PATH;$NPM_GLOBAL"
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($userPath -notmatch "npm") {
        [Environment]::SetEnvironmentVariable("Path", "$userPath;$NPM_GLOBAL", "User")
    }
}

# Check if gemini is installed
$geminiCmd = Get-Command gemini -ErrorAction SilentlyContinue
if (-not $geminiCmd) {
    Write-Host "`n[i] 'gemini' CLI nativo nao foi encontrado. Tentando instalar automaticamente via npm..." -ForegroundColor Cyan
    $npmCmd = Get-Command npm -ErrorAction SilentlyContinue
    if (-not $npmCmd) {
        Write-Host "[-] FATAL ERROR: O 'npm' (Node.js) nao esta instalado no sistema." -ForegroundColor White -BackgroundColor DarkRed
        Write-Host "    Para instalar o Gemini CLI automaticamente, baixe e instale o Node.js pelo site: https://nodejs.org" -ForegroundColor Yellow
        exit 1
    }
    try {
        Write-Host "[i] Buscando o pacote oficial do Gemini CLI no repositorio NPM..." -ForegroundColor DarkGray
        # Buscando o pacote dinamicamente como solicitado
        $searchOutput = & $npmCmd.Source search "@google/gemini-cli" --json 2>$null | ConvertFrom-Json
        $pkgName = if ($searchOutput -is [array] -and $searchOutput.Count -gt 0) { $searchOutput[0].name } else { "@google/gemini-cli" }
        
        Write-Host "[+] Pacote identificado na nuvem: $pkgName. Iniciando download..." -ForegroundColor Cyan
        
        # Uso nativo do powershell ao inves de Start-Process para permitir piping visual direto
        & $npmCmd.Source "install" "-g" $pkgName "--force"
        if ($LASTEXITCODE -ne 0) { throw "Falha na execucao do NPM. Codigo de erro: $LASTEXITCODE" }

        # Forca carregamento de atalhos novos em memoria se foram recem criados
        $geminiCmd = Get-Command gemini -ErrorAction SilentlyContinue
        if (-not $geminiCmd) { 
            $fallbackPath = "$env:APPDATA\npm\gemini.cmd"
            if (Test-Path $fallbackPath) { $geminiCmd = Get-Command $fallbackPath } else { throw "NPM instalou, mas o executavel gemini.cmd nao foi revelado no PATH." }
        }
        Write-Host "[v] Pacote dinâmico '$pkgName' (gemini) instalado com sucesso!`n" -ForegroundColor Green
    } catch {
        Write-Host "`n[-] FATAL ERROR: A resolulacao ou instalacao automatica pelo NPM falhou." -ForegroundColor White -BackgroundColor DarkRed
        Write-Host "    -> Detalhe Tecnico: $_" -ForegroundColor Red
        Write-Host "    -> Solucao manual: Rode no terminal: 'npm install -g @google/gemini-cli' e reabra o seu PowerShell.`n" -ForegroundColor Yellow
        [Environment]::Exit(1)
    }
}

if ($env:DEBUG) {
    Write-Host "[+] jacazul-gemini: Starting for project [$($env:PROJECT_ID)]"
}

# DRY RUN: Exit before execution if DRY is set
if ($env:DRY) {
    Write-Host "[v] Dry run complete. Gemini bootstrap verified for project [$($env:PROJECT_ID)]."
    Write-Host "[+] Arguments for gemini: $FINAL_ARGS"
    exit 0
}

# Execute Gemini CLI with arguments correctly unrolled
& $geminiCmd.Source @FINAL_ARGS
