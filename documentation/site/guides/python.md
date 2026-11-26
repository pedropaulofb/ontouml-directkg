# Python guide

This guide describes **specified integration capabilities** and a bounded verified example. The [generated API reference](../reference/api/index.md) renders actual public objects and docstrings. The example below was executed with Python 3.12.14 against development revision `25bf7b2259331d0c439fe0f79f826bae0218b8f7`; wider contract coverage remains distinct from that execution.

## Conversion and configuration

Every Python transformation requires a concrete [OntoUML JSON input file](../reference/input.md#source-file-input) identified by a file path (`str` or `os.PathLike`), regardless of provenance mode. Parsed JSON objects, dictionaries, and other fileless representations are not accepted substitutes. Passing a non-path Python source-input argument outside `str | os.PathLike` must be rejected **before conversion starts** as a configuration error (signaled programmatically; producing no conversion start, transformation outcome, ontology, or conversion-diagnostics report). Internal processing in memory and the existing output-graph and diagnostic capabilities remain available under their separate contracts.

Python and CLI must expose every established ontology-transformation control with equivalent selectable behavior, identical defaults, and the same transformation effects. An equivalent effective configuration on the same supported input invokes the same accepted rules. This does not promise identical execution provenance from separate runs.

Use [Controls](../reference/controls.md#established-controls) as the canonical inventory, including metadata and provenance. Python need not copy CLI flag spelling, representation, or negative-flag polarity. The exception is the specifically prescribed parameter name `relation_labels`, with accepted values `"source-only"` and `"generated"`, default `"source-only"`. This requirement does not establish the containing function's name or signature.

An equivalent optional Python control must accept a caller-supplied [ontology version IRI](../reference/output.md#optional-ontology-version-iri), with the same emission and absence behavior as the CLI control. Its parameter name is not prescribed by the specification; the [inspected conversion signature](../reference/controls.md#interface-parity) declares this optional control.

An integrator prepares a [supported JSON file](../reference/input.md), supplies its path, chooses effective settings, inspects the outcome and diagnostics, and consumes only eligible ontology output. The specification leaves most API names and representations open; the generated reference describes the implementation's actual choices.

After the [source installation](../getting-started.md#installation-status), run this example from the repository root:

```python
from ontouml_directkg import convert

result = convert(
    "documentation/site/examples/files/classes-and-attributes.json",
    base_iri="https://example.org/directkg-example#",
    iri_strategy="id",
    language="pt-BR",
    provenance="none",
)
print(result.outcome)
if result.ontology is not None:
    delivery = result.deliver("python-example.ttl")
    for failure in delivery.failures:
        print(failure.destination, failure.reason)
for diagnostic in result.diagnostics:
    print(diagnostic.severity, diagnostic.message)
result.export_diagnostics("python-example-diagnostics.json")
```

The verified example completed, delivered a 20-triple ontology and exported two INFO diagnostics. It uses the same configuration as [Getting started](../getting-started.md#inspecting-the-result). Diagnostics export occurs after delivery so any delivery diagnostics are included. An aborted result has no eligible ontology; diagnostics remain accessible. This small successful run does not verify every recovery, delivery-failure or provenance path. The exception boundaries below remain applicable.

**Pre-conversion configuration validation** applies uniformly before conversion starts across all invalid transformation controls—including `base_iri`, `ontology_version_iri`, enum choices and types, boolean flags, `language` (single valid lexical tag under `DK-LBL-02`), and `metadata_file` (path type `str | os.PathLike` and explicit filename `metadata.yaml`)—as well as non-path `source` arguments outside `str | os.PathLike`. Every rejection must be signaled programmatically, independently of input policy (`strict`, `tolerant`, `best-effort`), without starting conversion or producing an ontology, sidecar, diagnostics file, transformation outcome, or conversion-diagnostics report. No particular exception class is selected by the specification. This remains distinct from source-file read, parse, or root-structure failures on a valid `source` path (`UNPROCESSABLE_DOCUMENT`) and file-existence, read, YAML-parse, or content failures on an explicit `metadata.yaml` path (`DK-GEN-09`). See [Base and ontology IRIs](../reference/identifiers.md#base-and-ontology-iris) and the version-IRI boundary linked above.

For `language`, lexical acceptance does not establish BCP 47 grammatical well-formedness. Supplying a grammatically well-formed and semantically correct override is the caller's responsibility; see [Language resolution](../reference/text.md#language-resolution).

**Implementation status.** *Historical observation:* at [specification registration revision `ade0de86886c9da316dfbcf2ea5e6d4a3a3447cc`](https://github.com/pedropaulofb/ontouml-directkg/blob/ade0de86886c9da316dfbcf2ea5e6d4a3a3447cc/src/ontouml_directkg/conversion.py#L101-L135), `convert()` validated transformation controls pre-conversion with `ConfigurationError` but passed `source` to `Path(source)` inside the conversion `try:` block rather than rejecting non-path values outside `str | os.PathLike` before conversion started. *Current implementation:* RD-04 Decision 2 was implemented in [revision `b787d07d33a6c96c06b65a84013dd8b96cfc9edb`](https://github.com/pedropaulofb/ontouml-directkg/commit/b787d07d33a6c96c06b65a84013dd8b96cfc9edb); at [revision `8cafc3516fad3dff9aadd23c19061a497dc2f87a`](https://github.com/pedropaulofb/ontouml-directkg/blob/8cafc3516fad3dff9aadd23c19061a497dc2f87a/src/ontouml_directkg/conversion.py#L102-L142), `convert()` validates `source` (`str | os.PathLike` and `os.fspath`) alongside transformation controls with `ConfigurationError` before entering the conversion `try:` block (lines 134–142). Focused Python pre-conversion validation tests (including `None`, `int`, and `dict` `source` values) pass at this revision; this does not establish complete RD-04 runtime conformance, and separate public API exception-contract documentation remains outside this note.

**Conversion, serialization, and delivery boundaries.** The required ontology-serialization capability uses RDF 1.1 Turtle. Prefix names, blank-node labels, statement order, and other textual layout are not fixed; compare the accepted graph rather than assuming byte-identical serializations. See [Graph and text stability](../reference/output.md#graph-and-text-stability).

- Conversion and direct programmatic serialization operations (such as `convert()`, `to_turtle()`, and `to_provenance_turtle()`) write **no files**.
- If a direct programmatic serialization error occurs, it must signal failure programmatically **without mutating `diagnostics`, `outcome`, or `ontology`**.
- Explicit delivery (such as `deliver()`) writes complete ontology and sidecar bytes safely without leaving partial artifacts at the destination, and writes no files and adds no diagnostics when invoked on an already-aborted result (`outcome == "aborted"`).

## Diagnostics and aborts

For each conversion that runs, expose exactly one transformation outcome: `completed`, `completed-with-errors`, or `aborted`. Their conditions and output eligibility are defined in [Outcomes and output eligibility](../reference/diagnostics.md#outcomes-and-output-eligibility). JSON exports store this value in the required `outcome` member; Python result types and representations remain unspecified. Pre-conversion configuration rejections (and residual CLI exit code `7`) establish no fourth transformation outcome.

Structured access must retain **every diagnostic actually produced**, including severity, meaning, and applicable source information. It remains available after a policy-driven abort, including duplicate-ID abortion, and after a reportable unexpected internal failure during transformation (once conversion starts through result construction) or required-provenance construction failure (including late `sidecar` output-provenance construction inside explicit delivery). Do not derive success solely from a quiet console or treat every ERROR as proof that conversion aborted.

!!! note "Output eligibility depends on the outcome"

    An aborted conversion must not deliver its accumulated ontology through Python. A completed `best-effort` conversion can deliver permitted partial output despite retained ERROR diagnostics.

When an [unexpected internal failure stops transformation](../reference/diagnostics.md#unexpected-internal-failures-during-transformation) (once conversion starts through result construction) and DirectKG can report it, Python must expose `aborted`, the preceding diagnostics, and the `INTERNAL_TRANSFORMATION_FAILURE` ERROR, with stage and cause when available. The accumulated ontology graph is unavailable through Python, and the aborted run delivers neither an ontology file nor a provenance sidecar. The specification does not prescribe whether the API communicates these outcomes through return values or exceptions.

Accessing diagnostics or exporting them must not create additional transformation diagnostics, change their severity/meaning, recovery, outcome, or ontology-output eligibility. Console thresholds affect presentation only; they do not filter Python structured access. Intentional silence remains silent. The shared JSON contract fixes report fields and types. Every produced diagnostic must populate `code` as a nonempty string; **only** the [eight stable diagnostic identifiers](../reference/diagnostics.md#stable-first-release-diagnostic-core) carry a normative first-release stability guarantee for their strings and condition meanings, while non-core identifiers remain implementation-defined / unguaranteed in the first release (without a separate v1 catalogue) and must not suppress required reporting.

Python must signal failure programmatically and keep produced diagnostics accessible for any post-conversion main-ontology file delivery failure occurring before the main ontology write completes—including destination path resolution/handling, Turtle serialization, UTF-8 encoding, file creation/writing/replacement, or an unexpected runtime error during that ontology-delivery step (excluding `sidecar` output-provenance construction failures before writing, which abort under `REQUIRED_PROVENANCE`). This failure produces `ONTOLOGY_DELIVERY` ERROR while preserving the established outcome (`completed` or `completed-with-errors`), generated graph, and requested provenance mode.

When serialization or encoding fails, Python must also retain access to the conversion result, including the generated graph. Any existing ontology and sidecar files stay intact, neither artifact is delivered for that request, no partial ontology file is left presented as valid, and an older ontology is reported as not updated. The [delivery contract and implementation status](cli.md#reporting-and-retained-results) describe the accepted behavior and inspected development revision.

## Separate exports

### Diagnostic JSON

Python conversion must **not automatically write a diagnostics file**. Provide a separate operation, explicitly called by the application, to export produced diagnostics to its chosen JSON destination. This operation uses the same [shared JSON report contract](../reference/diagnostics.md#shared-json-report-contract) as the CLI: required fields and types, empty/null context, compatible extensions, the exposed outcome, and a complete mirror of produced diagnostics.

The CLI's `--diagnostics-file` spelling does not prescribe a Python parameter or operation name. Persistent diagnostics writing is separate from transformation-control parity; applications may inspect diagnostics without saving them.

If that separate export operation fails to serialize, create, or write its requested file (including I/O errors and unexpected export/serialization errors), signal failure programmatically while retaining caller access to transformation diagnostics and outcome. Export failure must not change their severities, transformation outcome, or ontology/sidecar delivery eligibility, and must not conceal a prior abort. No exception/result type, file-writing internals, or recovery from an unwritable destination is selected.

### Provenance graph and file output

Python must provide semantically equivalent metadata-file and provenance controls, including provenance default `embedded`. Separate provenance must be available programmatically **as a graph**, with explicit serialization for file output. Direct `to_provenance_turtle()` (and equivalent serialization) writes no files and signals direct serialization errors without mutating `diagnostics`, `outcome`, or `ontology`. This graph capability does not select a concrete Python graph class, method, or return-object layout.

Automatic sidecar writing requires a concrete ontology output path; do not invent one for an in-memory graph or stdout. Embedded provenance excludes concrete output-file information, including from its configuration record. See [Provenance modes](metadata-and-provenance.md#provenance-modes) and [Artifacts and digests](metadata-and-provenance.md#artifacts-and-digests).

Failure to construct required provenance in an enabled mode—including both conversion-time provenance construction and post-conversion `sidecar` output-provenance construction inside explicit delivery (`deliver()`) before writing any ontology or sidecar file—produces `REQUIRED_PROVENANCE` ERROR and aborts before writing under every input policy, leaving any existing ontology and sidecar files untouched while retaining programmatic diagnostic access. In contrast, once main ontology writing succeeds, failure to prepare, serialize, encode, create, or write the sidecar (including an unexpected runtime error in that stage) produces `SIDECAR_DELIVERY` ERROR, leaves successfully written ontology output available, leaves any existing sidecar untouched (reporting that any older sidecar was not updated), preserves the established outcome, and must be explicitly exposed as failed delivery. Do not silently change mode, modify the ontology graph to compensate, or report fully successful delivery. No new sidecar may be delivered for an ontology file whose delivery failed.

See the [metadata/provenance failure reference](metadata-and-provenance.md#failure-boundaries) for construction-versus-delivery details and [Exit codes and delivery failures](cli.md#exit-codes-and-delivery-failures) for CLI process codes. These codes do not prescribe Python exception classes or return codes.

---

Governing rules: §3.2; §15; DK-DIAG-04–05; DK-GEN-09–10; DK-IRI-01; DK-LBL-02; baseline consolidated: **2026-11-25**; repository commit: `0523cc4f51356d7de75286ceb176493f714ef7f2`; source: [`documentation/specification/transformation-specification.md`](https://github.com/pedropaulofb/ontouml-directkg/blob/0523cc4f51356d7de75286ceb176493f714ef7f2/documentation/specification/transformation-specification.md).

Accepted update: **RD-04 Decision 2 — Runtime, configuration, and artifact-delivery failure contract (Q1-A, Q1 Adjustment residual exit code `7`, Q2-A, Q3-A, Q4-A)** (project-owner formalization included in the cited consolidation).

Accepted update: **RD-04 — Condition-to-code catalogue boundary for v1 (Alternative A)** (project-owner formalization included in the cited consolidation).

Accepted update: **RD-05 — Optional caller-supplied ontology version IRI** (project-owner formalization, Option B, included in the cited consolidation).

Accepted update: **RD-05 — File-only transformation input and exact-byte source checksums** (project-owner formalization included in the cited consolidation).
