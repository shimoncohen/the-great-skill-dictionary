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
