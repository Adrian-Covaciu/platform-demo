# platform-demo

A personal, single-repo GitOps platform: engineers author schema-validated
YAML describing services, a Python synthesizer turns it into Kubernetes
manifests, and ArgoCD reconciles them onto a local cluster.

**Status: 🚧 implementation started.** Epic A (registry models, example
data, name-uniqueness checks) is done; nothing else yet — see
[Project status](#project-status) below.

## Why this exists

Two goals:

1. **Portfolio piece** demonstrating GitOps experience — schema-first
   config, a typed synthesizer, pull-based deployment via ArgoCD.
2. **Learning Python** in a platform-engineering context: typed data
   modeling, CLI design, and a real synthesis library — skills that don't
   come up in everyday scripting.

The design is a scaled-down, single-repo version of a two-repo GitOps
pattern reviewed in [`registry-review.md`](registry-review.md) — see that
file for the original architecture this project borrows ideas from.

## How it works (target design)

```
registry/*.yaml  --(validate)--> CDK8s synth
                 --> rendered/<retailer>/*.yaml --> git commit
                 --> ArgoCD (watches rendered/) --> local kind cluster
```

A `platform` CLI is the only entry point: `platform validate` checks the
registry, `platform generate` runs the full pipeline, `platform diff`
previews what would change before committing.

## Tech stack

| Concern | Choice | Why |
|---|---|---|
| Registry models & validation | [Pydantic](https://docs.pydantic.dev/) | typed, fail-fast on bad data |
| CLI | [Click](https://click.palletsprojects.com/) | `<verb> <noun>` commands |
| Manifest synthesis | [CDK8s](https://cdk8s.io/) (Python) | real typed objects, not templating |
| GitOps controller | [ArgoCD](https://argo-cd.readthedocs.io/) | pull-based sync from git |
| Local cluster | [kind](https://kind.sigs.k8s.io/) | zero-cost, reproducible |
| Ingress | [Traefik](https://traefik.io/) (via [Helm](https://helm.sh/)) | reach the ArgoCD/app UI from the local cluster |

Full rationale for each choice: [`docs/adr/`](docs/adr/).

## Repository layout

```
registry/    # YAML source of truth — one file per entity, one directory per parent
  retailers/
    <retailer>/retailer.yaml       # services: [<name>, ...] — references the catalog below
  services/                        # shared catalog, referenced by name from retailer.yaml
    <service>/service.yaml
      <component>/component.yaml   # every subdirectory except `shared/` is a component
      shared/<resource>.yaml       # this service's Resources, one file each
src/platform_generator/   # the installable Python package
  imports/k8s/                     # generated K8s typed classes (`cdk8s import k8s`), committed
  workload.py                      # K8sWorkload — shared CDK8s construct base for Api/Worker/Cronjob
tests/                # pytest suite
docs/                 # PRD, ADRs, epics, stories
```

`registry/retailers/acme/` is the worked example, referencing both
services in `registry/services/`; `registry/retailers/paris-lvh/` is a
second, bare retailer with no `services:` showing the layout holds more
than one client. See
[`CLAUDE.md`](CLAUDE.md)'s "Domain model" section for what each entity
means.

## Project docs

- [`docs/PRD.md`](docs/PRD.md) — goals, requirements, what's explicitly out of scope for v1.
- [`docs/adr/`](docs/adr/) — one decision record per major technical choice.
- [`docs/epics/README.md`](docs/epics/README.md) — the 7 epics and build order.
- [`docs/stories/`](docs/stories/) — one file per story: acceptance criteria + links to the specific documentation to read before starting it.

## Project status

Checked off as each epic's stories are completed. This list — and the
sections above — are kept up to date as the codebase grows, not written
once at the end.

- [x] [Epic A — Registry & Schema](docs/epics/epic-a-registry-schema.md)
- [ ] [Epic B — Typed Loader](docs/epics/epic-b-loader-merge.md)
- [ ] [Epic C — CLI](docs/epics/epic-c-cli.md)
- [ ] [Epic D — CDK8s Synthesizer](docs/epics/epic-d-synthesizer.md)
- [x] [Epic E — GitOps Wiring](docs/epics/epic-e-gitops-wiring.md)
- [ ] [Epic F — Docs/Demo](docs/epics/epic-f-docs-demo.md)

## Getting started

```
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest
```

This section grows as each epic lands; [`docs/epics/README.md`](docs/epics/README.md)
describes the build order until then.

### Bootstrapping a local cluster with ArgoCD

Requires Docker running locally, and `kind`, `kubectl`, and `helm` on
your `$PATH`:

```
./scripts/bootstrap-cluster.sh
```

This creates a `kind` cluster named `platform-demo`, installs Traefik
as its ingress controller, and installs ArgoCD, waiting until every
ArgoCD pod is `Ready` before exiting. It's safe to run more than once —
it skips creating the cluster or `argocd` namespace if either already
exists. Its last line of output prints the command to retrieve the
ArgoCD admin password.

### Pointing ArgoCD at this repo

Once the cluster and ArgoCD are up, apply the `Application` that tells
ArgoCD to watch this repo's rendered `acme` output:

```
kubectl apply -f argocd/application.yaml
```

This creates an `Application` named `acme` in the `argocd` namespace,
scoped to `rendered/k8s/acme` only (see `docs/stories/e4-argocd-application.md`
for why `paris-lvh` isn't included). With `syncPolicy.automated` set, it
syncs on its own within one cycle — no `argocd app sync` needed.

### Demo flow: registry edit to cluster

With the cluster bootstrapped and the `Application` applied, this is the
full FR6 loop, hands-on:

```
# 1. edit a registry file, e.g. add `replicas: 3` to
#    registry/services/web/http/component.yaml

# 2. preview what would change, before generating anything
.venv/bin/platform diff --retailer acme

# 3. render the change to rendered/k8s/acme/
.venv/bin/platform generate --retailer acme

# 4. commit and push both the registry edit and the regenerated file
git add registry/services/web/http/component.yaml rendered/k8s/acme/web.yaml
git commit -m "Scale acme web"
git push

# 5. ArgoCD polls git on its own default interval; force an immediate
#    check instead of waiting for it
kubectl patch application acme -n argocd --type merge \
  -p '{"metadata": {"annotations": {"argocd.argoproj.io/refresh": "hard"}}}'

# 6. confirm it synced on its own, no `argocd app sync` needed
kubectl get application acme -n argocd
kubectl get deployment -n web
```

`platform diff` and `platform generate` are documented in `docs/stories/e1-generate-command.md`
and `docs/stories/e2-diff-command.md`; the full walkthrough, including
reverting the change, is `docs/stories/e5-e2e-verification.md`.

### Regenerating `src/platform_generator/imports/`

The typed Kubernetes classes under `imports/` (`k8s.Container`, etc.) are
generated by CDK8s's own code generator, not hand-written, and are
committed to git rather than gitignored — no runtime codegen or network
access needed just to install the project. Regenerating them (e.g. after
bumping the target Kubernetes API version) requires the `cdk8s` CLI
(Node.js-based — `npm install -g cdk8s-cli`, or run via `npx`):

```
cdk8s import k8s --language python --output src/platform_generator/imports
```
