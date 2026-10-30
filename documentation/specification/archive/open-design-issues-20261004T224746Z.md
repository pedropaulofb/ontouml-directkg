# OntoUML DirectKG — Open Design Issues

## Purpose and reconciled baseline

This is a non-normative state document for the next OntoUML DirectKG Architect conversation. It records unresolved design work, not requirements or an implementation backlog. Use it together with the current Documenter-maintained specification. It is not a specification and must not be supplied as required input to the Documenter.

Reconciliation used:

- The session's supplied baseline, `ontouml-directkg-current-specification(3).md`, consolidated 2026-10-01.
- The current `ontouml-directkg-current-specification(2).md`, stored version 28, whose header says **Consolidated: 2026-10-04**, original baseline 2026-09-18 and supplied baseline 2026-09-28. Its actual rule text was checked for integration.
- `2026-09-28 - remaining decisions handoff.md`, also present as `ontouml-directkg-open-design-issues.md` stored version 4, the prior open-issues document.
- Accessible session decisions, including the explicit identifier-preservation decision, external-metadata/provenance scope, and source-project/external-title choice.

Stored version 28 is a document-storage version, not a DirectKG release. References below use rule identifiers in that specification. The recovered specification contains the session's accepted transfers through **RD-04 — Failure to generate required transformation provenance**.

Every issue in the prior handoff was checked for retention, narrowing, or removal. Resolved questions are omitted; unchanged unresolved questions are retained. This reconciliation is bounded by the accessible documents and discussion, and does not establish that the entire specification is complete. Historical research findings below are retained evidence, not fresh inspections of those repositories.

## Remaining transformation semantics

### RD-17 — Remaining semantics of recognized relation stereotypes

**Status:** Partially resolved.

**Decision needed:** For recognized VP-plugin 0.5.3 relation stereotypes without an accepted specialized mapping, decide whether their semantics justify additional logical axioms, annotation, a limitation diagnostic, or ordinary transformation without extra output.

The remaining coherent groups are:

- `mediation`, `characterization`, and `externalDependence` beyond their already accepted grounding roles;
- `historicalDependence`;
- `participation`, `participational`, `creation`, `termination`, and `manifestation`;
- `bringsAbout` and `triggers`.

**Boundaries and importance:** These stereotypes can express commitments that ordinary properties do not capture, but intuitive names do not justify functionality, transitivity, chains, or other characteristics. Material–relator/mode chains and their three modes, comparative–quality limitations, the covered mereological stereotypes, instantiation, and generic relation-valued connectors are settled by DK-REL-07–08, DK-REL-17–19, DK-GEN-04, and DK-INS-01–03.

**Alternatives:** Justified OWL axioms preserve more semantics but can affect profile compatibility; annotations preserve declarations without logical enforcement; limitation diagnostics expose loss; ordinary mapping alone is lighter but requires an explicit preservation boundary. No blanket alternative is accepted.

**Next investigation:** Examine authoritative meaning and actual 0.5.3 encoding for one coherent group at a time. The 2013 transformation paper is precedent, not authority. Coordinate profile consequences with RD-04. No new temporal or semantic-validation subsystem is implied.

### RD-18 — Property stereotypes `begin` and `end`

**Status:** Open.

**Decision needed:** Determine eligible source-property kinds, any naming effect, representable event-boundary semantics, and annotation or diagnostic treatment.

**Boundaries:** These are property stereotypes, not relation stereotypes. Ordinary property identity, labels, types, and cardinalities remain applicable. This issue does not authorize a temporal reasoning subsystem.

**Alternatives and trade-offs:** A justified logical mapping could preserve event-boundary meaning; annotations retain declarations without enforcement; explicit non-representation with a diagnostic exposes the limitation. None is accepted.

**Evidence and next step:** Verify the VP-plugin 0.5.3 property export and authoritative OntoUML meaning before comparing mappings. Coordinate with RD-17 where event semantics overlap, RD-27 for annotation treatment, and RD-04 for profile consequences.

### RD-20 — Residual placement of derived-status annotations

**Status:** Partially resolved; placement only.

**Decision needed:** Specify where the accepted `isDerived` annotation belongs when one source element corresponds to multiple generated resources, and what happens when it generates no resource.

**Resolved boundary:** DK-GEN-05 already requires comments for explicit boolean values, INFO only for `true`, no inferred derivation semantics, and no suppression of ordinary transformation. It expressly leaves these placement cases unresolved. Explicit derivation connectors retain their independent mappings.

**Why it matters:** A relation can generate primary and inverse properties, while intentionally omitted connectors and externally mapped primitives may have no local resource. Copying comments indiscriminately can misstate which declaration was supplied.

**Alternatives:** Select one designated generated resource; annotate every semantically corresponding resource; or define case-specific placement and omission. These differ in fidelity and duplication. No placement alternative is accepted.

