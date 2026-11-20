# Property features

These are **accepted intended mappings** for explicit UML property relationships and supported qualifiers. Property inclusion, comment preservation, and complete UML semantics are different guarantees; no production execution is asserted here.

## Subsetting

Each explicit `p1 subsets p0` reference in `subsettedProperties` contributes `OWL(p1) rdfs:subPropertyOf OWL(p0)`. Resolve both UML Properties independently using their accepted output expressions:

| UML Property | Output expression |
| --- | --- |
| Classifier-owned attribute | Its generated property (`owl:ObjectProperty` or `owl:DatatypeProperty`) |
| Target association end | The relation's primary property (`owl:ObjectProperty` or `owl:DatatypeProperty`) |
| Source association end of an `owl:ObjectProperty` relation with named inverse | That named inverse (`owl:ObjectProperty`) |
| Source association end of an `owl:ObjectProperty` relation without named inverse, when the primary exists | An anonymous inverse of that primary (`owl:ObjectProperty` expression) |
| Source association end of a datatype-valued (`owl:DatatypeProperty`) relation | None (no named or anonymous inverse datatype property exists) |

Consequently, between compatible property expressions of the same OWL property kind: target→target references give forward→forward inclusion (homogeneous `ObjectProperty` or homogeneous `DatatypeProperty`); source→source gives inverse→inverse (`ObjectProperty` relations only); target→source gives forward→inverse (`ObjectProperty` relations only); source→target gives inverse→forward (`ObjectProperty` relations only). These arrows describe which ends reference each other, not a change to the established relation directions. Anonymous expressions do not require a named inverse, new inverse name, or changed IRI.

Process every explicit reference, preserve multiple superproperties, and deduplicate identical resulting axioms. Do not additionally emit logically entailed inverse counterparts or the property's transitive hierarchy closure. [Explicit relation generalization](inverses.md#explicit-inverse-specialization) has a separately required inverse-mirroring rule.

Both references, their underlying property transformations, an available OWL property expression for each referenced UML Property, and **OWL property-kind compatibility** must resolve:

- **Unavailable inverse of a datatype property:** Whenever `subsettedProperties` or `redefinedProperties` requires an inverse expression of a datatype-valued relation (either referencing or referenced end is the source association end of a datatype-valued relation whose primary property exists), DirectKG reports a structural **ERROR** identifying the affected reference and explaining that an `owl:DatatypeProperty` has no named or anonymous inverse expression. Under `strict` and `tolerant`, conversion aborts. Under `best-effort`, DirectKG retains **ERROR** severity, omits only the affected inclusion axiom when the primary relation survives, and preserves other valid references and independently generated properties.
- **Mixed object/data property inclusions (global rejection):** Whenever a `DK-PROP-03` inclusion would connect an `owl:ObjectProperty` (or inverse object-property expression) and an `owl:DatatypeProperty`—whether as subproperty or superproperty—DirectKG reports a structural **ERROR** identifying the affected property reference and explaining the mixed object/data property-kind incompatibility. **This explicitly supersedes the previous allowance for mixed property-kind inclusions and applies globally across all mappings governed by `DK-PROP-03`, including existing classifier-owned attributes as well as datatype-valued relations.** For example, an attribute targeting a reified custom datatype cannot subset or redefine an `int` attribute. Under `strict` and `tolerant`, conversion aborts; under `best-effort`, DirectKG retains **ERROR** severity, omits only the incompatible inclusion axiom, and preserves independently valid properties and homogeneous object-property or homogeneous datatype-property inclusions.

