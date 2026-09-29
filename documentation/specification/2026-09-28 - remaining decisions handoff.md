# OntoUML DirectKG — Open Design Issues

## Purpose, authority, and reconciliation scope

This is a non-normative state document for the next OntoUML DirectKG Architect conversation. It records only unresolved design work. It MUST be used together with the current Documenter-maintained specification and MUST NOT be supplied to the Documenter as normative project input.

This handoff was reconciled against:

- `ontouml-directkg-current-working.md`, stored version 7, titled **OntoUML DirectKG Current Specification**, with original baseline date 2026-09-18 and consolidation date 2026-09-28;
- `2026-09-18 - remaining decisions handoff.md`, the prior non-normative open-issues state; and
- the accessible Architect-session discussion and explicit acceptances through 2026-09-28.

The stored file version is not a DirectKG release number. The current specification is authoritative for integrated decisions. This handoff is complete relative to those supplied sources and the accessible session record; it does not prove that inaccessible conversations or unsupplied project material contain no additional issue.

The prior entries RD-14, RD-16, RD-24, and RD-25 are omitted because the current specification now contains their accepted behavior. RD-17 remains only for recognized relation stereotypes whose additional semantics are still undecided. RD-04, ODI-CONTROLS, RD-05, and RD-27 are narrowed below to exclude the decisions integrated during this session.

## Source processing, output, and public controls

### RD-02 — Residual structural recovery

**Status:** Partially resolved.

**Decision still needed:** Define only the material recovery boundaries that remain unspecified when structurally unusable source elements are encountered, especially:

- invalid or duplicate source identifiers;
- collisions between distinct identifiers after ID escaping;
- interacting unresolved references where omission of one element affects otherwise transformable elements;
- missing or malformed generalization-set membership containers and duplicate memberships;
- categorizer or powertype handling after partial member failure; and
- the threshold at which a structural failure prevents meaningful processing of the complete document rather than permitting partial output under `best-effort`.

**Resolved boundary:** DK-DIAG-03 and DK-DIAG-05 establish structural severity and policy-dependent continuation. DK-DIAG-09–13 settle missing cardinalities, multiplicity recovery, empty generalization sets, and enumeration-list failures. DK-CLS-09 settles recovery of class-set disjointness and coverage after partial member failure. These cases MUST NOT be reopened under this issue.

**Why it matters and constraints:** Recovery must not guess identifiers or endpoints, merge distinct source elements, attach axioms to the wrong resource, or close a class over an incomplete set. Every delivered result must remain syntactically valid RDF. The issue is limited to observable in-scope behavior; it does not require a general validation subsystem or a separate rule for every malformed combination.

**Alternatives still open:** Depending on whether identity and references remain unambiguous, a failure may require document-level abort or may permit omission of the affected contribution under `best-effort`. No general fallback has been accepted for exceptional escaped-ID collisions or the residual set cases.

**Dependencies and next step:** Coordinate identifier cases with ODI-IRI and externally visible result/partial-output behavior with RD-04. Examine concrete unresolved cases before adding rules; absence of an example in the inspected corpus is not proof that a case is impossible.

### RD-04 — Output, profile, diagnostic schema, and result contract

**Status:** Partially resolved.

**Decision still needed:** Complete the public output and result contract:

- supported RDF serializations and the default serialization;
- prefix policy and any output-order determinism guarantee beyond the accepted identity and collision determinism;
- the declared OWL profile or precise conformance claim for default and configured outputs;
- exact diagnostic identifiers, JSON member names, required fields, aggregation/envelope format, and report schema;
- console presentation requirements, if any, beyond preservation of normal console diagnostics;
- externally observable success, failure, and partial-output status for the CLI and Python API;
- whether RDF output is delivered or suppressed on abort and how partial output is identified; and
- the externally visible outcome when the requested diagnostics file cannot be created or written.

**Resolved boundary:** DK-DIAG-04 and §15 require an optional persistent JSON diagnostic mirror at a complete user-supplied path, no file by default, preservation of console diagnostics, and inclusion of every diagnostic actually produced. The mirror does not create new diagnostics. DK-INS-02 fixes the content boundary for discarded instantiation-association values. Existing transformation rules continue to determine severity, continuation, and whether a diagnostic is produced.

