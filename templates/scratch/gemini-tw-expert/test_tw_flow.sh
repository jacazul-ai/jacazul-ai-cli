#!/bin/bash
# Smoke test for tw-flow script
# Tests basic functionality and edge cases

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TW_FLOW="$SCRIPT_DIR/tw-flow"
PONDER="$SCRIPT_DIR/ponder"
TASKP="$SCRIPT_DIR/taskp"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

TEST_PROJECT="test-smoke:$(date +%s)"
TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
pass() {
    echo -e "${GREEN}✓${NC} $1"
    TESTS_PASSED=$((TESTS_PASSED + 1))
}

fail() {
    echo -e "${RED}✗${NC} $1"
    TESTS_FAILED=$((TESTS_FAILED + 1))
}

info() {
    echo -e "${YELLOW}→${NC} $1"
}

cleanup() {
    if [[ -n "${TEST_PROJECT:-}" ]]; then
        info "Cleaning up test tasks..."
        task "project:$TEST_PROJECT" delete rc.confirmation=off 2>/dev/null || true
        task "project:${TEST_PROJECT}:_archive" delete rc.confirmation=off 2>/dev/null || true
    fi
}

# Trap cleanup on exit
trap cleanup EXIT

echo "========================================"
echo "tw-flow Smoke Test"
echo "Test Project: $TEST_PROJECT"
echo "========================================"
echo ""

# Test 1: Scripts exist and are executable
info "Test 1: Scripts exist and are executable"
if [[ -x "$TW_FLOW" ]] && [[ -x "$PONDER" ]]; then
    pass "Scripts are executable"
else
    fail "Scripts are not executable"
    exit 1
fi

# Test 2: Help command works
info "Test 2: Help command works"
"$TW_FLOW" help >/dev/null 2>&1 && pass "Help command works" || fail "Help command failed"

# Test 3: Create a simple initiative
info "Test 3: Create an initiative with tasks"
"$TW_FLOW" initiative "$TEST_PROJECT" \
    "First task|research|today" \
    "Second task|implementation|tomorrow" \
    "Third task|testing|2days" &>/dev/null && pass "Initiative created successfully" || fail "Initiative creation failed"

# Test 4: List initiatives
info "Test 4: List initiatives"
"$TW_FLOW" initiatives | grep -q "$TEST_PROJECT" && pass "Initiatives command shows test project" || fail "Initiatives command failed to show test project"

# Test 5: Show status of initiative
info "Test 5: Show initiative status"
"$TW_FLOW" status "$TEST_PROJECT" | grep -qE "Project:|Plan:|Initiative:" && pass "Status command works" || fail "Status command failed"

# Test 6: Show next tasks
info "Test 6: Show next tasks"
"$TW_FLOW" next "$TEST_PROJECT" &>/dev/null && pass "Next command works" || fail "Next command failed"

# Test 7: Get first task ID and execute
info "Test 7: Get first task ID and execute"
FIRST_TASK=$(task "project:$TEST_PROJECT" status:pending export | jq -r '.[0].uuid')
if [[ -n "$FIRST_TASK" ]] && [[ "$FIRST_TASK" != "null" ]]; then
    "$TW_FLOW" execute "$FIRST_TASK" &>/dev/null && pass "Execute command works (task $FIRST_TASK)" || fail "Execute command failed"
else
    fail "Could not find first task"
fi

# Test 8: Add note to task
info "Test 8: Add note to task"
if [[ -n "$FIRST_TASK" ]] && [[ "$FIRST_TASK" != "null" ]]; then
    "$TW_FLOW" note "$FIRST_TASK" research "Test research note" &>/dev/null && pass "Note command works" || fail "Note command failed"
fi

# Test 9: Show task context
info "Test 9: Show task context"
if [[ -n "$FIRST_TASK" ]] && [[ "$FIRST_TASK" != "null" ]]; then
    "$TW_FLOW" context "$FIRST_TASK" &>/dev/null && pass "Context command works" || fail "Context command failed"
fi

# Test 10: Complete task
info "Test 10: Complete task"
if [[ -n "$FIRST_TASK" ]] && [[ "$FIRST_TASK" != "null" ]]; then
    "$TW_FLOW" done "$FIRST_TASK" "Test completion" &>/dev/null && pass "Done command works" || fail "Done command failed"
fi

