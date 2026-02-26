#!/bin/bash
# Comprehensive Smoke test for tw-flow script (v1.4.0)
# Covers all core commands, interaction modes, and security measures.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TW_FLOW="$SCRIPT_DIR/tw-flow"
PONDER="$SCRIPT_DIR/ponder"
TASKP="$SCRIPT_DIR/taskp"

# CRITICAL: Create isolated test directory for this run
# This ensures we don't mess with production data
TEST_RUN_ID="run_$(date +%s)"
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

cleanup_test() {
    echo ""
    info "Cleaning up test artifacts..."
    rm -rf "$TASKDATA" 2>/dev/null || true
}
trap cleanup_test EXIT

echo "═══════════════════════════════════════════════════"
echo "  TW-FLOW COMPREHENSIVE SMOKE TEST (v1.4.0)"
echo "═══════════════════════════════════════════════════"
echo ""
info "Test Run: $TEST_RUN_ID"
info "TASKDATA: $TASKDATA"
echo ""

# --- 1. CORE AVAILABILITY ---

# Test 1: Scripts exist and are executable
info "Test 1: Executability"
if [[ -x "$TW_FLOW" ]] && [[ -x "$PONDER" ]] && [[ -x "$TASKP" ]]; then
    pass "Core scripts are executable"
else
    fail "Scripts missing or not executable"
    exit 1
fi

# Test 2: Help command
info "Test 2: Help command"
if $TW_FLOW help | grep -qi "USAGE:"; then
    pass "Help command returns valid usage"
else
    fail "Help output missing or unexpected"
fi

# --- 2. INITIATIVE WORKFLOW ---

# Test 3: Create Initiative (Multi-task)
info "Test 3: Create initiative"
INI_OUT=$($TW_FLOW initiative "$TEST_PROJECT" \
  "DESIGN|Spec phase|research|today" \
  "EXECUTE|Build phase|implementation|tomorrow" 2>/dev/null)
TASK_1_ID=$(echo "$INI_OUT" | grep -oP 'Created task \K\d+' | head -1)
TASK_2_ID=$(echo "$INI_OUT" | grep -oP 'Created task \K\d+' | tail -1)

if [ -n "$TASK_1_ID" ] && [ -n "$TASK_2_ID" ]; then
    pass "Initiative created (Task 1: $TASK_1_ID, Task 2: $TASK_2_ID)"
else
    fail "Initiative creation failed" "$INI_OUT"
fi

# Test 4: List Initiatives
info "Test 4: List initiatives"
if $TW_FLOW initiatives | grep -q "$TEST_PROJECT"; then
    pass "Initiative found in list"
else
    fail "Initiative list missing '$TEST_PROJECT'"
fi

# Test 5: Status Split-View
info "Test 5: Status split-view"
STATUS_OUT=$($TW_FLOW status "$TEST_PROJECT" 2>&1)
if echo "$STATUS_OUT" | grep -q "PENDING:" && echo "$STATUS_OUT" | grep -q "Initiative: $TEST_PROJECT"; then
    pass "Status displays split-view and project name"
else
    fail "Status output malformed" "$STATUS_OUT"
fi

# Test 6: Next Task Identification
info "Test 6: Next task"
if $TW_FLOW next "$TEST_PROJECT" | grep -qi "Spec phase"; then
    pass "Next task correctly identified"
else
    fail "Next task identification failed"
fi

# --- 3. TASK EXECUTION & CONTEXT ---

# Test 7: Execute Logic (ACTIVE state)
info "Test 7: Execute task"
if $TW_FLOW execute "$TASK_1_ID" > /dev/null 2>&1; then
    if $TASKP +ACTIVE export | jq -r '.[0].id' | grep -q "$TASK_1_ID"; then
        pass "Task started and marked ACTIVE"
    else
        fail "Task not showing as active in database"
    fi
else
    fail "Execute command failed"
fi

# Test 8: Structured Notes (RESEARCH/DECISION)
info "Test 8: Structured notes"
$TW_FLOW note "$TASK_1_ID" decision "Using architecture X" > /dev/null 2>&1
$TW_FLOW note "$TASK_1_ID" research "Found library Y" > /dev/null 2>&1
ANNOTATIONS=$($TASKP "$TASK_1_ID" export | jq -r '.[0].annotations[].description')
if echo "$ANNOTATIONS" | grep -q "DECISION: Using architecture X" && echo "$ANNOTATIONS" | grep -q "RESEARCH: Found library Y"; then
    pass "Structured notes added with correct prefixes"
else
    fail "Notes missing or prefixing failed" "$ANNOTATIONS"
fi

