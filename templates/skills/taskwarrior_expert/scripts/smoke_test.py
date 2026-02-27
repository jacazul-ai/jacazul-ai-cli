#!/usr/bin/env python
import os
import subprocess
import orjson
import time
import re
import shutil
import atexit
import sys

# 🐊 Jaka Python Smoke Test (v1.4.0) - PARITY VERSION (24 TESTS)
# Comprehensive test suite for the taskwarrior-expert tools.

# Setup Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TW_FLOW = os.path.join(SCRIPT_DIR, "tw-flow")
PONDER = os.path.join(SCRIPT_DIR, "ponder")
TASKP = os.path.join(SCRIPT_DIR, "taskp")
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../../../.."))

# Isolated Test Directory
TEST_RUN_ID = f"py_parity_{int(time.time())}"
TASKDATA = os.path.expanduser(f"~/.task/build/smoketests/{TEST_RUN_ID}")
os.makedirs(TASKDATA, exist_ok=True)

# Results tracking
results = {"passed": 0, "failed": 0}

def cleanup():
    if os.path.exists(TASKDATA):
        shutil.rmtree(TASKDATA)

atexit.register(cleanup)

# Environment Overrides
ENV = os.environ.copy()
ENV["TASKDATA"] = TASKDATA
ENV["PROJECT_ID"] = "smoke"
ENV["PYTHONPATH"] = f"{SCRIPT_DIR}:{ENV.get('PYTHONPATH', '')}"

def pass_test(name):
    print(f"\033[0;32m✓\033[0m {name}")
    results["passed"] += 1

def fail_test(name, debug=""):
    print(f"\033[0;31m✗\033[0m {name}")
    if debug:
        print(f"   \033[1;33mDEBUG:\033[0m {debug}")
    results["failed"] += 1

def info(msg):
    print(f"\033[1;33m→\033[0m {msg}")

def run_cmd(cmd, check=False):
    res = subprocess.run(cmd, shell=True, env=ENV, capture_output=True, text=True, check=False)
    return res.stdout.strip(), res.stderr.strip(), res.returncode

print("═══════════════════════════════════════════════════")
print("  TW-FLOW PARITY SMOKE TEST (v1.4.0)")
print("═══════════════════════════════════════════════════")
info(f"Test Run: {TEST_RUN_ID}")
info(f"TASKDATA: {TASKDATA}\n")

# --- 1. CORE AVAILABILITY ---

info("Phase 1: Core Availability")
scripts = [TW_FLOW, PONDER, TASKP]
if all(os.access(f, os.X_OK) for f in scripts):
    pass_test("Test 1: Executability")
else:
    fail_test("Test 1: Executability", "Scripts missing or not executable")

out, _, _ = run_cmd(f"{TW_FLOW} help")
if "tw-flow USAGE:" in out:
    pass_test("Test 2: Help command")
else:
    fail_test("Test 2: Help command", out)

# --- 2. INITIATIVE WORKFLOW ---

info("Phase 2: Initiative Workflow")
out, err, _ = run_cmd(f"{TW_FLOW} initiative parity 'DESIGN|Spec phase|research|today' 'EXECUTE|Build phase|implementation|tomorrow'")
# New Regex for 8-char UUIDs: Created task [0-9a-f]{8}:
ids = re.findall(r'Created task ([0-9a-f]{8}):', out)
if len(ids) >= 2:
    t1, t2 = ids[0], ids[1]
    pass_test(f"Test 3: Create initiative (Tasks {t1}, {t2})")
else:
    fail_test("Test 3: Create initiative", out or err)

out, _, _ = run_cmd(f"{TW_FLOW} inis")
if "parity" in out:
    pass_test("Test 4: List initiatives")
else:
    fail_test("Test 4: List initiatives", out)

out, _, _ = run_cmd(f"{TW_FLOW} status parity")
if "PENDING:" in out and "Initiative: parity" in out:
    pass_test("Test 5: Status split-view")
else:
    fail_test("Test 5: Status split-view", out)

