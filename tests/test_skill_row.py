import unittest
import urllib.error
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


class TestParseSkillUrl(unittest.TestCase):
    def test_valid_blob_url(self):
        skill_row.parse_skill_url("https://github.com/owner/repo/blob/main/skills/x/SKILL.md")

    def test_valid_raw_url(self):
        skill_row.parse_skill_url("https://raw.githubusercontent.com/owner/repo/main/SKILL.md")

    def assert_rejected(self, url):
        with self.assertRaises(ValueError):
            skill_row.parse_skill_url(url)

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
        skill_row.parse_skill_url("https://github.com/o/r/blob/main/skills/x/skill.md")
        skill_row.parse_skill_url("https://github.com/o/r/blob/main/my-skill.MD")
        skill_row.parse_skill_url("https://github.com/o/r/blob/main/README.md")

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
            skill_row.repo_web_url("https://github.com/o/r/blob/main/skills/x/my-skill.md"),
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
        f = skill_row.parse_issue_body(self.BODY)
        self.assertEqual(f["SKILL.md URL"], "https://github.com/o/r/blob/main/SKILL.md")
        self.assertEqual(f["Category"], "🧪 Testing")
        self.assertIsNone(f["Trigger (optional — defaults to auto)"])

    def test_unanswered_dropdown_renders_as_None_string(self):
        body = "### Trigger (optional \u2014 defaults to auto)\n\nNone\n"
        f = skill_row.parse_issue_body(body)
        self.assertIsNone(f["Trigger (optional \u2014 defaults to auto)"])

    def test_agents_cell(self):
        self.assertEqual(skill_row.agents_cell("CC, CX"), "CC · CX")
        self.assertEqual(skill_row.agents_cell("✅ any"), "✅ any")
        self.assertEqual(skill_row.agents_cell("✅ any, CC"), "✅ any")


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

