#!/home/fpiraz/.jacazul-ai/.venv/bin/python
import os
import shutil
import tempfile
import subprocess
import unittest
from typing import Tuple

class JacazulTest(unittest.TestCase):
    """Base class for Jacazul tool tests with strict environment isolation."""
    
    @classmethod
    def setUpClass(cls):
        # Base paths for tools
        # The project_root is the parent of the root 'tests' directory
        cls.test_dir_path = os.path.dirname(__file__)
        cls.project_root = os.path.abspath(os.path.join(cls.test_dir_path, ".."))
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
        self.env["PYTHONPATH"] = f"{self.project_root}:{self.env.get('PYTHONPATH', '')}"
        # Prevent Jacazul scripts from looking at real user config
        self.env["TASKRC"] = os.path.join(self.test_dir, ".taskrc")
        
        # Create a dummy .taskrc to avoid Taskwarrior complaints
        with open(self.env["TASKRC"], "w") as f:
            f.write(f"data.location={self.taskdata}\n")
            f.write("confirmation=no\n")
            f.write("uda.externalid.type=string\n")
            f.write("uda.externalid.label=Ticket\n")

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
