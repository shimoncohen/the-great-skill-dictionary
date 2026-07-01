# Agent Skill Dictionary README Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build phase 1 of the skill dictionary — a hand-maintained `README.md` cataloguing agent skills with categories, cost data, and discovery pointers, plus a `CONTRIBUTING.md`.

**Architecture:** Two markdown files, no tooling. README = title/intro → disclaimers → agent legend → installing section → TOC → 14 category sections (description + name-sorted table or empty placeholder) → collections & registries section → contributing pointer. Spec: `docs/superpowers/specs/2026-07-01-skill-dictionary-design.md`.

**Tech Stack:** GitHub-flavored markdown only. Verification via grep/python3 one-liners (anchor and column checks).

---

### Task 1: README header — title, intro, disclaimers, legend, installing, TOC

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write the file with header content**

Create `README.md` with exactly this content:

````markdown
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
````

- [ ] **Step 2: Verify file renders and TOC list is complete**

Run: `grep -c '^- \[' README.md`
Expected: `14`

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "Add README header: intro, disclaimers, legend, installing, TOC"
```

### Task 2: Category sections with descriptions and seed skills

**Files:**
- Modify: `README.md` (append)

Column format for every table (8 columns):

```markdown
| Skill | Description | Trigger | Agents | Cost ~(invoke / always-on) | Maturity | License | Repo |
| --- | --- | --- | --- | --- | --- | --- | --- |
```

- Trigger values: `manual` / `auto` / `always-on`. Maturity: `stable` / `beta` / `experimental` / `archived`. Unknown license: `—`.
- Every populated table ends with footnote: `*Token counts approximate, measured as of 2026-07.*`
- Empty category placeholder line: `No skills catalogued yet — [contribute](#contributing)!`
- Rows sorted alphabetically by skill name.

- [ ] **Step 1: Append all 14 category sections**

Append exactly this content to `README.md`:

````markdown

## 🪙 Token Reduction

Skills that cut token usage — compressed communication styles, output trimming, and context-saving delegation patterns.

| Skill | Description | Trigger | Agents | Cost ~(invoke / always-on) | Maturity | License | Repo |
| --- | --- | --- | --- | --- | --- | --- | --- |
| caveman | Compressed replies, ~75% fewer output tokens, full technical accuracy kept | manual | ✅ any | ~2k / ~140 | stable | MIT | [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman) |

*Token counts approximate, measured as of 2026-07.*

## 🛠️ Engineering Workflow

Process discipline for day-to-day development: brainstorming, planning, TDD, debugging, and code review workflows.

| Skill | Description | Trigger | Agents | Cost ~(invoke / always-on) | Maturity | License | Repo |
| --- | --- | --- | --- | --- | --- | --- | --- |
| brainstorming | Turns ideas into validated designs through collaborative dialogue before any code | auto | ✅ any | ~1.5k / ~80 | stable | MIT | [obra/superpowers](https://github.com/obra/superpowers) |
| karpathy-guidelines | Behavioral guardrails against common LLM coding mistakes: overcomplication, non-surgical edits | auto | ✅ any | ~1k / ~90 | stable | — | [andrej-karpathy-skills](https://github.com/forrestchang/andrej-karpathy-skills) |
| systematic-debugging | Root-cause-first debugging discipline; forbids guess-and-check fixes | auto | ✅ any | ~1.5k / ~40 | stable | MIT | [obra/superpowers](https://github.com/obra/superpowers) |
| test-driven-development | Red-green-refactor loop enforcement for every feature and bugfix | auto | ✅ any | ~2k / ~40 | stable | MIT | [obra/superpowers](https://github.com/obra/superpowers) |
| writing-plans | Produces bite-sized, zero-context implementation plans from specs | auto | ✅ any | ~1.5k / ~40 | stable | MIT | [obra/superpowers](https://github.com/obra/superpowers) |

*Token counts approximate, measured as of 2026-07.*

## 🧪 Testing

Test authoring, coverage analysis, and app-level verification.

| Skill | Description | Trigger | Agents | Cost ~(invoke / always-on) | Maturity | License | Repo |
| --- | --- | --- | --- | --- | --- | --- | --- |
| webapp-testing | Drives and tests local web apps with Playwright | auto | CC | ~2.5k / ~60 | stable | Apache-2.0 | [anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/webapp-testing) |

*Token counts approximate, measured as of 2026-07.*

## 🎨 Design & Frontend

Visual design quality, UI component work, and frontend best practices.

| Skill | Description | Trigger | Agents | Cost ~(invoke / always-on) | Maturity | License | Repo |
| --- | --- | --- | --- | --- | --- | --- | --- |
| frontend-design | Produces distinctive, production-grade frontend interfaces instead of generic AI styling | auto | ✅ any | ~1.5k / ~70 | stable | Apache-2.0 | [anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/frontend-design) |
| react-best-practices | React and Next.js performance patterns from the Vercel team | auto | ✅ any | ~3k / ~60 | stable | MIT | [vercel-labs/skills](https://github.com/vercel-labs/skills) |

*Token counts approximate, measured as of 2026-07.*

## 🌐 Web Development

Building and shipping web applications end to end.

| Skill | Description | Trigger | Agents | Cost ~(invoke / always-on) | Maturity | License | Repo |
| --- | --- | --- | --- | --- | --- | --- | --- |
| web-artifacts-builder | Builds elaborate multi-component claude.ai artifacts with React and Tailwind | auto | CC | ~2k / ~70 | stable | Apache-2.0 | [anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/web-artifacts-builder) |

*Token counts approximate, measured as of 2026-07.*

## 📚 Documentation

Writing, generating, and maintaining docs.

| Skill | Description | Trigger | Agents | Cost ~(invoke / always-on) | Maturity | License | Repo |
| --- | --- | --- | --- | --- | --- | --- | --- |
| doc-coauthoring | Structured doc co-writing workflow: context gathering, drafting, reader-testing | auto | ✅ any | ~2k / ~90 | stable | Apache-2.0 | [anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/doc-coauthoring) |

*Token counts approximate, measured as of 2026-07.*

## 🔒 Security

Auditing, vulnerability hunting, and secure-coding review.

| Skill | Description | Trigger | Agents | Cost ~(invoke / always-on) | Maturity | License | Repo |
| --- | --- | --- | --- | --- | --- | --- | --- |
| differential-review | Security-focused review of diffs: hunts vulnerabilities introduced by a change | auto | CC · CX | ~2k / ~60 | stable | CC-BY-SA-4.0 | [trailofbits/skills](https://github.com/trailofbits/skills) |
| semgrep-rule-writing | Authors and refines Semgrep static-analysis rules | auto | CC · CX | ~2.5k / ~60 | stable | CC-BY-SA-4.0 | [trailofbits/skills](https://github.com/trailofbits/skills) |

*Token counts approximate, measured as of 2026-07.*

## 🔌 API & Integration

APIs, MCP servers, and service integration.

| Skill | Description | Trigger | Agents | Cost ~(invoke / always-on) | Maturity | License | Repo |
| --- | --- | --- | --- | --- | --- | --- | --- |
| mcp-builder | Guides building MCP servers in Python or TypeScript | auto | ✅ any | ~3k / ~70 | stable | Apache-2.0 | [anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/mcp-builder) |

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
| find-skills | Discovers and installs skills from the open ecosystem when you ask "how do I X" | auto | ✅ any | ~1k / ~110 | stable | MIT | [vercel-labs/skills](https://github.com/vercel-labs/skills/tree/main/skills/find-skills) |
| skill-creator | Guides creating, structuring, and packaging new skills | auto | ✅ any | ~3k / ~120 | stable | Apache-2.0 | [anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/skill-creator) |
| writing-skills | Best practices for authoring and testing skills, TDD-style | auto | ✅ any | ~2k / ~40 | stable | MIT | [obra/superpowers](https://github.com/obra/superpowers) |

*Token counts approximate, measured as of 2026-07.*

## 🔍 Research

Multi-source research, fact-checking, and synthesis.

No skills catalogued yet — [contribute](#contributing)!

## 📄 Documents

Creating and editing office documents: PDF, Word, PowerPoint, Excel.

| Skill | Description | Trigger | Agents | Cost ~(invoke / always-on) | Maturity | License | Repo |
| --- | --- | --- | --- | --- | --- | --- | --- |
| docx | Creates and edits Word documents with tracked changes | auto | CC | ~3k / ~80 | stable | Source-available† | [anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/docx) |
| pdf | Generates and manipulates PDFs: forms, merging, extraction | auto | CC | ~3k / ~80 | stable | Source-available† | [anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/pdf) |
| pptx | Creates and edits PowerPoint presentations | auto | CC | ~3k / ~80 | stable | Source-available† | [anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/pptx) |
| xlsx | Creates and edits Excel spreadsheets with formulas | auto | CC | ~3k / ~80 | stable | Source-available† | [anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/xlsx) |

*Token counts approximate, measured as of 2026-07.*

†**Source-available, not open source:** code is visible on GitHub but licensed for use within Claude products only — not free to port to other agents or redistribute. "On GitHub" ≠ "free to use anywhere"; check the license before reuse.

## 💼 Business & Productivity

Non-dev skills: marketing, product management, comms, and brand work.

| Skill | Description | Trigger | Agents | Cost ~(invoke / always-on) | Maturity | License | Repo |
| --- | --- | --- | --- | --- | --- | --- | --- |
| brand-guidelines | Applies Anthropic brand colors and typography to artifacts (template for your own brand skill) | auto | ✅ any | ~1.5k / ~70 | stable | Apache-2.0 | [anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/brand-guidelines) |
| internal-comms | Drafts status reports, newsletters, and FAQs in a consistent internal voice | auto | ✅ any | ~1.5k / ~70 | stable | Apache-2.0 | [anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/internal-comms) |

*Token counts approximate, measured as of 2026-07.*
````

- [ ] **Step 2: Verify structure**

Run: `grep -c '^## ' README.md`
Expected: `18` (4 header sections + 14 categories)

Run: `grep -c 'No skills catalogued yet' README.md`
Expected: `3`

Run: `grep -c 'measured as of 2026-07' README.md`
Expected: `11`

- [ ] **Step 3: Verify every table row has 8 columns**

Run:

```bash
awk -F'|' '/^\|/ && !/^\| ---/ {if (NF != 10) print "BAD ("NF-2" cols): "$0}' README.md
```

Expected: no output (each row line has 10 `|`-separated fields = 8 columns + 2 empty edges).

- [ ] **Step 4: Verify rows are alphabetically sorted within each table**

Run:

```bash
python3 - <<'EOF'
import re
rows, bad = [], []
for line in open('README.md'):
    if line.startswith('|') and not line.startswith('| ---') and not line.startswith('| Skill') and not line.startswith('| Code') and not line.startswith('| `'):
        rows.append(line.split('|')[1].strip())
    elif rows:
        if rows != sorted(rows, key=str.lower): bad.append(rows[:])
        rows = []
print("UNSORTED:", bad) if bad else print("OK")
EOF
```

Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add README.md
git commit -m "Add 14 category sections with seed skills"
```

### Task 3: Collections & registries section + contributing pointer

**Files:**
- Modify: `README.md` (append)

- [ ] **Step 1: Append the section**

Append exactly this content to `README.md`:

````markdown

## 📦 Skill Collections & Registries

For further discovery and research. Skills found here still get their own row in a category above once curated — these are places to browse for more.

### Collections

| Repo | Description | License | Link |
| --- | --- | --- | --- |
| alirezarezvani/claude-skills | Large community skill pack, explicitly multi-agent portable | — | [GitHub](https://github.com/alirezarezvani/claude-skills) |
| anthropics/skills | Anthropic's official example skills and skill spec template | Apache-2.0 / Source-available† | [GitHub](https://github.com/anthropics/skills) |
| obra/superpowers | Software-engineering methodology pack: TDD, debugging, planning workflows | MIT | [GitHub](https://github.com/obra/superpowers) |
| trailofbits/skills | Security-audit skills from Trail of Bits | CC-BY-SA-4.0 | [GitHub](https://github.com/trailofbits/skills) |
| vercel-labs/skills | Vercel's skill collection and registry CLI | MIT | [GitHub](https://github.com/vercel-labs/skills) |

### Registries & lists

| Name | Type | Link |
| --- | --- | --- |
| awesome-agent-skills (heilcheng) | awesome-list | [GitHub](https://github.com/heilcheng/awesome-agent-skills) |
| awesome-claude-skills (travisvn) | awesome-list | [GitHub](https://github.com/travisvn/awesome-claude-skills) |
| SkillHub | marketplace | [skillhub.club](https://www.skillhub.club/) |
| SkillsMP | registry | [skillsmp.com](https://skillsmp.com/) |
| skills.sh | registry | [skills.sh](https://www.skills.sh/) |

## Contributing

Want to add a skill? See [CONTRIBUTING.md](CONTRIBUTING.md) for the row template and rules. Automated submission via GitHub issue form is planned (phase 2).
````

- [ ] **Step 2: Verify all TOC anchors resolve to real headings**

Run:

```bash
python3 - <<'EOF'
import re
text = open('README.md').read()
anchors = set(re.findall(r'\]\(#([^)]+)\)', text))
def slug(h):
    h = h.strip().lower()
    h = re.sub(r'[^\w\sÀ-￿-]', '', h, flags=re.UNICODE)
    return h.replace(' ', '-')
slugs = {slug(h) for h in re.findall(r'^#{1,6} (.+)$', text, re.M)}
from urllib.parse import unquote
missing = {a for a in anchors if unquote(a).replace('️','').replace('⚠','') not in {s.replace('️','').replace('⚠','') for s in slugs}}
print("MISSING:", missing) if missing else print("OK")
EOF
```

Expected: `OK` (if emoji-anchor slugs mismatch, fix TOC links to match GitHub's generated anchors and re-run).

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "Add skill collections, registries, and contributing pointer"
```

### Task 4: CONTRIBUTING.md

**Files:**
- Create: `CONTRIBUTING.md`

- [ ] **Step 1: Write the file**

Create `CONTRIBUTING.md` with exactly this content:

````markdown
# Contributing

Add a skill by opening a pull request that inserts one row into the right category table in [README.md](README.md).

## Row template

```markdown
| skill-name | One-line description of what it does | auto | ✅ any | ~2k / ~100 | stable | MIT | [repo-name](https://github.com/owner/repo) |
```

## Rules

1. **One row per skill**, in the single best-fit category.
2. **Alphabetical placement** by skill name within the table.
3. **Columns, in order:** Skill · Description · Trigger · Agents · Cost ~(invoke / always-on) · Maturity · License · Repo.
4. **Trigger:** `manual` (user runs a slash command) / `auto` (model activates it when relevant) / `always-on` (hook or system-level, active every turn).
5. **Agents:** `✅ any` if the skill is plain portable markdown; otherwise list tested/restricted agents with legend codes separated by `·` (e.g. `CC · CX`).
6. **Cost:** approximate token counts, `~` prefix mandatory, format `~<invoke> / ~<always-on>`.
   - Always-on ≈ tokens of the skill's frontmatter name + description (what sits in context every turn).
   - On-invoke ≈ tokens of the full `SKILL.md` body.
   - Rough measure: `words × 1.3`. Example: `wc -w SKILL.md` → 1500 words ≈ `~2k`.
7. **Maturity:** `stable` / `beta` / `experimental` / `archived` — your honest judgment from repo activity and docs.
8. **License:** SPDX short form (`MIT`, `Apache-2.0`, …). Use `—` if unknown. If the code is public but not freely licensed, use `Source-available†` and make sure the category's footnote explains it.
9. **As-of date:** when you add or re-measure costs in a table, update its `*Token counts approximate, measured as of YYYY-MM.*` footnote.
10. **Empty categories:** when adding the first skill to an empty category, replace the placeholder line with the standard table header plus your row and the as-of footnote.

## Coming in phase 2

Issue-form submission: you file a GitHub issue with just the SKILL.md URL, category, agents tested, and maturity — automation infers the rest (name, description, license, token counts) and opens a PR for maintainer review.
````

- [ ] **Step 2: Verify README's contributing link resolves**

Run: `grep -q 'CONTRIBUTING.md' README.md && test -f CONTRIBUTING.md && echo OK`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add CONTRIBUTING.md
git commit -m "Add CONTRIBUTING.md with row template and rules"
```

### Task 5: Final review pass

**Files:**
- Modify: `README.md` (fixes only, if needed)

- [ ] **Step 1: Lint if available**

Run: `npx --yes markdownlint-cli2 README.md CONTRIBUTING.md 2>/dev/null || echo "linter unavailable, skip"`
Expected: no errors (warnings about line length acceptable), or skip message. Fix any table-style (MD060) or link-fragment (MD051) errors.

- [ ] **Step 2: Re-run all Task 2/3 verification scripts**

Run the column-count awk, sort-check python, and anchor-check python from Tasks 2–3.
Expected: no BAD lines, `OK`, `OK`.

- [ ] **Step 3: Read the rendered file top to bottom**

Check against spec sections: intro w/ spec link, 2 disclaimers, legend, installing, TOC (14), 14 categories each with description, 3 empty placeholders, collections + registries, contributing pointer. Fix any drift.

- [ ] **Step 4: Commit any fixes**

```bash
git add -A
git commit -m "Fix review findings in README and CONTRIBUTING" || echo "nothing to fix"
```
