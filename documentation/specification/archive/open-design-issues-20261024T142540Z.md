# OntoUML DirectKG — Open Design Issues

## Purpose, baseline, and incomplete reconciliation

This is a **non-normative, incomplete state document** for a subsequent OntoUML DirectKG Architect conversation. It records remaining design questions recoverable from the available sources. It is not a specification or an implementation backlog. Use it together with the current Documenter-maintained specification; it must not be supplied as required input to the Documenter.

The actual supplied sources were recovered and inspected:

- `2026-10-05 - specification handoff(2).md`, titled *OntoUML DirectKG Current Specification*: **Consolidated: 2026-10-04**, **Original baseline: 2026-09-18**, **Supplied baseline: 2026-09-28**. No DirectKG release number is asserted.
- `2026-10-05 - remaining decisions handoff(1).md`, titled *OntoUML DirectKG — Open Design Issues*.
- Accessible explicit user decisions in this Architect conversation. Earlier proposals and complete decision-transfer messages are not all accessible in full.

**Do not use this file as a complete next-session handoff yet.** Several acceptances refer only to an unavailable option or recommendation. Consequently, a complete issue-by-issue disposition and accepted-transfer audit cannot be established without the original proposal/transfer text. In particular, reconciliation still needs that text for RD-20; RD-27's multilingual selection and project-description discussions; ODI-IRI's owner/source qualification and supplied-base-IRI discussions; and RD-04's later prefix, textual-repeatability, and ontology-delivery discussions. These are access limitations, not new design issues or permission to reopen accepted decisions. Their detailed rules have not been reconstructed here.

The entries below preserve the recoverable remaining questions and evidence, with resolved portions omitted where the accessible acceptance is explicit. Absence of an issue or subquestion from this partial file is not evidence that it was resolved. Restore the missing discussion, account for every prior issue, and finish reconciliation before replacing the prior handoff. Integration uncertainty is reported separately from this document.

## Remaining transformation semantics

### RD-17 — Remaining semantics of recognized relation stereotypes

**Status:** Partially resolved in the supplied state; remaining groups retained pending completion of the session audit.

**Decision needed:** For recognized VP-plugin 0.5.3 relation stereotypes without an accepted specialized mapping, determine whether to add justified logical axioms, preserve a declaration through annotation, report a semantic limitation, or apply the ordinary mapping without extra output.

The recorded remaining groups are:

- `mediation`, `characterization`, and `externalDependence` beyond their accepted grounding roles;
- `historicalDependence`;
- `participation`, `participational`, `creation`, `termination`, and `manifestation`;
- `bringsAbout` and `triggers`.

**Constraints and resolved boundary:** The lightweight domain-graph goal and prohibition on invented semantics remain applicable (§3.1). Material–relator/mode chains and their modes, comparative–quality limitations, covered mereological relations, instantiation, and generic relation-valued endpoints already have accepted treatment: DK-REL-07–08, DK-REL-17–19, DK-GEN-04, and DK-INS-01–03. Do not reopen them through this issue. A stereotype's name alone does not justify functionality, transitivity, or a property chain.

**Alternatives and trade-offs — non-normative:** Additional justified axioms can preserve more meaning but affect OWL compatibility; annotations preserve declarations without logical enforcement; limitation diagnostics expose loss; ordinary mapping alone is lighter but needs a clear preservation boundary. No blanket alternative is recorded as accepted for these remaining groups.

**Evidence and next investigation:** Study one coherent group using authoritative language sources and the actual 0.5.3 export representation. Distinguish language semantics from exporter recognition and from schema capability. The 2013 OntoUML-to-OWL/SWRL paper is precedent, not project authority. Coordinate profile effects with RD-04. No temporal reasoning or semantic-validation subsystem is implied.

### RD-18 — Property stereotypes `begin` and `end`

**Status:** Open in the supplied state; no fully accessible session resolution recovered.

**Decision needed:** Determine the eligible source-property kinds, any naming effect, representable event-boundary semantics, and annotation or diagnostic treatment.

**Constraints:** These are property stereotypes rather than relation stereotypes. Existing property identity, labels, typing, and cardinality rules continue to apply. This question does not authorize a temporal reasoning subsystem or semantic validation.

**Alternatives — non-normative:** A justified logical mapping; annotations without logical enforcement; or explicit non-representation with a limitation diagnostic. Their fidelity and complexity differ; none is recorded as accepted for this issue.