The accepted material-property chains, relation-property disjointness, UML property inclusion, and imported `dkgm` chains do not establish a general OWL-profile guarantee. DK-DIAG-07 already requires its specific compatibility notice when material-property chains are emitted. The accepted `dkgm` mapping preserves source-specific cardinality and asymmetry where its subproperties remain simple, but does not guarantee that every complete output is OWL 2 DL.

**Why it matters and constraints:** Callers require an unambiguous output and failure contract, and the exact persistent report must be machine-processable. The solution must preserve all existing silence requirements, diagnostic severities, and intentional-loss boundaries. It must describe profile compatibility precisely rather than labeling every non-DL case simply as “OWL Full.”

**Alternatives still open:** The prior state retained stderr, logs, structured reports, or combinations as delivery possibilities; persistent JSON plus console output is now accepted, but their exact presentation and the Python-facing result remain undecided. No serialization, report schema, exit-code model, or general profile claim has been selected.

**Dependencies and next step:** Coordinate structural/partial results with RD-02, ontology identity and prefixes with RD-05 and ODI-IRI, metadata with RD-27 and RD-31, public controls with ODI-CONTROLS, and the final profile statement with remaining semantic mappings. Produce a focused output/result proposal without prescribing ordinary internal architecture.

### ODI-CONTROLS — Remaining transformation-control interface choices

**Status:** Partially resolved.

**Decision still needed:** Select:

- the exact CLI name for the inverse-generation modes `all`, `informed`, `named`, and `none`;
- the exact CLI name for the default-off typed-attribute `owl:allValuesFrom` option;
- the exact name of the diagnostics-file option, for which `--diagnostics-file PATH` is currently illustrative;
- whether and how each established transformation control is exposed by the Python library;
- whether the CLI and Python library require exact option parity; and
- whether persistent diagnostics export has a Python-library counterpart.

**Resolved boundary:** The values, defaults, and transformation effects of established controls are not open. The diagnostics-file option is mandatory on the CLI, accepts a complete path, preserves console diagnostics, and creates no file when absent. No mereology-specific control exists for DK-GEN-04, DK-REL-19, or DK-PROP-04. `--material-property-chains` controls only the accepted material–relator and material–mode chains.

**Why it matters and constraints:** These choices define the public means of requesting already accepted behavior. They do not require decisions about internal configuration objects, package structure, dependencies, or implementation architecture.

**Dependencies and next step:** Resolve the enabled value-restriction behavior under ODI-VALUE-RESTRICTIONS, and coordinate diagnostic/results exposure with RD-04.

## Hierarchies, restrictions, and relation semantics

### RD-13 — Singleton relation-generalization-set completeness

**Status:** Partially resolved; one bounded case remains.

**Decision still needed:** Define the treatment of a fully resolved relation generalization set with `isComplete: true` and exactly one distinct specific relation, including whether any generated named inverse participates in the representation.

**Resolved boundary:** DK-CLS-06–09 settle class-set disjointness and completeness, including fully resolved class singletons and partial class-set recovery. DK-REL-15 settles relation-property disjointness and corresponding named-inverse pairs. DK-REL-16 settles the limitation and warning for complete relation sets with two or more distinct specific relations. Empty sets follow DK-DIAG-12. None of those rules determines the relation-singleton case.

**Why it matters and constraints:** A singleton does not require an object-property union, so the reason for the multi-member limitation does not automatically apply. Any mapping must preserve primary directions and the accepted inverse-generation modes, and it must not force generation of an inverse.

**Alternatives still open:** A property-equivalence treatment, the same omission/diagnostic policy used for multi-member sets, or another justified OWL representation require explicit comparison. No alternative or recommendation is accepted.

**Dependencies and next step:** Analyze the case under DK-REL-14 and DK-INV-12, using the OWL 2 object-property axioms. Keep malformed/duplicate membership recovery under RD-02 rather than expanding this issue.

