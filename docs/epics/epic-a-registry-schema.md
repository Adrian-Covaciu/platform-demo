# Epic A — Registry & Schema

**Goal:** stand up the YAML registry and validate it on load via typed
Pydantic models, so every later epic has real, schema-checked data to work
against.

**Related ADR:** [ADR-0002 — Pydantic typed registry models](../adr/0002-pydantic-typed-registry-models.md)

**Stories:**
1. [A1. Define Pydantic models for the registry](../stories/a1-pydantic-models.md)
2. [A2. Author an example retailer registry](../stories/a2-example-registry.md)
3. [A3. Enforce name uniqueness where collisions can actually happen](../stories/a3-name-uniqueness.md)

**📚 Read before starting this epic**
- [Pydantic — Models](https://docs.pydantic.dev/latest/concepts/models/) — the core concept this whole epic is built on.
- [Pydantic — Fields](https://docs.pydantic.dev/latest/concepts/fields/) — required vs optional fields, defaults.
- [Python `enum` module](https://docs.python.org/3/library/enum.html) — backs the `workload_type` enum.
