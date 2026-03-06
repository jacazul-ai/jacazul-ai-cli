#!/usr/bin/env python
import os
import sys
from typing import Optional
from tornado import template
from jacazul.hatch.persona import PersonaManager

# 🐊 Jacazul JIT Prompt Forge - 'engine.py' (v0.5.0)
# Orchestrates JIT prompts with Persona Anchoring.


def hatch_prompt(client: str, persona_override: Optional[str] = None):
    # Paths
    # Now that we are in a package, we need to locate
    # templates relative to this file
    package_dir = os.path.dirname(os.path.abspath(__file__))
    # The root_dir is 2 levels up from jacazul/hatch/engine.py
    root_dir = os.path.dirname(os.path.dirname(package_dir))

    # 1. Determine Anchored Persona
    manager = PersonaManager()
    state = manager.load()
    anchored = persona_override or state.anchored_persona

    # 2. Setup Tornado Template Loader
    template_dir = os.path.join(package_dir, "templates")
    loader = template.Loader(template_dir)

    # 3. Context
    context = {
        "client": client,
        "project_id": os.environ.get(
            "PROJECT_ID", "jacazul-ai_jacazul-ai-cli"
        ),
        "user_pulse": os.environ.get("USER_PULSE", "LAKE_STEADY"),
        "mode": os.environ.get("JACAZUL_MODE", "COUNSELOR"),
        "persona_name": anchored.capitalize(),
        "persona_id": anchored,
        "persona_role": (
            "Tactical AI Companion"
            if anchored == "cortana"
            else "Project navigator and context assistant"
        ),
    }

    try:
        # Generate Jacazul Engine Skill (Shared by all clients via symlinks)
        skill_dir = os.path.join(root_dir, "skills", "jacazul-engine")
        os.makedirs(skill_dir, exist_ok=True)
        rendered_skill = loader.load("gemini_full.md").generate(**context)
        with open(os.path.join(skill_dir, "SKILL.md"), "wb") as f:
            f.write(rendered_skill)

        if os.environ.get("DEBUG"):
            print(f"✓ Hatched Engine Skill: {skill_dir}/SKILL.md")

        if client in ["copilot", "opencode"]:
            # AGENT: Client-Specific Fragment
            agent_dir = os.path.join(root_dir, "agents")
            os.makedirs(agent_dir, exist_ok=True)

            rendered_agent = loader.load("agent_master.md").generate(**context)
            agent_file = f"{anchored}-{client}.md"
            with open(os.path.join(agent_dir, agent_file), "wb") as f:
                f.write(rendered_agent)

            if os.environ.get("DEBUG"):
                print(
                    f"✓ Hatched Agent ({client}, Anchored: {anchored}): "
                    f"{agent_dir}/{agent_file}"
                )

    except Exception as e:
        print(f"❌ Failed to hatch prompt: {e}", file=sys.stderr)
        sys.exit(1)
