# Python Expert Skill

Guide for the python-expert skill - a toolset and set of standards for high-quality Python development following PEP 8 and project-specific mandates.

## 🎯 Overview

The python-expert skill enforces strict engineering standards for Python 3.13+ development using:
- **py-check**: A mandatory quality gate tool.
- **Ruff**: For fast linting, logic checks, and auto-formatting.
- **Pycodestyle**: For strict adherence to the PEP 8 style guide.
- **Error as Prompt**: Transforming linter failures into actionable instructions.

---

## 🛠 The py-check Tool

The `py-check` command is the central gateway for Python quality in the Jacazul ecosystem.

### Usage
```bash
py-check [path]
```
*If no path is provided, it defaults to the current directory.*

### What it does:
1.  **Auto-Beautify**: Runs `ruff format` to align code with the project's style (79-character lines).
2.  **Logic Check**: Runs `ruff check --fix` to catch and fix common programming errors.
3.  **Style Validation**: Runs `pycodestyle` to ensure 100% PEP 8 compliance.
4.  **Instructional Feedback**: If any check fails, it outputs a `💡 PROMPT` with specific instructions on how to fix the violation.

---

## 📋 Engineering Standards

### 1. Line Length
- **Mandate**: All Python code MUST respect a maximum line length of **79 characters**.
- **Reason**: PEP 8 compliance and better readability in CLI/terminal environments.

### 2. Mandatory Verification
- **Protocol**: You MUST run `py-check` before submitting any Python code for review or closing a task.
- **Enforcement**: Tasks involving Python implementation will not be considered complete unless `py-check` passes.

### 3. Error as Prompt Loop
When a linter error occurs, do not just report the error code. Use the mapping provided by `py-check` to understand the required action:
- **E302**: Add 2 blank lines between functions.
- **E501**: Wrap the line at 79 characters (use implicit string concatenation for long strings/f-strings).
- **W291**: Remove trailing whitespace.

---

## 💡 Best Practices

1.  **Run Early, Run Often**: Run `py-check` frequently during implementation to catch issues before they accumulate.
2.  **Trust the Formatter**: Let `ruff format` handle most of the heavy lifting for indentation and spacing.
3.  **Manual Wrapping**: For very long strings or complex logic, you may need to manually break lines to satisfy the 79-character limit.

---

**Version:** 1.1.0  
**Last Updated:** 2026-03-03
