---
analyzed_by: fable
analyzed_at: 2026-06-10
session_hash: 724c8181
---

# credentialed-write-gate

**What went wrong:** Wrote infra resource to wrong scope with ambient
credentials, marked task done, left orphan for user to clean up.

**Rule:**
1. Before writing with ambient credentials, verify scope (`<tool> whoami`, `config view`).
2. Exact-match created resource name against intent.
3. On mismatch, roll back immediately.
4. Never mark done when acceptance probe failed.

**Check:** `grep -c "inoffensif\|harmless\|can delete\|not needed"` in session transcript — zero for any failed write.
