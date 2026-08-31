# D2. `Api` and `Worker` workload subclasses

**Goal:** write `Api(K8sWorkload)` and `Worker(K8sWorkload)`. Both
produce a `k8s.KubeDeployment`; `Api` additionally produces a
`k8s.KubeService` (a `ClusterIP` [Service](https://kubernetes.io/docs/concepts/services-networking/service/))
so the deployment is reachable inside the cluster. This is the story
where inheritance actually earns its keep: two sibling classes sharing
one base, diverging only where Kubernetes itself says they must.

**Depends on:** [D1](d1-k8sworkload-base.md) — `K8sWorkload`'s
`.labels` and `.container` are what both subclasses build on top of. The
same missing-ADR-0004 gap D1 flagged applies here too; this story
doesn't re-flag it, only adds the judgment calls specific to `Api`/
`Worker`.

## ⚠️ Blocker (continued from D1): two more `Component` fields

D1 added `image`. This story needs two more, and — per D1's own
reasoning — adds them only now, because only now do they have a real
consumer:

- **`replicas: int = 1`** — `Deployment.spec.replicas`. Defaulting to
  `1` means existing registry components don't need editing to stay
  valid; it also happens to be the value PRD success criterion 2
  exercises later ("editing a component's replica count"). No
  `ge=1`/positive-integer validation is added — a negative or zero
  replica count is nonsensical, but Kubernetes' own API server will
  reject it at apply time regardless, and CLAUDE.md's simplicity rule
  is explicit that error handling for a case the acceptance criteria
  don't require isn't worth the code. If that ever proves too late a
  failure point in practice, adding `Field(ge=1)` is a one-line change,
  not a redesign.
- **`port: int | None = None`** — only meaningful for `api`-type
  components (`Worker` never reads it). This is *not* made conditionally
  required on `workload_type == "api"` via a `model_validator` — if a
  real `api` component is missing `port`, `Api`'s own construction code
  will raise a plain `AttributeError`/`TypeError` trying to build the
  container port, which is a clear enough failure for a personal
  project. Add the cross-field validator later only if that error
  message actually turns out to be confusing in practice — don't
  pre-build it now for a failure that hasn't happened yet.
- Update `registry/services/web/http/component.yaml` with a real
  `port:` (e.g. `8080`) — the only component in the registry today with
  `workload_type: api`. `registry/services/gha/worker/component.yaml`
  needs no changes; `replicas` defaults to `1` and `port` stays unset,
  which is exactly the point of the field being optional.

## The concept: shared base, divergent shape — and where NOT to over-share

```python
class Worker(K8sWorkload):
    def __init__(self, scope, id, *, component):
        super().__init__(scope, id, component=component)
        k8s.KubeDeployment(self, "deployment", spec=k8s.DeploymentSpec(
            replicas=component.replicas,
            selector=k8s.LabelSelector(match_labels=self.labels),
            template=k8s.PodTemplateSpec(
                metadata=k8s.ObjectMeta(labels=self.labels),
                spec=k8s.PodSpec(containers=[self.container]),
            ),
        ))

class Api(Worker):
    ...  # tempting, but wrong — see below
```

The tempting shortcut is `class Api(Worker)`, since `Api` is "a `Worker`
plus a `Service`." Don't — `Api` and `Worker` are siblings under
`K8sWorkload`, not one specializing the other. If `Api` extends `Worker`,
anyone reading `class Api(Worker)` reasonably assumes an `Api` *is* a
kind of worker, and a future change to `Worker`'s deployment logic
silently changes `Api` too, whether or not that's wanted. Both should
extend `K8sWorkload` directly and each build their own
`KubeDeployment` — a few duplicated lines beats an inheritance
relationship that doesn't reflect the actual domain (this is the same
"three similar lines beat a premature abstraction" instinct CLAUDE.md
asks for, applied to class design instead of a config knob).

## Traps specific to this story

- **The selector/label duplication bug.** `Api`'s `KubeService.spec.selector`
  and its `KubeDeployment`'s pod template labels **must** come from the
  exact same `self.labels` dict (inherited from D1), not two
  independently written literals. Get this wrong — a typo, a label added
  to one but not the other — and nothing errors at synth time or even at
  `kubectl apply` time. The `Service` is created successfully; it just
  silently matches zero pods (`kubectl get endpoints` would show
  `<none>`). This is the kind of bug that's invisible until someone is
  debugging "why can't anything reach this service" in a running
  cluster. Build the acceptance criteria's selector check as a real
  assertion, not a spot-check.
- **Scope, not just parentage.** When `Api` creates its `KubeDeployment`
  and `KubeService`, pass `self` (the `Api` instance) as their `scope`,
  not the chart above it. This keeps their construct IDs namespaced
  under `Api`'s own path, so two different `Api` instances in the same
  chart can each have a construct literally called `"service"` without
  colliding — the scope tree, not manual name-mangling, is what CDK8s
  gives you for this.
- **Determinism is not actually at risk from dict ordering here.**
  Python 3.7+ dicts preserve insertion order, and this code always
  builds the same dict the same way on every run — there's no dynamic,
  order-varying iteration in `Api`/`Worker`'s own logic. The real
  determinism risks in this epic are the ones already named in D1 (don't
  invent random construct IDs) and the one D4 will name (be deliberate
  about `yaml.safe_dump`'s key ordering when writing files) — don't go
  looking for a dict-ordering bug that isn't actually there.

## Acceptance criteria

- `Component` gains `replicas: int = 1` and `port: int | None = None` in
  `src/platform_generator/models.py`; `registry/services/web/http/component.yaml`
  gains a real `port:` value.
- `Worker`, built from the real `gha`/`worker` component
  (`registry/services/gha/worker/component.yaml`), synthesizes exactly
  one `KubeDeployment` — no `KubeService` — with
  `spec.replicas == 1`, one container whose `image` matches the
  component's `image`, and no container ports set.
- `Api`, built from the real `web`/`http` component
  (`registry/services/web/http/component.yaml`), synthesizes a
  `KubeDeployment` (`spec.replicas == 1`, container port ==
  the component's `port`) **and** a `KubeService` of `type: ClusterIP`
  whose `spec.selector` is exactly the `Api`'s `.labels` and whose
  `spec.ports[0].port` matches the component's `port`.
- Changing only `registry/services/web/http/component.yaml`'s `replicas`
  to `3` and rebuilding changes `spec.replicas` in `Api`'s synthesized
  output from `1` to `3` and nothing else in that output — the
  construct-level proof of PRD success criterion 2, ahead of D5/E1
  actually writing files to disk.
- No new field is added to make `port` required for `api` components at
  the schema level (per the judgment call above) — confirm this by *not*
  finding a `model_validator` doing so, not by testing an error path
  that was deliberately not built.

## 📚 Read before starting this story

- [Kubernetes — Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/) — `spec.replicas`, `spec.selector`, `spec.template`.
- [Kubernetes — Services](https://kubernetes.io/docs/concepts/services-networking/service/) — `ClusterIP`, and specifically how `spec.selector` is matched against pod labels; this is the doc that explains why the selector/label bug above is invisible until runtime.
- [D1](d1-k8sworkload-base.md) — read the "concept" and "traps" sections again with `Api`/`Worker` in mind before writing either class.
