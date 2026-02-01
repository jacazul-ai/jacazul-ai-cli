# Custom Agents

This directory contains custom agent profiles for GitHub Copilot CLI.

## What are Custom Agents?

Custom agents are specialized versions of the Copilot coding agent that you can tailor to specific workflows and tasks. They are defined using Markdown files (`.agent.md`) with YAML frontmatter.

## Directory Structure

```
templates/agents/
 README.md                    # This file
 jacazul.agent.md             # Jacazul workflow navigator
```

## Available Agents

### 🐊 Jacazul Agent

**Purpose:** Workflow navigation and project context management

**Usage:**
```bash
# In Copilot CLI:
onboard

# Or natural language:
Use Jacazul to show me project status
```

**What it does:**
1. Activates taskwarrior-expert skill
2. Shows environment context (git user, PROJECT_ID, paths)
3. Displays project dashboard (ponder)
4. Presents current focus and ready tasks
5. Waits for your direction

**Commands:**
- `onboard` - Initialize session context
- `ponder` - Refresh status dashboard
- `planos` / `mostre planos` - List all project plans
- `trabalhar em [plan]` - Focus on specific plan

**Tools:** `bash`, `view`, `skill`

**Documentation:** `docs/agents/jacazul.md`

## How to Install Custom Agents

Custom agents can be installed at different scopes:

### Repository Level (Recommended for this project)
```bash
# Copy to repository agents directory
mkdir -p .github/agents
cp templates/agents/*.agent.md .github/agents/
```

### User Level (Available across all projects)
```bash
# Copy to user agents directory
mkdir -p ~/.copilot/agents
cp templates/agents/*.agent.md ~/.copilot/agents/
```

### Organization/Enterprise Level
```bash
# In .github-private repository
mkdir -p agents
cp templates/agents/*.agent.md agents/
```

## Agent Profile Format

An agent profile is a Markdown file with YAML frontmatter:

```markdown
---
name: agent-name
description: Brief description of what the agent does
tools: ["bash", "view", "edit"]  # Optional: limit available tools
model: claude-sonnet-4.5         # Optional: specify model
target: github-copilot           # Optional: vscode or github-copilot
---

# Agent prompt in Markdown

Instructions for the agent's behavior, expertise, and workflow...
```

### Required Properties

- **name**: Unique identifier for the agent
- **description**: Brief explanation of capabilities

### Optional Properties

- **tools**: List of allowed tools (omit to allow all)
- **model**: AI model to use (e.g., `claude-sonnet-4.5`)
- **target**: Limit to specific environment (`vscode` or `github-copilot`)
- **mcp-servers**: MCP server configurations (org/enterprise only)

## Creating New Custom Agents

1. **Create agent profile:**
   ```bash
   touch templates/agents/my-agent.agent.md
   ```

2. **Define YAML frontmatter:**
   ```yaml
   ---
   name: my-agent
   description: Does something specific
   tools: ["bash", "view"]
   ---
   ```

3. **Write agent prompt:**
   - Define responsibilities
   - Specify workflow steps
   - Set communication style
   - Document tools usage

4. **Test locally:**
   ```bash
   cp templates/agents/my-agent.agent.md ~/.copilot/agents/
   # In Copilot CLI:
   /agent my-agent
   ```

5. **Add to repository:**
   ```bash
   mkdir -p .github/agents
   cp templates/agents/my-agent.agent.md .github/agents/
   git add .github/agents/my-agent.agent.md
   git commit -m "feat(agents): add my-agent custom agent"
   ```

## Using Custom Agents

### In Copilot CLI

**Method 1: Slash Command**
```bash
/agent
# Select from list
```

**Method 2: Direct Reference**
```bash
Use the jacazul agent to show me the status
```

**Method 3: Command Line Argument**
```bash
copilot --agent=jacazul --prompt "Show me project status"
```

### In VS Code / JetBrains / Eclipse / Xcode

1. Open Copilot Chat
2. Click agents dropdown
3. Select your custom agent
4. Submit your prompt

## Agent Naming Conventions

- Use lowercase with hyphens: `my-agent.agent.md`
- Allowed characters: `.`, `-`, `_`, `a-z`, `A-Z`, `0-9`
- Name should reflect purpose: `test-specialist`, `code-reviewer`, `jacazul`

## Examples and Inspiration

- [Copilot Customization Library](https://github.com/github/copilot-customization-library)
- [Awesome Copilot Community](https://github.com/milanm/awesome-copilot)

## Best Practices

1. **Be specific:** Focus agents on single, well-defined tasks
2. **Limit tools:** Only enable tools the agent needs
3. **Clear prompts:** Write detailed instructions and workflows
4. **Test thoroughly:** Verify agent behavior before committing
5. **Document well:** Include examples and usage patterns

## Troubleshooting

**Agent not appearing in list:**
- Verify file ends with `.agent.md`
- Check YAML frontmatter is valid
- Ensure file is in correct directory
- Refresh Copilot CLI or IDE

**Agent behaves unexpectedly:**
- Review prompt for clarity
- Check tool limitations
- Verify environment variables
- Add more specific instructions

## Related Documentation

- [GitHub Docs: Creating Custom Agents](https://docs.github.com/copilot/customizing-copilot/creating-custom-agents)
- [Custom Agents Configuration](https://docs.github.com/copilot/customizing-copilot/custom-agents-configuration)
- [Copilot CLI Documentation](https://docs.github.com/copilot/concepts/agents/about-copilot-cli)

## Contributing

When adding new custom agents to this project:

1. Create agent profile in `templates/agents/`
2. Test locally first
3. Document in this README
4. Follow naming conventions
5. Include usage examples
6. Submit PR with description

---

**Last Updated:** 2026-02-01  
**Agents Count:** 1 (jacazul)
