# Classes and enumerations

This page describes **accepted intended mappings**, not verified converter output. The distinctions below matter even when transformation completes: class declarations, coverage, inequality, and comments preserve different kinds of information.

## Classes and disjointness

A supported OntoUML domain classifier becomes an `owl:Class`. Before that mapping, a `datatype` classifier is classified as a supported primitive, recognized `void`, or custom datatype. Supported primitives and `void` generate no local class; a custom datatype becomes a reified class. Enumerations also become classes. See [Attributes and datatypes](attributes-and-datatypes.md).

A class-to-class generalization generates `Specific rdfs:subClassOf General`. DirectKG need not materialize the transitive subclass closure. It does not validate the semantic appropriateness of stereotypes or repair contradictory axioms before emitting the accepted mappings.

### Stereotype-based disjointness

Two distinct generated classes directly carrying **any** ultimate-sortal stereotype are disjoint, including two classes carrying the same stereotype. The ultimate-sortal set is `collective`, `kind`, `mode`, `quality`, `quantity`, `relator`, and `type` (DK-CLS-03).

Independently, classes whose stereotypes belong to different groups below are disjoint (DK-CLS-04):

| Group | Stereotypes |
| --- | --- |
| 1 | `abstract`, `datatype`, `enumeration` |
| 2 | `event` |
| 3 | `situation` |
| 4 | `kind`, `collective`, `quantity`, `relator`, `mode`, `quality`, `subkind`, `role`, `phase`, `category`, `mixin`, `roleMixin`, `phaseMixin`, `historicalRole`, `historicalRoleMixin`, `type` |

Cross-group disjointness does not itself introduce pairs within a group. Ultimate-sortal disjointness and other independently applicable rules can still require such pairs. Primitive datatypes and `void` do not participate because they have no generated local classes.

Both stereotype rules use pairwise `owl:disjointWith`, with one statement per unordered pair sufficient; they do not use `owl:AllDisjointClasses`. Redundant disjointness inherited through subclasses need not be repeated. Preserving abstractness as a comment does not disable stereotype disjointness.

## Generalization sets

A class generalization set constrains its **explicit specific classifiers**. Disjointness and completeness are separate: the mappings do not use `owl:disjointUnionOf`.

| Source condition | Accepted contribution from the set |
| --- | --- |
| `isDisjoint: true` | Pairwise `owl:disjointWith` among its generated explicit specific classes. Do not include the general class, other siblings, or additionally materialized descendant pairs. |
| `isDisjoint: false` | No disjointness from that flag. It asserts neither actual overlap nor cancellation of other disjointness. |
| Fully resolved, `isComplete: true`, common generated general and at least two distinct generated specifics | The general is a subclass of an `owl:unionOf` containing exactly those explicit specifics. Existing specific-to-general subclass axioms remain. |
| `isComplete: false` | No covering axiom from that flag. It does not assert additional instances or subclasses. |
| Fully resolved, exactly one member generalization, `isComplete: true` | Add the reverse subclass axiom: general is a subclass of specific, alongside the existing specific-to-general axiom. |

