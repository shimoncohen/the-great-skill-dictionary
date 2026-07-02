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
