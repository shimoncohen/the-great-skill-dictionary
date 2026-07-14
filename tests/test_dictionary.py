import unittest
import urllib.error
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
import dictionary


class TestFrontmatter(unittest.TestCase):
    def test_parses_name_and_description(self):
        text = "---\nname: my-skill\ndescription: Does a thing well\n---\n\n# Body\ncontent"
        fm = dictionary.parse_frontmatter(text)
        self.assertEqual(fm["name"], "my-skill")
        self.assertEqual(fm["description"], "Does a thing well")

    def test_missing_frontmatter_raises(self):
        with self.assertRaises(ValueError):
            dictionary.parse_frontmatter("# Just a heading\nno frontmatter")

    def test_ignores_other_keys_and_colons_in_value(self):
        text = "---\nname: x\ndescription: Use when: always\nlicense: MIT\n---\nbody"
        fm = dictionary.parse_frontmatter(text)
        self.assertEqual(fm["description"], "Use when: always")

    def test_folded_scalar_description(self):
        text = "---\nname: x\ndescription: >-\n  line one\n  line two\n---\nbody"
        fm = dictionary.parse_frontmatter(text)
        self.assertEqual(fm["description"], "line one line two")


class TestTokens(unittest.TestCase):
    def test_estimate_words_times_1_3(self):
        text = " ".join(["word"] * 1000)
        self.assertEqual(dictionary.estimate_tokens(text), 1300)

    def test_format_small_rounds_to_ten(self):
        self.assertEqual(dictionary.format_tokens(143), "~140")

    def test_format_tokens_3_returns_ten(self):
        self.assertEqual(dictionary.format_tokens(3), "~10")

    def test_format_k(self):
        self.assertEqual(dictionary.format_tokens(2100), "~2.1k")
        self.assertEqual(dictionary.format_tokens(2000), "~2k")
        self.assertEqual(dictionary.format_tokens(12600), "~13k")

    def test_cost_cell(self):
        self.assertEqual(dictionary.cost_cell(2100, 143), "~2.1k / ~140")


class TestUrls(unittest.TestCase):
    def test_blob_url_to_raw(self):
        self.assertEqual(
            dictionary.to_raw_url("https://github.com/o/r/blob/main/skills/x/SKILL.md"),
            "https://raw.githubusercontent.com/o/r/main/skills/x/SKILL.md",
        )

    def test_raw_url_passthrough(self):
        u = "https://raw.githubusercontent.com/o/r/main/SKILL.md"
        self.assertEqual(dictionary.to_raw_url(u), u)

    def test_repo_web_url(self):
        self.assertEqual(
            dictionary.repo_web_url("https://github.com/o/r/blob/main/skills/x/SKILL.md"),
            ("o/r", "https://github.com/o/r/tree/main/skills/x"),
        )

    def test_rejects_non_github(self):
        with self.assertRaises(ValueError):
            dictionary.to_raw_url("https://evil.example.com/SKILL.md")


