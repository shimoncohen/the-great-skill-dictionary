# Phase 2: Contribution Automation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Contributors file a GitHub issue with minimal info; a GitHub Action infers the rest (name, description, license, token costs), inserts a README row, and opens a PR for maintainer review. Same logic re-measures costs monthly.

**Architecture:** One Python-stdlib script (`scripts/skill_row.py`, no pip deps) with pure functions + a CLI (`add`, `remeasure`). Two workflows call it: `skill-submission.yml` (on issue labeled `skill-submission`) and `cost-remeasure.yml` (monthly cron). Submissions are recorded in `.github/skill-sources.json` so the re-measure job knows each skill's SKILL.md URL. PRs created with `peter-evans/create-pull-request`; **maintainer merge = curation gate, never auto-commit**.

**Tech Stack:** Python 3 stdlib (`urllib`, `json`, `re`, `unittest`), GitHub issue forms, GitHub Actions, `peter-evans/create-pull-request@v7`.

**Spec:** "Phase 2" section of `docs/superpowers/specs/2026-07-01-skill-dictionary-design.md`.

---

### Task 1: Issue form template

**Files:**
- Create: `.github/ISSUE_TEMPLATE/skill-submission.yml`

- [ ] **Step 1: Write the issue form**

Create `.github/ISSUE_TEMPLATE/skill-submission.yml` with exactly:

```yaml
name: Skill submission
description: Submit a skill for the dictionary. Automation infers the rest and opens a PR.
title: "[Skill]: "
labels: ["skill-submission"]
body:
  - type: input
    id: skill-url
    attributes:
      label: SKILL.md URL
      description: Direct link to the skill's SKILL.md on GitHub (blob or raw URL).
      placeholder: https://github.com/owner/repo/blob/main/skills/my-skill/SKILL.md
    validations:
      required: true
  - type: dropdown
    id: category
    attributes:
      label: Category
      options:
        - 🪙 Token Reduction
        - 🛠️ Engineering Workflow
        - 🧪 Testing
        - 🎨 Design & Frontend
        - 🌐 Web Development
        - 📚 Documentation
        - 🔒 Security
        - 🔌 API & Integration
        - 🧠 Memory & Knowledge
        - ⚙️ Automation & Scheduling
        - 🧩 Meta
        - 🔍 Research
        - 📄 Documents
        - 💼 Business & Productivity
    validations:
      required: true
  - type: dropdown
    id: agents
    attributes:
      label: Agents tested
      description: Pick "✅ any" only if the skill is plain portable markdown.
      multiple: true
      options:
        - ✅ any
        - CC
        - CX
        - GM
        - CP
    validations:
      required: true
  - type: dropdown
    id: maturity
    attributes:
      label: Maturity
      options:
        - stable
        - beta
        - experimental
        - archived
    validations:
      required: true
  - type: dropdown
    id: trigger
    attributes:
      label: Trigger (optional — defaults to auto)
      options:
        - auto
        - manual
        - always-on
    validations:
      required: false
```

- [ ] **Step 2: Validate YAML parses**

Run: `python3 -c "import yaml,sys; yaml.safe_load(open('.github/ISSUE_TEMPLATE/skill-submission.yml')); print('OK')" 2>/dev/null || python3 -c "print('pyyaml missing, visual check only')"`
Expected: `OK` (or fallback message — then eyeball indentation).

- [ ] **Step 3: Commit**

```bash
git add .github/ISSUE_TEMPLATE/skill-submission.yml
git commit -m "Add skill submission issue form"
```

### Task 2: Script core — frontmatter parsing + token estimation

**Files:**
- Create: `scripts/skill_row.py`
- Create: `tests/test_skill_row.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_skill_row.py`:

