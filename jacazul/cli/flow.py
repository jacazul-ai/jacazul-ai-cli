#!/usr/bin/env python
import sys
import os
import re
import orjson
import subprocess
from typing import List, Optional, Dict, Any
from jacazul.taskwarrior.core import TaskWrapper, FocusManager, FocusState
from jacazul.cli.broker import GitHubBroker

# 🐊 tw-flow (v1.6.0)
# Python port of the Taskwarrior Flow manager.

VERSION = "1.6.0"


class FlowManager:
    def __init__(self):
        self.tw = TaskWrapper()
        self.focus = FocusManager()
        self.broker = GitHubBroker()

    def error(self, msg: str):
        print(f"ERROR: {msg}", file=sys.stderr)
        sys.exit(1)

    def success(self, msg: str):
        print(f"✓ {msg}")

    def cmd_reopen(self, input_id: str):
        uuid = self.resolve_uuid(input_id)
        self.tw.run([uuid, "modify", "status:pending"])
        self.success(f"Task {uuid[:8]} reopened and moved back to PENDING.")

    def cmd_amend(self, input_id: str, updates: List[str]):
        uuid = self.resolve_uuid(input_id)
        args = [uuid, "modify"]
        found = False
        for update in updates:
            if update.startswith("description="):
                args.append(update.replace("description=", "", 1))
                found = True
            elif update.startswith("ticket="):
                args.append(f"externalid:{update.replace('ticket=', '', 1)}")
                found = True

        if not found:
            self.error(
                "No valid fields to amend. "
                'Use description="..." or ticket="..."'
            )

        self.tw.run(args)
        self.success(f"Task {uuid[:8]} metadata amended successfully.")

    def info(self, msg: str):
        print(f"ℹ {msg}")

    def warning(self, msg: str):
        print(f"⚠ {msg}")

    def resolve_uuid(self, input_val: str) -> str:
        if re.match(
            r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$",
            input_val,
        ):
            return input_val
        tasks = self.tw.export()
        if input_val.isdigit():
            for t in tasks:
                if str(t.get("id")) == input_val:
                    return t["uuid"]
        if len(input_val) >= 8:
            for t in tasks:
                if t["uuid"].startswith(input_val.lower()):
                    return t["uuid"]
        return input_val

    def verify_not_completed(self, uuid: str):
        tasks = self.tw.export([uuid])
        if tasks and tasks[0].get("status") == "completed":
            short = uuid[:8]
            self.error(
                f"Task {short} is already COMPLETED.\n"
                f"   ACTION: To fix metadata (description/ticket), "
                f"use 'tw-flow amend {short} ...'.\n"
                f"   ACTION: To perform more work, "
                f"use 'tw-flow reopen {short}'."
            )

    def find_ticket(
        self, uuid: str, seen: Optional[set] = None
    ) -> Optional[str]:
        if seen is None:
            seen = set()
        if uuid in seen:
            return None
        seen.add(uuid)
        tasks = self.tw.export([uuid])
        if not tasks:
            return None
        task = tasks[0]
        if task.get("externalid"):
            return task["externalid"]
        deps = task.get("depends", [])
        for dep_uuid in deps:
            ticket = self.find_ticket(dep_uuid, seen)
            if ticket:
                return ticket
        return None

    def get_parent_context(self, uuid: str):
        def _collect(u: str, seen: set) -> List[Dict[str, Any]]:
            if u in seen:
                return []
            seen.add(u)
            tasks = self.tw.export([u])
            if not tasks:
                return []
            t = tasks[0]

            results = []
            # Recurse into dependencies first (climb up the tree)
            deps = t.get("depends", [])
            for dep_uuid in deps:
                results.extend(_collect(dep_uuid, seen))

            # Add current task to the list
            # (after its dependencies for top-down order)
            return results + [t]

        # Start collection from parents of the target task
        leaf_tasks = self.tw.export([uuid])
        if not leaf_tasks:
            return

        # We don't want to collect context from the target task itself here
        seen = {uuid}
        all_parents = []
        for dep_uuid in leaf_tasks[0].get("depends", []):
            all_parents.extend(_collect(dep_uuid, seen))

        if all_parents:
            header_shown = False
            for p in all_parents:
                annots = [
                    a["description"]
                    for a in p.get("annotations", [])
                    if re.match(
                        r"^(OUTCOME|DECISION|LESSON|HANDOFF|"
                        r"QUESTION|HYPOTHESIS):",
                        a["description"],
                    )
                ]
                if annots:
                    if not header_shown:
                        print("\n══ INHERITED CONTEXT ══")
                        header_shown = True
                    print(f"Task ({p['uuid'][:8]}) [{p['description']}]:")
                    for a in annots:
                        print(f"  - {a}")
            if header_shown:
                print("")

    def cmd_plan(self, name: str, tasks: List[str]):
        if not name:
            self.error("Plan name required")
        if not tasks:
            self.error("At least one task required")
        self.info(f"Creating plan: {name}")
        urgency, prev_uuid = 9.0, None
        for spec in tasks:
            parts = spec.split("|")
            mode, desc, tag, due = "", "", "implementation", "today"
            if len(parts) >= 1:
                if parts[0] in [
                    "DESIGN",
                    "SPIKE",
                    "INVESTIGATE",
                    "GUIDE",
                    "EXECUTE",
                    "TEST",
                    "DEBUG",
                    "REVIEW",
                    "PR-REVIEW",
                ]:
                    mode = parts[0]
                    desc = parts[1] if len(parts) > 1 else ""
                    tag = parts[2] if len(parts) > 2 else tag
                    due = parts[3] if len(parts) > 3 else due
                else:
                    desc = parts[0]
                    tag = parts[1] if len(parts) > 1 else tag
                    due = parts[2] if len(parts) > 2 else due
            if not desc:
                self.error("Task description cannot be empty")
            final_desc = f"[{mode}] {desc}" if mode else desc
            priority = (
                "H" if urgency >= 9.0 else ("L" if urgency <= 3.0 else "M")
            )
            args = [
                "add",
                f"project:{name}",
                final_desc,
                f"due:{due}",
                f"priority:{priority}",
                f"+{tag}",
            ]
            if prev_uuid:
                args.append(f"depends:{prev_uuid}")
            res = self.tw.run(args)
            match = re.search(r"Created task (\d+)", res.stdout)
            if match:
                new_id = match.group(1)
                new_tasks = self.tw.export([new_id])
                if new_tasks:
                    uuid = new_tasks[0]["uuid"]
                    prev_uuid = uuid
                    self.success(
                        f"Created task {uuid[:8]}: {final_desc} "
                        f"[priority: {priority}]"
                    )
            else:
                self.error(
                    f"Failed to create task: {final_desc}\n{res.stderr}"
                )
            urgency -= 2.0
        self.success(f"Plan created with {len(tasks)} tasks")

    def cmd_rename(self, old_name: str, new_name: str):
        self.info(f"Renaming plan '{old_name}' to '{new_name}'...")

        # 1. Check if plan exists
        tasks = self.tw.export([f"project:{old_name}"])
        if not tasks:
            self.error(f"Plan '{old_name}' not found or has no tasks.")

        # 2. Modify tasks in Taskwarrior
        # Use 'yes all' to bypass confirmation if bulk modifying
        res = self.tw.run(
            [f"project:{old_name}", "modify", f"project:{new_name}"]
        )
        if res.returncode != 0:
            self.error(f"Failed to rename plan in Taskwarrior: {res.stderr}")

        # 3. Synchronize Focus Context
        state = self.focus.load()
        updated = False

        if state.focused_plan == old_name:
            state.focused_plan = new_name
            updated = True

        if old_name in state.plans_of_interest:
            state.plans_of_interest = [
                new_name if i == old_name else i
                for i in state.plans_of_interest
            ]
            state.plans_of_interest = sorted(
                list(set(state.plans_of_interest))
            )
            updated = True

        for entry in state.task_track:
            if entry.get("plan") == old_name:
                entry["plan"] = new_name
                updated = True
            elif entry.get("ini") == old_name:
                entry["plan"] = new_name
                updated = True

        if updated:
            self.focus.save(state)
            self.info("Focus context synchronized with new plan name.")

        self.success(
            f"Plan '{old_name}' successfully renamed to '{new_name}'."
        )

    def cmd_status(
        self,
        filter_val: Optional[str] = None,
        pending_only: bool = False,
        use_table: bool = False,
    ):
        state = self.focus.load()
        plan_name = filter_val or state.focused_plan
        if not plan_name:
            active = self.tw.export(["+ACTIVE"])
            plan_name = active[0].get("project") if active else "ALL ACTIVE"

        filter_args = (
            [f"project:{plan_name}"] if plan_name != "ALL ACTIVE" else []
        )
        if pending_only:
            filter_args.append("status:pending")

        tasks = self.tw.export(filter_args)
        # Sort tasks: pending first, then by entry date
        tasks.sort(
            key=lambda x: (0 if x["status"] == "pending" else 1, x["entry"])
        )

        print(f"══ Plan: {plan_name} ══")
        # 🐊 Prompt as Ad: Focus Context
        print("ℹ TIP: 'tw-flow status' is for the current FOCUS (FOCO).")
        print("ℹ Use 'tw-flow focus' for any anchor-related actions.")
        print("ℹ Use 'tw-flow ponder' for the PROJECT-WIDE landscape.\n")

        mode = os.environ.get("JACAZUL_MODE", "COUNSELOR")
        print(f"🛡️  MODE: {mode}")
        if mode != "UNHINGED":
            print(
                "⚠️  RESTRICTION: User confirmation required for Commits/Push."
            )
        print("")

        if plan_name == state.focused_plan:
            print("📌 ANCHORED SESSION")

        if state.focused_task_uuid:
            print(f"\n🎯 FOCUS CONTEXT [{state.focused_task_uuid[:8]}]:")
            self.get_parent_context(state.focused_task_uuid)
            ft_tasks = self.tw.export([state.focused_task_uuid])
            if ft_tasks:
                task = ft_tasks[0]
                ticket = self.find_ticket(task["uuid"])
                if ticket:
                    is_inherited = ticket != task.get("externalid")
                    prefix = "Inherited" if is_inherited else "External"
                    print(
                        f"🐊 ALERT: {prefix} ticket detected "
                        f"({ticket}). Git-expert will use this for "
                        "automated commit referencing."
                    )
                for a in task.get("annotations", []):
                    print(f"  - {a['description']}")

        pending = [t for t in tasks if t["status"] == "pending"]
        completed = [t for t in tasks if t["status"] == "completed"]

        if use_table:
            self.render_status_table(pending, completed, state)
        else:
            self.render_status_list(pending, completed, state)

        print(f"\nTotal: {len(pending)} pending, {len(completed)} completed.")

    def render_status_list(self, pending, completed, state):
        def format_task_line(t):
            uuid_short = t["uuid"][:8]
            mark = (
                " - ACTIVE"
                if t.get("start")
                else (
                    " - FOCUSED"
                    if t["uuid"] == state.focused_task_uuid
                    else ""
                )
            )
            ticket = self.find_ticket(t["uuid"])
            ticket_str = f" [{ticket}]" if ticket else ""
            return f"[{uuid_short}{mark}]{ticket_str} {t['description']}"

        if pending:
            print("\nPENDING:")
            for t in pending:
                print(f"- {format_task_line(t)}")
        if completed:
            print("\nCOMPLETED:")
            for t in completed:
                print(f"  ✓ {format_task_line(t)}")

    def render_status_table(self, pending, completed, state):
        print("\n| ST | UUID | TICKET | DESCRIPTION |")
        print("|---|---|---|---|")

        def format_table_row(t, icon):
            uuid_short = t["uuid"][:8]
            ticket = self.find_ticket(t["uuid"]) or "-"
            desc = t["description"]
            # Highlight focused task in description
            if t["uuid"] == state.focused_task_uuid:
                desc = f"**{desc}**"
            return f"| {icon} | `{uuid_short}` | {ticket} | {desc} |"

        for t in pending:
            icon = "⚡" if t.get("start") else "○"
            if t["uuid"] == state.focused_task_uuid:
                icon = "🎯"
            print(format_table_row(t, icon))

        for t in completed:
            print(format_table_row(t, "✓"))

    def cmd_next(self, filter_val: str = "status:pending"):
        self.info("Next tasks ready to work:")
        print("")
        # We need to capture output to filter out numeric IDs
        args = (
            [filter_val, "ready"]
            if "project:" in filter_val or "status:" in filter_val
            else [f"project:{filter_val}", "status:pending", "ready"]
        )
        res = self.tw.run(args, capture=True)
        if res.returncode == 0:
            lines = res.stdout.strip().split("\n")
            for line in lines:
                # Taskwarrior ready report line format:
                # ID Age Tag Urgency Description
                # We want to replace ID with short UUID
                match = re.match(r"^\s*(\d+)\s+", line)
                if match:
                    numeric_id = match.group(1)
                    # Resolve to UUID
                    tasks = self.tw.export([numeric_id])
                    if tasks:
                        uuid_short = tasks[0]["uuid"][:8]
                        new_line = re.sub(r"^\s*\d+", f"  {uuid_short}", line)
                        print(new_line)
                else:
                    # Header or other lines
                    print(line)
        else:
            self.warning("No tasks ready")

    def cmd_execute(self, input_id: str):
        uuid = self.resolve_uuid(input_id)
        self.verify_not_completed(uuid)
        self.get_parent_context(uuid)
        res = self.tw.run([uuid, "start"])
        if res.returncode == 0:
            self.success(f"Started working on task {uuid[:8]}")
            self.tw.run([uuid], capture=False)
        else:
            self.error(f"Failed to start task: {res.stderr}")

    def cmd_done(self, input_id: str, note: Optional[str] = None):
        uuid = self.resolve_uuid(input_id)
        self.verify_not_completed(uuid)
        tasks = self.tw.export([uuid])
        if not tasks:
            self.error("Task not found")

        # 🐊 Python Quality Gate (Vaccinated Tool)
        # Check for modified or untracked .py files in the current context
        res = subprocess.run(
            ["git", "status", "--porcelain", "-uall"],
            capture_output=True,
            text=True,
            check=False,
        )
        modified_py = [
            line.split()[-1]
            for line in res.stdout.splitlines()
            if line.strip().endswith(".py")
            and os.path.exists(line.split()[-1])
        ]

        if modified_py and os.environ.get("JACAZUL_TESTING") != "true":
            self.info(
                "Python files detected. Running Quality Gate (py-check)..."
            )

            pycheck_bin = os.path.join(
                os.path.expanduser("~/.jacazul-ai"),
                "skills/python_expert/scripts/py-check",
            )
            # Fallback to local path if not in home
            if not os.path.exists(pycheck_bin):
                pycheck_bin = os.path.join(
                    os.path.dirname(
                        os.path.dirname(
                            os.path.dirname(os.path.abspath(__file__))
                        )
                    ),
                    "skills/python_expert/scripts/py-check",
                )

            check_res = subprocess.run(
                [pycheck_bin] + modified_py,
                capture_output=False,  # Allow it to print its own beauty
                text=True,
                check=False,
            )
            if check_res.returncode != 0:
                self.error(
                    "Python validation failed. Task completion BLOCKED.\n"
                    "   ACTION: Fix the PEP 8 violations reported above "
                    "before running 'done'."
                )

        if not any(
            "OUTCOME:" in a["description"]
            for a in tasks[0].get("annotations", [])
        ):
            self.error(
                f"Task {uuid[:8]} cannot be completed without an "
                "OUTCOME record.\n   "
                f'Use: tw-flow outcome {uuid[:8]} "your result"'
            )
        if note:
            self.tw.run([uuid, "annotate", f"DONE: {note}"])
        os.environ["TW_FLOW_INTERNAL"] = "true"
        res = self.tw.run([uuid, "done"])
        if res.returncode == 0:
            self.success(f"Task {uuid[:8]} completed!")

            # GitHub Protocol Sync
            ticket = self.find_ticket(uuid)
            if ticket and ticket.startswith("#"):
                print("")
                self.info(f"The Protocol: Synchronizing ticket {ticket}...")
                self.broker.sync_issue(ticket)

            # Check if any tasks were unblocked
            print("")
            self.info("Checking for newly unblocked tasks...")
            # Reuse cmd_next logic for standardized output
            tasks = self.tw.export(["status:pending", "ready", "limit:3"])
            if tasks:
                self.success(f"{len(tasks)} task(s) now ready to work")
                for t in tasks:
                    print(
                        f"  {t['uuid'][:8]} - {t['description']} "
                        f"[{t.get('urgency', 0):.1f}]"
                    )
        else:
            self.error(f"Failed to complete task: {res.stderr}")

    def cmd_outcome(self, input_id: str, msg: str):
        uuid = self.resolve_uuid(input_id)
        self.verify_not_completed(uuid)
        self.tw.run([uuid, "annotate", f"OUTCOME: {msg}"])
        self.success(f"Recorded outcome for task {uuid[:8]}")

    def cmd_handoff(self, input_id: str, msg: str):
        uuid = self.resolve_uuid(input_id)
        self.verify_not_completed(uuid)
        self.cmd_execute(uuid)
        self.tw.run([uuid, "annotate", f"HANDOFF: {msg}"])
        self.success(f"Handoff to task {uuid[:8]} with note")

    def cmd_note(self, input_id: str, note_type: str, msg: str):
        uuid = self.resolve_uuid(input_id)
        self.verify_not_completed(uuid)
        prefixes = {
            "research": "RESEARCH",
            "r": "RESEARCH",
            "decision": "DECISION",
            "d": "DECISION",
            "outcome": "OUTCOME",
            "o": "OUTCOME",
            "handoff": "HANDOFF",
            "h": "HANDOFF",
            "blocked": "BLOCKED",
            "b": "BLOCKED",
            "lesson": "LESSON",
            "l": "LESSON",
            "question": "QUESTION",
            "q": "QUESTION",
            "hypothesis": "HYPOTHESIS",
            "y": "HYPOTHESIS",
            "ac": "AC",
            "a": "AC",
            "note": "NOTE",
            "n": "NOTE",
            "link": "LINK",
        }
        prefix = prefixes.get(note_type.lower())
        if not prefix:
            allowed = ", ".join(sorted(set(p for p in prefixes.values())))
            self.error(
                f"Invalid note type: '{note_type}'.\n   "
                f"ACTION: Use one of the allowed semantic types: {allowed}"
            )
        self.tw.run([uuid, "annotate", f"{prefix}: {msg}"])
        self.success(f"Added {prefix} note to task {uuid[:8]}")

    def cmd_ticket(self, input_id: str, ticket: str):
        uuid = self.resolve_uuid(input_id)
        self.verify_not_completed(uuid)

        # Validate ticket if it looks like a GitHub issue
        if ticket.startswith("#"):
            self.info(f"The Protocol: Validating ticket {ticket}...")
            # We use sync_issue here because it provides a good summary
            # and checks existence. If it fails, we still allow the link
            # but warn the user.
            self.broker.sync_issue(ticket)

        self.tw.run([uuid, "modify", f"externalid:{ticket}"])
        self.success(f"Task {uuid[:8]} linked to ticket: {ticket}")

    def cmd_commit(self, is_fix: bool = False):
        state = self.focus.load()
        uuid = state.focused_task_uuid
        if not uuid:
            active = self.tw.export(["+ACTIVE"])
            if active:
                uuid = active[0]["uuid"]

        if not uuid:
            self.error("No active or focused task found to generate commit.")
            return

        tasks = self.tw.export([uuid])
        if not tasks:
            self.error("Task not found.")
            return

        task = tasks[0]
        desc = task["description"]
        ticket = self.find_ticket(uuid)

        # Determine prefix from interaction mode
        prefix = "feat"
        if "[DESIGN]" in desc or "[SPIKE]" in desc:
            prefix = "docs"
        elif "[DEBUG]" in desc or "[BUG]" in desc:
            prefix = "fix"
        elif "[TEST]" in desc:
            prefix = "test"
        elif "[REFINE]" in desc or "[REFACTOR]" in desc:
            prefix = "refactor"

        # Clean description (remove mode and initiative name if present)
        clean_desc = re.sub(r"\[[A-Z-]+\]\s*", "", desc).lower()

        mode = os.environ.get("JACAZUL_MODE", "COUNSELOR")
        print("\n══ DRAFT CONVENTIONAL COMMIT ══")
        print(f"{prefix}: {clean_desc}")

        if mode != "UNHINGED":
            if ticket:
                ref_type = "Fixes" if is_fix else "Refs"
                print(f"\n{ref_type}: {ticket}")
            print("═══════════════════════════════")
            print("\n🛡️  SAFETY GATE: Manual Confirmation Required.")
            print("   AGENT ACTION: Present this draft to the user and WAIT.")
            print(
                "   The 'git commit' command must not be executed "
                "automatically."
            )
            return

        print("\n[Body: explain what and why...]")

        if ticket:
            ref_type = "Fixes" if is_fix else "Refs"
            print(f"\n{ref_type}: {ticket}")
        print("═══════════════════════════════")
        self.info("Copy the draft above and use 'git commit -m \"...\"'")

    def cmd_context(self, input_id: str):
        uuid = self.resolve_uuid(input_id)
        self.info(f"Full context for task {uuid[:8]}:")
        print("")
        verbose = (
            "affected,header,foot,label,columns,subtotal,"
            "stats,history,project,context,annotations"
        )
        self.tw.run([uuid, "info"], capture=False, verbose=verbose)

    def cmd_plans(self, show_all: bool = False, show_closed: bool = False):
        self.info("Project Plans Landscape:")
        print("")

        # Fetch all relevant tasks
        filter_args = [] if show_all or show_closed else ["status:pending"]
        all_tasks = self.tw.export(filter_args)

        # Group tasks by project
        projects = {}
        for t in all_tasks:
            plan = t.get("project")
            if not plan or "_archive" in plan or "_trash" in plan:
                continue
            if plan not in projects:
                projects[plan] = {
                    "pending": 0,
                    "active": 0,
                    "completed": 0,
                    "blocked": 0,
                }

            if t["status"] == "pending":
                projects[plan]["pending"] += 1
                if t.get("start"):
                    projects[plan]["active"] += 1
                if t.get("tags") and "BLOCKED" in t["tags"]:
                    projects[plan]["blocked"] += 1
            elif t["status"] == "completed":
                projects[plan]["completed"] += 1

        # Determine which projects to show
        plans = sorted(projects.keys())
        displayed = 0

        for plan in plans:
            p = projects[plan]
            is_open = p["pending"] > 0

            if show_all:
                should_show = True
            elif show_closed:
                should_show = not is_open
            else:
                should_show = is_open

            if should_show:
                icon = "●" if is_open else "✓"
                status_label = "ACTIVE" if is_open else "ZEROED"
                print(f"{icon} {plan} [{status_label}]")
                print(
                    f"  Pending: {p['pending']} | Active: {p['active']} | "
                    f"Completed: {p['completed']} | Blocked: {p['blocked']}\n"
                )

                displayed += 1

        if displayed == 0:
            self.success("No plans match the filter!")

    def cmd_ponder(self, args: List[str]):
        from jacazul.cli.ponder import Dashboard

        show_all = "--all" in args
        use_table = "--table" in args
        project_root = next((a for a in args if not a.startswith("-")), None)
        db = Dashboard(
            project_root, show_all, hide_tip=True, use_table=use_table
        )
        db.render()

    def cmd_active(self):
        self.info("Currently active tasks:")
        print("")
        self.tw.run(["+ACTIVE"], capture=False)

    def cmd_blocked(self):
        self.info("Blocked tasks:")
        print("")
        self.tw.run(["+BLOCKED"], capture=False)

    def cmd_overdue(self):
        self.info("Overdue tasks:")
        print("")
        self.tw.run(["due.before:today", "status:pending"], capture=False)

    def cmd_urgent(self, input_id: str, urgency: str = "15.0"):
        uuid = self.resolve_uuid(input_id)
        self.tw.run([uuid, "modify", f"urgency:{urgency}", "priority:H"])
        self.success(f"Task {uuid[:8]} marked as urgent (urgency: {urgency})")

    def cmd_block(self, input_id: str, dep_id: str):
        uuid, dep_uuid = self.resolve_uuid(input_id), self.resolve_uuid(dep_id)
        self.tw.run([uuid, "modify", f"depends:{dep_uuid}"])
        self.success(f"Task {uuid[:8]} now depends on task {dep_uuid[:8]}")

    def cmd_unblock(self, input_id: str, dep_id: str):
        uuid, dep_uuid = self.resolve_uuid(input_id), self.resolve_uuid(dep_id)
        tasks = self.tw.export([uuid])
        if not tasks:
            return
        new_deps = [
            d for t in tasks for d in t.get("depends", []) if d != dep_uuid
        ]
        self.tw.run(
            [
                uuid,
                "modify",
                f"depends:{','.join(new_deps)}" if new_deps else "depends:",
            ]
        )
        self.success(
            f"Removed dependency on task {dep_uuid[:8]} from task {uuid[:8]}"
        )

    def cmd_wait(self, input_id: str, date: str):
        uuid = self.resolve_uuid(input_id)
        self.tw.run([uuid, "modify", f"wait:{date}"])
        self.success(f"Task {uuid[:8]} waiting until {date}")

    def cmd_discard(self, input_id: str):
        uuid = self.resolve_uuid(input_id)
        tasks = self.tw.export([uuid])
        if not tasks:
            return
        ini = tasks[0].get("project", "unscoped")
        archive = f"{ini.split(':_archive')[0]}:_archive"
        os.environ["TW_FLOW_INTERNAL"] = "true"
        self.tw.run([uuid, "modify", f"project:{archive}", "+DISCARDED"])
        self.tw.run(
            [uuid, "annotate", "OUTCOME: Task discarded and moved to archive."]
        )
        self.tw.run([uuid, "done"])
        self.success(f"Task {uuid[:8]} moved to archive and marked done.")

    def cmd_tree(self, filter_val: str = "status:pending"):
        plan = (
            filter_val
            if "project:" in filter_val or "status:" in filter_val
            else f"project:{filter_val}"
        )
        print(f"══ Plan: {filter_val} ══")

        def render(uuid, indent="", last=True):
            tasks = self.tw.export([uuid])
            if not tasks:
                return
            t = tasks[0]
            icon = (
                "✓"
                if t["status"] == "completed"
                else (
                    "⚡"
                    if t.get("start")
                    else (
                        "🔒"
                        if "READY"
                        not in self.tw.run(
                            [uuid, "+READY"], capture=True
                        ).stdout
                        else "○"
                    )
                )
            )
            marker = ("└── " if last else "├── ") if indent else ""
            print(f"{indent}{marker}{icon} ({uuid[:8]}) | {t['description']}")
            children = [
                c["uuid"]
                for c in self.tw.export(
                    [f"depends.contains:{uuid}", "status:pending"]
                )
                if "_archive" not in c.get("project", "")
            ]
            for i, c_uuid in enumerate(children):
                render(
                    c_uuid,
                    indent + ("    " if last else "│   "),
                    i == len(children) - 1,
                )

        roots = [
            t["uuid"]
            for t in self.tw.export([plan])
            if not t.get("depends") and "_archive" not in t.get("project", "")
        ]
        for uuid in roots:
            render(uuid)


