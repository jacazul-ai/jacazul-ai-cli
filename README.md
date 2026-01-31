# AI CLI Sandboxed

This project provides a containerized environment for running AI-powered command line interface (CLI) tools within Docker or Podman containers on Linux. It offers a flexible, isolated, and reproducible environment for experimenting with and deploying AI CLI agents.

## ✨ Features

- **Containerized CLI environment** - Isolated and reproducible
- **Supports Docker and Podman** - Use your preferred container runtime
- **Pre-configured workflows** - Taskwarrior integration with structured 7-phase workflow
- **Skill-based system** - Modular capabilities for different tasks
- **Session persistence** - Maintain context across sessions
- **Optimized for Linux** - Designed for Linux container environments

## 🚀 Quick Start

### Build the Container
```bash
# Using Docker
docker build -f Dockerfile.copilot -t ai-cli-copilot .

# Using Podman
podman build -f Dockerfile.copilot -t ai-cli-copilot .
```

### Run the Container
```bash
# Docker
docker run -it --rm ai-cli-copilot

# Podman
podman run -it --rm ai-cli-copilot
```

### Try Taskwarrior Workflow
```bash
# Check current state
ponder copilot

# Create a plan
tw-flow plan copilot:my-feature \
  "PLAN|Design API|research|today" \
  "EXECUTE|Build API|implementation|tomorrow"

# Start working
tw-flow execute <task_id>
```

## 📚 Documentation

- **[Getting Started](docs/getting-started.md)** - Setup and first steps
- **[Taskwarrior Expert](docs/taskwarrior-expert.md)** - Complete workflow guide
- **[Skills Overview](docs/skills/README.md)** - Available skills

## 🛠 Available Skills

### Taskwarrior Expert (v1.2.0)
Structured workflow management with 7 phases and interaction modes.

**Features:**
- Dashboard visualization (`ponder`)
- Task management (`tw-flow`)
- Session continuity and handoffs
- 18 comprehensive tests

[→ Complete Guide](docs/taskwarrior-expert.md)

## 📁 Project Structure

```
/project/
├── docs/              # Documentation
├── templates/         # Agent configurations
│   ├── skills/       # Available skills
│   └── context/      # Agent instructions
├── scripts/          # CLI wrappers
├── sandbox/          # Sandboxed environments
└── Dockerfile.*      # Container definitions
```

## 🔧 Development

### Adding a New Skill
1. Create skill directory in `templates/skills/`
2. Add SKILL.md documentation
3. Create helper scripts in `scripts/`
4. Add tests
5. Update documentation

### Running Tests
```bash
# Taskwarrior skill tests
./templates/skills/taskwarrior_expert/scripts/test-tw-flow.sh
```

## 🤝 Contributing

Contributions welcome! Please ensure:
- Documentation is updated
- Tests pass
- Follows existing patterns
- Uses Conventional Commits

## 📝 License

MIT

## 🔗 Resources

- [Taskwarrior Documentation](https://taskwarrior.org/docs/)
- [Docker Documentation](https://docs.docker.com/)
- [Podman Documentation](https://podman.io/)
