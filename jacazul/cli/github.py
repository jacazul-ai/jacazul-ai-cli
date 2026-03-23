#!/usr/bin/env python
import os
import sys
import json
import subprocess
import argparse
from typing import Optional, Dict, Any

# 🐊 Jacazul GitHub Manager (The Manager)
# Manages hierarchical GitHub tokens in vault.json using IdZoid security.


class GitHubManager:
    def __init__(self):
        self.vault_dir = os.path.expanduser("~/.jacazul-ai")
        self.vault_file = os.path.join(self.vault_dir, "vault.json")
        self.vault_name = "jacazul-vault"
        self.cryptozoid_bin = os.path.expanduser("~/go/bin/cryptozoid")

    def _ensure_vault_dir(self):
        if not os.path.exists(self.vault_dir):
            os.makedirs(self.vault_dir, exist_ok=True)

    def _load_vault(self) -> Dict[str, Any]:
        if not os.path.exists(self.vault_file):
            return {
                "github": {
                    "classic": {"default": None, "named": {}},
                    "owners": {},
                }
            }
        try:
            with open(self.vault_file, "r") as f:
                data = json.load(f)
                # Ensure structure exists
                if "classic" not in data["github"]:
                    data["github"]["classic"] = {"default": None, "named": {}}
                if "owners" not in data["github"]:
                    data["github"]["owners"] = {}
                return data
        except Exception:
            return {
                "github": {
                    "classic": {"default": None, "named": {}},
                    "owners": {},
                }
            }

    def _save_vault(self, data: Dict[str, Any]):
        self._ensure_vault_dir()
        with open(self.vault_file, "w") as f:
            json.dump(data, f, indent=2)

    def _encrypt(self, token: str) -> str:
        """Encrypts token via cryptozoid ec encrypt."""
        try:
            cmd = [
                self.cryptozoid_bin,
                "ec",
                "encrypt",
                "-n",
                self.vault_name,
                "-p",
                self.vault_dir,
                token,
            ]
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"❌ Encryption failed: {e.stderr}", file=sys.stderr)
            sys.exit(1)

    def show_guide(self):
        """Prints the educational GitHub Auth Guide (The Gold)."""
        print("===========================================================")
        print("🐊 JACAZUL GITHUB AUTH GUIDE")
        print("===========================================================")
        print(
            "To automate GitHub interactions, you need a "
            "Personal Access Token (PAT)."
        )

        print("")
        print("1. GO TO: https://github.com/settings/tokens?type=beta")
        print(
            "2. SELECT OWNER: Choose 'jacazul-ai' (for Org) or your username."
        )
        print(
            "3. REPOSITORY ACCESS: 'Only select repositories' is recommended."
        )
        print("4. PERMISSIONS:")
        print("   - Issues: Read and Write")
        print("   - Pull requests: Read and Write")
        print("5. GENERATE & COPY")
        print("")
        print("HOW TO SAVE IN VAULT:")
        print("- For your user:   jacazul-github auth --user <name>")
        print("- For an Org:     jacazul-github auth --org <name>")
        print(
            "- For a Project:  jacazul-github auth --org <name> "
            "--project <name>"
        )

        print("- For a Classic:  jacazul-github auth --classic [name]")
        print("===========================================================")

    def auth(
        self,
        user: Optional[str] = None,
        org: Optional[str] = None,
        project: Optional[str] = None,
        classic: Optional[str] = None,
        classic_mode: bool = False,
    ):
        """Prompts for token and stores it in the hierarchical vault."""
        import getpass

        target = None
        if classic_mode:
            target = f"Classic Token ({classic if classic else 'default'})"
        elif user:
            target = f"User Owner '{user}'"
        elif org:
            if project:
                target = f"Project '{org}/{project}'"
            else:
                target = f"Organization Owner '{org}'"

        if not target:
            self.show_guide()
            return

        print(f"🔐 Setting up token for: {target}")

        if classic_mode:
            print("ℹ️  Link: https://github.com/settings/tokens")
            print(
                "ℹ️  Required Scopes: 'repo' (Full control of private "
                "repositories)"
            )
        else:
            print("ℹ️  Link: https://github.com/settings/tokens?type=beta")
            if user:
                print(f"ℹ️  Instructions: Select '{user}' as Resource owner.")
            elif org:
                print(f"ℹ️  Instructions: Select '{org}' as Resource owner.")

            if project:
                print(
                    f"ℹ️  Repository Access: Select 'Only select "
                    f"repositories' and pick '{project}'."
                )
            else:
                print(
                    "ℹ️  Repository Access: 'All repositories' or 'Only "
                    "select repositories'."
                )

            scopes = "'Issues' and 'Pull Requests' (Read/Write)"
            print(f"ℹ️  Required Scopes: {scopes}")

        token = getpass.getpass("Paste your GitHub Token (hidden): ").strip()

        if not token:
            print("❌ Error: Token cannot be empty.")
            sys.exit(1)

        encrypted_token = self._encrypt(token)
        vault = self._load_vault()

        if classic_mode:
            if classic:
                vault["github"]["classic"]["named"][classic] = encrypted_token
            else:
                vault["github"]["classic"]["default"] = encrypted_token
        else:
            owner = user or org
            if owner not in vault["github"]["owners"]:
                vault["github"]["owners"][owner] = {
                    "token": None,
                    "projects": {},
                }

            if project:
                if "projects" not in vault["github"]["owners"][owner]:
                    vault["github"]["owners"][owner]["projects"] = {}
                vault["github"]["owners"][owner]["projects"][project] = (
                    encrypted_token
                )
            else:
                vault["github"]["owners"][owner]["token"] = encrypted_token

        self._save_vault(vault)
        print(f"✅ Token for {target} successfully blindado in vault.json.")

    def list_vault(self):
        """Lists configured scopes in the vault."""
        vault = self._load_vault()
        print("🐊 Jacazul Vault - Configured GitHub Scopes:")

        classic = vault["github"].get("classic", {})
        if classic.get("default"):
            print("  - [Classic: default] ✓")
        for name in classic.get("named", {}):
            print(f"  - [Classic: {name}] ✓")

        for owner, data in vault["github"]["owners"].items():
            token_status = "✓" if data.get("token") else " "
            print(f"  - [Owner: {owner}] {token_status}")
            projects = data.get("projects", {})
            for project in projects:
                print(f"    - [Project: {project}] ✓")


