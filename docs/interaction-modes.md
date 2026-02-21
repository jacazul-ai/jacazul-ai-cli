# 🚦 INTERACTION MODES - Task-Level Behavior Control

> **CRITICAL DISTINCTION:** Interaction Modes are **TASK-LEVEL**, not AGENT-LEVEL. They control how the agent behaves when executing a specific task, based on a prefix in the task description.

---

## Overview

Each task can be prefixed with a **MODE** that dictates the agent's autonomy level and behavior type:

```
[MODE] Task Description
       ↑
       └─ This prefix controls agent behavior for THIS task only
```

**Where are modes specified?**
- In the task **description prefix**: `[PLAN] Refactor auth`, `[EXECUTE] Fix bug`, etc.
- Agent detects the prefix and adjusts behavior accordingly
- Each task can have a **different mode**

---

## Mode Definitions

### 1. **[PLAN]** — Conversational Design
**Autonomy:** Low | **Interaction:** High

**Behavior:**
- Agent acts as requirements analyst
- Breaks down task into subtasks/steps
- Converses with user for consensus
- **Does NOT execute** — only plans
- Presents plan and waits for approval before proceeding

**When to use:**
- New features where approach is unclear
- Refactoring with multiple valid strategies
- Complex changes requiring design discussion

**Example Flow:**
```
User: [PLAN] Redesign user authentication system
Agent: "Here's my breakdown: 1. JWT tokens, 2. Refresh strategy, 3. Session storage. 
        Sound good? Any changes?"
User: "Skip JWT, use sessions directly"
Agent: Updates plan, presents revised breakdown
User: "Ready to execute this part" → Agent moves to EXECUTE mode
```

---

### 2. **[EXECUTE]** — Implementation with Interaction
**Autonomy:** High | **Interaction:** Medium

**Behavior:**
- Agent **implements/writes code**
- Makes decisions autonomously on technical details
- **Pauses periodically for feedback**
- Shows progress, asks for direction on blockers
- User stays engaged, not just a reviewer

**When to use:**
- Building features from approved plan
- Bug fixes with clear root cause
- Implementation tasks where approach is known

**Example Flow:**
```
User: [EXECUTE] Implement JWT token generation
Agent: "Writing token service... [shows code]
        Should I add rate limiting here?"
User: "Yes"
Agent: "Done. Token service ready. Next: refresh endpoint?"
User: "Go"
Agent: Implements, shows result
```

---

### 3. **[GUIDE]** — Zero Autonomy Direction
**Autonomy:** Zero | **Interaction:** Instructional

**Behavior:**
- Agent is **READ-ONLY** during execution
- Provides step-by-step instructions
- User executes the steps
- Agent guides, doesn't execute
- No code writing, only coaching

**When to use:**
- Infrastructure setup (Docker, K8s)
- DevOps tasks where user needs to run commands
- Learning/training scenarios
- Tasks requiring manual intervention

**Example Flow:**
```
User: [GUIDE] Deploy to production
Agent: "Step 1: Update version in package.json (line 3)"
User: [updates]
Agent: "Step 2: Run 'npm run build'"
User: [runs command]
Agent: "Step 3: Push to main branch"
...
```

---

### 4. **[INVESTIGATE]** — Exploration & Findings
**Autonomy:** High (read-only) | **Interaction:** Analytical

**Behavior:**
- Agent **reads codebase extensively**
- Maps relationships, traces flows
- Identifies patterns, risks, dependencies
- **Does NOT modify code**
- Returns findings, context, and recommendations

**When to use:**
- Understanding complex codebase sections
- Root cause analysis of issues
- Risk assessment before major changes
- Technical debt exploration

**Example Flow:**
```
User: [INVESTIGATE] Why is auth failing for social logins?
Agent: [Traces code] "Found it: provider.js line 42 timeout too short.
        Also: 3 other places with same issue. Report:"
        [Shows findings with line references and context]
User: "Got it. [EXECUTE] Fix all three spots"
Agent: Switches to EXECUTE mode
```

---

### 5. **[TEST]** — Verification & QA
**Autonomy:** High | **Interaction:** Results-focused

**Behavior:**
- Agent runs test suites
- Creates/updates tests as needed
- Verifies implementation against acceptance criteria
- Reports test results and coverage
- Suggests fixes for failing tests

**When to use:**
- Validating completed features
- Running full test suite after changes
- Creating test cases for edge cases
- Verification before merge

**Example Flow:**
```
User: [TEST] Verify auth implementation
Agent: "Running tests... 
        ✓ 47 passing
        ✗ 2 failing (social login timeout cases)
        Missing: 3 edge case tests
        
        Want me to create those tests?"
User: "Yes"
Agent: Writes tests, runs again, reports
```

---

### 6. **[DEBUG]** — Root Cause Analysis
**Autonomy:** High (read-only) | **Interaction:** Diagnostic

**Behavior:**
- Agent digs into issue deeply
- Traces execution paths
- Identifies root cause
- Provides diagnosis and **fix proposal** (not implementation)
- Recommends next steps

