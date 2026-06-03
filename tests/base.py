#!/home/fpiraz/.jacazul-ai/.venv/bin/python
import os
import shutil
import tempfile
import subprocess
import unittest
import sys
from typing import Tuple


class JacazulTest(unittest.TestCase):
    """Base class for Jacazul tool tests with strict environment isolation."""

    @classmethod
    def setUpClass(cls):
        # Base paths for tools
        # The project_root is the parent of the root 'tests' directory
        cls.test_dir_path = os.path.dirname(__file__)
        cls.project_root = os.path.abspath(
            os.path.join(cls.test_dir_path, "..")
        )
        cls.cli_dir = os.path.join(cls.project_root, "jacazul/cli")

        cls.taskp = os.path.join(cls.cli_dir, "taskp.py")
        cls.tw_flow = os.path.join(cls.cli_dir, "flow.py")
        cls.ponder = os.path.join(cls.cli_dir, "ponder.py")

    def setUp(self):
        # Create a unique temporary directory for Taskwarrior data
        self.test_dir = tempfile.mkdtemp(prefix="jacazul_test_")
        self.taskdata = os.path.join(self.test_dir, "data")
        os.makedirs(self.taskdata, exist_ok=True)

        # Prepare environment overrides
        self.env = os.environ.copy()
        self.env["TASKDATA"] = self.taskdata
        self.env["PROJECT_ID"] = "test_project"
        # Ensure PYTHONPATH includes the project root for jacazul.* imports
        self.env["PYTHONPATH"] = (
            f"{self.project_root}{os.pathsep}{self.env.get('PYTHONPATH', '')}"
        )
        # Prevent Jacazul scripts from looking at real user config
        self.env["TASKRC"] = os.path.join(self.test_dir, ".taskrc")
        self.env["JACAZUL_HOME"] = self.test_dir
        # Isolate tests from session context
        self.env.pop("JACAZUL_SESSION_ID", None)

        # Create a dummy .taskrc to avoid Taskwarrior complaints
        with open(self.env["TASKRC"], "w") as f:
            f.write(f"data.location={self.taskdata}\n")
            f.write("confirmation=no\n")
            f.write("uda.externalid.type=string\n")
            f.write("uda.externalid.label=Ticket\n")
            f.write("uda.backlog.type=numeric\n")
            f.write("uda.backlog.label=Backlog\n")
            f.write("uda.backlog.default=0\n")
            f.write("uda.archive.type=numeric\n")
            f.write("uda.archive.label=Archive\n")
            f.write("uda.archive.default=0\n")
            f.write("uda.project_weight.type=numeric\n")
            f.write("uda.project_weight.label=Weight\n")
            f.write("uda.project_weight.default=0\n")
            f.write("uda.phase.type=string\n")
            f.write("uda.phase.label=Phase\n")
            f.write("uda.operational_ini.type=string\n")
            f.write("uda.operational_ini.label=Operational Ini\n")

    def tearDown(self):
        # Forcefully remove temporary test data
        if os.path.exists(self.test_dir):
            if os.name == "nt":
                import stat
                def remove_readonly(func, path, excinfo):
                    try:
                        os.chmod(path, stat.S_IWRITE)
                        func(path)
                    except Exception:
                        pass
                shutil.rmtree(self.test_dir, onexc=remove_readonly)
            else:
                shutil.rmtree(self.test_dir)

    def run_cmd(
        self, cmd: str, env: dict = None, check: bool = False
    ) -> Tuple[str, str, int]:
        """Run a command within the isolated test environment."""
        import shlex
        import re
        run_env = self.env.copy()
        if env:
            run_env.update(env)

        # Parse inline environment variables like KEY=VAL at the start of the command
        # e.g., "JACAZUL_TESTING=false tw-flow done ..."
        while True:
            match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)=((?:'[^']*')|(?:\"[^\"]*\")|[^\s]*)\s+(.*)$", cmd)
            if match:
                key, val, rest = match.groups()
                if len(val) >= 2 and val[0] in ("'", '"') and val[-1] == val[0]:
                    val = val[1:-1]
                run_env[key] = val
                cmd = rest.strip()
            else:
                break

        # On Windows, prepend python interpreter to local scripts
        if os.name == "nt":
            for script_path in [self.tw_flow, self.taskp, self.ponder]:
                if script_path in cmd and not cmd.startswith(f'"{sys.executable}"'):
                    cmd = cmd.replace(script_path, f'"{sys.executable}" "{script_path}"')

        if os.name == "nt":
            # On Windows cmd.exe does not understand single quotes for arguments.
            # Convert single quotes to double quotes, parse with posix=False to preserve
            # backslashes in Windows paths, and strip the outer quotes manually.
            cmd_replaced = cmd.replace("'", '"')
            tokens = shlex.split(cmd_replaced, posix=False)
            args = []
            for t in tokens:
                if len(t) >= 2 and t.startswith('"') and t.endswith('"'):
                    args.append(t[1:-1])
                else:
                    args.append(t)
            
            # Resolve the binary path in PATH (finds scripts like task.cmd, etc.)
            import shutil
            resolved_bin = shutil.which(args[0], path=run_env.get("PATH"))
            if resolved_bin:
                args[0] = resolved_bin
            shell = False
        else:
            args = cmd
            shell = True

        res = subprocess.run(
            args,
            shell=shell,
            cwd=self.test_dir,
            env=run_env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=check,
        )
        return res.stdout.strip(), res.stderr.strip(), res.returncode
