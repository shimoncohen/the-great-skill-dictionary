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
