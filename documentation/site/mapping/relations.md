# Binary relations

This page explains **accepted intended mappings**. Revision-pinned execution notes identify the cases checked against the converter. Ordinary relations, generalizations, and relation-valued connectors have different output boundaries. DirectKG retains stated directions rather than repairing a model's semantics.

## Primary direction and naming

An eligible ordinary binary relation with two resolved `Class` endpoints follows one of two primary-property branches according to its endpoint classification (`DK-REL-01`, `DK-GEN-03`):

- **Class-to-class ordinary relation (`owl:ObjectProperty`):** When both source and target resolve to `Class` elements with generated local `owl:Class` representations (domain classes, custom `datatype` classes, and `enumeration` classes), DirectKG generates an IRI-identified `owl:ObjectProperty` with `rdfs:domain` equal to the source's local `owl:Class` and `rdfs:range` equal to the target's local `owl:Class`.
- **Datatype-valued ordinary relation (`owl:DatatypeProperty`):** When the source resolves to a `Class` with a generated local `owl:Class` and the target resolves to a supported primitive `datatype` (`stereotype == "datatype"`, resolving via the existing [nine-entry primitive registry](attributes-and-datatypes.md#primitive-registry) under `DK-DAT-02`), and all compatibility rules below hold, DirectKG generates an IRI-identified `owl:DatatypeProperty` with `rdfs:domain` equal to the source's local `owl:Class` and `rdfs:range` equal to the registered XSD datatype.

Relations with relation-valued endpoints follow the [specialized connector boundary](#relation-valued-endpoints) instead. Attributes retain their separate [type mappings](attributes-and-datatypes.md#property-kinds-and-ranges).

Every non-`«instantiation»` `Relation` (ordinary or `derivation`) requires a 2-element `properties` array of `Property` objects (`DK-DIAG-03`). Absent, explicit `null`, non-array, malformed (non-object or non-`Property` entries), empty, unary, or unsupported n-ary (`>= 3` ends) containers trigger a structural **ERROR** (`strict` and `tolerant` abort; `best-effort` omits the affected relation and all dependent output—without generating primary or inverse properties, annotations, cardinalities, bridges, chains, grounding/derivation recognition, or attribute mappings from its ends—and joins the omitted-relations set, without adding n-ary relation support). See [Non-binary and malformed relation properties containers](../reference/diagnostics.md#non-binary-and-malformed-relation-properties-containers) for `«instantiation»` container rules, diagnostic precedence, `DK-PROP-03` suppression, and current `NotImplementedError` implementation status in `source.py` and `relations.py`. Similarly, a `Relation` with a malformed `stereotype` value (non-`null`, non-string JSON value or empty/whitespace-only string) triggers a structural **ERROR** under `DK-DIAG-05` (`strict` and `tolerant` abort; `best-effort` omits the `Relation` and its `Relation.properties` descendants at element level and joins the omitted-relations set), whereas a malformed `stereotype` on a valid `Property` association end omits only that field under `best-effort` and preserves the enclosing `Relation`; see [Malformed stereotype values](../reference/diagnostics.md#malformed-stereotype-values).

Malformed Boolean flags on surviving ordinary `Relation` elements (`isAbstract`, `isDerived`) or their association-end `Property` objects (`isDerived`, `isReadOnly`, `isOrdered`) are structural **ERROR**s under `DK-DIAG-05` (`strict` and `tolerant` abort; `best-effort` retains **ERROR** severity, omits only the malformed flag field and its comment or `DK-DIAG-15`/`16`/`18` INFO, and preserves the `Relation`, both ends, valid sibling flags, and independent mappings). Validation is strictly restricted to each element type's defined Boolean flags—so `isReadOnly`/`isOrdered` on `Relation` and `isAbstract` on `Property` remain governed by `UNKNOWN_INFORMATION`—and earlier omissions (`«instantiation»`, malformed/non-binary `Relation.properties`, unresolved or relation-valued endpoints under `DK-REL-08`, `DK-REL-17`, and `DK-REL-18`) retain precedence before flag validation. See [Malformed Boolean flags](../reference/diagnostics.md#malformed-boolean-flags) for policy outcomes and current `NotImplementedError` / `relations.py` over-check status.

For an eligible ordinary relation (whether `owl:ObjectProperty` or compatible `owl:DatatypeProperty`), explicit recognized `begin` or `end` stereotypes on its association ends follow [boundary stereotype comment placement](property-features.md#boundary-stereotype-comments): identify each source/target occurrence on the successfully generated primary property, independently of named-inverse generation. The relation's logical mappings remain unchanged.

Under name-based identity, choose the primary property's lexical candidate in this order:

1. Usable relation name.
2. Usable **target-end** role name.
3. Applicable stereotype-derived semantic name, when enabled and its required endpoint roles are distinguishable.
4. Synthesized source–target name.
5. Applicable qualification and deterministic collision resolution.

The source-end role does not name the primary property. Supported localized fields use the [original-text selector](../reference/identifiers.md#multilingual-naming) before naming (including for primitive recognition on localized datatype targets), subject to `DK-LBL-02` carrier validation and `best-effort` omission of malformed fields or invalid `languageString` entries (if zero valid usable entries remain, the next naming-precedence step applies; see [Malformed textual and language-tag carriers](../reference/diagnostics.md#malformed-textual-and-language-tag-carriers)). The endpoint fallback is `lowerFirst(normalize(source.name)) + "_" + lowerFirst(normalize(target.name))`: change only the first character, not the whole classifier name. Unnamed endpoints first receive their established synthetic identifiers, which may supply these components. General normalization, source-ID fallback, and collisions remain owned by [Identifiers and naming](../reference/identifiers.md#names-escaping-and-collisions).

### Datatype-valued relations and compatibility

Datatype-valued ordinary binary relations (`Class → Primitive` → `owl:DatatypeProperty`) reuse `DK-DAT-02`'s existing nine-entry primitive registry and introduce no new datatype mappings, aliases, local classes for registered primitives, or configuration options. This branch is a narrowly scoped exception to the `owl:ObjectProperty` and inverse-generation assumptions of class-to-class relations; it preserves existing property identity (`DK-IRI-06` target-end ID under `id`, `DK-IRI-09` `dcterms:identifier` under `name`), primary direction, naming (`DK-REL-02–04`), labels (`DK-LBL-01`), descriptions (`DK-LBL-02`), applicable annotations (`isDerived`, relation `isAbstract`, `isReadOnly`/`SHARED`/`COMPOSITE` aggregation on compatible non-mereological relations, `isOrdered` with `DK-DIAG-18` INFO, `begin`/`end`), and representable target-end multiplicity constraints (`DK-REL-10–13`).

**Compatibility principle:** DirectKG applies all compatible established mappings. When two applicable transformation requirements cannot both be satisfied, DirectKG reports a structural transformation **ERROR** identifying the affected relation, property reference, or dependent mapping and explaining the conflict, rather than arbitrarily prioritizing one requirement or silently discarding meaningful information.

- **Endpoint rejections:**
  - **`Class → void`:** When the target endpoint resolves to Visual Paradigm `void` (`stereotype == "datatype"`), DirectKG reports a structural **ERROR** because `void` has no registered datatype mapping and **must not** generate a rangeless datatype property. (This differs from `void`-typed attributes, which remain rangeless `owl:DatatypeProperty` declarations with a nonfatal warning under [Untyped and void](attributes-and-datatypes.md#untyped-and-void).)
  - **Source without a generated local `owl:Class`:** When the source endpoint resolves to a supported primitive `datatype`, `void`, or any other `Class` lacking a generated local `owl:Class` (`Primitive/void → Class` or `Primitive/void → Primitive/void`), DirectKG rejects the relation with a structural **ERROR** (`DK-DIAG-03`, `DK-DIAG-05`). It must not reverse relation direction, invent a local OWL class, or reinterpret the source endpoint. Custom `datatype` classifiers retain their local `owl:Class` and `owl:ObjectProperty` mappings.
- **Stereotype compatibility:**
  - **Rejected stereotypes (`ERROR`):** Datatype-valued relations carrying any of the eight object-property-only stereotypes **`componentOf`**, **`memberOf`**, **`subCollectionOf`**, **`subQuantityOf`**, **`characterization`**, **`mediation`**, **`participational`**, or **`externalDependence`** must be rejected with a structural **ERROR** before IRI allocation and naming.
  - **Compatible stereotypes:** `historicalDependence`, `participation`, `creation`, `termination`, `manifestation`, `bringsAbout`, `triggers`, and accepted missing or custom stereotypes (`DK-DIAG-06`) retain the datatype-property mapping when otherwise compatible, preserving naming rules, annotations, and limitation or residual-semantics warnings. Never infer, repair, replace, or discard stereotypes merely to make another mapping applicable.
  - **`material` relations:** Enabling `--material-property-chains` (`omit-conflicting-constraints` or `preserve-conflicting-constraints`) alone is **not** a conflict. DirectKG reports a structural compatibility **ERROR** only when an applicable, unambiguous [material-property-chain mapping](derivations-and-chains.md#material-chain-modes) actually requires an incompatible `owl:ObjectProperty` representation. Under `best-effort`, when a required `mediation` or `characterization` grounding relation fails (or an incomplete or ambiguous pattern prevents chain emission), DirectKG preserves the independently valid datatype-valued `material` relation rather than propagating the grounding failure.
  - **`comparative` relations:** Retain the datatype-property mapping when otherwise compatible; report a structural compatibility **ERROR** if an explicitly recognized [comparative–quality derivation](derivations-and-chains.md#recognized-derivations) activates `DK-REL-18`'s requirement for an ordinary `owl:ObjectProperty`. Under `best-effort`, omit the comparative relation and dependent output while preserving the grounding quality and independent mappings.
- **Inverses and source-end role metadata:**
  - Datatype-valued relations are not [inverse-eligible](inverses.md#generation-and-eligibility); selecting `--inverse-properties` (`all`, `informed`, `named`, or `none`) never independently causes a compatibility **ERROR**.
  - When an explicit, nonempty source-end role name (non-whitespace under `DK-INV-05`) on an otherwise compatible datatype-valued relation cannot be represented because no inverse property exists, DirectKG emits a **nonfatal WARNING under every input policy, including `strict`**, without treating the role name as a structural conflict. Source-end descriptions are omitted without an extra diagnostic per `DK-LBL-02`.
- **Check timing and clean `best-effort` recovery:** Relation-local incompatibilities (endpoint rejections, the eight rejected stereotypes, and incompatible source-end multiplicities—including invalid source-end multiplicities with meaningful recoverable reverse bounds under `best-effort`) are detected **before property IRI allocation and naming**. Dependent-mapping incompatibilities (`DK-REL-18` comparative–quality derivation and `DK-REL-07` eligible material chain) are evaluated where required information is available. Under `strict` and `tolerant`, compatibility **ERROR**s abort (`aborted`, no ontology delivered). Under `best-effort`, DirectKG retains **ERROR** severity, omits only the affected relation or dependent axiom, and preserves independently transformable output with **zero** orphaned inverse expressions, property hierarchies, cardinality restrictions, annotations, property inclusions, or chain axioms referring to an omitted relation.

For example, suppose `Person` (`kind`) has a compatible ordinary binary relation `birthDate` targeting primitive `string` (`datatype`) with target multiplicity `1`, source multiplicity `0..*`, name-based identity without collisions, and entity base `https://example.org/people#`. This **specification illustration**, not captured converter output, shows only the core datatype property and restriction (omitting header/import, labels, identifier annotations, and provenance):

```turtle
@prefix : <https://example.org/people#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

:birthDate a owl:DatatypeProperty ;
    rdfs:domain :Person ;
    rdfs:range xsd:string .

:Person a owl:Class ;
    rdfs:subClassOf [ a owl:Restriction ;
        owl:onProperty :birthDate ;
        owl:cardinality "1"^^xsd:nonNegativeInteger ] .
```

**Implementation status.** At [specification registration revision `283f9b01361830c2dfb1e96b08111e1f8f849b31`](https://github.com/pedropaulofb/ontouml-directkg/blob/283f9b01361830c2dfb1e96b08111e1f8f849b31/src/ontouml_directkg/relations.py#L119-L120), `collect_relations` in `src/ontouml_directkg/relations.py` still raises `NotImplementedError("Ordinary relation endpoints without local class representations remain unspecified")` when either endpoint lacks a generated local `owl:Class` (caught in `conversion.py` as `INTERNAL_TRANSFORMATION_FAILURE` and aborting under every policy). The datatype-valued relation branch and endpoint/compatibility rules above describe accepted intended behavior.

### Semantic naming candidates

The following candidates apply when the stereotype step is reached, subject to the [structural-evidence conditions](#structural-evidence-for-semantic-naming). Source–target positions alone do not establish every semantic role in the table. This table does not authorize semantic orientation checks, reversal, or repair.

| Stereotype | Primary direction | Candidate |
| --- | --- | --- |
| `bringsAbout` | Event → Situation / Situation → Event | `bringsAbout` / `broughtAboutBy` |
| `characterization` | Bearer → Feature / Feature → Bearer | `isCharacterizedBy` / `characterizes` |
| `componentOf` | Whole → Component / Component → Whole | `hasComponent` / `componentOf` |
| `creation` | Event → Endurant / Endurant → Event | `creates` / `wasCreatedIn` |
| `externalDependence` | Extrinsic Mode → Endurant / Endurant → Extrinsic Mode | `externallyDependsOn` / `isExternalDependencyOf` |
| `historicalDependence` | Dependent → Antecedent / Antecedent → Dependent | **Unavailable for automatic selection:** `historicallyDependsOn` / `isHistoricalDependencyOf` |
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

An unnamed `material` relation without a usable target role instead attempts its grounding **relator's** name at this step: `lowerFirst(normalize(relator.name))` (using `DK-IRI-10` subject to `DK-LBL-02` carrier validation and `best-effort` entry omission, falling back if zero valid usable entries remain), with no `has` prefix. The property still connects its participant classes, not a relator individual. Successful relator-based naming should produce an informational provenance diagnostic and requires no warning merely for that success. An unavailable usable grounding relator requires a warning, then the endpoint fallback; the initial diagnostic need not distinguish absence, ambiguity, or unusable naming. No special mode-grounded material name is established.

`comparative` has no generic semantic predicate: reaching that step requires a warning before the endpoint fallback. An unnamed ordinary relation using a target-role or source–target fallback requires a nonfatal warning unless a specific rule replaces it. If both an endpoint and its relation are unnamed, their diagnostics should distinguish the conditions. Covered derivation connectors do not enter ordinary naming fallback. See [Recognized derivations](derivations-and-chains.md#recognized-derivations).

Original relation/target-role labels and descriptions have their [separate text rules](../reference/text.md#labels-and-descriptions); lexical identity is not a substitute for a label. Primary-property IDs use the target association-end ID under ID-based construction, as specified in [Strategy and renaming](../reference/identifiers.md#strategy-and-renaming).

### Structural evidence for semantic naming

Use the structured JSON and its represented direction as authoritative. In the supported binary representation, `properties[0]` is the source end and `properties[1]` the target end; their `propertyType` references identify the endpoint classifiers. These positions establish the primary direction, without supplying unstated semantic roles. Earlier usable relation names and target-end role names still supply lexical text in their established precedence; do not interpret that text as role evidence.

**Verified execution at [revision `6aba9b8819b35648d920802c598f4a35bfe32d1d`](https://github.com/pedropaulofb/ontouml-directkg/commit/6aba9b8819b35648d920802c598f4a35bfe32d1d).** Focused Python cases exercised the direction-specific candidates and the six structural selectors below, including endpoint fallback when evidence was insufficient. Separate `strict` cases with two collective endpoints for `memberOf` and two mode endpoints for `characterization` completed with the source–target name, retained the primary property direction and source identifier, and reported the naming warning. [Naming checks](https://github.com/pedropaulofb/ontouml-directkg/blob/6aba9b8819b35648d920802c598f4a35bfe32d1d/tests/transformation/test_relations.py#L95)

**Historical source observation.** The [`4fdef7bbaf8b73bf1ed0ff47fc793494493083dc` source](https://github.com/pedropaulofb/ontouml-directkg/blob/4fdef7bbaf8b73bf1ed0ff47fc793494493083dc/src/ontouml_directkg/relations.py) raised `NotImplementedError` when semantic naming reached any of the six stereotypes below.

| Stereotype | Supported evidence for the table's lexical roles |
| --- | --- |
| `componentOf` | Exactly one whole-marked end identifies the whole occurrence; the opposite occurrence is the component. |
| `participational` | Exactly one whole-marked end identifies the whole event; the opposite occurrence is the part event. |
| `subCollectionOf` | Exactly one whole-marked end identifies the supercollection; the opposite occurrence is the subcollection. |
| `subQuantityOf` | Exactly one whole-marked end identifies the superquantity; the opposite occurrence is the subquantity. |
| `externalDependence` | Exactly one endpoint classifier explicitly has stereotype `mode`; the other explicitly has a supported non-`mode` endurant stereotype listed below. The mode occurrence supplies the lexical mode role. |
| `historicalDependence` | No accepted explicit discriminator identifies Dependent versus Antecedent under the current input contract. Use endpoint fallback; see [Historical dependence](#historical-dependence). |

An end is **whole-marked** only by explicit `aggregationKind: "SHARED"` or `aggregationKind: "COMPOSITE"`. Absent, null and `"NONE"` values supply no marker. With zero or two marked ends, the roles remain undetermined: do not prefer `COMPOSITE` over `SHARED` or break ties using endpoint position. A unique marker supplies the whole/super role for lexical selection while preserving the primary direction shown in the candidate table.

For `externalDependence`, the complete supported non-`mode` endurant set is `kind`, `collective`, `quantity`, `relator`, `quality`, `subkind`, `role`, `phase`, `historicalRole`, `category`, `mixin`, `roleMixin`, `phaseMixin`, and `historicalRoleMixin`. Both or neither endpoint explicitly carrying `mode`, or an opposite endpoint outside this set, leaves the roles undetermined. The table's “Extrinsic Mode” denotes a lexical role, not a separate required exported stereotype. Do not introduce intrinsic/extrinsic stereotype aliases or use `restrictedTo`, which remains deliberately omitted.

For these six selectors, do not infer roles through inheritance searches, custom assignments, names, labels, descriptions or other heuristics. DirectKG does not detect or correct potential modeling mistakes. When evidence is insufficient, continue to the established source–target fallback; that uncertainty alone neither omits the relation nor aborts conversion. Existing malformed-input, reference-resolution and diagnostic rules still apply.

These criteria select lexical candidates only. Identity construction, inverses, domains/ranges, cardinalities, annotations and logical mappings retain their existing rules. In particular, an aggregation marker does not change the eligibility or direction of the [DKGM bridge](mereology.md#source-specific-properties). Generated labels under either IRI strategy use the selected lexical candidate before IRI-only processing, without an additional naming diagnostic solely for label generation. Other stereotype-specific naming, normalization, collision and control rules remain unchanged.

The following are **specification illustrations, not converter output**. Assume endpoint names `A` and `B`, primary direction A → B, no usable relation or target-role name, and stereotype naming enabled:

| Source declaration | Selected lexical candidate |
| --- | --- |
| `componentOf`; source end `NONE`, target end `COMPOSITE` | `componentOf` |
| `componentOf`; source end `SHARED`, target end `NONE` | `hasComponent` |
| `componentOf`; zero or two whole-marked ends | `a_b` |
| `externalDependence`; source classifier `mode`, target classifier `kind` | `externallyDependsOn` |
| `externalDependence`; both classifiers `mode` | `a_b` |
| `historicalDependence`; no accepted role discriminator | `a_b` |

Every row retains A → B as the primary direction; neither endpoint name supplies semantic-role evidence.

### Historical dependence

An eligible ordinary relation carrying recognized `historicalDependence` retains its ordinary property identity, direction, naming, labels, descriptions, domain, range, inverses, cardinalities, and applicable generalization mappings. **Historical-dependence semantics are only partially translated** through this ordinary mapping. The stereotype alone supplies no additional logical axioms or annotations recording its declaration. The general metadata permission in DK-GEN-11 does not override this omission.

Source-description mappings and independently required annotations remain applicable. Earlier relation-name and target-role terminology retains precedence. When the semantic naming step is reached, neither specialized historical-dependence candidate is automatically selectable: use the source–target fallback and its corresponding [generated fallback label](../reference/text.md#primary-relation-labels) when enabled. Endpoint positions, `historicalRole`, multiplicities and read-only flags do not identify Dependent or Antecedent. Source-label and language rules remain unchanged; omitting a stereotype-declaration annotation does not suppress these lexical or descriptive mappings.

The existing nonfatal [limitation warning](../reference/diagnostics.md#names-typing-and-source-text) for a deliberately unmapped applicable relation stereotype still applies under DK-DIAG-01. Naming success or fallback does not suppress this warning; no warning-suppression exception is established for `historicalDependence`.

### Participation, creation, and termination

Eligible ordinary relations carrying `participation`, `creation`, or `termination` retain their existing property identity, direction, naming, labels, descriptions, domains, ranges, cardinalities, inverses, and applicable generalization mappings. **Their stereotype semantics are only partially translated.** Ordinary properties and explicit source constraints do not, by themselves, enforce the full participation, creation, or termination semantics (DK-REL-01 / RD-17).

These stereotypes alone add no logical axioms or annotations recording their declaration. This exclusion does not remove source descriptions, labels, applicable source-ID annotations, association-end annotations, or other independently required output. The [automatic metadata permission](../guides/metadata-and-provenance.md#optional-automatic-enrichment) does not override it.

The existing naming precedence and [semantic candidates](#semantic-naming-candidates) remain applicable: relation names and target-role names take precedence over stereotype naming. Successful naming does not establish full semantic preservation or suppress the applicable [limitation warning](../reference/diagnostics.md#names-typing-and-source-text). Disabling stereotype-derived naming changes lexical selection under its existing rules; it does not suppress independently applicable limitation reporting.

The limitation warning is **nonfatal under every input policy, including `strict`**. Independently applicable errors and abort conditions remain in force. Existing diagnostic consolidation, content restrictions, console filtering, JSON reporting, and delivery rules still apply; this decision selects no diagnostic identifier or diagnostic-count requirement.

`participation` and `participational` are distinct stereotypes. The accepted [asymmetry for `participational`](#additional-relation-axioms) and its [per-axiom compatibility gate](#compatibility-of-each-addition) remain unchanged; its [remaining semantic limitation](#participational-and-manifestation) has separate warning requirements. No temporal subsystem, semantic validation, source repair, or general OWL-profile guarantee is introduced.

For example, suppose an unnamed `creation` relation runs from an endurant class `active_entity` to an event class `process`, with no usable target-role name and stereotype naming enabled. Assume entity base `https://example.org/model#` and no naming collisions. Under the applicable name-based rules, this **specification illustration** shows only the primary property's core mapping:

```turtle
@prefix : <https://example.org/model#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

:wasCreatedIn a owl:ObjectProperty ;
    rdfs:domain :active_entity ;
    rdfs:range :process .
```

This is a partial graph, not captured converter output. It omits the ontology header/import, class declarations, annotations, cardinality restrictions, named inverse, and provenance; their independently applicable mappings still apply. The fragment does not establish a complete temporal lifecycle theory. Domain and range retain their [inferential meaning](../concepts/semantics.md#domain-graph-and-inferential-axioms).

**Verified warning cases at [revision `6aba9b8819b35648d920802c598f4a35bfe32d1d`](https://github.com/pedropaulofb/ontouml-directkg/commit/6aba9b8819b35648d920802c598f4a35bfe32d1d).** The Python conversions for all three stereotypes completed with the ordinary properties and their residual-semantics warnings, including tested `strict` cases and cases with stereotype naming disabled. [Partial-semantics checks](https://github.com/pedropaulofb/ontouml-directkg/blob/6aba9b8819b35648d920802c598f4a35bfe32d1d/tests/transformation/test_relations.py#L2332)

**Historical source observation.** At [`d74c0e7da378d88abbf5c400d2e7b3d6488dc35a`](https://github.com/pedropaulofb/ontouml-directkg/blob/d74c0e7da378d88abbf5c400d2e7b3d6488dc35a/src/ontouml_directkg/relations.py), the ordinary relation handler had a limitation-warning branch for `historicalDependence` and lacked one for these three stereotypes.

### Participational and manifestation

Eligible ordinary `participational` (when mapped to `owl:ObjectProperty`; rejected with a structural **ERROR** when targeting a supported primitive) and `manifestation` (including compatible datatype-valued `manifestation` relations) retain their existing property identity, direction, naming, labels, descriptions, domains, ranges, explicit cardinalities, applicable inverses, generalizations, and independently required annotations. **Their semantics are only partially translated:** ordinary mappings and applicable `participational` asymmetry do not, by themselves, establish full participant-dependent decomposition or manifestation semantics (DK-REL-01 / RD-17).

`participational` retains its [asymmetry declaration](#additional-relation-axioms), subject to the existing [compatibility gate](#compatibility-of-each-addition). In every material-chain mode, the gate accounts for the property hierarchy and inverse relationships in the generated graph and applicable import closure. `manifestation` alone supplies no additional property characteristic. Neither stereotype supplies further stereotype-only logical axioms or annotations recording its declaration. Independently required source descriptions, labels, source-ID annotations, association-end annotations, and other axioms remain applicable; the [automatic metadata permission](../guides/metadata-and-provenance.md#optional-automatic-enrichment) does not override this exclusion.

Existing naming precedence, language handling, and controls remain applicable. In particular, `participational` semantic naming still requires [exactly one whole-marked end](#structural-evidence-for-semantic-naming); endpoint positions or descriptive text cannot supply missing role evidence. Successful naming does not establish complete semantic preservation.

When an eligible ordinary relation carrying either stereotype is successfully mapped, report the remaining semantic limitation through a **WARNING, nonfatal under every input policy, including `strict`**. Successful naming or generation of `participational` asymmetry does not suppress this warning; it also applies when the compatibility gate omits that asymmetry. Disabling stereotype naming does not suppress it. Independently applicable errors and abort conditions retain their existing behavior. Existing diagnostic consolidation, content restrictions, console filtering, [JSON reporting](../reference/diagnostics.md#shared-json-report-contract), and delivery rules apply; this decision prescribes no exact diagnostic identifier, wording, or count.

For a **specification illustration**, assume unnamed relations with no usable target-role names: event `ParticipantEvent` → event `Meeting`, with exactly one whole-marked end at `Meeting`; and mode `Disposition` → event `ManifestationEvent`. Assume name-based identity, stereotype naming enabled, entity base `https://example.org/model#`, no naming collisions, and a passing asymmetry compatibility check:

```turtle
@prefix : <https://example.org/model#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

:participationalPartOf
    a owl:ObjectProperty, owl:AsymmetricProperty ;
    rdfs:domain :ParticipantEvent ;
    rdfs:range :Meeting .

:manifestedIn
    a owl:ObjectProperty ;
    rdfs:domain :Disposition ;
    rdfs:range :ManifestationEvent .
```

These are partial graph fragments, not captured converter output. The ontology header/import, class declarations, explicit cardinalities, inverses, labels, descriptions, identifiers, other applicable annotations, and provenance are omitted from the illustration; their governing rules remain applicable. The fragments supply neither a full participant-based decomposition of the meeting nor a complete dispositional or triggering theory. This decision introduces no temporal subsystem, generic event-parthood vocabulary extension, semantic validation, source repair, or overall OWL-profile guarantee.

**Verified warning cases at [revision `6aba9b8819b35648d920802c598f4a35bfe32d1d`](https://github.com/pedropaulofb/ontouml-directkg/commit/6aba9b8819b35648d920802c598f4a35bfe32d1d).** The Python conversions for `participational` and `manifestation` completed with their residual-semantics warnings. The `participational` cases exercised emission and compatibility-based omission of asymmetry under each input policy. [Partial-semantics checks](https://github.com/pedropaulofb/ontouml-directkg/blob/6aba9b8819b35648d920802c598f4a35bfe32d1d/tests/transformation/test_relations.py#L2332) · [Asymmetry gate checks](https://github.com/pedropaulofb/ontouml-directkg/blob/6aba9b8819b35648d920802c598f4a35bfe32d1d/tests/transformation/test_relations.py#L2557)

**Historical source observation.** The [`fb05478031e290b123e766ad5188e4cef9935357` relation handler](https://github.com/pedropaulofb/ontouml-directkg/blob/fb05478031e290b123e766ad5188e4cef9935357/src/ontouml_directkg/relations.py) lacked a residual-semantics warning for both stereotypes. Its [axiom handler](https://github.com/pedropaulofb/ontouml-directkg/blob/fb05478031e290b123e766ad5188e4cef9935357/src/ontouml_directkg/relation_axioms.py) contained guarded `participational` asymmetry.

### Mediation, characterization, and external dependence

Eligible ordinary `mediation`, `characterization`, and `externalDependence` relations (which require `owl:ObjectProperty` and are rejected with a structural **ERROR** when targeting a supported primitive) retain their existing property identity, direction, naming, labels, descriptions, domains, ranges, explicit cardinalities, inverses, generalizations, and independently required annotations. **These are partial semantic translations:** the retained structural constraints do not encode the complete modal/existential-dependence semantics of these stereotypes (DK-REL-01 / RD-17).

The accepted [property characteristics](#additional-relation-axioms) remain: asymmetry for `mediation` and `characterization`, and irreflexivity for `externalDependence`. [Characterization–external-dependence disjointness](#characterization-and-external-dependence), including its partial illustration, retains its eligibility and direction-alignment rules. The [per-axiom compatibility gate](#compatibility-of-each-addition) applies in every material-chain mode. Existing grounding roles, [derivation treatment and optional material chains](derivations-and-chains.md#recognized-derivations), and mode-specific constraint policies remain applicable.

Beyond these accepted mappings, the three stereotypes supply no further logical axioms or annotations solely recording their declarations. Source descriptions, labels, applicable source-ID annotations, association-end annotations, and other independently required output remain governed by their existing rules. The [automatic metadata permission](../guides/metadata-and-provenance.md#optional-automatic-enrichment) does not override this exclusion. Naming precedence, structural-evidence conditions, language handling, and controls remain unchanged.

Successfully mapping an eligible ordinary relation with any of these three stereotypes requires a **residual-semantics WARNING, nonfatal under every input policy, including `strict`**. Successful naming, generation of accepted axioms or eligible material chains, and gate-based axiom omission do not suppress it. Disabling stereotype naming does not suppress it either. The warning reports partial translation; it does not imply that the ordinary properties or applicable accepted axioms were discarded.

Independently applicable errors and abort conditions retain their established behavior. Existing diagnostic consolidation, content restrictions, console filtering, [JSON reporting](../reference/diagnostics.md#shared-json-report-contract), and delivery rules apply. This decision selects no exact diagnostic identifier, wording, or count and establishes no new reasoning subsystem, semantic validation, or overall OWL-profile guarantee.

**Implementation status for the five warnings.** Source inspection at `8d4e4acd2ad3bee98c1a425026faa05199381a67` showed the residual-semantics warning branch for `mediation`, `characterization`, `externalDependence`, `bringsAbout` and `triggers` and the separate handler for guarded characteristics and paired disjointness. [Warning branch](https://github.com/pedropaulofb/ontouml-directkg/blob/8d4e4acd2ad3bee98c1a425026faa05199381a67/src/ontouml_directkg/relations.py#L327) · [Axiom handler](https://github.com/pedropaulofb/ontouml-directkg/blob/8d4e4acd2ad3bee98c1a425026faa05199381a67/src/ontouml_directkg/relation_axioms.py)

Focused Python conversions at [revision `6aba9b8819b35648d920802c598f4a35bfe32d1d`](https://github.com/pedropaulofb/ontouml-directkg/commit/6aba9b8819b35648d920802c598f4a35bfe32d1d) completed with residual-semantics warnings for all five. The dependency-relation cases exercised gate-based axiom omission and eligible material-chain generation. For `bringsAbout` and `triggers`, the checks covered successful naming under all three input policies and disabled stereotype naming under `strict`. [Dependency warning checks](https://github.com/pedropaulofb/ontouml-directkg/blob/6aba9b8819b35648d920802c598f4a35bfe32d1d/tests/transformation/test_relations.py#L2587) · [Event warning checks](https://github.com/pedropaulofb/ontouml-directkg/blob/6aba9b8819b35648d920802c598f4a35bfe32d1d/tests/transformation/test_relations.py#L2654)

### BringsAbout and triggers

An eligible ordinary binary `bringsAbout` or `triggers` relation with resolved classifier endpoints becomes a primary `owl:ObjectProperty` (or compatible `owl:DatatypeProperty` when targeting a supported primitive) in the source direction. The ordinary mapping retains its identity, labels, descriptions, domain, range, explicit cardinalities, applicable inverses, applicable generalizations, and independently required output. Existing relation-name and target-role precedence and the [direction-specific naming candidates](#semantic-naming-candidates) apply.

Omit additional logical axioms and declaration annotations based solely on either stereotype. The annotation exclusion also applies to [automatic metadata enrichment](../guides/metadata-and-provenance.md#optional-automatic-enrichment). Preserve independently required annotations and axioms, including applicable source identifiers and association-end annotations. An authored description mentioning either stereotype follows the ordinary [source description and language rules](../reference/text.md#labels-and-descriptions).

**Partial temporal and causal translation.** The ordinary properties and explicit source constraints preserve the modeled event–situation links. The mapping leaves unexpressed when a resulting or triggering situation obtains and which event occurrences cause others.

A successfully mapped eligible ordinary relation carrying either stereotype requires a **residual-semantics WARNING, nonfatal under every input policy, including `strict`**, even when naming succeeds. Existing consolidation, content restrictions, console filtering, Python access and requested JSON delivery follow [the diagnostic contract](../reference/diagnostics.md#diagnostic-collection-and-export). Exact diagnostic identifiers, wording and counts remain unspecified for these warnings. Independently applicable errors and abort conditions retain their governing rules. The implementation-status note above covers both warning cases.

In this **specification illustration**, `TrustorAction` is an event that brings about the situation `HazardousSituation`, which triggers the event `ThreatEvent`. Assume usable source relation names `broughtAboutHazardousSituation` and `contributedToTriggerThreatEvent`, name-based identity with entity base `https://example.org/trust#`, and no naming collisions. The partial Turtle shows the primary properties with illustrative IRIs.

```turtle
@prefix : <https://example.org/trust#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

:broughtAboutHazardousSituation a owl:ObjectProperty ;
    rdfs:domain :TrustorAction ;
    rdfs:range :HazardousSituation .

:contributedToTriggerThreatEvent a owl:ObjectProperty ;
    rdfs:domain :HazardousSituation ;
    rdfs:range :ThreatEvent .
```

The fragment omits class declarations, the ontology header and import, applicable explicit cardinalities, inverses, generalizations, annotations and provenance. These outputs follow their existing rules.

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

Assess **each proposed new axiom separately** against its applicable OWL 2 DL restrictions. Consider the property hierarchy, inverse relationships, and axioms in the generated graph and its applicable import closure. The selected [DKGM vocabulary mode](mereology.md#vocabulary-delivery-modes) determines the contribution to this assessment. In `import`, the gate considers the imported vocabulary. In `embed`, it considers the locally emitted core. In `none`, it uses the generated graph and applicable import closure without assuming axioms supplied separately by the consumer.

Asymmetry and irreflexivity require a simple participating property expression. Paired disjointness requires **both** expressions to be simple. A property used only in a chain body is not non-simple solely because of that use.

Omit a new axiom that fails its simplicity condition; retain other compatible additions. For example, a non-simple characterization expression excludes its new asymmetry declaration and a disjointness pair using it, but does not exclude an otherwise compatible external-dependence irreflexivity declaration.

This gate applies in **all three material-chain modes**, including `none` and `preserve-conflicting-constraints`. Emitting a chain alone does not suppress these additions, and preservation mode does not override their gate. Assess whether a proposed addition introduces an additional violation; do not require the existing ontology to satisfy an overall OWL 2 DL guarantee.

Established cardinality, [relation-set disjointness](#generalization-and-disjointness), [source-specific mereology](mereology.md#source-specific-properties), and selected vocabulary output follow their own omission and preservation rules. Do not remove other accepted axioms to accommodate the five additions. This introduces no semantic validation, consistency checking, source-model repair, or overall OWL 2 DL guarantee. The OWL definitions are in [W3C OWL 2 Structural Specification, §§11.1–11.2](https://www.w3.org/TR/2012/REC-owl2-syntax-20121211/).

## Relation cardinalities

The **target-end** multiplicity constrains source-class instances through the primary property (`owl:ObjectProperty` or compatible `owl:DatatypeProperty`). For class-to-class `owl:ObjectProperty` relations, the **source-end** multiplicity constrains target-class instances through the inverse direction. Both become necessary conditions using `rdfs:subClassOf`, not exhaustive class definitions.

Use unqualified `owl:minCardinality`, `owl:maxCardinality`, and `owl:cardinality`; there is no qualified-restriction switch. Global domain/range axioms remain. For reverse-side constraints on `owl:ObjectProperty` relations, use the corresponding named inverse when generated, otherwise an anonymous inverse of the primary property. This does not force a named inverse or permit dropping reverse restrictions. [Chain steps use a different direction rule](inverses.md#direction-and-anonymous-inverses).

For a **datatype-valued relation (`owl:DatatypeProperty`)**, no named or anonymous inverse datatype property may be generated:

- **Target end:** Preserve representable multiplicities on the primary `owl:DatatypeProperty` using the unqualified restrictions below.
- **Compatible source ends:** Explicit `*`, `0..*`, explicit `null`, and absent `cardinality` (with `DK-DIAG-09`'s nonfatal warning) require no reverse restriction and remain compatible.
- **Incompatible source ends (`ERROR`):** Any valid, meaningful source-end multiplicity requiring a cardinality restriction (`0`, `0..0`, `0..u` with `u > 0`, `l..*` with `l > 0`, or `l..u` with `l > 0` or finite `u`, including contradictory `l > u` intervals) requires an unavailable inverse datatype property and produces a structural **ERROR** before IRI allocation and naming, rather than discarding the constraint or inventing an inverse.
- **`DK-DIAG-10` precedence for invalid source ends:** Invalid source-end multiplicities retain `INVALID_CARDINALITY` **ERROR** (`strict`/`tolerant` abort). Under `best-effort`, inverse unavailability takes precedence over recoverable source-end bounds: if a meaningful recoverable reverse constraint exists (`lower > 0` or finite `upper`), report the compatibility **ERROR** and omit the relation; if no meaningful recoverable reverse constraint exists (such as `"n"`, `"0..n"`, or `"2...*"`), preserve the otherwise compatible datatype property under `DK-DIAG-10`. (Attributes and `owl:ObjectProperty` relations retain ordinary `DK-DIAG-10` recovery.)

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

An explicit relation generalization emits `SpecificProperty rdfs:subPropertyOf GeneralProperty` using the successfully generated **primary** properties and their established directions when **both** relations generate `owl:ObjectProperty` resources or **both** generate `owl:DatatypeProperty` resources (`DK-REL-14`). No endpoint-class, domain, range, or semantic-orientation compatibility check is required. Unresolved references and failed underlying transformations remain structural errors. For homogeneous `owl:ObjectProperty` generalizations, when both named inverses exist, [explicit inverse specialization](inverses.md#explicit-inverse-specialization) is additionally required; for homogeneous `owl:DatatypeProperty` generalizations (which have no inverses), no inverse specialization or warning is emitted. Do not materialize transitive closure.

A relation generalization set with `isDisjoint: true` adds pairwise `owl:propertyDisjointWith` among the primary properties for its explicit specific relations that share the same OWL property kind—both homogeneous `owl:ObjectProperty` pairs and homogeneous `owl:DatatypeProperty` pairs (`DK-REL-15`). For each homogeneous `owl:ObjectProperty` pair, also emit the corresponding named-inverse pair when both inverses exist; otherwise (and for homogeneous `owl:DatatypeProperty` pairs) omit that inverse pair without a warning or forced inverse. `false` supplies no disjointness from that flag. Any non-`null`, non-boolean `GeneralizationSet.isDisjoint` value on a relation set with a valid nonempty `generalizations` array triggers a structural **ERROR** (`strict` and `tolerant` abort; `best-effort` retains **ERROR** severity, omits only the malformed `isDisjoint` field with no `owl:propertyDisjointWith` emitted from it, and preserves valid sibling `isComplete` behavior, independent relation generalizations, and relations; `DK-DIAG-12` retains precedence; see [Malformed Boolean flags](../reference/diagnostics.md#malformed-boolean-flags)). A singleton has no pair. Other applicable disjointness remains.

**Mixed object/data rejections (`DK-REL-14`, `DK-REL-15`):** A relation generalization connecting one `owl:ObjectProperty` and one `owl:DatatypeProperty`, and each cross-kind pair among surviving explicit specifics in a disjoint relation generalization set, triggers a structural **ERROR**. Under `strict` and `tolerant`, conversion aborts. Under `best-effort`, DirectKG retains **ERROR** severity, omits only the incompatible hierarchy edge or cross-kind disjointness pair, and preserves independent properties, valid homogeneous hierarchy edges, and valid homogeneous disjointness pairs. Under `best-effort`, generalizations referencing a relation omitted under `DK-DIAG-03` (including for non-binary or absent/`null`/malformed `Relation.properties` containers) retain `FAILED_RELATION_GENERALIZATION` handling: the hierarchy edge is omitted and singleton completeness / `DK-DIAG-14` INFO are prevented while surviving specifics' disjointness and independent mappings remain intact. Under `best-effort`, an inapplicable non-null `categorizer` on a relation generalization set alone does not suppress valid homogeneous disjointness, and when another member fails, surviving explicit specifics retain applicable homogeneous pairwise disjointness (subject to DK-REL-07's mode-specific omission below). See [Non-null categorizer on relation generalization sets](higher-order.md#non-null-categorizer-on-relation-generalization-sets).

Property disjointness means the same ordered pair cannot belong to both properties; it does not make their endpoint classes disjoint or create relationship-occurrence resources. Under `none` and `preserve-conflicting-constraints`, independently applicable homogeneous pairs remain. Under `omit-conflicting-constraints`, omit only pairs containing an expression made non-simple by emitted material chains, including propagated effects; retain unrelated pairs.

**OWL 2 DL requires simple properties for these disjointness axioms.** Chains can make participating properties non-simple, so retaining such an axiom can move the result outside OWL 2 DL (E08 / DK-REL-15; DK-DIAG-07). See [OWL compatibility](derivations-and-chains.md#owl-compatibility) for the required explanation and reasoner consequences.

## Relation-set completeness

Count members using the [generalization-set membership rule](../reference/input.md#generalization-set-membership). Repeated references to one declaration count once within the set; a fully resolved `[g1, g1]` follows the singleton mapping below when complete. Distinct declarations remain distinct members even when their endpoint classifiers coincide. The input reference records the implementation status of this accepted rule.

**Coverage for a complete relation set with at least two distinct specifics is not represented** (E05 / DK-REL-16). DirectKG emits neither a completeness axiom nor a substitute validation constraint. A nonfatal warning identifies the set and omitted coverage, even under `strict`. Properties, compatible subproperty mappings, inverses, and applicable disjointness remain. OWL property chains express composition, not a union of alternative properties; they do not repair this omission.

`isComplete: false` contributes no completeness axiom or warning solely for that flag. Any non-`null`, non-boolean `GeneralizationSet.isComplete` value on a relation set with a valid nonempty `generalizations` array triggers a structural **ERROR** (`strict` and `tolerant` abort; `best-effort` retains **ERROR** severity, omits only the malformed `isComplete` field—emitting neither `DK-REL-16`'s completeness-limitation warning nor `DK-REL-20`'s singleton completeness or `DK-DIAG-14` INFO—and preserves valid sibling `isDisjoint` axioms, independent relation generalizations, and relations; `DK-DIAG-12` retains precedence; see [Malformed Boolean flags](../reference/diagnostics.md#malformed-boolean-flags)). Under `best-effort`, an inapplicable non-null `categorizer` on a relation generalization set alone does not suppress the multi-member completeness warning when its conditions hold ([Non-null categorizer on relation generalization sets](higher-order.md#non-null-categorizer-on-relation-generalization-sets)). This relation limitation does not change [class-set coverage](classes.md#generalization-sets).

### Fully resolved singleton

For exactly one member generalization in a fully resolved complete relation set, whose general and specific relations both successfully generate primary `owl:ObjectProperty` resources or both generate primary `owl:DatatypeProperty` resources, add `GeneralProperty rdfs:subPropertyOf SpecificProperty` alongside ordinary specific-to-general inclusion. Do not add `owl:equivalentProperty` for this mapping. Together the two directions make the properties extensionally equivalent while retaining distinct identifiers and directions.

For homogeneous `owl:ObjectProperty` generalizations, if both named inverses exist, add the corresponding general-inverse-to-specific-inverse inclusion alongside their ordinary specialization. An absent inverse (or a homogeneous `owl:DatatypeProperty` generalization, which has no inverses) means this extra axiom is omitted without a warning; do not create a named or anonymous inverse solely for completeness. Applying singleton completeness requires nonfatal INFO identifying the set, general, specific, and equivalence consequence. Membership alone is not a warning and supplies no disjoint pair.

The added hierarchy participates in material-chain non-simplicity propagation; the hierarchy axioms themselves are not targeted for omission. A failed relation generalization—including failure due to mixed object/data property kinds under `DK-REL-14`—**must not** activate singleton completeness or `DK-DIAG-14` INFO, and a larger incomplete set **must not** be treated as a valid singleton merely because partial failure leaves one surviving member (including after counting repeated references once). An explicitly empty membership array follows the structural-error policy: `strict`/`tolerant` abort; `best-effort` reports the error and omits that set's contribution. Under `best-effort`, a [missing or malformed membership container](../reference/diagnostics.md#missing-or-malformed-generalization-set-membership) contributes no set-derived disjointness or completeness axioms. An absent or explicit `null` `categorizer` on a relation generalization set remains uncategorized without error; under `best-effort`, an inapplicable non-null `categorizer` alone does not suppress singleton completeness or its DK-DIAG-14 INFO diagnostic when membership is complete, whereas when a member also fails, completeness and DK-DIAG-14 INFO are omitted (including when partial failure leaves one survivor) ([Non-null categorizer on relation generalization sets](higher-order.md#non-null-categorizer-on-relation-generalization-sets)). Independently supported relation generalizations still apply. Class-set recovery does not establish an additional relation-set recovery algorithm.

## Relation-valued endpoints

An endpoint resolving to a source `Relation` differs from an unresolved endpoint. It does not supply an ordinary class domain/range.

| Resolved connector pattern | Accepted handling |
| --- | --- |
| `derivation`: material–relator or material–mode | Transformation-time information under [Recognized derivations](derivations-and-chains.md#recognized-derivations); no separate connector property |
| `derivation`: comparative–quality | Ordinary comparative relation retained; connector semantics unsupported with its specific nonfatal diagnostic |
| Other resolved binary relation-valued pattern with no accepted mapping | No connector resource/property, named or anonymous inverse, domain/range/cardinality axiom, reification, punning, or grounding annotation; nonfatal limitation warning under every policy |

For the last case, identify the connector and lack of an accepted endpoint-pattern mapping. Retain independently transformable endpoint classes and relations. Do not infer missing stereotypes, alter endpoint identity, or reinterpret the connector to fit a supported pattern. Null, malformed, or unresolved endpoints remain structural errors and cannot use this omission fallback. Ordinary relation qualifiers are documented in [Property features](property-features.md); the mereological bridge has its [own direction rule](mereology.md#source-specific-properties).

---

Governing rules: §§3.2–3.4; DK-REL-01–20; DK-GEN-03–05, 11–12; DK-DAT-02, 04–05; DK-CLS-01; DK-HO-04; DK-INV-01–02, 05, 12; DK-IRI-06, 09–10; DK-LBL-01–02; DK-PROP-03–06; DK-DIAG-01–03, 05–07, 09–12, 14–16, 18; §15; baseline consolidated: **2026-11-24**; repository commit: `15eff98eb9dfeed69694ff81f099e0b9785e700f`; source: [`documentation/specification/transformation-specification.md`](https://github.com/pedropaulofb/ontouml-directkg/blob/15eff98eb9dfeed69694ff81f099e0b9785e700f/documentation/specification/transformation-specification.md).

Accepted update: **RD-02 — Malformed Boolean flags (Alternative 1 — Uniform field-level omission)** (project-owner formalization included in the cited consolidation).

Accepted update: **RD-02 — Malformed `stereotype` values on `Class`, `Relation`, and `Property` (Alternative 1C + Sub-option 2A)** (project-owner formalization included in the cited consolidation).

Accepted update: **RD-02 — Malformed textual and language-tag carriers (`name`, `description`, `languageString`, and `Project.languages`; Alternatives 1A + 2A)** (project-owner formalization included in the cited consolidation).

Accepted update: **RD-02 — Non-binary (`len != 2`) and absent/null/malformed `Relation.properties` association-end containers (Alternative A)** (project-owner formalization included in the cited consolidation).

Accepted update: **RD-02 — Datatype-valued ordinary binary relations (`Alternative B + Q1–Q7 + Conflicts A–I`)** (project-owner formalization included in the cited consolidation).

Accepted update: **RD-17 — Five relation-axiom additions with per-axiom OWL 2 DL compatibility** (project-owner formalization included in the cited consolidation).

Accepted update: **RD-18 — Comment preservation of `begin` and `end` property stereotypes** (project-owner formalization included in the cited consolidation).

Accepted update: **RD-17 — Ordinary mapping of `historicalDependence` with the applicable limitation warning (Alternative A)** (project-owner formalization included in the cited consolidation).
