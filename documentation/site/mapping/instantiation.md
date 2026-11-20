# Instantiation associations

This page describes the **accepted declaration boundary**, not verified runtime behavior. Declaring an OntoUML `instantiation` association is different from supplying concrete instance-to-classifier links.

## Declaration and concrete links

`rdf:type` is the canonical representation of actual instantiation facts. An explicit `instantiation` association does not become an ordinary `owl:ObjectProperty`, and DirectKG does not mint a property IRI for it. The current conceptual-model input supplies no concrete instance links merely by declaring the association, so that declaration may produce no RDF/OWL statement.

If concrete instantiation links are supported in the future, each must be represented directly as an instance's `rdf:type` assertion to its classifier. This is conditional normative context; it does not establish existing input support, a runnable example, or a Python API. Do not invent an individual or a type assertion from the association declaration alone.

Instantiation declarations are not eligible for [named inverse generation](inverses.md#generation-and-eligibility). They do not become reified association resources solely to preserve their source data.

## Discarded association information

Association-level names, role names, identifiers/IRIs, multiplicities, and other association-level characteristics are deliberately not materialized. When one or more are present and discarded, emit **one consolidated warning** identifying the association and the information categories lost.

The warning's traceability and content have a strict boundary:

| Include | Do not reproduce |
| --- | --- |
| The source element ID as a locator; source element type where available | A minted association/property IRI or alternative OWL association resource |
| Categories such as association name, role names, or multiplicities | The actual discarded name, role-name strings, multiplicity expressions, separately declared association IRI, or values of other discarded characteristics |
| The effect of discarding those categories on output | A substitute representation of the discarded association semantics |

Discarded values cannot reappear in RDF/OWL, provenance metadata, annotations, alternative resources, or diagnostic payloads. Retaining the source ID solely to locate the diagnostic is allowed; it is not an OWL representation of the association or a basis for minting one.

The console form, when visible under its selected threshold, and persistent JSON describe the same underlying diagnostic event and respect the same content boundary. Their presentation formats may differ. Persistent JSON follows the [shared JSON report contract](../reference/diagnostics.md#shared-json-report-contract). This warning's identifier remains [provisional](../reference/diagnostics.md#stable-first-release-diagnostic-core); it is outside the eight-code stable core. Console filtering does not remove the produced warning from complete diagnostic access/export.

The warning makes information loss visible; it does not preserve the association-level semantics. See [Presentation and persistence](../reference/controls.md#presentation-and-persistence-do-not-change-transformation-outcomes) for the diagnostic boundary and [Preservation boundaries](../concepts/semantics.md#preservation-boundaries) for the limitation index.

For `«instantiation»` relations (`DK-INS-01–02`, `DK-DIAG-03`), absent `properties`, explicit `properties: null`, and valid `Property`-object arrays (where every entry is a JSON object with `type: "Property"`, regardless of array length) retain this existing discard behavior. By contrast, a non-array `properties` value (including non-array primitives or objects) or a `properties` array containing any non-object or non-`Property` entry triggers a structural **ERROR**: `strict` and `tolerant` abort, while `best-effort` retains **ERROR** severity, omits the affected relation and dependent output without generating discard warnings or output from malformed container entries, and continues with independently transformable elements. Fatal duplicate declaration IDs (`§3.4`, `DK-DIAG-05`), `§3.4` relation-ID validity, and stereotype acceptance/rejection (`DK-DIAG-06`) over valid `Property` entries retain precedence. See [Non-binary and malformed relation properties containers](../reference/diagnostics.md#non-binary-and-malformed-relation-properties-containers) for policy outcomes and current `08abccac8a6923c587cf351a5137f1e140e44a17` implementation status (`_discard_instantiation` in `relations.py` and `index_project` in `source.py` still raise `NotImplementedError` for malformed containers).

## No reconciliation

DirectKG does not compare or reconcile an explicit instantiation association with [categorizer-derived classifications](higher-order.md#categorizers-and-powertypes). There is no precedence rule, and classifications are not suppressed merely because they overlap or appear inconsistent.

The [semantic-validation boundary](../concepts/semantics.md#validation-boundary) still applies. Structural processing requirements retain their own diagnostics; this mapping supplies no semantic repair, general consistency guarantee, or new concrete-instance support.

---

Governing rules: §3.4; DK-INS-01–03; DK-INV-02; DK-DIAG-03–06; baseline consolidated: **2026-11-20**; repository commit: `08abccac8a6923c587cf351a5137f1e140e44a17`; source: [`documentation/specification/transformation-specification.md`](https://github.com/pedropaulofb/ontouml-directkg/blob/08abccac8a6923c587cf351a5137f1e140e44a17/documentation/specification/transformation-specification.md).

Accepted update: **RD-02 — Non-binary (`len != 2`) and absent/null/malformed `Relation.properties` association-end containers (Alternative A)** (project-owner formalization included in the cited consolidation).
