# Contributing a rule

**Experimental.** The existing artifacts come from one person's setup.
Your friction patterns will differ — the real value is running your own
pipeline.

If you extract a rule that feels broadly useful, submit it via **pull
request** to `artifacts/`.

## Flow

```
1. python3 collector/collect.py --since-days 7
2. Pick the most painful session
3. Send it to Fable (or your strongest model) using prompt.md
4. Copy output → artifacts/<name>.md
5. Add analyzed_by + session_hash frontmatter
6. python3 collector/anonymize.py artifacts/<name>.md
7. Review, remove anything the script missed
8. Open a PR
9. Once merged: git pull && bash gleanin/sync.sh
```

## Artifact format

```markdown
---
analyzed_by: fable | opus | <model>
analyzed_at: 2026-06-12
session_hash: a3f8b2c
---

# artifact-name

**What went wrong:** <1 sentence>

**Rule:** <≤5 lines, verb-first>

**Check:** <one grep/bash/node command>
```

## Quality

- **General** — not "fix this bug" but "always read the reference"
- **Testable** — someone can grep-check if the rule is followed
- **Short** — ≤10 lines, fits in context
- **Single pattern** — one root cause, one intervention