```python
import unittest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
import skill_row


class TestFrontmatter(unittest.TestCase):
    def test_parses_name_and_description(self):
        text = "---\nname: my-skill\ndescription: Does a thing well\n---\n\n# Body\ncontent"
        fm = skill_row.parse_frontmatter(text)
        self.assertEqual(fm["name"], "my-skill")
        self.assertEqual(fm["description"], "Does a thing well")

    def test_missing_frontmatter_raises(self):
        with self.assertRaises(ValueError):
            skill_row.parse_frontmatter("# Just a heading\nno frontmatter")

    def test_ignores_other_keys_and_colons_in_value(self):
        text = "---\nname: x\ndescription: Use when: always\nlicense: MIT\n---\nbody"
        fm = skill_row.parse_frontmatter(text)
        self.assertEqual(fm["description"], "Use when: always")


class TestTokens(unittest.TestCase):
    def test_estimate_words_times_1_3(self):
        text = " ".join(["word"] * 1000)
        self.assertEqual(skill_row.estimate_tokens(text), 1300)

    def test_format_small_rounds_to_ten(self):
        self.assertEqual(skill_row.format_tokens(143), "~140")

    def test_format_k(self):
        self.assertEqual(skill_row.format_tokens(2100), "~2.1k")
        self.assertEqual(skill_row.format_tokens(2000), "~2k")
        self.assertEqual(skill_row.format_tokens(12600), "~13k")

    def test_cost_cell(self):
        self.assertEqual(skill_row.cost_cell(2100, 143), "~2.1k / ~140")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests, verify they fail**

Run: `python3 -m unittest tests.test_skill_row -v 2>&1 | tail -3`
Expected: FAIL/ERROR (module `skill_row` not found).

- [ ] **Step 3: Implement**

Create `scripts/skill_row.py`:

```python
"""Skill dictionary automation: infer row fields from a SKILL.md and update README.md.

Stdlib only. Commands:
  add        --issue-body FILE --date YYYY-MM   (reads GitHub issue-form body)
  remeasure  --date YYYY-MM                     (refresh costs from skill-sources.json)
"""
import json
import os
import re
import sys
import urllib.request

README = "README.md"
SOURCES = ".github/skill-sources.json"
FOOTNOTE_RE = re.compile(r"\*Token counts approximate, measured as of \d{4}-\d{2}\.\*")
PLACEHOLDER = "No skills cataloged yet — [contribute](#contributing)!"
TABLE_HEADER = (
    "| Skill | Description | Trigger | Agents | Cost ~(invoke / always-on) | Maturity | License | Repo |\n"
    "| --- | --- | --- | --- | --- | --- | --- | --- |"
)


