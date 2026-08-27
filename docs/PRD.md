# PRD: platform-demo — a single-repo GitOps platform

## Summary

`platform-demo` is a personal, single-repo re-implementation of the
two-repo GitOps pattern reviewed in [`registry-review.md`](../registry-review.md)
(Kaluza's `platform-registry` + `kmi-deployments`). Engineers author
schema-validated YAML describing services and their infrastructure; a
Python synthesizer turns that YAML into Kubernetes manifests; ArgoCD
reconciles those manifests onto a local cluster. The whole loop — registry,
synthesizer, and rendered output — lives in one repo instead of two.

## Purpose & goals

1. **Portfolio piece** — a runnable, screen-recordable demonstration of
   GitOps experience: schema-first config, a typed synthesizer, and
   pull-based deployment via ArgoCD.
2. **Learning vehicle** — deliberately uses this project to build Python
   skill in a platform-engineering context: typed data modeling (Pydantic),
   CLI design (Click), and a real synthesis library (CDK8s) — skills that
   don't come up in typical scripting.

This PRD scopes a v1 that is complete and demoable end-to-end, deferring
several ideas noted in the review as explicit non-goals (see below) rather
than under-building the core loop.

## Audience

- The author (primary learner/builder).
- Anyone evaluating the author's platform-engineering experience (portfolio
  reviewers, interviewers) — the repo and its README/demo script are
  written with this reader in mind.

## Background: what this borrows from the review

Directly adopted "ideas worth stealing" from `registry-review.md`:

- Two-repo split with a rendered-artifact seam → **collapsed into one repo**,
  with a committed `rendered/` directory standing in for the S3 blob. Still
  gives a diffable snapshot and trivial rollback (`git revert`), without the
  operational overhead of a second repo a solo project doesn't need.
- Workload-type polymorphism (`api` / `worker` / `cronjob`, ...) as a bounded,
  schema-gated enum.
- Schema-first, with a typed loader (Pydantic) from day one rather than
  retrofitted, directly answering the review's #1 critique of
  `retailer_output.py`'s untyped, mutating-dict style.
- CDK8s over Helm/Kustomize for the synthesizer — real language, real types,
  real objects instead of string templates.
- Fail-hard loader errors: a missing referenced file, a duplicate name, or
  a schema validation error all raise immediately and stop the run. The
  reviewed system's "warn-and-skip on data quality" half was considered
  and dropped in favor of one uniform rule — simpler to implement and
  reason about, per this repo's simplicity-over-robustness bias.
- CLI shipped as `<verb> <noun>` (`platform generate service`, etc.) —
  discoverable and scriptable.

Directly adopted "improvements for a from-scratch version":

- Type the loader from day one (Pydantic); fail fast on missing files.
- Bake a `rendered_schema_version` into the rendered artifact.
- Enforce cross-file uniqueness (component/resource names) at schema/
  validation time, so a collision is caught on load.

## Functional requirements

### FR1 — YAML registry + schema validation
- Registry content is validated against Pydantic models at load time; the
  models are the single source of truth (no separately hand-maintained
  JSON Schema). The models encode this hierarchy:
  - A `Retailer` (a client — maps to its own Kubernetes cluster and
    environment, deployed as a unit) contains one or more `Service`s.
  - A `Service` (a part required for the retailer to operate) contains
    **at least one** `Component`, plus zero or more `Resource`s
    (S3 buckets, ECR repos, etc.) shared across that service's components.
  - A `Component` **is** a workload: `workload_type` is a bounded enum
    (start with `api`, `worker`, `cronjob`) and lives on `Component`, not
    `Service`.
- Name uniqueness is enforced by the loader at the scope where a real
  collision could occur, not uniformly: `Service` names are unique
  *within* a retailer (a service is a Kubernetes namespace, and namespaces
  are unique per-cluster); `Resource` names are unique *across the whole
  registry* (cloud resource names like S3 buckets are a global/account-
  wide namespace). `Component` names are not checked at all — a component
  lives inside its service's namespace, so cross-service reuse never
  collides.

