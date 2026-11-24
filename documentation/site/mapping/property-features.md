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

If an accepted mapping intentionally creates no property expression, do not create one solely for subsetting, override an [unsupported connector's omission](relations.md#relation-valued-endpoints), or reference a relation, attribute, or misplaced `Property` omitted under `best-effort`. Specifically, under `best-effort` for attributes omitted under [Attributes owned without a local OWL class](attributes-and-datatypes.md#attributes-owned-without-a-local-owl-class) (`DK-ATT-01`, because their owning `Class` is a registered primitive `datatype` or `void` and lacks a generated local `owl:Class`), misplaced `Property` declarations (with valid source IDs) omitted from `Package.contents` under [Malformed package contents](../reference/diagnostics.md#malformed-package-contents) (`DK-GEN-06`), and relations in the omitted-relations set (including relations omitted under `DK-DIAG-03` for non-binary or absent/`null`/malformed `Relation.properties` containers, whose valid `Property` ends reside inside that array):

- When another property's `subsettedProperties` or `redefinedProperties` references an attribute already omitted under that `DK-ATT-01` rule, a misplaced `Property` (with a valid source ID) omitted from `Package.contents` under `DK-GEN-06`, or a valid `Property` end of an omitted relation, DirectKG omits that dependent inclusion axiom cleanly without generating an additional `UNRESOLVED_PROPERTY_REFERENCE` error.
- When the omitted attribute, omitted misplaced `Property`, or a valid `Property` end of an omitted relation itself declares `subsettedProperties` or `redefinedProperties`, DirectKG applies the same clean handling: it omits dependent property-inclusion processing without generating an additional `UNRESOLVED_PROPERTY_REFERENCE` error (or secondary inclusion diagnostic for the omitted attribute's, misplaced `Property`'s, or end's unavailable expression).
- This suppression applies **strictly** to references whose targets are known to have been omitted under `DK-ATT-01`'s owner-lacks-local-class rule, misplaced `Property` declarations omitted from `Package.contents` under `DK-GEN-06`, the omitted-relations set (including `DK-DIAG-03` container/arity omissions and `DK-REL-01` compatibility omissions), or unsupported connectors under `DK-REL-17`. On non-omitted properties, genuinely unresolved references (such as dangling identifiers, non-`Property` targets, reference-type mismatches, and references targeting unindexed non-`Property` entries in `Class.properties` or `Package.contents`), malformed reference values or containers (`INVALID_PROPERTY_REFERENCES`), and references targeting attributes omitted for other independent failures outside this rule (such as `UNRESOLVED_ATTRIBUTE_TYPE`) retain their established `DK-PROP-03` and `DK-DIAG-05` diagnostics.

**Implementation status for `DK-ATT-01`, `DK-GEN-06`, and `DK-DIAG-03` omission suppression.** At [specification registration revision `c87a6a2cd83f6da675018edb1b0af81f86ad7013`](https://github.com/pedropaulofb/ontouml-directkg/blob/c87a6a2cd83f6da675018edb1b0af81f86ad7013/src/ontouml_directkg/properties.py#L40-L61), [`PropertyExpressions` / `emit_property_references`](https://github.com/pedropaulofb/ontouml-directkg/blob/c87a6a2cd83f6da675018edb1b0af81f86ad7013/src/ontouml_directkg/properties.py#L182-L327) already suppress `DK-PROP-03` inclusions for `DK-ATT-01` owner-lacks-local-class omitted attributes (populated via [`collect_attributes`](https://github.com/pedropaulofb/ontouml-directkg/blob/c87a6a2cd83f6da675018edb1b0af81f86ad7013/src/ontouml_directkg/properties.py#L42-L61)) and for `DK-DIAG-03` `Relation.properties` omitted relations (passed through [`index_project`](https://github.com/pedropaulofb/ontouml-directkg/blob/c87a6a2cd83f6da675018edb1b0af81f86ad7013/src/ontouml_directkg/source.py#L177-L191) and added to `omitted` in [`collect_relations`](https://github.com/pedropaulofb/ontouml-directkg/blob/c87a6a2cd83f6da675018edb1b0af81f86ad7013/src/ontouml_directkg/relations.py#L105-L150)). By contrast, misplaced `Property` declarations in `Package.contents` still raise `NotImplementedError` in [`collect_attributes`](https://github.com/pedropaulofb/ontouml-directkg/blob/c87a6a2cd83f6da675018edb1b0af81f86ad7013/src/ontouml_directkg/properties.py#L40-L41) before reaching `omitted_attributes`, and non-object entries or non-list `Class.properties` and `Package.contents` containers still raise `NotImplementedError` in [`index_project`](https://github.com/pedropaulofb/ontouml-directkg/blob/c87a6a2cd83f6da675018edb1b0af81f86ad7013/src/ontouml_directkg/source.py#L151-L185) (lines 151–152 and 184–185).

Unresolved references or failed required transformations outside the defined omission-suppression scope above follow the structural-error policy. Except for this targeted OWL property-kind compatibility check (and inverse availability), DirectKG still does **not** check owner, endpoint, type, domain, range, or other UML semantic compatibility before emitting an otherwise processable inclusion. Structurally processable, kind-compatible references may still yield output outside an OWL 2 DL profile. Inclusion neither merges nor replaces the properties and does not authorize a union-domain/range repair.

## Partial redefinition

An explicit `p1 redefines p0` reference in `redefinedProperties` uses the same expression selection, **OWL property-kind compatibility check** (rejecting unavailable datatype-property inverses and mixed object/data inclusions globally across attributes and relations), `best-effort` omission and scoped `DK-ATT-01` suppression rules, and inclusion axiom as subsetting. **This is a partial translation** (E03 / DK-PROP-03): property inclusion is preserved, while UML's full contextual replacement semantics are not.

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

`isReadOnly` is a defined Boolean flag on `Property` (surviving attributes and association ends of surviving ordinary relations). Any non-`null`, non-boolean value triggers a structural **ERROR** under `DK-DIAG-05` (`strict` and `tolerant` abort; `best-effort` retains **ERROR** severity, omits only the malformed `isReadOnly` field—producing no read-only comment—and preserves the owning `Property`, enclosing `Relation`, valid sibling flags/annotations, and independently applicable mappings). `isReadOnly` is not a defined field on `Relation`: an unexpected `isReadOnly` field on `Relation` remains governed by `UNKNOWN_INFORMATION`, not Boolean-flag validation. See [Malformed Boolean flags](../reference/diagnostics.md#malformed-boolean-flags) for policy outcomes and current `NotImplementedError` / `relations.py` over-check status.

## Boundary stereotype comments

Preserve each explicitly supplied, recognized `begin` or `end` property stereotype through an **English `rdfs:comment` identifying the declared stereotype**, when its eligible property is successfully generated.

| Source occurrence | Comment target and context |
| --- | --- |
| Supported attribute carrying `begin` or `end` | Its generated attribute property |
| Source end of an eligible ordinary relation carrying `begin` or `end` | Its generated primary relation property; identify the source association end |
| Target end of an eligible ordinary relation carrying `begin` or `end` | Its generated primary relation property; identify the target association end |

If both association ends carry covered stereotypes, preserve both occurrences. Placement remains independent of named-inverse generation.

These comments **preserve boundary-stereotype declarations without enforcing temporal semantics**. They introduce no additional logical axioms or temporal validation. Naming, property kind, range, cardinality, and inverse mappings remain unchanged. In particular, an [untyped attribute](attributes-and-datatypes.md#untyped-and-void) retains its datatype-property, owner-domain, and applicable cardinality mappings without a guessed range.

Do not infer either stereotype from names, supply a missing `begin`/`end` counterpart, or reconstruct stereotype information discarded by the exporter. Preserve only the recognized stereotype explicitly supplied in supported input. Malformed `Property.stereotype` values (non-`null`, non-string values or empty/whitespace-only strings) trigger a structural **ERROR** under `DK-DIAG-05` regardless of `--stereotype-policy`: `strict` and `tolerant` abort, while `best-effort` omits only the malformed `stereotype` field (producing no `begin`/`end` comment under `DK-PROP-06`) and preserves the otherwise valid attribute, association end, and enclosing `Relation`. See [Malformed stereotype values](../reference/diagnostics.md#malformed-stereotype-values) for full policy outcomes, precedence, and current implementation status.

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

Each successfully preserved `true` occurrence requires nonfatal INFO identifying the attribute/end and explaining the loss of actual value order (DK-DIAG-18). This limitation alone is not a warning. `false`, absent, and null values generate neither ordering comments nor ordering-loss INFO; do not infer `true` from other source features. Any non-`null`, non-boolean value for `Property.isOrdered` on a surviving attribute or association end triggers a structural **ERROR** under `DK-DIAG-05` (`strict` and `tolerant` abort; `best-effort` retains **ERROR** severity, omits only the malformed `isOrdered` field—producing no ordering comment and no `DK-DIAG-18` INFO—and preserves the owning `Property`, enclosing `Relation`, valid sibling flags/annotations, and independently applicable mappings). `isOrdered` is not a defined field on `Relation`: an unexpected `isOrdered` field on `Relation` remains governed by `UNKNOWN_INFORMATION`. See [Malformed Boolean flags](../reference/diagnostics.md#malformed-boolean-flags).

Derived status, both true and false, has its distinct [cross-cutting comment mapping](../reference/text.md#derived-status-comments). Abstractness/extensionality belong to [Class declarations preserved as comments](classes.md#class-declarations-preserved-as-comments). Produced diagnostics remain accessible/exportable even when console filtering hides them; comments and diagnostics serve separate purposes.

---

Governing rules: §§3.3–3.4; DK-ATT-01; DK-PROP-03–06; DK-REL-01, 04, 19; DK-GEN-02, 05–06; DK-INV-04; DK-DIAG-01–03, 05–06, 18; baseline consolidated: **2026-11-24**; repository commit: `15eff98eb9dfeed69694ff81f099e0b9785e700f`; source: [`documentation/specification/transformation-specification.md`](https://github.com/pedropaulofb/ontouml-directkg/blob/15eff98eb9dfeed69694ff81f099e0b9785e700f/documentation/specification/transformation-specification.md).

Accepted update: **RD-02 — Malformed Boolean flags (Alternative 1 — Uniform field-level omission)** (project-owner formalization included in the cited consolidation).

Accepted update: **RD-02 — Malformed `stereotype` values on `Class`, `Relation`, and `Property` (Alternative 1C + Sub-option 2A)** (project-owner formalization included in the cited consolidation).

Accepted update: **RD-02 — Declaration containers, malformed entries, and misplaced declarations (`Package.contents`, `Class.properties`, non-enumeration `Class.literals`; Alternatives 1A + 2A + 3A + 4A)** (project-owner formalization included in the cited consolidation).

Accepted update: **RD-02 — Non-binary (`len != 2`) and absent/null/malformed `Relation.properties` association-end containers (Alternative A)** (project-owner formalization included in the cited consolidation).

Accepted update: **RD-02 — Attributes owned by a `Class` without a generated local `owl:Class` (Alternative A) and dependent `DK-PROP-03` handling** (project-owner formalization included in the cited consolidation).

Accepted update: **RD-02 — Datatype-valued ordinary binary relations (`Alternative B + Q1–Q7 + Conflicts A–I`) & global `DK-PROP-03` mixed-kind rejection** (project-owner formalization included in the cited consolidation).

Accepted update: **RD-18 — Comment preservation of `begin` and `end` property stereotypes** (project-owner formalization included in the cited consolidation).