# Test 9: Context Retrieval
info "Test 9: Context retrieval"
CONTEXT_OUT=$($TW_FLOW context "$TASK_1_ID")
if echo "$CONTEXT_OUT" | grep -q "DECISION: Using architecture X"; then
    pass "Context command displays annotations"
else
    fail "Context command failed to show annotations" "$CONTEXT_OUT"
fi

# --- 4. EDGE CASES & FILTERS ---

# Test 10: Special Character Handling
info "Test 10: Special characters"
EDGE_OUT=$($TASKP add project:"$TEST_PROJECT" "Task with 'quotes' and \"double quotes\"" 2>&1)
EDGE_UUID=$(echo "$EDGE_OUT" | grep -oP 'Created task \K\d+')
if [ -n "$EDGE_UUID" ]; then
    pass "Handles single and double quotes in description"
else
    fail "Special character creation failed" "$EDGE_OUT"
fi

# Test 11: Quick Filters (active/blocked)
info "Test 11: Quick filters"
if $TW_FLOW active | grep -q "Spec phase"; then
    pass "Active filter works"
else
    fail "Active filter failed"
fi

# Test 12: Archive Isolation
info "Test 12: Archive isolation"
ARCHIVE_DESC="Hidden in shadow"
$TASKP add project:"$TEST_PROJECT:_archive" "$ARCHIVE_DESC" > /dev/null 2>&1
PONDER_OUT=$($PONDER "$TEST_PROJECT" 2>&1)
if ! echo "$PONDER_OUT" | grep -q "$ARCHIVE_DESC"; then
    pass "Ponder correctly ignores _archive projects"
else
    fail "Archive task leaked into ponder output"
fi

# --- 5. INTERACTION MODES ---

# Test 13: Interaction Mode Support
info "Test 13: Interaction modes"
$TW_FLOW initiative "$TEST_PROJECT" "GUIDE|Verification task|testing|today" > /dev/null 2>&1
if $TASKP project:"$TEST_PROJECT" export | jq -r '.[].description' | grep -q "\[GUIDE\] Verification task"; then
    pass "Initiative command correctly prepends [MODE]"
else
    fail "Mode prefixing failed"
fi

# Test 14: Dashboard Mode Highlighting
info "Test 14: Dashboard mode detection"
if $PONDER "$TEST_PROJECT" | grep -q "GUIDE"; then
    pass "Ponder displays interaction modes"
else
    fail "Ponder failed to show mode"
fi

# --- 6. ADVANCED WORKFLOW ---

# Test 15: Handoff Protocol
info "Test 15: Handoff protocol"
$TW_FLOW outcome "$TASK_1_ID" "Phase 1 complete" > /dev/null 2>&1
$TW_FLOW done "$TASK_1_ID" > /dev/null 2>&1
$TW_FLOW handoff "$TASK_2_ID" "Start implementation" > /dev/null 2>&1
if $TASKP "$TASK_2_ID" export | jq -r '.[0].annotations[].description' | grep -q "HANDOFF: Start implementation"; then
    if $TASKP +ACTIVE export | jq -r '.[0].id' | grep -q "$TASK_2_ID"; then
        pass "Handoff added note and auto-executed next task"
    else
        fail "Handoff failed to start next task"
    fi
else
    fail "Handoff note missing"
fi

# --- 7. SECURITY & ENFORCEMENT ---

# Test 16: Project Isolation
info "Test 16: Project isolation"
OTHER_PROJECT="project-iso-$(date +%s)"
PROJECT_ID="$OTHER_PROJECT" $TASKP add "Project Private Task" > /dev/null 2>&1
if ! $TASKP project:"$TEST_PROJECT" list | grep -q "Project Private Task"; then
    pass "Project isolation verified (TASKDATA segregation)"
else
    fail "Data leak: foreign task visible in current project"
fi

# Test 17: Vaccination - Block direct 'done'
info "Test 17: Vaccination - Block direct 'done'"
if $TASKP "$TASK_2_ID" done 2>&1 | grep -q "ERROR: Direct 'done' command via taskp is restricted"; then
    pass "Direct taskp done blocked correctly"
else
    fail "Direct taskp done was NOT blocked"
fi

# Test 18: Vaccination - Block manual +DISCARDED
info "Test 18: Vaccination - Block manual +DISCARDED"
if $TASKP "$TASK_2_ID" modify +DISCARDED 2>&1 | grep -q "ERROR: Manual '+DISCARDED' tag via taskp is restricted"; then
    pass "Manual +DISCARDED tag blocked correctly"
else
    fail "Manual +DISCARDED tag was NOT blocked"
fi

# Test 19: Outcome Enforcement
info "Test 19: Outcome enforcement"
if $TW_FLOW done "$TASK_2_ID" 2>&1 | grep -q "cannot be completed without an OUTCOME"; then
    pass "Done blocked without outcome correctly"