### FR2 — Typed loader, fail-hard on any error
- Loader raises immediately (fails the CLI invocation) on: a referenced
  file that doesn't exist, a schema validation error, or a duplicate
  name. There is no warn-and-skip path — any loader error stops the
  whole run.

### FR3 — CLI (Click)
- `platform validate` — load and validate the registry, no output written.
- `platform generate [--instance NAME]` — run the full load → synth
  pipeline, writing `rendered/<instance>/*.yaml`.
- `platform diff [--instance NAME]` — generate to a temp path and diff
  against the committed `rendered/` output.
- `platform impact <path>` (stretch, may slip past v1) — given a changed
  registry file, list the rendered manifests that would change.

### FR4 — CDK8s synthesizer
- A `K8sWorkload` base construct with `Api`, `Worker`, `Cronjob` subclasses.
- Deterministic output: re-running `generate` with no registry changes
  produces byte-identical YAML (required for the `platform diff` story).

### FR5 — Rendered artifact
- Every generated manifest set is written under `rendered/<platform-
  instance>/` and stamped with a `rendered_schema_version` the loader
  checks on any future "load rendered output" path, rejecting unknown
  versions rather than guessing.

### FR6 — GitOps wiring
- A bootstrap script stands up a local `kind` cluster and installs ArgoCD.
- An ArgoCD `Application` manifest points at this repo's `rendered/`
  directory.
- Demo flow: edit a registry YAML file → `platform generate` → commit →
  ArgoCD detects the diff and syncs the cluster.

## Non-functional requirements

- **Determinism**: synth output must not depend on dict ordering, wall-
  clock time, or environment — required for `platform diff` to produce a
  meaningful, stable diff rather than spurious noise.
- **Traceability**: every non-trivial design choice is recorded as an ADR
  under `docs/adr/`, so the repo itself documents *why*, not just *what*.

## Out of scope for v1

These are explicitly deferred, not overlooked — each maps to a specific
item raised in `registry-review.md`:

- **Override / env-type merge tier.** Review critique #2 flags multi-tier
  as eventually necessary; this demo skips the override mechanism
  entirely — each retailer's registry is fully specified, with no merge
  step. Deferred to a future, separate synthesis repo (mirroring the
  reviewed two-repo pattern) rather than bolted onto this single-repo
  demo.
- **Multiple environments per retailer** (test/sandbox/prod, each a
  separate AWS account with its own cluster). v1 treats each `Retailer` as
  a single environment. Not a new mechanism when addressed later — it
  would reuse whatever override tier a future two-repo implementation
  adds, applied per retailer.
- **CDKTF / real cloud infrastructure provisioning.** v1 is Kubernetes-only;
  no AWS/GCP resources are created, so there's no cost or credential
  surface.
- **Secrets management** (SOPS, SSM/Secrets Manager references). Review
  critique #4; nothing in v1's scope is actually secret, so this is
  deferred rather than faked.
- **Datadog / observability generation.** Review notes this as coupled to
  the workload synthesizer in the original system; v1 has no observability
  story at all rather than a half-built one.
- **Okta / RBAC drift checking.** Review critique on
  `identity-grants-view.py` being a script, not a check; v1 has no RBAC
  modeling to drift-check in the first place.
- **Incremental/impact-aware regeneration.** Review critique #8 on
  `platform-registry`; at this repo's scale, regenerating everything on
  every change is fine.
- **`kmi impact` full implementation.** Listed as FR3 stretch; may ship as
  a stub or slip entirely without blocking the rest of v1.

## Success criteria

1. A fresh clone, following the README, can: create a kind cluster, install
   ArgoCD, run `platform generate`, commit, and watch the cluster converge —
   with no manual kubectl edits.
2. Editing one registry YAML field (e.g. a component's replica count) and
   re-running `platform generate` changes exactly the expected line(s) in
   `rendered/`, demonstrating the synth pipeline is deterministic.
3. `platform validate` succeeds on a valid registry and fails meaningfully
   (a clear message, not a stack trace) when a registry file is
   intentionally broken.
4. The repo's README + a short scripted walkthrough are usable, unmodified,
   as a portfolio demo.
