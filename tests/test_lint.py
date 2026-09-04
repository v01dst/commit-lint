import unittest

from commit_lint import lint, main, format_report


class LintTests(unittest.TestCase):
    def test_valid_plain(self):
        r = lint("feat: add user export")
        self.assertTrue(r.ok)
        self.assertEqual(r.type, "feat")
        self.assertEqual(r.errors, [])

    def test_valid_scope_and_bang(self):
        r = lint("fix(api)!: handle null cursor")
        self.assertTrue(r.ok)
        self.assertEqual(r.parsed["scope"], "api")
        self.assertEqual(r.parsed["bang"], "!")

    def test_valid_multi_line(self):
        r = lint("feat: add export\n\nLonger body explaining why.\n")
        self.assertTrue(r.ok)

    def test_empty_rejected(self):
        self.assertFalse(lint("").ok)
        self.assertFalse(lint("   \n").ok)

    def test_unknown_type(self):
        r = lint("magic: do things")
        self.assertFalse(r.ok)
        self.assertTrue(any("unknown type" in e for e in r.errors))

    def test_missing_colon(self):
        r = lint("feat add user export")
        self.assertFalse(r.ok)
        self.assertTrue(any("format" in e for e in r.errors))

    def test_header_too_long(self):
        r = lint("feat: " + "x" * 80)
        self.assertFalse(r.ok)
        self.assertTrue(any("<= 72" in e for e in r.errors))

    def test_subject_capital_is_warning_only(self):
        r = lint("feat: Add user export")
        self.assertTrue(r.ok)
        self.assertTrue(any("capital" in w for w in r.warnings))

    def test_subject_punctuation_rejected(self):
        r = lint("feat: add user export.")
        self.assertFalse(r.ok)

    def test_missing_body_separator(self):
        r = lint("feat: add export\nbody right away")
        self.assertTrue(r.ok)
        self.assertTrue(any("blank" in w for w in r.warnings))

    def test_long_body_line_warns(self):
        r = lint("feat: add export\n\n" + "y" * 120)
        self.assertTrue(r.ok)
        self.assertTrue(any("exceeds 100" in w for w in r.warnings))

    def test_merge_commits_pass(self):
        r = lint("Merge branch 'feature/x' into main")
        self.assertTrue(r.ok)

    def test_all_types_accepted(self):
        for t in ["feat", "fix", "docs", "style", "refactor", "perf", "test", "build", "ci", "chore", "revert"]:
            self.assertTrue(lint(f"{t}: ok thing").ok, t)

    def test_strict_upgrades_warnings(self):
        code = main(["--strict", "feat: Add export"])
        self.assertEqual(code, 1)
        code_ok = main(["feat: Add export"])
        self.assertEqual(code_ok, 0)


class FormatTests(unittest.TestCase):
    def test_report_shows_type(self):
        r = lint("fix(api): handle null")
        report = format_report(r, "fix(api): handle null")
        self.assertIn("valid", report)
        self.assertIn("bug fix", report)
        self.assertIn("api", report)


if __name__ == "__main__":
    unittest.main(verbosity=2)
