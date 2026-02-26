# Interaction Modes: UNHINGED vs CAGED

This project supports two primary interaction modes that dictate how the environment is bootstrapped and where data is stored.

## 🔓 UNHINGED Mode (Native/Direct)

**Purpose:** Direct execution on the host system (Fedora/Debian/Ubuntu) without containerization. Designed for speed and seamless integration with the user's host environment.

### 📍 Key Locations

| Component | Path |
| :--- | :--- |
| **JAKA_HOME** | `~/.candango/jaka_ai` |
| **Taskwarrior Config** | `~/.candango/jaka_ai/.taskrc` |
| **Taskwarrior Data** | `~/.candango/jaka_ai/.task/$PROJECT_ID` |
| **Python VENV** | `~/.candango/jaka_ai/.venv` |
| **Skills Symlink** | `~/.copilot/skills` (points to project templates) |
| **Templates Symlink** | `~/.copilot/templates` (points to project templates) |

### 🚀 Bootstrap Dynamics
- **Script:** `scripts/bootstrap/environment`
- **Behavior:** Dynamically detects the host OS, initializes the persistent Python venv using `uv`, and ensures Taskwarrior is configured with per-project isolation.
- **Entry Points:** `copilot-direct`, `can-gemini`, `can-copilot`, `can-opencode`.

---

## 🔒 CAGED Mode (Containerized)

**Purpose:** Fully isolated execution inside a Podman/Docker container. Designed for maximum reproducibility and a clean host system.

### 📍 Key Locations

| Component | Path |
| :--- | :--- |
| **Project Root** | `/project` (inside container) |
| **Taskwarrior Config** | `/root/.taskrc` |
| **Taskwarrior Data** | `/root/.task` or `/project/.task` (depending on mount) |
| **Python VENV** | Managed within the container image |
| **Skills** | `/project/templates/skills` |
| **Templates** | `/project/templates` |

### 🚀 Bootstrap Dynamics
- **Script:** Managed via `Dockerfile.copilot` and `scripts/bootstrap/` within the container.
- **Behavior:** Relies on the container's isolated filesystem. Data persistence is typically handled via volume mounts.
- **Entry Point:** Standard `copilot` command within the container.

---

## 🔄 Switching Modes

- To use **UNHINGED** mode: Use the `scripts/configure-direct` setup and run commands like `copilot-direct`.
- To use **CAGED** mode: Build and run the container using `Dockerfile.copilot` or `Dockerfile.gemini`.

---

**Last Updated:** 2026-02-25