**Next step:** Compare a small set of actual multi-resource and no-resource cases and specify placement and associated diagnostic applicability together. Preserve existing intentional omissions; do not create out-of-scope resources merely to carry the flag. Coordinate with RD-27 without assuming its description placements also govern derived status.

## Names, labels, and source metadata

### ODI-IRI — Generic unnamed-element and exceptional identity boundaries

**Status:** Open.

**Decisions needed:**

- Generic handling of unnamed or unusably named elements not covered by element-specific fallbacks, particularly enumeration literals.
- Treatment of invalid or unusable supplied base IRIs.
- Exact disposition of exceptional collisions between distinct escaped source IDs.
- Owner/source qualification in name mode when the owner/source classifier is unnamed.

**Boundaries:** DK-IRI-01–08 settle ordinary name and ID construction, base delimiters, ontology-IRI derivation, collision groups, unnamed classes, and enumeration identity. No enumeration-specific `unnamedLiteral_<id>` fallback, invented label, or silent omission is authorized. Distinct source-backed resources cannot be merged. Exceptional escaped-ID collisions are not ordinary name collisions. RD-28 annotations do not repair or change identity construction.

**Alternatives:** A deterministic synthetic name with a diagnostic, source-ID fallback where permitted, or treating the element as untransformable under the input policy. Compare only cases still outside existing fallbacks.

**Evidence:** The prior RD-09 inspection reported 202 catalog JSON files, 84 enumerations, and 290 direct literals at commit `2a60b2f77f9e43734d1fdd98ebdec954a840dc18`, with no malformed or partially transformable direct literals observed. This supports proportionate treatment, not a claim that such input is impossible.

**Dependencies and next step:** Coordinate identity failures with RD-02 and multilingual lexical selection with RD-27. Resolve a compact generic policy rather than creating a separate feature for each malformed example.

### RD-26 — Distinguishing generated fallback labels

**Status:** Partially resolved; residual annotation question only.

**Decision needed:** Whether a generated fallback label needs an explicit machine-readable distinction from a source-authored label, and, if so, its standard-vocabulary representation.

**Boundaries:** DK-LBL-01 and §15 settle `--relation-labels`, its default, source-label precedence, fallback lexical source, both IRI strategies, and Python parity. DK-LBL-02 excludes generated fallback labels from source-language propagation, including the override. None of those choices is reopened.

**Alternatives and trade-offs:** No additional marker keeps output light; an explicit standard-vocabulary representation can help consumers distinguish authored terminology but adds statements and may require a richer annotation structure. No marker or vocabulary has been accepted. DK-GEN-11 forbids DirectKG-specific metadata predicates; a missing appropriate standard term cannot be filled by inventing one.

**Next step:** Determine whether the distinction needs RDF representation and, only if so, identify a semantically appropriate standard representation. This is the remaining distinction question from the prior RD-26 entry, not a proposal for general label provenance.

### RD-27 — Residual multilingual naming and source-metadata scope

**Status:** Partially resolved; one naming clarification and evidence-limited metadata questions.

**Decisions needed:**

1. Select the lexical value used for name-based IRI construction and generated naming candidates when a supported `languageString` contains multiple localized names or role names. Preserving all labels does not select one lexical naming input.
2. Resolve project-description placement if that field is actually supported, and establish treatment of any other previously raised descriptive fields only where the supported exporter provides evidence for them.

**Boundaries:** Language carriers, precedence, multilingual source-literal preservation, direct description placements, project-name labels, external metadata mappings, and excluded language sources are settled. DK-INV-11 now explicitly distinguishes plain exporter input from the bounded language enrichment, while leaving multilingual inverse-IRI candidate selection unspecified. DK-LBL-02 expressly leaves project-description placement unresolved. The bounded enrichment does not enable unrelated newer-schema metadata. Package descriptions and custom assignments are intentionally omitted. The seven-field external whitelist cannot be expanded through this issue.

**Why it matters:** The new multilingual input allowance can supply several lexical candidates where earlier naming rules assumed one. An implementation-selected language or object-key order could change IRIs despite equivalent input.

**Alternatives:** A declared deterministic selection rule, an explicitly selected preference, or an identity fallback where no unique lexical candidate exists; each must preserve accepted labels and avoid translation. No alternative is accepted. For project descriptions and other source metadata, compare an explicit standard annotation mapping with recognized omission only after establishing actual input support.

**Evidence gaps and next step:** Inspect supported `languageString` values and the name-selection paths, then bring the lexical-selection decision back to the Architect. For other metadata, verify the 0.5.3 exporter rather than treating standalone-schema capability as authorization. Coordinate naming with ODI-IRI, generated labels with RD-26, and ontology-level placement with RD-05.

