# The Great Skill Dictionary

[![Awesome](https://awesome.re/badge.svg)](https://awesome.re)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](CONTRIBUTING.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)
[![Last commit](https://img.shields.io/github/last-commit/shimoncohen/the-great-skill-dictionary?style=flat-square)](https://github.com/shimoncohen/the-great-skill-dictionary/commits/main)

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

## Reading the tables

- **Trigger** — how the skill activates: `manual` (you run a slash command), `auto` (the agent activates it when relevant), `always-on` (hook or system-level, active every turn).
- **Cost ~(invoke / always-on)** — approximate token counts: what loading the full skill costs when it activates / what its name + description cost in context every turn. See the [disclaimers](#%EF%B8%8F-disclaimers).
- **Maturity** — `stable` / `beta` / `experimental` / `archived`, judged from repo activity and docs.

## Installing skills

Install is per-agent, not per-skill — a skill is just a folder containing `SKILL.md`:

- **Claude Code:** copy the skill folder to `~/.claude/skills/<name>/` (personal) or `.claude/skills/<name>/` (project), or install a plugin that bundles it via `/plugin`.
- **OpenAI Codex:** copy to `~/.codex/skills/<name>/`.
- **Gemini CLI:** copy to `~/.gemini/skills/<name>/`.
- **Copilot CLI:** copy to `~/.copilot/skills/<name>/`.
- **Any spec-compatible agent:** see the [Agent Skills spec](https://agentskills.io/) for your agent's skill directory.

Directory conventions may change between agent versions — check your agent's docs, and each skill's repository for skill-specific install notes.

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

## 🪙 Token Reduction

Skills that cut token usage — compressed communication styles, output trimming, and context-saving delegation patterns.

| Skill | Description | Trigger | Agents | Cost ~(invoke / always-on) | Maturity | License | Repo |
| --- | --- | --- | --- | --- | --- | --- | --- |
| caveman | Compressed replies, ~75% fewer output tokens, full technical accuracy kept | manual | ✅ any | ~880 / ~70 | stable | MIT | [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman) |

*Token counts approximate, measured as of 2026-07.*

## 🛠️ Engineering Workflow

Process discipline for day-to-day development: brainstorming, planning, TDD, debugging, and code review workflows.

| Skill | Description | Trigger | Agents | Cost ~(invoke / always-on) | Maturity | License | Repo |
| --- | --- | --- | --- | --- | --- | --- | --- |
| brainstorming | Turns ideas into validated designs through collaborative dialogue before any code | auto | ✅ any | ~2k / ~40 | stable | MIT | [obra/superpowers](https://github.com/obra/superpowers) |
| karpathy-guidelines | Behavioral guardrails against common LLM coding mistakes: overcomplication, non-surgical edits | auto | ✅ any | ~480 / ~40 | stable | — | [andrej-karpathy-skills](https://github.com/forrestchang/andrej-karpathy-skills) |
| systematic-debugging | Root-cause-first debugging discipline; forbids guess-and-check fixes | auto | ✅ any | ~2k / ~20 | stable | MIT | [obra/superpowers](https://github.com/obra/superpowers) |
| test-driven-development | Red-green-refactor loop enforcement for every feature and bugfix | auto | ✅ any | ~1.9k / ~20 | stable | MIT | [obra/superpowers](https://github.com/obra/superpowers) |
| writing-plans | Produces bite-sized, zero-context implementation plans from specs | auto | ✅ any | ~1.4k / ~20 | stable | MIT | [obra/superpowers](https://github.com/obra/superpowers) |

*Token counts approximate, measured as of 2026-07.*

## 🧪 Testing

Test authoring, coverage analysis, and app-level verification.

| Skill | Description | Trigger | Agents | Cost ~(invoke / always-on) | Maturity | License | Repo |
| --- | --- | --- | --- | --- | --- | --- | --- |
| webapp-testing | Drives and tests local web apps with Playwright | auto | CC | ~650 / ~30 | stable | Apache-2.0 | [anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/webapp-testing) |

*Token counts approximate, measured as of 2026-07.*

## 🎨 Design & Frontend

Visual design quality, UI component work, and frontend best practices.

| Skill | Description | Trigger | Agents | Cost ~(invoke / always-on) | Maturity | License | Repo |
| --- | --- | --- | --- | --- | --- | --- | --- |
| frontend-design | Produces distinctive, production-grade frontend interfaces instead of generic AI styling | auto | ✅ any | ~1.7k / ~40 | stable | Apache-2.0 | [anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/frontend-design) |
| react-best-practices | React and Next.js performance patterns from the Vercel team | auto | ✅ any | ~1.2k / ~60 | stable | MIT | [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills/tree/main/skills/react-best-practices) |
| theme-factory | Toolkit for styling artifacts with a theme. These artifacts can be slides, docs, reportings, HTML landing pages, etc. There are 10 pre-set themes with colors/fonts that you can apply to any artifact that has been creating, or can generate a new theme on-the-fly | auto | ✅ any | ~630 / ~60 | stable | — | [anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/theme-factory) |

*Token counts approximate, measured as of 2026-07.*

## 🌐 Web Development

Building and shipping web applications end to end.

| Skill | Description | Trigger | Agents | Cost ~(invoke / always-on) | Maturity | License | Repo |
| --- | --- | --- | --- | --- | --- | --- | --- |
| web-artifacts-builder | Generates code for elaborate claude.ai artifacts using React and Tailwind | auto | CC | ~580 / ~50 | stable | Apache-2.0 | [anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/web-artifacts-builder) |

*Token counts approximate, measured as of 2026-07.*

## 📚 Documentation

Writing, generating, and maintaining docs.

| Skill | Description | Trigger | Agents | Cost ~(invoke / always-on) | Maturity | License | Repo |
| --- | --- | --- | --- | --- | --- | --- | --- |
| doc-coauthoring | Structured doc co-writing workflow: context gathering, drafting, reader-testing | auto | ✅ any | ~3.2k / ~80 | stable | Apache-2.0 | [anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/doc-coauthoring) |

*Token counts approximate, measured as of 2026-07.*

## 🔒 Security

Auditing, vulnerability hunting, and secure-coding review.

| Skill | Description | Trigger | Agents | Cost ~(invoke / always-on) | Maturity | License | Repo |
| --- | --- | --- | --- | --- | --- | --- | --- |
| differential-review | Security-focused review of diffs: hunts vulnerabilities introduced by a change | auto | CC · CX | ~1.3k / ~50 | stable | CC-BY-SA-4.0 | [trailofbits/skills](https://github.com/trailofbits/skills/tree/main/plugins/differential-review/skills/differential-review) |
| semgrep | Authors and refines Semgrep static-analysis rules | auto | CC · CX | ~1.8k / ~90 | stable | CC-BY-SA-4.0 | [trailofbits/skills](https://github.com/trailofbits/skills/tree/main/plugins/static-analysis/skills/semgrep) |

*Token counts approximate, measured as of 2026-07.*

## 🔌 API & Integration

APIs, MCP servers, and service integration.

| Skill | Description | Trigger | Agents | Cost ~(invoke / always-on) | Maturity | License | Repo |
| --- | --- | --- | --- | --- | --- | --- | --- |
| mcp-builder | Guides building MCP servers in Python or TypeScript | auto | ✅ any | ~1.5k / ~50 | stable | Apache-2.0 | [anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/mcp-builder) |

*Token counts approximate, measured as of 2026-07.*

## 🧠 Memory & Knowledge

Persistent memory, knowledge graphs, and recall across sessions.

No skills catalogued yet — [contribute](#contributing)!

## ⚙️ Automation & Scheduling

Recurring tasks, background workers, and scheduled agent runs.

No skills catalogued yet — [contribute](#contributing)!

## 🧩 Meta

Skills for making skills: skill/plugin/agent development and skill discovery.

| Skill | Description | Trigger | Agents | Cost ~(invoke / always-on) | Maturity | License | Repo |
| --- | --- | --- | --- | --- | --- | --- | --- |
| find-skills | Discovers and installs skills from the open ecosystem when you ask "how do I X" | auto | ✅ any | ~1.1k / ~70 | stable | MIT | [vercel-labs/skills](https://github.com/vercel-labs/skills/tree/main/skills/find-skills) |
| skill-creator | Guides creating, structuring, and packaging new skills | auto | ✅ any | ~6.8k / ~60 | stable | Apache-2.0 | [anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/skill-creator) |
| writing-skills | Best practices for authoring and testing skills, TDD-style | auto | ✅ any | ~4.9k / ~20 | stable | MIT | [obra/superpowers](https://github.com/obra/superpowers) |

*Token counts approximate, measured as of 2026-07.*

## 🔍 Research

Multi-source research, fact-checking, and synthesis.

No skills catalogued yet — [contribute](#contributing)!

## 📄 Documents

Creating and editing office documents: PDF, Word, PowerPoint, Excel.

| Skill | Description | Trigger | Agents | Cost ~(invoke / always-on) | Maturity | License | Repo |
| --- | --- | --- | --- | --- | --- | --- | --- |
| docx | Creates and edits Word documents with tracked changes | auto | CC | ~3.4k / ~150 | stable | Source-available† | [anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/docx) |
| pdf | Generates and manipulates PDFs: forms, merging, extraction | auto | CC | ~1.3k / ~90 | stable | Source-available† | [anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/pdf) |
| pptx | Creates and edits PowerPoint presentations | auto | CC | ~1.8k / ~140 | stable | Source-available† | [anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/pptx) |
| xlsx | Creates and edits Excel spreadsheets with formulas | auto | CC | ~2.1k / ~200 | stable | Source-available† | [anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/xlsx) |

*Token counts approximate, measured as of 2026-07.*

†**Source-available, not open source:** code is visible on GitHub but licensed for use within Claude products only — not free to port to other agents or redistribute. "On GitHub" ≠ "free to use anywhere"; check the license before reuse.

## 💼 Business & Productivity

Non-dev skills: marketing, product management, comms, and brand work.

| Skill | Description | Trigger | Agents | Cost ~(invoke / always-on) | Maturity | License | Repo |
| --- | --- | --- | --- | --- | --- | --- | --- |
| brand-guidelines | Applies Anthropic brand colors and typography to artifacts | auto | ✅ any | ~430 / ~50 | stable | Apache-2.0 | [anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/brand-guidelines) |
| internal-comms | Drafts status reports, newsletters, and FAQs in a consistent internal voice | auto | ✅ any | ~270 / ~70 | stable | Apache-2.0 | [anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/internal-comms) |

*Token counts approximate, measured as of 2026-07.*

## 📦 Skill Collections & Registries

For further discovery and research. Skills found here are candidates for their own row in a category above once curated — these are places to browse for more.

### Collections

| Repo | Description | Stars | License | Link |
| --- | --- | --- | --- | --- |
| addyosmani/agent-skills | Production-grade engineering skills for AI coding agents from Addy Osmani | ![Stars](https://img.shields.io/github/stars/addyosmani/agent-skills?style=flat-square&label=%E2%AD%90) | MIT | [GitHub](https://github.com/addyosmani/agent-skills) |
| alirezarezvani/claude-skills | Large community skill pack, explicitly multi-agent portable | ![Stars](https://img.shields.io/github/stars/alirezarezvani/claude-skills?style=flat-square&label=%E2%AD%90) | — | [GitHub](https://github.com/alirezarezvani/claude-skills) |
| anthropics/skills | Anthropic's official example skills and skill spec template | ![Stars](https://img.shields.io/github/stars/anthropics/skills?style=flat-square&label=%E2%AD%90) | Apache-2.0 / Source-available† | [GitHub](https://github.com/anthropics/skills) |
| obra/superpowers | Software-engineering methodology pack: TDD, debugging, planning workflows | ![Stars](https://img.shields.io/github/stars/obra/superpowers?style=flat-square&label=%E2%AD%90) | MIT | [GitHub](https://github.com/obra/superpowers) |
| tech-leads-club/agent-skills | Validated and security-reviewed skill library for professional coding agents | ![Stars](https://img.shields.io/github/stars/tech-leads-club/agent-skills?style=flat-square&label=%E2%AD%90) | — | [GitHub](https://github.com/tech-leads-club/agent-skills) |
| trailofbits/skills | Security-audit skills from Trail of Bits | ![Stars](https://img.shields.io/github/stars/trailofbits/skills?style=flat-square&label=%E2%AD%90) | CC-BY-SA-4.0 | [GitHub](https://github.com/trailofbits/skills) |
| vercel-labs/skills | Vercel's skill collection and registry CLI | ![Stars](https://img.shields.io/github/stars/vercel-labs/skills?style=flat-square&label=%E2%AD%90) | MIT | [GitHub](https://github.com/vercel-labs/skills) |

*†See the Source-available note in the [📄 Documents](#-documents) section.*

### Registries & lists

| Name | Type | Stars | Link |
| --- | --- | --- | --- |
| awesome-agent-skills (heilcheng) | awesome-list | ![Stars](https://img.shields.io/github/stars/heilcheng/awesome-agent-skills?style=flat-square&label=%E2%AD%90) | [GitHub](https://github.com/heilcheng/awesome-agent-skills) |
| awesome-agent-skills (VoltAgent) | awesome-list | ![Stars](https://img.shields.io/github/stars/VoltAgent/awesome-agent-skills?style=flat-square&label=%E2%AD%90) | [GitHub](https://github.com/VoltAgent/awesome-agent-skills) |
| awesome-claude-skills (travisvn) | awesome-list | ![Stars](https://img.shields.io/github/stars/travisvn/awesome-claude-skills?style=flat-square&label=%E2%AD%90) | [GitHub](https://github.com/travisvn/awesome-claude-skills) |
| SkillHub | marketplace | — | [skillhub.club](https://www.skillhub.club/) |
| skills.sh | registry | — | [skills.sh](https://www.skills.sh/) |
| SkillsMP | registry | — | [skillsmp.com](https://skillsmp.com/) |

## Contributing

Want to add a skill? Preferred: open a [Skill submission issue](../../issues/new?template=skill-submission.yml) — automation infers the details and opens a PR for review. Manual PRs also welcome; see [CONTRIBUTING.md](CONTRIBUTING.md) for the row template and rules.
