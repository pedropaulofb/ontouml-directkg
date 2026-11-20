# Output contract

This reference explains **accepted intended output**. It does not claim that a working converter, captured conversion result, or deployed API is available.

## Artifacts and serialization

| Artifact | Format | Availability under the accepted contract |
| --- | --- | --- |
| Ontology serialization | RDF 1.1 Turtle | The sole officially supported ontology serialization for CLI output and Python serialization capabilities, subject to transformation eligibility and successful delivery. |
| Separate transformation provenance | Turtle | Sidecar mode, with a concrete output-file path; separate provenance is also available programmatically as a graph under the specified Python contract. |
| Persistent diagnostics | JSON | Explicitly requested CLI diagnostics file, or a separate explicitly invoked Python export operation. Python conversion does not write it automatically. |

A conversion eligible for ontology delivery produces the RDF/OWL graph defined by its applicable mappings. The CLI and Python use RDF 1.1 Turtle when serializing that graph.

The contract establishes no format-selection control. Separate provenance beside `hospital.ttl` uses `hospital.provenance.ttl`; no automatic sidecar filename is invented for stdout or an in-memory graph. A new sidecar must not be delivered for an ontology file whose delivery failed.

## Ontology header

### Identity from the entity base

The ontology IRI is derived from the effective entity base: remove a final `#`; otherwise preserve the base, including a final `/`. There is no separate ontology-IRI control.

| Supplied base | Effective entity base | Ontology IRI |
| --- | --- | --- |
| `https://example.org/model` | `https://example.org/model#` | `https://example.org/model` |
| `https://example.org/model/` | `https://example.org/model/` | `https://example.org/model/` |

