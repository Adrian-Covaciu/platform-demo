# D3. `Cronjob` workload subclass

**Goal:** write `Cronjob(K8sWorkload)`, producing a single
`k8s.KubeCronJob`. This isn't "one more sibling of `Api`/`Worker`" in the
way D2's two classes were siblings of each other — a
[`CronJob`](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/)
wraps a `JobTemplate`, which wraps a `PodTemplate`. That's a genuinely
different, deeper shape than `Deployment`'s single `spec.template`, and
it comes with a real Kubernetes constraint `Api`/`Worker` never had to
think about.

**Depends on:** [D1](d1-k8sworkload-base.md) — same base, same
`.labels`/`.container`. Not on [D2](d2-api-worker-subclasses.md) — `Cronjob`
shares nothing with `Api`/`Worker` beyond the D1 base, and needs neither
`replicas` nor `port`. Same missing-ADR-0004 gap as D1/D2, not re-flagged
here.

## The concept: three levels of nesting, not two

`Deployment` is `spec.template.spec.containers` — one wrapper
(`PodTemplateSpec`) around a `PodSpec`. `CronJob` is
`spec.jobTemplate.spec.template.spec.containers` — a `JobTemplateSpec`
wrapping a `JobSpec` wrapping the *same* `PodTemplateSpec`/`PodSpec`
shape `Deployment` uses. It's one layer deeper because a `CronJob`
doesn't run pods directly — it creates `Job` objects on schedule, and
each `Job` is itself the thing that runs pods. Understanding this nesting
before writing the construct saves a lot of "why won't this attribute
exist" debugging; sketch it out on paper first if it helps:

```
KubeCronJob
  .spec: CronJobSpec
    .schedule: str
    .job_template: JobTemplateSpec
      .spec: JobSpec
        .template: PodTemplateSpec   # <- same shape as Deployment's
          .spec: PodSpec
            .containers: [...]
            .restart_policy: ...     # <- see the trap below
```

## Trap: `restartPolicy: Always` is invalid here

A `Deployment`'s pods effectively assume `restartPolicy: Always` — the
whole point of a `Deployment` is that its pods are meant to keep running.
A `Job` (and therefore a `CronJob`, which only ever creates `Job`s) is a
*run-to-completion* workload: it must use `restartPolicy: OnFailure` or
`restartPolicy: Never`, and the [Kubernetes Jobs
docs](https://kubernetes.io/docs/concepts/workloads/controllers/job/)
say so explicitly. If `Cronjob`'s `PodSpec` is built by literally copying
`Worker`'s pod-template code from D2 without changing this one field, the
result is a manifest the Kubernetes API server will reject outright —
not a subtle bug, but one that's easy to introduce precisely *because*
the rest of the pod spec looks identical to `Worker`'s. Use
`restart_policy="OnFailure"` here; `Worker`/`Api` don't set it at all
(they get the correct `Always` default from Kubernetes itself).

`schedule` (the cron string, e.g. `"0 3 * * *"`) is not validated as real
cron syntax — that field already existed on `Component` before this
story and this story doesn't add a `croniter`-style check to it.
Kubernetes' own API server already rejects a malformed schedule at
`kubectl apply` (or ArgoCD sync, in Epic E) time; duplicating that
validation here would be exactly the kind of robustness CLAUDE.md's
simplicity rule says to skip when the acceptance criteria don't call for
it.

## ⚠️ Real gap: there is no cronjob component in the registry yet

`registry/services/` has exactly two components today — `web/http`
(`api`) and `gha/worker` (`worker`) — and zero `cronjob` components
anywhere. This repo's convention (confirmed in project memory: test
against real registry data, never invented fixtures) means this story
can't just make up a `Component(workload_type="cronjob", ...)` inline in
a test the way a fixture-based test suite would. Two ways to resolve
that:

1. Add a genuine `cronjob` component to the registry — real registry
   content, not test scaffolding, the same way any other component gets
   added over the life of this project.
2. Leave the registry as-is and accept that `Cronjob` can only be tested
   by constructing a `Component` object directly in Python (not loaded
   from YAML) — which technically isn't a "fixture" in the tmp_path/mock
   sense, but also doesn't exercise the loader at all, and never proves
   a `cronjob` component round-trips through real YAML.

This story takes option 1: add a new component, `nightly-report`
(`workload_type: cronjob`, a plausible `schedule` like `"0 3 * * *"`, and
an `image`), under `registry/services/gha/`, and add it to
`registry/services/gha/service.yaml`'s `components:` list alongside
`worker`. Both `acme` and `paris-lvh` already list `gha` under
`services:`, so both instances pick up the new component automatically —
no `retailer.yaml` edits needed. This is a real, permanent addition to
the registry, not a scratch fixture; treat it with the same care as any
other registry change (and flag it for the human's sign-off before
committing, since it's new committed content, not just code).

## Acceptance criteria

- `registry/services/gha/nightly-report/component.yaml` exists with
  `workload_type: cronjob`, a real `schedule`, and a real `image`;
  `registry/services/gha/service.yaml`'s `components:` list includes it.
  `platform validate` still exits `0` against `registry/retailers/acme`
  and `registry/retailers/paris-lvh` after the addition.
- `Cronjob`, built from that real component, synthesizes exactly one
  `KubeCronJob` with `spec.schedule` matching the component's `schedule`,
  `spec.job_template.spec.template.spec.restart_policy` equal to
  `"OnFailure"` (not `"Always"`, and not unset), and a container whose
  `image` matches the component's `image`.
- No `KubeDeployment` or `KubeService` is produced for a `cronjob`
  component — `Cronjob` and `Api`/`Worker` are mutually exclusive
  outputs per component, driven by `workload_type`.
- Re-synthesizing with no registry changes produces byte-identical
  output (same determinism check as D2, applied to `Cronjob`).

## 📚 Read before starting this story

- [Kubernetes — CronJob](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/) — the `JobTemplate`/`PodTemplate` nesting this story's construct mirrors.
- [Kubernetes — Jobs](https://kubernetes.io/docs/concepts/workloads/controllers/job/) — specifically the "Pod backoff failure policy" / restart policy constraint; the `CronJob` doc alone doesn't spell out the `restartPolicy` restriction as clearly as this one does.
- [D1](d1-k8sworkload-base.md) — the base construct `Cronjob` extends; re-read its "concept" section before assuming `Cronjob` needs anything `Api`/`Worker` needed that it doesn't.
