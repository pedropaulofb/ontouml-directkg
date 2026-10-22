# Property features

These are **accepted intended mappings** for explicit UML property relationships and supported qualifiers. Property inclusion, comment preservation, and complete UML semantics are different guarantees; no production execution is asserted here.

## Subsetting

Each explicit `p1 subsets p0` reference in `subsettedProperties` contributes `OWL(p1) rdfs:subPropertyOf OWL(p0)`. Resolve both UML Properties independently using their accepted output expressions:

| UML Property | Output expression |
| --- | --- |
| Classifier-owned attribute | Its generated property |
| Target association end | The relation's primary property |
| Source association end with named inverse | That named inverse |
| Source association end without named inverse, with a primary object property | An anonymous inverse of that primary |

Consequently, target→target references give forward→forward inclusion; source→source gives inverse→inverse; target→source gives forward→inverse; source→target gives inverse→forward. These arrows describe which ends reference each other, not a change to the established relation directions. Anonymous expressions do not require a named inverse, new inverse name, or changed IRI.

Process every explicit reference, preserve multiple superproperties, and deduplicate identical resulting axioms. Do not additionally emit logically entailed inverse counterparts or the property's transitive hierarchy closure. [Explicit relation generalization](inverses.md#explicit-inverse-specialization) has a separately required inverse-mirroring rule.

Both references and their underlying property transformations must resolve structurally. If an accepted mapping intentionally creates no property expression, do not create one solely for subsetting or override an [unsupported connector's omission](relations.md#relation-valued-endpoints). Unresolved references or failed required transformations follow the structural-error policy.

DirectKG does not check owner, endpoint, type, property-kind, or other UML semantic compatibility before emitting an otherwise processable inclusion. Such source relationships may produce output outside an OWL 2 DL profile. Inclusion neither merges nor replaces the properties and does not authorize a union-domain/range repair.

## Partial redefinition

An explicit `p1 redefines p0` reference in `redefinedProperties` uses the same expression selection and inclusion axiom as subsetting. **This is a partial translation** (E03 / DK-PROP-03): property inclusion is preserved, while UML's full contextual replacement semantics are not.

Subsetting and redefinition remain distinct UML relationships despite their shared DirectKG representation. A redefinition alone does not generate `owl:equivalentProperty`, contextual value equality, property merging/replacement, new domain/range axioms, or copied/additional cardinality restrictions. Independently applicable declarations, domains, ranges, cardinalities, and relation-generalization mappings remain in force.

This limitation is explained here rather than turned into a new runtime warning. A structurally processable redefinition mapped as specified requires **no warning solely for being a partial translation**. Other applicable diagnostics, including unresolved-reference or underlying-transformation errors, still apply. A quiet conversion does not establish complete contextual preservation.

## Read-only and aggregation comments

The following explicit characteristics have human-readable `rdfs:comment` preservation when the indicated local property is successfully generated:

| Source characteristic | Comment target and context |
| --- | --- |
| `isReadOnly: true` on a supported class attribute | Attribute property; identify the read-only declaration |
| `isReadOnly: true` on either end of an eligible ordinary relation | Primary source-specific property; identify source or target end |
| `aggregationKind: "SHARED"` on either eligible relation end | Primary property; identify end and shared aggregation |
| `aggregationKind: "COMPOSITE"` on either eligible relation end | Primary property; identify end and composite aggregation |

Preserve each covered occurrence, including both ends or several characteristics on one end. Named inverse generation is not a prerequisite. Do not create a property/inverse solely to host comments or move the end comments to an inverse. Consistent wording should make the end and characteristic clear; suitable English forms include “OntoUML source metadata: the target association end has composite aggregation.”

These annotations do not enforce read-only access or add aggregation logic. They introduce no dedicated DirectKG predicate, additional logical property characteristic, or existential dependence solely from `isReadOnly`. They do not determine [mereological eligibility or orientation](mereology.md#source-specific-properties), reverse a relation, substitute an inverse, or repair the source. Independently accepted mappings still apply.

Comment preservation supports human inspection, without guaranteeing machine-readable reconstruction or round-tripping. DK-PROP-04 establishes no additional diagnostic solely for preserving these comments; ordering has its separate INFO rule below. Generated explanatory text does not acquire source-language propagation or the source-language override. See [Language resolution](../reference/text.md#language-resolution).

## Ordering without ordered values

For each supported `isOrdered: true` occurrence, preserve an ordering-declaration comment on the attribute property or the relation's **primary** property. Relation comments identify the source or target end; if both are ordered, preserve both occurrences. No inverse is required or created solely for this purpose.

The declaration says values are ordered; **the generated property mapping does not preserve an actual value sequence**. Do not introduce RDF lists, sequence structures, properties, or inverses solely because of this flag. Range, cardinality, and inverse mappings remain independently applicable.

Each successfully preserved `true` occurrence requires nonfatal INFO identifying the attribute/end and explaining the loss of actual value order (DK-DIAG-18). This limitation alone is not a warning. `false`, absent, and null values generate neither ordering comments nor ordering-loss INFO; do not infer `true` from other source features.

Derived status, both true and false, has its distinct [cross-cutting comment mapping](../reference/text.md#derived-status-comments). Abstractness/extensionality belong to [Class declarations preserved as comments](classes.md#class-declarations-preserved-as-comments). Produced diagnostics remain accessible/exportable even when console filtering hides them; comments and diagnostics serve separate purposes.

---

Governing rules: DK-PROP-03–05; §§3.3–3.4; DK-GEN-02; DK-INV-04; DK-DIAG-18; baseline consolidated: **2026-10-21**; repository commit: `0307dd346c91346fa38bda2f8d57c9930b00751f`; source: [`documentation/specification/2026-10-21 - specification handoff.md`](https://github.com/pedropaulofb/ontouml-directkg/blob/0307dd346c91346fa38bda2f8d57c9930b00751f/documentation/specification/2026-10-21%20-%20specification%20handoff.md).
