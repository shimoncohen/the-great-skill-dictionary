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


if __name__ == "__main__":
    unittest.main()