out, _, _ = run_cmd(f"{TW_FLOW} next parity")
if "Spec phase" in out:
    pass_test("Test 6: Next task identification")
else:
    fail_test("Test 6: Next task identification", out)

# --- 3. TASK EXECUTION & CONTEXT ---

info("Phase 3: Task Execution & Context")
run_cmd(f"{TW_FLOW} execute {t1}")
out, _, _ = run_cmd(f"{TASKP} +ACTIVE export")
if any(t.get('uuid', '').startswith(t1) for t in orjson.loads(out or "[]")):
    pass_test("Test 7: Execute logic (ACTIVE state)")
else:
    fail_test("Test 7: Execute logic", out)

run_cmd(f"{TW_FLOW} note {t1} decision 'Arch X'")
run_cmd(f"{TW_FLOW} note {t1} research 'Lib Y'")
out, _, _ = run_cmd(f"{TASKP} {t1} export")
annots = [a["description"] for a in orjson.loads(out or "[]")[0].get("annotations", [])]
if "DECISION: Arch X" in annots and "RESEARCH: Lib Y" in annots:
    pass_test("Test 8: Structured notes")
else:
    fail_test("Test 8: Structured notes", str(annots))

out, _, _ = run_cmd(f"{TW_FLOW} context {t1}")
if "DECISION: Arch X" in out:
    pass_test("Test 9: Context retrieval")
else:
    fail_test("Test 9: Context retrieval", f"OUT: {out}")

# --- 4. EDGE CASES & FILTERS ---

info("Phase 4: Edge Cases & Filters")
out, _, _ = run_cmd(f"{TASKP} add project:parity \"Task with 'quotes'\"")
if "Created task" in out:
    pass_test("Test 10: Special character handling")
else:
    fail_test("Test 10: Special character handling", out)

out, _, _ = run_cmd(f"{TW_FLOW} active")
if "Spec phase" in out:
    pass_test("Test 11: Quick filters (active)")
else:
    fail_test("Test 11: Quick filters", out)

run_cmd(f"{TASKP} add project:parity:_archive \"Hidden task\"")
out, _, _ = run_cmd(f"{PONDER} parity")
if "Hidden task" not in out:
    pass_test("Test 12: Archive isolation")
else:
    fail_test("Test 12: Archive isolation", out)

# --- 5. INTERACTION MODES ---

info("Phase 5: Interaction Modes")
run_cmd(f"{TW_FLOW} initiative parity \"GUIDE|Guide task|testing|today\"")
out, _, _ = run_cmd(f"{TASKP} project:parity export")
if any("[GUIDE] Guide task" in t["description"] for t in orjson.loads(out or "[]")):
    pass_test("Test 13: Interaction mode support")
else:
    fail_test("Test 13: Interaction mode support")

out, _, _ = run_cmd(f"{PONDER} parity")
if "GUIDE" in out:
    pass_test("Test 14: Dashboard mode highlighting")
else:
    fail_test("Test 14: Dashboard mode highlighting", out)

# --- 6. ADVANCED WORKFLOW ---

info("Phase 6: Advanced Workflow")
run_cmd(f"{TW_FLOW} outcome {t1} 'Done'")
run_cmd(f"{TW_FLOW} done {t1}")
run_cmd(f"{TW_FLOW} handoff {t2} 'Go'")
out, _, _ = run_cmd(f"{TASKP} {t2} export")
task2 = orjson.loads(out or "[]")[0]
if any("HANDOFF: Go" in a["description"] for a in task2.get("annotations", [])) and task2.get("start"):
    pass_test("Test 15: Handoff protocol")
else:
    fail_test("Test 15: Handoff protocol")

# --- 7. SECURITY & ENFORCEMENT ---

info("Phase 7: Security & Enforcement")
ENV["PROJECT_ID"] = "foreign"
run_cmd(f"{TASKP} add \"Private\"")
ENV["PROJECT_ID"] = "smoke"
out, _, _ = run_cmd(f"{TASKP} project:parity list")
if "Private" not in out:
    pass_test("Test 16: Project isolation")
