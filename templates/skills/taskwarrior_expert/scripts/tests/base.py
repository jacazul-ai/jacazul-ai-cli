import unittest
import os
import shutil
import tempfile
import subprocess
from typing import Tuple

class JakaTest(unittest.TestCase):
    """Base class for Jaka tool tests with strict environment isolation."""
    
    @classmethod
    def setUpClass(cls):
        # Base paths for tools
        cls.script_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        cls.taskp = os.path.join(cls.script_dir, "taskp")
        cls.tw_flow = os.path.join(cls.script_dir, "tw-flow")
        cls.ponder = os.path.join(cls.script_dir, "ponder")
        cls.project_root = os.path.abspath(os.path.join(cls.script_dir, "../../../.."))

    def setUp(self):
        # Create a unique temporary directory for Taskwarrior data
        self.test_dir = tempfile.mkdtemp(prefix="jaka_test_")
        self.taskdata = os.path.join(self.test_dir, "data")
        os.makedirs(self.taskdata, exist_ok=True)
        
        # Prepare environment overrides
        self.env = os.environ.copy()
        self.env["TASKDATA"] = self.taskdata
        self.env["PROJECT_ID"] = "test_project"
        # Ensure PYTHONPATH includes the script directory for tw_expert import
        self.env["PYTHONPATH"] = f"{self.script_dir}:{self.env.get('PYTHONPATH', '')}"
        # Prevent Jaka scripts from looking at real user config
        self.env["TASKRC"] = os.path.join(self.test_dir, ".taskrc")
        
        # Create a dummy .taskrc to avoid Taskwarrior complaints
        with open(self.env["TASKRC"], "w") as f:
            f.write(f"data.location={self.taskdata}\nconfirmation=no\n")

    def tearDown(self):
        # Forcefully remove temporary test data
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def run_cmd(self, cmd: str, check: bool = False) -> Tuple[str, str, int]:
        """Run a command within the isolated test environment."""
        # Ensure the command uses our wrappers if they aren't absolute paths
        res = subprocess.run(
            cmd,
            shell=True,
            env=self.env,
            capture_output=True,
            text=True,
            check=check
        )
        return res.stdout.strip(), res.stderr.strip(), res.returncode
