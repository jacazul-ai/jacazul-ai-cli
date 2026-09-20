# Documentation Central 📚

Welcome to the Jacazul AI CLI documentation. This project is built around the concept of **Persistent Tactical Memory** and **Multi-Persona Navigation**.

## 📖 Table of Contents

### 🚀 Getting Started
- [Quick Start Guide](getting-started.md) - Host and Sandbox setup.
- [Verification Methodology](verification-methodology.md) - How we ensure high-integrity delivery.
- [Technical Architecture](ARCHITECTURE.md) - Internal structure and CLI reference.

### 🎭 The Navigators (Personas)
- [Multi-Persona System](agents/persona-system.md) - Architecture and design.
- [Jacazul & Codana](agents/README.md) - The original duo.
- [Arnalbam & Atena](agents/README.md) - The Shredded and the Wise additions.
- [Persona Switching](agents/persona-switching.md) - How to swap partners mid-session.

### 🛠️ Expert Skills
- [Taskwarrior Expert](taskwarrior-expert.md) - Mastering the 7-phase workflow.
- [Interaction Modes](interaction-modes.md) - DESIGN/GUIDE/REVIEW/EXECUTE collaboration semantics.
- [Python Expert](python-expert.md) - Legacy, greenfield and migration modes, py-mode, py-check and PEP 8.
- [JS/TS Expert](js-ts-expert.md) - Framework-neutral JavaScript and TypeScript, js-mode, js-check, thin edge or full-stack by your choice.
- [Zig Expert](zig-expert.md) - Version-pinned Zig, allocators and errdefer, safety modes, std.Io, review on the shared scale.
- [PHP Expert](php-expert.md) - PHP as a language, php-mode, php-census, the two-pin 5.6 to 8.x migration method.
- [Shell Expert](bash-expert.md) - POSIX sh and bash, sh-mode, sh-census, set -e truth table, portability and idempotence.
- [Git Expert](git-expert.md) - Commit standards, git-mode workflow pin and detection, git-census before push, non-interactive rebase recipes.
- [Go Expert](go-expert.md) - Idiomatic Go, gofmt-to-goimports formatting, and Line of Sight readability.
- [Tutors](tutor.md) - Learning a language with a tutor paired to its expert.
- [Skills Index](skills/README.md) - Every skill, including Rust Expert, Rust Tutor, Go Tutor, and the shared Code Review scale.
- [GitHub Broker](github-broker.md) - Secure issue and ticket synchronization.

### 🔒 Advanced Concepts
- [Environment Modes](environment-modes.md) - COUNSELOR (Safety) vs UNHINGED (Autonomy).
- [Output Caching](tw-flow-cache.md) - Session-scoped context protection.
- [Production Readiness Proposal](proposals/production-readiness.md) - Future risk-based release review across security, correctness, operations, and UX.
- [NO BULLSHIT Policy](agents/no-bullshit-policy.md) - Our feedback standard.

---

## 🌟 The Navigator Ecosystem

We use distinct AI personalities to match your workflow needs. Swapping is conversational—no commands required.

| Navigator | Voice | Specialization |
| :--- | :--- | :--- |
| **🐊 Jacazul** | PT-BR | Street-smart orientation and quick wins. |
| **{🔷} Codana** | EN | Tactical precision and complex logic. |
| **{💪} Arnalbam** | Bilingual | High-octane motivation and heavy refactoring. |
| **🦉 Atena** | Pedagogical | Step-by-step guidance and workflow training. |

---

## 🆘 Troubleshooting & Support

1. Check the **[Technical Architecture](ARCHITECTURE.md)** for CLI parity and path issues.
2. Use the `onboard` trigger to refresh your agent's context.
3. Consult the **[Verification Methodology](verification-methodology.md)** if tasks are failing Quality Gates.

---

**Philosophy:** "Plan effectively, execute efficiently, and never lose context."
