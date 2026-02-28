# Per-Project Taskwarrior Database Architecture

## Overview

This architecture enables isolated Taskwarrior databases per project, providing better organization, isolation, and scalability.

## Architecture

### Directory Structure

```
~/.task/
  ├── jacazul-ai_jacazul-ai-cli/      # Project-specific database
  │   ├── pending.data
  │   ├── completed.data
  │   ├── backlog.data
  │   └── undo.data
  ├── outro_projeto/                # Another project
  │   └── ...
  └── [central]/                    # Legacy central database (optional)
```

### Components

#### 1. **taskp** - Project-Aware Wrapper

Location: `/project/templates/skills/taskwarrior_expert/scripts/taskp`

Automatically detects the current project and uses the appropriate database.

**Detection Priority:**
1. `$PROJECT_ID` environment variable (copilot environment)
2. Git repository (parent_current format)
3. Current directory name (fallback)

**Usage:**
```bash
# Automatically uses correct database
taskp list
taskp add "New task"
taskp 42 done

# Manual override
PROJECT_ID=other_project taskp list
```

#### 2. **tw-flow** - Updated for TASKDATA

Version: 1.3.0

Automatically sets `TASKDATA` based on `PROJECT_ID` before executing commands.

**Changes:**
- Added `detect_and_set_taskdata()` function
- Executes before any taskwarrior operations
- Creates project directory if it doesn't exist

**Usage:**
```bash
./tw-flow initiative my-feature "DESIGN|Task 1|research|today"
./tw-flow next my-feature
./tw-flow execute <uuid>
```

#### 3. **ponder** - Dashboard with TASKDATA Support

Automatically uses project-specific database when `PROJECT_ID` is set.

**Usage:**
```bash
./ponder jacazul-ai_jacazul-ai-cli           # Show project overview
./ponder jacazul-ai_jacazul-ai-cli:feature   # Show specific plan
```

## Migration Process

### From Central to Per-Project Database

```bash
# 1. Export from central database
task export > /tmp/tasks-backup.json

# 2. Import to project database
TASKDATA=~/.task/PROJECT_ID task import /tmp/tasks-backup.json rc.hooks=0

# 3. Verify
TASKDATA=~/.task/PROJECT_ID task count
```

## Benefits

### 1. **Isolation**
- Each project has its own task database
- No cross-contamination between projects
- Clean separation of concerns

### 2. **Performance**
- Smaller databases = faster queries
- No need to filter by project constantly
- Reduced index size

### 3. **Backup & Portability**
- Easy to backup individual projects
- Simple to archive completed projects
- Can share project tasks independently

### 4. **Scalability**
- Scales linearly with number of projects
- No single-database bottleneck
- Easy to distribute across teams

## Usage Examples

### Scenario 1: Working on Current Project

```bash
# Automatic detection via PROJECT_ID
cd /path/to/jacazul-ai_jacazul-ai-cli/
taskp list                    # Uses jacazul-ai_jacazul-ai-cli DB
taskp add "New feature"       # Adds to project DB
```

### Scenario 2: Switching Projects

```bash
# Change directory
cd /path/to/another_project/

# taskp automatically switches
taskp list                    # Uses another_project DB
```

### Scenario 3: Manual Project Selection

```bash
# Override PROJECT_ID
PROJECT_ID=specific_project taskp list

# Or use TASKDATA directly
TASKDATA=~/.task/specific_project task list
```

### Scenario 4: Creating an Initiative

```bash
cd /project/templates/skills/taskwarrior_expert/scripts

./tw-flow initiative new-feature \
  "DESIGN|Design API|research|today" \
  "EXECUTE|Implement|implementation|tomorrow" \
  "TEST|Test|testing|2days"

# Tasks created in project database automatically
```

## Environment Variables

### PROJECT_ID

Set automatically by the copilot script:

```bash
PROJECT_ID="${PARENT_DIR}_${CURRENT_DIR}"
```

Example: `/home/user/ai_cli_sandboxed/` → `PROJECT_ID=user_ai_cli_sandboxed`

### TASKDATA

Set automatically by `taskp`, `tw-flow`, and `ponder` based on `PROJECT_ID`:

```bash
export TASKDATA="$HOME/.task/$PROJECT_ID"
```

## Compatibility

- **Taskwarrior Version:** 2.6.2 (tested)
- **Future:** Architecture supports Taskwarrior 3.x (SQLite) migration
- **Backward Compatible:** Central database still accessible without `PROJECT_ID`

## Troubleshooting

### Tasks Not Showing Up

```bash
# Check which database is being used
echo $PROJECT_ID
echo $TASKDATA

# Verify database exists
ls -la ~/.task/$PROJECT_ID/

# Check task count
taskp count
```

### Wrong Database Selected

```bash
# Explicitly set PROJECT_ID
export PROJECT_ID=correct_project_name
taskp list

# Or use TASKDATA directly
TASKDATA=~/.task/correct_project task list
```

### Migration Issues

```bash
# Verify export
task export | jq '. | length'

# Test import (dry run - check output first)
TASKDATA=~/.task/test task import /tmp/backup.json rc.hooks=0

# If successful, import to real project
TASKDATA=~/.task/PROJECT_ID task import /tmp/backup.json rc.hooks=0
```

## Future Enhancements

### Planned for Taskwarrior 3.x Migration

When Taskwarrior 3.x becomes available in package repositories:

1. **SQLite Backend**: Native SQLite support (taskchampion.sqlite3)
2. **Better Performance**: Improved query performance with indexes
3. **Transaction Safety**: ACID compliance for data integrity

### Migration Path to 3.x

```bash
# 1. Export from 2.6.2
TASKDATA=~/.task/PROJECT_ID task export > /tmp/project.json

# 2. Install Taskwarrior 3.x (when available)
sudo apt install taskwarrior  # version 3.x

# 3. Import to 3.x
TASKDATA=~/.task/PROJECT_ID task import /tmp/project.json

# 4. Verify SQLite database created
ls -la ~/.task/PROJECT_ID/taskchampion.sqlite3
```

## References

- [Taskwarrior Documentation](https://taskwarrior.org/docs/)
- [Taskwarrior 3.x Upgrade Guide](https://taskwarrior.org/docs/upgrade-3/)
- [tw-flow Script](../templates/skills/taskwarrior_expert/scripts/tw-flow)
- [taskp Wrapper](../templates/skills/taskwarrior_expert/scripts/taskp)
- [ponder Dashboard](../templates/skills/taskwarrior_expert/scripts/ponder)