**When to use:**
- Complex bugs with unclear cause
- Performance issues
- Mysterious crashes/errors
- Systems behavior investigation

**Example Flow:**
```
User: [DEBUG] Why do requests timeout after 30 min?
Agent: [Analyzes logs, traces connections]
       "Root cause: Session pool exhaustion.
        Memory leak in connection handler (line 234).
        Fix: Add connection.close() in finally block.
        Proposal: [shows exact code change]"
User: "Looks right. [EXECUTE] Apply that fix"
```

---

### 7. **[REVIEW]** — Code Audit & Feedback
**Autonomy:** Zero (read-only) | **Interaction:** Critical

**Behavior:**
- Agent reads code/implementation
- Provides critique and suggestions
- Identifies issues: bugs, style, performance, security
- **Does NOT modify code**
- Reports findings and asks for user decision on fixes

**When to use:**
- Before committing code
- Architecture review
- Security audit
- Performance optimization analysis

**Example Flow:**
```
User: [REVIEW] Check my authentication implementation
Agent: "Review results:
        ⚠️  SECURITY: Passwords logged at line 45
        ⚠️  PERFORMANCE: Query N+1 in userDetail loop
        ✓ Good: Input validation solid
        
        Want me to suggest fixes?"
User: "Yes"
Agent: "1. Remove console.log at line 45
        2. Add .lean() to Query at..."
```

---

### 8. **[PR-REVIEW]** — Merge Readiness Check
**Autonomy:** Zero (read-only) | **Interaction:** Summary

**Behavior:**
- Agent reviews PR diffs, changes, commits
- Checks: compliance, coverage, standards
- Validates against acceptance criteria
- Reports readiness assessment
- Flags blockers before merge

**When to use:**
- Pre-merge verification
- PR readiness evaluation
- Final checks before release
- Compliance verification

**Example Flow:**
```
User: [PR-REVIEW] Check if PR #142 is merge-ready
Agent: "PR #142 Review:
        ✓ All tests passing
        ✓ Acceptance criteria met
        ✓ Code coverage improved (89% → 92%)
        ⚠️  1 BREAKING: Changed API return format
        
        Status: ⏸️  READY WITH NOTES
        Action: Update changelog for breaking change"
User: "Will do. Thanks"
```

---

## Mode Behavior Matrix

| Mode | Autonomy | Writes Code | Reads Code | Interaction | Output |
|:---|:---|:---|:---|:---|:---|
| **PLAN** | Low | ❌ | ✓ | High | Plan/breakdown |
| **EXECUTE** | High | ✓ | ✓ | Medium | Modified files + feedback |
| **GUIDE** | Zero | ❌ | ✓ | Instructional | Step-by-step guide |
| **INVESTIGATE** | High* | ❌ | ✓ | Analytical | Findings + context |
| **TEST** | High | ✓ | ✓ | Results | Test results + coverage |
| **DEBUG** | High* | ❌ | ✓ | Diagnostic | Root cause + proposal |
| **REVIEW** |  | Critical | Audit report + suggestions |Zero | ❌ | 
| **PR-REVIEW** | Zero | ❌ | ✓ | Summary | Readiness check |

*High autonomy in exploration, zero autonomy in decisions

---

## How Agent Switches Modes

**Detection:**
1. Agent reads task description
2. Looks for `[MODE]` prefix at start
3. If found → switch to that mode's behavior
4. If not found → use default EXECUTE mode

**Example:**
```
Task created: "[PLAN] Refactor payment service"
              └─ Agent detected [PLAN] → uses PLAN mode behavior
              
Task created: "Fix login button styling"
              └─ No prefix detected → defaults to EXECUTE mode
```

**Switching During Task:**
- Within a task: mode doesn't change unless explicitly requested
- Between tasks: each task has its own mode
- User can request mode change: "Switch to [REVIEW] mode and audit this"

---

## Interaction Pattern by Mode

### Continuous Feedback Loop (EXECUTE)
```
User request → Agent acts → Shows progress → Asks for input → Acts again
                                                                    ↓
 Repeats until task complete ──────────────────┘
```

### One-Way Direction (GUIDE)
```
User ready → Agent provides step → User executes → Next step → ...
```

### Analytical Report (INVESTIGATE, DEBUG)
```
User question → Agent analyzes → Returns findings → User decides next
```

### Decision Checkpoint (PLAN)
```
Agent proposes → User reviews → Approves/changes → Then proceeds to EXECUTE
```

---

## Key Rules

1. **One mode per task** — task description has one prefix
2. **Mode doesn't change mid-task** unless explicitly requested
3. **Default mode is EXECUTE** if no prefix specified
4. **Always show mode being used** in agent responses
5. **Interaction level varies** — some modes require constant feedback, others don't
6. **No hybrid modes** — pick one, stay consistent

---

## Common Mode Combinations

**Feature Development Flow:**
```
1. [PLAN] - Design approach
2. [EXECUTE] - Build it
3. [TEST] - Verify
4. [REVIEW] - Audit
5. [EXECUTE] - Address feedback
```