else:
    fail_test("Test 16: Project isolation", out)

out, err, _ = run_cmd(f"{TASKP} {t2} done")
if "ERROR: Direct 'done' command via taskp is restricted" in (out + err):
    pass_test("Test 17: Vaccination - Block direct 'done'")
else:
    fail_test("Test 17: Vaccination - Block direct 'done'", out + err)

out, err, _ = run_cmd(f"{TASKP} {t2} modify +DISCARDED")
if "ERROR: Manual '+DISCARDED' tag via taskp is restricted" in (out + err):
    pass_test("Test 18: Vaccination - Block manual +DISCARDED")
else:
    fail_test("Test 18: Vaccination - Block manual +DISCARDED", out + err)

out, err, _ = run_cmd(f"{TW_FLOW} done {t2}")
if "cannot be completed without an OUTCOME" in (out + err):
    pass_test("Test 19: Outcome enforcement")
else:
    fail_test("Test 19: Outcome enforcement", out + err)

run_cmd(f"{TW_FLOW} outcome {t2} 'Verified'")
if run_cmd(f"{TW_FLOW} done {t2}")[2] == 0:
    pass_test("Test 20: Happy path (Done with outcome)")
else:
    fail_test("Test 20: Happy path")

run_cmd(f"{TASKP} add project:parity 'Discard me'")
out, _, _ = run_cmd(f"{TASKP} project:parity export")
dis_uuid = [t["uuid"] for t in orjson.loads(out or "[]") if t["description"] == "Discard me"][0]
run_cmd(f"{TW_FLOW} discard {dis_uuid}")
out, _, _ = run_cmd(f"{TASKP} {dis_uuid} export")
if any("OUTCOME: Task discarded" in a["description"] for a in orjson.loads(out or "[]")[0].get("annotations", [])):
    pass_test("Test 21: Discard audit trail")
else:
    fail_test("Test 21: Discard audit trail")

ENV["PATH"] = f"{os.path.join(PROJECT_ROOT, 'scripts')}:{ENV['PATH']}"
out, err, _ = run_cmd("task")
if "ERROR: Direct usage of 'task' is restricted" in (out + err):
    pass_test("Test 22: Task binary obfuscation")
else:
    fail_test("Test 22: Task binary obfuscation", out + err)

# --- 8. ANCHOR SYSTEM & INTERESTS ---

info("Phase 8: Anchor System & Interests")
run_cmd(f"{TW_FLOW} focus ini parity")
run_cmd(f"{TASKP} add project:heap 'Heap task'")
run_cmd(f"{TW_FLOW} focus ini heap")
focus_file = os.path.join(TASKDATA, "focus.json")
with open(focus_file, "rb") as f:
    state = orjson.loads(f.read())
    if len(state.get("task_track", [])) >= 2:
        pass_test("Test 23: Anchor system (Heap accumulation)")
    else:
        fail_test("Test 23: Anchor system", str(state))

run_cmd(f"{TASKP} add project:uninteresting 'Boring'")
run_cmd(f"{TW_FLOW} focus interest add parity")
out, _, _ = run_cmd(f"{PONDER} smoke")
if "parity" in out and "uninteresting" not in out:
    out_all, _, _ = run_cmd(f"{PONDER} --all smoke")
    if "uninteresting" in out_all:
        pass_test("Test 24: Ponder interest filtering")
    else:
        fail_test("Test 24: Ponder interest filtering (--all bypass)", out_all)
else:
    fail_test("Test 24: Ponder interest filtering", out)

print("\n═══════════════════════════════════════════════════")
print("Test Summary")
print("═══════════════════════════════════════════════════")
print(f"Passed: \033[0;32m{results['passed']}\033[0m")
print(f"Failed: \033[0;31m{results['failed']}\033[0m")
print("═══════════════════════════════════════════════════")
if results["failed"] == 0:
    print("\n\033[0;32mAll 24 parity tests passed! Python toolset is 100% logic-compliant.\033[0m")
    sys.exit(0)
else:
    sys.exit(1)
