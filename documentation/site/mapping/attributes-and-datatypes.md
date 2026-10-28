# Attributes and datatypes

These are **accepted intended mappings** for supported attributes and datatype classifiers. They are independent of any unimplemented Python signature or CLI invocation. Global domains/ranges are inferential; see [Semantics and limitations](../concepts/semantics.md#domain-graph-and-inferential-axioms).

## Property kinds and ranges

An attribute's resolved `propertyType` determines its property kind and range; the domain is its owning class.

| Resolved source type | Property kind | Range |
| --- | --- | --- |
| Supported primitive datatype | `owl:DatatypeProperty` | Registered XSD datatype |
| Custom `datatype` | `owl:ObjectProperty` | Reified custom datatype class |
| `enumeration` | `owl:ObjectProperty` | Generated enumeration class |
| Explicit `null` | `owl:DatatypeProperty` | None |
| Recognized VP `void` | `owl:DatatypeProperty` | None; nonfatal warning |

An enumeration-valued attribute therefore links to enumeration individuals rather than string literals. See [Enumerations and closure](classes.md#enumerations-and-closure). Distinct modeled attributes remain distinct properties even when their names coincide; [identifier disambiguation](../reference/identifiers.md#names-escaping-and-collisions) never changes the property kind.

`isDerived` does not suppress ordinary attribute transformation; its [comment mapping](../reference/text.md#derived-status-comments) is separate. Supported `isReadOnly: true` and `isOrdered: true` declarations also have comment mappings, with INFO for each preserved ordering occurrence. Those comments do not implement read-only enforcement or ordered property values. See [Property features](property-features.md#read-only-and-aggregation-comments) and its [ordering explanation](property-features.md#ordering-without-ordered-values).

Explicit recognized `begin` and `end` stereotypes have [boundary stereotype comment preservation](property-features.md#boundary-stereotype-comments). They do not select a temporal datatype or change the existing typing, range, or cardinality mapping.

## Primitive registry

The **complete current primitive registry contains nine entries**. VP `void` is recognized separately and is not a tenth primitive mapping.

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

Primitive recognition is exact registry lookup after lexical normalization of classifiers being interpreted as datatypes. The normalization should perform Unicode normalization, surrounding-whitespace trimming and case folding; recognize known XSD prefix/namespace forms before ordinary normalization; and ignore whitespace, hyphen, and underscore separators. Recognition of standard prefixed/full XSD names should be limited to those supported entries. These recommendations do not register additional mappings (DK-DAT-02).

No fuzzy matching, spelling correction, stemming, plural adjustment, abbreviation expansion, translation, or synonym detection is allowed. `int` and `integer` denote semantically distinct XSD datatypes; the registry registers only `int`. Aliases such as `bool`, `str`, `wholeNumber`, and `integer32` are not activated by resembling registered entries. Additional primitives require a separate accepted decision; an otherwise supported modeled datatype outside the registry receives custom-datatype treatment.

For a localized datatype name, first use the [deterministic multilingual selector](../reference/identifiers.md#multilingual-naming), then pass **only its selected original source text** through primitive normalization/lookup. Do not use a normalized/disambiguated IRI, synthetic fallback, or an alternative translation to find a primitive match. Selection is identical under both IRI strategies and independent of language overrides and `Project.languages`.

For example, `{"de":"Ganzzahl","en":"int"}` selects `Ganzzahl`, so existing custom-datatype treatment applies. `{"en":"int","nl":"float"}` selects `int` and resolves to `xsd:int`; the unselected translation adds no competing-outcome diagnostic. Multiple localized values introduce no new primitive-conflict check; existing naming, input, and `void` diagnostics still apply.

## Untyped and void

An explicit `propertyType: null` means **unspecified typing**. Keep the datatype property, owner domain, and applicable explicit cardinality. Generate no range or value-type restriction; do not guess `rdfs:Literal`, `xsd:string`, or another datatype. Null typing is not automatically an input error (DK-DAT-03).

The downloadable [classes-and-attributes example](../examples/index.md#classes-and-untyped-attributes) pairs a checked Catalog adaptation with a labelled Turtle illustration of two distinct untyped attributes and their owner domains.

VP `void` means **an explicitly selected, recognized but unsupported type** (E02 / DK-DAT-04). Keep the attribute as a datatype property, its domain, and applicable explicit cardinality, but supply no range or local value-type restriction from `void`. The datatype element creates neither a local class nor an OWL datatype. A nonfatal warning must identify the attribute, owner, `void`, and missing mapping/range where available.

!!! warning "The void type does not prohibit values"

    Do not substitute an XSD datatype, `rdfs:Literal`, `owl:Nothing`, `owl:bottomDataProperty`, `xsd:anySimpleType`, `xsd:anyAtomicType`, or an invented empty datatype for `void`. In particular, `void` does not mean that the attribute must have no values. Its warning and unsupported status distinguish it from null typing; both preserve the property's otherwise applicable mappings.

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

Governing rules: DK-ATT-01–04; DK-DAT-01–05; DK-GEN-03, 05; DK-CLS-10–11; DK-DIAG-09–11, 18; DK-IRI-10; baseline consolidated: **2026-10-21**; repository commit: `9e52a66af43e39b374d0a642298b1117d12be4d8`; source: [`documentation/specification/2026-10-21 - specification handoff.md`](https://github.com/pedropaulofb/ontouml-directkg/blob/9e52a66af43e39b374d0a642298b1117d12be4d8/documentation/specification/2026-10-21%20-%20specification%20handoff.md).

Accepted update: **RD-18 — Comment preservation of `begin` and `end` property stereotypes** (project-owner formalization supplied after this baseline).
