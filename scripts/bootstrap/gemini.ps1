<#
.SYNOPSIS
    Jacazul - Bootstrap for Gemini CLI Settings (PowerShell)
    Configures experimental agents and preview features surgically.
#>

$ErrorActionPreference = "Stop"
$SCRIPT_DIR = $PSScriptRoot
$PROJECT_ROOT = (Resolve-Path "$SCRIPT_DIR\..\..").Path
$TEMPLATES_DIR = "$PROJECT_ROOT\templates"

$GEMINI_DIR = if ($args.Count -gt 0) { $args[0] } else { "$env:USERPROFILE\.gemini" }
$SETTINGS_FILE = "$GEMINI_DIR\settings.json"
$TEMPLATE_SETTINGS = "$PROJECT_ROOT\templates\gemini\unhinged\settings.json"

# 1. Ensure the Gemini directory exists
if (!(Test-Path $GEMINI_DIR)) {
    Write-Host "[+] Creating Gemini directory at $GEMINI_DIR..."
    New-Item -ItemType Directory -Force -Path $GEMINI_DIR | Out-Null
}

# 2. Ensure settings.json exists
if (!(Test-Path $SETTINGS_FILE)) {
    if (Test-Path $TEMPLATE_SETTINGS) {
        Write-Host "[+] Initializing Gemini settings.json from template..."
        Copy-Item -Path $TEMPLATE_SETTINGS -Destination $SETTINGS_FILE -Force
    } else {
        Set-Content -Path $SETTINGS_FILE -Value "{}" -Encoding Ascii
    }
}

# 3. Surgical update without breaking JSON (Compatible with PS 5.1+)
try {
    $settingsRaw = Get-Content -Path $SETTINGS_FILE -Raw
    $settings = if ([string]::IsNullOrWhiteSpace($settingsRaw) -or $settingsRaw.Trim() -eq "{}") { 
        New-Object PSObject 
    } else { 
        $settingsRaw | ConvertFrom-Json 
    }
    
    if (-not $settings.PSObject.Properties.Match("experimental").Count) {
        $settings | Add-Member -MemberType NoteProperty -Name "experimental" -Value (New-Object PSObject)
    }
    $settings.experimental | Add-Member -MemberType NoteProperty -Name "enableAgents" -Value $true -Force
    
    if (-not $settings.PSObject.Properties.Match("general").Count) {
        $settings | Add-Member -MemberType NoteProperty -Name "general" -Value (New-Object PSObject)
    }
    $settings.general | Add-Member -MemberType NoteProperty -Name "previewFeatures" -Value $true -Force
    
    # Compress JSON logic equivalent to jq
    $settings | ConvertTo-Json -Depth 10 | Set-Content -Path $SETTINGS_FILE -Encoding Ascii
} catch {
    Write-Host "[-] Aviso: Falha silenciosa ao atualizar $SETTINGS_FILE." -ForegroundColor Yellow
}

# 4. Link Global Skills
$SKILLS_DIR = "$GEMINI_DIR\skills"
if (!(Test-Path $SKILLS_DIR)) { New-Item -ItemType Directory -Force -Path $SKILLS_DIR | Out-Null }

$ROOT_SKILLS = "$PROJECT_ROOT\skills"
if (Test-Path $ROOT_SKILLS) {
    Get-ChildItem -Path $ROOT_SKILLS -Directory | ForEach-Object {
        $skillDir = $_.FullName
        $name = $_.Name
        $target = "$SKILLS_DIR\$name"
        
        # Uses Windows Junction points (Directory symbolic links that don't require Admin privileges)
        if (Test-Path $target) {
            Remove-Item -Path $target -Force -Recurse -ErrorAction SilentlyContinue
        }
        
        if ($env:DEBUG) { Write-Host "[+] Linking global Gemini skill: $name" }
        New-Item -ItemType Junction -Path $target -Target $skillDir | Out-Null
    }
}

# 4.2 Link legacy skills from templates
$LEGACY_SKILLS = "$TEMPLATES_DIR\skills"
if (Test-Path $LEGACY_SKILLS) {
    Get-ChildItem -Path $LEGACY_SKILLS -Directory | ForEach-Object {
        $skillDir = $_.FullName
        $name = $_.Name
        $target = "$SKILLS_DIR\$name"
        
        if (!(Test-Path $target)) {
            if ($env:DEBUG) { Write-Host "[+] Linking legacy Gemini skill: $name" }
            New-Item -ItemType Junction -Path $target -Target $skillDir | Out-Null
        }
    }
}

if ($env:DEBUG) {
    Write-Host "[v] Jacazul: Gemini configuration verified (enableAgents: true, previewFeatures: true)."
}
