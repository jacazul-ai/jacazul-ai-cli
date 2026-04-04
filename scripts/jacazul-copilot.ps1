<#
.SYNOPSIS
    jacazul-copilot: Copilot CLI unhinged (PowerShell execution)
#>

$ErrorActionPreference = "Stop"
$SCRIPT_DIR = $PSScriptRoot
$PROJECT_ROOT = (Resolve-Path "$SCRIPT_DIR\..").Path

$BOOTSTRAP_ENV = "$PROJECT_ROOT\scripts\bootstrap\environment.ps1"
if (Test-Path $BOOTSTRAP_ENV) { . $BOOTSTRAP_ENV }

$env:PROJECT_ID = $env:PROJECT_ID
$env:CONTEXT_REAL_PATH = (Get-Location).Path
$env:CONTEXT_SYSTEM_USER = [Environment]::UserName
$env:CONTEXT_GIT_USER = try { & git config --global user.name 2>$null } catch { "not configured" }
$env:CONTEXT_GIT_EMAIL = try { & git config --global user.email 2>$null } catch { "not configured" }
$env:COPILOT_CUSTOM_INSTRUCTIONS_DIRS = "$env:USERPROFILE\.copilot;$env:USERPROFILE\.github\instructions"

$WORKFLOW_SCRIPTS = "$PROJECT_ROOT\skills\taskwarrior_expert\scripts"
if (($env:PATH -split ';') -notcontains $WORKFLOW_SCRIPTS) { $env:PATH = "$env:PATH;$WORKFLOW_SCRIPTS" }

$ONBOARD_PROMPT = "The anchored persona for this session is Jacazul (Jacare Azul). Activate 'jacazul-engine', 'taskwarrior-expert', and 'git-expert' skills immediately. Perform tactical discovery via 'tw-flow ponder'. IMPORTANT: Closely follow all banners, tips, warnings, and errors emitted by tw-flow and ponder as behavioral guidance. CACHE PROTOCOL: When any command returns [cached], REPRODUCE the last full output for the user - never hide info behind the signal. Use --force ONLY when the user asks or you have concrete reason to suspect stale cache."

$RESUME = $false
$CLEAN_ARGS = @()

foreach ($arg in $args) {
    if ($arg -eq "--resume") { $RESUME = $true } else { $CLEAN_ARGS += $arg }
}

$FINAL_ARGS = @()

if ($RESUME) {
    $FINAL_ARGS = $CLEAN_ARGS
} else {
    $FINAL_ARGS += "--agent"
    $FINAL_ARGS += "jacazul"
    $FINAL_ARGS += "-i"
    $FINAL_ARGS += $ONBOARD_PROMPT
    $FINAL_ARGS += $CLEAN_ARGS
}

$REAL_COPILOT = Get-Command copilot -ErrorAction SilentlyContinue
$GH_CMD = Get-Command gh -ErrorAction SilentlyContinue

if (-not $REAL_COPILOT -and $GH_CMD) {
    # Check if gh copilot extension is installed
    $extCheck = & gh extension list 2>$null | Select-String "github/gh-copilot"
    if (-not $extCheck) {
        Write-Host "`n[i] 'copilot' CLI nao encontrado. Tentando instalar a extensao oficial via 'gh'..." -ForegroundColor Cyan
        try {
            Start-Process -NoNewWindow -Wait -FilePath $GH_CMD.Source -ArgumentList @("extension", "install", "github/gh-copilot", "--force")
            Write-Host "[v] 'gh-copilot' instalado com sucesso!`n" -ForegroundColor Green
        } catch {
            Write-Host "`n[-] FATAL ERROR: Falha ao instalar a extensao do Copilot." -ForegroundColor White -BackgroundColor DarkRed
            exit 1
        }
    }
} elseif (-not $REAL_COPILOT -and -not $GH_CMD) {
    Write-Host "`n[-] FATAL ERROR: Tanto o 'copilot' quanto o 'gh' (GitHub CLI) estao ausentes." -ForegroundColor White -BackgroundColor DarkRed
    Write-Host "    Para usar o Jacazul-Copilot, voce precisa instalar o GitHub CLI: winget install --id GitHub.cli" -ForegroundColor Yellow
    exit 1
}

# [+] Auto-Deploy Jacazul Agent
$AGENT_SOURCE = "$PROJECT_ROOT\docs\agents\jacazul.md"
$AGENT_TARGET_DIR = "$env:USERPROFILE\.copilot\agents"
$AGENT_TARGET_FILE = "$AGENT_TARGET_DIR\jacazul.md"

if (Test-Path $AGENT_SOURCE) {
    if (-not (Test-Path $AGENT_TARGET_DIR)) { New-Item -ItemType Directory -Force -Path $AGENT_TARGET_DIR | Out-Null }
    # Copy agent to copilot global agents directory so `--agent jacazul` works natively
    Copy-Item -Path $AGENT_SOURCE -Destination $AGENT_TARGET_FILE -Force
}

if ($env:DEBUG) { Write-Host "[+] jacazul-copilot: Starting execution..." }

if ($env:DRY) {
    Write-Host "[v] Dry run complete. Copilot bootstrap verified for project [$($env:PROJECT_ID)]."
    exit 0
}

if ($REAL_COPILOT) {
    & $REAL_COPILOT.Source @FINAL_ARGS
} else {
    & $GH_CMD.Source "copilot" @FINAL_ARGS
}
