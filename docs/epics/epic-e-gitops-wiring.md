# Epic E — GitOps Wiring

**Goal:** ship the `generate` and `diff` CLI commands that turn Epic D's
synthesizer into something a user actually runs, then stand up a local
kind cluster with ArgoCD watching `rendered/`, and verify by hand that
the full edit → generate → commit → sync loop actually works.

**Depends on:** [Epic D](epic-d-synthesizer.md) (`generate_retailer` is
what E1/E2 call into, and rendered manifests are what E3/E4 sync
against) and [C1](../stories/c1-validate-command.md) (the `platform` CLI
scaffold E1/E2 add commands to).

**Stories:**
1. [E1. `platform generate`](../stories/e1-generate-command.md)
2. [E2. `platform diff`](../stories/e2-diff-command.md)
3. [E3. Local kind cluster bootstrap script](../stories/e3-kind-bootstrap.md)
4. [E4. ArgoCD Application pointed at `rendered/`](../stories/e4-argocd-application.md)
5. [E5. End-to-end demo flow verified manually](../stories/e5-e2e-verification.md)

**📚 Read before starting this epic**
- [Click — Quickstart](https://click.palletsprojects.com/en/stable/quickstart/) — for E1/E2, a second and third command on the existing `cli` group.
- [Python `difflib`](https://docs.python.org/3/library/difflib.html) — producing the unified diff for `platform diff` (E2).
- [kind — Quick start](https://kind.sigs.k8s.io/docs/user/quick-start/) — creating a local cluster.
- [ArgoCD — Getting started](https://argo-cd.readthedocs.io/en/stable/getting_started/) — install + first app sync.
- [ArgoCD — Application CRD reference](https://argo-cd.readthedocs.io/en/stable/operator-manual/application.yaml/) — the manifest E4 writes.
- [kubectl — Command reference](https://kubernetes.io/docs/reference/kubectl/) — for the manual verification in E5.
