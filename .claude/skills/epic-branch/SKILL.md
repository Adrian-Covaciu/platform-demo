---
name: epic-branch
description: Detects which epic is currently in progress from docs/stories/, commits all pending changes, and pushes them to a remote branch named epic-<letter> (creating it if needed). Use when the user asks to push/sync the current epic's work to its own branch.
disable-model-invocation: true
---

# Epic Branch Push

Commits all pending work and pushes it to a remote branch named after the
epic currently in progress (`epic-<letter>`), matching the `epic-b` /
`pre-epic-b` branches already used in this repo's history.

## Steps

1. **Detect the current epic.**
   - List `docs/stories/*.md` and extract the leading letter from each
     filename (pattern `^([a-z])\d+-`, e.g. `c1-validate-command.md` → `c`).
   - All story files must share the same letter — in this repo,
     `docs/stories/` only ever holds one epic's stories at a time. If you
     find more than one distinct letter, or zero `.md` files, stop and ask
     the user which epic to use instead of guessing.
   - Confirm `docs/epics/epic-<letter>-*.md` exists for that letter. Read
     its `# ` heading — you'll use it in the commit message.

2. **Branch name** = `epic-<letter>` (e.g. `epic-c`).

3. **Check out the branch before committing anything**, creating it if it
   doesn't exist locally yet:
   ```
   git rev-parse --verify <branch> >/dev/null 2>&1 && git checkout <branch> || git checkout -b <branch>
   ```
   Work must land on the epic branch, not on whatever branch is currently
   checked out — mirrors how `pre-epic-b` and `epic-b` were built as
   separate branches merged into `master` via PR, rather than committed
   to `master` directly.

4. **Review what's about to be committed.** Run `git status --porcelain`.
   Stop and warn the user — do not commit or push — if anything looks
   like a credential/secret file (`.env`, `*.pem`, `credentials*.json`,
   `id_rsa*`, etc.) or an unexpectedly large binary.

5. **Stage and commit everything.** This skill's whole purpose is
   pushing all outstanding work for the epic, so use `git add -A` here
   (the usual "prefer specific files" guidance is waived for this one
   skill, by design):
   ```
   git add -A
   git commit -m "$(cat <<'EOF'
   Epic <LETTER-UPPER> — <epic title from its epic-*.md H1>: sync work in progress

   Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
   EOF
   )"
   ```
   If `git status --porcelain` was already empty, skip the commit — that's
   not an error, it just means there's nothing new to push.

6. **Push to origin:**
   ```
   git push -u origin <branch>
   ```
   If this fails as non-fast-forward (the remote branch has diverged),
   stop and surface the error to the user. Never force-push.

7. **Report back**: the branch name, whether it was created or reused,
   the commit hash (or "nothing to commit"), and confirmation the push
   succeeded.

## Notes

- No PR is opened — this skill only creates/updates the branch and
  pushes it. Opening the PR is a separate, deliberate step for the user.
- Safe to re-run later in the same epic: it just adds another commit and
  pushes again to the same branch.
