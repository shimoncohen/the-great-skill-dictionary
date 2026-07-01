# The Great Skill Dictionary

A curated dictionary of **agent skills** — portable instruction packages (folders with a `SKILL.md` file) that extend AI coding agents like Claude Code, Codex, Gemini CLI, and Copilot CLI with new capabilities, workflows, and domain knowledge. Skills follow the open [Agent Skills spec](https://agentskills.io/), which is what makes most of them portable across agents.

Unlike existing skill lists, every entry here records **token cost**, **trigger type**, **agent support**, **maturity**, and **license** — so you can judge what a skill costs you before installing it.

## ⚠️ Disclaimers

- **Token counts are approximations**, marked with `~`. Always-on cost = the skill's name + description injected into the agent's context every turn. On-invoke cost = the full `SKILL.md` loaded when the skill activates. Each category table notes when its counts were measured.
- **Audit before you install.** A skill is a set of instructions injected into your agent's context — a prompt-injection surface. Read a skill's `SKILL.md` before installing it, especially from unfamiliar sources.

## Agent legend

| Code | Agent |
| --- | --- |
| `✅ any` | Plain portable markdown — works in any [spec-compatible](https://agentskills.io/) agent |
| `CC` | Claude Code |
| `CX` | OpenAI Codex |
| `GM` | Gemini CLI |
| `CP` | GitHub Copilot CLI |

Skills marked with codes are known to work on (or are restricted to) those agents; `✅ any` means the skill is plain instructions with no agent-specific dependencies.

## Installing skills

Install is per-agent, not per-skill — a skill is just a folder containing `SKILL.md`:

- **Claude Code:** copy the skill folder to `~/.claude/skills/<name>/` (personal) or `.claude/skills/<name>/` (project), or install a plugin that bundles it via `/plugin`.
- **OpenAI Codex:** copy to `~/.codex/skills/<name>/`.
- **Gemini CLI:** copy to `~/.gemini/skills/<name>/`.
- **Copilot CLI:** copy to `~/.copilot/skills/<name>/`.
- **Any spec-compatible agent:** see the [Agent Skills spec](https://agentskills.io/) for your agent's skill directory.

Check each skill's repository for skill-specific install notes.

## Categories

- [🪙 Token Reduction](#-token-reduction)
- [🛠️ Engineering Workflow](#%EF%B8%8F-engineering-workflow)
- [🧪 Testing](#-testing)
- [🎨 Design & Frontend](#-design--frontend)
- [🌐 Web Development](#-web-development)
- [📚 Documentation](#-documentation)
- [🔒 Security](#-security)
- [🔌 API & Integration](#-api--integration)
- [🧠 Memory & Knowledge](#-memory--knowledge)
- [⚙️ Automation & Scheduling](#%EF%B8%8F-automation--scheduling)
- [🧩 Meta](#-meta)
- [🔍 Research](#-research)
- [📄 Documents](#-documents)
- [💼 Business & Productivity](#-business--productivity)

Also see: [📦 Skill Collections & Registries](#-skill-collections--registries) · [Contributing](#contributing)
