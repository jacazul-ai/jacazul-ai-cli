#!/bin/bash
# Smoke test for tw-flow script
# Tests basic functionality and edge cases

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TW_FLOW="$SCRIPT_DIR/tw-flow"

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
        task "project:$TEST_PROJECT" delete 2>/dev/null || true
    fi
}

# Trap cleanup on exit
trap cleanup EXIT

echo "========================================"
echo "tw-flow Smoke Test"
echo "Test Project: $TEST_PROJECT"
echo "========================================"
echo ""

# Test 1: Script exists and is executable
info "Test 1: Script exists and is executable"
if [[ -x "$TW_FLOW" ]]; then
    pass "Script is executable"
else
    fail "Script is not executable"
    exit 1
fi

# Test 2: Help command works
info "Test 2: Help command works"
"$TW_FLOW" help >/dev/null 2>&1 && pass "Help command works" || fail "Help command failed"

# Test 3: Create a simple plan
info "Test 3: Create a plan with tasks"
"$TW_FLOW" plan "$TEST_PROJECT" \
    "First task|research|today" \
    "Second task|implementation|tomorrow" \
    "Third task|testing|2days" &>/dev/null && pass "Plan created successfully" || fail "Plan creation failed"

# Test 4: List plans
info "Test 4: List plans"
"$TW_FLOW" plans | grep -q "$TEST_PROJECT" && pass "Plans command shows test project" || fail "Plans command failed to show test project"

# Test 5: Show status of plan
info "Test 5: Show plan status"
"$TW_FLOW" status "$TEST_PROJECT" | grep -q "Plano:" && pass "Status command works" || fail "Status command failed"

# Test 6: Show next tasks
info "Test 6: Show next tasks"
"$TW_FLOW" next "$TEST_PROJECT" &>/dev/null && pass "Next command works" || fail "Next command failed"

# Test 7: Get first task ID
info "Test 7: Get first task ID and execute"
FIRST_TASK=$(task "project:$TEST_PROJECT" status:pending export | jq -r '.[0].id')
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

# Test 11: Test with spaces in project name (edge case)
info "Test 11: Test edge case - task with special characters"
EDGE_TASK=$(task add "project:$TEST_PROJECT" "Task with 'quotes' and \"double quotes\"" 2>/dev/null | grep -oP 'Created task \K\d+' || echo "")
if [[ -n "$EDGE_TASK" ]]; then
    if task "$EDGE_TASK" &>/dev/null; then
        pass "Handles special characters in task description"
        task "$EDGE_TASK" delete &>/dev/null || true
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