def parse_frontmatter(text):
    m = re.match(r"\A---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not m:
        raise ValueError("SKILL.md has no YAML frontmatter")
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith((" ", "\t", "#")):
            key, _, value = line.partition(":")
            fm[key.strip()] = value.strip().strip("\"'")
    if "name" not in fm or "description" not in fm:
        raise ValueError("frontmatter missing name or description")
    return fm


def estimate_tokens(text):
    return round(len(text.split()) * 1.3)


def format_tokens(n):
    if n < 1000:
        return f"~{round(n, -1)}"
    if n < 10000:
        k = round(n / 1000, 1)
        return f"~{int(k)}k" if k == int(k) else f"~{k}k"
    return f"~{round(n / 1000)}k"


def cost_cell(invoke, always_on):
    return f"{format_tokens(invoke)} / {format_tokens(always_on)}"
```

- [ ] **Step 4: Run tests, verify pass**

Run: `python3 -m unittest tests.test_skill_row -v 2>&1 | tail -3`
Expected: `OK` (7 tests).

- [ ] **Step 5: Commit**

```bash
git add scripts/skill_row.py tests/test_skill_row.py
git commit -m "Add frontmatter parsing and token estimation with tests"
```

### Task 3: URL normalization + issue-body parsing

**Files:**
- Modify: `scripts/skill_row.py` (append functions)
- Modify: `tests/test_skill_row.py` (append test classes)

- [ ] **Step 1: Write failing tests**

Append to `tests/test_skill_row.py` (before the `if __name__` block):

```python
class TestUrls(unittest.TestCase):
    def test_blob_url_to_raw(self):
        self.assertEqual(
            skill_row.to_raw_url("https://github.com/o/r/blob/main/skills/x/SKILL.md"),
            "https://raw.githubusercontent.com/o/r/main/skills/x/SKILL.md",
        )

    def test_raw_url_passthrough(self):
        u = "https://raw.githubusercontent.com/o/r/main/SKILL.md"
        self.assertEqual(skill_row.to_raw_url(u), u)

    def test_repo_web_url(self):
        self.assertEqual(
            skill_row.repo_web_url("https://github.com/o/r/blob/main/skills/x/SKILL.md"),
            ("o/r", "https://github.com/o/r/tree/main/skills/x"),
        )

    def test_rejects_non_github(self):
        with self.assertRaises(ValueError):
            skill_row.to_raw_url("https://evil.example.com/SKILL.md")


class TestIssueBody(unittest.TestCase):
    BODY = (
        "### SKILL.md URL\n\nhttps://github.com/o/r/blob/main/SKILL.md\n\n"
        "### Category\n\n🧪 Testing\n\n"
        "### Agents tested\n\nCC, CX\n\n"
        "### Maturity\n\nstable\n\n"
        "### Trigger (optional — defaults to auto)\n\n_No response_\n"
    )

    def test_parse_fields(self):
        f = skill_row.parse_issue_body(self.BODY)
        self.assertEqual(f["SKILL.md URL"], "https://github.com/o/r/blob/main/SKILL.md")
        self.assertEqual(f["Category"], "🧪 Testing")
        self.assertIsNone(f["Trigger (optional — defaults to auto)"])

    def test_agents_cell(self):
        self.assertEqual(skill_row.agents_cell("CC, CX"), "CC · CX")
        self.assertEqual(skill_row.agents_cell("✅ any"), "✅ any")
        self.assertEqual(skill_row.agents_cell("✅ any, CC"), "✅ any")
```

- [ ] **Step 2: Run tests, verify new ones fail**

Run: `python3 -m unittest tests.test_skill_row 2>&1 | tail -3`
Expected: ERROR (missing attributes).

- [ ] **Step 3: Implement**

Append to `scripts/skill_row.py`:

```python
def to_raw_url(url):
    if url.startswith("https://raw.githubusercontent.com/"):
        return url
    m = re.match(r"https://github\.com/([^/]+)/([^/]+)/blob/(.+)", url)
    if not m:
        raise ValueError(f"not a GitHub SKILL.md URL: {url}")
    return f"https://raw.githubusercontent.com/{m.group(1)}/{m.group(2)}/{m.group(3)}"


def repo_web_url(url):
    """Return (owner/repo, web URL of the skill's directory)."""
    m = re.match(r"https://(?:raw\.githubusercontent|github)\.com/([^/]+)/([^/]+)/(?:blob/)?(.+)/SKILL\.md", url)
    if not m:
        raise ValueError(f"cannot derive repo from: {url}")
    owner, repo, path = m.groups()
    return f"{owner}/{repo}", f"https://github.com/{owner}/{repo}/tree/{path}"


def parse_issue_body(body):
    fields = {}
    for m in re.finditer(r"^### (.+?)\n+(.*?)(?=\n### |\Z)", body, re.S | re.M):
        value = m.group(2).strip()
        fields[m.group(1).strip()] = None if value in ("", "_No response_") else value
    return fields


def agents_cell(raw):
    agents = [a.strip() for a in raw.split(",") if a.strip()]
    if "✅ any" in agents:
        return "✅ any"
    return " · ".join(agents)


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "skill-dictionary-bot"})
    token = os.environ.get("GITHUB_TOKEN")
    if token and "api.github.com" in url:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def detect_license(owner_repo):
    try:
        data = json.loads(fetch(f"https://api.github.com/repos/{owner_repo}/license"))
        spdx = data.get("license", {}).get("spdx_id")
        return spdx if spdx and spdx != "NOASSERTION" else "—"
    except Exception:
        return "—"
