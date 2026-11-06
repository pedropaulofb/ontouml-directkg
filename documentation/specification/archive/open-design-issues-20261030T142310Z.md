# OntoUML DirectKG — Open Design Issues

## Purpose, sources, and reconciliation boundary

This is a **non-normative state document** for the next OntoUML DirectKG Architect conversation. It records unresolved design questions, not requirements or an implementation backlog. Use it together with the current Architect-maintained specification retrieved from GitHub. It is not a specification. The Architect maintains unresolved state alongside accepted specification registration; an independent Architect Reviewer verifies both documents.

**Reconciled:** 2026-10-29. The actual sources inspected were:

- `ontouml-directkg-current-specification(6).md`, **Consolidated: 2026-10-29**, stored revision **7**, read after the specification was updated during this handoff. Storage revision numbers are not DirectKG releases.
- `2026-10-21 - remaining decisions handoff(1).md`, the supplied non-normative, incomplete prior handoff.
- The recovered fuller predecessor, `2026-10-05 - remaining decisions handoff(1).md`. Its text is identical to the existing `ontouml-directkg-open-design-issues.md`, stored revision 6, inspected before this update.
- Accessible discussion, explicit user decisions, and decision-transfer messages in this Architect session, checked against the current normative rule text.

All eleven issue IDs in the recovered prior lists were accounted for. Only their remaining questions appear below; resolved questions and accepted scope exclusions are omitted. This does not establish that the entire specification is complete.

**Completeness limitation:** RD-27 inherits a reference to unspecified “other previously raised descriptive fields.” The prior files identify no concrete remaining field, and the original discussion identifying any such field is not accessible here. That conditional entry remains blocked. This document is therefore not a complete historical reconciliation of that unidentified scope; it does not reconstruct missing fields or acceptances. The older handoff's access warnings concerning named questions already settled in the current specification do not reopen those questions.

Alternatives and the advisory discussion order below are non-normative. No new mapping, recovery policy, or conformance guarantee is selected by preparing this document.

## Remaining relation semantics

### RD-17 — Remaining semantics of recognized relation stereotypes

**Status:** Partially resolved.

**Decision still needed:** Complete the previously recorded stereotype-treatment decisions for these groups:

- `mediation`, `characterization`, and `externalDependence`: determine whether their remaining treatment is adequately covered by the accepted partial mappings and applicable limitation reporting, or whether another justified mapping is needed. The accepted grounding roles and five additional axioms are not open alternatives.
- `participation`, `participational`, `creation`, `termination`, and `manifestation`: decide the remaining stereotype-specific treatment. Asymmetry for `participational` is settled; this acceptance does not extend to `participation`.
- `bringsAbout` and `triggers`: decide whether an additional justified logical mapping, declaration annotation, or explicit ordinary-mapping/limitation treatment is appropriate.

`historicalDependence` is outside these remaining questions: its ordinary mapping, applicable limitation warning, and omission of extra stereotype-only axioms and declaration annotations are settled in DK-REL-01.

**Why it matters and constraints:** Ordinary properties may preserve only part of a source stereotype's meaning. A stereotype name alone does not justify functionality, transitivity, chains, or other characteristics. Partial logical translation is also not, by itself, a reason to add a stereotype annotation. The domain-graph and lightweight-output goals in §3.1 and the no-semantic-validation boundary in §3.4 continue to apply. No universal stereotype-annotation policy or temporal subsystem is implied.

**Accepted boundaries to preserve:** DK-REL-01's five additions have per-axiom simplicity conditions based on the hierarchy, inverse relationships, and import closure. Those conditions apply in every material-chain mode, including `preserve-conflicting-constraints`; chain-body use alone does not make a property non-simple. Keep the accepted pairing, direction-alignment, and named/anonymous-inverse rules. Do not remove accepted axioms to accommodate another proposal or infer an overall OWL 2 DL guarantee from this limited gate.

Material–relator/mode chains and derivation treatment (DK-REL-07–08), comparative–quality limitations (DK-REL-18), covered mereological mappings (DK-REL-19 and DK-GEN-04), and instantiation treatment (DK-INS-01–03) remain settled. The accepted `begin`/`end` comments under DK-PROP-06 do not automatically establish annotation treatment for other stereotypes.

**Alternatives still available — non-normative:** Retain the existing ordinary/partial mapping with the applicable diagnostics and documented limitation; add a specifically justified OWL mapping; or preserve a declaration through an appropriate annotation where a concrete benefit is established. These differ in semantic coverage, graph size, compatibility effects, and implementation/documentation cost. No blanket alternative or further recommendation has been accepted for the remaining groups.

