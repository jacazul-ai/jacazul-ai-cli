#!/usr/bin/env python
import os
import subprocess
import orjson
import time
import re
import shutil
import atexit
import sys

# 🧪 E2E UUID Workflow Smoke Test
# Purpose: Verify full workflow using ONLY 8-char UUIDs.

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TW_FLOW = os.path.join(SCRIPT_DIR, "tw-flow")
TASKP = os.path.join(SCRIPT_DIR, "taskp")
PONDER = os.path.join(SCRIPT_DIR, "ponder")

# Isolated Test Directory
TEST_RUN_ID = f"e2e_uuid_{int(time.time())}"
TASKDATA = os.path.expanduser(f"~/.task/build/smoketests/{TEST_RUN_ID}")
os.makedirs(TASKDATA, exist_ok=True)

def cleanup():
    if os.path.exists(TASKDATA):
        shutil.rmtree(TASKDATA)

atexit.register(cleanup)

ENV = os.environ.copy()
ENV["TASKDATA"] = TASKDATA
ENV["PROJECT_ID"] = "e2e_test"
ENV["PYTHONPATH"] = f"{SCRIPT_DIR}:{ENV.get('PYTHONPATH', '')}"

def pass_test(name): print(f"\033[0;32m✓\033[0m {name}")
def fail_test(name, debug=""):
    print(f"\033[0;31m✗\033[0m {name}")
    if debug: print(f"   \033[1;33mDEBUG:\033[0m {debug}")
    sys.exit(1)

def run_cmd(cmd):
    res = subprocess.run(cmd, shell=True, env=ENV, capture_output=True, text=True, check=False)
    return res.stdout.strip(), res.stderr.strip(), res.returncode

print("═══════════════════════════════════════════════════")
print("  E2E UUID-ONLY WORKFLOW TEST")
print("═══════════════════════════════════════════════════")

# 1. Create Initiative
out, err, _ = run_cmd(f"{TW_FLOW} ini e2e 'Step 1|research|today' 'Step 2|implementation|tomorrow'")
uuids = re.findall(r'Created task ([0-9a-f]{8}):', out)
if len(uuids) < 2: fail_test("Failed to get UUIDs from ini creation", out + err)
u1, u2 = uuids[0], uuids[1]
pass_test(f"Initiative created with UUIDs: {u1}, {u2}")

# 2. Execute via UUID
out, _, code = run_cmd(f"{TW_FLOW} execute {u1}")
if code == 0: pass_test(f"Task {u1} executed successfully via UUID")
else: fail_test(f"Failed to execute task {u1}", out)

# 3. Add Note via UUID
out, _, code = run_cmd(f"{TW_FLOW} note {u1} decision 'Standardized'")
if code == 0: pass_test(f"Note added to {u1} successfully via UUID")
else: fail_test(f"Failed to add note to {u1}", out)

# 4. Add Outcome and Done via UUID
run_cmd(f"{TW_FLOW} outcome {u1} 'Finished step 1'")
out, _, code = run_cmd(f"{TW_FLOW} done {u1}")
if code == 0: pass_test(f"Task {u1} completed successfully via UUID")
else: fail_test(f"Failed to complete task {u1}", out)

# 5. Verify unblocking via UUID
out, _, _ = run_cmd(f"{TW_FLOW} next e2e")
if u2 in out: pass_test(f"Task {u2} correctly unblocked and identified via UUID")
else: fail_test(f"Task {u2} not found in next tasks", out)

# 6. Ponder check
out, _, _ = run_cmd(f"{PONDER} e2e")
if u2 in out: pass_test(f"Ponder correctly displays UUID {u2}")
else: fail_test(f"Ponder failed to show UUID {u2}", out)

print("\n═══════════════════════════════════════════════════")
print("\033[0;32mE2E UUID Workflow verified! Numeric IDs are history.\033[0m")
print("═══════════════════════════════════════════════════")
