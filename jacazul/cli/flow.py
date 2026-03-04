#!/usr/bin/env python
import sys
import os
import re
import orjson
from typing import List, Optional, Dict, Any
from jacazul.taskwarrior.core import TaskWrapper, FocusManager, FocusState

# 🐊 tw-flow (v1.6.0)
# Python port of the Taskwarrior Flow manager.

VERSION = "1.6.0"


class FlowManager:
    def __init__(self):
        self.tw = TaskWrapper()
        self.focus = FocusManager()

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

    def cmd_initiative(self, name: str, tasks: List[str]):
        if not name:
            self.error("Initiative name required")
        if not tasks:
            self.error("At least one task required")
        self.info(f"Creating initiative: {name}")
        urgency, prev_uuid = 9.0, None
        for spec in tasks:
            parts = spec.split("|")
            mode, desc, tag, due = "", "", "implementation", "today"
            if len(parts) >= 1:
                if parts[0] in [
                    "DESIGN",
                    "PLAN",
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
        self.success(f"Initiative created with {len(tasks)} tasks")

    def cmd_status(
        self, filter_val: Optional[str] = None, pending_only: bool = False
    ):
        state = self.focus.load()
        ini_name = filter_val or state.focused_ini
        if not ini_name:
            active = self.tw.export(["+ACTIVE"])
            ini_name = active[0].get("project") if active else "ALL ACTIVE"

        filter_args = (
            [f"project:{ini_name}"] if ini_name != "ALL ACTIVE" else []
        )
        if pending_only:
            filter_args.append("status:pending")

        tasks = self.tw.export(filter_args)
        # Sort tasks: pending first, then by entry date
        tasks.sort(
            key=lambda x: (0 if x["status"] == "pending" else 1, x["entry"])
        )

        print(f"══ Initiative: {ini_name} ══")
        if ini_name == state.focused_ini:
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
                        f"🐊 \033[1;33mALERT:\033[0m {prefix} ticket detected "
                        f"({ticket}). Git-expert will use this for "
                        "automated commit referencing."
                    )
                for a in task.get("annotations", []):
                    print(f"  - {a['description']}")

        pending = [t for t in tasks if t["status"] == "pending"]
        completed = [t for t in tasks if t["status"] == "completed"]

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
        print(f"\nTotal: {len(pending)} pending, {len(completed)} completed.")

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
        self.tw.run([uuid, "modify", f"externalid:{ticket}"])
        self.success(f"Task {uuid[:8]} linked to ticket: {ticket}")

    def cmd_context(self, input_id: str):
        uuid = self.resolve_uuid(input_id)
        self.info(f"Full context for task {uuid[:8]}:")
        print("")
        verbose = (
            "affected,header,foot,label,columns,subtotal,"
            "stats,history,project,context,annotations"
        )
        self.tw.run([uuid, "info"], capture=False, verbose=verbose)

    def cmd_initiatives(self):
        self.info("Initiatives with pending tasks:")
        print("")
        tasks = self.tw.export(["status:pending"])
        inis = sorted(
            list(set(t["project"] for t in tasks if t.get("project")))
        )
        if not inis:
            self.success("No active initiatives!")
            return
        for ini in inis:
            p = [t for t in tasks if t.get("project") == ini]
            a = len([t for t in p if t.get("start")])
            b = len([t for t in p if t.get("tags") and "BLOCKED" in t["tags"]])
            print(
                f"● {ini}\n  "
                f"Pending: {len(p) - a} | Active: {a} | Blocked: {b}\n"
            )

    def cmd_ponder(self, args: List[str]):
        from jacazul.cli.ponder import Dashboard

        show_all = "--all" in args
        project_root = next((a for a in args if not a.startswith("-")), None)
        db = Dashboard(project_root, show_all, hide_tip=True)
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
        ini = (
            filter_val
            if "project:" in filter_val or "status:" in filter_val
            else f"project:{filter_val}"
        )
        print(f"══ Initiative: {filter_val} ══")

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
            for t in self.tw.export([ini])
            if not t.get("depends") and "_archive" not in t.get("project", "")
        ]
        for uuid in roots:
            render(uuid)


def main():
    if len(sys.argv) < 2:
        print(f"tw-flow v{VERSION}")
        sys.exit(0)
    cmd, args, flow = sys.argv[1], sys.argv[2:], FlowManager()
    if cmd in ["initiative", "ini"]:
        flow.cmd_initiative(args[0], args[1:])
    elif cmd == "status":
        pending_only = "--pending" in args
        filter_val = next((a for a in args if not a.startswith("-")), None)
        flow.cmd_status(filter_val, pending_only)
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
    elif cmd == "context":
        flow.cmd_context(args[0])
    elif cmd in ["inis", "initiatives"]:
        flow.cmd_initiatives()
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
    elif cmd == "tree":
        flow.cmd_tree(args[0] if args else "status:pending")
    elif cmd == "focus":
        sub = args[0] if args else None
        if sub == "ini":
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
                flow.focus.update_ini(name)
                tasks = flow.tw.export(
                    [f"project:{name}", "status:pending", "limit:1"]
                )
                if tasks:
                    flow.focus.push_task(tasks[0]["uuid"], name)
                    flow.success(
                        f"Focused initiative anchored to: {name} "
                        f"(Task pushed to heap: {tasks[0]['uuid'][:8]})"
                    )
                else:
                    flow.success(f"Focused initiative anchored to: {name}")
            else:
                flow.error("Initiative name required")
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
                state.inis_of_interest = sorted(
                    list(set(state.inis_of_interest + [name]))
                )
                flow.focus.save(state)
                flow.success(f"Added '{name}' to interests.")
            elif action == "remove" and name:
                state.inis_of_interest = [
                    i for i in state.inis_of_interest if i != name
                ]
                flow.focus.save(state)
                flow.success(f"Removed '{name}' from interests.")
            elif action == "list":
                print(
                    "══ Initiatives of Interest ══\n"
                    + (
                        "\n".join(state.inis_of_interest)
                        if state.inis_of_interest
                        else "(empty)"
                    )
                )
            else:
                flow.error("Usage: focus interest [add|remove|list] <name>")
        elif sub == "clear":
            flow.focus.save(FocusState(task_track=[], inis_of_interest=[]))
            flow.success("Focus and task track cleared.")
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
            "  ini <ini> <tasks...>\n"
            "  next [ini]\n"
            "  execute <id>\n"
            "  done <id> [note]\n"
            "  outcome <id> <msg>\n"
            "  reopen <id>\n"
            '  amend <id> [description="..."] [ticket="..."]\n'
            "  note <id> <type> <msg>\n"
            "  ticket <id> <ticket>\n"
            "  inis | status [ini] [--pending]\n"
            "  ponder [project_root] [--all]\n"
            "  focus [ini|task|pop|interest|clear]\n"
            "  tree [ini]"
        )
    else:
        flow.error(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()
