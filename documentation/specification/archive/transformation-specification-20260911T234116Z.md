# OntoUML DirectKG Specification Handoff

**Status:** Authoritative working specification snapshot  
**Snapshot date:** 2026-09-11  
**Repository:** https://github.com/pedropaulofb/ontouml-directkg

## 1. Document purpose and authority

This document consolidates the currently established specification of OntoUML DirectKG. It reconciles the earlier specification baseline with later decisions, refinements, corrections, and supersessions. It is intended as authoritative input for future specification maintenance, architecture discussions, and implementation planning.

This is not a final specification: matters listed in [Remaining open specification issues](#18-remaining-open-specification-issues) are intentionally unresolved. A future conversation or implementation MUST NOT infer answers to those issues from examples, historical approaches, or recommendations.

Normative terms such as **MUST**, **MUST NOT**, **SHOULD**, and **MAY** preserve the strength of the decisions from which they were consolidated. Explanatory rationale is non-normative unless it is itself stated as a requirement.

When this document records an unresolved conflict in earlier normative wording, that conflict remains open rather than being silently resolved.

## 2. Project overview

OntoUML DirectKG transforms OntoUML models into a domain-oriented RDF/OWL knowledge graph. Its primary output resources represent the domain classes and properties modeled by the user, rather than the OntoUML metamodel, JSON serialization objects, or Visual Paradigm presentation structures.

The transformation is intended to produce a substantially simpler and more directly usable graph than a structural RDF reproduction of OntoUML JSON.

### 2.1 Relationship to related approaches

- gUFO preserves OntoUML ontological commitments through a UFO-based representation. DirectKG has a different objective: a simpler, general-purpose, domain-oriented graph. DirectKG MUST NOT acquire gUFO imports or metamodel structure merely because gUFO is a related approach.
- OntoUML JSON to Graph preserves much of the JSON structure and internal identifiers. DirectKG MUST NOT reproduce serialization machinery unless an explicit DirectKG rule requires it.
- *An Automated Transformation from OntoUML to OWL and SWRL* (2013) is design precedent, not a binding rule set. Its rules apply only where independently adopted by this specification.

### 2.2 Implementation form

The project MUST be provided as both a Python library and a command-line interface. Detailed architecture, package structure, supported Python versions, dependencies, packaging, performance, CI/CD, and deployment requirements remain unspecified.

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

The input contract is JSON generated from Visual Paradigm models by `ontouml-vp-plugin`.

The standalone `ontouml-schema` is a reference for interpretation; it MUST NOT silently broaden the accepted input contract to arbitrary schema-conformant documents. Which VP-plugin versions and legacy export dialects are accepted remains open.

The current VP association extraction path emits two association ends. N-ary relation support is therefore outside the current input scope and is deferred unless that export contract changes.

### 3.3 Output scope

The target is an RDF/OWL knowledge graph. Turtle is used in examples only. Supported serializations, ontology header and identity, OWL profile guarantees, prefix policy, and output ordering have not yet been established.

DirectKG avoids a DirectKG or OntoUML metamodel vocabulary in the domain graph except where a later explicit rule requires a vocabulary term. In particular, higher-order classification uses standard RDF/OWL constructs rather than companion metamodel resources.

### 3.4 Semantic validation boundary

DirectKG transforms the source model as stated. It is not an OntoUML semantic validator.

DirectKG MUST NOT suppress otherwise applicable output because the source appears semantically incorrect or because the resulting ontology may be inconsistent. Structural processability remains required: malformed JSON, dangling references, missing elements, unresolved endpoints, or invalid identifiers that make a transformation technically impossible MUST be reported as errors. The exact global policy for aborting versus skipping affected constructs remains open where not explicitly specified.

## 4. Terminology

**Source-backed resource**  
A generated resource corresponding directly to a source-model element. This includes classes, classifier-owned properties, and primary properties generated from explicit relations.

**Generated auxiliary resource**  
A generated resource without a separate source-model element. A generated inverse property is auxiliary.

**Domain class**  
An OntoUML class represented as an `owl:Class`. Supported primitive datatype elements and Visual Paradigm `void` are exceptions. Custom OntoUML datatypes are represented as reified domain classes.

**Generated property**  
An `owl:ObjectProperty` or `owl:DatatypeProperty` produced from an attribute, relation, or inverse-generation rule.

**Supported primitive datatype**  
A datatype classifier whose normalized name resolves exactly through the controlled DirectKG primitive registry to an XSD datatype.

**Custom OntoUML datatype**  
A `«datatype»` classifier that is neither a registered primitive nor Visual Paradigm `void`.

**Usable name**  
A non-null name containing meaningful source text that produces a nonempty local name under the applicable normalization rules. For inverse-role presence specifically, at least one non-whitespace character is required.

**Source and target association ends**  
For a direct relation property `A → B`, the source end has `propertyType A` and supplies the direct domain; the target end has `propertyType B` and supplies the direct range.

## 5. General output model

### DK-GEN-01 — Domain resources

DirectKG MUST generate RDF/OWL resources for supported domain classes and properties. It MUST NOT generate resources merely to mirror source JSON containers, diagram views, or metamodel objects.

### DK-GEN-02 — Explicit source structures

Unless a rule explicitly requires closure materialization, DirectKG transforms explicit source structures and does not materialize logically inferred closure. Class generalization is such a case: explicit subclass axioms are emitted, but their transitive closure need not be repeated. Powertype extension materialization is an explicit exception.

### DK-GEN-03 — Property domains and ranges

Every generated OWL property MUST receive an `rdfs:domain`.

- Attribute domain: the owning classifier.
- Primary relation domain: the source-end classifier.
- Generated inverse domain: the primary property's range.

DirectKG MUST generate `rdfs:range` whenever the target or value type is unambiguously resolvable to a supported DirectKG range.

- Primitive-valued attribute: mapped XSD datatype.
- Custom-datatype-valued attribute: custom datatype class.
- Primary relation: target-end classifier.
- Generated inverse: primary property's domain.

DirectKG MUST NOT invent a range for an untyped attribute, `void`, or an unresolved target.

`rdfs:domain` and `rdfs:range` are inferential axioms, not validation constraints. DirectKG deliberately adopts their RDF/OWL semantics.

## 6. Class transformation

### DK-CLS-01 — Domain classes

Every OntoUML class representing a domain type MUST become an `owl:Class`.

Before applying this rule, a `«datatype»` classifier MUST be classified as a supported primitive, `void`, or custom datatype:

- Supported primitive datatype: no local `owl:Class`.
- `void`: no local `owl:Class` or OWL datatype.
- Custom datatype: local reified `owl:Class`.

### DK-CLS-02 — Class generalization

For a class-to-class OntoUML generalization, DirectKG MUST emit:

```turtle
:Specific rdfs:subClassOf :General .
```

The transitive subclass closure need not be materialized. Relation-to-relation generalization remains open.

### DK-CLS-03 — Ultimate-sortal disjointness

The ultimate-sortal set is:

```text
collective, kind, mode, quality, quantity, relator, type
```

Any two distinct generated OWL classes directly carrying any stereotype in this set MUST be disjoint, including two classes carrying the same ultimate-sortal stereotype. Redundant subclass-inherited disjointness assertions need not be emitted.

### DK-CLS-04 — Cross-group disjointness

The following stereotype groups are established:

1. `abstract`, `datatype`, `enumeration`
2. `event`
3. `situation`
4. `kind`, `collective`, `quantity`, `relator`, `mode`, `quality`, `subkind`, `role`, `phase`, `category`, `mixin`, `roleMixin`, `phaseMixin`, `historicalRole`, `historicalRoleMixin`, `type`

Two generated classes MUST be disjoint when their stereotypes belong to different groups. This rule does not itself create intra-group disjointness. Primitive datatype elements and `void` do not participate because they do not generate local classes.

The exact RDF/OWL serialization of these disjointness requirements remains open.

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

DirectKG MUST NOT:

- compare or reconcile `«instantiation»` with `GeneralizationSet.categorizer`;
- establish precedence between higher-order classification sources;
- suppress multiple classifications;
- validate classifier orders or stereotype appropriateness;
- detect semantic conflicts among higher-order classifications;
- suppress an assertion because it might contribute to an inconsistent ontology.

Different higher-order types are not treated as conflicting merely because they classify related elements.

The transformation of `GeneralizationSet.isDisjoint`, `isComplete`, and relation-classifier generalization sets remains open.

## 8. Attributes and datatypes

### DK-ATT-01 — Attribute property kind

An attribute is classified by its resolved `propertyType`:

| Source type | Generated property | Range behavior |
|---|---|---|
| Supported primitive datatype | `owl:DatatypeProperty` | Registered XSD datatype |
| Custom `«datatype»` | `owl:ObjectProperty` | Custom datatype class |
| `null` | `owl:DatatypeProperty` | No range |
| Visual Paradigm `void` | `owl:DatatypeProperty` | No range; warning |

The attribute's domain is always its owning class.

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

When `l = u = n`, DirectKG MAY use an exact-cardinality restriction instead of separate minimum and maximum restrictions.

Cardinality requirements are independent of optional value-type restrictions. The meaning of `cardinality = null` remains open.

### DK-ATT-04 — Optional `owl:allValuesFrom`

Local `owl:allValuesFrom` restrictions for typed attributes are optional and disabled by default. One explicit option is to control this behavior for both primitive-valued and custom-datatype-valued attributes; its name remains open.

When the option is disabled, DirectKG MUST NOT emit the local `only` restriction. When enabled and the type is resolvable, DirectKG MAY emit it. Whether enabled mode makes generation mandatory remains open.

Untyped and `void` attributes cannot receive this restriction. Whether the same option applies to ordinary relations remains open.

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

The established or explicitly illustrated registry entries are:

| Key | Target |
|---|---|
| `boolean` | `xsd:boolean` |
| `byte` | `xsd:byte` |
| `char` | `xsd:string` |
| `double` | `xsd:double` |
| `float` | `xsd:float` |
| `int` | `xsd:int` |
| `integer` | `xsd:integer` |
| `long` | `xsd:long` |
| `short` | `xsd:short` |
| `string` | `xsd:string` |
| `decimal` | `xsd:decimal` |
| `date` | `xsd:date` |
| `datetime` | `xsd:dateTime` |
| `positiveinteger` | `xsd:positiveInteger` |
| `nonnegativeinteger` | `xsd:nonNegativeInteger` |
| `unsignedint` | `xsd:unsignedInt` |

The registry is extensible and has not been declared permanently exhaustive. Semantically distinct XSD datatypes, including `xsd:int` and `xsd:integer`, MUST remain distinct.

Standard prefixed and full XSD datatype identifiers SHOULD be recognized. Semantic aliases such as `bool`, `str`, `wholeNumber`, or `integer32` MUST be accepted only if explicitly registered; the examples do not themselves activate those aliases.

DirectKG MUST NOT use fuzzy matching, edit-distance correction, stemming, singular/plural normalization, abbreviation expansion, translation, or synonym detection for datatype resolution.

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

A custom OntoUML datatype MUST become a reified `owl:Class`. An attribute or explicit relation targeting it MUST become an `owl:ObjectProperty` with the custom datatype class as range.

DirectKG MUST preserve the structured value and MUST NOT flatten the custom datatype's attributes into the referring classifier. Nested custom datatype properties MUST be transformed recursively under the same rules.

DirectKG MUST NOT infer an XSD mapping from a custom datatype's name. For example, `TimeInterval` does not automatically become `xsd:duration`.

## 9. Property identity, labels, and general collision rules

### DK-PROP-01 — Distinct property identity

Every distinct source attribute or relation MUST remain a distinct OWL property. DirectKG MUST NOT merge independently modeled properties because their names or normalized candidates coincide. IRI disambiguation MUST NOT change whether a property is an object or datatype property.

DirectKG MUST NOT repair merged properties by introducing union domains or ranges.

### DK-PROP-02 — Name-based owner/source qualification

For source-backed properties in name mode, a unique normalized property candidate MAY be used directly. When ordinary source-backed properties collide, DirectKG MUST first qualify them as:

```text
<propertyName>_<ownerOrSourceName>
```

If collisions remain, every member of the collision group MUST receive deterministic `_1` through `_N` suffixes. No unsuffixed member remains in a collision group. Source IDs MAY determine stable numbering but need not appear in the IRI.

The owner/source qualification behavior when the owner/source classifier is unnamed remains incompletely specified.

### DK-LBL-01 — Source labels

A named source property or relation MUST preserve its original name as `rdfs:label`, even if its IRI is disambiguated.

An unnamed class MUST NOT receive an invented label. For named classes and other non-property resources, earlier authoritative material contains unreconciled **MUST** and **SHOULD** formulations for preserving source names as labels; the exact normative strength remains open.

Generated inverse labels are governed by [Section 11](#11-generated-inverse-properties).

## 10. Primary binary-relation transformation

### DK-REL-01 — Eligible ordinary relation

A supported binary relation with two resolved classifier endpoints that is transformed as a primary relation MUST become an IRI-identified `owl:ObjectProperty` with explicit source domain and target range.

Detailed relation-end multiplicity semantics remain open.

### DK-REL-02 — Forward name precedence

Under the name strategy, with stereotype-derived naming enabled, the direct property's candidate is selected in this order:

1. usable relation name;
2. usable target-end role name;
3. an established stereotype-derived semantic name;
4. synthesized `<source>_<target>`;
5. deterministic collision resolution.

The source-end role MUST NOT name the forward property. Generic prefixes such as `has`, `relatedTo`, or `isRelatedTo` MUST NOT be invented unless present in the source or an adopted stereotype mapping.

Stereotype-derived naming is enabled by default and MAY be disabled with:

```text
--no-stereotype-relation-naming
```

When disabled, step 3 is skipped.

### DK-REL-03 — Synthesized endpoint name

The source-target fallback is:

```text
lowerFirst(normalize(source.name)) + "_" + lowerFirst(normalize(target.name))
```

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

Successful ordinary stereotype-derived naming produces no warning or information message.

`comparative` has no generic semantic name because the required predicate is domain-specific. If its semantic naming step is reached, DirectKG MUST warn and continue to the source-target fallback.

`derivation` has no generic property-name mapping and its primary transformation remains open.

### DK-REL-05 — Material relation naming

An unnamed `«material»` relation with no usable target-end role MUST NOT receive a fixed predicate such as `materiallyRelatedTo`. At the stereotype-derived naming step, DirectKG MUST attempt to resolve its grounding `«relator»` through an OntoUML `«derivation»`.

When a usable grounding relator name exists, the candidate is:

```text
lowerFirst(normalize(relator.name))
```

No `has` prefix is added. The property continues to connect the material relation's source and target; it does not point to a relator individual. Successful relator-based naming SHOULD produce an informational provenance diagnostic and MUST NOT produce a warning merely because this naming path succeeded.

If no usable grounding relator can be resolved, DirectKG MUST warn and continue to the source-target fallback. The initial diagnostics need not distinguish absence, ambiguity, an unnamed target, or an unusable target; all MAY be reported as an unavailable grounding relator.

This section establishes naming only. Material-relation semantic derivation remains open.

### DK-REL-06 — Relation naming diagnostics

An unnamed relation using a target-role or source-target fallback MUST produce a non-fatal warning, except where a later stereotype-specific rule replaces it. A deliberately unmapped `comparative` or `derivation` reaching semantic naming MUST warn before lexical fallback, subject to the unresolved primary transformation of `derivation`.

When both an endpoint class and its relation are unnamed, separate diagnostics SHOULD identify the two conditions unless a later stereotype-specific rule replaces the generic relation warning.

DirectKG currently assumes valid relation orientation and does not need a defensive semantic-orientation recovery branch.

## 11. Generated inverse properties

### DK-INV-01 — Generation modes

DirectKG MUST expose a transformation argument with four modes:

| Mode | Behavior |
|---|---|
| `all` | Default; generate every eligible inverse property |
| `informed` | Generate when the inverse-facing end has a nonempty role name or non-null multiplicity |
| `named` | Generate only when the inverse-facing end has a nonempty role name |
| `none` | Generate no inverse properties |

Under `informed`, either qualifying datum is sufficient. The exact CLI spelling of this transformation argument has not been established.

**Rationale.** Examination of 198 OntoUML JSON exports confirmed that real relation ends can have absent role names and null multiplicities, so the conditional modes represent meaningful distinctions.

### DK-INV-02 — Eligibility

A relation is inverse-eligible exactly when it is a supported binary OntoUML relation whose primary transformation successfully produces an IRI-identified `owl:ObjectProperty` with two resolved classifier endpoints suitable as domain and range.

Eligible cases include self-relations, supported stereotyped relations, and unnamed source relations that receive generated IRIs.

The following are not eligible:

- `«instantiation»`;
- attributes represented as `owl:DatatypeProperty`;
- generalizations and generalization sets;
- unsupported n-ary relations;
- constructs mapped as assertions, annotations, or reified structures instead of object properties.

Malformed relations are diagnosed under their underlying problem and MUST NOT be silently reclassified as ineligible. The eligibility of `«derivation»` depends on its unresolved primary transformation.

### DK-INV-03 — Inverse direction, domain, and range

For a primary property `A → B`, the generated inverse maps `B → A`. Its inverse-facing end is the association end typed by `A`—the inverse range and primary domain.

Every generated inverse MUST receive explicit reversed domain and range declarations derived mechanically from the primary property. These axioms are intentionally explicit even though they are logically redundant with `owl:inverseOf`, so non-reasoning consumers can inspect the property directly.

### DK-INV-04 — Explicit `owl:inverseOf`

Every generated inverse property MUST have exactly one explicit assertion directed from the inverse to the primary property:

```turtle
:Inverse owl:inverseOf :Primary .
```

DirectKG MUST NOT emit the redundant reciprocal assertion. This applies regardless of generation mode, naming path, collision path, or IRI strategy. When no inverse is generated, no `owl:inverseOf` assertion is emitted.

### DK-INV-05 — Inverse-facing role and label

A role is present when it is non-null and contains at least one non-whitespace character. Under the name strategy, only the inverse-facing end's role may name the inverse.

When present:

- under the name strategy, its normalized value is the preferred IRI candidate;
- under either IRI strategy, the original role name MUST be preserved as the inverse's `rdfs:label`.

When the inverse-facing role is absent, no synthetic `rdfs:label` is generated for the inverse under either IRI strategy.

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

**Rationale.** Treating source-backed properties and generated inverses as one undifferentiated collision group would allow enabling inverse generation to rename source-backed resources. Corpus analysis found that this would affect 30 primary relation-property IRIs and two classifier-owned property IRIs across 14 models.

### DK-INV-08 — Secondary name-strategy collisions

If the primary-based fallback collides, only the generated inverse is further qualified. The qualifier is the inverse domain—the primary property's range:

```text
inverseOf<ResolvedPrimaryPropertyLocalName>_<InverseDomain>
```

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

Special multilingual inverse-name selection is not required while input remains limited to JSON exported from VPP through the current VP-plugin extraction path, which exports at most one role name per end. A review of 198 `ontology.json`/`ontology.vpp` pairs found no multilingual role names in actual exports. The standalone schema and plugin data structures can represent multilingual text, but that capability does not broaden the current input contract. Multilingual inverse naming MAY be reconsidered if arbitrary schema-conformant JSON becomes supported.

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

Discarded information MUST NOT be retained through transformation reports, provenance metadata, annotations, or alternative resources.

### DK-INS-03 — No reconciliation

An `«instantiation»` association is not compared or reconciled with categorizer-derived classifications. No precedence is established, and classifications are not suppressed merely because they overlap or appear inconsistent.

## 13. IRI generation and naming

### DK-IRI-01 — Base IRI

DirectKG MUST support:

```text
--base-iri <IRI>
```

If absent, it MUST use `https://example.org/directkg#` and emit a non-fatal warning explaining that this is a placeholder namespace and is not recommended for publication.

If a supplied base ends with `#` or `/`, that delimiter MUST be preserved. Otherwise DirectKG MUST append `#` without warning. Behavior for a syntactically invalid or unusable base IRI remains open.

### DK-IRI-02 — Strategies

DirectKG MUST support:

```text
--iri-strategy name
--iri-strategy id
```

The default is `name`. Name mode prioritizes readability; renaming a source element MAY change its IRI, and documentation MUST explain this consequence. ID mode prioritizes identity stability.

Under the ID strategy, a source-backed resource's local name MUST be derived from its designated source identifier rather than its source name, even when the resource is named. For classes and classifier-owned properties, the designated identifier is the source element's own ID. Relation-derived properties use the association-end identifiers specified by DK-IRI-06.

### DK-IRI-03 — Name normalization

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

### DK-IRI-04 — Unusable and unnamed names

If normalization yields no usable local name, DirectKG MUST use the applicable unnamed fallback and warn. The original source name MAY still be retained as a label where labeling rules permit.

An unnamed class in name mode MUST use:

```text
unnamedClass_<escaped-source-id>
```

The stereotype MUST NOT appear in this synthetic IRI. The class receives no invented label, and transformation continues after a non-fatal warning identifying available source details and the generated IRI.

Where available, that warning MUST identify the source element type, source element ID, stereotype, and generated IRI.

In ID mode, unnamed resources use their source IDs rather than an unnamed fallback, but DirectKG MUST still warn that the source element is unnamed.

### DK-IRI-05 — Source ID escaping

Source IDs use technical escaping, not name normalization. DirectKG MUST preserve ASCII letters, digits, and case. Every other UTF-8 byte MUST be encoded as `_xHH` using uppercase hexadecimal. `_` itself MUST be encoded as `_x5F`.

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

When inverse generation is disabled, the direct property still uses the target-end ID and the source-end ID produces no separate property.

### DK-IRI-07 — Ordinary name collision groups

After all applicable name fallbacks and source-backed property qualification, DirectKG MUST check local-name collisions. A unique candidate remains unsuffixed. Every member of a collision group of size `N` MUST receive `_1` through `_N`; DirectKG MUST NOT leave one unsuffixed.

Suffix allocation MUST be deterministic and stable for an unchanged source model. Stable source information, preferably element IDs or deterministic source order, SHOULD assign suffixes.

Distinct source elements MUST NOT be merged. A collision between distinct escaped source IDs is exceptional and MUST NOT be silently repaired as an ordinary name collision; its exact disposition remains open.

## 14. Validation, diagnostics, and loss reporting

### DK-DIAG-01 — Established diagnostics

| Condition | Required behavior | Fatal? |
|---|---|---:|
| No base IRI | Warning; use placeholder base | No |
| Unnamed or unusably named class in name mode | Warning; use synthetic IRI | No |
| Unnamed source element in ID mode | Warning; ID-based IRI remains usable | No |
| Attribute typed by `void` | Warning; omit datatype mapping/range | No |
| Unnamed ordinary relation using target-role or source-target fallback | Warning | No |
| Successful ordinary stereotype-derived name | No diagnostic | No |
| Successful material relator-derived name | Information message SHOULD be emitted; no warning | No |
| Material semantic name unavailable | Warning; use source-target fallback | No |
| Deliberately unmapped applicable relation stereotype | Warning; use weaker fallback where transformation is otherwise defined | No |
| Expected inverse omission under `informed` or `named` | No diagnostic or element report | No |
| Discarded `«instantiation»` association data | One consolidated warning | No by itself |
| Structurally unprocessable source | Error | Not specified globally; abort-versus-skip policy remains open |
| Collision after injective ID escaping | Exceptional; do not merge | Exact policy open |

### DK-DIAG-02 — Semantically questionable input

DirectKG does not validate source OntoUML semantics. It does not validate classifier orders, stereotype appropriateness, higher-order conflicts, or output consistency. It emits every applicable higher-order assertion from transformable source structures, even if the resulting ontology is inconsistent.

### DK-DIAG-03 — Failed relations

A relation requires resolvable source and target classifiers before either directional property can be generated. A missing or invalid association-end ID, or a null or unresolved end `propertyType`, invokes established diagnostics and neither the direct nor inverse property is generated.

An association-end ID can be valid even when its `propertyType` is null; the relation remains untransformable because its classifier is unresolved, not because its ID is absent.

### DK-DIAG-04 — Diagnostic format

Where content requirements are stated, diagnostics SHOULD identify the relevant source element and reason. Exact diagnostic identifiers, message schema, output channel, aggregation format, and structured-report format remain open.

## 15. Configuration, CLI, and Python library API

The following transformation controls are established:

| Control | Status |
|---|---|
| `--base-iri <IRI>` | Established |
| `--iri-strategy name\|id` | Established; default `name` |
| `--no-stereotype-relation-naming` | Established; stereotype naming otherwise enabled |
| Inverse-generation argument with `all\|informed\|named\|none` | Semantics established; default `all`; exact argument name open |
| Single typed-attribute `owl:allValuesFrom` option | Existence and default-off behavior established; exact name and enabled strength open |

The project MUST provide both a CLI and a Python library. How the established transformation controls are exposed through each interface—including whether exact option parity is required—remains unspecified, as do function names, classes, return types, exception hierarchies, configuration objects, and the diagnostics API.

## 16. Determinism, stability, and conformance

### DK-CONF-01 — Determinism

For an unchanged supported input and identical configuration, IRI generation and collision resolution MUST satisfy the deterministic requirements stated in their governing rules. Stable source IDs or deterministic source ordering should be used where a rule explicitly uses **SHOULD**.

### DK-CONF-02 — Identity preservation

Distinct source-backed elements and distinct generated inverses MUST never be merged due to candidate collisions.

Changing inverse mode MAY change generated inverse IRIs but MUST NOT change source-backed IRIs. Inverse candidates are resolved only after all source-backed candidate claims and final IRIs.

### DK-CONF-03 — Strategy separation

Name normalization MUST NOT be applied to source IDs. ID escaping MUST NOT be treated as semantic name normalization. Name-strategy inverse fallbacks MUST NOT become ordinary ID-strategy identifiers.

### DK-CONF-04 — Testing boundary

No standalone test framework, coverage threshold, fixture format, conformance-suite design, or CI requirement has been established. Detailed testing requirements remain to be specified.

### Non-normative retained recommendations

The following recommendations were recorded in the authoritative design material but were not accepted as requirements:

- **Pairwise disjointness encoding:** pairwise `owl:disjointWith` was suggested for the broad cross-group disjointness rule because one `owl:AllDisjointClasses` axiom over all grouped classes would incorrectly impose intra-group disjointness. The semantic disjointness rule is established; its concrete OWL encoding remains open.
- **Cycle-safe custom-datatype processing:** recursive custom-datatype processing should terminate even when datatype references are cyclic. This is an implementation-safety recommendation, not an established semantic or implementation requirement.
- **Deterministic enabled value restrictions:** when the optional `owl:allValuesFrom` mode is enabled, DirectKG should generate the restriction whenever the value type is resolvable. This stronger behavior was not accepted; the normative strength of enabled mode remains open.

## 17. Rejected and superseded alternatives

The following alternatives are not current normative behavior:

1. **Unconditional `Class → owl:Class`:** superseded by datatype classification before class generation.
2. **Mandatory attribute `owl:allValuesFrom`:** superseded by the default-off optional mode.
3. **`owl:equivalentClass` for attribute constraints:** rejected in favor of necessary `rdfs:subClassOf` restrictions.
4. **Guessing a datatype for `propertyType = null`:** rejected.
5. **Mapping `void` to an RDF/OWL/XSD construct:** rejected.
6. **Guessing XSD semantics from custom datatype names or fuzzy datatype matching:** rejected.
7. **Flattening custom datatype structure:** rejected.
8. **Merging same-name source properties and repairing ranges with unions:** rejected.
9. **Embedding source IDs in ordinary final name-collision IRIs:** superseded by deterministic numeric suffixes.
10. **Using the source-end role for the forward property:** rejected.
11. **Inventing generic relation prefixes:** rejected.
12. **`hasFeature` for forward characterization:** rejected in favor of `isCharacterizedBy`.
13. **A fixed `materiallyRelatedTo` predicate or automatic `has<RelatorName>`:** rejected.
14. **Adding the class stereotype to unnamed-class IRIs:** rejected.
15. **Higher-order companion individuals, OWL Full metamodeling, or omitting higher-order support:** rejected in favor of OWL 2 punning.
16. **Transforming `«instantiation»` as an ordinary object property:** rejected in favor of `rdf:type` for actual instantiation facts.
17. **A machine-readable external or custom property for classifier `order`:** rejected in favor of informative `rdfs:comment`.
18. **Resolving source-backed properties and generated inverses in one undifferentiated collision group:** rejected; source-backed resources have precedence.
19. **Using `inverseOf<InverseRoleName>` after an inverse-role collision:** rejected; the fallback is based on the resolved primary-property local name.
20. **Association ID as the ID-strategy basis of the direct property:** superseded by the target association-end ID. The earlier association-ID rule is not retained as an option.
21. **Reciprocal serialization of `owl:inverseOf`:** rejected as redundant; only inverse-to-primary is emitted.

## 18. Remaining open specification issues

The following inventory describes current boundaries only. It is not a replacement for a dedicated remaining-decisions handoff.

1. **Input compatibility:** supported VP-plugin versions, legacy dialect detection, unknown fields, and compatibility-layer behavior.
2. **Attribute cardinality:** meaning of `cardinality = null`.
3. **Value-type restrictions:** option name; whether enabled mode requires deterministic `owl:allValuesFrom`; application to ordinary relations.
4. **Relation-end multiplicities:** direction of restrictions, qualified versus unqualified cardinalities, anonymous inverse expressions, null and symbolic bounds, and behavior when no named inverse exists.
5. **Disjointness serialization:** pairwise `owl:disjointWith` versus appropriate `owl:AllDisjointClasses` structures.
6. **Generalization sets:** `isDisjoint`, `isComplete`, coverage, and relation-classifier sets. Categorizer and powertype behavior are resolved.
7. **Relation generalization:** subproperty mapping and interaction with generalization sets.
8. **Enumerations:** representation of enumeration classifiers and literals.
9. **Classifier and property metaproperties:** `isAbstract`, `isDerived`, `isExtensional`, `restrictedTo`, `isOrdered`, `isReadOnly`, `aggregationKind`, `subsettedProperties`, and `redefinedProperties`, together with any additional semantics of the `«abstract»` stereotype. Classifier `order` and `isPowertype` are resolved.
10. **Property stereotypes:** behavior of `«begin»` and `«end»`.
11. **Relation stereotypes:** semantic OWL axioms beyond established naming, including material semantics, `«derivation»`, comparative semantics, parthood, dependence, mediation, event relations, and related property characteristics or rules.
12. **`«derivation»`:** primary transformation and consequent inverse eligibility.
13. **Individuals:** general instance-data transformation beyond established higher-order classification and future concrete instantiation-link semantics.
14. **Temporal semantics:** no general mapping has been established beyond the currently adopted naming and disjointness treatment of temporal/historical constructs.
15. **Labels and annotations:** normative strength for class labels; generated labels for unnamed non-inverse relations; descriptions; multilingual labels and name selection outside the current inverse-role limitation; source-ID traceability; provenance; arbitrary `propertyAssignments`.
16. **Packages and namespaces:** package semantics, modularization, annotations, and whether packages influence IRIs. Package paths MUST NOT silently enter IRIs without a future explicit decision.
17. **Ontology identity and metadata:** `owl:Ontology`, ontology IRI, version IRI, imports, title, description, license, provenance, and propagation of source project metadata.
18. **Presentation data:** diagrams, element views, paths, layout geometry, and shapes present in the VP-plugin export. Standalone-schema-only note and anchor structures are outside the current input contract unless that contract is explicitly expanded.
19. **Unknown stereotypes:** whether to preserve structural transformation with warning or fail.
20. **Malformed and dangling references:** exact global abort/skip policy beyond the requirement to report structurally impossible transformations as errors.
21. **IRI edge cases:** invalid base IRIs, exceptional escaped-ID collisions, and unnamed owner/source qualification.
22. **Output contract:** RDF serializations, prefixes, OWL profile, deterministic statement ordering, and diagnostic/report channels and formats.
23. **Implementation and API design:** architecture, dependencies, public Python API, exception model, packaging, compatibility/versioning policy, performance, and deployment.
24. **Testing:** conformance suite, fixtures, coverage, regression requirements, and CI policy.
25. **Primitive datatype registry:** completeness and maintenance of the registry, and the contents of any explicit semantic-alias registry.
26. **Relation endpoint coverage:** treatment of relation endpoints not transformed as ordinary classes, beyond the established handling of custom-datatype targets.

## 19. Handoff instructions

A future Documenter, Architect, or implementation agent should:

1. treat the normative rules in Sections 2–16 as the established baseline, subject to explicit open boundaries, while keeping the explicitly non-normative recommendations in Section 16 non-normative;
2. treat Section 17 as rejected or superseded behavior, not alternative supported behavior;
3. keep every item in Section 18 unresolved until explicitly decided;
4. preserve the distinction between source OntoUML semantics, DirectKG transformation choices, RDF/OWL semantics, and implementation details;
5. avoid promoting examples, historical 2013 rules, or recommendations into requirements;
6. update this handoff whenever a later authoritative decision refines, supersedes, or conflicts with a rule;
7. maintain OntoUML DirectKG's central objective: a pragmatic, simplified, domain-oriented graph rather than a structural serialization of OntoUML.

### Reference context

The design material relies on the following sources for historical, semantic, source-contract, or corpus context. They do not override the normative DirectKG decisions in this document:

- **An Automated Transformation from OntoUML to OWL and SWRL** (2013), used as the historical transformation baseline.
- **OntoUML metamodel:** <https://github.com/OntoUML/ontouml-metamodel>.
- **OntoUML VP Plugin:** <https://github.com/OntoUML/ontouml-vp-plugin>. The source-contract study specifically referenced `IAssociationTransformer.java`, `IGeneralizationTransformer.java`, `IGeneralizationSetTransformer.java`, `IClassTransformer.java`, `ClassSerializer.java`, and `ModelElementSerializer.java` under the plugin's `src/main/java/it/unibz/inf/ontouml/vp/model/` tree.
- **OntoUML Vocabulary v1.1.1:** <https://dev.ontouml.org/ontouml-vocabulary/>.
- **OntoUML Schema v1.0.2:** <https://github.com/OntoUML/ontouml-schema/blob/master/src/ontouml-schema.yaml>. It is a reference, not the current DirectKG input contract.
- **OntoUML model corpus:** <https://github.com/OntoUML/ontouml-models>, used as supporting evidence rather than as normative specification text.
