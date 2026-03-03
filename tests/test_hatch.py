#!/home/fpiraz/.jacazul-ai/.venv/bin/python
import unittest
import os
import shutil
import tempfile
from jacazul.hatch.engine import hatch_prompt
from jacazul.hatch.persona import PersonaManager, PersonaState

class TestHatchEngine(unittest.TestCase):
    def setUp(self):
        self.test_root = tempfile.mkdtemp()
        self.script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # We need to mock the PROJECT_ROOT logic in hatch.py or set environment
        os.environ["PROJECT_ID"] = "test_project"
        
        # Link templates to test dir for Tornado loader
        # Actually, hatch.py uses script_dir for loader, so we just check outputs
        self.manager = PersonaManager(data_dir=self.test_root)

    def tearDown(self):
        shutil.rmtree(self.test_root)

    def test_hatch_gemini_parity(self):
        # This is more of an integration test
        # We check if artifacts are created in the right place
        # The actual hatch.py uses root_dir = script_dir/../..
        # For testing purposes, we'll just run it and check if it crashes
        try:
            hatch_prompt("gemini", persona_override="jacazul")
            hatch_prompt("copilot", persona_override="cortana")
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"Hatching failed: {e}")

if __name__ == "__main__":
    unittest.main()