def main():
    if len(sys.argv) < 2:
        print(f"tw-flow v{VERSION}")
        sys.exit(0)
    cmd, args, flow = sys.argv[1], sys.argv[2:], FlowManager()
    if cmd in ["plan", "initiative", "ini"]:
        flow.cmd_plan(args[0], args[1:])
    elif cmd == "status":
        pending_only = "--pending" in args
        use_table = "--table" in args
        filter_val = next((a for a in args if not a.startswith("-")), None)
        flow.cmd_status(filter_val, pending_only, use_table)
    elif cmd == "ponder":
        flow.cmd_ponder(args)
    elif cmd == "next":
        flow.cmd_next(args[0] if args else "status:pending")
    elif cmd == "execute":
        flow.cmd_execute(args[0])
    elif cmd == "done":
        flow.cmd_done(args[0], args[1] if len(args) > 1 else None)
    elif cmd == "outcome":
        flow.cmd_outcome(args[0], " ".join(args[1:]))
    elif cmd == "handoff":
        flow.cmd_handoff(args[0], " ".join(args[1:]))
    elif cmd == "reopen":
        flow.cmd_reopen(args[0])
    elif cmd == "amend":
        flow.cmd_amend(args[0], args[1:])
    elif cmd == "note":
        flow.cmd_note(args[0], args[1], " ".join(args[2:]))
    elif cmd == "ticket":
        flow.cmd_ticket(args[0], args[1])
    elif cmd == "commit":
        flow.cmd_commit(is_fix="--fix" in args)
    elif cmd == "context":
        flow.cmd_context(args[0])
    elif cmd in ["plans", "inis", "initiatives"]:
        show_all = "--all" in args
        show_closed = "--closed" in args
        flow.cmd_plans(show_all, show_closed)
    elif cmd == "active":
        flow.cmd_active()
    elif cmd == "blocked":
        flow.cmd_blocked()
    elif cmd == "overdue":
        flow.cmd_overdue()
    elif cmd == "urgent":
        flow.cmd_urgent(args[0], args[1] if len(args) > 1 else "15.0")
    elif cmd == "block":
        flow.cmd_block(args[0], args[1])
    elif cmd == "unblock":
        flow.cmd_unblock(args[0], args[1])
    elif cmd == "wait":
        flow.cmd_wait(args[0], args[1])
    elif cmd == "discard":
        flow.cmd_discard(args[0])
    elif cmd == "rename":
        if len(args) < 2:
            flow.error("Usage: tw-flow rename <old_name> <new_name>")
        flow.cmd_rename(args[0], args[1])
    elif cmd == "tree":
        flow.cmd_tree(args[0] if args else "status:pending")
    elif cmd == "focus":
        sub = args[0] if args else None
        if sub == "ind":
            ind_sub = args[1] if len(args) > 1 else None
            if ind_sub in ["plan", "ini"]:
                name = (
                    args[2] if len(args) > 2
                    else (
                        flow.tw.export(["+ACTIVE"])[0].get("project")
                        if flow.tw.export(["+ACTIVE"])
                        else None
                    )
                )
                if name:
                    flow.focus.update_plan(name)
                    tasks = flow.tw.export(
                        [f"project:{name}", "status:pending", "limit:1"]
                    )
                    if tasks:
                        flow.focus.push_task(tasks[0]["uuid"], name)
                        flow.success(
                            f"Independent focus anchored to plan: {name} "
                            f"(Task pushed to heap: {tasks[0]['uuid'][:8]})"
                        )
                    else:
                        flow.success(f"Independent focus anchored to plan: {name}")
                else:
                    flow.error("Plan name required")
            elif ind_sub == "task":
                uuid = flow.resolve_uuid(args[2]) if len(args) > 2 else None
                tasks = flow.tw.export([uuid]) if uuid else []
                if tasks:
                    flow.focus.push_task(uuid, tasks[0].get("project", ""))
                    flow.success(
                        f"Independent focus anchored to task: {uuid[:8]} "
                        f"(pushed to stack)"
                    )
                else:
                    flow.error("Usage: focus ind task <uuid>")
            elif ind_sub:
                tasks = flow.tw.export([f"project:{ind_sub}", "limit:1"])
                if tasks:
                    name = tasks[0]["project"]
                    flow.focus.update_plan(name)
                    pending = flow.tw.export(
                        [f"project:{name}", "status:pending", "limit:1"]
                    )
                    if pending:
                        flow.focus.push_task(pending[0]["uuid"], name)
                        flow.success(
                            f"Independent smart-focus anchored to: {name} "
                            f"(Task: {pending[0]['uuid'][:8]})"
                        )
                    else:
                        flow.success(
                            f"Independent smart-focus anchored to: {name}"
                        )
                else:
                    flow.error(
                        f"Unknown plan or smart-focus: '{ind_sub}'.\n"
                        "   ACTION: Use 'focus ind plan <name>', "
                        "'focus ind task <uuid>', or 'focus ind <plan-name>'."
                    )
            else:
                flow.error("Usage: focus ind [plan <name>|task <uuid>|<plan-name>]")
        elif sub == "back":
            session_file = flow.focus.session_file_path
            if session_file and os.path.exists(session_file):
                os.remove(session_file)
                flow.success(
                    "Exited independent session. Switched back to global focus."
                )
            else:
                flow.error(
                    "No independent session active. Already in global mode."
                )
        elif sub in ["plan", "ini"]:
            name = (
                args[1]
                if len(args) > 1
                else (
                    flow.tw.export(["+ACTIVE"])[0].get("project")
                    if flow.tw.export(["+ACTIVE"])
                    else None
                )
            )
            if name:
                flow.focus.update_plan(name)
                tasks = flow.tw.export(
                    [f"project:{name}", "status:pending", "limit:1"]
                )
                if tasks:
                    flow.focus.push_task(tasks[0]["uuid"], name)
                    flow.success(
                        f"Focused plan anchored to: {name} "
                        f"(Task pushed to heap: {tasks[0]['uuid'][:8]})"
                    )
                else:
                    flow.success(f"Focused plan anchored to: {name}")
            else:
                flow.error("Plan name required")
        elif sub == "task":
            uuid = flow.resolve_uuid(args[1])
            tasks = flow.tw.export([uuid])
            if tasks:
                flow.focus.push_task(uuid, tasks[0].get("project", ""))
                flow.success(
                    f"Focused task anchored to: {uuid[:8]} (pushed to stack)"
                )
        elif sub == "pop":
            flow.focus.pop_task()
            flow.success(
                f"Popped task focus. Current top: "
                f"{flow.focus.load().focused_task_uuid or 'none'}"
            )
        elif sub == "interest":
            action, name = (
                (args[1] if len(args) > 1 else None),
                (args[2] if len(args) > 2 else None),
            )
            state = flow.focus.load()
            if action == "add" and name:
                state.plans_of_interest = sorted(
                    list(set(state.plans_of_interest + [name]))
                )
                flow.focus.save(state)
                flow.success(f"Added '{name}' to interests.")
            elif action == "remove" and name:
                state.plans_of_interest = [
                    i for i in state.plans_of_interest if i != name
                ]
                flow.focus.save(state)
                flow.success(f"Removed '{name}' from interests.")
            elif action == "list":
                print(
                    "══ Plans of Interest ══\n"
                    + (
                        "\n".join(state.plans_of_interest)
                        if state.plans_of_interest
                        else "(empty)"
                    )
                )
            else:
                flow.error("Usage: focus interest [add|remove|list] <name>")
        elif sub == "clear":
            session_file = flow.focus.session_file_path
            if session_file and os.path.exists(session_file):
                os.remove(session_file)
                flow.success("Independent session focus cleared.")
            else:
                flow.error(
                    "No independent session active. focus.json is never "
                    "touched by clear."
                )
        elif sub:
            # Smart Focus: Check if 'sub' is a valid plan name
            tasks = flow.tw.export([f"project:{sub}", "limit:1"])
            if tasks:
                name = tasks[0]["project"]
                flow.focus.update_plan(name)
                pending = flow.tw.export(
                    [f"project:{name}", "status:pending", "limit:1"]
                )
                if pending:
                    flow.focus.push_task(pending[0]["uuid"], name)
                    flow.success(
                        f"Smart-focused anchored to: {name} "
                        f"(Task: {pending[0]['uuid'][:8]})"
                    )
                else:
                    flow.success(f"Smart-focused anchored to: {name}")
            else:
                flow.error(
                    f"Unknown focus subcommand or plan: '{sub}'.\n"
                    "   ACTION: Use 'focus plan <name>'"
                    " or 'focus task <uuid>'."
                )
        else:
            print(
                "══ Current Session Focus ══\n"
                + orjson.dumps(
                    flow.focus.load().to_dict(), option=orjson.OPT_INDENT_2
                ).decode()
            )
    elif cmd in ["help", "--help", "-h"]:
        print(
            "tw-flow USAGE:\n"
            "  plan <plan> <tasks...>\n"
            "  next [plan]\n"
            "  execute <id>\n"
            "  done <id> [note]\n"
            "  outcome <id> <msg>\n"
            "  reopen <id>\n"
            '  amend <id> [description="..."] [ticket="..."]\n'
            "  note <id> <type> <msg>\n"
            "  ticket <id> <ticket>\n"
            "  commit [--fix]\n"
            "  discard <id>\n"
            "  rename <old> <new>\n"
            "  plans [--all|--closed] | status [plan] [--pending] [--table]\n"
            "  ponder [project_root] [--all]\n"
            "  focus [plan|task|pop|interest|clear]\n"
            "  tree [plan]"
        )
    else:
        flow.error(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()
