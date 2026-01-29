# Taskwarrior Flow Scripts

Imperative helper scripts that simplify Taskwarrior usage for AI agents.

## tw-flow

Main script providing high-level commands for task management.

### Quick Reference

```bash
# Planning
./tw-flow plan <project:plan> "task1|tag|due" "task2|tag|due" ...

# Execution
./tw-flow next [project:plan]          # What's ready
./tw-flow execute <id>                 # Start task
./tw-flow done <id> [note]             # Complete task
./tw-flow pause <id>                   # Pause task

# Context
./tw-flow note <id> <type> <msg>       # Add annotation
./tw-flow context <id>                 # Show full details

# Viewing
./tw-flow plans                      # List all plans
./tw-flow status [project:plan]        # Overview
./tw-flow active                       # Active tasks
./tw-flow blocked                      # Blocked tasks
./tw-flow overdue                      # Overdue tasks

# Modifications
./tw-flow urgent <id> [urgency]        # Make urgent
./tw-flow block <id> <dep_id>          # Add dependency
./tw-flow unblock <id> <dep_id>        # Remove dependency
./tw-flow wait <id> <date>             # Put on hold
```

### Examples

#### Create a 3-task plan

```bash
./tw-flow plan copilot:login-feature \
  "Design auth flow|research|today" \
  "Implement JWT|implementation|tomorrow" \
  "Write tests|testing|2days"
```

#### Work on tasks

```bash
# See what's next
./tw-flow next copilot:login-feature

# Start first task
./tw-flow execute 42

# Add context
./tw-flow note 42 research "Found passport.js library"
./tw-flow note 42 decision "Using JWT tokens"

# Complete
./tw-flow done 42 "Design complete"

# Next task auto-unblocks
./tw-flow execute 43
```

#### Check progress

```bash
./tw-flow status copilot:login-feature
```

### Dependencies

- `bash` (4.0+)
- `taskwarrior` (installed and configured)
- `jq` (for JSON parsing)
- `bc` (for calculations)
- `grep` with Perl regex support

## Testing

Run the smoke test to validate all commands:

```bash
./test-tw-flow.sh
```

The smoke test validates:
- Basic command execution
- Plan creation and management
- Task lifecycle (execute, note, context, done)
- Edge cases (special characters, empty states)
- All viewing commands (plans, status, active, blocked, overdue)

### Dependencies

```bash
# System-wide installation
sudo cp ./tw-flow /usr/local/bin/
sudo chmod +x /usr/local/bin/tw-flow

# User installation
mkdir -p ~/.local/bin
cp ./tw-flow ~/.local/bin/
chmod +x ~/.local/bin/tw-flow
# Add ~/.local/bin to PATH if not already there

# Or use directly from repo
././tw-flow help
```

## Design Philosophy

These scripts follow these principles:

1. **Imperative over declarative** - Commands do actions, not describe states
2. **Smart defaults** - Minimize required parameters
3. **Automatic relationships** - Dependencies created automatically in `plan`
4. **Clear feedback** - Always show what changed
5. **Error prevention** - Check preconditions before executing
6. **Context preservation** - Annotations always include type prefix

## Architecture

```
tw-flow
├── Planning commands    (plan)
├── Execution commands   (next, execute, done, pause)
├── Context commands     (note, context)
├── Viewing commands     (status, active, blocked, overdue)
└── Modification commands (urgent, block, unblock, wait)
```

Each command:
- Validates inputs
- Provides clear error messages
- Shows success confirmation
- Displays relevant next actions

## Future Enhancements

Potential additions:

- `./tw-flow edit <id>` - Edit task description
- `./tw-flow move <id> <new_project:plan>` - Move task to different plan
- `./tw-flow split <id>` - Split task into subtasks
- `./tw-flow merge <id1> <id2>` - Merge two tasks
- `./tw-flow dashboard` - Show overall statistics
- `./tw-flow export <project:plan>` - Export plan to markdown
- `./tw-flow import <file>` - Import plan from markdown

## Contributing

When adding new commands:

1. Add function `cmd_<name>` with clear parameter validation
2. Update `show_usage()` with command documentation
3. Add case in `main()` dispatcher
4. Follow existing patterns for output (error, success, info, warning)
5. Test with invalid inputs to ensure good error messages

## License

MIT
