# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`platform-demo` is a personal, single-repo GitOps platform: a
Pydantic-validated YAML registry, synthesized by CDK8s into Kubernetes
manifests, reconciled onto a local `kind` cluster by ArgoCD. It exists to
(1) demonstrate GitOps experience as a portfolio piece, and (2) teach
Python in a platform-engineering context. Full context: `docs/PRD.md`.
Design rationale for every non-obvious choice: `docs/adr/`.

**Current state:** planning complete (`docs/PRD.md`, `docs/adr/`,
`docs/epics/`, `docs/stories/`). Epic A is done: Pydantic registry models
(`src/platform_generator/models.py`, A1), the example registry
(`registry/`, A2), and `src/platform_generator/schema.py` (A3 — walks the
registry and enforces name uniqueness at the scope where collisions can
occur; see "Domain model" below). The loader does **not** yet fail hard
on missing files or warn-skip bad data — that's Epic B. CLI (Epic C) and
synthesizer (Epic D) don't exist yet. Build order is epic-by-epic per
`docs/epics/README.md` (A → B → C/D → E → F).

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

In a production-ready version a single retailer could have multiple
environments (test/sandbox/prod), each its own AWS account with its own
cluster — out of scope for this demo (see `docs/PRD.md`). When that's
picked up, it would need a base + env-type override tier — but that
belongs to a future, separate synthesis repo (mirroring the reviewed
two-repo pattern), not this one; it's explicitly out of scope here (see
`docs/PRD.md`).

**Name uniqueness follows the same hierarchy, not a blanket rule** (A3):
a `Service` is a Kubernetes namespace, so its name only needs to be unique
*within* its retailer (namespaces are per-cluster); a `Resource` name
needs to be unique *across the whole registry* (cloud resource names like
S3 buckets are a global/account-wide namespace); `Component` names are
never checked — a component lives inside its service's namespace, so
reusing a name across services can't collide. Don't default to "unique
everywhere" for a new name field — derive the scope from where a real
collision could occur.

## Two rules that override normal instincts here

1. **Simplicity beats robustness.** This is a learning project, not a
   production platform. When a story's acceptance criteria are satisfied
   by the plain, obvious implementation, stop there — don't add config
   knobs, extensibility hooks, or error handling for cases the acceptance
   criteria don't mention. Prefer the stdlib and the smallest slice of a
   library's API that does the job. Code should read as something a
   learner would understand a year from now, not a demonstration of
   Python's expressiveness. If a simpler version of a story would still
   satisfy its acceptance criteria, write the simpler version.
2. **`README.md` is updated in the same change that outgrows it, not
   after.** Any change that adds a new module, CLI command, dependency, or
   manual setup step updates the matching section of `README.md` in the
   same commit — "Getting started," "Repository layout," or the epic
   progress checklist. When an epic's stories are all done, check it off
   in the README. When unsure whether a change is README-worthy, update
   it — a stale README costs more than an over-eager edit here.

## Where decisions already live

Tech stack and architecture decisions are pre-made in `docs/adr/` — don't
re-litigate them while implementing a story:

- `0001` single repo, `rendered/` as the seam (no S3, no second repo)
- `0002` Pydantic for registry models
- `0004` CDK8s (Python) synthesizer · `0005` Click CLI
  (`platform <verb> <noun>`)
- `0006` `rendered_schema_version` pin
- `0008` ArgoCD on local `kind`, no cloud account

Each file under `docs/stories/` links the ADR(s) it implements and the
specific docs to read before starting it — read the story file itself
before writing code for it, not just its epic summary.

## Architecture (target shape, once built)

```
registry/*.yaml  --(Pydantic load + validate, ADR-0002)-->
                 --(CDK8s synth, ADR-0004)--> rendered/<instance>/*.yaml
                 --(git commit)--> ArgoCD watching rendered/ (ADR-0008) --> kind cluster
```

The `platform` CLI (Click, ADR-0005) is the only entry point into this
pipeline: `validate` (load only), `generate` (full pipeline), `diff`
(dry-run against committed `rendered/`).

Loader errors follow one rule throughout: a bad *invocation* (missing
file, duplicate name, unparseable YAML) fails hard and stops the run; bad
*data* on an otherwise-valid entity (an optional field absent) warns via
`logging` and skips just that entity. See `docs/stories/b1-*.md` and
`b2-*.md`.

## Commands

```
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"   # one-time setup
```

No `platform` CLI yet (Epic C) — nothing else to invoke until then. Add
its commands here once it exists.
