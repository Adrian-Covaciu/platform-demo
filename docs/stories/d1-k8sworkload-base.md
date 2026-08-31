# D1. `K8sWorkload` base construct

**Goal:** write `K8sWorkload`, a CDK8s *construct* (a node in CDK8s's
scope tree — more on that below) that holds everything `Api`, `Worker`,
and `Cronjob` (D2/D3) will need in common: a deterministic name, a shared
`labels` dict, and a `k8s.Container` built from a `Component`. It doesn't
emit a `Deployment` or `CronJob` itself — that shape genuinely differs per
subclass, which is D2/D3's job. D1 is the plumbing they'll all reuse, and
it's also where `pyproject.toml` first gains a `cdk8s` dependency and this
repo first touches the CDK8s API at all.

**Depends on:** [Epic A](../epics/epic-a-registry-schema.md) (`Component`
is the input; this story also *extends* it — see the blocker below) and
[Epic B](../epics/epic-b-loader-merge.md) (`load_retailers()` is what
hands D1 a real `Component` to build from). Not depended on by C1
(`validate` never synthesizes), but this story's model change to
`Component` must not break `platform validate`, which already ships.

**Related ADR:** ADR-0004 — CDK8s Python synthesizer — **this file does
not exist.** See the flag below.

## ⚠️ ADR-0004 is missing

`docs/epics/epic-d-synthesizer.md` used to link
`../adr/0004-cdk8s-python-synthesizer.md`, and that link was dropped when
the epic file was trimmed — but no ADR for *any* number (0002, 0004,
0005, 0006, 0008) exists anywhere in this repo. [C1](c1-validate-command.md)
already flagged this for ADR-0005; the same gap applies here, one level
deeper: nothing has settled *how* CDK8s constructs in this repo compose
(one construct per `Component`? per `Service`? does a `Chart` map to a
`Service` or a `Retailer`?) or *how* they're named. The judgment calls
below are this story's stand-in. If ADR-0004 ever gets written, D1–D4 are
what it needs to ratify or override — treat this section (and the
matching ones in D2–D4) as the working notes for that future document,
not a settled design.

## ⚠️ Blocker: `Component` doesn't have an `image` field

Read `src/platform_generator/models.py`. `Component` today is:

```python
class Component(BaseModel):
    name: str
    workload_type: WorkloadType
    schedule: str | None = None
```

