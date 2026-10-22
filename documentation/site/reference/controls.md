# Controls

This is the canonical catalog of **specified controls and defaults**. No production CLI or public conversion API exists at the reviewed repository revision. Option spellings below establish the intended contract; they are not runnable invocation instructions.

## Established controls

| CLI control | Values / supplied form | Default | Accepted effect and boundary |
| --- | --- | --- | --- |
| `--base-iri` | One absolute RDF IRI | `https://example.org/directkg#`, with a placeholder warning when omitted | Select the entity base and derive the ontology IRI. Preserve a final `#` or `/`; otherwise append `#`. Validate the supplied base and both derived IRIs before conversion, without automatic repair or network checking. See [Ontology header](output.md#ontology-header). |
| `--iri-strategy` | `name`, `id` | `name` | Select readable name-based identity or identity derived from designated source IDs. Renaming can change name-based IRIs. A resource-specific ID fallback does not change the configured strategy. See [Strategy and renaming](identifiers.md#strategy-and-renaming). |
| `--input-policy` | `strict`, `tolerant`, `best-effort` | `tolerant` | Govern unrecognized non-stereotype information and structural-error recovery. `strict` aborts on unrecognized information; the other modes warn and continue with recognized information. Recoverable invalid values/references remain errors: `strict`/`tolerant` abort, while `best-effort` can continue only within accepted recovery rules. |
| `--stereotype-policy` | `require-known`, `allow-missing`, `allow-custom` | `allow-custom` | Exclusively govern missing/unrecognized stereotypes. `require-known` requires known class/relation stereotypes; `allow-missing` additionally permits their absence; `allow-custom` also accepts supplied unrecognized stereotypes with a warning. Missing attribute/end stereotypes are accepted in every mode. Rejected conditions abort independently of input policy. |
| `--inverse-properties` | `all`, `informed`, `named`, `none` | `all` | Generate all eligible named inverses; only those with an inverse-facing role or non-null multiplicity; only those with an inverse-facing role; or none, respectively. This does not prohibit anonymous inverse expressions required or permitted by accepted mappings. |
| `--no-stereotype-relation-naming` | Boolean flag | Not supplied; stereotype-derived naming enabled | Skip the stereotype-derived semantic naming step when supplied. Source names and target roles retain their precedence, followed by the applicable endpoint fallback. |
| `--relation-labels` | `source-only`, `generated` | `source-only` | Preserve relation names or target-role terminology where available. When neither supplies a label, `generated` adds a lexical fallback; `source-only` does not. Fallback labels precede IRI-only collision/encoding processing and receive no RDF origin markers solely to distinguish their origin. |
| `--material-property-chains` | `none`, `omit-conflicting-constraints`, `preserve-conflicting-constraints` | `none` | Disable material chains, or generate eligible unambiguous material–relator/mode chains with targeted omission or preservation of affected cardinality and property-disjointness constraints. This replaces the former boolean flag and does not control DKGM imports, generic chains, or source-specific mereology. |
| `--language` | Exactly one language tag | No user override | Override local/project language information for supported source-authored text. It does not choose naming/primitive-recognition inputs or propagate to generated fallback labels, source-ID annotations, or external YAML text. See [Language enrichment](input.md#language-enrichment). |
| `--omit-identifiers` | Boolean flag | Not supplied; RD-28 annotations enabled under `name` | Suppress only RD-28 source-ID `dcterms:identifier` annotations. Accepted with either strategy; a valid no-op under `id`. It does not change IRIs, internal IDs, diagnostics, or independently established identifier annotations. See [Source identifiers](identifiers.md#source-identifiers). |
| `--metadata-file` | Explicit path to a file named `metadata.yaml` | Not supplied; no discovery | Ingest only the seven selected Catalog metadata fields from YAML. Other formats and implicit discovery are not accepted. Ignored metadata fields supply neither annotations nor language/configuration settings. |
| `--provenance` | `none`, `embedded`, `sidecar` | `embedded` | Omit transformation provenance, include it in the ontology graph, or write separate Turtle provenance. Descriptive metadata is retained in all modes. Automatic sidecar writing requires a concrete ontology output path. See [Artifacts and serialization](output.md#artifacts-and-serialization). |
| `--diagnostics-file` | Complete caller-selected output-file path | Not supplied; no CLI diagnostics file | Export every diagnostic actually produced to JSON, including those hidden by console filtering and those produced before an accepted abort. For conversions that run, export is attempted even after specified artifact-delivery failures. Supplied-base rejection produces no conversion-diagnostics report. |
| `--console-level` | `info`, `warning`, `error` | `info` | Display INFO/WARNING/ERROR, WARNING/ERROR, or ERROR, respectively. Filter console presentation only; retain every produced diagnostic for collection, programmatic access, and requested JSON export. |

See [Identifiers and naming](identifiers.md) and [Labels, comments, and language](text.md) for the available identity/text explanations. Detailed inverse construction, chain semantics, metadata/provenance, and diagnostic policies remain assigned to later waves. Links are added as their owning pages are delivered.

## Interface parity

Every established ontology-transformation control must be available through both CLI and Python, with equivalent selectable behaviors, identical defaults, and the same transformation effects. Equivalent effective configurations invoke the same accepted transformation rules. This does not promise identical execution provenance across separate runs.

The specification fixes the Python parameter `relation_labels`, with values `"source-only"` and `"generated"` and default `"source-only"`. Most other Python parameter names, configuration representations, function signatures, return types, and exception classes remain unspecified. A negative CLI flag need not dictate Python spelling or polarity. No Python call is fabricated here.

Persistent diagnostic writing is separate from transformation-control parity. The CLI can request its diagnostics file with the control above. Python must expose structured diagnostics, including after an accepted abort, and a **separate explicitly invoked** JSON export operation using the same report schema/content contract as the CLI. Python conversion does not automatically write that file. Exact report member names and runtime diagnostic codes remain unspecified.

Python must also expose semantically equivalent metadata/provenance controls with the same provenance default, and make separate provenance available as a graph with explicit file serialization. Source-derived API signatures remain pending real public source and mkdocstrings generation.

## Control boundaries

### Input handling is distinct from stereotype acceptance

The stereotype policy takes precedence for missing and unrecognized stereotypes. `strict` input handling cannot reject a custom stereotype accepted by `allow-custom`; `best-effort` cannot continue after a stereotype condition rejected by the selected stereotype policy. Accepted missing stereotypes do not produce a warning solely for absence. Acceptance does not invent stereotype-specific semantics or validate semantic appropriateness.

Under every input policy, duplicate declaration IDs in the defined scope abort conversion, and failures preventing meaningful document processing abort. Existing explicitly nonfatal fallbacks retain their behavior even under `strict`. Intentional omissions do not become unknown-information errors merely because stricter input handling is selected. See [Input contract](input.md).

### Named inverse selection does not disable inverse expressions

For `informed`, a non-null multiplicity includes `*` and `0..*`, even though these add no cardinality restriction. Null or absent multiplicity does not satisfy that condition; a qualifying role can still trigger an inverse. A multilingual role is present when any value contains a non-whitespace character; successful ASCII normalization is not an extra eligibility requirement.

Selecting `none` prevents named inverse generation, while accepted reverse-side cardinalities and property references can still require anonymous inverse expressions. Backward material-chain steps use anonymous inverse expressions even when named inverses exist. The mode must not change source-backed IRIs.

### Material chains have targeted effects

`omit-conflicting-constraints` evaluates actually emitted chains and the property expressions they make non-simple through accepted hierarchies and inverse mappings. It omits affected multiplicity-derived restrictions and property-disjointness axioms, while retaining unrelated constraints. A property used only inside a chain body does not become non-simple solely from that participation.

`preserve-conflicting-constraints` keeps the otherwise applicable cardinality and property-disjointness mappings. Its name does not promise preservation of every OntoUML semantic feature. Either generating mode produces the required nonfatal compatibility notice when a chain is emitted, even if no relevant constraint ultimately conflicts. The `none` mode alone does not produce that notice.

Neither generating mode guarantees OWL 2 DL conformance. See [Reasoner and profile expectations](../concepts/semantics.md#reasoner-and-profile-expectations) for the conceptual boundary; the detailed explanation belongs to the planned chain-mapping page.

### Presentation and persistence do not change transformation outcomes

Changing console thresholds must not change diagnostic production/severity, recovery, abortion, transformation outcome, ontology-output eligibility, or exit-code selection. Requesting or accessing diagnostic exports must not change transformation diagnostics, recovery, abortion, transformation outcome, or ontology-output eligibility. On the CLI, failure to create or write a requested diagnostics file returns `4`, taking precedence over transformation codes `0`, `1`, and `3` and delivery-failure codes `5` and `6`. JSON mirrors diagnostics actually produced; it does not generate reports of every known semantic loss. A quiet console therefore does not establish full preservation.

Transformation outcome remains distinct from delivery failure. The detailed CLI exit-code table and precedence belong to the planned CLI guide; the available [Output contract](output.md#delivery-boundaries) summarizes artifact eligibility.

### Controls that are not established

No independent ontology-IRI, format-selection, prefix-selection, sorting/canonicalization, qualified-relation-cardinality, or reverse-cardinality-omission control is established. The redundant local `owl:allValuesFrom` option has been removed. No generic mereology-specific control is specified. These boundaries must not be filled with guessed switches or Python parameters.

---

Governing rules: §15; DK-GEN-09–10; DK-IRI-01–02, 09–10; DK-LBL-01–02; DK-INV-01, 04–05, 10; DK-REL-07; DK-ATT-04; DK-DIAG-04–07; baseline consolidated: **2026-10-21**; repository commit: `c2262aff7ce41a874875e354c9842fd97c8c879b`; source: [`documentation/specification/2026-10-21 - specification handoff.md`](https://github.com/pedropaulofb/ontouml-directkg/blob/c2262aff7ce41a874875e354c9842fd97c8c879b/documentation/specification/2026-10-21%20-%20specification%20handoff.md).
