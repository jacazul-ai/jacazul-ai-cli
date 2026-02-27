#!/usr/bin/env python
import os
import subprocess
import time
import shutil
import atexit
import sys
import re

# 🧪 tw-flow UUID Output Smoke Test
# Purpose: Verify that tw-flow emits 8-char UUIDs and hides numeric IDs.

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TW_FLOW = os.path.join(SCRIPT_DIR, "tw-flow")

# Isolated Test Directory
TEST_RUN_ID = f"tw_uuid_{int(time.time())}"
TASKDATA = os.path.expanduser(f"~/.task/build/smoketests/{TEST_RUN_ID}")
os.makedirs(TASKDATA, exist_ok=True)

def cleanup():
    if os.path.exists(TASKDATA):
        shutil.rmtree(TASKDATA)

atexit.register(cleanup)

ENV = os.environ.copy()
ENV["TASKDATA"] = TASKDATA
ENV["PROJECT_ID"] = "tw_uuid_test"
ENV["PYTHONPATH"] = f"{SCRIPT_DIR}:{ENV.get('PYTHONPATH', '')}"

def pass_test(name):
    print(f"\033[0;32m✓\033[0m {name}")

def fail_test(name, debug=""):
    print(f"\033[0;31m✗\033[0m {name}")
    if debug:
        print(f"   \033[1;33mDEBUG:\033[0m {debug}")

def run_cmd(cmd):
    res = subprocess.run(cmd, shell=True, env=ENV, capture_output=True, text=True, check=False)
    return res.stdout.strip(), res.stderr.strip(), res.returncode

print("═══════════════════════════════════════════════════")
print("  TW-FLOW UUID OUTPUT REPRODUCTION TEST")
print("═══════════════════════════════════════════════════")

# 1. Create an initiative
print("TEST: Creating initiative...")
out, _, _ = run_cmd(f"{TW_FLOW} initiative smoke 'Task 1|research|today'")

print(f"→ Output: {out}")

# 2. VERIFICATION: Check if 'Created task [uuid]' is present instead of number
if re.search(r'Created task [0-9a-f]{8}:', out):
    pass_test("Standardized Output: tw-flow is now emitting 8-char UUIDs.")
    if "Created task 1" not in out:
        pass_test("Verification: Numeric IDs are hidden.")
    else:
        fail_test("Failure: Numeric IDs still present in output.")
        sys.exit(1)
else:
    fail_test("Standardization failed: Could not find 8-char UUID in output.", out)
    sys.exit(1)

print("\nCONCLUSION: tw-flow output standardized to UUID-only.")
