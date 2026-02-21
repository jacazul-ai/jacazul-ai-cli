#!/bin/bash
# Smoke test for tw-flow script (Gemini-enhanced + TASKDATA fixed + isolated test directory)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TW_FLOW="$SCRIPT_DIR/tw-flow"
PONDER="$SCRIPT_DIR/ponder"
TASKP="$SCRIPT_DIR/taskp"

# CRITICAL: Create isolated test directory inside smoketests/
TEST_RUN_ID="run_$(date +%s)"
TEST_RUN_DIR="$(cd "$SCRIPT_DIR/../../../.." && pwd)/build/smoketests/$TEST_RUN_ID"
export TASKDATA="$HOME/.task/build/smoketests/$TEST_RUN_ID"
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
    [ -n "$2" ] && echo -e "   ${YELLOW}DEBUG:${NC} $2"
}

info() {
    echo -e "${YELLOW}→${NC} $1"
}

# Cleanup on exit
cleanup_test() {
    echo ""
    info "Cleaning up test artifacts..."
    rm -rf "$TASKDATA" 2>/dev/null || true
}
trap cleanup_test EXIT

echo "═══════════════════════════════════════════════════"
echo "  TW-FLOW SMOKE TEST (Improved Transparency)"
echo "═══════════════════════════════════════════════════"
echo ""
info "Test Run: $TEST_RUN_ID"
info "TASKDATA: $TASKDATA"
echo ""

# Test 1: Help
info "Test 1: tw-flow help"
HELP_OUT=$($TW_FLOW help)
if echo "$HELP_OUT" | grep -qi "USAGE:"; then
    pass "Help command works"
else
    fail "Help output missing or unexpected" "$HELP_OUT"
fi

# Test 2: Create Initiative
info "Test 2: Create initiative"
# Using absolute path for taskp internal call check
INI_OUT=$($TW_FLOW initiative "$TEST_PROJECT" \
  "DESIGN|Design spec|research|today" \
  "EXECUTE|Implement feature|implementation|tomorrow" \
  "TEST|Write tests|testing|2days" 2>&1)

TASK_1_ID=$(echo "$INI_OUT" | grep -oP 'Created task \K\d+' | head -1)

if [ -n "$TASK_1_ID" ]; then
    pass "Initiative created (Task 1 ID: $TASK_1_ID)"
else
    fail "Failed to create initiative" "$INI_OUT"
fi

# Test 3: List initiatives
info "Test 3: List initiatives"
INIT_LIST=$($TW_FLOW initiatives 2>&1)
if echo "$INIT_LIST" | grep -q "smoke"; then
    pass "Initiative found in list"
else
    fail "Initiative 'smoke' missing from list" "$INIT_LIST"
fi

# Test 4: Status
info "Test 4: Status check"
STATUS_OUT=$($TW_FLOW status "$TEST_PROJECT" 2>&1)
if echo "$STATUS_OUT" | grep -qi "Initiative: smoke"; then
    pass "Status displays initiative name"
else
    fail "Status output missing initiative info" "$STATUS_OUT"
fi

# Test 5: Next task
info "Test 5: Next task check"
NEXT_OUT=$($TW_FLOW next "$TEST_PROJECT" 2>&1)
if echo "$NEXT_OUT" | grep -qi "Design spec"; then
    pass "Next task correctly identified"
else
    fail "Next task 'Design spec' not found" "$NEXT_OUT"
fi

# Test 6: Isolation verification
info "Test 6: Verify isolation"
TEST_COUNT=$($TASKP status:pending count 2>/dev/null || echo "0")
if [ "$TEST_COUNT" -ge 1 ]; then
    pass "Isolation verified (found $TEST_COUNT tasks in isolated TASKDATA)"
else
    fail "No tasks found in isolated TASKDATA"
fi

echo ""
echo "═══════════════════════════════════════════════════"
echo "TEST RESULTS: $TESTS_PASSED passed, $TESTS_FAILED failed"
echo "═══════════════════════════════════════════════════"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    exit 0
else
    exit 1
fi
