# Binary relations

This page explains **accepted intended mappings**, not verified converter behavior. Ordinary relations, generalizations, and relation-valued connectors have different output boundaries. DirectKG retains stated directions rather than repairing a model's semantics.

## Primary direction and naming

An eligible ordinary binary relation with resolved classifier endpoints becomes a distinct IRI-identified `owl:ObjectProperty`. Its domain is the source-end classifier and its range is the target-end classifier. Relations with relation-valued endpoints follow the [specialized connector boundary](#relation-valued-endpoints) instead. Attributes retain their separate [type mappings](attributes-and-datatypes.md#property-kinds-and-ranges).

For an eligible ordinary relation, explicit recognized `begin` or `end` stereotypes on its association ends follow [boundary stereotype comment placement](property-features.md#boundary-stereotype-comments): identify each source/target occurrence on the successfully generated primary property, independently of named-inverse generation. The relation's logical mappings remain unchanged.

Under name-based identity, choose the primary property's lexical candidate in this order:

1. Usable relation name.
2. Usable **target-end** role name.
3. Applicable stereotype-derived semantic name, when enabled.
4. Synthesized source–target name.
5. Applicable qualification and deterministic collision resolution.

The source-end role does not name the primary property. Supported localized fields use the [original-text selector](../reference/identifiers.md#multilingual-naming) before naming. The endpoint fallback is `lowerFirst(normalize(source.name)) + "_" + lowerFirst(normalize(target.name))`: change only the first character, not the whole classifier name. Unnamed endpoints first receive their established synthetic identifiers, which may supply these components. General normalization, source-ID fallback, and collisions remain owned by [Identifiers and naming](../reference/identifiers.md#names-escaping-and-collisions).

### Semantic naming candidates

The following candidates apply when the stereotype step is reached and the source has the indicated direction. This table does not authorize semantic orientation checks, reversal, or repair.

| Stereotype | Primary direction | Candidate |
| --- | --- | --- |
| `bringsAbout` | Event → Situation / Situation → Event | `bringsAbout` / `broughtAboutBy` |
| `characterization` | Bearer → Feature / Feature → Bearer | `isCharacterizedBy` / `characterizes` |
| `componentOf` | Whole → Component / Component → Whole | `hasComponent` / `componentOf` |
| `creation` | Event → Endurant / Endurant → Event | `creates` / `wasCreatedIn` |
| `externalDependence` | Extrinsic Mode → Endurant / Endurant → Extrinsic Mode | `externallyDependsOn` / `isExternalDependencyOf` |
| `historicalDependence` | Dependent → Antecedent / Antecedent → Dependent | `historicallyDependsOn` / `isHistoricalDependencyOf` |
| `manifestation` | Aspect/Disposition → Event / Event → Aspect/Disposition | `manifestedIn` / `manifests` |
| `mediation` | Relator → Endurant / Endurant → Relator | `mediates` / `isMediatedBy` |
| `memberOf` | Member → Collective / Collective → Member | `memberOf` / `hasMember` |
| `participation` | Participant → Event / Event → Participant | `participatesIn` / `hasParticipant` |
| `participational` | Part Event → Whole Event / Whole Event → Part Event | `participationalPartOf` / `hasParticipationalPart` |
| `subCollectionOf` | Subcollection → Collection / Collection → Subcollection | `subCollectionOf` / `hasSubCollection` |
| `subQuantityOf` | Subquantity → Quantity / Quantity → Subquantity | `subQuantityOf` / `hasSubQuantity` |
| `termination` | Endurant → Event / Event → Endurant | `wasTerminatedIn` / `terminates` |
| `triggers` | Situation → Event / Event → Situation | `triggers` / `triggeredBy` |

Stereotype naming is enabled by default; the [naming control](../reference/controls.md#established-controls) can skip this step. Do not invent `has`, `relatedTo`, or `isRelatedTo` prefixes unless supplied by the source or an accepted stereotype mapping. Successful ordinary stereotype naming adds no warning or INFO solely for naming success; independently applicable limitation warnings remain.

An unnamed `material` relation without a usable target role instead attempts its grounding **relator's** name at this step: `lowerFirst(normalize(relator.name))`, with no `has` prefix. The property still connects its participant classes, not a relator individual. Successful relator-based naming should produce an informational provenance diagnostic and requires no warning merely for that success. An unavailable usable grounding relator requires a warning, then the endpoint fallback; the initial diagnostic need not distinguish absence, ambiguity, or unusable naming. No special mode-grounded material name is established.

`comparative` has no generic semantic predicate: reaching that step requires a warning before the endpoint fallback. An unnamed ordinary relation using a target-role or source–target fallback requires a nonfatal warning unless a specific rule replaces it. If both an endpoint and its relation are unnamed, their diagnostics should distinguish the conditions. Covered derivation connectors do not enter ordinary naming fallback. See [Recognized derivations](derivations-and-chains.md#recognized-derivations).

Original relation/target-role labels and descriptions have their [separate text rules](../reference/text.md#labels-and-descriptions); lexical identity is not a substitute for a label. Primary-property IDs use the target association-end ID under ID-based construction, as specified in [Strategy and renaming](../reference/identifiers.md#strategy-and-renaming).

### Historical dependence

An eligible ordinary relation carrying recognized `historicalDependence` retains its ordinary property identity, direction, naming, labels, descriptions, domain, range, inverses, cardinalities, and applicable generalization mappings. **Historical-dependence semantics are only partially translated** through this ordinary mapping. The stereotype alone supplies no additional logical axioms or annotations recording its declaration. The general metadata permission in DK-GEN-11 does not override this omission.

Source-description mappings and independently required annotations remain applicable. The stereotype-derived names in the table above and any corresponding [generated fallback label](../reference/text.md#primary-relation-labels) retain their existing conditions, as do source-label and language rules. Omitting a stereotype-declaration annotation does not suppress these lexical or descriptive mappings.

The existing nonfatal [limitation warning](../reference/diagnostics.md#names-typing-and-source-text) for a deliberately unmapped applicable relation stereotype still applies under DK-DIAG-01. Successful stereotype-derived naming does not suppress this warning; no warning-suppression exception is established for `historicalDependence`.

## Additional relation axioms

The following additions apply to successfully mapped primary `owl:ObjectProperty` resources, subject to the [compatibility check for each addition](#compatibility-of-each-addition):

| Recognized relation stereotype | Additional declaration on the primary property |
| --- | --- |
| `characterization` | `rdf:type owl:AsymmetricProperty` |
| `mediation` | `rdf:type owl:AsymmetricProperty` |
| `participational` | `rdf:type owl:AsymmetricProperty` |
| `externalDependence` | `rdf:type owl:IrreflexiveProperty` |

Each declaration preserves the primary property's actual direction. Asymmetry excludes a pair together with its reverse; irreflexivity excludes relating an individual to itself.

### Characterization and external dependence

Pair every successfully mapped `characterization` relation with every successfully mapped `externalDependence` relation whose feature endpoint resolves to the **same source class in the feature role of both relations**. Match exact source-class identifiers, without discovering further pairs through inheritance or names. No material relation, derivation connector, or property chain is required. Multiple matching characterizations or external-dependence relations produce all eligible pairs rather than disqualifying the pattern.

If a feature endpoint cannot be identified unambiguously, omit the affected new disjointness axiom while retaining the ordinary mappings.

For each eligible pair, select expressions directed **from the feature to its bearer and external dependency**, respectively. Use a primary property when already aligned; when reversal is needed, use its corresponding generated named inverse, or an anonymous `ObjectInverseOf(primary)` expression when no named inverse exists. This [inverse-expression selection](inverses.md#direction-and-anonymous-inverses) preserves both primary directions and never forces named-inverse generation or changes the selected inverse mode.

Emit pairwise `owl:propertyDisjointWith` between the aligned expressions when compatible. This prevents the same feature–individual pair from belonging to both properties; it does not declare their endpoint classes disjoint.

The following **specification illustration**, not observed converter output, assumes an eligible pair with primary `isCharacterizedBy` directed bearer → feature, primary `externallyDependsOn` directed feature → dependency, named inverses disabled, and simple participating expressions considering the full hierarchy and import closure. It shows selected axioms only; other required ontology output is omitted.

```turtle
@prefix : <https://example.org/dependence#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .

:isCharacterizedBy a owl:ObjectProperty, owl:AsymmetricProperty .
:externallyDependsOn a owl:ObjectProperty, owl:IrreflexiveProperty .
[ owl:inverseOf :isCharacterizedBy ]
    owl:propertyDisjointWith :externallyDependsOn .
```

### Compatibility of each addition

Assess **each proposed new axiom separately** against its applicable OWL 2 DL restrictions, considering the generated property hierarchy, inverse relationships, and import closure, including the [mandatory DKGM import](mereology.md#import-and-vocabulary-identity). Asymmetry and irreflexivity require a simple participating property expression; paired disjointness requires **both** expressions to be simple. A property used only in a chain body is not non-simple solely because of that use.

Omit a new axiom that fails its simplicity condition; retain other compatible additions. For example, a non-simple characterization expression excludes its new asymmetry declaration and a disjointness pair using it, but does not exclude an otherwise compatible external-dependence irreflexivity declaration.

This gate applies in **all three material-chain modes**, including `none` and `preserve-conflicting-constraints`. Emitting a chain alone does not suppress these additions, and preservation mode does not override their gate. Assess whether a proposed addition introduces an additional violation; do not require the existing ontology to satisfy an overall OWL 2 DL guarantee.

The additions leave established cardinality, [relation-set disjointness](#generalization-and-disjointness), [source-specific mereology](mereology.md#source-specific-properties), and imported vocabulary mappings and their omission/preservation policies unchanged. Do not remove other accepted axioms to accommodate the five additions. This introduces no semantic validation, consistency checking, source-model repair, or overall OWL 2 DL guarantee. The OWL definitions are in [W3C OWL 2 Structural Specification, §§11.1–11.2](https://www.w3.org/TR/2012/REC-owl2-syntax-20121211/).

## Relation cardinalities

The **target-end** multiplicity constrains source-class instances through the primary property. The **source-end** multiplicity constrains target-class instances through the inverse direction. Both become necessary conditions using `rdfs:subClassOf`, not exhaustive class definitions.

Use unqualified `owl:minCardinality`, `owl:maxCardinality`, and `owl:cardinality`; there is no qualified-restriction switch. Global domain/range axioms remain. For reverse-side constraints, use the corresponding named inverse when generated, otherwise an anonymous inverse of the primary property. This does not force a named inverse or permit dropping reverse restrictions. [Chain steps use a different direction rule](inverses.md#direction-and-anonymous-inverses).

| Multiplicity | Cardinality contribution |
| --- | --- |
| `n` or `n..n`, including zero | Exact `n` |
| `0..u`, finite `u > 0` | Maximum `u` only |
| `l..u`, `0 < l < u` | Minimum `l` and maximum `u` |
| Contradictory nonnegative bounds, `l > u` | Minimum `l` and maximum `u`; no diagnostic solely for the contradiction, under every policy |
| `*` or `0..*` | None; no diagnostic solely for being unbounded |
| `l..*`, positive `l` | Minimum `l`; no invented finite upper bound |
| Explicit JSON `null` | None; no guessed default or diagnostic solely for null |
| Absent field | None; warning and continuation under every input policy |

No numeric restriction does not mean no relation. Null/absence differs from non-null `*` and `0..*` for [informed inverse eligibility](inverses.md#generation-and-eligibility). Present but invalid multiplicities are errors, rather than the absent-field fallback. `strict`/`tolerant` abort; `best-effort` retains error severity and only independently valid, unambiguously positioned bounds where permitted. See [Multiplicity parsing and recovery](../reference/diagnostics.md#multiplicity-parsing-and-recovery) for the full DK-DIAG-10–11 rules.

The following **specification illustration** assumes a named `worksFor` relation from `Person` to `Organization`, target multiplicity `1..*`, source multiplicity `0..1`, named inverses disabled, material chains disabled, name-based identity without collisions, and entity base `https://example.org/employment#`. This parseable excerpt shows direction and restrictions; labels, identifier annotations, ontology header/import, and execution provenance are omitted. It is not executed converter output.

```turtle
@prefix : <https://example.org/employment#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

:worksFor a owl:ObjectProperty ;
    rdfs:domain :Person ;
    rdfs:range :Organization .
:Person a owl:Class ;
    rdfs:subClassOf [ a owl:Restriction ;
        owl:onProperty :worksFor ;
        owl:minCardinality "1"^^xsd:nonNegativeInteger ] .
:Organization a owl:Class ;
    rdfs:subClassOf [ a owl:Restriction ;
        owl:onProperty [ owl:inverseOf :worksFor ] ;
        owl:maxCardinality "1"^^xsd:nonNegativeInteger ] .
```

An absent triple alone does not establish a closed-world minimum violation. Contradictory bounds can make a class unsatisfiable. Separately, [material-chain omission](derivations-and-chains.md#material-chain-modes) removes restrictions only when their property expression becomes non-simple through actually emitted chains and accepted propagation.

## Generalization and disjointness

An explicit relation generalization emits `SpecificProperty rdfs:subPropertyOf GeneralProperty` using the successfully generated **primary** properties and their established directions. No endpoint-class, domain, range, or semantic-orientation compatibility check is required. Unresolved references and failed underlying transformations remain structural errors. When both named inverses exist, [explicit inverse specialization](inverses.md#explicit-inverse-specialization) is additionally required; do not materialize transitive closure.

A relation generalization set with `isDisjoint: true` adds pairwise `owl:propertyDisjointWith` among the primary properties for its explicit specific relations. For each pair, also emit the corresponding named-inverse pair when both inverses exist; otherwise omit that inverse pair without a warning or forced inverse. `false` supplies no disjointness from that flag. A singleton has no pair. Other applicable disjointness remains.

Property disjointness means the same ordered pair cannot belong to both properties; it does not make their endpoint classes disjoint or create relationship-occurrence resources. Under `none` and `preserve-conflicting-constraints`, independently applicable pairs remain. Under `omit-conflicting-constraints`, omit only pairs containing an expression made non-simple by emitted material chains, including propagated effects; retain unrelated pairs.

**OWL 2 DL requires simple properties for these disjointness axioms.** Chains can make participating properties non-simple, so retaining such an axiom can move the result outside OWL 2 DL (E08 / DK-REL-15; DK-DIAG-07). See [OWL compatibility](derivations-and-chains.md#owl-compatibility) for the required explanation and reasoner consequences.

## Relation-set completeness

**Coverage for a complete relation set with at least two distinct specifics is not represented** (E05 / DK-REL-16). DirectKG emits neither a completeness axiom nor a substitute validation constraint. A nonfatal warning identifies the set and omitted coverage, even under `strict`. Properties, ordinary subproperty mappings, inverses, and applicable disjointness remain. OWL property chains express composition, not a union of alternative properties; they do not repair this omission.

`isComplete: false` contributes no completeness axiom or warning solely for that flag. This relation limitation does not change [class-set coverage](classes.md#generalization-sets).

### Fully resolved singleton

For exactly one member generalization in a fully resolved complete relation set, with both primary properties successfully generated, add `GeneralProperty rdfs:subPropertyOf SpecificProperty` alongside ordinary specific-to-general inclusion. Do not add `owl:equivalentProperty` for this mapping. Together the two directions make the properties extensionally equivalent while retaining distinct identifiers and directions.

If both named inverses exist, add the corresponding general-inverse-to-specific-inverse inclusion alongside their ordinary specialization. An absent inverse means this extra axiom is omitted without a warning; do not create a named or anonymous inverse solely for completeness. Applying singleton completeness requires nonfatal INFO identifying the set, general, specific, and equivalence consequence. Membership alone is not a warning and supplies no disjoint pair.

The added hierarchy participates in material-chain non-simplicity propagation; the hierarchy axioms themselves are not targeted for omission. Do not apply singleton completeness merely because partial failure leaves one member of a larger set. An explicitly empty membership array follows the structural-error policy: `strict`/`tolerant` abort; `best-effort` reports the error and omits that set's contribution. Duplicate membership and missing/malformed membership-container handling remain unspecified. Class-set recovery does not establish an additional relation-set recovery algorithm.

## Relation-valued endpoints

An endpoint resolving to a source `Relation` differs from an unresolved endpoint. It does not supply an ordinary class domain/range.

| Resolved connector pattern | Accepted handling |
| --- | --- |
| `derivation`: material–relator or material–mode | Transformation-time information under [Recognized derivations](derivations-and-chains.md#recognized-derivations); no separate connector property |
| `derivation`: comparative–quality | Ordinary comparative relation retained; connector semantics unsupported with its specific nonfatal diagnostic |
| Other resolved binary relation-valued pattern with no accepted mapping | No connector resource/property, named or anonymous inverse, domain/range/cardinality axiom, reification, punning, or grounding annotation; nonfatal limitation warning under every policy |

For the last case, identify the connector and lack of an accepted endpoint-pattern mapping. Retain independently transformable endpoint classes and relations. Do not infer missing stereotypes, alter endpoint identity, or reinterpret the connector to fit a supported pattern. Null, malformed, or unresolved endpoints remain structural errors and cannot use this omission fallback. Ordinary relation qualifiers are documented in [Property features](property-features.md); the mereological bridge has its [own direction rule](mereology.md#source-specific-properties).

---

Governing rules: DK-REL-01–06, 09–17, 20; DK-GEN-03; DK-INV-12; DK-DIAG-07, 09–12, 14; baseline consolidated: **2026-10-21**; repository commit: `a36322fa87c006cece63aaadd2aa5ccd513f6087`; source: [`documentation/specification/2026-10-21 - specification handoff.md`](https://github.com/pedropaulofb/ontouml-directkg/blob/a36322fa87c006cece63aaadd2aa5ccd513f6087/documentation/specification/2026-10-21%20-%20specification%20handoff.md).

Accepted update: **RD-17 — Five relation-axiom additions with per-axiom OWL 2 DL compatibility** (project-owner formalization supplied after this baseline).

Accepted update: **RD-18 — Comment preservation of `begin` and `end` property stereotypes** (project-owner formalization supplied after this baseline).

Accepted update: **RD-17 — Ordinary mapping of `historicalDependence` with the applicable limitation warning (Alternative A)** (project-owner formalization supplied after this baseline).
