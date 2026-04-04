# 🐊 Jacazul Taskwarrior Bootstrap (PowerShell)
# Sets TASKDATA based on JACAZUL_MODE and PROJECT_ID
# Initializes independent session focus if JACAZUL_FOCUS_PLAN is set

if ($env:PROJECT_ID) {
    $env:JACAZUL_HOME = "$env:USERPROFILE\.jacazul-ai"
    $env:TASKDATA = "$env:JACAZUL_HOME\.task\$($env:PROJECT_ID)"

    if ($env:JACAZUL_MODE -eq "UNHINGED") {
        $env:TASKRC = "$env:JACAZUL_HOME\.taskrc"
        
        # Ensure the .taskrc is in place
        if (!(Test-Path $env:TASKRC)) {
            Write-Host "🐊 Initializing Unhinged Taskwarrior config at $($env:TASKRC)..." -ForegroundColor Cyan
            if (!(Test-Path $env:JACAZUL_HOME)) { New-Item -ItemType Directory -Force -Path $env:JACAZUL_HOME | Out-Null }
            $TEMPLATE_RC = "$PROJECT_ROOT\templates\taskwarrior\unhinged\.taskrc"
            if (Test-Path $TEMPLATE_RC) {
                Copy-Item -Path $TEMPLATE_RC -Destination $env:TASKRC
                # Explicitly override data.location to avoid confusion
                $content = Get-Content $env:TASKRC
                $content = $content -replace "data.location=.*", "data.location=$($env:JACAZUL_HOME)\.task"
                $content | Set-Content $env:TASKRC
            }
        } else {
            # Surgical sync of UDAs from project template to global config
            $TEMPLATE_RC = "$PROJECT_ROOT\templates\taskwarrior\unhinged\.taskrc"
            if (Test-Path $TEMPLATE_RC) {
                $templateContent = Get-Content $TEMPLATE_RC
                $taskrcContent = Get-Content $env:TASKRC
                
                foreach ($line in $templateContent) {
                    if ($line -match "^uda\.") {
                        $key = ($line -split "=")[0]
                        if ($taskrcContent -notmatch "^$([regex]::Escape($key))=") {
                            if ($env:DEBUG) { Write-Host "🐊 Injecting missing UDA from project: $line" -ForegroundColor Gray }
                            Add-Content -Path $env:TASKRC -Value $line
                        }
                    }
                }
            }
            # Always ensure data.location is correct in the existing config
            $content = Get-Content $env:TASKRC
            if ($content -notmatch "data.location=$($env:JACAZUL_HOME -replace '\\', '\\')\\.task") {
                 $content = $content -replace "data.location=.*", "data.location=$($env:JACAZUL_HOME)\.task"
                 $content | Set-Content $env:TASKRC
            }
        }
    }

    # Create task data directory if missing
    if (!(Test-Path $env:TASKDATA)) {
        Write-Host "🐊 Creating task data directory: $($env:TASKDATA)" -ForegroundColor Cyan
        New-Item -ItemType Directory -Force -Path $env:TASKDATA | Out-Null
    }

    # Taskwarrior 2.x to 3.x Migration (Taskchampion)
    if ($env:JACAZUL_REAL_TASK -and $env:JACAZUL_TASK_VERSION -eq "3") {
        # Check if legacy data exists but SQLite doesn't
        if ((Test-Path "$($env:TASKDATA)\pending.data") -and !(Test-Path "$($env:TASKDATA)\taskchampion.sqlite3")) {
            Write-Host "⚠️  Detected Taskwarrior 2.x data in version 3 environment." -ForegroundColor Yellow
            Write-Host "🐊 Migrating database to SQLite (task import-v2)..." -ForegroundColor Cyan
            
            # Backup first just in case
            $BACKUP_DIR = "$($env:JACAZUL_HOME)\.task-backups\migration-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
            New-Item -ItemType Directory -Force -Path $BACKUP_DIR | Out-Null
            Copy-Item -Path "$($env:TASKDATA)\*.data" -Destination $BACKUP_DIR
            
            # Perform import
            # Using the real task binary directly
            & $env:JACAZUL_REAL_TASK f"rc:$($env:TASKRC)" f"rc.data.location=$($env:TASKDATA)" import-v2 rc.hooks=0
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ Migration successful." -ForegroundColor Green
            } else {
                Write-Host "❌ Migration failed! Please check logs." -ForegroundColor Red
            }
        }
    }

    # Initialize independent session focus if JACAZUL_FOCUS_PLAN is set
    if ($env:JACAZUL_FOCUS_PLAN -and $env:JACAZUL_SESSION_ID) {
        $SESSION_FILE = "$($env:TASKDATA)\focus-$($env:JACAZUL_SESSION_ID).json"
        if (!(Test-Path $SESSION_FILE)) {
            if ($env:DEBUG) {
                Write-Host "🐊 Creating independent session focus: $SESSION_FILE" -ForegroundColor Gray
            }
            $focusPlan = $env:JACAZUL_FOCUS_PLAN
            $focusTask = if ($env:JACAZUL_FOCUS_TASK) { $env:JACAZUL_FOCUS_TASK } else { "" }
            
            $focusJson = @"
{
  "focused_plan": "$focusPlan",
  "focused_task_uuid": "$focusTask",
  "task_track": [],
  "plans_of_interest": []
}
"@
            $focusJson | Set-Content -Path $SESSION_FILE -Encoding UTF8
        }
    }

    # Purge orphan session caches (dirs from expired sessions)
    $FLOW_CACHE_DIR = "$($env:JACAZUL_HOME)\cache\tw-flow\$($env:PROJECT_ID)"
    if ((Test-Path $FLOW_CACHE_DIR) -and $env:JACAZUL_SESSION_ID) {
        Get-ChildItem -Path $FLOW_CACHE_DIR -Directory | ForEach-Object {
            $dirname = $_.Name
            if ($dirname -ne "global" -and $dirname -ne $env:JACAZUL_SESSION_ID) {
                Remove-Item -Path $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
            }
        }
    }

    # Emit logs only in DEBUG mode
    if ($env:DEBUG) {
        Write-Host "🐊 Task Data: $($env:TASKDATA)" -ForegroundColor Gray
        if ($env:TASKRC) { Write-Host "🐊 Task RC: $($env:TASKRC)" -ForegroundColor Gray }
        if ($env:JACAZUL_SESSION_ID) { Write-Host "🐊 Session ID: $($env:JACAZUL_SESSION_ID)" -ForegroundColor Gray }
    }
}
