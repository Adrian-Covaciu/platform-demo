# C2. `platform generate`

**Goal:** ship `platform generate [--instance NAME]` — run the full
load → synth → write pipeline, producing `rendered/<instance>/*.yaml`.

**Depends on:**

- [Epic B](../epics/epic-b-loader-merge.md) — the loader this command
  calls into already exists.
- **[Epic D](../epics/epic-d-synthesizer.md) (CDK8s synthesizer) — not
  built yet.** `src/platform_generator/generator.py` is currently a
  0-line empty file; there is no synth function for this command to
  call. This story can define the CLI's contract (flags, exit behavior,
  where files land) but cannot actually be implemented or tested
  end-to-end until D1–D4 exist. Pick one explicitly before starting: (a)
  sequence this story after Epic D, even though
  `docs/epics/README.md`'s build-order table lists C before D, or (b)
  land the CLI command now against a stub synth function with the
  intended signature, to be filled in once D lands. Don't quietly start
  coding as if the synthesizer already exists.
- ADR-0005 missing — see [C1](c1-validate-command.md#-adr-0005-is-missing)
  for the general flag; the judgment calls specific to this story are
  below.

## ⚠️ ADR-0005 is missing

Same underlying gap as C1: `docs/adr/0005-click-cli-structure.md` doesn't
exist. Two additional judgment calls this story had to make in its
absence:

1. **How `--instance` resolves to a retailer.** CLAUDE.md defines a
   "platform-instance" as a `Retailer` (`--instance NAME` maps to
   `rendered/<instance>/`), so `--instance NAME` is read here as "the
   retailer whose `name` field equals `NAME`." But
   `loader.load_retailers()` has no parameter to select a single
   retailer — it always loads every retailer under
   `registry/retailers/`. Nothing settles whether filtering to one
   instance belongs in the loader (e.g. `load_retailers(instance=...)`)
   or in the CLI (load everything, then pick one out of the list). This
   story does the filtering in the CLI — the smaller change, and it
   leaves the loader's existing all-or-nothing signature untouched — but
   that's a choice, not a settled design.
2. **Whether `--instance` is required.** FR3 shows it as
   `[--instance NAME]` — optional. This story treats omitting it as
   "generate every retailer currently in the registry, one
   `rendered/<name>/` per retailer" rather than requiring a single
   instance or picking an arbitrary default — the simplest reading of
   "optional" that doesn't need a hidden default value.

## Acceptance criteria

- `platform generate --instance acme` loads and validates the *entire*
  registry the same way `validate` does — a loader error anywhere in the
  registry (not just in `acme`'s own files) still stops `generate`, per
  the fail-hard rule — then synthesizes only the `acme` retailer and
  writes its manifests to `rendered/acme/`.
- `platform generate` with no `--instance` does the same for every
  retailer under `registry/retailers/` (today: `acme`, `paris-lvh`).
- `--instance` naming a retailer that doesn't exist in the registry fails
  with a clear message and non-zero exit — no silent no-op.
- Running `platform generate` twice in a row with no registry changes
  produces byte-identical files under `rendered/` — FR4's determinism
  requirement, and the property `platform diff` (C3) depends on to
  produce a meaningful diff instead of noise.
- Every file written under `rendered/<instance>/` carries whatever
  `rendered_schema_version` stamp Epic D's D4 story produces. This
  command doesn't invent its own versioning — it just writes what the
  synthesizer returns.

## 📚 Read before starting this story

- PRD FR3 (this command's spec), FR4 (determinism requirement), FR5 (the
  `rendered_schema_version` stamp).
- [Epic D](../epics/epic-d-synthesizer.md)'s reading list — even though
  this story doesn't write the synthesizer, understanding what it
  returns is necessary to wire the CLI call correctly.
- [Click — Options](https://click.palletsprojects.com/en/stable/options/) — for `--instance`.