def main():
    try:
        parser = argparse.ArgumentParser(description="Jacazul GitHub Manager")
        subparsers = parser.add_subparsers(dest="command")

        auth_parser = subparsers.add_parser(
            "auth", help="Store a GitHub token in the vault"
        )
        auth_parser.add_argument("--user", help="User owner name")
        auth_parser.add_argument("--org", help="Organization owner name")
        auth_parser.add_argument(
            "--project", help="Specific project name (requires --org)"
        )
        auth_parser.add_argument(
            "--classic",
            nargs="?",
            const="__DEFAULT__",
            help="Classic token name (optional)",
        )

        subparsers.add_parser(
            "list", help="List configured scopes in the vault"
        )

        args = parser.parse_args()
        manager = GitHubManager()

        if args.command == "auth":
            classic_mode = args.classic is not None
            classic_name = None
            if classic_mode and args.classic != "__DEFAULT__":
                classic_name = args.classic

            manager.auth(
                user=args.user,
                org=args.org,
                project=args.project,
                classic=classic_name,
                classic_mode=classic_mode,
            )
        elif args.command == "list":
            manager.list_vault()
        else:
            parser.print_help()
    except (KeyboardInterrupt, EOFError):
        print("\n\n🐊 Interrupted. Alligator heading back to the swamp...")
        sys.exit(0)


if __name__ == "__main__":
    main()