```

- [ ] **Step 4: Run tests, verify pass**

Run: `python3 -m unittest tests.test_skill_row 2>&1 | tail -3`
Expected: `OK` (13 tests).

- [ ] **Step 5: Commit**

```bash
git add scripts/skill_row.py tests/test_skill_row.py
git commit -m "Add URL normalization, issue-body parsing, license detection"
```

### Task 4: README row insertion

**Files:**
- Modify: `scripts/skill_row.py` (append)
- Modify: `tests/test_skill_row.py` (append)

- [ ] **Step 1: Write failing tests**

Append to `tests/test_skill_row.py` (before `if __name__`):

```python
SAMPLE_README = """# Title

## 🧪 Testing

Test authoring.

| Skill | Description | Trigger | Agents | Cost ~(invoke / always-on) | Maturity | License | Repo |
| --- | --- | --- | --- | --- | --- | --- | --- |
| alpha | A | auto | ✅ any | ~1k / ~50 | stable | MIT | [r](https://github.com/a/r) |
| zeta | Z | auto | ✅ any | ~1k / ~50 | stable | MIT | [r](https://github.com/z/r) |

*Token counts approximate, measured as of 2026-07.*

## 🔍 Research

Multi-source research.

No skills cataloged yet — [contribute](#contributing)!

## 📦 Skill Collections & Registries
"""


class TestInsertRow(unittest.TestCase):
    ROW = "| mid | M | auto | ✅ any | ~2k / ~60 | stable | MIT | [r](https://github.com/m/r) |"

    def test_sorted_insert(self):
        out = skill_row.insert_row(SAMPLE_README, "🧪 Testing", self.ROW, "mid", "2026-08")
        lines = out.splitlines()
        names = [l.split("|")[1].strip() for l in lines if l.startswith("| ") and not l.startswith("| Skill") and not l.startswith("| ---")]
        self.assertEqual(names, ["alpha", "mid", "zeta"])

    def test_updates_asof_date(self):
        out = skill_row.insert_row(SAMPLE_README, "🧪 Testing", self.ROW, "mid", "2026-08")
        self.assertIn("measured as of 2026-08", out)
        self.assertNotIn("measured as of 2026-07", out)

    def test_empty_category_gets_table(self):
        out = skill_row.insert_row(SAMPLE_README, "🔍 Research", self.ROW, "mid", "2026-08")
        section = out.split("## 🔍 Research")[1].split("## 📦")[0]
        self.assertIn("| Skill | Description |", section)
        self.assertIn("| mid |", section)
        self.assertIn("measured as of 2026-08", section)
        self.assertNotIn("No skills cataloged yet", section)

    def test_duplicate_name_raises(self):
        with self.assertRaises(ValueError):
            skill_row.insert_row(SAMPLE_README, "🧪 Testing", self.ROW.replace("mid", "alpha"), "alpha", "2026-08")

    def test_unknown_category_raises(self):
        with self.assertRaises(ValueError):
            skill_row.insert_row(SAMPLE_README, "🚀 Nope", self.ROW, "mid", "2026-08")
```

- [ ] **Step 2: Run tests, verify new ones fail**

Run: `python3 -m unittest tests.test_skill_row 2>&1 | tail -3`
Expected: ERROR (`insert_row` missing).

- [ ] **Step 3: Implement**

Append to `scripts/skill_row.py`:

```python
def _split_section(text, category):
    """Return (before, section, after) for the '## <category>' section."""
    heading = f"## {category}"
    idx = text.find(heading + "\n")
    if idx == -1:
        raise ValueError(f"category not found in README: {category}")
    end = text.find("\n## ", idx + len(heading))
    end = len(text) if end == -1 else end + 1  # keep trailing newline in section
    return text[:idx], text[idx:end], text[end:]


