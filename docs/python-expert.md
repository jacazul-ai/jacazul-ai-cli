# Python Expert Skill

Guide for the python-expert skill - a toolset and set of standards for high-quality Python development following PEP 8 and project-specific mandates.

## 🎯 Overview

The python-expert skill enforces strict engineering standards for Python 3.13+ development using:
- **py-check**: A mandatory quality gate tool.
- **Ruff**: The formatter *and* linter. `ruff format` rewrites files; `ruff check` reports and auto-fixes logic issues.
- **Pycodestyle**: For strict adherence to the PEP 8 style guide.
- **Error as Prompt**: Transforming linter failures into actionable instructions.

---

## 🛠 The py-check Tool

The `py-check` command is the central gateway for Python quality in the Jacazul ecosystem.

### Usage
```bash
py-check <path>
```

**Always pass an explicit path.** With no argument the target defaults to `.`,
which reformats every Python file in the repository.

### What it does:
1.  **Auto-Beautify**: Runs `ruff format` to align code with the project's style (79-character lines). **This writes to disk.**
2.  **Logic Check**: Runs `ruff check --fix` to catch and fix common programming errors.
3.  **Style Validation**: Runs `pycodestyle --first` to ensure 100% PEP 8 compliance.
4.  **Instructional Feedback**: If any check fails, it outputs a `💡 PROMPT` with specific instructions on how to fix the violation.

---

## ⚠️ Two Behaviors That Surprise People

### 1. py-check modifies your working tree

`py-check` is not a read-only gate. It formats before it validates, and it
saves the result. Running it with no path reformats the whole repository and
can dirty files that have nothing to do with your task.

**Trigger → Action:**

| You want to | Run |
|---|---|
| Check and fix one file or directory | `py-check path/to/file.py` |
| Check without changing anything | `ruff format --check <path>` then `pycodestyle <path>` |
| See the state before committing | `git status` after any `py-check` run |

### 2. py-check shows one violation per error code

It calls `pycodestyle --first`, which prints only the *first occurrence* of
each error code. One reported `E501` does not mean one long line — it means at
least one.

**Trigger → Action:**

| You want to | Run |
|---|---|
| Fix violations iteratively | `py-check <path>`, fix, repeat until it passes |
| See the complete list at once | `pycodestyle <path>` |

---

## 📋 Engineering Standards

### 1. Line Length
- **Mandate**: All Python code MUST respect a maximum line length of **79 characters**.
- **Reason**: PEP 8 compliance and better readability in CLI/terminal environments.
- **Configured in**: `line-length` in `pyproject.toml`, and the `--line-length=79` flags hardcoded in the `py-check` script. Both must agree.

### 2. Mandatory Verification
- **Protocol**: You MUST run `py-check` before submitting any Python code for review or closing a task.
- **Enforcement**: Tasks involving Python implementation will not be considered complete unless `py-check` passes.

### 3. Error as Prompt Loop
When a linter error occurs, do not just report the error code. Use the mapping provided by `py-check` to understand the required action:
- **E302**: Add 2 blank lines between functions.
- **E501**: Wrap the line at 79 characters. Inside a docstring, comment, or string, wrap the *text* across lines and preserve the original wording.
- **W291**: Remove trailing whitespace.

### 4. What the formatter cannot fix

`ruff format` reflows code, but it never breaks a string literal. Every `E501`
inside a docstring, comment, or string is a manual fix.

Do not split a long string into implicitly concatenated parts and assume it
stays split — `ruff format` rejoins adjacent string literals whenever the
merged line fits within 79 characters. Wrap the text across lines instead:

```python
# Undone by the next py-check run: the parts fit on one line when merged.
msg = ("Standardization: tw-flow plan must not add default "
       "due/priority.")

# Survives: the docstring text is wrapped, not concatenated.
def test_cool_down(self):
    """Standardization: 'tw-flow plan' must not add default
    due/priority and must support hyphens (Fix #37).
    """
```

---

## 🐊 The Python Policy Sentinel

`scripts/python` wraps the interpreter and prints the JACAZUL PYTHON POLICY
ALERT banner on every invocation, reminding you to run `py-check` and load the
skill.

Silence it with `--skill-activated`, which the wrapper consumes before handing
the remaining arguments to Python:

```bash
python --skill-activated script.py
```

**The flag belongs to that wrapper only.** `py-check` performs no argument
parsing and treats whatever you pass as the target path, so
`py-check --skill-activated .` lints a path named `--skill-activated` and
ignores the `.` entirely.

---

## 💡 Best Practices

1.  **Run Early, Run Often**: Run `py-check` frequently during implementation to catch issues before they accumulate.
2.  **Scope the Path**: Point `py-check` at the file or directory you are working on, never at the bare repository root.
3.  **Trust the Formatter for Code**: Let `ruff format` handle indentation and spacing — but expect nothing from it inside strings.
4.  **Manual Wrapping**: Long strings, docstrings, and comments are always yours to break, with the original wording preserved.

---

**Version:** 1.2.0
**Last Updated:** 2026-09-04
