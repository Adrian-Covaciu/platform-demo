# Epic B — Typed Loader

**Goal:** implement the fail-hard / warn-skip error split borrowed from
the reviewed system's CLAUDE.md rule. (The base + env-type override tier
from the reviewed two-repo system is out of scope here — see
`docs/PRD.md`'s "Out of scope" section; it belongs to a future, separate
synthesis repo.)

**Depends on:** [Epic A](epic-a-registry-schema.md) (models must exist before there's anything to load).

**Stories:**
1. [B1. Fail-hard on missing references](../stories/b1-fail-hard-missing-refs.md)
2. [B2. Warn-and-skip on non-fatal data issues](../stories/b2-warn-skip.md)

**📚 Read before starting this epic**
- [Python `logging` module — basic tutorial](https://docs.python.org/3/howto/logging.html) — the warn-skip path logs, it doesn't print.
- [Pydantic — Error handling](https://docs.pydantic.dev/latest/concepts/models/#error-handling) — turning `ValidationError` into a clean CLI message.
