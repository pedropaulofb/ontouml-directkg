# Python guide

This guide describes **specified integration capabilities**. The [inspected source](../reference/controls.md#interface-parity) exports `convert` and declares its public conversion signature. Runtime behavior and source-generated API reference content have not been verified for this documentation update.

## Conversion and configuration

Every Python transformation requires a concrete [OntoUML JSON input file](../reference/input.md#source-file-input) identified by a file path, regardless of provenance mode. Parsed JSON objects, dictionaries, and other fileless representations are not accepted substitutes. Internal processing in memory and the existing output-graph and diagnostic capabilities remain available under their separate contracts.

Python and CLI must expose every established ontology-transformation control with equivalent selectable behavior, identical defaults, and the same transformation effects. An equivalent effective configuration on the same supported input invokes the same accepted rules. This does not promise identical execution provenance from separate runs.

Use [Controls](../reference/controls.md#established-controls) as the canonical inventory, including metadata and provenance. Python need not copy CLI flag spelling, representation, or negative-flag polarity. The exception is the specifically prescribed parameter name `relation_labels`, with accepted values `"source-only"` and `"generated"`, default `"source-only"`. This requirement does not establish the containing function's name or signature.

An equivalent optional Python control must accept a caller-supplied [ontology version IRI](../reference/output.md#optional-ontology-version-iri), with the same emission and absence behavior as the CLI control. Its parameter name is not prescribed by the specification; the [inspected conversion signature](../reference/controls.md#interface-parity) declares this optional control.

An integrator's conceptual sequence is to prepare a [supported JSON file](../reference/input.md), supply its file path, choose effective transformation settings, request conversion through the Python conversion interface, inspect its outcome and diagnostics, and consume only eligible ontology output. Exact Python input parameter names, function signatures, and output representations are not prescribed here; this sequence is not executable code.

Base validation and validation of a supplied ontology version IRI happen before conversion. Either rejection must be signaled programmatically, independently of input policy, without an ontology, transformation outcome, or conversion-diagnostics report. No particular exception class is selected. See [Base and ontology IRIs](../reference/identifiers.md#base-and-ontology-iris) and the version-IRI boundary linked above.

The required ontology-serialization capability uses RDF 1.1 Turtle. Prefix names, blank-node labels, statement order, and other textual layout are not fixed; compare the accepted graph rather than assuming byte-identical serializations. See [Graph and text stability](../reference/output.md#graph-and-text-stability).

## Diagnostics and aborts

For each conversion that runs, expose exactly one transformation outcome: `completed`, `completed-with-errors`, or `aborted`. Their conditions and output eligibility are defined in [Outcomes and output eligibility](../reference/diagnostics.md#outcomes-and-output-eligibility). Fixed names do not select a result type or JSON member name.

Structured access must retain **every diagnostic actually produced**, including severity, meaning, and applicable source information. It remains available after a policy-driven abort, including duplicate-ID abortion, for everything produced before termination. Do not derive success solely from a quiet console or treat every ERROR as proof that conversion aborted.

!!! note "Output eligibility depends on the outcome"

    An aborted conversion must not deliver its accumulated ontology through Python. A completed `best-effort` conversion can deliver permitted partial output despite retained ERROR diagnostics.

The specification does not prescribe whether the API communicates these outcomes through return values or exceptions.

Accessing diagnostics or exporting them must not create additional transformation diagnostics, change their severity/meaning, recovery, outcome, or ontology-output eligibility. Console thresholds affect presentation only; they do not filter Python structured access. Intentional silence remains silent. Exact runtime diagnostic codes, required-field matrices, and report schemas remain unspecified.

Requested ontology-file creation/write failure, after successful ontology serialization and construction of any required provenance, must be exposed programmatically with diagnostics still accessible. It does not alter the established outcome or graph. A failed write cannot be presented as a valid delivered ontology; an older destination left in place must be identified as not updated. Other unresolved output failures remain outside that specifically accepted failure policy.

## Separate exports

### Diagnostic JSON

Python conversion must **not automatically write a diagnostics file**. Provide a separate operation, explicitly called by the application, to export produced diagnostics to its chosen JSON destination. This operation uses the same report schema and content contract as the CLI, including the exposed outcome and complete mirror of produced diagnostics.

The CLI's `--diagnostics-file` spelling does not prescribe a Python parameter or operation name. Persistent diagnostics writing is separate from transformation-control parity; applications may inspect diagnostics without saving them.

If that separate export operation cannot create or write its requested file, signal failure programmatically while retaining access to transformation diagnostics. Export failure must not change their severities, transformation outcome, or ontology-output eligibility, and must not conceal a prior abort. No exception/result type, file-writing internals, or recovery from an unwritable destination is selected.

### Provenance graph and file output

Python must provide semantically equivalent metadata-file and provenance controls, including provenance default `embedded`. Separate provenance must be available programmatically **as a graph**, with explicit serialization for file output. This graph capability does not select a concrete Python graph class, method, or return-object layout.

Automatic sidecar writing requires a concrete ontology output path; do not invent one for an in-memory graph or stdout. Embedded provenance excludes concrete output-file information, including from its configuration record. See [Provenance modes](metadata-and-provenance.md#provenance-modes) and [Artifacts and digests](metadata-and-provenance.md#artifacts-and-digests).

Failure to construct required provenance in an enabled mode aborts before ontology delivery under every input policy. In contrast, a later sidecar serialization/create/write failure leaves successfully written ontology output available and must be explicitly exposed as failed delivery. Do not silently change mode, modify the ontology graph to compensate, or report fully successful delivery. No new sidecar may be delivered for an ontology file whose delivery failed.

See the [metadata/provenance failure reference](metadata-and-provenance.md#failure-boundaries) for construction-versus-delivery details and [Exit codes and delivery failures](cli.md#exit-codes-and-delivery-failures) for CLI process codes. These codes do not prescribe Python exception classes or return codes.

---

Governing rules: §15; DK-DIAG-04–05; DK-GEN-09–10; DK-IRI-01; baseline consolidated: **2026-10-21**; repository commit: `a36322fa87c006cece63aaadd2aa5ccd513f6087`; source: [`documentation/specification/2026-10-21 - specification handoff.md`](https://github.com/pedropaulofb/ontouml-directkg/blob/a36322fa87c006cece63aaadd2aa5ccd513f6087/documentation/specification/2026-10-21%20-%20specification%20handoff.md).

Accepted update: **RD-05 — Optional caller-supplied ontology version IRI** (project-owner formalization, Option B, supplied after this baseline).

Accepted update: **RD-05 — File-only transformation input and exact-byte source checksums** (project-owner formalization supplied after this baseline).
