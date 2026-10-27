# Metadata and provenance

This guide explains **accepted intended contracts**. Descriptive metadata describes the ontology; transformation provenance describes its production. No converter execution, captured provenance record, or working metadata-file invocation is asserted here.

## Descriptive metadata

Source `Project.name` supplies the generated ontology's `rdfs:label`, and supported `Project.description` supplies its `rdfs:comment`, with the [source-text language rules](../reference/text.md#language-resolution). Absent/null/empty source text produces neither a fallback annotation nor a diagnostic solely for that condition. Project naming does not select ontology identity, mint a project resource, or add a project-ID annotation.

External enrichment requires the explicitly supplied `--metadata-file PATH` identifying a file named **`metadata.yaml`**. There is no automatic discovery. JSON, RDF, Ion, and other formats are not accepted through this mechanism. Python must expose an equivalent metadata-file control without a prescribed parameter name.

### External-field whitelist

Only these seven fields are ingested from the supported OntoUML/UFO Catalog metadata structure:

| Field | Ontology predicate | Accepted nonempty shape |
| --- | --- | --- |
| `title` | `dcterms:title` | One string |
| `acronym` | `mod:acronym` | One untagged string |
| `contributor` | `dcterms:contributor` | List of contributor IRIs |
| `keyword` | `dcat:keyword` | List of strings |
| `source` | `dcterms:source` | List of source-resource IRIs |
| `landingPage` | `dcat:landingPage` | One IRI or a list of IRIs |
| `license` | `dcterms:license` | One license-document IRI |

`mod:acronym` denotes `https://w3id.org/mod#acronym`. All these statements describe the generated **ontology resource**. Optional absent/null/empty values add no annotation. Emit separate statements for list members, preserving supplied text and IRIs rather than concatenating values, inventing contributor identities, or looking up names externally.

Ignore all other fields, including `issued`, `modified`, `theme`, `editorialNote`, `ontologyType`, `language`, `designedForTask`, `context`, and `representationStyle`. They supply neither annotations, language information, nor transformation settings. Validate the supported subset rather than requiring unrelated Catalog fields. The YAML document must nevertheless parse as a top-level mapping.

External YAML text is **untagged**: neither `Project.languages` nor the user language override propagates to it. An external title supplements the source project label through `dcterms:title`; it never replaces that label or supplies another `rdfs:label`, even when the project name is absent.

The following valid YAML is a **specification illustration**, not a file processed by DirectKG:

```yaml
title: Clinical Study Ontology
keyword:
  - clinical study
  - research
source:
  - https://example.org/study-source
language: pt
```

Assume a supported source project named `Clinical Study`, explicit language override `en`, entity base `https://example.org/study#`, and provenance mode `none`. The following selected metadata assertions illustrate the distinction. The external `language` value is ignored. This parseable excerpt omits the ontology declaration/import and domain axioms; it is not a complete conversion result or executed output.

```turtle
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix dcat: <http://www.w3.org/ns/dcat#> .

<https://example.org/study>
    rdfs:label "Clinical Study"@en ;
    dcterms:title "Clinical Study Ontology" ;
    dcat:keyword "clinical study", "research" ;
    dcterms:source <https://example.org/study-source> .
```

## Provenance modes

