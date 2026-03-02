#!/home/fpiraz/.jacazul-ai/.venv/bin/python
import os
import sys
import argparse
from typing import Optional
from tornado import template
from persona_switch import PersonaManager

# 🐊 Jacazul JIT Prompt Forge - 'hatch.py' (v0.4.0)
# Orchestrates JIT prompts with Persona Anchoring.


def hatch_prompt(client: str, persona_override: Optional[str] = None):
    # Paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(os.path.dirname(script_dir))

    # 1. Determine Anchored Persona
    manager = PersonaManager()
    state = manager.load()
    anchored = persona_override or state.anchored_persona

    # 2. Setup Tornado Template Loader
    template_dir = os.path.join(script_dir, "templates")
    loader = template.Loader(template_dir)

    # 3. Context
    context = {
        "client": client,
        "project_id": os.environ.get(
            "PROJECT_ID", "jacazul-ai_jacazul-ai-cli"
        ),
        "user_pulse": os.environ.get("USER_PULSE", "LAKE_STEADY"),
        "mode": os.environ.get("JACAZUL_MODE", "COMPANION"),
        "persona_name": anchored.capitalize(),
        "persona_id": anchored,
        "persona_role": (
            "Tactical AI Companion" if anchored == "cortana"
            else "Project navigator and context assistant"
        )
    }

    try:
        if client == "gemini":
            # GEMINI: Unified Full Context
            output_dir = os.path.join(root_dir, "skills", "jacazul-gemini")
            os.makedirs(output_dir, exist_ok=True)

            # Select Master Template based on anchored persona
            # In the future, we can have gemini_full_cortana.tmpl etc.
            # For now, we use the unified one which includes both.
            rendered = loader.load("gemini_full.md").generate(**context)
            with open(os.path.join(output_dir, "SKILL.md"), "wb") as f:
                f.write(rendered)

            if os.environ.get("DEBUG"):
                print(
                    f"✓ Hatched Gemini Full Context (Anchored: {anchored}): "
                    f"{output_dir}/SKILL.md"
                )

        elif client in ["copilot", "opencode"]:
            # AGENT: Client-Specific Fragment
            agent_dir = os.path.join(root_dir, "agents")
            os.makedirs(agent_dir, exist_ok=True)

            rendered_agent = loader.load("agent_master.md").generate(**context)
            agent_file = f"{anchored}-{client}.md"
            with open(os.path.join(agent_dir, agent_file), "wb") as f:
                f.write(rendered_agent)

            # Generate Partial Skill
            skill_dir = os.path.join(root_dir, "skills", "jacazul-partial")
            os.makedirs(skill_dir, exist_ok=True)
            rendered_skill = loader.load(
                "skill_partial.md"
            ).generate(**context)
            with open(os.path.join(skill_dir, "SKILL.md"), "wb") as f:
                f.write(rendered_skill)

            if os.environ.get("DEBUG"):
                print(
                    f"✓ Hatched Agent ({client}, Anchored: {anchored}): "
                    f"{agent_dir}/{agent_file}"
                )
                print(f"✓ Hatched Partial Skill: {skill_dir}/SKILL.md")

    except Exception as e:
        print(f"❌ Failed to hatch prompt: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Jacazul Prompt Hatchery")
    parser.add_argument(
        "--client", required=True, choices=["gemini", "copilot", "opencode"]
    )
    parser.add_argument("--persona", help="Manual persona override")
    args = parser.parse_args()

    hatch_prompt(args.client, args.persona)


if __name__ == "__main__":
    main()
