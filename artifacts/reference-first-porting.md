---
analyzed_by: fable
analyzed_at: 2026-06-10
session_hash: b8d83e5
---

# reference-first-porting

**What went wrong:** Ported math from memory instead of reading the
reference first. Result: 15 edit loops, session limit hit.

**Rule:**
1. Read the reference before editing any formula or algorithm.
2. Cite `file:line` per edit.
3. Apply supplied values verbatim before re-derivation.

**Check:** `grep -rn "TODO\|FIXME\|guess\|maybe" <target-file>` — zero after a port.
