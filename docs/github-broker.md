# GitHub Broker & Hierarchical Vault

The GitHub Broker ("The Caboco") provides a bidirectional bridge between Taskwarrior tasks and GitHub Issues/PRs, secured by IdZoid's `cryptozoid` encryption.

## 🔐 Hierarchical Vault (vault.json)

Jacazul manages multiple GitHub tokens using a hierarchical resolution strategy. Tokens are stored in `~/.jacazul-ai/vault.json` and are encrypted using EC P256 keys.

### Resolution Precedence:
1. **Project:** Specific token for a repository (`user|org/project`).
2. **Owner:** Token for an entire organization or user account (`user|org`).
3. **Classic Default:** A fallback classic token used if no granular token is found.
4. **System Default:** The native GitHub CLI login (`gh auth login`).

## 🛠️ Jacazul GitHub Manager (jacazul-github)

Use this tool to manage your encrypted tokens.

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

## 🚀 GitHub Broker (The Caboco)

The Broker is the engine that performs the actual synchronization.

### Key Features:
- **Git Context Inference:** Automatically detects Org and Project from local `.git` remotes.
- **Hierarchical Decryption:** Resolves and decrypts the best token from the vault.
- **Killer Sync:** Automatically closes Taskwarrior tasks if the corresponding GitHub issue is marked as `CLOSED`.

### CLI Commands (Direct Use):
```bash
# Sync local tasks with GitHub status
python3 jacazul/cli/broker.py sync <issue_id>

# Open a new issue
python3 jacazul/cli/broker.py open "Title" "Body description"

# Close an issue
python3 jacazul/cli/broker.py close <issue_id> "Closing comment"
```

## 🧪 IdZoid Security Integration

All tokens are processed via `cryptozoid`. 
- **Encryption:** `cryptozoid ec encrypt`
- **Decryption:** `cryptozoid ec decrypt`
- **Cleaning:** The Broker automatically strips trailing newlines (`\n`) from decrypted tokens to ensure API compatibility.

---
**Version:** 1.0.0  
**Last Updated:** 2026-03-22
