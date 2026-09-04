<div align="center">

# ✅ commit-lint

**Enforce conventional commits — validate messages, keep history clean.**

[![CI](https://github.com/v01dst/commit-lint/actions/workflows/ci.yml/badge.svg)](https://github.com/v01dst/commit-lint/actions/workflows/ci.yml)
![License](https://img.shields.io/badge/license-MIT-8A2BE2)
![Python](https://img.shields.io/badge/python-3.14-3776AB?logo=python&logoColor=white)
![Deps](https://img.shields.io/badge/dependencies-stdlib%20only-00c853)
![Tests](https://img.shields.io/badge/tests-15%20passing-brightgreen)

`feat` · `fix` · `chore` · `11 types` · `scopes` · `breaking changes`

</div>

---

## ✨ Features

- **📋 Full conventional spec** — `type(scope)!: subject`, 11 standard types
- **📏 Header limit** — 72-char headers, 65-char subjects enforced
- **⚠️ Warnings vs errors** — capital subjects warn; punctuation errors
- **🧵 Body rules** — blank-line separation, 100-char body lines
- **🔀 Merge-aware** — merge commits pass untouched
- **🪶 Pure stdlib** — zero deps, any Python ≥ 3.10

## 🚀 Quick Start

```bash
git clone https://github.com/v01dst/commit-lint
cd commit-lint
python3 -m commit_lint "feat(auth): add password reset"
```

### Use as a git hook

```bash
# .git/hooks/commit-msg
#!/bin/sh
python3 /path/to/commit-lint/commit_lint "$1"
```

Or in CI:

```bash
git log --format=%s origin/main..HEAD | while read -r msg; do
  echo "$msg" | python3 -m commit_lint --strict - || exit 1
done
```

## 📖 Usage

```
commit-lint [--strict] <file-or-message> [...]

  --strict   treat warnings as errors
```

### Examples

```bash
$ python3 -m commit_lint "feat(auth): add password reset"
✅ commit message valid
  type:    feat (new feature)
  scope:   auth

$ python3 -m commit_lint "did some stuff!!"
❌ commit message invalid
  error:   format must be "type[(scope)]: subject" — e.g. "feat(auth): add login"
```

| Exit code | Meaning                          |
|-----------|----------------------------------|
| `0`       | All messages valid               |
| `1`       | One or more invalid              |
| `2`       | Usage error                      |

## 🧱 Tech Stack

| Layer     | Tech                        |
|-----------|-----------------------------|
| Runtime   | Python ≥ 3.10 (stdlib only) |
| Testing   | unittest                    |
| Packaging | Docker                      |
| CI        | GitHub Actions              |

---

<div align="center">

Built with ⚡ by **v01dst**

[![GitHub](https://img.shields.io/badge/github-v01dst-181717?logo=github)](https://github.com/v01dst)
[![Discord](https://img.shields.io/badge/discord-9p.1-5865F2?logo=discord&logoColor=white)](https://discord.com/users/9p.1)

*Project 015 / 99 — The Loop*

</div>
