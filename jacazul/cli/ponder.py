#!/usr/bin/env python
import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

import re
from datetime import datetime
from typing import Dict, Any, Optional, List
from jacazul.taskwarrior.core import TaskWrapper, FocusManager

# 🐊 ponder (v1.5.2)
# Python port of the tactical Taskwarrior dashboard.


class Dashboard:
    def __init__(
        self,
        project_root: Optional[str] = None,
        show_all: bool = False,
        hide_tip: bool = False,
        use_table: bool = False,
        with_backlog: bool = False,
    ):
        self.project_root = project_root
        self.show_all = show_all
        self.hide_tip = hide_tip
        self.use_table = use_table
        self.with_backlog = with_backlog
        self.tw = TaskWrapper()
        self.focus = FocusManager()
        self.state = self.focus.load()
        # Friendly name for header
        self.project_id = os.environ.get("PROJECT_ID", "standalone")

    def is_interesting(self, plan: str) -> bool:
        if self.show_all:
            return True
        # If a specific root was requested as filter, respect it
        if self.project_root and not plan.startswith(self.project_root):
            return False
        if not self.state.plans_of_interest:
            return True
        if plan == self.state.focused_plan:
            return True
        return plan in self.state.plans_of_interest

    def render(self):
        # 🐊 Prompt as Ad: Agent Guidance
        print("═══════════════════════════════════════════════════")
        print("🐊 AGENT GUIDANCE: DASHBOARD INTENT")
        print("═══════════════════════════════════════════════════")
        print("Running this? You are seeking a GLOBAL view of the project.")
        print("Primary interest is usually the current FOCUS (or 'FOCO').")
        print("ANY reference to focus/foco must use 'tw-flow focus'.")
        print("Use 'tw-flow status' for focus-related updates.")
        print(
            "🛑 STOP and ask the user if you find yourself repeating 'ponder'."
        )
        print("═══════════════════════════════════════════════════\n")

        # Fetch all pending tasks
        all_tasks = self.tw.export(["status:pending"])
        # Filter: project must be a string and not None
        all_tasks = [t for t in all_tasks if isinstance(t.get("project"), str)]
        # Filter backlog plans unless --with-backlog or --all
        if not self.with_backlog and not self.show_all:
            all_tasks = [
                t
                for t in all_tasks
                if not (t.get("backlog") and int(t.get("backlog", 0)) == 1)
            ]

        header = self.project_id
        if self.project_root:
            header += f" (Filter: {self.project_root})"
        print(f"══ TACTICAL VIEW: {header} ══")

        # 1. Context Section (The Brain)
        print("\n [SESSION CONTEXT]")
        focused_plan = self.state.focused_plan or "None"
        focused_task = self.state.focused_task_uuid or "None"
        print(f"  🎯 Focus: {focused_plan} | Task: {focused_task[:8]}")

        if self.state.task_track:
            track = [
                f"{t.get('plan') or t.get('ini')}({t['uuid'][:8]})"
                for t in self.state.task_track[:5]
            ]
            print(f"  🛤️ Track: {' -> '.join(track)}")

        if self.state.plans_of_interest:
            print(f"  ⭐ Interests: {', '.join(self.state.plans_of_interest)}")

        # 2. Pulse Section (Honest Layers)
        interesting_tasks = [
            t for t in all_tasks if self.is_interesting(t["project"])
        ]
        pending_filtered = len(interesting_tasks)
        active_filtered = len([t for t in interesting_tasks if t.get("start")])
        now_str = datetime.now().strftime("%Y%m%dT%H%M%SZ")
        overdue_filtered = len(
            [
                t
                for t in interesting_tasks
                if t.get("due") and t["due"] < now_str
            ]
        )

        comp_today = self.tw.export(["status:completed", "end:today"])
        comp_count = len(
            [
                t
                for t in comp_today
                if isinstance(t.get("project"), str)
                and (
                    not self.project_root
                    or t["project"].startswith(self.project_root)
                )
            ]
        )

        # Archaeology stats
        all_projects = self.tw.run(
            ["_projects"], capture=True
        ).stdout.splitlines()
        archived_count = len(
            [p for p in all_projects if p.endswith("_archive")]
        )
        trashed_count = len(
            [
                p
                for p in all_projects
                if p.endswith("_trash") or p.endswith("_deleted")
            ]
        )

        print("\n [PULSE SUMMARY]")
        print(
            f"  Pulse  | Focused: {focused_plan[:20]:<20} | "
            f"Plans: {len(set(t['project'] for t in interesting_tasks)):<2} | "
            f"Done Today: {comp_count}"
        )
        print(
            f"  Health | Pending: {pending_filtered:<3} | "
            f"Active: {active_filtered:<2} | "
            f"Overdue: {overdue_filtered:<2} (Filtered)"
        )
        print(
            f"  Global | Pending: {len(all_tasks):<3} | "
            f"Active: {len([t for t in all_tasks if t.get('start')]):<2} | "
            f"Registry: {archived_count} Arch / {trashed_count} Trash"
        )
        print("")

        # 3. Task Landscape
        print("[TASK LANDSCAPE]")
        projects = sorted(list(set(t["project"] for t in all_tasks)))
        for p in projects:
            if "_archive" in p or "_trash" in p:
                continue
            if not self.is_interesting(p):
                continue

            p_tasks = [t for t in all_tasks if t["project"] == p]
            p_active = len([t for t in p_tasks if t.get("start")])
            p_ready = len([t for t in p_tasks if not t.get("depends")])
            p_total = len(p_tasks)

            icon = "○"
            if p == self.state.focused_plan:
                icon = "📌"
            elif p_active > 0:
                icon = "⚡"

            print(
                f"  {icon} {p:<35} | "
                f"Active: {p_active:<2} | "
                f"Ready: {p_ready:<2} | "
                f"Total: {p_total:<2}"
            )
        print("")

        # 3. Tactical Readout
        readout_tasks = [
            t
            for t in all_tasks
            if not re.search(r"(_archive|_trash)$", t["project"])
        ]
        readout_tasks = [
            t for t in readout_tasks if self.is_interesting(t["project"])
        ]

        for t in readout_tasks:
            t["sort_status"] = 2 if t.get("start") else 1

        readout_tasks.sort(
            key=lambda x: (x["sort_status"], x.get("urgency", 0)), reverse=True
        )

        if self.use_table:
            self.render_tactical_table(readout_tasks[:15])
        else:
            self.render_tactical_list(readout_tasks[:15])

        self.render_recently_closed()

        if not self.hide_tip:
            print(
                "\nWARN: You are using the standalone 'ponder' command. "
                "Prefer using 'tw-flow ponder' for full workflow integration."
            )

    def render_tactical_list(self, tasks: List[Dict[str, Any]]):
        print("[TACTICAL READOUT]")
        header = (
            "  ST | UUID     | MODE       | "
            "PLAN                               | "
            "DESCRIPTION                                        | URG"
        )
        print(header)
        print("  " + "-" * 130)
        for t in tasks:
            self.render_task_line(t)

    def render_tactical_table(self, tasks: List[Dict[str, Any]]):
        print("\n[TACTICAL READOUT]")
        print("| ST | UUID | MODE | PLAN | DESCRIPTION | URG |")
        print("|---|---|---|---|---|---|")
        for t in tasks:
            uuid = t["uuid"]
            desc = t["description"]
            urgency = t.get("urgency", 0)
            start = t.get("start")
            due = t.get("due")
            project = t.get("project", "[none]")

            status_icon = "○"
            if uuid == self.state.focused_task_uuid:
                status_icon = "🎯"
            elif start:
                status_icon = "⚡"
            elif due and due < datetime.now().strftime("%Y%m%dT%H%M%SZ"):
                status_icon = "!!"

            mode = "--------"
            match = re.search(r"\[([A-Z-]+)\]", desc)
            if match:
                mode = match.group(1)
                desc = re.sub(r"\[[A-Z-]+\]\s*", "", desc)

            # Highlight focused task
            if uuid == self.state.focused_task_uuid:
                desc = f"**{desc}**"

            print(
                f"| {status_icon} | `{uuid[:8]}` | {mode} | "
                f"{project} | {desc[:50]:<50} | {urgency:.1f} |"
            )

    def render_task_line(self, t: Dict[str, Any]):
        uuid = t["uuid"]
        desc = t["description"]
        urgency = t.get("urgency", 0)
        start = t.get("start")
        due = t.get("due")
        project = t.get("project", "[none]")

        status_icon = "○"
        if uuid == self.state.focused_task_uuid:
            status_icon = "🎯"
        elif start:
            status_icon = "⚡"
        elif due and due < datetime.now().strftime("%Y%m%dT%H%M%SZ"):
            status_icon = "!!"

        mode = "--------"
        # Match interaction modes like [EXECUTE], [PLAN], etc.
        match = re.search(r"\[([A-Z-]+)\]", desc)
        if match:
            mode = match.group(1)
            # Remove the mode prefix from description for cleaner view
            desc = re.sub(r"\[[A-Z-]+\]\s*", "", desc)

        print(
            f"  {status_icon:<2} | {uuid[:8]} | {mode:<10} | "
            f"{project:<35} | {desc[:50]:<50} | [{urgency:.1f}]"
        )

    def render_recently_closed(self, max_plans: int = 3):
        pending_projects = set(
            t["project"]
            for t in self.tw.export(["status:pending"])
            if isinstance(t.get("project"), str)
        )

        completed = self.tw.export(["status:completed"])
        completed = [
            t
            for t in completed
            if isinstance(t.get("project"), str)
            and "_archive" not in t["project"]
            and "_trash" not in t["project"]
            and t["project"] not in pending_projects
            and (
                not self.project_root
                or t["project"].startswith(self.project_root)
            )
        ]

        # Group by project, track most recent end date
        by_plan: Dict[str, Dict[str, Any]] = {}
        for t in completed:
            plan = t["project"]
            end = t.get("end", "")
            if plan not in by_plan or end > by_plan[plan]["end"]:
                by_plan[plan] = {"end": end, "tasks": []}
            by_plan[plan]["tasks"].append(t)

        if not by_plan:
            return

        recent = sorted(
            by_plan.items(), key=lambda x: x[1]["end"], reverse=True
        )
        recent = recent[:max_plans]

        print("[RECENTLY CLOSED]")
        for plan, data in recent:
            # Find OUTCOME annotation from any task in this plan
            outcome = None
            for t in sorted(data["tasks"], key=lambda x: x.get("end", "")):
                for ann in t.get("annotations", []):
                    desc = ann.get("description", "")
                    if desc.startswith("OUTCOME:"):
                        outcome = desc.split("OUTCOME:", 1)[1].strip()
            end_date = data["end"][:10] if data["end"] else "?"
            outcome_str = f" — {outcome[:60]}" if outcome else ""
            print(f"  ✓ {plan:<35} [{end_date}]{outcome_str}")
        print("")


def main():
    show_all = "--all" in sys.argv
    use_table = "--table" in sys.argv
    project_root = None
    project_id = os.environ.get("PROJECT_ID")

    for arg in sys.argv[1:]:
        if not arg.startswith("-"):
            # If the filter matches the project ID, ignore it as a filter
            # as it is likely passed by onboarding scripts.
            if arg != project_id:
                project_root = arg
            break

    db = Dashboard(project_root, show_all, use_table=use_table)
    db.render()


if __name__ == "__main__":
    main()
