#!/home/fpiraz/.jacazul-ai/.venv/bin/python
import os
import sys
import argparse
import orjson
from dataclasses import dataclass, asdict
from typing import Optional

# 🐊 Jacazul Persona Switcher (v1.0.0)
# Manages anchored persona state in persona.json

@dataclass
class PersonaState:
    anchored_persona: str = "jacazul"

    def to_dict(self):
        return asdict(self)

class PersonaManager:
    def __init__(self, data_dir: Optional[str] = None):
        if not data_dir:
            # Fallback to Taskwarrior project data dir
            project_id = os.environ.get("PROJECT_ID", "global")
            home = os.path.expanduser("~/.jacazul-ai")
            data_dir = os.path.join(home, ".task", project_id)
        
        self.file_path = os.path.join(data_dir, "persona.json")
        os.makedirs(data_dir, exist_ok=True)

    def load(self) -> PersonaState:
        if not os.path.exists(self.file_path):
            return PersonaState()
        try:
            with open(self.file_path, "rb") as f:
                data = orjson.loads(f.read())
                return PersonaState(anchored_persona=data.get("anchored_persona", "jacazul"))
        except Exception:
            return PersonaState()

    def save(self, state: PersonaState):
        with open(self.file_path, "wb") as f:
            f.write(orjson.dumps(state.to_dict(), option=orjson.OPT_INDENT_2))

def main():
    parser = argparse.ArgumentParser(description="Switch anchored persona")
    parser.add_argument("name", choices=["jacazul", "cortana"], help="Persona name")
    args = parser.parse_args()

    manager = PersonaManager()
    state = manager.load()
    state.anchored_persona = args.name
    manager.save(state)
    
    print(f"✓ Persona anchored to: {args.name}")

if __name__ == "__main__":
    main()