def insert_row(text, category, row, name, date):
    before, section, after = _split_section(text, category)
    if any(l.startswith(f"| {name} |") for l in section.splitlines()):
        raise ValueError(f"skill already listed: {name}")
    footnote = f"*Token counts approximate, measured as of {date}.*"
    if PLACEHOLDER in section:
        section = section.replace(
            PLACEHOLDER, f"{TABLE_HEADER}\n{row}\n\n{footnote}"
        )
    else:
        lines = section.splitlines()
        rows = [i for i, l in enumerate(lines)
                if l.startswith("| ") and not l.startswith("| Skill") and not l.startswith("| ---")]
        if not rows:
            raise ValueError(f"no table found in category: {category}")
        pos = rows[-1] + 1
        for i in rows:
            if name.lower() < lines[i].split("|")[1].strip().lower():
                pos = i
                break
        lines.insert(pos, row)
        section = FOOTNOTE_RE.sub(footnote, "\n".join(lines))
        if not section.endswith("\n"):
            section += "\n"
    return before + section + after


def build_row(name, description, trigger, agents, cost, maturity, license_id, repo_name, repo_url):
    return (f"| {name} | {description} | {trigger} | {agents} | {cost} "
            f"| {maturity} | {license_id} | [{repo_name}]({repo_url}) |")
```

- [ ] **Step 4: Run tests, verify pass**

Run: `python3 -m unittest tests.test_skill_row 2>&1 | tail -3`
Expected: `OK` (18 tests).

- [ ] **Step 5: Commit**

```bash
git add scripts/skill_row.py tests/test_skill_row.py
git commit -m "Add README row insertion with empty-category and as-of handling"
```

### Task 5: CLI — `add` command + sources registry

**Files:**
- Modify: `scripts/skill_row.py` (append)
- Modify: `tests/test_skill_row.py` (append)

- [ ] **Step 1: Write failing test for cost-cell replacement helper and registry update**

Append to `tests/test_skill_row.py` (before `if __name__`):

```python
class TestRegistryAndReplace(unittest.TestCase):
    def test_replace_cost_cell(self):
        row = "| alpha | A | auto | ✅ any | ~1k / ~50 | stable | MIT | [r](u) |"
        out = skill_row.replace_cost_cell(row, "~3k / ~90")
        self.assertEqual(out, "| alpha | A | auto | ✅ any | ~3k / ~90 | stable | MIT | [r](u) |")

    def test_update_sources(self):
        reg = {}
        skill_row.update_sources(reg, "my-skill", "https://raw.githubusercontent.com/o/r/main/SKILL.md", "🧪 Testing")
        self.assertEqual(reg["my-skill"]["category"], "🧪 Testing")
```

- [ ] **Step 2: Run tests, verify new ones fail**

Run: `python3 -m unittest tests.test_skill_row 2>&1 | tail -3`
Expected: ERROR.

- [ ] **Step 3: Implement helpers + `add` CLI**

Append to `scripts/skill_row.py`:

```python
def replace_cost_cell(row, new_cost):
    cells = row.split("|")
    cells[5] = f" {new_cost} "
    return "|".join(cells)


def update_sources(registry, name, raw_url, category):
    registry[name] = {"url": raw_url, "category": category}


def _load_sources():
    if os.path.exists(SOURCES):
        with open(SOURCES) as f:
            return json.load(f)
    return {}


def _save_sources(registry):
    os.makedirs(os.path.dirname(SOURCES), exist_ok=True)
    with open(SOURCES, "w") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")


def cmd_add(issue_body_file, date):
    fields = parse_issue_body(open(issue_body_file).read())
    url = fields["SKILL.md URL"]
    category = fields["Category"]
    trigger_key = next((k for k in fields if k.startswith("Trigger")), None)
    trigger = fields.get(trigger_key) or "auto"
    raw_url = to_raw_url(url.strip())
    skill_md = fetch(raw_url)
    fm = parse_frontmatter(skill_md)
    owner_repo, dir_url = repo_web_url(raw_url)
    cost = cost_cell(estimate_tokens(skill_md), estimate_tokens(fm["name"] + " " + fm["description"]))
    row = build_row(
        fm["name"], fm["description"].rstrip("."), trigger,
        agents_cell(fields["Agents tested"]), cost, fields["Maturity"],
        detect_license(owner_repo), owner_repo, dir_url,
    )
    text = open(README).read()
    new_text = insert_row(text, category, row, fm["name"], date)
    open(README, "w").write(new_text)
    registry = _load_sources()
    update_sources(registry, fm["name"], raw_url, category)
    _save_sources(registry)
    print(f"added: {fm['name']} -> {category}")


