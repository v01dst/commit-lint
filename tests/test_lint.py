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

class CustomTypesTests(unittest.TestCase):
    def setUp(self):
        import json, tempfile, os
        self.tmp = tempfile.mkdtemp()
        self.config = os.path.join(self.tmp, "types.json")
        with open(self.config, "w") as f:
            json.dump({"types": {"wip": "work in progress", "spike": "exploration"}}, f)

    def test_custom_type_accepted_with_config(self):
        from commit_lint import load_types
        types = load_types(self.config)
        r = lint("wip: half done feature", types)
        self.assertTrue(r.ok)
        r2 = lint("spike: try new cache", types)
        self.assertTrue(r2.ok)

    def test_custom_type_rejected_without_config(self):
        r = lint("wip: half done feature")
        self.assertFalse(r.ok)

    def test_env_var_config(self):
        import os
        from commit_lint import load_types
        old = os.environ.get("COMMIT_LINT_CONFIG")
        os.environ["COMMIT_LINT_CONFIG"] = self.config
        try:
            types = load_types(None)
            self.assertIn("wip", types)
        finally:
            if old is None:
                del os.environ["COMMIT_LINT_CONFIG"]
            else:
                os.environ["COMMIT_LINT_CONFIG"] = old

    def test_invalid_config_entries_ignored(self):
        import json
        from commit_lint import load_types
        bad = self.config + ".bad"
        with open(bad, "w") as f:
            json.dump({"types": {"BAD TYPE": "x", 123: "y", "ok-type": "fine"}}, f)
        types = load_types(bad)
        self.assertNotIn("BAD TYPE", types)
        self.assertIn("ok-type", types)

    def test_main_with_config_file(self):
        import os
        msg = os.path.join(self.tmp, "msg.txt")
        with open(msg, "w") as f:
            f.write("wip: half done feature\n")
        code = main(["--config" if False else self.config, msg])
        self.assertEqual(code, 0)

class ScopeWhitelistTests(unittest.TestCase):
    def setUp(self):
        import json, tempfile, os
        self.tmp = tempfile.mkdtemp()
        self.config = os.path.join(self.tmp, "cfg.json")
        with open(self.config, "w") as f:
            json.dump({"scopes": ["api", "web", "core"]}, f)

    def test_allowed_scope_passes(self):
        from commit_lint import load_config_file, load_types
        cfg = load_config_file(self.config)
        types = load_types(self.config)
        scopes = {str(x) for x in cfg["scopes"]}
        r = lint("fix(api): handle null cursor", types, scopes)
        self.assertTrue(r.ok)

    def test_disallowed_scope_fails(self):
        from commit_lint import load_config_file, load_types
        cfg = load_config_file(self.config)
        types = load_types(self.config)
        scopes = {str(x) for x in cfg["scopes"]}
        r = lint("fix(db): wrong scope", types, scopes)
        self.assertFalse(r.ok)
        self.assertTrue(any("unknown scope 'db'" in e for e in r.errors))

    def test_no_scope_still_passes(self):
        from commit_lint import load_config_file, load_types
        cfg = load_config_file(self.config)
        types = load_types(self.config)
        scopes = {str(x) for x in cfg["scopes"]}
        r = lint("chore: routine maintenance", types, scopes)
        self.assertTrue(r.ok)

    def test_no_whitelist_means_any_scope(self):
        r = lint("fix(anything-goes): fine")
        self.assertTrue(r.ok)