else
    fail "Done allowed without outcome"
fi

# Test 20: Happy Path (Done with Outcome)
info "Test 20: Happy path (Outcome bypass)"
$TW_FLOW outcome "$TASK_2_ID" "Verified" > /dev/null 2>&1
if $TW_FLOW done "$TASK_2_ID" > /dev/null 2>&1; then
    pass "tw-flow done works correctly with outcome"
else
    fail "tw-flow done failed even with outcome present"
fi

# Test 21: Discard Audit
info "Test 21: Discard audit trail"
$TASKP add project:"$TEST_PROJECT" "Discard me" > /dev/null 2>&1
DIS_UUID=$($TASKP project:"$TEST_PROJECT" export | jq -r '.[] | select(.description=="Discard me") | .uuid' | head -1)
if $TW_FLOW discard "$DIS_UUID" > /dev/null 2>&1; then
    if $TASKP "$DIS_UUID" export | jq -r '.[0].annotations[].description' | grep -q "OUTCOME: Task discarded and moved to archive"; then
        pass "Discard created automatic audit trail"
    else
        fail "Discard outcome missing"
    fi
    else
        fail "Discard command failed"
fi

# Test 22: Task Binary Obfuscation
info "Test 22: Task binary obfuscation"
# We simulate the project scripts/ being in PATH
PROJECT_SCRIPTS="$(cd "$SCRIPT_DIR/../../../../scripts" && pwd)"
info "DEBUG: Project scripts dir: $PROJECT_SCRIPTS"
ls -d "$PROJECT_SCRIPTS" > /dev/null 2>&1 || fail "Project scripts directory not found"
export PATH="$PROJECT_SCRIPTS:$PATH"
hash -r # Clear bash command cache
DET_TASK=$(which task 2>/dev/null)
info "DEBUG: Found task at: $DET_TASK"
if task 2>&1 | grep -q "ERROR: Direct usage of 'task' is restricted"; then
    pass "Raw task binary obfuscated and blocked correctly"
    else
        fail "Raw task binary was NOT blocked"
fi

# Test 23: Anchor System (Focus)
info "Test 23: Anchor system (Focus)"
# 1. Anchor initiative
$TW_FLOW focus ini "$TEST_PROJECT" > /dev/null 2>&1
if $TW_FLOW status 2>&1 | grep -q "📌 ANCHORED SESSION"; then
    # 2. Anchor task
    $TW_FLOW focus task "$TASK_2_ID" > /dev/null 2>&1
    if $TW_FLOW status 2>&1 | grep -q "🎯 .* FOCUSED"; then
        # 3. Clear focus
        $TW_FLOW focus clear > /dev/null 2>&1
        if ! $TW_FLOW status 2>&1 | grep -q "📌 ANCHORED SESSION"; then
            pass "Anchor system (ini/task/clear) verified"
        else
            fail "Focus clear failed"
        fi
    else
        fail "Task anchoring failed"
    fi
else
    fail "Initiative anchoring failed"
fi

# Test 24: Ponder Interest Filtering
info "Test 24: Ponder interest filtering"
# 1. Add interest
OTHER_PROJECT="interest-$(date +%s)"
$TASKP add project:"$OTHER_PROJECT" "Interesting task" > /dev/null 2>&1
$TW_FLOW focus interest add "$TEST_PROJECT" > /dev/null 2>&1
# 2. Ponder should show TEST_PROJECT but NOT OTHER_PROJECT
PONDER_FOCUSED=$($PONDER "$TEST_PROJECT" 2>&1)
if echo "$PONDER_FOCUSED" | grep -q "$TEST_PROJECT" && ! echo "$PONDER_FOCUSED" | grep -q "$OTHER_PROJECT"; then
    # 3. Ponder --all should show both
    PONDER_ALL=$($PONDER --all "$TEST_PROJECT" 2>&1)
    if echo "$PONDER_ALL" | grep -q "$TEST_PROJECT" && echo "$PONDER_ALL" | grep -q "$OTHER_PROJECT"; then
        pass "Ponder interest filtering and --all bypass verified"
    else
        fail "Ponder --all failed to show all initiatives"
    fi
else
    fail "Ponder failed to filter initiatives correctly"
fi

# --- SUMMARY ---

echo ""
echo "═══════════════════════════════════════════════════"
echo "Test Summary"
echo "═══════════════════════════════════════════════════"
echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed: ${RED}$TESTS_FAILED${NC}"
echo "═══════════════════════════════════════════════════"

if [[ $TESTS_FAILED -eq 0 ]]; then
    echo -e "${GREEN}All 24 tests passed! Workflow is stable. v1.4.0 verified.${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed! Check DEBUG info above.${NC}"
    exit 1
fi
