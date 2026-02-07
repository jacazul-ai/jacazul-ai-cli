#!/bin/bash
set -e

PROJECT_ID="${1:-$PROJECT_ID}"
[ -z "$PROJECT_ID" ] && { echo "ERROR: PROJECT_ID required"; exit 1; }

TASKDATA="$HOME/.task/$PROJECT_ID"
echo "🔍 Scanning $PROJECT_ID..."

TASKS=$(TASKDATA="$TASKDATA" task export | jq -r --arg pid "$PROJECT_ID:" '
  .[] | 
  if .project and ((.project | type) == "string") and (.project | startswith($pid)) then
    .uuid + " " + .project
  else empty end
')

[ -z "$TASKS" ] && { echo "✅ No tasks with prefix"; exit 0; }

COUNT=$(echo "$TASKS" | wc -l)
echo "📋 Found $COUNT tasks"

BACKUP="/tmp/tw-backup-$(date +%Y%m%d-%H%M%S).json"
TASKDATA="$TASKDATA" task export > "$BACKUP"
echo "💾 Backup: $BACKUP"

echo "$TASKS" | while read uuid old_project; do
    new_project="${old_project#$PROJECT_ID:}"
    echo "  $uuid → $new_project"
    TASKDATA="$TASKDATA" task "$uuid" modify "project:$new_project" rc.confirmation=off >/dev/null 2>&1 || true
done

echo "✅ Done!"