**Evidence and next step:** Study one coherent group at a time using authoritative OntoUML meaning and the actual VP-plugin 0.5.3 export representation. Retained exporter paths include `src/main/java/it/unibz/inf/ontouml/vp/model/ontouml/model/RelationStereotype.java` and the `vp2ontouml` property, association, and stereotype transformers. Distinguish language semantics from exporter recognition and standalone-schema capability. The 2013 OntoUML-to-OWL/SWRL transformation paper remains precedent, not DirectKG authority. Research anchors are listed below.

**Dependency:** Coordinate any remaining logical-mapping proposal with RD-04's general profile claim. Do not reopen accepted mappings through that coordination.

## Structural identity and recovery

### RD-02 — Remaining structural recovery boundaries

**Status:** Partially resolved.

**Decisions still needed:**

- Bound the affected contributions and dependent output that may safely be omitted after a missing/invalid identifier or unresolved reference, where no explicit local recovery rule already settles the case.
- Specify handling of missing or malformed generalization-set membership containers and duplicate memberships.
- Specify categorizer/powertype recovery when a relevant member cannot be resolved or transformed.
- Classify any still-unsettled structural condition that prevents meaningful document-level processing even under `best-effort`, rather than assuming that every failure permits local omission.

The exceptional escaped-ID collision question is retained once, under ODI-IRI below.

**Why it matters and accepted boundaries:** Recovery must not invent missing information, merge source elements, attach axioms to the wrong resource, or deliver invalid RDF. Source-ID validity is already fixed by §3.4's minimal opaque identifier definitions; duplicate declaration IDs already abort under every input policy. Those questions are not open. Unparseable JSON already prevents transformation in every policy.

DK-DIAG-03, DK-DIAG-05, DK-DIAG-09–13, DK-CLS-09, and DK-REL-20 settle substantial local behavior. In particular, a failed larger class set must not be covered using survivors or acquire singleton completeness merely because one member survives. DK-HO-04 expressly leaves duplicate memberships, missing/malformed membership containers, and categorizer recovery unspecified. Metadata and provenance failures retain their separate DK-GEN-09–10 rules. The file-only source-input boundary in §3.2 and §15 remains applicable.

**Alternatives — non-normative:** Abort when identity or meaningful processing cannot be preserved; otherwise omit only affected contributions where independent transformation remains technically well-defined. Preserve established error severities, fallbacks, and nonfatal conditions. No general semantic validator, exhaustive malformed-input taxonomy, or additional input mechanism is proposed.

**Evidence, blockers, and next step:** Use a few concrete supported-file examples and fundamental correctness cases to determine the residual boundaries. Missing containers, duplicate memberships, and incomplete categorizer/powertype inputs need distinct examination; the accepted empty-array and failed-class-coverage rules must not be generalized without a decision. No additional corpus occurrence is asserted here.

**Dependencies:** Coordinate exceptional identity failures with ODI-IRI and externally observable recovery/reporting with RD-04.

### ODI-IRI — Exceptional collisions between distinct escaped source IDs

**Status:** Blocked on identifying the technical condition; its disposition remains unresolved.

**Decision still needed:** Specify what happens if distinct source identifiers produce the exceptional escaped-ID collision referred to in DK-IRI-07.

**Why it matters and accepted boundaries:** DK-IRI-05 requires injective technical escaping, DK-IRI-07 excludes silent repair as an ordinary name collision, and DK-CONF-02 prohibits merging distinct resources. First establish what reachable condition the exceptional clause represents despite the injectivity requirement. No observed occurrence or defect in the escaping algorithm is established by the available state.

Generic source-ID naming fallback, owner/source qualification, supplied-base validation, ordinary name collisions, and source-ID validity already have rules in DK-IRI-01, DK-IRI-04–08, DK-PROP-02, and §3.4. Duplicate declaration IDs are separately resolved by RD-02. None is reopened here.

**Alternatives — non-normative:** Abort, or omit affected contributions only if their identities and dependent references can still be bounded unambiguously. No exceptional repair, replacement-ID scheme, or ordinary collision suffixing is accepted for this case.

**Next investigation and dependency:** Identify the exact failing construction stage and a concrete case before designing recovery. Distinguish an escaping-rule implementation violation from a genuine unresolved construction boundary. Then discuss the smallest deterministic disposition with RD-02. Do not introduce elaborate collision recovery without evidence.

