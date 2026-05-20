# Jacazul AI CLI (Monstro do Lago) 🐊

**Stop AI Amnesia. Master Your Workflow.**

Jacazul AI CLI is a high-performance, dual-mode environment designed to run AI-powered command line tools (Gemini, Opencode, Copilot, Claude) with persistent memory, structured task management, and distinct personalities.

## 🌟 Why Jacazul?

Most AI interactions are transient. You lose context, plans get messy, and results are hard to reproduce. Jacazul solves this by providing:

- **🧠 Persistent Tactical Memory**: Isolated Taskwarrior databases per project. Your AI never forgets what it was doing.
- **🛡️ Dual-Mode Security**: Run in isolated containers (**CAGED**) for maximum safety or native host (**COUNSELOR**) for raw performance.
- **🎭 Multi-Persona System**: Switch between distinct AI characters to match your current workflow vibe.
- **🚀 7-Phase Lifecycle**: A robust workflow (Orient, Plan, Execute, Context, Review, Outcome, Close) that ensures high-integrity delivery.

---

## 🎭 Meet the Navigators

You don't just work with an AI; you work with a partner. Swapping is conversational—no special commands required. Just ask for them by name: *"me traz a codana"*, *"bring me Arnalbam"*, or *"chama o jacazul"*.

| Navigator | Style | Best For... |
| :--- | :--- | :--- |
| **🐊 Jacazul** | PT-BR, Street-smart, Laid-back. | Project orientation and quick navigation. |
| **{🔷} Codana** | EN, Tactical, Professional, Sharp. | Complex implementations and exactness. |
| **{💪} Arnalbam** | Bilingual, High-octane, Gym-themed. | Motivation, heavy refactoring, and "shredding" code. |
| **🦉 Atena** | Pedagogical, Wise, Encouraging. | Learning new workflows and step-by-step guidance. |

For detailed persona guides and switching examples, see the **[Documentation Central](docs/README.md)**.

---

## 🚀 Getting Started

### 1. Pre-requisites
- **Python 3.13+**
- **Go** (for security modules)
- **Taskwarrior** (2.6+ or 3.x)
- **GitHub CLI (gh)**

### 2. Quick Install
```bash
make configure
make github
```

### 3. Run Your Engine
```bash
jacazul-gemini      # Gemini CLI
jacazul-claude      # Claude CLI
jacazul-opencode    # Opencode CLI
jacazul-copilot     # Copilot CLI
jacazul-pi          # Pi CLI with Jacazul footer/dashboard integration
```

For Pi footer/dashboard behavior, see [pi-jacazul-line](docs/pi-jacazul-line.md).

### 4. The First Set (Conversational Flow)

Jacazul tools are designed for natural interaction. You provide the intent; your Navigator handles the CLI.

| You Say... | Your Navigator Runs... |
| :--- | :--- |
| "onboard" or "full status" | `tw-flow ponder` (Strategic View) |
| "status" or "o que estamos fazendo?" | `tw-flow status` (Tactical View) |
| "create a plan X with tasks A and B" | `tw-flow plan X "A" "B"` |
| "focus on this" or "foca nessa task" | `tw-flow focus ind task <uuid>` |
| "start task <uuid>" | `tw-flow execute <uuid>` |
| "me traz a codana" | `jacazul-persona codana` |

---

## 🌟 Interaction Philosophy: NO BULLSHIT

We follow a strict **NO BULLSHIT** policy. Your navigators won't give you fake praise or fluff. 
- **Genuine Feedback:** If a technical approach is weak, they'll say it. 
- **Direct Action:** High-autonomy modes (like **UNHINGED**) allow the agent to fix environmental issues without asking for permission every time.
- **Conversational Switching:** No special syntax. Just ask for your preferred partner by name.

---

## 🏗️ Deep Dive

For technical details, internal architecture, and file layouts, see [Technical Architecture](docs/ARCHITECTURE.md).

## 🛠️ Expert Skills

Jacazul extends your capabilities via specialized skills:
- **Taskwarrior Expert**: Advanced workflow persistence.
- **Python Expert**: PEP 8 compliance and auto-beautification.
- **Git Expert**: Strict conventional commit standards.
- **GitHub Broker**: Secure, credential-less ticket synchronization.

---

## 📝 License

MIT

**Philosophy:** "Plan effectively, execute efficiently, and never lose context."
