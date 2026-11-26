# CLI guide

This guide explains the **specified command-line contract**. [Getting started](../getting-started.md) provides a complete invocation verified with Python 3.12.14 against development revision `25bf7b2259331d0c439fe0f79f826bae0218b8f7`. That bounded execution does not establish verification of every contract below.

## Invocation

Every CLI transformation requires a concrete [OntoUML JSON input file](../reference/input.md#source-file-input) identified by a file path, including when provenance is `none`, and a concrete ontology output file path (`-o`/`--output`). CLI `stdout` ontology streaming remains outside the first-release scope (`§15`, `DK-GEN-10`).

The [control catalog](../reference/controls.md#established-controls) lists established option spellings, values, and defaults. Follow [First conversion](../getting-started.md#first-conversion) for verified working usage from the repository root.

The accepted `--ontology-version-iri IRI` option supplies an [optional ontology-header version identifier](../reference/output.md#optional-ontology-version-iri), while retaining the base-derived ontology IRI. The [inspected CLI parser](../reference/controls.md#interface-parity) declares this option.

For an invocation, prepare an export satisfying the [input contract](../reference/input.md), select effective controls from that catalog, and interpret the result using the separate transformation and delivery contracts below. Do not infer additional format, prefix, sorting, qualified-cardinality, or independent ontology-IRI switches.

**Pre-conversion configuration and invocation validation** applies uniformly before conversion starts under every input policy (`strict`, `tolerant`, and `best-effort`). Any invalid CLI invocation or rejected transformation control—including unknown options, invalid enum choices or types, invalid boolean flags, invalid `--language` syntax (must satisfy `^[a-zA-Z]+(?:-[a-zA-Z0-9]+)*$` without trailing newline characters), `--metadata-file` whose filename is not `metadata.yaml`, invalid supplied `--base-iri` or `--ontology-version-iri`, or a `--diagnostics-file` alias with a protected destination subject to the invocation-time rejection rule—reports a configuration/invocation error and exits **`2`**. No conversion starts, and no ontology, sidecar, diagnostics file, transformation outcome, or conversion-diagnostics report is produced, even if `--diagnostics-file` was supplied.

This pre-conversion rejection remains distinct from:

- source-file read, parse, or root-structure failures on a valid supplied path (`UNPROCESSABLE_DOCUMENT` under `DK-DIAG-05`, aborting with exit `3` overridden by `4`),
- `--metadata-file` existence, read, YAML-parse, or content failures on an explicit `metadata.yaml` path (`DK-GEN-09`), and
- unexpected pre-conversion runtime failures that are not invalid CLI invocations or pre-conversion configuration rejections (classified under residual exit code `7`, not `2`).

The [base-IRI reference](../reference/identifiers.md#base-and-ontology-iris) owns base validation and delimiter rules; the [version-IRI reference](../reference/output.md#optional-ontology-version-iri) owns its separate validation boundary.

For `--language`, lexical acceptance does not establish BCP 47 grammatical well-formedness. Supplying a grammatically well-formed and semantically correct override is the caller's responsibility; see [Language resolution](../reference/text.md#language-resolution).

## Files and console

Treat the artifacts independently:

- Ontology serialization uses RDF 1.1 Turtle. A completed conversion (`completed` or `completed-with-errors`) is eligible for delivery; an aborted conversion must not deliver its accumulated ontology or leave partial files presented as valid.
- Separate provenance uses Turtle beside a concrete ontology output path, with the accepted `<output-stem>.provenance.ttl` convention. Do not invent a sidecar name for stdout or an in-memory graph, or deliver a new sidecar when ontology-file delivery failed. `<output-stem>.provenance.ttl` is a protected output-artifact path **only when `--provenance sidecar` is active**; under `embedded` or `none`, that pathname alone is not a reason to reject diagnostics export. The main ontology destination remains protected in every mode. See [Artifacts and digests](metadata-and-provenance.md#artifacts-and-digests).
- `--diagnostics-file PATH` explicitly requests persistent JSON at the complete caller-selected path. When absent, the CLI creates no diagnostics file. Aliasing covered by the existing invocation-time checks rejects pre-conversion (`2`), whereas protected aliasing established or persisting at export results in diagnostics-delivery failure (`4`). For conversions that run, attempt export of every diagnostic produced before termination even after a policy-driven abort, `INTERNAL_TRANSFORMATION_FAILURE`, required-provenance construction failure (including late `sidecar` output-provenance construction inside explicit delivery before writing), recorded ontology-file delivery failure, or recorded provenance-sidecar delivery failure.

Use independent destinations for ontology, active sidecar and diagnostics files. The [replacement-aware aliasing contract](../reference/diagnostics.md#replacement-aware-cli-aliasing) distinguishes invocation-time acceptance from export-time protection: initially shared filesystem identity alone does not justify rejection when the destination entries are distinct, but diagnostics export must be refused if a protected alias remains or is established at export. Acceptance before conversion does not guarantee successful report delivery.

The [console-level control](../reference/controls.md#established-controls) filters presentation: `info` shows INFO/WARNING/ERROR, `warning` shows WARNING/ERROR, and `error` shows ERROR. It changes neither diagnostic production/collection nor transformation behavior, output eligibility, outcome, or exit-code selection. Hidden events remain available through the requested report. This contract does not select stdout/stderr routing or console formatting.

**Console-only failures**—failure to write, encode, or flush CLI console output (`stdout` or `stderr`) alone—must **not** change the transformation outcome, collected diagnostics, Python result, or delivered output files, must **not** prevent requested `--diagnostics-file PATH` export from being attempted, and must **not** alter the otherwise applicable CLI exit code (`0`–`7`). Console error reporting on failures is best-effort so console write failures cannot mask exports or alter exit status.

The report is a **mirror of produced diagnostics**, not an inventory of every possible loss. Export must not create extra transformation events, alter their severity, or turn deliberate silence into warnings. [Diagnostics and recovery](../reference/diagnostics.md#diagnostic-collection-and-export) explains collection and content; the [shared JSON report contract](../reference/diagnostics.md#shared-json-report-contract) fixes required fields and types, empty/null context, and compatible extensions for both interfaces. Every produced diagnostic must populate `code` as a nonempty string; **only** the [eight stable diagnostic identifiers](../reference/diagnostics.md#stable-first-release-diagnostic-core) carry a normative first-release stability guarantee for their strings and condition meanings, while non-core identifiers remain implementation-defined / unguaranteed in the first release (without a separate v1 catalogue) and must not suppress required reporting.

## Exit codes and delivery failures

Transformation outcome and requested-file delivery are separate. `completed-with-errors` can deliver permitted partial output; error severity alone does not establish abortion. INFO and WARNING alone do not require a nonzero status. The table below lists the complete accepted CLI code mapping within its stated scope (`§15`).

| Code | Specified condition |
| --- | --- |
| `0` | Transformation outcome is `completed`, and requested output delivery succeeds. |
| `1` | Transformation outcome is `completed-with-errors`, and requested output delivery succeeds. |
| `2` | Invalid CLI invocation or pre-conversion configuration/invocation rejection (unknown option, invalid transformation control value/type, invalid supplied base or ontology version IRI, `--metadata-file` filename `!= metadata.yaml`, or a `--diagnostics-file` alias with a protected destination subject to the invocation-time rejection rule). |
| `3` | Transformation outcome is `aborted` (including policy aborts, duplicate source IDs, `INTERNAL_TRANSFORMATION_FAILURE` once conversion starts through result construction, and `REQUIRED_PROVENANCE` including late `sidecar` construction inside delivery before writing), with no diagnostics-delivery failure. |
| `4` | Failure to serialize, create, or write a requested diagnostics file (including I/O errors, export-time/late aliasing, and unexpected export/serialization errors). Strictly reserved for diagnostics-file delivery failure; console-only failures must not trigger `4`. |
| `5` | Post-ontology provenance-sidecar delivery failure (after main ontology writing succeeds, while preparing, serializing, encoding, creating, or writing the sidecar, or an unexpected runtime error in that stage), without a requested diagnostics-file or ontology-file delivery failure. |
| `6` | Post-conversion ontology-file delivery failure before main ontology write completes (including path handling, Turtle serialization, UTF-8 encoding, file creation/writing/replacement, or an unexpected runtime error in that stage), without a requested diagnostics-file delivery failure. |
| `7` | Residual fallback exclusively for reportable unexpected runtime failures that cannot be classified under exit codes `0`–`6` (excluding console-only write, encode, or flush failures). |

### Precedence and scope

Apply precedence only to failures that can arise within their specified stages:

1. Diagnostics-file failure `4` takes precedence over `0`, `1`, `3`, `5`, and `6`.
2. Ontology-file failure `6` takes precedence over `0`, `1`, and `5`, when applicable.
3. Sidecar delivery failure `5` takes precedence over `0` and `1`, independently of `--input-policy`.

Code `2` concerns rejection before conversion rather than a competing transformation result. Unexpected pre-conversion runtime failures that are not invalid CLI invocations or pre-conversion configuration rejections must **not** use `2`; they use residual fallback exit code `7` instead. Abortion (`3`) prohibits ontology delivery; it is not a completed result whose ontology-file delivery should be attempted. Code `1` must not suppress eligible ontology output.

**Exit code `7` scope boundary.** Exit code `7` is strictly a residual fallback for reportable unexpected runtime failures that cannot be classified under exit codes `0`–`6` (excluding console-only `stdout`/`stderr` write, encode, or flush failures). It must not replace any established transformation (`0`, `1`, `3`), configuration/invocation (`2`), artifact- or diagnostics-delivery (`4`, `5`, `6`), or console-presentation failure treatment; establishes no fourth transformation outcome; does not expand `DK-DIAG-04`'s eight-code stable diagnostic core; and modifies no previously accepted behavior.

Required-provenance **construction** failure under `embedded` or `sidecar`—including both conversion-time construction and post-conversion `sidecar` output-provenance construction inside explicit delivery before writing any ontology or sidecar file—produces `REQUIRED_PROVENANCE` and aborts before ontology delivery under every input policy: code `3`, overridden by `4` if requested diagnostics delivery also fails, with existing ontology and sidecar files left untouched. Once main ontology writing succeeds and required provenance has been constructed, failure to prepare, serialize, encode, create, or write its sidecar (including an unexpected runtime error in that stage) is instead a **delivery** failure using `5` (`SIDECAR_DELIVERY`), keeping the successfully written ontology. See [Failure boundaries](metadata-and-provenance.md#failure-boundaries).

An unexpected internal error that stops transformation once conversion starts through result construction causes an `aborted` outcome (`INTERNAL_TRANSFORMATION_FAILURE`) when DirectKG can still report the failure. This applies under every input policy, including `best-effort`. Exit `3` if no diagnostics file was requested or the report was written. If the requested report cannot be written, exit `4` and show both failures on the console on a best-effort basis. See [Unexpected internal failures during transformation](../reference/diagnostics.md#unexpected-internal-failures-during-transformation).

Code `6` (`ONTOLOGY_DELIVERY`) applies under every input policy to post-conversion main-ontology file delivery failures before main ontology writing completes (destination path handling, Turtle serialization, UTF-8 encoding, file creation/writing/replacement, or an unexpected runtime error in that stage, excluding late `sidecar` output-provenance construction aborts under `3`). Code `4` remains strictly reserved for requested `--diagnostics-file` delivery failures; code `0` must not imply successful delivery when any specified delivery failure occurs.

### Reporting and retained results

An ontology-file delivery failure reports `ONTOLOGY_DELIVERY` ERROR with the failure stage (where applicable), destination, available cause, and failed delivery. Any existing ontology and provenance sidecar remain untouched, neither artifact is delivered for that request, and no partial ontology artifact may be left presented as valid. The established transformation outcome (`completed` or `completed-with-errors`), generated graph, and requested provenance mode are preserved. Attempt requested CLI JSON export after recording the delivery ERROR. The report includes that ERROR and the established outcome. If the report also cannot be written, report both failures on the console on a best-effort basis and exit `4`.

**Implementation status.** RD-04 Decision 2's runtime, configuration and delivery boundaries were addressed in [revision `b787d07d33a6c96c06b65a84013dd8b96cfc9edb`](https://github.com/pedropaulofb/ontouml-directkg/commit/b787d07d33a6c96c06b65a84013dd8b96cfc9edb). C13's accepted replacement-aware contract is described above; full export-time conformance remains subject to implementation and acceptance-test verification.

A sidecar failure reports `SIDECAR_DELIVERY` ERROR and failed delivery independently of input policy. Retain successfully delivered ontology output, without modifying its graph, deleting it solely for the sidecar failure, or switching provenance mode. Attempt requested diagnostics export after recording the failure.

!!! warning "A remaining file may be outdated"

    Neither failed ontology nor failed sidecar writes may leave a partial file presented as valid output. If an older destination remains, the CLI must report that it was **not updated for the current execution**.

A requested diagnostics-file delivery failure (I/O error, export-time/late aliasing, or unexpected export/serialization error) requires a best-effort console error identifying the report-delivery failure, requested diagnostics destination and available failure reason, with code `4`. Preserve independently applicable transformation and artifact-delivery diagnostics. The underlying transformation outcome, severities, and ontology/sidecar delivery eligibility remain unchanged. If conversion already aborted, report-write failure must not replace or conceal its transformation diagnostics. Recovery from an unwritable destination is not prescribed.

The following are **contract illustrations, not observed executions**:

| Situation | Outcome and CLI result |
| --- | --- |
| Only warnings; requested delivery succeeds | `completed`, code `0` |
| Accepted recovery completes with errors; requested delivery succeeds | `completed-with-errors`, code `1`; partial ontology remains eligible |
| Invalid control value/type, `--metadata-file` filename `!= metadata.yaml`, or a `--diagnostics-file` alias with a protected destination subject to the invocation-time rejection rule | Rejected before conversion, code `2`; no outcome, ontology, sidecar, or diagnostics report |
| Duplicate declaration IDs; requested diagnostics file is written | `aborted`, code `3`; no ontology or sidecar |
| Late `sidecar` output-provenance construction fails inside delivery before writing | `aborted` (`REQUIRED_PROVENANCE`), code `3` (or `4` if requested diagnostics write fails); existing ontology and sidecar untouched; `--diagnostics-file` still attempted |
| A placeholder-base WARNING precedes a reportable internal failure during relation mapping | `aborted`, with no ontology or provenance sidecar. A successfully written JSON report includes `aborted`, the earlier WARNING and the internal-failure ERROR. Exit `3` if export succeeds or was not requested. If requested export fails, both failures are shown best-effort on the console and the run exits `4`. |
| Otherwise completed conversion; diagnostics destination is unwritable or hits export-time aliasing | Outcome and ontology/sidecar eligibility unchanged, code `4` |
| `--provenance embedded` or `none`; `--diagnostics-file` targets `<output-stem>.provenance.ttl` independently of the main ontology destination | Permitted; the inactive sidecar-shaped pathname alone is not an artifact alias. Exit code reflects outcome/delivery (`0` or `1` on success) |
| Console `stdout`/`stderr` write, encode, or flush fails alone | Outcome, diagnostics, delivered files, `--diagnostics-file` export, and applicable exit code (`0`–`7`) unchanged |
| Ontology written; requested sidecar cannot be prepared, serialized, or written | Outcome unchanged, code `5`; ontology retained |
| Ontology destination cannot be written or Turtle serialization/encoding fails before write completes | Outcome unchanged, code `6`; no new sidecar; code `4` if requested diagnostics writing also fails |
| Reportable unexpected runtime failure unclassifiable under `0`–`6` (including unexpected pre-conversion runtime failure, excluding console-only failure) | Residual fallback code `7`; no fourth transformation outcome and no expansion of the eight-code diagnostic core |

The [Python guide](python.md) explains equivalent transformation capabilities and its separate export/access contract.

---

Governing rules: §15; DK-DIAG-01, 04–05; DK-GEN-09–10; DK-IRI-01; DK-LBL-02; baseline consolidated: **2026-11-26**; repository commit: `3156ff81731a7ee5b4720245380bc2ccb72dcaf1`; source: [`documentation/specification/transformation-specification.md`](https://github.com/pedropaulofb/ontouml-directkg/blob/3156ff81731a7ee5b4720245380bc2ccb72dcaf1/documentation/specification/transformation-specification.md).

Accepted update: **RD-04 Decision 2 — Runtime, configuration, and artifact-delivery failure contract (Q1-A, Q1 Adjustment residual exit code `7`, Q2-A, Q3-A, Q4-A)** (project-owner formalization included in the cited consolidation).

Accepted update: **RD-04 — Condition-to-code catalogue boundary for v1 (Alternative A)** (project-owner formalization included in the cited consolidation).

Accepted update: **RD-05 — Optional caller-supplied ontology version IRI** (project-owner formalization, Option B, included in the cited consolidation).

Accepted update: **RD-05 — File-only transformation input and exact-byte source checksums** (project-owner formalization included in the cited consolidation).