### RD-17 — Remaining semantics of recognized relation stereotypes

**Status:** Partially resolved and substantially narrowed.

**Decision still needed:** For recognized VP-plugin 0.5.3 relation stereotypes not already given a specialized semantic mapping, decide whether they generate justified OWL axioms beyond ordinary relation transformation and naming, are preserved only through annotations or diagnostics, or deliberately receive no additional output.

The remaining coherent groups include:

- `mediation`, `characterization`, and `externalDependence` beyond their accepted transformation-time role in material–mode and material–relator patterns;
- `historicalDependence`;
- `participation`, `participational`, `creation`, `termination`, and `manifestation`; and
- `bringsAbout` and `triggers`.

For each group, determine whether the supported semantics justify generic superproperties, property characteristics, property chains, restrictions, or only an explicit limitation. Functionality, inverse functionality, transitivity, or other characteristics MUST NOT be inferred from intuitive names alone.

**Resolved boundary:** DK-REL-07–08 settle material–relator and material–mode grounding and optional chains, including same-class ambiguity. DK-REL-18 settles comparative–quality behavior. DK-GEN-04 and DK-REL-19 settle the four covered mereological stereotypes. DK-INS-01–03 settle `instantiation`. DK-REL-17 supplies the generic behavior for otherwise unsupported relation-valued connectors. These decisions MUST NOT be reopened here.

**Why it matters and constraints:** Remaining stereotypes carry ontological commitments that ordinary domain/range and inverse axioms may not preserve, but DirectKG must remain lightweight and must not invent unsupported semantics. The 2013 OntoUML-to-OWL/SWRL transformation is precedent, not authority. Any new profile consequence must be coordinated with RD-04.

**Alternatives still open:** Supported logical axioms, lightweight annotation, explicit non-representation with an appropriate diagnostic policy, or ordinary transformation without additional semantics remain possible depending on the authoritative semantics of each coherent group. No blanket treatment or accepted recommendation exists.

**Evidence gap and next step:** Reinspect the authoritative language meaning and actual VP-plugin 0.5.3 encoding for one coherent stereotype group at a time. Distinguish OntoUML semantics from exporter defaults and from DirectKG design.

### RD-18 — Property stereotypes `begin` and `end`

**Status:** Open.

**Decision still needed:** Define the treatment of the recognized property stereotypes `begin` and `end`: eligible source-property kinds, any naming effect, representable event-boundary semantics, annotation or diagnostic treatment, and behavior when their source meaning cannot be preserved logically.

**Context and constraints:** These are property stereotypes, not relation stereotypes, and do not inherit RD-17 behavior automatically. Ordinary property identity, labels, types, and cardinalities remain governed by their accepted rules. The mapping must not introduce a temporal reasoning subsystem without an explicit in-scope decision.

**Alternatives still open:** A supported semantic mapping, annotation-only preservation, or explicit non-representation with a defined diagnostic policy. None is accepted.

**Evidence gap and next step:** Verify how VP-plugin 0.5.3 exports these stereotypes and examine authoritative OntoUML event-boundary semantics. Coordinate annotation choices with RD-27 and output/profile consequences with RD-04.

### ODI-DISJOINT — Serialization of stereotype-based class disjointness

**Status:** Open; semantics are resolved and only representation remains.

**Decision still needed:** Select the RDF/OWL serialization for the ultimate-sortal and cross-group class disjointness required by DK-CLS-03 and DK-CLS-04 without changing which class pairs are disjoint.

**Why it matters and constraints:** A single `owl:AllDisjointClasses` list spanning several stereotype groups would incorrectly add intra-group disjointness. The representation must preserve exactly the accepted pair relation and should remain deterministic.

**Alternatives still open:** Pairwise `owl:disjointWith` is directly inspectable. Grouped `owl:AllDisjointClasses` encodings may be more compact but require carefully constructed groups and RDF-list traversal.

**Unaccepted recommendation:** Use pairwise `owl:disjointWith` for cross-group disjointness. This was previously recommended but has not been accepted. RD-13's pairwise serialization for generalization sets does not decide this separate rule.

