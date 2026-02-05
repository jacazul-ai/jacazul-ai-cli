#!/bin/bash
# Smoke test for tw-flow script (Gemini-enhanced + TASKDATA fixed)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TW_FLOW="$SCRIPT_DIR/tw-flow"
PONDER="$SCRIPT_DIR/ponder"
TASKP="$SCRIPT_DIR/taskp"

# CRITICAL: Override PROJECT_ID to use test database
TEST_SILO="test-smoke-$(date +%s)"
export PROJECT_ID="$TEST_SILO"
export TASKDATA="$HOME/.task/$TEST_SILO"
mkdir -p "$TASKDATA"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

TEST_PROJECT="smoke"
TESTS_PASSED=0
TESTS_FAILED=0

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
    info "Cleaning up test database..."
    rm -rf "$TASKDATA" 2>/dev/null || true
}

trap cleanup EXIT

echo "========================================"
echo "tw-flow Smoke Test"
echo "Test Silo: $TEST_SILO"
echo "Test Project: $TEST_PROJECT"
echo "TASKDATA: $TASKDATA"
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

# Test 3: Create initiative
info "Test 3: Create an initiative with tasks"
"$TW_FLOW" initiative "$TEST_PROJECT" \
    "First task|research|today" \
    "Second task|implementation|tomorrow" \
    "Third task|testing|2days" &>/dev/null && pass "Initiative created successfully" || fail "Initiative creation failed"

# Test 4: List initiatives
info "Test 4: List initiatives"
"$TW_FLOW" initiatives 2>&1 | grep -q "$TEST_PROJECT" && pass "Initiatives command shows test project" || fail "Initiatives command failed"

# Test 5: Show status
info "Test 5: Show initiative status"
"$TW_FLOW" status "$TEST_PROJECT" 2>&1 | grep -qE "Initiative:" && pass "Status command works" || fail "Status command failed"

# Test 6: Show next tasks
info "Test 6: Show next tasks"
"$TW_FLOW" next "$TEST_PROJECT" &>/dev/null && pass "Next command works" || fail "Next command failed"

# Test 7: Get first task UUID and execute
info "Test 7: Get first task UUID and execute"
FIRST_TASK=$(task "$TEST_PROJECT" status:pending export 2>/dev/null | jq -r '.[0].uuid // empty')
if [[ -n "$FIRST_TASK" ]] && [[ "$FIRST_TASK" != "null" ]]; then
    "$TW_FLOW" execute "$FIRST_TASK" &>/dev/null && pass "Execute command works (task ${FIRST_TASK:0:8})" || fail "Execute command failed"
else
    fail "Could not find first task (TASKDATA: $TASKDATA)"
fi

# Test 8: Add note
info "Test 8: Add note to task"
if [[ -n "$FIRST_TASK" ]] && [[ "$FIRST_TASK" != "null" ]]; then
    "$TW_FLOW" note "$FIRST_TASK" research "Test research note" &>/dev/null && pass "Note command works" || fail "Note command failed"
fi

# Test 9: Show context
info "Test 9: Show task context"
if [[ -n "$FIRST_TASK" ]] && [[ "$FIRST_TASK" != "null" ]]; then
    "$TW_FLOW" context "$FIRST_TASK" &>/dev/null && pass "Context command works" || fail "Context command failed"
fi

# Test 10: Add outcome
info "Test 10: Add outcome"
if [[ -n "$FIRST_TASK" ]] && [[ "$FIRST_TASK" != "null" ]]; then
    "$TW_FLOW" outcome "$FIRST_TASK" "Test completion outcome" &>/dev/null && pass "Outcome command works" || fail "Outcome command failed"
fi

# Test 11: Complete task
info "Test 11: Complete task with outcome"
if [[ -n "$FIRST_TASK" ]] && [[ "$FIRST_TASK" != "null" ]]; then
    "$TW_FLOW" done "$FIRST_TASK" &>/dev/null && pass "Done command works" || fail "Done command failed"
fi

# Test 12: Special characters
info "Test 12: Special characters in task description"
EDGE_TASK=$(task add "$TEST_PROJECT" "Task with 'quotes' and \"double quotes\"" 2>&1 | grep -oP 'Created task \K[0-9a-fA-F-]+' || task "$TEST_PROJECT" export 2>/dev/null | jq -r '.[-1].uuid // empty')
if [[ -n "$EDGE_TASK" ]] && [[ "$EDGE_TASK" != "null" ]]; then
    if task "$EDGE_TASK" &>/dev/null; then
        pass "Handles special characters"
        task "$EDGE_TASK" delete rc.confirmation=off &>/dev/null || true
    else
        fail "Failed special characters"
    fi
else
    fail "Failed to create task with special characters"
fi

# Test 13: Active tasks
info "Test 13: Active tasks command"
"$TW_FLOW" active &>/dev/null && pass "Active command works" || fail "Active command failed"

# Test 14: Blocked tasks
info "Test 14: Blocked tasks command"
"$TW_FLOW" blocked &>/dev/null && pass "Blocked command works" || fail "Blocked command failed"

# Test 15: Overdue tasks
info "Test 15: Overdue tasks command"
"$TW_FLOW" overdue &>/dev/null && pass "Overdue command works" || fail "Overdue command failed"

# Test 16: Archive projects
info "Test 16: Ponder ignores _archive projects"
ARCHIVE_TASK_DESC="This should be hidden"
task add "${TEST_PROJECT}:_archive" "$ARCHIVE_TASK_DESC" >/dev/null 2>&1
PONDER_OUTPUT=$("$PONDER" "$TEST_PROJECT" 2>/dev/null)
if ! echo "$PONDER_OUTPUT" | grep -q "$ARCHIVE_TASK_DESC"; then
    pass "Ponder hides _archive projects"
