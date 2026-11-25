# Classes and enumerations

This page describes **accepted intended mappings**, not verified converter output. The distinctions below matter even when transformation completes: class declarations, coverage, inequality, and comments preserve different kinds of information.

## Classes and disjointness

A supported OntoUML domain classifier becomes an `owl:Class`. Before that mapping, a `datatype` classifier is classified as a supported primitive, recognized `void`, or custom datatype. Supported primitives and `void` generate no local class; a custom datatype becomes a reified class. Enumerations also become classes. See [Attributes and datatypes](attributes-and-datatypes.md). A `Class` with a malformed `stereotype` value (non-`null`, non-string JSON value or empty/whitespace-only string) triggers a structural **ERROR** under `DK-DIAG-05` (`strict`/`tolerant` abort; `best-effort` omits the `Class` and its owned `properties`/`literals` descendants at element level). See [Malformed stereotype values](../reference/diagnostics.md#malformed-stereotype-values).

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

Count members using the [generalization-set membership rule](../reference/input.md#generalization-set-membership): repeated references to the same declaration count once within the set. A fully resolved, complete `[g1, g1]` therefore uses singleton completeness and its required INFO. The linked input reference records the implementation status of this accepted behavior.

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

For an incomplete class set with a usable categorizer, [categorizer recovery](higher-order.md#recovery-for-incomplete-categorized-class-sets) preserves classifications of surviving explicit specifics under `best-effort` and omits powertype expansion. For a class set with a nonempty `generalizations` array and a present, non-null unusable categorizer, [unusable-categorizer recovery](higher-order.md#recovery-for-an-unusable-categorizer) reports a structural ERROR and aborts under `strict` or `tolerant`; under `best-effort`, it omits all categorizer and powertype-extension assertions from that set without suppressing independently valid pairwise disjointness, multi-member coverage, singleton completeness and its required DK-DIAG-14 INFO diagnostic when membership is complete, or independent class generalizations. When a member also fails under DK-CLS-09, both rules apply together under `best-effort`: coverage and all categorizer/powertype assertions from that set are omitted while applicable pairwise disjointness among surviving specifics and independent mappings are retained. For [missing or malformed membership containers](../reference/diagnostics.md#missing-or-malformed-generalization-set-membership), `best-effort` omits the entire set contribution and preserves independently supported class generalizations and classifications. See [Higher-order classification](higher-order.md#categorizers-and-powertypes) for the fully resolved mappings and [Controls](../reference/controls.md#control-boundaries) for policy boundaries; see [Diagnostics and recovery](../reference/diagnostics.md#diagnostic-conditions-and-intentional-silence) for the detailed conditions.

For a `GeneralizationSet` with a valid nonempty `generalizations` array, any non-`null`, non-boolean value (`type(val) is not bool`) for `isDisjoint` or `isComplete` triggers a structural **ERROR** under `DK-DIAG-05` (`strict` and `tolerant` abort). Under `best-effort`, DirectKG retains **ERROR** severity and omits only the malformed flag field: a malformed `isDisjoint` emits no `owl:disjointWith` statements from that flag, and a malformed `isComplete` emits no `owl:unionOf` coverage and no singleton completeness or `DK-DIAG-14` INFO, while valid sibling flags, valid `categorizer` mappings, and independent generalizations remain preserved (`DK-DIAG-12` retains precedence before flag validation). See [Malformed Boolean flags](../reference/diagnostics.md#malformed-boolean-flags) for policy outcomes and current `NotImplementedError` status.

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

Malformed lists and untransformable supplied values on `enumeration` classes follow input-error policy: abort under `strict`/`tolerant`; retain error severity and transformable information under `best-effort`. Preserve each successful individual's membership, but never close over a surviving subset. No extra diagnostic is required solely for the count of survivors. An unnamed or unusably named value preserved through the generic source-ID fallback counts as successfully transformed; fallback alone does not make a complete list incomplete (DK-CLS-11; DK-DIAG-13).

For non-enumeration `Class` declarations (`stereotype != "enumeration"`, including ordinary OntoUML stereotypes, `datatype`, `abstract`, `null` stereotype, and accepted custom stereotypes), absent `literals`, explicit `literals: null`, and `literals: []` are accepted silently as empty; any non-null, non-array `literals` value, non-object/non-`Literal` entry, or valid `Literal` entry triggers a structural **ERROR** (`DK-CLS-11`, `DK-DIAG-05`): `strict` and `tolerant` abort, while `best-effort` retains **ERROR** severity, omits those `literals` without creating `owl:NamedIndividual`s (or enumeration membership, `owl:oneOf`, or `owl:AllDifferent` assertions), and retains the owning `Class` (where eligible under `DK-CLS-01`) and independent mappings. See [Class properties and non-enumeration literals](../reference/diagnostics.md#class-properties-and-non-enumeration-literals) for `DUPLICATE_SOURCE_ID` / `DK-DIAG-06` / `§3.4` precedence and current `NotImplementedError` implementation status in `source.py` and `classifiers.py`.

## Class declarations preserved as comments

Comments preserve declarations for readers; they do not impose the source feature's additional logical semantics.

| Declaration | Preserved information and diagnostic boundary |
| --- | --- |
| Explicit `abstract` class stereotype | Comment on the generated class, plus expressivity-limitation INFO. Existing stereotype disjointness still applies. |
| Explicit Boolean `isAbstract`, either value | Comment on the generated class or primary relation property, plus expressivity-limitation INFO. Treat the flag and stereotype independently. |
| Explicit Boolean `isExtensional`, either value | Comment on the generated class. `true` requires INFO explaining that essential-parthood semantics are not enforced; `false` alone produces no diagnostic. |
| Explicit JSON string classifier `order` | On a `Class` with a generated local `owl:Class`: `"OntoUML classifier order: orderless (*)."@en` for exact `"*"`, or `"OntoUML classifier order: S."@en` verbatim for any other JSON string `S` (without lexical validation, trimming, or normalization). Absent/`null` or surviving primitive/`void` classes emit no order comment and no diagnostic solely for `order`. |
| `restrictedTo` | Recognized omission: no output, annotation, or diagnostic solely for that presence/omission under any input policy. |

Abstractness does not establish completeness over modeled subclasses, emptiness, or extra classification. Extensionality does not introduce additional logical axioms. Do not infer Boolean values from missing/null fields, or infer `isAbstract` from the `abstract` stereotype. The abstractness/extensionality expressivity limitations alone produce no warning or error (DK-DIAG-15, 17).

All four defined `Class` Boolean flags (`isAbstract`, `isDerived`, `isExtensional`, `isPowertype`) are validated on every surviving `Class` declaration—including registered primitive `datatype` and Visual Paradigm `void` declarations not omitted earlier—under `DK-DIAG-05`, without generating a local `owl:Class` for primitives or `void` and preserving existing no-target comment/INFO omission when valid flags occur on classes without a local `owl:Class`. Any non-`null`, non-boolean value triggers a structural **ERROR** (`strict` and `tolerant` abort; `best-effort` omits only the malformed flag field—producing no `isAbstract`/`isExtensional` comment and no `DK-DIAG-15`/`DK-DIAG-17` INFO for that flag—while preserving the owning `Class`, valid sibling flags, any valid `abstract` stereotype handling, and independent mappings). See [Malformed Boolean flags](../reference/diagnostics.md#malformed-boolean-flags) and [Higher-order classification](higher-order.md#categorizers-and-powertypes) (for `isPowertype`).

`Class.order` accepts absent fields, explicit JSON `null`, and any JSON string regardless of lexical content without lexical validation, whitespace trimming/normalization, or extra diagnostics (`DK-CLS-05`; `RD-02`, `V4 + R1`). Only exact `"*"` produces `"OntoUML classifier order: orderless (*)."@en`; any other JSON string `S`—including numeric strings, empty `""`, whitespace-only strings, `" * "`, and non-numeric strings—produces `"OntoUML classifier order: S."@en` verbatim on classes with a generated local `owl:Class` (for example, `" * "` produces `"OntoUML classifier order:  * ."@en` and `""` produces `"OntoUML classifier order: ."@en`). Surviving registered primitive `datatype` and Visual Paradigm `void` `Class` declarations lacking a generated local `owl:Class` emit no `rdfs:comment` and acquire no local `owl:Class`. Order comments are informative only: they do not drive classification, inference, or semantic validation, and no machine-readable order property, external order vocabulary, or custom DirectKG predicate is introduced. Any non-`null`, non-string JSON value (`int`, `float`, `bool`, `list`, `dict`) on a surviving `Class` (including surviving primitives and `void` not omitted earlier) triggers a structural **ERROR** under `DK-DIAG-05` (`strict` and `tolerant` abort; `best-effort` omits only the malformed `order` field—emitting no order comment—while preserving the owning `Class`, valid sibling fields, and all independently applicable mappings). `order` is defined only on `Class`; an `order` field on any other element type remains governed by `UNKNOWN_INFORMATION`. See [Malformed class order](../reference/diagnostics.md#malformed-class-order). `restrictedTo` must not alter class, disjointness, order, or higher-order mappings; omission does not excuse independently invalid structure.

Explicit `isDerived` values have the separate cross-cutting [derived-status comment mapping](../reference/text.md#derived-status-comments), including the condition for INFO and omission when no local target exists. Other property qualifiers belong to [Property features](property-features.md).

---

Governing rules: §3.4; DK-CLS-01–11; DK-DAT-01–05; DK-GEN-05, 12; DK-HO-03–04; DK-DIAG-05–06, 12–17; baseline consolidated: **2026-11-25**; repository commit: `03c4f88487631979c4debc38634668ee9cbaf612`; source: [`documentation/specification/transformation-specification.md`](https://github.com/pedropaulofb/ontouml-directkg/blob/03c4f88487631979c4debc38634668ee9cbaf612/documentation/specification/transformation-specification.md).

Accepted update: **RD-02 — `Class.order` validation and field-level recovery (V4 + R1)** (project-owner formalization included in the cited consolidation).

Accepted update: **RD-02 — Malformed Boolean flags (Alternative 1 — Uniform field-level omission)** (project-owner formalization included in the cited consolidation).

Accepted update: **RD-02 — Malformed `stereotype` values on `Class`, `Relation`, and `Property` (Alternative 1C + Sub-option 2A)** (project-owner formalization included in the cited consolidation).

Accepted update: **RD-02 — Non-enumeration `Class.literals` container and entry validation (Alternative 4A)** (project-owner formalization included in the cited consolidation).
