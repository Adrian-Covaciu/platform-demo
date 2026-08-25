# Epic B — Typed Loader & Merge

**Goal:** implement the base + env-type deep merge with a documented array
policy, and the fail-hard / warn-skip error split borrowed from the
reviewed system's CLAUDE.md rule.

**Related ADR:** [ADR-0003 — Single override tier + merge policy](../adr/0003-single-override-tier-plus-merge-policy.md)

**Depends on:** [Epic A](epic-a-registry-schema.md) (models must exist before there's anything to merge).

**Stories:**
1. [B1. Implement base + env-type deep merge](../stories/b1-deep-merge.md)
2. [B2. Fail-hard on missing references](../stories/b2-fail-hard-missing-refs.md)
3. [B3. Warn-and-skip on non-fatal data issues](../stories/b3-warn-skip.md)

**📚 Read before starting this epic**
- [PyYAML documentation](https://pyyaml.org/wiki/PyYAMLDocumentation) — custom tag constructors, needed for the `!merge` tag.
- [Python `logging` module — basic tutorial](https://docs.python.org/3/howto/logging.html) — the warn-skip path logs, it doesn't print.
- [Pydantic — Error handling](https://docs.pydantic.dev/latest/concepts/models/#error-handling) — turning `ValidationError` into a clean CLI message.
