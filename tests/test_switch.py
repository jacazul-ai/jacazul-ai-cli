#!/home/fpiraz/.jacazul-ai/.venv/bin/python
import unittest
import os
import shutil
import tempfile
import orjson
from jacazul.hatch.persona import PersonaManager, PersonaState

class TestPersonaSwitch(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.manager = PersonaManager(data_dir=self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_default_state(self):
        state = self.manager.load()
        self.assertEqual(state.anchored_persona, "jacazul")

    def test_save_and_load(self):
        state = self.manager.load()
        state.anchored_persona = "cortana"
        self.manager.save(state)
        
        new_state = self.manager.load()
        self.assertEqual(new_state.anchored_persona, "cortana")

    def test_json_structure(self):
        state = PersonaState(anchored_persona="cortana")
        self.manager.save(state)
        
        with open(os.path.join(self.test_dir, "persona.json"), "rb") as f:
            data = orjson.loads(f.read())
            self.assertEqual(data["anchored_persona"], "cortana")

if __name__ == "__main__":
    unittest.main()