else
    fail "Ponder shows _archive projects"
fi

# Test 17: Mode support
info "Test 17: Initiative command supports modes"
MODE_TASK_DESC="Mode verification task"
"$TW_FLOW" initiative "$TEST_PROJECT" "GUIDE|$MODE_TASK_DESC|testing|today" &>/dev/null
if task "$TEST_PROJECT" export 2>/dev/null | jq -r '.[].description // empty' | grep -q "\[GUIDE\] $MODE_TASK_DESC"; then
    pass "Initiative prepends [MODE]"
else
    fail "Initiative mode failed"
fi

# Test 18: Ponder shows modes
info "Test 18: Ponder highlights modes"
PONDER_OUTPUT=$("$PONDER" "$TEST_PROJECT" 2>/dev/null)
if echo "$PONDER_OUTPUT" | grep -qE "\[GUIDE\]"; then
    pass "Ponder displays modes"
else
    fail "Ponder mode display failed"
fi

# Test 19: Handoff command
info "Test 19: Handoff command works"
SECOND_TASK=$(task "$TEST_PROJECT" export 2>/dev/null | jq -r '.[] | select(.description | contains("Second task")) | .uuid // empty')
if [[ -n "$SECOND_TASK" ]] && [[ "$SECOND_TASK" != "null" ]]; then
    "$TW_FLOW" execute "$SECOND_TASK" &>/dev/null
    "$TW_FLOW" outcome "$SECOND_TASK" "Ready for handoff" &>/dev/null
    
    THIRD_TASK=$(task "$TEST_PROJECT" export 2>/dev/null | jq -r '.[] | select(.description | contains("Third task")) | .uuid // empty')
    if [[ -n "$THIRD_TASK" ]] && [[ "$THIRD_TASK" != "null" ]]; then
        "$TW_FLOW" handoff "$THIRD_TASK" "Test handoff message" &>/dev/null
        if task "$THIRD_TASK" export 2>/dev/null | jq -r '.[].annotations // [] | .[].description // empty' | grep -q "HANDOFF: Test handoff message"; then
            pass "Handoff command works"
        else
            fail "Handoff annotation failed"
        fi
    else
        fail "Could not find third task for handoff"
    fi
else
    fail "Could not find second task for handoff"
fi


# Test 20: Context propagation from dependencies
info "Test 20: Context propagation displays parent context"
PARENT_TASK=$(task "$TEST_PROJECT" export 2>/dev/null | jq -r '.[0].uuid // empty')
if [[ -n "$PARENT_TASK" ]] && [[ "$PARENT_TASK" != "null" ]]; then
    # Add OUTCOME to parent
    "$TW_FLOW" outcome "$PARENT_TASK" "Parent task completed successfully" &>/dev/null
    
    # Create child task with dependency
    CHILD_UUID=$(task add "$TEST_PROJECT" "Child task with dependency" depends:"$PARENT_TASK" 2>&1 | grep -oP 'Created task \K[0-9a-fA-F-]+' || task "$TEST_PROJECT" export 2>/dev/null | jq -r '.[] | select(.description | contains("Child task")) | .uuid // empty')
    
    if [[ -n "$CHILD_UUID" ]] && [[ "$CHILD_UUID" != "null" ]]; then
        # Execute child - should show inherited context
        EXECUTE_OUTPUT=$("$TW_FLOW" execute "$CHILD_UUID" 2>&1)
        if echo "$EXECUTE_OUTPUT" | grep -q "INHERITED CONTEXT"; then
            pass "Context propagation works"
        else
            fail "Context propagation not displayed"
        fi
    else
        fail "Could not create child task"
    fi
else
    fail "Could not find parent task"
fi

echo ""
echo "========================================"

# Test 21: Discard command (soft delete)
info "Test 21: Discard command moves to trash"
DISCARD_UUID=$(task add "$TEST_PROJECT" "Unique discard test" 2>&1 | grep -oP 'Created task \K[0-9]+\b')
if [[ -n "$DISCARD_UUID" ]]; then
    # Get the actual UUID before discard
    ACTUAL_UUID=$(task "$DISCARD_UUID" export 2>/dev/null | jq -r '.[0].uuid[0:8]')
    
    # Temporarily unset PROJECT_ID so tw-flow uses TASKDATA env
    OLD_PROJECT_ID="$PROJECT_ID"
    unset PROJECT_ID
    "$TW_FLOW" discard "$ACTUAL_UUID" &>/dev/null
    export PROJECT_ID="$OLD_PROJECT_ID"
    
    # Check if in trash with DISCARDED tag
    TRASH_CHECK=$(task "$TEST_PROJECT:trash" export 2>/dev/null | jq -r ".[] | select(.tags // [] | map(. == \"DISCARDED\") | any) | .uuid")
    
    if [[ -n "$TRASH_CHECK" ]]; then
        pass "Discard moves to trash"
    else
        fail "Discard did not move to trash"
    fi
else
    fail "Could not create task to discard"
fi

# Test 22: Tree command shows dependencies
info "Test 22: Tree command displays dependency tree"
TREE_OUTPUT=$("$TW_FLOW" tree "$TEST_PROJECT" 2>/dev/null)
if echo "$TREE_OUTPUT" | grep -q "══ Initiative:"; then
    pass "Tree command works"
else
    fail "Tree command failed"
fi
echo "Test Summary"
echo "========================================"
echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed: ${RED}$TESTS_FAILED${NC}"
echo "========================================"

if [ $TESTS_FAILED -gt 0 ]; then
    echo "Some tests failed!"
    exit 1
else
    echo "All tests passed!"
    exit 0
fi
