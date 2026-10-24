# Examples

Use these files to inspect the accepted mappings alongside their source data. No production converter exists at the consulted revision, so the Turtle is a **specification illustration**, not captured output. Installation, a runnable first conversion, and source-generated Python API documentation remain pending implementation and verification.

## Examples and evidence status

### Classes and untyped attributes

The example retains two banking-model classes, `Operação` and `Recibo`, each with a distinct attribute named `valor`. It illustrates [class declarations](../mapping/classes.md#classes-and-disjointness), [unspecified attribute typing](../mapping/attributes-and-datatypes.md#untyped-and-void), and [source-ID identity](../reference/identifiers.md#strategy-and-renaming).

The JSON is a complete, bounded **adaptation** of a Catalog project. Its structure and retained values were checked against the supported [input contract](../reference/input.md#exporter-contract) and the official VP-plugin 0.5.3 serializers. That is structural evidence, not an executed conversion, a Visual Paradigm round trip, or a guarantee for the full source project or other Catalog models. The original export's plugin version is not established by its Catalog location.

### Catalog source and adaptation

Source: **Bank Account Ontology**, [OntoUML/UFO Catalog model](https://github.com/OntoUML/ontouml-models/tree/99d23ff1e1c2bf58a7bd99ef0156eba79a611c99/models/bank-account2013), at immutable commit `99d23ff1e1c2bf58a7bd99ef0156eba79a611c99`.

- [Original `ontology.json`](https://github.com/OntoUML/ontouml-models/blob/99d23ff1e1c2bf58a7bd99ef0156eba79a611c99/models/bank-account2013/ontology.json), blob `93d9a809d0f88d18344b50f6e961f8090a7ae10e`.
- [Model metadata and attribution record](https://github.com/OntoUML/ontouml-models/blob/99d23ff1e1c2bf58a7bd99ef0156eba79a611c99/models/bank-account2013/metadata.yaml), which describes a classroom model and declares [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

The adaptation retains the original Project, root Package, and enclosing `Caixa Banco` Package. It keeps only classes `1H9APOGFS_j2pNya` and `1H9APOGFS_j2pNye` and their complete owned attributes. Those class/attribute objects, source IDs, names, flags, and null values are unchanged. Other model declarations are removed, diagrams are set to `null`, and JSON is reformatted. Package organization remains input structure, not an output mapping.

The retained file has seven declarations with unique nonempty IDs: one Project, two Packages, two Classes, and two Properties. It has no non-null cross-reference to a declaration outside that file. Both attribute `propertyType` and `cardinality` fields are explicitly null; neither is a missing or unresolved reference.

The field/nesting comparison used the [VP-plugin 0.5.3 serialization sources](https://github.com/OntoUML/ontouml-vp-plugin/tree/9fc02b8162db9910f21b8713549cafce2627dad0/src/main/java/it/unibz/inf/ontouml/vp/model/ontouml/serialization) at commit `9fc02b8162db9910f21b8713549cafce2627dad0`: Project/model, Package/contents, Class/properties, Property/null typing and cardinality, their inherited fields, and nullable-array/reference handling. No arbitrary schema-only extensions were introduced.

The adapted JSON and illustrative Turtle pair are distributed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/), consistent with the [Catalog repository license](https://github.com/OntoUML/ontouml-models/blob/99d23ff1e1c2bf58a7bd99ef0156eba79a611c99/LICENSE). Retain the source attribution, license links, and adaptation notice when reusing the pair.

### Effective configuration and interpretation

These settings describe the illustration; they are not a runnable invocation:

| Setting | Selected behavior |
| --- | --- |
| Entity base | `https://example.org/directkg-example#` |
| IRI strategy | `id` |
| Language override | `pt-BR` |
| Provenance | `none` |
| External metadata | Not supplied |
| Other controls | Their [established defaults](../reference/controls.md#established-controls) |

The language override tags supported source-authored labels while preserving their text. Each class/attribute uses its own designated source ID. The source underscore becomes `_x5F`, and the leading digit requires the `id_` prefix under [technical ID escaping](../reference/identifiers.md#technical-source-id-escaping). For example, `1H9APOGFS_j2pNyb` becomes local name `id_1H9APOGFS_x5Fj2pNyb`. Equal `valor` labels do not merge the two properties. ID mode adds no RD-28 source-ID annotation.

Both untyped attributes remain `owl:DatatypeProperty` with their respective owner as `rdfs:domain`. Explicit null typing supplies no range; do not infer `xsd:decimal`, `xsd:string`, or another datatype from the banking context or attribute name. Explicit null cardinality supplies no restriction or default. These nulls alone require no diagnostic. Domains remain [inferential axioms](../concepts/semantics.md#domain-graph-and-inferential-axioms), not closed-world validation rules.

The Turtle excerpt includes only those class/property declarations, labels, and domains. It omits the ontology header, including its required DKGM import and Project label, and the applicable classifier-order/flag comments. For example, retained `isAbstract: false` declarations still have the accepted comment/INFO treatment; the excerpt does not show those comments or claim an empty diagnostic report. Provenance is disabled for this illustration. No execution-specific provenance, diagnostic JSON, or byte-exact result is fabricated.

The accepted concrete [DKGM import URI](../mapping/mereology.md#import-and-vocabulary-identity) is shown in the mereology header example. This `.ttl` file retains its focused scope as a parseable mapping excerpt, **not a complete conversion result or deployable ontology**. Prefix spelling, statement order, and whitespace are illustrative; see [Graph and text stability](../reference/output.md#graph-and-text-stability).

## Downloadable pairs

| Pair | Complete adapted input | Illustrative mapping excerpt | Question answered |
| --- | --- | --- | --- |
| Classes and attributes | [classes-and-attributes.json](files/classes-and-attributes.json) | [classes-and-attributes.ttl](files/classes-and-attributes.ttl) | How do distinct same-named attributes with null typing/cardinality retain their identity and owner domains? |

These are the canonical downloadable copies. Use the [CLI guide](../guides/cli.md) and [Python guide](../guides/python.md) for specified interface contracts; neither currently supplies verified conversion calls.

---

Governing rules: §3.2–3.3; DK-CLS-01; DK-ATT-01–03; DK-DAT-03; DK-IRI-02, 05, 09; DK-LBL-02; DK-GEN-05–08, 10; DK-DIAG-15; baseline consolidated: **2026-10-21**; repository commit: `9e52a66af43e39b374d0a642298b1117d12be4d8`; source: [`documentation/specification/2026-10-21 - specification handoff.md`](https://github.com/pedropaulofb/ontouml-directkg/blob/9e52a66af43e39b374d0a642298b1117d12be4d8/documentation/specification/2026-10-21%20-%20specification%20handoff.md).