def main(argv):
    args = dict(zip(argv[2::2], argv[3::2]))
    if argv[1] == "add":
        cmd_add(args["--issue-body"], args["--date"])
    elif argv[1] == "remeasure":
        cmd_remeasure(args["--date"])
    else:
        raise SystemExit(f"unknown command: {argv[1]}")


if __name__ == "__main__":
    main(sys.argv)
```

Note: `cmd_remeasure` is defined in Task 6 — until then, running `remeasure` raises NameError, which is fine; tests don't call `main`.

- [ ] **Step 4: Run tests, verify pass**

Run: `python3 -m unittest tests.test_skill_row 2>&1 | tail -3`
Expected: `OK` (20 tests).

- [ ] **Step 5: Commit**

```bash
git add scripts/skill_row.py tests/test_skill_row.py
git commit -m "Add add command: fetch, infer, insert row, record source"
```

### Task 6: CLI — `remeasure` command

**Files:**
- Modify: `scripts/skill_row.py` (append `cmd_remeasure` ABOVE `main`)
- Modify: `tests/test_skill_row.py` (append)

- [ ] **Step 1: Write failing test**

Append to `tests/test_skill_row.py` (before `if __name__`):

```python
class TestRemeasureText(unittest.TestCase):
    def test_remeasure_updates_row_and_date(self):
        fetched = {"https://raw.x/SKILL.md": "---\nname: alpha\ndescription: A\n---\n" + ("w " * 2000)}
        registry = {"alpha": {"url": "https://raw.x/SKILL.md", "category": "🧪 Testing"}}
        out = skill_row.remeasure_text(SAMPLE_README, registry, "2026-09", fetcher=fetched.get)
        row = next(l for l in out.splitlines() if l.startswith("| alpha |"))
        self.assertIn("~2.6k", row)
        self.assertIn("measured as of 2026-09", out)

    def test_missing_skill_skipped(self):
        registry = {"ghost": {"url": "https://raw.x/S.md", "category": "🧪 Testing"}}
        out = skill_row.remeasure_text(SAMPLE_README, registry, "2026-09", fetcher=lambda u: None)
        self.assertEqual(out, SAMPLE_README)