# Test 11: Test edge case - task with special characters
info "Test 11: Test edge case - task with special characters"
EDGE_TASK=$(task add "project:$TEST_PROJECT" "Task with 'quotes' and \"double quotes\"" rc.verbose:new-uuid 2>/dev/null | grep -oP 'Created task \K[0-9a-fA-F-]+' || echo "")
if [[ -n "$EDGE_TASK" ]]; then
    if task "$EDGE_TASK" &>/dev/null; then
        pass "Handles special characters in task description"
        task "$EDGE_TASK" delete rc.confirmation=off &>/dev/null || true
    else
        fail "Failed to handle special characters"
    fi
else
    fail "Failed to create task with special characters"
fi

# Test 12: Active tasks command
info "Test 12: Active tasks command"
"$TW_FLOW" active &>/dev/null && pass "Active command works" || fail "Active command failed"

# Test 13: Blocked tasks command
info "Test 13: Blocked tasks command"
"$TW_FLOW" blocked &>/dev/null && pass "Blocked command works" || fail "Blocked command failed"

# Test 14: Overdue tasks command
info "Test 14: Overdue tasks command"
"$TW_FLOW" overdue &>/dev/null && pass "Overdue command works" || fail "Overdue command failed"

# Test 15: Ponder ignores _archive projects
info "Test 15: Ponder ignores _archive projects"
ARCHIVE_TASK_DESC="This should be hidden"
task add "project:${TEST_PROJECT}:_archive" "$ARCHIVE_TASK_DESC" rc.verbose:new-uuid >/dev/null
PONDER_OUTPUT=$("$PONDER" "$TEST_PROJECT")
if ! echo "$PONDER_OUTPUT" | grep -q "$ARCHIVE_TASK_DESC"; then
    pass "Ponder correctly hides tasks from _archive project"
else
    fail "Ponder output contains task from _archive project"
fi

# Test 16: Initiative command supports modes
info "Test 16: Initiative command supports modes"
MODE_TASK_DESC="Mode verification task"
"$TW_FLOW" initiative "$TEST_PROJECT" "GUIDE|$MODE_TASK_DESC|testing|today" &>/dev/null
if task "project:$TEST_PROJECT" export | jq -r '.[].description' | grep -q "\[GUIDE\] $MODE_TASK_DESC"; then
    pass "Initiative command correctly prepends [MODE]"
else
    fail "Initiative command failed to prepend [MODE]"
fi

# Test 17: Ponder highlights modes
info "Test 17: Ponder highlights modes"
PONDER_OUTPUT=$("$PONDER" "$TEST_PROJECT")
if echo "$PONDER_OUTPUT" | grep -qE "\[GUIDE\]"; then
    pass "Ponder displays task with mode in dashboard"
else
    fail "Ponder failed to display task with mode"
fi

# Test 18: Handoff command works
info "Test 18: Handoff command works"
ACTIVE_TASK=$(task "project:$TEST_PROJECT" description:Second export | jq -r '.[0].uuid')
"$TW_FLOW" execute "$ACTIVE_TASK" &>/dev/null
"$TW_FLOW" outcome "$ACTIVE_TASK" "Ready for handoff" &>/dev/null

NEXT_TASK=$(task "project:$TEST_PROJECT" description:Third export | jq -r '.[0].uuid')
"$TW_FLOW" handoff "$NEXT_TASK" "Test handoff message" &>/dev/null
if task "$NEXT_TASK" export | jq -r '.[].annotations // [] | .[].description' | grep -q "HANDOFF: Test handoff message"; then
    pass "Handoff command correctly added annotation"
else
    fail "Handoff command failed to add annotation"
fi

# Test 19: Silo isolation works
info "Test 19: Silo isolation works"
ISOLATION_PROJECT="silo-iso-$(date +%s)"
PROJECT_ID="$ISOLATION_PROJECT" "$TASKP" add "Hidden Task" &>/dev/null
# Current test project silo should NOT see this task
if ! task list | grep -q "Hidden Task"; then
    pass "Silo isolation verified: tasks are project-private"
else
    fail "Silo isolation failed: foreign task visible in current silo"
fi
# Cleanup isolation project
rm -rf "/root/.task/silos/$ISOLATION_PROJECT"

# Summary

echo ""
echo "========================================"
echo "Test Summary"
echo "========================================"
echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed: ${RED}$TESTS_FAILED${NC}"
echo "========================================"

if [[ $TESTS_FAILED -eq 0 ]]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed!${NC}"
    exit 1
fi
