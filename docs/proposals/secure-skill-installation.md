# Proposal: Secure Skill Installation

**Status:** Proposal, not implemented.
**Audience:** Contributors and agents.
**Related:** `docs/ARCHITECTURE.md` (Security & Isolation), `security-expert`.

## Problem

A skill is a Markdown file that an agent reads as instructions, sometimes
with scripts next to it. For a language model, text is executable: a
skill can tell the agent to read `~/.ssh`, send data to a URL, skip the
commit gate, or push to a remote. Today every bootstrap does the same
thing with the `skills/` directory:

```bash
for skill_dir in "$PROJECT_ROOT/skills"/*; do
    [ -f "$skill_dir/SKILL.md" ] || continue
    ln -sfn -- "$skill_dir" "$SKILLS_DIR/$name"
done
```

Nothing checks who wrote the file, whether it changed since it was
reviewed, what it asks the agent to do, or whether it ships scripts. This
is fine while every skill comes from this repository and is reviewed as
code. It stops being fine the moment skills are shared between people or
installed from an index.

## Threat model

| Threat | Vector | Blast radius |
|---|---|---|
| Prompt injection in the skill body | Visible text, HTML comments, invisible Unicode (zero-width, RTL override, homoglyphs), long base64, instructions phrased as "before anything else" | Exfiltration of secrets and code, disabled gates, unwanted git operations, destructive commands |
| Embedded scripts | A `scripts/` directory or a referenced executable that runs with the user's privileges | Arbitrary code execution at use time |
| Post-install tampering | The installed skill is a symlink into a directory anyone can edit; what was reviewed is not what loads tomorrow | Same as injection, delayed |
| Over-reaching but honest skills | Instructions that ask for destructive or privileged actions without need | Accidental damage, normalized bypassing of gates |
| Impersonation | A skill named like an official one (`git-expert`) from an untrusted source | Trust transferred to hostile content |

A skill cannot grant itself more than the harness allows (tool
permissions, sandbox, the broker vault). That containment is the last
layer, not the first.

## Design

Seven layers, each cheap, each catching a different threat. The first two
close the most likely threats without any signing infrastructure.

### 1. Content lint (`jacazul-skill lint`)

A static check over every `SKILL.md` and companion file:

- frontmatter present, `name` equals the directory name, `description`
  bounded in length, no unknown top-level keys;
- size limit per file and per skill;
- no invisible or bidirectional Unicode, no HTML comments, no base64 or
  hex blobs above a small length;
- denied instruction patterns: reading `~/.ssh`, `~/.aws`, environment
  tokens or the vault; `curl | sh`; `rm -rf` on roots or variables;
  `--force` pushes and history rewrites; "ignore the system prompt",
  "do not tell the user", "disable the gate"; requests to contact URLs
  other than documentation domains;
- referenced scripts must be declared in the manifest (layer 3) with a
  hash.

Findings use the shared `code-review` scale. The lint runs in this
repository's test suite over every bundled skill, so the rules are
dogfooded before they judge anyone else's work.

### 2. Lockfile (`skills.lock`)

An installed skill is recorded with the hash of every file it contains
and the trust tier it was installed under. Bootstraps link only skills
present in the lock whose hashes still match. A changed file is refused
with an Error as Prompt: what changed, how to re-approve
(`jacazul-skill lock <name>` after review). This turns the symlink from a
live wire into a reviewed snapshot.

### 3. Capability manifest

A skill declares what it needs in its frontmatter or a `skill.toml`:
scripts it ships (path and hash), tools it expects, network access,
whether it writes to the working tree. The installer prints the
declaration and asks for consent, the way a package manager prints
permissions. Scripts not declared are not made executable. A skill that
declares more than its body uses is a lint finding.

### 4. Provenance and signing

Bundles are signed by their author (`ssh-keygen -Y sign` with a known
key, or a sigstore identity) and published in an index that maps
`name@version` to a hash and a signature. `jacazul-skill install` verifies
before writing anything. Key management reuses what the project already
has: the vault for private material, a public `allowed_signers` file in
the repository for maintainers.

### 5. Trust tiers

| Tier | Source | Shown as |
|---|---|---|
| `bundled` | This repository, signed by maintainers | default, no badge |
| `community` | An index entry with a valid signature | `[community]` in the engine banner |
| `local` | Written by the user, unsigned | `[local]` in the engine banner |
| `unverified` | Anything else | refused unless `--unsafe` is passed once, with a warning |

The engine states the tier when it activates a skill, so the user knows
whose instructions are running.

### 6. Prompt review

A new skill from outside the `bundled` tier goes through a `[REVIEW]`
with the `security-expert` lens before it is locked: what it asks for,
what it can reach, what it hides. Findings use the shared scale; a
`BLOCKER` prevents the lock.

### 7. Harness containment

Independent of the layers above, the harness keeps its own limits:
permission prompts, sandboxing, the broker as the sole GitHub authority,
no raw `task`. A skill can ask; the harness decides.

## Command surface

```bash
jacazul-skill lint [path]          # content lint; used by tests on bundled skills
jacazul-skill lock <name>          # record hashes and tier after review
jacazul-skill verify [name]        # compare installed files to the lock
jacazul-skill install <ref>        # fetch, verify signature, lint, review, lock, link
jacazul-skill list                 # installed skills with tier and lock state
```

Bootstraps replace the blind loop with `jacazul-skill verify` and link
only what passes; `DRY=true` and `DEBUG=true` behave as everywhere else.

## Rollout

1. Lint and lock, with the lint running in CI over the bundled skills
   (closes injection and tampering for everything that exists today).
2. Manifest and the consent step in the installer.
3. Trust tiers in the engine banner and the bootstraps.
4. Signing and the index, when there is a second party to sign for.

Each step is independently useful and reversible: removing the lock file
restores today's behavior.

## Open questions

- Which tool builds the Unicode and pattern rules: a small Python module
  (consistent with `py-mode`, `js-mode`, `sh-census`) or a reuse of an
  existing scanner?
- Whether the lock lives per project (`.jacazul/skills.lock`) or per user
  (`~/.jacazul-ai/skills.lock`); probably both, project first.
- How generated skills (`jacazul-engine` from hatch templates) are
  locked: hash the template inputs, not the rendered output.