class TestParseSkillUrl(unittest.TestCase):
    def test_valid_blob_url(self):
        dictionary.parse_skill_url("https://github.com/owner/repo/blob/main/skills/x/SKILL.md")

    def test_valid_raw_url(self):
        dictionary.parse_skill_url("https://raw.githubusercontent.com/owner/repo/main/SKILL.md")

    def assert_rejected(self, url):
        with self.assertRaises(ValueError):
            dictionary.parse_skill_url(url)

    def test_rejects_other_domains(self):
        self.assert_rejected("https://gitlab.com/o/r/blob/main/SKILL.md")
        self.assert_rejected("https://evil.example.com/SKILL.md")

    def test_rejects_lookalike_hosts(self):
        self.assert_rejected("https://github.com.evil.com/o/r/blob/main/SKILL.md")
        self.assert_rejected("https://notgithub.com/o/r/blob/main/SKILL.md")
        self.assert_rejected("https://github.com@evil.com/o/r/blob/main/SKILL.md")

    def test_rejects_http(self):
        self.assert_rejected("http://github.com/o/r/blob/main/SKILL.md")

    def test_accepts_any_markdown_filename_case_insensitive(self):
        dictionary.parse_skill_url("https://github.com/o/r/blob/main/skills/x/skill.md")
        dictionary.parse_skill_url("https://github.com/o/r/blob/main/my-skill.MD")
        dictionary.parse_skill_url("https://github.com/o/r/blob/main/README.md")

    def test_rejects_non_markdown_target(self):
        self.assert_rejected("https://github.com/o/r/tree/main/skills/x")
        self.assert_rejected("https://github.com/o/r/blob/main/SKILL.md.evil")
        self.assert_rejected("https://github.com/o/r/blob/main/script.py")
        self.assert_rejected("https://github.com/o/r/blob/SKILL.md")

    def test_rejects_path_traversal_and_empty_segments(self):
        self.assert_rejected("https://github.com/o/r/blob/main/../../x/SKILL.md")
        self.assert_rejected("https://github.com/o/r/blob/main//x/SKILL.md")
        self.assert_rejected("https://raw.githubusercontent.com/o/r/main/../SKILL.md")

    def test_rejects_query_fragment_and_encoding_tricks(self):
        self.assert_rejected("https://github.com/o/r/blob/main/SKILL.md?token=x")
        self.assert_rejected("https://github.com/o/r/blob/main/SKILL.md#frag")
        self.assert_rejected("https://github.com/o/r/blob/main/%2e%2e/SKILL.md")
        self.assert_rejected("https://github.com/o/r/blob/main/a b/SKILL.md")

    def test_rejects_bad_owner_or_repo(self):
        self.assert_rejected("https://github.com/o?x/r/blob/main/SKILL.md")
        self.assert_rejected("https://github.com/o/../blob/main/SKILL.md")
        self.assert_rejected("https://github.com/o/.git/blob/main/SKILL.md")

    def test_repo_web_url_any_markdown_name(self):
        self.assertEqual(
            dictionary.repo_web_url("https://github.com/o/r/blob/main/skills/x/my-skill.md"),
            ("o/r", "https://github.com/o/r/tree/main/skills/x"),
        )


class TestIssueBody(unittest.TestCase):
    BODY = (
        "### SKILL.md URL\n\nhttps://github.com/o/r/blob/main/SKILL.md\n\n"
        "### Category\n\n🧪 Testing\n\n"
        "### Agents tested\n\nCC, CX\n\n"
        "### Maturity\n\nstable\n\n"
        "### Trigger (optional — defaults to auto)\n\n_No response_\n"
    )

    def test_parse_fields(self):
        f = dictionary.parse_issue_body(self.BODY)
        self.assertEqual(f["SKILL.md URL"], "https://github.com/o/r/blob/main/SKILL.md")
        self.assertEqual(f["Category"], "🧪 Testing")
        self.assertIsNone(f["Trigger (optional — defaults to auto)"])

    def test_unanswered_dropdown_renders_as_None_string(self):
        body = "### Trigger (optional \u2014 defaults to auto)\n\nNone\n"
        f = dictionary.parse_issue_body(body)
        self.assertIsNone(f["Trigger (optional \u2014 defaults to auto)"])

    def test_agents_cell(self):
        self.assertEqual(dictionary.agents_cell("CC, CX"), "CC · CX")
        self.assertEqual(dictionary.agents_cell("✅ any"), "✅ any")
        self.assertEqual(dictionary.agents_cell("✅ any, CC"), "✅ any")