For example, a complete set specializing `Vehicle` into `Car` and `Bicycle` constrains every vehicle to at least one of those classes. Overlap remains possible unless disjointness is separately required. This statement concerns class coverage; [relation-set completeness](relations.md#relation-set-completeness) has a different mapping boundary.

### Singleton and recovery boundaries

For singleton completeness, the two subclass directions make the classes extensionally equivalent while their IRIs remain distinct. DirectKG uses the reverse subclass statement, rather than a one-member union or an additional `owl:equivalentClass`. Applying this mapping requires a nonfatal INFO identifying the set, general, and specific and explaining that consequence. Singleton membership alone is not a warning. A singleton has no pair for set-derived disjointness; other disjointness remains applicable.

An unresolved member reference or failed member transformation is an error. `strict` and `tolerant` abort; under `best-effort`, retain independently transformable class/generalization mappings and any pairwise disjointness among surviving specifics, but **omit coverage**. Never cover the general using only survivors or apply singleton completeness just because one member survives. No surviving pair means no disjointness from that set (DK-CLS-09).

An explicitly empty `generalizations` array is a structural error under every completeness/disjointness combination. `strict` and `tolerant` abort; `best-effort` reports the error, omits the empty set's contribution, and continues elsewhere. Do not infer a general class, invent members, or assert an empty class extension from that array (DK-DIAG-12).

Duplicate-member handling, missing or malformed membership containers, and categorizer recovery after failed members remain unspecified. The accepted rules for explicitly empty arrays and unresolved members do not fill those gaps. See [Higher-order classification](higher-order.md#categorizers-and-powertypes) for categorizer mappings and [Controls](../reference/controls.md#control-boundaries) for policy boundaries; see [Diagnostics and recovery](../reference/diagnostics.md#diagnostic-conditions-and-intentional-silence) for the detailed conditions.

## Enumerations and closure

Only explicit source enumeration literals in the classifier's `literals` collection supply values. Each successfully transformed literal becomes a distinct `owl:NamedIndividual`, explicitly typed by its enumeration class. Same-named values remain distinct resources; their identity and fallback rules belong to [Identifiers and naming](../reference/identifiers.md#names-escaping-and-collisions).

An enumeration-owned `Property` is not an enumeration value merely because of its owner, name, null `propertyType`, or proximity to an absent/null/empty `literals` field. It retains its independently applicable attribute/property mapping. No historical exporter convention is inferred from that pattern.

| Value-list result | Closure using `owl:oneOf` | Inequality using `owl:AllDifferent` |
| --- | --- | --- |
| Complete, nonempty list | Yes, containing all generated values | Required when at least two distinct values are generated |
| Incomplete list, at least two surviving values | No | Required among the generated values |
| Incomplete list, one or zero surviving values | No | No |
| Absent, null, or explicitly empty `literals` | No | No values supplied by that field |

`owl:oneOf` defines the complete class extension. Different IRIs alone do not establish inequality; `owl:AllDifferent` supplies that assertion. Applicable class generalizations and disjointness remain in force. An attribute typed by the enumeration is an object property whose range is the enumeration class.

The following **specification illustration** shows selected enumeration assertions for complete values `Pending` and `Approved` of `OrderStatus`. Assume name-based identity without collisions and entity base `https://example.org/orders#`. It is a parseable graph excerpt, not executed output; ontology header/import, identifier annotations, labels, and execution provenance are outside the excerpt.

```turtle
@prefix : <https://example.org/orders#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .

:OrderStatus a owl:Class ;
    owl:oneOf ( :OrderStatus_Pending :OrderStatus_Approved ) .

:OrderStatus_Pending a owl:NamedIndividual, :OrderStatus .
:OrderStatus_Approved a owl:NamedIndividual, :OrderStatus .

[] a owl:AllDifferent ;
    owl:distinctMembers ( :OrderStatus_Pending :OrderStatus_Approved ) .
```

Absent, null, or empty `literals` requires a warning that values were unavailable and closure was omitted, but this fallback is nonfatal even under `strict`. Keep the enumeration class and independent mappings. Do not equate it with `owl:Nothing` or otherwise assert an empty extension. When owned properties are present, the warning should clarify that they were not interpreted as values.

Malformed lists and untransformable supplied values follow input-error policy: abort under `strict`/`tolerant`; retain error severity and transformable information under `best-effort`. Preserve each successful individual's membership, but never close over a surviving subset. No extra diagnostic is required solely for the count of survivors. An unnamed or unusably named value preserved through the generic source-ID fallback counts as successfully transformed; fallback alone does not make a complete list incomplete (DK-CLS-11; DK-DIAG-13).

## Class declarations preserved as comments

Comments preserve declarations for readers; they do not impose the source feature's additional logical semantics.

| Declaration | Preserved information and diagnostic boundary |
| --- | --- |
| Explicit `abstract` class stereotype | Comment on the generated class, plus expressivity-limitation INFO. Existing stereotype disjointness still applies. |
| Explicit Boolean `isAbstract`, either value | Comment on the generated class or primary relation property, plus expressivity-limitation INFO. Treat the flag and stereotype independently. |
| Explicit Boolean `isExtensional`, either value | Comment on the generated class. `true` requires INFO explaining that essential-parthood semantics are not enforced; `false` alone produces no diagnostic. |
| Explicit non-null classifier `order` | English comment: `OntoUML classifier order: N.` for numeric `N`, or `OntoUML classifier order: orderless (*).` for `*`. |
| `restrictedTo` | Recognized omission: no output, annotation, or diagnostic solely for that presence/omission under any input policy. |

Abstractness does not establish completeness over modeled subclasses, emptiness, or extra classification. Extensionality does not introduce additional logical axioms. Do not infer Boolean values from missing/null fields, or infer `isAbstract` from the `abstract` stereotype. The abstractness/extensionality expressivity limitations alone produce no warning or error (DK-DIAG-15, 17).

Order comments are informative: they do not drive classification, inference, or semantic validation. Absent/null order produces no order comment. No machine-readable order property, external order vocabulary, or custom DirectKG predicate is introduced. `restrictedTo` must not alter class, disjointness, order, or higher-order mappings; omission does not excuse independently invalid structure.

Explicit `isDerived` values have the separate cross-cutting [derived-status comment mapping](../reference/text.md#derived-status-comments), including the condition for INFO and omission when no local target exists. Other property qualifiers belong to [Property features](property-features.md).

---

Governing rules: DK-CLS-01–11; DK-DAT-01–05; DK-GEN-05; DK-DIAG-12–17; baseline consolidated: **2026-10-21**; repository commit: `a36322fa87c006cece63aaadd2aa5ccd513f6087`; source: [`documentation/specification/2026-10-21 - specification handoff.md`](https://github.com/pedropaulofb/ontouml-directkg/blob/a36322fa87c006cece63aaadd2aa5ccd513f6087/documentation/specification/2026-10-21%20-%20specification%20handoff.md).
