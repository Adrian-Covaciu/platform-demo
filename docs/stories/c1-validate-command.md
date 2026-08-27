# C1. `platform validate`

**Goal:** ship `platform validate` — load and validate the whole registry
via the existing `loader.load_retailers()`, fail hard with a clean
message on any loader error, otherwise exit `0`. This is also where the
`platform` CLI itself gets scaffolded (Click added as a dependency, a
console-script entry point wired up), since no CLI exists yet.

**Depends on:** [Epic B](../epics/epic-b-loader-merge.md) —
`src/platform_generator/loader.py` already exists and is exactly what
this command wraps. No dependency on Epic D (the synthesizer); `validate`
never renders anything.

**Related ADR:** [ADR-0005 — Click CLI structure](../adr/0005-click-cli-structure.md)
— **this file does not exist.** See the flag below.

## ⚠️ ADR-0005 is missing

`docs/epics/epic-c-cli.md` links `../adr/0005-click-cli-structure.md`,
but `docs/adr/` doesn't exist anywhere in this repo yet — no ADR has ever
been written, for this epic or any other (0002, 0004, 0006, 0008 are all
referenced from epic files and none exist on disk). CLAUDE.md says
architecture decisions "are pre-made in `docs/adr/` — don't re-litigate
them while implementing a story," but the doc that's supposed to have
already settled the CLI's shape simply isn't there. The judgment calls
below are this story's stand-in for that missing decision, not a settled
design — revise every story in this epic once ADR-0005 actually exists.

**Judgment calls made in its absence:**

1. **Command grouping.** The PRD's "Background" section and this epic's
   own goal line both describe the CLI as a `<verb> <noun>` design
   (echoing the two-repo system it's modeled on, e.g. `kmi generate
   service`) — but PRD FR3, and the story list in `epic-c-cli.md` itself,
   only ever give flat, noun-less commands: `platform validate`,
   `platform generate`, `platform diff`, `platform impact <path>`. These
   two descriptions of the same CLI contradict each other. This story
   (and C2–C4) go with the flat form, since that's what FR3 spells out
   concretely per command. If ADR-0005 lands on true verb-noun
   subcommands instead, every command signature in this epic needs
   revisiting.
2. **Entry point wiring.** Nothing anywhere names the CLI's module or how
   it's installed. This story adds `src/platform_generator/cli.py`
   exposing a single Click group (`cli`), registered in `pyproject.toml`
   under `[project.scripts]` as `platform = "platform_generator.cli:cli"`
   — the standard Click packaging pattern, not a decision documented
   anywhere in this repo.
3. **How errors surface.** Click's own `click.ClickException` mechanism
   is used to turn a loader exception into a one-line `Error: ...`
   message and a non-zero exit code, satisfying PRD success criterion 3
   ("fails meaningfully ... not a stack trace") without inventing a
   custom error-formatting layer of our own.

## Acceptance criteria

- `pyproject.toml` gains `click` as a runtime dependency (it isn't there
  today) and a `[project.scripts]` entry, so `pip install -e ".[dev]"`
  puts a `platform` command on `PATH`.
- `platform validate` fully consumes `loader.load_retailers()` — it's a
  generator, so validation of a given retailer only actually happens
  when that item is iterated. Calling the function without iterating it
  (e.g. forgetting to wrap it in `list(...)`) would silently validate
  nothing; the command must force full iteration to get the fail-hard
  behavior FR2 promises.
- On success, the command exits `0`. A short confirmation line on stdout
  (e.g. `Registry OK`) is fine — FR3's "no output written" refers to not
  writing anything under `rendered/`, not to stdout being silent.
- On any loader error — a missing referenced file, unparseable YAML, a
  duplicate name (per A3's scoped uniqueness rules), or a file that
  parses but fails `Model.model_validate()` — the command exits non-zero
  and prints the underlying error message once, with no raw Python
  traceback. This is FR2's fail-hard contract surfacing through the CLI
  for the first time.
- `platform validate` never creates, modifies, or deletes any file —
  it's read-only against `registry/`.
- Verified against the registry as it stands today: `platform validate`
  exits `0` for `registry/retailers/acme` and
  `registry/retailers/paris-lvh` as committed right now. To exercise the
  failure path, use a temporarily-broken copy of one of these rather than
  adding a permanent broken fixture to the registry (per this repo's
  practice of testing against real registry data, not synthetic
  fixtures).

## 📚 Read before starting this story

- [Click — Quickstart](https://click.palletsprojects.com/en/stable/quickstart/) — commands, options, groups.
- [Click — Setuptools Integration](https://click.palletsprojects.com/en/stable/setuptools-integration/) — the console-script entry point this story adds; new territory since no CLI exists yet.
- [Click — Exceptions](https://click.palletsprojects.com/en/stable/exceptions/) — `ClickException`, used here to avoid a raw traceback on a loader error.
- `CLAUDE.md`'s "Architecture" section — restates the fail-hard rule this command has to honor.
