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

## Collections & registries rows

Preferred: open a [Collection / registry submission issue](../../issues/new?template=collection-submission.yml) with the GitHub repo URL and target table — automation infers the rest (license, stars badge) and opens a PR, same flow as skills. Automation handles GitHub-hosted entries only; non-GitHub registries (standalone sites) need a manual PR.

PRs for repositories with **1000+ GitHub stars** merge automatically (star count checked server-side), provided the description is plain prose — no links, images, or HTML. Everything else waits for maintainer review. Skill submissions always get maintainer review regardless of stars.

For manual PRs: both tables include a **Stars** column with a dynamic shields.io badge:

```markdown
![Stars](https://img.shields.io/github/stars/owner/repo?style=flat-square&label=%E2%AD%90)
```

- Replace `owner/repo` with the entry's GitHub repository. The count updates automatically — never hard-code star numbers.
- For entries not hosted on GitHub (e.g. standalone marketplaces), use `—` in the Stars cell.

## Preferred: submit via issue form

Open a [Skill submission issue](../../issues/new?template=skill-submission.yml) with just:
SKILL.md URL, category, agents tested, and maturity. Automation fetches the skill,
infers name, description, license, and token counts, and opens a PR that a
maintainer reviews. No hand-edited tables, no transcription mistakes.

Manual PRs following the rules above remain welcome.
