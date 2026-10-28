# Diagnostics and recovery

This reference explains **specified diagnostic behavior**, not observed converter execution. Source rule IDs are traceability references, not invented runtime diagnostic codes. The specification fixes capabilities and outcome names without selecting a complete JSON schema or Python result/exception mechanism.

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

Supplied-base rejection is **configuration rejection before conversion**, not input-policy recovery. It produces no ontology, outcome, or conversion-diagnostics report under any policy, even when report persistence was requested. Python signals it programmatically; CLI code `2` is described in [Invocation](../guides/cli.md#invocation).

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

## Diagnostic collection and export

Retain every diagnostic actually produced, preserving severity, meaning, and applicable source information. Python structured access remains available after policy-driven abortion for all events produced before termination. Python persistence is a **separate explicitly invoked JSON export operation**, not automatic writing during conversion. CLI persistence is requested by `--diagnostics-file PATH`; without it, the CLI creates no diagnostics file.

Both exports use the same report schema/content contract, exposing the outcome and mirroring produced INFO, compatibility notices, warnings, and errors—including produced reports of omitted, unsupported, invalid, ignored, or approximated source information. Attempt requested CLI export after an accepted abort and after recording specified ontology/sidecar delivery failures.

Console thresholds filter only display: `info` shows INFO/WARNING/ERROR, `warning` shows WARNING/ERROR, and `error` shows ERROR. Hidden diagnostics remain in complete structured access and requested exports. Filtering changes neither transformation behavior, collection, recovery, abortion, outcome, output eligibility, nor exit-code selection.

Access/export must not generate additional transformation diagnostics, change their meaning/severity, or alter continuation/output eligibility. A report is not required to invent an event for every documented limitation. Deliberate silence remains silent; absence of an event does not prove complete semantic preservation.

Where applicable, a diagnostic should provide enough structured information to explain and locate the event: severity, diagnostic code, source ID/type, human-readable message, and output effect. These are content recommendations, **not fixed JSON keys or a required-field matrix**. Exact codes, schema, aggregation, and Python representations remain unspecified. Console and JSON may present an event differently while preserving its content boundary.

A requested diagnostics-file creation/write failure is a separate delivery failure. CLI reports a destination/reason console error and uses code `4` with its defined precedence. Python's explicit export signals failure programmatically while retaining transformation diagnostics. Neither changes the outcome, severities, or ontology eligibility; a report failure must not replace/conceal a prior abort. No unwritable-destination recovery is prescribed. See [Separate exports](../guides/python.md#separate-exports) and [CLI reporting](../guides/cli.md#reporting-and-retained-results).

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
| Attribute explicitly typed by recognized unsupported `void` | Nonfatal warning identifying available attribute/owner/type information and omitted mapping/range; null typing is separately supported |
| Unnamed ordinary relation uses target-role or endpoint fallback | Nonfatal warning unless a specific rule replaces it; comparative reaching its deliberately unmapped semantic-name step warns before fallback |
| Successful ordinary stereotype naming / successful relator naming | Ordinary stereotype success adds no event; relator-derived success should produce informational provenance reporting, without a warning merely for success |
| Usable material semantic name unavailable | Warning, then accepted source–target fallback |
| Multiple project languages with no local tag or override for a supported value | Nonfatal WARNING and untagged value; may consolidate to avoid unnecessary repetition |

[Identifiers](identifiers.md#unnamed-or-unusably-named-resources) owns fallback prerequisites and exceptions; [Binary relations](../mapping/relations.md#primary-direction-and-naming) owns naming precedence. Collision after injective ID escaping remains exceptional: do not merge; its exact disposition is unspecified rather than an invented ordinary warning/recovery.

Multiple localized naming values alone and multilingual primitive recognition add no new diagnostic/conflict check. An explicit local language or override avoids the project-language ambiguity condition; multiple explicit local languages are not themselves ambiguous. Absent/null/empty supported names on the project or supported descriptions add no diagnostic solely for that absence. Source labels, comments, and generated-label boundaries remain in [Labels, comments, and language](text.md).

### Structural failures, sets, and connectors

For directional relation generation, missing/invalid end IDs or null/unresolved end types mean **neither primary nor inverse property is generated in any policy**. Diagnose the structural problem; a valid end ID does not make a null type resolvable. Accepted best-effort continuation concerns other transformable information, not invention of that relation (DK-DIAG-03).

An explicitly empty `generalizations` array is an ERROR under every flag combination: `strict`/`tolerant` abort; `best-effort` omits the set contribution and continues elsewhere. Do not infer a general, invent members, or assert an empty class extension. This decision does not define missing/malformed containers, duplicates, or a set emptied by failed transformations (DK-DIAG-12).

Unresolved/failed class-set members are errors. `strict`/`tolerant` abort; `best-effort` omits coverage while retaining applicable surviving pairwise disjointness and independent mappings. Never apply singleton coverage merely because one member survives. See [Class-set recovery](../mapping/classes.md#singleton-and-recovery-boundaries).

Absent/null/empty enumeration `literals` requires a nonfatal warning even under `strict`, retaining the class and independent mappings without closure/empty-extension assertions. With owned properties, the warning should clarify that they were not treated as values. Malformed supplied lists or failed values remain errors: strict/tolerant abort, best-effort preserves successful individuals/membership without subset closure. Survivor count alone adds no event. A generic fallback-preserved literal is a success, not a failed value (DK-DIAG-13; [enumeration mapping](../mapping/classes.md#enumerations-and-closure)).

Complete relation sets with at least two distinct specifics require a nonfatal omitted-coverage warning under every policy; `isComplete: false` alone does not warn. [Singleton completeness](../mapping/relations.md#fully-resolved-singleton) instead has the applied-mapping INFO below.

For chains, ambiguities omit the affected chain with their specified nonfatal diagnostic; multiple matching relator mediations require a warning. Same-class relator/mode grounding is nonfatal even under `strict`, while `none` alone adds no same-class warning. At least one **emitted** material chain requires the mode-specific nonfatal compatibility notice, even without a conflicting constraint. Omission-mode reporting identifies applied policy and actual omitted categories/source elements; preservation-mode reporting explains retained constraints and possible OWL 2 DL incompatibility. [Derivations and material chains](../mapping/derivations-and-chains.md#owl-compatibility) owns these conditions (DK-DIAG-07–08).

Intentional non-representation or either valid endpoint order of a supported material derivation alone adds no warning/error. A comparative–quality connector instead has its specific nonfatal unsupported-semantics diagnostic. Other resolved relation-valued patterns without accepted mappings warn nonfatally and omit the connector while retaining independent endpoints. Null/malformed/unresolved endpoints are structural errors, not that intentional-omission fallback.

### Informational preservation notices

| Applied preservation condition | INFO content and limits |
| --- | --- |
| Singleton class/relation completeness actually applied | Identify set, general, specific, and extensional-equivalence consequence with distinct identifiers. Membership alone or a survivor count does not trigger it. |
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

Required-provenance construction failure aborts before ontology delivery, independently of input policy; unavailable optional enrichment and accepted exclusions do not trigger that abort alone. Later ontology-file, sidecar, and requested diagnostic-file failures are reported separately from transformation outcomes. [Failure boundaries](../guides/metadata-and-provenance.md#failure-boundaries) and [CLI codes](../guides/cli.md#exit-codes-and-delivery-failures) own the exact stage and precedence distinctions.

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

Governing rules: DK-DIAG-01–19; §3.4; §15; DK-GEN-09–10; baseline consolidated: **2026-10-21**; repository commit: `a36322fa87c006cece63aaadd2aa5ccd513f6087`; source: [`documentation/specification/2026-10-21 - specification handoff.md`](https://github.com/pedropaulofb/ontouml-directkg/blob/a36322fa87c006cece63aaadd2aa5ccd513f6087/documentation/specification/2026-10-21%20-%20specification%20handoff.md).

Accepted update: **RD-18 — Comment preservation of `begin` and `end` property stereotypes** (project-owner formalization supplied after this baseline).