### ODI-DATATYPES — Primitive and alias registry boundary

**Status:** Open.

**Decision needed:** Decide whether the controlled registry in DK-DAT-02 is the complete supported contract and which additional semantic aliases, if any, are justified.

**Boundaries:** Lexical normalization followed by exact lookup, distinct XSD meanings, `void`, and custom-datatype reification are settled. Examples of aliases do not register them. Fuzzy matching is excluded.

**Alternatives:** Freeze the current registry or add only aliases evidenced in supported exports and justified by exact semantics. A larger registry can avoid unnecessary custom-type reification but risks incorrect equivalence if aliases are guessed.

**Next step:** Compare actual 0.5.3 primitive spellings against DK-DAT-02. Registry-maintenance policy belongs here only insofar as it changes the public mapping contract.

## Ontology identity and provenance boundaries

### RD-05 — Remaining vocabulary identity, versioning, and in-memory digest boundary

**Status:** Partially resolved; in-memory canonicalization explicitly depends on a separate decision.

**Decisions needed:**

- Select the concrete stable `dkgm` ontology URI `U`.
- Determine the remaining `owl:versionIRI` policy for the reusable vocabulary and generated ontologies.
- Decide whether canonicalized in-memory source digests are supported at all; if supported, specify their canonicalization and distinguish them from exact-file-byte digests.

**Boundaries:** DK-GEN-04 settles the stable latest-version import target and `U#` property namespace. DK-IRI-01 settles generated ontology identity with no independent ontology-IRI control. Versioning must not replace the accepted stable import with a pinned release. DK-GEN-08–11 settle project/external metadata, provenance modes, standard vocabularies, and file-digest boundaries. The external title supplements the project label under a different predicate; precedence is not open.

**Why it matters:** `U` is still a placeholder in a mandatory import. Version identity affects consumers without changing the accepted entity namespace. Canonicalization determines what an in-memory digest identifies and whether two equivalent inputs receive the same digest.

**Alternatives and trade-offs:** Choose a durable controlled URI suitable for the accepted hash namespace; no concrete candidate is recorded as accepted. For version IRIs, compare explicit version identity with deliberate omission where no reliable version exists. For in-memory digests, retain the current absence of an original-file digest or adopt a separately specified canonical representation. Do not fabricate file bytes or a self-referential embedded digest.

**Dependencies and next step:** Select the public identity/versioning policy without prescribing deployment tooling. Coordinate source descriptions with RD-27 and output contracts with RD-04. Canonicalized in-memory digests remain unsupported unless their separate rule is accepted; their absence alone is not a required-provenance failure.

## Structural recovery and public output contract

### RD-02 — Residual structural recovery

**Status:** Partially resolved.

**Decisions needed:** Define material recovery boundaries for invalid/duplicate identifiers; exceptional escaped-ID collisions; dependent unresolved references; missing/malformed generalization-set membership containers and duplicate memberships; categorizer/powertype recovery after member failure; and when structural failure prevents meaningful document-level processing even under `best-effort`.

**Boundaries:** DK-DIAG-03, DK-DIAG-05, DK-DIAG-09–13, DK-CLS-09, and DK-REL-20 already settle substantial recovery and singleton boundaries. Do not reapply singleton completeness to one survivor of a failed larger set. Metadata-file and provenance failure policies are independently settled by DK-GEN-09–10.

**Constraints and alternatives:** Compare abort with omission of affected contributions where identity and references remain unambiguous. Recovery cannot guess IDs/endpoints, merge source elements, attach axioms to the wrong resource, close an incomplete class set, or deliver invalid RDF. No exceptional collision fallback is accepted.

**Next step:** Use concrete in-scope cases, coordinated with ODI-IRI, to establish a compact recovery rule. Public delivery/reporting follows RD-04; this does not require a general validation subsystem or an exhaustive malformed-input taxonomy.

### RD-04 — Remaining output, profile, report-schema, and delivery contract

**Status:** Partially resolved.

**Decisions needed:**

- Supported ontology serializations and default; prefix policy; any serialization-order guarantee beyond deterministic identity.
- A precise general OWL conformance/profile claim.
- Exact diagnostic codes, shared JSON envelope/member names, required fields, and aggregation rules; any necessary console requirements beyond the accepted diagnostics.
- Externally observable handling of ontology-output delivery failure and unexpected runtime failure, including their relation to existing exit-code precedence and already produced results/diagnostics.

**Boundaries:** DK-DIAG-04–05 and §15 settle semantic CLI/Python parity, structured Python diagnostics, separate JSON export, three transformation outcomes, suppression of aborted ontology output, and the existing exit-code mapping. DK-GEN-10 settles required-provenance generation failure and sidecar-delivery failure. These are not pending design questions. Sidecar Turtle does not select the ontology serialization.

