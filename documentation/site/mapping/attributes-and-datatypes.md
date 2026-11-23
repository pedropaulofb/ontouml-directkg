# Attributes and datatypes

These are **accepted intended mappings** for supported attributes and datatype classifiers. They are independent of any unimplemented Python signature or CLI invocation. Global domains/ranges are inferential; see [Semantics and limitations](../concepts/semantics.md#domain-graph-and-inferential-axioms).

## Property kinds and ranges

An attribute's resolved `propertyType` determines its property kind and range; `rdfs:domain` is always its owning class's generated local `owl:Class`. Primitive normalization (`DK-DAT-02`) and Visual Paradigm `void` recognition (`DK-DAT-04`) apply **only** when the resolved target `Class` has `stereotype == "datatype"`.

| Resolved source type | Property kind | Range |
| --- | --- | --- |
| Supported primitive datatype (`stereotype == "datatype"`) | `owl:DatatypeProperty` | Registered XSD datatype |
| Custom `datatype` (`stereotype == "datatype"`) | `owl:ObjectProperty` | Reified custom datatype class |
| `enumeration` | `owl:ObjectProperty` | Generated enumeration class |
| Other `Class` with a generated local `owl:Class` (ordinary OntoUML class stereotypes, `null` stereotype, or unrecognized custom stereotypes accepted under [stereotype policy](../reference/controls.md#established-controls)) | `owl:ObjectProperty` | Target `Class`'s generated local `owl:Class` |
| Explicit `null` | `owl:DatatypeProperty` | None |
| Recognized VP `void` (`stereotype == "datatype"`) | `owl:DatatypeProperty` | None; nonfatal warning |

An enumeration-valued attribute therefore links to enumeration individuals rather than string literals. See [Enumerations and closure](classes.md#enumerations-and-closure). Distinct modeled attributes remain distinct properties even when their names coincide; [identifier disambiguation](../reference/identifiers.md#names-escaping-and-collisions) never changes the property kind.

### Class-valued attributes

Whenever an eligible class attribute's `propertyType` resolves to any `Class` that has a generated local `owl:Class` under `DK-CLS-01`—including custom `datatype`, `enumeration`, ordinary OntoUML class stereotypes (such as `kind`, `subkind`, `role`, `phase`, `category`, `mixin`, `roleMixin`, `phaseMixin`, `relator`, `mode`, `quality`, `event`, `historicalRole`, `situation`, `type`, etc.), a `null` stereotype (accepted under `allow-missing` or `allow-custom`), or an unrecognized custom stereotype (accepted under `allow-custom` with its standard warning under `DK-DIAG-06`)—DirectKG transforms the attribute as an **ordinary `owl:ObjectProperty`** with `rdfs:domain` equal to the owning class's generated local `owl:Class` and `rdfs:range` equal to the target `Class`'s generated local `owl:Class` (aligned with `DK-GEN-03`).

Because primitive normalization and `void` recognition apply only when `stereotype == "datatype"`, a non-`datatype` class named `"string"` or `"void"` (for example with stereotype `kind`) receives its own local `owl:Class`, and an attribute typed by it becomes an `owl:ObjectProperty` targeting that local `owl:Class`.

For attributes transformed as `owl:ObjectProperty` under this rule:

- **No inferred relation stereotypes:** DirectKG generates ordinary `owl:ObjectProperty` declarations and axioms only. It does **not** infer any OntoUML relation stereotype or apply stereotype-specific relation mappings (for example, no `owl:AsymmetricProperty`, `owl:IrreflexiveProperty`, event, dependency, mereological, gUFO, or `dkgm` axioms inferred from attribute `propertyType`, and no derived `Relation` stereotypes).
- **No attribute flattening:** DirectKG does **not** infer or flatten owned attributes of the target `Class` onto the owning class.
- **No named inverses or redundant value restrictions:** Attributes remain excluded from named inverse generation under [Inverse properties](inverses.md#generation-and-eligibility) (`DK-INV-01–02`), and no redundant local `owl:allValuesFrom` restriction is generated (`DK-ATT-04`).
- **All existing attribute rules apply:** Necessary `rdfs:subClassOf` restrictions (`DK-ATT-02`, never `owl:equivalentClass`), preservation of explicit multiplicities (`DK-ATT-03`, with no new multiplicity mapping or configuration option, and subject to `omit-conflicting-constraints` if a property expression becomes non-simple through `subsettedProperties` or `redefinedProperties` hierarchy links beneath an emitted material chain), `isDerived` annotations (`DK-GEN-05`), distinct property identity, owner qualification, `subsettedProperties`/`redefinedProperties` (now subject to `DK-PROP-03`'s global rejection of mixed `owl:ObjectProperty`/`owl:DatatypeProperty` inclusions; see [Subsetting](property-features.md#subsetting)), and `isReadOnly`/`isOrdered`/`begin`/`end` comments (`DK-PROP-01–06`), labels, descriptions, and language resolution (`DK-LBL-01–02`), IRI construction and `dcterms:identifier` annotations (`DK-IRI-02–05, 07, 09–10`), and multiplicity recovery and diagnostics (`DK-DIAG-09–11`) all remain applicable.

Transforming a class attribute whose `propertyType` resolves to a `Class` with a generated local `owl:Class` outside `datatype` and `enumeration` is **non-erroneous under `strict`, `tolerant`, and `best-effort`**: DirectKG emits no extra warning or error solely because the target `Class` is not `datatype` or `enumeration`. Existing structural-error and recovery rules under `DK-DIAG-05` (`UNRESOLVED_ATTRIBUTE_TYPE`) continue to apply for unresolved or invalid `propertyType` references (such as a dangling ID, malformed reference, or non-`Class` reference). A target `Class` without a generated local `owl:Class` (other than handled primitives and `void`, for example a target omitted earlier under `best-effort`) retains its existing unresolved/unavailable-target boundary. `DK-DIAG-04`'s eight-code diagnostic core and established configuration options remain unchanged.

This **specification illustration** assumes `kind` class `Order` has attribute `customer` typed by `kind` class `Person` with explicit multiplicity `1`, and `Person` has its own attribute `fullName` typed by primitive `string`. With name-based identity, no collisions, and entity base `https://example.org/orders#`, the excerpt below omits labels, identifier annotations, ontology header/import, and provenance, and is not captured converter output.

```turtle
@prefix : <https://example.org/orders#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

:Order a owl:Class ;
    rdfs:subClassOf [ a owl:Restriction ;
        owl:onProperty :customer ;
        owl:cardinality "1"^^xsd:nonNegativeInteger ] .

:Person a owl:Class .

:customer a owl:ObjectProperty ;
    rdfs:domain :Order ;
    rdfs:range :Person .

:fullName a owl:DatatypeProperty ;
    rdfs:domain :Person ;
    rdfs:range xsd:string .
```

**Implementation status.** At the [reviewed registration revision `4f9a9ccfa016a052a9b955afb0f9d863e3df8222`](https://github.com/pedropaulofb/ontouml-directkg/blob/4f9a9ccfa016a052a9b955afb0f9d863e3df8222/src/ontouml_directkg/properties.py#L77-L78), `collect_attributes` in [`properties.py`](https://github.com/pedropaulofb/ontouml-directkg/blob/4f9a9ccfa016a052a9b955afb0f9d863e3df8222/src/ontouml_directkg/properties.py#L26-L82) still raises `NotImplementedError("Attribute value kinds outside datatype/enumeration mappings remain unspecified")` for resolved `Class` targets outside `datatype` and `enumeration`, which [`conversion.py`](https://github.com/pedropaulofb/ontouml-directkg/blob/4f9a9ccfa016a052a9b955afb0f9d863e3df8222/src/ontouml_directkg/conversion.py#L247-L251) catches as `INTERNAL_TRANSFORMATION_FAILURE` and aborts under every input policy. The section above describes the accepted intended behavior.

### Attributes owned without a local OWL class

When an attribute is owned by a `Class` that does **not** generate a local `owl:Class` under `DK-CLS-01`—specifically, a registered primitive `datatype` (`DK-DAT-02`) or Visual Paradigm `void` (`DK-DAT-04`)—DirectKG cannot transform that attribute and reports a structural transformation **ERROR** identifying the affected attribute, its owning `Class`, and the missing local `owl:Class` representation (`DK-ATT-01`, `DK-GEN-03`).

DirectKG must **not** generate a local `owl:Class` for a registered primitive `datatype` or `void`, introduce a domainless attribute property, or silently discard mandatory `rdfs:domain` (`DK-GEN-03`) and cardinality (`DK-ATT-03`) mappings to retain an otherwise incompatible attribute.

Input-policy behavior follows [Policies and precedence](../reference/diagnostics.md#policies-and-precedence) (`DK-DIAG-05`):

- **`strict` and `tolerant`:** Conversion aborts (`aborted` outcome, no ontology delivered).
- **`best-effort`:** DirectKG retains **ERROR** severity, omits the affected attribute and all output dependent on it—including any OWL property declaration, `rdfs:domain`, `rdfs:range`, labels, comments, source-ID annotations, multiplicity-derived cardinality restrictions, IRI candidate claims, and attribute-level processing or diagnostics (such as `propertyType` resolution, naming fallbacks, `void` warnings, flag annotations, and cardinality diagnostics) arising solely from transforming that attribute—and preserves independently transformable elements.

Dependent `subsettedProperties` and `redefinedProperties` references under `best-effort` follow [Subsetting](property-features.md#subsetting) (`DK-PROP-03`): inclusions referencing an attribute omitted under this rule, as well as inclusions declared on the omitted attribute itself, are omitted cleanly without generating an additional `UNRESOLVED_PROPERTY_REFERENCE` error. Suppression applies strictly to targets known to have been omitted under this owner-lacks-local-class rule (alongside omitted relations and unsupported relation-valued connectors); genuinely unresolved, malformed, or otherwise independently invalid references (including targets omitted due to `UNRESOLVED_ATTRIBUTE_TYPE`) retain their established diagnostics.

This rule does **not** affect attributes *owned by* classes that generate local `owl:Class` resources under `DK-CLS-01`—including custom `datatype` classes (`DK-DAT-05`), `enumeration` classes (`DK-CLS-10`), ordinary OntoUML class stereotypes, `null` stereotype, and accepted custom stereotypes—and preserves the existing mappings for attributes *typed by* registered primitives (`DK-DAT-02`), `void` (`DK-DAT-04`), or `propertyType: null` (`DK-DAT-03`) when owned by a class with a generated local `owl:Class`. Established diagnostic precedence (fatal duplicate declaration IDs under `§3.4` and `DK-DIAG-05`, stereotype acceptance and rejection under `DK-DIAG-06`, and source-ID validity under `§3.4` and `DK-DIAG-05`), identifier and stereotype policies, `DK-DIAG-04`'s eight-code stable diagnostic core (selecting no new stable diagnostic identifier), and existing configuration options remain unchanged.

This rule addresses a DirectKG transformation limitation (because registered primitives and `void` lack a generated local `owl:Class` for mandatory `rdfs:domain` and `rdfs:subClassOf` cardinality restrictions); it must **not** be interpreted as declaring the source OntoUML model semantically invalid or introducing additional semantic validation (`§3.4`, `DK-DIAG-02`).

**Implementation status.** At [specification registration revision `ddca486133edb1b27a26c8995d612c4579afd838`](https://github.com/pedropaulofb/ontouml-directkg/blob/ddca486133edb1b27a26c8995d612c4579afd838/src/ontouml_directkg/properties.py#L40-L41), `collect_attributes` in `src/ontouml_directkg/properties.py` (lines 40–41) still raises `NotImplementedError("Attribute ownership without a generated local class is outside the decided baseline")` when `element.owner not in generated_classes`, which [`conversion.py`](https://github.com/pedropaulofb/ontouml-directkg/blob/ddca486133edb1b27a26c8995d612c4579afd838/src/ontouml_directkg/conversion.py#L250-L254) catches as `INTERNAL_TRANSFORMATION_FAILURE` and aborts under every input policy, including `best-effort`; `PropertyExpressions` and `emit_property_references` do not yet track or suppress `DK-PROP-03` inclusions for attributes omitted under this rule. The section above describes the accepted intended behavior.

### Class properties container and entry validation

Absent `Class.properties`, explicit `Class.properties: null`, and `Class.properties: []` are accepted as empty without an error or warning (`DK-ATT-01`). Any non-null, non-array `Class.properties` value, any non-object entry, or any non-`Property` entry (including known non-`Property` OntoUML types, valid unknown string `type` values, or objects lacking a valid string `type`) triggers a structural **ERROR** under `DK-DIAG-05` (not `UNKNOWN_INFORMATION`): `strict` and `tolerant` abort, while `best-effort` retains **ERROR** severity, omits the malformed container or invalid entry without generating an attribute property or dependent output, and retains the owning `Class` (where eligible under `DK-CLS-01`), valid `Property` siblings in the same array, and independent mappings. See [Class properties and non-enumeration literals](../reference/diagnostics.md#class-properties-and-non-enumeration-literals) for `DUPLICATE_SOURCE_ID` / `DK-DIAG-06` / `§3.4` precedence, `DK-PROP-03` handling for unindexed non-`Property` entries, and current `NotImplementedError` implementation status in `source.py`.

`isDerived` does not suppress ordinary attribute transformation; its [comment mapping](../reference/text.md#derived-status-comments) is separate. Supported `isReadOnly: true` and `isOrdered: true` declarations also have comment mappings, with INFO for each preserved ordering occurrence. Those comments do not implement read-only enforcement or ordered property values. See [Property features](property-features.md#read-only-and-aggregation-comments) and its [ordering explanation](property-features.md#ordering-without-ordered-values).

Explicit recognized `begin` and `end` stereotypes have [boundary stereotype comment preservation](property-features.md#boundary-stereotype-comments). They do not select a temporal datatype or change the existing typing, range, or cardinality mapping.

## Primitive registry

The **complete current primitive registry contains nine entries** (reused for both primitive-valued attributes and compatible [datatype-valued ordinary relations](relations.md#datatype-valued-relations-and-compatibility)). VP `void` is recognized separately and is not a tenth primitive mapping.

| Normalized key | RDF range |
| --- | --- |
| `boolean` | `xsd:boolean` |
| `byte` | `xsd:byte` |
| `char` | `xsd:string` |
| `double` | `xsd:double` |
| `float` | `xsd:float` |
| `int` | `xsd:int` |
| `long` | `xsd:long` |
| `short` | `xsd:short` |
| `string` | `xsd:string` |

Here `xsd:` denotes `http://www.w3.org/2001/XMLSchema#`. Mapping `char` to `xsd:string` deliberately loses the one-character constraint. It adds no one-character validation or substitute restriction.

Primitive recognition is exact registry lookup after lexical normalization and applies only to `datatype` classifiers (`stereotype == "datatype"`). The normalization should perform Unicode normalization, surrounding-whitespace trimming and case folding; recognize known XSD prefix/namespace forms before ordinary normalization; and ignore whitespace, hyphen, and underscore separators. Recognition of standard prefixed/full XSD names should be limited to those supported entries. These recommendations do not register additional mappings (DK-DAT-02).

No fuzzy matching, spelling correction, stemming, plural adjustment, abbreviation expansion, translation, or synonym detection is allowed. `int` and `integer` denote semantically distinct XSD datatypes; the registry registers only `int`. Aliases such as `bool`, `str`, `wholeNumber`, and `integer32` are not activated by resembling registered entries. Additional primitives require a separate accepted decision; an otherwise supported modeled datatype outside the registry receives custom-datatype treatment.

For a localized datatype name, first use the [deterministic multilingual selector](../reference/identifiers.md#multilingual-naming), then pass **only its selected original source text** through primitive normalization/lookup. Do not use a normalized/disambiguated IRI, synthetic fallback, or an alternative translation to find a primitive match. Selection is identical under both IRI strategies and independent of language overrides and `Project.languages`.

For example, `{"de":"Ganzzahl","en":"int"}` selects `Ganzzahl`, so existing custom-datatype treatment applies. `{"en":"int","nl":"float"}` selects `int` and resolves to `xsd:int`; the unselected translation adds no competing-outcome diagnostic. Multiple localized values introduce no new primitive-conflict check; existing naming, input, and `void` diagnostics still apply.

## Untyped and void

An explicit `propertyType: null` means **unspecified typing**. Keep the datatype property, owner domain, and applicable explicit cardinality. Generate no range or value-type restriction; do not guess `rdfs:Literal`, `xsd:string`, or another datatype. Null typing is not automatically an input error (DK-DAT-03).

The downloadable [classes-and-attributes example](../examples/index.md#classes-and-untyped-attributes) pairs a checked Catalog adaptation with a labelled Turtle illustration of two distinct untyped attributes and their owner domains.

VP `void` (`stereotype == "datatype"`) means **an explicitly selected, recognized but unsupported type** (E02 / DK-DAT-04). This rangeless `owl:DatatypeProperty` and warning handling applies to **`void`-typed attributes only** (when owned by a class with a generated local `owl:Class`): keep the attribute as a datatype property, its domain, and applicable explicit cardinality, but supply no range or local value-type restriction from `void`. The datatype element creates neither a local class nor an OWL datatype. A nonfatal warning must identify the attribute, owner, `void`, and missing mapping/range where available. By contrast, an ordinary binary relation whose target resolves to `void` (`Class → void`) is a structural **ERROR** under [Datatype-valued relations](relations.md#datatype-valued-relations-and-compatibility) (`DK-REL-01`), and an attribute *owned by* `void` (or a registered primitive `datatype`) is a structural **ERROR** under [Attributes owned without a local OWL class](#attributes-owned-without-a-local-owl-class) (`DK-ATT-01`); neither generates a rangeless datatype property or domainless property.

!!! warning "The void type does not prohibit values"

    Do not substitute an XSD datatype, `rdfs:Literal`, `owl:Nothing`, `owl:bottomDataProperty`, `xsd:anySimpleType`, `xsd:anyAtomicType`, or an invented empty datatype for `void`. In particular, `void` does not mean that an attribute must have no values. Its warning and unsupported status distinguish it from null typing; both preserve an attribute's otherwise applicable mappings.

## Cardinalities and structured datatypes

### Necessary cardinality constraints

Attribute constraints use `rdfs:subClassOf` restrictions: they are necessary conditions, not exhaustive `owl:equivalentClass` definitions. Their OWL interpretation does not turn an absent assertion into a closed-world validation failure.

| Explicit multiplicity | Required numeric constraint |
| --- | --- |
| `1` | Exactly one |
| `1..*` | Minimum one |
| `0..1` | Maximum one |
| `2..5` | Minimum two and maximum five |
| `l..u` | Minimum `l` when positive; maximum `u` when finite |
| `l..u` with equal numeric bounds | Exact cardinality may replace the separate minimum/maximum constraints |
| `*` or `0..*` | No numeric bound to express as a cardinality restriction |
| Explicit JSON `null` | No cardinality restriction, guessed default, or diagnostic solely for null |

An absent cardinality field also supplies no restriction/default, but requires a warning and continuation of all other applicable mappings under every input policy. Explicit null remains distinct from both absent and explicitly unbounded input.

Contradictory nonnegative numeric bounds such as `5..2` remain minimum five and maximum two under every policy, without a warning/error solely for the contradiction. The resulting class can be unsatisfiable. Untranslatable bounds, lexical normalization, and ambiguous malformed expressions instead follow DK-DIAG-10–11; `best-effort` preserves independently valid bounds only where those rules permit. See [Multiplicity parsing and recovery](../reference/diagnostics.md#multiplicity-parsing-and-recovery) for the full parsing rules.

Multiplicity restrictions using object-property expressions made non-simple by actually emitted material chains are subject to the targeted `omit-conflicting-constraints` treatment, including accepted subproperty/inverse propagation. Other independently applicable constraints remain; see the [chain-control boundary](../reference/controls.md#material-chains-have-targeted-effects). [Material-chain modes](derivations-and-chains.md#material-chain-modes) explains the propagation and affected constraints.

### Structured custom datatypes

An otherwise supported `datatype` classifier that is neither a registered primitive nor `void` becomes a reified `owl:Class`. Attributes, and otherwise eligible explicit class-endpoint relations, targeting it become object properties with that class as range. Do not infer an XSD mapping from a suggestive name: `TimeInterval` does not automatically become `xsd:duration`.

Preserve the structured value. Do not flatten its attributes into the referring class; transform nested custom datatype properties recursively under the same rules. Relation-valued endpoints keep their independently specified connector boundaries.

This **specification illustration** assumes `Person` has an `address` attribute typed by custom datatype `Address`, whose `postcode` attribute has registered primitive type `string`. With name-based identity, no collisions, and entity base `https://example.org/addresses#`, the selected declarations below are a parseable excerpt. They omit cardinalities, labels, identifier annotations, ontology header/import, and provenance, and are not captured output.

```turtle
@prefix : <https://example.org/addresses#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

:Person a owl:Class .
:Address a owl:Class .
:address a owl:ObjectProperty ;
    rdfs:domain :Person ;
    rdfs:range :Address .
:postcode a owl:DatatypeProperty ;
    rdfs:domain :Address ;
    rdfs:range xsd:string .
```

Typed attributes keep their global range. DirectKG does not add local `owl:allValuesFrom` solely to repeat that range, and the former optional control has been removed. No new class-specific value-restriction feature or extension to ordinary relations is established by that removal (DK-ATT-04).

---

Governing rules: DK-ATT-01–04; DK-DAT-01–05; DK-GEN-03, 05; DK-CLS-01, 10–11; DK-INV-01–02; DK-PROP-01–06; DK-LBL-01–02; DK-IRI-02–05, 07, 09–10; DK-DIAG-01–02, 04–06, 09–11, 16, 18; DK-REL-01; §3.4; baseline consolidated: **2026-11-23**; repository commit: `c87a6a2cd83f6da675018edb1b0af81f86ad7013`; source: [`documentation/specification/transformation-specification.md`](https://github.com/pedropaulofb/ontouml-directkg/blob/c87a6a2cd83f6da675018edb1b0af81f86ad7013/documentation/specification/transformation-specification.md).

Accepted update: **RD-02 — `Class.properties` container and entry validation (Alternative 3A)** (project-owner formalization included in the cited consolidation).

Accepted update: **RD-02 — Attributes owned by a `Class` without a generated local `owl:Class` (Alternative A) and dependent `DK-PROP-03` handling** (project-owner formalization included in the cited consolidation).

Accepted update: **RD-02 — Datatype-valued ordinary binary relations (`Alternative B + Q1–Q7 + Conflicts A–I`) & global `DK-PROP-03` mixed-kind rejection** (project-owner formalization included in the cited consolidation).

Accepted update: **RD-18 — Comment preservation of `begin` and `end` property stereotypes** (project-owner formalization included in the cited consolidation).