These are namespace illustrations, not published ontology addresses. The [base control](controls.md#established-controls) records the placeholder default. Invalid supplied bases are rejected before conversion; delimiter handling does not authorize trimming or repairing them. See [Identifiers and naming](identifiers.md) for identity construction and source-ID annotations.

### Optional ontology version IRI

The optional `--ontology-version-iri IRI` control, with an equivalent optional Python control, adds `owl:versionIRI` on the generated ontology resource when supplied and valid. Its subject remains the ontology IRI derived above; its object is the supplied version IRI. When the control is absent, emit no `owl:versionIRI` statement and no diagnostic solely for its absence.

Validate the supplied value as an absolute IRI permitted for OWL ontology version identifiers. Invalid values follow [configuration rejection before conversion](diagnostics.md#policies-and-precedence), independently of the selected input policy.

This **specification illustration**, not converter output or publication, assumes entity base `https://example.org/model#` and caller-supplied version IRI `https://example.org/model/versions/1`. It shows only the added header statement:

```turtle
@prefix owl: <http://www.w3.org/2002/07/owl#> .

<https://example.org/model>
    owl:versionIRI <https://example.org/model/versions/1> .
```

The caller assigns version identifiers. Do not derive one from a filename, execution timestamp, checksum, or DirectKG software version. This control adds no field to the [external metadata whitelist](../guides/metadata-and-provenance.md#external-field-whitelist).

Supplying or changing only the version IRI retains the ontology IRI derivation, generated entity IRIs and selected DKGM vocabulary mode. The version statement is an ontology-header contribution independent of provenance mode.

DK-GEN-10 remains unchanged: when provenance is enabled, the [effective configuration record](../guides/metadata-and-provenance.md#required-provenance-representation) must reflect the ontology version IRI setting. In sidecar mode, the [output checksum](../guides/metadata-and-provenance.md#artifacts-and-digests) covers the final serialized ontology bytes, including the version IRI statement when present. This introduces no special provenance exclusion or requirement for provenance values to remain invariant.

Emitting a version IRI neither publishes the ontology nor verifies across executions that repeated use identifies identical ontology content. No cross-run version registry is introduced. See [Controls](controls.md#interface-parity) for the specified control's implementation status.

### Vocabulary delivery and descriptive text { #required-import-and-descriptive-text }

The default `import` mode adds `owl:imports <https://w3id.org/directkg/vocab/dkgm>` for the complete vocabulary, even when no covered mereological relation is mapped. `embed` supplies the fixed core locally. `none` supplies only declarations for generic properties targeted by emitted bridges. Both `embed` and `none` omit the DKGM import. See [Vocabulary delivery modes](../mapping/mereology.md#vocabulary-delivery-modes) for the full contract and its implementation status.

!!! warning "Imported axioms can change without changes to the output file"

    In `import` mode, the target is the stable URI representing the vocabulary's latest version, without the property's `#` namespace suffix. Resolving the same import later can bring in changed imported axioms without changing the generated ontology file. The [import example](../mapping/mereology.md#canonical-vocabulary-and-import) uses the stable IRI.

A nonempty source `Project.name` supplies an ontology `rdfs:label`; a nonempty supported `Project.description` supplies an ontology `rdfs:comment`, following source-language rules. Their absence does not generate fallback text or a diagnostic solely for that condition. They do not select ontology identity. An explicitly supplied external title supplements the project name using its separate metadata predicate rather than replacing the source label.

Descriptive metadata remains in the ontology independently of provenance mode. The ontology declaration, selected vocabulary output and domain axioms remain part of the ontology when provenance is `none`.

## Graph and text stability

For unchanged supported input and identical configuration, identity generation and collision resolution obey their governing deterministic rules. This is distinct from byte-identical output.

Turtle serialization preserves the generated graph, including IRIs, literal values, graph connections, and order encoded in RDF lists. Consistent blank-node relabeling is permitted. Statement order, whitespace layout, serialized blank-node labels, exact prefix labels, and declaration order are not guaranteed. Conventional prefixes, including `:` for the effective entity base, are recommended rather than fixed identifiers.

Do not compare RDF examples or conversion results solely as text. Graph comparison can allow blank-node renaming while preserving connections and RDF-list order. This contract requires neither a canonicalization algorithm nor sorting, prefix-selection, or canonicalization controls.

Execution provenance can differ between conversions, including the distinct execution activity and completion timestamp. Its effective-configuration YAML has a separate deterministic-serialization requirement. Source JSON checksums use SHA-256 over the exact bytes read from the [required source file](input.md#source-file-input), not a serialization of parsed data. A sidecar's ontology-file digest still covers the final serialized ontology bytes. Self-referential digests of embedded provenance remain prohibited. See [Artifacts and digests](../guides/metadata-and-provenance.md#artifacts-and-digests) for checksum scope and accepted exclusions.

## OWL profile conformance

DirectKG gives no general guarantee of OWL 2 DL, EL, QL or RL conformance. Output outside OWL 2 DL establishes neither conformance to another profile nor a fallback reasoning regime.

Assess conformance for the particular ontology and its **axiom closure**, which includes its own axioms and the axioms of resolved imports. The selected DKGM mode determines which vocabulary axioms enter that assessment. [Vocabulary delivery modes](../mapping/mereology.md#vocabulary-delivery-modes)

| DKGM mode | Axioms to include in the assessment |
| --- | --- |
| `import` | Include the DKGM vocabulary actually resolved through the import. |
| `embed` | Include the fixed local DKGM core as part of the generated graph. |
| `none` | Include separately supplied axioms only when assessing the consumer's combined ontology. |

The per-axiom compatibility gate, material-chain constraint treatment and compatibility notices apply under their existing conditions. The profile contract adds no runtime validation or conversion outcome. The outcome follows the transformation and recovery rules. [Per-axiom compatibility](../mapping/relations.md#compatibility-of-each-addition) · [Material-chain compatibility and notices](../mapping/derivations-and-chains.md#owl-compatibility) · [Transformation outcomes](diagnostics.md#outcomes-and-output-eligibility)

### OWL 2 DL compatibility guidance

DirectKG can produce OWL 2 DL-conformant ontologies from suitable source models and configurations. The settings below reduce known incompatibilities. Assess the ontology and its axiom closure for each input, including when the outcome is `completed`. A dedicated OWL 2 DL mode and additional profile-specific configuration constraints are outside first-release scope.

These recommendations apply to both interfaces. The Python names below follow the inspected conversion signature. Equivalent controls have the same choices, defaults, and effects. [Interface parity](controls.md#interface-parity) · [Conversion API](api/index.md#ontouml_directkg.convert)

- **Material chains.** Start with the default `--material-property-chains none` (Python `material_property_chains="none"`). This disables material–relator and material–mode chains and retains independently applicable cardinality and property-disjointness axioms. The `omit-conflicting-constraints` mode omits the specified multiplicity restrictions and relation-set disjointness axioms on property expressions made non-simple by emitted material chains, including effects propagated through the hierarchy and inverses. The `preserve-conflicting-constraints` mode keeps otherwise applicable constraints, including ones that conflict with a chain. Either generating mode can still yield output outside OWL 2 DL. [Targeted treatment and notices](../mapping/derivations-and-chains.md#owl-compatibility)
- **DKGM delivery.** Where mode selection is available, use `--dkgm-vocabulary none` (Python `dkgm_vocabulary="none"`) if you can omit the generic mereological chains. It omits the import and generic chains, preserves source-specific bridges and primary-property asymmetry, and declares the generic targets of emitted bridges locally. Supply chain axioms or equivalent rules to your reasoner if you need the generic entailments. The `embed` mode retains the fixed core locally, with non-simple chain conclusions. A bridge alone does not make its source-specific subproperty non-simple. In default `import` mode, assess the vocabulary actually resolved. DKGM delivery and material chains have independent controls. [Delivery modes, conditional warning and implementation status](../mapping/mereology.md#vocabulary-delivery-modes)
- **Domain namespace.** Use `--base-iri` (Python `base_iri`) with a dedicated namespace such as `https://example.org/model#` to keep generated IRIs separate from reserved OWL terms and terms in DKGM and other vocabularies used by the ontology. [Base and ontology IRIs](identifiers.md#base-and-ontology-iris)
- **Auxiliary RDF.** Use `--omit-identifiers` (Python `omit_identifiers=True`) to suppress the optional source-ID annotations under the `name` strategy. Set `--provenance` (Python `provenance`) to `none` to omit transformation provenance or `sidecar` to keep provenance out of the ontology graph. Automatic sidecar delivery requires a concrete ontology output path. Leave `--metadata-file` (Python `metadata_file`) unset to skip external descriptive metadata. Source-authored descriptive annotations follow their existing rules. [Source identifiers](identifiers.md#source-identifiers) · [Provenance modes](../guides/metadata-and-provenance.md#provenance-modes)

### Known incompatibilities

These issues can affect OWL 2 DL conformance even with material chains disabled.

- **Mixed property kinds.** DirectKG **rejects** mixed `owl:ObjectProperty` and `owl:DatatypeProperty` inclusions under `DK-PROP-03` (affecting both classifier-owned attributes and relations), mixed object/data relation generalizations under `DK-REL-14` and `DK-REL-20`, and cross-kind disjointness pairs under `DK-REL-15` as structural **ERROR**s, omitting incompatible axioms under `best-effort` rather than emitting subproperty or disjointness axioms across OWL object and datatype properties. For example, an attribute targeting a reified custom datatype cannot subset or redefine an `int` attribute. This targeted property-kind check removes that cross-kind incompatibility without introducing general semantic validation or guaranteeing overall OWL 2 DL conformance. *(Implementation status at [`283f9b01361830c2dfb1e96b08111e1f8f849b31`](https://github.com/pedropaulofb/ontouml-directkg/blob/283f9b01361830c2dfb1e96b08111e1f8f849b31/src/ontouml_directkg/properties.py#L198-L237): `emit_property_references` in `src/ontouml_directkg/properties.py` does not yet reject mixed-kind attribute inclusions.)* [Subsetting and redefinition](../mapping/property-features.md#subsetting) · [Generalization and disjointness](../mapping/relations.md#generalization-and-disjointness) · [OWL 2 Mapping to RDF Graphs §3.2.5](https://www.w3.org/TR/2012/REC-owl2-mapping-to-rdf-20121211/#Parsing_of_Axioms)
- **IRIs, declarations, and auxiliary RDF.** An IRI valid in RDF can be a reserved OWL term used in a prohibited position. A collision with a vocabulary term can assign incompatible property types to one IRI. Non-built-in annotation properties such as `dcterms:identifier` require an appropriate declaration in the axiom closure. External metadata and embedded provenance can contribute terms and statements whose declarations and OWL encoding also affect conformance. [OWL 2 Structural Specification §§2.4, 3.1, and 5.8.1](https://www.w3.org/TR/2012/REC-owl2-syntax-20121211/)
- **Property simplicity and hierarchy regularity.** OWL 2 DL requires simple object properties for object cardinality restrictions, asymmetry, irreflexivity, and object-property disjointness. Chain conclusions are non-simple, and superproperty and inverse links can propagate that status. The full property hierarchy with its chains must also be regular. Assess these conditions across the applicable axiom closure, including resolved imports and, for a consumer's combined ontology, separately supplied axioms. The conversion-time gate covers the five specified additions. [OWL 2 global restrictions](https://www.w3.org/TR/2012/REC-owl2-syntax-20121211/#Global_Restrictions_on_Axioms_in_OWL_2_DL) · [Per-axiom compatibility](../mapping/relations.md#compatibility-of-each-addition)

## Delivery boundaries

Transformation outcome and artifact delivery are separate. `completed` and `completed-with-errors` are eligible for ontology delivery, including permitted partial output; `aborted` prohibits delivery of the accumulated ontology. A [reportable unexpected internal failure during transformation](diagnostics.md#unexpected-internal-failures-during-transformation) aborts and yields neither an ontology file nor a provenance sidecar. Produced diagnostics remain accessible after accepted aborts, and requested CLI diagnostics export is still attempted. Invalid invocation and rejection of a supplied base or ontology version IRI happen before conversion and do not create a transformation outcome; either IRI rejection produces no conversion-diagnostics report.

Failure to serialize or encode Turtle for a requested ontology file after transformation leaves any existing ontology and provenance sidecar untouched. Neither new artifact is delivered. Ontology-file creation and write failures after successful serialization and required-provenance construction also prevent a new sidecar. Both categories preserve the established transformation outcome, generated graph, and requested provenance mode. A failed sidecar delivery leaves successfully written ontology output available. Failed diagnostics-file delivery likewise does not alter transformation outcome or ontology-output eligibility. Delivery failures must be reported explicitly; a partial file must not be presented as a valid ontology or sidecar, and an older destination left in place must be identified as not updated.

Required-provenance construction failure is different: with provenance enabled, it aborts before ontology delivery under every input policy. It must not silently change the requested provenance mode. Other runtime and ontology-output failures outside the defined cases remain unresolved.

See [CLI exit codes and delivery failures](../guides/cli.md#exit-codes-and-delivery-failures), [Metadata and provenance failure boundaries](../guides/metadata-and-provenance.md#failure-boundaries), and [Diagnostics and recovery](diagnostics.md) for the detailed contracts. Their accepted controls are already listed in [Controls](controls.md).

---

Governing rules: §3.3; DK-GEN-03–04, 08–11; DK-IRI-01, 09; DK-LBL-02; DK-PROP-03; DK-DIAG-04–05, 07; DK-REL-01, 07, 14–15, 20; §15; DK-CONF-01–03; baseline consolidated: **2026-11-20**; repository commit: `283f9b01361830c2dfb1e96b08111e1f8f849b31`; source: [`documentation/specification/transformation-specification.md`](https://github.com/pedropaulofb/ontouml-directkg/blob/283f9b01361830c2dfb1e96b08111e1f8f849b31/documentation/specification/transformation-specification.md).

Accepted update: **RD-02 — Datatype-valued ordinary binary relations (`Alternative B + Q1–Q7 + Conflicts A–I`) & global `DK-PROP-03` mixed-kind rejection** (project-owner formalization included in the cited consolidation).

Accepted update: **RD-05 — Optional caller-supplied ontology version IRI** (project-owner formalization, Option B, included in the cited consolidation).

Accepted update: **RD-05 — File-only transformation input and exact-byte source checksums** (project-owner formalization included in the cited consolidation).
