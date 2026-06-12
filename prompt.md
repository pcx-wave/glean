You are analyzing a Claude Code session transcript flagged for friction.

Your job: produce a structured rule that prevents this failure from repeating.

## Writing rules

Three sections only. Strict limits.

**What went wrong:** One sentence. The minimum context needed to understand
why the rule exists. No project names, no code, no file paths.

**Rule:** ≤5 lines. Actionable, ordered steps. Start each line with a verb
("Read", "Check", "Verify"). No explanations, no justifications.

**Check:** One grep/bash command the daily model can run to verify the rule
was followed. Must return zero under success.

## Format

```markdown
---
analyzed_by: <model>
analyzed_at: <date>
session_hash: <first 7 chars of session id sha256>
---

# <name>

**What went wrong:** <1 sentence>

**Rule:**
1. <action>
2. <action>
3. <action>

**Check:** <one command>
```

## Guidelines

- If no reproducible pattern → say "No generalizable pattern — skip."
- If multiple friction points → produce ONE rule for the dominant failure.
- Never include code, file paths, credentials, project names, or URLs.
