# Epic C — CLI

**Goal:** ship the `<verb> <noun>` Click CLI (`validate`, `generate`,
`diff`, and stretch `impact`) as thin commands delegating to the loader/
merge/synth modules.

**Related ADR:** [ADR-0005 — Click CLI structure](../adr/0005-click-cli-structure.md)

**Depends on:** [Epic B](epic-b-loader-merge.md) (loader/merge must exist for commands to call into).

**Stories:**
1. [C1. `platform validate`](../stories/c1-validate-command.md)
2. [C2. `platform generate`](../stories/c2-generate-command.md)
3. [C3. `platform diff`](../stories/c3-diff-command.md)
4. [C4. `platform impact <path>` (stretch)](../stories/c4-impact-command.md)

**📚 Read before starting this epic**
- [Click — Quickstart](https://click.palletsprojects.com/en/stable/quickstart/) — commands, options, arguments.
- [Python `difflib`](https://docs.python.org/3/library/difflib.html) — producing the unified diff for `platform diff`.