**Next step:** Compare only representations of the already accepted semantics; do not introduce new disjointness pairs.

### ODI-VALUE-RESTRICTIONS — Enabled `owl:allValuesFrom` behavior and scope

**Status:** Partially resolved.

**Decision still needed:** Decide:

- whether enabling the existing typed-attribute option requires an `owl:allValuesFrom` restriction whenever the attribute type is resolvable, rather than merely permitting one; and
- whether that option remains attribute-only or also applies to ordinary relation properties.

**Resolved boundary:** DK-ATT-04 establishes one default-off option for primitive-valued and custom-datatype-valued attributes. When disabled, the restriction is forbidden; when enabled with a resolvable type, it is currently permitted but not required. Untyped and `void` attributes receive no such restriction. Cardinality requirements remain independent.

**Why it matters and constraints:** A permissive `MAY` leaves outputs variable under identical configuration unless further constrained. Extending the option to relations would broaden its semantic and public-control scope and is not implied by the accepted attribute rule.

**Alternatives still open:** Mandatory generation for every resolvable typed attribute versus retaining implementation discretion; attribute-only scope versus explicitly extending the control to ordinary relations.

**Unaccepted recommendation:** Require deterministic generation for every resolvable typed attribute when the option is enabled, while retaining attribute-only scope unless relation support is separately justified.

**Dependencies and next step:** Coordinate the option name with ODI-CONTROLS and any profile/output implications with RD-04.

## Classifier and property metaproperties

### RD-19 — `abstract` stereotype and `isAbstract`

**Status:** Open.

**Decision still needed:** Define separate target behavior for the `abstract` class stereotype and the classifier-level `isAbstract` flag, including `isAbstract` on relations: justified semantic representation, annotation, diagnostic treatment, or intentional non-representation.

**Resolved boundary:** DK-CLS-04 already uses the `abstract` stereotype for accepted cross-group disjointness. That use does not settle the remaining meaning of the stereotype or the flag.

**Why it matters and constraints:** OWL does not directly express “no direct instances except through a specialization” in the same manner as UML abstractness. The two source mechanisms MUST NOT be conflated, and any treatment must respect higher-order punning and the semantic-validation boundary.

**Alternatives still open:** Annotation, explicit limitation/diagnostic, or a separately justified semantic approximation. No recommendation is accepted.

**Next step:** Inspect actual 0.5.3 values and compare the two source concepts before selecting a mapping.

### RD-20 — `isDerived`

**Status:** Open.

**Decision still needed:** Determine whether `isDerived` on classifiers and properties is ignored, preserved as an annotation, reported diagnostically, or given justified target semantics.

**Context and constraints:** The flag is distinct from an explicit `derivation` relation and does not inherit DK-REL-08 or DK-REL-17 behavior. A single policy may distinguish classifiers from properties if their transformable meaning differs.

**Alternatives still open:** Annotation, diagnostic/limitation, semantic mapping where justified, or intentional omission. No recommendation is accepted.

**Next step:** Inspect actual exporter usage and authoritative UML/OntoUML meaning before deciding.

### RD-21 — `isExtensional`

**Status:** Open; source-shape evidence remains necessary.

**Decision still needed:** Determine whether the flag generates an axiom, an annotation, a diagnostic, no output, or is recognized only for input compatibility.

**Why it matters and constraints:** Any semantic mapping must be grounded in the actual VP-plugin 0.5.3 representation and OntoUML meaning. Legacy or standalone-schema representations do not automatically belong to the supported input contract.

**Alternatives still open:** Logical mapping, annotation, diagnostic, or recognized omission. No recommendation is accepted.

**Next step:** Verify whether and how VP-plugin 0.5.3 exports the field and inspect representative corpus values before proposing behavior.

### RD-22 — `restrictedTo`

**Status:** Open.

**Decision still needed:** Decide whether `restrictedTo` is only transformation-time information, is preserved as an annotation, or generates additional semantic constraints beyond the accepted stereotype rules.

