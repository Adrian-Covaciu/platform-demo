# Review: `platform-registry` + `kmi-deployments`

Context: reviewing Kaluza's two-repo GitOps platform to inform a personal
platform-engineering project where engineers author YAML templates
(schema-validated) that a synthesizer turns into cloud infrastructure.

## Architecture summary

Two-repo GitOps pattern:

1. **platform-registry** — YAML source of truth (schemas + retailer / service /
   component / resource YAMLs). A Python script (`retailer_output.py`) merges
   everything for a given platform-instance into a single
   `rendered_<instance>.json`, uploaded to S3.
2. **kmi-deployments** — CDK8s + CDKTF (Python) synthesizer. Downloads rendered
   JSON, produces Terraform + K8s manifests, commits via GitOps (ArgoCD). CLI is
   `kmi generate ...` (Click), organized as commands → generators →
   resources/{workload}.

Override model: base YAML + a **single** environment-config override tier
(`environment-config/<platform-instance>/<env-type>/*.yaml`) — deep-merged.

## Things that work well

- **Separation of concerns.** Registry = declarative intent; deployments =
  synthesis. Registry PRs are readable by app devs; synthesis complexity is hidden.
- **Schemas as contract.** JSON Schema (draft-07) for
  `service` / `component` / `resources` / `container-config`, validated in CI.
  Gives app engineers autocomplete via `.idea/jsonSchemas.xml`.
- **Workload-type abstraction** (`api`, `worker`, `cronjob`, `agent`, `s3-proxy`,
  `kb-ingester`, `mcp-gateway/server`). Each has its own CDK8s class inheriting
  from `K8sWorkload` / `K8sApiV2`. Adding a new type is a bounded change.
- **CLAUDE.md discipline** in kmi-deployments (thin commands, fail-fast on
  invocation errors, warn+skip on bad registry data, Cilium ingress/egress pair
  every workload). Very clear rules that keep CI green on partial bad data.
- **CDK8s/CDKTF constructs** committed to `src/kmi/imports/` — pinned generated
  code, regenerable via `cdktf get` / `cdk8s import`. No runtime chart download.
- **Rendered JSON artifact** as the seam between repos — decouples release
  cadence, makes rollback trivial (revert the JSON), gives a diffable snapshot.
- **Registry model classes** (`Retailer`, `Service`, `Component`, `Environment`,
  `Resource`) centralize override resolution — synth code stays declarative.
- **Access + IAM baked into the schema** (`interface.identity.defines.roles` /
  `.grants`) — service-to-service AuthZ is declared next to the API, not managed
  elsewhere.
- **Datadog Software Catalog, monitors, dashboards** generated from the same
  source — observability isn't a bolt-on.

## Things that could change

### platform-registry

