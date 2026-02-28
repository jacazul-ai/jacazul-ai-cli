# Getting Started

Quick start guide for the Jacazul AI CLI environment.

## 🎯 Overview

Jacazul AI CLI is a powerful workflow automation system that runs directly on your machine or inside a container. It provides:
- **Direct Native Setup:** Run directly in your shell for maximum speed.
- **Isolated Containers:** Sandboxed environment for safe experimentation.
- **Expert Skills:** Taskwarrior-based workflow management, Python expert system, and more.
- **Rebranded Identity:** Modern, direct, and action-oriented.

---

## 🚀 Direct Setup (Recommended)

The fastest way to get started is by configuring your local environment to use the Jacazul wrappers.

### 1. Run Configuration

This will create symbolic links in `~/bin` and prepare your local environment.

```bash
make configure
```

### 2. Update your PATH

Ensure `~/bin` is in your shell path:

```bash
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### 3. Start the Agent

Now you can call the Jacazul agents from anywhere:

```bash
# Start Jacazul for Gemini CLI
jacazul-gemini

# Start Jacazul for GitHub Copilot CLI
jacazul-copilot

# Start Jacazul for OpenCode
jacazul-opencode
```

---

## 🐳 Container Setup (Sandbox)

If you prefer isolation, use the containerized environment.

### 1. Build the Image

```bash
make sandbox
```

### 2. Run the Container

```bash
# Using the jacazul-gemini wrapper in sandboxed mode
./scripts/jacazul-gemini-sandboxed
```

---

## 🛠 Core Workflow

Jacazul is built on top of **Taskwarrior**. Use the expert tools to manage your progress.

### 1. Orient (Ponder)
See the state of your project.
```bash
ponder
```

### 2. Plan (tw-flow)
Break down your goals into actionable tasks.
```bash
tw-flow plan my-feature \
  "DESIGN|Schema review|research|today" \
  "EXECUTE|Implementation|implementation|tomorrow"
```

### 3. Execute
Pick the top task and start working.
```bash
tw-flow execute <uuid>
```

---

## 📁 Directory Structure

- `scripts/`: Core CLI wrappers and bootstraps.
- `templates/`: Skill definitions and agent instructions.
- `docs/`: Documentation and guides.
- `~/bin/`: (After configure) Symbolic links to core tools.
- `~/.jacazul-ai/`: Global configuration and Taskwarrior databases.

---

## 📚 Next Steps

1. **Taskwarrior Mastery:** Read the [Taskwarrior Expert Guide](taskwarrior-expert.md).
2. **Explore Skills:** See [Skills Overview](skills/README.md).
3. **Environment Modes:** Understand [Unhinged vs Caged modes](environment-modes.md).

---

**Last Updated:** 2026-02-27