## Public output and diagnostics

### RD-04 — Remaining profile, diagnostic-report, and failure contract

**Status:** Partially resolved.

**Decisions still needed:**

1. State a precise general OWL conformance/profile claim consistent with the accepted mappings and import closure.
2. Select exact diagnostic identifiers and the shared JSON report contract: envelope and member names, required-field rules, and aggregation structure. Preserve all existing diagnostic-content and outcome requirements.
3. Establish externally observable behavior for unexpected runtime failures and ontology-output delivery failures outside the already resolved scope, including treatment of available results, diagnostics, transformation outcomes, and exit-code precedence.

**Why it matters:** Consumers need an accurate interoperability claim and a stable report/failure contract. The five RD-17 additions' compatibility gate is not a global profile guarantee. A result outside OWL 2 DL must not automatically be characterized as conforming to some other particular profile or regime.

**Resolved boundaries and constraints:** §3.3 settles RDF 1.1 Turtle, conventional prefix policy, and serialized-presentation freedom; DK-CONF-01 preserves the established identity determinism without adding textual repeatability. Console filtering is settled and does not change collected diagnostics. These are not open format, ordering, or verbosity choices.

DK-DIAG-04–05 and §15 settle structured Python access, separate JSON export, diagnostic mirroring, the three named transformation outcomes, aborted-output suppression, and existing delivery precedence. DK-GEN-10 settles required-provenance generation failure and provenance-sidecar delivery failure. DK-DIAG-04 and §15 settle ontology-file creation/write failure after successful serialization and construction of required provenance. Invalid base/version-IRI configuration is also already covered before conversion. Preserve these distinctions; do not assign their policies again or treat every failure as an input-policy failure.

The exact report schema remains unspecified in DK-DIAG-04. §15 explicitly leaves other ontology-output delivery failures and unexpected runtime failures outside its resolved mapping. Exact Python signatures, exception classes, internal file-writing design, extra console features, and optional formats are not added as Architect backlog items.

**Alternatives — non-normative:**

| Remaining question | Alternatives and trade-offs |
|---|---|
| General profile claim | A qualified, bounded claim versus a stronger guarantee that would require justification against all accepted mappings. A stronger proposal does not authorize removing accepted axioms. |
| Diagnostic report | Select a fixed shared envelope and diagnostic-record schema, balancing a small contract against sufficient source/effect information. No concrete schema or code set is accepted. |
| Uncovered failures | Shared or distinct public failure treatment, preserving the already established separation of transformation outcomes and delivery status. No additional status or exit-code mapping is selected. |

**Dependencies and next step:** Analyze the profile claim with the remaining RD-17 semantics and actual hierarchy/import effects. Coordinate the report and residual failure contract with RD-02, and with ODI-IRI only if that technical condition is established. Discuss a concrete bounded failure/report question rather than inventing speculative failure classes. OWL references are listed below.

## Source-scope evidence checks

### RD-27 — Evidence for any remaining previously raised descriptive fields

**Status:** Blocked on source identification and access to the discussion naming any residual field.

**Question still to establish:** Does a concrete, previously raised descriptive field remain undecided within the accepted input contract? The inherited entry names no such residual field. Recover its identity before proposing a mapping; this is an access/evidence limitation, not an established requirement for another metadata feature.

**Resolved boundary:** Multilingual lexical selection, its use in primitive recognition, and top-level project-description placement are settled in DK-IRI-10, DK-DAT-02, DK-LBL-02, and §3.2. They are not pending decisions. Literal-language handling and naming selection remain separate. The project-description rule is accepted even though the inspected 0.5.3 extraction path leaves that field empty; its placement must not be reopened through the residual evidence check.

**Constraints and importance:** §3.2 permits only its bounded source-text enrichment. Standalone-schema capability does not authorize unrelated metadata mappings. Package descriptions and custom assignments remain omitted under DK-GEN-06–07, and DK-GEN-09's external metadata whitelist must not be expanded here. An unidentified field cannot justify a new annotation, implementation task, or universal stereotype-preservation policy.

**Alternatives — non-normative:** If an actual in-scope unresolved field is recovered, compare an appropriate standard annotation mapping with deliberate omission and its stated limitation. If no such field is established, close this conditional evidence check after completing that reconciliation. No new field, vocabulary, or recommendation is selected now.