**Next investigation and dependencies:** Verify the VP-plugin 0.5.3 property transformation and authoritative meaning first. Coordinate event semantics with RD-17 and OWL consequences with RD-04. Do not assume that descriptions or derived-status annotations determine stereotype treatment.

## Structural identity and recovery

### ODI-IRI — Exceptional collisions between distinct escaped source IDs

**Status:** Partially resolved overall; this exceptional identity question remains recorded separately from the accepted generic source-ID naming fallback.

**Decision needed:** Specify the exact disposition if distinct source identifiers produce a colliding escaped identifier under the applicable identity construction.

**Constraints and resolved boundary:** DK-IRI-05 requires injective technical escaping; DK-IRI-07 prohibits treating an exceptional escaped-ID collision as an ordinary name collision. DK-CONF-02 prohibits merging distinct resources. The generic fallback explicitly accepted in this session uses existing source IDs and existing escaping/collision rules; it does not establish recovery for an exceptional identity collision. Duplicate source-element IDs are separately governed by the user's explicit RD-02 decision to abort under every input policy.

**Alternatives and trade-offs — non-normative:** The prior structural-recovery comparison is abort versus omission of affected contributions only where identities and references remain unambiguous. No exceptional-collision repair is accepted. Ordinary name-collision suffixing cannot silently be substituted for the missing disposition.

**Evidence gap and next step:** Establish exactly which failure the exceptional boundary represents despite the injectivity requirement, then discuss a simple deterministic disposition with RD-02. Do not infer a corpus occurrence or develop elaborate recovery without evidence. This does not reopen the generic fallback, owner qualification, base-IRI validation, or ordinary naming collisions; the owner-qualification and base-IRI discussions still require their complete accepted texts for this handoff's audit.

### RD-02 — Remaining structural recovery boundaries

**Status:** Partially resolved; duplicate source-element IDs removed from the unresolved questions.

**Decisions still recorded:**

- What constitutes a missing or invalid source identifier, and which affected contributions can be omitted safely when processing continues.
- Recovery for dependent unresolved references beyond existing explicit rules.
- Missing or malformed generalization-set membership containers and duplicate memberships.
- Categorizer/powertype recovery after a member cannot be resolved or transformed.
- Which structural failures prevent meaningful document-level processing even under `best-effort`.
- The exceptional escaped-ID collision disposition shared with ODI-IRI.

**Constraints and accepted boundary:** The user's explicit **RD-02 — Option A accepted** decision requires abortion for duplicate source-element IDs under every input policy. That question is resolved; documentation or transfer uncertainty does not reopen it. §3.4 and DK-DIAG-05 distinguish structural processability from OntoUML semantic validation. Recovery cannot invent missing data, merge source elements, attach axioms to the wrong resource, or deliver invalid RDF.

DK-DIAG-03 already prevents both directional properties when required relation endpoints or their identifiers cannot resolve. DK-DIAG-09–13, DK-CLS-09, and DK-REL-20 settle substantial local recovery. In particular, failure in a larger class generalization set must not produce coverage from survivors or trigger singleton completeness merely because one member survives. Metadata-file and provenance failures retain their separate DK-GEN-09–10 policies.

**Alternatives — non-normative:** Abort where identity or document processing is ambiguous; omit only affected contributions where safe independent transformation remains possible. Preserve already accepted severities and nonfatal fallbacks. No general malformed-input taxonomy or new validation subsystem is implied.

**Next investigation:** Use a few concrete supported-export cases and fundamental correctness cases to specify the residual boundaries. Prioritize observed problems and simple safe behavior, following the user's session guidance. Coordinate identity with ODI-IRI and externally observable reporting with RD-04.

## Ontology identity and provenance

### RD-05 — Vocabulary identity, versioning, and in-memory source digests

**Status:** Partially resolved; the in-memory digest extension requires a separate decision.

**Decisions needed:**

- Determine remaining ontology-versioning matters outside the accepted DKGM `U/X.Y.Z` pattern, including generated-ontology versioning.
- Decide whether canonicalized in-memory source digests are supported at all; if supported, define the canonical representation and distinguish its digest from an exact-file-byte digest.

