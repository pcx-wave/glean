---
analyzed_by: fable
analyzed_at: 2026-06-10
session_hash: dd0e343b
---

# device-first-check

**What went wrong:** Asked user for facts the filesystem already held,
declared service "not deployed" without testing, committed file
corruption without tail check.

**Rule:**
1. Search filesystem (`find`, `grep`, `ls`) before asking the user.
2. `curl -sI` before declaring anything "not deployed."
3. Syntax check + tail check before committing.

**Check:** `grep -c "AskUserQuestion\|curl.*not.find\|edit.*then.*ask"` in session transcript — near zero with this rule.
