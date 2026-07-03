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
from urllib.parse import urlsplit

README = "README.md"
SOURCES = ".github/skill-sources.json"
FOOTNOTE_RE = re.compile(r"\*Token counts approximate, measured as of \d{4}-\d{2}\.\*")
PLACEHOLDER = "No skills catalogued yet — [contribute](#contributing)!"
TABLE_HEADER = (
    "| Skill | Description | Trigger | Agents | Cost ~(invoke / always-on) | Maturity | License | Repo |\n"
    "| --- | --- | --- | --- | --- | --- | --- | --- |"
)

CATEGORIES = {
    "🪙 Token Reduction", "🛠️ Engineering Workflow", "🧪 Testing",
    "🎨 Design & Frontend", "🌐 Web Development", "📚 Documentation",
    "🔒 Security", "🔌 API & Integration", "🧠 Memory & Knowledge",
    "⚙️ Automation & Scheduling", "🧩 Meta", "🔍 Research",
    "📄 Documents", "💼 Business & Productivity",
}
AGENT_CODES = {"✅ any", "CC", "CX", "GM", "CP"}
MATURITIES = {"stable", "beta", "experimental", "archived"}
TRIGGERS = {"auto", "manual", "always-on"}

_BLOCK_SCALAR_INDICATORS = {">", ">-", ">+", "|", "|-", "|+", ""}


def clean_cell(s):
    """Make untrusted text safe inside a markdown table cell."""
    return re.sub(r"\s+", " ", s).replace("|", "\\|").strip()


def parse_frontmatter(text):
    m = re.match(r"\A---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not m:
        raise ValueError("SKILL.md has no YAML frontmatter")
    fm = {}
    lines = m.group(1).splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if ":" in line and not line.startswith((" ", "\t", "#")):
            key, _, value = line.partition(":")
            value = value.strip().strip("\"'")
            if value in _BLOCK_SCALAR_INDICATORS:
                # Consume following more-indented lines as the scalar value
                block_lines = []
                i += 1
                while i < len(lines) and lines[i].startswith((" ", "\t")):
                    block_lines.append(lines[i].strip())
                    i += 1
                fm[key.strip()] = " ".join(block_lines)
                continue
            fm[key.strip()] = value
        i += 1
    if not fm.get("name") or not fm.get("description"):
        raise ValueError("frontmatter missing name or description")
    return fm


def estimate_tokens(text):
    return round(len(text.split()) * 1.3)


def format_tokens(n):
    if n < 100:
        return f"~{max(10, round(n, -1))}"
    if n < 1000:
        return f"~{round(n, -1)}"
    if n < 10000:
        k = round(n / 1000, 1)
        return f"~{int(k)}k" if k == int(k) else f"~{k}k"
    return f"~{round(n / 1000)}k"


def cost_cell(invoke, always_on):
    return f"{format_tokens(invoke)} / {format_tokens(always_on)}"


# SECURITY: URLs come from untrusted issue bodies. parse_skill_url runs
# before any network request; everything it rejects is never fetched.
_OWNER_RE = re.compile(r"\A[A-Za-z0-9-]{1,39}\Z")
_REPO_RE = re.compile(r"\A[A-Za-z0-9._-]{1,100}\Z")
_SEGMENT_RE = re.compile(r"\A[A-Za-z0-9._-]+\Z")


def parse_skill_url(url):
    """Validate an untrusted skill URL and return its parts.

    Accepts only https URLs on github.com (blob) or raw.githubusercontent.com
    pointing at a markdown file (any name, .md case-insensitive), with a
    conservative path charset (no query, fragment, %-encoding, userinfo,
    empty segments, or '..'). Returns (owner, repo, segments) where segments
    is the ref+path, e.g. ['main', 'skills', 'x', 'SKILL.md'].
    Raises ValueError otherwise."""
    parts = urlsplit(url)
    if parts.scheme != "https" or parts.query or parts.fragment:
        raise ValueError(f"not an official GitHub skill file URL: {url}")

    segments = parts.path.lstrip("/").split("/")
    if parts.netloc == "github.com":
        if len(segments) < 5 or segments[2] != "blob":
            raise ValueError(f"expected a github.com blob URL: {url}")
        owner, repo, segments = segments[0], segments[1], segments[3:]
    elif parts.netloc == "raw.githubusercontent.com":
        if len(segments) < 4:
            raise ValueError(f"expected a raw.githubusercontent.com URL: {url}")
        owner, repo, segments = segments[0], segments[1], segments[2:]
    else:
        raise ValueError(f"not an official GitHub host: {url}")

    if not _OWNER_RE.match(owner):
        raise ValueError(f"invalid owner in URL: {url}")
    if not _REPO_RE.match(repo) or repo in (".", "..") or repo.endswith(".git"):
        raise ValueError(f"invalid repository name in URL: {url}")
    for seg in segments:
        if seg in (".", "..") or not _SEGMENT_RE.match(seg):
            raise ValueError(f"invalid path segment in URL: {url}")
    if not segments[-1].lower().endswith(".md"):
        raise ValueError(f"URL must point directly to a markdown file: {url}")
    return owner, repo, segments


def to_raw_url(url):
    owner, repo, segments = parse_skill_url(url)
    return f"https://raw.githubusercontent.com/{owner}/{repo}/{'/'.join(segments)}"


def repo_web_url(url):
    """Return (owner/repo, web URL of the skill's directory)."""
    owner, repo, segments = parse_skill_url(url)
    return f"{owner}/{repo}", f"https://github.com/{owner}/{repo}/tree/{'/'.join(segments[:-1])}"


def parse_issue_body(body):
    fields = {}
    for m in re.finditer(r"^### (.+?)\n+(.*?)(?=\n### |\Z)", body, re.S | re.M):
        value = m.group(2).strip()
        fields[m.group(1).strip()] = None if value in ("", "_No response_", "None") else value
    return fields


def agents_cell(raw):
    agents = [a.strip() for a in raw.split(",") if a.strip()]
    if "✅ any" in agents:
        return "✅ any"
    return " · ".join(agents)


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "skill-dictionary-bot"})
    token = os.environ.get("GITHUB_TOKEN")
    if token and url.startswith("https://api.github.com/"):
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read(2_000_000).decode("utf-8")


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
    # Global duplicate check across the entire README text
    if any(l.startswith(f"| {name} |") for l in text.splitlines()):
        raise ValueError(f"skill already listed: {name}")
    before, section, after = _split_section(text, category)
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
    if not repo_url.startswith("https://github.com/"):
        raise ValueError(f"repo URL must start with https://github.com/: {repo_url}")
    return (
        f"| {clean_cell(name)} | {clean_cell(description)} | {clean_cell(trigger)} "
        f"| {clean_cell(agents)} | {cost} "
        f"| {clean_cell(maturity)} | {clean_cell(license_id)} "
        f"| [{clean_cell(repo_name)}]({repo_url}) |"
    )


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


