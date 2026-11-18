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
| Attribute explicitly typed by recognized unsupported `void` (`stereotype == "datatype"`) | Nonfatal warning identifying available attribute/owner/type information and omitted mapping/range; null typing is separately supported |
| Class attribute whose `propertyType` resolves to a `Class` with a generated local `owl:Class` outside `datatype` and `enumeration` | Transform as an ordinary `owl:ObjectProperty` under DK-ATT-01 and DK-GEN-03 without inferring relation stereotypes or stereotype-specific relation mappings; no warning or error solely because the target `Class` is not `datatype` or `enumeration` (nonfatal / non-erroneous under every input policy, including `strict`). Unresolved or invalid `propertyType` references retain structural-error handling under DK-DIAG-05. See [Class-valued attributes](../mapping/attributes-and-datatypes.md#class-valued-attributes) for prohibitions, unchanged boundaries, and current implementation status. |
| Unnamed ordinary relation uses target-role or endpoint fallback, including insufficient [semantic-role evidence](../mapping/relations.md#structural-evidence-for-semantic-naming) | Nonfatal warning under existing naming conditions unless a specific rule replaces it; comparative reaching its deliberately unmapped semantic-name step warns before fallback. No additional naming diagnostic solely for generating a fallback label. |
| Successful ordinary stereotype naming / successful relator naming | Ordinary stereotype success adds no event solely for that success; relator-derived success should produce informational provenance reporting, without a warning merely for success. Independently applicable diagnostics remain. |
| Deliberately unmapped applicable relation stereotype, including `historicalDependence`, `participation`, `creation`, and `termination` | Nonfatal limitation warning under DK-DIAG-01; retain the ordinary mapping where defined. For the latter three, the warning remains nonfatal under every input policy, including `strict`. Naming success, fallback, or disabling stereotype naming does not suppress independently applicable limitation reporting. See [Historical dependence](../mapping/relations.md#historical-dependence) and [Participation, creation, and termination](../mapping/relations.md#participation-creation-and-termination), including the implementation status. |
| Successfully mapped eligible ordinary `participational` or `manifestation` relation | Required residual-semantics WARNING, nonfatal under every input policy, including `strict`. Retain ordinary mappings and applicable guarded `participational` asymmetry. Successful naming and emission or gate-based omission of that asymmetry do not suppress reporting. Existing consolidation and delivery rules apply; this decision prescribes no exact code, wording, or count. See [Participational and manifestation](../mapping/relations.md#participational-and-manifestation) for partial mappings and implementation status. |
| Successfully mapped eligible ordinary `mediation`, `characterization`, or `externalDependence` relation | Required residual-semantics WARNING, nonfatal under every input policy, including `strict`. Retain ordinary mappings, applicable accepted axioms, grounding roles, derivation treatment, and selected eligible material chains. Successful naming, axiom/chain generation, or gate-based axiom omission does not suppress it. Existing consolidation and delivery rules apply; no exact code, wording, or count is selected. See [Dependency relations](../mapping/relations.md#mediation-characterization-and-external-dependence) for the implementation-status note based on source inspection. |
| Successfully mapped eligible ordinary `bringsAbout` or `triggers` relation | Required residual-semantics WARNING, nonfatal under every input policy, including `strict`, independently of naming success. Ordinary mappings and independently required output remain applicable. Existing consolidation and delivery rules apply. Exact codes, wording and counts remain unspecified. See [BringsAbout and triggers](../mapping/relations.md#bringsabout-and-triggers) for the partial translation and the implementation-status note above that section. |
| Usable material semantic name unavailable | Warning, then accepted source–target fallback |
| Multiple project languages with no local tag or override for a supported value | Nonfatal WARNING and untagged value; may consolidate to avoid unnecessary repetition |

[Identifiers](identifiers.md#unnamed-or-unusably-named-resources) owns fallback prerequisites and exceptions; [Binary relations](../mapping/relations.md#primary-direction-and-naming) owns naming precedence. Detected collisions under the same ID-based construction follow the [internal-failure contract](#unexpected-internal-failures-during-transformation).

Insufficient semantic-role evidence alone is not a structural failure: use the established endpoint naming fallback without omitting the relation or aborting solely for that uncertainty. Structured JSON remains authoritative; this creates no semantic-orientation validation or source-repair branch. Malformed input and unresolved required references retain their existing policies.

Multiple localized naming values alone and multilingual primitive recognition add no new diagnostic/conflict check. An explicit local language or override avoids the project-language ambiguity condition; multiple explicit local languages are not themselves ambiguous. Absent/null/empty supported names on the project or supported descriptions add no diagnostic solely for that absence. Source labels, comments, and generated-label boundaries remain in [Labels, comments, and language](text.md).

### Structural failures, sets, and connectors

For directional relation generation, missing/invalid end IDs or null/unresolved end types mean **neither primary nor inverse property is generated in any policy**. Diagnose the structural problem; a valid end ID does not make a null type resolvable. Accepted best-effort continuation concerns other transformable information, not invention of that relation (DK-DIAG-03).

An explicitly empty `generalizations` array is an ERROR under every flag combination: `strict`/`tolerant` abort; `best-effort` omits the set contribution and continues elsewhere. Do not infer a general, invent members, or assert an empty class extension. This rule applies to an explicitly empty input array (DK-DIAG-12).

Otherwise valid repeated references to one generalization count as one membership under every input policy, with no additional diagnostic solely for repetition. The [membership-identity rule](input.md#generalization-set-membership) preserves existing errors and independently required diagnostics; it cannot turn a partially failed larger set into a complete singleton. The linked reference records the implementation status of this accepted behavior.

Unresolved/failed class-set members are errors. `strict`/`tolerant` abort; `best-effort` omits coverage while retaining applicable surviving pairwise disjointness and independent mappings. Never apply singleton coverage merely because one member survives. For a class set with a nonempty membership array and a usable categorizer, [bounded categorizer recovery](../mapping/higher-order.md#recovery-for-incomplete-categorized-class-sets) uses the existing member ERROR and preserves surviving explicit classifications under `best-effort`, with powertype expansion omitted. When the categorizer is also unusable, all categorizer and powertype-extension assertions from that set are omitted under [unusable-categorizer recovery](#unusable-categorizer-in-class-generalization-sets). See [Class-set recovery](../mapping/classes.md#singleton-and-recovery-boundaries).

Absent/null/empty enumeration `literals` requires a nonfatal warning even under `strict`, retaining the class and independent mappings without closure/empty-extension assertions. With owned properties, the warning should clarify that they were not treated as values. Malformed supplied lists or failed values remain errors: strict/tolerant abort, best-effort preserves successful individuals/membership without subset closure. Survivor count alone adds no event. A generic fallback-preserved literal is a success, not a failed value (DK-DIAG-13; [enumeration mapping](../mapping/classes.md#enumerations-and-closure)).

Complete relation sets with at least two distinct specifics require a nonfatal omitted-coverage warning under every policy; `isComplete: false` alone does not warn. [Singleton completeness](../mapping/relations.md#fully-resolved-singleton) instead has the applied-mapping INFO below.

For chains, ambiguities omit the affected chain with their specified nonfatal diagnostic; multiple matching relator mediations require a warning. Same-class relator/mode grounding is nonfatal even under `strict`, while `none` alone adds no same-class warning. At least one **emitted** material chain requires the mode-specific nonfatal compatibility notice, even without a conflicting constraint. Omission-mode reporting identifies applied policy and actual omitted categories/source elements; preservation-mode reporting explains retained constraints and possible OWL 2 DL incompatibility. [Derivations and material chains](../mapping/derivations-and-chains.md#owl-compatibility) owns these conditions (DK-DIAG-07–08).

With [DKGM vocabulary mode `none`](../mapping/mereology.md#vocabulary-delivery-modes), an emitted bridge to `dkgm:memberOf`, `dkgm:subCollectionOf` or `dkgm:subQuantityOf` requires a **nonfatal WARNING under every input policy, including `strict`**. The warning explains that the generic chains are absent and that consumers needing those entailments must supply the chain axioms or equivalent rules to their reasoner. This condition applies only in `none` and depends on emitted bridges. A graph with only `componentOf` bridges or no emitted bridge does not trigger it. [Diagnostic collection and export](#diagnostic-collection-and-export) governs consolidation, content, filtering and delivery.

Intentional non-representation or either valid endpoint order of a supported material derivation alone adds no warning/error. A comparative–quality connector instead has its specific nonfatal unsupported-semantics diagnostic. Other resolved relation-valued patterns without accepted mappings warn nonfatally and omit the connector while retaining independent endpoints. Null/malformed/unresolved endpoints are structural errors, not that intentional-omission fallback.

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
| Singleton class/relation completeness actually applied | Identify set, general, specific, and extensional-equivalence consequence with distinct identifiers. This includes a fully resolved complete `[g1, g1]` after counting one membership. Membership alone or a survivor count does not trigger it. |
| `abstract` stereotype or explicit Boolean `isAbstract` preserved as comments | Explain annotation preservation without extra logical enforcement; do not imply existing stereotype disjointness was omitted. Both Boolean values retain this rule. |
| `isDerived: true` whose eligible local comment is generated | Identify element and explain no derivation rule is supplied by the annotation; do not claim an independently applied explicit derivation was omitted. False/no eligible target alone adds no event. |
| `isExtensional: true` | Identify class and explain annotation preservation without enforced essential-parthood semantics. False alone adds no event. |
| Each `isOrdered: true` occurrence successfully preserved | Identify attribute/end and explain that actual value order is not represented. False/absent/null produces neither ordering comment nor ordering-loss INFO. |

These are the nonfatal INFO conditions in DK-DIAG-14–18; the limitation alone is not a warning/error. Include produced events in complete access and requested JSON export even when hidden from console display. Comment targets remain owned by [Class declarations](../mapping/classes.md#class-declarations-preserved-as-comments), [Derived status](text.md#derived-status-comments), and [Property features](../mapping/property-features.md).

### Deliberate silence and restricted payloads

Package/diagram/presentation omission, recognized custom `propertyAssignments`, and `restrictedTo` omission add no diagnostic solely for their presence/omission, including under `strict`. They do not become unknown-input errors; independent structural failures still apply.

Expected named-inverse omission under `informed`/`named` produces no warning, INFO, or element-level report. Missing named inverses for otherwise applicable specialization, disjointness pairs, or singleton reverse inclusion omit those extra inverse axioms without warnings or forced inverses. Structurally processable redefinition adds no runtime warning solely for its [partial translation](../mapping/property-features.md#partial-redefinition). Read-only/aggregation comment preservation and [explicit `begin`/`end` comment preservation](../mapping/property-features.md#boundary-stereotype-comments) establish no additional event solely for preserving those comments.

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

An empty bound is not zero or unlimited. Preserve the affected property and other independent mappings in best-effort, including a valid opposite relation end. Recovered restrictions retain the appropriate attribute/relation representation, direction, necessary-condition placement, and inverse selection. They remain subject to [targeted material-chain omission](../mapping/derivations-and-chains.md#material-chain-modes).

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

Governing rules: DK-DIAG-01–19; §3.4; §15; DK-ATT-01; DK-DAT-02; DK-GEN-03–04, 09–10, 12, including I1's recovery within list-valued metadata; DK-REL-01–06, 14–16, 20; DK-LBL-01; DK-INV-06–08, 10, 12; DK-HO-04; DK-IRI-05, 07; baseline consolidated: **2026-11-18**; repository commit: `4f9a9ccfa016a052a9b955afb0f9d863e3df8222`; source: [`documentation/specification/transformation-specification.md`](https://github.com/pedropaulofb/ontouml-directkg/blob/4f9a9ccfa016a052a9b955afb0f9d863e3df8222/documentation/specification/transformation-specification.md).

Accepted update: **RD-18 — Comment preservation of `begin` and `end` property stereotypes** (project-owner formalization included in the cited consolidation).

Accepted update: **RD-17 — Ordinary mapping of `historicalDependence` with the applicable limitation warning (Alternative A)** (project-owner formalization included in the cited consolidation).

Accepted update: **RD-05 — Optional caller-supplied ontology version IRI** (project-owner formalization, Option B, included in the cited consolidation).
