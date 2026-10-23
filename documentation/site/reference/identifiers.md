# Identifiers and naming

This reference describes **specified identity construction**, not tested converter behavior. Identity and display text serve different purposes: an IRI can require disambiguation while its source label remains unchanged. The [control catalog](controls.md#established-controls) owns selectable values and defaults. These are IRIs **generated for converted models**; registered project and vocabulary PIDs are described separately in [Persistent identifiers and redirects](persistent-identifiers.md).

## Base and ontology IRIs

The effective entity base supplies the prefix to which generated local names are appended. Preserve a supplied final `#` or `/`; otherwise append `#` without a warning. Derive the ontology IRI by removing a final `#` from that effective base, or preserving it unchanged otherwise, including a final `/`.

| Selected base | Effective entity base | Ontology IRI |
| --- | --- | --- |
| `https://example.org/model` | `https://example.org/model#` | `https://example.org/model` |
| `https://example.org/model#` | `https://example.org/model#` | `https://example.org/model` |
| `https://example.org/model/` | `https://example.org/model/` | `https://example.org/model/` |
| Omitted | `https://example.org/directkg#` | `https://example.org/directkg` |

These are namespace illustrations, not published ontology addresses. Omission requires a nonfatal warning that the default is a placeholder namespace and is not recommended for publication. It does not authorize treating an explicitly empty or whitespace-only supplied value as omission.

Before conversion, validate the supplied, effective, and derived ontology IRIs as syntactically valid absolute RDF IRIs. Beyond the delimiter rule, do not trim, percent-encode repairs, resolve a relative reference, or substitute the placeholder. There is no HTTP(S)-only restriction, network-availability check, or rejection of syntactically permitted Unicode solely because it is Unicode.

For example, relative `my-model` is rejected. `https://example.org/model#part` is itself an absolute IRI, but the delimiter rule would produce invalid `https://example.org/model#part#`; reject the configuration rather than repairing it. Rejection applies under every input policy before conversion: CLI code `2`, programmatic Python signaling, and no ontology, transformation outcome, or conversion-diagnostics report. The Python exception class is unspecified.

There is no independent ontology-IRI control. This derivation neither changes entity identity nor selects the imported DKGM vocabulary's still-unresolved persistent identity. See [Ontology header](output.md#ontology-header).

## Strategy and renaming

The default `name` strategy favors readable identifiers. **Renaming a source element may change its IRI** (E06 / DK-IRI-02). In particular, name-based enumeration-value identity also depends on its enumeration class's resolved local name. Adding a usable translation that sorts earlier can change the selected name even if an existing translation stays unchanged.

The `id` strategy favors source-identity stability. A named resource still uses its designated source ID, not its name; changing a label does not itself select a different ID-based local name. Stability depends on retaining that designated ID and base. It is not a promise that copied/re-exported models retain the same source IDs.

| Generated resource | Designated ID for `id` construction |
| --- | --- |
| Class or classifier-owned attribute | Its own source element ID |
| Enumeration-value individual | The literal element's own ID, without an enumeration-ID prefix |
| Primary relation property | Target association-end ID |
| Generated named inverse | Source association-end ID |

The enclosing association's ID is not the IRI basis for either direction, including self-relations. Disabling inverse generation leaves the primary property's target-end basis unchanged; the source-end ID then produces no separate inverse property. Association IDs can still be used internally or in diagnostics.

Changing inverse mode must not change source-backed IRIs. Generated inverse candidates are resolved only after all source-backed claims/final IRIs, preserving source-backed precedence. [Inverse naming](../mapping/inverses.md#inverse-naming) owns the inverse-specific algorithms and their collision order.

## Names, escaping, and collisions

### Source names

For a supported localized field, first [select its original text](#multilingual-naming). Name normalization then performs Unicode normalization, trimming, diacritic removal, replacement of whitespace/punctuation with `_`, collapse of repeated underscores, removal of leading/trailing underscores, restriction to ASCII letters/digits/underscores, and protection of a leading digit using `_`. Canonical decomposition-based Unicode normalization is recommended (DK-IRI-03).

This is lexical processing, not terminology repair. Do not translate, singularize/pluralize, expand abbreviations, correct spelling, substitute synonyms, fuzzy-match, or infer semantic equivalence. Retained source labels preserve their original wording rather than this IRI form.

### Unnamed or unusably named resources

Established naming rules and type-specific fallbacks take priority. In name mode, an unnamed or unusably named class uses `unnamedClass_<escaped-source-id>`, without its stereotype in that synthetic name or an invented label. Transformation continues with a nonfatal warning identifying available element type, ID, stereotype, and generated IRI. In ID mode an unnamed class uses its source ID while retaining the type-specific unnamed-source warning.

For an otherwise transformable source-backed resource still lacking a usable name-based candidate after applicable fallbacks, reuse its existing ID-strategy candidate **if its designated ID is usable**. This resource-specific fallback retains ID escaping, digit protection, collision handling, and source-backed precedence; it does not switch the configured strategy.

Enumeration literals use this generic fallback with their own IDs. They do not gain an `unnamedLiteral_` prefix. Keep any source-authored label even if it cannot supply an ASCII naming candidate; do not invent a label for an unnamed value. A fallback-preserved literal still counts as successfully transformed for [enumeration closure and inequality](../mapping/classes.md#enumerations-and-closure).

| Generic-policy condition | Diagnostic |
| --- | --- |
| `name` needs generic source-ID fallback | Nonfatal WARNING identifying the affected element and generated IRI |
| `id`, with name absent, null, empty, or whitespace-only | Nonfatal INFO identifying the element and missing-name condition |
| Ordinary designated-ID use under `id` | None solely for using that ID |

These generic diagnostics remain nonfatal under every input policy. Type-specific diagnostics, including the unnamed-class warning above, retain priority and are not replaced by the generic INFO rule. The generic ID-mode INFO condition concerns missing descriptive text; a nonempty source label that cannot normalize into an ASCII candidate is not thereby an absent name. This fallback defines no treatment for cases where its prerequisites fail and no other accepted rule resolves them.

### Technical source-ID escaping

IDs use byte escaping, not semantic name normalization. Preserve ASCII letters, digits, and case. Encode every other UTF-8 byte as `_xHH`, using uppercase hexadecimal; `_` itself becomes `_x5F`. Do not trim, transliterate, case-fold, or otherwise rewrite source IDs. The escaping must be injective with respect to source-ID bytes and should be reversible.

| Source ID | Escaped bytes | When used as the entire local name |
| --- | --- | --- |
| `A_B` | `A_x5FB` | `A_x5FB` |
| `9A` | `9A` | `id_9A` |
| `é` | `_xC3_xA9` | `_xC3_xA9` |

The `id_` protection applies only when an escaped ID is the entire local name and starts with a digit. Do not add it when that ID follows an already-safe synthetic prefix, such as `unnamedClass_`.

### Qualification and collision groups

Independently modeled properties remain distinct even when names coincide. A unique normalized source-backed property candidate may be used directly. Colliding ordinary source-backed properties are first qualified as `<propertyName>_<ownerOrSourceName>` (DK-PROP-01–02).

If the required owner/source qualifier has no usable name, use its class fallback candidate `unnamedClass_<escaped-source-id>`, based on that **owner/source classifier's own ID**. Reuse the candidate and technical escaping before classifier collision suffixes. Thus a colliding `name` property owned by an unnamed classifier with ID `C17` has qualified candidate `name_unnamedClass_C17`. Qualification itself adds no diagnostic; existing missing-name/fallback/input diagnostics remain.

After applicable fallbacks and qualification, a unique candidate remains unsuffixed. Every member of a remaining collision group of size `N` receives `_1` through `_N`; none remains unsuffixed. Allocation must be deterministic and stable for unchanged supported input, using stable source information, preferably IDs or deterministic source order. The contract does not select which member receives a particular suffix independently of those rules.

Do not merge properties, change an object/datatype property kind, replace them through inclusion axioms, or repair a merge by introducing union domains/ranges. Name collisions are also not duplicate declaration IDs: duplicates in the [input contract's scope](input.md#structural-requirements) abort under every input policy. A collision between distinct escaped source IDs is exceptional and must not be silently repaired as an ordinary name collision; its exact disposition is unspecified.

For a usable name-based enumeration value, construct `<ResolvedEnumerationLocalName>_<NormalizedValueName>`. The enumeration prefix is its class's **already resolved** local name after naming/collisions. A value's normalized name follows the same lexical selector and normalization; distinct literals remain distinct even when their names coincide (DK-IRI-08).

## Source identifiers

Name mode normally adds one untagged `dcterms:identifier` string to each eligible generated resource. Preserve the designated ID's original lexical content, without IRI escaping, normalization, or language tagging; ordinary RDF serialization escaping is allowed.

| Eligible generated resource | Identifier annotation value |
| --- | --- |
| Local class/custom datatype resource | Its source classifier ID |
| Enumeration-value individual | Its source literal ID |
| Attribute property | Its source attribute ID |
| Primary relation property | Target association-end ID |
| Named inverse property | Source association-end ID |

The source-ID fallback in name mode retains this default annotation. `--omit-identifiers` suppresses only these RD-28 annotations; it does not alter identity, strategy, internal IDs, diagnostics, or identifier annotations established independently. Under `id`, no RD-28 annotation is emitted solely for traceability and the flag is a valid no-op.

Do not additionally attach the association's ID to generated relation properties, add a project-ID annotation through the project-name mapping, or create a resource solely to hold an ID. Anonymous restrictions, omitted packages/diagrams, deliberately discarded instantiation information, and other out-of-scope resources do not acquire RD-28 annotations. Neither source-language propagation nor its explicit override applies to these strings (DK-IRI-09).

## Multilingual naming

Lexical selection and literal language tagging are separate. For a supported `languageString`, consider only values that yield a nonempty candidate under name normalization **before collision handling**, then choose the first under this ordering:

1. Compare language keys lexicographically after changing ASCII uppercase letters to lowercase. The empty key sorts first.
2. For equally comparing language keys, compare the original text values lexicographically by Unicode code points.
3. Identical text needs no further tie-break.

Use the selected **original text** as input to applicable naming rules. Existing field precedence, normalization, synthesis, and collisions still apply. If no candidate is usable, apply the affected resource's accepted fallback/diagnostic rules; the selector adds no new fallback for unspecified cases.

This **JSON field-fragment illustration** is not a complete VP-plugin input and has not been executed through DirectKG:

```json
{
  "name": {
    "nl": "Persoon",
    "en": "Person"
  }
}
```

The naming input is `Person`, regardless of JSON key order. Both applicable labels remain preserved with their [language treatment](text.md#language-resolution). A usable value under the empty language key would sort first; for tagging, that key supplies no local language.

Neither the user language override nor `Project.languages` selects or reorders candidates. Primitive recognition uses the same selected original text and [bounded registry lookup](../mapping/attributes-and-datatypes.md#primitive-registry) under both IRI strategies. Generated primary-relation fallback labels also use the applicable lexical candidate under either strategy, before IRI-specific artifacts; ID-based IRI construction itself remains unchanged.

Multiple localized values alone produce no additional diagnostic or new control. For inverse eligibility, a role is present when **any** value contains a non-whitespace character; successful ASCII normalization is not required merely to count it as present. Inverse eligibility and inverse-specific naming retain their own rules.

Deterministic identity does not guarantee byte-identical Turtle. See [Graph and text stability](output.md#graph-and-text-stability) for serialization, RDF-list order, and provenance boundaries.

---

Governing rules: DK-IRI-01–10; DK-PROP-01–02; DK-CONF-01–03; DK-DIAG-05; baseline consolidated: **2026-10-21**; repository commit: `0307dd346c91346fa38bda2f8d57c9930b00751f`; source: [`documentation/specification/2026-10-21 - specification handoff.md`](https://github.com/pedropaulofb/ontouml-directkg/blob/0307dd346c91346fa38bda2f8d57c9930b00751f/documentation/specification/2026-10-21%20-%20specification%20handoff.md).
