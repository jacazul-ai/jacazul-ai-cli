# [Jacazul] Bootstrap - Gemini CLI Settings (PowerShell Version)
# Configures experimental agents and preview features surgically.

# Locate the project root directory
if (!$env:PROJECT_ROOT) {
    $scriptDir = Split-Path $MyInvocation.MyCommand.Path -Parent
    if (!$scriptDir) { $scriptDir = $PSScriptRoot }
    $env:PROJECT_ROOT = (Resolve-Path (Join-Path $scriptDir "..\..")).Path
}

$GEMINI_DIR = Join-Path $env:USERPROFILE ".gemini"
$SETTINGS_FILE = Join-Path $GEMINI_DIR "settings.json"
$TEMPLATE_SETTINGS = Join-Path $env:PROJECT_ROOT "templates\gemini\unhinged\settings.json"

# 1. Ensure the Gemini directory exists
if (!(Test-Path $GEMINI_DIR)) {
    if ($env:DEBUG -eq "true") {
        Write-Output "🐊 Creating Gemini directory at $GEMINI_DIR..."
    }
    New-Item -ItemType Directory -Path $GEMINI_DIR -Force | Out-Null
}

# 2. Ensure settings.json exists (use template if available)
if (!(Test-Path $SETTINGS_FILE)) {
    if (Test-Path $TEMPLATE_SETTINGS) {
        if ($env:DEBUG -eq "true") {
            Write-Output "🐊 Initializing Gemini settings.json from template..."
        }
        Copy-Item -Path $TEMPLATE_SETTINGS -Destination $SETTINGS_FILE -Force
    } else {
        "{}" | Set-Content $SETTINGS_FILE -Force
    }
}

# 3. Surgical update of settings.json
# Preserves existing config and only ensures required fields are present
try {
    $settingsContent = Get-Content -Raw -Path $SETTINGS_FILE
    if ([string]::IsNullOrWhiteSpace($settingsContent)) {
        $settingsJson = [PSCustomObject]@{}
    } else {
        $settingsJson = ConvertFrom-Json $settingsContent
    }
} catch {
    $settingsJson = [PSCustomObject]@{}
}

# Ensure the experimental section exists and enableAgents is set
if ($null -eq $settingsJson.experimental) {
    $settingsJson | Add-Member -MemberType NoteProperty -Name "experimental" -Value ([PSCustomObject]@{}) -Force
}
if ($settingsJson.experimental -is [System.Management.Automation.PSCustomObject]) {
    $settingsJson.experimental | Add-Member -MemberType NoteProperty -Name "enableAgents" -Value $true -Force
    $settingsJson.experimental | Add-Member -MemberType NoteProperty -Name "skills" -Value $true -Force
}

# Ensure the general section exists and previewFeatures is set
if ($null -eq $settingsJson.general) {
    $settingsJson | Add-Member -MemberType NoteProperty -Name "general" -Value ([PSCustomObject]@{}) -Force
}
if ($settingsJson.general -is [System.Management.Automation.PSCustomObject]) {
    $settingsJson.general | Add-Member -MemberType NoteProperty -Name "previewFeatures" -Value $true -Force
}

$settingsJson | ConvertTo-Json -Depth 10 | Set-Content $SETTINGS_FILE -Force

# 4. Inject Gemini Policies (Surgical)
$POLICIES_DIR = Join-Path $GEMINI_DIR "policies"
if (!(Test-Path $POLICIES_DIR)) {
    New-Item -ItemType Directory -Path $POLICIES_DIR -Force | Out-Null
}

# 4.1 Sync policies from root-level /policies/gemini directory
$REPO_POLICIES = Join-Path $env:PROJECT_ROOT "policies\gemini"
if (Test-Path $REPO_POLICIES) {
    $policyFiles = Get-ChildItem -Path $REPO_POLICIES -Filter *.toml
    foreach ($file in $policyFiles) {
        $target = Join-Path $POLICIES_DIR $file.Name
        if ($env:DEBUG -eq "true") {
            Write-Output "🐊 Syncing Gemini policy: $($file.Name)"
        }
        Copy-Item -Path $file.FullName -Destination $target -Force
    }
}

# 5. Link Global Skills (Surgical)
$SKILLS_DIR = Join-Path $GEMINI_DIR "skills"
if (!(Test-Path $SKILLS_DIR)) {
    New-Item -ItemType Directory -Path $SKILLS_DIR -Force | Out-Null
}

# 5.1 Link skills from root-level /skills directory
$REPO_SKILLS = Join-Path $env:PROJECT_ROOT "skills"
if (Test-Path $REPO_SKILLS) {
    $skills = Get-ChildItem -Path $REPO_SKILLS -Directory
    foreach ($skill in $skills) {
        $target = Join-Path $SKILLS_DIR $skill.Name
        
        # If target already exists, remove it first
        if (Test-Path $target) {
            $item = Get-Item -Path $target
            if ($item.Attributes -match "ReparsePoint") {
                $item.Delete()
            } else {
                Remove-Item -Path $target -Force -Recurse -ErrorAction SilentlyContinue
            }
        }
        
        if ($env:DEBUG -eq "true") {
            Write-Output "🐊 Linking global Gemini skill: $($skill.Name)"
        }
        
        # Use Junction as standard on Windows since it does not require administrator privileges
        try {
            cmd.exe /c "mklink /j `"$target`" `"$($skill.FullName)`"" | Out-Null
        } catch {
            try {
                New-Item -ItemType SymbolicLink -Path $target -Value $skill.FullName -ErrorAction Stop | Out-Null
            } catch {
                # Fallback to recursive copy if link creation fails
                Copy-Item -Path $skill.FullName -Destination $target -Recurse -Force
            }
        }
    }
}

# 5.2 Link legacy skills from templates
$TEMPLATES_SKILLS = Join-Path $env:PROJECT_ROOT "templates\skills"
if (Test-Path $TEMPLATES_SKILLS) {
    $legacySkills = Get-ChildItem -Path $TEMPLATES_SKILLS -Directory
    foreach ($skill in $legacySkills) {
        $target = Join-Path $SKILLS_DIR $skill.Name
        if (Test-Path $target) {
            continue
        }
        
        if ($env:DEBUG -eq "true") {
            Write-Output "🐊 Linking legacy Gemini skill from templates: $($skill.Name)"
        }
        
        try {
            cmd.exe /c "mklink /j `"$target`" `"$($skill.FullName)`"" | Out-Null
        } catch {
            try {
                New-Item -ItemType SymbolicLink -Path $target -Value $skill.FullName -ErrorAction Stop | Out-Null
            } catch {
                Copy-Item -Path $skill.FullName -Destination $target -Recurse -Force
            }
        }
    }
}

# Log only in DEBUG mode
if ($env:DEBUG -eq "true") {
    Write-Output "✅ Jacazul: Gemini configuration verified (enableAgents: true, previewFeatures: true)."
}