!!! warning "Behavioral change and implementation status for `DK-PROP-03`"

    Rejecting mixed `owl:ObjectProperty` / `owl:DatatypeProperty` inclusions under `subsettedProperties` and `redefinedProperties` is an **intentional global supersession** affecting classifier-owned attributes as well as relations. At [specification registration revision `283f9b01361830c2dfb1e96b08111e1f8f849b31`](https://github.com/pedropaulofb/ontouml-directkg/blob/283f9b01361830c2dfb1e96b08111e1f8f849b31/src/ontouml_directkg/properties.py#L198-L237), `emit_property_references` in `src/ontouml_directkg/properties.py` does not yet enforce this mixed-kind check (and `relations.py` does not yet transform datatype-valued relations). The behavior described here is the accepted intended specification.

If an accepted mapping intentionally creates no property expression, do not create one solely for subsetting, override an [unsupported connector's omission](relations.md#relation-valued-endpoints), or reference a relation omitted under `best-effort`. Unresolved references or failed required transformations follow the structural-error policy.

Except for this targeted OWL property-kind compatibility check (and inverse availability), DirectKG still does **not** check owner, endpoint, type, domain, range, or other UML semantic compatibility before emitting an otherwise processable inclusion. Structurally processable, kind-compatible references may still yield output outside an OWL 2 DL profile. Inclusion neither merges nor replaces the properties and does not authorize a union-domain/range repair.

## Partial redefinition

An explicit `p1 redefines p0` reference in `redefinedProperties` uses the same expression selection, **OWL property-kind compatibility check** (rejecting unavailable datatype-property inverses and mixed object/data inclusions globally across attributes and relations), and inclusion axiom as subsetting. **This is a partial translation** (E03 / DK-PROP-03): property inclusion is preserved, while UML's full contextual replacement semantics are not.

Subsetting and redefinition remain distinct UML relationships despite their shared DirectKG representation. A redefinition alone does not generate `owl:equivalentProperty`, contextual value equality, property merging/replacement, new domain/range axioms, or copied/additional cardinality restrictions. Independently applicable declarations, domains, ranges, cardinalities, and relation-generalization mappings remain in force.

A structurally processable, **property-kind-compatible** redefinition mapped as specified requires **no warning solely for being a partial translation**. Other applicable diagnostics, including mixed-kind, unavailable-inverse, unresolved-reference, or underlying-transformation errors, still apply. A quiet conversion does not establish complete contextual preservation.

## Read-only and aggregation comments

The following explicit characteristics have human-readable `rdfs:comment` preservation when the indicated local property is successfully generated:

| Source characteristic | Comment target and context |
| --- | --- |
| `isReadOnly: true` on a supported class attribute | Attribute property; identify the read-only declaration |
| `isReadOnly: true` on either end of an eligible ordinary relation | Primary source-specific property (`owl:ObjectProperty` or compatible `owl:DatatypeProperty`); identify source or target end |
| `aggregationKind: "SHARED"` on either eligible relation end | Primary property (`owl:ObjectProperty` or compatible `owl:DatatypeProperty`); identify end and shared aggregation |
| `aggregationKind: "COMPOSITE"` on either eligible relation end | Primary property (`owl:ObjectProperty` or compatible `owl:DatatypeProperty`); identify end and composite aggregation |

Preserve each covered occurrence, including both ends or several characteristics on one end. Named inverse generation is not a prerequisite, and compatible datatype-valued relations retain these primary-property annotations (whereas mereological relations carrying `componentOf`, `memberOf`, `subCollectionOf`, or `subQuantityOf` are rejected with a structural **ERROR** when targeting a supported primitive). Do not create a property/inverse solely to host comments or move the end comments to an inverse. Consistent wording should make the end and characteristic clear; suitable English forms include “OntoUML source metadata: the target association end has composite aggregation.”

These annotations do not enforce read-only access or add aggregation logic. They introduce no dedicated DirectKG predicate, additional logical property characteristic, or existential dependence solely from `isReadOnly`. They do not determine [mereological eligibility or orientation](mereology.md#source-specific-properties), reverse a relation, substitute an inverse, or repair the source. Independently accepted mappings still apply.

A unique aggregation marker has a separate [lexical role in semantic naming](relations.md#structural-evidence-for-semantic-naming). This does not change comment preservation: retain every covered occurrence, including two competing whole markers when naming must use endpoint fallback. It authorizes none of the direction or logical-mapping changes excluded above.

Comment preservation supports human inspection, without guaranteeing machine-readable reconstruction or round-tripping. DK-PROP-04 establishes no additional diagnostic solely for preserving these comments; ordering has its separate INFO rule below. Generated explanatory text does not acquire source-language propagation or the source-language override. See [Language resolution](../reference/text.md#language-resolution).

## Boundary stereotype comments

Preserve each explicitly supplied, recognized `begin` or `end` property stereotype through an **English `rdfs:comment` identifying the declared stereotype**, when its eligible property is successfully generated.

| Source occurrence | Comment target and context |
| --- | --- |
| Supported attribute carrying `begin` or `end` | Its generated attribute property |
| Source end of an eligible ordinary relation carrying `begin` or `end` | Its generated primary relation property; identify the source association end |
| Target end of an eligible ordinary relation carrying `begin` or `end` | Its generated primary relation property; identify the target association end |

If both association ends carry covered stereotypes, preserve both occurrences. Placement remains independent of named-inverse generation.

These comments **preserve boundary-stereotype declarations without enforcing temporal semantics**. They introduce no additional logical axioms or temporal validation. Naming, property kind, range, cardinality, and inverse mappings remain unchanged. In particular, an [untyped attribute](attributes-and-datatypes.md#untyped-and-void) retains its datatype-property, owner-domain, and applicable cardinality mappings without a guessed range.

Do not infer either stereotype from names, supply a missing `begin`/`end` counterpart, or reconstruct stereotype information discarded by the exporter. Preserve only the recognized stereotype explicitly supplied in supported input.

This **specification illustration** assumes an attribute explicitly carrying `begin` and shows only its generated comment. The wording is illustrative, and no converter execution is claimed:

```turtle
@prefix : <https://example.org/events#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

:startTime rdfs:comment
    "Declared OntoUML property stereotype: begin."@en .
```

These generated English comments retain their language under the [generated-text rules](../reference/text.md#language-resolution), including when a source-language override is supplied. This preservation alone introduces **no runtime diagnostic**; existing diagnostic conditions, including ordering's separate INFO requirement, remain unchanged. See [Diagnostic silence](../reference/diagnostics.md#deliberate-silence-and-restricted-payloads).

## Ordering without ordered values

For each supported `isOrdered: true` occurrence, preserve an ordering-declaration comment on the attribute property or the relation's **primary** property. Relation comments identify the source or target end; if both are ordered, preserve both occurrences. No inverse is required or created solely for this purpose.

The declaration says values are ordered; **the generated property mapping does not preserve an actual value sequence**. Do not introduce RDF lists, sequence structures, properties, or inverses solely because of this flag. Range, cardinality, and inverse mappings remain independently applicable.

Each successfully preserved `true` occurrence requires nonfatal INFO identifying the attribute/end and explaining the loss of actual value order (DK-DIAG-18). This limitation alone is not a warning. `false`, absent, and null values generate neither ordering comments nor ordering-loss INFO; do not infer `true` from other source features.

Derived status, both true and false, has its distinct [cross-cutting comment mapping](../reference/text.md#derived-status-comments). Abstractness/extensionality belong to [Class declarations preserved as comments](classes.md#class-declarations-preserved-as-comments). Produced diagnostics remain accessible/exportable even when console filtering hides them; comments and diagnostics serve separate purposes.

---

Governing rules: §§3.3–3.4; DK-PROP-03–06; DK-REL-01, 04, 19; DK-GEN-02; DK-INV-04; DK-DIAG-02, 05, 18; baseline consolidated: **2026-11-20**; repository commit: `283f9b01361830c2dfb1e96b08111e1f8f849b31`; source: [`documentation/specification/transformation-specification.md`](https://github.com/pedropaulofb/ontouml-directkg/blob/283f9b01361830c2dfb1e96b08111e1f8f849b31/documentation/specification/transformation-specification.md).

Accepted update: **RD-02 — Datatype-valued ordinary binary relations (`Alternative B + Q1–Q7 + Conflicts A–I`) & global `DK-PROP-03` mixed-kind rejection** (project-owner formalization included in the cited consolidation).

Accepted update: **RD-18 — Comment preservation of `begin` and `end` property stereotypes** (project-owner formalization included in the cited consolidation).