There is no way to build a real `k8s.Container` from this — every
container in Kubernetes needs an image, full stop (see the [Deployment
docs](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
this epic's reading list already points at: the pod template's
`containers[].image` is not optional). This isn't a nice-to-have D1 can
defer to D2/D3 — the *base* construct is exactly where a shared container
gets built, so this is where the model has to grow.

Epic A is already merged (PRs #2/#3), so this is a genuine cross-epic
change, not something to quietly assume into existence in an acceptance
criterion. This story does it explicitly, as its first concrete step:

- Add `image: str` to `Component` — required, no default. A container
  with no image isn't a valid-but-incomplete state worth defaulting
  around; it's just wrong, and Pydantic making it a required field means
  `platform validate` already catches a missing image before D1's
  construct code ever runs, which is the fail-hard behavior CLAUDE.md
  already commits this repo to.
- Update both real components on disk —
  `registry/services/web/http/component.yaml` and
  `registry/services/gha/worker/component.yaml` — with a real `image:`
  value. For `http`, the `web` service already declares an
  `http-image-repo` ECR resource
  (`registry/services/web/shared/http-image-repo.yaml`) — use an image
  reference that plausibly points at that repo (e.g.
  `123456789012.dkr.ecr.eu-west-1.amazonaws.com/http-image-repo:latest`)
  so the registry tells one consistent story instead of an arbitrary
  string. `gha`'s `worker` has no matching ECR resource declared, so a
  plain placeholder (e.g. `ghcr.io/acme/gha-worker:latest`) is honest
  about that gap rather than inventing a resource this story doesn't own.

`replicas` (needed for `Api`/`Worker`'s `Deployment.spec.replicas`, and
the field PRD success criterion 2 explicitly calls out) and `port`
(needed for `Api`'s container port and `Service`) are **not** added here.
Only add a field when the story that actually needs it is being written
— [D2](d2-api-worker-subclasses.md) adds both, and references this
section instead of re-deriving the "Epic A model is now cross-epic"
point. `Cronjob` (D3) needs nothing beyond what D1 adds.

## The concept: a construct is a node in a tree, not just a class instance

CDK8s (like the AWS CDK it borrows its `constructs` library from) doesn't
work like a typical Python object graph where you just instantiate things
and pass them around. Every construct you create takes a `scope` (its
parent in a tree) and an `id` (unique *only among its siblings under that
same scope* — not globally unique). CDK8s walks that whole tree from the
top (an `App`) down to decide what to synthesize, and it also uses the
tree *path* (not just the `id`) to auto-generate things like resource
names when you don't specify one yourself.

Minimal illustration of the shape (not this story's real code):

```python
from constructs import Construct

class K8sWorkload(Construct):
    def __init__(self, scope: Construct, id: str, *, component):
        super().__init__(scope, id)
        self.labels = {"app": component.name}
        self.container = self._build_container(component)
```

`K8sWorkload` extends the plain `Construct` base (from the `constructs`
package CDK8s is built on) — not `cdk8s.Chart` and not an `ApiObject`. It
doesn't need to *be* a chart (a chart is what maps to one output file)
and it doesn't need to *be* an `ApiObject` (an actual K8s API resource
like a `Deployment`) — it's just a place to put logic and state that
`Api`, `Worker`, and `Cronjob` all reuse. This is the moment class
hierarchies in CDK8s actually click: the base class doesn't need to
emit anything on its own to be useful.

Resist the instinct to make this "properly abstract" with `abc.ABC` and
`@abstractmethod`. Python doesn't require that ceremony to say "this
class isn't meant to be instantiated on its own" — nothing in this
epic's generator code will ever call `K8sWorkload(...)` directly (D4's
orchestration always picks `Api`/`Worker`/`Cronjob`), so there's no real
bug an `ABC` would prevent here. That's exactly the kind of
extensibility scaffolding CLAUDE.md's simplicity rule asks you to skip —
three known, fixed subclasses don't need a plugin system.

## Traps specific to this story

- **Construct IDs are not resource names, but they influence them.** If
  you don't pass an explicit `metadata={"name": ...}` when building a
  K8s API object later (D2/D3), CDK8s derives a name from the construct's
  path in the scope tree, and it's not guaranteed to be a clean,
  human-readable `component.name` — check this empirically once D2/D3
  exist, don't assume it. D1 itself doesn't create an `ApiObject`, so
  this doesn't bite yet, but the `id` you choose here (this story's call:
  use `component.name` as both `K8sWorkload`'s construct `id` and the
  container's `name`) is what D2/D3 build on top of.
- **Don't manufacture a "safer" random ID.** A learner's instinct when
  told "IDs must be unique" is often to append a `uuid4()` or a hash.
  Don't — CLAUDE.md's own scoping rule (A3) already guarantees
  `component.name` is unique everywhere it needs to be (components live
  inside their service's namespace scope), and a random suffix would
  make the output different on every run, which breaks FR4's
  determinism requirement outright. Determinism here is not automatic
  robustness — it's a hard requirement `platform diff` (E2) depends on.
- **`cdk8s import`, not hand-written K8s types.** Don't hand-write
  classes for `Container`, `PodSpec`, etc. — CDK8s ships a code generator
  (`cdk8s import k8s`) that turns the Kubernetes OpenAPI spec into typed
  Python classes (`k8s.Container`, `k8s.KubeDeployment`, ...). Generate
  them once into `src/platform_generator/imports/` and **commit the
  generated code** — this mirrors a pattern this project's own review
  notes call out as worth stealing (`registry-review.md`: "CDK8s/CDKTF
  constructs committed... pinned generated code, regenerable via
  `cdktf get` / `cdk8s import`. No runtime chart download."). Don't add
  `imports/` to `.gitignore`.

## Acceptance criteria

- `pyproject.toml` gains `cdk8s` as a runtime dependency.
  `src/platform_generator/imports/` contains the generated K8s typed
  classes from `cdk8s import k8s`, committed to git.
- `Component.image: str` is added (required) to
  `src/platform_generator/models.py`, and both real components on disk
  (`registry/services/web/http/component.yaml`,
  `registry/services/gha/worker/component.yaml`) are updated with a real
  `image:` value, per the blocker section above.
- `platform validate` (C1, already shipped) still exits `0` against
  `registry/retailers/acme` and `registry/retailers/paris-lvh` after this
  change — a regression check that the model edit didn't quietly break
  an already-working command.
- `K8sWorkload` is a `constructs.Construct` subclass, constructed as
  `K8sWorkload(scope, component.name, component=component)`, exposing:
  - `.labels` — a dict, `{"app": component.name}`.
  - `.container` — a `k8s.Container` with `name == component.name` and
    `image == component.image`, and no ports set.
- Instantiating `K8sWorkload` (directly — nothing stops you doing this in
  a test even though production code never will) twice with the same
  `id` under the same scope raises — this is `constructs`' own
  sibling-uniqueness rule, not code D1 writes, and the test is there to
  confirm the assumption D2/D3 build on, not to add new behavior.
- Built and inspected against real registry data: instantiate
  `K8sWorkload` from the actual `http` component
  (`registry/services/web/http/component.yaml`, once it has `image`) and
  from the actual `worker` component
  (`registry/services/gha/worker/component.yaml`) — no synthetic
  component data invented for this test.

## 📚 Read before starting this story

- [CDK8s — Getting started (Python)](https://cdk8s.io/docs/latest/getting-started/) — the construct model, `App`/`Chart`/`Construct`, and `cdk8s import`.
- [Kubernetes — Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/) — confirms `containers[].image` is required; the fact this story's blocker is built on.
- `registry-review.md`'s "Things that work well" section — the "workload-type abstraction... inheriting from `K8sWorkload`" line this story is directly implementing, and the "constructs committed to git" pattern this story adopts for `imports/`.
- CLAUDE.md's "Rules that override normal instincts here" §1 (simplicity) — read it again right before deciding whether `K8sWorkload` needs `abc.ABC`. It doesn't.