**Next investigation:** Recover the exact earlier field reference, then check its supported representation against the 0.5.3 exporter and the bounded enrichment. Do not perform an unrestricted metadata inventory. Relevant exporter, schema, and JavaScript representation references are retained below.

**Dependencies:** Source evidence precedes a mapping discussion. There is no remaining dependency on the already settled multilingual naming or project-description decisions.

### ODI-INSTANCES — Applicability of general instance-data transformation

**Status:** Blocked on source-scope evidence; no feature expansion accepted.

**Question:** Does VP-plugin 0.5.3 export additional general instance data within the supported JSON-file contract that needs a mapping beyond higher-order classification, enumeration values, and explicit instantiation associations?

**Why it matters and constraints:** A mapping must correspond to an actual in-scope source construct. DK-HO-01–04, DK-CLS-10–11, and DK-INS-01–03 already govern existing cases. DK-INS-01's conditional statement about possible future concrete links establishes no present support obligation. Standalone-schema capability and the ability to represent data in Python do not establish supported exporter behavior or authorize fileless input.

**Evidence gap, alternatives, and next step:** Inspect the actual 0.5.3 exporter path and representative JSON files. If no additional in-scope construct exists, close the evidence check. If one exists, identify its exact source shape before bringing a bounded mapping choice to the Architect. Do not design identity, typing, assertions, or recovery for a general instance subsystem in advance.

**Dependencies:** Establish source scope before any new mapping discussion; coordinate with RD-02 only if an actual construct exposes an unsettled recovery question.

## Advisory dependency order

This is a non-normative discussion order, not an implementation plan or an accepted decision.

1. Establish the missing source evidence for RD-27 and ODI-INSTANCES before retaining any additional mapping question from those checks.
2. Examine concrete residual recovery cases under RD-02; investigate ODI-IRI only after its technical condition is identified.
3. Complete RD-17 in coherent stereotype groups. The RD-04 profile claim depends on the relevant semantic decisions, while its report/failure contract can proceed with the necessary RD-02 recovery boundaries.

The source-evidence checks and independent semantic/recovery questions need not block one another. Accepted scope exclusions and transfers awaiting integration are not unresolved design alternatives.

## Retained research anchors and continuation

These are research pointers retained from the inspected prior state and session; this handoff is not a fresh execution or exhaustive review of those repositories.

- Supported exporter release: https://github.com/OntoUML/ontouml-vp-plugin/releases/tag/0.5.3
- Exporter repository: https://github.com/OntoUML/ontouml-vp-plugin
  - Previously inspected paths include `src/main/java/it/unibz/inf/ontouml/vp/utils/Stereotype.java`, `src/main/java/it/unibz/inf/ontouml/vp/model/ontouml/model/RelationStereotype.java`, and `src/main/java/it/unibz/inf/ontouml/vp/model/vp2ontouml/` transformers for properties, associations, and stereotypes.
- Foundational metamodel: https://github.com/OntoUML/ontouml-metamodel
- JSON schema reference: https://github.com/OntoUML/ontouml-schema
  - Retained paths include `dist/ontouml-schema.json` and property, property-stereotype, relation-stereotype, and aggregation-kind documentation under `website/docs/`.
- JavaScript representation and language structures: https://github.com/OntoUML/ontouml-js
- Catalog: https://github.com/OntoUML/ontouml-models
  - Historical prior inspection snapshots: 198 JSON models at `8ea0398cc273a49d9ea28aa534b1bb0316c6687c`; 202 JSON files at `2a60b2f77f9e43734d1fdd98ebdec954a840dc18`. These are historical scopes, not current counts.
  - The retained RD-09 study reported 84 enumerations and 290 direct literals in the latter snapshot, without malformed or partially transformable direct literals observed. This supports proportionate investigation, not a claim that malformed inputs are impossible.
- OWL 2 structural specification, Second Edition, especially property simplicity and global restrictions (§§11.1–11.2): https://www.w3.org/TR/2012/REC-owl2-syntax-20121211/
- Standard provenance/metadata references, if a remaining question requires them: https://www.w3.org/TR/prov-o/ ; https://www.dublincore.org/specifications/dublin-core/dcmi-terms/ ; https://spdx.org/rdf/terms/

At continuation, the Architect retrieves this record and the current consolidated specification directly from GitHub. Registration and independent review status are reported separately from unresolved design state. A substantive integration conflict needs an explicit owner decision in the Architect workflow; it must not be silently resolved during record maintenance or independent review.
