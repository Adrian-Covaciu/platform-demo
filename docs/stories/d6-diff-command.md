# D6. `platform diff`

**Goal:** ship `platform diff [--instance NAME]` — generate into a
temporary directory (never touching the committed `rendered/`), then
print a unified diff (the `---`/`+++`/`@@`-hunk format `git diff` and
`diff -u` both use) between each generated file and its committed
counterpart. This is the story where Python's `difflib` and basic
temp-directory hygiene meet the UX question every dry-run command has to
answer: what does it mean to show someone a change without making it?

**Depends on:**

- [D5](d5-generate-command.md) — `platform diff` reuses the *exact same*
  `generate_retailer` call `platform generate` uses, just pointed at a
  temp directory instead of `rendered/<instance>/`. Don't write a second
  "diff mode" synth path — two implementations of the same thing drifting
  apart over time is a much harder bug to notice than it sounds.
- [D4](d4-rendered-schema-version.md) — the determinism guarantee this
  command's entire premise rests on: if `generate_retailer` weren't
  byte-identical on repeated runs with no registry changes, `platform
  diff` would show spurious noise every single time, even against an
  unmodified registry, and would be useless.
- ADR-0005 missing, same general flag as [C1](c1-validate-command.md#-adr-0005-is-missing).
  The judgment call below is specific to this command.

## Judgment call: exit codes don't distinguish "found a diff" from "broke"

Click's `ClickException` (already used by `validate` and `generate` for
real errors) exits non-zero — typically `1`. The Unix `diff` convention
this command's name borrows from uses `0` = no differences, `1` =
differences found, `2` = error, specifically so scripts can tell those
two outcomes apart programmatically. This command doesn't bother
replicating that three-way split: it exits `0` when there's no
difference and non-zero (reusing whatever Click already does, including
for genuine loader/synth errors) otherwise. There's no CI pipeline in
this repo yet that would need to distinguish "the registry changed" from
"something broke" by exit code alone — a human running this locally can
already tell the two apart by reading the output (a diff body vs. an
`Error: ...` line). If that distinction ever becomes load-bearing, it's
a two-line change to pick separate exit codes, not a redesign — not worth
building against a need that doesn't exist yet.

## The concept: `difflib` has several diff functions, and only one gives you this format

```python
import difflib

before = "replicas: 1\n".splitlines(keepends=True)
after = "replicas: 3\n".splitlines(keepends=True)

diff = difflib.unified_diff(before, after, fromfile="committed", tofile="generated")
print("".join(diff))
```

`difflib.unified_diff` is what actually produces the familiar
`---`/`+++`/`@@` hunk format. It's easy to reach for the wrong tool here:
`difflib.Differ`/`ndiff` produce a different, more verbose line-by-line
marked format (`+ `/`- `/`? ` prefixes, no `@@` hunks), and
`difflib.context_diff` produces yet another format (`***`/`---` markers).
None of the three are wrong, exactly — they're just not the format this
story's acceptance criteria describe, and a learner who's only skimmed
the module docs will often grab `ndiff` because its name sounds more
obviously like "the diff one."

The other easy mistake: `unified_diff` takes **sequences of lines**, not
one big multi-line string. Read a file with `.read_text()` and hand the
whole string straight to `unified_diff` and you'll get a diff of
individual *characters*, which is technically correct and completely
useless. Call `.splitlines(keepends=True)` on each file's contents
first (`keepends=True` matters — without it, `unified_diff`'s output
loses the newlines between lines and everything runs together when
printed).

## Trap: a service that doesn't exist yet on one side

If the registry has gained a service since `rendered/` was last
committed, the generated temp directory will have a file with no
committed counterpart to compare against (or vice versa, if a service
was removed from a retailer). Don't write special-case "this file is
new" / "this file was deleted" messaging — treat a missing file as an
empty string for diffing purposes. `unified_diff` against an empty
"before" already renders the whole file as added lines (`+` on every
line), which is exactly what a new file's diff should look like, for
free.

## Trap: temp directory cleanup

Use `tempfile.TemporaryDirectory()` as a context manager
(`with tempfile.TemporaryDirectory() as tmp:`), not
`tempfile.mkdtemp()` called on its own — the context manager form
deletes the directory automatically when the `with` block exits, even if
`generate_retailer` raises partway through. `mkdtemp()` on its own leaves
the directory behind unless you remember to clean it up yourself in a
`finally`, and it's easy to forget that on the error path specifically —
exactly the path most likely to be exercised by accident during
development.

## Acceptance criteria

- With the registry and the committed `rendered/` in sync (i.e. right
  after a `platform generate` whose output was committed), `platform
  diff` prints no differences and exits `0`.
- Temporarily editing a real registry file without regenerating or
  committing — e.g. bumping `registry/services/web/http/component.yaml`'s
  `replicas` — and running `platform diff --instance acme` prints a
  unified diff showing exactly the `replicas:` line changing inside the
  generated `web.yaml` content, with `fromfile`/`tofile` labels that make
  clear which side is "committed" and which is "what generate would
  produce now."
- After running `platform diff`, every file under the committed
  `rendered/acme/` is byte-identical to what it was before the command
  ran — this command never writes to the committed directory, only to
  its temp directory. Verify this directly (e.g. compare file mtimes or
  contents before/after), not just by absence of an error.
- No temp directory created by `platform diff` still exists on disk
  after the command exits, including when the diffed component was
  edited (the success path) and when the registry has an unrelated
  loader error (the failure path) — both must clean up.
- `--instance` behaves the same way it does for `generate` (D5): omit it
  to diff every retailer, name one to diff only that one, name a
  nonexistent one to fail with a clear message.

## 📚 Read before starting this story

- [Python `difflib`](https://docs.python.org/3/library/difflib.html) — read the whole module page once before writing anything; specifically compare `unified_diff`'s signature and example output against `context_diff` and `Differ`/`ndiff` so the choice is deliberate, not the first function that appeared in a search result.
- [Python `tempfile`](https://docs.python.org/3/library/tempfile.html) — `TemporaryDirectory` as a context manager, and why it's preferred over `mkdtemp()` for anything short-lived.
- [D4](d4-rendered-schema-version.md) and [D5](d5-generate-command.md) — this story adds no new synth logic; it should be nearly all diffing and temp-directory plumbing wrapped around a call this codebase already has.
