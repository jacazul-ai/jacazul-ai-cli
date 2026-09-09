#!/usr/bin/env python
import os
import sys
from pathlib import Path
from typing import Optional

from tornado import template

from jacazul.hatch.persona import PersonaManager

# 🐊 Jacazul JIT Prompt Forge - 'engine.py' (v0.6.0)
# Generates one shared engine and optional target-specific adapters.

HATCH_TARGETS = (
    "gemini",
    "copilot",
    "opencode",
    "claude",
    "pi",
    "openai",
    "all",
)

ALL_TARGETS = (
    "gemini",
    "copilot",
    "opencode",
    "claude",
    "pi",
    "openai",
)
AGENT_TARGETS = frozenset({"copilot", "opencode"})
PERSONA_ROLES = {
    "codana": "Tactical AI Companion",
    "codama": "Tactical AI Companion",
    "arnalbam": "High-octane bodybuilding motivator",
    "atena": "Wise pedagogical mentor",
}
DEFAULT_PERSONA_ROLE = "Project navigator and context assistant"


def _resolve_targets(target: str) -> tuple[str, ...]:
    """Resolve one target or the complete supported target set."""
    if target == "all":
        return ALL_TARGETS
    if target not in ALL_TARGETS:
        supported = ", ".join(HATCH_TARGETS)
        raise ValueError(
            f"Unsupported hatch target '{target}'. Use: {supported}"
        )
    return (target,)


def _context(
    persona: str, target: Optional[str] = None
) -> dict[str, str | None]:
    """Build the template context for the shared engine or an adapter."""
    return {
        "client": target,
        "project_id": os.environ.get(
            "PROJECT_ID", "jacazul-ai_jacazul-ai-cli"
        ),
        "user_pulse": os.environ.get("USER_PULSE", "LAKE_STEADY"),
        "mode": os.environ.get("JACAZUL_MODE", "COUNSELOR"),
        "chat_lang": os.environ.get("JACAZUL_CHAT_LANG", "pt-br"),
        "data_lang": os.environ.get("JACAZUL_DATA_LANG", "en"),
        "persona_name": persona.capitalize(),
        "persona_id": persona,
        "persona_role": PERSONA_ROLES.get(persona, DEFAULT_PERSONA_ROLE),
    }


def hatch_prompt(
    client: str,
    persona_override: Optional[str] = None,
    output_root: Optional[str | os.PathLike[str]] = None,
) -> None:
    """Generate the shared engine and adapters for the selected target."""
    targets = _resolve_targets(client)
    package_dir = Path(__file__).resolve().parent
    root_dir = Path(output_root) if output_root else package_dir.parents[1]

    manager = PersonaManager()
    state = manager.load()
    anchored = persona_override or state.anchored_persona

    loader = template.Loader(str(package_dir / "templates"))
    shared_context = _context(anchored)

    try:
        # Generate the neutral engine exactly once for every invocation.
        skill_dir = root_dir / "skills" / "jacazul-engine"
        skill_dir.mkdir(parents=True, exist_ok=True)
        rendered_skill = loader.load("gemini_full.md").generate(
            **shared_context
        )
        skill_path = skill_dir / "SKILL.md"
        skill_path.write_bytes(rendered_skill)

        if os.environ.get("DEBUG"):
            print(f"✓ Hatched Engine Skill: {skill_path}")

        for target in targets:
            if target not in AGENT_TARGETS:
                continue

            agent_dir = root_dir / "agents"
            agent_dir.mkdir(parents=True, exist_ok=True)
            agent_context = _context(anchored, target)
            rendered_agent = loader.load("agent_master.md").generate(
                **agent_context
            )
            # OpenCode has one executable agent identity.  The anchored
            # persona is rendered into its system prompt, not its agent name.
            filename = (
                "jacazul-opencode.md"
                if target == "opencode"
                else f"{anchored}-{target}.md"
            )
            agent_path = agent_dir / filename
            if target == "opencode":
                for legacy_path in agent_dir.glob("*-opencode.md"):
                    if legacy_path != agent_path:
                        legacy_path.unlink()
            agent_path.write_bytes(rendered_agent)

            if os.environ.get("DEBUG"):
                print(
                    f"✓ Hatched Agent ({target}, Anchored: {anchored}): "
                    f"{agent_path}"
                )

    except Exception as error:
        print(f"❌ Failed to hatch prompt: {error}", file=sys.stderr)
        sys.exit(1)
