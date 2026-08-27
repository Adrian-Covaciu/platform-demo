# Epic B — Typed Loader

**Goal:** implement the fail-hard loader error rule from CLAUDE.md — any
loader error (missing file, unparseable YAML, duplicate name, or a file
that fails `Model.model_validate()`) stops the whole run. (The base +
env-type override tier from the reviewed two-repo system is out of scope
here — see `docs/PRD.md`'s "Out of scope" section; it belongs to a
future, separate synthesis repo.)

**Depends on:** [Epic A](epic-a-registry-schema.md) (models must exist before there's anything to load).

**Stories:**
1. [B1. Fail-hard on missing references](../stories/b1-fail-hard-missing-refs.md)

**Dropped:** B2 ("warn-and-skip on non-fatal data issues") was scoped
before this epic settled on fail-hard-everywhere. There is no
warn-and-skip path in this loader by design — see CLAUDE.md's
Architecture section. `docs/stories/b2-warn-skip.md` is kept for
historical context but is not to be implemented.

**📚 Read before starting this epic**
- [Pydantic — Error handling](https://docs.pydantic.dev/latest/concepts/models/#error-handling) — turning `ValidationError` into a clean CLI message.