SAMPLE_README = """# Title

## 🧪 Testing

Test authoring.

| Skill | Description | Trigger | Agents | Cost ~(invoke / always-on) | Maturity | License | Last edit | Repo |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| alpha | A | auto | ✅ any | ~1k / ~50 | stable | MIT | 2026-01-05 | [r](https://github.com/a/r/tree/main/skills/alpha) |
| zeta | Z | auto | ✅ any | ~1k / ~50 | stable | MIT | 2026-01-05 | [r](https://github.com/z/r) |

*Token counts approximate, measured as of 2026-07.*

## 🔍 Research

Multi-source research.

No skills catalogued yet — [contribute](#contributing)!

## 📦 Skill Collections & Registries
"""


class TestInsertRow(unittest.TestCase):
    ROW = "| mid | M | auto | ✅ any | ~2k / ~60 | stable | MIT | 2026-02-01 | [r](https://github.com/m/r) |"

    def test_sorted_insert(self):
        out = dictionary.insert_row(SAMPLE_README, "🧪 Testing", self.ROW, "mid", "2026-08")
        lines = out.splitlines()
        names = [l.split("|")[1].strip() for l in lines if l.startswith("| ") and not l.startswith("| Skill") and not l.startswith("| ---")]
        self.assertEqual(names, ["alpha", "mid", "zeta"])

    def test_preserves_asof_date(self):
        # Only `remeasure` refreshes costs, so inserting a row must not
        # touch the existing footnote date.
        out = dictionary.insert_row(SAMPLE_README, "🧪 Testing", self.ROW, "mid", "2026-08")
        self.assertIn("measured as of 2026-07", out)
        self.assertNotIn("measured as of 2026-08", out)

    def test_empty_category_gets_table(self):
        out = dictionary.insert_row(SAMPLE_README, "🔍 Research", self.ROW, "mid", "2026-08")
        section = out.split("## 🔍 Research")[1].split("## 📦")[0]
        self.assertIn("| Skill | Description |", section)
        self.assertIn("| mid |", section)
        self.assertIn("measured as of 2026-08", section)
        self.assertNotIn("No skills catalogued yet", section)

    def test_duplicate_name_raises(self):
        with self.assertRaises(ValueError):
            dictionary.insert_row(SAMPLE_README, "🧪 Testing", self.ROW.replace("mid", "alpha"), "alpha", "2026-08")

    def test_unknown_category_raises(self):
        with self.assertRaises(ValueError):
            dictionary.insert_row(SAMPLE_README, "🚀 Nope", self.ROW, "mid", "2026-08")

    def test_cross_category_duplicate_raises(self):
        # "alpha" already exists in "🧪 Testing"; inserting into "🔍 Research" must also raise
        row = self.ROW.replace("mid", "alpha")
        with self.assertRaises(ValueError):
            dictionary.insert_row(SAMPLE_README, "🔍 Research", row, "alpha", "2026-08")

    def test_insert_is_pure_row_addition(self):
        out = dictionary.insert_row(SAMPLE_README, "🧪 Testing", self.ROW, "mid", "2026-08")
        self.assertEqual(out.replace(self.ROW + "\n", ""), SAMPLE_README)


class TestRegistryAndReplace(unittest.TestCase):
    def test_replace_cost_cell(self):
        row = "| alpha | A | auto | ✅ any | ~1k / ~50 | stable | MIT | 2026-01-05 | [r](u) |"
        out = dictionary.replace_cost_cell(row, "~3k / ~90")
        self.assertEqual(out, "| alpha | A | auto | ✅ any | ~3k / ~90 | stable | MIT | 2026-01-05 | [r](u) |")

    def test_replace_last_edit_cell(self):
        row = "| alpha | pipe \\| desc | auto | ✅ any | ~1k / ~50 | stable | MIT | 2026-01-05 | [r](u) |"
        out = dictionary.replace_last_edit_cell(row, "2026-07-11")
        self.assertEqual(out, "| alpha | pipe \\| desc | auto | ✅ any | ~1k / ~50 | stable | MIT | 2026-07-11 | [r](u) |")

    def test_update_sources(self):
        reg = {}
        dictionary.update_sources(reg, "my-skill", "https://raw.githubusercontent.com/o/r/main/SKILL.md", "🧪 Testing")
        self.assertEqual(reg["my-skill"]["category"], "🧪 Testing")


