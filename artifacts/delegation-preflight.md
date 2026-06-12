---
analyzed_by: fable
analyzed_at: 2026-06-10
session_hash: b217279a
---

# delegation-preflight

**What went wrong:** Delegate silently dropped 7/9 modifications
because of documented limitations. Orchestrator patched symptoms
instead of diagnosing root cause.

**Rule:**
1. Scan delegation payload against delegate's Known Limitations first.
2. Verify with `git diff`, not the delegate's `[OK]` lines.
3. On partial landing, name the limitation before hand-editing.
4. Structural integrity check every delegate-touched file.

**Check:** `git diff --stat HEAD` after delegation — changed file count must match expected.
