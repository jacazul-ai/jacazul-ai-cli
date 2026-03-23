#!/usr/bin/env python
import os
import subprocess
import sys
import json
import re
from typing import Optional, Tuple
from jacazul.taskwarrior.core import TaskWrapper

# 🐊 Jacazul GitHub Broker (The Caboco)
# Handles synchronization between Taskwarrior and GitHub via IdZoid security.


class GitHubBroker:
    def __init__(self):
        self.tw = TaskWrapper()
        self.vault_dir = os.path.expanduser("~/.jacazul-ai")
        self.vault_name = "jacazul-vault"
        self.vault_file = os.path.join(self.vault_dir, "vault.json")
        self.github_vault_legacy = os.path.join(self.vault_dir, "github.enc")
        self.cryptozoid_bin = os.path.expanduser("~/go/bin/cryptozoid")

    def _decrypt(self, encrypted_blob: str) -> Optional[str]:
        """Decrypts a blob using cryptozoid ec decrypt."""
        if not os.path.exists(self.cryptozoid_bin):
            return None

        try:
            cmd = [
                self.cryptozoid_bin,
                "ec",
                "decrypt",
                "-n",
                self.vault_name,
                "-p",
                self.vault_dir,
                encrypted_blob,
            ]

            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True
            )
            return result.stdout.strip()
        except Exception:
            return None

    def _infer_context(self) -> Tuple[Optional[str], Optional[str]]:
        """Infers Org and Project from the current git remote."""
        try:
            result = subprocess.run(
                ["git", "remote", "-v"],
                capture_output=True,
                text=True,
                check=True,
            )
            # Match SSH or HTTPS patterns
            # git@github.com:org/repo.git or https://github.com/org/repo.git
            pattern = r"github\.com[:/](?P<org>[^/]+)/(?P<repo>[^.\s]+)"
            match = re.search(pattern, result.stdout)
            if match:
                return match.group("org"), match.group("repo")
        except Exception:
            pass
        return None, None

    def _get_token(
        self, org: Optional[str] = None, project: Optional[str] = None
    ) -> Optional[str]:
        """Resolves the best GitHub token from vault.json or legacy vault."""

        # 1. Try vault.json (Hierarchical)
        if os.path.exists(self.vault_file):
            try:
                with open(self.vault_file, "r") as f:
                    vault = json.load(f).get("github", {})

                # Precedence: Project > Org > User > Classic Default
                owners = vault.get("owners", {})

                # Check Project level
                if org and project:
                    proj_token = (
                        owners.get(org, {}).get("projects", {}).get(project)
                    )
                    if proj_token:
                        return self._decrypt(proj_token)

                # Check Org/Owner level
                if org:
                    org_token = owners.get(org, {}).get("token")
                    if org_token:
                        return self._decrypt(org_token)

                # Check Classic Default
                classic_default = vault.get("classic", {}).get("default")
                if classic_default:
                    return self._decrypt(classic_default)

            except Exception as e:
                print(
                    f"⚠️ Warning: Failed to read vault.json: {e}",
                    file=sys.stderr,
                )

        # 2. Try legacy github.enc
        if os.path.exists(self.github_vault_legacy):
            try:
                with open(self.github_vault_legacy, "r") as f:
                    blob = f.read().strip()
                return self._decrypt(blob)
            except Exception:
                pass

        return None

    def _run_gh(
        self, args: list, repo: Optional[str] = None
    ) -> subprocess.CompletedProcess:
        """Runs a gh command with the best resolved token injected."""

        # Infer context if repo is provided
        target_org = None
        target_proj = None

        if repo:
            if "/" in repo:
                target_org, target_proj = repo.split("/", 1)
        else:
            # Try to infer from current git environment
            target_org, target_proj = self._infer_context()
            if target_org and target_proj:
                repo = f"{target_org}/{target_proj}"

        token = self._get_token(org=target_org, project=target_proj)

        env = os.environ.copy()
        if token:
            env["GH_TOKEN"] = token

        cmd = ["gh"] + args
        if repo:
            cmd += ["--repo", repo]

        return subprocess.run(cmd, capture_output=True, text=True, env=env)

    def sync_issue(self, issue_id: str, repo: Optional[str] = None):
        """
        Syncs a GitHub issue status with Taskwarrior and closes task if needed.
        """
        # Strip # if present
        clean_id = issue_id.lstrip("#")

        # Resolve repo for display
        display_repo = repo
        if not display_repo:
            org, proj = self._infer_context()
            if org and proj:
                display_repo = f"{org}/{proj}"

        print(
            f"🐊 Syncing issue #{clean_id} from "
            f"{display_repo or 'current repo'}..."
        )

        result = self._run_gh(
            ["issue", "view", clean_id, "--json", "state,title"], repo=repo
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            state = data.get("state", "UNKNOWN").upper()
            title = data.get("title", "")
            print(f"✅ GitHub Status: {state} | {title}")

            if state == "CLOSED":
                # Find local tasks with this externalid
                tasks = self.tw.export(
                    [f"externalid:#{clean_id}", "status:pending"]
                )
                if not tasks:
                    # Try without # just in case
                    tasks = self.tw.export(
                        [f"externalid:{clean_id}", "status:pending"]
                    )

                if tasks:
                    print(
                        f"🐊 Found {len(tasks)} pending task(s) for this "
                        "ticket. Closing..."
                    )

                    for task in tasks:
                        uuid = task["uuid"]
                        outcome = (
                            f"Automatically closed by Broker sync. "
                            f"GitHub issue #{clean_id} is CLOSED."
                        )
                        # Record outcome first (MANDATORY in tw-flow done)
                        self.tw.run(
                            [uuid, "modify", f"annotation:OUTCOME: {outcome}"]
                        )
                        self.tw.run([uuid, "modify", "status:completed"])
                        print(f"✅ Task {uuid[:8]} closed locally.")
                else:
                    print("ℹ️ No pending local tasks found for this ticket.")
        else:
            print(f"❌ Error fetching issue: {result.stderr}", file=sys.stderr)

    def open_issue(
        self,
        title: str,
        body: Optional[str] = None,
        repo: Optional[str] = None,
    ):
        """Opens a new GitHub issue."""
        args = ["issue", "create", "--title", title]
        if body:
            args += ["--body", body]

        result = self._run_gh(args, repo=repo)
        if result.returncode == 0:
            # gh issue create prints the URL of the new issue
            issue_url = result.stdout.strip()
            print(f"✅ Issue created: {issue_url}")
            return issue_url
        else:
            print(
                f"❌ Failed to create issue: {result.stderr}", file=sys.stderr
            )
            return None

    def close_issue(
        self,
        issue_id: str,
        repo: Optional[str] = None,
        comment: Optional[str] = None,
    ):
        """Closes a GitHub issue with an optional comment."""
        clean_id = issue_id.lstrip("#")
        args = ["issue", "close", clean_id]
        if comment:
            args += ["--comment", comment]

        result = self._run_gh(args, repo=repo)
        if result.returncode == 0:
            print(f"✅ Issue #{clean_id} closed.")
        else:
            print(
                f"❌ Failed to close issue: {result.stderr}", file=sys.stderr
            )


if __name__ == "__main__":
    # Quick CLI for testing the broker directly
    broker = GitHubBroker()
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "sync":
            broker.sync_issue(
                sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None
            )
        elif cmd == "open":
            # Syntax: broker.py open <title> [body] [repo]
            title = sys.argv[2]
            body = (
                sys.argv[3]
                if len(sys.argv) > 3 and sys.argv[3] != "-"
                else None
            )
            repo = sys.argv[4] if len(sys.argv) > 4 else None
            broker.open_issue(title, body, repo)
        elif cmd == "close":
            # Syntax: broker.py close <id> [repo] [comment]
            issue_id = sys.argv[2]
            repo = (
                sys.argv[3]
                if len(sys.argv) > 3 and sys.argv[3] != "-"
                else None
            )
            comment = sys.argv[4] if len(sys.argv) > 4 else None
            broker.close_issue(issue_id, repo, comment)
    else:
        print("Usage: broker.py <sync|close> <issue_id> [repo] [comment]")
