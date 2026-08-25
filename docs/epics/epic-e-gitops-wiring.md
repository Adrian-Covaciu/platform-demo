# Epic E — GitOps Wiring

**Goal:** stand up a local kind cluster with ArgoCD watching `rendered/`,
and verify by hand that the full edit → generate → commit → sync loop
actually works.

**Related ADR:** [ADR-0008 — ArgoCD on local kind](../adr/0008-argocd-on-local-kind.md)

**Depends on:** [Epic D](epic-d-synthesizer.md) (needs rendered manifests to sync against).

**Stories:**
1. [E1. Local kind cluster bootstrap script](../stories/e1-kind-bootstrap.md)
2. [E2. ArgoCD Application pointed at `rendered/`](../stories/e2-argocd-application.md)
3. [E3. End-to-end demo flow verified manually](../stories/e3-e2e-verification.md)

**📚 Read before starting this epic**
- [kind — Quick start](https://kind.sigs.k8s.io/docs/user/quick-start/) — creating a local cluster.
- [ArgoCD — Getting started](https://argo-cd.readthedocs.io/en/stable/getting_started/) — install + first app sync.
- [ArgoCD — Application CRD reference](https://argo-cd.readthedocs.io/en/stable/operator-manual/application.yaml/) — the manifest E2 writes.
- [kubectl — Command reference](https://kubernetes.io/docs/reference/kubectl/) — for the manual verification in E3.
