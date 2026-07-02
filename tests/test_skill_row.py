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


if __name__ == "__main__":
    unittest.main()