No skills catalogued yet — [contribute](#contributing)!

## 📦 Skill Collections & Registries
"""


class TestInsertRow(unittest.TestCase):
    ROW = "| mid | M | auto | ✅ any | ~2k / ~60 | stable | MIT | [r](https://github.com/m/r) |"

    def test_sorted_insert(self):
        out = skill_row.insert_row(SAMPLE_README, "🧪 Testing", self.ROW, "mid", "2026-08")
        lines = out.splitlines()
        names = [l.split("|")[1].strip() for l in lines if l.startswith("| ") and not l.startswith("| Skill") and not l.startswith("| ---")]
        self.assertEqual(names, ["alpha", "mid", "zeta"])

    def test_preserves_asof_date(self):
        # Only `remeasure` refreshes costs, so inserting a row must not
        # touch the existing footnote date.
        out = skill_row.insert_row(SAMPLE_README, "🧪 Testing", self.ROW, "mid", "2026-08")
        self.assertIn("measured as of 2026-07", out)
        self.assertNotIn("measured as of 2026-08", out)

    def test_empty_category_gets_table(self):
        out = skill_row.insert_row(SAMPLE_README, "🔍 Research", self.ROW, "mid", "2026-08")
        section = out.split("## 🔍 Research")[1].split("## 📦")[0]
        self.assertIn("| Skill | Description |", section)
        self.assertIn("| mid |", section)
        self.assertIn("measured as of 2026-08", section)
        self.assertNotIn("No skills catalogued yet", section)

    def test_duplicate_name_raises(self):
        with self.assertRaises(ValueError):
            skill_row.insert_row(SAMPLE_README, "🧪 Testing", self.ROW.replace("mid", "alpha"), "alpha", "2026-08")

    def test_unknown_category_raises(self):
        with self.assertRaises(ValueError):
            skill_row.insert_row(SAMPLE_README, "🚀 Nope", self.ROW, "mid", "2026-08")


class TestRegistryAndReplace(unittest.TestCase):
    def test_replace_cost_cell(self):
        row = "| alpha | A | auto | ✅ any | ~1k / ~50 | stable | MIT | [r](u) |"
        out = skill_row.replace_cost_cell(row, "~3k / ~90")
        self.assertEqual(out, "| alpha | A | auto | ✅ any | ~3k / ~90 | stable | MIT | [r](u) |")

    def test_update_sources(self):
        reg = {}
        skill_row.update_sources(reg, "my-skill", "https://raw.githubusercontent.com/o/r/main/SKILL.md", "🧪 Testing")
        self.assertEqual(reg["my-skill"]["category"], "🧪 Testing")


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


class TestCleanCell(unittest.TestCase):
    def test_pipe_escaped_and_newline_collapsed(self):
        self.assertEqual(skill_row.clean_cell("a |\nb"), "a \\| b")

    def test_strips_leading_trailing_whitespace(self):
        self.assertEqual(skill_row.clean_cell("  hello  "), "hello")

    def test_multiple_spaces_collapsed(self):
        self.assertEqual(skill_row.clean_cell("a  b   c"), "a b c")


class TestBuildRowCleaning(unittest.TestCase):
    def test_description_cleaned(self):
        row = skill_row.build_row(
            "skill", "x | y\nz", "auto", "✅ any", "~1k / ~10", "stable", "MIT",
            "o/r", "https://github.com/o/r",
        )
        self.assertIn("x \\| y z", row)

    def test_non_github_url_raises(self):
        with self.assertRaises(ValueError):
            skill_row.build_row(
                "skill", "desc", "auto", "✅ any", "~1k / ~10", "stable", "MIT",
                "o/r", "https://evil.com/o/r",
            )


class TestFrontmatterBlockScalar(unittest.TestCase):
    def test_folded_scalar_description(self):
        text = "---\nname: x\ndescription: >-\n  line one\n  line two\n---\nbody"
        fm = skill_row.parse_frontmatter(text)
        self.assertEqual(fm["description"], "line one line two")


class TestInsertRowCrossCategoryDuplicate(unittest.TestCase):
    def test_cross_category_duplicate_raises(self):
        # "alpha" already exists in "🧪 Testing"; inserting into "🔍 Research" must also raise
        row = "| alpha | A | auto | ✅ any | ~1k / ~10 | stable | MIT | [r](https://github.com/a/r) |"
        with self.assertRaises(ValueError):
            skill_row.insert_row(SAMPLE_README, "🔍 Research", row, "alpha", "2026-08")


class TestFormatTokensSmall(unittest.TestCase):
    def test_format_tokens_3_returns_ten(self):
        self.assertEqual(skill_row.format_tokens(3), "~10")


class TestValidateFields(unittest.TestCase):
    def test_bad_category_raises(self):
        with self.assertRaises(ValueError):
            skill_row.validate_fields("🚀 Nope", "CC", "stable", "auto")

    def test_bad_agent_raises(self):
        with self.assertRaises(ValueError):
            skill_row.validate_fields("🧪 Testing", "ZZ", "stable", "auto")

    def test_bad_maturity_raises(self):
        with self.assertRaises(ValueError):
            skill_row.validate_fields("🧪 Testing", "CC", "legacy", "auto")

    def test_bad_trigger_raises(self):
        with self.assertRaises(ValueError):
            skill_row.validate_fields("🧪 Testing", "CC", "stable", "weekly")

    def test_valid_fields_no_raise(self):
        skill_row.validate_fields("🧪 Testing", "CC, CX", "stable", "auto")


class TestRemeasureMissingCategory(unittest.TestCase):
    def test_missing_category_no_crash(self):
        """Registry entry pointing to non-existent category must not raise."""
        fetched = {"https://raw.x/SKILL.md": "---\nname: alpha\ndescription: A\n---\n" + ("w " * 2000)}
        registry = {"alpha": {"url": "https://raw.x/SKILL.md", "category": "🚀 Nonexistent"}}
        # Must not raise even though the category heading does not exist in SAMPLE_README
        out = skill_row.remeasure_text(SAMPLE_README, registry, "2026-09", fetcher=fetched.get)
        self.assertTrue(any(l.startswith("| alpha |") for l in out.splitlines()))


SAMPLE_COLLECTIONS = """## 📦 Skill Collections & Registries

Intro text.

### Collections

| Repo | Description | Stars | License | Link |
| --- | --- | --- | --- | --- |
| a/alpha | First | ![Stars](https://img.shields.io/github/stars/a/alpha?style=flat-square&label=%E2%AD%90) | MIT | [GitHub](https://github.com/a/alpha) |
| z/zeta | Last | ![Stars](https://img.shields.io/github/stars/z/zeta?style=flat-square&label=%E2%AD%90) | MIT | [GitHub](https://github.com/z/zeta) |

*Footnote.*

### Registries & lists

| Name | Type | Stars | Link |
| --- | --- | --- | --- |
| alist (a) | awesome-list | ![Stars](https://img.shields.io/github/stars/a/alist?style=flat-square&label=%E2%AD%90) | [GitHub](https://github.com/a/alist) |
| WebHub | marketplace | — | [webhub.example](https://webhub.example/) |

## Contributing
"""


class TestParseRepoUrl(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(skill_row.parse_repo_url("https://github.com/owner/repo"), ("owner", "repo"))
        self.assertEqual(skill_row.parse_repo_url("https://github.com/owner/repo/"), ("owner", "repo"))

    def assert_rejected(self, url):
        with self.assertRaises(ValueError):
            skill_row.parse_repo_url(url)

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
        skill_row.ensure_repo_exists("o/r", fetcher=lambda u: "{}")

    def test_404_raises_value_error(self):
        def fetcher(u):
            raise _http_error(404)
        with self.assertRaises(ValueError):
            skill_row.ensure_repo_exists("o/ghost", fetcher=fetcher)

    def test_other_http_errors_propagate(self):
        # Rate limit / outage must fail the workflow, not read as "not found"
        def fetcher(u):
            raise _http_error(403)
        with self.assertRaises(urllib.error.HTTPError):
            skill_row.ensure_repo_exists("o/r", fetcher=fetcher)

    def test_queries_repos_api(self):
        seen = []
        skill_row.ensure_repo_exists("o/r", fetcher=lambda u: seen.append(u) or "{}")
        self.assertEqual(seen, ["https://api.github.com/repos/o/r"])


class TestStarsBadge(unittest.TestCase):
    def test_badge(self):
        self.assertEqual(
            skill_row.stars_badge("o/r"),
            "![Stars](https://img.shields.io/github/stars/o/r?style=flat-square&label=%E2%AD%90)",
        )


class TestBuildCollectionRows(unittest.TestCase):
    def test_collection_row_shape(self):
        row = skill_row.build_collection_row("o/r", "Does | things", "MIT")
        self.assertEqual(
            row,
            "| o/r | Does \\| things "
            "| ![Stars](https://img.shields.io/github/stars/o/r?style=flat-square&label=%E2%AD%90) "
            "| MIT | [GitHub](https://github.com/o/r) |",
        )

    def test_registry_row_shape(self):
        row = skill_row.build_registry_row("r (o)", "registry", "o/r")
        self.assertEqual(
            row,
            "| r (o) | registry "
            "| ![Stars](https://img.shields.io/github/stars/o/r?style=flat-square&label=%E2%AD%90) "
            "| [GitHub](https://github.com/o/r) |",
        )


class TestInsertCollectionRow(unittest.TestCase):
    def test_sorted_insert_collections(self):
        row = skill_row.build_collection_row("m/mid", "Mid", "MIT")
        out = skill_row.insert_collection_row(SAMPLE_COLLECTIONS, "Collections", row, "m/mid")
        section = out.split("### Collections")[1].split("### Registries")[0]
        names = [l.split("|")[1].strip() for l in section.splitlines()
                 if l.startswith("| ") and not l.startswith(("| Repo |", "| ---"))]
        self.assertEqual(names, ["a/alpha", "m/mid", "z/zeta"])

    def test_insert_does_not_leak_into_registries(self):
        row = skill_row.build_collection_row("zz/last", "Last of all", "MIT")
        out = skill_row.insert_collection_row(SAMPLE_COLLECTIONS, "Collections", row, "zz/last")
        self.assertLess(out.find("| zz/last |"), out.find("### Registries & lists"))

    def test_sorted_insert_registries(self):
        row = skill_row.build_registry_row("blist (b)", "registry", "b/blist")
        out = skill_row.insert_collection_row(SAMPLE_COLLECTIONS, "Registries & lists", row, "blist (b)")
        section = out.split("### Registries & lists")[1].split("## Contributing")[0]
        names = [l.split("|")[1].strip() for l in section.splitlines()
                 if l.startswith("| ") and not l.startswith(("| Name |", "| ---"))]
        self.assertEqual(names, ["alist (a)", "blist (b)", "WebHub"])

    def test_duplicate_raises(self):
        row = skill_row.build_collection_row("a/alpha", "Dup", "MIT")
        with self.assertRaises(ValueError):
            skill_row.insert_collection_row(SAMPLE_COLLECTIONS, "Collections", row, "a/alpha")

    def test_duplicate_case_insensitive(self):
        row = skill_row.build_collection_row("A/Alpha", "Dup", "MIT")
        with self.assertRaises(ValueError):
            skill_row.insert_collection_row(SAMPLE_COLLECTIONS, "Collections", row, "A/Alpha")

    def test_unknown_table_raises(self):
        with self.assertRaises(ValueError):
            skill_row.insert_collection_row(SAMPLE_COLLECTIONS, "Nope", "| x |", "x")

    def test_missing_heading_raises(self):
        with self.assertRaises(ValueError):
            skill_row.insert_collection_row("# Empty\n", "Collections", "| x |", "x")

    def test_preserves_blank_lines_around_table(self):
        row = skill_row.build_collection_row("m/mid", "Mid", "MIT")
        out = skill_row.insert_collection_row(SAMPLE_COLLECTIONS, "Collections", row, "m/mid")
        self.assertIn("*Footnote.*\n\n### Registries & lists", out)
        self.assertEqual(out.replace(row + "\n", ""), SAMPLE_COLLECTIONS)


class TestInsertRowPreservesBlankLines(unittest.TestCase):
    def test_insert_is_pure_row_addition(self):
        row = "| mid | M | auto | ✅ any | ~2k / ~60 | stable | MIT | [r](https://github.com/m/r) |"
        out = skill_row.insert_row(SAMPLE_README, "🧪 Testing", row, "mid", "2026-08")
        self.assertEqual(out.replace(row + "\n", ""), SAMPLE_README)


if __name__ == "__main__":
    unittest.main()
