# Epics: platform-demo v1

Index of the epics for the single-repo GitOps demo described in
[`docs/PRD.md`](../PRD.md). Each epic links to its own stories under
[`docs/stories/`](../stories/) — this index and each epic file are kept
short on purpose; the detail lives one level down.

| Epic | Focus | Stories |
|---|---|---|
| [A — Registry & Schema](epic-a-registry-schema.md) | Typed YAML registry, validated on load | 3 |
| [B — Typed Loader & Merge](epic-b-loader-merge.md) | Base + env-type merge, fail-hard/warn-skip | 3 |
| [C — CLI](epic-c-cli.md) | `platform validate/generate/diff/impact` | 4 |
| [D — CDK8s Synthesizer](epic-d-synthesizer.md) | Workload constructs → K8s manifests | 4 |
| [E — GitOps Wiring](epic-e-gitops-wiring.md) | kind + ArgoCD, end-to-end sync | 3 |
| [F — Docs/Demo](epic-f-docs-demo.md) | README quickstart, demo script | 2 |

Suggested build order matches the table top-to-bottom: each epic's stories
depend on registry/loader work from A and B being in place first, and E/F
depend on the CLI (C) and synthesizer (D) existing.

See also: [`docs/PRD.md`](../PRD.md) for scope and success criteria, and
[`docs/adr/`](../adr/) for the reasoning behind each technical choice.
