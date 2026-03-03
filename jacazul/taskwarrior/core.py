import os
import subprocess
import orjson
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict

# 🐊 tw_expert Core Module (v1.4.0)
# Centralized logic for Environment, Taskwarrior, and Focus management.

class Environment:
    @staticmethod
    def get_mode() -> str:
        return os.environ.get("JACAZUL_MODE", "SANDBOXED")

    @staticmethod
    def get_project_id() -> str:
        return os.environ.get("PROJECT_ID", "global")

    @staticmethod
    def get_jacazul_home() -> str:
        return os.path.expanduser("~/.jacazul-ai")

    @staticmethod
    def get_taskrc() -> str:
        if "TASKRC" in os.environ:
            return os.environ["TASKRC"]
        if Environment.get_mode() == "UNHINGED":
            return os.path.join(Environment.get_jacazul_home(), ".taskrc")
        return os.path.expanduser("~/.taskrc")

    @staticmethod
    def get_taskdata() -> str:
        # If TASKDATA is explicitly set in env, we MUST respect it (e.g. tests)
        if "TASKDATA" in os.environ:
            return os.environ["TASKDATA"]
        
        project_id = Environment.get_project_id().split(":")[0]
        if Environment.get_mode() == "UNHINGED":
            return os.path.join(Environment.get_jacazul_home(), ".task", project_id)
        return os.path.join(os.path.expanduser("~/.task"), project_id)

    @staticmethod
    def get_real_task_bin() -> str:
        if "JACAZUL_REAL_TASK" in os.environ:
            return os.environ["JACAZUL_REAL_TASK"]
        
        try:
            # We want to avoid our own scripts/task wrapper
            res = subprocess.run(["which", "-a", "task"], capture_output=True, text=True, check=False)
            bins = res.stdout.strip().split("\n")
            for b in bins:
                if "scripts/task" not in b:
                    return b
        except Exception:
            pass
        return "/usr/bin/task"

class TaskWrapper:
    def __init__(self):
        self.bin = Environment.get_real_task_bin()
        self.rc = Environment.get_taskrc()
        self.data = Environment.get_taskdata()
        os.makedirs(self.data, exist_ok=True)

    def run(self, args: List[str], capture: bool = True, verbose: Optional[str] = "new-id") -> subprocess.CompletedProcess:
        cmd = [self.bin, f"rc:{self.rc}", f"rc.data.location={self.data}"]
        if verbose:
            cmd.append(f"rc.verbose={verbose}")
        cmd.extend(args)
        
        res = subprocess.run(
            cmd, 
            capture_output=capture, 
            text=True, 
            env=os.environ.copy(),
            check=False
        )
        return res

    def export(self, filter_args: List[str] = None) -> List[Dict[str, Any]]:
        args = filter_args or []
        if "export" not in args:
            args.append("export")
        res = self.run(args, capture=True, verbose="no")
        if res.returncode != 0:
            return []
        try:
            return orjson.loads(res.stdout)
        except Exception:
            return []

@dataclass
class FocusState:
    focused_ini: Optional[str] = None
    focused_task_uuid: Optional[str] = None
    task_track: List[Dict[str, str]] = None
    inis_of_interest: List[str] = None

    def to_dict(self):
        return asdict(self)

class FocusManager:
    def __init__(self):
        self.data_dir = Environment.get_taskdata()
        self.file_path = os.path.join(self.data_dir, "focus.json")

    def load(self) -> FocusState:
        if not os.path.exists(self.file_path):
            return FocusState(task_track=[], inis_of_interest=[])
        
        try:
            with open(self.file_path, "rb") as f:
                data = orjson.loads(f.read())
                return FocusState(
                    focused_ini=data.get("focused_ini"),
                    focused_task_uuid=data.get("focused_task_uuid"),
                    task_track=data.get("task_track", []),
                    inis_of_interest=data.get("inis_of_interest", [])
                )
        except Exception:
            return FocusState(task_track=[], inis_of_interest=[])

    def save(self, state: FocusState):
        os.makedirs(self.data_dir, exist_ok=True)
        with open(self.file_path, "wb") as f:
            f.write(orjson.dumps(state.to_dict(), option=orjson.OPT_INDENT_2))

    def update_ini(self, name: str):
        state = self.load()
        state.focused_ini = name
        self.save(state)

    def push_task(self, uuid: str, ini: str):
        state = self.load()
        state.task_track = [t for t in state.task_track if t.get("uuid") != uuid]
        state.task_track.insert(0, {"uuid": uuid, "ini": ini})
        state.focused_task_uuid = uuid
        state.focused_ini = ini
        self.save(state)

    def pop_task(self) -> Optional[Dict[str, str]]:
        state = self.load()
        if not state.task_track:
            state.focused_task_uuid = None
            state.focused_ini = None
            self.save(state)
            return None
        
        state.task_track.pop(0)
        if state.task_track:
            top = state.task_track[0]
            state.focused_task_uuid = top["uuid"]
            state.focused_ini = top["ini"]
        else:
            state.focused_task_uuid = None
            state.focused_ini = None
        
        self.save(state)
        return state.task_track[0] if state.task_track else None
