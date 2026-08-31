# D5. Write rendered output with the schema-version header

**Goal:** write the orchestration function this whole epic has been
building toward — call it `generate_retailer(retailer: Retailer) -> None`
in `src/platform_generator/generator.py` — that takes one validated
`Retailer`, builds a CDK8s `App`/`Chart` per service, dispatches each
`Component` to `Api`/`Worker`/`Cronjob` (D2/D3) by `workload_type`, and
writes the result to `rendered/<retailer.name>/*.yaml`, each file stamped
with a `rendered_schema_version`. This is the story where file I/O and a
version-compatibility contract (a rule for what happens when old code
reads new data, or vice versa) become real concerns for the first time
in this epic — everything before this was in-memory constructs.

**Depends on:** [D1](d1-k8sworkload-base.md), [D2](d2-api-worker-subclasses.md),
[D3](d3-cronjob-subclass.md) — this story's whole job is wiring those
three classes together; it adds no new construct of its own.
[D4](d4-service-namespace.md) — `Api`/`Worker`/`Cronjob` now take a
`namespace` argument, and each service's `Chart` needs one `KubeNamespace`
object alongside its workloads; this story is what actually calls into
D4's namespace plumbing when it builds each chart, it doesn't add any new
namespace logic of its own. [Epic B](../epics/epic-b-loader-merge.md) —
`load_retailers()` is what supplies the `Retailer` this function takes.
`src/platform_generator/generator.py` is currently a scratch file; this
story is the first to put the real orchestration in it.

**Related ADR:** ADR-0006 — `rendered_schema_version` pin — **this file
does not exist.** See the flag below.

## ⚠️ ADR-0006 is missing

Same underlying gap as D1's ADR-0004 flag, one story later: PRD FR5 says
every rendered manifest set is "stamped with a `rendered_schema_version`
the loader checks on any future 'load rendered output' path, rejecting
unknown versions rather than guessing" — but nothing has ever settled
what that stamp actually looks like (a plain integer? a string? where
does it live — in each file, or once per instance?) or where the
"reject unknown versions" check lives. `registry-review.md`'s own
"Ideas worth stealing" section is where this idea came from in the first
place (a `rendered_schema_version` pin inside the rendered JSON, to make
a broken/incompatible artifact fail loudly instead of syncing silently)
— but that note describes *why* the pin exists, not the concrete format.
The judgment calls below fill that gap for now.

**Judgment calls made in its absence:**

1. **Format: a plain integer, starting at `1`.** Not semver
   (`"1.0.0"`). Semver's major/minor/patch distinction buys nothing
   here — this repo doesn't (yet) have a concept of "backwards-compatible
   rendered-output change," and FR5's own wording is "rejecting unknown
   versions," which is a flat equality check, not a range check. Start
   with the smallest thing that satisfies that.
2. **Placement: a one-line comment at the top of every generated
   file** — `# rendered_schema_version: 1` — not a separate sidecar file
   (e.g. `rendered/<instance>/.rendered_schema_version`) and not an
   annotation baked into every individual K8s object's metadata. A
   sidecar file was considered and rejected: it's an extra file per
   instance that isn't itself a Kubernetes manifest, and Epic E's ArgoCD
   `Application` will need to point at `rendered/<instance>/` as a
   directory of manifests to apply — a stray non-manifest file sitting
   in that same directory is exactly the kind of thing that epic would
   otherwise have to special-case around. A YAML comment, by contrast,
   is invisible to any YAML parser (comments are stripped on load) and
   costs nothing to add once you're already writing the file's text
   yourself (see the next judgment call). The tradeoff: nothing
   currently *parses* this comment back out programmatically — see
   point 4.
