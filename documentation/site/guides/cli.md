# CLI guide

This guide explains the **specified command-line contract**. At the consulted revision, no production executable, installation mechanism, or conversion entry point exists. The option spellings and exit codes below are accepted requirements, not evidence of a runnable CLI.

## Invocation

Executable names, positional arguments, input/output invocation mechanics, and a default output destination remain unavailable or unspecified. No complete command is offered as working usage. The [control catalog](../reference/controls.md#established-controls) lists established option spellings, values, and defaults; it does not establish an executable.

For an eventual verified invocation, prepare an export satisfying the [input contract](../reference/input.md), select effective controls from that catalog, and interpret the result using the separate transformation and delivery contracts below. Do not infer additional format, prefix, sorting, qualified-cardinality, or independent ontology-IRI switches.

Invalid invocation, such as an unknown option or invalid value, is rejected **before conversion** with code `2` and no transformation outcome. A rejected supplied base likewise returns `2`: no conversion starts and no ontology, outcome, or conversion-diagnostics report is produced, even if a diagnostics-file path was supplied. The [base-IRI reference](../reference/identifiers.md#base-and-ontology-iris) owns the exact validation and delimiter rules.

## Files and console

Treat the artifacts independently:

- Ontology serialization uses RDF 1.1 Turtle. A completed conversion is eligible for delivery; an aborted conversion must not deliver its accumulated ontology.
- Separate provenance uses Turtle beside a concrete ontology output path, with the accepted `<output-stem>.provenance.ttl` convention. Do not invent a sidecar name for stdout or an in-memory graph, or deliver a new sidecar when ontology-file delivery failed. See [Artifacts and digests](metadata-and-provenance.md#artifacts-and-digests).
- `--diagnostics-file PATH` explicitly requests persistent JSON at the complete caller-selected path. When absent, the CLI creates no diagnostics file. For conversions that run, attempt export of every diagnostic produced before termination, including after an accepted abort or a recorded ontology/sidecar delivery failure.

The [console-level control](../reference/controls.md#established-controls) filters presentation: `info` shows INFO/WARNING/ERROR, `warning` shows WARNING/ERROR, and `error` shows ERROR. It changes neither diagnostic production/collection nor transformation behavior, output eligibility, outcome, or exit-code selection. Hidden events remain available through the requested report. This contract does not select stdout/stderr routing or console formatting.

The report is a **mirror of produced diagnostics**, not an inventory of every possible loss. Export must not create extra transformation events, alter their severity, or turn deliberate silence into warnings. The fixed outcome names and diagnostic content are explained in [Diagnostics and recovery](../reference/diagnostics.md#diagnostic-collection-and-export); exact JSON member names, schema, and runtime diagnostic identifiers remain unspecified.

## Exit codes and delivery failures

Transformation outcome and requested-file delivery are separate. `completed-with-errors` can deliver permitted partial output; error severity alone does not establish abortion. INFO and WARNING alone do not require a nonzero status. The table below lists the complete accepted CLI code mapping within its stated scope (§15).

| Code | Specified condition |
| --- | --- |
| `0` | Outcome `completed`, with requested output delivery successful |
| `1` | Outcome `completed-with-errors`, with requested output delivery successful |
| `2` | Invalid invocation before conversion; also rejected supplied-base configuration |
| `3` | Outcome `aborted`, with no requested diagnostics-file delivery failure |
| `4` | A requested diagnostics file cannot be created or written |
| `5` | Requested provenance-sidecar serialization, creation, or writing fails, without a requested diagnostics-file or ontology-file delivery failure |
| `6` | Requested ontology-file creation or writing fails **after successful ontology serialization and construction of any required provenance**, without a requested diagnostics-file delivery failure |

### Precedence and scope

Apply precedence only to failures that can arise within their specified stages:

1. Diagnostics-file failure `4` takes precedence over `0`, `1`, `3`, `5`, and `6`.
2. Ontology-file failure `6` takes precedence over `0`, `1`, and `5`, when applicable.
3. Sidecar delivery failure `5` takes precedence over `0` and `1`.

Code `2` concerns rejection before conversion, rather than a competing transformation result. Abortion prohibits ontology delivery; it is not a completed result whose ontology-file delivery should be attempted. Code `1` must not suppress eligible ontology output.

Required-provenance **construction** failure under `embedded` or `sidecar` aborts before ontology delivery under every input policy: code `3`, overridden by `4` if requested diagnostics delivery also fails. Once provenance is constructed, failure to serialize/create/write its sidecar is instead a **delivery** failure using `5`; keep the successfully written ontology. See [Failure boundaries](metadata-and-provenance.md#failure-boundaries).

Code `6` covers the stated ontology-file creation/write stage. Other ontology-output failures, including serialization failures outside that resolved scope, and unexpected runtime failures have no additional specified code mapping. Do not extend `4` to unspecified diagnostic-export failure mechanisms or present `0` as successful delivery after a specified delivery failure.

### Reporting and retained results

An ontology-file failure reports ERROR with destination, available reason, and failed delivery. It does not change the established outcome, graph, or requested provenance mode. Attempt requested CLI diagnostics export after recording it, and do not deliver a new provenance sidecar for that failed ontology file.

A sidecar failure reports ERROR and failed delivery independently of input policy. Retain successfully delivered ontology output, without modifying its graph, deleting it solely for the sidecar failure, or switching provenance mode. Attempt requested diagnostics export after recording the failure.

!!! warning "A remaining file may be outdated"

    Neither failed ontology nor failed sidecar writes may leave a partial file presented as valid output. If an older destination remains, the CLI must report that it was **not updated for the current execution**.

A requested diagnostics-file creation/write failure requires a console error identifying destination and available reason, with code `4`. The underlying transformation outcome, severities, and ontology-output eligibility remain unchanged. If conversion already aborted, report-write failure must not replace or conceal its transformation diagnostics. Recovery from an unwritable destination is not prescribed.

The following are **contract illustrations, not observed executions**:

| Situation | Outcome and CLI result |
| --- | --- |
| Only warnings; requested delivery succeeds | `completed`, code `0` |
| Accepted recovery completes with errors; requested delivery succeeds | `completed-with-errors`, code `1`; partial ontology remains eligible |
| Duplicate declaration IDs; requested diagnostics file is written | `aborted`, code `3`; no ontology |
| Otherwise completed conversion; diagnostics destination is unwritable | Outcome unchanged, code `4` |
| Ontology written; requested sidecar cannot be written | Outcome unchanged, code `5`; ontology retained |
| Ontology destination cannot be written after serialization/provenance construction | Outcome unchanged, code `6`; no new sidecar; code `4` if requested diagnostics writing also fails |

The [Python guide](python.md) explains equivalent transformation capabilities and its separate export/access contract.

---

Governing rules: §15; DK-DIAG-04–05; DK-GEN-10; DK-IRI-01; baseline consolidated: **2026-10-21**; repository commit: `a36322fa87c006cece63aaadd2aa5ccd513f6087`; source: [`documentation/specification/2026-10-21 - specification handoff.md`](https://github.com/pedropaulofb/ontouml-directkg/blob/a36322fa87c006cece63aaadd2aa5ccd513f6087/documentation/specification/2026-10-21%20-%20specification%20handoff.md).
