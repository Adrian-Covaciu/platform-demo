# C4. `platform impact <path>` (stretch)

**Goal:** given the path to one changed registry YAML file, report which
retailers' rendered output would be affected, by reusing `diff`'s
machinery rather than building a new dependency graph. This is
explicitly a stretch story — per PRD FR3, it "may ship as a stub or slip
entirely without blocking the rest of v1." Keep it that small; resist
growing its scope past what's below.

**Depends on:**

- **[C3](c3-diff-command.md) (`platform diff`)** — this command is a thin
  wrapper: resolve `<path>` to the affected retailer(s), then run C3's
  diff logic for each one.
- **[Epic D](../epics/epic-d-synthesizer.md)** — same blocker as C2/C3,
  one level further removed; nothing here can run end-to-end before the
  synthesizer exists.
- ADR-0005 missing — see [C1](c1-validate-command.md#-adr-0005-is-missing);
  judgment calls specific to this story below.

## ⚠️ ADR-0005 is missing

Same gap as C1–C3. Judgment calls specific to `impact`:

1. **What "impact" means, precisely.** Registry files can be shared: a
   `registry/services/<name>/...` file can be referenced by more than
   one retailer (per CLAUDE.md's domain model — a service catalog entry
   is reusable). This story defines impact at **retailer granularity**,
   not manifest-file granularity: it reports *which retailers* are
   affected, then shows each one's full diff via C3 — it does not try to
   pinpoint the exact rendered file or line the changed component would
   touch. A finer-grained mapping is a bigger feature than a stretch CLI
   command justifies; flag it for a future iteration if that precision
   turns out to matter.
2. **Argument shape.** FR3 gives `platform impact <path>` — a single
   positional path, no flags. This story takes that literally rather
   than adding an `--instance` override, since the entire point of the
   command is to *derive* the instance(s) from the given path.

## Acceptance criteria

- `platform impact registry/retailers/acme/retailer.yaml` resolves the
  path to retailer `acme` and reports the result of
  `platform diff --instance acme` for it (reusing C3 directly, not a
  reimplementation of it).
- `platform impact registry/services/web/service.yaml` resolves to every
  retailer that lists `web` under its `services:` — today, just `acme` —
  and reports that retailer's diff.
  `registry/retailers/paris-lvh/`, which has no `services:` key, is
  correctly reported as unaffected by any change under
  `registry/services/`.
- A path outside `registry/`, or one that doesn't map to any known
  retailer or catalog service, reports "no impact" rather than raising —
  that's a valid state (e.g. a genuinely unrelated file), not a data
  error, so it doesn't get the fail-hard treatment loader errors get.
- Shipping this command as a stub (e.g. a "not yet implemented" message
  with a documented, chosen exit code) is an acceptable outcome for this
  story if it slips past the rest of v1 — per PRD FR3, that's expected,
  not a failure.

## 📚 Read before starting this story

- PRD FR3's `impact` line, and the "Out of scope" section's note on
  "Incremental/impact-aware regeneration" — both clarify how small this
  command is meant to stay.
- [`pathlib`](https://docs.python.org/3/library/pathlib.html) — for
  resolving `<path>` against `registry/retailers/` vs
  `registry/services/`.
- [C3](c3-diff-command.md) — read this story fully before starting C4;
  `impact` has almost no logic of its own beyond routing into it.