1. **`retailer_output.py` is one ~400-line procedural file with mutating dicts.**
   No models, no types, string paths everywhere, `sys.stderr` prints instead of
   `logger`, commented-out chart code left in. Very brittle:
   - Silent `continue` on missing files (WARN then skip). One misspelled
     resource → resource never provisioned, no CI failure.
   - `_ENVIRONMENTS` is a hardcoded module-level list.
   - `service.get("parent", "")` used as a path segment — empty parent becomes
     `//` in paths; works on POSIX but is fragile.

   → Refactor into a typed loader (`pydantic` / `dataclass`) mirroring the JSON
   schemas. Fail hard on any referenced-but-missing file (same "invocation
   error" rule kmi-deployments already applies).

2. **Override system is only one tier deep.** Docs state this explicitly. Real
   orgs need at least: default → platform-instance → env-type → env-instance.
   Also useful: retailer-tier defaults (e.g. all `prod` envs across all
   retailers share DR settings). Current single tier forces per-instance /
   per-env files that repeat identical content.

3. **Deep merge of arrays is dangerous.** With YAML merge, arrays typically
   replace, but there's no explicit merge policy documented. Adding one item to
   an `env` array in a base file plus one item in an override → hard to reason
   about. Adopt a documented strategy (JSON-Patch, or per-key merge annotations
   like `!merge` / `!replace`).

4. **Secrets in plain YAML** (Aiven CA, RDS CA blocks in
   `environments/prod.yaml`). CAs aren't secret, but the pattern invites real
   secrets to be pasted next. Move to SSM / Secrets Manager references or
   SOPS-encrypted files with age keys.

5. **Naming collisions guarded by convention, not code.** CLAUDE.md says
   "Component names are unique across the entire registry" but only a test
   (`test_dupe_construct_check`) enforces it. Should be schema-level (an `$id`
   scan or pre-commit).

6. **`v1` / `v2` component version enum** without a documented migration path —
   easy to accumulate `v1` forever.

7. **Legacy code exists.** `retailer_output_split.py` is marked "dark launch,
   experimental", and both `retailer_output.py` and `all_services_output.py`
   re-implement similar traversal. Consolidate into one loader; make
   split-vs-monolith an output flag.

8. **CI incremental generation.** Every merge that touches `services/`
   regenerates every retailer's rendered JSON. On a big org this is wasteful.
   Compute the affected platform-instance set from the diff.

### kmi-deployments

1. **Two-repo coupling via S3 blob.** Works, but the failure mode is silent — a
   broken rendered JSON syncs, then kmi-deployments fails synthesis. Add a
   schema pin (`rendered_schema_version`) inside the JSON and reject unknown
   versions at load time.

2. **Contract testing does full `ap2` regen inside `behave` `environment.py`.**
   Slow, ties test runtime to network availability (`GH_TOKEN` for repo id
   resolution, Helm auth). Snapshot the golden `ap2` `rendered.json` into the
   repo and diff-test. Real full-generation runs can be a separate nightly job.

3. **`DataTerraformRemoteStateS3` → SSM Parameter Store** rule is documented in
   CLAUDE.md but not enforced. A lint step / grep in CI would prevent
   regression.

4. **Manual `phase init` steps** documented in README for adding a new Terraform
   provider (secret creation is manual). Classic gap — either fully automate or
   generate a change-plan issue.

5. **`src/kmi/imports/` in git.** Pragmatic — reproducible builds, offline
   synthesis — but a massive diff on every provider bump. Consider a lockfile +
   generation on CI with a cache, keeping only the lockfile in git.

6. **Fluent-bit / DataDog / logs path** is coupled with the workload
   synthesizer. Swapping DataDog for OpenTelemetry would touch every workload
   class. Extract an `Observability` mixin / provider.

7. **The registry mixes runtime concerns and infra concerns** (e.g. Kafka
   producer resources are declared, then egress interface types are also
   declared). In practice the synth infers one from the other. Declare once and
   derive.

### Cross-cutting

- **The output artifact is a giant JSON file per retailer.** Fine at current
  scale, but `rendered_ap2.json` will grow unbounded. Consider splitting per
  service (registry already has `retailer_output_split.py` as prototype) so
  downstream generation is naturally parallel.
- **Documentation excellent for humans** (mkdocs site + CLAUDE.md), but
  machine-checkable contract only via JSON schema. A CUE / OpenAPI-style schema
  could give both stronger validation AND generate the language types used in
  kmi-deployments (registry models are currently hand-written).
- **No blast-radius / impact CLI.** "If I change this component's namespace,
  what infra changes?" is answered today by generating and diffing. A
  `kmi impact <path>` command would speed reviews significantly.
- **RBAC in the schema (`access.admin/qa/readonly`) is Okta-group based** —
  great for onboarding, but there's no drift check between the registry
  declaration and actual Okta state (`identity-grants-view.py` exists but is a
  script, not a check).

## Ideas worth stealing

1. **Two-repo split with a rendered-artifact seam** — the single most valuable
   pattern here. Keep the "developer-facing YAML" repo and the "synthesis" repo
   separate.
2. **Workload-type polymorphism.** `workload_type: api|worker|cronjob|...` is a
   clean UX for app teams. Bounded set, gated by schema enum.
3. **Single override tier** as an MVP is fine — avoid Kustomize-style N-level
   rabbit holes. Add tiers only when concrete duplication justifies it.
4. **Schema-first.** JSON Schema draft-07 works, but if starting fresh, consider
   CUE or Pydantic-generated OpenAPI — one source, both validation and codegen.
5. **CDK8s + CDKTF over Helm + Terraform HCL.** Real language, real types,
   testable synth.
6. **Warn-and-skip on data quality, raise on invocation.** Explicit split in
   CLAUDE.md is worth borrowing verbatim.
7. **Ship the CLI as `<verb> <noun>`** (`kmi generate service resources -p ap2`).
   Discoverable, scriptable, per-service filtering built in.

## Improvements for a from-scratch version

- Type the loader from day one (Pydantic). Fail fast on missing files.
- Bake `rendered_schema_version` into the artifact.
- Include a snapshot / golden test in the synthesis repo instead of live regen.
- Provide `impact` and `diff` commands as first-class citizens.
- Adopt SOPS or SSM-refs for anything remotely secret-shaped.
- Enforce cross-file uniqueness (component names, resource names) at schema
  time, not test time.
- Pick a documented array-merge policy.
