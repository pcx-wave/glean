Analyze a Claude Code session transcript flagged for friction.
Produce one structured rule that prevents this failure from repeating.

## Format

**What went wrong:** 1 sentence. Minimum context. No names, code, paths.

**Rule:** ≤5 lines. Verb-first ("Read", "Check", "Verify"). No explanations.

**Check:** One grep/bash/node command. Zero = success.

## Rules

- No generalizable pattern → "No generalizable pattern — skip."
- Multiple friction points → one rule for the dominant failure.
- Never leak code, file paths, credentials, project names, or URLs.
