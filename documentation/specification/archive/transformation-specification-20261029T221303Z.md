# OntoUML DirectKG Current Specification

**Status:** Consolidated normative baseline
**Consolidated:** 2026-10-29
**Repository:** https://github.com/pedropaulofb/ontouml-directkg

## 1. Document purpose and authority

This document is the consolidated current specification of OntoUML DirectKG and is the normative baseline for subsequent specification maintenance, architecture work, and implementation planning.

Sections 2–16 define the accepted scope and behavior. Normative terms such as **MUST**, **MUST NOT**, **SHOULD**, and **MAY** retain their ordinary requirement strength. Explanatory rationale and examples are non-normative unless explicitly stated otherwise.

Statements that a behavior is outside the current scope or is not specified are deliberate specification boundaries. Implementations and later specification work MUST NOT infer behavior for those matters from examples, related approaches, historical proposals, or omitted alternatives.

## 2. Project overview

OntoUML DirectKG transforms OntoUML models into a domain-oriented RDF/OWL knowledge graph. Its primary output resources represent the domain classes and properties modeled by the user, rather than the OntoUML metamodel, JSON serialization objects, or Visual Paradigm presentation structures.

The transformation is intended to produce a substantially simpler and more directly usable graph than a structural RDF reproduction of OntoUML JSON.

### 2.1 Relationship to related approaches

- gUFO preserves OntoUML ontological commitments through a UFO-based representation. DirectKG has a different objective: a simpler, general-purpose, domain-oriented graph. DirectKG MUST NOT acquire gUFO imports or metamodel structure merely because gUFO is a related approach.
- OntoUML JSON to Graph preserves much of the JSON structure and internal identifiers. DirectKG MUST NOT reproduce serialization machinery unless an explicit DirectKG rule requires it.
- *An Automated Transformation from OntoUML to OWL and SWRL* (2013) is design precedent, not a binding rule set. Its rules apply only where independently adopted by this specification.

### 2.2 Implementation form

The project MUST be provided as both a Python library and a command-line interface. Apart from the documentation requirements in §2.3, this specification does not define detailed architecture, package structure, supported Python versions, dependencies, packaging, performance, CI/CD, or deployment requirements.

### 2.3 Documentation framework and publication (DOC-FRAMEWORK)

DirectKG documentation MUST use Zensical + mkdocstrings. Zensical MUST provide the documentation website. mkdocstrings MUST automatically generate Python API references from source code and docstrings.

Documentation MUST be maintained alongside the source code in the project's GitHub repository and MUST be automatically published through GitHub Pages.

**Rationale (non-normative):** The chosen setup aims to provide modern, readable documentation with API references derived directly from the Python code.


## 3. Scope, goals, and principles

### 3.1 Goals

DirectKG is governed by the following established goals:

1. It MUST generate a domain-oriented RDF/OWL graph, not an RDF serialization of OntoUML abstract syntax or JSON structure.
2. Generated classes and properties should be directly usable as domain concepts and relations.
3. Simplification is deliberate, but MUST NOT become arbitrary information loss.
4. OntoUML stereotypes and metamodel features MAY guide transformation without becoming resources in the output.
5. The default result should be comparatively lightweight. Stronger axiomatization may be enabled only where explicitly specified.
6. DirectKG MUST NOT invent semantic mappings unsupported by the source model or a controlled DirectKG registry.

### 3.2 Current input scope

**RD-05 — File-only transformation input.** Every transformation in the current version of DirectKG MUST require a concrete OntoUML JSON input file identified by a file path. This requirement MUST apply to both the CLI and the Python library, independently of the selected provenance mode. The file's contents remain subject to the existing input contract below.

DirectKG MUST NOT support transformation entry points that accept already parsed JSON objects, Python dictionaries, or other fileless representations as substitutes for the required source file. This restriction concerns the supplied transformation input. It does not prohibit internal parsing and processing of the file in memory or change existing Python output and diagnostic capabilities.

Alternative source-input mechanisms remain outside the current version's scope. This decision establishes no commitment to implement them in a future release.

The input contract is JSON generated from Visual Paradigm models by `ontouml-vp-plugin`, qualified by the bounded language enrichment specified below (RD-27 / RD-01). DirectKG MUST retain the VP-plugin 0.5.3-style project/model structure, element variants, identifiers, nesting, and references as its supported input baseline.

The standalone `ontouml-schema` is a reference for interpretation; it MUST NOT silently broaden the accepted input contract to arbitrary schema-conformant documents.

