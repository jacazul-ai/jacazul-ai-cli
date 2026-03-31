#!/usr/bin/env python
import os
import subprocess
import sys
import json
import re
import time
from typing import Optional, Any, Tuple
from jacazul.taskwarrior.core import TaskWrapper

# 🐊 Jacazul GitHub Broker (The Protocol)
# Handles synchronization between Taskwarrior and GitHub via IdZoid security.


class GitHubBroker:
    def __init__(
        self,
        vault_dir: Optional[str] = None,
        vault_name: Optional[str] = None,
        cryptozoid_bin: Optional[str] = None,
    ):
        self.tw = TaskWrapper()
        self.vault_dir = vault_dir or os.environ.get(
            "JACAZUL_HOME", os.path.expanduser("~/.jacazul-ai")
        )
        self.vault_name = vault_name or "jacazul-vault"
        self.vault_file = os.path.join(self.vault_dir, "vault.json")
        self.github_vault_legacy = os.path.join(self.vault_dir, "github.enc")
        self.cache_dir = os.path.join(self.vault_dir, "cache", "github")
        self.cryptozoid_bin = cryptozoid_bin or os.path.expanduser(
            "~/go/bin/cryptozoid"
        )

    def _ensure_cache_dir(self, repo: str):
        path = os.path.join(self.cache_dir, repo.replace("/", "_"))
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
        return path

    def _get_cache_file(self, repo: str, kind: str) -> str:
        repo_path = self._ensure_cache_dir(repo)
        return os.path.join(repo_path, f"{kind}.json")

    def _read_cache(
        self, repo: str, kind: str, ttl_seconds: int
    ) -> Optional[Any]:
        """Reads data from local cache if not expired."""
        cache_file = self._get_cache_file(repo, kind)
        if not os.path.exists(cache_file):
            return None

        # Check TTL
        mtime = os.path.getmtime(cache_file)
        if (time.time() - mtime) > ttl_seconds:
            return None

        try:
            with open(cache_file, "r") as f:
                return json.load(f)
        except Exception:
            return None

    def _write_cache(self, repo: str, kind: str, data: Any):
        """Writes data to local cache."""
        cache_file = self._get_cache_file(repo, kind)
        try:
            with open(cache_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"⚠️ Warning: Failed to write cache: {e}", file=sys.stderr)

    def _invalidate_cache(self, repo: str, kind: Optional[str] = None):
        """Invalidates cache for a specific repo and kind (or all kinds)."""
        repo_path = self._ensure_cache_dir(repo)
        if kind:
            cache_file = os.path.join(repo_path, f"{kind}.json")
            if os.path.exists(cache_file):
                os.remove(cache_file)
        else:
            import shutil

            shutil.rmtree(repo_path, ignore_errors=True)

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
        self,
        args: list,
        repo: Optional[str] = None,
        use_repo_flag: bool = True,
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
                if use_repo_flag:
                    repo = f"{target_org}/{target_proj}"

        token = self._get_token(org=target_org, project=target_proj)

        env = os.environ.copy()
        if token:
            env["GH_TOKEN"] = token

        cmd = ["gh"] + args
        if repo and use_repo_flag:
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
        body_file: Optional[str] = None,
        repo: Optional[str] = None,
        assignee: Optional[str] = None,
        labels: Optional[list] = None,
    ):
        """Opens a new GitHub issue."""
        args = ["issue", "create", "--title", title]
        if body_file:
            args += ["--body-file", body_file]
        elif body:
            args += ["--body", body]
        if assignee:
            args += ["--assignee", assignee]
        if labels:
            for label in labels:
                args += ["--label", label]

        result = self._run_gh(args, repo=repo)
        if result.returncode == 0:
            # Invalidate cache on success
            if not repo:
                org, proj = self._infer_context()
                repo = f"{org}/{proj}" if org and proj else None
            if repo:
                self._invalidate_cache(repo)

            # gh issue create prints the URL of the new issue
            issue_url = result.stdout.strip()
            print(f"✅ Issue created: {issue_url}")
            return issue_url
        else:
            print(
                f"❌ Failed to create issue: {result.stderr}", file=sys.stderr
            )
            return None

    def list_labels(self, repo: Optional[str] = None):
        """Lists available labels in the repository (with cache)."""
        if not repo:
            org, proj = self._infer_context()
            if org and proj:
                repo = f"{org}/{proj}"

        if not repo:
            print(
                "❌ Error: Could not infer repository context.",
                file=sys.stderr,
            )
            return

        # Try cache (24h TTL)
        cached = self._read_cache(repo, "labels", 86400)
        if cached:
            print(f"🐊 Labels for {repo} (Cached):")
            for label in cached:
                print(f"  - {label['name']}: {label.get('description', '')}")
            return

        result = self._run_gh(
            ["label", "list", "--json", "name,description"], repo=repo
        )
        if result.returncode == 0:
            labels = json.loads(result.stdout)
            self._write_cache(repo, "labels", labels)
            print(f"🐊 Labels for {repo} (API):")
            for label in labels:
                print(f"  - {label['name']}: {label.get('description', '')}")
        else:
            print(
                f"❌ Failed to list labels: {result.stderr}", file=sys.stderr
            )

    def list_milestones(self, repo: Optional[str] = None):
        """Lists available milestones in the repository (with cache)."""
        # Infer context if not provided
        if not repo:
            org, proj = self._infer_context()
            if org and proj:
                repo = f"{org}/{proj}"

        if not repo:
            print(
                "❌ Error: Could not infer repository context.",
                file=sys.stderr,
            )
            return

        # Try cache (1h TTL)
        cached = self._read_cache(repo, "milestones", 3600)
        if cached:
            print(f"🐊 Milestones for {repo} (Cached):")
            for ms in cached:
                print(f"  - [{ms['number']}] {ms['title']} ({ms['state']})")
            return

        # Use api with the full path. gh api doesn't support --repo flag
        endpoint = f"repos/{repo}/milestones"
        result = self._run_gh(
            ["api", endpoint], repo=None, use_repo_flag=False
        )
        if result.returncode == 0:
            milestones = json.loads(result.stdout)
            self._write_cache(repo, "milestones", milestones)
            if not milestones:
                print(f"ℹ️ No milestones found in {repo}.")
                return
            print(f"🐊 Milestones for {repo} (API):")
            for ms in milestones:
                print(f"  - [{ms['number']}] {ms['title']} ({ms['state']})")
        else:
            print(
                f"❌ Failed to list milestones: {result.stderr}",
                file=sys.stderr,
            )

    def edit_issue(
        self,
        issue_id: str,
        title: Optional[str] = None,
        body: Optional[str] = None,
        body_file: Optional[str] = None,
        repo: Optional[str] = None,
        assignee: Optional[str] = None,
        add_labels: Optional[list] = None,
        remove_labels: Optional[list] = None,
    ):
        """Edits an existing GitHub issue."""
        clean_id = issue_id.lstrip("#")
        args = ["issue", "edit", clean_id]
        if title:
            args += ["--title", title]
        if body_file:
            args += ["--body-file", body_file]
        elif body:
            args += ["--body", body]
        if assignee:
            args += ["--assignee", assignee]
        if add_labels:
            for label in add_labels:
                args += ["--add-label", label]
        if remove_labels:
            for label in remove_labels:
                args += ["--remove-label", label]

        result = self._run_gh(args, repo=repo)
        if result.returncode == 0:
            # Invalidate cache on success
            if not repo:
                org, proj = self._infer_context()
                repo = f"{org}/{proj}" if org and proj else None
            if repo:
                self._invalidate_cache(repo)

            print(f"✅ Issue #{clean_id} updated.")
        else:
            print(
                f"❌ Failed to update issue: {result.stderr}", file=sys.stderr
            )

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
            # Invalidate cache on success
            if not repo:
                org, proj = self._infer_context()
                repo = f"{org}/{proj}" if org and proj else None
            if repo:
                self._invalidate_cache(repo)

            print(f"✅ Issue #{clean_id} closed.")
        else:
            print(
                f"❌ Failed to close issue: {result.stderr}", file=sys.stderr
            )

    def view_issue(self, issue_id: str, repo: Optional[str] = None):
        """Fetches and displays full details of a GitHub issue."""
        clean_id = issue_id.lstrip("#")
        result = self._run_gh(
            [
                "issue", "view", clean_id,
                "--json",
                "number,title,state,body,labels,assignees,createdAt",
            ],
            repo=repo,
        )
        if result.returncode != 0:
            print(
                f"❌ Failed to fetch issue: {result.stderr}", file=sys.stderr
            )
            return

        data = json.loads(result.stdout)
        state = data.get("state", "UNKNOWN").upper()
        title = data.get("title", "")
        body = data.get("body", "")
        labels = [lb["name"] for lb in data.get("labels", [])]
        assignees = [a["login"] for a in data.get("assignees", [])]

        print(f"🐊 Issue #{clean_id} [{state}] — {title}")
        if labels:
            print(f"   Labels: {', '.join(labels)}")
        if assignees:
            print(f"   Assignees: {', '.join(assignees)}")
        print()
        print(body)

    def list_issues(
        self,
        repo: Optional[str] = None,
        state: str = "open",
        milestone: Optional[str] = None,
        limit: int = 30,
    ):
        """Lists issues in the repository."""
        args = ["issue", "list", "--state", state, "--limit", str(limit)]
        if milestone:
            args += ["--milestone", milestone]

        args += ["--json", "number,title,state,updatedAt"]

        result = self._run_gh(args, repo=repo)
        if result.returncode == 0:
            issues = json.loads(result.stdout)
            if not issues:
                print(
                    f"ℹ️ No {state} issues found in {repo or 'current repo'}."
                )
                return

            print(
                f"🐊 {state.capitalize()} issues for {repo or 'current repo'}:"
            )
            for issue in issues:
                print(
                    f"  - [#{issue['number']}] {issue['title']} "
                    f"({issue['state']})"
                )
        else:
            print(
                f"❌ Failed to list issues: {result.stderr}", file=sys.stderr
            )