```

- [ ] **Step 2: Run tests, verify new ones fail**

Run: `python3 -m unittest tests.test_skill_row 2>&1 | tail -3`
Expected: ERROR (`remeasure_text` missing).

- [ ] **Step 3: Implement**

Insert into `scripts/skill_row.py` ABOVE `def main(`:

```python
def remeasure_text(text, registry, date, fetcher=None):
    fetcher = fetcher or fetch
    for name, meta in sorted(registry.items()):
        skill_md = None
        try:
            skill_md = fetcher(meta["url"])
        except Exception:
            pass
        if not skill_md:
            print(f"skip (fetch failed): {name}", file=sys.stderr)
            continue
        try:
            fm = parse_frontmatter(skill_md)
        except ValueError:
            print(f"skip (bad frontmatter): {name}", file=sys.stderr)
            continue
        cost = cost_cell(estimate_tokens(skill_md), estimate_tokens(fm["name"] + " " + fm["description"]))
        changed = False
        lines = text.splitlines(True)
        for i, line in enumerate(lines):
            if line.startswith(f"| {name} |"):
                new_line = replace_cost_cell(line.rstrip("\n"), cost) + "\n"
                if new_line != line:
                    lines[i] = new_line
                    changed = True
        if changed:
            text = "".join(lines)
            before, section, after = _split_section(text, meta["category"])
            footnote = f"*Token counts approximate, measured as of {date}.*"
            text = before + FOOTNOTE_RE.sub(footnote, section) + after
            print(f"remeasured: {name} -> {cost}")
    return text


def cmd_remeasure(date):
    registry = _load_sources()
    if not registry:
        print("no recorded sources; nothing to do")
        return
    text = open(README).read()
    new_text = remeasure_text(text, registry, date)
    if new_text != text:
        open(README, "w").write(new_text)
```

- [ ] **Step 4: Run tests, verify pass**

Run: `python3 -m unittest tests.test_skill_row 2>&1 | tail -3`
Expected: `OK` (22 tests).

- [ ] **Step 5: Commit**

```bash
git add scripts/skill_row.py tests/test_skill_row.py
git commit -m "Add remeasure command for monthly cost refresh"
```

### Task 7: Submission workflow

**Files:**
- Create: `.github/workflows/skill-submission.yml`

- [ ] **Step 1: Write the workflow**

```yaml
name: Skill submission
on:
  issues:
    types: [opened, labeled]

permissions:
  contents: write
  pull-requests: write
  issues: write

jobs:
  add-skill:
    if: contains(github.event.issue.labels.*.name, 'skill-submission')
    runs-on: ubuntu-latest
    concurrency:
      group: skill-submission-${{ github.event.issue.number }}
      cancel-in-progress: true
    steps:
      - uses: actions/checkout@v4

      - name: Save issue body
        env:
          ISSUE_BODY: ${{ github.event.issue.body }}
        run: printf '%s' "$ISSUE_BODY" > /tmp/issue-body.md

      - name: Run tests
        run: python3 -m unittest tests.test_skill_row

      - name: Add skill row
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: python3 scripts/skill_row.py add --issue-body /tmp/issue-body.md --date "$(date -u +%Y-%m)"

      - name: Create pull request
        id: pr
        uses: peter-evans/create-pull-request@v7
        with:
          branch: skill-submission/issue-${{ github.event.issue.number }}
          title: "Add skill from #${{ github.event.issue.number }}"
          commit-message: |
            Add skill from issue #${{ github.event.issue.number }}
          body: |
            Automated skill row for #${{ github.event.issue.number }}.
            Inferred: name, description, license, token costs. Review before merging.

            Closes #${{ github.event.issue.number }}
          add-paths: |
            README.md
            .github/skill-sources.json

      - name: Comment on issue
        if: steps.pr.outputs.pull-request-url
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              body: `Automation opened ${{ steps.pr.outputs.pull-request-url }} — a maintainer will review it.`,
            })
```

Security note (leave as comment ABOVE the `Save issue body` step in the file):

```yaml
      # SECURITY: issue body is untrusted input. It is passed via env (not shell
      # interpolation) and only ever parsed by skill_row.py — never eval'd.
      # The resulting PR requires maintainer review before merge.
```

- [ ] **Step 2: Validate workflow YAML**

Run: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/skill-submission.yml')); print('OK')" 2>/dev/null || echo "pyyaml missing, visual check"`
Expected: `OK` or fallback.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/skill-submission.yml
git commit -m "Add skill submission workflow: issue to PR"
```

### Task 8: Monthly re-measure workflow

**Files:**
- Create: `.github/workflows/cost-remeasure.yml`

- [ ] **Step 1: Write the workflow**

```yaml
name: Monthly cost re-measure
on:
  schedule:
    - cron: "17 4 1 * *"   # 04:17 UTC on the 1st of each month
  workflow_dispatch:

permissions:
  contents: write
  pull-requests: write

jobs:
  remeasure:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run tests
        run: python3 -m unittest tests.test_skill_row

      - name: Re-measure token costs
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: python3 scripts/skill_row.py remeasure --date "$(date -u +%Y-%m)"

      - name: Create pull request
        uses: peter-evans/create-pull-request@v7
        with:
          branch: cost-remeasure
          title: "Monthly token-cost re-measure"
          commit-message: Re-measure skill token costs
          body: |
            Automated monthly refresh of token counts for skills recorded in
            `.github/skill-sources.json`. Review before merging.
          add-paths: README.md