**Constraints and resolved boundary:** DK-GEN-04 requires a stable latest-version import target `U`, without a fragment, and derives the property namespace as `U#`. The project-owner decision of 2026-10-24 selects `U = https://w3id.org/directkg/vocab/dkgm` and DKGM version IRIs `U/X.Y.Z`; versions 0.1.0 and 0.1.1 retain their numbers during the authorized pre-release identity correction. Generated imports remain unversioned. DK-IRI-01 derives the generated ontology IRI from the effective entity base and establishes no independent ontology-IRI control. Project labels, external metadata, provenance modes, and file-byte digest boundaries are governed by DK-GEN-08–11.

**Why it matters:** The mandatory import now has an accepted concrete target. Remaining version-identity decisions must preserve that target and its hash namespace. A canonical in-memory digest needs a defined identity claim and cannot masquerade as a digest of unavailable original file bytes.

**Alternatives and trade-offs — non-normative:** Compare explicit version identity with deliberate omission where no reliable version exists. For in-memory source digests, retain the current exclusion or adopt a separately specified canonical representation. These remaining alternatives are not selected by the identifier migration.

**Next discussion and dependencies:** Discuss only the remaining versioning matters; the concrete DKGM identity and its established version-IRI pattern are selected. The in-memory question does not block accepted file-based provenance: DK-GEN-10 requires exact input bytes and, in sidecar mode, final serialized ontology bytes. Absence of an explicitly excluded original-file digest for in-memory input is not a required-provenance failure. Source canonicalization and a guarantee of byte-identical Turtle output are different questions; check the complete session serialization transfer before discussing their interaction.

## Public output and diagnostics

### RD-04 — Remaining profile, diagnostic-report, and failure contract

**Status:** Partially resolved; the later session output transfers must be restored before the residual failure boundary can be audited completely.

**Remaining decisions recoverable from the supplied state:**

- A precise general OWL conformance/profile claim.
- Exact diagnostic codes and the shared JSON report envelope, member names, required fields, and aggregation rules.
- Externally observable handling of unexpected runtime failures and any output-failure classes not covered by accepted decisions, including their relationship to transformation outcomes, available results, diagnostic access, and exit-code precedence.

**Resolved boundary:** The user explicitly accepted **Turtle only for the current scope** and the console-only `--console-level {info,warning,error}` threshold, defaulting to `info`, while retaining complete JSON exports and Python diagnostic access. These are not open alternatives. Nor is adding routine INFO messages for expected transformations a remaining verbosity question. Prefixes, textual repeatability, and ontology-file delivery were also discussed and accepted by option reference; their exact accepted text must be recovered, not reopened or inferred here.

DK-DIAG-04–05 and §15 already establish structured Python diagnostics, separate JSON export, the three transformation outcomes, non-delivery of an aborted ontology, and diagnostic-delivery failure behavior. DK-GEN-10 separately establishes required-provenance construction failure and provenance-sidecar delivery failure. Preserve those boundaries. Do not assign a new failure policy during this handoff or assume that all failures are input-policy failures.

**Why it matters:** Consumers need an accurate interoperability claim and an implementable shared report contract. Accepted chains, disjointness, property inclusions, and imports do not establish a general OWL 2 DL guarantee. A profile statement must not equate every non-DL result with a specific alternative conformance claim. Delivery success and transformation outcome remain distinct.

**Alternatives and trade-offs — non-normative:** A qualified conformance statement versus a stronger justified guarantee; a fixed shared JSON envelope with diagnostic records, whose exact schema is still unselected; shared versus distinct statuses for genuinely uncovered failure classes. These comparisons do not authorize changing accepted mappings, severities, silence requirements, or delivery precedence.

**Dependencies and next step:** Restore the full later RD-04 transfers before enumerating residual failure classes or changing the exit-code table. Analyze profile consequences after the relevant RD-17/RD-18 mappings; finalize reporting with RD-02's remaining recovery boundaries. Exact Python signatures, exception classes, file-writing internals, additional console features, and optional format controls are not added as backlog items.

## Bounded source-scope evidence checks

### RD-27 — Evidence for any remaining source-descriptive fields

**Status:** Evidence-limited residual check carried from the prior document; full reconciliation of the named multilingual/project-description decisions is blocked by missing discussion text.

**Question still to verify:** Beyond the named questions addressed during this session, does any *previously raised* descriptive field actually occur within the supported export contract and still require a decision? No additional concrete field has been established by the recovered prior issue text.

**Constraints:** §3.2 permits only bounded language enrichment of already supported text fields. Newer standalone-schema capability does not authorize additional metadata mappings. Packages and their descriptions are intentionally omitted under DK-GEN-06; custom assignments are omitted under DK-GEN-07. DK-GEN-09's seven-field external metadata whitelist must not be expanded through this issue.

