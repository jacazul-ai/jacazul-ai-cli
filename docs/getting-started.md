# Getting Started

Quick start guide for the AI CLI Sandboxed environment.

## 🎯 Overview

AI CLI Sandboxed provides a containerized environment for running AI-powered command line tools with:
- Isolated, reproducible containers (Docker/Podman)
- Pre-configured AI CLI agents
- Skill-based workflow systems
- Session persistence

## 🚀 Quick Start

### 1. Build the Container

```bash
# Using Docker
docker build -f Dockerfile.copilot -t ai-cli-copilot .

# Using Podman
podman build -f Dockerfile.copilot -t ai-cli-copilot .
```

### 2. Run the Container

```bash
# Docker
docker run -it --rm ai-cli-copilot

# Podman
podman run -it --rm ai-cli-copilot
```

### 3. Inside the Container

The environment comes pre-configured with:
- **Taskwarrior** for task management
- **tw-flow** and **ponder** scripts
- **Copilot CLI** integration

---

## 🛠 Available Tools

### Taskwarrior Expert Skill

Complete workflow management system. See [Taskwarrior Expert Guide](taskwarrior-expert.md).

**Quick example:**
```bash
# Check current state
ponder copilot

# Create a plan
tw-flow plan copilot:my-feature \
  "PLAN|Design API|research|today" \
  "EXECUTE|Build API|implementation|tomorrow"

# Start work
tw-flow execute 42
```

---

## 📁 Directory Structure

```
/project/
├── templates/          # Agent configurations
│   ├── skills/        # Available skills
│   └── context/       # Agent instructions
├── scripts/           # CLI wrappers
├── docs/              # Documentation (you are here)
└── sandbox/           # Sandboxed environments
```

---

## 🔧 Configuration

### Customizing the Environment

Edit `Dockerfile.copilot` to add packages or tools:

```dockerfile
RUN apt-get update && apt-get install -y \
    your-package-here
```

### Adding Skills

Place skill directories in `/project/templates/skills/`

Structure:
```
templates/skills/my-skill/
├── SKILL.md           # Skill documentation
├── scripts/           # Helper scripts
└── ...
```

---

## 📚 Next Steps

1. **Learn Taskwarrior workflow:** Read [Taskwarrior Expert Guide](taskwarrior-expert.md)
2. **Explore skills:** Check [Skills Overview](skills/README.md)
3. **Run examples:** Try the complete workflow example

---

## 🆘 Troubleshooting

### Container won't build
- Check Docker/Podman is installed
- Verify you're in the project root
- Try removing cached layers: `docker system prune`

### Scripts not found
- Ensure you're inside the container
- Check `/project/templates/skills/*/scripts/` paths
- Verify scripts are executable: `chmod +x script-name`

### Taskwarrior not working
- Initialize if needed: `task` (first time)
- Check data location: `~/.task/` or `~/.local/share/task/`

---

## 🔗 Additional Resources

- [Main README](../README.md)
- [Taskwarrior Official Docs](https://taskwarrior.org/docs/)
- [Docker Documentation](https://docs.docker.com/)

---

**Last Updated:** 2026-01-31