**Why it matters:** Consumers need a usable output and diagnostic contract. Existing chains, disjointness, property inclusions, and imports do not guarantee OWL 2 DL. A profile statement must be accurate rather than calling every non-DL result “OWL Full.” Delivery failures must not be confused with transformation outcomes.

**Alternatives and trade-offs:** A small explicitly supported serialization set versus broader format support; deterministic serialized presentation versus graph/identity determinism alone; a qualified conformance statement versus a stronger guarantee that would need justification against accepted mappings. The report can use a fixed shared envelope with diagnostic records, but no concrete schema is accepted. Remaining failure classes can share a documented failure status or have distinct statuses; no mapping is selected here.

**Dependencies and next step:** Discuss this as one public-output contract after the remaining semantic/profile questions and RD-02 boundaries. Preserve all accepted severities, silence requirements, diagnostics mirroring, and delivery precedence. Do not turn unspecified Python signatures, exception classes, or file-writing internals into Architect backlog items.

## Source-scope evidence

### ODI-INSTANCES — Applicability of general instance-data transformation

**Status:** Blocked on source-scope evidence; no feature expansion accepted.

**Question:** Does VP-plugin 0.5.3 export additional general instance data within the current input contract that needs a mapping beyond higher-order classification, enumeration values, and explicit instantiation associations?

**Boundaries:** DK-HO-01–04, DK-INS-01–03, and RD-09 settle those existing cases. A conditional future-support statement does not create a present requirement.

**Next investigation:** Inspect the exporter path and representative JSON. If no additional in-scope construct exists, close the evidence check. If one exists, identify its exact source shape before discussing identity, typing, assertions, or recovery. Do not design a general instance subsystem based solely on standalone-schema capability.

## Suggested dependency order

This is an advisory discussion order, not an accepted requirement or resolution.

1. Advance the remaining substantive semantics in RD-17, followed by RD-18 and the bounded RD-20 placement question.
2. Resolve multilingual naming under RD-27 with ODI-IRI; address RD-26's remaining distinction question only at its recorded scope.
3. Select RD-05's concrete vocabulary identity and versioning; complete evidence checks for other source metadata, primitive aliases, and instances where actual supported input warrants them.
4. Consolidate RD-02 recovery and the remaining RD-04 public-output contract in coherent batches.

RD-04's profile statement depends on the final semantic mappings. RD-02 and ODI-IRI share identity-failure cases. RD-27 and ODI-IRI share lexical-name selection. RD-05 and RD-27 share ontology-level source metadata. The in-memory digest question does not block the already accepted file-based provenance behavior.

## Retained research anchors

- Supported exporter: https://github.com/OntoUML/ontouml-vp-plugin/releases/tag/0.5.3
- Exporter repository: https://github.com/OntoUML/ontouml-vp-plugin
  - Previously inspected paths include `src/main/java/it/unibz/inf/ontouml/vp/utils/Stereotype.java`, `src/main/java/it/unibz/inf/ontouml/vp/model/ontouml/model/RelationStereotype.java`, and VP-to-OntoUML property/association transformers.
- Metamodel: https://github.com/OntoUML/ontouml-metamodel
- Schema: https://github.com/OntoUML/ontouml-schema
  - Relevant retained paths: `dist/ontouml-schema.json` and property, property-stereotype, relation-stereotype, and aggregation-kind documentation under `website/docs/`.
- Language representation implementation: https://github.com/OntoUML/ontouml-js
- Catalog: https://github.com/OntoUML/ontouml-models
  - Historical inspection scopes: 198 JSON models at `8ea0398cc273a49d9ea28aa534b1bb0316c6687c`; 202 JSON files at `2a60b2f77f9e43734d1fdd98ebdec954a840dc18`. These are snapshots, not current corpus counts.
- Catalog metadata guidance inspected during the session: https://github.com/OntoUML/ontouml-models/blob/master/scripts/validate-metadata-yaml.md
  - Pinned example: https://github.com/OntoUML/ontouml-models/blob/617dc16ee30a94d8c0587463f1b9ba3b3aef07d7/models/amaral2019rot/metadata.yaml
- OWL 2: https://www.w3.org/TR/owl2-syntax/
- Standard provenance/metadata references: https://www.w3.org/TR/prov-o/ ; https://www.dublincore.org/specifications/dublin-core/dcmi-terms/ ; https://spdx.org/rdf/terms/
- Historical precedent: *An Automated Transformation from OntoUML to OWL and SWRL* (2013), not a binding DirectKG authority.

No issue is resolved by this handoff. Alternatives remain non-normative. The next Architect session must pair this document with the specification consolidated after the accepted transfers. If integration reveals a substantive conflict, bring its unresolved clarification back to the Architect rather than choosing a resolution during documentation.
