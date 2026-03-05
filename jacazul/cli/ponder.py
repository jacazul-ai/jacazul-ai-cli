#!/usr/bin/env python
import os
import sys
import re
from datetime import datetime
from typing import Dict, Any, Optional, List
from jacazul.taskwarrior.core import TaskWrapper, FocusManager

# 🐊 ponder (v1.5.1)
# Python port of the tactical Taskwarrior dashboard.


class Dashboard:
    def __init__(
        self,
        project_root: Optional[str] = None,
        show_all: bool = False,
        hide_tip: bool = False,
        use_table: bool = False,
    ):
        self.project_root = project_root
        self.show_all = show_all
        self.hide_tip = hide_tip
        self.use_table = use_table
        self.tw = TaskWrapper()
        self.focus = FocusManager()
        self.state = self.focus.load()
        # Friendly name for header
        self.project_id = os.environ.get("PROJECT_ID", "standalone")

    def is_interesting(self, ini: str) -> bool:
        if self.show_all:
            return True
        # If a specific root was requested as filter, respect it
        if self.project_root and not ini.startswith(self.project_root):
            return False
        if not self.state.inis_of_interest:
            return True
        if ini == self.state.focused_ini:
            return True
        return ini in self.state.inis_of_interest

    def render(self):
        # Fetch all pending tasks
        all_tasks = self.tw.export(["status:pending"])
        # Filter: project must be a string and not None
        all_tasks = [t for t in all_tasks if isinstance(t.get("project"), str)]

        header = self.project_id
        if self.project_root:
            header += f" (Filter: {self.project_root})"
        print(f"══ TACTICAL VIEW: {header} ══")

        # 1. Pulse Summary
        pending_count = len(all_tasks)
        active_count = len([t for t in all_tasks if t.get("start")])
        now_str = datetime.now().strftime("%Y%m%dT%H%M%SZ")
        overdue_count = len(
            [t for t in all_tasks if t.get("due") and t["due"] < now_str]
        )

        # Completed today (respect optional filter)
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

        print(
            f"Pulse: Pending ({pending_count}) | "
            f"Active ({active_count}) | "
            f"Overdue ({overdue_count}) | "
            f"Done Today ({comp_count})\n"
        )

        # 2. Initiative Landscape
        print("[INITIATIVE LANDSCAPE]")
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
            if p == self.state.focused_ini:
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

        if not self.hide_tip:
            print(
                "\nWARN: You are using the standalone 'ponder' command. "
                "Prefer using 'tw-flow ponder' for full workflow integration."
            )

    def render_tactical_list(self, tasks: List[Dict[str, Any]]):
        print("[TACTICAL READOUT]")
        print(
            "  ST | UUID     | MODE       | INITIATIVE                | "
            "DESCRIPTION                                        | URG"
        )
        print("  " + "-" * 120)
        for t in tasks:
            self.render_task_line(t)

    def render_tactical_table(self, tasks: List[Dict[str, Any]]):
        print(f"\n[TACTICAL READOUT]")
        print("| ST | UUID | MODE | INITIATIVE | DESCRIPTION | URG |")
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
                f"{project[:25]:<25} | {desc[:50]:<50} | {urgency:.1f} |"
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
            f"{project[:25]:<25} | {desc[:50]:<50} | [{urgency:.1f}]"
        )


def main():
    show_all = "--all" in sys.argv
    use_table = "--table" in sys.argv
    project_root = None
    for arg in sys.argv[1:]:
        if not arg.startswith("-"):
            project_root = arg
            break

    db = Dashboard(project_root, show_all, use_table=use_table)
    db.render()


if __name__ == "__main__":
    main()
