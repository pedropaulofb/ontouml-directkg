# Input contract

This reference describes **specified input support**. The membership section identifies the repeated-reference cases checked against the converter.

## Exporter contract

The supported baseline is JSON exported from Visual Paradigm by the official [OntoUML VP-plugin release 0.5.3](https://github.com/OntoUML/ontouml-vp-plugin/releases/tag/0.5.3), within DirectKG's accepted transformation scope. Its Project/model structure, element variants, identifiers, nesting, and references remain the baseline. The bounded language extension below does not replace that structure.

Earlier or later exporter versions may work, but compatibility is not guaranteed and is outside the current development/testing commitment. This contract does not require automatic exporter-version detection or historical compatibility adapters.

The standalone OntoUML Schema is an interpretation reference. Arbitrary schema-conformant documents and arbitrary `ontouml-js` output are not thereby accepted. The current association extraction supplies two ends; n-ary relation support is outside scope.

A Catalog `ontology.json` file is a candidate example, not evidence of compatibility. A selected file must be checked against this contract before being presented as a supported complete input.

The [classes-and-attributes example](../examples/index.md#catalog-source-and-adaptation) documents a bounded Catalog adaptation checked against the 0.5.3 serialization structure, with its exact provenance and reference checks. It does not establish compatibility for the full source project or other Catalog files.

### Source file input

Every transformation in the current version requires a concrete OntoUML JSON input file identified by a file path, through both CLI and Python, independently of provenance mode, including `none`. The file's contents remain subject to the exporter baseline above and the accepted language enrichment below.

Already parsed JSON objects, Python dictionaries, and other fileless representations cannot substitute for the required source file. Internal parsing and processing of that file in memory remain allowed. This restriction does not change Python output or diagnostic capabilities.

Alternative source-input mechanisms are outside the current version's scope, with no commitment to implement them in a future release. Source checksums follow [Artifacts and digests](../guides/metadata-and-provenance.md#artifacts-and-digests).

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

Non-`«instantiation»` `Relation` elements (including ordinary relations and `«derivation»` relations) require a 2-element `properties` JSON array of `Property` objects (`DK-DIAG-03`, `§3.2`). If `properties` is absent, explicitly `null`, not a JSON array, contains non-object or non-`Property` entries, or has length other than `2` (empty, unary, or unsupported n-ary with `>= 3` ends), DirectKG reports a structural **ERROR** (`strict` and `tolerant` abort; `best-effort` omits the relation and all dependent output and continues, without adding n-ary relation support). For `«instantiation»` relations, absent `properties`, explicit `properties: null`, and valid `Property`-object arrays (regardless of length) retain `DK-INS-01–02` discard behavior, whereas non-array or malformed containers trigger the structural **ERROR**. See [Non-binary and malformed relation properties containers](diagnostics.md#non-binary-and-malformed-relation-properties-containers) for policy outcomes, diagnostic precedence, downstream `best-effort` handling, and current implementation status.

Within the existing scope of accepted mappings and required reference resolution, source IDs are opaque strings. An `id` field is **missing** when absent. A supplied ID is **invalid** when null, not a JSON string, empty (`""`), or not encodable as UTF-8. Accept every other string unchanged, including whitespace-only strings. Do not trim, normalize, case-fold, coerce, or invent replacement IDs.

Missing and invalid IDs follow the existing [structural-error policies](diagnostics.md#policies-and-precedence). The duplicate-ID abort rule below remains unchanged.

!!! warning "Duplicate declaration IDs abort under every input policy"

    For separate declarations participating in accepted mappings or required reference resolution, decoded JSON ID strings are compared exactly: no trimming, normalization, or case folding. A duplicate declaration ID is fatal under **every** input policy, even when the declarations have identical contents or unrelated fragments could be transformed. Selecting a declaration, merging declarations, or assigning replacement IDs is prohibited. Ordinary repeated reference objects pointing to one declaration are not duplicate declarations.

Other structural failures follow their applicable recovery rules. `best-effort` does not authorize inventing missing information or delivering syntactically invalid RDF. It also does not authorize continuation after a stereotype condition rejected by the separate stereotype policy. See [Controls](controls.md#control-boundaries) for the policy boundaries.

An explicit attribute `propertyType: null` is supported as [unspecified typing](../mapping/attributes-and-datatypes.md#untyped-and-void); it is not automatically a structural failure. Likewise, an explicit `cardinality: null` on supported attributes and ordinary relation ends is accepted without substituting a multiplicity or producing a diagnostic solely for null. An absent cardinality field instead has the accepted warning-and-continuation fallback. See [Multiplicity parsing and recovery](diagnostics.md#multiplicity-parsing-and-recovery) for the detailed rules and [Policies and precedence](diagnostics.md#policies-and-precedence) for continuation and abortion.

### Package contents

The root model package and nested packages accept an absent `contents` field, explicit `null`, or an empty JSON array (`[]`) as an empty collection. These representations produce no additional diagnostic solely for being empty (`DK-GEN-06`). The VP-plugin 0.5.3 [package serializer](https://github.com/OntoUML/ontouml-vp-plugin/blob/9fc02b8162db9910f21b8713549cafce2627dad0/src/main/java/it/unibz/inf/ontouml/vp/model/ontouml/serialization/PackageSerializer.java) can serialize an empty collection as `null`.

A non-null, non-array `contents` value is a structural error. At the root model (`Project.model.contents`) it prevents reliable discovery of declarations and aborts under every input policy. In a nested package, `best-effort` permits omission of the affected contents.

Within valid `Package.contents` arrays (root and nested), permitted package-level declaration types are `Package`, `Class`, `Relation`, `Generalization`, and `GeneralizationSet`. Non-object entries, objects lacking a valid nonempty string `type` (absent, `null`, non-string, empty, or whitespace-only), and misplaced declarations of known OntoUML types not permitted in `Package.contents` (`Project`, `Property`, `Literal`) trigger a structural **ERROR** (`DK-GEN-06`, `DK-DIAG-05`): `strict` and `tolerant` abort, while `best-effort` retains **ERROR** severity, omits only the malformed or misplaced entry without aborting the root package, and preserves valid siblings in both root and nested packages. Objects inside `Package.contents` carrying a valid nonempty string `type` outside the supported OntoUML declaration-type set (`Project`, `Package`, `Class`, `Relation`, `Property`, `Generalization`, `GeneralizationSet`, `Literal`) continue to use `UNKNOWN_INFORMATION`. See [Malformed package contents](diagnostics.md#malformed-package-contents) for policy outcomes, diagnostic precedence, downstream `DK-PROP-03` handling, and current implementation status.

### Class properties and non-enumeration literals

- **`Class.properties` (`DK-ATT-01`, `DK-DIAG-05`):** Absent `properties`, explicit `properties: null`, and `properties: []` are accepted as empty without a diagnostic. Any non-null, non-array `Class.properties` value, non-object entry, or non-`Property` entry (including known non-`Property` OntoUML types, valid unknown string `type` values, or objects lacking a valid string `type`) triggers a structural **ERROR** (not `UNKNOWN_INFORMATION`): `strict` and `tolerant` abort, while `best-effort` retains **ERROR** severity, omits the malformed container or invalid entry, and retains the owning `Class` (where eligible under `DK-CLS-01`), valid `Property` siblings, and independent mappings.
- **Non-enumeration `Class.literals` (`DK-CLS-11`, `DK-DIAG-05`):** For any `Class` without `stereotype == "enumeration"`, absent `literals`, explicit `literals: null`, and `literals: []` are accepted as empty without a diagnostic. Any non-null, non-array `literals` value, non-object/non-`Literal` entry, or valid `Literal` entry triggers a structural **ERROR**: `strict` and `tolerant` abort, while `best-effort` retains **ERROR** severity, omits those `literals` without creating `owl:NamedIndividual`s or enumeration axioms, and retains the owning `Class` (where eligible under `DK-CLS-01`) and independent mappings. Enumeration classes (`stereotype == "enumeration"`) remain governed by [Enumerations and closure](../mapping/classes.md#enumerations-and-closure) and `DK-DIAG-13`.

See [Class properties and non-enumeration literals](diagnostics.md#class-properties-and-non-enumeration-literals) for policy outcomes, `DUPLICATE_SOURCE_ID` / `DK-DIAG-06` / `§3.4` precedence, `DK-PROP-03` interaction, and current implementation status.

### Generalization-set membership

Within each set's `generalizations` array, otherwise valid references resolving to the same source `Generalization` declaration count as **one membership** (DK-GEN-12). Identity uses the exact decoded source-ID string, without trimming, normalization, or case folding. Counting is separate for each set and applies under `strict`, `tolerant`, and `best-effort`. The existing class, relation, and categorizer mappings use that effective membership.

Distinct generalization declarations remain distinct members even when they share endpoint classifiers. Repeated references are also distinct from separate declarations sharing an ID: duplicate declaration IDs still abort under every input policy. Repetition alone adds no diagnostic or control; independently required diagnostics remain applicable.

These are **specification illustrations** using shorthand references to declarations, not complete JSON inputs or observed conversion results:

| References in one set | Accepted treatment |
| --- | --- |
| Fully resolved `[g1, g1]` | One member. Apply the existing singleton rules, including required INFO when completeness is applied. |
| Fully resolved `[g1, g2, g1]`, with distinct declarations | Two members. Apply the existing mappings and their prerequisites. |
| `[g1, g1, g2]`, with `g2` unresolved or its transformation failed | Retain the existing error/recovery treatment. Counting `g1` once cannot authorize singleton completeness. |

Counting repeated references once does not authorize ignoring invalid references, unresolved references, or failed member transformations. An explicitly empty array has its own structural-error rule. An incomplete class set with a usable categorizer follows [the bounded categorizer recovery rule](../mapping/higher-order.md#recovery-for-incomplete-categorized-class-sets). A class set with a nonempty `generalizations` array and a present, non-null unusable `categorizer` follows [unusable-categorizer recovery](../mapping/higher-order.md#recovery-for-an-unusable-categorizer), and a relation set with a nonempty `generalizations` array and a present, non-null `categorizer` follows [relation-set categorizer recovery](../mapping/higher-order.md#non-null-categorizer-on-relation-generalization-sets), while an absent or explicit `null` `categorizer` on either set remains uncategorized without error. See [class-set recovery](../mapping/classes.md#singleton-and-recovery-boundaries), [relation-set completeness](../mapping/relations.md#relation-set-completeness), and [diagnostic conditions](diagnostics.md#structural-failures-sets-and-connectors).

A recognized set with an absent, explicitly `null`, or other non-array `generalizations` value follows the [membership-container error rule](diagnostics.md#missing-or-malformed-generalization-set-membership). VP-plugin 0.5.3 can serialize an empty membership collection as JSON `null`. DirectKG treats that exported value as explicit null under DK-DIAG-12. [Exporter serializer source](https://github.com/OntoUML/ontouml-vp-plugin/blob/9fc02b8162db9910f21b8713549cafce2627dad0/src/main/java/it/unibz/inf/ontouml/vp/model/ontouml/serialization/Serializer.java#L57-L72)

**Verified execution at [revision `6aba9b8819b35648d920802c598f4a35bfe32d1d`](https://github.com/pedropaulofb/ontouml-directkg/commit/6aba9b8819b35648d920802c598f4a35bfe32d1d).** Focused Python conversions of class and relation sets confirmed that repeating valid references left the resulting mappings and diagnostics equivalent to the corresponding unrepeated inputs across the three input policies. The checks covered fully resolved singleton completeness and its INFO, distinct declarations with equal endpoints, and partial failures that preclude singleton completeness. [Class-set checks](https://github.com/pedropaulofb/ontouml-directkg/blob/6aba9b8819b35648d920802c598f4a35bfe32d1d/tests/transformation/test_classes.py#L306) · [Relation-set checks](https://github.com/pedropaulofb/ontouml-directkg/blob/6aba9b8819b35648d920802c598f4a35bfe32d1d/tests/transformation/test_relations.py#L1000)

**Historical source observation.** At [`2b427908a7e29d546486a616a22495ea0424f294`](https://github.com/pedropaulofb/ontouml-directkg/blob/2b427908a7e29d546486a616a22495ea0424f294/src/ontouml_directkg/generalizations.py), both class- and relation-set processing had a `NotImplementedError` guard for repeated references.

## Intentional omissions

| Source information | Accepted treatment |
| --- | --- |
| Packages | Traverse when needed to discover supported elements; generate no package resources or annotations, names, descriptions, paths, hierarchy, or membership. |
| Diagrams and presentation data | Omit diagram identities/names, appearances, placement, coordinates, dimensions, routing, grouping, layout, colors, and other concrete syntax. |
| Custom `propertyAssignments` | Recognize and omit; do not derive output, transformation settings, or language information from custom entries. Dedicated exported fields retain their own mappings. |

These defined omissions alone produce no diagnostic and are not unsupported-input conditions under any input policy. Package organization and diagram membership/layout must not alter generated domain-level semantics, entity IRIs, or namespaces. Structural traversal remains distinct from preserving organizational data.

Other recognized omissions, such as `restrictedTo`, have their own rules. Not every omission warrants a warning, and absence of warnings does not establish lossless transformation. The [semantic preservation overview](../concepts/semantics.md#preservation-boundaries) distinguishes partial mappings, comments, and intentional omission.

---

Governing rules: §3.2 / RD-01, RD-27; §3.4; DK-GEN-06–07, 12; DK-CLS-01, 08–09, 11; DK-ATT-01; DK-PROP-03; DK-HO-04; DK-REL-15–16, 20; DK-INS-01–02; DK-LBL-02; DK-IRI-10; DK-DAT-02; DK-DIAG-03, 05–06, 09, 12–14, 19; baseline consolidated: **2026-11-23**; repository commit: `c87a6a2cd83f6da675018edb1b0af81f86ad7013`; source: [`documentation/specification/transformation-specification.md`](https://github.com/pedropaulofb/ontouml-directkg/blob/c87a6a2cd83f6da675018edb1b0af81f86ad7013/documentation/specification/transformation-specification.md).

Accepted update: **RD-02 — Declaration containers, malformed entries, and misplaced declarations (`Package.contents`, `Class.properties`, non-enumeration `Class.literals`; Alternatives 1A + 2A + 3A + 4A)** (project-owner formalization included in the cited consolidation).

Accepted update: **RD-02 — Non-binary (`len != 2`) and absent/null/malformed `Relation.properties` association-end containers (Alternative A)** (project-owner formalization included in the cited consolidation).

Accepted clarification: **RD-02 — Minimal opaque source identifiers, Alternative A** (project-owner formalization included in the cited consolidation).

Accepted update: **RD-05 — File-only transformation input and exact-byte source checksums** (project-owner formalization included in the cited consolidation).
