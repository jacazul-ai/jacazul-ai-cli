## Initiative Rename Workaround (2026-02-10)

**Problem:** `tw-flow rename` command doesn't exist yet. Need to rename initiatives manually.

**Solution:** Use taskwarrior directly with UUID iteration:

```bash
# List all task UUIDs in the initiative
for uuid in $(TASKDATA=/home/jacazul/.task/$PROJECT_ID task project:old-name uuids); do
  echo "yes" | TASKDATA=/home/jacazul/.task/$PROJECT_ID task $uuid modify project:new-name 2>/dev/null
done
```

**Example:** Renamed `piraz_ai_cli_sandboxed.sandbox-entrypoint` → `sandbox-entrypoint`

**Implementation needed:**
- Add `tw-flow rename <old-name> <new-name>` command
- Should handle confirmation automatically (rc.confirmation=off issue)
- Link to tw-flow-to-py initiative

