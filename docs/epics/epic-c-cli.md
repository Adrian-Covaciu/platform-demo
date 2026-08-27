# Epic C — CLI

**Goal:** ship the `<verb> <noun>` Click CLI scaffold and its first
command, `validate`, as a thin command delegating to the loader.
`generate` and `diff` need the CDK8s synthesizer to back them, so they
ship as D5/D6 once [Epic D](epic-d-synthesizer.md) exists.

**Depends on:** [Epic B](epic-b-loader-merge.md) (loader must exist for commands to call into).

**Stories:**
1. [C1. `platform validate`](../stories/c1-validate-command.md)

**📚 Read before starting this epic**
- [Click — Quickstart](https://click.palletsprojects.com/en/stable/quickstart/) — commands, options, arguments.
