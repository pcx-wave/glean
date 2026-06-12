# Contributing a rule

Rules are submitted via **pull requests** to `artifacts/`.

## Flow

```
1. python3 collector/collect.py --since-days 7
2. Pick the most painful session
3. Send it to Fable (or your strongest model) using prompt.md
4. Copy the output → artifacts/<name>.md
5. Add analyzed_by + session_hash frontmatter
6. Remove any credentials, project names, code, URLs
7. Open a PR
8. Once merged: git pull && bash ~/.claude/skills/gleanin/sync.sh
```

## Artifact format

```markdown
---
analyzed_by: fable | opus | <model>
analyzed_at: 2026-06-12
session_hash: a3f8b2c
---

# artifact-name

**What went wrong:** <one sentence>

**Rule:** <≤10 lines, actionable>

**Check:** <one grep/bash/node command>
```

## Quality

- **General** — not "fix this bug" but "always read the reference"
- **Testable** — someone can grep-check if the rule is followed
- **Short** — ≤10 lines, fits in context
- **Single pattern** — one root cause, one intervention
