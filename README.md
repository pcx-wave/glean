# glean

Improve your cheaper Claude models with daily guards from stronger ones.

This repo has two tools:

- **glean** — collects failure/friction session data and analyzes them
  with a stronger model (Fable, Opus) to extract structured rules.
- **gleanin** — a Claude Code skill that loads those rules every session
  so future code benefits from past mistakes.

```
collect.py → stronger model → artifacts/*.md → gleanin (skill)
(scans logs) (analyzes)       (rule)          (loaded every session)
```

## How it works

1. **Collect** — `python3 collector/collect.py` scans your Claude Code logs
   and prints them sorted by friction density (errors + edits + corrections
   per 1000 lines, corrections weighted 5×).
2. **Analyze** — Send a session + `prompt.md` to a stronger model (Fable,
   Opus). It returns a structured rule.
3. **Store** — Save the rule in `artifacts/` with frontmatter (title, date,
   model, rating). Run `collector/anonymize.py` to strip sensitive info.
4. **Load** — Install the gleanin skill. It loads every rule in
   `artifacts/` at session start — no `CLAUDE.md` bloat.
5. **Contribute** — Run `collector/anonymize.py`, review, open a PR.

## Installation

```bash
git clone https://github.com/pcx-wave/glean.git
cd glean
```

**Prerequisites:**
- Python 3.x (stdlib only)
- Claude Code session logs at `~/.claude/projects/`
- Access to a stronger model for analysis (Fable, Opus, ...)

## Quick start

```bash
# 1. List sessions sorted by friction density
python3 collector/collect.py

# 2. Analyze a session with a stronger model
cat /path/to/session.jsonl | claude -p "$(cat prompt.md)" --model fable > artifacts/my-rule.md

# 3. Add frontmatter, anonymize, review
python3 collector/anonymize.py artifacts/my-rule.md
vim artifacts/my-rule.md

# 4. Install the gleanin skill to load rules at every session start
ln -s "$(pwd)/gleanin" ~/.claude/skills/gleanin
```

The symlink installs gleanin into Claude Code's skill directory.
Reference it in `CLAUDE.md` or set up auto-loading so it runs
every session. Rules stay out of `CLAUDE.md`.

## Concrete results

4 rules extracted from real sessions:

| Rule | What it prevents |
|------|-----------------|
| `reference-first-porting` | Porting math from memory instead of reading the reference |
| `delegation-preflight` | Delegating payload that the sub-agent silently drops |
| `device-first-check` | Asking the user for facts the filesystem holds |
| `credentialed-write-gate` | Writing infra to wrong scope without rollback |

## Project structure

```
glean/
├── README.md
├── collector/
│   ├── collect.py       ← friction scanner (Python stdlib)
│   └── anonymize.py     ← strips sensitive info from artifacts
├── prompt.md            ← analysis protocol for the stronger model
├── artifacts/           ← extracted rules (community-contributable)
├── gleanin/             ← Claude Code skill that loads rules
│   ├── SKILL.md         ← injected at session start
│   └── sync.sh          ← rebuilds SKILL.md from artifacts/
├── CONTRIBUTING.md      ← how to submit a rule
└── LICENSE
```

## License

MIT
