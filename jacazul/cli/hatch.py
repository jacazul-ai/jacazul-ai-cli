import argparse
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

from jacazul.hatch.engine import hatch_prompt

# 🐊 jacazul-hatch CLI Entry Point
# Bridges the CLI to the hatch engine logic.


def main():
    parser = argparse.ArgumentParser(description="Jacazul Prompt Hatchery")
    parser.add_argument(
        "--client",
        required=True,
        choices=["gemini", "copilot", "opencode", "claude"],
    )
    parser.add_argument("--persona", help="Manual persona override")
    args = parser.parse_args()

    hatch_prompt(args.client, args.persona)


if __name__ == "__main__":
    main()
