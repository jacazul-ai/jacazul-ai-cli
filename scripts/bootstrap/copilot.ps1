# 🐊 Jacazul - Bootstrap for Copilot (Global UNHINGED Mode - PowerShell)

$scriptDir = Split-Path $MyInvocation.MyCommand.Path -Parent
if (!$scriptDir) { $scriptDir = $PSScriptRoot }
$PROJECT_ROOT = (Resolve-Path (Join-Path $scriptDir "..\..\")).Path
$COPILOT_GLOBAL_DIR = Join-Path $env:USERPROFILE ".copilot"
$TEMPLATES_DIR = Join-Path $PROJECT_ROOT "templates"

# 1. Ensure global directories exist
$dirs = @("agents", "skills")
foreach ($d in $dirs) {
    $target = Join-Path $COPILOT_GLOBAL_DIR $d
    New-Item -ItemType Directory -Path $target -Force | Out-Null
}

function Set-JacazulLinkFile {
    param($Src, $Target)
    if (Test-Path $Target) { Remove-Item $Target -Force }
    try {
        New-Item -ItemType SymbolicLink -Path $Target -Value $Src -ErrorAction Stop | Out-Null
        if ($env:DEBUG) { Write-Output "🐊 Linked file: $Target -> $Src" }
    } catch {
        Copy-Item -Path $Src -Destination $Target -Force
        if ($env:DEBUG) { Write-Output "⚠️ Symlink failed (needs Dev Mode). Copied file instead: $Target" }
    }
}

function Set-JacazulJunction {
    param($Src, $Target)
    if (Test-Path $Target) {
        $item = Get-Item $Target -Force
        if ($item.LinkType -match "Junction|SymbolicLink") {
            $item.Delete()
        } else {
            Remove-Item $Target -Force -Recurse
        }
    }
    try {
        New-Item -ItemType Junction -Path $Target -Value $Src -ErrorAction Stop | Out-Null
        if ($env:DEBUG) { Write-Output "🐊 Junctioned dir: $Target -> $Src" }
    } catch {
        Write-Error "Failed to create junction for $Target to $Src"
    }
}

# 2. Link Global Agents
$AGENT_SRC = Join-Path $PROJECT_ROOT "agents\jacazul-copilot.md"
$AGENT_TARGET = Join-Path $COPILOT_GLOBAL_DIR "agents\jacazul.md"
if (Test-Path $AGENT_SRC) {
    Set-JacazulLinkFile -Src $AGENT_SRC -Target $AGENT_TARGET
}

# 3. Link Global Skills
$skillsPath = Join-Path $PROJECT_ROOT "skills\*"
if (Test-Path $skillsPath) {
    $skillsDirs = Get-ChildItem -Path $skillsPath -Directory
    foreach ($skill in $skillsDirs) {
        $target = Join-Path $COPILOT_GLOBAL_DIR "skills\$($skill.Name)"
        Set-JacazulJunction -Src $skill.FullName -Target $target
    }
}

# 4. Link Instructions Template
$INSTRUCTIONS_SRC = Join-Path $TEMPLATES_DIR "context\copilot-instructions.md"
$INSTRUCTIONS_TARGET = Join-Path $COPILOT_GLOBAL_DIR "copilot-instructions.md"
if (Test-Path $INSTRUCTIONS_SRC) {
    Set-JacazulLinkFile -Src $INSTRUCTIONS_SRC -Target $INSTRUCTIONS_TARGET
}

if ($env:DEBUG) {
    Write-Output "✅ Jacazul: Global Copilot environment verified (Windows)."
}
