# Input contract

This reference describes **specified input support**, not a compatibility result from an implemented converter.

## Exporter contract

The supported baseline is JSON exported from Visual Paradigm by the official [OntoUML VP-plugin release 0.5.3](https://github.com/OntoUML/ontouml-vp-plugin/releases/tag/0.5.3), within DirectKG's accepted transformation scope. Its Project/model structure, element variants, identifiers, nesting, and references remain the baseline. The bounded language extension below does not replace that structure.

Earlier or later exporter versions may work, but compatibility is not guaranteed and is outside the current development/testing commitment. This contract does not require automatic exporter-version detection or historical compatibility adapters.

The standalone OntoUML Schema is an interpretation reference. Arbitrary schema-conformant documents and arbitrary `ontouml-js` output are not thereby accepted. The current association extraction supplies two ends; n-ary relation support is outside scope.

A Catalog `ontology.json` file is a candidate example, not evidence of compatibility. A selected file must be checked against this contract before being presented as a supported complete input.

## Language enrichment

In textual fields already supported by DirectKG, both plain strings and the schema-defined `languageString` representation are accepted. The schema-defined top-level `Project.languages` field supplies project-level language information. Top-level `Project.description` is supported in plain-string or accepted localized form and maps to an ontology comment when nonempty.

The following is a **JSON field fragment illustrating a localized name**. It is not a complete VP-plugin input document and has not been executed through DirectKG.

```json
{
  "name": {
    "en": "Person",
    "nl": "Persoon"
  }
}
```

For supported source-authored text, language assignment uses this precedence:

1. An explicit user language override.
2. Explicit local language information on the textual value.
3. Exactly one applicable declared project language.
4. An untagged literal.

Without an override, applicable localized values are preserved independently. The empty language key supplies no explicit local tag. Multiple project languages do not authorize choosing one arbitrarily: an otherwise unresolved value remains untagged and produces the specified nonfatal language-assignment warning, with repetition/consolidation governed by DK-DIAG-19.

The override changes literal tagging; it does not select or reorder the original source text used for naming or primitive recognition. Generated/built-in text and external YAML metadata have separate exclusions from source-language propagation. Plain VP-plugin strings remain untagged unless the override or a single applicable project language supplies a tag; the exporter's internal English default is not language evidence.

This extension adds no package-local language declarations, general newer-schema support, or new metadata mappings. Custom `propertyAssignments`, even keys named `language`, `lang`, or `locale`, never supply language information.

See [Labels, comments, and language](text.md) for the text targets and exclusions, and [Multilingual naming](identifiers.md#multilingual-naming) for the separate deterministic selection of naming input.

## Structural requirements

Accepted mappings require source elements and their necessary references to be structurally resolvable. For an ordinary relation undergoing directional-property generation, both classifier endpoints and the required association-end IDs must be valid before either primary or inverse property is generated. A resolved relation-valued endpoint has a different mapping boundary from a null, malformed, or unresolved endpoint.

For separate declarations participating in accepted mappings or required reference resolution, decoded JSON ID strings are compared exactly: no trimming, normalization, or case folding. A duplicate declaration ID is fatal under **every** input policy, even when the declarations have identical contents or unrelated fragments could be transformed. Selecting a declaration, merging declarations, or assigning replacement IDs is prohibited. Ordinary repeated reference objects pointing to one declaration are not duplicate declarations.

Other structural failures follow their applicable recovery rules. `best-effort` does not authorize inventing missing information or delivering syntactically invalid RDF. It also does not authorize continuation after a stereotype condition rejected by the separate stereotype policy. See [Controls](controls.md#control-boundaries) for the policy boundaries.

An explicit attribute `propertyType: null` is supported as [unspecified typing](../mapping/attributes-and-datatypes.md#untyped-and-void); it is not automatically a structural failure. Likewise, an explicit `cardinality: null` on supported attributes and ordinary relation ends is accepted without substituting a multiplicity or producing a diagnostic solely for null. An absent cardinality field instead has the accepted warning-and-continuation fallback. See [Multiplicity parsing and recovery](diagnostics.md#multiplicity-parsing-and-recovery) for the detailed rules and [Policies and precedence](diagnostics.md#policies-and-precedence) for continuation and abortion.

## Intentional omissions

| Source information | Accepted treatment |
| --- | --- |
| Packages | Traverse when needed to discover supported elements; generate no package resources or annotations, names, descriptions, paths, hierarchy, or membership. |
| Diagrams and presentation data | Omit diagram identities/names, appearances, placement, coordinates, dimensions, routing, grouping, layout, colors, and other concrete syntax. |
| Custom `propertyAssignments` | Recognize and omit; do not derive output, transformation settings, or language information from custom entries. Dedicated exported fields retain their own mappings. |

These defined omissions alone produce no diagnostic and are not unsupported-input conditions under any input policy. Package organization and diagram membership/layout must not alter generated domain-level semantics, entity IRIs, or namespaces. Structural traversal remains distinct from preserving organizational data.

Other recognized omissions, such as `restrictedTo`, have their own rules. Not every omission warrants a warning, and absence of warnings does not establish lossless transformation. The [semantic preservation overview](../concepts/semantics.md#preservation-boundaries) distinguishes partial mappings, comments, and intentional omission.

---

Governing rules: §3.2 / RD-01, RD-27; §3.4; DK-GEN-06–07; DK-LBL-02; DK-IRI-10; DK-DAT-02; DK-DIAG-03, 05–06, 09, 19; baseline consolidated: **2026-10-21**; repository commit: `a36322fa87c006cece63aaadd2aa5ccd513f6087`; source: [`documentation/specification/2026-10-21 - specification handoff.md`](https://github.com/pedropaulofb/ontouml-directkg/blob/a36322fa87c006cece63aaadd2aa5ccd513f6087/documentation/specification/2026-10-21%20-%20specification%20handoff.md).