**RD-01 — Supported VP-plugin release.** OntoUML DirectKG will be developed and tested against JSON exports generated by the official [`ontouml-vp-plugin` release 0.5.3](https://github.com/OntoUML/ontouml-vp-plugin/releases/tag/0.5.3), within DirectKG's specified transformation scope.

Exports from other plugin versions, including earlier and later versions, may work, but compatibility is not guaranteed. Supporting those versions does not form part of the current development and testing commitment.

This commitment does not require automatic exporter-version detection or historical compatibility adapters.

The wording describes the intended development and testing commitment. It does not claim that implementation or testing has already been completed. RD-01 establishes no unknown-field handling or malformed-input policy.

**RD-27 / RD-01 — Bounded language enrichment.** In textual fields already supported by DirectKG, it MUST accept either the existing plain-string representation or the `languageString` representation defined by `ontouml-schema` and implemented by `ontouml-js`. Existing permitted absent and null values remain governed by their applicable rules. DirectKG MUST accept the schema-defined `languages` field on the top-level `Project` as the project/high-level language carrier.

Within the accepted project/model structure, DirectKG MUST support top-level `Project.description` as a plain string or the supported `languageString` representation. Its ontology-comment mapping is specified in DK-LBL-02. This addition does not authorize arbitrary schema-conformant documents or expand the external metadata whitelist.

These carriers MUST follow DK-LBL-02's accepted precedence: user override (`--language LANG` or its semantically equivalent Python control), then explicit local language, then a single applicable declared project language, then an untagged literal. Without an override, explicitly localized values MUST be preserved independently with their respective language tags. The empty language key denotes unknown language and supplies no explicit local tag. When multiple project languages are declared and an otherwise untagged value has neither a user override nor a safely determined local language, DirectKG MUST preserve it untagged and emit the nonfatal WARNING under DK-DIAG-19, with its existing consolidation and repetition rules.

Supported localized names and role names used for IRI naming components or generated lexical naming candidates follow DK-IRI-10's deterministic selector. The same selector supplies the original source text used for primitive recognition under DK-DAT-02 (RD-27, option A). Selecting one naming input does not discard other applicable localized labels under DK-LBL-01–02.

VP `propertyAssignments` MUST NOT participate in language resolution, including entries named `language`, `lang`, `locale`, or similar. DirectKG MUST NOT introduce package-local language declarations unless separately established by the supported input contract.

This extension MUST be limited to the language-bearing structures needed by RD-27. It MUST NOT implicitly enable the complete newer OntoUML Schema document structure, additional metadata fields, new element representations, or other schema features. DK-LBL-02's user-authored-text scope and generated- or built-in-text exclusions remain unchanged.

Existing plain VP-plugin 0.5.3 exports MUST remain valid input under the existing transformation rules. This extension MUST NOT change their language treatment unless the explicit user override is supplied. The exporter's internal English default MUST NOT supply a language tag.

The current VP association extraction path emits two association ends. N-ary relation support is therefore outside the current input scope unless that export contract changes.

For binary relations with an endpoint whose `propertyType` resolves to another source `Relation`, DK-REL-08 (RD-16 / RD-17) governs recognized material–relator and material–mode derivations; DK-REL-18 (RD-17) governs recognized comparative–quality derivations; and DK-REL-17 (RD-16) governs other resolved relation-valued endpoint patterns without an accepted mapping. A null, malformed, or unresolved endpoint remains a structural failure.

### 3.3 Output scope

The target is an RDF/OWL knowledge graph. Turtle is used in ontology examples; provenance sidecars MUST use Turtle under DK-GEN-10. The generated ontology IRI is derived exclusively from the effective entity base under DK-IRI-01 (RD-05). Apart from DK-IRI-01's IRI-selection, supplied-base validation, and optional caller-supplied ontology version IRI rules, the required `dkgm` import under DK-GEN-04 (RD-17 / RD-25), the project-name label under DK-GEN-08 (RD-05 / RD-27), the project-description comment under DK-LBL-02 (RD-27, option B), and the metadata and provenance rules in DK-GEN-09–11, this specification does not define other ontology-header details, other ontology-identity matters, or general OWL profile guarantees. The mandatory `dkgm` import uses the stable URI identifying or redirecting to the vocabulary's latest version under DK-GEN-04 (RD-05); it is not pinned to a vocabulary release. The accepted concrete URI is `https://w3id.org/directkg/vocab/dkgm`. Emitted material-property chains are subject to the compatibility-notice and documentation requirements in DK-DIAG-07 (RD-17); this does not establish a general OWL profile guarantee.

The UML property subsetting and redefinition mapping in DK-PROP-03 (RD-14) does not establish a general OWL profile guarantee. The general output and OWL-profile contract remains the responsibility of RD-04.

DirectKG avoids a DirectKG or OntoUML metamodel vocabulary in the domain graph except where an explicit rule requires a vocabulary term. DK-GEN-04 requires an import of the reusable DirectKG mereology vocabulary; its generic mereological properties are distinct from OntoUML metamodel resources and from source-specific domain properties. Higher-order classification uses standard RDF/OWL constructs rather than companion metamodel resources.

Package organization, diagrams, and diagramming information are intentionally omitted under DK-GEN-06 (RD-31 / RD-32). Custom `propertyAssignments` are recognized and omitted under DK-GEN-07 (RD-30).

#### Ontology serialization (RD-04, option A)

RDF 1.1 Turtle MUST be the sole officially supported ontology serialization in the current specification, and therefore the default serialized ontology output.

This format requirement MUST apply to both CLI ontology output and Python ontology-serialization capabilities. It does not prescribe Python return types or function signatures.

This serialization decision introduces no format-selection control. Existing Turtle provenance-sidecar requirements under DK-GEN-10 and JSON diagnostic-report requirements under DK-DIAG-04 remain unchanged.

**Rationale (non-normative):** Turtle supports the accepted output structures and provides readable output consistent with the existing examples and provenance sidecars. Supporting one format keeps the current public contract small.

#### Turtle prefix policy (RD-04, option A — conventional prefixes)

Turtle ontology serialization SHOULD use the empty/default prefix `:` for the effective entity base and conventional prefixes for vocabularies used in the graph, such as `rdf:`, `rdfs:`, `owl:`, and `xsd:`.

Prefix bindings and their use MUST preserve the generated RDF graph and its IRIs. Prefix selection MUST NOT change the effective entity base, ontology IRI, or generated entity IRIs.

Exact prefix labels, the complete set of declarations, and declaration order are not guaranteed. Serializers MAY use additional prefixes or full IRIs while preserving the graph.

This policy applies to CLI and Python ontology serialization. It introduces no prefix-configuration control or additional diagnostic solely for prefix choice.

**Rationale (non-normative):** Conventional prefixes improve readability while allowing serializer flexibility. Resource identity continues to depend on the expanded IRIs, independently of the chosen abbreviations.

#### Serialized presentation and repeatability (RD-04, option A — serialized presentation)

DirectKG establishes no additional guarantee of statement order, whitespace layout, stable serialized blank-node labels, or byte-identical Turtle output.

Every serialization MUST preserve its generated RDF graph, allowing consistent blank-node relabeling. IRIs, literals, and graph connections MUST remain preserved. This includes preservation of the RDF graph produced by the accepted transformation rules.

This freedom MUST NOT alter order encoded within RDF lists, including property-chain sequences.

Existing determinism requirements remain unchanged, including IRI generation, collision handling under DK-CONF-01 and its governing rules, and DK-GEN-10's deterministically serialized configuration YAML. Provenance requirements and checksums over actual file bytes also remain unchanged.

This policy applies to CLI and Python ontology serialization and provenance-sidecar serialization. It requires no canonicalization algorithm and introduces no sorting or canonicalization control. Implementations MAY nevertheless produce stable text.

**Rationale (non-normative):** Different textual presentations can preserve the same RDF graph. This policy preserves correctness and deterministic resource identity without requiring an additional formatting mechanism. Execution-specific provenance can legitimately differ between conversions.

### 3.4 Semantic validation boundary

DirectKG transforms the source model as stated. It is not an OntoUML semantic validator. Relation-to-relation generalization follows DK-REL-14 (RD-12), and relation generalization-set disjointness follows DK-REL-15 (RD-13), without semantic endpoint, domain, or range compatibility checks; structural resolution remains required.

DirectKG MUST NOT suppress otherwise applicable output because the source appears semantically incorrect or because the resulting ontology may be inconsistent. Structural processability remains required: malformed JSON, dangling references, missing elements, unresolved endpoints, or invalid identifiers that make a transformation technically impossible MUST be reported as errors.

The mereological mapping in DK-REL-19 (RD-17 / RD-25) uses the recognized stereotype and the relation's existing primary direction without checking or repairing its intended orientation. The source characteristics preserved as comments under DK-PROP-04 (RD-24 / RD-25) do not provide a separate semantic-orientation validation mechanism.

A structurally resolved relation-valued endpoint is governed by DK-REL-08, DK-REL-18, or DK-REL-17, as applicable, rather than treated as an unresolved endpoint. DirectKG MUST NOT infer missing stereotypes or change endpoint identity to make a connector match a supported pattern.

Explicit UML property subsetting and redefinition references follow DK-PROP-03 (RD-14) without owner, endpoint, type, property-kind, or other UML semantic-compatibility checks. Their structural references and underlying property transformations must still resolve. Semantic preservation of the resulting inclusion depends on the source satisfying the mapping's assumptions; structurally processable but semantically invalid source relationships may yield output outside an OWL 2 DL profile.

The per-axiom OWL 2 DL compatibility assessment for the five additions under DK-REL-01 (RD-17) does not change this semantic-validation boundary. It establishes no semantic validation, consistency checking, or source-model repair, and no overall OWL 2 DL guarantee.

RD-02 establishes policy-dependent severity and continuation in DK-DIAG-05, subject to the duplicate-source-element-ID exception below. RD-03 (DK-DIAG-06) exclusively governs acceptance and rejection of missing and unrecognized stereotypes, taking precedence over the input policy for those conditions. The semantic-validation boundary applies in every input and stereotype policy: semantically questionable but structurally processable information remains subject to the accepted transformation rules. DirectKG MUST NOT introduce OntoUML semantic validation or output-consistency checking through these policies. No recovery behavior is defined beyond the explicit recovery rules in this specification.

#### Minimal opaque source identifiers (RD-02, Alternative A)

Within this section's existing identity/reference scope—source declarations participating in DirectKG's accepted mappings and identifiers needed for required reference resolution—the following definitions apply:

| Condition | Definition |
|---|---|
| Missing source identifier | The `id` field is absent. |
| Invalid supplied source identifier | The supplied value is null, is not a JSON string, is empty, or cannot be encoded as UTF-8. |

Every other identifier string MUST be accepted unchanged, including whitespace-only strings. DirectKG MUST NOT trim, normalize, case-fold, coerce, or invent replacement identifiers.

These definitions establish the valid/usable source-ID prerequisite in the applicable rules. Missing and invalid identifiers MUST follow the existing structural-error policies under DK-DIAG-05. The mandatory-abortion rule for duplicate declaration IDs remains unchanged. No additional dependent-output recovery or exceptional escaped-ID collision disposition is established.

**Rationale (non-normative):** Identifiers are opaque identity keys. These minimum requirements establish technical processability without imposing descriptive-name, UUID, or exporter-specific lexical conventions.

#### Duplicate source-element IDs (RD-02, option A)

For source IDs valid under the definitions above, separate declarations participating in DirectKG's accepted mappings or required reference resolution MUST NOT share an ID. DirectKG MUST compare decoded JSON ID strings exactly, without trimming, normalization, or case folding.

Repeated reference objects identifying one declaration MUST NOT be treated as duplicate declarations. This rule introduces no validation of intentionally omitted diagram or custom-metadata content.

Duplicate declaration IDs within this scope follow DK-DIAG-05's fatal duplicate-ID rule under every input policy, including when the separate declarations have identical contents.

**Rationale and examples (non-normative):** The policy avoids choosing between competing identities and keeps recovery simple and deterministic.

For example, separate declarations of `Person` and `Organization` sharing ID `C17` trigger an error and abort. Multiple ordinary references to a single declaration with ID `C17` do not.

#### Contradictory numeric multiplicity bounds (RD-11)

For supported attributes and ordinary binary relation ends, when both multiplicity bounds are nonnegative integers and the lower bound `l` exceeds the upper bound `u`, DirectKG MUST generate both a minimum-cardinality restriction with value `l` and a maximum-cardinality restriction with value `u`.

DirectKG MUST NOT swap, clamp, discard, or substitute either bound because they contradict one another. This behavior MUST apply under every input policy. DirectKG MUST NOT emit an error or warning solely because the lower bound exceeds the upper bound.

Generated restrictions MUST follow the applicable accepted cardinality representation, direction, class-constraint placement, and property-selection rules: DK-ATT-02 and DK-ATT-03 for attributes, and the applicable RD-11 rules in DK-REL-09–11 for ordinary relations.

These cardinality-output requirements remain subject to DK-REL-07's targeted `omit-conflicting-constraints` rule when an emitted material chain makes the restriction's property expression non-simple. Contradictory bounds alone do not trigger that omission.

Such intervals are transformable and MUST NOT be treated as untranslatable multiplicities under DK-DIAG-10. Other input problems remain subject to their applicable policies.

**Rationale and example (non-normative):** When the restrictions are not subject to the targeted material-chain omission rule, `5..2` generates minimum 5 and maximum 2. Together, these constraints make the affected class unsatisfiable. This does not by itself make the entire ontology inconsistent unless other axioms require that class to have an instance. DirectKG preserves the stated constraints without performing semantic consistency validation.

## 4. Terminology

**Source-backed resource**
A generated resource corresponding directly to a source-model element. This includes classes, enumeration value individuals, classifier-owned properties, and primary properties generated from explicit relations.

**Generated auxiliary resource**
A generated resource without a separate source-model element. A generated inverse property is auxiliary.

**Domain class**
An OntoUML class represented as an `owl:Class`. Supported primitive datatype elements and Visual Paradigm `void` are exceptions. Custom OntoUML datatypes are represented as reified domain classes.

**Generated property**
An `owl:ObjectProperty` or `owl:DatatypeProperty` produced from an attribute, relation, or inverse-generation rule.

**Generic mereological property**
An object property defined in the reusable `dkgm` vocabulary under DK-GEN-04, distinct from a generated property representing a source-model relation.

**Supported primitive datatype**
A datatype classifier whose normalized name resolves exactly through the controlled DirectKG primitive registry to an XSD datatype. For a supported localized datatype name, DK-IRI-10 selects the original source text passed through primitive normalization and exact lookup under DK-DAT-02.

**Custom OntoUML datatype**
A `«datatype»` classifier that is neither a registered primitive nor Visual Paradigm `void`.

**Usable name**
A non-null name containing meaningful source text that produces a nonempty local name under the applicable normalization rules. For supported localized names, DK-IRI-10 selects among usable naming candidates. For inverse-role presence specifically, at least one non-whitespace character is required; a multilingual role is present when any value meets that condition, independently of successful ASCII normalization.

**Source and target association ends**
For a direct relation property `A → B`, the source end has `propertyType A` and supplies the direct domain; the target end has `propertyType B` and supplies the direct range.

## 5. General output model

### DK-GEN-01 — Domain resources

DirectKG MUST generate RDF/OWL resources for supported domain classes and properties, together with the enumeration value individuals required by DK-CLS-10–11 (RD-09). It MUST NOT generate resources merely to mirror source JSON containers, diagram views, or metamodel objects. Material–relator and material–mode derivation connectors are used as transformation-time information without a separate output representation, as specified in DK-REL-08 (RD-16 / RD-17). Comparative–quality derivation connectors are intentionally unrepresented with the diagnostic specified in DK-REL-18 (RD-17). Other resolved binary connectors with relation-valued endpoints and no accepted mapping are omitted with the nonfatal limitation warning specified in DK-REL-17 (RD-16). Independently transformable endpoint classes and relations retain their applicable mappings.

Every generated ontology also imports the reusable `dkgm` vocabulary under DK-GEN-04 (RD-17 / RD-25), including when no covered mereological relation is present. The generic vocabulary terms are not source-model resources. Covered source relations remain distinct domain properties under DK-REL-19.

### DK-GEN-02 — Explicit source structures

Unless a rule explicitly requires closure materialization, DirectKG transforms explicit source structures and does not materialize logically inferred closure. Class generalization is such a case: explicit subclass axioms are emitted, but their transitive closure need not be repeated. Explicit relation-to-relation generalizations map to primary-property `rdfs:subPropertyOf` axioms under DK-REL-14 (RD-12), subject to this explicit-source-structure rule. Class generalization-set disjointness under DK-CLS-06 (RD-13) uses only the set’s explicit specific classifiers and MUST NOT additionally materialize inherited disjointness for their descendants. Relation generalization-set disjointness under DK-REL-15 (RD-13) uses the generated properties corresponding to the set's explicit specific relations. Powertype extension materialization is an explicit exception. DK-INV-12 (RD-12) is another explicitly required materialization: it mirrors each successfully mapped explicit relation generalization between generated named inverses when both exist. It MUST NOT additionally materialize the generalization edges’ transitive closure. DK-REL-20 (RD-13) additionally requires explicit reverse inclusion for singleton relation completeness, including between corresponding named inverses when both exist.

Explicit UML property subsetting and redefinition references follow DK-PROP-03 (RD-14). Their identical resulting axioms are deduplicated, but DirectKG MUST NOT additionally emit logically entailed inverse counterparts or materialize the transitive closure of their property hierarchy. The inverse-specialization requirement for relation generalizations in DK-INV-12 does not extend to RD-14 references.

The three generic mereological chains in DK-GEN-04 are defined in the imported vocabulary. Their inferred instance-level consequences do not require materialization as source-specific property assertions or additional source-specific chains under DK-REL-19 (RD-17 / RD-25).

### DK-GEN-03 — Property domains and ranges

Every generated OWL property MUST receive an `rdfs:domain`.

- Attribute domain: the owning classifier.
- Primary relation domain: the source-end classifier.
- Generated inverse domain: the primary property's range.

DirectKG MUST generate `rdfs:range` whenever the target or value type is unambiguously resolvable to a supported DirectKG range.

- Primitive-valued attribute: mapped XSD datatype.
- Custom-datatype-valued attribute: custom datatype class.
- Enumeration-valued attribute: enumeration class generated under DK-CLS-10 (RD-09).
- Primary relation: target-end classifier.
- Generated inverse: primary property's domain.

DirectKG MUST NOT invent a range for an untyped attribute, `void`, or an unresolved target.

`rdfs:domain` and `rdfs:range` are inferential axioms, not validation constraints. DirectKG deliberately adopts their RDF/OWL semantics.

For supported ordinary binary class-to-class relations, the unqualified cardinality forms are specified in DK-REL-10 (RD-11); the endpoint domain and range declarations above continue to apply.

The four generic `dkgm` properties in DK-GEN-04 are vocabulary terms, not generated properties representing source attributes, relations, or inverses. The source-class domain and range requirements of this rule do not assign them domain or range from a particular converted model.

### DK-GEN-04 — Reusable DirectKG mereology vocabulary and import (RD-17 / RD-25 / RD-05)

DirectKG MUST define a reusable OWL mereology vocabulary, denoted here by the `dkgm:` prefix. RD-05 establishes the identifier pattern and stable-URI import-target policy below. The concrete stable ontology URI is `https://w3id.org/directkg/vocab/dkgm`; the property namespace is derived from it rather than selected independently. DKGM version IRIs follow `U/X.Y.Z`, including `https://w3id.org/directkg/vocab/dkgm/0.1.0` for version 0.1.0. Optional caller-supplied version IRIs for generated ontologies are governed separately by DK-IRI-01 (RD-05, Option B). The vocabulary MUST declare four generic object properties: `dkgm:memberOf`, `dkgm:subCollectionOf`, `dkgm:subQuantityOf`, and `dkgm:componentOf`. These stereotype-level terms are distinct from the source-specific properties generated from individual OntoUML relations.

Let `U = https://w3id.org/directkg/vocab/dkgm` denote the stable URI identifying the `dkgm` ontology and representing its latest version (project-owner identity decision, 2026-10-24). `U` MUST have no fragment component. The vocabulary's property namespace MUST be formed by appending `#` to `U`; `dkgm:` denotes that namespace. The four generic property IRIs MUST be:

| Vocabulary term | Property IRI pattern |
|---|---|
| `dkgm:memberOf` | `U#memberOf` |
| `dkgm:subCollectionOf` | `U#subCollectionOf` |
| `dkgm:subQuantityOf` | `U#subQuantityOf` |
| `dkgm:componentOf` | `U#componentOf` |

`U` is the selected concrete stable URI; `dkgm:` denotes `https://w3id.org/directkg/vocab/dkgm#`. Redirecting `U` to a newer vocabulary document MUST NOT substitute that document's address into the ontology/import URI or these four property IRIs.

**Non-normative namespace rationale (RD-05):** A hash namespace suits the small vocabulary whose four properties are published together. The vocabulary's identity and property identifiers remain independent of the document location serving its current version.

The vocabulary MUST define these three accepted generic property-chain axioms:

| Ordered chain | Conclusion |
|---|---|
| `dkgm:subCollectionOf o dkgm:subCollectionOf` | `dkgm:subCollectionOf` |
| `dkgm:subQuantityOf o dkgm:subQuantityOf` | `dkgm:subQuantityOf` |
| `dkgm:memberOf o dkgm:subCollectionOf` | `dkgm:memberOf` |

The vocabulary MUST NOT define generic `componentOf` transitivity or a generic `componentOf` property-chain axiom solely from the OntoUML stereotype. In particular, it MUST NOT define a `dkgm:componentOf o dkgm:componentOf` chain concluding in `dkgm:componentOf`. The four generic properties MUST NOT be declared asymmetric by default, and no additional generic asymmetric superproperty is introduced by this mapping. The three chain-bearing properties, `dkgm:memberOf`, `dkgm:subCollectionOf`, and `dkgm:subQuantityOf`, are non-simple because they are superproperties of the accepted chains. This does not, by itself, make each source-specific subproperty non-simple; other independently applicable axioms can affect its simplicity. The general output and OWL-profile contract remains governed by RD-04 and other applicable rules.

Every ontology generated by DirectKG MUST import the *complete* reusable `dkgm` vocabulary, even when the source model contains no covered mereological relation. Its import closure consequently includes all four generic property declarations and all three accepted chains. The vocabulary is the authoritative location for these generic axioms: DirectKG MUST NOT copy them into each generated ontology or construct a model-specific subset. DK-IRI-01 (RD-05) establishes the generated ontology IRI by derivation from the effective entity base. The `dkgm` vocabulary MUST have a stable URI that identifies or redirects to its latest version. Every generated ontology MUST use that stable URI `U` as the object of its mandatory `owl:imports` statement, without the appended `#` or a property local name. The generated import MUST NOT be pinned to a particular vocabulary release or replaced with a version-specific URI obtained by following the stable URI's redirect. The concrete import target is the selected `U` above.

**Non-normative import rationale (RD-05):** The stable URI provides access to the latest vocabulary without requiring a different import statement for each release. When an existing generated ontology's import is subsequently resolved against a newer vocabulary version, its imported axioms may change even though the generated ontology file has not changed. The import therefore does not record which vocabulary version was current when conversion occurred.

The core `dkgm` vocabulary MUST remain independent of gUFO. It MUST NOT import gUFO or declare an `owl:equivalentProperty`, `rdfs:subPropertyOf`, or other alignment axiom between its four properties and gUFO properties as part of this mapping.

**Non-normative rationale:** Generic chains support stereotype-level inferences through the shared vocabulary while the source relations remain separately identifiable. `componentOf` transitivity depends on domain-level characteristics that cannot be derived from the supported source representation alone.

### DK-GEN-05 — Comment preservation of derived status (RD-20, option C)

DirectKG MUST preserve explicit boolean `isDerived` values, both `true` and `false`, through `rdfs:comment` annotations according to the following placement:

| Source occurrence | Comment target, when successfully generated |
|---|---|
| Class, including an enumeration or custom datatype | Corresponding local class resource |
| Attribute | Corresponding attribute property |
| Relation | Corresponding primary relation property |
| Source association end | Corresponding primary relation property |
| Target association end | Corresponding primary relation property |

Relation and association-end comments MUST distinguish whether each value belongs to the relation, its source end, or its target end. Each explicit occurrence MUST remain distinguishable.

These derived-status comments MUST NOT be copied onto generated inverse properties or enumeration-value individuals. Preservation of association-end flags MUST NOT depend on named inverse generation.

When no eligible local annotation target is generated, DirectKG MUST omit the derived-status comment. It MUST NOT create an additional resource or use an alternative annotation target solely to preserve the flag, including shared XSD datatype IRIs or generic `dkgm` terms.

DirectKG MUST NOT infer derived status when `isDerived` is absent or null. The flag alone MUST NOT generate a derivation rule, property chain, equivalence, or other additional logical constraint. It MUST NOT suppress ordinary transformation.

For `isDerived: true`, DirectKG MUST emit the INFO diagnostic specified in DK-DIAG-16 only when the corresponding derived-status comment is generated. DirectKG MUST NOT emit a diagnostic solely because `isDerived` is `false` or because a flag has no eligible annotation target. Independently required structural, mapping-limitation, and other diagnostics remain applicable.

Explicit `«derivation»` relations MUST continue to follow their independently accepted mappings under DK-REL-07–08 and DK-REL-18. The INFO diagnostic MUST NOT imply that such a mapping was omitted when it was actually applied. Description placement remains separately governed by DK-LBL-02.

**Rationale (non-normative):** Primary-property placement preserves distinct relation and end facts independently of inverse-generation settings. Annotation-dependent INFO avoids claiming preservation when no comment was generated.

**Example (non-normative):** Declaring an attribute derived does not provide its calculation. For example, `isDerived: true` on an age attribute does not authorize DirectKG to invent a calculation from a birth-date attribute. Preserving `false` does not warrant an expressivity-loss notice about an unavailable derivation.


### DK-GEN-06 — Omission of package organization and diagrammatic presentation (RD-31 / RD-32)

Packages are input-side organizational containers only. DirectKG MAY traverse them as needed to discover and process supported model elements. Packages themselves MUST generate no RDF/OWL resources or annotations. DirectKG MUST omit package names, descriptions, hierarchy, membership information, paths, and similar organizational information.

Package organization MUST NOT affect generated entity IRIs, namespaces, logical mappings, or other transformation semantics.

Diagrams and diagramming information are outside DirectKG's output scope. DirectKG MUST NOT generate RDF/OWL resources or annotations for diagrams, diagram views, or visual-presentation information. The omitted presentation information includes diagram identities and names, element placement, coordinates, dimensions, routing/path points, positioning, visual grouping, layout, colors, and other concrete-syntax information describing how the model is visually presented.

Transformation of a supported model element MUST depend on its abstract-model semantics, not its package, diagram membership, number of diagram appearances, position, or visual representation. Differences solely in package organization, diagram organization, or visual layout MUST NOT change the generated domain-level RDF/OWL semantics.

DirectKG MUST NOT emit a diagnostic solely because package, diagram, or diagramming information is omitted. These omissions MUST NOT be treated as unsupported-input conditions; they are intentional scope boundaries. Structural processing needed to reach supported model elements remains distinct from preservation of organizational or presentation information.

**Rationale (non-normative):** DirectKG transforms the OntoUML abstract/domain model. Organizational and visual-presentation information is intentionally lost.

### DK-GEN-07 — Recognized omission of custom property assignments (RD-30)

DirectKG MUST recognize `propertyAssignments` but MUST NOT generate RDF/OWL output or transformation behavior from its custom entries.

DirectKG MUST NOT emit a diagnostic solely because custom assignments are present or omitted from output. Their recognized omission MUST NOT itself trigger an unrecognized-information warning or error. Existing structural-input rules remain unchanged.

Custom assignments MUST NOT participate in language resolution, regardless of their names or intended use. Dedicated, separately exported fields, such as `isExtensional`, MUST remain governed by their own accepted transformation rules. Omitting custom assignments MUST NOT disable those mappings.

This rule introduces no custom-metadata preservation mechanism, whitelist, or user-defined mapping system.

**Rationale (non-normative):** No specific custom key has been established as necessary for DirectKG. General preservation would add complexity without a defined consumer requirement.

### DK-GEN-08 — Project name on the generated ontology (RD-05 / RD-27)

DirectKG MUST preserve a nonempty top-level `Project.name` as `rdfs:label` on the generated ontology resource. The label MUST follow the accepted RD-27 lexical-preservation and language-resolution rules under DK-LBL-02, including supported multilingual values and the explicit user language override.

When the project name is absent, null, or empty, DirectKG MUST emit no ontology label and no diagnostic solely for that condition. DirectKG MUST NOT manufacture an ontology label from the filename, ontology IRI, or root-package name.

The project name MUST NOT affect ontology identity, generated entity IRIs, namespaces, or logical mappings. This mapping MUST NOT create a separate project resource or introduce a project-ID annotation under RD-28 / DK-IRI-09.

This project-name rule introduces no mappings or controls for other ontology-header metadata. Top-level project descriptions are separately mapped under DK-LBL-02 (RD-27, option B); external descriptive metadata and transformation provenance are separately governed by DK-GEN-09–11. Package descriptions and custom `propertyAssignments` remain governed by DK-GEN-06 and DK-GEN-07. The existing ontology declaration, ontology-IRI derivation, and mandatory `dkgm` import remain unchanged. The concrete persistent `dkgm` URI is selected under DK-GEN-04; optional caller-supplied generated-ontology version IRIs follow DK-IRI-01 (RD-05, Option B).

**Rationale (non-normative):** Preserves the source project's human-readable name through a bounded annotation mapping.

### DK-GEN-09 — External descriptive metadata (RD-05 / RD-27 / ODI-CONTROLS)

Descriptive ontology metadata describes the generated ontology. Transformation provenance describes the execution that produced it. The ontology declaration, mandatory imports, domain axioms, and other required semantic output MUST NOT be treated as transformation provenance. The provenance modes in DK-GEN-10 MUST NOT disable descriptive metadata obtained from the source project or an explicitly supplied `metadata.yaml`.

DirectKG MUST provide `--metadata-file PATH`, explicitly identifying a file named `metadata.yaml` using the supported OntoUML/UFO Catalog field structure. DirectKG MUST NOT automatically discover this file. JSON, RDF, Ion, and other external metadata formats MUST NOT be accepted through this mechanism.

Only the following fields MUST be ingested:

| Field | RDF predicate | Accepted nonempty value shape |
|---|---|---|
| `title` | `dcterms:title` | One string |
| `acronym` | `mod:acronym` | One untagged string |
| `contributor` | `dcterms:contributor` | List of contributor IRIs |
| `keyword` | `dcat:keyword` | List of strings |
| `source` | `dcterms:source` | List of source-resource IRIs |
| `landingPage` | `dcat:landingPage` | One IRI or a list of IRIs |
| `license` | `dcterms:license` | One license-document IRI |

Here, `mod:acronym` denotes `https://w3id.org/mod#acronym`.

These statements MUST describe the generated ontology resource. The selected fields are optional enrichment: absent, null, or empty values MUST produce no annotation. DirectKG MUST emit separate statements for list values rather than concatenate them. It MUST preserve supplied text and IRIs without inventing contributor identities or resolving names through external searches.

All other fields MUST be ignored, including `issued`, `modified`, `theme`, `editorialNote`, `ontologyType`, `language`, `designedForTask`, `context`, and `representationStyle`. Their values MUST NOT supply annotations, language tags, or transformation settings. Validation MUST concern the supported subset; it MUST NOT require unrelated Catalog fields.

#### Source-project name and external title

DirectKG MUST retain `Project.name → rdfs:label` under DK-GEN-08. An external title MUST supplement it through `metadata.yaml title → dcterms:title`. Neither value replaces the other. The external title MUST NOT additionally generate an `rdfs:label`, including when the project name is absent.

**Example (non-normative):**

```turtle
<https://example.org/study>
    rdfs:label "Clinical Study" ;
    dcterms:title "Clinical Study Ontology" .
```

Source-project text MUST continue to follow RD-27 under DK-LBL-02. External YAML text MUST remain untagged. The external `language` field is ignored; neither `Project.languages` nor `--language` propagates to external YAML text under this rule.

#### Metadata-input failures

Invalid selected metadata values MUST follow the accepted input-policy pattern: under `strict` and `tolerant`, report an error; under `best-effort`, omit affected values and report an error. Ignored fields MUST NOT trigger field-validation diagnostics. When an explicitly supplied `metadata.yaml` cannot be read or parsed into a valid top-level mapping, DirectKG MUST report an ERROR. This includes a missing file, permission failure, malformed YAML, or a root value that is not a mapping. Such failures MUST NOT be treated as absence of an optional input.

| Input policy | Required whole-file recovery |
|---|---|
| `strict` | Abort; deliver no ontology output. |
| `tolerant` | Abort; deliver no ontology output. |
| `best-effort` | Omit all external metadata contributions and continue transforming the OntoUML input. |

Under `best-effort`, DirectKG MUST preserve source-project metadata, required ontology structure, domain axioms, and independently available provenance according to their existing rules. If no other condition requires abort, the outcome MUST be `completed-with-errors`.

DirectKG MUST NOT attempt to salvage fragments of malformed YAML. Once a valid top-level mapping is available, invalid selected field values MUST follow the field-level recovery rules above. Ignored fields remain excluded from field validation; their presence or values MUST NOT independently trigger field-validation diagnostics. The document must nevertheless be syntactically parseable as YAML.

The diagnostic MUST identify the metadata-file failure and its effect: conversion aborted or external metadata omitted. It MUST be available through the existing console, programmatic, and requested diagnostics-file mechanisms under DK-DIAG-04.

Provenance MUST NOT claim successful use of metadata that was never read or parsed. The effective configuration MAY record that external metadata was requested.

The existing CLI exit-code contract applies: `3` for abortion, `1` for a result delivered with errors, and `4` taking precedence when requested diagnostics cannot be written. Requested diagnostics MUST still be written on abort, subject to the existing diagnostics-delivery rules. Provenance-sidecar delivery failures remain governed separately by DK-GEN-10 and §15.

### DK-GEN-10 — Transformation provenance (RD-05 / RD-27 / ODI-CONTROLS)

DirectKG MUST provide `--provenance {none,embedded,sidecar}`, defaulting to `embedded`.

| Mode | Transformation provenance | Descriptive ontology metadata |
|---|---|---|
| `none` | Not generated | Retained in the ontology graph |
| `embedded` | Included in the ontology graph | Retained in the ontology graph |
| `sidecar` | Written separately as Turtle | Retained in the ontology graph |

#### Sidecar placement and output-artifact boundary

The provenance sidecar MUST be written beside the concrete output file using `<output-stem>.provenance.ttl`. For example, `hospital.ttl` has the sidecar `hospital.provenance.ttl`. The sidecar MUST use Turtle. Ontology serialization follows the RDF 1.1 Turtle requirement in §3.3 (RD-04, option A). The serialized-presentation boundary in §3.3 (RD-04, option A — serialized presentation) applies to ontology and provenance-sidecar serialization.

Concrete output-file information—including its filename, serialization format, and content digest—MUST be described only in sidecar mode. Embedded provenance MUST describe the generated ontology and transformation without representing the containing serialization file as an external artifact describing itself. Concrete output-file information MUST also be excluded from the embedded configuration record.

Automatic sidecar writing MUST require a concrete output path. DirectKG MUST NOT invent a sidecar filename for stdout or an in-memory graph.

DirectKG MUST NOT deliver a new provenance sidecar for an ontology file whose delivery failed. Existing sidecar-failure behavior remains unchanged when ontology-file delivery succeeds. Ontology-file creation and write failures are governed by DK-DIAG-04 and §15 (RD-04, option A — ontology-file delivery).

#### Required representation

When provenance is enabled, DirectKG MUST represent:

| Information | Representation |
|---|---|
| Execution | A distinct `prov:Activity` for each execution |
| Generating software | A resource typed as `prov:SoftwareAgent` and `schema:SoftwareApplication`, identifying DirectKG |
| Software association | Activity → `prov:wasAssociatedWith` → software resource |
| DirectKG version | `schema:softwareVersion` on the software resource |
| Transformation completion timestamp | `prov:endedAtTime` on the activity, expressed in UTC |
| Generated ontology | Ontology → `prov:wasGeneratedBy` → activity |
| Source JSON artifact | A `prov:Entity` linked from the activity through `prov:used` |
| Effective configuration | A separate `prov:Entity` linked through `prov:used` |
| Supplied metadata file | A separate input entity linked through `prov:used`, subject to DK-GEN-09’s prohibition on claiming successful use of metadata never read or parsed |
| File content digest | An SPDX checksum structure using SHA-256 |
| Concrete output artifact, in sidecar mode | A separate entity linked to the ontology through `dcterms:isFormatOf`, with filename, serialization format, checksum, and generation relationship |

The configuration entity MUST contain a deterministically serialized YAML string under `prov:value`, with its format identified through `dcterms:format`. It MUST record effective transformation settings, including defaults, subject to the output-file exclusion for embedded provenance. Configuration keys inside this literal are data, not RDF predicates.

The descriptive `source` field MUST remain distinct from execution inputs: cited resources use `dcterms:source`; artifacts actually processed use `prov:used`.

#### Digest boundaries

For file inputs, SHA-256 MUST be calculated over the exact bytes read. Source JSON checksums required under this rule MUST use the exact bytes read from the source file used for the transformation; a serialization of parsed data MUST NOT substitute for those bytes. In sidecar mode, the output-file digest MUST be calculated over the final serialized ontology bytes. The serialized-presentation freedom in §3.3 does not change these digest boundaries.

DirectKG MUST NOT compute a self-referential digest of embedded provenance.

The current version MUST NOT introduce canonicalized in-memory source checksums, additional checksum controls, or failure-handling mechanisms for such an extension (RD-05). Existing provenance modes and their requirements remain applicable, including the absence of transformation provenance under `none`. This decision does not change existing input, provenance, or output failure policies.

#### Delivery and Python access

The Python interface MUST expose semantically equivalent provenance and metadata-file controls, including the same provenance default. Separate provenance MUST be available programmatically as a graph, with explicit serialization for file output.

Provenance delivery failures MUST be reported. DirectKG MUST NOT silently downgrade the requested mode to `none`. Existing RD-04 ontology-output and diagnostic behavior remains applicable.

#### Required-provenance generation failure (RD-04)

Under `--provenance embedded` or `--provenance sidecar`, inability to construct required transformation provenance MUST produce an ERROR and abort the conversion before ontology delivery. DirectKG MUST NOT substitute another provenance mode or emit an incomplete required provenance record.

This behavior MUST be independent of `--input-policy`. Best-effort recovery from source-input errors MUST NOT authorize omission of required provenance.

Unavailability of optional automatically generated metadata under DK-GEN-11 MUST NOT, by itself, cause abort. An explicitly accepted exclusion MUST NOT be treated as a provenance-generation failure.

Under `--provenance none`, DirectKG MUST NOT perform provenance-only operations whose failure could prevent an otherwise valid conversion.

Required-provenance generation failure MUST follow the existing aborted-conversion contract under DK-DIAG-04–05 and §15: the outcome MUST be `aborted`; DirectKG MUST deliver no ontology output; diagnostics MUST remain programmatically available; requested diagnostics-file delivery MUST still be attempted; and the CLI MUST return exit code `3`, overridden by `4` if requested diagnostics-file delivery fails.

Provenance construction and sidecar delivery MUST remain distinct. Once provenance has been constructed, failure to serialize, create, or write its sidecar MUST follow the sidecar-delivery rules below: exit code `5`, subject to §15's delivery-failure precedence, with successfully written ontology output retained.

#### Provenance-sidecar delivery failure (RD-04)

Failure to serialize, create, or write a requested provenance sidecar MUST produce an ERROR. DirectKG MUST NOT report complete delivery. A successfully written ontology MUST remain available; DirectKG MUST NOT delete it solely because provenance-sidecar delivery failed.

DirectKG MUST NOT switch to `embedded` or `none`, or modify the ontology graph to compensate for the failure.

The CLI MUST use exit code `5` for provenance-sidecar delivery failure, subject to the delivery-failure precedence in §15. Diagnostics-file delivery failure (`4`) and, when applicable, ontology-file delivery failure (`6`) MUST take precedence over `5`. This behavior MUST be independent of `--input-policy`. Code `5` MUST take precedence over transformation codes `0` and `1`.

Transformation outcome and output delivery MUST remain distinct. The transformation outcome remains `completed` or `completed-with-errors`, according to transformation processing. Provenance-sidecar delivery MUST be reported separately as failed. The Python interface MUST expose this delivery failure explicitly rather than indicate fully successful delivery.

The failure MUST be reported through existing console and programmatic diagnostics and included in the requested diagnostics file. DirectKG MUST attempt requested diagnostics-file delivery after recording the sidecar failure.

A failed write MUST NOT leave a partial sidecar presented as a valid result. If an older sidecar remains at the destination, the failure report MUST explicitly state that it was not updated for the current execution.

Required-provenance generation failures before delivery follow the preceding abort rule. Failures to write the ontology itself remain outside this sidecar-delivery rule. Ontology-file creation and write failures after successful ontology serialization and construction of any required provenance follow DK-DIAG-04.

### DK-GEN-11 — Automatically generated metadata and external vocabularies (RD-05 / RD-27 / ODI-CONTROLS)

DK-GEN-09's seven-field whitelist MUST limit only ingestion from external `metadata.yaml`. It MUST NOT limit all metadata or provenance DirectKG may generate.

DirectKG MAY generate additional metadata or provenance when it can be determined reliably from the transformation context, source artifact, generated ontology, software execution, or output process, and it meaningfully improves description, traceability, reproducibility, or usability.

This permission remains subject to the selected provenance mode, the sidecar-only output-file boundary, and existing explicit omission rules, including DK-LBL-01's prohibition on RDF markers, annotations, or auxiliary resources solely to distinguish primary-relation fallback labels from source-authored labels, and DK-REL-01's omission of additional annotations solely recording the `historicalDependence` stereotype declaration. It MUST NOT be used to ingest excluded external metadata fields indirectly.

All metadata and provenance MUST use appropriate established external vocabulary terms. DirectKG MUST NOT define or emit DirectKG-specific metadata or provenance predicates. Where no appropriate standard representation has been identified, the concept MUST remain unsupported pending identification of such a representation or a separate explicit design decision.

## 6. Class transformation

### DK-CLS-01 — Domain classes

Every OntoUML class representing a domain type MUST become an `owl:Class`. Explicit boolean `isDerived` values follow DK-GEN-05 (RD-20).

Before applying this rule, a `«datatype»` classifier MUST be classified as a supported primitive, `void`, or custom datatype:

- Supported primitive datatype: no local `owl:Class`.
- `void`: no local `owl:Class` or OWL datatype.
- Custom datatype: local reified `owl:Class`.

Enumeration classifiers and their values are governed by DK-CLS-10–11 (RD-09). Every enumeration classifier is an `owl:Class`.

#### Preservation of `abstract` and `isAbstract` (RD-19)

DirectKG MUST preserve an explicitly supplied `abstract` class stereotype through an `rdfs:comment` on its generated OWL class. DirectKG MUST preserve explicit boolean `isAbstract` values through `rdfs:comment` annotations on the corresponding generated OWL class or primary relation property. Both explicit `true` and explicit `false` values are covered.

The stereotype and flag MUST be treated independently. DirectKG MUST NOT infer an `isAbstract` value from the `abstract` stereotype or from missing data.

These declarations MUST NOT, by themselves, generate additional logical constraints, including inferred completeness, emptiness, or additional classification. Existing class, relation, generalization-set, and stereotype-disjointness mappings remain applicable. Comment preservation requires the expressivity-loss INFO diagnostic under DK-DIAG-15; for the `abstract` stereotype, that diagnostic must not imply omission of the existing stereotype-disjointness mapping.

**Rationale (non-normative):** Comments retain the source declarations for readers while avoiding unsupported logical approximations. INFO makes the remaining expressivity loss visible without treating a valid source construct as erroneous. In particular, classifier abstractness alone does not establish completeness over the currently modeled specializations.

#### Preservation of `isExtensional` (RD-21)

DirectKG MUST preserve an explicit Boolean `isExtensional` value through an `rdfs:comment` annotation on the corresponding generated class. “Explicit” means present as a Boolean in the input JSON; it does not imply deliberate selection by the model author. DirectKG MUST NOT infer an `isExtensional` value when the field is absent or null.

For `isExtensional: true`, DirectKG MUST emit the INFO diagnostic specified in DK-DIAG-17. For `isExtensional: false`, DirectKG MUST NOT emit a diagnostic solely because of that value.

DirectKG MUST NOT generate additional logical axioms solely from this flag. Existing class and mereological mappings remain unchanged.

**Rationale (non-normative):** Extensionality concerns the essential dependence of a whole on its parts. Comment preservation retains the source declaration without substituting cardinality or range restrictions that do not capture that meaning. The INFO diagnostic makes this expressivity limitation visible.

#### Recognized omission of `restrictedTo` (RD-22)

DirectKG MUST recognize `restrictedTo` as supported input information but MUST NOT generate output solely from this field, including logical axioms, `rdfs:comment` annotations, or other annotations.

DirectKG MUST NOT emit an INFO diagnostic merely because `restrictedTo` is present or its information is omitted from the output. Recognized omission of this field MUST NOT itself trigger an unrecognized-information warning or error under any input policy. Existing handling of structurally invalid input remains unchanged.

This field MUST NOT replace stereotypes or alter the accepted class, disjointness, classifier-order, powertype, or higher-order classification mappings, including DK-CLS-03–05 and DK-HO-01–04. It MUST NOT introduce semantic-appropriateness validation. No transformation-time dependency on `restrictedTo` is introduced.

**Rationale (non-normative):** Ontological-nature information occurs widely in the input. Per-class INFO messages would create excessive diagnostic volume. The accepted treatment deliberately omits this information without adding annotations or logical constraints.

### DK-CLS-02 — Class generalization

For a class-to-class OntoUML generalization, DirectKG MUST emit:

```turtle
:Specific rdfs:subClassOf :General .
```

The transitive subclass closure need not be materialized. Class generalization-set disjointness in DK-CLS-06 and completeness in DK-CLS-07–08 (RD-13) preserve these subclass mappings. Relation-to-relation generalization is specified in DK-REL-14 (RD-12).

### DK-CLS-03 — Ultimate-sortal disjointness (ODI-DISJOINT)

The ultimate-sortal set is:

```text
collective, kind, mode, quality, quantity, relator, type
```

Any two distinct generated OWL classes directly carrying any stereotype in this set MUST be disjoint, including two classes carrying the same ultimate-sortal stereotype. Redundant subclass-inherited disjointness assertions need not be emitted. Serialization MUST follow the shared pairwise rule below DK-CLS-04 (ODI-DISJOINT).

### DK-CLS-04 — Cross-group disjointness (ODI-DISJOINT)

The following stereotype groups are established:

1. `abstract`, `datatype`, `enumeration`
2. `event`
3. `situation`
4. `kind`, `collective`, `quantity`, `relator`, `mode`, `quality`, `subkind`, `role`, `phase`, `category`, `mixin`, `roleMixin`, `phaseMixin`, `historicalRole`, `historicalRoleMixin`, `type`

Two generated classes MUST be disjoint when their stereotypes belong to different groups. This rule does not itself create intra-group disjointness. Primitive datatype elements and `void` do not participate because they do not generate local classes.

DirectKG MUST serialize the stereotype-based class disjointness required by DK-CLS-03 and DK-CLS-04 using pairwise `owl:disjointWith` statements. One statement per unordered pair is sufficient; reciprocal statements are not required. DirectKG MUST NOT use `owl:AllDisjointClasses` to represent disjointness under these two rules.

This serialization choice MUST preserve the class pairs required by DK-CLS-03 and DK-CLS-04: distinct generated classes directly carrying any ultimate-sortal stereotype remain disjoint, including classes carrying the same such stereotype; cross-group disjointness does not itself introduce intra-group disjointness. Disjointness independently required by other accepted mappings remains applicable. The existing permission to omit redundant subclass-inherited disjointness assertions remains unchanged. The separate generalization-set mapping in DK-CLS-06 remains unchanged.

**Rationale (non-normative):** Pairwise statements provide a uniform, directly inspectable representation consistent with the existing class generalization-set serialization, without introducing additional disjointness pairs.

The preservation of `abstract` and `isAbstract` under DK-CLS-01 (RD-19), and its INFO diagnostic under DK-DIAG-15, do not replace or disable this stereotype-disjointness mapping.

### DK-CLS-05 — Classifier order

Every explicit, non-null classifier `order` value MUST be preserved through an English `rdfs:comment`.

For a numeric value `N`:

```turtle
:Classifier rdfs:comment "OntoUML classifier order: N."@en .
```

For orderless `*`:

```turtle
:Classifier rdfs:comment "OntoUML classifier order: orderless (*)."@en .
```

Absent or null `order` produces no order comment. The comment is informative only and MUST NOT drive inference or semantic validation.

DirectKG MUST NOT represent classifier order using `ontouml:order`, lemon-tree, XKOS, another external machine-readable property, or a custom DirectKG property.

### DK-CLS-06 — Pairwise disjointness for class generalization sets (RD-13)

For a class generalization set with `isDisjoint: true`, DirectKG MUST emit pairwise `owl:disjointWith` statements between the generated OWL classes corresponding to its explicit specific classifiers. One statement per unordered pair is sufficient; reciprocal statements are not required.

This mapping MUST NOT include the general classifier or additional subclasses merely because they share the same general classifier. It MUST NOT additionally materialize inherited disjointness for descendants of the set's specific classifiers.

For `isDisjoint: false`, DirectKG MUST NOT generate disjointness axioms from that flag. This value neither asserts that overlap exists nor cancels disjointness required by other accepted mappings. Completeness is represented separately under DK-CLS-07–08; DirectKG MUST NOT replace the separate disjointness and completeness mappings with `owl:disjointUnionOf`.

Existing subclass mappings and stereotype-based disjointness rules in DK-CLS-02–04 MUST remain applicable. DirectKG MUST NOT check or repair semantic contradictions as a prerequisite to emitting these axioms, consistently with §3.4.

For the fully resolved singleton class set covered by DK-CLS-08, `isDisjoint: true` MUST generate no disjointness statement because there is no pair of specific classes to constrain. Disjointness required by other accepted mappings remains applicable.

For partial failures, DK-CLS-09 preserves pairwise disjointness among successfully resolved and generated specific classes when `isDisjoint: true`. Explicitly empty `generalizations` arrays are governed by DK-DIAG-12. This specification defines no handling for missing or malformed membership containers. This rule does not define the serialization of disjointness generated by other accepted mappings.

**Rationale and example (non-normative):** For a disjoint generalization set containing the specializations of `A` by `B`, `C`, and `D`, the additional output is:

```turtle
:B owl:disjointWith :C, :D .
:C owl:disjointWith :D .
```

The existing subclass statements remain unchanged. Pairwise statements make the disjointness directly inspectable without traversing an RDF list.

### DK-CLS-07 — Coverage of complete class generalization sets (RD-13)

For a class generalization set with `isComplete: true`, whose member generalizations resolve to a common generated general class and at least two distinct generated specific classes, DirectKG MUST emit a covering axiom:

```turtle
:GeneralClass rdfs:subClassOf [
    a owl:Class ;
    owl:unionOf ( :SpecificClass1 :SpecificClass2 )
] .
```

The union MUST contain only the specific classes explicitly participating in that generalization set.

For `isComplete: false`, DirectKG MUST NOT generate a covering axiom from that flag. This value MUST NOT be translated into an assertion that additional instances or subclasses exist.

Existing subclass and disjointness mappings MUST remain applicable. DirectKG MUST NOT test or repair semantic consistency as a prerequisite to emitting the covering axiom.

Completeness and disjointness MUST be represented separately. DirectKG MUST NOT replace these mappings with `owl:disjointUnionOf`.

This union-based mapping applies to fully resolved class generalization sets with at least two distinct specific classes. DK-CLS-08 extends completeness to fully resolved singleton sets using a reverse subclass axiom. When a member reference is unresolved or a member transformation fails, DK-CLS-09 prohibits constructing coverage from the surviving members. Explicitly empty `generalizations` arrays are governed by DK-DIAG-12. Duplicate-member handling and missing or malformed membership containers remain outside these decisions.

**Rationale and example (non-normative):** For a complete set of specializations of `A` by `B`, `C`, and `D`:

```turtle
:B rdfs:subClassOf :A .
:C rdfs:subClassOf :A .
:D rdfs:subClassOf :A .

:A rdfs:subClassOf [
    a owl:Class ;
    owl:unionOf ( :B :C :D )
] .
```

Every instance of `A` must belong to at least one listed specific class. Overlap remains possible unless disjointness is separately required.

### DK-CLS-08 — Complete singleton class generalization sets (RD-13)

For a fully resolved class generalization set containing exactly one member generalization, from specific class `B` to general class `A`, when `isComplete: true`, DirectKG MUST emit:

```turtle
:A rdfs:subClassOf :B .
```

The existing generalization mapping in DK-CLS-02 MUST remain applicable:

```turtle
:B rdfs:subClassOf :A .
```

DirectKG MUST express singleton coverage using the reverse subclass axiom, rather than a one-member union or an additional `owl:equivalentClass` axiom.

DirectKG MUST NOT issue a warning solely because the generalization set contains one member. Whenever this singleton completeness mapping is applied, DirectKG MUST emit the nonfatal INFO diagnostic specified in DK-DIAG-14, identifying the set and its general and specific class and explaining their extensional equivalence with distinct identifiers.

If `isDisjoint: true`, this singleton set MUST generate no disjointness statement, because there is no pair of specific classes to constrain. Disjointness required by other accepted mappings remains applicable.

This extends the completeness mapping to fully resolved singleton sets and does not replace DK-CLS-07's mapping for sets with at least two distinct specific classes. DK-CLS-09 prohibits applying this singleton-completeness mapping merely because partial failure leaves one surviving member. Explicitly empty `generalizations` arrays are governed by DK-DIAG-12. Duplicate-member handling remains excluded from this decision.

**Rationale (non-normative):** The two subclass axioms entail that `A` and `B` have the same instances. Their identifiers remain distinct. The reverse subclass axiom preserves the stated completeness without requiring a one-member union.

### DK-CLS-09 — Partial recovery of class generalization-set constraints (RD-13 / RD-02)

Under `best-effort`, when an unresolved member reference or failed member transformation prevents constructing a class generalization set's full coverage, DirectKG MUST omit that set's covering axiom. It MUST NOT generate coverage using only the surviving members.

If `isDisjoint: true`, DirectKG MUST retain pairwise `owl:disjointWith` statements among the successfully resolved and generated specific classes. Fewer than two such classes MUST produce no disjointness statements from that set.

DirectKG MUST NOT apply the singleton-completeness mapping in DK-CLS-08 merely because only one member survives reference resolution or transformation.

The underlying failure MUST retain error severity. Under `strict` or `tolerant`, DirectKG MUST report the error and abort the transformation under DK-DIAG-05. Under `best-effort`, independently applicable class and generalization mappings MUST remain applicable.

This rule does not change the mappings for fully resolved sets. It does not settle categorizer recovery or missing or malformed membership containers.

**Rationale and example (non-normative):** If a complete, disjoint set specializes `A` into `B`, `C`, and `D`, but the `D` member cannot be resolved or transformed, retaining `B owl:disjointWith C` preserves part of the original constraint. Covering `A` using only `B` and `C` would incorrectly strengthen the model by excluding the missing alternative.

### DK-CLS-10 — Enumeration representation (RD-09)

DirectKG MUST represent an enumeration classifier as an `owl:Class`.

Each successfully transformed source enumeration literal MUST become an `owl:NamedIndividual`, explicitly typed as an instance of its enumeration class.

For a nonempty enumeration whose complete source value list is successfully transformed, DirectKG MUST define the enumeration class's extension using `owl:oneOf` containing the generated value individuals.

Distinct successfully transformed source values within the same enumeration MUST be asserted mutually different. When at least two distinct value individuals are generated, DirectKG MUST express this using `owl:AllDifferent`.

Attributes typed by an enumeration MUST become `owl:ObjectProperty` resources with the enumeration class as their range, as reflected in DK-ATT-01 and DK-GEN-03.

Applicable class generalization and class-disjointness mappings MUST remain applicable.

Value sources and complete or incomplete value-list handling are specified in DK-CLS-11. Value identity, IRI construction, and labels are specified in DK-IRI-08 and DK-LBL-01. Diagnostics and input-policy behavior are specified in DK-DIAG-13.

**Rationale and example (non-normative):**

```turtle
:OrderStatus a owl:Class ;
    owl:oneOf ( :OrderStatus_Pending :OrderStatus_Approved ) .

:OrderStatus_Pending a owl:NamedIndividual, :OrderStatus ;
    rdfs:label "Pending" .

:OrderStatus_Approved a owl:NamedIndividual, :OrderStatus ;
    rdfs:label "Approved" .

[] a owl:AllDifferent ;
   owl:distinctMembers ( :OrderStatus_Pending :OrderStatus_Approved ) .
```

`owl:oneOf` defines the complete extension. `owl:AllDifferent` establishes inequality between the values, which different IRIs alone do not establish.

### DK-CLS-11 — Enumeration value sources and closure recovery (RD-09)

Only source enumeration literals explicitly encoded in the classifier's `literals` collection supply enumeration values under RD-09.

A `Property` element MUST NOT be reinterpreted as an enumeration value merely because it belongs to an enumeration classifier, has a name resembling a value, has null `propertyType`, or occurs alongside a null, absent, or empty `literals` field. Such properties MUST retain independently applicable property or attribute mappings. DirectKG MUST NOT infer a historical exporter convention from this structure alone.

When `literals` is null, absent, or explicitly empty, DirectKG MUST retain the enumeration class and independently applicable mappings. DirectKG MUST NOT emit `owl:oneOf`, equate the class with `owl:Nothing`, or otherwise assert an empty extension from this condition. The warning and nonfatal behavior for this defined fallback are specified in DK-DIAG-13.

Malformed value lists and untransformable supplied values follow DK-DIAG-13 and the accepted input-policy rules. Whenever processing continues, DirectKG MUST preserve successfully generated value individuals and their enumeration-membership assertions.

An enumeration value successfully preserved through DK-IRI-04's generic source-ID fallback MUST count as successfully transformed when applying enumeration membership, `owl:oneOf`, and `owl:AllDifferent`. A fallback alone MUST NOT make the value list incomplete.

DirectKG MUST emit `owl:oneOf` only when the source value list is nonempty and every supplied source value was successfully transformed. It MUST NOT close an enumeration over only the surviving subset.

DirectKG MUST emit `owl:AllDifferent` when at least two distinct value individuals were successfully generated, including during incomplete transformation. The general completeness and generated-value-count rules require:

| Transformation result | `owl:oneOf` | `owl:AllDifferent` |
|---|---|---|
| Complete, nonempty list | Yes | When at least two distinct values are generated |
| Incomplete, at least two survivors | No | Yes |
| Incomplete, exactly one survivor | No | No |
| Incomplete, no survivors | No | No |

During incomplete transformation, exactly one surviving value MUST retain its individual and enumeration-membership assertion, but DirectKG MUST emit neither `owl:oneOf` nor `owl:AllDifferent`. With no surviving values, DirectKG MUST emit neither axiom and MUST retain the enumeration class and other independently applicable mappings subject to existing transformation and input-policy rules.

Multiple-survivor and one-survivor cases MUST NOT require separate implementation features. No dedicated validation pass, catalog-verification rule, configuration option, error category, or diagnostic code is required for those cases. Existing transformation errors provide the required reporting for failed values; no additional diagnostic is required solely because incomplete transformation leaves multiple, one, or zero surviving values.

## 7. Higher-order classification and generalization-set categorizers

### DK-HO-01 — OWL 2 punning

DirectKG MUST use OWL 2 punning for higher-order classification.

Every supported OntoUML class remains an `owl:Class`, subject to the datatype classification exceptions in DK-CLS-01. When classifier `S` is explicitly classified by higher-order classifier `C`, the same IRI for `S` also serves as an `owl:NamedIndividual`, and DirectKG MUST emit:

```turtle
:S rdf:type :C .
```

This rule MAY be applied recursively at further classification orders. DirectKG MUST NOT create companion IRIs or separate classifier-representation resources.

Documentation MUST explain that the shared IRI has logically separate class and individual facets under OWL 2 punning; axioms about one facet do not automatically entail facts about the other.

### DK-HO-02 — Ordinary categorizer rule

For a generalization set whose categorizer is `C`, DirectKG MUST emit `S rdf:type C` for every explicit specific classifier `S` in the set. Each categorizer declaration is transformed as stated. Multiple higher-order classifications of the same classifier MUST all be emitted.

When `C.isPowertype` is false or null, only the set's explicit specifics receive this assertion from the categorizer rule. The common general and specializations outside the set do not.

### DK-HO-03 — Powertype extension

`isPowertype` is a property of the categorizer classifier, not of the generalization set. For a generalization set categorized by `P`, where the member generalizations share common general classifier `B`, if `P.isPowertype` is true, DirectKG MUST explicitly emit `rdf:type P` for:

- `B` itself;
- every modeled direct specialization of `B`;
- every modeled indirect specialization of `B`;
- including modeled specializations not explicitly listed in the generalization set.

These assertions MUST be materialized because subclass axioms over the class facets do not propagate `rdf:type` facts over their punned individual facets. The rule applies only to classifiers represented in the transformed model and makes no claim about unknown, unmodeled, or future specializations.

### DK-HO-04 — No higher-order reconciliation or validation

`restrictedTo` is recognized and omitted under DK-CLS-01 (RD-22). It MUST NOT alter the powertype or higher-order classification mappings in DK-HO-01–03 or introduce semantic-appropriateness validation.

DirectKG MUST NOT:

- compare or reconcile `«instantiation»` with `GeneralizationSet.categorizer`;
- establish precedence between higher-order classification sources;
- suppress multiple classifications;
- validate classifier orders or stereotype appropriateness;
- detect semantic conflicts among higher-order classifications;
- suppress an assertion because it might contribute to an inconsistent ontology.

Different higher-order types are not treated as conflicting merely because they classify related elements.

The class generalization-set `isDisjoint` mapping is specified in DK-CLS-06 and completeness in DK-CLS-07–08 (RD-13). Partial recovery of those class-set constraints is specified in DK-CLS-09 (RD-13 / RD-02). Explicitly empty `generalizations` arrays are structural errors under DK-DIAG-12 (RD-13 / RD-02). Relation generalization-set disjointness is specified in DK-REL-15 (RD-13). DK-REL-16 establishes the explicit coverage limitation for complete relation sets with two or more distinct specific relations. DK-REL-20 specifies fully resolved singleton relation-set completeness. Duplicate-member handling, handling for missing or malformed membership containers, and categorizer recovery when a class-set member is unresolved or fails transformation remain unspecified.

## 8. Attributes and datatypes

### DK-ATT-01 — Attribute property kind

Explicit boolean `isDerived` values on source attributes follow DK-GEN-05 (RD-20); the flag does not suppress ordinary attribute transformation.

An attribute is classified by its resolved `propertyType`. For a supported datatype classifier with a localized name, primitive recognition uses DK-IRI-10's selector and the selected original text under DK-DAT-02, independently of the IRI strategy:

| Source type | Generated property | Range behavior |
|---|---|---|
| Supported primitive datatype | `owl:DatatypeProperty` | Registered XSD datatype |
| Custom `«datatype»` | `owl:ObjectProperty` | Custom datatype class |
| `«enumeration»` | `owl:ObjectProperty` | Enumeration class generated under DK-CLS-10 |
| `null` | `owl:DatatypeProperty` | No range |
| Visual Paradigm `void` | `owl:DatatypeProperty` | No range; warning |

The attribute's domain is always its owning class. Enumeration-typed attributes follow the object-property and range mapping established by RD-09 in DK-CLS-10.

For a supported attribute that generates a property, `isReadOnly: true` is preserved as a comment on that property under DK-PROP-04 (RD-24). Ordering declarations with `isOrdered: true` follow DK-PROP-05 (RD-23), including per-occurrence INFO reporting under DK-DIAG-18. An explicitly supplied, recognized `begin` or `end` property stereotype follows the English-comment preservation mapping under DK-PROP-06 (RD-18).

### DK-ATT-02 — Necessary conditions

Attribute class constraints MUST be expressed through `rdfs:subClassOf` restrictions, not `owl:equivalentClass`. They are necessary conditions rather than exhaustive definitions of the owning class.

### DK-ATT-03 — Explicit attribute multiplicity

An explicit attribute multiplicity MUST be preserved as OWL cardinality restrictions:

| Multiplicity | Required restriction |
|---|---|
| `[1]` | exactly 1 |
| `[1..*]` | minimum 1 |
| `[0..1]` | maximum 1 |
| `[2..5]` | minimum 2 and maximum 5 |
| `[l..u]` | minimum `l` when `l > 0`; maximum `u` when finite |
| `[l..u]`, with nonnegative integer bounds and `l > u` | minimum `l` and maximum `u` under every input policy; no warning or error solely for the contradiction (§3.4, RD-11) |

When `l = u = n`, DirectKG MAY use an exact-cardinality restriction instead of separate minimum and maximum restrictions.

Cardinality mappings remain unchanged by the removal of the optional value-type restriction behavior under DK-ATT-04. Multiplicity-derived restrictions using object-property expressions made non-simple by actually emitted material chains remain subject to DK-REL-07's targeted `omit-conflicting-constraints` rule, including propagated effects through accepted subproperty and inverse mappings.

For supported attributes, an explicit JSON `cardinality: null` MUST be treated as the absence of an explicit multiplicity available for transformation. DirectKG MUST NOT generate a cardinality restriction from that value or substitute a default multiplicity. All other applicable mappings MUST continue. An explicit null cardinality MUST NOT, by itself, cause a warning, error, or transformation failure under any input policy. Null MUST remain distinct from explicit `*` or `0..*`.

This explicit-null handling is established by RD-11 / DK-ATT-03. The corresponding ordinary relation-end handling is specified in DK-REL-13. An absent `cardinality` field uses the fallback in DK-DIAG-09 (RD-11 / RD-02): no cardinality restriction or default multiplicity, a warning identifying the affected property, and continuation of all other applicable mappings under every input policy. Untranslatable multiplicities and bounds follow DK-DIAG-10, including partial recovery of independently valid numeric bounds in `best-effort`. Contradictory numeric intervals are transformable under §3.4 (RD-11). Cardinality syntax, limited lexical normalization, and treatment of ambiguous malformed expressions are specified in DK-DIAG-11 (RD-11 / RD-02).

### DK-ATT-04 — No redundant local value-type restrictions (ODI-VALUE-RESTRICTIONS)

DirectKG MUST NOT provide the optional `owl:allValuesFrom` control previously specified by this rule. Its corresponding optional transformation behavior is removed.

Typed attributes MUST continue to receive their existing property-kind and global `rdfs:range` mappings under DK-ATT-01 and DK-GEN-03. Existing cardinality mappings remain unchanged.

DirectKG MUST NOT generate local `owl:allValuesFrom` restrictions solely to repeat the same type already expressed by the generated property's global `rdfs:range`. Untyped and `void` attributes retain their existing no-range and no-value-type-restriction treatment under DK-DAT-03 and DK-DAT-04.

Any future support for genuinely class-specific value restrictions that are not entailed by the global property range requires a separate feature and design decision. This decision does not authorize such support. Removal of the option also resolves the question of extending that option to ordinary relations; no such extension is established.

**Rationale (non-normative):** The global property range already entails a local universal restriction using the same type. Explicitly repeating that restriction adds no logical constraint. No concrete downstream-consumer requirement for that explicit representation was established in the accepted decision discussion; its redundancy therefore does not justify the additional control, transformation behavior, maintenance, or output.

### DK-DAT-01 — Visual Paradigm built-ins

Recognized Visual Paradigm datatype names are:

```text
boolean, byte, char, double, float, int, long, short, string, void
```

Established mappings are:

| Source | Target |
|---|---|
| `boolean` | `xsd:boolean` |
| `byte` | `xsd:byte` |
| `char` | `xsd:string` |
| `double` | `xsd:double` |
| `float` | `xsd:float` |
| `int` | `xsd:int` |
| `long` | `xsd:long` |
| `short` | `xsd:short` |
| `string` | `xsd:string` |

The `char → xsd:string` mapping deliberately loses the one-character constraint.

### DK-DAT-02 — Primitive normalization and registry

Primitive resolution uses aggressive lexical normalization followed by exact lookup in a controlled registry. Normalization does not itself determine semantics and applies only to classifiers being interpreted as datatypes.

The normalization SHOULD:

1. perform Unicode normalization;
2. trim surrounding whitespace;
3. case-fold;
4. recognize known XSD prefix or namespace forms before ordinary normalization;
5. ignore whitespace, hyphen, and underscore separators;
6. perform exact lookup using the normalized key.

The following nine entries MUST constitute the complete current primitive registry:

| Normalized key | Target |
|---|---|
| `boolean` | `xsd:boolean` |
| `byte` | `xsd:byte` |
| `char` | `xsd:string` |
| `double` | `xsd:double` |
| `float` | `xsd:float` |
| `int` | `xsd:int` |
| `long` | `xsd:long` |
| `short` | `xsd:short` |
| `string` | `xsd:string` |

No additional primitive mappings are registered. Excluded mappings MUST NOT be retained as provisional registry entries or pending mapping candidates. Future registry additions require a separate explicit decision. Semantically distinct XSD datatypes, including `xsd:int` and `xsd:integer`, MUST remain distinct; this distinction does not register a mapping for `integer`.

Standard prefixed and full XSD datatype identifiers for supported registry entries SHOULD be recognized. Such recognition MUST be limited to supported registry entries and MUST NOT provide an independent route to mappings outside this nine-entry registry. Semantic aliases such as `bool`, `str`, `wholeNumber`, or `integer32` MUST be accepted only if explicitly registered; the examples do not themselves activate those aliases.

DirectKG MUST NOT use fuzzy matching, edit-distance correction, stemming, singular/plural normalization, abbreviation expansion, translation, or synonym detection for datatype resolution.

**Rationale (non-normative, ODI-DATATYPES, option C):** A bounded registry provides a clear mapping contract aligned with the supported exporter's identified primitive names. Other modeled datatypes retain their custom-type representation.

#### Multilingual datatype names (RD-27, option A)

For a supported datatype classifier whose name is represented as a `languageString`, DirectKG MUST reuse DK-IRI-10's lexical selection algorithm, including its candidate eligibility, language-key ordering, text tie-breaking, and existing fallback boundaries, to obtain the name used for primitive recognition.

DirectKG MUST pass the selected original source text through the existing primitive normalization and exact registry lookup above. The lookup input MUST NOT be the normalized or disambiguated IRI local name, a synthetic fallback name, or the final IRI.

Only the selected value MUST participate in primitive recognition. Other localized values MUST NOT supply alternative primitive matches or trigger comparison of competing registry outcomes. Existing primitive, custom-datatype, and `void` behavior MUST apply to the selected value.

Selection for primitive recognition MUST be the same under the `name` and `id` IRI strategies. Selection MUST remain independent of `--language`, its equivalent Python control, and `Project.languages`. Plain-string datatype names retain their existing treatment.

The nine-entry primitive registry and its mappings remain unchanged. Existing normalization rules and their normative strength remain unchanged; this selection registers no additional aliases or XSD mappings.

DirectKG MUST NOT introduce additional diagnostics or conflict handling for multilingual primitive recognition. Existing diagnostics, including applicable naming warnings, `void` warnings, and input errors, remain unchanged. Existing label rules continue to apply where their output targets exist.

**Rationale and examples (non-normative):** Reusing the selector avoids additional recognition and conflict logic for a variation absent from the inspected catalog.

For `{"de":"Ganzzahl","en":"int"}`, the selector chooses `Ganzzahl`; it does not match the primitive registry, so existing custom-datatype treatment applies.

For `{"en":"int","nl":"float"}`, the selector chooses `int`; recognition yields `xsd:int`, without a multilingual-conflict diagnostic. The unselected `float` value does not participate in primitive recognition.


### DK-DAT-03 — Untyped attributes

`propertyType = null` means that no datatype was specified. The attribute MUST remain an `owl:DatatypeProperty`, retain its domain, and retain any explicit cardinality. It receives no range or value-type restriction.

DirectKG MUST NOT substitute `rdfs:Literal`, `xsd:string`, or another guessed datatype.

### DK-DAT-04 — Visual Paradigm `void`

`void` is recognized but unsupported. DirectKG MUST NOT map it to an XSD datatype, OWL datatype, local class, `rdfs:Literal`, `owl:Nothing`, `owl:bottomDataProperty`, `xsd:anySimpleType`, `xsd:anyAtomicType`, or a locally invented empty datatype.

An attribute typed by `void`:

- MUST still become an `owl:DatatypeProperty`;
- MUST receive its domain and any explicit cardinality;
- MUST NOT receive a range or local value-type restriction from `void`;
- MUST produce a non-fatal warning identifying the attribute, owner, `void`, and the missing mapping/range where available.

This differs from `null`: `null` means unspecified, while `void` means explicitly selected, recognized, and unsupported.

The unsupported status of `void` MUST be explicitly documented in user-facing DirectKG documentation.

### DK-DAT-05 — Custom datatypes

An otherwise supported `«datatype»` classifier that does not resolve through DK-DAT-02's registry and is not `void` MUST receive this custom-datatype treatment. Excluding a primitive mapping MUST NOT cause the source datatype element to be discarded.

A custom OntoUML datatype MUST become a reified `owl:Class`. An attribute or otherwise eligible explicit relation targeting it MUST become an `owl:ObjectProperty` with the custom datatype class as range. A relation with a relation-valued endpoint is governed by DK-REL-08, DK-REL-18, or DK-REL-17, as applicable, without changing this mapping for eligible class-endpoint relations.

DirectKG MUST preserve the structured value and MUST NOT flatten the custom datatype's attributes into the referring classifier. Nested custom datatype properties MUST be transformed recursively under the same rules.

DirectKG MUST NOT infer an XSD mapping from a custom datatype's name. For example, `TimeInterval` does not automatically become `xsd:duration`.

## 9. Property identity, labels, and general collision rules

### DK-PROP-01 — Distinct property identity

Every distinct source attribute or relation that undergoes property generation MUST remain a distinct OWL property. Material–relator and material–mode derivation connectors covered by DK-REL-08, comparative–quality derivation connectors covered by DK-REL-18, and unsupported relation-valued endpoint connectors covered by DK-REL-17 do not undergo property generation. DirectKG MUST NOT merge independently modeled properties because their names or normalized candidates coincide. IRI disambiguation MUST NOT change whether a property is an object or datatype property.

Property-inclusion axioms generated from UML subsetting and redefinition under DK-PROP-03 (RD-14) MUST NOT merge or replace the properties involved.

The shared generic superproperties in DK-REL-19 (RD-17 / RD-25) likewise MUST NOT merge or replace source-specific mereological properties; their established identities and IRIs remain distinct.

DirectKG MUST NOT repair merged properties by introducing union domains or ranges.

### DK-PROP-02 — Name-based owner/source qualification

For source-backed properties in name mode, a unique normalized property candidate MAY be used directly. When ordinary source-backed properties collide, DirectKG MUST first qualify them as:

```text
<propertyName>_<ownerOrSourceName>
```

Supported localized names supplying property or owner/source naming components follow DK-IRI-10.

When this qualification is required and the owner/source classifier has no usable normalized name under the existing name-selection and normalization rules in DK-IRI-03 and DK-IRI-10, DirectKG MUST use that classifier's DK-IRI-04 fallback candidate as the qualifier:

```text
unnamedClass_<escaped-source-id>
```

The source ID MUST be the owner/source classifier's own ID. DirectKG MUST reuse this candidate unchanged, including the technical source-ID escaping defined by DK-IRI-05. The qualifier MUST use the candidate before classifier collision handling and MUST NOT include subsequently assigned classifier collision suffixes.

If collisions remain, every member of the collision group MUST receive deterministic `_1` through `_N` suffixes. No unsuffixed member remains in a collision group. Source IDs MAY determine stable numbering but need not appear in the IRI.

Existing property collision handling under DK-IRI-07, distinct property identity under DK-PROP-01, and source-authored label rules remain applicable without change.

DirectKG MUST NOT introduce an additional diagnostic solely because this qualification rule is used. Existing missing-name, fallback, and input diagnostics remain applicable.

This fallback qualification rule applies only to owner/source qualification of source-backed properties under this rule. Qualification using usable owner/source names, ID-mode property construction, and generated-inverse naming retain their existing rules.

**Rationale and example (non-normative, ODI-IRI, option A — owner/source qualification):** Reusing the established class fallback avoids introducing a separate owner-qualification convention. Using the candidate before classifier collision suffixes preserves the existing ordering in which property qualification precedes final collision resolution.

For example, when a property named `name` requires qualification and its unnamed owner has source ID `C17`, its qualified candidate is:

```text
name_unnamedClass_C17
```

Existing property collision handling then applies.

### DK-PROP-03 — UML property subsetting and redefinition (RD-14)

For every explicit UML Property reference `p1 subsets p0` in `subsettedProperties`, DirectKG MUST generate `OWL(p1) rdfs:subPropertyOf OWL(p0)`. For every explicit UML Property reference `p1 redefines p0` in `redefinedProperties`, DirectKG MUST generate the same property-inclusion axiom. Subsetting and redefinition remain semantically distinct UML relationships despite this shared DirectKG mapping.

`OWL(p)` is the OWL property or property expression assigned to UML Property `p` under the accepted property-generation and direction rules:

| UML Property | `OWL(p)` |
|---|---|
| Classifier-owned attribute | Its generated OWL property |
| Target association end | The relation's primary property |
| Source association end with a generated named inverse | The corresponding named inverse property |
| Source association end without a generated named inverse, when the primary object property exists | An anonymous inverse expression of that primary property |

Each association end MUST be resolved independently. For either `subsets` or `redefines`, the direction combinations are:

| Referencing end → referenced end | Property inclusion |
|---|---|
| Target → target | Forward → forward |
| Source → source | Inverse → inverse |
| Target → source | Forward → inverse |
| Source → target | Inverse → forward |

DirectKG MUST process every explicit subsetting and redefinition reference independently and preserve multiple superproperty relationships. It MUST deduplicate identical resulting axioms. It MUST NOT additionally emit logically entailed inverse counterparts or materialize the transitive closure of the property hierarchy. These requirements are distinct from DK-INV-12's explicit mirroring of relation generalizations.

Eligibility requires structural resolution and an OWL property expression for each referenced UML Property under existing mappings. If an accepted rule intentionally produces no property expression for either UML Property, including an unsupported relation-valued endpoint connector under DK-REL-17 (RD-16), DirectKG MUST NOT generate a property solely for the reference or override that non-representation decision. An anonymous inverse expression under this rule MUST NOT force generation of a named inverse property, assign an inverse name, or change established primary and inverse naming and IRI rules. DK-INV-04 permits this additional anonymous-inverse use specifically for RD-14; inverse-generation modes and eligibility remain unchanged.

DirectKG MUST NOT check owner, endpoint, type, property-kind, or other UML semantic compatibility before applying this mapping. Structurally processable references with available property expressions remain transformable even if the source appears semantically invalid or the resulting graph may be outside an OWL 2 DL profile. Unresolved references and failures of required underlying property transformations follow DK-DIAG-05 and other applicable diagnostic rules.

The `redefines` mapping is a partial translation: it preserves property inclusion without representing UML's full contextual replacement semantics. From the redefinition relationship alone, DirectKG MUST NOT derive `owl:equivalentProperty`, contextual value equality, property merging or replacement, additional domain or range axioms, or copied or additional cardinality restrictions. Independently applicable property declarations, domains, ranges, cardinalities, and relation-generalization rules remain unchanged.

DirectKG MUST document redefinition as a partial translation. It MUST NOT emit a runtime warning solely because a structurally processable `redefines` relationship is transformed under this rule. Other applicable diagnostics remain required. RD-14 does not define the general output and OWL-profile contract, which remains the responsibility of RD-04.

**Rationale and example (non-normative):** Subsetting expresses inclusion of property extensions. Redefinition has stronger contextual semantics; this mapping preserves its property-inclusion consequence. For primary properties `a1` and `a0`, the four association-end combinations generate, respectively, `a1 ⊑ a0`, `inverse(a1) ⊑ inverse(a0)`, `a1 ⊑ inverse(a0)`, and `inverse(a1) ⊑ a0`. Generated named inverses are used when present; otherwise `inverse(a)` is an anonymous inverse expression. No special inverse name is created by this mapping.

### DK-PROP-04 — Comments for read-only and aggregation metadata (RD-24 / RD-25)

DirectKG MUST preserve the following source characteristics as human-readable `rdfs:comment` annotations where the applicable generated property exists:

| Source occurrence | Comment target and required source context |
|---|---|
| `isReadOnly: true` on a supported class attribute | Its successfully generated attribute property; identify that the attribute is read-only |
| `isReadOnly: true` on either end of an eligible ordinary relation | Its successfully generated primary source-specific object property; identify the source or target association end |
| `aggregationKind: "SHARED"` on either end of an eligible ordinary relation | The same primary property; identify the source or target association end and shared aggregation |
| `aggregationKind: "COMPOSITE"` on either end of an eligible ordinary relation | The same primary property; identify the source or target association end and composite aggregation |

Each applicable occurrence MUST be preserved. If both ends carry a characteristic or one end carries multiple covered characteristics, the comments MUST retain those distinct facts. Comment preservation MUST NOT depend on whether a separately named inverse property is generated. DirectKG MUST NOT create a property or inverse property solely to host these comments.

Comment wording SHOULD be consistent. Suitable forms include:

```text
OntoUML source metadata: this attribute is read-only.
OntoUML source metadata: the source association end is read-only.
OntoUML source metadata: the target association end is read-only.
OntoUML source metadata: the source association end has shared aggregation.
OntoUML source metadata: the target association end has shared aggregation.
OntoUML source metadata: the source association end has composite aggregation.
OntoUML source metadata: the target association end has composite aggregation.
```

Comments are informational annotations only and introduce no additional OWL logical semantics. DirectKG MUST NOT introduce dedicated DirectKG vocabulary properties solely to represent `isReadOnly`, shared aggregation, or composite aggregation.

DirectKG MUST preserve the covered comments according to characteristics explicitly present in the supported source representation. This mapping MUST NOT use `isReadOnly`, `SHARED`, or `COMPOSITE` to reverse or normalize relation direction, determine eligibility for the generic mereological mapping, replace a primary property with a named or anonymous inverse, create additional logical property characteristics, repair the source model, or infer semantics not independently established by another accepted rule. In particular, `isReadOnly` alone MUST NOT imply an existential-dependence axiom. Independently applicable mappings remain in force. The comments preserve source information for human-readable documentation and provenance without guaranteeing machine-readable reconstruction or round-tripping from the generated OWL ontology.

**Non-normative example:** A primary relation property may carry both `rdfs:comment "OntoUML source metadata: the target association end is read-only."@en` and `rdfs:comment "OntoUML source metadata: the target association end has composite aggregation."@en` when both characteristics occur on its target end.

### DK-PROP-05 — Comments for ordered attributes and relation ends (RD-23)

For `isOrdered: true`, DirectKG MUST preserve the ordering declaration as an `rdfs:comment` at the following location, following DK-PROP-04's annotation placement:

| Source occurrence | Comment target and required source context |
|---|---|
| `isOrdered: true` on a supported attribute | Its successfully generated property |
| `isOrdered: true` on either end of an eligible ordinary relation | Its successfully generated primary source-specific object property; the comment MUST identify whether the declaration concerns the source or target end |

If both relation ends are ordered, both occurrences MUST be preserved. Comment preservation MUST NOT depend on whether a separately named inverse property is generated. For each occurrence preserved under this rule, DirectKG MUST emit the INFO diagnostic specified in DK-DIAG-18.

For `isOrdered: false`, or when the field is absent or null, DirectKG MUST NOT generate an ordering comment or ordering-loss INFO. DirectKG MUST NOT infer `isOrdered: true`.

Existing range, cardinality, and inverse mappings MUST remain unchanged. DirectKG MUST NOT create lists, sequence structures, properties, or inverse properties solely because of this flag. DK-PROP-04's existing rules and their diagnostic behavior remain unchanged.

**Rationale (non-normative):** The comments preserve the declaration that values are ordered, not an actual sequence of values. INFO diagnostics expose this limitation only for explicit `true` occurrences, avoiding routine messages for unordered properties.

### DK-PROP-06 — Comments for `begin` and `end` property stereotypes (RD-18)

DirectKG MUST preserve each explicitly supplied, recognized `begin` or `end` property stereotype through an English `rdfs:comment` identifying the declared stereotype.

Comment placement MUST follow this mapping, alongside the annotation-placement pattern in DK-PROP-04–05:

| Source occurrence | Comment target |
|---|---|
| Supported attribute carrying `begin` or `end` | Its successfully generated property |
| Source end of an eligible ordinary relation carrying `begin` or `end` | The successfully generated primary relation property; identify the source association end |
| Target end of an eligible ordinary relation carrying `begin` or `end` | The successfully generated primary relation property; identify the target association end |

If both association ends carry a covered stereotype, both occurrences MUST be preserved. Preservation MUST remain independent of named-inverse generation.

Existing naming, property-kind, range, cardinality, and inverse mappings MUST remain unchanged, including DK-DAT-03's treatment of untyped attributes. These stereotypes MUST NOT, by themselves, introduce additional logical axioms or temporal validation.

DirectKG MUST NOT infer `begin` or `end` stereotypes from names, supply a missing counterpart, or reconstruct stereotype information discarded by the exporter. Preservation applies to the recognized stereotype explicitly supplied in the supported input.

These transformation-generated comments remain subject to DK-LBL-02's generated-comment language handling.

This mapping MUST NOT introduce a runtime diagnostic solely for its comment-based preservation. Existing diagnostics MUST retain their established conditions, including the separate diagnostic requirements of DK-PROP-04–05.

Documentation MUST explain that the comments preserve boundary-stereotype declarations without enforcing temporal semantics.

**Rationale and example (non-normative):** Comments retain the explicit boundary designation without selecting a temporal datatype or supplying temporal inference.

An illustrative comment on a generated attribute property is:

```turtle
:startTime rdfs:comment
    "Declared OntoUML property stereotype: begin."@en .
```

The wording is illustrative rather than a required literal template.

### DK-LBL-01 — Source labels and configurable primary-relation labels (RD-26 / ODI-CONTROLS)

A named source property or relation that generates a property resource MUST preserve its original name as `rdfs:label`, even if its IRI is disambiguated. This requirement does not create a separate output representation for derivation connectors covered by DK-REL-08 or DK-REL-18 or unsupported relation-valued endpoint connectors covered by DK-REL-17.

For every successfully transformed source-backed non-property resource whose source element has a name, DirectKG MUST emit an `rdfs:label` preserving that source name. This requirement applies under every IRI strategy, including when the resource IRI is derived from the same name. The label value MUST follow the established literal and language-handling rules, including DK-LBL-02 (RD-27 / ODI-CONTROLS).

Selecting one localized naming input under DK-IRI-10 MUST NOT discard other applicable source-authored labels under this rule and DK-LBL-02.

DirectKG MUST NOT treat the IRI local name as a substitute for the required label.

The general non-property-resource rule does not apply to property resources, whose label behavior is governed by their existing rules. It does not require labels to be invented for unnamed source elements. DK-IRI-04's fallback MUST preserve available source-authored labels under the existing rules, including text that cannot supply a usable IRI name; it MUST NOT invent a label for an unnamed element.

An unnamed class MUST NOT receive an invented label.

Every named source enumeration literal MUST preserve its source name as `rdfs:label`, as specified in DK-IRI-08. This requirement remains an explicit application of the general non-property-resource rule. DirectKG MUST NOT independently invent a label for an unnamed enumeration literal.

The generated ontology receives the nonempty top-level `Project.name` as its label under DK-GEN-08 (RD-05 / RD-27), with no invented fallback label or diagnostic solely for an absent, null, or empty project name.

#### Primary-relation label modes

The `--relation-labels {source-only,generated}` control in §15 governs labels on successfully generated primary relation properties. Its default MUST be `source-only`.

In both modes, DirectKG MUST select source terminology in this order:

1. Preserve the original relation name as `rdfs:label` when present.
2. Otherwise, preserve a usable target-end role name as `rdfs:label`.

Source-derived labels MUST preserve the original source wording rather than the normalized or disambiguated IRI form and MUST follow DK-LBL-02's language-resolution policy. The source-end role MUST NOT substitute for the target-end role when labeling the primary property.

If neither source label is available, the following behavior MUST apply:

| Mode | Primary-property label behavior |
|---|---|
| `source-only` | DirectKG MUST NOT generate a label. |
| `generated` | DirectKG MUST generate a fallback `rdfs:label` from the lexical naming candidate selected by the applicable name-based relation-naming rules in DK-REL-02–05. This includes established stereotype-derived naming, grounding-relator-derived naming where applicable, and endpoint synthesis, following their existing precedence and conditions. |

Supported localized inputs to the generated lexical naming candidate follow DK-IRI-10 under either IRI strategy. Generated fallback labels MUST be based on the selected lexical naming candidate before IRI-specific processing. DirectKG MUST NOT obtain them by parsing the final IRI or incorporate collision suffixes, collision qualification, IRI encoding, or other artifacts introduced solely for IRI construction.

Label selection MUST apply under both name-based and ID-based IRI strategies. An ID-based IRI MUST NOT cause the generated fallback label to be derived from that IRI instead of the lexical naming candidate. The existing relation-naming precedence and stereotype-naming control govern lexical fallback selection. Generated fallback labels remain outside automatic source-language propagation under DK-LBL-02, including the user language override. Relation IRI construction and existing naming diagnostics remain unchanged.

Generated inverse labels remain governed by [Section 11](#11-generated-inverse-properties); these modes do not change inverse-label rules.

**Rationale (non-normative):** The default preserves source terminology without inventing labels. The optional mode provides fallback labels for display while keeping them independent of the selected IRI strategy and IRI collision handling.

#### No RDF origin markers (RD-26, option A)

DirectKG MUST NOT add RDF markers, annotations, or auxiliary resources solely to distinguish primary-relation fallback labels from source-authored labels. The absence of an origin marker MUST NOT, by itself, introduce a diagnostic or configuration control. Existing label-generation, lexical-selection, and language rules remain unchanged, including the `source-only` default and behavior under both IRI strategies. Existing naming and other applicable diagnostics remain unchanged.

**Rationale (non-normative, RD-26, option A):** Keeps the generated graph lightweight. Consumers requiring source terminology can select `--relation-labels source-only`.


### DK-LBL-02 — Source descriptions and language resolution (RD-27 / ODI-CONTROLS)

#### Source descriptions

DirectKG MUST preserve nonempty supported source descriptions using `rdfs:comment`. The exported lexical content MUST be preserved without translation, summarization, or automatic removal of embedded markup. RDF serialization escaping MAY be applied without changing the lexical content.

Absent, null, or empty descriptions MUST generate no description annotation and no diagnostic solely because of that condition.

DirectKG MUST apply the following direct description mappings where the corresponding resource is successfully generated:

| Source description | Output target |
|---|---|
| Top-level `Project.description` | Generated ontology resource |
| Class | Corresponding generated local class resource |
| Enumeration literal | Corresponding generated enumeration-value individual |
| Attribute | Corresponding generated attribute property |
| Relation | Corresponding generated primary relation property |

These description mappings, including `Project.description`, MUST follow this section's lexical-preservation and language-resolution rules, including preservation of applicable localized values and the explicit user language override. Other applicable language and input diagnostics remain applicable.

**Rationale and example (non-normative, project descriptions):** Preserves supplied project documentation through the existing description predicate and language handling. The inspected VP-plugin 0.5.3 extraction path leaves this field empty, while its data structures and serializer can represent populated descriptions. For example, a supplied description `"A model of clinical studies."` is preserved as an `rdfs:comment` on the generated ontology, with language treatment determined by this section.

DirectKG MUST NOT create a resource solely to host a description or attach primitive-datatype descriptions to shared external datatype IRIs. An enclosing relation's description MUST NOT automatically be copied onto its generated inverse property.

For association ends, DirectKG MUST preserve a nonempty target-end description on the successfully generated primary relation property. The enclosing relation's description and the target-end description MUST be emitted independently as comments on that property, without concatenation.

DirectKG MUST preserve a nonempty source-end description on the corresponding generated named inverse property, when that inverse exists. DirectKG MUST NOT generate an inverse solely to preserve a description. When no named inverse is generated, the source-end description MUST be omitted without an additional diagnostic solely for that omission. Existing inverse-generation controls determine whether that named inverse is available.

All descriptions remain subject to the lexical-preservation and language-resolution rules in this section. Package descriptions are omitted under DK-GEN-06, and custom `propertyAssignments` are omitted under DK-GEN-07.

#### Recognized language carriers

DirectKG MUST recognize language information only from:

- the explicit user override supplied through `--language LANG` or its semantically equivalent Python control;
- explicit local language information in the `languageString` structures defined by `ontouml-schema` and implemented by `ontouml-js`; and
- the corresponding schema-defined project language field, `Project.languages`.

A `languageString` represents localized text through language-tag keys and their associated lexical values. Its empty key denotes unknown language and MUST NOT be treated as an explicit local language tag.

These carrier rules apply to textual fields supported by the transformation. They do not independently establish mappings for additional metadata fields. References to project/high-level language information in the language-resolution policy mean the recognized project language carrier specified here.

Custom `propertyAssignments` are recognized and omitted under DK-GEN-07. VP custom tagged values exported through `propertyAssignments` MUST NOT participate in language resolution, even when deliberately supplied to express language. Keys such as `language`, `lang`, `locale`, or similar custom fields MUST NOT be interpreted as language declarations. DirectKG MUST NOT define a VP tagged-value convention for language or infer language semantics heuristically from custom metadata field names.

#### Language-resolution precedence

For supported user-authored textual content originating from the source model, DirectKG MUST apply the following precedence:

| Priority | Condition | Required treatment |
|---|---|---|
| 1 | A user language override is supplied | Apply the override in preference to local and project/high-level language information. |
| 2 | No override; an explicit language is associated with the individual textual value | Preserve that local language. |
| 3 | No override or explicit local language; exactly one applicable project/high-level language is declared | Apply that language to the otherwise untagged value. |
| 4 | None of the above | Preserve an ordinary untagged RDF literal. |

This literal-language policy does not select or reorder naming candidates. Naming selection MUST use the original source language keys under DK-IRI-10, independently of the user language override and `Project.languages`.

DirectKG MUST NOT infer language from lexical content, locale, editor defaults, or similar heuristics.

Without a user language override, explicitly localized versions of the same textual value MUST be preserved independently with their respective language tags, wherever that source field is supported by the transformation. Multiple explicitly localized values MUST NOT be treated as ambiguous merely because they use different languages.

When multiple applicable project/high-level languages are declared, DirectKG MUST NOT arbitrarily select one for a value that has neither an explicit local language nor a user override. Such a value MUST remain untagged. DirectKG MUST emit the nonfatal WARNING specified in DK-DIAG-19. Explicitly localized values and values covered by a user override do not trigger this ambiguity warning.

#### Scope and supported-input boundary

This language-resolution policy MUST apply to supported source-authored textual content, including class, relation, property/end, enumeration-literal, project, and similar names; source descriptions; user-supplied role names; and other supported source-authored textual annotations. This list establishes language treatment where a mapping is supported; it does not create additional mappings.

The policy MUST NOT automatically apply to transformation-generated or built-in text, including OntoUML stereotype names, DirectKG explanatory comments (including the `begin` and `end` boundary-stereotype comments under DK-PROP-06), diagnostic messages, vocabulary terms, fixed modeling-tool text, or generated fallback labels. Existing rules explicitly requiring English generated comments remain unchanged. Generated fallback labels under RD-26 remain outside automatic source-language propagation, including the user language override.

For supported VP-plugin 0.5.3 JSON strings without explicit language information, DirectKG MUST leave the text untagged unless a user override or exactly one applicable declared project/high-level language supplies its language. The exporter's internal English default MUST NOT be treated as evidence that source text is English.

These rules apply within the supported input contract, including the bounded language enrichment expressly established in §3.2 (RD-27 / RD-01). The multilingual and project/high-level language provisions use the supported `languageString` representation and top-level `Project.languages` field; they MUST NOT broaden the input contract beyond that extension. DirectKG MUST NOT introduce package-local language declarations unless separately established by the supported input contract. Recognition of these language carriers does not authorize general support for unrelated schema constructs or arbitrary `ontouml-js` output structures. RD-28 source-ID annotations under DK-IRI-09 MUST remain untagged and are not subject to this language policy, including the user override. External YAML text under DK-GEN-09 MUST remain untagged; neither the user override nor `Project.languages` propagates to it. The language override control is specified in §15.

**Rationale and example (non-normative):** Explicit language information can be preserved without guessing the language of plain strings. Without an override, localized names such as `"en": "Person"` and `"pt-BR": "Pessoa"` produce separate labels `"Person"@en` and `"Pessoa"@pt-BR`.

## 10. Primary binary-relation transformation

### DK-REL-01 — Eligible ordinary relation

A supported binary relation with two resolved classifier endpoints that is transformed as a primary relation MUST become an IRI-identified `owl:ObjectProperty` with explicit source domain and target range. Explicit relation-to-relation generalizations use these primary properties under DK-REL-14 (RD-12), and relation generalization-set disjointness uses them under DK-REL-15 (RD-13).

Relation descriptions and target-end descriptions MUST be preserved independently on the successfully generated primary property under DK-LBL-02. Source-end descriptions follow its named-inverse placement rule.

Explicitly supplied, recognized `begin` or `end` property stereotypes on either association end follow DK-PROP-06 (RD-18): comments identify the source or target end on the successfully generated primary relation property, independently of named-inverse generation.

For covered ordinary mereological relations, DK-REL-19 (RD-17 / RD-25) additionally maps that primary property beneath an imported generic `dkgm` property and declares the primary property asymmetric. Association-end `isReadOnly` and aggregation comments follow DK-PROP-04 (RD-24 / RD-25). Association-end `isOrdered: true` comments follow DK-PROP-05 (RD-23), including per-occurrence INFO reporting under DK-DIAG-18. Explicit boolean relation `isAbstract` values MUST be preserved as `rdfs:comment` on the generated primary property under DK-CLS-01 (RD-19), with the INFO reporting required by DK-DIAG-15; they MUST NOT, by themselves, introduce additional logical constraints or change the existing relation and generalization-set mappings. These rules do not change the source-backed property identity, direction, domain, range, inverses, or cardinality mappings.

A binary relation whose endpoint `propertyType` resolves to a source `Relation` does not undergo ordinary primary-property generation; its mapping or intentional omission is specified in DK-REL-08, DK-REL-18, and DK-REL-17. This does not change ordinary relations with eligible class endpoints, including the material and comparative relations connected by recognized derivations.

Property selection for reverse-side cardinality restrictions is established in DK-REL-09 (RD-11). DK-REL-10 (RD-11) establishes unqualified cardinality forms for supported ordinary binary class-to-class relations. DK-REL-11 (RD-11) establishes direction, necessary-condition representation, and finite numeric multiplicity mapping. DK-REL-12 (RD-11) establishes unbounded relation-end multiplicity mapping. Explicit null cardinalities are specified in DK-REL-13. Missing `cardinality` fields use the fallback in DK-DIAG-09 (RD-11 / RD-02). Untranslatable multiplicities and bounds follow DK-DIAG-10, including partial recovery of independently valid numeric bounds in `best-effort`. Contradictory numeric intervals are transformable under §3.4 (RD-11). Cardinality syntax, limited lexical normalization, and treatment of ambiguous malformed expressions are specified in DK-DIAG-11 (RD-11 / RD-02).

#### Ordinary mapping of `historicalDependence` with the applicable limitation warning (RD-17, Alternative A)

Eligible ordinary relations carrying the recognized `historicalDependence` stereotype MUST retain their existing ordinary relation mappings, including property identity, direction, naming, labels, descriptions, domains, ranges, inverses, cardinalities, and applicable generalization mappings.

DirectKG MUST NOT introduce additional logical axioms or stereotype-preservation annotations solely because a relation carries `historicalDependence`.

This omission concerns additional annotations recording the stereotype declaration. Existing source-description mappings, independently required annotations, and lexical naming and labeling rules MUST remain applicable. In particular, stereotype-derived naming under DK-REL-04 and any corresponding generated fallback label under DK-LBL-01 remain unchanged. DK-LBL-02's source-description and language rules remain applicable.

Existing applicable diagnostics MUST remain applicable, including the limitation warning governed by DK-DIAG-01's deliberately unmapped applicable relation-stereotype condition. This mapping establishes no warning-suppression exception.

Documentation MUST explain that historical-dependence semantics are only partially translated through the existing ordinary mapping, with no additional axiomatization supplied solely by this stereotype.

DK-GEN-11's general metadata permission does not override the omission of additional annotations solely recording this stereotype declaration.

#### Additional relation property characteristics (RD-17)

For each eligible ordinary relation successfully mapped to a primary `owl:ObjectProperty`, DirectKG MUST emit the following additional declaration when the per-axiom compatibility conditions below are satisfied:

| Recognized relation stereotype | Declaration on the primary property |
|---|---|
| `characterization` | `rdf:type owl:AsymmetricProperty` |
| `mediation` | `rdf:type owl:AsymmetricProperty` |
| `participational` | `rdf:type owl:AsymmetricProperty` |
| `externalDependence` | `rdf:type owl:IrreflexiveProperty` |

Each declaration MUST preserve the primary property's actual direction.

#### Characterization–external-dependence disjointness (RD-17)

DirectKG MUST pair every successfully mapped `characterization` relation with every successfully mapped `externalDependence` relation whose feature endpoint resolves to the same source class in the feature role of both relations.

Matching MUST use exact source-class identifiers. It MUST NOT discover additional pairs through inheritance or names. Pairing MUST NOT require a material relation, a derivation connector, or a generated property chain. Multiple matching characterizations or external-dependence relations MUST produce all eligible pairs rather than disqualifying the pattern.

Where the feature endpoint cannot be identified unambiguously, DirectKG MUST omit the affected new disjointness axiom without changing the ordinary mappings.

For every eligible pair, DirectKG MUST select expressions directed from the feature toward its bearer and external dependency, respectively. For each participating primary property, selection MUST follow:

| Required direction relative to the primary property | Selected property expression |
|---|---|
| Primary direction already follows the required direction | The primary property |
| Reversal is required and the corresponding named inverse is generated | That named inverse property |
| Reversal is required and no corresponding named inverse is generated | An anonymous `ObjectInverseOf(primary)` expression |

DirectKG MUST emit pairwise property disjointness between the aligned expressions using `owl:propertyDisjointWith` when the per-axiom compatibility conditions below are satisfied. This selection MUST preserve each primary property's direction and MUST NOT force named-inverse generation or change the selected inverse-generation mode. DK-INV-01 and DK-INV-04 permit the anonymous inverse expressions needed by this mapping; selection rules for other mappings remain unchanged.

**Rationale and example (non-normative):** The aligned disjointness axiom prevents the same feature–individual pair from representing both characterization and external dependence: a feature cannot externally depend on its own bearer through the paired properties.

If `isCharacterizedBy` points from bearer to feature, no named inverse is generated, and `externallyDependsOn` already points from feature to dependency, compatible output can use:

```turtle
[ owl:inverseOf :isCharacterizedBy ]
    owl:propertyDisjointWith :externallyDependsOn .
```

This preserves both primary directions without introducing a named inverse.

#### Per-axiom OWL 2 DL compatibility for the five additions (RD-17)

Each new axiom specified above MUST be assessed separately against the applicable OWL 2 DL restrictions, considering the generated property hierarchy, inverse relationships, and import closure, including the mandatory vocabulary import under DK-GEN-04.

| Proposed new axiom | Required simplicity condition |
|---|---|
| Asymmetry declaration | Its property expression is simple. |
| Irreflexivity declaration | Its property expression is simple. |
| Property-disjointness axiom | Both participating property expressions are simple. |

A property used only in a property-chain body MUST NOT be treated as non-simple solely because of that use. If a proposed axiom fails its applicable simplicity condition, DirectKG MUST omit that new axiom. Other compatible additions remain applicable.

These conditions MUST apply in every material-property-chain mode: `none`, `omit-conflicting-constraints`, and `preserve-conflicting-constraints`. Material-chain generation alone MUST NOT suppress the additions. In particular, DK-REL-07's preservation mode MUST NOT override this compatibility gate.

The test concerns whether the proposed addition introduces an additional violation; it does not require the existing ontology to satisfy an overall OWL 2 DL guarantee. Existing mappings and their established omission/preservation policies MUST remain unchanged, including relation-generalization-set disjointness under DK-REL-15, source-specific mereology under DK-REL-19, and the imported vocabulary under DK-GEN-04. DirectKG MUST NOT remove other accepted axioms to accommodate these additions.

This rule is limited to the four property-characteristic mappings and the paired-disjointness mapping above. It establishes neither an overall OWL 2 DL guarantee nor new semantic validation, consistency checking, or source-model repair.

**Accepted dependencies and cross-references:** DK-REL-09 and DK-PROP-03 provide the existing primary/named-inverse/anonymous-inverse selection approach extended here. DK-GEN-04 establishes the mandatory imported vocabulary relevant to the compatibility assessment. OWL 2 property simplicity and global restrictions are defined in [*OWL 2 Web Ontology Language: Structural Specification and Functional-Style Syntax, Second Edition*, W3C Recommendation, 11 December 2012, §§11.1–11.2](https://www.w3.org/TR/2012/REC-owl2-syntax-20121211/).

### DK-REL-02 — Forward name precedence

Under the name strategy, with stereotype-derived naming enabled, the direct property's candidate is selected in this order:

1. usable relation name;
2. usable target-end role name;
3. an established stereotype-derived semantic name;
4. synthesized `<source>_<target>`;
5. deterministic collision resolution.

Supported localized relation names and target-end role names follow DK-IRI-10. Its selected original text feeds the applicable naming rule without changing this field precedence.

The source-end role MUST NOT name the forward property. Generic prefixes such as `has`, `relatedTo`, or `isRelatedTo` MUST NOT be invented unless present in the source or an adopted stereotype mapping.

Stereotype-derived naming is enabled by default and MAY be disabled with:

```text
--no-stereotype-relation-naming
```

When disabled, step 3 is skipped.

DK-LBL-01 uses the selected lexical naming candidate for generated fallback labels under either IRI strategy. This label use follows the existing naming precedence and conditions in DK-REL-02–05 but excludes deterministic collision resolution and all other IRI-only processing; it does not change relation IRI construction or naming diagnostics.

### DK-REL-03 — Synthesized endpoint name

The source-target fallback is:

```text
lowerFirst(normalize(source.name)) + "_" + lowerFirst(normalize(target.name))
```

For supported localized endpoint names, DK-IRI-10 selects each original source text before normalization.

`lowerFirst` changes only the first character. It MUST NOT lowercase the entire classifier name. Unnamed endpoints first receive their synthetic identifiers, which MAY then supply fallback components.

### DK-REL-04 — Stereotype-derived names

When the semantic naming step is reached, the following direction-specific candidates are established:

| Stereotype | Direction | Candidate |
|---|---|---|
| `bringsAbout` | Event → Situation | `bringsAbout` |
| `bringsAbout` | Situation → Event | `broughtAboutBy` |
| `characterization` | Bearer → Feature | `isCharacterizedBy` |
| `characterization` | Feature → Bearer | `characterizes` |
| `componentOf` | Whole → Component | `hasComponent` |
| `componentOf` | Component → Whole | `componentOf` |
| `creation` | Event → Endurant | `creates` |
| `creation` | Endurant → Event | `wasCreatedIn` |
| `externalDependence` | Extrinsic Mode → Endurant | `externallyDependsOn` |
| `externalDependence` | Endurant → Extrinsic Mode | `isExternalDependencyOf` |
| `historicalDependence` | Dependent → Antecedent | `historicallyDependsOn` |
| `historicalDependence` | Antecedent → Dependent | `isHistoricalDependencyOf` |
| `manifestation` | Aspect/Disposition → Event | `manifestedIn` |
| `manifestation` | Event → Aspect/Disposition | `manifests` |
| `mediation` | Relator → Endurant | `mediates` |
| `mediation` | Endurant → Relator | `isMediatedBy` |
| `memberOf` | Member → Collective | `memberOf` |
| `memberOf` | Collective → Member | `hasMember` |
| `participation` | Participant → Event | `participatesIn` |
| `participation` | Event → Participant | `hasParticipant` |
| `participational` | Part Event → Whole Event | `participationalPartOf` |
| `participational` | Whole Event → Part Event | `hasParticipationalPart` |
| `subCollectionOf` | Subcollection → Collection | `subCollectionOf` |
| `subCollectionOf` | Collection → Subcollection | `hasSubCollection` |
| `subQuantityOf` | Subquantity → Quantity | `subQuantityOf` |
| `subQuantityOf` | Quantity → Subquantity | `hasSubQuantity` |
| `termination` | Endurant → Event | `wasTerminatedIn` |
| `termination` | Event → Endurant | `terminates` |
| `triggers` | Situation → Event | `triggers` |
| `triggers` | Event → Situation | `triggeredBy` |

Successful ordinary stereotype-derived naming produces no warning or information message solely for that successful naming. Other applicable diagnostics retain their established conditions.

For `historicalDependence`, the direction-specific naming candidates above and any corresponding generated fallback label under DK-LBL-01 remain applicable. DK-REL-01's historical-dependence boundary retains the applicable limitation warning under DK-DIAG-01; successful naming establishes no warning-suppression exception.

`comparative` has no generic semantic name because the required predicate is domain-specific. If its semantic naming step is reached, DirectKG MUST warn and continue to the source-target fallback.

`derivation` has no generic property-name mapping. Recognized material–relator and material–mode derivations under DK-REL-08 and comparative–quality derivations under DK-REL-18 do not undergo ordinary primary-property generation or lexical naming fallback. Other resolved binary relations with relation-valued endpoints are governed by DK-REL-17 (RD-16).

### DK-REL-05 — Material relation naming

An unnamed `«material»` relation with no usable target-end role MUST NOT receive a fixed predicate such as `materiallyRelatedTo`. At the stereotype-derived naming step, DirectKG MUST attempt to resolve its grounding `«relator»` through an OntoUML `«derivation»`.

When a usable grounding relator name exists, the candidate is:

```text
lowerFirst(normalize(relator.name))
```

For a supported localized relator name, DK-IRI-10 selects the original text used in this construction. No `has` prefix is added. The property continues to connect the material relation's source and target; it does not point to a relator individual. Successful relator-based naming SHOULD produce an informational provenance diagnostic and MUST NOT produce a warning merely because this naming path succeeded.

If no usable grounding relator can be resolved, DirectKG MUST warn and continue to the source-target fallback. The initial diagnostics need not distinguish absence, ambiguity, an unnamed target, or an unusable target; all MAY be reported as an unavailable grounding relator.

The use of the derivation connector as transformation-time information without separate output is specified in DK-REL-08 (RD-16). Recognition of the supported material–relator pattern is independent of the derivation's serialized endpoint order.

This section establishes naming only. It introduces no special name for mode-grounded material relations; the established name-precedence and fallback rules remain applicable. Optional material-property-chain semantics are specified in DK-REL-07 (RD-17), with chain-direction representation completed by the accepted DK-INV-04 clarification. This specification defines no material semantics beyond that accepted scope.

### DK-REL-06 — Relation naming diagnostics

An unnamed relation using a target-role or source-target fallback MUST produce a non-fatal warning, except where a later stereotype-specific rule replaces it. A deliberately unmapped `comparative` reaching semantic naming MUST warn before lexical fallback. Derivations covered by DK-REL-08 and DK-REL-18 and unsupported relation-valued endpoint connectors covered by DK-REL-17 do not invoke generic lexical naming fallbacks; DK-REL-18 requires its unsupported-semantics diagnostic and DK-REL-17 requires its nonfatal limitation warning for unsupported resolved patterns. Diagnostics for material-relation naming, property-chain ambiguity, and malformed or unresolved source data remain applicable under their respective conditions.

When both an endpoint class and its relation are unnamed, separate diagnostics SHOULD identify the two conditions unless a later stereotype-specific rule replaces the generic relation warning.

DirectKG currently assumes valid relation orientation and does not need a defensive semantic-orientation recovery branch.

### DK-REL-07 — Material-property-chain modes and construction (RD-17 / ODI-CONTROLS)

An `isDerived` flag alone does not establish a material-property chain; DK-GEN-05 (RD-20) governs its annotation preservation independently of the explicit derivation mappings in this rule, DK-REL-08, and DK-REL-18.

Material-property-chain generation is controlled by the three-mode `--material-property-chains` parameter in §15, with default `none`. The chain-generating modes are `omit-conflicting-constraints` and `preserve-conflicting-constraints`. Both govern the accepted material–relator and material–mode patterns below. The parameter does not govern the imported `dkgm` vocabulary, its generic chains, or source-specific mereological mappings.

The four additional property-characteristic mappings and characterization–external-dependence disjointness under DK-REL-01 (RD-17) have their own per-axiom compatibility gate in every mode. `preserve-conflicting-constraints` MUST NOT override that gate. The policies below retain their established treatment of existing cardinality and relation-generalization-set disjointness mappings; DirectKG MUST NOT remove other accepted axioms to accommodate the additions.

#### Mode-specific constraint treatment

The selected mode changes only whether eligible material-property chains are generated and how simplicity-dependent constraints affected by generated chains are treated. Existing pattern eligibility, completeness, ambiguity handling, direction, primary-property and anonymous-inverse construction, and independently applicable source-element mappings continue to apply, subject to the targeted omission rule below.

Under `none`, DirectKG MUST NOT generate material–relator or material–mode property-chain axioms. All independently applicable mappings, including cardinality restrictions and property-disjointness axioms, MUST remain applicable. DirectKG MUST NOT emit DK-DIAG-07 solely because material-property-chain generation is disabled.

Under either chain-generating mode, DirectKG MUST generate every eligible, unambiguous material–relator and material–mode property chain required by this rule.

Under `omit-conflicting-constraints`, DirectKG MUST first determine which material chains are actually emitted. It MUST then determine the object-property expressions made non-simple by those emitted chains under the generated OWL property hierarchy. Affected expressions include, as applicable:

- each property used as the conclusion of an emitted material-property chain;
- its anonymous inverse expression;
- a corresponding generated named inverse; and
- generated superproperties that become non-simple because a non-simple property occurs beneath them in the generated property hierarchy.

This propagation includes applicable accepted subproperty and inverse mappings, including relation specialization (RD-12), the primary and named-inverse singleton-completeness axioms in DK-REL-20 (RD-13), and UML `subsets` or `redefines` mappings (DK-PROP-03). The added singleton-completeness hierarchy axioms are not themselves subject to the targeted omission of cardinality restrictions and property-disjointness axioms. A property used only as a member of a property-chain body MUST NOT be considered non-simple solely because of that participation.

For the affected non-simple property expressions, DirectKG MUST omit:

1. every multiplicity-derived cardinality restriction whose `owl:onProperty` would use an affected property expression, including restrictions expressed through primary properties, named inverses, or anonymous inverse expressions; and
2. every generated property-disjointness axiom in which at least one participating property expression is affected.

For pairwise property-disjointness output, only the affected pairwise axiom MUST be omitted. Unrelated disjointness pairs MUST remain applicable. Constraints MUST NOT be omitted merely because a source relation is material or participates in a candidate grounding pattern. Omission applies only when an eligible property chain is actually emitted and the relevant property expression consequently becomes non-simple. All unrelated cardinality restrictions, property-disjointness axioms, and other independently applicable mappings MUST remain applicable.

This omission rule qualifies the otherwise applicable multiplicity mappings, including DK-ATT-03 and DK-REL-09–13, and generated property-disjointness mappings under DK-REL-15. It removes the known simplicity conflicts introduced by emitted material-property chains within DirectKG's accepted cardinality and property-disjointness mappings. It MUST NOT be described as guaranteeing that the complete generated ontology conforms to OWL 2 DL.

Under `preserve-conflicting-constraints`, DirectKG MUST preserve all independently applicable cardinality restrictions and relation-generalization-set property-disjointness axioms under DK-REL-15, including those involving property expressions made non-simple by emitted chains. This may cause the generated ontology to fall outside OWL 2 DL. This mode MUST NOT be described as preserving all OntoUML semantics or guaranteeing complete source-model preservation: it preserves those established cardinality and property-disjointness mappings. The additional axioms under DK-REL-01 remain subject to their own per-axiom compatibility gate.

Either chain-generating mode requires the nonfatal compatibility notice in DK-DIAG-07 whenever at least one material-property chain is emitted, even when no cardinality or property-disjointness axiom ultimately conflicts.

**Rationale and examples (non-normative):** OWL 2 DL requires simple object properties in cardinality restrictions and property-disjointness axioms. If an emitted chain concludes in material property `M`, cardinality restrictions using `M` or its inverse are simplicity-dependent. If `M` is also a subproperty of `P`, `P` may likewise become non-simple, so applicable cardinality or property-disjointness axioms using `P` must also be considered by the omission mode. Mediation, characterization, or external-dependence properties used only inside a chain body do not become non-simple solely from that participation.

#### Material–relator chains

Under either chain-generating mode, generation MUST be restricted to the following supported pattern:

- A `«material»` relation connects two distinct non-relator classes, A and C.
- An explicit `«derivation»` connects that material relation to its grounding `«relator»` class R.
- Exactly one `«mediation»` relation connects R to A.
- Exactly one distinct `«mediation»` relation connects R to C.

Participant classes and mediation endpoints MUST be matched directly by source-model class identifiers. Matching MUST NOT search through class inheritance or infer correspondence from names or JSON ordering. Same-class material–relator relations follow the shared ambiguity rule below.

The grounding material–relator derivation MUST be recognized in either serialized endpoint order under DK-REL-08 (RD-16); its endpoint order has no effect on this pattern's chain eligibility.

Mediation uniqueness MUST be evaluated separately for each participant class against the same grounding relator. Additional mediations from that relator to classes other than the material relation's two endpoints MUST NOT disqualify the pattern.

The generated OWL property-chain axiom MUST express the directed composition from the material relation's source participant, through the grounding relator, to its target participant, with the material property as the chain's conclusion. Mediation orientation MUST be accounted for when determining the required property directions.

Under the accepted DK-INV-04 clarification, for each mediation step in a generated material-property chain:

- A step following the primary mediation property's direction MUST use that primary property directly.
- A step traversing the primary mediation property backwards MUST use an anonymous inverse expression of that primary property.

This chain representation MUST apply regardless of the selected inverse-generation mode and regardless of whether a corresponding named inverse property is also generated. A named inverse MUST NOT replace the anonymous inverse expression in a backward chain step.

Generating a material-property chain MUST NOT cause DirectKG to generate a named inverse property that the selected inverse-generation mode would otherwise omit.

Chains outside the supported pattern MUST be omitted. When multiple matching mediations on either participant side prevent unique correspondence, DirectKG MUST omit the affected chain and issue a warning identifying the material relation and the ambiguity. Both sides need not be ambiguous. This ambiguity alone MUST NOT abort conversion under any input policy. Unrelated structural failures remain governed by their applicable rules.

Omitting a chain MUST NOT itself suppress classes, material properties, mediation properties, or other output otherwise prescribed by accepted mappings. Mode-specific omission remains determined by chains actually emitted and their propagated effects, as specified above.

Cardinality restrictions, including those under DK-REL-11 (RD-11), and property-disjointness axioms under DK-REL-15 (RD-13) MUST follow the mode-specific constraint treatment above. Under `preserve-conflicting-constraints`, emitting chains MUST NOT recalculate, weaken, or omit those independently applicable constraints; under `omit-conflicting-constraints`, only the specified affected constraints MUST be omitted.

Existing relation identity, naming, domain, range, and inverse-generation rules continue to govern the ordinary generated properties. Emitting at least one material-property chain requires the compatibility notice specified in DK-DIAG-07. RD-17 does not establish the complete relation-multiplicity mapping. The absence of a separate representation for its material–relator derivation connector is established by DK-REL-08 (RD-16).

**Non-normative rationale and example:** For a material relation from Person to Organization grounded in Employment, one mediation from Employment to Person and one to Organization uniquely identify the chain components. An additional mediation to EmploymentAgency does not affect that correspondence. Two mediations to Person make the correspondence ambiguous even if only one mediation connects Employment to Organization.

**Non-normative rationale for chain representation:** An anonymous inverse expression means “use this property backwards” without introducing a separately named inverse property. Using this representation consistently keeps chain construction independent of named inverse-generation settings.

#### Mode-grounded material chains with distinct endpoint classes (RD-17)

For an explicit material–mode derivation recognized under DK-REL-08, when either chain-generating mode is selected and the material relation `M` has two endpoint classes with distinct source identifiers, DirectKG MUST generate a property-chain axiom concluding in `M`'s primary property when exactly one explicit `«characterization»` connects the grounding `«mode»` class `Q` to one endpoint class, exactly one explicit `«externalDependence»` connects `Q` to the other endpoint class, and the complete pattern resolves directly by source element identifiers. Pattern matching MUST NOT use names, inheritance, or diagram or serialization order.

The chain MUST follow a path from the source of `M`'s primary property to its target. Each participating ordinary property MUST be used directly when its primary direction matches the required path step; otherwise that step MUST use an anonymous inverse expression of the primary property. A generated named inverse MUST NOT replace that anonymous expression. Chain generation MUST NOT force named inverse-property generation, regardless of the selected inverse-generation mode.

Additional `«characterization»` or `«externalDependence»` relations involving classes outside the candidate pattern MUST NOT disqualify an otherwise unique pattern. Under either chain-generating mode, if multiple matching relations or complete matching patterns make the chain ambiguous, DirectKG MUST omit the affected chain and issue a nonfatal chain-ambiguity diagnostic identifying `M` and the ambiguity. If no complete direct pattern exists, DirectKG MUST generate no chain. Other applicable structural diagnostics remain governed by their existing rules.

When `--material-property-chains none` is selected, DirectKG MUST NOT generate this chain. The material relation, grounding mode, participant classes, and participating ordinary relations retain their independently applicable transformations whether or not a chain is generated. Cardinality restrictions and property-disjointness axioms MUST follow the mode-specific constraint treatment above. Every emitted mode-grounded material chain requires the compatibility notice in DK-DIAG-07.

#### Same-class material relations grounded in a relator or mode (RD-17)

A same-class material relation is a `«material»` relation whose source and target association ends resolve to the same source classifier identifier. Its ends may be distinct UML Properties with different identifiers, names, roles, or multiplicities. Sharing a classifier identifier does not assert that the two relata are the same individual.

For a material–relator or material–mode derivation recognized under DK-REL-08, same-class endpoints do not uniquely associate the source and target occurrences of the material relation with the semantic roles of the grounding relations. In a material–relator derivation, the mediation paths cannot be uniquely assigned to the two material occurrences. In a material–mode derivation, `«characterization»` and `«externalDependence»` distinguish bearer and external-dependence roles but do not establish which occurrence is the material property's source or target.

When either chain-generating mode is selected, DirectKG MUST omit the material-property-chain axiom for either same-class grounding pattern and emit a nonfatal chain-ambiguity diagnostic identifying the affected material relation and explaining that its same-class endpoints cannot be assigned uniquely to the grounding relations' semantic roles. The diagnostic MUST remain nonfatal under every input policy, including `strict`. For a mode-grounded relation, DirectKG MUST omit both the characterization-first and external-dependence-first candidate chains; it MUST NOT generate either as a substitute.

DirectKG MUST NOT resolve this ambiguity by selecting an ordering arbitrarily, generating both candidate chains, or using class or relation names, association-end or role names, the identifiers of the material relation's distinct end Properties, diagram order, or JSON or other serialization order as a correspondence mechanism.

When `--material-property-chains none` is selected, DirectKG MUST NOT warn solely because a grounded material relation has same-class endpoints. Omission of the same-class chain MUST NOT itself suppress or modify independently applicable transformations of the material relation, either association-end Property, grounding relator or mode, mediation, characterization, or external-dependence relation, or their domains, ranges, inverses, cardinality restrictions, naming, or other accepted mappings. The derivation connector remains a recognized transformation-time construct under DK-REL-08 and MUST NOT receive DK-REL-17's generic unsupported-connector warning on account of the same-class ambiguity. The compatibility notice under DK-DIAG-07 applies when at least one chain is actually emitted.

### DK-REL-08 — Transformation-time use of material derivations (RD-16 / RD-17)

For an explicit `«derivation»` connecting a `«material»` relation to its grounding `«relator»` class, DirectKG MUST inspect both resolved endpoints and identify which endpoint resolves to the `«material»` source relation and which resolves to the `«relator»` source class. It MUST apply this mapping regardless of whether the serialized order is material-relation end followed by relator-class end or the reverse. Both orders are valid representations of this supported pattern. Recognizing either order MUST NOT be characterized as reversing, repairing, normalizing, or reinterpreting the source model, and MUST NOT produce a warning or error solely because of endpoint order.

DirectKG MUST use the recognized connector as transformation-time information for the accepted material-relation naming and optional property-chain mappings, subject to those mappings' conditions and configuration.

DirectKG MUST NOT generate a separate resource, ordinary object property, inverse property, or grounding annotation representing that derivation connector. Covered derivation connectors do not undergo ordinary primary-property or inverse-property generation. Their lack of such output does not invoke generic lexical naming fallbacks or warnings merely for being intentionally unrepresented. The diagnostic requirements are specified in DK-DIAG-08.

For an explicit `«derivation»` whose resolved endpoints are a `«material»` relation `M` and a `«mode»` class `Q`, DirectKG MUST recognize the pattern independently of their serialized endpoint order. DirectKG MUST use this derivation connector only as transformation-time information and MUST NOT generate a separate resource, ordinary or inverse property, or grounding annotation for it. Its intentional lack of separate output and either valid serialized order MUST NOT, by themselves, generate a warning or error. This supported connector MUST NOT receive DK-REL-17's generic unsupported-pattern warning, including when no mode-grounded property chain is generated.

The ordinary identity, naming, inverse, domain, range, and cardinality mappings for the material relation and participating relations remain applicable, subject to DK-REL-07's mode-specific constraint treatment. This decision introduces no special naming convention for mode-grounded material relations. Optional mode-grounded chain generation follows DK-REL-07. DK-REL-05's relator-derived naming path remains unchanged. The material–relator derivation rules above retain their existing behavior.

Other resolved binary relations with relation-valued endpoints follow DK-REL-18 (RD-17) for comparative–quality derivations or DK-REL-17 (RD-16) where no accepted mapping applies.

#### Derivation-multiplicity documentation requirements for material–relator derivations

DirectKG's documentation MUST explain the current derivation-multiplicity limitation:

- Derivation multiplicities can express meaningful OntoUML constraints.
- The inspected `ontouml-vp-plugin` 0.5.3 association-class export path creates derivation ends with default cardinality `"1"` rather than extracting independently specified connector-end multiplicities.
- Consequently, these exported values are not reliable evidence of the original author's intended derivation multiplicities.
- The current DirectKG mapping does not preserve those derivation-multiplicity constraints.

The documentation MUST state the future support objective: if the export tool gains reliable support for preserving author-specified derivation multiplicities, support for those multiplicities SHOULD be added to future DirectKG versions that support the corresponding exporter version. This specification does not define those future transformation semantics or their output representation; the support objective does not select them or automatically change the current mapping.

**Non-normative rationale and examples:**

The output remains focused on domain classes and properties. A derivation connecting Employment to worksFor can inform the accepted naming and chain mappings without becoming another output property or resource.

When no chain is generated, this decision provides no separate explicit grounding link. A relator-derived property name does not formally encode grounding.

**Non-normative evidence supplied with RD-16:** Catalog evidence corroborates the exporter limitation: in `guizzardi2005ontological`, the original diagram shows derivation multiplicities `1..2` and `1..*` at the material-relation ends of the Registration–parentOf and Recording–records derivations, respectively. Both corresponding JSON values are `"1"` in catalog commit `8ea0398cc273a49d9ea28aa534b1bb0316c6687c`.

This limitation supports the current transformation scope; it does not establish that derivation multiplicities lack meaning or should remain unsupported permanently.

### DK-REL-09 — Property selection for reverse-side cardinality restrictions (RD-11)

The ordinary cardinality mappings in DK-REL-09–13 are subject to DK-REL-07's mode-specific omission rule. Property selection determines the expression whose affected status is assessed; it does not exempt primary properties, named inverses, or anonymous inverse expressions from that rule.

When expressing a reverse-side cardinality restriction for a supported ordinary binary relation, DirectKG MUST use the corresponding named inverse property if that property is generated.

Otherwise, DirectKG MUST use an anonymous inverse expression of the primary relation property.

DirectKG MUST NOT force generation of a named inverse property merely to express the restriction. The established inverse-generation modes in DK-INV-01 determine whether a corresponding named inverse is generated.

No additional configuration argument is introduced to omit reverse-side cardinality restrictions when no named inverse property is generated.

This rule extends the accepted permission in DK-INV-04 for anonymous inverse expressions to reverse-side relation-cardinality restrictions. The existing material-property-chain representation in DK-REL-07 remains unchanged: backward chain steps continue to use anonymous inverse expressions even when named inverses exist.

This rule specifies property selection when expressing such a restriction. DK-REL-10 specifies the unqualified forms, and DK-REL-11 specifies direction, necessary-condition representation, and finite numeric multiplicity mapping. DK-REL-12 specifies unbounded multiplicities, and DK-REL-13 specifies explicit null cardinalities; DK-DIAG-09 specifies the missing-field fallback. Untranslatable multiplicities and bounds follow DK-DIAG-10. Contradictory numeric intervals are transformable under §3.4 (RD-11). Cardinality syntax, limited lexical normalization, and treatment of ambiguous malformed expressions are specified in DK-DIAG-11 (RD-11 / RD-02).

### DK-REL-10 — Unqualified relation-cardinality restrictions (RD-11)

For supported ordinary binary class-to-class relations, generated minimum, maximum, and exact cardinality restrictions MUST use the following unqualified OWL forms:

| Restriction | OWL form |
|---|---|
| Minimum | `owl:minCardinality` |
| Maximum | `owl:maxCardinality` |
| Exact | `owl:cardinality` |

This rule applies in both directions, including restrictions expressed through named inverse properties or anonymous inverse expressions. Reverse-side property selection MUST follow DK-REL-09 (RD-11).

No configuration argument is introduced for choosing qualified restrictions.

DK-GEN-03 supplies the endpoint domain and range declarations. This rule does not change attribute mappings. Direction, necessary-condition representation, and finite numeric multiplicity mapping are specified in DK-REL-11. Unbounded multiplicities are specified in DK-REL-12, and explicit null cardinalities in DK-REL-13; DK-DIAG-09 specifies the missing-field fallback. Untranslatable multiplicities and bounds follow DK-DIAG-10. Contradictory numeric intervals are transformable under §3.4 (RD-11). Cardinality syntax, limited lexical normalization, and treatment of ambiguous malformed expressions are specified in DK-DIAG-11 (RD-11 / RD-02).

**Rationale (non-normative):** With the accepted endpoint domain and range axioms, unqualified cardinalities express the same constraints as cardinalities qualified by the corresponding endpoint classes. The unqualified representation avoids repeating those classes inside each restriction.

### DK-REL-11 — Direction and finite numeric relation-cardinality mapping (RD-11)

For a supported ordinary binary class-to-class relation:

- The target-end multiplicity MUST constrain instances of the source class through the primary relation property.
- The source-end multiplicity MUST constrain instances of the target class through the inverse direction.

These constraints MUST be expressed as necessary conditions using `rdfs:subClassOf` restrictions, not as class definitions using `owl:equivalentClass`.

Finite numeric multiplicities MUST be mapped as follows, where the bounds are nonnegative integers, including contradictory intervals under §3.4 (RD-11):

| Multiplicity | Required output |
|---|---|
| `n` or `n..n`, including zero | One exact-cardinality restriction with value `n` |
| `0..u`, where `u > 0` | One maximum-cardinality restriction with value `u`; no minimum-cardinality restriction |
| `l..u`, where `0 < l < u` | Separate minimum-cardinality and maximum-cardinality restrictions with values `l` and `u` |
| `l..u`, where `l > u` | Separate minimum-cardinality and maximum-cardinality restrictions with values `l` and `u`, under every input policy; no warning or error solely for the contradiction (§3.4, RD-11) |

The generated restrictions MUST use the unqualified OWL forms specified in DK-REL-10. Reverse-side property selection MUST follow DK-REL-09: use the corresponding named inverse when generated; otherwise, use an anonymous inverse expression of the primary property.

These cardinalities MUST follow DK-REL-07's mode-specific treatment (RD-17 / ODI-CONTROLS): `none` retains the independently applicable mapping; `preserve-conflicting-constraints` MUST NOT adjust or omit it to accommodate chains; `omit-conflicting-constraints` MUST omit only restrictions using property expressions made non-simple by actually emitted material chains, including through the accepted hierarchy and inverse mappings.

This mapping does not modify the attribute mapping in DK-ATT-03. Unbounded relation-end multiplicities are specified in DK-REL-12. Explicit null cardinalities are specified in DK-REL-13. Missing `cardinality` fields use the fallback in DK-DIAG-09 (RD-11 / RD-02). Untranslatable multiplicities and bounds follow DK-DIAG-10, including partial recovery of independently valid numeric bounds in `best-effort`. Contradictory numeric intervals are transformable under §3.4 (RD-11). Cardinality syntax, limited lexical normalization, and treatment of ambiguous malformed expressions are specified in DK-DIAG-11 (RD-11 / RD-02).

**Rationale (non-normative):** Equal minimum and maximum bounds have the same OWL meaning as an exact-cardinality restriction. Using one exact restriction expresses that requirement compactly.

### DK-REL-12 — Unbounded relation-end multiplicities (RD-11)

For supported ordinary binary class-to-class relations, standalone `*` MUST be interpreted as `0..*`. Unbounded multiplicities MUST be mapped as follows:

| Multiplicity | Required cardinality output |
|---|---|
| `*` or `0..*` | No cardinality restriction |
| `l..*`, where `l` is a positive integer | One unqualified `owl:minCardinality` restriction with value `l` |

DirectKG MUST NOT generate a maximum-cardinality or exact-cardinality restriction from these multiplicities. An unbounded upper bound MUST NOT be replaced with a finite numeric limit.

Restrictions MUST follow the relation-end direction and `rdfs:subClassOf` placement in DK-REL-11 and the reverse-side property-selection rules in DK-REL-09. The unqualified forms are specified in DK-REL-10.

These forms MUST be accepted without a warning or error solely because they are unbounded.

Generating no cardinality restriction for `*` or `0..*` MUST NOT omit the relation property or change inverse-generation eligibility. These values remain non-null multiplicities under the `informed` inverse mode in DK-INV-01.

This unbounded relation-end mapping does not change attribute mappings. Explicit null cardinalities are governed by DK-ATT-03 and DK-REL-13. Missing `cardinality` fields use the fallback in DK-DIAG-09 (RD-11 / RD-02). Untranslatable multiplicities and bounds follow DK-DIAG-10, including partial recovery of independently valid numeric bounds in `best-effort`. Contradictory numeric intervals are transformable under §3.4 (RD-11). Cardinality syntax, limited lexical normalization, and treatment of ambiguous malformed expressions are specified in DK-DIAG-11 (RD-11 / RD-02).

**Rationale (non-normative):** An unbounded upper bound imposes no maximum; it does not require infinitely many related individuals. A minimum of zero adds no cardinality constraint.

### DK-REL-13 — Explicit null relation-end cardinalities (RD-11 / DK-ATT-03)

For supported ordinary binary relation ends, an explicit JSON `cardinality: null` MUST be treated as the absence of an explicit multiplicity available for transformation. DirectKG MUST NOT generate a cardinality restriction from that value or substitute a default multiplicity.

All other applicable mappings MUST continue. An explicit null cardinality MUST NOT, by itself, cause a warning, error, or transformation failure under any input policy.

Existing inverse-generation eligibility rules remain unchanged. Under `informed`, a null cardinality does not satisfy the non-null multiplicity condition; a qualifying role name may independently trigger inverse generation, as specified in DK-INV-01. Null MUST remain distinct from explicit `*` or `0..*`, including when evaluating inverse-generation eligibility.

The corresponding supported-attribute handling is specified in DK-ATT-03. Missing `cardinality` fields use the distinct fallback in DK-DIAG-09, which requires a warning. Untranslatable multiplicities and bounds are governed separately by DK-DIAG-10; contradictory numeric intervals are transformable under §3.4 (RD-11). Cardinality syntax, limited lexical normalization, and treatment of ambiguous malformed expressions are specified in DK-DIAG-11 (RD-11 / RD-02).

**Rationale (non-normative, for attributes and ordinary relation ends):** VP-plugin 0.5.3 converts Visual Paradigm's “Unspecified” multiplicity to null. Generating a numeric restriction would introduce a bound not supplied by that JSON value.

### DK-REL-14 — Direct mapping of relation generalization (RD-12)

For every explicit relation-to-relation generalization whose specific and general relations both successfully generate primary `owl:ObjectProperty` resources, DirectKG MUST emit:

```turtle
:SpecificProperty rdfs:subPropertyOf :GeneralProperty .
```

DirectKG MUST use the primary properties generated under the existing relation-transformation rules, preserving their established source-to-target directions.

Generation of this axiom MUST NOT depend on checking semantic compatibility between the relations' endpoint classes, domains, or ranges. DirectKG MUST NOT require corresponding endpoint classes to have an explicit or inferred specialization relationship.

DirectKG MUST NOT reverse, repair, or reinterpret either relation to establish endpoint correspondence. Classes and relations MUST otherwise retain their existing mappings.

Structural resolution remains required. Unresolved references or failures to generate the required primary properties remain subject to the accepted input-processing rules in DK-DIAG-05 (RD-02); they MUST NOT be treated as semantic compatibility failures.

This rule establishes the primary-property mapping for ordinary relation generalizations. DK-INV-12 (RD-12) additionally requires the corresponding specialization between generated named inverses when both exist. Endpoint compatibility and semantic orientation checks are not eligibility conditions. Disjoint relation generalization sets are mapped under DK-REL-15 (RD-13). The completeness limitation for relation sets with two or more distinct specific relations is specified in DK-REL-16; fully resolved singleton relation-set completeness is specified in DK-REL-20.

Explicit UML Property subsetting and redefinition references are mapped separately under DK-PROP-03 (RD-14). They do not inherit the additional inverse-specialization emission required for relation generalizations by DK-INV-12.

**Example (non-normative):** If `relates` connects A to B and `relates2` connects C to D, an explicit specialization of `relates` by `relates2` produces `relates2 rdfs:subPropertyOf relates`, without checking compatibility between C and A or between D and B.

### DK-REL-15 — Disjointness of relation specializations and generated inverses (RD-13)

The examples below illustrate the ordinary disjointness mapping; emitted axioms remain subject to the mode-specific treatment in this rule and DK-REL-07.

For a relation generalization set with `isDisjoint: true`, DirectKG MUST emit pairwise `owl:propertyDisjointWith` statements between the successfully generated primary `owl:ObjectProperty` resources corresponding to the set's explicit specific relations.

For each such pair, DirectKG MUST also emit `owl:propertyDisjointWith` between the corresponding named inverse properties when both inverses are generated.

If either named inverse is absent under the selected inverse-generation mode, DirectKG MUST omit that inverse disjointness pair without a warning. DirectKG MUST NOT force inverse generation to express the pair.

For `isDisjoint: false`, DirectKG MUST generate no disjointness axiom from that flag.

DirectKG MUST preserve the properties' established directions and existing mappings. Generation of these disjointness axioms MUST NOT depend on checking or repairing semantic compatibility between endpoint classes, domains, or ranges.

These disjointness axioms MUST follow DK-REL-07's mode-specific treatment. Under `none` and `preserve-conflicting-constraints`, all independently applicable pairs MUST remain. Under `omit-conflicting-constraints`, DirectKG MUST omit only pairwise axioms with at least one property expression made non-simple by actually emitted material chains, including through accepted hierarchy and inverse mappings; unrelated pairs MUST remain. DK-DIAG-07 requires documentation of the resulting OWL 2 DL compatibility limitation. This rule does not change inverse-generation eligibility, primary-property directions, or material-property-chain generation. Multi-member relation-set completeness is governed by DK-REL-16 and singleton completeness by DK-REL-20. For `isDisjoint: true`, a singleton relation generalization set MUST generate no disjointness statement from that set because no pair of specific relations exists; independently applicable disjointness mappings remain in force.

**Rationale and examples (non-normative):**

```turtle
:approves rdfs:subPropertyOf :respondsTo .
:rejects rdfs:subPropertyOf :respondsTo .
:approves owl:propertyDisjointWith :rejects .
```

The same ordered pair cannot be connected by both specific properties. This does not make their participant classes disjoint. When both named inverses are generated:

```turtle
:isApprovedBy owl:propertyDisjointWith :isRejectedBy .
```

This mapping concerns binary relation properties, not disjointness between separately represented relationship occurrences.

### DK-REL-16 — Completeness limitation for multi-member relation generalization sets (RD-13)

For a relation generalization set with `isComplete: true` and two or more distinct specific relations, DirectKG MUST NOT generate a completeness axiom or substitute a validation constraint.

DirectKG MUST emit a warning identifying the affected set and explaining that its relation-set coverage is not represented. This warning alone MUST NOT abort transformation under any input policy, including `strict`.

Documentation MUST identify this omission as a mapping limitation.

All other applicable mappings MUST remain applicable, including relation properties, subproperty axioms, generated inverses, and disjointness axioms.

For `isComplete: false`, DirectKG MUST generate no completeness axiom and MUST NOT issue a warning solely because of that flag.

This rule does not change class-set completeness mappings. Fully resolved singleton relation-set completeness is governed separately by DK-REL-20.

**Rationale (non-normative):** OWL 2 provides no ordinary object-property union constructor corresponding to class union. Property chains express composition, not alternatives. Omitting coverage preserves the supported mappings without introducing an incorrect approximation or a separate validation representation.

### DK-REL-17 — Binary relations with relation-valued endpoints (RD-16 / RD-17)

A binary source relation whose endpoint `propertyType` resolves to another source `Relation` MUST NOT undergo ordinary primary-property or inverse-property generation unless an explicit specialized rule establishes a different mapping for that endpoint pattern. Material–relator and material–mode derivations are recognized independently of endpoint order and used only as specified in DK-REL-08 (RD-16 / RD-17). Comparative–quality derivations follow DK-REL-18 (RD-17).

Any other structurally resolved binary relation with a relation-valued endpoint and no explicitly accepted DirectKG mapping MUST generate no resource or property representing that connector; no named or anonymous inverse for it; no domain, range, or cardinality axioms from it; and no reification, punning, or grounding annotation from it. DirectKG MUST issue a nonfatal warning under every input policy identifying the connector and explaining that no accepted mapping exists for its endpoint pattern. This specific warning MUST remain nonfatal even under `strict`.

Independently transformable endpoint classes and endpoint relations MUST retain their applicable mappings. Omitting the connector MUST NOT suppress those independent transformations. DirectKG MUST NOT infer a missing `material`, `comparative`, `relator`, `mode`, or `quality` stereotype, change endpoint identity, or otherwise reinterpret a connector to make it match a supported pattern.

A null, malformed, or unresolved endpoint remains a structural failure under DK-DIAG-03 and DK-DIAG-05 and MUST NOT use this intentional-omission fallback. Recognized material–relator and material–mode derivations retain the transformation-time use, non-representation, and diagnostics of DK-REL-08 and DK-DIAG-08. Recognized comparative–quality derivations use the specific diagnostic of DK-REL-18 instead of this generic limitation warning. A later explicitly accepted specialized transformation-time mapping for another relation-valued endpoint pattern MAY consume that connector and replace the limitation warning for that pattern; this rule implies no such additional mapping.

RD-17 establishes the accepted material–mode and comparative–quality behavior in DK-REL-07–08 and DK-REL-18. Other additional truthmaker patterns retain this generic boundary unless an explicit mapping is accepted. The general output and OWL-profile contract remains the responsibility of RD-04.

**Rationale and example (non-normative):** VP-plugin exports include both material-relation → relator-class and relator-class → material-relation endpoint orders. Resolving endpoint identities and types recognizes the same supported material–relator derivation in either order. Mode-grounded material and quality-grounded comparative patterns likewise do not depend on serialized endpoint order. An otherwise unmapped relation-valued connector is omitted because an ordinary object property would assign misleading class-domain and class-range semantics. The omission does not reject potential future transformations of other truthmaker patterns.

### DK-REL-18 — Quality-grounded comparative derivations (RD-17)

For an explicit `«derivation»` whose resolved endpoints are a `«comparative»` relation `C` and a `«quality»` class `Q`, DirectKG MUST recognize the pattern independently of serialized endpoint order. DirectKG MUST transform `C` as an ordinary object property under the existing rules, including its independently applicable naming, inverse, domain, range, and diagnostic behavior. The derivation connector MUST NOT receive a separate resource or ordinary-property representation.

DirectKG MUST NOT derive a property chain, property equivalence, value-comparison rule, cardinality restriction, special property name, or property characteristic solely from the comparative–quality derivation. In particular, it MUST NOT infer transitivity, symmetry, asymmetry, reflexivity, irreflexivity, functionality, or inverse functionality merely from the `«comparative»` stereotype or its grounding quality.

DirectKG MUST emit a nonfatal unsupported-semantics diagnostic under every input policy, including `strict`, identifying the derivation connector and comparative relation and, where available, the grounding quality. The diagnostic SHOULD explain that the supported source representation does not provide the comparison rule needed to preserve the derivation semantics. It replaces the generic unsupported-connector warning in DK-REL-17 for this recognized pattern. Unresolved endpoints and other structural failures remain subject to DK-DIAG-03 and DK-DIAG-05.

### DK-REL-19 — Source-specific mereological properties (RD-17 / RD-25)

The comment preservation of `isExtensional` under DK-CLS-01 (RD-21) introduces no additional logical axioms solely from that flag and leaves this mereological mapping unchanged.

For each eligible ordinary binary class-to-class relation carrying the recognized OntoUML stereotype `memberOf`, `subCollectionOf`, `subQuantityOf`, or `componentOf`, DirectKG MUST retain its distinct source-specific primary `owl:ObjectProperty` and generate a direct `rdfs:subPropertyOf` axiom from that primary property to the corresponding generic property in the imported `dkgm` vocabulary (DK-GEN-04):

| Source stereotype | Superproperty of source relation's primary property |
|---|---|
| `memberOf` | `dkgm:memberOf` |
| `subCollectionOf` | `dkgm:subCollectionOf` |
| `subQuantityOf` | `dkgm:subQuantityOf` |
| `componentOf` | `dkgm:componentOf` |

The generic property IRIs in this table use the `U#` namespace established by DK-GEN-04 (RD-05); the ontology/import URI remains `U`. This identifier pattern does not change the source-specific mappings.

DirectKG MUST use the relation's already established primary direction. The recognized stereotype alone determines this bridge; `aggregationKind` MUST NOT determine whether it applies, its direction, or whether the primary property is replaced by an inverse expression. DirectKG MUST NOT reverse, normalize, repair, or otherwise reinterpret the source relation, substitute a generated named inverse or anonymous inverse expression for the primary property, or generate a named inverse solely for this bridge. Its existing naming, IRI, inverse, domain, range, multiplicity, cardinality, relation-generalization, and other independently applicable mappings remain in force. The supported source representation and its primary direction are authoritative even when they do not express the author's intended mereological orientation.

For every such covered relation, DirectKG MUST also declare its primary generated property an `owl:AsymmetricProperty`. It MUST NOT additionally declare a generated named inverse asymmetric solely because of the covered stereotype; when `owl:inverseOf` relates that inverse to the primary, its asymmetry follows semantically. A separate `owl:IrreflexiveProperty` declaration is not required by this mapping because asymmetry entails irreflexivity. The four generic `dkgm` properties are not declared asymmetric by default under DK-GEN-04.

Multiplicity-derived restrictions MUST continue to use the appropriate source-specific properties under DK-REL-09–13. Being a subproperty of a non-simple generic chain-bearing property alone does not make a source-specific property non-simple or prevent its accepted asymmetry or cardinality restrictions. Other independently applicable axioms may affect simplicity; this decision supplies no general OWL 2 DL conformance guarantee.

The accepted generic chains operate on the imported `dkgm` properties. DirectKG MUST NOT construct arbitrary source-specific mereological property-chain axioms solely because source relations have compatible covered stereotypes. The generic-level mapping and asymmetry are part of the default transformation and are independent of `--material-property-chains`, which controls only the accepted material-relation chains in DK-REL-07.

**Non-normative example:** If `r1` and `r2` are distinct subproperties of `dkgm:subQuantityOf`, assertions `a r1 b` and `b r2 c` permit the imported generic chain to infer `a dkgm:subQuantityOf c`; they do not, from those facts alone, infer `a r1 c` or `a r2 c`. A model whose primary direction is opposite its intended mereological direction may consequently yield an unintended generic assertion; this mapping does not validate or fix that model.

### DK-REL-20 — Complete singleton relation generalization sets (RD-13)

For a fully resolved relation generalization set containing exactly one member generalization, with `isComplete: true`, whose general and specific relations successfully generate primary `owl:ObjectProperty` resources, DirectKG MUST emit:

```turtle
:GeneralProperty rdfs:subPropertyOf :SpecificProperty .
```

The existing specialization mapping under DK-REL-14 MUST remain applicable:

```turtle
:SpecificProperty rdfs:subPropertyOf :GeneralProperty .
```

DirectKG MUST represent singleton completeness using the reverse subproperty axiom. It MUST NOT additionally emit `owl:equivalentProperty` for this completeness mapping. The properties MUST retain their distinct identifiers and established directions. DirectKG MUST NOT introduce semantic endpoint, domain, or range compatibility checks as prerequisites for this mapping.

When both corresponding named inverse properties are generated, DirectKG MUST additionally emit:

```turtle
:GeneralInverse rdfs:subPropertyOf :SpecificInverse .
```

The existing specific-to-general inverse specialization under DK-INV-12 MUST remain applicable. If either named inverse is absent, DirectKG MUST omit the additional reverse inverse-specialization axiom without a warning. It MUST NOT generate a named inverse or an anonymous inverse expression solely to represent this completeness.

Singleton membership alone MUST NOT produce a warning. For `isDisjoint: true`, a singleton relation generalization set MUST generate no disjointness statement from that set because no pair of specific relations exists. Independently applicable disjointness mappings remain in force.

DirectKG MUST NOT apply singleton completeness merely because partial processing failure leaves one surviving member of a larger set. Existing structural-error policies remain unchanged. This rule does not define duplicate-membership handling or handling of missing or malformed membership containers.

The added subproperty axioms MUST participate in DK-REL-07's non-simplicity propagation through the generated property hierarchy when material chains are emitted. These hierarchy axioms are not themselves subject to that rule's targeted omission of cardinality restrictions and property-disjointness axioms.

Whenever this singleton completeness mapping is applied, DirectKG MUST emit the nonfatal INFO diagnostic specified in DK-DIAG-14 for the affected set and corresponding general and specific relation.

**Rationale (non-normative):** Ordinary specialization provides inclusion from the specific property to the general property. Singleton completeness adds inclusion in the opposite direction. Together, these axioms entail the same set of related ordered pairs without merging identifiers. The construct is valid, but this equivalence consequence may be unexpected or unintended; INFO reporting makes it visible without classifying it as a modeling error.

## 11. Generated inverse properties

The generated inverse properties governed by this section are separately named inverse properties. DK-INV-04 also specifies the permission for anonymous inverse expressions in material-property chains, as extended by RD-11 for reverse-side relation-cardinality restrictions under DK-REL-09, by RD-14 for UML property subsetting and redefinition under DK-PROP-03, and by RD-17 for aligned characterization–external-dependence disjointness under DK-REL-01.

### DK-INV-01 — Generation modes (ODI-CONTROLS)

The CLI MUST expose `--inverse-properties` with the values `all`, `informed`, `named`, and `none`. The default MUST be `all`. This control governs generation of separately named inverse properties. It MUST NOT prohibit anonymous inverse expressions required or permitted by the accepted mappings, including those inside material-property chains generated under RD-17, those required by DK-REL-09 for reverse-side relation-cardinality restrictions when no corresponding named inverse is generated, those required by DK-PROP-03 (RD-14) for source association ends without generated named inverses, or those required by DK-REL-01 (RD-17) to align characterization–external-dependence disjointness when reversal is required and no corresponding named inverse is generated:

| Mode | Behavior |
|---|---|
| `all` | Default; generate every eligible named inverse property |
| `informed` | Generate when the inverse-facing end has a nonempty role name or non-null multiplicity |
| `named` | Generate only when the inverse-facing end has a nonempty role name |
| `none` | Generate no named inverse properties |

Role presence follows DK-INV-05: a multilingual role is present when any value contains a non-whitespace character. Successful ASCII normalization MUST NOT be an additional inverse-eligibility condition.

Under `informed`, either qualifying datum is sufficient. The values `*` and `0..*` remain non-null multiplicities even though DK-REL-12 generates no cardinality restriction for them; this absence MUST NOT change inverse-generation eligibility. An explicit null cardinality does not satisfy the non-null multiplicity condition; a qualifying role name may independently trigger generation. Null MUST remain distinct from explicit `*` or `0..*` when evaluating inverse-generation eligibility (DK-REL-13). An absent `cardinality` field MUST NOT satisfy the non-null multiplicity condition; other accepted eligibility conditions remain applicable (DK-DIAG-09).

**Rationale (non-normative):** Examination of 198 OntoUML JSON exports confirmed that real relation ends can have absent role names and null multiplicities, so the conditional modes represent meaningful distinctions.

### DK-INV-02 — Eligibility

A relation is inverse-eligible exactly when it is a supported binary OntoUML relation whose primary transformation successfully produces an IRI-identified `owl:ObjectProperty` with two resolved classifier endpoints suitable as domain and range.

Eligible cases include self-relations, supported stereotyped relations, and unnamed source relations that receive generated IRIs.

The following are not eligible:

- `«instantiation»`;
- material–relator and material–mode `«derivation»` connectors covered by DK-REL-08;
- comparative–quality `«derivation»` connectors covered by DK-REL-18;
- other resolved binary relations with relation-valued endpoints lacking an accepted mapping under DK-REL-17 (RD-16);
- attributes represented as `owl:DatatypeProperty`;
- generalizations and generalization sets;
- unsupported n-ary relations;
- constructs mapped as assertions, annotations, or reified structures instead of object properties.

Malformed relations are diagnosed under their underlying problem and MUST NOT be silently reclassified as ineligible. Recognized derivation connectors covered by DK-REL-08 and DK-REL-18 and other resolved relation-valued endpoint connectors omitted under DK-REL-17 do not produce inverse properties. In particular, DK-REL-17 prohibits both named and anonymous inverses representing an unsupported connector. Independently generated material and comparative properties retain their established inverse eligibility.

### DK-INV-03 — Inverse direction, domain, and range

For a primary property `A → B`, the generated inverse maps `B → A`. Its inverse-facing end is the association end typed by `A`—the inverse range and primary domain.

Every generated inverse MUST receive explicit reversed domain and range declarations derived mechanically from the primary property. These axioms are intentionally explicit even though they are logically redundant with `owl:inverseOf`, so non-reasoning consumers can inspect the property directly. DK-INV-12 similarly requires explicit specialization between generated named inverses for successfully mapped explicit relation generalizations when both inverses exist.

### DK-INV-04 — Explicit `owl:inverseOf`

Every generated named inverse property MUST have exactly one explicit `owl:inverseOf` assertion directed from the named inverse to its primary property:

```turtle
:Inverse owl:inverseOf :Primary .
```

DirectKG MUST NOT emit the redundant reciprocal assertion. This applies regardless of generation mode, naming path, collision path, or IRI strategy. When a named inverse property is not generated, its corresponding named inverse-to-primary `owl:inverseOf` assertion is not emitted. This does not prohibit `owl:inverseOf` triples representing anonymous inverse expressions inside material-property chains, reverse-side relation-cardinality restrictions as specified in DK-REL-09 (RD-11), UML property subsetting and redefinition under DK-PROP-03 (RD-14), or aligned characterization–external-dependence disjointness under DK-REL-01 (RD-17).

The permission for anonymous inverse expressions established here covers material-property chains, including material–relator and mode-grounded material chains; through RD-11, reverse-side relation-cardinality restrictions for supported ordinary binary relations; through RD-14, UML property subsetting and redefinition; and through RD-17, aligned characterization–external-dependence disjointness under DK-REL-01. It does not establish their treatment in other transformations or the broader cardinality mapping. DK-REL-09 requires a corresponding named inverse when generated and an anonymous inverse expression of the primary relation property otherwise. DK-PROP-03 applies the same selection to source association ends participating in its references. Under DK-REL-01, alignment uses the primary property when its direction is already correct; when reversal is required, it uses the corresponding generated named inverse, or an anonymous inverse expression if no such named inverse is generated. This extension does not change named-inverse generation eligibility or assertions. The direction-specific chain representation in DK-REL-07 remains independent of the selected inverse-generation mode and always uses anonymous inverse expressions for backward steps, even when corresponding named inverses exist.

### DK-INV-05 — Inverse-facing role and label

A role is present when it is non-null and contains at least one non-whitespace character. A multilingual role MUST count as present when any of its values contains a non-whitespace character; successful ASCII normalization MUST NOT be an additional condition for inverse eligibility. Under the name strategy, only the inverse-facing end's role may name the inverse. Supported localized role names follow DK-IRI-10 for the IRI naming input; all applicable source-authored labels remain subject to DK-LBL-01–02.

When present:

- under the name strategy, its normalized value is the preferred IRI candidate;
- under either IRI strategy, the original role name MUST be preserved as the inverse's `rdfs:label`, with language resolved under DK-LBL-02.

When the inverse-facing role is absent, no synthetic `rdfs:label` is generated for the inverse under either IRI strategy.

Source-end descriptions MUST be preserved on the corresponding generated named inverse under DK-LBL-02. That rule does not require generating an inverse solely for a description and does not automatically copy the enclosing relation's description to the inverse.

### DK-INV-06 — Name-strategy structural fallback

When no inverse-facing role is present, DirectKG MUST derive the inverse candidate from the resolved primary-property local name:

```text
inverseOf<ResolvedPrimaryPropertyLocalName>
```

For example, `employs` produces `inverseOfEmploys`. As established in DK-INV-05, no synthetic `rdfs:label` is generated because the source supplies no inverse domain term.

This fallback applies to `all` and to `informed` when multiplicity triggers generation without a role. It is unnecessary under `named`.

### DK-INV-07 — Source-backed precedence

Generated auxiliary resources MUST NOT change the IRIs of source-backed resources.

DirectKG MUST resolve all source-backed resource candidates and IRIs before generated inverse candidates. Source-backed resources continue to use their ordinary naming and collision rules.

If a role-derived inverse candidate is unique, it remains unchanged. If it collides with a source-backed resource, a source-backed candidate claim, or one or more other generated inverse candidates, every colliding generated inverse MUST abandon the role-derived candidate and use its own primary-based fallback:

```text
inverseOf<ResolvedPrimaryPropertyLocalName>
```

The prefix is applied to the primary property's resolved local name, never to the inverse role. A retained role label remains unchanged after fallback.

When several inverses share the same role-derived candidate, none remains at the shared candidate; each uses its own primary-based fallback. Distinct inverse properties MUST never be merged.

**Rationale (non-normative):** Treating source-backed properties and generated inverses as one undifferentiated collision group would allow enabling inverse generation to rename source-backed resources. Corpus analysis found that this would affect 30 primary relation-property IRIs and two classifier-owned property IRIs across 14 models.

### DK-INV-08 — Secondary name-strategy collisions

If the primary-based fallback collides, only the generated inverse is further qualified. The qualifier is the inverse domain—the primary property's range:

```text
inverseOf<ResolvedPrimaryPropertyLocalName>_<InverseDomain>
```

A supported localized inverse-domain name supplying this naming component follows DK-IRI-10.

If distinct generated inverses still share the qualified candidate, every inverse in that collision group receives a deterministic numeric suffix:

```text
inverseOfWorksFor_Organization_1
inverseOfWorksFor_Organization_2
```

The inverse-facing association-end ID is the stable ordering key for `_1 … _N`; it MUST NOT appear in the resulting IRI merely for this purpose.

### DK-INV-09 — ID-strategy inverse IRI

Under `--iri-strategy id`, the generated inverse property MUST use the source association-end ID as its source identifier. It MUST NOT ordinarily use the association ID, target-end ID, a synthetic modification of the association ID, or the name-strategy `inverseOf<PrimaryPropertyLocalName>` construction.

The end ID is processed by the established ID-escaping and exceptional collision rules.

### DK-INV-10 — Stability and diagnostics

Changing inverse-generation mode MAY change generated inverse IRIs, because a newly generated inverse may create an inverse–inverse collision. It MUST NOT change a source-backed resource IRI.

Adding or changing an inverse-facing role name MAY also change the generated inverse IRI.

When `informed` or `named` intentionally omits an inverse, DirectKG MUST emit no warning, information message, or element-level report entry. This silence does not apply to malformed relations, unresolved endpoints, or failures of the primary transformation.

### DK-INV-11 — Multilingual scope

For plain JSON exported from VPP through the VP-plugin extraction path, which exports at most one role name per end, special multilingual inverse-name selection is not required. The bounded language enrichment in §3.2 additionally accepts supported textual fields in `languageString` form; supported source-authored labels and descriptions follow DK-LBL-02. Within that bounded enrichment, DK-IRI-10 establishes deterministic lexical selection for supported multilingual inverse-property naming candidates, and DK-INV-05 governs multilingual role presence. This extension does not authorize arbitrary schema-conformant JSON. Additional multilingual inverse-naming behavior MAY be reconsidered if arbitrary schema-conformant JSON becomes supported.

**Context (non-normative):** The baseline review of 198 `ontology.json`/`ontology.vpp` pairs found no multilingual role names in actual exports. The standalone schema and plugin data structures can represent multilingual text; the accepted input extension remains limited to §3.2.

### DK-INV-12 — Explicit specialization of generated named inverses (RD-12)

For each explicit relation generalization successfully mapped to a primary-property `rdfs:subPropertyOf` axiom under DK-REL-14, DirectKG MUST also emit the corresponding specialization between the named inverse properties when both named inverses are generated:

```turtle
:SpecificInverse rdfs:subPropertyOf :GeneralInverse .
```

The inverse of the specific relation specializes the inverse of the general relation.

If either named inverse is absent under the selected inverse-generation mode, DirectKG MUST omit this additional axiom without a warning. DirectKG MUST NOT generate a named inverse or an anonymous inverse expression solely to express this specialization.

For the specific-to-general specialization in this rule, DirectKG MUST mirror only the explicit source generalization edges. This mapping MUST NOT additionally materialize their transitive closure. DK-REL-20 (RD-13) additionally requires the reverse named-inverse inclusion for fully resolved complete singleton relation generalization sets when both named inverses are generated; it does not change inverse-generation eligibility.

Generation of the inverse specialization MUST NOT depend on semantic-compatibility checks between endpoint classes, domains, or ranges.

This behavior MUST follow the existing inverse-generation setting. No additional configuration argument is introduced. This is an explicitly required materialization under DK-GEN-02; it does not replace the primary-property generalization mapping or change inverse-generation eligibility. Named-inverse disjointness for relation generalization sets is governed separately by DK-REL-15 (RD-13).

This explicitly mirrored specialization applies to relation generalizations under DK-REL-14, not to UML Property subsetting or redefinition references under DK-PROP-03 (RD-14).

**Rationale and example (non-normative):** The inverse specialization is already entailed by the primary specialization and inverse axioms. Explicit emission makes the hierarchy available to consumers without OWL reasoning, consistently with the rationale of DK-INV-03.

```turtle
:relates2 rdfs:subPropertyOf :relates .
:isRelatedBy owl:inverseOf :relates .
:isRelatedBy2 owl:inverseOf :relates2 .

:isRelatedBy2 rdfs:subPropertyOf :isRelatedBy .
```

## 12. Explicit `«instantiation»` associations

### DK-INS-01 — Canonical representation

`rdf:type` is the canonical representation of actual instantiation facts.

An explicit `«instantiation»` association MUST NOT become an ordinary `owl:ObjectProperty`, and DirectKG MUST NOT mint a property IRI for it. Because the current conceptual-model input does not provide concrete instantiation links merely by declaring the association, the declaration itself MAY produce no RDF/OWL statement.

If concrete instantiation links are supported in the future, each link MUST be represented directly as:

```turtle
:Instance rdf:type :Classifier .
```

### DK-INS-02 — Deliberately discarded association data

The following `«instantiation»` association-level information is deliberately not materialized:

- association name;
- role names;
- association identifier or IRI;
- multiplicities;
- other association-level characteristics.

Whenever one or more of these are present and discarded, DirectKG MUST emit one consolidated warning identifying the association and discarded information.

The warning MUST identify the affected `«instantiation»` association using its source element identifier, include its source element type where available, identify the categories of association-level information discarded, and describe the effect on the generated output. Categories such as “association name,” “role names,” and “multiplicities” MAY be listed; the actual discarded values MUST NOT be reproduced in the diagnostic payload. This prohibits copying the actual association name, role-name strings, multiplicity expressions, a separately declared association IRI, or values of other discarded association-level characteristics into the diagnostic.

Discarded association-level values MUST NOT be reproduced as RDF/OWL output, provenance metadata, annotations, alternative resources, or diagnostic payload data. The source element identifier MAY be retained solely as a diagnostic traceability locator, despite the absence of an association identifier in the OWL output. This locator MUST NOT be treated as an OWL representation of the association; DirectKG MUST NOT mint an association or property IRI from the diagnostic occurrence or create an alternative association resource from its information.

When the warning is displayed under the selected console threshold, its console form and persistent JSON representation under DK-DIAG-04 MUST describe the same underlying diagnostic event and obey the same content boundary. They MAY use different presentation formats. The diagnostic documents the loss of association-level information; it does not preserve or substitute for the discarded association semantics.

### DK-INS-03 — No reconciliation

An `«instantiation»` association is not compared or reconciled with categorizer-derived classifications. No precedence is established, and classifications are not suppressed merely because they overlap or appear inconsistent.

## 13. IRI generation and naming

### DK-IRI-01 — Base IRI

DirectKG MUST support:

```text
--base-iri <IRI>
```

If absent, it MUST use `https://example.org/directkg#` and emit a non-fatal warning explaining that this is a placeholder namespace and is not recommended for publication.

If a supplied base ends with `#` or `/`, that delimiter MUST be preserved. Otherwise DirectKG MUST append `#` without warning. Supplied-base validation and rejection follow the requirements below.

#### Generated ontology IRI (RD-05)

DirectKG MUST automatically derive the generated ontology's IRI from the effective entity base established above, after applying base selection and delimiter handling. The derivation MUST use this fixed rule:

- If the effective entity base ends with `#`, remove that final character.
- Otherwise, preserve the effective entity base unchanged, including a final `/`.

DirectKG MUST NOT provide a separate configuration control for choosing an ontology IRI independently of the entity base. This derivation MUST NOT modify the effective entity base or the entity IRIs generated from it. The placeholder default, delimiter handling, and warning requirements above remain unchanged.

This rule establishes the generated ontology's IRI only; it does not select the imported `dkgm` vocabulary's IRI under DK-GEN-04.

**Rationale and examples (non-normative):** Automatic derivation keeps configuration simple and avoids a second independently configured identifier.

| Supplied `--base-iri` | Effective entity base | Derived ontology IRI |
|---|---|---|
| `https://example.org/model` | `https://example.org/model#` | `https://example.org/model` |
| `https://example.org/model#` | `https://example.org/model#` | `https://example.org/model` |
| `https://example.org/model/` | `https://example.org/model/` | `https://example.org/model/` |
| Not supplied | `https://example.org/directkg#` | `https://example.org/directkg` |

When the base is absent, the existing placeholder warning remains applicable. Reusing the same effective entity base produces the same derived ontology IRI.

#### Supplied-base validation before conversion (ODI-IRI, option A — invalid supplied base)

Before conversion starts, DirectKG MUST validate a supplied base as a syntactically valid absolute RDF IRI. An explicitly empty or whitespace-only value MUST be rejected; it MUST NOT be treated as an omitted base.

DirectKG MUST apply the existing delimiter-handling and ontology-IRI derivation rules above. The resulting effective entity base and derived ontology IRI MUST both be valid absolute RDF IRIs. If either is invalid, DirectKG MUST reject the configuration before conversion starts.

Beyond the already accepted delimiter handling, DirectKG MUST NOT automatically repair the supplied base. This prohibits trimming, percent-encoding repair, relative-reference resolution, and substitution of the placeholder namespace.

Rejection MUST apply under every input policy: `strict`, `tolerant`, and `best-effort`:

- The CLI MUST report a configuration error and exit with code `2` under §15's invalid-invocation contract.
- Python MUST signal the configuration error programmatically; no particular exception class is prescribed.
- No conversion starts, and no ontology, transformation outcome, or conversion-diagnostics report is produced for this rejection.

Validation MUST be syntactic. DirectKG MUST NOT impose an HTTP(S)-only restriction or perform network-availability checks. Syntactically permitted Unicode characters remain supported. Valid bases and the existing omitted-base fallback retain their accepted behavior.

**Rationale and examples (non-normative, ODI-IRI, option A — invalid supplied base):** Rejecting invalid configuration preserves the user's namespace intent and avoids generating an ontology under a substituted namespace.

For example, `my-model` is relative and is rejected. Although `https://example.org/model#part` is itself a valid IRI, the established delimiter rule would produce `https://example.org/model#part#`; that configuration is therefore rejected rather than repaired.

**Technical anchors (informative):** [RDF 1.1 Concepts §3.2](https://www.w3.org/TR/rdf11-concepts/#section-IRIs); [RFC 3987 §2.2](https://www.rfc-editor.org/rfc/rfc3987.html#section-2.2).

#### Optional caller-supplied ontology version IRI (RD-05, Option B)

DirectKG MUST provide the optional CLI control `--ontology-version-iri IRI` and an equivalent optional Python API control.

When supplied and valid, DirectKG MUST emit the following statement on the generated ontology resource:

```text
<ontologyIRI> owl:versionIRI <suppliedVersionIRI> .
```

The subject MUST remain the ontology IRI derived under this rule. When the input is absent, DirectKG MUST emit no `owl:versionIRI` statement and MUST issue no diagnostic solely because it is absent.

Before conversion starts, DirectKG MUST validate the supplied value as an absolute IRI permitted for OWL ontology version identifiers. Invalid values MUST follow the existing pre-conversion configuration-rejection rules, independently of the selected input policy: the CLI reports a configuration error and exits with code `2`; Python signals the error programmatically without a prescribed exception class; and no conversion starts or produces an ontology, transformation outcome, or conversion-diagnostics report.

Version identifiers are assigned by the caller. DirectKG MUST NOT derive a version IRI from filenames, execution timestamps, checksums, or the DirectKG software version. This decision adds no field to the external metadata whitelist under DK-GEN-09.

Supplying or changing only the version IRI does not change ontology IRI derivation, generated entity IRIs, or the established DKGM import under DK-GEN-04.

The ontology version IRI setting does not change the provenance rules in DK-GEN-10. When provenance is enabled, the effective configuration record MUST reflect the ontology version IRI setting. In sidecar mode, the output checksum MUST be calculated over the final serialized ontology bytes, including the version IRI statement when present. This decision introduces no special provenance exclusion or requirement for provenance values to remain invariant.

Emitting a version IRI neither publishes the ontology nor verifies across executions that repeated use of that identifier refers to identical ontology content. No cross-run version registry is introduced.

### DK-IRI-02 — Strategies

DirectKG MUST support:

```text
--iri-strategy name
--iri-strategy id
```

The default is `name`. Name mode prioritizes readability; renaming a source element MAY change its IRI, and documentation MUST explain this consequence. ID mode prioritizes identity stability.

Supported localized names supplying naming components follow DK-IRI-10. Its selected original text is the input to the applicable naming rules; ID-based IRI construction remains unchanged.

Under the ID strategy, a source-backed resource's local name MUST be derived from its designated source identifier rather than its source name, even when the resource is named. For classes and classifier-owned properties, the designated identifier is the source element's own ID. Enumeration values use their literal elements' own source IDs under DK-IRI-08. Relation-derived properties use the association-end identifiers specified by DK-IRI-06.

When name-based naming rules and applicable type-specific fallbacks yield no usable candidate for an otherwise transformable source-backed resource, DK-IRI-04 requires the generic source-ID fallback where its prerequisites hold. This resource-specific fallback does not switch the configured IRI strategy.


### DK-IRI-03 — Name normalization

For a supported localized name, DK-IRI-10 selects the original source text used as input to this normalization.

Name-based local names MUST use deterministic lexical normalization:

```text
source name
→ Unicode normalization
→ trim
→ remove diacritics
→ replace whitespace and punctuation with _
→ collapse repeated _
→ remove leading/trailing _
→ restrict to ASCII letters, digits, and _
→ protect a leading digit
→ collision handling
```

A canonical decomposition-based Unicode normalization SHOULD be used. A normalized name beginning with a digit MUST receive a leading `_`.

DirectKG MUST NOT translate, singularize, pluralize, expand abbreviations, spell-correct, substitute synonyms, fuzzy-match, infer equivalence, or otherwise semantically rewrite source terminology.

### DK-IRI-04 — Unusable and unnamed names (ODI-IRI, option A)

Established naming rules and applicable type-specific fallbacks MUST retain priority over the generic source-ID fallback below. Their existing diagnostic rules remain applicable and unchanged. Labels are governed by DK-LBL-01, including its separate rules for property and non-property resources.

For this rule, a usable source ID is a source identifier valid under §3.4's minimal opaque identifier definitions (RD-02, Alternative A).

When no localized naming candidate is usable under DK-IRI-10, DirectKG MUST apply the applicable fallback and diagnostic rules for the affected resource type, including this generic policy where its prerequisites hold.

An unnamed or unusably named class in name mode MUST use:

```text
unnamedClass_<escaped-source-id>
```

The stereotype MUST NOT appear in this synthetic IRI. The class receives no invented label, and transformation continues after a non-fatal warning identifying available source details and the generated IRI.

Where available, that warning MUST identify the source element type, source element ID, stereotype, and generated IRI.

For resources governed by the type-specific naming and fallback rules above rather than the generic policy below, unnamed resources in ID mode use their source IDs rather than an unnamed fallback, but DirectKG MUST still warn that the source element is unnamed. Existing type-specific diagnostic rules remain applicable and unchanged.

#### Generic source-ID fallback

For an otherwise transformable source-backed resource requiring a name-based IRI, when its established naming rules and applicable type-specific fallbacks yield no usable candidate, DirectKG MUST use the candidate defined by its existing ID-strategy rules, provided its designated source ID is usable. The designated identifier follows the existing resource-specific ID basis, including DK-IRI-02, DK-IRI-06, and DK-IRI-08.

The generic fallback MUST reuse existing source-ID escaping, leading-digit protection, collision handling, and source-backed-resource precedence. Distinct source elements MUST NOT be merged. Applying this resource-specific fallback does not switch the configured IRI strategy.

This generic policy MUST apply to unnamed or unusably named enumeration literals. The literal's own source ID supplies the fallback candidate. DirectKG MUST NOT introduce an enumeration-specific prefix such as `unnamedLiteral_<id>`.

For cases governed by this generic policy, DirectKG MUST produce diagnostics as follows:

| Condition | Required diagnostic |
|---|---|
| Name mode requires the generic source-ID fallback because no usable name-based candidate is available | WARNING identifying the affected element and generated IRI |
| ID mode and the element's name is absent, null, empty, or whitespace-only | INFO identifying the affected element and missing-name condition |
| ID mode uses the designated source ID as ordinarily required | No diagnostic solely for using that ID |

These generic diagnostics MUST be nonfatal under every input policy. Existing type-specific diagnostic rules remain applicable and unchanged. Diagnostic delivery follows DK-DIAG-04, including the accepted console threshold: console filtering does not suppress diagnostic collection or export.

DirectKG MUST preserve available source-authored labels under the existing rules, including text that cannot supply a usable IRI name. It MUST NOT invent a label for an unnamed element.

An enumeration value successfully preserved through this fallback MUST count as successfully transformed when applying the existing enumeration-membership, `owl:oneOf`, and `owl:AllDifferent` rules in DK-CLS-10–11. A fallback alone MUST NOT make the value list incomplete.

**Rationale (non-normative):** Preserves identifiable source information while reusing existing identity rules. In name mode, the ID fallback warrants a warning. In ID mode, the INFO reports missing descriptive text rather than treating intentional ID use as exceptional.


### DK-IRI-05 — Source ID escaping

Source IDs valid under §3.4's minimal opaque identifier definitions (RD-02, Alternative A) use technical escaping, not name normalization. DirectKG MUST preserve ASCII letters, digits, and case. Every other UTF-8 byte MUST be encoded as `_xHH` using uppercase hexadecimal. `_` itself MUST be encoded as `_x5F`.

The algorithm MUST be injective with respect to source-ID byte sequences and SHOULD be reversible. It MUST NOT trim, transliterate, translate, case-fold, or semantically rewrite IDs.

When an escaped ID is the entire local name and begins with a digit, DirectKG MUST prefix `id_`. This prefix is not added when the escaped ID follows an already-safe synthetic prefix.

Examples:

```text
A3Jb3OGFS_j2pBF8 → A3Jb3OGFS_x5Fj2pBF8
9rqa._6AUB1CSiNo → id_9rqa_x2E_x5F6AUB1CSiNo
```

### DK-IRI-06 — ID basis for relation-derived properties

Under `--iri-strategy id`:

- direct property IRI basis = target association-end ID;
- generated inverse IRI basis = source association-end ID.

The association's own ID MUST NOT be the IRI basis for either property. It MAY remain internal for tracking, diagnostics, or processing.

This directional rule applies to self-relations: distinct end IDs identify the two property directions even when both ends have the same classifier.

When inverse generation is disabled, the direct property still uses the target-end ID and the source-end ID produces no separate property. Under name-based IRIs, DK-IRI-09 uses these designated end IDs for its source-ID annotations without changing IRI construction.

### DK-IRI-07 — Ordinary name collision groups

After all applicable name fallbacks and source-backed property qualification, DirectKG MUST check local-name collisions. A unique candidate remains unsuffixed. Every member of a collision group of size `N` MUST receive `_1` through `_N`; DirectKG MUST NOT leave one unsuffixed.

Suffix allocation MUST be deterministic and stable for an unchanged source model. Stable source information, preferably element IDs or deterministic source order, SHOULD assign suffixes.

Distinct source elements MUST NOT be merged. A collision between distinct escaped source IDs is exceptional and MUST NOT be silently repaired as an ordinary name collision; this specification does not define its exact disposition.

### DK-IRI-08 — Enumeration value identity, IRIs, and labels (RD-09)

Distinct source enumeration literal elements MUST remain distinct generated resources, including when their source names or normalized names coincide.

Under `--iri-strategy name`, a value with a usable normalized name MUST use the following local-name construction, subject to the existing collision handling:

```text
<ResolvedEnumerationLocalName>_<NormalizedValueName>
```

`ResolvedEnumerationLocalName` MUST be the enumeration class's already-resolved local name after its applicable naming and collision handling. The value name MUST use the name-normalization rules in DK-IRI-03, with DK-IRI-10 selecting the original text for a supported localized name.

Every named source enumeration literal MUST preserve its source name as an `rdfs:label`, consistently with DK-LBL-01.

Under `--iri-strategy id`, an enumeration value MUST use the literal element's own source ID processed according to DK-IRI-05. Its IRI MUST NOT be based on or prefixed with the enumeration classifier's ID.

The existing collision handling and source-backed-resource precedence MUST apply. Name collisions MUST NOT cause distinct source elements to be merged.

For an unnamed literal or a literal whose name yields no usable naming candidate, DK-IRI-04's generic source-ID fallback MUST apply where its prerequisites hold, using that literal's own source ID. DirectKG MUST NOT introduce an enumeration-specific `unnamedLiteral_<escaped-source-id>` prefix. Applicable diagnostics follow DK-IRI-04, including its nonfatal generic diagnostics under every input policy.

Available source-authored labels MUST be preserved under the existing rules even when their text cannot supply a usable IRI name. DirectKG MUST NOT independently invent a label for an unnamed literal. A value successfully preserved through this fallback MUST count as successfully transformed for enumeration membership, `owl:oneOf`, and `owl:AllDifferent`; a fallback alone MUST NOT make its value list incomplete.

These rules do not authorize reinterpretation or silent omission of unnamed literals.

### DK-IRI-09 — Source-ID annotations (RD-28 / ODI-CONTROLS)

Under `--iri-strategy name`, DirectKG MUST, by default, emit one source-ID `dcterms:identifier` annotation on each successfully generated eligible resource:

| Generated resource | Designated source identifier |
|---|---|
| Local class or datatype resource | Corresponding source class/datatype element ID |
| Enumeration-value individual | Source literal ID |
| Attribute property | Source attribute ID |
| Primary relation property | Target association-end ID |
| Named inverse property | Source association-end ID |

Using DK-IRI-04's resource-specific source-ID fallback in name mode does not switch the configured strategy or remove this rule's default identifier-annotation requirement.

The identifier MUST be preserved as an untagged string, without normalization, IRI escaping, or application of `--language`. Normal RDF serialization escaping MUST preserve its lexical content.

**Example (non-normative):**

```turtle
:Person dcterms:identifier "A3Jb3OGFS_j2pBF8" .
```

Under `--iri-strategy id`, DirectKG MUST NOT emit `dcterms:identifier` solely for RD-28 traceability. The accepted IRI construction already incorporates the designated source ID. Default identifier preservation therefore applies only to the additional annotations under the `name` strategy.

The boolean `--omit-identifiers` flag specified in §15 MUST suppress only the source-ID annotations introduced by this rule. It MUST be accepted with either IRI strategy; under `id`, it is a valid no-op.

| IRI strategy | Default | With `--omit-identifiers` |
|---|---|---|
| `name` | Emit RD-28 identifier annotations | Omit RD-28 identifier annotations |
| `id` | Emit no RD-28 identifier annotations | Same result; the flag has no effect |

The project-name mapping under DK-GEN-08 MUST NOT introduce a project-ID annotation under RD-28.

The control MUST NOT change IRI construction, the selected IRI strategy, internal source IDs, diagnostics, or other identifier-related behavior. It MUST NOT suppress identifier annotations established independently of RD-28.

DirectKG MUST NOT additionally attach the enclosing association ID to generated relation properties under this rule. DirectKG MUST NOT create resources solely to preserve source IDs. Anonymous restrictions, omitted packages, diagrams, diagramming information, deliberately discarded instantiation-association information, and other resources outside the transformation scope MUST NOT receive identifier annotations solely for RD-28.

Existing IRI construction, collision handling, relation-direction identity rules under DK-IRI-06, and diagnostics MUST remain unchanged.

**Rationale (non-normative):** Preserving designated source IDs supports traceability when name-based IRIs change, while allowing users to omit the additional annotations.

### DK-IRI-10 — Deterministic multilingual naming (RD-27, option C)

This rule specifies lexical selection from supported `languageString` fields when names or role names supply IRI naming components or generated lexical naming candidates. Plain-string names retain their existing treatment. For supported multilingual datatype names, the same selector also supplies the original source text used for primitive recognition under DK-DAT-02 (RD-27, option A).

For a naming field represented as a `languageString`, DirectKG MUST consider the values that yield a nonempty naming candidate under DK-IRI-03's normalization before collision handling. It MUST select the first value under this ordering:

1. Compare language keys lexicographically after converting ASCII uppercase letters to lowercase. The empty key sorts first.
2. If language keys compare equally, compare their original text values lexicographically by Unicode code points.
3. Identical text values require no further tie-break.

DirectKG MUST use the selected original text as input to the applicable naming rules. Existing field precedence, normalization, synthesis, and collision handling MUST continue to apply. This selection also applies to lexical candidates used for generated primary-relation fallback labels under either IRI strategy. Such labels remain based on the applicable lexical candidate before IRI-specific processing, as required by DK-LBL-01. ID-based IRI construction remains unchanged.

Selection MUST use the original source language keys. Neither `--language`, its equivalent Python control, nor `Project.languages` MUST select or reorder naming candidates. Their accepted literal-language behavior remains unchanged. DirectKG MUST continue preserving all applicable source-authored labels under DK-LBL-01–02; selecting one naming input does not discard other localized labels.

For inverse-generation purposes, a multilingual role MUST count as present when any of its values contains a non-whitespace character. Successful ASCII normalization MUST NOT be an additional condition for inverse eligibility. Existing inverse-generation modes and other eligibility conditions remain applicable.

When no naming candidate is usable, DirectKG MUST apply the applicable fallback and diagnostic rules for the affected resource type, including DK-IRI-04's generic source-backed-resource policy. This lexical-selection rule itself establishes no additional fallback for other cases whose treatment remains unspecified.

Multiple localized values alone MUST NOT introduce an additional diagnostic. Other applicable diagnostics remain unchanged. This rule introduces no additional configuration control.

**Rationale and examples (non-normative):** The fixed ordering avoids dependence on JSON object order or an implicit language preference.

For a class name represented as `{"nl": "Persoon", "en": "Person"}`, the selected naming input is `Person`, regardless of key order. Applicable labels retain both source values under the existing language rules.

Adding a usable translation under an earlier-sorting key can change a name-based IRI. The accepted ID strategy continues to provide identity based on source identifiers.


## 14. Validation, diagnostics, and loss reporting

### DK-DIAG-01 — Established diagnostics

Cardinality-output descriptions in this table are subject to DK-REL-07's mode-specific constraint treatment; input-error and recovery diagnostics retain their established behavior.

For duplicate source-element IDs within §3.4's scope, DK-DIAG-05 requires abortion under every input policy; general `best-effort` recovery entries below do not override that rule.

| Condition | Required behavior | Fatal? |
|---|---|---:|
| Base IRI omitted | Warning; use placeholder base under DK-IRI-01 | No |
| Supplied-base or ontology-version IRI validation fails under DK-IRI-01 | Configuration rejection before conversion; CLI reports a configuration error and exits `2`; Python signals the error programmatically; no ontology, transformation outcome, or conversion-diagnostics report | Rejected before conversion under every input policy |
| Ontology version IRI input is absent | No `owl:versionIRI` statement and no diagnostic solely for absence under DK-IRI-01 (RD-05, Option B) | No solely for absence |
| Absent, null, or empty top-level project name | No ontology label and no diagnostic solely for this condition under DK-GEN-08 | No solely for this condition |
| Unnamed or unusably named class in name mode | Warning; use synthetic IRI | No |
| Unnamed source element in ID mode, outside cases governed by DK-IRI-04's generic policy | Existing WARNING and type-specific diagnostics remain applicable; ID-based IRI remains usable | No |
| Name mode requires DK-IRI-04's generic source-ID fallback because no usable name-based candidate is available | WARNING identifying the affected element and generated IRI; existing type-specific rules retain priority | No under every input policy |
| ID mode and the name is absent, null, empty, or whitespace-only in a case governed by DK-IRI-04's generic policy | INFO identifying the affected element and missing-name condition; existing type-specific diagnostic rules remain unchanged | No under every input policy |
| Ordinary designated source-ID use in ID mode in a case governed by DK-IRI-04's generic policy | No diagnostic solely for using that ID | No solely for using that ID |
| Owner/source qualification using the classifier's DK-IRI-04 fallback candidate under DK-PROP-02 | No additional diagnostic solely because this qualification rule is used; existing missing-name, fallback, and input diagnostics remain applicable | No additional fatality solely for qualification |
| Attribute typed by `void` | Warning; omit datatype mapping/range | No |
| Unnamed ordinary relation using target-role or source-target fallback | Warning | No |
| Successful ordinary stereotype-derived name | No diagnostic solely for successful naming; other applicable diagnostics retain their established conditions | No solely for successful naming |
| Absence of an RDF origin marker for primary-relation fallback labels | No diagnostic or configuration control solely for that absence under DK-LBL-01 (RD-26, option A); existing naming and other applicable diagnostics remain unchanged | No solely for this condition |
| Multiple localized naming values alone | No additional diagnostic under DK-IRI-10; other applicable diagnostics remain unchanged | No solely for this condition |
| Multilingual primitive recognition under DK-DAT-02 | No additional diagnostic or multilingual-conflict handling; existing naming warnings, `void` warnings, and input errors remain applicable | No additional fatality solely for multilingual primitive recognition |
| Multiple applicable project/high-level languages for supported source-authored text without an explicit local language or user override | Leave the value untagged; nonfatal WARNING under DK-DIAG-19; avoid unnecessary repetition for individual literals | No |
| Absent, null, or empty supported source description, including `Project.description` | No description annotation or diagnostic solely for this condition under DK-LBL-02 | No solely for this condition |
| `isOrdered: true` occurrence preserved under DK-PROP-05 | Required INFO for each preserved occurrence under DK-DIAG-18 identifies the source attribute or relation end and explains that ordering is documented but value order is not represented; no warning solely for this limitation | No solely for this limitation |
| `isOrdered: false`, absent, or null | No ordering comment or ordering-loss INFO under DK-PROP-05 | No solely for this condition |
| Explicitly supplied, recognized `begin` or `end` property stereotype preserved under DK-PROP-06 (RD-18) | Preserve the declaration through an English comment at the specified generated property; no runtime diagnostic solely for this comment-based preservation; existing diagnostics retain their established conditions | No solely for this preservation |
| `isExtensional: true` | Required INFO under DK-DIAG-17 identifies the source class and explains annotation preservation without enforcement of essential-parthood semantics by this mapping; no warning solely for this limitation | No solely for this limitation |
| `isExtensional: false` | No diagnostic solely because of that value under DK-CLS-01 (RD-21) | No solely for that value |
| `isDerived: true` with its corresponding derived-status comment generated under DK-GEN-05 | Required INFO under DK-DIAG-16 identifies the source element and explains that annotation preservation does not itself supply a derivation rule; MUST NOT imply omission of an explicit derivation mapping actually applied; no warning solely for this limitation | No solely for this limitation |
| `isDerived: false`, or a derived-status flag with no eligible local annotation target | No diagnostic solely because of that value or absence of a target under DK-GEN-05; independently required diagnostics remain applicable | No solely for that condition |
| `abstract` stereotype or explicit boolean `isAbstract` declaration preserved through comments under RD-19 | Required INFO under DK-DIAG-15 explains annotation preservation without additional OWL logical enforcement; existing stereotype-disjointness remains applicable; expose and export under DK-DIAG-04; no warning or error solely for this expressivity limitation | No, solely for this expressivity limitation |
| Singleton class or relation completeness applied under DK-CLS-08 or DK-REL-20 | Required INFO under DK-DIAG-14 identifies the set and corresponding general and specific elements and explains extensional equivalence with distinct identifiers; include in enabled JSON diagnostics export; no warning or error solely for this equivalence | No under any input policy |
| Singleton membership without application of completeness, or one survivor after partial failure of a larger set | No singleton-completeness INFO solely for this condition; membership alone produces no warning; partial failure MUST NOT trigger singleton completeness and retains its existing structural diagnostics | No additional fatality solely for membership or survivor count |
| Either named inverse is absent for singleton relation completeness | Omit the reverse inverse-specialization axiom without a warning under DK-REL-20; do not generate an inverse solely for completeness | No solely for this omission |
| Generalization set with an explicitly empty `generalizations` array | Structural error under DK-DIAG-12; report an error and abort under `strict` or `tolerant`; under `best-effort`, report an error, omit the set's contribution, and continue with other transformable input | Yes under `strict` and `tolerant`; `best-effort` continues with error severity retained |
| Unresolved member reference or failed member transformation in a class generalization set | Error; under `strict` or `tolerant`, abort; under `best-effort`, apply DK-CLS-09 by omitting coverage while preserving applicable pairwise disjointness and independent mappings | Yes under `strict` and `tolerant`; `best-effort` continues with error severity retained |
| Enumeration `literals` field is null, absent, or explicitly empty | Warning that no enumeration values were available and closure was omitted; retain the enumeration class and independent mappings under DK-CLS-11 and DK-DIAG-13 | No under any input policy, including `strict` |
| Malformed enumeration value list or untransformable supplied value | Error; under `strict` or `tolerant`, abort; under `best-effort`, preserve successfully transformable information under DK-CLS-11 and DK-DIAG-13 | Yes under `strict` and `tolerant`; `best-effort` continues with error severity retained |
| Incomplete enumeration transformation leaves multiple, one, or zero surviving values | No additional diagnostic solely because of the survivor count; existing transformation errors report failed values | No additional fatality solely for the survivor count |
| Successful material relator-derived name | Information message SHOULD be emitted; no warning | No |
| Material semantic name unavailable | Warning; use source-target fallback | No |
| Intentional absence of a separate representation for a covered material–relator or material–mode derivation | No warning or error solely for this absence; other applicable diagnostics remain under DK-DIAG-08 | No solely for this absence under any input policy |
| Either valid endpoint order of a supported material–relator or material–mode derivation under DK-REL-08 | No warning or error solely because of the order | No under any input policy solely for the order |
| Multiple matching mode-grounded material chain components or complete patterns | Omit the affected chain and issue a nonfatal chain-ambiguity diagnostic identifying the material relation and ambiguity under DK-REL-07 | No solely for this ambiguity under any input policy |
| Same-class material relation grounded in a relator or mode, with either chain-generating mode selected | Omit the chain and issue a nonfatal chain-ambiguity diagnostic identifying the material relation and explaining the unresolved assignment of its source and target occurrences to grounding roles under DK-REL-07 | No under any input policy, including `strict`, solely for this ambiguity |
| Same-class grounded material relation with `--material-property-chains none` selected | No chain and no warning solely because its endpoints resolve to the same classifier identifier under DK-REL-07 | No solely for this condition |
| Recognized comparative–quality derivation under DK-REL-18 | Nonfatal unsupported-semantics diagnostic identifying connector and comparative relation and, where available, quality; ordinary comparative-property mapping continues | No under any input policy, including `strict`, solely for this limitation |
| Structurally resolved binary relation with a relation-valued endpoint and no accepted mapping | Omit the connector's output under DK-REL-17 (RD-16); warn identifying the connector and mapping limitation; retain independent endpoint transformations | No under any input policy, including `strict`, solely for this limitation |
| Null, malformed, or unresolved endpoint on a relation-valued connector | Structural error under DK-DIAG-03 and DK-DIAG-05; do not treat as the defined unsupported-pattern fallback | Input-policy-dependent |
| Multiple matching mediations on either participant side prevent unique chain correspondence | Warning identifying material relation and ambiguity; omit affected chain under DK-REL-07 | No under any input policy solely for this ambiguity |
| At least one material-property chain emitted under either chain-generating mode | Mode-specific compatibility notice under DK-DIAG-07, even when no cardinality or property-disjointness axiom conflicts; omission mode reports the applied policy and categories actually omitted, where applicable, with affected-source identification under existing rules; preservation mode explains preservation and possible OWL 2 DL incompatibility | No |
| Material-property-chain mode `none` | No material chains; no DK-DIAG-07 solely because chain generation is disabled | No solely for this mode |
| Deliberately unmapped applicable relation stereotype | Warning; use weaker fallback where transformation is otherwise defined. The `historicalDependence` boundary under DK-REL-01 retains this warning whenever its established condition applies and introduces no warning-suppression exception. | No |
| Expected inverse omission under `informed` or `named` | No diagnostic or element report | No |
| Either named inverse is absent under the selected inverse-generation mode for a mapped explicit relation generalization | Omit the additional inverse-specialization axiom without a warning under DK-INV-12 | No solely for this omission |
| Either named inverse is absent for a primary-property pair disjoint under DK-REL-15 | Omit that inverse-disjointness pair without a warning; do not force inverse generation | No solely for this omission |
| Structurally processable UML Property `redefines` reference transformed under DK-PROP-03 (RD-14) | No runtime warning solely because redefinition is mapped as property inclusion; document the partial translation | No solely for this mapping |
| Unresolved UML Property subsetting or redefinition reference, or failed required underlying property transformation | Apply the existing structural-error and input-policy rules, particularly DK-DIAG-05 | Policy-dependent |
| Relation generalization set with `isComplete: true` and at least two distinct specific relations | Warning identifying the set and explaining that relation-set coverage is not represented; generate no completeness axiom or substitute validation constraint under DK-REL-16 | No under any input policy, including `strict`, solely for this limitation |
| Relation generalization set with `isComplete: false` | No completeness axiom and no warning solely because of that flag under DK-REL-16 | No solely for this flag |
| Unbounded relation-end multiplicity accepted under DK-REL-12 | No warning or error solely because it is unbounded | No solely for being unbounded |
| Explicit JSON `cardinality: null` on a supported attribute or ordinary binary relation end | No cardinality restriction or default multiplicity; continue all other applicable mappings under DK-ATT-03 and DK-REL-13; no warning or error solely for this value | No solely for this value under any input policy |
| Absent `cardinality` field on a supported attribute or ordinary binary relation end | Warning identifying the affected property or relation end; no cardinality restriction or default multiplicity; continue all other applicable mappings under DK-DIAG-09 | No solely for field absence under any input policy, including `strict` |
| Untranslatable multiplicity or bound on a supported attribute or ordinary binary relation end | Error under every input policy; partial-bound recovery in `best-effort` follows DK-DIAG-10 | Yes under `strict` and `tolerant`; `best-effort` MAY continue under DK-DIAG-10 |
| Nonnegative integer multiplicity bounds with lower bound greater than upper bound | Generate both minimum and maximum restrictions under §3.4 (RD-11), subject to DK-REL-07's targeted mode-specific omission; no warning or error solely for the contradiction | No solely for this contradiction under any input policy |
| Cardinality lexical normalization alone under DK-DIAG-11 | No diagnostic | No |
| Incorrect JSON cardinality type, blank string, or ambiguous malformed cardinality expression | Error; no automatic type conversion or notation repair; `best-effort` preserves independently transformable information under DK-DIAG-11 | Yes under `strict` and `tolerant`; applicable recovery under `best-effort` |
| Discarded `«instantiation»` association data | One consolidated warning identifying the source association ID, available type, discarded-information categories, and output effect without copying discarded values under DK-INS-02; mirror the produced warning in JSON when enabled | No by itself |
| Omission of package, diagram, or diagramming information under DK-GEN-06 | No diagnostic solely for omission; intentional scope boundary, not unsupported input | No solely for omission |
| Recognized omission of custom `propertyAssignments` under DK-GEN-07 | No diagnostic solely for presence or omission; no unrecognized-information warning or error solely for recognized omission | No solely for recognized omission |
| Recognized omission of `restrictedTo` under RD-22 | No INFO merely for presence or omission; no unrecognized-information warning or error solely for this omission under any input policy; existing structural-error handling remains applicable | No solely for recognized omission |
| Unrecognized input information other than stereotypes | Severity and continuation follow DK-DIAG-05 | Input-policy-dependent |
| Missing stereotype accepted by the selected stereotype policy | No warning solely for absence; other applicable diagnostics remain in effect | No solely for absence |
| Supplied, unrecognized stereotype accepted under `allow-custom` | Warning; apply DK-DIAG-06 | No solely for that stereotype |
| Stereotype condition rejected by the selected stereotype policy | Error; abort conversion under DK-DIAG-06 | Yes, regardless of input policy |
| Missing or invalid source identifier within §3.4's existing identity/reference scope | Apply §3.4's minimal opaque identifier definitions and the existing structural-error policies under DK-DIAG-05; no replacement identifier | Governed by the existing structural-error policies; no additional recovery established |
| Duplicate declaration ID within §3.4's scope | ERROR identifies the duplicated ID, available competing-declaration location information, and abort under DK-DIAG-05; selecting, merging, or assigning replacement IDs is prohibited even for identical declaration contents | Yes under every input policy, including `best-effort` |
| Repeated reference objects identifying one declaration | MUST NOT be treated as duplicate declarations under §3.4 | No duplicate-ID failure solely for the repeated references |
| Structurally unprocessable source | Error; continuation follows DK-DIAG-05 | Policy-dependent; failure preventing meaningful document processing always aborts |
| Requested ontology file cannot be created or written after successful ontology serialization and construction of any required provenance | ERROR identifies destination, available failure reason, and failed delivery under DK-DIAG-04; CLI code `6`, subject to diagnostics-file code `4`; retain diagnostic access and attempt requested CLI JSON export | No transformation abort; established outcome unchanged under every input policy |
| Collision after injective ID escaping | Exceptional; do not merge | Exact behavior not specified |

### DK-DIAG-02 — Semantically questionable input

In every input and stereotype policy, DirectKG does not validate source OntoUML semantics. It does not validate classifier orders, stereotype appropriateness, higher-order conflicts, or output consistency. It emits every applicable higher-order assertion from transformable source structures, even if the resulting ontology is inconsistent.

Under DK-PROP-03 (RD-14), structurally processable UML Property subsetting and redefinition references likewise do not undergo owner, endpoint, type, property-kind, or other UML semantic-compatibility checks.

DK-REL-01's per-axiom OWL 2 DL compatibility assessment for the five RD-17 additions does not introduce source-semantic validation, consistency checking, or source-model repair. It does not require overall OWL 2 DL conformance of the existing ontology.

### DK-DIAG-03 — Failed relations

A relation undergoing directional-property generation requires resolvable source and target classifiers before either directional property can be generated. For such a relation, a missing or invalid association-end ID, or a null or unresolved end `propertyType`, invokes established error diagnostics and neither the direct nor inverse property is generated in any input policy. Whether conversion aborts or continues with other output is governed by DK-DIAG-05.

The missing and invalid association-end ID conditions in this rule use §3.4's minimal opaque identifier definitions (RD-02, Alternative A).

An association-end ID can be valid even when its `propertyType` is null; the relation remains untransformable because its classifier is unresolved, not because its ID is absent. Recognized material–relator and material–mode derivations do not undergo directional-property generation; DK-DIAG-08 preserves diagnostics for malformed or unresolved source data without treating intentional non-representation as an error. A structurally resolved endpoint typed by a source `Relation` follows DK-REL-08, DK-REL-18, or DK-REL-17, as applicable. Null, malformed, or unresolved endpoints on these connectors remain structural failures, not intentionally unsupported resolved patterns.

For supported ordinary binary relation ends with untranslatable multiplicities or bounds, DK-DIAG-10 requires preservation of the affected property and all independently applicable mappings in `best-effort`, including restrictions from a valid opposite-end multiplicity. The endpoint-processing requirements above remain applicable.

### DK-DIAG-04 — Diagnostic format and persistent delivery (RD-04 / ODI-CONTROLS)

Where content requirements are stated, diagnostics SHOULD identify the relevant source element and reason. DirectKG MUST support exporting transformation diagnostics to a persistent, machine-readable JSON file through the CLI control `--diagnostics-file PATH` in §15, accepting the complete user-specified output file path. When this option is absent, the CLI MUST NOT create a diagnostics file. This export is additional to normal console diagnostics; enabling it MUST NOT suppress or replace them, and console diagnostics MUST remain available subject to the selected console threshold below.

Rejection of an invalid supplied base or ontology version IRI under DK-IRI-01 occurs before conversion and MUST NOT produce a conversion-diagnostics report, including when `--diagnostics-file PATH` was supplied. The diagnostic-delivery rules for conversions that run remain unchanged.

When `--diagnostics-file PATH` is provided, DirectKG MUST write the transformation diagnostics produced during that conversion to the specified JSON file. The file is a diagnostic mirror: it MUST represent every diagnostic actually produced, including produced informational or compatibility notices, warnings, and errors. It MUST include all produced warnings and errors concerning source information omitted, unsupported, invalid, ignored, approximated, or otherwise not preserved in the generated OWL output.

When the CLI is invoked with `--diagnostics-file PATH`, DirectKG MUST attempt to export every diagnostic produced before termination even when conversion aborts under an accepted input policy. This requirement includes abortion for duplicate source-element IDs under §3.4 and DK-DIAG-05. Failures to create or write the requested file are governed by the diagnostics-delivery failure requirements below.

The Python library MUST provide structured programmatic access to every diagnostic actually produced during a conversion, preserving its severity, meaning, and applicable source information. This access MUST remain available when conversion aborts under an accepted input policy, covering all diagnostics produced before termination.

The Python library MUST provide a separate, explicitly invoked operation to export those diagnostics to a caller-specified JSON file. This operation MUST use the same report schema and diagnostic-content rules as the CLI diagnostics export, including the diagnostic-mirror requirements in this rule. Python conversion MUST NOT write a diagnostics file automatically; persistence is requested through the separate export operation.

Accessing or exporting diagnostics MUST NOT independently create additional transformation diagnostics, change their severity or meaning, alter whether conversion continues or aborts, or change output eligibility. Existing rules requiring no diagnostic remain applicable.

The INFO diagnostic required whenever class or relation singleton completeness is applied under DK-DIAG-14 MUST be included when persistent JSON diagnostics export is enabled. The expressivity-loss INFO required by DK-DIAG-15 for comment preservation of `abstract` or explicit boolean `isAbstract` declarations MUST be included wherever produced diagnostics are exposed or exported under these delivery rules.

The persistent export MUST NOT independently create diagnostics for every known limitation or information loss documented by this specification. Rules that intentionally require no diagnostic remain in force and do not become reportable merely because export is enabled. The DK-INS-02 warning is a produced diagnostic and MUST be included in the JSON mirror, observing DK-INS-02's boundary between source-locator and discarded-value content. Its console and JSON forms MAY differ in presentation but MUST represent the same underlying diagnostic event.

Each exported diagnostic SHOULD contain sufficient structured information to identify what happened and, where applicable, trace it to the relevant source element. As applicable, this information includes severity, diagnostic code, source element identifier, source element type, human-readable message, and effect on the generated output. This specification does not define the exact diagnostic identifiers, JSON member names, required-field matrix, aggregation format, or report schema.

The Python API and, when exported, the shared JSON diagnostics report MUST expose exactly one transformation outcome for each conversion, using the outcome names and classification defined in DK-DIAG-05: `completed`, `completed-with-errors`, or `aborted`. This applies to reports exported through either the CLI or Python. Exposing the outcome MUST NOT itself introduce additional diagnostics. JSON member names and Python representations remain unspecified.

The INFO diagnostics produced for `isDerived: true` under DK-DIAG-16 and `isExtensional: true` under DK-DIAG-17 MUST be exposed and exported under these diagnostic-delivery rules.

Provenance-sidecar delivery errors under DK-GEN-10 MUST be reported through console and programmatic diagnostics and included in the requested diagnostics file. DirectKG MUST attempt that file delivery after recording the sidecar failure. These delivery errors MUST NOT change the transformation outcome.

#### Ontology-file creation and write failures (RD-04, option A)

After successful ontology serialization and construction of any required provenance, failure to create or write the requested ontology file MUST produce an ERROR identifying the destination, available failure reason, and failed delivery. This applies independently of `--input-policy`.

The delivery failure MUST NOT change the established transformation outcome (`completed` or `completed-with-errors`), modify the generated graph, or change the requested provenance mode.

The CLI MUST report the failure through console diagnostics. Python MUST expose it programmatically, with produced diagnostics remaining accessible. Requested CLI JSON diagnostics export MUST still be attempted after recording the failure.

The CLI MUST use exit code `6` for this ontology-file delivery failure. Diagnostic-file delivery failure (`4`) MUST take precedence over `6`; `6` MUST take precedence over `0`, `1`, and `5` when applicable. Existing invalid-invocation and transformation-abort rules remain unchanged.

A failed write MUST NOT leave a partial ontology file presented as a valid result. If an older ontology file remains at the destination, the failure report MUST state that it was not updated for the current execution.

The provenance-sidecar delivery prerequisite is specified in DK-GEN-10.

**Rationale (non-normative):** A dedicated code distinguishes failure to deliver the main ontology artifact from provenance-sidecar failure accompanying a successfully written ontology. Delivery failure remains separate from transformation success.

#### Console severity threshold (RD-04 / CONSOLE-LEVEL)

The CLI MUST provide `--console-level {info,warning,error}`, defaulting to `info`. The selected threshold MUST determine which produced diagnostics are displayed on the console:

| Value | Diagnostics displayed |
|---|---|
| `info` | INFO, WARNING, and ERROR |
| `warning` | WARNING and ERROR |
| `error` | ERROR |

Filtering MUST affect console presentation only. It MUST NOT change diagnostic production, collection, severity, or meaning; transformation behavior; continuation or abortion; transformation outcome; ontology-output eligibility; or exit-code selection.

CLI and Python JSON diagnostic exports MUST include every produced diagnostic, including diagnostics hidden from the console. Python structured diagnostic access MUST likewise remain complete. Existing export and access requirements, including availability after abortion, remain unchanged.

Selecting a console threshold MUST NOT introduce additional diagnostic events. Existing requirements governing when diagnostics are produced remain applicable. Console-display requirements in this specification are subject to this threshold; INFO and WARNING may be hidden from the console without being suppressed from collection or export.

**Rationale and example (non-normative):** Allows quieter console output while retaining complete diagnostics. The default preserves the existing console behavior. With `--console-level warning`, a produced INFO diagnostic remains available through Python and any requested JSON export, but is not displayed on the console.

#### Diagnostics-delivery failures (RD-04)

Failure to create or write a requested diagnostics file MUST be explicitly reported as a diagnostics-delivery failure, distinct from transformation diagnostics.

- On the CLI, this failure MUST produce exit code `4` under §15 and a console error identifying the requested destination and the available failure reason.
- In Python, the separate diagnostics-export operation MUST signal failure programmatically. Python callers MUST retain access to the transformation diagnostics after an export failure.

A diagnostics-delivery failure MUST NOT change the conversion's transformation outcome, diagnostic severities, or ontology-output eligibility. The `completed` and `completed-with-errors` outcomes remain eligible for ontology delivery, including permitted partial output from `best-effort`; the `aborted` outcome prohibits ontology delivery under DK-DIAG-05. Diagnostics-delivery failure MUST remain separate from the transformation outcome.

If conversion has already aborted and the subsequent CLI diagnostics export also fails, both failures MUST remain visible. The report-write failure MUST NOT replace or conceal the transformation diagnostics.

CLI exit code `4` MUST take precedence over transformation codes `0`, `1`, and `3`, provenance-sidecar delivery code `5`, and ontology-file delivery code `6`, under §15; the underlying transformation outcome and its diagnostics MUST remain unchanged and available through the applicable diagnostic-access and export mechanisms, with console presentation subject to the selected threshold. The Python exception or result mechanism remains unspecified. These requirements do not require recovery from an unwritable destination or prescribe file-writing internals.

**Rationale (non-normative):** Failure to save a requested report must be visible to users and automation, but does not invalidate an otherwise completed transformation. Ontology delivery and diagnostics-file delivery therefore retain distinct outcomes.

### DK-DIAG-05 — Configurable input handling policies (RD-02 / RD-04)

Validation and rejection of supplied base and ontology version IRIs under DK-IRI-01 occur before conversion and apply under `strict`, `tolerant`, and `best-effort`. Such rejection starts no conversion and produces no ontology, transformation outcome, or conversion-diagnostics report. CLI configuration-error reporting uses exit code `2`; Python signals the configuration error programmatically. The conversion policies and outcomes below retain their existing behavior for conversions that run.

Failure to construct required provenance under DK-GEN-10 MUST produce an ERROR and the `aborted` outcome before ontology delivery, independently of input policy. Optional enrichment unavailability and accepted provenance exclusions do not, by themselves, trigger this abort. Diagnostics remain accessible, and requested diagnostics-file delivery MUST still be attempted under DK-DIAG-04.

External metadata validation is limited to the selected subset under DK-GEN-09. Invalid selected values follow its accepted input-policy pattern; ignored fields MUST NOT trigger field-validation diagnostics. Whole-file metadata failures follow DK-GEN-09: ERROR and abort under `strict` or `tolerant`; ERROR, omit external metadata, and continue under `best-effort`. Provenance-sidecar delivery failures follow DK-GEN-10, remain separate from transformation outcomes, and use code `5` subject to §15's delivery-failure precedence.

Ontology-file creation and write failures after successful ontology serialization and construction of any required provenance follow DK-DIAG-04 and §15 independently of `--input-policy`. These failures MUST NOT change an established `completed` or `completed-with-errors` transformation outcome.

The intentional omissions in DK-GEN-06 and DK-GEN-07 MUST NOT themselves trigger unsupported- or unrecognized-input diagnostics. Existing structural-input rules remain unchanged.

Within §3.4's existing identity/reference scope, missing and invalid source identifiers as defined there MUST follow the existing structural-error policies below. The clarification of valid/usable identifiers in RD-02, Alternative A establishes no additional dependent-output recovery; the mandatory-abortion rule for duplicate declaration IDs remains unchanged.

The input policies MUST behave as follows, subject to RD-03 (DK-DIAG-06), which exclusively governs stereotype acceptance and rejection. The duplicate-source-element-ID rule below requires abortion under every input policy. `restrictedTo` is recognized supported input that is omitted under DK-CLS-01 (RD-22); its recognized omission MUST NOT itself trigger an unrecognized-information warning or error under any input policy. Other existing handling of structurally invalid input remains unchanged:

| Situation | `strict` | `tolerant` | `best-effort` |
|---|---|---|---|
| Unrecognized input information other than stereotypes | Report an error and abort the conversion | Warn and continue with recognized information | Warn and continue with recognized information |
| Recognized information that cannot be transformed because of invalid values or unresolved references | Report an error and abort the conversion | Report an error and abort the conversion | Report the error, omit affected output, and continue where possible |
| Failure preventing meaningful processing of the document | Report an error and abort the conversion | Report an error and abort the conversion | Report an error and abort the conversion |
| Duplicate declaration ID within the scope defined in §3.4 | Report an ERROR and abort the conversion | Report an ERROR and abort the conversion | Report an ERROR and abort the conversion |

Structural errors MUST retain error severity in `best-effort`. Subject to the duplicate-ID abort rule below, this policy permits continuation and, when conversion completes, delivery of partial output; it does not downgrade structural errors to warnings. DK-DIAG-10 specifies partial recovery of untranslatable multiplicity bounds for supported attributes and ordinary binary relation ends, preserving independently valid numeric bounds without weakening error severity. DK-DIAG-11 establishes cardinality parsing and limited lexical normalization. The input policies are unchanged; `strict` and `tolerant` intentionally have identical outcomes for these multiplicity cases.

When conversion aborts under an accepted input policy, DirectKG MUST NOT deliver the ontology accumulated during that conversion through either the CLI or the Python API. A `best-effort` conversion that completes despite recoverable errors remains eligible to deliver partial ontology output under the existing transformation and recovery rules. The presence of error diagnostics alone MUST NOT be treated as an abort. These delivery rules do not change the existing rules determining when conversion continues or aborts. A diagnostics-delivery failure under DK-DIAG-04 MUST NOT change the transformation outcome, diagnostic severities, or this ontology-output eligibility.

**Rationale (non-normative):** An aborted graph may reflect where processing stopped rather than a completed application of recovery rules. Suppressing it distinguishes an aborted conversion from a completed `best-effort` conversion that legitimately delivers partial output.

#### Fatal duplicate source-element IDs (RD-02, option A)

A duplicate declaration ID within §3.4's scope MUST produce an ERROR identifying the duplicated ID, available information locating the competing declarations, and the resulting abort. DirectKG MUST NOT resolve the conflict by selecting one declaration, merging declarations, or assigning replacement IDs. This prohibition also applies when the declarations have identical contents.

Conversion MUST abort under every input policy: `strict`, `tolerant`, and `best-effort`. This applies even when unrelated fragments could otherwise be transformed.

Existing aborted-conversion requirements under DK-DIAG-04 and §15 MUST apply:

- The transformation outcome is `aborted`.
- No ontology is delivered through either the CLI or Python interface.
- Produced diagnostics remain accessible through Python.
- Requested CLI JSON diagnostics export is attempted.
- Existing exit codes and diagnostic-delivery failure precedence remain unchanged.

For this duplicate-ID condition only, the abort requirement supersedes the usual `best-effort` omission-and-continuation behavior. Other structural-error and recovery rules remain unchanged.

#### Transformation outcomes (RD-04)

DirectKG MUST classify each conversion with exactly one of the following transformation outcomes. DK-DIAG-04 requires its exposure through the Python API and, when exported, the shared JSON diagnostics report.

| Outcome | Condition | Ontology-output eligibility |
|---|---|---|
| `completed` | Processing completes with no transformation errors. INFO and WARNING diagnostics may exist. | Eligible for delivery. |
| `completed-with-errors` | Processing completes despite one or more transformation errors under accepted recovery rules. | Eligible for delivery, including permitted partial output. |
| `aborted` | Processing terminates under an accepted abort rule. | Ontology delivery is prohibited. |

An abort MUST take precedence over the number or severity of diagnostics already produced when classifying the transformation outcome. INFO and WARNING diagnostics alone MUST NOT produce `completed-with-errors`. Existing transformation policies continue to determine recovery and abortion.

The `completed` outcome MUST NOT be interpreted as a guarantee of lossless conversion, semantic consistency, or conformance to a particular OWL profile. Diagnostics-delivery failure under DK-DIAG-04, ontology-file delivery failure within that rule's scope, and provenance-sidecar delivery failure under DK-GEN-10 MUST remain separate from the transformation outcome and MUST NOT change it. Exposing the outcome MUST NOT itself introduce additional diagnostics.

The outcome names are fixed as shown above. JSON member names and Python representations remain unspecified. The CLI exit-code mapping and its scope are specified in §15; code `1` MUST NOT suppress otherwise eligible ontology output. Invalid CLI invocation occurs before conversion starts and MUST NOT create a transformation outcome for a conversion that never ran.

**Rationale and example (non-normative):** Explicit outcomes let callers distinguish completed error recovery from abortion without deriving that distinction themselves. A transformation may be `completed` while the CLI exits unsuccessfully because a requested diagnostics file could not be written.

#### Policy interactions and recovery

Accessing diagnostics or enabling persistent JSON diagnostics export under DK-DIAG-04 MUST NOT change when a diagnostic is produced, its severity or meaning, whether conversion continues or aborts, or output eligibility, including whether partial OWL output is permitted. Python structured diagnostic access MUST remain available after a policy-driven abort for every diagnostic produced before termination, as specified in DK-DIAG-04.

The console threshold under DK-DIAG-04 affects presentation only. Filtering MUST NOT change diagnostic production, collection, severity, or meaning; transformation behavior; continuation or abortion; transformation outcome; ontology-output eligibility; or exit-code selection. Hidden diagnostics remain available through complete Python access and requested CLI or Python JSON exports, including after abortion under the existing rules.

Every policy MUST produce syntactically valid RDF whenever output is delivered. `best-effort` permits incomplete output, not invalid RDF syntax. It MUST NOT invent missing information to make a transformation possible.

The semantic-validation boundary in §3.4 and DK-DIAG-02 applies in every policy, even when the resulting ontology is inconsistent.

Existing explicitly accepted fallbacks, permitted values, and nonfatal diagnostics retain their behavior in every policy. Selecting `strict` MUST NOT automatically turn existing warnings into errors. Explicit JSON `cardinality: null` is supported under every input policy for supported attributes and ordinary binary relation ends, as specified in DK-ATT-03 and DK-REL-13. An absent `cardinality` field on these elements uses the defined warning-and-continuation fallback in DK-DIAG-09 under every input policy, including `strict`.

DK-REL-17 (RD-16) establishes a nonfatal warning and connector-omission fallback for structurally resolved binary relations with relation-valued endpoints lacking an accepted mapping. That warning MUST NOT abort conversion under any input policy, including `strict`. Null, malformed, and unresolved endpoints remain structural errors under the applicable input policy.

For recognized comparative–quality derivations, DK-REL-18 (RD-17) replaces that generic warning with its specific nonfatal unsupported-semantics diagnostic under every input policy, including `strict`. Mode-grounded chain-component ambiguity and same-class material–relator or material–mode chain ambiguity under DK-REL-07 are likewise nonfatal under every input policy. Other applicable structural errors retain their input-policy behavior.

An enumeration whose `literals` field is null, absent, or explicitly empty uses the defined warning-and-continuation fallback in DK-CLS-11 and DK-DIAG-13 under every input policy, including `strict`. Malformed enumeration value lists and untransformable supplied values remain errors: `strict` and `tolerant` abort, while `best-effort` retains error severity and continues with successfully transformable information as specified in those rules.

A generalization set with an explicitly empty `generalizations` array is a structural error governed by DK-DIAG-12: `strict` and `tolerant` abort, while `best-effort` retains error severity, omits the empty set's contribution, and continues with other transformable input.

An unresolved member reference or failed member transformation in a class generalization set is an error. Under `strict` and `tolerant`, transformation aborts. Under `best-effort`, error severity is retained and partial recovery follows DK-CLS-09: the covering axiom is omitted, applicable pairwise disjointness is retained, and independently applicable class and generalization mappings remain applicable.

The warning required by DK-REL-16 for a complete relation generalization set with two or more distinct specific relations is nonfatal under every input policy, including `strict`. All other applicable relation mappings continue.

Unrecognized information MUST NOT acquire invented transformation semantics. When continuation is permitted, recognized structure may still receive its applicable accepted transformations. A known class with an unknown stereotype is distinct from an element whose type itself is unknown. For accepted missing or unrecognized stereotypes, DK-DIAG-06 requires ordinary transformations wherever their established prerequisites hold. Other unrecognized information and structural failures remain governed by this input policy.

For DK-PROP-03 (RD-14), unresolved property references and failures of required underlying property transformations follow these existing structural-error and continuation rules. A structurally processable `redefines` reference transformed under the accepted inclusion mapping does not itself require a runtime warning.

These rules establish policy-dependent continuation, subject to the duplicate-ID abort rule above. No recovery behavior is defined beyond the explicit recovery rules in this specification. The input-policy argument and default are specified in §15.

**Non-normative rationale and examples:**

- Diagnostic severity describes the problem; the selected policy determines whether conversion stops.
- A relation with a null end `propertyType` remains untransformable. In `best-effort`, its omission can permit delivery of the usable remainder.
- An attribute with `propertyType: null` is explicitly supported by DK-ATT-01 and is not automatically invalid.
- Malformed JSON that cannot be parsed prevents transformation in every policy.

### DK-DIAG-06 — Stereotype acceptance policy (RD-03)

The stereotype policy MUST determine acceptance as follows:

| Condition | `require-known` | `allow-missing` | `allow-custom` |
|---|---|---|---|
| Missing stereotype on a class or relation | Report an error and abort conversion | Accept | Accept |
| Missing stereotype on an attribute or association end | Accept | Accept | Accept |
| Supplied, unrecognized stereotype on a class, relation, attribute, or association end | Report an error and abort conversion | Report an error and abort conversion | Accept with a warning |

An accepted missing stereotype MUST NOT produce a warning solely because it is absent. Other applicable diagnostics remain in effect.

Stereotype acceptance MUST be governed exclusively by `--stereotype-policy`. Its acceptance and rejection behavior takes precedence over `--input-policy` for missing and unrecognized stereotypes:

- `--input-policy strict` MUST NOT reject a custom stereotype accepted by `--stereotype-policy allow-custom`.
- `--input-policy best-effort` MUST NOT permit continuation after a stereotype condition rejected by the selected stereotype policy.

For an accepted missing or unrecognized stereotype, DirectKG MUST apply ordinary transformations wherever their established prerequisites hold. It MUST NOT invent stereotype-specific semantics. Other structural failures remain governed by `--input-policy`.

“Unrecognized” means that DirectKG has no established interpretation for the stereotype; it does not imply that the custom stereotype is intrinsically erroneous. Recognition MUST NOT introduce validation of whether a recognized stereotype is ontologically appropriate for its use.

A recognized stereotype whose transformation is explicitly unresolved MUST retain that unresolved status. It MUST NOT be treated as unrecognized merely to bypass the unresolved mapping.

RD-03 replaces application of RD-02's general unrecognized-input policy to unrecognized stereotypes. RD-02 continues to govern other unrecognized information and structural failures. Its semantic-validation boundary and requirement for syntactically valid RDF output remain in effect. The stereotype-policy argument and default are specified in §15.

**Non-normative rationale:** Separate policies allow users to accept custom or missing stereotypes while retaining strict handling of other input problems. Attributes and association ends commonly have no stereotype, so requiring stereotypes on classes and relations does not impose the same requirement on properties.

### DK-DIAG-07 — Material-property-chain compatibility notice (RD-17 / ODI-CONTROLS)

Whenever at least one material-property chain is emitted under either chain-generating mode, whether grounded in a relator or a mode, DirectKG MUST issue a nonfatal compatibility notice that OWL 2 DL conformance is not guaranteed. The notice MUST apply even when no cardinality or property-disjointness axiom ultimately conflicts with the emitted chain. DirectKG MUST NOT emit this notice solely because `none` disables material-property-chain generation.

Under `omit-conflicting-constraints`, the notice MUST identify that the omission policy was applied; report the categories of simplicity-dependent constraints actually omitted, where applicable; identify affected source elements as required by the existing diagnostic-content rules; and explain that removing the known material-chain conflicts does not establish a general OWL 2 DL conformance guarantee.

Under `preserve-conflicting-constraints`, the notice MUST explain that the applicable simplicity-dependent cardinality and relation-generalization-set disjointness constraints governed by DK-REL-07 were preserved and that their combination with emitted material-property chains may place the output outside OWL 2 DL. This preservation does not override the compatibility gate for the additional axioms under DK-REL-01.

Existing ambiguity, structural-error, and unsupported-semantics diagnostics remain unchanged. Documentation MUST explain that combinations with other axioms can cause reasoners to reject the ontology or disregard unsupported axioms. The notice MUST NOT imply that every property chain violates OWL 2 DL.

Documentation MUST also explain that OWL 2 DL requires simple properties in property-disjointness axioms and that chains making a property participating in an axiom under DK-REL-15 non-simple can therefore cause the output to fall outside OWL 2 DL.

### DK-DIAG-08 — Intentional non-representation of material derivations (RD-16 / RD-17)

The intentional absence of a separate representation for a material–relator or material–mode derivation connector covered by DK-REL-08 MUST NOT, by itself, trigger a warning or error under any input policy.

The two supported serialized endpoint orders MUST NOT, by themselves, trigger a warning or error. Order-independent recognition under DK-REL-08 does not repair or reverse the source.

Existing diagnostics for material-relation naming, property-chain ambiguity, and malformed or unresolved source data MUST continue to apply where their respective conditions hold. Under either chain-generating mode, this includes the nonfatal same-class ambiguity diagnostic for either recognized material grounding pattern under DK-REL-07; under `none`, same-class endpoints alone require no warning. Intentional omission of the connector's separate representation MUST NOT suppress applicable diagnostics or trigger DK-REL-17's generic unsupported-connector warning. Recognized comparative–quality derivations are governed separately by the nonfatal unsupported-semantics diagnostic in DK-REL-18.

### DK-DIAG-09 — Missing cardinality field (RD-11 / RD-02)

For supported attributes and ordinary binary relation ends, an absent `cardinality` field MUST generate no cardinality restriction. DirectKG MUST NOT substitute a default multiplicity.

DirectKG MUST emit a warning identifying the affected property or relation end and continue all other applicable mappings. This specifically defined fallback MUST apply under every input policy, including `strict`. Field absence alone MUST NOT abort transformation.

For inverse-generation eligibility, an absent cardinality MUST NOT satisfy the non-null multiplicity condition. Other accepted eligibility conditions remain applicable.

This fallback applies only when the field is absent. It does not cover present-but-invalid values, including blank strings or incorrect JSON types. The explicit-null behavior in DK-ATT-03 and DK-REL-13 remains unchanged: explicit null produces no diagnostic solely because it is null.

**Rationale (non-normative):** The fallback avoids inventing a multiplicity while identifying a departure from the expected exporter representation.

### DK-DIAG-10 — Partial recovery of untranslatable multiplicity bounds (RD-11 / RD-02)

For supported attributes and ordinary binary relation ends, an untranslatable multiplicity or bound MUST be diagnosed as an error. Under `strict` and `tolerant`, transformation MUST abort according to DK-DIAG-05 (RD-02). Under `best-effort`, processing MAY continue using the recovery rules below; diagnostic severity MUST remain error.

When lower and upper bounds can be separated unambiguously, `best-effort` MUST preserve independently valid numeric bounds as follows:

| Multiplicity | Cardinality output in `best-effort` |
|---|---|
| Untranslatable single value | No cardinality restriction |
| Both bounds untranslatable | No cardinality restriction |
| Untranslatable lower bound; valid finite upper bound `u` | Maximum-cardinality restriction with value `u` |
| Valid lower bound `l`; untranslatable upper bound | Minimum-cardinality restriction with value `l` when `l > 0`; none when `l = 0` |

Partial recovery MUST NOT guess replacement bounds or repair ambiguous notation. Under DK-DIAG-11, an empty or untranslatable bound in an interval with unambiguous lower and upper positions follows this recovery policy. An empty bound MUST NOT be interpreted as zero or unlimited. Ambiguous malformed expressions yield no cardinality restriction.

The affected property and all other independently applicable mappings MUST be preserved in `best-effort`. For relations, this includes restrictions derived from a valid opposite-end multiplicity.

Recovered restrictions remain subject to DK-REL-07's targeted mode-specific omission rule. Otherwise, recovered restrictions MUST follow the applicable accepted cardinality mapping, direction, class-constraint placement, and property-selection rules: DK-ATT-02 and DK-ATT-03 for attributes, and DK-REL-09–11 for ordinary relations.

Mixed numeric/symbolic expressions may retain their independently valid numeric bound. Contradictory intervals whose bounds are both nonnegative integers are transformable under §3.4 (RD-11) and MUST NOT be treated as untranslatable multiplicities under this recovery rule. Cardinality syntax, limited lexical normalization, and treatment of ambiguous malformed expressions are specified in DK-DIAG-11 (RD-11 / RD-02). The accepted explicit-null and missing-field behavior remains governed by DK-ATT-03, DK-REL-13, and DK-DIAG-09.

**Rationale (non-normative):** An untranslatable bound does not invalidate independently transformable information. Partial recovery preserves that information while explicitly reporting the incomplete transformation.

### DK-DIAG-11 — Cardinality syntax and limited lexical normalization (RD-11 / RD-02)

These parsing rules apply to supported attributes and ordinary binary relation ends. Explicit null and absent `cardinality` fields retain their separately accepted handling in DK-ATT-03, DK-REL-13, and DK-DIAG-09 under every input policy.

Other cardinality values MUST be JSON strings. DirectKG MUST NOT automatically convert numbers, booleans, arrays, or objects into cardinality strings.

DirectKG MUST trim surrounding whitespace from the complete string and from individual bounds. Numeric bounds MUST consist of decimal digits `0–9`. Leading zeros MUST be accepted and interpreted numerically. Signs, decimal points, and exponent notation are not accepted numeric forms.

DirectKG MUST recognize a single numeric value, standalone `*`, or an interval separated by exactly one `..` delimiter. DirectKG MUST NOT repair extra dots, repeated delimiters, commas, or colons into accepted interval notation.

When an interval's lower and upper positions are unambiguous, an empty or untranslatable bound MUST follow the partial-bound recovery policy in DK-DIAG-10. An empty bound MUST NOT be interpreted as zero or unlimited.

Lexical normalization alone MUST NOT generate a diagnostic. Untranslatable values, incorrect JSON types, blank strings, and ambiguous malformed expressions MUST produce errors. Under `strict` and `tolerant`, transformation MUST abort according to DK-DIAG-05 (RD-02). Under `best-effort`, applicable recovery MUST preserve independently transformable information; ambiguous malformed expressions yield no cardinality restriction.

Contradictory numeric bounds retain their accepted treatment in §3.4: generate both restrictions without a diagnostic solely because the lower exceeds the upper.

The three input policies remain unchanged; `strict` and `tolerant` intentionally have identical outcomes for these multiplicity cases. The accepted finite and unbounded cardinality mappings continue to apply.

**Examples (non-normative):**

| Input | Treatment |
|---|---|
| `" 01 .. 03 "` | Interpret as `1..3`; no diagnostic |
| `"1..n"` or `"1.."` | Error; `best-effort` retains minimum 1 |
| `"..3"` | Error; `best-effort` retains maximum 3 |
| `"2...*"` or `"2,,*"` | Error; no cardinality restriction recovered |
| `""`, whitespace-only text, or JSON number `1` | Error; no cardinality restriction |
| `"5..2"` | Minimum 5 and maximum 2; no diagnostic solely for the contradiction |

### DK-DIAG-12 — Empty generalization sets (RD-13 / RD-02)

DirectKG MUST treat a generalization set whose `generalizations` field is explicitly an empty array as a structural error, regardless of its completeness or disjointness flags.

The input policies in DK-DIAG-05 MUST apply as follows:

- under `strict`, DirectKG MUST report an error and abort the transformation;
- under `tolerant`, DirectKG MUST report an error and abort the transformation;
- under `best-effort`, DirectKG MUST report an error, omit the empty set's contribution, and continue transforming other transformable input.

Under `best-effort`, DirectKG MUST generate no axioms from the empty generalization set. Independently applicable mappings for other elements MUST remain applicable.

DirectKG MUST NOT infer a general classifier, invent members, or interpret the empty set as an assertion that some class has no instances.

This rule applies only when the `generalizations` field is explicitly an empty input array. Missing or malformed membership fields, unresolved references, and sets emptied by failed transformations remain outside this decision.

**Rationale (non-normative):** The element type is recognized, but its membership supplies neither classifiers to constrain nor a general classifier identifiable through member generalizations. The error concerns missing transformation structure, not semantic inconsistency.

### DK-DIAG-13 — Enumeration value-list input handling (RD-09 / RD-02)

When an enumeration's `literals` field is null, absent, or explicitly empty, DirectKG MUST warn that no enumeration values were available and enumeration closure was omitted. This defined fallback MUST be nonfatal under `strict`, `tolerant`, and `best-effort`. When enumeration-owned properties are present, the warning SHOULD clarify that those properties were not interpreted as enumeration values.

The enumeration class and independently applicable mappings MUST remain, and DK-CLS-11 governs the required omission of `owl:oneOf` and any assertion of an empty extension.

Unnamed or unusably named enumeration literals successfully preserved through DK-IRI-04's generic source-ID fallback follow that rule's nonfatal generic diagnostics under every input policy. Such a fallback alone MUST NOT make the value list incomplete or count a successfully preserved value as failed.

Malformed value lists and untransformable supplied values MUST follow the input-error policy in DK-DIAG-05:

- under `strict`, DirectKG MUST report an error and abort;
- under `tolerant`, DirectKG MUST report an error and abort;
- under `best-effort`, DirectKG MUST retain error severity and continue with successfully transformable information.

Whenever processing continues, DirectKG MUST preserve successfully generated value individuals and their enumeration-membership assertions. Closure and mutual-difference output MUST follow the completeness and generated-value-count rules in DK-CLS-10–11. DirectKG MUST NOT close an incomplete enumeration over only the surviving subset.

Existing transformation errors MUST provide the required reporting for failed values. No additional diagnostic is required solely because incomplete transformation leaves multiple, one, or zero surviving values.

### DK-DIAG-14 — INFO for singleton completeness (RD-13)

Whenever DirectKG applies singleton completeness to a class generalization set under DK-CLS-08 or a relation generalization set under DK-REL-20, it MUST emit an INFO diagnostic for that affected set. The diagnostic MUST:

- identify the affected generalization set;
- identify the corresponding general and specific class or relation; and
- explain that applying completeness to the single-member set makes the generated classes or properties extensionally equivalent, while their identifiers remain distinct.

The diagnostic MUST be informational and nonfatal under every input policy. Singleton completeness MUST NOT be treated as a warning or error solely because of this equivalence. The INFO diagnostic is required when singleton completeness is applied, not merely when a set has one member or when partial failure leaves one survivor. Singleton membership alone MUST NOT produce a warning. Existing structural-error policies and the prohibition on deriving singleton coverage from partial failure remain unchanged.

The class transformation remains DK-CLS-08's reverse subclass mapping; the relation transformation is DK-REL-20's reverse subproperty mapping. When persistent JSON diagnostics export is enabled, this INFO diagnostic MUST be included under DK-DIAG-04.

### DK-DIAG-15 — INFO for abstractness comment preservation (RD-19)

Whenever the `abstract` stereotype or an explicit boolean `isAbstract` declaration is preserved only through comments under DK-CLS-01 (RD-19), DirectKG MUST emit an INFO diagnostic indicating the expressivity limitation: the declaration is preserved as an annotation, but its meaning is not additionally enforced through OWL logical constraints. For the `abstract` stereotype, this explanation MUST NOT imply that its existing stereotype-disjointness mapping has been omitted.

This expressivity limitation MUST NOT, by itself, produce a WARNING or ERROR. The INFO diagnostic MUST be included wherever produced diagnostics are exposed or exported under DK-DIAG-04 and the accepted structured Python diagnostic-access and JSON-export rules.

### DK-DIAG-16 — INFO for derived-status annotations (RD-20, option C)

For `isDerived: true`, DirectKG MUST emit an INFO diagnostic only when the corresponding derived-status comment under DK-GEN-05 is generated. The diagnostic MUST identify the source element and explain that annotation preservation does not itself supply a derivation rule. This limitation alone MUST NOT produce a WARNING. The INFO diagnostic MUST NOT imply that an independently accepted explicit `«derivation»` mapping was omitted when it was actually applied.

DirectKG MUST NOT generate a diagnostic solely because `isDerived` is `false` or because a flag has no eligible annotation target. Independently required structural, mapping-limitation, and other diagnostics remain applicable. Produced INFO diagnostics MUST be exposed and exported under DK-DIAG-04 and the existing accepted diagnostic-delivery rules. DK-GEN-05 specifies comment placement and omission where no eligible local target exists.


### DK-DIAG-17 — INFO for extensionality annotations (RD-21)

For `isExtensional: true`, DirectKG MUST emit an INFO diagnostic identifying the source class and explaining that the declaration is preserved as an annotation, but its essential-parthood semantics are not enforced by this mapping. This limitation alone MUST NOT produce a WARNING.

For `isExtensional: false`, DirectKG MUST NOT emit a diagnostic solely because of that value. DK-CLS-01 (RD-21) governs comment preservation, and DK-DIAG-04 governs delivery of the produced INFO diagnostic.

### DK-DIAG-18 — INFO for ordering declarations (RD-23)

For each `isOrdered: true` occurrence preserved under DK-PROP-05, DirectKG MUST emit an INFO diagnostic identifying the source attribute or relation end and explaining that ordering is documented, but value order is not represented by the generated property mapping. This limitation alone MUST NOT produce a WARNING.

For `isOrdered: false`, or when the field is absent or null, DirectKG MUST NOT generate an ordering-loss INFO. DK-DIAG-04 governs delivery of the produced diagnostics. This rule does not change the diagnostic behavior of DK-PROP-04's existing read-only and aggregation mappings.

### DK-DIAG-19 — Unresolved project/high-level language assignment (RD-27)

Language declarations for this rule MUST come from the recognized carriers in DK-LBL-02; VP custom metadata does not participate.

When multiple applicable project/high-level languages are declared and a supported source-authored textual value has neither an explicit local language nor a user override, DirectKG MUST leave the value untagged and emit a nonfatal WARNING explaining that language assignment was unresolved because multiple applicable project/high-level languages were available.

The diagnostic MUST avoid unnecessary repetition for individual literals and MAY be consolidated for the affected project or conversion. Explicitly localized values and values covered by a user override do not trigger this ambiguity warning. Multiple explicitly localized values MUST NOT be treated as ambiguous merely because they use different languages.

## 15. Configuration, CLI, and Python library API

Both the CLI and the Python library MUST require a concrete OntoUML JSON input file identified by a file path for every transformation, independently of the provenance mode, under §3.2's file-only source-input requirement (RD-05). The exclusion of fileless source-input substitutes in that section applies to both interfaces. Exact Python API names and signatures remain unspecified; existing transformation-control parity, Python output, and diagnostic capabilities remain unchanged.

CLI ontology output and Python ontology-serialization capabilities MUST follow the RDF 1.1 Turtle format requirement in §3.3 (RD-04, option A). This serialization decision introduces no format-selection control. The Turtle prefix policy in §3.3 (RD-04, option A — conventional prefixes) also applies to both interfaces and introduces no prefix-configuration control.

The serialized-presentation boundary in §3.3 (RD-04, option A — serialized presentation) applies to ontology serialization through both interfaces and to provenance-sidecar serialization. It introduces no sorting or canonicalization control.

The generated ontology IRI MUST be derived from the effective entity base under DK-IRI-01 (RD-05). DirectKG MUST NOT provide a separate configuration control for choosing an ontology IRI independently of that base.

Validation and configuration rejection for supplied base and ontology version IRIs MUST follow DK-IRI-01 before conversion starts in both interfaces. Python MUST signal a rejected configuration programmatically; no particular exception class is prescribed. The CLI follows the invalid-invocation contract below.

DirectKG MUST expose the optional CLI control `--ontology-version-iri IRI` and an equivalent optional Python API control under DK-IRI-01 (RD-05, Option B). A supplied valid value adds `owl:versionIRI` to the derived ontology resource; absence adds no such statement and no diagnostic solely for absence. The ontology IRI derivation, entity IRIs, DKGM import, and DK-GEN-10 provenance rules remain unchanged. When provenance is enabled, the effective configuration MUST reflect this setting; a sidecar output checksum covers the final ontology bytes, including the version IRI statement when present.

DirectKG MUST support the argument `--input-policy` with the values `strict`, `tolerant`, and `best-effort`. The default MUST be `tolerant`. The policies are specified in DK-DIAG-05 (RD-02).

DirectKG MUST support `--stereotype-policy` with the values `require-known`, `allow-missing`, and `allow-custom`. The default MUST be `allow-custom`. Acceptance, diagnostics, and precedence over `--input-policy` are specified in DK-DIAG-06 (RD-03).

The CLI MUST expose `--inverse-properties` with the values `all`, `informed`, `named`, and `none`, defaulting to `all`. The modes retain their behavior under DK-INV-01 and govern separately named inverse properties; they MUST NOT prohibit anonymous inverse expressions required or permitted by the accepted mappings.

The CLI MUST expose `--diagnostics-file PATH`, accepting the complete user-specified output file path for a persistent JSON diagnostics file. When this option is provided for a conversion that starts, DirectKG MUST write the diagnostic mirror to the specified path under DK-DIAG-04. Supplied-base or ontology-version IRI rejection before conversion follows DK-IRI-01 and produces no conversion-diagnostics report. The CLI MUST NOT create a diagnostics file when this option is absent. Use of the option MUST leave console diagnostics available subject to the selected console threshold. When conversion aborts under an accepted input policy, DirectKG MUST still attempt to export every diagnostic produced before termination to the requested path. Requested CLI JSON diagnostics export MUST also still be attempted after recording an ontology-file delivery failure under DK-DIAG-04. DK-DIAG-04 specifies the diagnostic-content and delivery requirements, including explicit diagnostics-delivery failure reporting. Failure to create or write the requested file MUST produce CLI exit code `4` and a console error identifying the requested destination and available failure reason, without changing ontology-output eligibility. If conversion has already aborted, the export failure MUST NOT replace or conceal the transformation diagnostics.

The CLI MUST provide `--console-level {info,warning,error}`, defaulting to `info`. Console filtering follows DK-DIAG-04 and affects presentation only. All produced diagnostics MUST remain available through complete Python structured access and requested CLI or Python JSON exports, including after abortion under the existing delivery rules.

DirectKG MUST provide the three-mode CLI parameter:

```text
--material-property-chains {none,omit-conflicting-constraints,preserve-conflicting-constraints}
```

The default MUST be `none`. This parameter replaces the former boolean flag. It governs both accepted material–relator and material–mode chains. DK-REL-07 (RD-17 / ODI-CONTROLS and the accepted DK-INV-04 clarification) specifies their eligibility, construction, ambiguity handling, and mode-specific constraint treatment. Under `none`, no material chains are generated and same-class grounded material endpoints alone MUST NOT trigger a warning. Both other modes generate eligible, unambiguous chains; `omit-conflicting-constraints` applies targeted omission, while `preserve-conflicting-constraints` retains the applicable cardinality and property-disjointness mappings. DK-DIAG-07 specifies their compatibility notices. The corresponding material-property-chain control MUST also be available through the Python library under this section's semantic-parity requirements; Python spelling and representation need not match the CLI parameter.

The five additions under DK-REL-01 (RD-17) MUST follow their per-axiom compatibility gate in every material-property-chain mode, including `preserve-conflicting-constraints`. Existing mode-specific policies for established cardinality and property-disjointness mappings remain unchanged.

The `dkgm` vocabulary import and its generic chains, the source-specific bridge axioms and primary-property asymmetry in DK-REL-19, and the source-metadata comments in DK-PROP-04 are default behavior. No mereology-specific control is established for these rules. `--material-property-chains` applies only to material-relation chains under DK-REL-07; it does not control the `dkgm` vocabulary or the mapping to it.

RD-11 introduces no additional configuration argument to omit reverse-side cardinality restrictions when no named inverse property is generated; DK-REL-09 specifies the required property selection. RD-11 also introduces no configuration argument for choosing qualified restrictions; DK-REL-10 specifies the unqualified forms for supported ordinary binary class-to-class relations.

RD-12 inverse specialization follows the existing inverse-generation setting; no additional configuration argument is introduced (DK-INV-12).

DirectKG MUST expose the CLI control `--relation-labels {source-only,generated}`, with default `source-only`. The Python interface MUST expose the semantically equivalent control as `relation_labels="source-only"` or `relation_labels="generated"`, also defaulting to `"source-only"`. Both interfaces MUST expose the same values, default, and transformation semantics under DK-LBL-01 (RD-26 / ODI-CONTROLS).

DirectKG MUST provide `--language LANG`, accepting exactly one language tag, not a list. It is an explicit override, not merely a default language. The Python interface MUST expose a semantically equivalent control; both interfaces MUST implement the same override behavior under DK-LBL-02 (RD-27 / ODI-CONTROLS). This decision establishes no particular Python parameter name. Neither the override nor `Project.languages` selects or reorders naming candidates or primitive-recognition input; DK-IRI-10 and DK-DAT-02 use the original source language keys.

DirectKG MUST provide the boolean CLI flag `--omit-identifiers`. When supplied, it MUST suppress only the source-ID `dcterms:identifier` annotations introduced by DK-IRI-09 (RD-28). The Python interface MUST expose a semantically equivalent boolean control, disabled by default, with the same behavior; no Python parameter name is prescribed. The flag MUST be accepted under both IRI strategies and is a valid no-op under `id`.

DirectKG MUST expose `--metadata-file PATH` under DK-GEN-09 and `--provenance {none,embedded,sidecar}` under DK-GEN-10, with provenance defaulting to `embedded`. Python MUST expose semantically equivalent controls with the same provenance default; separate provenance MUST be available as a graph, with explicit serialization for file output.

The following transformation, diagnostic-delivery, and CLI presentation controls are established:

| Control | Status |
|---|---|
| `--metadata-file PATH` | Explicitly supplied file named `metadata.yaml`; no discovery; only the selected Catalog fields under DK-GEN-09; equivalent Python control required |
| `--provenance none\|embedded\|sidecar` | Default `embedded`; independent of descriptive metadata; sidecar placement, output-file boundary, and Python graph access under DK-GEN-10 |
| `--base-iri <IRI>` | Established; determines the effective entity base and derived ontology IRI under DK-IRI-01; supplied, effective, and derived IRIs undergo its syntactic validation before conversion; invalid supplied-base configurations are rejected under every input policy, with CLI exit code `2` and programmatic Python signaling; no independent ontology-IRI control |
| `--ontology-version-iri IRI` | Optional caller-supplied ontology version IRI under DK-IRI-01 (RD-05, Option B); equivalent optional Python control required; a supplied valid value emits `owl:versionIRI` on the derived ontology resource; absent input emits no such statement or diagnostic solely for absence; invalid values follow pre-conversion configuration rejection under every input policy; no automatic version assignment or change to ontology IRI derivation |
| `--material-property-chains none\|omit-conflicting-constraints\|preserve-conflicting-constraints` | Established by RD-17 / ODI-CONTROLS; default `none`; replaces the boolean flag; both chain-generating modes follow DK-REL-07 eligibility, construction, and ambiguity rules, with mode-specific constraint omission or preservation and DK-DIAG-07 notices; the additional axioms under DK-REL-01 retain their per-axiom compatibility gate in every mode; independent of the imported `dkgm` vocabulary and DK-REL-19 |
| `--input-policy strict\|tolerant\|best-effort` | Established by RD-02; default `tolerant`; behavior in DK-DIAG-05, subject to RD-03 stereotype-policy precedence |
| `--stereotype-policy require-known\|allow-missing\|allow-custom` | Established by RD-03; default `allow-custom`; behavior and precedence in DK-DIAG-06 |
| `--diagnostics-file PATH` | Established by RD-04 / ODI-CONTROLS; accepts the complete user-specified output file path and writes a mirror of every produced diagnostic under DK-DIAG-04; no diagnostics file when absent; export MUST be attempted even after a policy-driven abort and after recording an ontology-file delivery failure; creation or write failure produces exit code `4` and an explicit console error under DK-DIAG-04 without changing ontology-output eligibility; console diagnostics remain available subject to the selected console threshold |
| `--console-level info\|warning\|error` | Established by RD-04 / CONSOLE-LEVEL; default `info`; console presentation only under DK-DIAG-04; diagnostic collection, JSON export, Python access, transformation behavior, output eligibility, and exit-code selection remain unchanged |
| `--iri-strategy name\|id` | Established; default `name`; RD-28 identifier annotations follow DK-IRI-09 |
| `--omit-identifiers` | Established by RD-28 / ODI-CONTROLS; boolean opt-out, disabled by default; suppresses only RD-28 source-ID annotations under `name`; accepted no-op under `id`; equivalent Python boolean required, parameter name unspecified |
| `--language LANG` | Established by RD-27 / ODI-CONTROLS; exactly one language tag; overrides input language information for supported source-authored text under DK-LBL-02; equivalent Python control required, parameter name unspecified; excludes generated fallback labels |
| `--no-stereotype-relation-naming` | Established; stereotype naming otherwise enabled |
| `--relation-labels source-only\|generated` | Established by RD-26 / ODI-CONTROLS; default `source-only`; Python `relation_labels` exposes the same values and default; primary-relation label selection under DK-LBL-01 applies under either IRI strategy; RDF origin markers solely distinguishing fallback labels from source-authored labels are prohibited; absence of a marker alone adds no diagnostic or control |
| `--inverse-properties all\|informed\|named\|none` | Established by ODI-CONTROLS; controls separately named inverse properties under DK-INV-01; default `all`; does not prohibit anonymous inverse expressions in material-property chains or those required for reverse-side cardinality restrictions under DK-REL-09, property subsetting/redefinition under DK-PROP-03 (RD-14), or aligned characterization–external-dependence disjointness under DK-REL-01 (RD-17) |

### Semantic parity of transformation controls (ODI-CONTROLS)

The project MUST provide both a CLI and a Python library. Every established control affecting ontology transformation MUST be available through both interfaces. This includes the entity base, optional ontology version IRI, IRI strategy, input policy, stereotype policy, inverse-generation mode, stereotype-based relation naming, primary-relation label mode, material-property-chain mode, the user language override, the source-ID annotation opt-out, external metadata-file input, and provenance mode.

Corresponding controls MUST provide equivalent selectable behaviors and identical defaults and transformation effects. Equivalent effective configurations applied to the same supported input MUST invoke the same accepted transformation rules, regardless of interface. Existing control values, defaults, and transformation rules remain applicable.

Python parameter names and representations need not reproduce CLI spellings or flag polarity, provided they preserve the corresponding selectable behaviors, defaults, and effects. RD-26 specifically establishes the Python parameter name `relation_labels` and its values as stated above. This requirement establishes semantic parity without requiring exact parameter parity. The exact CLI spellings `--inverse-properties` and `--diagnostics-file` do not prescribe Python parameter names.

The `owl:allValuesFrom` option removed under ODI-VALUE-RESTRICTIONS / DK-ATT-04 is not an established control to expose through either interface.

Console presentation filtering is separate from transformation-control parity; it does not affect the complete Python diagnostic-access and export requirements. Persistent diagnostics-file writing remains outside this transformation-control parity requirement. The CLI delivery behavior is governed by `--diagnostics-file PATH`; the Python library provides the separately established diagnostic-access and export capabilities below.

This specification does not prescribe Python function signatures, configuration objects, return types, or exception classes. Function names, classes, and exception hierarchies likewise remain unspecified. The required Python diagnostic capabilities are specified below without selecting their exact API names or a result or exception mechanism.

**Rationale and example (non-normative):** Semantic parity lets CLI and Python users request the same transformations while allowing conventions appropriate to each interface. A negative CLI flag may correspond to a positive Python boolean with the opposite value; this illustration establishes no Python parameter name.

### Ontology delivery after conversion abort (RD-04)

Duplicate-ID failure under §3.4 and DK-DIAG-05 MUST produce the `aborted` outcome under every input policy, including `best-effort`; no ontology is delivered through either interface even when unrelated fragments could otherwise be transformed.

Under DK-DIAG-05, DirectKG MUST NOT deliver the ontology accumulated during a conversion that aborts under an accepted input policy through either the CLI or the Python API. A completed `best-effort` conversion remains eligible to deliver partial ontology output under the accepted recovery rules; error diagnostics alone MUST NOT be treated as an abort. Python diagnostic access remains available under DK-DIAG-04, and a requested CLI diagnostics export MUST still be attempted.

The outcomes `completed` and `completed-with-errors` are eligible for ontology delivery; `aborted` prohibits delivery, as defined in DK-DIAG-05. Diagnostics-delivery failure does not change the transformation outcome or this ontology-output eligibility; DK-DIAG-04 governs its reporting. The CLI exit-code mapping below preserves this eligibility, including for code `1`. Python result or exception types remain unspecified.

### Ontology-file creation and write failures (RD-04, option A)

Both interfaces MUST follow DK-DIAG-04's ontology-file delivery-failure policy for failure to create or write a requested ontology file after successful ontology serialization and construction of any required provenance. The CLI uses code `6` subject to the precedence below; Python exposes the failure programmatically with produced diagnostics accessible. Requested CLI JSON diagnostics export MUST still be attempted after recording the failure. DK-GEN-10 prohibits a new provenance sidecar when ontology-file delivery failed.

### CLI exit codes (RD-04)

The CLI MUST use the following exit-code mapping within the scope defined here:

| Code | Condition |
|---|---|
| `0` | Transformation outcome is `completed`, and requested output delivery succeeds. |
| `1` | Transformation outcome is `completed-with-errors`, and requested output delivery succeeds. |
| `2` | Invalid CLI invocation, such as an unknown option or invalid option value. |
| `3` | Transformation outcome is `aborted`, with no diagnostics-delivery failure. |
| `4` | A requested diagnostics file could not be created or written. |
| `5` | Requested provenance-sidecar serialization, creation, or writing failed, without a requested diagnostics-file or ontology-file delivery failure. |
| `6` | Requested ontology-file creation or writing failed after successful ontology serialization and construction of any required provenance, without a requested diagnostics-file delivery failure. |

Diagnostics-delivery failure (`4`) MUST take precedence over transformation codes `0`, `1`, and `3`, provenance-sidecar delivery failure (`5`), and ontology-file delivery failure (`6`). Ontology-file delivery failure (`6`) MUST take precedence over `0`, `1`, and `5` when applicable. Code `5` MUST take precedence over transformation codes `0` and `1`, independently of `--input-policy`. The underlying transformation outcome and its diagnostics MUST remain unchanged and available through the applicable diagnostic-access and export mechanisms, with console presentation subject to DK-DIAG-04's threshold.

Duplicate-ID failures under §3.4 and DK-DIAG-05 produce an `aborted` conversion and follow this existing exit-code mapping and diagnostic-delivery failure precedence.

INFO and WARNING diagnostics alone MUST NOT cause a nonzero exit status. Exit code `1` MUST NOT suppress ontology output otherwise eligible for delivery under the accepted recovery rules.

An invalid invocation (`2`) is a CLI-level failure before conversion starts. It MUST NOT create a transformation outcome for a conversion that never ran.

Rejection of an invalid or unusable supplied base, or an invalid supplied ontology version IRI, under DK-IRI-01 follows this contract: the CLI MUST report a configuration error and exit with code `2`. No conversion starts, and no ontology, transformation outcome, or conversion-diagnostics report is produced for this configuration rejection. Existing exit-code mapping and diagnostic delivery for conversions that run remain unchanged.

Ontology-file creation and write failures within DK-DIAG-04's scope use code `6`. Other ontology-output delivery failures and unexpected runtime failures remain outside this mapping's resolved scope. Failure to construct required provenance under DK-GEN-10 uses abortion code `3`, overridden by `4` if requested diagnostics-file delivery fails. Provenance-sidecar delivery failures are governed by code `5` and DK-GEN-10; code `4` remains reserved for diagnostics-file delivery failure. Code `0` MUST NOT imply successful delivery when such a failure occurs.

**Rationale and example (non-normative):** Distinct codes allow automation to distinguish completed error recovery from abortion. A completed `best-effort` conversion with errors returns `1` when requested output delivery succeeds; failure to write its requested diagnostics file instead returns `4`, without changing the transformation outcome.

### Python diagnostic access and JSON export (ODI-CONTROLS / RD-04)

The Python library MUST provide the structured diagnostic access and separate, explicitly invoked JSON export operation specified in DK-DIAG-04. That rule governs access after a policy-driven abort, preservation of every produced diagnostic, the shared CLI/Python report schema and content, and the prohibition on automatic diagnostics-file writing during Python conversion. Its non-interference requirements apply to both access and export. If the separate export operation fails to create or write the requested file, it MUST signal failure programmatically, and callers MUST retain access to the transformation diagnostics. The CLI `--diagnostics-file PATH` behavior remains governed by its separate delivery contract.

The Python API and, when exported, the shared JSON diagnostics report MUST expose exactly one outcome for each conversion under DK-DIAG-04–05: `completed`, `completed-with-errors`, or `aborted`. Exposing it MUST NOT itself introduce additional diagnostics.

These requirements establish capabilities and outcome names without selecting exact API names, Python representations, a result or exception mechanism, JSON member names, or the complete JSON report schema. Diagnostics-delivery failure behavior is specified in DK-DIAG-04 without prescribing file-writing internals or requiring recovery from an unwritable destination.

**Rationale (non-normative):** Python applications can inspect diagnostics directly and choose whether to save a report afterward. A shared JSON format avoids requiring callers to reconstruct the CLI report format. Access after a policy-driven abort preserves the diagnostics needed to understand the failure.

## 16. Determinism, stability, and conformance

### DK-CONF-01 — Determinism

For an unchanged supported input and identical configuration, IRI generation and collision resolution MUST satisfy the deterministic requirements stated in their governing rules. Stable source IDs or deterministic source ordering should be used where a rule explicitly uses **SHOULD**.

The serialized-presentation boundary in §3.3 (RD-04, option A — serialized presentation) adds no statement-order or textual-repeatability guarantee and does not change these determinism requirements or DK-GEN-10's deterministically serialized configuration YAML.

### DK-CONF-02 — Identity preservation

Distinct source-backed elements and distinct generated inverses MUST never be merged due to candidate collisions.

Duplicate source-element IDs within §3.4's scope follow DK-DIAG-05's abort rule independently of these IRI-collision rules.

Changing inverse mode MAY change generated inverse IRIs but MUST NOT change source-backed IRIs. Inverse candidates are resolved only after all source-backed candidate claims and final IRIs.

### DK-CONF-03 — Strategy separation

Name normalization MUST NOT be applied to source IDs. ID escaping MUST NOT be treated as semantic name normalization. Name-strategy inverse fallbacks MUST NOT become ordinary ID-strategy identifiers.

### DK-CONF-04 — Testing boundary

This specification defines no standalone test framework, coverage threshold, fixture format, conformance-suite design, CI requirement, or other detailed testing requirement.
