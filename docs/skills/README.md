# Available Skills

Index of skills available in the AI CLI Sandboxed environment.

## 📋 Skills List

### Taskwarrior Expert
**Status:** ✅ Active  
**Version:** 1.2.0  
**Documentation:** [Complete Guide](../taskwarrior-expert.md)

Structured workflow management system with 7-phase workflow and interaction modes.

**Key Features:**
- Dashboard visualization with `ponder`
- Task management with `tw-flow`
- Session continuity and handoffs
- 18 comprehensive tests

**Quick Start:**
```bash
ponder
tw-flow initiative my-feature "EXECUTE|Build API|implementation|today"
```

**Location:** `/project/skills/taskwarrior_expert/`

---

## 🔜 Future Skills

Skills planned for addition:
- Code review automation
- Test generation
- Documentation generation
- Deployment workflows

---

## 🛠 Creating Custom Skills

### Structure
```
skills/my-skill/
├── SKILL.md           # Skill documentation
├── HIERARCHY.md       # (Optional) Conventions
├── scripts/           # Helper scripts
│   ├── main-script
│   ├── test-script.sh
│   └── README.md
└── ...
```

### Requirements
- Clear documentation in SKILL.md
- Executable helper scripts
- Test suite (recommended)
- Examples and usage guide

### Integration
Place skill directory in `/project/skills/` and reference in agent instructions.

---

**Last Updated:** 2026-01-31
