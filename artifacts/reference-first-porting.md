---
analyzed_by: fable
analyzed_at: 2026-06-10
session_hash: b8d83e5
---

# reference-first-porting

**What went wrong:** When porting code from a reference implementation,
the model derived the math from memory and conversation instead of reading
the reference file first. Result: 15 edits to guess the correct formula,
multiple user corrections, and a session limit hit.

**Rule:** Before editing any formula, algorithm, or data transformation,
read the reference implementation (paper, legacy code, pasted table)
first. Cite file:line per edit. Apply user-supplied values verbatim
before any re-derivation.

**Check:** `grep -rn "TODO\|FIXME\|guess\|maybe" <target-file>` — these
markers should appear zero times after a port. If they appear, the model
didn't anchor on the reference.
