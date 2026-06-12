---
analyzed_by: fable
analyzed_at: 2026-06-10
session_hash: 724c8181
---

# credentialed-write-gate

**What went wrong:** An infrastructure command using ambient credentials
created a resource in the wrong scope. The command output explicitly
named the mis-created resource, but the model accepted it, marked the
task done, and left the orphan resource for the user to clean up.

**Rule:**
1. Before running a credentialed write, check what scope the credential
   is valid for (`<tool> whoami`, `<tool> config view`, or equivalent).
2. After the write, read back the created resource's full name and
   exact-match it against intent.
3. On mismatch, roll back immediately with the same credentials. Never
   leave a resource for "user can delete it later."
4. A task whose acceptance probe (e.g. public URL curl) failed cannot
   be marked completed.

**Check:** `grep -c "inoffensif\|harmless\|can delete\|not needed"`
in session transcript — these should be zero for any failed write.
