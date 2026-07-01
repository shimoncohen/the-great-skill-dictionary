# Agent Skill Dictionary — Design

**Date:** 2026-07-01
**Status:** Approved in brainstorming session

## Purpose

A single hand-maintained `README.md` cataloguing agent skills (portable SKILL.md instruction packages) across categories, so users can discover skills, judge their token cost, and find where to get them. Discovery ease is the primary goal — everything lives in one file.

## Decisions Made

| Decision | Choice |
| --- | --- |
| Structure | Hand-written single README (no generation tooling) |
| Agent display | `✅ any` default for portable skills; short codes for exceptions/tested-on, with legend |
| Cost display | Approximate raw token counts (`~` prefix), on-invoke + always-on, per-category "as of" date footnote |
| Cost disclaimer | Explicit statement that counts are approximations |
| Sorting | Rows sorted alphabetically by skill name |
| Per-agent index | Skipped for now |
| Category cost ranking | Dropped |
| Install command column | Dropped — replaced by one "Installing skills" prose section (install is per-agent, not per-skill) |
| Seed content | Real skills from user's installed set + well-known public skills |
| Empty categories | Shown with placeholder text inviting contribution |

## Files

- `README.md` — the dictionary
- `CONTRIBUTING.md` — row template + how to PR a new skill

## README Structure

1. **Title + intro** — what this is; what an "agent skill" is (portable markdown instruction package loaded by coding agents); link to the open [agentskills.io](https://agentskills.io/) spec, which explains the portability behind `✅ any`
2. **Disclaimers** —
   - token counts are approximations, marked `~`; each category table has an "as of" measurement date footnote
   - security caution: skills are instructions injected into your agent's context (a prompt-injection surface) — audit a skill before installing it
3. **Agent legend** — `CC` = Claude Code, `CX` = Codex, `GM` = Gemini CLI, `CP` = Copilot CLI, `✅ any` = plain portable markdown, works in any SKILL.md-compatible agent
4. **Installing skills** — short per-agent instructions (paths/commands), written once
5. **TOC** — clickable anchors to each category
6. **Categories** — each has:
   - Header (emoji + name)
   - 1–2 sentence category description
   - Table, rows sorted by name
   - Footnote: `*Token counts approximate, measured as of YYYY-MM.*`
   - If empty: placeholder text `No skills catalogued yet — [contribute](#contributing)!`

## Table Columns

| Skill | Description | Trigger | Agents | Cost ~(invoke / always-on) | Maturity | License | Repo |

- **Trigger:** `manual` (slash command) / `auto` (model decides) / `always-on` (hook or system-level)
- **Agents:** `✅ any` or code list (`CC · CX`)
- **Cost:** `~2.1k / ~150` — tokens loaded on invoke / tokens present every turn
- **Maturity:** `stable` / `beta` / `experimental` / `archived`
- **License:** SPDX short form (MIT, Apache-2.0, …). Skills that are visible on GitHub but not open source (e.g. Anthropic's pdf/docx/pptx/xlsx document skills — usable only within Claude) are marked `Source-available*` with a footnote explaining the restriction. Protects readers from assuming "on GitHub = free to use anywhere."
- **Repo:** markdown link to source repository

## Categories (shown even when empty)

1. 🪙 Token Reduction
2. 🛠️ Engineering Workflow (TDD, debugging, planning, code review)
3. 🧪 Testing
4. 🎨 Design & Frontend
5. 🌐 Web Development
6. 📚 Documentation
7. 🔒 Security
8. 🔌 API & Integration
9. 🧠 Memory & Knowledge
10. ⚙️ Automation & Scheduling
11. 🧩 Meta (skill/plugin/agent development)
12. 🔍 Research
13. 📄 Documents (pdf/docx/pptx/xlsx creation and editing)
14. 💼 Business & Productivity (marketing, PM, comms — non-dev skills)

## Skill Collections & Registries Section

Placed after the category tables, before contributing. Purpose: further discovery and research — NOT a substitute for category rows. A skill that belongs to a collection still gets its own row in the appropriate category; this section only points at places to browse for more.

Two small tables:

1. **Collections** — multi-skill repos: | Repo | Description | License | Link |
   - e.g. anthropics/skills (official), obra/superpowers, trailofbits/skills, vercel-labs/skills, alirezarezvani/claude-skills
2. **Registries & lists** — searchable directories: | Name | Type (registry / awesome-list / marketplace) | Link |
   - e.g. skills.sh, SkillsMP, SkillHub, heilcheng/awesome-agent-skills, travisvn/awesome-claude-skills

No skill counts — they drift and add no decision value.

## Seed Content

Populate from user's installed set and known public skills:

- User's installed set: superpowers suite (brainstorming, TDD, systematic-debugging, writing-plans…), caveman suite, postman skills, ruflo plugin skills, skill-creator, graphify, karpathy-guidelines, deep-research
- anthropics/skills official 17 (skill-creator, mcp-builder, webapp-testing, frontend-design, pdf/docx/pptx/xlsx `Source-available*`, …) — Apache-2.0 except document skills
- obra/superpowers (MIT), trailofbits/skills security pack (CC-BY-SA-4.0), vercel-labs/skills (find-skills, react-best-practices — MIT), laravel/boost (MIT)

Always-on costs can be seeded from the session `/context` output (description tokens per skill); invoke costs estimated from SKILL.md sizes.

## CONTRIBUTING.md

- Row template matching the 8 columns
- Rules: alphabetical placement, `~` on token counts, how to measure (rough: words × 1.3), pick correct category, one row per skill
- Note on updating the category "as of" date when costs are re-measured

## Out of Scope (deferred ideas)

- Data-backed generation (YAML per skill + script) — migration path if maintenance hurts
- Per-agent reverse index
- Cost ranking sections
- Automated cost-measurement script