**Why it matters and constraints:** The effective set can be broader than the usual default associated with a stereotype and may include `type`. Treatment must remain compatible with accepted punning, classifier order, powertype, and disjointness rules. DirectKG must not turn this field into semantic-appropriateness validation.

**Alternatives still open:** Internal-use only, annotation, or explicitly justified logical constraints. No recommendation is accepted.

**Next step:** Inspect the actual exported values and distinguish transformation conditions from additional output semantics.

### RD-23 — `isOrdered`

**Status:** Open.

**Decision still needed:** Select how `isOrdered: true` is treated for attributes and association ends when ordinary RDF property assertions do not preserve assignment order.

**Alternatives and trade-offs:** Silent omission is simplest but loses source information. A human-readable annotation preserves the occurrence without machine-readable order semantics. A diagnostic makes the loss visible. A list or sequence representation preserves ordering structurally but changes the output model and mapping complexity.

**Unaccepted recommendation:** Prefer lightweight annotation or diagnostic treatment over structural list/sequence reification. This has not been accepted.

**Dependencies and next step:** Coordinate any annotation with RD-27 and any structural representation or profile consequence with RD-04. First decide the required preservation level.

## Names, identifiers, labels, and datatypes

### ODI-IRI — Generic unnamed-element and exceptional IRI boundaries

**Status:** Open.

**Decision still needed:** Complete the remaining generic IRI policy for cases not covered by element-specific rules:

- unnamed source elements or names that normalize to no usable local name, especially enumeration literals;
- behavior for a syntactically invalid or unusable supplied base IRI;
- exact disposition of a collision between distinct source IDs after injective escaping; and
- name-mode owner/source qualification when the owner or source classifier is unnamed.

**Resolved boundary:** DK-IRI-01–08 establish base delimiter behavior, name and ID strategies, normalization separation, source-ID escaping, ordinary collision handling, unnamed-class behavior, and enumeration-value identity. DK-IRI-04 and DK-IRI-08 explicitly defer the generic unnamed-literal policy. RD-09 does not authorize an enumeration-specific `unnamedLiteral_<id>` fallback, invented label, or silent omission. Source-backed resources must remain distinct.

**Why it matters and constraints:** Identity failures can invalidate references or merge source elements. The solution must preserve existing element-specific fallbacks and source-backed precedence. Exceptional escaped-ID collisions MUST NOT be silently handled as ordinary name collisions.

**Alternatives still open:** A deterministic synthetic IRI with a diagnostic, use of the source ID where permitted, or treating the element as untransformable under the input policy require a compact generic decision. No general fallback is accepted.

**Evidence and next step:** The RD-09 evidence reported 202 catalog JSON files, 84 enumerations, and 290 direct literals at commit `2a60b2f77f9e43734d1fdd98ebdec954a840dc18`, with no observed malformed or partially transformable direct literals. This supports proportionate handling but does not eliminate the boundary. Coordinate invalid/duplicate identity recovery with RD-02 and ontology-versus-entity identity with RD-05.

### RD-26 — Labels for unnamed generated relation properties

**Status:** Open only for remaining non-inverse relation labels.

**Decision still needed:** Decide whether an unnamed direct relation whose IRI is derived from a target role, stereotype naming, grounding-relator naming, or source–target synthesis receives a generated `rdfs:label`; if so, define its lexical source and whether it is distinguishable from a source-supplied label.

**Resolved boundary:** DK-LBL-01 requires labels for named source properties and named non-property resources. Unnamed classes receive no invented labels. Inverse-role labels and the no-synthetic-label inverse fallback are settled. Named enumeration literals require source labels. These decisions do not determine labels for unnamed primary relations.

**Alternatives and trade-offs:** No generated label preserves the absence of a source term. A generated label improves display usability but may be mistaken for authored terminology unless its status is clear.

**Dependencies and next step:** Coordinate language and annotation behavior with RD-27 and generic unusable-name handling with ODI-IRI.

### RD-27 — Multilingual names, descriptions, and general annotations

**Status:** Open and narrowed by the current exporter boundary.

