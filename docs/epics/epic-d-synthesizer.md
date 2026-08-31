# Epic D — CDK8s Synthesizer

**Goal:** turn validated registry models into Kubernetes manifests via
CDK8s constructs, one per workload type, each service's workloads
isolated in their own namespace, with a version-stamped rendered output.
The `generate` and `diff` CLI commands that consume this synth ship as
part of [Epic E](epic-e-gitops-wiring.md), since they're really about
wiring the synth into the GitOps loop, not about the synth itself.

**Depends on:** [Epic A](epic-a-registry-schema.md) (models feed the
constructs) and [Epic B](epic-b-loader-merge.md) (validated registry
output is the synth input).

**Stories:**
1. [D1. `K8sWorkload` base construct](../stories/d1-k8sworkload-base.md)
2. [D2. `Api` and `Worker` workload subclasses](../stories/d2-api-worker-subclasses.md)
3. [D3. `Cronjob` workload subclass](../stories/d3-cronjob-subclass.md)
4. [D4. Per-service Kubernetes namespace](../stories/d4-service-namespace.md)
5. [D5. Write rendered output with the schema-version header](../stories/d5-rendered-schema-version.md)

**📚 Read before starting this epic**
- [CDK8s — Getting started (Python)](https://cdk8s.io/docs/latest/getting-started/) — installing the CLI, `cdk8s init python-app`, the construct model.
- [Kubernetes — Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/) — what `Api`/`Worker` actually emit.
- [Kubernetes — Services](https://kubernetes.io/docs/concepts/services-networking/service/) — the ClusterIP Service that `Api` adds.
- [Kubernetes — CronJob](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/) — for D3.
- [Kubernetes — Namespaces](https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/) — for D4.
