"""Skill dictionary automation: infer row fields from a SKILL.md and update README.md.

Stdlib only. Commands:
  add  --kind KIND --issue-body FILE --date YYYY-MM  (reads GitHub issue-form body;
                                                      KIND: skill|collection|plugin)
  remeasure       --date YYYY-MM                     (refresh costs from skill-sources.json
                                                      and Last edit dates for skill rows)
  check                                              (README links, local targets, category TOC)
"""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from urllib.parse import urlsplit

# --- Constants ---------------------------------------------------------------

README = "README.md"
SOURCES = ".github/skill-sources.json"
FOOTNOTE_RE = re.compile(r"\*Token counts approximate, measured as of \d{4}-\d{2}\.\*")
PLACEHOLDER = "No skills catalogued yet — [contribute](#contributing)!"
TABLE_HEADER = (
    "| Skill | Description | Trigger | Agents | Cost ~(invoke / always-on) | Maturity | License | Last edit | Repo |\n"
    "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"
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

# Collections & registries tables (h3 sections under 📦), hand-shaped:
# Collections:         | Repo | Description | Stars | License | Last edit | Link |
# Registries & lists:  | Name | Type | Stars | Last edit | Link |
# Plugin marketplaces: | Repo | Description | Stars | License | Last edit | Link |
COLLECTION_HEADINGS = {
    "Collections": "### Collections",
    "Registries & lists": "### Registries & lists",
    "Plugin marketplaces": "### Plugin marketplaces",
}
REGISTRY_TYPES = {"awesome-list", "registry", "marketplace"}

# Collection/registry PRs for repos at or above this star count are merged
# without maintainer review (the workflow acts on the automerge output).
AUTO_MERGE_STARS = 1000

_BLOCK_SCALAR_INDICATORS = {">", ">-", ">+", "|", "|-", "|+", ""}

# --- Text and issue-body parsing ----------------------------------------------


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


# --- Token estimation ----------------------------------------------------------


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


# --- URL validation -------------------------------------------------------------

# SECURITY: URLs come from untrusted issue bodies. parse_skill_url and
# parse_repo_url run before any network request; everything they reject is
# never fetched.
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


def _raw_url(owner, repo, segments):
    return f"https://raw.githubusercontent.com/{owner}/{repo}/{'/'.join(segments)}"


def _dir_url(owner, repo, segments):
    return f"https://github.com/{owner}/{repo}/tree/{'/'.join(segments[:-1])}"


def to_raw_url(url):
    return _raw_url(*parse_skill_url(url))


def repo_web_url(url):
    """Return (owner/repo, web URL of the skill's directory)."""
    owner, repo, segments = parse_skill_url(url)
    return f"{owner}/{repo}", _dir_url(owner, repo, segments)


def parse_repo_url(url):
    """Validate an untrusted repository URL and return (owner, repo).

    Accepts only https://github.com/<owner>/<repo> — exactly two path
    segments, no query, fragment, or userinfo. Same charset rules as skill
    URLs. Non-GitHub registries are out of scope for automation (manual PR).
    Raises ValueError otherwise."""
    parts = urlsplit(url)
    if parts.scheme != "https" or parts.netloc != "github.com" or parts.query or parts.fragment:
        raise ValueError(f"not a github.com repository URL: {url}")
    segments = parts.path.strip("/").split("/")
    if len(segments) != 2 or not all(segments):
        raise ValueError(f"expected https://github.com/<owner>/<repo>: {url}")
    owner, repo = segments
    if not _OWNER_RE.match(owner):
        raise ValueError(f"invalid owner in URL: {url}")
    if not _REPO_RE.match(repo) or repo in (".", "..") or repo.endswith(".git"):
        raise ValueError(f"invalid repository name in URL: {url}")
    return owner, repo


# --- GitHub API ------------------------------------------------------------------


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "skill-dictionary-bot"})
    token = os.environ.get("GITHUB_TOKEN")
    if token and url.startswith("https://api.github.com/"):
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read(2_000_000).decode("utf-8")