The [control catalog](../reference/controls.md#established-controls) owns selectable controls and defaults. Provenance defaults to `embedded`:

| Mode | Transformation provenance | Descriptive metadata |
| --- | --- | --- |
| `none` | Not generated | Retained in ontology |
| `embedded` | Included in ontology graph | Retained in ontology |
| `sidecar` | Written separately as Turtle | Retained in ontology |

Ontology declaration, required imports, and domain axioms are semantic output, not transformation provenance. Disabling provenance does not disable them or descriptive source/external metadata. Under `none`, do not perform provenance-only operations whose failure could prevent an otherwise valid conversion.

### Required provenance representation

When enabled, provenance records the following without selecting resource-IRI templates, Python objects, or a configuration-key schema:

| Information | Required representation |
| --- | --- |
| Each execution | A distinct `prov:Activity` |
| DirectKG software | A resource typed `prov:SoftwareAgent` and `schema:SoftwareApplication` |
| Software association | Activity → `prov:wasAssociatedWith` → software resource |
| DirectKG version | `schema:softwareVersion` on software resource |
| Completion timestamp | Activity's `prov:endedAtTime`, in UTC |
| Generated ontology | Ontology → `prov:wasGeneratedBy` → activity |
| Source JSON artifact | A `prov:Entity` used by the activity through `prov:used` |
| Effective configuration | Separate `prov:Entity`, also linked through `prov:used` |
| Supplied metadata file | Separate input entity through `prov:used`, without claiming successful use of a file never read or parsed |
| File content digest | SPDX checksum structure using SHA-256 |
| Concrete output file, sidecar mode only | Separate entity linked to ontology by `dcterms:isFormatOf`, with filename, serialization format, checksum, and generation relationship |

The configuration entity contains a **deterministically serialized YAML string** under `prov:value`, identified by `dcterms:format`. Record effective transformation settings, including defaults, subject to the embedded-output-file exclusion below. Configuration keys inside this literal are data, not RDF predicates.

Descriptive citations through `dcterms:source` differ from execution inputs actually processed through `prov:used`. Do not treat every cited source as an execution input.

### Optional automatic enrichment

The seven-field whitelist limits only external-file ingestion. Additional metadata/provenance may be generated when reliably determined from source, ontology, execution, or output context and meaningfully useful. It remains subject to the selected mode, output-file boundary, and explicit omission rules. It cannot indirectly ingest ignored fields or add RDF origin markers solely to distinguish generated relation labels.

Use appropriate **established external vocabulary terms**, without DirectKG-specific metadata/provenance predicates. Where no appropriate standard representation has been identified, the concept remains unsupported pending such identification or an accepted decision. Unavailable optional enrichment alone does not require abortion.

## Artifacts and digests

Sidecars use Turtle beside a **concrete ontology output path**, named `<output-stem>.provenance.ttl`: for example, `hospital.ttl` → `hospital.provenance.ttl`. Do not invent a name for stdout or an in-memory graph. Python must also expose separate provenance as a graph with explicit serialization, without a prescribed graph class or method.

Concrete output-file information—filename, serialization format, and content digest—belongs **only in sidecar mode**. Embedded provenance describes the ontology and transformation without representing its containing serialization as an external artifact describing itself. The embedded configuration record also excludes that concrete output-file information.

For file inputs, SHA-256 covers the **exact bytes read**. A sidecar's ontology-file digest covers the **final serialized ontology bytes**. Graph-equivalent files can have different byte digests because prefixes, statement order, blank-node labels, and whitespace need not be identical. The [serialization contract](../reference/output.md#graph-and-text-stability) preserves graph connections and ordered RDF lists.

Do not compute a self-referential digest of embedded provenance or claim an original-file byte digest for an in-memory input when the bytes are unavailable. Canonicalized in-memory digesting depends on a separately specified canonicalization rule. These accepted exclusions are not provenance-construction failures.

## Failure boundaries

### Metadata input

An explicitly requested file that is missing, unreadable, malformed YAML, or not a top-level mapping produces ERROR. It is not absence of optional enrichment. `strict` and `tolerant` abort without ontology delivery. `best-effort` omits **all external metadata**, retains error severity, and continues other transformable input; absent another abort condition, the outcome is `completed-with-errors`.

Do not salvage fragments of malformed YAML. Once a valid mapping exists, invalid selected values follow the input-policy pattern: errors under `strict`/`tolerant`, with abortion under their structural-error rules; under `best-effort`, omit affected values and report errors. Ignored fields generate no field-validation diagnostics, although YAML syntax still must parse.

Best-effort metadata omission preserves source-project metadata, required ontology structure, domain axioms, and independently available provenance. Report the file failure and whether conversion aborted or external metadata was omitted through existing diagnostic mechanisms. Provenance must not claim successful use of metadata never read/parsed; effective configuration may record that it was requested.

### Required construction versus later delivery

| Failure stage | Required behavior |
| --- | --- |
| Required provenance cannot be constructed under `embedded` or `sidecar` | ERROR and `aborted` before ontology delivery under every input policy, including `best-effort`; retain diagnostic access and attempt requested CLI JSON export |
| Constructed sidecar cannot be serialized, created, or written after ontology delivery | ERROR and failed sidecar delivery; retain successfully written ontology and established transformation outcome; expose failure programmatically and include it in requested diagnostics |
| Requested ontology file cannot be created/written after successful ontology serialization and required-provenance construction | Follow the separate ontology-delivery policy; no new sidecar for that failed ontology file |
| Requested diagnostics file cannot be created/written | Follow the separate report-delivery policy without changing transformation outcome or ontology-output eligibility |

Do not replace a failed required provenance record with an incomplete one or silently downgrade to another mode. After sidecar delivery failure, do not switch to embedded/none, modify the ontology graph to compensate, or delete the successfully written ontology solely because its sidecar failed. Report incomplete delivery explicitly, independently of input policy.

A partial sidecar must not be presented as valid. If an older sidecar remains, report that it was not updated for this execution. Requested CLI diagnostics export is attempted after recording sidecar failure. Python explicitly exposes failed delivery rather than fully successful delivery.

Required-construction abortion uses CLI `3`, overridden by diagnostics-file failure `4`. Sidecar serialization/create/write failure uses `5`, with `4` and applicable ontology-file failure `6` taking precedence. The complete table, exact scopes, and retained-file rules belong to [Exit codes and delivery failures](cli.md#exit-codes-and-delivery-failures). The [diagnostics reference](../reference/diagnostics.md#outcomes-and-output-eligibility) owns transformation outcomes; delivery failure does not relabel a completed transformation as aborted.

---

Governing rules: DK-GEN-08–11; DK-LBL-02; DK-DIAG-04–05; §15; baseline consolidated: **2026-10-21**; repository commit: `a36322fa87c006cece63aaadd2aa5ccd513f6087`; source: [`documentation/specification/2026-10-21 - specification handoff.md`](https://github.com/pedropaulofb/ontouml-directkg/blob/a36322fa87c006cece63aaadd2aa5ccd513f6087/documentation/specification/2026-10-21%20-%20specification%20handoff.md).