class TestRemeasureText(unittest.TestCase):
    def test_remeasure_updates_row_and_date(self):
        fetched = {"https://raw.x/SKILL.md": "---\nname: alpha\ndescription: A\n---\n" + ("w " * 2000)}
        registry = {"alpha": {"url": "https://raw.x/SKILL.md", "category": "🧪 Testing"}}
        out = dictionary.remeasure_text(SAMPLE_README, registry, "2026-09", fetcher=fetched.get)
        row = next(l for l in out.splitlines() if l.startswith("| alpha |"))
        self.assertIn("~2.6k", row)
        self.assertIn("measured as of 2026-09", out)

    def test_missing_skill_skipped(self):
        registry = {"ghost": {"url": "https://raw.x/S.md", "category": "🧪 Testing"}}
        out = dictionary.remeasure_text(SAMPLE_README, registry, "2026-09", fetcher=lambda u: None)
        self.assertEqual(out, SAMPLE_README)

    def test_missing_category_no_crash(self):
        """Registry entry pointing to non-existent category must not raise."""
        fetched = {"https://raw.x/SKILL.md": "---\nname: alpha\ndescription: A\n---\n" + ("w " * 2000)}
        registry = {"alpha": {"url": "https://raw.x/SKILL.md", "category": "🚀 Nonexistent"}}
        out = dictionary.remeasure_text(SAMPLE_README, registry, "2026-09", fetcher=fetched.get)
        self.assertTrue(any(l.startswith("| alpha |") for l in out.splitlines()))


class TestCleanCell(unittest.TestCase):
    def test_pipe_escaped_and_newline_collapsed(self):
        self.assertEqual(dictionary.clean_cell("a |\nb"), "a \\| b")

    def test_strips_leading_trailing_whitespace(self):
        self.assertEqual(dictionary.clean_cell("  hello  "), "hello")

    def test_multiple_spaces_collapsed(self):
        self.assertEqual(dictionary.clean_cell("a  b   c"), "a b c")


class TestBuildRowCleaning(unittest.TestCase):
    def test_description_cleaned(self):
        row = dictionary.build_row(
            "skill", "x | y\nz", "auto", "✅ any", "~1k / ~10", "stable", "MIT",
            "2026-07-11", "o/r", "https://github.com/o/r",
        )
        self.assertIn("x \\| y z", row)
        self.assertIn("| 2026-07-11 |", row)

    def test_non_github_url_raises(self):
        with self.assertRaises(ValueError):
            dictionary.build_row(
                "skill", "desc", "auto", "✅ any", "~1k / ~10", "stable", "MIT",
                "2026-07-11", "o/r", "https://evil.com/o/r",
            )


class TestValidateFields(unittest.TestCase):
    def test_bad_category_raises(self):
        with self.assertRaises(ValueError):
            dictionary.validate_fields("🚀 Nope", "CC", "stable", "auto")

    def test_bad_agent_raises(self):
        with self.assertRaises(ValueError):
            dictionary.validate_fields("🧪 Testing", "ZZ", "stable", "auto")

    def test_bad_maturity_raises(self):
        with self.assertRaises(ValueError):
            dictionary.validate_fields("🧪 Testing", "CC", "legacy", "auto")

    def test_bad_trigger_raises(self):
        with self.assertRaises(ValueError):
            dictionary.validate_fields("🧪 Testing", "CC", "stable", "weekly")

    def test_valid_fields_no_raise(self):
        dictionary.validate_fields("🧪 Testing", "CC, CX", "stable", "auto")


