# Labels, comments, and language

These are **specified text mappings**. They preserve supported source terminology and declarations while keeping lexical naming, literal tagging, and logical axioms distinct. No converter execution or public API is asserted by this reference.

## Labels and descriptions

### Source labels

A named source property/relation that successfully generates a property preserves its original name as `rdfs:label`. Successfully transformed source-backed non-property resources with names also receive source labels, under either IRI strategy. This includes named classes and enumeration-value individuals. The IRI local name is not a substitute for the label, even when it derives from that same text (DK-LBL-01).

Preserve original wording rather than normalized, qualified, or collision-suffixed IRI text. Selecting one localized value for naming must not discard other applicable source-authored labels. Keep available source text even if it cannot supply an ASCII naming candidate. Do not invent labels for unnamed classes or enumeration literals; [source-ID fallback](identifiers.md#unnamed-or-unusably-named-resources) does not change that boundary.

The generated ontology receives a nonempty top-level `Project.name` as `rdfs:label`. Absent, null, or empty project names produce neither fallback labels nor a diagnostic solely for that absence. Naming the project does not select ontology identity or create a project-ID annotation.

### Primary-relation labels

For a successfully generated primary property, both relation-label modes first use the original relation name, or otherwise a usable **target-end** role name. The source-end role does not substitute for that target role.

| When neither source label is available | Accepted behavior |
| --- | --- |
| `source-only` (default) | Generate no primary-property label |
| `generated` | Add a fallback label from the lexical candidate selected by applicable name-based relation-naming rules |

That lexical candidate retains the established source-field/stereotype/grounding-relator/endpoint naming precedence and conditions. See [Primary direction and naming](../mapping/relations.md#primary-direction-and-naming) for the relation-naming algorithm. The fallback label uses the candidate **before IRI-specific processing**, under both IRI strategies; do not parse the final IRI or include IRI-only encoding, collision qualification, or suffixes.

Generated fallback labels receive no automatic source-language propagation, including the explicit language override. Do not add RDF markers, annotations, or auxiliary resources solely to distinguish them from source-authored labels. Absence of such a marker adds no diagnostic or control. These modes leave inverse-label rules and existing naming diagnostics unchanged. See [Controls](controls.md#established-controls) for the canonical options and Python `relation_labels` parameter.

### Description targets

Preserve nonempty supported descriptions as `rdfs:comment`, without translation, summarization, or automatic removal of embedded markup. RDF escaping may change the serialization while preserving lexical content. Absent/null/empty descriptions produce no description annotation or diagnostic solely for that condition.

| Description source | Target, when successfully generated |
| --- | --- |
| Top-level `Project.description` | Ontology resource |
| Class | Corresponding local class |
| Enumeration literal | Corresponding enumeration-value individual |
| Attribute | Attribute property |
| Relation | Primary relation property |
| Target association end | Primary relation property |
| Source association end | Corresponding named inverse property, if generated |

Relation and target-end descriptions are separate comments on the primary property; do not concatenate them. Do not automatically copy the relation description to its inverse. A source-end description does not itself cause inverse generation; if no named inverse exists, omit it without an extra diagnostic solely for that omission.

Do not create a resource solely to host a description or attach primitive-datatype descriptions to shared external datatype IRIs. Package descriptions and custom `propertyAssignments` retain their recognized-omission rules. `Project.description` accepts the supported plain/localized forms within the [bounded input contract](input.md#language-enrichment); that does not establish additional metadata mappings.

## Language resolution

Recognized carriers are the explicit user language override, explicit local keys in supported `languageString` fields, and schema-defined top-level `Project.languages`. For supported source-authored text, use this precedence:

1. Apply the explicit user override in preference to local/project language information.
2. Otherwise preserve the individual value's explicit local language.
3. Otherwise apply exactly one applicable declared project language.
4. Otherwise preserve an untagged literal.

The override accepts one language tag, not a list. Without it, preserve applicable explicitly localized versions independently with their respective tags. The empty key denotes unknown language and supplies no explicit local tag; its value can still use a qualifying override or single project language.

Multiple applicable project languages do not authorize choosing one arbitrarily. A source value with neither override nor explicit local language remains untagged and produces the nonfatal ambiguity warning under DK-DIAG-19. Avoid unnecessary repetition for individual literals; the warning may be consolidated for the affected project/conversion. Explicitly localized values or values covered by an override do not trigger that ambiguity warning. Several explicit local languages are not themselves ambiguous.

Plain VP-plugin strings remain untagged unless an override or single applicable project language supplies a tag. Do not infer language from lexical content, locale, editor defaults, or the exporter's internal English default. Custom assignments such as `language`, `lang`, or `locale` are not language carriers; no VP tagged-value convention or package-local declaration is introduced.

This applies only where source-authored text already has a supported mapping: names/roles, descriptions, enumeration labels, project text, and similar supported annotations. It does not add newer-schema features or expand input beyond the bounded enrichment.

| Text category | Boundary |
| --- | --- |
| Supported source-authored text | Apply the precedence above |
| Generated/built-in text, including stereotype names, explanatory comments, diagnostics, vocabulary terms, fixed tool text, and generated fallback labels | No automatic source-language propagation or override; existing required-English comments retain their wording/language rule |
| RD-28 source-ID annotations | Untagged original strings; no language override |
| External YAML text | Untagged; neither override nor project languages propagate to it |

External descriptive metadata retains its separate [accepted whitelist and mappings](../guides/metadata-and-provenance.md#descriptive-metadata). [Multilingual naming](identifiers.md#multilingual-naming) chooses original lexical input independently of this tagging precedence. Retagging does not choose a different name, reorder translations, or change primitive-recognition input.

## Derived-status comments

Explicit Boolean `isDerived` values, **both `true` and `false`**, are preserved as comments when their eligible local target is successfully generated (DK-GEN-05).

| Source occurrence | Comment target |
| --- | --- |
| Class, including enumeration/custom datatype | Corresponding local class |
| Attribute | Corresponding attribute property |
| Relation | Corresponding primary relation property |
| Source association end | Corresponding primary relation property |
| Target association end | Corresponding primary relation property |

Relation/end comments must distinguish whether each value belongs to the relation, its source end, or its target end. Each explicit occurrence remains distinguishable. Both end flags are preserved independently of named inverse generation; these comments are not copied onto inverses or enumeration-value individuals.

When no eligible local target exists, omit the comment. Do not create a resource, redirect the comment onto a shared XSD datatype or generic DKGM term, or use another target solely to preserve the flag. Absent/null `isDerived` does not imply either Boolean value.

The flag alone supplies no derivation rule, property chain, equivalence, calculation, or other extra logical constraint, and does not suppress ordinary transformation. For example, derived `age` does not authorize inventing a calculation from a birth date. Independently accepted explicit derivation connectors retain their own mappings.

`true` requires a nonfatal INFO **only when its derived-status comment is generated**, identifying the element and explaining that annotation preservation supplies no derivation rule. This limitation alone is not a warning. Do not claim an independently applicable explicit derivation mapping was omitted if it was applied. `false`, or a flag lacking an eligible target, produces no diagnostic solely for that condition; other independently required diagnostics remain.

Descriptions have their separate target rules above. Abstractness, extensionality, and order belong to [Class declarations preserved as comments](../mapping/classes.md#class-declarations-preserved-as-comments); read-only, aggregation, and ordering declarations belong to [Property features](../mapping/property-features.md).

Produced INFO and warnings remain accessible/exportable under the diagnostic contract even when hidden by [console filtering](controls.md#presentation-and-persistence-do-not-change-transformation-outcomes). [Diagnostics and recovery](diagnostics.md#diagnostic-conditions-and-intentional-silence) owns the detailed diagnostic conditions.

---

Governing rules: DK-LBL-01–02; DK-GEN-05, 08; DK-IRI-04, 08–10; DK-DIAG-04, 16, 19; baseline consolidated: **2026-10-21**; repository commit: `a36322fa87c006cece63aaadd2aa5ccd513f6087`; source: [`documentation/specification/2026-10-21 - specification handoff.md`](https://github.com/pedropaulofb/ontouml-directkg/blob/a36322fa87c006cece63aaadd2aa5ccd513f6087/documentation/specification/2026-10-21%20-%20specification%20handoff.md).