def validate_fields(category, agents_raw, maturity, trigger):
    """Validate enum fields; raise ValueError on any mismatch."""
    if category not in CATEGORIES:
        raise ValueError(f"unknown category: {category}")
    for agent in [a.strip() for a in agents_raw.split(",") if a.strip()]:
        if agent not in AGENT_CODES:
            raise ValueError(f"unknown agent code: {agent}")
    if maturity not in MATURITIES:
        raise ValueError(f"unknown maturity: {maturity}")
    if trigger not in TRIGGERS:
        raise ValueError(f"unknown trigger: {trigger}")


def cmd_add(issue_body_file, date):
    fields = parse_issue_body(open(issue_body_file).read())
    url = (fields["SKILL.md URL"] or "").strip()
    category = fields["Category"]
    trigger_key = next((k for k in fields if k.startswith("Trigger")), None)
    trigger = fields.get(trigger_key) or "auto"
    validate_fields(category, fields["Agents tested"], fields["Maturity"], trigger)
    raw_url = to_raw_url(url)  # parse_skill_url inside rejects non-GitHub URLs before any fetch
    skill_md = fetch(raw_url)
    fm = parse_frontmatter(skill_md)
    name = clean_cell(fm["name"])  # normalize once; row, dup check, and registry all use the same form
    owner_repo, dir_url = repo_web_url(raw_url)
    cost = cost_cell(estimate_tokens(skill_md), estimate_tokens(fm["name"] + " " + fm["description"]))
    row = build_row(
        name, fm["description"].rstrip("."), trigger,
        agents_cell(fields["Agents tested"]), cost, fields["Maturity"],
        detect_license(owner_repo), owner_repo, dir_url,
    )
    text = open(README).read()
    new_text = insert_row(text, category, row, name, date)
    open(README, "w").write(new_text)
    registry = _load_sources()
    update_sources(registry, name, raw_url, category)
    _save_sources(registry)
    print(f"added: {name} -> {category}")


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
            try:
                before, section, after = _split_section(text, meta["category"])
                footnote = f"*Token counts approximate, measured as of {date}.*"
                text = before + FOOTNOTE_RE.sub(footnote, section) + after
            except ValueError:
                print(f"skip (footnote update, category not found): {name}", file=sys.stderr)
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
