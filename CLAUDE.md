# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`platform-demo` is a personal, single-repo GitOps platform: a
Pydantic-validated YAML registry, synthesized by CDK8s into Kubernetes
manifests, reconciled onto a local `kind` cluster by ArgoCD. It exists to
(1) demonstrate GitOps experience as a portfolio piece, and (2) teach
Python in a platform-engineering context. Full context: `docs/PRD.md`.
Design rationale for every non-obvious choice: `docs/adr/`.

## Domain model

The registry hierarchy, top to bottom — get this wrong and every model/
loader/synth story built on it inherits the mistake:

- **`Retailer`** — a client. Conceptually maps to its own Kubernetes
  cluster *and* environment, deployed as a unit (this is the
  "platform-instance" referenced elsewhere as `--instance NAME` /
  `rendered/<instance>/`).
- **`Service`** — a part required for a retailer to operate. Has:
  - one or more **`Component`s** (never zero) — a `Component` *is* a
    workload: `workload_type` (`api` / `worker` / `cronjob`) lives here,
    not on `Service`.
  - zero or more **`Resource`s** (S3 buckets, ECR repos, etc.) — these
    live on `Service`, shared across its components, not on `Component`.

On disk, `Service`s live in a shared catalog (`registry/services/`),
separate from `registry/retailers/`. A `retailer.yaml` opts into a
service by listing its catalog name under `services:`; the same service
can be referenced by more than one retailer. A retailer with no
`services:` key has zero services (that's a valid, supported case).

Multiple environments per retailer (test/sandbox/prod) are explicitly
out of scope for this demo — see `docs/PRD.md`.

**Name uniqueness follows the same hierarchy, not a blanket rule** (A3):
a `Service` is a Kubernetes namespace, so its name only needs to be unique
*within* its retailer (namespaces are per-cluster); a `Resource` name
needs to be unique *across the whole registry* (cloud resource names like
S3 buckets are a global/account-wide namespace); `Component` names are
never checked — a component lives inside its service's namespace, so
reusing a name across services can't collide. Don't default to "unique
everywhere" for a new name field — derive the scope from where a real
collision could occur.

## Rules that override normal instincts here

1. **Simplicity beats robustness.** This is a learning project, not a
   production platform. When a story's acceptance criteria are satisfied
   by the plain, obvious implementation, stop there — don't add config
   knobs, extensibility hooks, or error handling for cases the acceptance
   criteria don't mention. If a simpler version of a story would still
   satisfy its acceptance criteria, write the simpler version.
2. **`README.md` is updated in the same change that outgrows it, not
   after.** Any change that adds a new module, CLI command, dependency, or
   manual setup step updates the matching section of `README.md` in the
   same commit. When unsure whether a change is README-worthy, update it.
3. **Acceptance criteria in `docs/epics/` and `docs/stories/` are a draft,
   not a contract.** If a criterion looks wrong or conflicts with a later
   design decision, flag it instead of building to the letter of the doc.
   Doesn't apply to `docs/adr/` — those are settled (see below).

## Where decisions already live

Tech stack and architecture decisions are pre-made in `docs/adr/` — don't
re-litigate them while implementing a story. Each file under
`docs/stories/` links the ADR(s) it implements and the specific docs to
read before starting it — read the story file itself before writing code
for it, not just its epic summary.

## Architecture (target shape, once built)

```
registry/*.yaml  --(Pydantic load + validate, ADR-0002)-->
                 --(CDK8s synth, ADR-0004)--> rendered/<instance>/*.yaml
                 --(git commit)--> ArgoCD watching rendered/ (ADR-0008) --> kind cluster
```

The `platform` CLI (Click, ADR-0005) is the only entry point into this
pipeline: `validate` (load only), `generate` (full pipeline), `diff`
(dry-run against committed `rendered/`).

Loader errors fail hard, full stop: a missing file, unparseable YAML,
duplicate name, or a file that parses but fails `Model.model_validate()`
all stop the run and surface the underlying error — there is no
warn-and-skip path. One bad entity anywhere in the registry fails the
whole load. See `docs/stories/b1-*.md`.

## Commands

```
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"   # one-time setup
```

No `platform` CLI yet (Epic C) — nothing else to invoke until then. Add
its commands here once it exists.