**Decision still needed:** Define the treatment of source descriptions, alternative names, editorial notes, creators/contributors, and other supported descriptive metadata; determine language-tag preservation and deterministic handling when the supported export actually provides multiple language variants; and decide which annotations belong on model resources versus the ontology header.

**Resolved boundary:** DK-LBL-01 now requires labels for named source-backed resources under its stated property and non-property rules. DK-INV-11 requires no special multilingual inverse-role selection for the current VP-plugin extraction path. DK-CLS-05 and DK-PROP-04 settle their specific English comments. Those rules MUST NOT be generalized into an unaccepted policy for all descriptions or languages.

**Why it matters and constraints:** The standalone schema can represent richer multilingual metadata than the supported VP-plugin 0.5.3 path necessarily exports. Schema capability must not silently broaden the input contract. Annotation choices must preserve source fidelity without turning metadata into logical axioms.

**Alternatives still open:** Preserve all exported language variants, select a deterministic preferred variant while retaining others where supported, or limit output to the actual single-language exporter path. Description representation may use `rdfs:comment` or another selected standard annotation. No general policy is accepted.

**Evidence gap and next step:** Reinspect the 0.5.3 extraction and representative JSON for each metadata field before deciding. Coordinate ontology-level placement with RD-05, generated labels with RD-26, provenance with RD-28, and package/custom metadata with RD-30–31.

### RD-28 — Source-ID provenance in name-based output

**Status:** Open.

**Decision still needed:** Decide whether resources generated under the name IRI strategy receive source-ID provenance annotations; if so, select the annotation vocabulary, lexical form, multiplicity, and exact IDs preserved.

**Material directional case:** For relation properties, decide whether provenance records the target/source association-end ID, the enclosing association ID, or a defined combination. Accepted directional identity and IRI rules MUST NOT be replaced.

**Alternatives and trade-offs:** A standard term such as `dcterms:identifier`, a DirectKG annotation property, or no identifier annotation remain possible. An annotation improves traceability across renames but expands output and requires a clear source-element correspondence.

**Constraints:** DK-INS-02's deliberately discarded instantiation-association values MUST NOT be reintroduced through provenance. Diagnostics may use allowed source IDs without establishing this RDF annotation policy.

**Dependencies and next step:** Decide first whether RDF-level source-ID provenance is required, then its representation. Coordinate with RD-27 and ontology-level provenance under RD-05.

### ODI-DATATYPES — Primitive and alias registry boundary

**Status:** Open.

**Decision still needed:** Establish whether the primitive registry listed under DK-DAT-02 is complete for the supported VP-plugin 0.5.3 contract and which, if any, additional semantic aliases are explicitly supported. Define registry-maintenance expectations only where they affect the public mapping contract.

**Resolved boundary:** Primitive resolution uses lexical normalization followed by exact controlled lookup. Existing primitive mappings, distinct XSD meanings, `void`, and custom-datatype reification are settled. Mentioned aliases are not activated merely by appearing in examples or discussion.

**Why it matters and constraints:** Missing aliases can unnecessarily reify common primitives, while fuzzy matching can silently assign the wrong datatype. The mapping must remain explicit and deterministic.

**Alternatives still open:** Freeze the current registry as the supported contract or add only aliases evidenced in supported exports and justified by exact semantics. Fuzzy resolution is outside the accepted approach.

**Next step:** Inventory primitive spellings in representative 0.5.3 exports and compare them with the existing registry before selecting additions.

## Ontology identity, metadata, packages, and presentation

### RD-05 — Ontology identity, header metadata, and `dkgm` import identity

**Status:** Open and newly constrained by the accepted `dkgm` import.

**Decision still needed:** Define:

- the generated ontology resource and its IRI relative to the entity base/namespace, including `#` and `/` behavior;
- the concrete ontology declaration needed to carry the mandatory `owl:imports` statement;
- the persistent `dkgm` namespace IRI, ontology IRI, and any version IRI;
- whether generated ontologies import a stable or version-specific `dkgm` ontology IRI;
- the generated ontology's version IRI policy; and
- treatment of supplied title, description, creators/contributors, provenance, license, and source-project metadata at ontology level.

