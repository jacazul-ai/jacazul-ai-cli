# [Jacazul] Taskwarrior Bootstrap (PowerShell Version)

if ($env:PROJECT_ID) {
    $env:JACAZUL_HOME = Join-Path $env:USERPROFILE ".jacazul-ai"
    $env:TASKDATA = Join-Path $env:JACAZUL_HOME ".task\$env:PROJECT_ID"
    $TASKRC = Join-Path $env:JACAZUL_HOME ".taskrc"

    if ($env:JACAZUL_MODE -eq "UNHINGED") {
        $env:TASKRC = $TASKRC
        
        # Ensure the .taskrc is in place
        if (!(Test-Path $TASKRC)) {
            Write-Output "[Jacazul] Initializing Unhinged Taskwarrior config at $TASKRC..."
            $parentHome = Split-Path $TASKRC -Parent
            if (!(Test-Path $parentHome)) {
                New-Item -ItemType Directory -Path $parentHome -Force | Out-Null
            }
            Copy-Item -Path (Join-Path $env:PROJECT_ROOT "templates\taskwarrior\unhinged\.taskrc") -Destination $TASKRC -Force
            
            $content = Get-Content -Raw -Path $TASKRC
            $escapedLocation = ($env:JACAZUL_HOME -replace '\\', '/')
            $content = $content -replace 'data.location=.*', "data.location=$escapedLocation/.task"
            $content | Set-Content $TASKRC -Force
        } else {
            # Surgical sync of UDAs from project template to global config
            $TEMPLATE_RC = Join-Path $env:PROJECT_ROOT "templates\taskwarrior\unhinged\.taskrc"
            if (Test-Path $TEMPLATE_RC) {
                $lines = Get-Content -Path $TEMPLATE_RC
                $existingContent = Get-Content -Path $TASKRC
                foreach ($line in $lines) {
                    if ($line -like "uda.*") {
                        $key = $line.Split('=')[0]
                        $found = $false
                        foreach ($el in $existingContent) {
                            if ($el.StartsWith("$key=")) {
                                $found = $true
                                break
                            }
                        }
                        if (!$found) {
                            if ($env:DEBUG) { Write-Output "[Jacazul] Injecting missing UDA from project: $line" }
                            Add-Content -Path $TASKRC -Value $line
                        }
                    }
                }
            }
            # Always ensure data.location is correct in the existing config
            $content = Get-Content -Raw -Path $TASKRC
            $escapedLocation = ($env:JACAZUL_HOME -replace '\\', '/')
            if ($content -notmatch "data.location=$escapedLocation/.task") {
                $content = $content -replace 'data.location=.*', "data.location=$escapedLocation/.task"
                $content | Set-Content $TASKRC -Force
            }
        }
    }

    # Surgical sync of UDAs for COUNSELOR mode (caged template)
    if ($env:JACAZUL_MODE -ne "UNHINGED" -and $env:TASKRC -and (Test-Path $env:TASKRC)) {
        $TEMPLATE_RC = Join-Path $env:PROJECT_ROOT "templates\taskwarrior\caged\.taskrc"
        if (Test-Path $TEMPLATE_RC) {
            $lines = Get-Content -Path $TEMPLATE_RC
            $existingContent = Get-Content -Path $env:TASKRC
            foreach ($line in $lines) {
                if ($line -like "uda.*") {
                    $key = $line.Split('=')[0]
                    $found = $false
                    foreach ($el in $existingContent) {
                        if ($el.StartsWith("$key=")) {
                            $found = $true
                            break
                        }
                    }
                    if (!$found) {
                        if ($env:DEBUG) { Write-Output "[Jacazul] Injecting missing UDA: $line" }
                        Add-Content -Path $env:TASKRC -Value $line
                    }
                }
            }
        }
    }

    # Create task data directory if missing
    if (!(Test-Path $env:TASKDATA)) {
        Write-Output "[Jacazul] Creating task data directory: $env:TASKDATA"
        New-Item -ItemType Directory -Path $env:TASKDATA -Force | Out-Null
    }

    # Taskwarrior 2.x to 3.x Migration (Taskchampion)
    $REAL_TASK = $env:JACAZUL_REAL_TASK
    if (!$REAL_TASK) {
        $taskBins = Get-Command task -All -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source
        foreach ($bin in $taskBins) {
            if ($bin -notmatch "scripts\\task") {
                $REAL_TASK = $bin
                break
            }
        }
        if (!$REAL_TASK) { $REAL_TASK = "task.exe" }
        $env:JACAZUL_REAL_TASK = $REAL_TASK
    }

    $TW_VERSION = "3"
    $verOut = & "$REAL_TASK" --version 2>$null
    if ($LastExitCode -eq 0 -and $verOut) {
        $verStr = [string]$verOut
        $TW_VERSION = $verStr.Split('.')[0].Trim()
    }

    if ($TW_VERSION -eq "3") {
        $pendingData = Join-Path $env:TASKDATA "pending.data"
        $sqliteData = Join-Path $env:TASKDATA "taskchampion.sqlite3"
        if ((Test-Path $pendingData) -and !(Test-Path $sqliteData)) {
            Write-Output "[WARNING] Detected Taskwarrior 2.x data in version 3 environment."
            Write-Output "[Jacazul] Migrating database to SQLite (task import-v2)..."
            
            $backupDir = Join-Path $env:JACAZUL_HOME ".task-backups\migration-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
            New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
            Copy-Item -Path (Join-Path $env:TASKDATA "*.data") -Destination $backupDir -Force
            
            & "$REAL_TASK" import-v2 rc.hooks=0
            if ($LastExitCode -eq 0) {
                Write-Output "[OK] Migration successful."
            } else {
                Write-Error "[ERROR] Migration failed! Please check logs."
            }
        }
    }

    # Initialize independent session focus if JACAZUL_FOCUS_PLAN is set
    if ($env:JACAZUL_FOCUS_PLAN -and $env:JACAZUL_SESSION_ID) {
        $SESSION_FILE = Join-Path $env:TASKDATA "focus-$($env:JACAZUL_SESSION_ID).json"
        if (!(Test-Path $SESSION_FILE)) {
            if ($env:DEBUG) {
                Write-Output "[Jacazul] Creating independent session focus: $SESSION_FILE"
            }
            $focusObj = [PSCustomObject]@{
                focused_plan = $env:JACAZUL_FOCUS_PLAN
                focused_task_uuid = if ($env:JACAZUL_FOCUS_TASK) { $env:JACAZUL_FOCUS_TASK } else { "" }
                task_track = @()
                plans_of_interest = @()
            }
            $focusObj | ConvertTo-Json | Set-Content $SESSION_FILE -Force
        }
    }

    # Purge orphan session caches
    $FLOW_CACHE_DIR = Join-Path $env:JACAZUL_HOME "cache/tw-flow/$env:PROJECT_ID"
    if ((Test-Path $FLOW_CACHE_DIR) -and $env:JACAZUL_SESSION_ID) {
        $subDirs = Get-ChildItem -Path $FLOW_CACHE_DIR -Directory
        foreach ($d in $subDirs) {
            $dirname = $d.Name
            if ($dirname -eq "global") { continue }
            if ($dirname -eq $env:JACAZUL_SESSION_ID) { continue }
            Remove-Item -Path $d.FullName -Recurse -Force -ErrorAction SilentlyContinue
        }
    }

    if ($env:DEBUG) {
        Write-Output "[Jacazul] Task Data: $env:TASKDATA"
        if ($env:TASKRC) { Write-Output "[Jacazul] Task RC: $env:TASKRC" }
        if ($env:JACAZUL_SESSION_ID) { Write-Output "[Jacazul] Session ID: $env:JACAZUL_SESSION_ID" }
    }
}