**Alternatives and evidence gap — non-normative:** For a concrete supported field that remains undecided, compare a justified standard annotation mapping with recognized omission. First establish that there is such a field. Do not turn this conditional evidence check into a generic metadata inventory or feature request.

**Next step:** Recover the full RD-27 decisions and any exact previously raised field names. Verify an actual 0.5.3 export path before retaining another metadata mapping question. If no concrete supported unresolved field remains, close this residual evidence check. Primitive recognition's use of the existing IRI naming selector, explicitly accepted by the user with no new diagnostics, is not reopened.

### ODI-INSTANCES — Applicability of general instance-data transformation

**Status:** Blocked on source-scope evidence; no feature expansion accepted in the supplied state.

**Question:** Does VP-plugin 0.5.3 export additional general instance data within the accepted input contract requiring a mapping beyond higher-order classification, enumeration values, and explicit instantiation associations?

**Constraints:** DK-HO-01–04, DK-CLS-10–11, and DK-INS-01–03 govern the existing cases. A conditional future-support statement is not a current requirement. Standalone-schema capability alone is insufficient evidence of supported exporter behavior.

**Next investigation:** Inspect the actual exporter path and representative JSON. If no additional in-scope construct exists, close the evidence check. If one exists, identify its exact source shape before discussing its mapping. Do not design a general instance subsystem in advance.

## Dependencies and retained evidence anchors

RD-02 and ODI-IRI share identity failures. RD-04's profile claim depends on the relevant remaining semantic mappings; its report contract depends on residual recovery and the restored failure decisions. RD-05's remaining versioning matters can be discussed independently of source-digest canonicalization. Source-scope evidence checks precede any new mapping discussion. This is a dependency description, not an accepted implementation order.

The following anchors are retained from the supplied prior issues and baseline. They identify research starting points, not fresh inspection or proof that all relevant files were examined during this reconciliation:

- Supported exporter release: https://github.com/OntoUML/ontouml-vp-plugin/releases/tag/0.5.3
- Exporter code: https://github.com/OntoUML/ontouml-vp-plugin
  - Retained inspected paths: `src/main/java/it/unibz/inf/ontouml/vp/utils/Stereotype.java`, `src/main/java/it/unibz/inf/ontouml/vp/model/ontouml/model/RelationStereotype.java`, and VP-to-OntoUML property/association transformers.
- Foundational metamodel: https://github.com/OntoUML/ontouml-metamodel
- JSON schema reference: https://github.com/OntoUML/ontouml-schema
  - Retained paths: `dist/ontouml-schema.json` and documentation under `website/docs/` for properties, property/relation stereotypes, and aggregation kinds. Schema capability is distinct from the accepted export contract.
- JavaScript representation: https://github.com/OntoUML/ontouml-js
- Catalog: https://github.com/OntoUML/ontouml-models
  - Historical prior inspection scopes: 198 JSON models at `8ea0398cc273a49d9ea28aa534b1bb0316c6687c`; 202 JSON files at `2a60b2f77f9e43734d1fdd98ebdec954a840dc18`. These are historical snapshots, not current counts or exhaustive claims about possible inputs.
  - The prior RD-09 inspection reported 84 enumerations and 290 direct literals in the latter scope, without malformed or partially transformable direct literals observed. Sample/corpus absence does not establish impossibility.
- Catalog metadata guidance: https://github.com/OntoUML/ontouml-models/blob/master/scripts/validate-metadata-yaml.md
- Pinned metadata example: https://github.com/OntoUML/ontouml-models/blob/617dc16ee30a94d8c0587463f1b9ba3b3aef07d7/models/amaral2019rot/metadata.yaml
- OWL 2: https://www.w3.org/TR/owl2-syntax/
- Standard metadata/provenance references: https://www.w3.org/TR/prov-o/ ; https://www.dublincore.org/specifications/dublin-core/dcmi-terms/ ; https://spdx.org/rdf/terms/
- Historical design precedent: *An Automated Transformation from OntoUML to OWL and SWRL* (2013); it is not normative for DirectKG.

No issue is resolved by preparing this document. Alternatives remain non-normative. Complete the missing-source reconciliation first. The next Architect session must pair the resulting handoff with the specification consolidated by the Documenter after the accepted transfers. If integration exposes a substantive conflict, return the unresolved clarification to the Architect workflow; do not select a resolution during documentation.