def ensure_repo_exists(owner_repo, fetcher=None):
    """Fail loudly when the repository does not exist on GitHub; return its
    API metadata (dict) when it does.

    Called only with an already-validated owner/repo (parse_skill_url or
    parse_repo_url), so the API URL is built from trusted parts. A 404 raises
    ValueError (clear submission error); other API failures (rate limit,
    outage) propagate so the workflow fails visibly instead of minting a row
    for a repo nobody checked."""
    fetcher = fetcher or fetch
    try:
        return json.loads(fetcher(f"https://api.github.com/repos/{owner_repo}"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise ValueError(f"repository not found on GitHub: {owner_repo}") from e
        raise


def detect_license(owner_repo, fetcher=None):
    """SPDX id via the GitHub API; the repo is known to exist by now
    (ensure_repo_exists ran), so a 404 here means "no license" (—). Other
    failures (rate limit, outage) propagate rather than minting a wrong —."""
    fetcher = fetcher or fetch
    try:
        data = json.loads(fetcher(f"https://api.github.com/repos/{owner_repo}/license"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return "—"
        raise
    spdx = data.get("license", {}).get("spdx_id")
    return spdx if spdx and spdx != "NOASSERTION" else "—"


def last_edit_from_commits(owner_repo, ref=None, path=None, fetcher=None):
    """Date (YYYY-MM-DD) of the newest commit touching `path` on `ref`.

    Built only from already-validated URL parts (parse_skill_url charset), so
    the query string needs no encoding. A 404 (bad ref) or 409 (empty repo)
    reads as "no history" (—); other API failures propagate so workflows fail
    visibly instead of minting a wrong date."""
    fetcher = fetcher or fetch
    url = f"https://api.github.com/repos/{owner_repo}/commits?per_page=1"
    if ref:
        url += f"&sha={ref}"
    if path:
        url += f"&path={path}"
    try:
        commits = json.loads(fetcher(url))
    except urllib.error.HTTPError as e:
        if e.code in (404, 409):
            return "—"
        raise
    if not commits:
        return "—"
    return commits[0]["commit"]["committer"]["date"][:10]


def automerge_eligible(stars, description):
    """Whether a collection/registry PR may merge without maintainer review.

    Stars come from the GitHub API (server-side), never from issue text. The
    description is the only attacker-authored prose in the row and auto-merge
    publishes it unreviewed, so the auto path additionally requires plain
    text — no links, images, HTML, or code spans. Anything fancier waits for
    a maintainer."""
    if stars < AUTO_MERGE_STARS:
        return False
    return not re.search(r"https?://|!\[|\]\(|[<>`]", description or "")


def _write_github_output(**kv):
    """Append key=value outputs for the calling workflow step; no-op locally."""
    path = os.environ.get("GITHUB_OUTPUT")
    if not path:
        return
    with open(path, "a") as f:
        for k, v in kv.items():
            f.write(f"{k}={v}\n")


# --- Markdown table operations ----------------------------------------------------


def stars_badge(owner_repo):
    return (
        f"![Stars](https://img.shields.io/github/stars/{owner_repo}"
        "?style=flat-square&label=%E2%AD%90)"
    )


def last_edit_badge(owner_repo):
    """Dynamic last-commit badge (default branch) — always current, so
    collection/registry rows need no sweep refresh."""
    return (
        f"![Last commit](https://img.shields.io/github/last-commit/{owner_repo}"
        "?style=flat-square&label=)"
    )


def build_row(name, description, trigger, agents, cost, maturity, license_id, last_edit, repo_name, repo_url):
    if not repo_url.startswith("https://github.com/"):
        raise ValueError(f"repo URL must start with https://github.com/: {repo_url}")
    return (
        f"| {clean_cell(name)} | {clean_cell(description)} | {clean_cell(trigger)} "
        f"| {clean_cell(agents)} | {cost} "
        f"| {clean_cell(maturity)} | {clean_cell(license_id)} "
        f"| {clean_cell(last_edit)} "
        f"| [{clean_cell(repo_name)}]({repo_url}) |"
    )


def build_collection_row(owner_repo, description, license_id):
    return (
        f"| {clean_cell(owner_repo)} | {clean_cell(description)} "
        f"| {stars_badge(owner_repo)} | {clean_cell(license_id)} "
        f"| {last_edit_badge(owner_repo)} "
        f"| [GitHub](https://github.com/{owner_repo}) |"
    )


def build_registry_row(name, type_, owner_repo):
    return (
        f"| {clean_cell(name)} | {clean_cell(type_)} "
        f"| {stars_badge(owner_repo)} "
        f"| {last_edit_badge(owner_repo)} "
        f"| [GitHub](https://github.com/{owner_repo}) |"
    )


def _split_section(text, category):
    """Return (before, section, after) for the '## <category>' section."""
    heading = f"## {category}"
    idx = text.find(heading + "\n")
    if idx == -1:
        raise ValueError(f"category not found in README: {category}")
    end = text.find("\n## ", idx + len(heading))
    end = len(text) if end == -1 else end + 1  # keep trailing newline in section
    return text[:idx], text[idx:end], text[end:]


def _insert_sorted_row(lines, rows, name, row, kind):
    """Insert row at its alphabetical position (by first cell) among the table
    rows at indexes `rows`; reject a case-insensitive duplicate. Mutates lines."""
    for i in rows:
        if lines[i].split("|")[1].strip().lower() == name.lower():
            raise ValueError(f"{kind} already listed: {name}")
    pos = rows[-1] + 1
    for i in rows:
        if name.lower() < lines[i].split("|")[1].strip().lower():
            pos = i
            break
    lines.insert(pos, row)


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
        # split("\n") (not splitlines) so join round-trips blank lines exactly
        lines = section.split("\n")
        rows = [i for i, l in enumerate(lines)
                if l.startswith("| ") and not l.startswith("| Skill") and not l.startswith("| ---")]
        if not rows:
            raise ValueError(f"no table found in category: {category}")
        _insert_sorted_row(lines, rows, name, row, "skill")
        # Leave the existing footnote date alone: it records when costs were
        # measured, and only `remeasure` refreshes costs. Also keeps
        # concurrent submission PRs from all rewriting the same line.
        section = "\n".join(lines)
    return before + section + after


def insert_collection_row(text, table, row, name):
    """Insert a row (sorted by first cell) into a Collections/Registries table."""
    heading = COLLECTION_HEADINGS.get(table)
    if heading is None:
        raise ValueError(f"unknown table: {table}")
    idx = text.find(heading + "\n")
    if idx == -1:
        raise ValueError(f"table heading not found in README: {heading}")
    ends = [i for i in (text.find("\n### ", idx + len(heading)),
                        text.find("\n## ", idx + len(heading))) if i != -1]
    end = min(ends) + 1 if ends else len(text)
    # split("\n") (not splitlines) so join round-trips blank lines exactly
    lines = text[idx:end].split("\n")
    rows = [i for i, l in enumerate(lines)
            if l.startswith("| ") and not l.startswith(("| Repo |", "| Name |", "| ---"))]
    if rows:
        _insert_sorted_row(lines, rows, name, row, "entry")
    else:
        # Empty table (header + separator, no data rows yet): seed the first
        # row directly below the separator.
        seps = [i for i, l in enumerate(lines) if l.startswith("| ---")]
        if not seps:
            raise ValueError(f"no table found under: {heading}")
        lines.insert(seps[-1] + 1, row)
    return text[:idx] + "\n".join(lines) + text[end:]


def replace_cost_cell(row, new_cost):
    cells = row.split("|")
    cells[5] = f" {new_cost} "
    return "|".join(cells)


def replace_last_edit_cell(row, new_date):
    """Last edit is always the second-to-last column. Indexing from the right
    is immune to escaped pipes in description cells."""
    cells = row.split("|")
    cells[-3] = f" {new_date} "
    return "|".join(cells)


# Final-cell GitHub tree link of a skill row: [label](https://github.com/o/r/tree/ref/path)
_ROW_TREE_LINK_RE = re.compile(
    r"\]\(https://github\.com/([A-Za-z0-9-]+/[A-Za-z0-9._-]+)/tree/([^)\s]+)\)"
)


def refresh_last_edits(text, fetcher=None):
    """Refresh the Last edit cell of every skill row, using the row's own
    GitHub tree link: the date of the newest commit touching that directory.
    Collection/registry rows carry a self-updating last-commit badge and need
    no refresh. Rows without a tree link, or whose lookup fails, are left
    unchanged (URLError/ValueError/KeyError/TypeError cover API and response-
    shape failures; anything else is a bug and should crash the run)."""
    fetcher = fetcher or fetch
    lines = text.split("\n")
    in_table = False
    for i, line in enumerate(lines):
        if not line.startswith("|"):
            in_table = False
            continue
        if "| Last edit |" in line:
            in_table = True
            continue
        if not in_table or line.startswith("| ---"):
            continue
        m = _ROW_TREE_LINK_RE.search(line.split("|")[-2])
        if not m:
            continue
        owner_repo, tree = m.group(1), m.group(2)
        ref, _, path = tree.partition("/")
        try:
            date = last_edit_from_commits(owner_repo, ref, path, fetcher=fetcher)
        except (urllib.error.URLError, ValueError, KeyError, TypeError) as e:
            print(f"skip (last-edit lookup failed): {owner_repo}: {e}", file=sys.stderr)
            continue
        lines[i] = replace_last_edit_cell(line, date)
    return "\n".join(lines)


# --- Sources registry (skill-sources.json) -----------------------------------------


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


# --- Commands -----------------------------------------------------------------------


def cmd_add(issue_body_file, date):
    fields = parse_issue_body(open(issue_body_file).read())
    url = (fields["SKILL.md URL"] or "").strip()
    category = fields["Category"]
    trigger_key = next((k for k in fields if k.startswith("Trigger")), None)
    trigger = fields.get(trigger_key) or "auto"
    validate_fields(category, fields["Agents tested"], fields["Maturity"], trigger)
    owner, repo, segments = parse_skill_url(url)  # rejects non-GitHub URLs before any fetch
    owner_repo = f"{owner}/{repo}"
    raw_url = _raw_url(owner, repo, segments)
    dir_url = _dir_url(owner, repo, segments)
    ensure_repo_exists(owner_repo)
    skill_md = fetch(raw_url)
    fm = parse_frontmatter(skill_md)
    name = clean_cell(fm["name"])  # normalize once; row, dup check, and registry all use the same form
    cost = cost_cell(estimate_tokens(skill_md), estimate_tokens(fm["name"] + " " + fm["description"]))
    last_edit = last_edit_from_commits(owner_repo, segments[0], "/".join(segments[1:-1]))
    row = build_row(
        name, fm["description"].rstrip("."), trigger,
        agents_cell(fields["Agents tested"]), cost, fields["Maturity"],
        detect_license(owner_repo), last_edit, owner_repo, dir_url,
    )
    text = open(README).read()
    new_text = insert_row(text, category, row, name, date)
    open(README, "w").write(new_text)
    registry = _load_sources()
    update_sources(registry, name, raw_url, category)
    _save_sources(registry)
    _write_github_output(name=name, url=dir_url)
    print(f"added: {name} -> {category}")


def cmd_add_collection(issue_body_file):
    fields = parse_issue_body(open(issue_body_file).read())
    url = (fields.get("Repository URL") or "").strip()
    table = fields.get("Table")
    owner, repo = parse_repo_url(url)  # rejects non-GitHub URLs before any fetch
    owner_repo = f"{owner}/{repo}"
    repo_data = ensure_repo_exists(owner_repo)
    description = None
    if table == "Collections":
        description = fields.get("Description")
        if not description:
            raise ValueError("Collections entries require a description")
        name = owner_repo
        row = build_collection_row(owner_repo, description.rstrip("."), detect_license(owner_repo))
    elif table == "Registries & lists":
        type_ = fields.get("Type (registries only)")
        if type_ not in REGISTRY_TYPES:
            raise ValueError(f"unknown registry type: {type_}")
        name = f"{repo} ({owner})"
        row = build_registry_row(name, type_, owner_repo)
    else:
        raise ValueError(f"unknown table: {table}")
    text = open(README).read()
    new_text = insert_collection_row(text, table, row, name)
    open(README, "w").write(new_text)
    stars = repo_data.get("stargazers_count") or 0
    automerge = automerge_eligible(stars, description)
    _write_github_output(
        name=name, url=f"https://github.com/{owner_repo}",
        stars=stars, automerge=str(automerge).lower(),
    )
    print(f"added: {name} -> {table} (stars={stars}, automerge={automerge})")


def cmd_add_plugin(issue_body_file):
    fields = parse_issue_body(open(issue_body_file).read())
    url = (fields.get("Repository URL") or "").strip()
    description = fields.get("Description")
    owner, repo = parse_repo_url(url)  # rejects non-GitHub URLs before any fetch
    owner_repo = f"{owner}/{repo}"
    repo_data = ensure_repo_exists(owner_repo)
    if not description:
        raise ValueError("Plugin marketplace entries require a description")
    row = build_collection_row(owner_repo, description.rstrip("."), detect_license(owner_repo))
    text = open(README).read()
    new_text = insert_collection_row(text, "Plugin marketplaces", row, owner_repo)
    open(README, "w").write(new_text)
    stars = repo_data.get("stargazers_count") or 0
    automerge = automerge_eligible(stars, description)
    _write_github_output(
        name=owner_repo, url=f"https://github.com/{owner_repo}",
        stars=stars, automerge=str(automerge).lower(),
    )
    print(f"added: {owner_repo} -> Plugin marketplaces (stars={stars}, automerge={automerge})")


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
    text = open(README).read()
    new_text = remeasure_text(text, registry, date) if registry else text
    new_text = refresh_last_edits(new_text)
    if new_text != text:
        open(README, "w").write(new_text)


def readme_urls(text):
    """All https URLs used as markdown link or image targets."""
    return sorted(set(re.findall(r"\]\((https://[^)\s]+)\)", text)))


def readme_local_links(text):
    """Relative file targets like (CONTRIBUTING.md); skips anchors and the
    ../../issues/... GitHub web paths, which only resolve on github.com."""
    return sorted(set(re.findall(r"\]\((?!https?://|#|\.\./)([^)\s]+)\)", text)))


def check_readme_text(text, url_ok, file_exists):
    """Return a list of problems: category headings/TOC entries missing for
    any CATEGORIES member, broken external links, missing local link targets."""
    problems = []
    for cat in sorted(CATEGORIES):
        if f"## {cat}\n" not in text:
            problems.append(f"missing category heading: {cat}")
        if f"[{cat}](#" not in text:
            problems.append(f"missing TOC entry: {cat}")
    for path in readme_local_links(text):
        if not file_exists(path):
            problems.append(f"missing local link target: {path}")
    for url in readme_urls(text):
        if not url_ok(url):
            problems.append(f"broken link: {url}")
    return problems


def _url_ok(url):
    """True when a link is reachable, False only on a definitive-dead signal.

    The check exists to catch dead skill/collection repos, so it must not fail
    the build on transient noise: a rate limit (429), server outage (5xx), bot
    block (401/403), or network timeout says nothing about whether the target
    is gone. Only a 404/410 is a genuine "this link is dead". Everything else
    is warned and treated as reachable, mirroring how the GitHub-API helpers
    let outages propagate rather than minting a wrong verdict."""
    req = urllib.request.Request(url, headers={"User-Agent": "skill-dictionary-bot"})
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return 200 <= resp.status < 400
        except urllib.error.HTTPError as e:
            if e.code in (404, 410):
                print(f"  {url}: {e}", file=sys.stderr)
                return False
            # 429/5xx/403/etc: transient or bot-block, not proof of a dead link.
            print(f"  {url}: {e} (transient, treated as reachable)", file=sys.stderr)
            return True
        except Exception as e:
            if attempt == 0:
                continue  # one retry for a flaky network before giving benefit of doubt
            print(f"  {url}: {e} (unreachable, treated as reachable)", file=sys.stderr)
            return True


def cmd_check():
    text = open(README).read()
    problems = check_readme_text(text, _url_ok, os.path.exists)
    for p in problems:
        print(p, file=sys.stderr)
    if problems:
        raise SystemExit(1)
    print(f"README ok: {len(readme_urls(text))} links, "
          f"{len(readme_local_links(text))} local targets, {len(CATEGORIES)} categories")


def main(argv):
    parser = argparse.ArgumentParser(prog="dictionary.py", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="add a skill/collection/plugin row from an issue-form body")
    p_add.add_argument("--kind", choices=["skill", "collection", "plugin"], default="skill",
                       help="submission kind (derived from issue labels)")
    p_add.add_argument("--issue-body", required=True, help="file containing the issue body")
    # Required for all kinds so the workflow can pass one command; collection
    # and plugin rows ignore it (they have no as-of date column).
    p_add.add_argument("--date", required=True, help="as-of date, YYYY-MM")

    p_rem = sub.add_parser("remeasure", help="refresh token costs from skill-sources.json")
    p_rem.add_argument("--date", required=True, help="as-of date, YYYY-MM")

    sub.add_parser("check", help="verify README links, local targets, and category TOC")

    args = parser.parse_args(argv)
    if args.command == "add":
        if args.kind == "collection":
            cmd_add_collection(args.issue_body)
        elif args.kind == "plugin":
            cmd_add_plugin(args.issue_body)
        else:
            cmd_add(args.issue_body, args.date)
    elif args.command == "check":
        cmd_check()
    else:
        cmd_remeasure(args.date)


if __name__ == "__main__":
    main(sys.argv[1:])
