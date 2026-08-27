# Epic D — CDK8s Synthesizer

**Goal:** turn validated registry models into Kubernetes manifests via
CDK8s constructs, one per workload type, with a version-stamped rendered
output — then wire that synth into the `generate` and `diff` CLI
commands, which couldn't ship in Epic C without it.

**Depends on:** [Epic A](epic-a-registry-schema.md) (models feed the constructs), [Epic B](epic-b-loader-merge.md) (validated registry output is the synth input), and [C1](../stories/c1-validate-command.md) (the `platform` CLI scaffold that D5/D6 add commands to).

**Stories:**
1. [D1. `K8sWorkload` base construct](../stories/d1-k8sworkload-base.md)
2. [D2. `Api` and `Worker` workload subclasses](../stories/d2-api-worker-subclasses.md)
3. [D3. `Cronjob` workload subclass](../stories/d3-cronjob-subclass.md)
4. [D4. Write rendered output with the schema-version header](../stories/d4-rendered-schema-version.md)
5. [D5. `platform generate`](../stories/d5-generate-command.md)
6. [D6. `platform diff`](../stories/d6-diff-command.md)

**📚 Read before starting this epic**
- [CDK8s — Getting started (Python)](https://cdk8s.io/docs/latest/getting-started/) — installing the CLI, `cdk8s init python-app`, the construct model.
- [Kubernetes — Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/) — what `Api`/`Worker` actually emit.
- [Kubernetes — Services](https://kubernetes.io/docs/concepts/services-networking/service/) — the ClusterIP Service that `Api` adds.
- [Kubernetes — CronJob](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/) — for D3.
- [Python `difflib`](https://docs.python.org/3/library/difflib.html) — producing the unified diff for `platform diff` (D6).
