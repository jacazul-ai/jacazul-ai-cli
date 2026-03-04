import argparse
from jacazul.hatch.persona import PersonaManager

# 🐊 jacazul-persona CLI Entry Point
# Bridges the CLI to the persona management logic.


def main():
    parser = argparse.ArgumentParser(description="Switch anchored persona")
    parser.add_argument(
        "name", choices=["jacazul", "cortana"], help="Persona name"
    )
    args = parser.parse_args()

    manager = PersonaManager()
    state = manager.load()
    state.anchored_persona = args.name
    manager.save(state)

    print(f"✓ Persona anchored to: {args.name}")


if __name__ == "__main__":
    main()
