# GitHub Broker & Hierarchical Vault

The GitHub Broker ("The Protocol") provides a bidirectional bridge between Taskwarrior tasks and GitHub Issues/PRs, secured by IdZoid's `cryptozoid` encryption.

## 🔐 Hierarchical Vault (vault.json)

Jacazul manages multiple GitHub tokens using a hierarchical resolution strategy. Tokens are stored in `~/.jacazul-ai/vault.json` and are encrypted using EC P256 keys.

### Resolution Precedence:
1. **Project:** Specific token for a repository (`user|org/project`).
2. **Owner:** Token for an entire organization or user account (`user|org`).
3. **Classic Default:** A fallback classic token used if no granular token is found.
4. **System Default:** The native GitHub CLI login (`gh auth login`).

## 🛠️ Jacazul GitHub Manager (jacazul-github)

Use this tool to manage your encrypted tokens.

### Launcher behavior

When you run `scripts/configure`, Jacazul exposes `jacazul-github` through a project-owned launcher instead of a pip-generated console-script shim. If an older shim exists in `~/.local/bin/jacazul-github`, configure replaces that Jacazul-specific shim with a link to the portable launcher so the command also works when `~/.local/bin` appears before `~/bin` in your `PATH`.

### Common Commands:
```bash
# Show current configured scopes
jacazul-github list

# Setup a token for an organization
jacazul-github auth --org jacazul-ai

# Setup a token for a specific project
jacazul-github auth --org jacazul-ai --project jacazul-ai-cli

# Setup a fallback classic token
jacazul-github auth --classic
```

## 🚀 GitHub Broker (The Protocol)

The Broker is the engine that performs the actual synchronization.

### Key Features:
- **Git Context Inference:** Automatically detects Org and Project from local `.git` remotes.
- **Hierarchical Decryption:** Resolves and decrypts the best token from the vault.
- **Killer Sync:** Automatically closes Taskwarrior tasks if the corresponding GitHub issue is marked as `CLOSED`.
- **Error as Prompt:** The Broker provides `ACTION:` hints and returns non-zero exit codes on failure.

### CLI Commands (Direct Use)

**CRITICAL:** Commands `open`, `edit`, and `comment` use **keyword arguments** (`key=val`). Other commands use positional arguments.

```bash
# Sync local tasks with GitHub status (positional)
jacazul-broker sync <issue_id> [repo]

# List issues (positional)
jacazul-broker list [repo] [state] [milestone]

# Open a new issue (kwargs)
jacazul-broker open title="Issue Title" [body="Description"] [repo="org/repo"] [labels="bug,ui"]

# Edit an existing issue (ID + kwargs)
jacazul-broker edit <id> [title="New Title"] [body="New body"] [add_labels="enhancement"]

# Comment on an existing issue (ID + kwargs)
# Use body_file= for Markdown/multiline comments, same as issue descriptions.
jacazul-broker comment '<id>' [body="Comment"] [body_file="/path/comment.md"] [repo="org/repo"]

# Close an issue (positional)
jacazul-broker close <id> [repo] [comment]
```

## 🧪 IdZoid Security Integration

All tokens are processed via `cryptozoid`. 
- **Encryption:** `cryptozoid ec encrypt`
- **Decryption:** `cryptozoid ec decrypt`
- **Cleaning:** The Broker automatically strips trailing newlines (`\n`) from decrypted tokens to ensure API compatibility.

---
**Version:** 1.1.0  
**Last Updated:** 2026-03-26
