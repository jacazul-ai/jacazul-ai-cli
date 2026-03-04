# Environment Modes: COMPANION vs UNHINGED

This project supports two primary interaction modes that dictate how the environment is bootstrapped and how much autonomy the AI agent has.

## 🛡️ COMPANION Mode (Safety Default)

**Purpose:** Interactive partnership. This is the default mode for all sessions. It ensures that the AI agent acts as a co-pilot, requiring user consent for significant system changes.

### 📍 Key Locations (UNHINGED/Native Baseline)

| Component | Path |
| :--- | :--- |
| **JACAZUL_HOME** | `~/.jacazul-ai` |
| **Taskwarrior Config** | `~/.jacazul-ai/.taskrc` |
| **Taskwarrior Data** | `~/.jacazul-ai/.task/$PROJECT_ID` |
| **Python VENV** | `~/.jacazul-ai/.venv` |

### 🧠 Behavior & Autonomy
- **Autonomy:** Propose-and-Wait.
- **Rules:**
  - **System Changes:** Requires explicit user approval for `chmod`, `rm`, `scripts/configure`, or editing bootstrap files.
  - **Git Commits:** Must present a draft and wait for an "OK" before committing to the `master` branch.
  - **Task Closure:** Must ask before running `tw-flow done`.

---

## 🔓 UNHINGED Mode (Active High-Autonomy)

**Purpose:** Rapid execution and automated environment stabilization. Designed for experienced users who trust the AI to "clean the swamp" without constant micro-management.

### 🧠 Behavior & Autonomy
- **Autonomy:** Execute-and-Report.
- **Rules:**
  - **Direct Action:** Authorized to fix environmental issues, create directories, and update internal configurations autonomously.
  - **Workflow Momentum:** May close tasks or execute commits once the technical approach is clear.
  - **Transparency:** All actions must be reported immediately after execution.

---

## 🔒 CAGED Mode (Containerized)

**Purpose:** Fully isolated execution inside a Podman/Docker container. 

### 🚀 Bootstrap Dynamics
- **Script:** `scripts/bootstrap/environment`
- **Default Baseline:** If `JACAZUL_MODE` is unset, the system defaults to **COMPANION**.
- **Switching:** Set the `JACAZUL_MODE` environment variable to `UNHINGED` to enable high-autonomy mode.

---

**Last Updated:** 2026-03-04
