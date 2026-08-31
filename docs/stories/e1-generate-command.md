# E1. `platform generate`

**Goal:** ship `platform generate [--instance NAME]` in `cli.py`, wired
to D5's `generate_retailer`. This is the story where a previously-empty
module (`generator.py`) and a previously-thin CLI (`cli.py`, one command
so far) actually meet — and where "tested end to end" stops being an
abstract phrase and starts meaning something concrete: real files landing
under `rendered/`, checked against the real registry, with no mocks.

**Depends on:**

- [D5](d5-rendered-schema-version.md) — `generate_retailer` is
  the only thing this command calls into; if you find yourself writing
  logic here that decides *how* a manifest is built, it belongs in
  `generator.py`, not `cli.py`.
- [C1](c1-validate-command.md) — the `platform` CLI group and its
  `[project.scripts]` entry point already exist; this story adds a
  second command to the same `cli` group, it doesn't scaffold a new one.
- ADR-0005 missing — see [C1](c1-validate-command.md#-adr-0005-is-missing)
  for the general flag. The two judgment calls below are specific to
  this command (they were originally drafted for a `platform generate`
  story on the `epic-c` branch, before the synthesizer existed to back
  it — sequencing it here, after Epic D, is what finally makes them
  testable instead of hypothetical).

## Judgment calls made in ADR-0005's absence

1. **How `--instance` resolves to a retailer.** CLAUDE.md defines a
   "platform-instance" as a `Retailer` (`--instance NAME` maps to
   `rendered/<instance>/`), so `--instance NAME` means "the retailer
   whose `name` equals `NAME`." `load_retailers()` has no parameter to
   select one retailer — it always loads everything under
   `registry/retailers/`. This command filters in the CLI layer (load
   everything, then pick one out of the list) rather than adding an
   `instance=` parameter to the loader — the smaller change, and it
   leaves Epic B's already-shipped loader signature untouched.
2. **`--instance` is optional; omitting it means "every retailer."**
   FR3 shows it as `[--instance NAME]`. Omitting it runs
   `generate_retailer` once per retailer currently in the registry
   (today: `acme`, `paris-lvh`) rather than requiring one or picking an
   arbitrary default — the simplest reading of "optional" that doesn't
   need a hidden default value.

## The concept: a CLI command as a composition root, not a place to put logic

A "composition root" is the one place in a program that wires already-built
pieces together — it calls things, it doesn't decide things. This
command's entire body should read like:

```python
@click.command()
@click.option("--instance", default=None)
def generate(instance):
    retailers = list(load_retailers())          # fail-hard, same as validate
    if instance is not None:
        retailers = [r for r in retailers if r.name == instance]
        if not retailers:
            raise click.ClickException(f"No such instance: {instance}")
    for retailer in retailers:
        generate_retailer(retailer)             # D5 does the actual work
    click.echo("Generated")
```

If a bug shows up here that's actually about *how* a `Deployment` gets
built, or *which* file a service's manifests land in, that's a sign the
fix belongs in `generator.py` (D5), not in `cli.py` — resist patching it
in place just because it's convenient. Click's own docs frame commands
this way for a reason: the CLI layer's only job is translating "the user
typed this" into "call this function," the same division of
responsibility C1's `validate` already established for this codebase.

## What "tested end to end" actually requires here

This repo's convention (confirmed in project memory) is real registry
data, not `tmp_path` fixtures or mocked loaders — which means an
end-to-end test for `generate` really does run `platform generate`
against the real `registry/` and inspect real files landing in
`rendered/`. That's not a testing shortcut to feel uneasy about: `rendered/`
is itself meant to be committed (ArgoCD watches it, per CLAUDE.md's
architecture diagram), so it's real project content, not disposable test
output, and D5's determinism guarantee is exactly what keeps repeated
test runs from generating spurious diffs to accidentally commit. This is
the practical payoff of D5's "byte-identical on re-run" requirement,
beyond satisfying FR4 as an abstract non-functional requirement.

## Acceptance criteria

- `platform generate --instance acme` loads and validates the *entire*
  registry (a loader error anywhere — not just in `acme`'s own files —
  still stops the command, per the fail-hard rule already established
  by `validate`), then synthesizes only `acme` and writes
  `rendered/acme/*.yaml`, leaving `rendered/paris-lvh/` untouched if it
  already exists.
- `platform generate` with no `--instance` does the same for every
  retailer currently in the registry (`acme` and `paris-lvh` today).
- `--instance` naming a retailer that doesn't exist (e.g. `--instance
  nope`) fails with a clear message and a non-zero exit — no silent
  no-op, no partial write.
- Running `platform generate` twice in a row with the registry unchanged
  produces byte-identical files under `rendered/` both times (D5's
  determinism guarantee, now exercised through the actual CLI command a
  user would run).
- Every file written under `rendered/<instance>/` carries the
  `# rendered_schema_version: 1` header D5 produces — this command
  doesn't invent its own stamping logic, it just writes what
  `generate_retailer` returns.

## 📚 Read before starting this story

- [Click — Options](https://click.palletsprojects.com/en/stable/options/) — for `--instance`.
- [Click — Commands and Groups](https://click.palletsprojects.com/en/stable/commands/) — adding a second command to the existing `cli` group without restructuring it.
- [D5](d5-rendered-schema-version.md) — read `generate_retailer`'s contract before wiring this command; this story should not need to know *how* that function works, only what it takes and does.