```

- [ ] **Step 2: Validate YAML**

Run: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/cost-remeasure.yml')); print('OK')" 2>/dev/null || echo "pyyaml missing, visual check"`
Expected: `OK` or fallback.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/cost-remeasure.yml
git commit -m "Add monthly token-cost re-measure workflow"
```

### Task 9: End-to-end dry run

**Files:**
- None permanent (temp files + revert)

- [ ] **Step 1: Simulate a submission locally**

```bash
cat > /tmp/e2e-issue.md <<'EOF'
### SKILL.md URL

https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md

### Category

🔍 Research

### Agents tested

✅ any

### Maturity

stable

### Trigger (optional — defaults to auto)

_No response_
EOF
python3 scripts/skill_row.py add --issue-body /tmp/e2e-issue.md --date 2026-07
```

Expected: prints `added: skill-creator -> 🔍 Research` (network required; if offline, defer to CI).

- [ ] **Step 2: Inspect the result**

```bash
git diff README.md | head -30
cat .github/skill-sources.json
```

Expected: Research placeholder replaced by table with a `skill-creator` row (8 columns, real description from frontmatter, Apache-2.0 license); registry has one entry.

- [ ] **Step 3: Test remeasure end-to-end**

```bash
python3 scripts/skill_row.py remeasure --date 2026-08
grep -A2 'skill-creator' README.md | head -3
```

Expected: runs without error; Research footnote says 2026-08 if cost cell changed, unchanged otherwise.

- [ ] **Step 4: Revert the dry run**

```bash
git checkout -- README.md
rm -f .github/skill-sources.json /tmp/e2e-issue.md
git status --short
```

Expected: clean tree.

- [ ] **Step 5: Run full test suite one more time and commit nothing**

Run: `python3 -m unittest tests.test_skill_row 2>&1 | tail -3`
Expected: `OK` (22 tests).

### Task 10: Documentation update

**Files:**
- Modify: `CONTRIBUTING.md` (replace phase-2 section)
- Modify: `README.md` (Contributing paragraph)

- [ ] **Step 1: Update CONTRIBUTING.md**

Replace the `## Coming in phase 2` section (heading + paragraph) with:

```markdown
## Preferred: submit via issue form

Open a [Skill submission issue](../../issues/new?template=skill-submission.yml) with just:
SKILL.md URL, category, agents tested, and maturity. Automation fetches the skill,
infers name, description, license, and token counts, and opens a PR that a
maintainer reviews. No hand-edited tables, no transcription mistakes.

Manual PRs following the rules above remain welcome.
```

- [ ] **Step 2: Update README Contributing paragraph**

Replace:

```markdown
Want to add a skill? See [CONTRIBUTING.md](CONTRIBUTING.md) for the row template and rules. Automated submission via GitHub issue form is planned (phase 2).
```

with:

```markdown
Want to add a skill? Preferred: open a [Skill submission issue](../../issues/new?template=skill-submission.yml) — automation infers the details and opens a PR for review. Manual PRs also welcome; see [CONTRIBUTING.md](CONTRIBUTING.md) for the row template and rules.
```

- [ ] **Step 3: Verify links and lint**

Run: `npx --yes markdownlint-cli2 README.md CONTRIBUTING.md 2>&1 | grep -v MD013 | tail -3`
Expected: only the summary line (no non-MD013 errors).

- [ ] **Step 4: Commit and push**

```bash
git add CONTRIBUTING.md README.md
git commit -m "Document issue-form submission path"
git push origin main
```

### Task 11: Live verification

- [ ] **Step 1: Push everything and verify workflows registered**

```bash
git push origin main
```

Then check https://github.com/shimoncohen/the-great-skill-dictionary/actions — both workflows listed.

- [ ] **Step 2: Real end-to-end test**

Maintainer opens a real skill-submission issue (e.g. the skill-creator example from Task 9). Verify: Action runs, PR appears with correct row, issue gets comment. Merge or close as desired.

- [ ] **Step 3: If Action fails, fix forward**

Read the Actions log, fix, commit, re-label the issue to re-trigger.