3. **How the file actually gets written.** CDK8s's own `App(outdir=...)`
   + `app.synth()` is the documented way to get files onto disk, but
   nothing here has verified that its default file naming lines up with
   FR5's literal `rendered/<instance>/*.yaml` requirement (CDK8s may
   name files after each chart's construct ID rather than the service
   name, or add its own prefix). Do this in two steps, in order, and
   don't skip the first one just because the second is described here:
   - Try `App(outdir=f"rendered/{retailer.name}")`, one `Chart` per
     service, `app.synth()`. Look at what actually landed on disk.
   - If the filenames don't already read as `<service-name>.yaml`,
     rename them (or write the manifests' own YAML text directly,
     bypassing `app.synth()`'s writer) rather than fighting CDK8s's
     naming convention to force it into this repo's layout. Either way,
     the version-stamp comment is prepended to each file's text as a
     final step, after CDK8s has produced it — this is a plain
     read-the-file / prepend-a-line / write-it-back operation, not a
     CDK8s feature.
4. **The loader-side "reject unknown versions" check is out of scope for
   this story.** FR5 describes it as something to happen "on any future
   'load rendered output' path" — and nothing in this epic reads
   `rendered/` back into Python models; E1 only *writes* there, and E2
   only text-diffs two directories of files, it never parses either side
   into a `Retailer`. Building a version-check function with no caller
   yet would be exactly the "extensibility hook for a problem that
   doesn't exist yet" CLAUDE.md's simplicity rule warns against. Stamp
   the version now; leave the check for whichever future story actually
   needs to load rendered output back in.

## The concept: dispatch by enum, not a plugin registry

`generate_retailer` needs to turn `component.workload_type` into the
right class. The whole type space is three fixed values
(`WorkloadType.API`, `.WORKER`, `.CRONJOB`), known today and not
expected to grow dynamically — so a plain dict or `if`/`elif` chain is
the entire mechanism needed:

```python
WORKLOAD_CLASSES = {
    WorkloadType.API: Api,
    WorkloadType.WORKER: Worker,
    WorkloadType.CRONJOB: Cronjob,
}
WORKLOAD_CLASSES[component.workload_type](
    chart, component.name, component=component, namespace=service.name,
)
```

Per D4, each chart also gets one `KubeNamespace` built alongside its
workloads, using the same `service.name` passed as `namespace=` above.

A learner's instinct at this point is often to reach for a decorator-based
registry (`@register_workload("api")`) so "adding a new workload type
later is easier." Don't — that's solving a problem this repo doesn't
have. Adding a fourth workload type today means editing this dict *and*
the `WorkloadType` enum *and* writing a new construct class; a registry
saves you touching one of those three files, at the cost of a layer of
indirection that makes this exact function harder to read for a junior
seeing it for the first time. Three fixed cases is a dict, not a
framework.

## Traps specific to this story

- **`yaml.safe_dump`'s key ordering.** If any part of this story ends up
  hand-writing YAML (rather than only using CDK8s's own writer), decide
  once, deliberately, whether to pass `sort_keys=False` (preserve the
  order keys were set on the dict — usually more readable, e.g.
  `apiVersion`/`kind`/`metadata`/`spec` in that order) or leave the
  default `sort_keys=True` (alphabetical). Either is deterministic run
  to run — Python dicts preserve insertion order, so this isn't a
  correctness risk — but pick one and use it consistently across every
  file this story writes, rather than letting it vary by which code path
  happened to write which file.
- **Chart granularity is a design decision, not a detail.** This story
  treats one `Chart` per `Service` (so one output file per service,
  which lines up with `Service` already being a Kubernetes namespace
  per CLAUDE.md's domain model) as the unit CDK8s synthesizes. If a
  future ADR-0004 lands on a different granularity (per-component
  files, or one chart per retailer), this story's file-naming logic is
  exactly what needs revisiting.
- **Determinism end to end.** This is the first story that can actually
  prove FR4's "byte-identical on re-run" requirement, because it's the
  first one writing real files rather than in-memory constructs — make
  the "run twice, diff nothing" check a real acceptance criterion here,
  not just an assertion in prose.

## Acceptance criteria

- `generate_retailer(retailer)` exists in `src/platform_generator/generator.py`
  and, called with the real `acme` retailer (via
  `next(r for r in load_retailers() if r.name == "acme")`), writes
  `rendered/acme/web.yaml` and `rendered/acme/gha.yaml`.
- `rendered/acme/web.yaml` contains the `KubeDeployment` + `KubeService`
  for `http` (D2's `Api`), plus a `KubeNamespace` named `web` (D4);
  `rendered/acme/gha.yaml` contains the `KubeDeployment` for `worker`
  (D2's `Worker`) and the `KubeCronJob` for `nightly-report` (D3's
  `Cronjob`, once that component exists per D3), plus a `KubeNamespace`
  named `gha`. Every namespaced object in each file has `metadata.namespace`
  set to that file's service name, per D4.
- Every file under `rendered/acme/` begins with
  `# rendered_schema_version: 1`.
- Calling `generate_retailer` twice in a row with no registry changes in
  between produces byte-identical files both times — check this with an
  actual byte comparison (or `git status` showing no changes the second
  time), not just "it looked the same."
- Editing only `registry/services/web/http/component.yaml`'s `replicas`
  and calling `generate_retailer` again changes exactly the
  `replicas:` line inside `rendered/acme/web.yaml` and no other line in
  any file — the full, file-on-disk version of PRD success criterion 2
  (D2 already proved this at the in-memory construct level; this is the
  same proof one layer further out).
- No function anywhere in this story reads `rendered/` back into a
  `Retailer` or checks `rendered_schema_version` against a known set —
  confirm this is absent, per judgment call 4 above, rather than
  assuming it should exist and building it.

## 📚 Read before starting this story

- [CDK8s — Getting started (Python)](https://cdk8s.io/docs/latest/getting-started/) — `App`, `Chart`, and what `app.synth()` actually writes; verify the file-naming behavior empirically as described above rather than trusting this doc's examples to match this repo's layout exactly.
- [Python — `open()` / file objects](https://docs.python.org/3/library/functions.html#open) and [`pathlib`](https://docs.python.org/3/library/pathlib.html) — for the prepend-a-line step; `pathlib.Path.write_text`/`read_text` is enough, no need for anything heavier.
- `registry-review.md`'s "kmi-deployments" section, point 1 — the original `rendered_schema_version` idea and the failure mode (a broken artifact syncing silently) it exists to prevent.
- [D1](d1-k8sworkload-base.md)'s "no random construct IDs" trap and [D2](d2-api-worker-subclasses.md)'s determinism note — re-read both before writing the "run twice, diff nothing" test; this story is where that promise finally gets checked against real files.