**Debugging Sequence:**
```
1. [INVESTIGATE] - What's going on?
2. [DEBUG] - Why is it happening?
3. [EXECUTE] - Fix it
4. [TEST] - Verify fix
```

**Infrastructure Deployment:**
```
1. [GUIDE] - Setup steps
2. [EXECUTE] - Automated parts
3. [GUIDE] - Manual verification
```

---

## Agent Checklist by Mode

### PLAN Mode Checklist
- [ ] Break down task into logical steps
- [ ] Identify dependencies and risks
- [ ] Propose approach, explain tradeoffs
- [ ] Wait for user consensus before proceeding
- [ ] Show updated plan if user changes direction

### EXECUTE Mode Checklist
- [ ] Understand the goal
- [ ] Make necessary decisions without asking
- [ ] Write/modify code/files
- [ ] Show progress periodically
- [ ] Ask for direction on blockers/decisions outside scope
- [ ] Confirm completion with user

### GUIDE Mode Checklist
- [ ] Understand what needs to happen
- [ ] Break into numbered steps
- [ ] Explain each step clearly
- [ ] Provide exact commands/actions
- [ ] Wait for user to complete step before next
- [ ] No code writing, only coaching

### INVESTIGATE Mode Checklist
- [ ] Understand what to explore
- [ ] Map code structure, flows, relationships
- [ ] Identify patterns and anomalies
- [ ] Document findings with references (file:line)
- [ ] Don't modify anything
- [ ] Present clear findings and recommendations

### TEST Mode Checklist
- [ ] Understand success criteria
- [ ] Run relevant test suites
- [ ] Report coverage and results
- [ ] Create missing tests if needed
- [ ] Suggest fixes for failures
- [ ] Confirm acceptance criteria are met

### DEBUG Mode Checklist
- [ ] Understand the problem
- [ ] Trace execution paths
- [ ] Identify root cause
- [ ] Propose fix (show code)
- [ ] Don't implement yet
- [ ] Present diagnosis clearly

### REVIEW Mode Checklist
- [ ] Read all code/changes carefully
- [ ] Check: bugs, style, performance, security
- [ ] Identify issues with references
- [ ] Don't modify code
- [ ] Ask user approval before suggesting fixes
- [ ] Report summary assessment

### PR-REVIEW Mode Checklist
- [ ] Read PR description and files changed
- [ ] Check tests, coverage, CI/CD status
- [ ] Validate against acceptance criteria
- [ ] Identify breaking changes
- [ ] Flag blockers for merge
- [ ] Provide readiness summary

---

## Examples in Practice

### Example 1: [PLAN] Task
```
Task: [PLAN] Implement two-factor authentication

Agent Response:
"I'm in PLAN mode. Here's my breakdown:

1. **Setup Phase**
   - Add 'totp' library
   - Create secrets table
   - API endpoint for enabling 2FA

2. **Verification Phase**
   - QR code generation
   - Token validation logic
   - Backup codes system

3. **Integration Phase**
   - Update login endpoint
   - Check 2FA during auth
   - Session handling

Tradeoff: TOTP vs SMS → TOTP is more secure but user-dependent
         We should warn users about backup codes.

Sound good? Any changes to this approach?"
```

### Example 2: [EXECUTE] Task
```
Task: [EXECUTE] Create user preferences endpoint

Agent Response:
"In EXECUTE mode. Creating endpoint...

 Created models/userPreferences.js
 Added database schema
 Created routes/preferences.js

[Shows code snippet]

I'm adding PUT endpoint to update preferences. 
Should I also add a DELETE endpoint to reset to defaults?"

User: "Yes"

Agent: "Done. Also added validation for preference values.
        Endpoint ready at /api/users/:id/preferences

        What's next?"
```

### Example 3: [GUIDE] Task
```
Task: [GUIDE] Deploy to production

Agent Response:
"In GUIDE mode. Follow these steps:

**Step 1:** Update VERSION in package.json
"Currently: 1.2.0 → Change to: 1.2.1"

Let me know when done."

User: "Done"

Agent: "**Step 2:** Run 'npm run build' and wait for success message"
```

### Example 4: [INVESTIGATE] Task
```
Task: [INVESTIGATE] Why is database query slow?

Agent Response:
"In INVESTIGATE mode. Analyzing...

**Root Cause Found:**
- Query in controllers/user.js:45 is missing index
- Database scanning 50k rows instead of using index
- N+1 problem in feedList loop (services/feed.js:120)

**Impact:**
- User page load: 2.3s → should be <300ms
- Feed generation: timeout after 30s

**Recommendations:**
1. Add index on users(email) 
2. Use .lean() in feedList query
3. Add database.explain() to catch similar issues

**Next:** Want me to [DEBUG] the specific fixes?"
```

---

## When Modes Fail

If agent doesn't detect mode or behaves wrong:

1. **Specify mode explicitly:** "Now in [EXECUTE] mode, implement X"
2. **Redirect agent:** "Stop. Switch to [GUIDE] mode and walk me through this"
3. **Clarify expectations:** "This is [REVIEW] mode, so audit the code, don't modify it"


---

**Last Updated:** 2026-02-21