def error(msg: str):
    """🐊 Error as Prompt: Emits error to stderr with ACTION hints."""
    print(f"❌ ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def main():
    # Quick CLI for testing the broker directly
    broker = GitHubBroker()
    if len(sys.argv) < 2:
        print(
            "Usage: jacazul-broker "
            "<sync|view|list|labels|milestones|open|edit|close> ..."
        )
        print("\nCommands:")
        print(
            "  view <issue_id> [repo]        Shows full issue details and body"
        )
        print(
            "  sync <issue_id> [repo]        Syncs issue status to local tasks"
        )
        print(
            "  list [repo] [state] [ms]      Lists issues "
            "(state: open|closed|all)"
        )
        print(
            "  labels [repo]                 Lists repository labels (cached)"
        )
        print(
            "  milestones [repo]             Lists repository "
            "milestones (cached)"
        )
        print(
            '  open title="..." [body="..."] [body_file="..."] [repo="..."] '
            '[assignee="..."] [labels="l1,l2"]'
        )
        print(
            '  edit <id> [title="..."] [body="..."] [body_file="..."] '
            '[repo="..."] [assignee="..."] [add_labels="l1"]'
        )
        print("  close <id> [repo] [comment]   Closes an issue")
        print(
            "\n💡 Tip: For complex Markdown bodies (backticks, quotes, "
            "newlines), prefer body_file=\"/path/to/body.md\" over body=\"...\""
        )
        sys.exit(0)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    def parse_kwargs(args_list):
        kwargs = {}
        for arg in args_list:
            if "=" in arg:
                key, val = arg.split("=", 1)
                kwargs[key] = val
        return kwargs

    if cmd == "view":
        if not args:
            error(
                "Issue ID required.\n"
                "   ACTION: Use 'jacazul-broker view #123'"
            )
        broker.view_issue(args[0], args[1] if len(args) > 1 else None)

    elif cmd == "sync":
        if not args:
            error(
                "Issue ID required for sync.\n"
                "   ACTION: Use 'jacazul-broker sync #123'"
            )
        broker.sync_issue(args[0], args[1] if len(args) > 1 else None)

    elif cmd == "list":
        # Syntax: broker.py list [repo] [state] [milestone]
        repo = args[0] if len(args) > 0 and args[0] != "-" else None
        state = args[1] if len(args) > 1 and args[1] != "-" else "open"
        milestone = args[2] if len(args) > 2 and args[2] != "-" else None
        broker.list_issues(repo, state, milestone)

    elif cmd == "labels":
        broker.list_labels(args[0] if args else None)

    elif cmd == "milestones":
        broker.list_milestones(args[0] if args else None)

    elif cmd == "open":
        kwargs = parse_kwargs(args)
        title = kwargs.get("title")
        if not title:
            error(
                "Title required to open issue.\n"
                "   ACTION: Use 'jacazul-broker open title=\"My title\"'"
            )
        body = kwargs.get("body")
        body_file = kwargs.get("body_file")
        repo = kwargs.get("repo")
        assignee = kwargs.get("assignee")
        labels_raw = kwargs.get("labels")
        labels = labels_raw.split(",") if labels_raw else None
        broker.open_issue(title, body, body_file, repo, assignee, labels)

    elif cmd == "edit":
        if not args:
            error(
                "Issue ID required to edit.\n"
                "   ACTION: Use 'jacazul-broker edit #123 title=\"New Title\"'"
            )
        issue_id = args[0]
        kwargs = parse_kwargs(args[1:])
        title = kwargs.get("title")
        body = kwargs.get("body")
        body_file = kwargs.get("body_file")
        repo = kwargs.get("repo")
        assignee = kwargs.get("assignee")
        add_labels_raw = kwargs.get("add_labels")
        add_labels = add_labels_raw.split(",") if add_labels_raw else None
        broker.edit_issue(issue_id, title, body, body_file, repo, assignee, add_labels)

    elif cmd == "close":
        # Syntax: broker.py close <id> [repo] [comment]
        if len(args) < 1:
            error(
                "Issue ID required to close.\n"
                "   ACTION: Use 'jacazul-broker close #123'"
            )
        issue_id = args[0]
        repo = args[1] if len(args) > 1 and args[1] != "-" else None
        comment = args[2] if len(args) > 2 else None
        broker.close_issue(issue_id, repo, comment)

    else:
        error(
            f"Unknown command: '{cmd}'.\n"
            "   ACTION: Use one of: view, sync, list, labels, milestones, "
            "open, edit, close."
        )


if __name__ == "__main__":
    main()