**Resolved boundary:** DK-GEN-04 requires every generated ontology to import the complete reusable `dkgm` vocabulary, including when no covered mereological relation occurs. The vocabulary contents, source-property bridges, default asymmetry, and independence from gUFO are settled. The concrete import statement remains blocked only on the ontology and `dkgm` identities; this issue MUST NOT reopen whether the import is required.

**Why it matters and constraints:** Ontology identity is distinct from the namespace used for generated entities. The mandatory import cannot be serialized correctly without a subject and import target. DirectKG must not invent project metadata that is absent from the source or user input.

**Alternatives still open:** Stable versus version-specific ontology/import IRIs, and minimal versus metadata-rich headers, remain undecided. No ontology-identity pattern or header vocabulary has been accepted.

**Dependencies and next step:** Resolve the minimal ontology and `dkgm` identity core with ODI-IRI. Coordinate language and descriptive metadata with RD-27, source identifiers with RD-28, and package/module questions with RD-31. Publication tooling or deployment architecture is not itself a specification requirement unless it changes the public IRI/import contract.

### RD-30 — `propertyAssignments`

**Status:** Open.

**Decision still needed:** Determine whether exported custom tagged values/property assignments are ignored, preserved as annotations, diagnosed, handled through an explicit whitelist, or exposed through a user-supplied mapping mechanism.

**Why it matters and constraints:** Arbitrary tags cannot be converted blindly into OWL properties without a namespace, datatype, and semantic policy. Retention improves fidelity but may expand the mapping surface beyond a lightweight domain graph. A general user-defined mapping system is not an accepted feature.

**Alternatives still open:** Intentional omission, annotation/diagnostic preservation, a controlled whitelist, or explicit configurable mappings. No recommendation is accepted.

**Evidence gap and next step:** Inspect actual `propertyAssignments` emitted by VP-plugin 0.5.3 and representative corpus values before selecting a boundary. Coordinate general annotation choices with RD-27 and output/reporting with RD-04.

### RD-31 — Package semantics and namespaces

**Status:** Open.

**Decision still needed:** Determine whether source packages are ignored, preserved as provenance/annotations, represented as modules or ontologies, or allowed to influence any IRI or namespace behavior.

**Why it matters and constraints:** Allowing package paths to enter IRIs would make package refactoring alter resource identity. Package containers MUST NOT become output metamodel resources without an explicit rule. Module or ontology treatment depends on the selected ontology-header model.

**Alternatives still open:** Ignore packages; annotate package membership/path; use packages as ontology/module boundaries; or allow a deliberately defined namespace influence. None is accepted.

**Dependencies and next step:** Coordinate with RD-05, RD-27, RD-28, and ODI-IRI. Decide the intended semantic/provenance role before any namespace rule.

### RD-32 — Diagrams, views, and geometry

**Status:** Open.

**Decision still needed:** Define the treatment of diagram/view and concrete-syntax information exported by VP-plugin 0.5.3: silent omission, selected annotations, separate provenance output, or a defined diagnostic role when semantic references fail.

**Why it matters and constraints:** Layout, coordinates, paths, and diagram placement MUST NOT alter OWL semantics derived from valid model elements. Diagram topology is not an authorized source-repair mechanism. Standalone-schema-only note and anchor structures remain outside the supported input contract unless shown in the supported exporter output.

**Alternatives still open:** Silent omission, limited annotation/provenance, or separate non-semantic output. No recommendation is accepted.

**Dependencies and next step:** Inspect actual 0.5.3 diagram output and decide the preservation boundary. Coordinate structural-error behavior with RD-02, annotations/provenance with RD-27–28, and any separate output with RD-04.

## Remaining source-scope evidence boundary

### ODI-INSTANCES — Applicability of general instance-data transformation

**Status:** Blocked on source-scope evidence; not an accepted feature expansion.

**Question still needing evidence:** Determine whether VP-plugin 0.5.3 exports any general instance data that belongs to the current DirectKG input contract and requires a mapping beyond the already settled higher-order classification, enumeration values, and explicit `instantiation`-association handling.

