# Epic D — CDK8s Synthesizer

**Goal:** turn merged registry models into Kubernetes manifests via CDK8s
constructs, one per workload type, with a version-stamped rendered output.

**Related ADRs:**
- [ADR-0004 — CDK8s Python synthesizer](../adr/0004-cdk8s-python-synthesizer.md)
- [ADR-0006 — `rendered_schema_version` pin](../adr/0006-rendered-schema-version-pin.md)

**Depends on:** [Epic A](epic-a-registry-schema.md) (models feed the constructs) and [Epic B](epic-b-loader-merge.md) (merged output is the synth input).

**Stories:**
1. [D1. `K8sWorkload` base construct](../stories/d1-k8sworkload-base.md)
2. [D2. `Api` and `Worker` workload subclasses](../stories/d2-api-worker-subclasses.md)
3. [D3. `Cronjob` workload subclass](../stories/d3-cronjob-subclass.md)
4. [D4. Write rendered output with the schema-version header](../stories/d4-rendered-schema-version.md)

**📚 Read before starting this epic**
- [CDK8s — Getting started (Python)](https://cdk8s.io/docs/latest/getting-started/) — installing the CLI, `cdk8s init python-app`, the construct model.
- [Kubernetes — Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/) — what `Api`/`Worker` actually emit.
- [Kubernetes — Services](https://kubernetes.io/docs/concepts/services-networking/service/) — the ClusterIP Service that `Api` adds.
- [Kubernetes — CronJob](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/) — for D3.