SAMPLE_COLLECTIONS = """## 📦 Skill Collections & Registries

Intro text.

### Collections

| Repo | Description | Stars | License | Last edit | Link |
| --- | --- | --- | --- | --- | --- |
| a/alpha | First | ![Stars](https://img.shields.io/github/stars/a/alpha?style=flat-square&label=%E2%AD%90) | MIT | ![Last commit](https://img.shields.io/github/last-commit/a/alpha?style=flat-square&label=) | [GitHub](https://github.com/a/alpha) |
| z/zeta | Last | ![Stars](https://img.shields.io/github/stars/z/zeta?style=flat-square&label=%E2%AD%90) | MIT | ![Last commit](https://img.shields.io/github/last-commit/z/zeta?style=flat-square&label=) | [GitHub](https://github.com/z/zeta) |

*Footnote.*

### Registries & lists

| Name | Type | Stars | Last edit | Link |
| --- | --- | --- | --- | --- |
| alist (a) | awesome-list | ![Stars](https://img.shields.io/github/stars/a/alist?style=flat-square&label=%E2%AD%90) | ![Last commit](https://img.shields.io/github/last-commit/a/alist?style=flat-square&label=) | [GitHub](https://github.com/a/alist) |
| WebHub | marketplace | — | — | [webhub.example](https://webhub.example/) |

## Contributing
"""


