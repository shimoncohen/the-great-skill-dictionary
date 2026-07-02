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
PLACEHOLDER = "No skills catalogued yet — [contribute](#contributing)!"
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
