# Context Engine Workflow

How to start any LLM session with beestgraph context.

## Quick Start

```bash
# Default level 1 — identity + daily note + projects + graph stats (~2K tokens)
bg context

# Copy to clipboard for pasting into an LLM chat
bg context --clipboard

# Save to a file
bg context --level 2 --file /tmp/context.md
```

## Context Levels

| Level | Contents | Typical Size | Use When |
|-------|----------|-------------|----------|
| 0 | identity.md only | ~500 tokens | Quick question, LLM already knows the system |
| 1 | identity + daily note + top 3 projects + graph stats | ~2K tokens | Default for most sessions |
| 2 | Level 1 + last 7 daily notes + task board + recent log | ~5K tokens | Planning sessions, weekly reviews |
| 3 | Level 2 + full project READMEs + full graph stats + queue items | ~15K tokens | Deep work sessions, onboarding a new LLM |

## Recommended Workflow

1. **Start a new LLM session** (Claude, ChatGPT, Ollama, etc.)
2. **Run:** `bg context --level 1 --clipboard`
3. **Paste** the context as your first message
4. **Continue** with your question or task — the LLM now understands
   your current projects, recent work, and graph state

## Keeping identity.md Current

`identity.md` lives at `~/vault/identity.md`. It is the only file in
the context engine that you maintain manually. Update it when:

- Your role or focus changes
- You start or finish a major project
- You make a significant architectural decision
- Your LLM communication preferences evolve

Target length: under 1KB. This is a summary, not a journal.

To create it for the first time:

```bash
bg init --identity
```

Then edit `~/vault/identity.md` in Obsidian or any text editor.
