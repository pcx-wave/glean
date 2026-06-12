# glean

Extract rules from failing Claude Code sessions using a stronger model.

```
collect.py → stronger model → artifacts/*.md → copy into CLAUDE.md
(scans logs) (analyzes)       (rule)          (at session start)
```

## How it works

1. **Collect** — `python3 collector/collect.py` scans your Claude Code logs
   and prints them sorted by friction density (errors + edits + corrections
   per 1000 lines, with corrections weighted 5×).
2. **Analyze** — Send a session + `prompt.md` to a stronger model (Fable,
   Opus). It returns a structured rule.
3. **Load** — Copy the rule into `~/.claude/CLAUDE.md`. Your daily model
   reads it at session start.
4. **Contribute** — Open a PR to `artifacts/` with your anonymized rule.

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

# 3. Add frontmatter, remove project names / code / credentials
vim artifacts/my-rule.md

# 4. Copy the rule into CLAUDE.md so your daily model reads it
echo '
## glean rules
- **my-new-rule:** <what the rule says, 1 line>
' >> ~/.claude/CLAUDE.md
```

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
├── collector/collect.py   ← friction scanner (Python stdlib)
├── prompt.md              ← analysis protocol for the stronger model
├── artifacts/             ← extracted rules (community-contributable)
└── CONTRIBUTING.md        ← how to submit a rule
```

## License

MIT
