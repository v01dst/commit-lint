"""commit-lint — validate conventional commit messages. Pure stdlib."""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass

TYPES = {
    "feat": "new feature",
    "fix": "bug fix",
    "docs": "documentation",
    "style": "formatting, no code change",
    "refactor": "code change that neither fixes nor adds",
    "perf": "performance improvement",
    "test": "adding or correcting tests",
    "build": "build system or dependencies",
    "ci": "ci configuration",
    "chore": "maintenance",
    "revert": "revert a previous commit",
}

HEADER_RE = re.compile(
    r"^(?P<type>[a-z]+)"
    r"(?:\((?P<scope>[a-z0-9][a-z0-9/_.-]*)\))?"
    r"(?P<bang>!)?: "
    r"(?P<subject>.+)$"
)

MAX_HEADER = 72
MAX_SUBJECT = 65


@dataclass
class LintResult:
    ok: bool
    errors: list[str]
    warnings: list[str]
    parsed: dict | None
    types: dict[str, str] | None = None

    @property
    def type(self) -> str | None:
        return self.parsed["type"] if self.parsed else None


def load_types(config_path: str | None = None) -> dict[str, str]:
    """Load type registry, merging extra types from a config file if present."""
    types = dict(TYPES)
    path = config_path or os.environ.get("COMMIT_LINT_CONFIG")
    if path and os.path.isfile(path):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            extra = data.get("types", {})
            if isinstance(extra, dict):
                for t, desc in extra.items():
                    if re.fullmatch(r"[a-z][a-z-]{0,20}", str(t)):
                        types[str(t)] = str(desc)
        except (json.JSONDecodeError, OSError):
            pass
    return types


def lint(message: str, types: dict[str, str] | None = None) -> LintResult:
    errors: list[str] = []
    warnings: list[str] = []
    types = types or TYPES

    if not message.strip():
        return LintResult(False, ["message is empty"], [], None, types)

    lines = message.rstrip("\n").split("\n")
    header = lines[0]

    if header.startswith("Merge "):
        return LintResult(True, [], [], {"type": "merge", "subject": header}, types)

    if len(header) > MAX_HEADER:
        errors.append(f"header must be <= {MAX_HEADER} chars (got {len(header)})")

    if header != header.rstrip():
        errors.append("header has trailing whitespace")

    m = HEADER_RE.match(header)
    if not m:
        errors.append(
            'format must be "type[(scope)]: subject" or "type(scope)!: subject" — '
            f'e.g. "feat(auth): add login"'
        )
        return LintResult(False, errors, warnings, None, types)

    parsed = m.groupdict()
    ctype = parsed["type"]

    if ctype not in types:
        errors.append(
            f"unknown type '{ctype}' — allowed: {', '.join(sorted(types))}"
        )

    subject = parsed["subject"]
    if len(subject) > MAX_SUBJECT:
        errors.append(f"subject too long (max {MAX_SUBJECT} chars, got {len(subject)})")
    if subject and subject[0].isupper():
        warnings.append("subject should not start with a capital letter")
    if subject.endswith((".", "!", "?")):
        errors.append("subject must not end with punctuation")
    if any(ch in subject for ch in "<>") :
        warnings.append("subject contains unusual characters (< >)")

    if parsed["bang"] and ctype not in TYPES:
        warnings.append("breaking change marker (!) on an unknown type is unusual")

    body = lines[1:]
    if body and body[0] != "":
        warnings.append("second line should be blank (body separation)")
    for i, line in enumerate(body):
        if len(line) > 100:
            warnings.append(f"body line {i + 2} exceeds 100 chars (got {len(line)})")

    return LintResult(not errors, errors, warnings, parsed, types)


def format_report(result: LintResult, message: str) -> str:
    icon = "✅" if result.ok else "❌"
    out = [f"{icon} commit message {icon == '✅' and 'valid' or 'invalid'}"]
    for e in result.errors:
        out.append(f"  error:   {e}")
    for w in result.warnings:
        out.append(f"  warning: {w}")
    if result.parsed and result.parsed.get("type") not in (None, "merge"):
        desc = (result.types or TYPES).get(result.parsed["type"], "")
        scope = result.parsed.get("scope")
        out.append(f"  type:    {result.parsed['type']} ({desc})")
        if scope:
            out.append(f"  scope:   {scope}")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    strict = False
    files: list[str] = []

    for a in args:
        if a == "--strict":
            strict = True
        elif a == "--help" or a == "-h":
            print(__doc__)
            print("\nUsage: commit-lint [--strict] <file-or-message> [...]\n")
            return 0
        else:
            files.append(a)

    if not files:
        print("error: provide a message or a file containing the message", file=sys.stderr)
        return 2

    types = load_types(next((f for f in files if f.endswith(".json") and os.path.isfile(f)), None))

    messages: list[str] = []
    for f in files:
        if f.endswith(".json") and os.path.isfile(f):
            continue
        try:
            with open(f, encoding="utf-8") as fh:
                messages.append(fh.read())
        except OSError:
            messages.append(f)

    if not messages:
        print("error: no messages to lint", file=sys.stderr)
        return 2

    failures = 0
    for msg in messages:
        result = lint(msg, types)
        if strict and result.warnings:
            result.ok = False
            result.errors.extend(result.warnings)
        print(format_report(result, msg))
        if not result.ok:
            failures += 1

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
