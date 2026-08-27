# C3. `platform diff`

**Goal:** ship `platform diff [--instance NAME]` — run the same
generate pipeline into a throwaway location and print a unified diff
against the committed `rendered/` tree, without touching any committed
file.

**Depends on:**

- **[Epic D](../epics/epic-d-synthesizer.md) (CDK8s synthesizer) — not
  built yet**, same blocker as [C2](c2-generate-command.md). `diff`
  reuses whatever load → synth function C2 lands, so it can't be
  exercised end-to-end until Epic D exists either.
- **[C2](c2-generate-command.md), structurally.** `diff` should call the
  same internal "load, synth, write manifests" function `generate` uses
  — pointed at a temporary directory instead of `rendered/<instance>/` —
  rather than a second, copy-pasted implementation of the same pipeline.
  Flag it in review if C3 lands as a duplicate of C2's body instead of a
  thin wrapper around a shared function.
- ADR-0005 missing — see [C1](c1-validate-command.md#-adr-0005-is-missing)
  for the general flag; this story's own judgment calls are below.

## ⚠️ ADR-0005 is missing

Same gap as C1/C2. Judgment calls specific to `diff`:

1. **`--instance` semantics** — identical judgment call to C2's: filtered
   in the CLI, not the loader; optional, defaulting to "every retailer."
2. **Exit code convention.** Neither FR3 nor the PRD says what `diff`
   should return. This story adopts the familiar Unix `diff` /
   `git diff --exit-code` convention: exit `0` when there's no
   difference, `1` when there is one — useful for scripting
   (`platform diff || echo "drift detected"`). That's this story's
   choice, not a documented requirement.
3. **Where the throwaway output goes.** Python's stdlib `tempfile`
   module (a `tempfile.TemporaryDirectory()`, cleaned up automatically)
   is the obvious, simplest choice. Flagging this only because nothing
   spells out that the comparison has to go through real files on disk
   rather than, say, comparing in-memory strings directly — worth
   revisiting once Epic D's actual synth return type is known, since an
   in-memory comparison could turn out to be simpler still.

## Acceptance criteria

- `platform diff --instance acme` generates `acme`'s manifests to a
  temporary location, then compares them file-by-file against the
  committed `rendered/acme/`, printing a unified diff (via stdlib
  `difflib.unified_diff`) for any file that differs.
- No file under the committed `rendered/` is created, modified, or
  deleted by running `diff` — it's read-only against the committed tree.
- When there's no difference, `platform diff` prints nothing (or a short
  "no changes" line) and exits `0`.
- When `rendered/<instance>/` doesn't exist yet (an instance that has
  never been generated), the freshly-generated output is reported as
  entirely new/added — this needs no special-cased error handling, since
  comparing against an empty tree is just the normal behavior of a diff.
- `platform diff` with no `--instance` runs the same comparison for
  every retailer in the registry.

## 📚 Read before starting this story

- [Python `difflib`](https://docs.python.org/3/library/difflib.html) — `unified_diff`, the function this command centers on.
- [`tempfile`](https://docs.python.org/3/library/tempfile.html) — `TemporaryDirectory`, for the throwaway generate target.
- PRD's non-functional "Determinism" requirement — the reason `diff` is meaningful at all; re-read it before assuming synth output is stable.