**Resolved boundary:** DK-HO-01–04, DK-INS-01–03, and RD-09 govern their respective cases. DK-INS-01's conditional statement about future concrete instantiation links does not create a current requirement.

**Why it matters and constraints:** A feature should not be designed for a construct absent from the supported input. Conversely, actual supported instance data would require identity, typing, property-assertion, and error rules.

**Next step:** Inspect the 0.5.3 export path and representative JSON. If no additional in-scope construct exists, close the evidence check without expanding the feature backlog.

## Compact dependency order

The following order is advisory and does not establish requirements:

1. Resolve the minimal identity core in ODI-IRI and RD-05, including the generated ontology subject and persistent `dkgm` import identity.
2. Complete the bounded hierarchy/restriction choices: RD-13, ODI-DISJOINT, and ODI-VALUE-RESTRICTIONS.
3. Address remaining semantic fields in coherent groups: RD-17, RD-18, and RD-19–23.
4. Complete labels and metadata together: RD-26–28 and RD-30–31, coordinated with the remaining RD-05 header metadata.
5. Consolidate only material residual recovery under RD-02, then finalize RD-04 and ODI-CONTROLS against the selected semantic and metadata scope.
6. Complete ODI-DATATYPES, RD-32, and the blocked ODI-INSTANCES evidence check without expanding scope unless actual supported input requires it.

Principal dependency links:

| Issue | Depends on or coordinates with |
|---|---|
| RD-02 | ODI-IRI for identity failures; RD-04 for partial-result reporting |
| RD-04 | RD-02, RD-05, RD-27, RD-31, ODI-CONTROLS, and remaining profile-affecting semantics |
| ODI-CONTROLS | ODI-VALUE-RESTRICTIONS and RD-04 |
| RD-13 | DK-REL-14 and DK-INV-12; RD-02 for malformed membership |
| RD-17–23 | RD-27 for annotations and RD-04 for profile/reporting consequences |
| ODI-IRI | RD-02 and RD-05 |
| RD-26–28, RD-30–31 | RD-05 and RD-27 |
| RD-05 | ODI-IRI plus RD-27–28 and RD-31 |

## Retained research anchors

- Current supported exporter: https://github.com/OntoUML/ontouml-vp-plugin/releases/tag/0.5.3
- VP-plugin source: https://github.com/OntoUML/ontouml-vp-plugin
  - Relevant inspected paths include `src/main/java/it/unibz/inf/ontouml/vp/utils/Stereotype.java`, `src/main/java/it/unibz/inf/ontouml/vp/model/ontouml/model/RelationStereotype.java`, and the VP-to-OntoUML property and association transformers.
- OntoUML metamodel: https://github.com/OntoUML/ontouml-metamodel
- OntoUML Schema: https://github.com/OntoUML/ontouml-schema
  - Relevant inspected paths include `dist/ontouml-schema.json` and the property, relation-stereotype, property-stereotype, and aggregation-kind documentation under `website/docs/`.
- OntoUML JavaScript implementation: https://github.com/OntoUML/ontouml-js
- OntoUML model catalog: https://github.com/OntoUML/ontouml-models
  - Retained historical evidence scopes: 198 JSON models at commit `8ea0398cc273a49d9ea28aa534b1bb0316c6687c`; RD-09 reported 202 JSON files at commit `2a60b2f77f9e43734d1fdd98ebdec954a840dc18`. These are snapshot scopes, not fixed corpus counts.
- OWL 2 Structural Specification and Functional-Style Syntax: https://www.w3.org/TR/owl2-syntax/
- Historical transformation precedent: *An Automated Transformation from OntoUML to OWL and SWRL* (2013); precedent only, not a DirectKG authority.

No unresolved issue is resolved by this document. Alternatives and recommendations remain non-normative unless accepted in a future Architect decision. The next Architect session must pair this handoff with the specification consolidated after all accepted transfers. If later integration exposes a substantive conflict, that clarification belongs back in the Architect workflow rather than being inferred from this handoff.
