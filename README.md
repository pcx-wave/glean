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
4. **Load** — Install the gleanin skill, then add a one-line `@`-import to
   `~/.claude/CLAUDE.md`. Claude Code loads imported files into context every
   session, so every rule in `artifacts/` is applied automatically — without
   pasting the rules themselves into `CLAUDE.md`.

## Protocol index (two-tier loading)

Not every distilled lesson fits the compact rule format. Longer, multi-rule
protocols (with triggers and falsifiable success criteria) would blow the
token budget if inlined into every session. `sync.sh` handles them with a
second tier:

- **Tier 1 — inlined rules**: every `artifacts/*.md` (compact
  What/Rule/Check format) is rendered in full into `gleanin/SKILL.md`.
  Always in context.
- **Tier 2 — protocol index**: every `*.md` found in `GLEAN_PROTOCOL_DIRS`
  (colon-separated, default `~/distillation/artifacts:~/fable-build/rules`)
  gets ONE line in `gleanin/SKILL.md`: display name, trigger sentence, and
  file path. The model reads the full protocol only when the trigger matches
  the task at hand — the filesystem replaces context.

Files whose name collides with an `artifacts/` rule are skipped (the inlined
compact rule wins). Directories that don't exist are skipped silently, so
the default works out of the box even if you don't have those pipelines.

Point `GLEAN_PROTOCOL_DIRS` at your own protocol collections:

```bash
GLEAN_PROTOCOL_DIRS="$HOME/my-protocols:$HOME/team-playbooks" bash gleanin/sync.sh
```

## Installation

One-liner — clones glean, installs the gleanin skill, and wires it into
`CLAUDE.md` so its rules load every session:

```bash
git clone https://github.com/pcx-wave/glean.git ~/glean && mkdir -p ~/.claude/skills && ln -sf ~/glean/gleanin ~/.claude/skills/gleanin && grep -qxF '@~/.claude/skills/gleanin/SKILL.md' ~/.claude/CLAUDE.md 2>/dev/null || echo '@~/.claude/skills/gleanin/SKILL.md' >> ~/.claude/CLAUDE.md
```

That's it for setup. `glean` itself (the collection pipeline) isn't a
service — it's the scripts in `~/glean/collector/`, run on demand (see
Quick start below).

**Prerequisites:**
- Python 3.x (stdlib only)
- Claude Code session logs at `~/.claude/projects/`
- Access to a stronger model for analysis (Fable, Opus, ...)

## Quick start

```bash
cd ~/glean

# 1. List sessions sorted by friction density
# (defaults to your "sonnet" sessions — the cheaper model you're improving;
#  pass --model-filter '' to see all models)
python3 collector/collect.py

# 2. Analyze a session with a stronger model
cat /path/to/session.jsonl | claude -p "$(cat prompt.md)" --model fable > artifacts/my-rule.md

# 3. Add frontmatter, anonymize, review
python3 collector/anonymize.py artifacts/my-rule.md
vim artifacts/my-rule.md

# 4. Rebuild gleanin/SKILL.md from artifacts/ (installed via the one-liner above)
bash gleanin/sync.sh
```

The `@`-import added during installation loads `gleanin/SKILL.md`'s content
(including the generated rules) into every session automatically. Only that
one line lives in `CLAUDE.md` — the rules themselves stay in `artifacts/`
and `gleanin/SKILL.md`.

## Measuring impact

Rules are only worth their context-token cost if they move the friction
metric. `collector/metrics.py` closes that loop:

```bash
python3 collector/metrics.py --days 7            # aggregate + append CSV
python3 collector/metrics.py --days 7 --dry-run  # table only
```

It aggregates friction density per model family (fable/opus/sonnet/haiku/
other) over a sliding window and appends one row per family per day to
`metrics/friction.csv` (idempotent — reruns the same day are skipped, so a
weekly cron is safe). Compare rows before and after loading a new rule: if
mean/median density does not drop for the model the rule targets, drop the
rule.

Caveats: families with few sessions or tiny line counts produce noisy
densities (corrections are weighted 5x, so one correction in a small session
dominates) — read `sessions` and `total_lines` before trusting a density.
Delegated runs (Mistral Vibe, Gemini, ...) do not appear in these logs;
they are measured separately by their own delegate run log.

`metrics/` is gitignored — it is personal measurement data.

## Concrete results

4 rules extracted from one person's Sonnet sessions. Your friction
patterns will be different — use the pipeline to find yours.

### Friction categories observed

| Category | Example rule | Root cause |
|----------|-------------|------------|
| **Weak planning** | `reference-first-porting` | Model jumps to code instead of reading the reference first |
| **False confidence** | `delegation-preflight` | Orchestrator trusts delegate's "OK" signal without verifying |
| **Lazy diagnostics** | `device-first-check` | Asks user for facts the filesystem already holds |
| **Scope confusion** | `credentialed-write-gate` | Writes infra with ambient creds to wrong environment |

### Rule catalog

| Rule | What it prevents |
|------|-----------------|
| `reference-first-porting` | Porting math from memory instead of reading the reference |
| `delegation-preflight` | Delegating payload that the sub-agent silently drops |
| `device-first-check` | Asking the user for facts the filesystem holds |
| `credentialed-write-gate` | Writing infra to wrong scope without rollback |

## Contributing

**Experimental.** These artifacts reflect one setup. Your mileage will
vary — the pipeline is the point, not the rule set.

If you extract a rule that feels broadly useful, open a PR to
`artifacts/`. Run `collector/anonymize.py` first. See `CONTRIBUTING.md`.

## Project structure

```
glean/
├── README.md
├── collector/
│   ├── collect.py       ← friction scanner (Python stdlib)
│   └── anonymize.py     ← strips sensitive info from artifacts
├── prompt.md            ← analysis protocol for the stronger model
├── artifacts/           ← extracted rules (personal observations)
├── gleanin/             ← Claude Code skill that loads rules
│   ├── SKILL.md         ← injected at session start
│   └── sync.sh          ← rebuilds SKILL.md from artifacts/
├── CONTRIBUTING.md      ← how to submit a rule
└── LICENSE
```

## License

MIT
