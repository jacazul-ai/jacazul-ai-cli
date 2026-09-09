import argparse

from jacazul.hatch.engine import HATCH_TARGETS, hatch_prompt

# 🐊 jacazul-hatch CLI Entry Point
# Bridges the CLI to the hatch engine logic.


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser for prompt generation."""
    parser = argparse.ArgumentParser(description="Jacazul Prompt Hatchery")
    parser.add_argument(
        "--target",
        "--client",
        dest="target",
        required=True,
        choices=HATCH_TARGETS,
        help="target harness/provider, or all supported targets",
    )
    parser.add_argument("--persona", help="Manual persona override")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    hatch_prompt(args.target, args.persona)


if __name__ == "__main__":
    main()
