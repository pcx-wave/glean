---
analyzed_by: fable
analyzed_at: 2026-06-10
session_hash: b217279a
---

# delegation-preflight

**What went wrong:** A delegation prompt contained special characters
that the delegate's edit mechanism silently dropped. The delegate
reported `[OK]` for each change, but 7 of 9 modifications never landed.
The orchestrator patched symptoms instead of diagnosing the root cause.

**Rule:**
1. Before composing a delegation prompt, scan the payload against the
   delegate's documented Known Limitations (character encoding, file size,
   tool restrictions).
2. Delegate logs are progress, not verification. Verify with `git diff`
   or a parser, not the delegate's `[OK]` lines.
3. On partial landing (changes missing), diagnose and name the documented
   limitation before any hand edit.
4. Run a structural integrity check on every delegate-touched file.

**Check:** `git diff --stat HEAD` after delegation — the changed file
count should match the expected count. If it doesn't, the delegate
silently dropped something.
