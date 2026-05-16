#!/home/fpiraz/.jacazul-ai/.venv/bin/python
import os
import shutil
import subprocess
import tempfile
import unittest


class TestProjectIdentity(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="jacazul_project_identity_")
        self.project_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..")
        )
        self.helper = os.path.join(
            self.project_root, "scripts", "bootstrap", "project-identity"
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def run_cmd(self, command, cwd=None, env=None):
        run_env = os.environ.copy()
        if env:
            run_env.update(env)
        return subprocess.run(
            command,
            cwd=cwd,
            env=run_env,
            shell=True,
            executable="/bin/bash",
            capture_output=True,
            text=True,
            check=True,
        )

    def resolve_identity(self, cwd, env=None):
        result = self.run_cmd(
            (
                f'source "{self.helper}" && '
                "jacazul_export_project_identity && "
                "printf '%s\n%s\n%s\n%s\n' "
                '"$JACAZUL_PROJECT_ANCHOR" '
                '"$PARENT_DIR" '
                '"$CURRENT_DIR" '
                '"$PROJECT_ID"'
            ),
            cwd=cwd,
            env=env,
        )
        return result.stdout.strip().splitlines()

    def init_repo(self, path):
        os.makedirs(path, exist_ok=True)
        self.run_cmd("git init -b master", cwd=path)
        self.run_cmd('git config user.name "Test User"', cwd=path)
        self.run_cmd('git config user.email "test@example.com"', cwd=path)
        with open(os.path.join(path, "README.md"), "w", encoding="utf-8") as f:
            f.write("# test\n")
        self.run_cmd("git add README.md", cwd=path)
        self.run_cmd('git commit -m "init"', cwd=path)

    def test_regular_repo_uses_git_toplevel(self):
        repo_root = os.path.join(self.test_dir, "jacazul-ai", "jacazul-ai-cli")
        self.init_repo(repo_root)

        nested_dir = os.path.join(repo_root, "nested", "inside")
        os.makedirs(nested_dir, exist_ok=True)

        anchor, parent_dir, current_dir, project_id = self.resolve_identity(
            nested_dir
        )

        self.assertEqual(anchor, repo_root)
        self.assertEqual(parent_dir, "jacazul-ai")
        self.assertEqual(current_dir, "jacazul-ai-cli")
        self.assertEqual(project_id, "jacazul-ai_jacazul-ai-cli")

    def test_linked_worktree_uses_common_dir_parent(self):
        seed_repo = os.path.join(self.test_dir, "seed")
        self.init_repo(seed_repo)

        workspace_root = os.path.join(
            self.test_dir, "jacazul-ai", "jacazul-ai-cli"
        )
        os.makedirs(workspace_root, exist_ok=True)

        bare_repo = os.path.join(workspace_root, ".bare")
        self.run_cmd(f'git clone --bare "{seed_repo}" "{bare_repo}"')
        self.run_cmd(
            f'git -C "{bare_repo}" worktree add '
            f'"{os.path.join(workspace_root, "master")}" master'
        )

        nested_dir = os.path.join(workspace_root, "master", "nested")
        os.makedirs(nested_dir, exist_ok=True)

        anchor, parent_dir, current_dir, project_id = self.resolve_identity(
            nested_dir
        )

        self.assertEqual(anchor, workspace_root)
        self.assertEqual(parent_dir, "jacazul-ai")
        self.assertEqual(current_dir, "jacazul-ai-cli")
        self.assertEqual(project_id, "jacazul-ai_jacazul-ai-cli")

    def test_project_root_env_is_preferred(self):
        seed_repo = os.path.join(self.test_dir, "seed")
        self.init_repo(seed_repo)

        workspace_root = os.path.join(
            self.test_dir, "jacazul-ai", "jacazul-ai-cli"
        )
        os.makedirs(workspace_root, exist_ok=True)

        bare_repo = os.path.join(workspace_root, ".bare")
        self.run_cmd(f'git clone --bare "{seed_repo}" "{bare_repo}"')
        worktree_root = os.path.join(workspace_root, "master")
        self.run_cmd(
            f'git -C "{bare_repo}" worktree add "{worktree_root}" master'
        )

        unrelated_cwd = os.path.join(self.test_dir, "outside")
        os.makedirs(unrelated_cwd, exist_ok=True)

        anchor, parent_dir, current_dir, project_id = self.resolve_identity(
            unrelated_cwd,
            env={"PROJECT_ROOT": worktree_root},
        )

        self.assertEqual(anchor, workspace_root)
        self.assertEqual(parent_dir, "jacazul-ai")
        self.assertEqual(current_dir, "jacazul-ai-cli")
        self.assertEqual(project_id, "jacazul-ai_jacazul-ai-cli")

    def test_explicit_project_id_override_is_preserved(self):
        repo_root = os.path.join(self.test_dir, "sample", "repo")
        self.init_repo(repo_root)

        _, parent_dir, current_dir, project_id = self.resolve_identity(
            repo_root,
            env={"PROJECT_ID": "manual_override"},
        )

        self.assertEqual(parent_dir, "sample")
        self.assertEqual(current_dir, "repo")
        self.assertEqual(project_id, "manual_override")


if __name__ == "__main__":
    unittest.main()
