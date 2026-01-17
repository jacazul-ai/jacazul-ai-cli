# Copilot Global Context

## Formatting and Output
- Always generate technical tickets, tasks and project documentation in
  Markdown (.md) format.
- Maintain a consistent structure: Title, Description, Tasks and Acceptance
  Criteria.
- Keep answers short and concise; avoid flattery and unnecessary information.

## Language Handling
- Respond in the same language as the user (language-switch): if addressed in
  Portuguese, reply in Portuguese; if in English, reply in English.
- If the user is chatting in Portuguese and requests code, comments or tickets,
  generate them in English unless explicitly asked for another language.
- All code, comments and tickets must be in English unless otherwise requested.

## Context and Behavior
- If a message ends with 'ack', simply acknowledge and build context.
- When the user is building context, do not provide information unless given
  clear instructions.

## Git Commit Messages
- Commit messages must follow the Conventional Commits specification
  (https://www.conventionalcommits.org/), using types like feat, fix, chore,
  build, docs, etc.
- The commit message title must be up to 50 characters, and the body lines must
  be wrapped at 72 characters.
