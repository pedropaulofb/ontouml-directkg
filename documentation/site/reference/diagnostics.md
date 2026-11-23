# Diagnostics and recovery

This reference explains **accepted diagnostic behavior**, with bounded implementation evidence identified below. Source rule IDs are traceability references, not runtime diagnostic codes. The specification fixes the minimum shared JSON report structure; Python result/exception mechanisms remain unspecified.

## Policies and precedence

Input handling and stereotype acceptance are separate controls. Their canonical values/defaults belong to [Controls](controls.md#established-controls): input policy defaults to `tolerant`; stereotype policy defaults to `allow-custom`.

### Input policy

| Situation | `strict` | `tolerant` | `best-effort` |
| --- | --- | --- | --- |
| Unrecognized non-stereotype input information | ERROR and abort | WARNING; continue recognized information | WARNING; continue recognized information |
| Recognized but untransformable values or unresolved references | ERROR and abort | ERROR and abort | ERROR; omit affected output and continue where accepted recovery permits |
| Failure preventing meaningful document processing | ERROR and abort | ERROR and abort | ERROR and abort |
| Duplicate declaration ID within the defined scope | ERROR and abort | ERROR and abort | ERROR and abort |

Best-effort recovery **retains ERROR severity**. It may deliver permitted partial output only if conversion completes; it neither invents missing information nor permits syntactically invalid RDF. `strict` does not automatically turn an explicitly nonfatal warning/fallback into an error. Recovery is bounded to accepted rules, not an arbitrary repair strategy (DK-DIAG-05).

Duplicate-ID scope covers separate declarations participating in accepted mappings or required reference resolution. Compare decoded ID strings exactly, without trimming, normalization, or case folding. Identical declaration contents do not excuse duplicates: identify the ID, available competing-declaration locations, and abort. Do not select, merge, or replace declarations. Repeated reference objects identifying one declaration are not duplicates; the rule introduces no validation of deliberately omitted diagram/custom-metadata content. See [Structural requirements](input.md#structural-requirements).

### Stereotype policy takes precedence

| Source condition | `require-known` | `allow-missing` | `allow-custom` |
| --- | --- | --- | --- |
| Missing class/relation stereotype | ERROR and abort | Accept | Accept |
| Missing attribute/end stereotype | Accept | Accept | Accept |
| Supplied unrecognized stereotype on class/relation/attribute/end | ERROR and abort | ERROR and abort | Accept with WARNING |

An accepted missing stereotype adds no warning solely for absence. `strict` input policy cannot reject a custom stereotype accepted by `allow-custom`; `best-effort` cannot continue past a stereotype rejection. Accepted missing/custom stereotypes retain ordinary mappings wherever prerequisites hold, without invented stereotype-specific semantics. A known class with an unknown stereotype differs from an unknown element type.

Unknown does not mean ontologically wrong. DirectKG does not validate classifier orders, stereotype appropriateness, higher-order conflicts, UML semantic compatibility, or output consistency. A recognized but explicitly unresolved mapping remains unresolved; it cannot be relabelled unknown to bypass that boundary (DK-DIAG-02, 06).

Rejection of a supplied base or [ontology version IRI](output.md#optional-ontology-version-iri) is **configuration rejection before conversion**, not input-policy recovery. It produces no ontology, outcome, or conversion-diagnostics report under any policy, even when report persistence was requested. Python signals it programmatically; CLI code `2` is described in [Invocation](../guides/cli.md#invocation). Absence of the optional version IRI alone adds no diagnostic.

## Outcomes and output eligibility

Expose exactly one outcome for every conversion that runs, through Python and any exported shared diagnostic report:

| Outcome | Condition | Ontology-output eligibility |
| --- | --- | --- |
| `completed` | Processing completes with no transformation errors; INFO/WARNING may exist | Eligible for delivery |
| `completed-with-errors` | Processing completes despite transformation errors under accepted recovery | Eligible, including permitted partial output |
| `aborted` | Processing terminates under an accepted abort rule | No ontology delivery through CLI or Python |

Abortion takes precedence over earlier diagnostic counts/severities. ERRORs alone do not prove abortion, and INFO/WARNING alone do not create `completed-with-errors`. Exposing the outcome adds no diagnostic event. Invalid invocation has no conversion outcome because conversion never started.

Do not deliver the graph accumulated during an aborted conversion, even when useful fragments exist. Complete diagnostic access remains available, and requested CLI JSON export is still attempted. Duplicate IDs require this abort behavior even under `best-effort`.

`completed` does not guarantee losslessness, semantic consistency, or an OWL profile. Required-provenance construction failure aborts before delivery under every policy; later ontology-file, sidecar, or diagnostics-file delivery failures **do not change an established transformation outcome**. Delivery must be reported separately. [CLI exit codes](../guides/cli.md#exit-codes-and-delivery-failures) distinguish codes `0`–`6`; code `1` does not suppress eligible output.

### Unexpected internal failures during transformation

If an unexpected internal error stops transformation after conversion has started and DirectKG can still report it, the outcome is `aborted` under every input policy, including `best-effort`. Retain all earlier diagnostics and add an ERROR with code `INTERNAL_TRANSFORMATION_FAILURE`, identifying the internal failure, with stage and cause when available. Python exposes the outcome and diagnostics and withholds the accumulated ontology graph. The run delivers neither an ontology file nor a provenance sidecar.

A [collision between distinct escaped source IDs](identifiers.md#collisions-between-distinct-escaped-source-ids) detected during allocation under the same DK-IRI-05 construction follows this contract (DK-IRI-07).

The CLI attempts requested JSON export after recording the ERROR. A successfully written report uses the shared schema and includes `aborted`, the preceding diagnostics, and the internal-failure ERROR. The CLI uses exit `3` when no report was requested or export succeeds. If the requested report cannot be written, both failures appear on the console and the CLI exits `4`. [CLI exit codes and example](../guides/cli.md#exit-codes-and-delivery-failures)

**Implementation status at the reviewed registration.** The conversion handler reports caught unexpected exceptions as `INTERNAL_TRANSFORMATION_FAILURE`. Both allocation guards still raise `NotImplementedError` with a message that calls for an Architect decision. This is based on static source inspection. [Conversion handler](https://github.com/pedropaulofb/ontouml-directkg/blob/a919e64df8555227270d1f8b3b82ac4ef8c4edc5/src/ontouml_directkg/conversion.py#L243-L251) · [Source-resource guard](https://github.com/pedropaulofb/ontouml-directkg/blob/a919e64df8555227270d1f8b3b82ac4ef8c4edc5/src/ontouml_directkg/classifiers.py#L115-L116) · [Inverse guard](https://github.com/pedropaulofb/ontouml-directkg/blob/a919e64df8555227270d1f8b3b82ac4ef8c4edc5/src/ontouml_directkg/inverses.py#L27-L29)

## Diagnostic collection and export

Retain every diagnostic actually produced, preserving severity, meaning, and applicable source information. Python structured access remains available after a policy-driven abort or a reportable unexpected internal failure during transformation, covering all diagnostics produced before termination. Python persistence is a **separate explicitly invoked JSON export operation**, not automatic writing during conversion. CLI persistence is requested by `--diagnostics-file PATH`; without it, the CLI creates no diagnostics file.

Both exports use the same report schema/content contract, exposing the outcome and mirroring produced INFO, compatibility notices, warnings, and errors—including produced reports of omitted, unsupported, invalid, ignored, or approximated source information. Attempt requested CLI export after a policy-driven abort, after recording a reportable unexpected internal failure during transformation, and after recording specified ontology or sidecar delivery failures.

Console thresholds filter only display: `info` shows INFO/WARNING/ERROR, `warning` shows WARNING/ERROR, and `error` shows ERROR. Hidden diagnostics remain in complete structured access and requested exports. Filtering changes neither transformation behavior, collection, recovery, abortion, outcome, output eligibility, nor exit-code selection.

Access/export must not generate additional transformation diagnostics, change their meaning/severity, or alter continuation/output eligibility. A report is not required to invent an event for every documented limitation. Deliberate silence remains silent; absence of an event does not prove complete semantic preservation.

Where applicable, a diagnostic should provide enough structured information to explain and locate the event. The shared JSON report contract below fixes its required fields and representations. Console and JSON may present an event differently while preserving its meaning and content boundary.

A requested diagnostics-file creation/write failure is a separate delivery failure. CLI reports a destination/reason console error and uses code `4` with its defined precedence. Python's explicit export signals failure programmatically while retaining transformation diagnostics. Neither changes the outcome, severities, or ontology eligibility; a report failure must not replace/conceal a prior abort. No unwritable-destination recovery is prescribed. See [Separate exports](../guides/python.md#separate-exports) and [CLI reporting](../guides/cli.md#reporting-and-retained-results).

## Shared JSON report contract

CLI diagnostics files and Python's separate JSON export use the same minimum structure (DK-DIAG-04 / RD-04). A report is a JSON object; each entry in `diagnostics` is a diagnostic object, and each entry in a diagnostic's `sources` array is a source-location object.

| Object | Required member | Type and meaning |
| --- | --- | --- |
| Report | `outcome` | String: `"completed"`, `"completed-with-errors"`, or `"aborted"`, classified under the [outcome rules](#outcomes-and-output-eligibility). |
| Report | `diagnostics` | Array of every produced diagnostic; `[]` when none were produced. Existing consolidation rules still apply. |
| Diagnostic | `severity` | String: `"INFO"`, `"WARNING"`, or `"ERROR"`. |
| Diagnostic | `code` | String identifying the diagnostic condition. |
| Diagnostic | `message` | String explaining the condition for a human reader. |
| Diagnostic | `effect` | String explaining its effect on transformation or delivery. |
| Diagnostic | `sources` | Array of relevant source-location objects; `[]` when none apply. |
| Diagnostic | `generated_iri` | Relevant generated IRI as a string; otherwise JSON `null`. |
| Source location | `path` | String locating the relevant source position or file. |
| Source location | `identifier` | Source identifier as a string when available; otherwise JSON `null`. |
| Source location | `element_type` | Source element type as a string when available; otherwise JSON `null`. |

**Every listed member is required** on its object. Optional context uses the specified empty arrays or nulls; do not omit those members. Existing diagnostic-content rules determine which context must be retained. Empty/null representations do not permit discarding required source information or copying discarded association values into a report; the [instantiation payload boundary](../mapping/instantiation.md#discarded-association-information) remains applicable.

Additional members may be added compatibly while required names, types, and meanings remain preserved. Consumers must ignore unrecognized members. No `schema_version` member is required.

The [stable first-release diagnostic core](#stable-first-release-diagnostic-core) fixes eight identifiers and their condition meanings; all other identifiers remain provisional, and the complete condition-to-code catalogue remains unresolved. This contract adds no stability guarantee for exact message wording, JSON object-member order, or diagnostic-array order. Python object representations, API names, signatures, and result/exception mechanisms remain outside this JSON contract.

The following is a **specification illustration**, not captured converter output. `PLACEHOLDER_BASE` belongs to the stable diagnostic core; the example wording remains illustrative:

```json
{
  "outcome": "completed",
  "diagnostics": [
    {
      "severity": "WARNING",
      "code": "PLACEHOLDER_BASE",
      "message": "A placeholder base IRI was used.",
      "effect": "Generated entities use https://example.org/directkg#.",
      "sources": [],
      "generated_iri": null
    }
  ]
}
```

A completed conversion with no produced diagnostics has the following report shape:

```json
{"outcome": "completed", "diagnostics": []}
```

The structure introduces no diagnostic event, outcome, control, or change to consolidation, console filtering, abortion, output eligibility, or failure policies. Reports retain all produced events, including those hidden by console filtering or produced before an accepted abort. Delivery failures remain separate from transformation outcomes; rejection of a supplied base or ontology version IRI before conversion still produces no conversion report.

**Implementation evidence:** With Python 3.12.14 at [revision `37e68764202a2a18e0c54ac264df1536ff47e28c`](https://github.com/pedropaulofb/ontouml-directkg/tree/37e68764202a2a18e0c54ac264df1536ff47e28c), ten CLI/Python exports passed bounded shape and mirroring checks covering all three outcomes, source context, empty diagnostics, and events hidden by console filtering. This verifies these report cases; it does not establish complete transformation conformance.

## Stable first-release diagnostic core

The following eight diagnostic identifiers and their specified condition meanings are stable for the first release (DK-DIAG-04 / RD-04). They identify diagnostic conditions in the `code` field; they are separate from [CLI exit codes](../guides/cli.md#exit-codes-and-delivery-failures).

| Stable identifier | Condition meaning |
| --- | --- |
| `PLACEHOLDER_BASE` | No base IRI was supplied, so DirectKG used its placeholder base under DK-IRI-01. |
| `UNPROCESSABLE_DOCUMENT` | The source JSON cannot be read or parsed, or an unsupported root makes meaningful document-level processing impossible under the accepted input contract and DK-DIAG-05. |
| `DUPLICATE_SOURCE_ID` | Separate declarations share an ID within the existing [identity/reference scope](input.md#structural-requirements), invoking the fatal duplicate-ID rule. Repeated references to one declaration are excluded. |
| `UNKNOWN_INFORMATION` | Unrecognized non-stereotype input information governed by DK-DIAG-05. Recognized intentional omissions are excluded. |
| `REQUIRED_PROVENANCE` | Required transformation provenance cannot be constructed under DK-GEN-10. |
| `INTERNAL_TRANSFORMATION_FAILURE` | A reportable unexpected internal error stops a transformation that has started, under DK-DIAG-05. |
| `ONTOLOGY_DELIVERY` | Main-ontology serialization, encoding, creation, or writing fails within DK-DIAG-04's settled ontology-file delivery scope. |
| `SIDECAR_DELIVERY` | Requested provenance-sidecar serialization, creation, or writing fails within DK-GEN-10's settled sidecar-delivery scope. |

When a diagnostic is produced for one of these conditions, use the same identifier in CLI JSON exports, structured Python access, Python JSON exports, and any CLI presentation that displays the code. No additional console format is required. `UNKNOWN_INFORMATION` retains its identifier when the selected input policy changes its established severity or continuation behavior; the [policy rules](#policies-and-precedence) still apply.

**All other identifiers remain provisional**, explicitly including `MISSING_CARDINALITY` and `INVALID_CARDINALITY`. They receive no first-release stability guarantee from this decision. Continue producing, exposing, and exporting their diagnostics under existing requirements; provisional status must not suppress required reporting. RD-04 remains partially unresolved: the complete catalogue and its other unresolved failure questions are not settled by this core.

Stability covers only these strings and condition meanings. It adds no diagnostic events, report members, controls, or guarantee of exact message wording, diagnostic count, or ordering. Existing severity, consolidation, content boundaries, console filtering, recovery, outcomes, output eligibility, and exit-status rules remain unchanged. Identifier selection does not establish implementation or testing completion; the [unexpected-failure implementation limitation](#unexpected-internal-failures-during-transformation) remains explicit.

## Diagnostic conditions and intentional silence

The following groups explain when diagnostics occur. Their linked mapping pages own complete transformation algorithms; rule numbers below identify governing source clauses rather than concrete report codes.

### Names, typing, and source text

| Trigger | Diagnostic boundary |
| --- | --- |
| Base omitted | Nonfatal warning for the placeholder namespace; invalid supplied-base configuration instead follows pre-conversion rejection |
| Unnamed/unusable class | Existing type-specific warning and fallback remain; ID mode does not remove that warning |
| Generic source-ID fallback needed in name mode | Nonfatal WARNING identifying element and generated IRI; type-specific rules retain priority |
| Name absent/null/empty/whitespace-only in generic-policy ID mode | Nonfatal INFO identifying the missing-name condition; ordinary designated-ID use alone adds no event |
| Owner/source fallback qualification | No additional event solely for qualification; existing missing-name/input diagnostics remain |
| Structural inverse-role fallback, inverse-domain qualification or numeric allocation | No additional diagnostic solely for the [inverse naming step](../mapping/inverses.md#inverse-naming); existing missing-name, input and other independently applicable diagnostics remain |
| Attribute explicitly typed by recognized unsupported `void` (`stereotype == "datatype"`) | Nonfatal warning identifying available attribute/owner/type information and omitted mapping/range; null typing is separately supported. By contrast, an ordinary `Class → void` relation is a structural **ERROR** under [Datatype-valued relation compatibility](#datatype-valued-relation-and-property-kind-compatibility), and an attribute *owned by* `void` (or a registered primitive `datatype`) is a structural **ERROR** under [Attributes owned without a local OWL class](#attributes-owned-without-a-local-owl-class). |
| Attribute owned by a `Class` without a generated local `owl:Class` (`DK-CLS-01`: registered primitive `datatype` or `void`) | Structural **ERROR** under `DK-ATT-01` before attribute `propertyType` resolution and IRI allocation; `strict` and `tolerant` abort; `best-effort` retains ERROR severity, omits the affected attribute and all dependent output (including attribute-level diagnostics), and applies scoped `DK-PROP-03` suppression. See [Attributes owned without a local OWL class](#attributes-owned-without-a-local-owl-class). |
| Class attribute whose `propertyType` resolves to a `Class` with a generated local `owl:Class` outside `datatype` and `enumeration` | Transform as an ordinary `owl:ObjectProperty` under DK-ATT-01 and DK-GEN-03 without inferring relation stereotypes or stereotype-specific relation mappings; no warning or error solely because the target `Class` is not `datatype` or `enumeration` (nonfatal / non-erroneous under every input policy, including `strict`). Unresolved or invalid `propertyType` references retain structural-error handling under DK-DIAG-05. See [Class-valued attributes](../mapping/attributes-and-datatypes.md#class-valued-attributes) for prohibitions, unchanged boundaries, and current implementation status. |
| Unnamed ordinary relation uses target-role or endpoint fallback, including insufficient [semantic-role evidence](../mapping/relations.md#structural-evidence-for-semantic-naming) | Nonfatal warning under existing naming conditions unless a specific rule replaces it; comparative reaching its deliberately unmapped semantic-name step warns before fallback. No additional naming diagnostic solely for generating a fallback label. |
| Successful ordinary stereotype naming / successful relator naming | Ordinary stereotype success adds no event solely for that success; relator-derived success should produce informational provenance reporting, without a warning merely for success. Independently applicable diagnostics remain. |
| Deliberately unmapped applicable relation stereotype, including `historicalDependence`, `participation`, `creation`, and `termination` | Nonfatal limitation warning under DK-DIAG-01; retain the ordinary mapping where defined. For the latter three, the warning remains nonfatal under every input policy, including `strict`. Naming success, fallback, or disabling stereotype naming does not suppress independently applicable limitation reporting. See [Historical dependence](../mapping/relations.md#historical-dependence) and [Participation, creation, and termination](../mapping/relations.md#participation-creation-and-termination), including the implementation status. |
| Successfully mapped eligible ordinary `participational` or `manifestation` relation | Required residual-semantics WARNING, nonfatal under every input policy, including `strict`. Retain ordinary mappings and applicable guarded `participational` asymmetry. Successful naming and emission or gate-based omission of that asymmetry do not suppress reporting. Existing consolidation and delivery rules apply; this decision prescribes no exact code, wording, or count. See [Participational and manifestation](../mapping/relations.md#participational-and-manifestation) for partial mappings and implementation status. |
| Successfully mapped eligible ordinary `mediation`, `characterization`, or `externalDependence` relation | Required residual-semantics WARNING, nonfatal under every input policy, including `strict`. Retain ordinary mappings, applicable accepted axioms, grounding roles, derivation treatment, and selected eligible material chains. Successful naming, axiom/chain generation, or gate-based axiom omission does not suppress it. Existing consolidation and delivery rules apply; no exact code, wording, or count is selected. See [Dependency relations](../mapping/relations.md#mediation-characterization-and-external-dependence) for the implementation-status note based on source inspection. |
| Successfully mapped eligible ordinary `bringsAbout` or `triggers` relation | Required residual-semantics WARNING, nonfatal under every input policy, including `strict`, independently of naming success. Ordinary mappings and independently required output remain applicable. Existing consolidation and delivery rules apply. Exact codes, wording and counts remain unspecified. See [BringsAbout and triggers](../mapping/relations.md#bringsabout-and-triggers) for the partial translation and the implementation-status note above that section. |
| Usable material semantic name unavailable | Warning, then accepted source–target fallback |
| Explicit, nonempty source-end role name on an otherwise compatible datatype-valued relation | Nonfatal **WARNING under every input policy, including `strict`**, because no inverse datatype property exists (`DK-REL-01` / `DK-INV-05`). Not a structural conflict; omit source-end description without an extra diagnostic (`DK-LBL-02`) and retain primary annotations. |
| Multiple project languages with no local tag or override for a supported value | Nonfatal WARNING and untagged value; may consolidate to avoid unnecessary repetition. A malformed `Project.languages` omitted under `best-effort` supplies no declared project languages and does not trigger `DK-DIAG-19`. |
| Wrong whole-field type (`name` or `description` non-`null`, non-string, non-object) or invalid `languageString` entry on a covered element | Structural **ERROR** (`DK-LBL-02`, `DK-DIAG-05`, `RD-02` Alternative 1A) regardless of `--language` or `--iri-strategy id`; `strict` and `tolerant` abort; `best-effort` omits only the malformed field or invalid entry and retains valid siblings or applies unnamed/fallback rules. See [Malformed textual and language-tag carriers](#malformed-textual-and-language-tag-carriers). |
| Malformed `Project.languages` (non-null non-array, or array with non-string, empty/whitespace string, or invalid lexical tag) | Structural **ERROR** (`DK-LBL-02`, `DK-DIAG-05`, `RD-02` Alternative 2A) regardless of `--language`; `strict` and `tolerant` abort; `best-effort` omits `Project.languages` as a whole without inventing a single-language tag or triggering `DK-DIAG-19`. See [Malformed textual and language-tag carriers](#malformed-textual-and-language-tag-carriers). |

[Identifiers](identifiers.md#unnamed-or-unusably-named-resources) owns fallback prerequisites and exceptions; [Binary relations](../mapping/relations.md#primary-direction-and-naming) owns naming precedence. Detected collisions under the same ID-based construction follow the [internal-failure contract](#unexpected-internal-failures-during-transformation).

Insufficient semantic-role evidence alone is not a structural failure: use the established endpoint naming fallback without omitting the relation or aborting solely for that uncertainty. Structured JSON remains authoritative; this creates no semantic-orientation validation or source-repair branch. Malformed input and unresolved required references retain their existing policies.

Multiple localized naming values alone and multilingual primitive recognition add no new diagnostic/conflict check. An explicit local language or override avoids the project-language ambiguity condition; multiple explicit local languages are not themselves ambiguous. Absent/null/empty supported names on the project or supported descriptions add no diagnostic solely for that absence. Source labels, comments, and generated-label boundaries remain in [Labels, comments, and language](text.md).

#### Malformed textual and language-tag carriers

Under `DK-LBL-02`, `DK-DIAG-05`, `DK-DIAG-19`, `§3.2`, and `§15` (`RD-02`, Alternatives 1A + 2A), DirectKG validates supported textual carriers and explicit language tags using the **simplified lexical language-tag validation rule**:

- **Simplified lexical language-tag rule:** Every nonempty explicit language tag in a supported `languageString` key, a `Project.languages` array element, or `--language` (and its Python equivalent) must satisfy a full-string match against `^[a-zA-Z]+(?:-[a-zA-Z0-9]+)*$` (without trailing newline characters), matching RDF 1.1 Turtle `LANGTAG` lexical syntax. This pattern is explicitly a **simplified lexical validation rule**—it is **not a complete BCP 47 validator** or an IANA language-subtag registry check.
- **Covered `name` and `description` carriers (Alternative 1A):** Validation applies to supported elements whose `name` or `description` participates in transformation: `Project`, `Class` (including `«datatype»` `name` evaluated under `DK-DAT-02`), `Relation`, `Property` (surviving attributes and association ends of surviving relations), and `Literal` (surviving enumeration values). Intentionally omitted text under `DK-GEN-06–07` and `DK-INS-02`—packages, diagrams, `propertyAssignments`, `Generalization`, `GeneralizationSet`, and `«instantiation»` relations—is excluded. Absent fields, explicit `null`, plain JSON strings (with empty strings ignored without error and whitespace-only strings governed by existing naming/missing-name/role-presence rules), and `languageString` objects whose keys are `""` (valid unknown-language key) or valid simplified lexical tags and whose values are JSON strings (with empty string values ignored without error) retain their existing behavior.
- **Wrong whole-field type (`name` or `description`):** Any non-`null`, non-string, non-object value on a covered element emits a structural **ERROR** under `DK-DIAG-05`. Under `strict` and `tolerant`, conversion aborts. Under `best-effort`, DirectKG retains **ERROR** severity, omits only the malformed field, and preserves the owning element under existing unnamed/fallback rules (`DK-GEN-08`, `DK-IRI-04`, `DK-DAT-05`, `DK-REL-02–05`, `DK-INV-05–06`, or omitting the description `rdfs:comment`).
- **Per-entry `languageString` validation:** Within a `languageString` object on a covered element, every `(key, value)` entry is validated independently regardless of whether `--language` (or its Python equivalent) or `--iri-strategy id` is active. Any entry whose value is not a JSON string or whose nonempty key fails `^[a-zA-Z]+(?:-[a-zA-Z0-9]+)*$` (including whitespace-only keys) emits a structural **ERROR**. Under `best-effort`, DirectKG retains **ERROR** severity, omits only the invalid entry or entries, and retains all valid localized siblings for labels and comments (`DK-GEN-08`, `DK-LBL-01–02`), `DK-IRI-10` naming selection (`DK-IRI-03–04`, `DK-REL-02–05`, `DK-INV-05–06/08`), `DK-DAT-02` primitive recognition, and `DK-INV-05` role presence; if zero valid nonempty entries remain, existing unnamed/fallback rules apply. Invalid `languageString` entries must not participate in or pollute `DK-IRI-10` or `DK-DAT-02` selection and must not be masked by `--language`.
- **`Project.languages` carrier (Alternative 2A):** Absent `Project.languages`, explicit `Project.languages: null`, and `Project.languages: []` are accepted as no declared project languages without a diagnostic. Any non-null, non-array value, or an array containing any non-string element, empty or whitespace-only string, or invalid simplified lexical language tag, emits a structural **ERROR** regardless of whether `--language` is supplied. Under `best-effort`, DirectKG retains **ERROR** severity, omits `Project.languages` as a whole—without salvaging individual array elements to invent a single-language tag and without triggering `DK-DIAG-19`—and continues with untagged fallback for otherwise untagged source text unless `--language` is supplied.

| Carrier condition | `strict` / `tolerant` (default) | `best-effort` |
| --- | --- | --- |
| Wrong whole-field type (`name` or `description` non-`null`, non-string, non-object) on a covered element | **ERROR** and `aborted` (exit `3` when diagnostics delivery does not fail) | `completed-with-errors` (exit `1`): retain **ERROR**, omit only the malformed field, and preserve the owning element under existing unnamed/fallback rules |
| Invalid `languageString` entry (non-string value or nonempty key failing `^[a-zA-Z]+(?:-[a-zA-Z0-9]+)*$`) on a covered element | **ERROR** and `aborted` (exit `3` when diagnostics delivery does not fail) | `completed-with-errors` (exit `1`): retain **ERROR**, omit only invalid entry/entries, keep valid localized siblings (for labels/comments, `DK-IRI-10`, `DK-DAT-02`, and `DK-INV-05`), and apply unnamed/fallback rules if zero valid entries remain |
| Malformed `Project.languages` (non-null non-array, or array with non-string, empty/whitespace string, or invalid lexical tag) | **ERROR** and `aborted` (exit `3` when diagnostics delivery does not fail) | `completed-with-errors` (exit `1`): retain **ERROR**, omit `Project.languages` as a whole without inventing a single-language tag or triggering `DK-DIAG-19`, and fall back to untagged literals unless `--language` is supplied |

- **Precedence and scope boundaries:** Established `DUPLICATE_SOURCE_ID` (`§3.4`), `DK-DIAG-06`, `§3.4` declaration-ID validity, and declaration-container checks (`Package.contents`, `Class.properties`, `Class.literals`, `Relation.properties`) retain precedence before textual and language validation. Elements omitted earlier before textual/language processing (such as omitted relations—including `«instantiation»`, malformed/non-binary `Relation.properties`, failed relations, and `«derivation»`/unsupported connectors—omitted attributes, misplaced declarations, or invalid/disallowed container entries) do not trigger textual errors after omission, while surviving and owning elements remain subject to validation. `DK-DIAG-04`'s eight-code first-release core remains unchanged (identifiers remain [provisional](#stable-first-release-diagnostic-core)), no new CLI or Python control is introduced, and unrelated scalar or flag guards remain outside this decision.

**Implementation status.** Stage 3 implementation for these rules has not run yet. At [specification registration revision `ed7a0d1b1cb75f6ac764b8117c5385928f97f86b`](https://github.com/pedropaulofb/ontouml-directkg/blob/ed7a0d1b1cb75f6ac764b8117c5385928f97f86b/src/ontouml_directkg/annotations.py#L17-L51):

- In [`src/ontouml_directkg/annotations.py`](https://github.com/pedropaulofb/ontouml-directkg/blob/ed7a0d1b1cb75f6ac764b8117c5385928f97f86b/src/ontouml_directkg/annotations.py#L17-L51), `source_text` (line 17) still raises `NotImplementedError("Malformed textual-carrier recovery is outside BI-W1")` for non-`None`/non-`str`/non-`dict[str, str]` carriers; `TextAnnotations.__init__` (line 26) still raises `NotImplementedError("Malformed project-language recovery is outside BI-W1")` for non-list `Project.languages` (including explicit `null`) or non-string/empty elements without checking whitespace-only or lexical tag syntax; and `TextAnnotations.add` (line 51) still raises `NotImplementedError("Malformed source-language-tag recovery is outside BI-W1")` when `rdflib.Literal` rejects a tag, while skipping empty-string values and bypassing local `languageString` keys whenever `--language` (`self.override`) is supplied.
- In [`src/ontouml_directkg/identity.py`](https://github.com/pedropaulofb/ontouml-directkg/blob/ed7a0d1b1cb75f6ac764b8117c5385928f97f86b/src/ontouml_directkg/identity.py#L135-L150), `naming_text` (line 135) and `missing_name` (line 150) still raise `NotImplementedError("Malformed textual-carrier recovery is outside BI-W1")` / `NotImplementedError("Malformed name-carrier recovery is outside BI-W1")` for malformed carriers, and `naming_text` does not yet filter out invalid `languageString` keys before `DK-IRI-10` selection (and `DK-DAT-02` `datatype_key`).
- In [`src/ontouml_directkg/conversion.py`](https://github.com/pedropaulofb/ontouml-directkg/blob/ed7a0d1b1cb75f6ac764b8117c5385928f97f86b/src/ontouml_directkg/conversion.py#L121-L127), `--language` / `language` validation (lines 121–127) still uses `rdflib.Literal("", lang=language)` rather than an explicit full-string match against `^[a-zA-Z]+(?:-[a-zA-Z0-9]+)*$` without trailing newline characters, and `NotImplementedError` exceptions raised during transformation are caught as `INTERNAL_TRANSFORMATION_FAILURE` (lines 252–256), aborting under every policy including `best-effort`. The rules above describe accepted intended behavior.

### Structural failures, sets, and connectors

For directional relation generation (`DK-DIAG-03`), the source must resolve to a `Class` with a generated local `owl:Class`, and the target must resolve to a `Class` that either has a generated local `owl:Class` (`owl:ObjectProperty`) or is a supported primitive `datatype` (`owl:DatatypeProperty`, subject to `DK-REL-01` compatibility checks). Missing/invalid end IDs, null/unresolved end types, a source `Class` lacking a generated local `owl:Class` (`Primitive`, `void`, or omitted class), or a target `void` invoke established structural **ERROR** diagnostics and **neither primary nor inverse property is generated in any policy**. A valid end ID does not make a null type resolvable. Accepted `best-effort` continuation concerns other transformable information, not invention of that relation or reversal of its direction. Non-binary and absent, `null`, or malformed `Relation.properties` containers follow the [relation-container rule](#non-binary-and-malformed-relation-properties-containers) below.

An explicitly empty `generalizations` array is an ERROR under every flag combination: `strict`/`tolerant` abort; `best-effort` omits the set contribution and continues elsewhere. Do not infer a general, invent members, or assert an empty class extension. This rule applies to an explicitly empty input array (DK-DIAG-12).

Otherwise valid repeated references to one generalization count as one membership under every input policy, with no additional diagnostic solely for repetition. The [membership-identity rule](input.md#generalization-set-membership) preserves existing errors and independently required diagnostics; it cannot turn a partially failed larger set into a complete singleton. The linked reference records the implementation status of this accepted behavior.

Unresolved/failed class-set members are errors. `strict`/`tolerant` abort; `best-effort` omits coverage while retaining applicable surviving pairwise disjointness and independent mappings. Never apply singleton coverage merely because one member survives. For a class set with a nonempty membership array and a usable categorizer, [bounded categorizer recovery](../mapping/higher-order.md#recovery-for-incomplete-categorized-class-sets) uses the existing member ERROR and preserves surviving explicit classifications under `best-effort`, with powertype expansion omitted. When the categorizer is also unusable, all categorizer and powertype-extension assertions from that set are omitted under [unusable-categorizer recovery](#unusable-categorizer-in-class-generalization-sets). See [Class-set recovery](../mapping/classes.md#singleton-and-recovery-boundaries).

Absent/null/empty enumeration `literals` requires a nonfatal warning even under `strict`, retaining the class and independent mappings without closure/empty-extension assertions. With owned properties, the warning should clarify that they were not treated as values. Malformed supplied lists or failed values remain errors: strict/tolerant abort, best-effort preserves successful individuals/membership without subset closure. Survivor count alone adds no event. A generic fallback-preserved literal is a success, not a failed value (DK-DIAG-13; [enumeration mapping](../mapping/classes.md#enumerations-and-closure)). `DK-DIAG-13` governs `Class` declarations with `stereotype == "enumeration"`; `literals` on non-enumeration `Class` declarations (`stereotype != "enumeration"`) is governed separately under [Class properties and non-enumeration literals](#class-properties-and-non-enumeration-literals) (`DK-CLS-11`, `DK-DIAG-05`).

Complete relation sets with at least two distinct specifics require a nonfatal omitted-coverage warning under every policy; `isComplete: false` alone does not warn. [Singleton completeness](../mapping/relations.md#fully-resolved-singleton) instead has the applied-mapping INFO below.

For chains, ambiguities omit the affected chain with their specified nonfatal diagnostic; multiple matching relator mediations require a warning. Same-class relator/mode grounding is nonfatal even under `strict`, while `none` alone adds no same-class warning. At least one **emitted** material chain requires the mode-specific nonfatal compatibility notice, even without a conflicting constraint. Omission-mode reporting identifies applied policy and actual omitted categories/source elements; preservation-mode reporting explains retained constraints and possible OWL 2 DL incompatibility. [Derivations and material chains](../mapping/derivations-and-chains.md#owl-compatibility) owns these conditions (DK-DIAG-07–08).

With [DKGM vocabulary mode `none`](../mapping/mereology.md#vocabulary-delivery-modes), an emitted bridge to `dkgm:memberOf`, `dkgm:subCollectionOf` or `dkgm:subQuantityOf` requires a **nonfatal WARNING under every input policy, including `strict`**. The warning explains that the generic chains are absent and that consumers needing those entailments must supply the chain axioms or equivalent rules to their reasoner. This condition applies only in `none` and depends on emitted bridges. A graph with only `componentOf` bridges or no emitted bridge does not trigger it. [Diagnostic collection and export](#diagnostic-collection-and-export) governs consolidation, content, filtering and delivery.

Intentional non-representation or either valid endpoint order of a supported material derivation alone adds no warning/error. A comparative–quality connector instead has its specific nonfatal unsupported-semantics diagnostic. Other resolved relation-valued patterns without accepted mappings warn nonfatally and omit the connector while retaining independent endpoints. Null/malformed/unresolved endpoints are structural errors, not that intentional-omission fallback.

#### Datatype-valued relation and property-kind compatibility

Under `RD-02` (`DK-REL-01`, `DK-PROP-03`, `DK-REL-14–15, 20`), DirectKG enforces targeted transformation-compatibility checks (without introducing general OntoUML semantic validation or guaranteeing overall OWL 2 DL conformance). `DK-DIAG-04`'s eight-code first-release core remains unchanged; diagnostic identifiers for these conditions remain [provisional](#stable-first-release-diagnostic-core).

| Condition | Severity & timing | `strict` / `tolerant` | `best-effort` recovery |
| --- | --- | --- | --- |
| `Class → void` ordinary relation | Structural **ERROR** (`DK-REL-01`, pre-IRI/naming) | `aborted`, no ontology | Retain **ERROR**; omit relation and all dependent output; no rangeless datatype property |
| Source `Class` lacking a generated local `owl:Class` (`Primitive/void → Class`, `Primitive/void → Primitive/void`, or omitted class) | Structural **ERROR** (`DK-REL-01`, `DK-DIAG-03`, pre-IRI/naming) | `aborted`, no ontology | Retain **ERROR**; omit relation and all dependent output; never reverse direction or invent a class |
| Datatype-valued relation carrying `componentOf`, `memberOf`, `subCollectionOf`, `subQuantityOf`, `characterization`, `mediation`, `participational`, or `externalDependence` | Structural **ERROR** (`DK-REL-01`, pre-IRI/naming) | `aborted`, no ontology | Retain **ERROR**; omit relation and all dependent output |
| Datatype-valued `material` relation with an eligible, unambiguous `DK-REL-07` property chain under `omit-conflicting-constraints` or `preserve-conflicting-constraints` | Structural compatibility **ERROR** (`DK-REL-01`, `DK-REL-07`, chain stage) | `aborted`, no ontology | Retain **ERROR**; omit the `material` relation and all dependent output. *(Failed or ambiguous grounding preserves compatible datatype-valued `material` relation.)* |
| Datatype-valued `comparative` relation paired with a recognized `DK-REL-18` comparative–quality derivation | Structural compatibility **ERROR** (`DK-REL-01`, `DK-REL-18`, derivation stage) | `aborted`, no ontology | Retain **ERROR**; omit comparative relation and dependent output while retaining `Q` and independent mappings |
| Datatype-valued relation with valid, meaningful source-end multiplicity requiring a restriction (`0`, `0..0`, `0..u`, `l..*` with `l > 0`, `l..u` with `l > 0` or finite `u`, including `l > u`) | Structural **ERROR** (`DK-REL-01`, pre-IRI/naming) | `aborted`, no ontology | Retain **ERROR**; omit relation and all dependent output |
| `DK-PROP-03` `subsettedProperties` / `redefinedProperties` requiring an unavailable datatype-property inverse | Structural **ERROR** (`DK-PROP-03`) | `aborted`, no ontology | Retain **ERROR**; omit only the affected inclusion axiom when primary relation survives |
| **Global:** `DK-PROP-03` `subsettedProperties` / `redefinedProperties` connecting an `owl:ObjectProperty` (or inverse expression) and an `owl:DatatypeProperty` (including attributes as well as relations) | Structural **ERROR** (`DK-PROP-03`, global supersession) | `aborted`, no ontology | Retain **ERROR**; omit only the incompatible inclusion axiom; preserve independently valid properties and homogeneous inclusions |
| Mixed `owl:ObjectProperty` / `owl:DatatypeProperty` relation generalization (`DK-REL-14`) or cross-kind disjointness pair (`DK-REL-15`) | Structural **ERROR** (`DK-REL-14`, `DK-REL-15`) | `aborted`, no ontology | Retain **ERROR**; omit only the incompatible hierarchy edge or cross-kind disjointness pair; preserve valid homogeneous edges/pairs; never activate singleton completeness or `DK-DIAG-14` INFO |

Under `best-effort`, omitting an incompatible relation must leave **zero** orphaned inverse expressions, property hierarchies, cardinality restrictions, annotations, property inclusions, or chain axioms referring to that omitted relation.

**Implementation status.** At [specification registration revision `283f9b01361830c2dfb1e96b08111e1f8f849b31`](https://github.com/pedropaulofb/ontouml-directkg/blob/283f9b01361830c2dfb1e96b08111e1f8f849b31/src/ontouml_directkg/relations.py#L119-L120), `collect_relations` in `src/ontouml_directkg/relations.py` still raises `NotImplementedError("Ordinary relation endpoints without local class representations remain unspecified")` when an endpoint lacks a local `owl:Class` (caught as `INTERNAL_TRANSFORMATION_FAILURE`), and `emit_property_references` in [`src/ontouml_directkg/properties.py`](https://github.com/pedropaulofb/ontouml-directkg/blob/283f9b01361830c2dfb1e96b08111e1f8f849b31/src/ontouml_directkg/properties.py#L198-L237) does not yet check for mixed object/data property kinds. The rules above describe accepted intended behavior.

#### Attributes owned without a local OWL class

When an attribute is owned by a `Class` that does not generate a local `owl:Class` under `DK-CLS-01`—specifically, a registered primitive `datatype` (`DK-DAT-02`) or Visual Paradigm `void` (`DK-DAT-04`)—DirectKG reports a structural **ERROR** under `DK-ATT-01` (`RD-02`, Alternative A) identifying the affected attribute, its owning `Class`, and the missing local `owl:Class` representation. This check runs before attribute `propertyType` resolution, IRI candidate allocation, `emit_attributes`, and multiplicity/flag diagnostics, avoiding secondary attribute errors (such as `UNRESOLVED_ATTRIBUTE_TYPE`, `VOID_DATATYPE`, `MISSING_CARDINALITY`, `INVALID_CARDINALITY`, `GENERIC_ID_FALLBACK`, or `MISSING_NAME`) or IRI candidate claims from the omitted attribute. Fatal duplicate declaration IDs (`§3.4`, `DK-DIAG-05`), stereotype policy (`DK-DIAG-06`), and source-ID validity (`§3.4`, `DK-DIAG-05`) retain their prior precedence. `DK-DIAG-04`'s eight-code first-release core remains unchanged (the diagnostic identifier remains [provisional](#stable-first-release-diagnostic-core)), and no new configuration option is introduced.

| Input policy | Transformation outcome and output | CLI exit code |
| --- | --- | --- |
| `strict` or `tolerant` (default) | `aborted`. No ontology is delivered. | `3` when diagnostics delivery does not fail. |
| `best-effort` | `completed-with-errors` for this error alone. Retain **ERROR** severity, omit the affected attribute and all dependent output (declaration, `rdfs:domain`, `rdfs:range`, labels, comments, source-ID annotations, multiplicity restrictions, IRI claims, and attribute-level processing/diagnostics), and preserve independently transformable elements. The ontology remains eligible for delivery. | `1` when requested output delivery succeeds. |

Under `best-effort`, dependent `subsettedProperties` and `redefinedProperties` references targeting an attribute omitted under this rule—or declared on the omitted attribute itself—are omitted cleanly without generating an additional `UNRESOLVED_PROPERTY_REFERENCE` error (`DK-PROP-03`). Suppression applies strictly to references whose targets are known to have been omitted under this `DK-ATT-01` owner-lacks-local-class rule (alongside omitted relations, omitted misplaced `Property` declarations from `Package.contents` under `DK-GEN-06`, and unsupported relation-valued connectors); genuinely unresolved references, malformed reference containers (`INVALID_PROPERTY_REFERENCES`), and references targeting attributes omitted for other independent failures (such as `UNRESOLVED_ATTRIBUTE_TYPE`) retain their established diagnostics.

DirectKG must not invent a local `owl:Class` for primitives or `void` or emit a domainless attribute property. Attributes owned by classes with generated local `owl:Class` resources (including custom `datatype` classes) and attributes *typed by* primitives, `void`, or `null` retain their existing mappings. Rejecting attributes owned by primitives or `void` is a transformation limitation, not OntoUML semantic validation (`DK-DIAG-02`). See [Attributes owned without a local OWL class](../mapping/attributes-and-datatypes.md#attributes-owned-without-a-local-owl-class) and [Subsetting](../mapping/property-features.md#subsetting).

**Implementation status.** At [specification registration revision `ddca486133edb1b27a26c8995d612c4579afd838`](https://github.com/pedropaulofb/ontouml-directkg/blob/ddca486133edb1b27a26c8995d612c4579afd838/src/ontouml_directkg/properties.py#L40-L41), `collect_attributes` in `src/ontouml_directkg/properties.py` (lines 40–41) still raises `NotImplementedError("Attribute ownership without a generated local class is outside the decided baseline")`, caught in [`conversion.py`](https://github.com/pedropaulofb/ontouml-directkg/blob/ddca486133edb1b27a26c8995d612c4579afd838/src/ontouml_directkg/conversion.py#L250-L254) as `INTERNAL_TRANSFORMATION_FAILURE` (aborting under every input policy, including `best-effort`), and `PropertyExpressions` / `emit_property_references` do not yet track or suppress `DK-PROP-03` inclusions for attributes omitted under this rule. The rules above describe accepted intended behavior.

#### Non-binary and malformed relation properties containers

Under `DK-DIAG-03` and `DK-DIAG-05` (`RD-02`, Alternative A), `Relation.properties` association-end containers distinguish non-`«instantiation»` relations from `«instantiation»` relations:

- **Non-`«instantiation»` relations (including ordinary relations and `«derivation»` relations):** A `Relation` whose `properties` field is absent, explicitly `null`, not a JSON array, contains any non-object or non-`Property` entry, or is an array of length other than `2` (empty `0`, unary `1`, or unsupported n-ary with `>= 3` ends) triggers a structural **ERROR** identifying the affected relation and the container or arity condition.
- **`«instantiation»` relations (`DK-INS-01–02`):** Absent `properties`, explicit `properties: null`, and valid `Property`-object arrays (every entry a JSON object with `type: "Property"`, regardless of array length) retain their existing [discard behavior](../mapping/instantiation.md#discarded-association-information). By contrast, a non-array `properties` value (including non-array primitives or objects) or a `properties` array containing any non-object or non-`Property` entry triggers the same structural **ERROR**.

| Input policy | Transformation outcome and output | CLI exit code |
| --- | --- | --- |
| `strict` or `tolerant` (default) | `aborted`. No ontology is delivered. | `3` when diagnostics delivery does not fail. |
| `best-effort` | `completed-with-errors` for this error alone. Retain **ERROR** severity, omit the affected relation and all dependent output (no primary or inverse properties, annotations, cardinalities, bridges, chains, grounding/derivation recognition, attribute mappings from its ends, or discard warnings/output from malformed `«instantiation»` entries), and continue processing independently transformable elements. The ontology remains eligible for delivery. | `1` when requested output delivery succeeds. |

Under `best-effort`, relations omitted under this rule join the omitted-relations set for clean downstream handling:

- **`DK-PROP-03` inclusions:** `subsettedProperties` and `redefinedProperties` references targeting—or declared on—valid `Property` ends within a non-binary or malformed `Relation.properties` array of an omitted relation are omitted cleanly without generating an additional `UNRESOLVED_PROPERTY_REFERENCE` error. Genuinely unresolved, malformed, or independently invalid references retain their established diagnostics. See [Subsetting](../mapping/property-features.md#subsetting).
- **Relation generalizations and sets (`DK-REL-14`, `DK-REL-15`, `DK-REL-20`):** Generalizations referencing an omitted relation retain `FAILED_RELATION_GENERALIZATION` handling—omitting the hierarchy edge and preventing singleton completeness or `DK-DIAG-14` INFO while preserving surviving specifics' disjointness and independent mappings. See [Generalization and disjointness](../mapping/relations.md#generalization-and-disjointness).

Established diagnostic precedence remains unchanged: fatal duplicate declaration IDs (`§3.4`, `DK-DIAG-05`), `§3.4` missing or invalid declaration IDs on the `Relation`, and stereotype acceptance/rejection (`DK-DIAG-06`) evaluated over valid `Property` objects inside a `Relation.properties` array retain precedence. Separate handling of other declaration containers (`Class.properties`, `Package.contents`, and non-enumeration `Class.literals`, governed by `DK-ATT-01`, `DK-GEN-06`, `DK-CLS-11`, and `DK-DIAG-05`), misplaced declarations outside `Relation.properties`, and malformed flag values remain distinct. This rule introduces no n-ary relation transformation, no change to `DK-DIAG-04`'s eight-code first-release core (identifiers remain [provisional](#stable-first-release-diagnostic-core)), and no new CLI or Python configuration option.

**Implementation status.** At [specification registration revision `08abccac8a6923c587cf351a5137f1e140e44a17`](https://github.com/pedropaulofb/ontouml-directkg/blob/08abccac8a6923c587cf351a5137f1e140e44a17/src/ontouml_directkg/relations.py#L83-L85), `index_project` in [`src/ontouml_directkg/source.py`](https://github.com/pedropaulofb/ontouml-directkg/blob/08abccac8a6923c587cf351a5137f1e140e44a17/src/ontouml_directkg/source.py#L150-L189) still raises `NotImplementedError` for non-list `properties` containers, non-object entries, or non-`Property` entries; `collect_relations` in `src/ontouml_directkg/relations.py` (lines 83–85) still raises `NotImplementedError("Non-binary/malformed relation-container handling is outside this increment")` when `properties` is absent, `null`, non-list, or has length other than `2`; and [`_discard_instantiation`](https://github.com/pedropaulofb/ontouml-directkg/blob/08abccac8a6923c587cf351a5137f1e140e44a17/src/ontouml_directkg/relations.py#L40-L42) still raises `NotImplementedError` for non-list or non-dict `properties` entries without validating `type == "Property"`. Those `NotImplementedError` exceptions are caught in [`conversion.py`](https://github.com/pedropaulofb/ontouml-directkg/blob/08abccac8a6923c587cf351a5137f1e140e44a17/src/ontouml_directkg/conversion.py#L250-L254) as `INTERNAL_TRANSFORMATION_FAILURE`, aborting under every input policy, including `best-effort`. The rules above describe accepted intended behavior.

#### Malformed package contents

An absent, explicitly `null`, or empty array-valued `Package.contents` is accepted as an empty collection under every input policy, without an additional diagnostic solely for that condition (`DK-GEN-06`). For a non-null, non-array value or invalid/misplaced entries inside a valid `Package.contents` array (`RD-02`, Alternatives 1A + 2A), apply the structural-error policies (`DK-GEN-06`, `DK-DIAG-05`):

| Condition in `Package.contents` | `strict` | `tolerant` (default) | `best-effort` |
| --- | --- | --- | --- |
| Non-null, non-array `Project.model.contents` (root model package) | **ERROR** and `aborted` | **ERROR** and `aborted` | **ERROR** and `aborted`, because reliable model discovery is impossible |
| Non-null, non-array `contents` on a nested `Package` | **ERROR** and `aborted` | **ERROR** and `aborted` | Retain **ERROR**, omit the affected nested contents, and continue with independent elements |
| Valid `Package.contents` array (root or nested): non-object entry, object lacking a valid nonempty string `type` (absent, `null`, non-string, empty/whitespace-only), or misplaced `Project`, `Property`, or `Literal` | **ERROR** and `aborted` | **ERROR** and `aborted` | Retain **ERROR**, omit only the malformed or misplaced entry (without generating OWL declarations, attributes, or `owl:NamedIndividual`s and without aborting the root package), and preserve valid siblings in root and nested packages |
| Valid `Package.contents` array: object with a valid nonempty string `type` outside the supported OntoUML set (`Project`, `Package`, `Class`, `Relation`, `Property`, `Generalization`, `GeneralizationSet`, `Literal`) | `UNKNOWN_INFORMATION` **ERROR** and `aborted` | `UNKNOWN_INFORMATION` **WARNING**; omit unrecognized entry and continue | `UNKNOWN_INFORMATION` **WARNING**; omit unrecognized entry and continue |

Permitted package-level declaration types in `Package.contents` are `Package`, `Class`, `Relation`, `Generalization`, and `GeneralizationSet`. Root-level abort under `best-effort` remains limited to unprocessable documents (including invalid or unsupported `Project` or `Project.model` roots under `§3.2` and `DK-DIAG-05`) and non-null, non-array `Project.model.contents`.

- **Outcomes and delivery:** An abort yields `aborted` with no ontology output (CLI exit `3` when diagnostics delivery does not fail). Successful continuation after a nested-container or entry error under `best-effort` yields `completed-with-errors` with eligible ontology output if no other condition requires abortion (CLI exit `1` when requested output delivery succeeds). Diagnostic access and export follow the [existing outcome and delivery contract](#outcomes-and-output-eligibility), including exit `4` when requested diagnostics delivery fails.
- **Precedence and `DK-PROP-03`:** Indexed misplaced declarations in `Package.contents` with valid source IDs (`Property`, `Literal`) retain fatal `DUPLICATE_SOURCE_ID` (`§3.4`, `DK-DIAG-05`), `DK-DIAG-06` stereotype-policy precedence (for `Property`), and `§3.4` missing/invalid declaration-ID precedence (`apply_identifier_policy` on `Property`) before entry omission. Under `best-effort`, a misplaced `Property` declaration with a valid ID omitted from `Package.contents` follows `DK-PROP-03`'s [omitted-property suppression rules](../mapping/property-features.md#subsetting): both its own `subsettedProperties`/`redefinedProperties` and references targeting it omit dependent inclusions cleanly without generating an additional `UNRESOLVED_PROPERTY_REFERENCE` error, whereas genuinely unresolved references and references targeting unindexed non-`Property` entries retain `UNRESOLVED_PROPERTY_REFERENCE`.
- **Scope boundary:** This rule introduces no new stable diagnostic identifier (`DK-DIAG-04`'s eight-code core remains unchanged; identifiers remain [provisional](#stable-first-release-diagnostic-core)) and no new configuration option.

**Implementation status.** At [specification registration revision `c87a6a2cd83f6da675018edb1b0af81f86ad7013`](https://github.com/pedropaulofb/ontouml-directkg/blob/c87a6a2cd83f6da675018edb1b0af81f86ad7013/src/ontouml_directkg/source.py#L150-L193), `index_project` in [`src/ontouml_directkg/source.py`](https://github.com/pedropaulofb/ontouml-directkg/blob/c87a6a2cd83f6da675018edb1b0af81f86ad7013/src/ontouml_directkg/source.py#L150-L193) accepts absent, `null`, and `[]` `Package.contents`, but still raises `NotImplementedError` for other non-array `Package.contents` (line 185) and non-object entries (line 152), routes objects lacking a valid nonempty string `type` to `UNKNOWN_INFORMATION` (lines 155–157), and traverses misplaced `Project`/`Property`/`Literal` entries in `Package.contents` (line 192) until [`collect_attributes`](https://github.com/pedropaulofb/ontouml-directkg/blob/c87a6a2cd83f6da675018edb1b0af81f86ad7013/src/ontouml_directkg/properties.py#L40-L41) raises `NotImplementedError` for misplaced `Property` or [`baseline_classes`](https://github.com/pedropaulofb/ontouml-directkg/blob/c87a6a2cd83f6da675018edb1b0af81f86ad7013/src/ontouml_directkg/classifiers.py#L36-L40) raises `NotImplementedError` for misplaced `Literal`. Those `NotImplementedError` exceptions are caught by the [internal-failure handler](https://github.com/pedropaulofb/ontouml-directkg/blob/c87a6a2cd83f6da675018edb1b0af81f86ad7013/src/ontouml_directkg/conversion.py#L250-L254) as `INTERNAL_TRANSFORMATION_FAILURE`, aborting under every policy. The rules above describe accepted intended behavior.

#### Class properties and non-enumeration literals

Under `DK-ATT-01`, `DK-CLS-01`, `DK-CLS-11`, and `DK-DIAG-05` (`RD-02`, Alternatives 3A + 4A), container and entry validation for `Class.properties` and non-enumeration `Class.literals` follows these policies:

- **`Class.properties` (Alternative 3A):** Absent `properties`, explicit `properties: null`, and `properties: []` are accepted as empty without an error or warning. Any non-null, non-array `Class.properties` value, any non-object entry, or any non-`Property` entry (including known non-`Property` OntoUML types, valid unknown string `type` values, or objects lacking a valid string `type`) emits a structural **ERROR** (not `UNKNOWN_INFORMATION`).
- **Non-enumeration `Class.literals` (Alternative 4A):** For any `Class` without `stereotype == "enumeration"` (including ordinary OntoUML stereotypes, `datatype`, `abstract`, `null` stereotype, and custom stereotypes accepted under `DK-DIAG-06`), absent `literals`, explicit `literals: null`, and `literals: []` are accepted as empty without an error or warning. Any non-null, non-array `literals` value, any non-object/non-`Literal` entry, or any valid `Literal` entry emits a structural **ERROR**. Enumeration classes (`stereotype == "enumeration"`) remain governed separately by `DK-DIAG-13` and [Enumerations and closure](../mapping/classes.md#enumerations-and-closure).

| Input policy | Transformation outcome and output | CLI exit code |
| --- | --- | --- |
| `strict` or `tolerant` (default) | `aborted`. No ontology is delivered. | `3` when diagnostics delivery does not fail. |
| `best-effort` | `completed-with-errors` for these errors alone. Retain **ERROR** severity; omit the malformed container or invalid entry (and non-enumeration `literals` without generating `owl:NamedIndividual`s, enumeration membership, `owl:oneOf`, or `owl:AllDifferent` assertions); retain the owning `Class` (where eligible under `DK-CLS-01`), any valid `Property` siblings in `Class.properties`, and all independently transformable mappings. | `1` when requested output delivery succeeds. |

Established diagnostic precedence and downstream handling remain preserved:

- **Precedence:** Valid `Property` objects inside `Class.properties` retain fatal `DUPLICATE_SOURCE_ID` (`§3.4`, `DK-DIAG-05`), `DK-DIAG-06` stereotype-policy precedence, and `§3.4` missing/invalid declaration-ID precedence before container or entry omission. Valid `Literal` objects inside non-enumeration `Class.literals` retain fatal `DUPLICATE_SOURCE_ID` precedence before entry omission, and the owning `Class` retains `DK-DIAG-06` stereotype-policy precedence and `§3.4` declaration-ID precedence before `literals` validation or omission.
- **`DK-PROP-03` references:** Non-`Property` entries in `Class.properties` are not indexed `Property` declarations, so any `DK-PROP-03` reference targeting them remains genuinely unresolved and retains `UNRESOLVED_PROPERTY_REFERENCE`.
- **Scope boundary:** Neither rule introduces a new stable diagnostic identifier (`DK-DIAG-04`'s eight-code first-release core remains unchanged; identifiers remain [provisional](#stable-first-release-diagnostic-core)) or a new configuration option.

**Implementation status.** At [specification registration revision `c87a6a2cd83f6da675018edb1b0af81f86ad7013`](https://github.com/pedropaulofb/ontouml-directkg/blob/c87a6a2cd83f6da675018edb1b0af81f86ad7013/src/ontouml_directkg/source.py#L151-L185), `index_project` in `src/ontouml_directkg/source.py` still raises `NotImplementedError` for non-list `Class.properties` or non-enumeration `Class.literals` containers (lines 184–185), non-object entries (lines 151–152), and misplaced non-`Property`/non-`Literal` entries of known types (lines 158–159), while routing missing/non-string or unknown `type` entries to `UNKNOWN_INFORMATION` (lines 155–157); and [`baseline_classes`](https://github.com/pedropaulofb/ontouml-directkg/blob/c87a6a2cd83f6da675018edb1b0af81f86ad7013/src/ontouml_directkg/classifiers.py#L36-L40) in `src/ontouml_directkg/classifiers.py` still raises `NotImplementedError("Literal declarations outside enumerations have no assigned baseline mapping")` for `Literal` entries on non-enumeration classes. Those `NotImplementedError` exceptions are caught in [`conversion.py`](https://github.com/pedropaulofb/ontouml-directkg/blob/c87a6a2cd83f6da675018edb1b0af81f86ad7013/src/ontouml_directkg/conversion.py#L250-L254) as `INTERNAL_TRANSFORMATION_FAILURE`, aborting under every input policy, including `best-effort`. The rules above describe accepted intended behavior.

#### Missing or malformed generalization-set membership

For a recognized `GeneralizationSet`, an absent, explicitly `null`, or other non-array JSON value for `generalizations` requires a structural **ERROR** under DK-DIAG-12. The diagnostic identifies the set and which field condition occurred. Its identifier remains [provisional](#stable-first-release-diagnostic-core). A fatal duplicate declaration ID still takes precedence under the [input-policy rules](#input-policy).

| Input policy | Transformation outcome and output | CLI exit code |
| --- | --- | --- |
| `strict` or `tolerant` (default) | `aborted`. No ontology is delivered. | `3` when diagnostics delivery does not fail. |
| `best-effort` | `completed-with-errors` for this error alone. Omit all output derived solely from the affected set and continue with independently transformable information. The ontology remains eligible for delivery. | `1` when requested output delivery succeeds. |

Under `best-effort`, DirectKG infers no members and emits no coverage, disjointness, categorizer assertions, or powertype expansion from the affected set. Generalization axioms and classifications supported independently of that set still apply. Failures inside a nonempty array follow the applicable member-failure rules above; unusable categorizers on class sets with a nonempty array follow [unusable-categorizer recovery](#unusable-categorizer-in-class-generalization-sets), and non-null categorizers on relation sets with a nonempty array follow [relation-set categorizer recovery](#non-null-categorizer-in-relation-generalization-sets) below. [Input contract and exporter behavior](input.md#generalization-set-membership)

The diagnostic follows the existing [CLI and Python access and export rules](#diagnostic-collection-and-export). Failure to deliver requested diagnostics takes precedence with CLI exit code `4`, leaving the transformation outcome intact. [CLI exit codes and delivery precedence](../guides/cli.md#exit-codes-and-delivery-failures)

**Implementation status.** At the [reviewed registration revision](https://github.com/pedropaulofb/ontouml-directkg/blob/5f8de1888f307c42b55c40bfac82ea07f60836a7/src/ontouml_directkg/generalizations.py#L90-L101), the non-array guard still raises `NotImplementedError`. The recovery above describes the accepted behavior.

#### Unusable categorizer in class generalization sets

For a class generalization set with a nonempty `generalizations` array and a present, non-null `categorizer` value that cannot supply a generated local `owl:Class` (a malformed reference; an unresolved reference, including a dangling ID, reference-type mismatch, or class omitted earlier under `best-effort`; a non-`Class` declaration; or a `Class` without a generated local `owl:Class` under DK-CLS-01, such as a supported primitive datatype or `void`), DirectKG reports a structural **ERROR** under DK-HO-04 identifying the affected generalization set and the unusable-categorizer condition. Absent or explicit `null` `categorizer` denotes an uncategorized set without error. The diagnostic identifier remains [provisional](#stable-first-release-diagnostic-core).

| Input policy | Transformation outcome and output | CLI exit code |
| --- | --- | --- |
| `strict` or `tolerant` (default) | `aborted`. No ontology is delivered. | `3` when diagnostics delivery does not fail. |
| `best-effort` | `completed-with-errors` for this error alone. Retain ERROR severity, omit all DK-HO-02 categorizer and DK-HO-03 powertype-extension assertions derived from that set, and continue with independently valid membership-based constraints and independent mappings. The ontology remains eligible for delivery. | `1` when requested output delivery succeeds. |

Under `best-effort`, an unusable categorizer alone does not suppress `isDisjoint: true` pairwise disjointness, `isComplete: true` multi-member coverage or singleton completeness (with its required DK-DIAG-14 INFO diagnostic) when membership is complete, independent class generalizations, or higher-order classifications established independently by other rules. When a member also fails under DK-CLS-09, both rules apply together: coverage and all categorizer/powertype assertions from that set are omitted while applicable pairwise disjointness among surviving specifics and independent mappings are retained.

[DK-DIAG-12](#missing-or-malformed-generalization-set-membership) continues to govern empty, missing, or malformed `generalizations` containers, and the fatal [duplicate-declaration-ID rule](#input-policy) retains precedence under every input policy, including `best-effort`. Non-null categorizers on relation generalization sets are outside this class-set rule and follow [Non-null categorizer in relation generalization sets](#non-null-categorizer-in-relation-generalization-sets) below. The diagnostic follows existing [CLI and Python access and export rules](#diagnostic-collection-and-export); diagnostics-delivery failure takes precedence with CLI exit code `4`, leaving the transformation outcome intact. See [unusable-categorizer recovery](../mapping/higher-order.md#recovery-for-an-unusable-categorizer) for prohibitions and illustration, and [CLI exit codes](../guides/cli.md#exit-codes-and-delivery-failures) for delivery precedence.

**Implementation status.** At the [reviewed registration revision `0f290d3afb830418297af13c30c4c65be1e13ca8`](https://github.com/pedropaulofb/ontouml-directkg/blob/0f290d3afb830418297af13c30c4c65be1e13ca8/src/ontouml_directkg/generalizations.py#L153-L162), unusable categorizers still raise `NotImplementedError`, caught in [`conversion.py`](https://github.com/pedropaulofb/ontouml-directkg/blob/0f290d3afb830418297af13c30c4c65be1e13ca8/src/ontouml_directkg/conversion.py#L246-L250) as `INTERNAL_TRANSFORMATION_FAILURE` and aborting under every input policy, including `best-effort`. The recovery above describes the accepted contract.

#### Non-null categorizer in relation generalization sets

For a relation generalization set (a `GeneralizationSet` with a nonempty `generalizations` array containing relation generalization(s)) carrying a present, non-null `categorizer` value—regardless of whether that value is malformed, unresolved, resolves to a non-`Class` declaration, or resolves to a `Class` (with or without a generated local `owl:Class`)—DirectKG reports a structural **ERROR** under DK-HO-04 identifying the affected generalization set and the inapplicable non-null `categorizer` condition. An absent or explicit `null` `categorizer` on a relation generalization set continues to denote an uncategorized set without error. No new stable diagnostic identifier is selected (`DK-DIAG-04`'s eight-code core remains unchanged; the identifier remains [provisional](#stable-first-release-diagnostic-core)).

| Input policy | Transformation outcome and output | CLI exit code |
| --- | --- | --- |
| `strict` or `tolerant` (default) | `aborted`. No ontology is delivered. | `3` when diagnostics delivery does not fail. |
| `best-effort` | `completed-with-errors` for this error alone. Retain ERROR severity, emit no DK-HO-02 categorizer, DK-HO-03 powertype-extension, or property-typing assertions derived from that set, and continue processing independently valid membership-based relation-set behavior and independent mappings. The ontology remains eligible for delivery. | `1` when requested output delivery succeeds. |

Under `best-effort`, a non-null `categorizer` alone does not suppress `isDisjoint: true` pairwise `owl:propertyDisjointWith` on primary and matching named-inverse properties (DK-REL-15, subject to DK-REL-07's mode-specific omission), singleton `isComplete: true` with its required DK-DIAG-14 INFO diagnostic (DK-REL-20), the multi-member `isComplete: true` limitation warning (DK-REL-16), independent relation generalizations (DK-REL-14, DK-INV-12), relations, or classes (including the referenced `Class` if independently declared). When a member also fails or is unresolved under `best-effort`, both structural ERRORs are retained and apply together: all DK-HO-02, DK-HO-03, and property-typing assertions derived from that set are omitted; singleton completeness and DK-DIAG-14 INFO are omitted (including when partial failure of a larger set leaves one survivor); multi-member `isComplete` emits no completeness axiom while retaining any applicable DK-REL-16 warning when its conditions hold; and `isDisjoint: true` retains applicable pairwise `owl:propertyDisjointWith` among successfully generated primary properties (and corresponding generated named inverses) of surviving explicit specific relations under DK-REL-15 (subject to DK-REL-07), together with independent relation generalizations, relations, and classes.

[DK-DIAG-12](#missing-or-malformed-generalization-set-membership) retains precedence for empty, absent, `null`, or other non-array `generalizations` containers, and the fatal [duplicate-declaration-ID rule](#input-policy) retains precedence under every input policy, including `best-effort`. Mixed class/relation generalizations and mixed class/relation generalization sets remain outside scope. The diagnostic follows existing [CLI and Python access and export rules](#diagnostic-collection-and-export); diagnostics-delivery failure takes precedence with CLI exit code `4`, leaving the transformation outcome intact. See [Non-null categorizer on relation generalization sets](../mapping/higher-order.md#non-null-categorizer-on-relation-generalization-sets) for prohibitions and illustration, and [CLI exit codes](../guides/cli.md#exit-codes-and-delivery-failures) for delivery precedence.

**Implementation status.** At the [reviewed registration revision `cc562c49a8274367e3a52d95c368abb484bfa713`](https://github.com/pedropaulofb/ontouml-directkg/blob/cc562c49a8274367e3a52d95c368abb484bfa713/src/ontouml_directkg/generalizations.py#L266-L267), `emit_relation_generalizations` still raises `NotImplementedError("Categorizer treatment for relation sets remains unspecified")` whenever `data.get("categorizer") is not None`, caught in [`conversion.py`](https://github.com/pedropaulofb/ontouml-directkg/blob/cc562c49a8274367e3a52d95c368abb484bfa713/src/ontouml_directkg/conversion.py#L247-L251) as `INTERNAL_TRANSFORMATION_FAILURE` and aborting under every input policy, including `best-effort`. The recovery above describes the accepted contract.

### Informational preservation notices

| Applied preservation condition | INFO content and limits |
| --- | --- |
| Singleton class/relation completeness actually applied | Identify set, general, specific, and extensional-equivalence consequence with distinct identifiers (covering homogeneous `owl:ObjectProperty` and homogeneous `owl:DatatypeProperty` relation generalizations). This includes a fully resolved complete `[g1, g1]` after counting one membership. Membership alone, a survivor count, or a failed generalization (including mixed object/data property-kind failure) does not trigger it. |
| `abstract` stereotype or explicit Boolean `isAbstract` preserved as comments | Explain annotation preservation without extra logical enforcement; do not imply existing stereotype disjointness was omitted. Both Boolean values retain this rule. |
| `isDerived: true` whose eligible local comment is generated | Identify element and explain no derivation rule is supplied by the annotation; do not claim an independently applied explicit derivation was omitted. False/no eligible target alone adds no event. |
| `isExtensional: true` | Identify class and explain annotation preservation without enforced essential-parthood semantics. False alone adds no event. |
| Each `isOrdered: true` occurrence successfully preserved | Identify attribute/end and explain that actual value order is not represented. False/absent/null produces neither ordering comment nor ordering-loss INFO. |

These are the nonfatal INFO conditions in DK-DIAG-14–18; the limitation alone is not a warning/error. Include produced events in complete access and requested JSON export even when hidden from console display. Comment targets remain owned by [Class declarations](../mapping/classes.md#class-declarations-preserved-as-comments), [Derived status](text.md#derived-status-comments), and [Property features](../mapping/property-features.md).

### Deliberate silence and restricted payloads

Package/diagram/presentation omission, recognized custom `propertyAssignments`, and `restrictedTo` omission add no diagnostic solely for their presence/omission, including under `strict`. They do not become unknown-input errors; independent structural failures still apply.

Expected named-inverse omission under `informed`/`named` produces no warning, INFO, or element-level report. Missing named inverses for otherwise applicable specialization, disjointness pairs, or singleton reverse inclusion (including homogeneous `owl:DatatypeProperty` relations, which have no inverses) omit those extra inverse axioms without warnings or forced inverses. Omitting a source-end description on a compatible datatype-valued relation because no named inverse exists produces no extra diagnostic solely for that omission (`DK-LBL-02`). Structurally processable, property-kind-compatible redefinition adds no runtime warning solely for its [partial translation](../mapping/property-features.md#partial-redefinition). Read-only/aggregation comment preservation and [explicit `begin`/`end` comment preservation](../mapping/property-features.md#boundary-stereotype-comments) establish no additional event solely for preserving those comments.

Discarded instantiation-association data instead requires **one consolidated warning**: source ID as locator, available type, lost categories, and output effect. Do not copy discarded name/role/multiplicity/other values into JSON, console payloads, provenance, or substitute resources. This content restriction still applies when the warning is mirrored; see [Discarded association information](../mapping/instantiation.md#discarded-association-information).

Generated fallback relation labels gain neither RDF origin markers nor extra diagnostics merely for lacking such markers. A quiet console or sparse report therefore cannot establish round-tripping or losslessness.

### Metadata and artifact failures

Explicit metadata-file read/parse/root failures are ERRORs: strict/tolerant abort; best-effort omits external contributions and continues, preserving source metadata and independent provenance. Invalid selected values follow their input-policy rules; ignored fields do not trigger field validation. See [Metadata input](../guides/metadata-and-provenance.md#metadata-input).

For a parseable top-level mapping under `best-effort`, invalid members of the four supported metadata lists are omitted while every valid sibling, independent metadata field and source transformation is retained under its existing rules. Keep applicable ERROR diagnostics; absent another abort condition, the outcome is `completed-with-errors` with eligible ontology output and existing diagnostic access/delivery. `strict` and `tolerant` still abort. The [list-recovery guide](../guides/metadata-and-provenance.md#recovery-within-metadata-lists) owns the field scope, all-invalid-list case, unchanged boundaries and implementation limitation. I1 introduces no new diagnostic identifier, schema or diagnostic-count requirement.

Required-provenance construction failure aborts before ontology delivery, independently of input policy; unavailable optional enrichment and accepted exclusions do not trigger that abort alone. Later ontology-file, sidecar, and requested diagnostic-file failures are reported separately from transformation outcomes. Turtle serialization or encoding failure for a requested ontology file produces an ERROR identifying the serialization stage, destination, available cause, and failed delivery. Requested CLI JSON export is attempted after recording the error and reports the established outcome and delivery ERROR if it succeeds. [Failure boundaries](../guides/metadata-and-provenance.md#failure-boundaries) and [CLI codes](../guides/cli.md#exit-codes-and-delivery-failures) own the exact stage and precedence distinctions.

## Multiplicity parsing and recovery

These rules apply to supported attributes and ordinary binary relation ends (DK-DIAG-09–11). Null and absence differ from present-but-invalid data:

| Input condition | Required handling |
| --- | --- |
| Explicit JSON `null` | No restriction/default and no diagnostic solely for null |
| Absent field | No restriction/default; warning and continuation under every policy; does not satisfy informed inverse mode's non-null multiplicity condition |
| Non-null value of a JSON type other than string | ERROR; no automatic conversion of numbers, booleans, arrays, or objects |
| Supported non-null string | Parse a numeric value, standalone `*`, or an interval with exactly one `..` delimiter |

Trim surrounding whitespace on the whole string and individual bounds. Accept leading zeros numerically; bounds use decimal digits `0`–`9`, without signs, decimal points, or exponent notation. Lexical normalization alone adds no event. Do not repair extra dots, repeated delimiters, commas, or colons. Blank text and ambiguous malformed expressions are errors.

Untranslatable multiplicities/bounds retain ERROR under every policy. `strict` and `tolerant` abort. In `best-effort`, preserve independently transformable information and only unambiguously positioned valid numeric bounds:

| Invalid input with unambiguous positions | Best-effort restriction contribution |
| --- | --- |
| Untranslatable single value, or both bounds invalid | None |
| Invalid/empty lower; valid finite upper `u` | Maximum `u` |
| Valid lower `l`; invalid/empty upper | Minimum `l` if positive; none when zero |
| Ambiguous malformed notation | None; do not guess positions or replacement bounds |

An empty bound is not zero or unlimited. Preserve the affected property and other independent mappings in `best-effort`, including a valid opposite relation end for `owl:ObjectProperty` relations. Recovered restrictions retain the appropriate attribute/relation representation, direction, necessary-condition placement, and inverse selection. They remain subject to [targeted material-chain omission](../mapping/derivations-and-chains.md#material-chain-modes).

**Datatype-valued relation source-end precedence (`DK-DIAG-10`):** For an invalid source-end multiplicity on a datatype-valued relation (`owl:DatatypeProperty` under `DK-REL-01`), DirectKG retains the `INVALID_CARDINALITY` **ERROR** (`strict`/`tolerant` abort). Under `best-effort`, the determination that an `owl:DatatypeProperty` has no inverse takes precedence over preservation of recoverable source-end bounds: if an independently identifiable meaningful recoverable reverse constraint exists (`lower > 0` or finite `upper` under the table above), DirectKG reports the compatibility **ERROR** and omits the affected relation rather than generating an inverse or retaining an incompatible relation; if no meaningful recoverable reverse constraint exists (e.g., `"n"`, `"0..n"`, `"2...*"`), DirectKG preserves the otherwise compatible datatype property (and any valid target-end constraints) under `DK-DIAG-10`. This precedence does not alter `DK-DIAG-10` recovery for attributes or ordinary `owl:ObjectProperty` relations.

The following are **specification illustrations**, not parser execution results:

| Input fragment | Accepted interpretation/recovery |
| --- | --- |
| `" 01 .. 03 "` | `1..3`; no diagnostic from normalization |
| `"1..n"` or `"1.."` | ERROR; best-effort retains minimum 1 |
| `"..3"` | ERROR; best-effort retains maximum 3 |
| `"2...*"` or `"2,,*"` | ERROR; no restriction recovered |
| `""`, whitespace-only text, or JSON number `1` | ERROR; no restriction recovered |
| `"5..2"` | Both numeric bounds preserved without diagnostic solely for contradiction |

Contradictory nonnegative numeric bounds are transformable under every policy; do not swap, clamp, discard, or substitute them as a repair. They can make a class unsatisfiable without independently establishing whole-ontology inconsistency. Explicit unbounded `*`/`0..*` adds no numeric constraint or warning solely for being unbounded, but still counts as non-null for inverse eligibility. Canonical successful mappings remain in [Attribute cardinalities](../mapping/attributes-and-datatypes.md#cardinalities-and-structured-datatypes) and [Relation cardinalities](../mapping/relations.md#relation-cardinalities).

---

Governing rules: DK-DIAG-01–19; §§3.2–3.4; §15; DK-ATT-01; DK-CLS-01, 11; DK-DAT-02, 04; DK-GEN-03–04, 06, 08–10, 12, including I1's recovery within list-valued metadata; DK-REL-01–07, 09–16, 18, 20; DK-PROP-03; DK-LBL-01–02; DK-INV-01–02, 05–08, 10, 12; DK-INS-01–02; DK-HO-04; DK-IRI-03–05, 07, 10; baseline consolidated: **2026-11-23**; repository commit: `ed7a0d1b1cb75f6ac764b8117c5385928f97f86b`; source: [`documentation/specification/transformation-specification.md`](https://github.com/pedropaulofb/ontouml-directkg/blob/ed7a0d1b1cb75f6ac764b8117c5385928f97f86b/documentation/specification/transformation-specification.md).

Accepted update: **RD-02 — Malformed textual and language-tag carriers (`name`, `description`, `languageString`, and `Project.languages`; Alternatives 1A + 2A)** (project-owner formalization included in the cited consolidation).

Accepted update: **RD-02 — Declaration containers, malformed entries, and misplaced declarations (`Package.contents`, `Class.properties`, non-enumeration `Class.literals`; Alternatives 1A + 2A + 3A + 4A)** (project-owner formalization included in the cited consolidation).

Accepted update: **RD-02 — Non-binary (`len != 2`) and absent/null/malformed `Relation.properties` association-end containers (Alternative A)** (project-owner formalization included in the cited consolidation).

Accepted update: **RD-02 — Attributes owned by a `Class` without a generated local `owl:Class` (Alternative A) and dependent `DK-PROP-03` handling** (project-owner formalization included in the cited consolidation).

Accepted update: **RD-02 — Datatype-valued ordinary binary relations (`Alternative B + Q1–Q7 + Conflicts A–I`) & global `DK-PROP-03` mixed-kind rejection** (project-owner formalization included in the cited consolidation).

Accepted update: **RD-18 — Comment preservation of `begin` and `end` property stereotypes** (project-owner formalization included in the cited consolidation).

Accepted update: **RD-17 — Ordinary mapping of `historicalDependence` with the applicable limitation warning (Alternative A)** (project-owner formalization included in the cited consolidation).

Accepted update: **RD-05 — Optional caller-supplied ontology version IRI** (project-owner formalization, Option B, included in the cited consolidation).
