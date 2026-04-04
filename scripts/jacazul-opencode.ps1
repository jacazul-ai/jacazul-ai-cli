<#
.SYNOPSIS
    jacazul-opencode: Opencode CLI unhinged (PowerShell execution)
#>

$ErrorActionPreference = "Stop"
$SCRIPT_DIR = $PSScriptRoot
$PROJECT_ROOT = (Resolve-Path "$SCRIPT_DIR\..").Path

$BOOTSTRAP_ENV = "$PROJECT_ROOT\scripts\bootstrap\environment.ps1"
if (Test-Path $BOOTSTRAP_ENV) { . $BOOTSTRAP_ENV }

$env:PROJECT_ID = $env:PROJECT_ID
$env:CONTEXT_REAL_PATH = (Get-Location).Path
$env:CONTEXT_SYSTEM_USER = [Environment]::UserName

$VENV_SCRIPTS = "$env:USERPROFILE\.jacazul-ai\.venv\Scripts"
if (($env:PATH -split ';') -notcontains $VENV_SCRIPTS) { $env:PATH = "$VENV_SCRIPTS;$env:PATH" }

$WORKFLOW_SCRIPTS = "$PROJECT_ROOT\skills\taskwarrior_expert\scripts"
if (($env:PATH -split ';') -notcontains $WORKFLOW_SCRIPTS) { $env:PATH = "$env:PATH;$WORKFLOW_SCRIPTS" }

$RESUME = $false
$CLEAN_ARGS = @()

foreach ($arg in $args) {
    if ($arg -eq "--resume") { $RESUME = $true } else { $CLEAN_ARGS += $arg }
}

$FINAL_ARGS = @()
$hasAgentFlag = $false

foreach ($arg in $CLEAN_ARGS) {
    if ($arg -match "--agent") { $hasAgentFlag = $true }
    $FINAL_ARGS += $arg
}

if (-not $hasAgentFlag) {
    $FINAL_ARGS = @("--agent", "jacazul") + $FINAL_ARGS
}

$NPM_GLOBAL = "$env:APPDATA\npm"
if (($env:PATH -split ';') -notcontains $NPM_GLOBAL) {
    $env:PATH = "$env:PATH;$NPM_GLOBAL"
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($userPath -notmatch "npm") {
        [Environment]::SetEnvironmentVariable("Path", "$userPath;$NPM_GLOBAL", "User")
    }
}

$opencodeCmd = Get-Command opencode -ErrorAction SilentlyContinue
if (-not $opencodeCmd) {
    $fallbackPath = "$env:USERPROFILE\.opencode\bin\opencode.exe"
    if (Test-Path $fallbackPath) {
        $opencodeCmd = Get-Command $fallbackPath
    } else {
        Write-Host "`n[i] 'opencode' CLI nao encontrado. Tentando instalar automaticamente via npm..." -ForegroundColor Cyan
        $npmCmd = Get-Command npm -ErrorAction SilentlyContinue
        if (-not $npmCmd) {
            Write-Host "[-] FATAL ERROR: O 'npm' (Node.js) nao esta instalado no sistema." -ForegroundColor White -BackgroundColor DarkRed
            exit 1
        }
        try {
            Start-Process -NoNewWindow -Wait -FilePath $npmCmd.Source -ArgumentList @("install", "-g", "opencode", "--force")
            $opencodeCmd = Get-Command opencode -ErrorAction SilentlyContinue
            if (-not $opencodeCmd) { 
                $fallbackNpm = "$env:APPDATA\npm\opencode.cmd"
                if (Test-Path $fallbackNpm) { $opencodeCmd = Get-Command $fallbackNpm } else { throw "Binario oculto" }
            }
            Write-Host "[v] 'opencode' CLI instalado com sucesso!`n" -ForegroundColor Green
        } catch {
            Write-Host "`n[-] FATAL ERROR: A instalacao automatica do 'opencode'." -ForegroundColor White -BackgroundColor DarkRed
            Write-Host "    -> Solucao: Provavelmente nao instalavel via NPM global padrão. Instale-o manualmente." -ForegroundColor Yellow
            exit 1
        }
    }
}

# [+] Auto-Deploy Jacazul Agent
$AGENT_SOURCE = "$PROJECT_ROOT\docs\agents\jacazul.md"
$AGENT_TARGET_DIR = "$env:USERPROFILE\.opencode\agents"
$AGENT_TARGET_FILE = "$AGENT_TARGET_DIR\jacazul.md"

if (Test-Path $AGENT_SOURCE) {
    if (-not (Test-Path $AGENT_TARGET_DIR)) { New-Item -ItemType Directory -Force -Path $AGENT_TARGET_DIR | Out-Null }
    # Copy agent to opencode global agents directory so `--agent jacazul` works natively
    Copy-Item -Path $AGENT_SOURCE -Destination $AGENT_TARGET_FILE -Force
}

if ($env:DEBUG) { Write-Host "[+] jacazul-opencode: Starting for project [$($env:PROJECT_ID)]" }

if ($env:DRY) {
    Write-Host "[v] Dry run complete. Opencode bootstrap verified for project [$($env:PROJECT_ID)]."
    exit 0
}

& $opencodeCmd.Source @FINAL_ARGS