class TestParseRepoUrl(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(dictionary.parse_repo_url("https://github.com/owner/repo"), ("owner", "repo"))
        self.assertEqual(dictionary.parse_repo_url("https://github.com/owner/repo/"), ("owner", "repo"))

    def assert_rejected(self, url):
        with self.assertRaises(ValueError):
            dictionary.parse_repo_url(url)

    def test_rejects_extra_path(self):
        self.assert_rejected("https://github.com/o/r/tree/main")
        self.assert_rejected("https://github.com/o")

    def test_rejects_non_github(self):
        self.assert_rejected("https://gitlab.com/o/r")
        self.assert_rejected("https://github.com.evil.com/o/r")
        self.assert_rejected("https://github.com@evil.com/o/r")

    def test_rejects_http_query_fragment(self):
        self.assert_rejected("http://github.com/o/r")
        self.assert_rejected("https://github.com/o/r?tab=stars")
        self.assert_rejected("https://github.com/o/r#readme")

    def test_rejects_bad_names(self):
        self.assert_rejected("https://github.com/o/r.git")
        self.assert_rejected("https://github.com/o/..")
        self.assert_rejected("https://github.com/o?x/r")


def _http_error(code):
    return urllib.error.HTTPError("https://api.github.com/repos/o/r", code, "err", None, None)


class TestEnsureRepoExists(unittest.TestCase):
    def test_existing_repo_no_raise(self):
        dictionary.ensure_repo_exists("o/r", fetcher=lambda u: "{}")

    def test_404_raises_value_error(self):
        def fetcher(u):
            raise _http_error(404)
        with self.assertRaises(ValueError):
            dictionary.ensure_repo_exists("o/ghost", fetcher=fetcher)

    def test_other_http_errors_propagate(self):
        # Rate limit / outage must fail the workflow, not read as "not found"
        def fetcher(u):
            raise _http_error(403)
        with self.assertRaises(urllib.error.HTTPError):
            dictionary.ensure_repo_exists("o/r", fetcher=fetcher)

    def test_queries_repos_api(self):
        seen = []
        dictionary.ensure_repo_exists("o/r", fetcher=lambda u: seen.append(u) or "{}")
        self.assertEqual(seen, ["https://api.github.com/repos/o/r"])

    def test_returns_parsed_metadata(self):
        data = dictionary.ensure_repo_exists(
            "o/r", fetcher=lambda u: '{"stargazers_count": 1234}')
        self.assertEqual(data["stargazers_count"], 1234)


class TestAutomergeEligible(unittest.TestCase):
    def test_enough_stars_plain_description(self):
        self.assertTrue(dictionary.automerge_eligible(1000, "Plain prose description"))

    def test_below_threshold_rejected(self):
        self.assertFalse(dictionary.automerge_eligible(999, "Plain prose"))

    def test_no_description_ok(self):
        # Registries have no free-text description
        self.assertTrue(dictionary.automerge_eligible(5000, None))

    def test_markdown_and_html_rejected(self):
        # Auto-merge publishes the description unreviewed; anything beyond
        # plain prose must wait for a maintainer.
        for desc in (
            "See https://evil.example",
            "a [link](https://x)",
            "an ![image](https://x/i.png)",
            "raw <img src=x>",
            "code `span`",
        ):
            self.assertFalse(dictionary.automerge_eligible(5000, desc), desc)


class TestDetectLicense(unittest.TestCase):
    def test_spdx_id_returned(self):
        fetcher = lambda u: '{"license": {"spdx_id": "MIT"}}'
        self.assertEqual(dictionary.detect_license("o/r", fetcher=fetcher), "MIT")

    def test_noassertion_becomes_dash(self):
        fetcher = lambda u: '{"license": {"spdx_id": "NOASSERTION"}}'
        self.assertEqual(dictionary.detect_license("o/r", fetcher=fetcher), "—")

    def test_404_means_no_license(self):
        def fetcher(u):
            raise _http_error(404)
        self.assertEqual(dictionary.detect_license("o/r", fetcher=fetcher), "—")

    def test_other_http_errors_propagate(self):
        # Rate limit must fail the workflow, not silently mint "—"
        def fetcher(u):
            raise _http_error(403)
        with self.assertRaises(urllib.error.HTTPError):
            dictionary.detect_license("o/r", fetcher=fetcher)


class TestLastEdit(unittest.TestCase):
    COMMITS = '[{"commit": {"committer": {"date": "2026-07-03T12:34:56Z"}}}]'

    def test_commit_date_returned(self):
        self.assertEqual(
            dictionary.last_edit_from_commits("o/r", "main", "skills/x", fetcher=lambda u: self.COMMITS),
            "2026-07-03",
        )

    def test_query_includes_ref_and_path(self):
        seen = []
        dictionary.last_edit_from_commits("o/r", "main", "skills/x",
                                          fetcher=lambda u: seen.append(u) or self.COMMITS)
        self.assertEqual(seen, ["https://api.github.com/repos/o/r/commits?per_page=1&sha=main&path=skills/x"])

    def test_root_skill_omits_path(self):
        seen = []
        dictionary.last_edit_from_commits("o/r", "main", "",
                                          fetcher=lambda u: seen.append(u) or self.COMMITS)
        self.assertEqual(seen, ["https://api.github.com/repos/o/r/commits?per_page=1&sha=main"])

    def test_no_commits_means_dash(self):
        self.assertEqual(dictionary.last_edit_from_commits("o/r", "main", "x", fetcher=lambda u: "[]"), "—")

    def test_404_means_dash(self):
        def fetcher(u):
            raise _http_error(404)
        self.assertEqual(dictionary.last_edit_from_commits("o/r", "gone", "x", fetcher=fetcher), "—")

    def test_other_http_errors_propagate(self):
        def fetcher(u):
            raise _http_error(403)
        with self.assertRaises(urllib.error.HTTPError):
            dictionary.last_edit_from_commits("o/r", "main", "x", fetcher=fetcher)

class TestRefreshLastEdits(unittest.TestCase):
    def fake_fetch(self, url):
        if "/commits?" not in url:
            raise AssertionError(f"refresh should only hit the commits API, got: {url}")
        return '[{"commit": {"committer": {"date": "2026-07-08T00:00:00Z"}}}]'

    def test_skill_row_uses_commit_date_of_tree_path(self):
        out = dictionary.refresh_last_edits(SAMPLE_README, fetcher=self.fake_fetch)
        row = next(l for l in out.splitlines() if l.startswith("| alpha |"))
        self.assertIn("| 2026-07-08 |", row)

    def test_bare_repo_link_skipped(self):
        out = dictionary.refresh_last_edits(SAMPLE_README, fetcher=self.fake_fetch)
        row = next(l for l in out.splitlines() if l.startswith("| zeta |"))
        self.assertIn("| 2026-01-05 |", row)

    def test_collections_and_registries_untouched(self):
        # Their Last edit cells hold self-updating badges — no API calls, no edits.
        out = dictionary.refresh_last_edits(SAMPLE_COLLECTIONS, fetcher=self.fake_fetch)
        self.assertEqual(out, SAMPLE_COLLECTIONS)

    def test_lookup_failure_leaves_row_unchanged(self):
        def fetcher(u):
            raise _http_error(403)
        out = dictionary.refresh_last_edits(SAMPLE_README, fetcher=fetcher)
        self.assertEqual(out, SAMPLE_README)

    def test_unexpected_errors_propagate(self):
        def fetcher(u):
            raise RuntimeError("bug, not an API failure")
        with self.assertRaises(RuntimeError):
            dictionary.refresh_last_edits(SAMPLE_README, fetcher=fetcher)

    def test_only_changes_last_edit_cells(self):
        out = dictionary.refresh_last_edits(SAMPLE_README, fetcher=self.fake_fetch)
        self.assertEqual(out.replace("| 2026-07-08 |", "| 2026-01-05 |"), SAMPLE_README)


class TestStarsBadge(unittest.TestCase):
    def test_badge(self):
        self.assertEqual(
            dictionary.stars_badge("o/r"),
            "![Stars](https://img.shields.io/github/stars/o/r?style=flat-square&label=%E2%AD%90)",
        )

    def test_last_edit_badge(self):
        self.assertEqual(
            dictionary.last_edit_badge("o/r"),
            "![Last commit](https://img.shields.io/github/last-commit/o/r?style=flat-square&label=)",
        )


class TestBuildCollectionRows(unittest.TestCase):
    def test_collection_row_shape(self):
        row = dictionary.build_collection_row("o/r", "Does | things", "MIT")
        self.assertEqual(
            row,
            "| o/r | Does \\| things "
            "| ![Stars](https://img.shields.io/github/stars/o/r?style=flat-square&label=%E2%AD%90) "
            "| MIT "
            "| ![Last commit](https://img.shields.io/github/last-commit/o/r?style=flat-square&label=) "
            "| [GitHub](https://github.com/o/r) |",
        )

    def test_registry_row_shape(self):
        row = dictionary.build_registry_row("r (o)", "registry", "o/r")
        self.assertEqual(
            row,
            "| r (o) | registry "
            "| ![Stars](https://img.shields.io/github/stars/o/r?style=flat-square&label=%E2%AD%90) "
            "| ![Last commit](https://img.shields.io/github/last-commit/o/r?style=flat-square&label=) "
            "| [GitHub](https://github.com/o/r) |",
        )


class TestInsertCollectionRow(unittest.TestCase):
    def test_sorted_insert_collections(self):
        row = dictionary.build_collection_row("m/mid", "Mid", "MIT")
        out = dictionary.insert_collection_row(SAMPLE_COLLECTIONS, "Collections", row, "m/mid")
        section = out.split("### Collections")[1].split("### Registries")[0]
        names = [l.split("|")[1].strip() for l in section.splitlines()
                 if l.startswith("| ") and not l.startswith(("| Repo |", "| ---"))]
        self.assertEqual(names, ["a/alpha", "m/mid", "z/zeta"])

    def test_insert_does_not_leak_into_registries(self):
        row = dictionary.build_collection_row("zz/last", "Last of all", "MIT")
        out = dictionary.insert_collection_row(SAMPLE_COLLECTIONS, "Collections", row, "zz/last")
        self.assertLess(out.find("| zz/last |"), out.find("### Registries & lists"))

    def test_sorted_insert_registries(self):
        row = dictionary.build_registry_row("blist (b)", "registry", "b/blist")
        out = dictionary.insert_collection_row(SAMPLE_COLLECTIONS, "Registries & lists", row, "blist (b)")
        section = out.split("### Registries & lists")[1].split("## Contributing")[0]
        names = [l.split("|")[1].strip() for l in section.splitlines()
                 if l.startswith("| ") and not l.startswith(("| Name |", "| ---"))]
        self.assertEqual(names, ["alist (a)", "blist (b)", "WebHub"])

    def test_duplicate_raises(self):
        row = dictionary.build_collection_row("a/alpha", "Dup", "MIT")
        with self.assertRaises(ValueError):
            dictionary.insert_collection_row(SAMPLE_COLLECTIONS, "Collections", row, "a/alpha")

    def test_duplicate_case_insensitive(self):
        row = dictionary.build_collection_row("A/Alpha", "Dup", "MIT")
        with self.assertRaises(ValueError):
            dictionary.insert_collection_row(SAMPLE_COLLECTIONS, "Collections", row, "A/Alpha")

    def test_unknown_table_raises(self):
        with self.assertRaises(ValueError):
            dictionary.insert_collection_row(SAMPLE_COLLECTIONS, "Nope", "| x |", "x")

    def test_missing_heading_raises(self):
        with self.assertRaises(ValueError):
            dictionary.insert_collection_row("# Empty\n", "Collections", "| x |", "x")

    def test_preserves_blank_lines_around_table(self):
        row = dictionary.build_collection_row("m/mid", "Mid", "MIT")
        out = dictionary.insert_collection_row(SAMPLE_COLLECTIONS, "Collections", row, "m/mid")
        self.assertIn("*Footnote.*\n\n### Registries & lists", out)
        self.assertEqual(out.replace(row + "\n", ""), SAMPLE_COLLECTIONS)


class TestCheckReadme(unittest.TestCase):
    TEXT = (
        "- [🧪 Testing](#-testing)\n\n"
        "## 🧪 Testing\n\n"
        "See [CONTRIBUTING.md](CONTRIBUTING.md) and [repo](https://github.com/o/r) "
        "and ![badge](https://img.shields.io/x) and [issue](../../issues/new) and [top](#top).\n"
    )

    def _check(self, text, url_ok=lambda u: True, file_exists=lambda p: True):
        # Restrict CATEGORIES to the one used in TEXT for focused assertions
        orig = dictionary.CATEGORIES
        dictionary.CATEGORIES = {"🧪 Testing"}
        try:
            return dictionary.check_readme_text(text, url_ok, file_exists)
        finally:
            dictionary.CATEGORIES = orig

    def test_extracts_link_and_image_urls_only(self):
        self.assertEqual(
            dictionary.readme_urls(self.TEXT),
            ["https://github.com/o/r", "https://img.shields.io/x"],
        )

    def test_local_links_skip_anchors_and_web_paths(self):
        self.assertEqual(dictionary.readme_local_links(self.TEXT), ["CONTRIBUTING.md"])

    def test_clean_readme_no_problems(self):
        self.assertEqual(self._check(self.TEXT), [])

    def test_missing_heading_reported(self):
        text = self.TEXT.replace("## 🧪 Testing", "## 🧪 Renamed")
        self.assertIn("missing category heading: 🧪 Testing", self._check(text))

    def test_missing_toc_entry_reported(self):
        text = self.TEXT.replace("- [🧪 Testing](#-testing)\n\n", "")
        self.assertIn("missing TOC entry: 🧪 Testing", self._check(text))

    def test_broken_url_reported(self):
        problems = self._check(self.TEXT, url_ok=lambda u: "shields" not in u)
        self.assertEqual(problems, ["broken link: https://img.shields.io/x"])

    def test_missing_local_target_reported(self):
        problems = self._check(self.TEXT, file_exists=lambda p: False)
        self.assertEqual(problems, ["missing local link target: CONTRIBUTING.md"])


if __name__ == "__main__":
    unittest.main()
