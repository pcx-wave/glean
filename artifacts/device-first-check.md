---
analyzed_by: fable
analyzed_at: 2026-06-10
session_hash: dd0e343b
---

# device-first-check

**What went wrong:** The model asked the user for facts that were
available on the filesystem (READMEs, config files, directory listings),
declared a service "not deployed" without testing the URL, and committed
visible file corruption because it never checked the tail of the edited
file.

**Rule:** Before asking the user for information, search the filesystem
first (`find`, `grep`, `ls`). Before declaring something "not deployed,"
test the URL with `curl -sI`. Before committing, check the edited file's
structural integrity (syntax check, tail check for stray characters).

**Check:** `grep -c "AskUserQuestion\|curl.*not.find\|edit.*then.*ask"`
in session transcript — these patterns should be near zero after this
rule is applied.
