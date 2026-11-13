# DirectKG executable development tests

Wave 1 — Executable foundation, input policies, and general identity — received
the forwarded independent OK for `7364ed8843c565592d4bfa550d90c218988c83ba`.
Wave 2 — Classes, enumerations, higher-order classification, and source text —
received the forwarded independent OK for
`196d16b056668f3292e8309d545e6aaa49c90497`, verified reachable from remote main.
Wave 3 — Attributes, datatypes, property references, and source flags — received
the forwarded independent OK for `f915ba0a3aaee70588fe115d23d992242180c226`,
verified on remote main before Wave 4. Wave 4 — Ordinary relations, named inverses,
and relation hierarchies — received the forwarded independent OK for
fe3eba9f46612f927c74edf52a62cdee6cb69365, verified reachable from remote main.
Wave 5 — Derivations, material-chain interactions, mereology, and non-representation —
received the forwarded independent OK for `786c91b8f8e446d8d67709c79f8923d600204056`,
verified reachable from remote main. Wave 6 — Metadata, provenance, CLI delivery,
and interface parity — received the forwarded independent OK for
`5076be06f1f3c21e408abbed385ef93985794f44`. Its effective-configuration
recording correction received the forwarded independent OK for
`7d1035cc746bbe381a4c0b436012fd07b8b97721`, verified on remote main.
All six waves and their latest corrections are accepted. Baseline generation is
complete within the accepted testable scope; unresolved specification questions
and historical production-execution limits remain explicitly recorded below.
Incremental RD-02 — Minimal opaque source identifiers, Alternative A — follows
the explicitly accepted formalization and corrected structure attachment supplied
by the project owner. Its test change is submitted for independent review.
Behavioral baseline: [`documentation/specification/2026-10-21 - specification handoff.md`](https://github.com/pedropaulofb/ontouml-directkg/blob/7870042a02e094dca772d6fdd6570ad7b2d02578/documentation/specification/2026-10-21%20-%20specification%20handoff.md)
at `7870042a02e094dca772d6fdd6570ad7b2d02578`.
Organization: [`documentation/specification/2026-10-21 - test suite structure.md`](https://github.com/pedropaulofb/ontouml-directkg/blob/7870042a02e094dca772d6fdd6570ad7b2d02578/documentation/specification/2026-10-21%20-%20test%20suite%20structure.md), same commit.
The single requirement-to-test inventory, source evidence, exact data pairings,
and remaining scope are in [`coverage.md`](coverage.md).

## Current agent workflow

The [active role prompts](../documentation/prompts/README.md) govern new assignments: Architect registration and Architect Reviewer OK, parallel documentation/testing assessments and their reviewer OKs, then implementation informed by accepted tests and its independent review. No-change assessments also require review. Retrieve current authoritative files from [documentation/specification/](../documentation/specification/) directly; historical baseline links, supplied-source references and execution records below describe their original reviewed work rather than a requirement to upload files today. Test-artifact acceptance does not certify passing production execution.

## Run from the repository root

Use an isolated Python environment if desired. The observed environment is
Python 3.12; this does not establish production Python-version support.

```bash
python -m pip install -e . -r tests/requirements.txt
python -m pytest --rootdir=. --collect-only -q tests
python -m pytest --rootdir=. -q tests -k 'fixture_contract or rdf_helper or existing_mereology_vocabulary'
python -m pytest --rootdir=. -q tests --tb=short
```

For a focused run, replace `tests` with a repository-relative module or node
listed in `coverage.md`, keeping `--rootdir=.`. Running inside a test subdirectory
is not the supported convention. No pytest configuration is currently needed.
tests/requirements.txt contains test dependencies. Bound conversion/process tests
also use the actual package from pyproject.toml; fixture/helper checks remain independent.

The fixture/harness subset runs independently of production. Intentionally
invalid source files are checked against their declared defects; one malformed
JSON file is expected not to parse. These passes do not certify transformation
behavior. Ten Turtle files are partial ground-triple expectations; one additional file
is an ordered-chain expectation with an anonymous inverse expression. None is a
complete conversion output. Pairings are explicit; integrity scans never infer
input/expectation pairings from filenames or directory order.

Cross-topic inputs use `shared/base_iri` and `shared/property_collisions`.
The canonical `shared/core_model` bundle contains both `input.json` and its
partial ID-mode `expected.ttl`; consumers select them explicitly. These files
were promoted under structure §8, with existing harness node IDs retained.
Wave 2 adds four class bundles, one higher-order bundle, and
`shared/source_text`, which is consumed by both ontology and shared-text tests.
No labels-only data directory is needed. Explicit small mutations, including
localized text and governed invalid cases, stay in their owning test modules.
The literal-fallback matrix includes a supported localized name whose every
value is unusable for naming; both source labels remain, and fallback does not
make enumeration closure incomplete.

Wave 4 adds canonical `shared/binary_relation` input/partial graph data from
its first use across relation and inverse topics. `shared/omitted_connector`
contains the byte-identical input promoted from the property topic when inverse
behavior began consuming it; all consumers/pairings and its old harness ID are
preserved. The material-naming and relation-hierarchy bundles stay under
`relations/`; the secondary inverse-collision bundle stays under `inverses/`.
No existing attribute JSON is newly reused across topics.

Wave 5 adds shared/material_pattern/input.json from its first use across
relation and property topics. Its relation-only expectation stays at
relations/material_pattern/expected_chain.ttl, explicitly paired across bundles
for the default relator geometry under ID mode. The chain-constraint input remains relation-owned. Wave 6 promotes the byte-identical
instantiation input to shared/instantiation/input.json because CLI now consumes it;
all higher-order and contract consumers use that canonical file and retain their node IDs. Existing reused data
was already canonical shared data; no further promotion is needed.
The existing vocabulary now lives at vocabulary/latest/dkgm-vocabulary.ttl and
vocabulary/versioned/dkgm-vocabulary-v0.1.0.ttl, with 0.1.1 also covered.
Tests read these paths
without modifying them; the plan's older root-resource pathname is not copied
or restored. Those resource checks test the accepted exact ontology IRI
`https://w3id.org/directkg/vocab/dkgm`, its `U#` namespace, version IRIs and axioms.
External redirect behavior remains separate.

## Actual invocation binding

**RD-02 scoped binding:** inspected against production at
`f9b55c997e5e3e0ed001d2231774d1a225599b7a`. The adapter calls the actual public
`ontouml_directkg.convert(source, **options)` and retains its native ConversionResult,
ontology, outcome and all produced diagnostics. Public result reads use that
object's actual attributes. Omitted controls stay omitted; the semantic positive
stereotype_relation_naming control maps to the inspected negative Python parameter.

The CLI binding runs the real `sys.executable -m ontouml_directkg` subprocess
with --output and --diagnostics-file. It requires fresh destinations and an explicitly
requested report, then reads the actual report and delivered Turtle. It never
reruns Python to manufacture CLI observations. read_report uses the actual shared
export_report/Diagnostic/SourceLocation format and retains raw decoded JSON and
those inspected format-definition objects; no JSON schema identifier is invented.

Native diagnostic severity, source IDs/types and generated IRI are copied from
actual fields; message and effect are retained together. Reported IDs also supply
identified_sources. The inspected code/category mapping is:
MISSING_SOURCE_ID/INVALID_SOURCE_ID → missing_id/invalid_id;
FAILED_RELATION → failed_relation; DUPLICATE_SOURCE_ID → duplicate_id;
UNTRANSFORMABLE_ENUMERATION_VALUE → invalid_enumeration_value;
ABSTRACTNESS_ANNOTATION → abstractness; MISSING_CLASS_NAME/MISSING_NAME → missing_name;
GENERIC_ID_FALLBACK → generic_id_fallback;
MISSING_STEREOTYPE/UNRECOGNIZED_STEREOTYPE → missing_stereotype/unrecognized_stereotype;
UNKNOWN_INFORMATION → unknown_information; UNPROCESSABLE_DOCUMENT → unprocessable_document.
Facts come only from actual wording and locators: aborted effect; competing-declaration
wording with at least two reported sources; annotation preservation; no additional
logical enforcement; missing descriptive name. Raw native events are retained.

For the F1 correction, console severity is read from actual captured stdout and
stderr records, recognizing the inspected bracket headers and colon headers
(such as ERROR:). Each event retains its raw bytes and originating stream.
No event or severity is inferred from JSON reports, exit status or source inputs.
Only severity, message and raw evidence are bound on console events; accessing
category/source/fact details raises ImplementationUnavailable.

Unmapped diagnostic meanings, fault injection, detailed console normalization,
existing-destination delivery and other protocol operations remain explicitly
unbound. Observation fields without actual readers raise ImplementationUnavailable
instead of exposing dataclass empty/false defaults. The contract below describes
remaining bindings; RD-02 does not claim full-suite execution or complete adapter
coverage. No skip, xfail, fake transformer or expected graph supplies observations.

`tests/support/invocation.py` remains the only implementation-dependent boundary.
Its protocol/dataclasses are test-side formats, not production API requirements.
Extend bindings only from inspected real interfaces.

The binding must execute the real public library and adapt only observed values:

- Leave omitted controls omitted. Test-side option names express semantic
  requests; they do not select Python production parameter spellings.
- Preserve every produced diagnostic and its original payload (`raw`), including
  repeated events and diagnostics produced before abort. Do not infer events,
  locators or facts from source inputs or expected behavior.
- Keep IDs explicitly reported by diagnostics in `source_ids`. Populate
  `identified_sources` with canonical source IDs only by resolving an actually
  reported locator unambiguously against the actual source. A reported name,
  path, native element reference, or ID can identify an affected declaration;
  this normalization must not assume which declaration a test expects. Generic
  missing-name and extensionality checks accept this identification without
  demanding a literal source ID in the diagnostic. Class-fallback and duplicate-ID
  assertions retain their separately required explicit-ID checks.
- Normalize actual diagnostic meanings to the test-side `kind` values used in
  tests: `placeholder_base`, `missing_name`, `ordinary_id_use`,
  `owner_qualification`, `unknown_information`, `duplicate_id`,
  `missing_stereotype`, `unrecognized_stereotype`, `semantic_validation`,
  `omitted_package`, `omitted_diagram`, `omitted_custom_assignments`, and
  `ambiguous_language`, `extensionality`, `abstractness`, `derived_status`,
  `singleton_completeness`, `empty_generalization_set`,
  `enumeration_values_unavailable`, `generic_id_fallback`, and
  `omitted_description`. These are semantic categories, not demanded production
  codes. The real binding must document how actual codes/fields/messages map to
  each category and retain evidence for review.
  Wave 3 adds `void_datatype`, `missing_cardinality`, `invalid_cardinality`,
  `redefinition_warning`, `ordering`, and `multilingual_primitive_conflict`.
  Their names are test-side readings of actual diagnostic meaning. The last
  category is used to reject an invented conflict, not to require a diagnostic.
  Wave 4 additionally reads `relation_naming`, `stereotype_naming`,
  `comparative_naming`, `unavailable_grounding_relator`, `relator_naming`,
  `inverse_omission`, and `relation_set_completeness`. These classify actual
  message/report meaning, never prescribe production codes or manufacture an
  event from the input. `invalid_cardinality` includes actual lexical/type
  multiplicity errors. Independent abstractness/derived INFO must not be
  mistaken for relation-naming or inverse-omission events.
  Wave 5 reads chain_ambiguity, chain_compatibility, unsupported_connector,
  derivation_omission, orientation_repair, comparative_derivation_semantics and
  discarded_instantiation_data. These are semantic readings of real events;
  nonfatal comparative/mode ambiguity notices need not have a fixed spelling
  or severity beyond INFO/WARNING. Relator-component ambiguity and unsupported
  resolved connectors retain their expressly required WARNING severity.
- Test-side diagnostic `facts` describe actually reported content. Wave 1 checks
  `placeholder_namespace`, `not_recommended_for_publication`,
  `stereotype:category`, `competing_declarations`, and `conversion_aborted`.
  No exact diagnostic English wording is required. Do not manufacture a fact
  merely because the source or test request makes it true.
  `competing_declarations` specifically requires actually reported locating
  information for the competing declarations; `conversion_aborted` requires
  the reported abort effect, not merely inference from the observed outcome.
  Wave 2 additionally checks `no_values_available`, `closure_omitted`,
  `extensional_equivalence`, `distinct_identifiers`, `preserved_as_annotation`,
  `not_logically_enforced`, `no_derivation_rule_supplied`,
  `essential_parthood_not_enforced`, `missing_name`,
  `multiple_project_languages`, and `language_unresolved`. A produced claim
  that abstract-stereotype disjointness was omitted is represented by
  `stereotype_disjointness_omitted`; tests reject that claim in this context.
  None of these spellings is required in production messages or JSON.
  Wave 3 additionally reads `void`, `range_omitted`, and
  `ordering_not_represented` from actual messages/fields, never from expectations.
  Wave 4 reads `coverage_not_represented` for the actual multi-member relation-
  set coverage explanation; singleton INFO reuses the established equivalence
  and distinct-identifier meanings.
  Wave 5 additionally reads ambiguous_correspondence,
  same_class_occurrences_unassigned, no_accepted_endpoint_mapping,
  not_dl_guarantee, omission_policy_applied, constraints_preserved,
  possible_owl_dl_incompatibility, cardinalities_omitted and
  property_disjointness_omitted. Preserve erroneous claims too, including
  all_chains_outside_dl, all_semantics_preserved, global_dl_guarantee and explicit_derivation_omitted,
  so negative checks inspect actual output. Instantiation category meanings are
  discarded_identifier, discarded_association_name, discarded_role_names,
  discarded_multiplicities and discarded_characteristics (including a discarded
  source description); association_data_not_materialized records the reported effect.
  None prescribes a production field or exact phrase. The actual source ID and
  available type must remain observable for the consolidated instantiation warning.
- Populate `Observation.comments` by reading the meanings of actually produced
  RDF comments for `isAbstract`, `isDerived`, `isExtensional`, and the `abstract`
  stereotype. Each `CommentMeaning` retains its exact RDF subject and literal;
  tests verify that triple before checking field/value. Aggregate comments may
  express multiple meanings. Preserve every relevant meaning, including an
  erroneous value or misplaced comment, so absence/placement checks are real.
  Never fill these observations from source flags, expected data, or requested
  controls. This test-side normalization avoids imposing an invented English
  template where the specification fixes only meaning. The binding must
  document its actual text/field interpretation for review. Fixed classifier-
  order comments are checked directly as RDF literals instead.
  Wave 3 also reads `isReadOnly`, `aggregationKind` (SHARED/COMPOSITE), and
  `isOrdered`. `CommentMeaning.context` records actually expressed occurrence
  context: `relation`, `source_end`, `target_end`, `attribute`, or `class`.
  A comment about both ends may produce two meanings with the same literal.
  Do not infer an end's context merely from which input flag is true: the
  produced comment must distinguish the occurrences. Attribute tests permit
  an implicit context where the property target already identifies it.
- Populate `Observation.project_description_output` with actual RDF statements
  representing source `Project.description` annotations and
  any text presented as a replacement for missing source-project description,
  including erroneous empty or fabricated fallback text. Do not classify
  independent generated metadata (for example modeled-class-count comments) as
  a source description merely because it uses `rdfs:comment` on the ontology.
  The positive project-description cases require the observed source-annotation
  evidence; omission cases require its absence while allowing independent
  metadata. A future real binding must document this interpretation from actual
  output/interface evidence, never assume absence from the input or expected
  outcome. The harness checks the assertion with explicit RDF/meaning samples;
  it does not simulate a conversion or certify the unimplemented reader.
- Populate `Observation.restricted_to_output` by reading the actual RDF for any
  statement expressing restrictedTo/nature information, including comments,
  other annotations, logical axioms, or auxiliary-resource statements. Retain
  the actual triples, including erroneous output. This is a test-side semantic
  reading, not a requested production attribute or a predicate spelling. Do
  not infer an empty result from the source field, the requested policy, or
  its expected omission. Document how actual output meanings are recognized;
  do not attribute unrelated reliable metadata to this field. Omission cases
  assert this evidence is empty while separately checking required mappings.
- Populate `Observation.flag_semantic_output` with actual prohibited logical
  or sequence output induced solely by GEN-05/CLS-01/PROP-04/05 characteristics, such
  as extra logical axioms, dependence, direction changes, value-order sequences,
  or properties generated solely to represent a flag. Exclude independently
  required mappings and permitted independent metadata. Document the actual
  RDF/interface evidence; never infer absence from the expected behavior.
- Read `relation_label_origin_output` from actual RDF statements/auxiliary
  resources serving solely to distinguish generated primary labels from source
  labels. Exclude independently permitted metadata/provenance.
- Read `relation_completeness_output` from actual multi-member coverage axioms
  or substitute validation structures. Exclude required hierarchy/disjointness
  and descriptive annotations; retain erroneous output for negative checks.
- Preserve actual element-level entries about intentional inverse omissions in
  `inverse_omission_reports`, including non-diagnostic native report entries.
  Required structural/mapping notices are separate. Neither this collection nor
  the semantic RDF collections above may be presumed empty from expected rules
  or requested controls. Document actual interface/RDF evidence for review.
- Populate mereology_import only from actual core-vocabulary interface or
  publication evidence, never from an expected URI or an arbitrary import.
  Populate provenance with the actual separately exposed Python graph when
  available; embedded provenance remains in ontology. The Wave 5 sidecar
  requests examine programmatic graph content only, not file delivery.
- Read unrepresented_connector_output from actual connector representations,
  including anonymous resources, reification, punning and grounding annotations.
  Read comparative_semantic_output from actual additional comparison rules,
  chains, equivalence, counts or characteristics induced solely by that
  derivation. Exclude independent accepted endpoint/property mappings.
- Read discarded_instantiation_output from actual RDF, provenance and native
  diagnostic evidence that reproduces discarded values or their characteristics.
  Include copied booleans/flags whose meaning string searching cannot establish;
  exclude diagnostic category names and permitted source-ID locators. Retain
  real diagnostic payloads in raw. Source names/roles/multiplicity sentinels are
  also checked directly across RDF and diagnostic payload text.
  These three new semantic readers default to None, not an observed empty
  tuple. A real binding must explicitly observe an empty tuple when appropriate;
  it cannot presume absence from the requested configuration or source data.
- Bind `has_relation_cardinality_control(feature)` to the actual public Python
  control surface for the semantic questions `omit_without_named_inverse` and
  `qualified`. These are test-side feature terms, not production spellings;
  unavailable inspection raises the integration error. CLI inspection is Wave 6.
- Bind `has_local_value_restriction_control()` to inspection of the real public
  Python controls for an optional local allValuesFrom feature. It is a test-side
  question, not a proposed production method or parameter spelling. The CLI
  counterpart is implemented in Wave 6. An unavailable interface must raise the
  integration error rather than answer from the specification.
- Read diagnostics, outcome, and delivered graph through the actual public
  result/access mechanisms when the tests request another read. Do not return
  a cached test snapshot in place of the real access operation.
- Preserve the actual programmatic configuration-rejection signal separately
  from conversion outcomes. Do not treat missing integration as an expected
  configuration error, derive outcomes by counting severities, hide a publicly
  delivered aborted graph, or synthesize a graph from RDF expectations.

Most graph-focused requests explicitly select a supplied base and
`provenance=none` to isolate their scoped behavior. Other controls remain omitted
unless selected by the case. Wave 6 adds default embedded provenance, explicit Python serialization/file delivery,
and actual CLI-process assertions. Every such integration remains unexecuted until
the real binding is available; fixture/helper passes do not certify them.
Stored expectations are partial ground graphs or the explicitly paired ordered
chain pattern. The generic property_chains reader retains list order and reads
anonymous inverse expressions without inference. Checks between separate
conversions compare explicitly selected domain predicates, including required
source labels/identifiers, without demanding repeatable optional metadata or
unfixed generated-comment wording. The allowed pairwise disjointness directions
are compared as unordered pairs. The identifier-opt-out test removes only its
identified RD-28 annotations from the expected projection. Whole-graph isomorphism
is used for serialization round trips and diagnostic-access non-interference
within one execution. No triples are deleted from observed production results.
Enumeration closure and class-set unions are inspected as actual RDF
collections with unordered membership; `rdf_list` rejects broken/cyclic lists.
Enumeration inequality requires `owl:AllDifferent`, accepting either standard
`owl:members` or `owl:distinctMembers` lists. Multiple AllDifferent groups may
establish the required unordered pairs. An equivalent anonymous enumeration
expression is also accepted. No inferred OWL fact substitutes for an assertion.
Harness checks of these assertions use explicit small RDF graphs and receive
no conversion-coverage credit.

Wave 3 reads cardinality restrictions only from asserted subclass conditions,
including explicit intersections. It accepts unqualified attribute counts or
qualified counts using the declared range or the applicable universal range,
and the accepted equal-count alternatives (including maximum zero). It does
not impose the relation-only cardinality serialization on attributes. RD-14
property expressions are inspected as actual named properties or explicit
anonymous inverses; no entailment supplies an expected inclusion.
Primitive XSD targets omit source-derived-status comments; independent generated
metadata under DK-GEN-11 is permitted. The primitive flag check reads actual
comment meanings rather than prohibiting every `rdfs:comment` on that IRI.
Primitive normalization recommendations remain SHOULD: their safety tests
allow custom treatment when a recommendation is declined and forbid a wrong
registered target. They do not certify compliance with the recommendation.

Wave 2's corrected comparisons can also select named subjects and logical type
objects, leaving unrelated descriptive resources/types unconstrained. They
compare flag-comment meanings with actual RDF evidence, not raw wording. The
enumeration omission case checks membership/closure independently so allowed
enumeration-expression presentation is not frozen across conversions. The
project-text cases compare required identity and class mappings, permitting
additional metadata under DK-GEN-11. Name-mode properties with unique candidates
are located through their default source-ID annotations and checked through
their domains/ranges and labels; they need not use the optional direct name.
Attribute selector cases introduce a second same-named property on a distinct
owner, making owner qualification mandatory and its exact construction testable.
ID-mode identity checks require the own-ID IRI and source labels while rejecting
the source-ID traceability annotation prohibited by DK-IRI-09.

Use `tests.support` absolute imports. Data paths resolve from this suite, not
the caller's current directory. Source mutations and converter artifacts belong
in pytest temporary locations. Never overwrite stored expectations or write
runtime reports/caches into `tests/fixtures/`.

## Placement and unresolved matters

No test-path exceptions are introduced. The structure document's canonical
relocation is deferred: the governing Test Engineer instruction prohibits
specification changes. Its current repository copy is read without modification.

The project-owner identity decision of 2026-10-24 fixes the stable DKGM URI to
`https://w3id.org/directkg/vocab/dkgm` and retains `U#` for terms. Import and
bridge assertions now require that exact identity; the three existing Turtle
representations are checked independently of production. These assertions do not
certify unavailable converter behavior or live HTTP resolution. Detailed
vocabulary/bridge checks and approved wave obligations remain in the inventory.
All six waves and the latest configuration-recording correction have
their applicable forwarded OKs; no wave remains under review.

D3/A4's reviewed existing-authority derivation resolves the historical standalone
attribute `*` coverage blocker. The supported exporter supplies bounds (0,
unbounded); DK-ATT-03 contributes no cardinality restriction. DK-DIAG-11 governs
recognition/normalization, while DK-REL-12 remains relation-specific. Exact empty
assertions now remain test-first at the native implementation guard; historical
execution results below retain their original meaning.

A1.1/A1.2 now resolve the former exact-name blockers for present-but-unusable
inverse roles and unusable inverse-domain qualifiers. Their exact naming,
eligibility, labels, direction and source-backed identity are asserted in the A1
increment below; current production guards remain visible test-first failures.
A2 now resolves the earlier role-selection questions in DK-REL-04. The four
part–whole families use a unique explicit SHARED/COMPOSITE occurrence; historical
semantic naming uses endpoint fallback; externalDependence uses exactly one
explicit mode and the complete approved non-mode endurant set. The existing
30 table IDs now have exact expectations. Source labels remain lexical text,
not semantic-role discriminators; aggregation never changes primary direction
or DK-REL-19's bridge. Native selector guards remain visible production failures.

Wave 4 reviewer correction F1's official mode encoding remains under
require-known for positive cases. No intrinsic/extrinsic aliases are introduced.
A2 also adds explicit ambiguous/unsupported inputs, both marker kinds and orders,
all-policy nonfatal fallback, ignored hints and both-strategy label/control cases.
F2 preserves specific-property disjointness when the general relation or its
reference fails, independently of the correctly omitted hierarchy edges.

Relation counts require the exact unqualified forms in REL-10/11, including one
exact restriction for equal numeric bounds; they do not reuse the looser
attribute alternatives. Named inverse assertions require explicit reversed
domains/ranges and exactly one inverse-to-primary axiom without its reciprocal.
Pairwise property disjointness is compared without fixing statement direction.
Public-control inspection and the new semantic/report readers remain unexecuted
until the real interface is bound; helper passes do not certify them.


## Metadata, provenance and process binding

Wave 6 adds `tests/cli/test_cli.py` at the approved location. Seven reviewed YAML
inputs are canonical under `tests/fixtures/shared/external_metadata/`: the root
`metadata.yaml`, plus `metadata/{ignored,nulls,empties,empty_mapping,root_list,partial_invalid}/metadata.yaml`.
These are purpose-authored selected Catalog-field inputs, not full Catalog records.
Both ontology and CLI behavior consume them. The relation-only and metadata-only
expectations remain in their owning topic bundles. The partial
`tests/fixtures/transformation/ontology/external_metadata/expected.ttl` is explicitly
paired with shared/base_iri/input.json and shared/external_metadata/metadata.yaml;
its eleven triples fix external enrichment only, not the complete ontology.
Malformed YAML, missing/unreadable files and unsupported-format paths are created
only in pytest temporary directories. No intentional malformed YAML is committed.
The existing VP-plugin 0.5.3 provenance/format evidence in the inventory remains
applicable to reused JSON and reviewed runtime mutations; no exporter support is added.
PyYAML is pinned in tests/requirements.txt for test data/configuration reading.

The expanded protocol in support/invocation.py still prescribes no production API.
Bind every operation to the inspected public library or real CLI entry point:

- `cli` must run a real subprocess, retain its actual argv/return status and raw
  stdout/stderr, and read actual console/report/output evidence. Do not run a
  second Python conversion to populate missing CLI observations. Where failure
  removes a public file, real instrumentation may retain the actual conversion
  result/operations; it must not infer outcomes from expected codes or severities.
- `serialize` calls the actual public ontology/provenance serialization capability.
  `deliver` calls actual explicit public file delivery. The binding must not supply
  production eligibility, sequencing, fallback modes or failure precedence itself.
  Capture pre_delivery_ontology from actual I/O interception after successful
  serialization/provenance construction. Failure comparisons use that graph,
  permitting independent metadata generated during normal output work.
- `export_diagnostics` is the separate real Python operation; `read_report` retains
  parsed JSON, every event and outcome, plus the actual shared schema/format
  evidence validated against those bytes. Optional JSON members may differ between
  instances. Equal normalized diagnostics alone cannot manufacture schema equality.
- `inspect_controls` reads real help/signature/public-definition evidence. Its
  semantic defaults account for actual flag polarity; only Python relation_labels
  is required to have that precise spelling. Version evidence comes from the real
  software, independently of the provenance's observed softwareVersion value.
- A `Fault` is a test-side interception directive, never a production CLI/API option.
  Bind it only to a real implementation operation or standard I/O, including actual
  child-process operations. Record raw triggered-operation/error evidence. Do not
  replace the converter, pre-return expected outcomes or add application fault hooks.
- Provenance roles identify actual source/configuration/output/execution and DirectKG
  software resources. Include erroneous metadata-use claims; a requested but unread
  file entity without a successful-use claim is not classified as used metadata.
  Do not confuse other associated agents/activities with the generating DirectKG run.
- Read configuration_literal from the actual designated prov:value, parse that YAML,
  and normalize only settings it really records into configuration_controls. Never
  fill missing settings from the request, expected defaults or fixtures. Actual
  filename/format evidence must retain produced RDF triples, and checksums come from
  actual SPDX structures. SPDX terms were checked against https://spdx.org/rdf/terms/.
- New omission/evidence fields must be explicitly read, not presumed empty. These
  distinguish external contributions, independent metadata, transformation provenance,
  output-artifact/configuration information, DirectKG metadata predicates, actual
  diagnostic/sidecar writes and advertised valid artifacts. Existing unbound None
  values cannot satisfy their negative assertions. Retain actual native failures.

RD-05 file-only input supersedes the former conditional in-memory-input clauses:
all transformations require a concrete source file, regardless of provenance mode.
Programmatic ontology/provenance graphs remain supported outputs. Stdout clauses
remain conditional on observed capability; no stdout syntax is invented and an
unbound inspection cannot pass. Automatic sidecar writing needs a concrete output
path. No additional rejection classification is imposed on excluded input forms.
I1 Alternative A now resolves mixed-list recovery: every valid sibling must survive
under best-effort. The inventory records the replacement assertions, native
metadata-emission binding and unresolved production guard separately.

Graph checks isolate known source roots/types/predicates across separate executions,
normalize only permitted unordered disjointness pairs, and follow selected blank-node
connections for lists/restrictions. Serialization within an execution compares the
entire observed graph by isomorphism. Named activity IRIs are comparable across runs;
blank-node labels are graph-scoped. Optional metadata, comment wording, prefixes,
statement order, whitespace and Turtle bytes are not frozen. Configuration YAML
repeatability and checksums over actual bytes are checked separately.

The following reconciliation results are historical baseline evidence. Run
available checks from the repository root using the commands above. The
inventory records collected cases, independent passes, unavailable integration
failures, conditional branches and unresolved normative limits. Final reconciliation
on 2026-10-23 verified all 2425 collected node IDs, 59 fixture paths, prescribed
test locations and applicable review approvals. The independent subset passed
90 checks: 88 fixture/helper checks and two existing-vocabulary checks. The baseline
full run on the reviewed test contents passed those same 90 checks and failed
2335 cases exclusively with ImplementationUnavailable, with no errors or skips.
No test defect remains identified. These results complete baseline generation
within the accepted testable scope; they do not certify production behavior or
resolve the recorded Architect questions. Binding the real implementation and
testing later accepted decisions belong to subsequent work.

## RD-02 execution evidence

No stored fixture changes. Complete existing models are mutated in their topical
modules. write_input's opt-in ensure_ascii=True passes escaped lone surrogates
through JSON to production, rather than failing in test setup. Fixture checks now
reject non-UTF-8-encodable IDs without normalizing valid opaque strings.

The decision selection passed 129 cases, including 24 existing failed-end cases;
104 additional regressions and 91 independent checks also passed. Collection
found 2531 nodes: all 2426 baseline IDs and 105 new IDs, with none removed.
Exact commands, branches and fixture paths are in coverage.md's RD-02 section.
The execution environment was interrupted and restored; focused tests and
collection were repeated after restoration. No full-suite run is claimed.

F1 corrects the six CLI error-case parameters' unsupported literal-prefix/stream
assertion. They now require an observed ERROR event through the adapter. Outcome,
report and ontology assertions, all node IDs and fixtures are unchanged.
The first submission at 29bf885cdf6390aafdd07a54d1e71988e1b54fc9 received NOT OK;
the F1 correction at e9b608894985dab43abb46a6bedca7d91c5b9652 subsequently received the forwarded independent OK. RD-02 is closed.


## RD-17 relation additions: test-first execution

The accepted five-addition decision is submitted as one increment under the existing
structure. No production/specification/vocabulary changes or new stored fixtures.
Coverage and exact nodes are in coverage.md's RD-17 section; nine canonical
aggregation rows there now describe mediation asymmetry independently of flags.

The actual file-conversion binding additionally interprets the inspected production
MATERIAL_CHAIN_COMPATIBILITY, MATERIAL_CHAIN_AMBIGUITY and EXTENSIONALITY_ANNOTATION
codes. Facts are read only from actual messages/effects and sources; raw native
events remain available. This extends diagnostic adaptation only. No new public
API, transformer, OWL simplicity evaluator or empty advanced-evidence default is
supplied by the adapter. Advanced readers remain unavailable as documented above.

Initial submission validation with Python 3.12.14 and pinned requirements found 2612 nodes: 81 new
cases and nine necessary aggregation-function node renames. The focused command
in coverage.md executed 90 cases: 14 passed, 76 failed at missing RD-17 addition
assertions in the current transformer. All reached baseline RDF preconditions
passed. The previous combined 324-case regression selection passed. No skips or
xfails were introduced; the full suite and remaining unbound capabilities were not
executed. These are valid test-first production failures, not an accepted review
verdict or a passing implementation claim.


### RD-17 F1/F2 correction

Initial submission 4b91d83661b2071cfc205671b7bd3f93275f1978 received NOT OK.
The same decision is resubmitted after narrowing aggregation equality to rooted
logical RDF (allowing independently generated descriptive metadata) and adding
one source-mereology preservation pattern in both chain-enabled modes. The
existing source asymmetry must survive actual non-simplicity; established
cardinality omission/preservation remains independently asserted. No adapter,
RDF-helper, fixture or production change is needed.

Collection now contains 2614 nodes: the previous 2612 are unchanged, plus two
preservation parameters. Changed cases: 8 passed and 3 existing production
failures; expanded decision selection: 16 passed, 76 production omissions;
previous combined regression selection: 324 passed. Six timestamp-variation
observations passed; six logical-change and two asymmetry-removal negative
controls failed at the intended assertions. Exact nodes, fixture paths, commands
and limits are recorded in coverage.md's F1/F2 subsection. Full suite and unbound
capabilities were not executed. This is submitted for independent re-review,
not accepted.


### RD-17 F3 correction

The reviewer confirmed F1/F2 resolved but rejected b04d3215884af60fbef52a7507e70be85a08278f
for missing newly generated domain properties in the bounded logical comparison.
Its nine aggregation parameters now include every subject of incoming domain/range
statements to either modeled class, without filtering property names or namespaces.
Selected logical output is still compared isomorphically; independent metadata
may vary. Existing direction, bridge and asymmetry assertions remain unchanged.

The same 2614 nodes are collected. Expanded RD-17 results remain 16 passed and
76 production omissions; the previous 324-case regression selection passes.
The demonstrated extra-property insertion now fails all nine parameters at the
comparison. Domain-only, range-only and anonymous variants each fail six; timestamp
variation remains allowed. Prior logical-restriction and F2-asymmetry controls
remain sensitive. Exact evidence and inventory entries are in coverage.md's F3
subsection. No fixture, adapter, helper or production change; independent verdict
pending. Full suite and unbound capabilities were not executed.


## RD-18 boundary-stereotype comments

RD-17 is closed with independent OK for 24676f1e383e04ee452a2c55b1f2ade02ff619e3.
RD-18 is one test-first increment, submitted for independent review. The accepted
formalization was cross-checked against DK-PROP-06 in the 2026-10-29 consolidated
specification; it introduces no prose-template requirement. Tests remain in the
existing properties module and reuse properties/source_flags without stored-data
changes. The inventory records 46 new cases and exact rule/parameter/fixture links.

The test-side read_property_stereotype_comments operation audits actual RDF.
Current production generates no boundary comments: the reader can verify absence
only for the inspected non-boundary comment forms. Unknown/new wording raises
ImplementationUnavailable until actual interpretation is bound. Positive English,
value and end-context expectations remain executable; no renderer is guessed,
no default empty result bypasses the audit, and no current positive preservation
success is claimed. English wording must be read from evidence; neither an exact
literal nor an exact language-tag spelling is prescribed. The general comments
reader remains unbound. Real conversion is unchanged; VOID_DATATYPE and
ORDERING_ANNOTATION interpretation now retains their actual event meanings.

The focused command in coverage.md ran 46 cases: 4 passed, 42 failed at missing
required boundary comments after successful mapping/diagnostic checks. Collection
contains 2660 nodes, preserving every previous node. The previous 324-case
selection passes. After refreshing intervening production commit d1aec3b67b7f7a0945e0d83608de0953bf7ac956, all 92 selected RD-17 cases pass; its expectations are unchanged. Additional
typing regressions gave 77 passes and 6 existing execution limits (3 unbound
MISSING_CARDINALITY reads; 3 deferred standalone attribute '*'), plus two existing
RDFlib namespace warnings. Exact commands and limitations are in coverage.md.
No full-suite pass, new production behavior or reviewer OK is claimed. Rule 6's
website explanation belongs to the Documentation Engineer in the current workflow; this recorded test increment made no site/spec edits.

Temporary actual-output controls additionally verified that independent timestamps
and metadata individuals are allowed, extra incoming domain properties are
rejected, permitted count syntax is accepted, and extra constraints on count
nodes are retained by the comparison. Unknown comment interpretation remains an
explicit binding limit; no positive comment evidence is synthesized.


## Incremental RD-17 — historicalDependence, Alternative A

This distinct RD-17 decision adds 13 relation parameters; it does not replace the
earlier five-axiom RD-17 increment or reopen RD-18. Exact nodes, branch rules and
fixture pairings are in coverage.md. Reused complete inputs remain at
shared/binary_relation and relations/hierarchy; no fixture promotion or new stored
data is required. The already approved RD-18 test commit is
`f45b1a09a72474146c6a735f13083001bce5ce18`.

The adapter still calls real public conversion. It now interprets the inspected
native RELATION_NAMING and MISSING_RELATION_NAME events, retaining their raw
payloads. The required historical limitation WARNING has no produced native
rendition yet: `unmapped_relation_stereotype` is a test-side semantic kind, not a
proposed native code. No generic naming warning or input-derived event substitutes
for it. Unknown native diagnostics remain explicitly unavailable.

The scoped historical annotation reader audits actual RDF and actual source
descriptions, including descriptions that mention historicalDependence. Known
independent flag and RD-18 comments are read as such. Unknown comments, predicates,
annotation structures or auxiliary labels raise ImplementationUnavailable. Empty
results therefore require inspected evidence; positive historical annotation
forms and uninspected metadata forms are not guessed. Existing all-comment and
RD-18 positive-meaning readers remain unchanged. Logical comparisons include
incoming domain/range subjects without namespace filtering, blank-node
constraints and newly declared logical resources, allowing independent metadata.

Production advanced during this increment to
`39e2a4b3a10845e9809c5d43a08b4a12fe69a746`, adding begin/end comments. Those changes
were incorporated unchanged. The ordinary-mapping comparison includes both end
stereotypes, so their actual independent comments survive historicalDependence.

Observed with Python 3.12.14 and pinned requirements: **2673 collected**, all
2660 earlier nodes unchanged plus 13. New historical selection: **13 failed,
931 deselected**: ten missing limitation-warning assertions, after their earlier
checks passed; three existing production NotImplementedError branches for deferred
historical semantic naming. At that historical checkpoint the two-candidate semantic-direction bound was
retained; A2 below now resolves it with exact endpoint fallback. Existing mapping selection:
**51 passed, 35 failed, 858 deselected** (two deferred naming branches; 33 existing
adapter limits: 3 comparative diagnostic, 22 fallback-origin and 8 inverse-omission
readers). Earlier combined regression selection: **324 passed, 2349 deselected**;
earlier RD-17 axiom selection: **92 passed, 852 deselected**. RD-18 regression:
**4 passed, 42 failed, 163 deselected**; those 42 now encounter explicitly
uninterpreted produced begin/end comments at its unchanged positive reader,
rather than claim verified meanings. No RD-18 assertion was changed. These are
visible production/binding limits; no skip or xfail was added. The full suite and
remaining unbound capabilities were not executed.

Controlled observations of actual conversions accepted timestamp/metadata
variation and source-authored historical text, rejected seven logical mutations,
and raised explicit unavailability for four unknown annotation forms. No
conversion or positive warning was fabricated. All 17 Python files parsed; the
inventory exactly reconciles with collection and affected fixture references.

Run from the repository root:

```bash
python -m pytest --rootdir=. --collect-only -q tests -p no:cacheprovider
python -m pytest --rootdir=. -q tests/transformation/test_relations.py -k 'historical_dependence_' --tb=short -p no:cacheprovider
python -m pytest --rootdir=. -q tests/transformation/test_relations.py -k 'primary_naming_precedence or primary_labels_preserve or explicit_relation_generalizations_mirror or relation_counts_use_directional or historicalDependence' --tb=short -p no:cacheprovider
python -m pytest --rootdir=. -q tests/transformation/test_properties.py -k 'boundary_' --tb=short -p no:cacheprovider
```


### HistoricalDependence F1/F2 correction

The NOT OK verdict for `7e53a2392f4447b0cc68e5a72d40ceb168023483` identified
two test-side defects. Diagnostic preservation now compares observed normalized
severity, kind, facts and source/IRI information with event multiplicity; raw
messages remain inspectable and prose is not compared. The annotation reader
requires actual source-name evidence for class labels; an owl:Class type alone
no longer permits an unknown declaration label. Existing property fallback and
independent metadata interpretation remain unchanged. All 2673 collected node
IDs, fixtures, production interfaces and earlier assertions remain otherwise
unchanged; the 13 inventory entries describe the corrected evidence.

The same commands above reproduce **13 focused failures** (ten missing warnings,
three production naming guards), **51 mapping passes / 35 existing limits**,
**324 combined regression passes**, **92 earlier axiom passes**, and the unchanged
**4 RD-18 passes / 42 positive-reader limits**. All 17 Python files parse and the
inventory reconciles exactly. Alternative ordering prose passed the comparison
in all three ordinary cases while changed source/severity/meaning/multiplicity
still changed the signature. Injected declaration class labels raised explicit
unavailability in all three cases; actual authored class labels containing the
same words and generated property fallback labels remained permitted. Prior
metadata and logical/annotation sensitivity controls remained effective. These
are controls on actual observations, not fabricated conversion or warning
results. The full suite and remaining unbound capabilities were not executed.


## RD-05 Option B — replacement Rule 5

This decision adds nine cases (eight Python parameters and one CLI case) in the
existing ontology/CLI modules, all reusing shared/core_model. Exact rule, node and
fixture traceability is in coverage.md. Only replacement Rule 5 and its immediate
version-header/interface prerequisites are exercised; the unchanged version
validation/assignment rules are not claimed fully covered by this increment.

Current production at `7e17f613e270346da981a35c011222ae34df37eb` exposes no
version-IRI Python control and advertises no --ontology-version-iri CLI option.
The new semantic request option ontology_version_iri stops explicitly with
ImplementationUnavailable. It does not prescribe or forward a guessed Python
parameter. The identically named configuration observation key is semantic,
not a prescribed native YAML key. Positive binding requires actual interface
and output evidence when production supports the capability; existing provenance
and delivery readers retain their documented limits. Omitted controls and
unrelated tests keep their actual bindings.

Observed with Python 3.12.14 and pinned dependencies: **2682 collected**, all
2673 previous node IDs unchanged plus nine. Focused RD-05: **9 failed, 2673
deselected**, all at explicit unavailable version controls (eight Python, one
CLI). Assertions for supplied-version behavior remain test-first and unexecuted;
no positive conversion/configuration/checksum/reuse evidence is claimed. Actual
baseline resource extraction passed in six real conversions covering both IRI
strategies and all provenance modes. Combined regression: **324 passed, 2358
deselected**. Direct provenance selection: **1 passed, 12 failed, 381 deselected**,
all failures at existing unbound observations/operations (4 metadata-predicate,
4 provenance-role, 1 provenance and 3 delivery readers). All Python files parse;
fixture and inventory checks pass. No skip/xfail or structural exception is added.
The full suite and remaining unbound capabilities were not executed.

Run from the repository root:

```bash
python -m pytest --rootdir=. --collect-only -q tests -p no:cacheprovider
python -m pytest --rootdir=. -q tests -k 'ontology_version_iri_' --tb=short -p no:cacheprovider
python -m pytest --rootdir=. -q tests/transformation/test_ontology.py tests/cli/test_cli.py -k 'input_digests_use_exact_bytes or provenance_modes_keep_domain_output or explicit_delivery_places_sidecar or cli_sidecar_names_and_final_ontology_byte_digest or core_asserted_domain_graph' --tb=short -p no:cacheprovider
```


## RD-05 — File-only transformation input and exact-byte source checksums

Submitted for independent review; distinct from the closed ontology-version-IRI
Option B increment (`fe5515b6719e60ec518c48d08ee68c79ddceef00`). The accepted
file-only rules supersede the two conditional in-memory source cases. All other
existing nodes and their assertions are preserved. The existing canonical
`shared/base_iri/input.json` supplies complete VP-plugin 0.5.3 data; changed names,
byte layouts and rejected representations exist only in pytest temporary work.

The inspected public `ontouml_directkg.convert` still receives the caller's actual
source object. `attempt_source_input` retains a native TypeError/ValueError/OSError
or actual result; it never serializes, saves, coerces or rejects input itself.
The Python observation now reads the real separate `ConversionResult.provenance`
field; CLI observations still come only from subprocesses and actual artifacts.
Missing-source CLI invocations retain actual status and captured streams without
inventing a conversion outcome or requiring a diagnostics-report omission.

The source-artifact reader identifies actually used JSON entities from the current
producer's MIME-format evidence in the actual graph. The tests assert their
PROV/SPDX structure and SHA-256 of the bytes supplied to the real file conversion,
including differing whitespace/escaping and a change to the file after conversion.
No public RDF template for role recognition is prescribed. The source-surface audit
interprets the actual exported names, signature and parser actions; unfamiliar
entries/controls raise ImplementationUnavailable rather than earn absence credit.
No new checksum/source control, public signature, fault mechanism or transformer is
introduced. Existing broader provenance/configuration/delivery readers remain
unbound; this increment does not claim to complete them.

Validation for this increment: **2711 collected**, with 31 additions and two
superseded conditional nodes removed; every other existing node and test function
body is unchanged. The new selection passed **31/31**; the combined accepted
regression selection passed **324/324**. Direct provenance/version/delivery
regressions produced **1 pass and 21 existing binding-limit failures**. No new
production failure occurred in the new cases. Six wrong canonicalized-digest
observations were rejected; three unknown interface additions required explicit
interpretation. All 17 Python files parse and the inventory reconciles exactly.
The full suite and remaining unbound capabilities were not executed.

Remote main advanced during this increment to
`794dd121661245a7a59a91a64d48bb5310a89b74`: consolidated specifications were
published/archived and ontology-version-IRI production support was added. No
intervening tests or fixtures changed. The file-only clauses match the accepted
text and all intervening changes are preserved. The prior version-control
adapter guards still report unavailability; their messages now distinguish
historical interface absence from current production support. Those older
positive version bindings are outside this file-only increment.


Publication resumed after interruption: refreshed remote main
`914f3611bce63aa95bda7bf6e38655427f6c1a71` differs from the validated
`794dd121661245a7a59a91a64d48bb5310a89b74` only in three site-documentation
files. Production, governing specifications, tests, fixtures, vocabulary and
configuration are unchanged, so the recorded validation remains applicable.
All intervening changes are preserved in the publication parent.


## RD-05 file-only input — F1 correction

The prior submission `f65be303753fca64e2f3cd2dd407471d65434540` received NOT OK
for two assertions imposing `provenance is None`. The corrected none-mode checks
audit actual provenance content while allowing an empty programmatic graph;
embedded mode permits an additional graph view while still checking the required
provenance and source checksum in the ontology itself. Exact consumed-byte and
no-automatic-sidecar checks remain. The four affected inventory rows are updated.
No node, fixture or invocation binding changes. This same decision is submitted
for independent re-review; no approval is claimed.

Correction validation: the 31 file-only cases and 324 accepted regressions pass;
collection remains 2711 with exact inventory reconciliation. Four permitted
programmatic-view controls now pass. Four provenance-content violations and all
six canonicalized-digest substitutions remain rejected. All 17 Python files parse.
The unchanged broader binding-limit selection and full suite were not rerun.

## T1 — Independent CLI diagnostic-mirror evidence

The owner explicitly authorized T1 audit remediation under existing DK-DIAG-04,
waiving the Architect Reviewer OK prerequisite for this assignment only. No
architectural review or new semantics are claimed. T1 received the forwarded
independent Test Reviewer OK for `51a5c93bc215167bc20f1b3424ade472b676fe97`;
the owner subsequently assigned T2. T3–T5 remain queued.

The nine existing `test_cli_opaque_identifier_policy_and_report` cases now request
unfiltered `--console-level info` output and compare it independently with the
JSON report. `diagnostic_mirror_records` reads the produced side exclusively from
the real CLI's captured console records. The reported side reads native report
events and normalizes their current inspected console presentation, including
source locators, generated IRIs and stderr escaping of invalid identifiers.
Counters retain event content and multiplicity without imposing diagnostic order.
Console rendering details belong to the replaceable adapter, not the behavioral
assertions or production contract; a renderer change requires an updated binding.
Filtered console output raises `ImplementationUnavailable` for this operation.
The general CLI observation remains report-derived and is not used as independent
diagnostic-completeness evidence here. Other readers and unbound operations remain
unchanged. No fixtures or expected graphs changed.

Focused command from the repository root:

```bash
python -m pytest --rootdir=. -p no:cacheprovider -q tests/cli/test_cli.py::test_cli_opaque_identifier_policy_and_report
```

All nine cases passed against unchanged production. Temporary interceptions after
real CLI execution removed, duplicated or altered an `ABSTRACTNESS_ANNOTATION`
INFO event in the JSON report; all nine mutation/policy combinations failed at
the corrected mirror assertion. A reordered two-event report passed and both
filtered-console guards refused completeness credit. Nine related CLI file-input
and Python diagnostic-access regressions passed. Collection remains 2711 with
unchanged nodes. Full-suite execution was not repeated; the previously observed
T2–T4 failures are outside this assignment. See the T1 inventory section for
authority, the owner exception and exact existing node/fixture traceability.

## T2 — Native configuration rejection and conversion-start evidence

The owner relayed T1's independent OK and explicitly directed T2 next. This is
recorded as the task-specific sequencing instruction for maintenance under the
existing DK-IRI-01/DK-DIAG-04/§15 contract. No Architect Reviewer verdict or new
semantics are claimed. T2 received the forwarded independent Test Reviewer OK
for `9f3e2890e58794fe7a02a40cd2836a49386ba7aa`; the owner subsequently assigned T3.

The real CLI command remains `sys.executable -m ontouml_directkg`. A temporary
`sitecustomize.py` installs a standard Python profile hook in that child process.
It only observes calls to the currently inspected input reader and native
`ArgumentParser.error`; it never replaces conversion, changes parser behavior or
supplies expected results. The original argv/status/streams and raw execution
trace are retained. Startup imports and reader identity are implementation
knowledge confined to the replaceable test adapter, not required public APIs.
Observer completion and an active profile at exit are required. Missing evidence
raises `ImplementationUnavailable` rather than supplying a false absence.

Actual parser rejection with code 2 before input processing has no conversion
result (`process.observation is None`). No report is required or manufactured for
that branch. Completed processing and policy-driven aborts still read the actual
requested report; a missing report remains a visible error. Existing version-IRI,
extra-argument, fault and other unbound capabilities remain unchanged. T1's
independent console/report comparison is preserved.

Focused command from the repository root:

```bash
python -m pytest --rootdir=. -p no:cacheprovider -q tests/cli/test_cli.py::test_supplied_base_rejection_precedes_conversion_and_requested_reporting tests/cli/test_cli.py::test_cli_external_metadata_does_not_ingest_unaccepted_formats
```

All 12 target cases passed, replacing their prior missing-report failures. The
19 T1/file-input/diagnostic-access/fixture regression checks passed. Twelve separate
uninstrumented native controls matched rejection behavior. Temporary negative
controls kept three lost post-processing reports visible (including a forged
code 2), refused two missing-observer traces and rejected two unexpected artifacts
on rejection. T1's nine report mutations, order control and both filtered-console
guards remained valid. Collection remains 2711 with unchanged nodes; all 17
Python files parse and 2623 behavioral inventory nodes reconcile. The full suite
was not repeated. No production, fixture or specification files changed; T3–T5
remain queued. See the T2 inventory section for authority and exact node pairings.

## T3 — Naming-warning facts and generic fallback category

The owner relayed T2's independent OK and explicitly directed T3 next under the
existing accepted contract. No Architect Reviewer verdict, new semantics or
normative supersession is claimed. T3 received the forwarded independent Test
Reviewer OK for `7f28538939fb5ec80023f00f28cbd60471745012`; the owner assigned T4 next.

The adapter now reads the available stereotype from the actual class naming
warning. It interprets the current producer's quoted source-ID/stereotype
literals and both name-mode and ID-mode warning forms, retaining the original
native event. Neither input data nor the expected fixture supplies the fact.
Unknown message forms remain explicitly unavailable. Native warning wording and
codes stay within the replaceable binding rather than becoming required APIs.

The generic attribute-fallback test selects the existing `generic_id_fallback`
semantic category. It retains its WARNING, source identification, generated IRI,
property kind/domain, name-strategy and source-label assertions. All 36 existing
node/parameter IDs and canonical input pairing remain unchanged.

Focused command from the repository root:

```bash
python -m pytest --rootdir=. -p no:cacheprovider -q tests/transformation/test_iris.py::test_unnamed_class_uses_type_specific_fallback tests/transformation/test_iris.py::test_generic_attribute_fallback_keeps_name_strategy
```

All 36 formerly failing cases passed. Sixty related naming/enumeration cases and
21 accepted T1/T2 cases passed. Temporary mutations of actual native warnings
were rejected in 30 behavioral controls; three unknown-wording controls refused
credit. Five actual-warning controls preserved quoted identifiers/custom
stereotypes and did not invent an absent stereotype. Collection remains 2711
with identical nodes; all 17 Python files parse and 2623 behavioral inventory
nodes reconcile. The full suite was not rerun. Production, fixtures and
specifications remain unchanged; T4–T5 remain queued.

## T4 — Supported input for chain/reference interaction cases

The owner relayed T3's independent OK and directed T4 next under the existing
accepted contract. T4 received the forwarded independent Test Reviewer OK for
`38ea538ed2997c94bafaf9d35f694c4cff16c094`; the owner assigned T5 next. No Architect
Reviewer verdict, new semantics or normative supersession is claimed.

The 24 chain/reference cases retain the canonical `shared/material_pattern`
input. Their existing temporary-input mutation now adds one complete custom
datatype classifier, dAffected/StructuredValue, and uses it as pAffected's value
type. This applies the already accepted DK-ATT-01/DK-DAT-05 object-property mapping.
The material participants, shared input, parameter IDs and 16 existing assertions
remain unchanged. Three explicit class/object-property/range assertions verify
the supported prerequisite. RD-14's reference mapping does not require matching
ranges; no ordinary kind-valued attribute mapping is selected or invented.

Focused command from the repository root:

```bash
python -m pytest --rootdir=. -p no:cacheprovider -q tests/transformation/test_properties.py::test_emitted_chain_nonsimplicity_follows_property_references_without_materializing_inverse_edges
```

All 24 cases passed after reproducing their prior unsupported-kind guards. Nine
nearby property-hierarchy/custom-datatype regressions and one shared fixture
contract passed. Temporary mutations after actual conversion removed the required
inclusion, inverted chain presence, violated the count policy or removed
unrelated counts; all 96 mutation/configuration controls were rejected by the
interaction assertions. Collection remains 2711 with identical nodes, 2623
behavioral inventory nodes reconcile, all 24 rule mappings retain their per-mode
associations and all 17 Python files parse. The full suite was not rerun. No
production, adapter, stored fixture or specification changes were made.


## T5 — Invalid ontology version IRI rejection

The owner forwarded T4's independent OK for
`38ea538ed2997c94bafaf9d35f694c4cff16c094` and directed T5 maintenance under the
existing DK-IRI-01 / §15 contract. T5 awaits independent Test Reviewer review.
No architectural review, new semantics or normative supersession is claimed.

The existing ontology/CLI modules now cover seven invalid string forms under
all three input policies, using the canonical `shared/base_iri/input.json`.
The control matrix also checks the optional version setting's absent default
and one-argument CLI arity. Exact nodes, assertions and pairings are in coverage.md.
No stored fixture, expectation or production file changes.

The adapter now forwards the inspected real `ontology_version_iri` Python
parameter and `--ontology-version-iri` CLI flag. Historical version-control
unavailability notes above describe earlier revisions. Python calls supplying
this control observe the actual input-reader and shared report-writer entries
with a standard profile hook, preserving an existing hook. Rejection retains
the native error without inventing a result; missing profiling evidence refuses
credit. CLI uses the existing same-process input/parser observer. This binding
knowledge imposes no production function name or new public trace API.
Control inspection binds only this setting; other lookups, complete enumeration
and unrelated observation readers still raise explicit unavailability.

Focused command from the repository root:

```bash
python -m pytest --rootdir=. -p no:cacheprovider -q tests/transformation/test_ontology.py::test_invalid_ontology_version_iri_rejected_before_conversion tests/cli/test_cli.py::test_cli_invalid_ontology_version_iri_rejected_before_conversion 'tests/cli/test_cli.py::test_cli_and_python_expose_all_established_controls_values_and_defaults[ontology_version_iri]'
```

All 43 new cases pass, after first reproducing 43 explicit binding failures.
The accepted T1–T4 cases and related base/file-input/diagnostic/fixture checks
pass (130 cases). The nine older version tests yield one reuse-case pass and
eight explicit limits: two broad provenance-absence readers, five provenance-role
readers and one Python-delivery operation. Their expectations remain intact.
Temporary native controls confirm 21 Python rejections, 21 uninstrumented CLI
matches and nine omission/HTTPS/URN combinations in both interfaces. Twenty-four
behavioral mutations and six missing-observer controls are rejected; five scoped
control lookups/enumerations and one untraced Python read refuse unsupported
credit. Existing profile hooks are preserved in two controls. Collection is
2754 nodes, with all 2711 previous nodes retained; 2666 behavioral inventory
nodes reconcile and all 17 test/support Python files parse. Full-suite execution
and the remaining unbound capabilities were not performed or certified.


## A1 — Reviewed inverse naming and numeric allocation

The owner relayed Architect Reviewer OK for A1.1, A1.2 and revised A1.3 at
`0328ae1300e99eafbce7d5f32d2476c4aa5db71f` (F1 resolved), then explicitly
waived only the preceding-assignment sequencing restriction for A1. The older
submission is outside this work and remains unclosed. A1 awaits its own
independent Test Reviewer review. Inspected base:
`642fb6e0657f65b8dc49f7c082187043e6c34add`.

The existing inverse module now asserts the accepted exact role/domain fallbacks,
occupied-slot allocation from the original qualified candidate, raw source-end-ID
ordering, and reservations shared with retained inverses across multiple groups.
It retains the original five relevant node IDs and all prior suite IDs, adding
105 parameters. Existing complete binary/collision inputs are adapted only in
pytest temporary files; no stored input/expectation or adapter is changed.
Exact Rules, parameter IDs, fixed names, fixtures and authority are in coverage.md.
Current former inverse-name blocker notes are updated; other historical records
and unrelated unresolved questions remain.

The real public file converter remains bound. A1 needs only the existing graph,
structured diagnostic and outcome observations. Inverse-disabled native runs
establish source-backed identity and independently applicable diagnostics;
ID mode also explicitly checks its known source-resource IRIs because it has no
DCTERMS identifiers. These comparisons implement invariance assertions, not a
replacement converter or inferred empty observations. No additional diagnostic
is required solely for inverse naming.

Commands from the repository root:

```bash
python -m pytest --rootdir=. -p no:cacheprovider -q tests/transformation/test_inverses.py -k 'unusable_present_role or unusable_inverse_domain or inverse_domain_fallback or inverse_numeric or residual_inverse_collision'
python -m pytest --rootdir=. -p no:cacheprovider -q tests/transformation/test_inverses.py
python -m pytest --rootdir=. -p no:cacheprovider --collect-only -q tests
```

The final inverse-module execution has **144 passed, 96 failed** across 240 cases.
Its 110 A1/relevant nodes have **46 passed and 64 production-only failures**:
58 existing production guards plus six wrong reserved-slot allocations. No A1
failure is adapter unavailability. Remaining inverse cases have 98 passes and
32 existing binding limits, explicitly retained. Seven related collision/fixture
checks pass. Eleven mutations of actual native output fail at behavioral
assertions; 22 numeric variants validate and complete real inverse-disabled
baselines. Unsupported production branches are not simulated or marked passing.
Collection is **2859**, all prior 2754 IDs retained plus 105; all 17 test/support
Python files parse and 2771 behavioral inventory nodes reconcile. The full project
suite was not executed. No production, vocabulary, specification, stored fixture,
new module or configuration change is included.


Publication was reconciled onto the parallel documentation commit
`8d846c9bee65870ed1a7744f059f3f15e1a644e3`. Its five root/site documentation
changes are preserved. Refreshed-tree and hash checks show no changed test,
production, fixture, packaging, vocabulary or governing-specification blob;
AST and exact inventory checks revalidate the unchanged executed foundation.


## A1 — F1 resubmission

The initial A1 revision `ff09ea706c52247929c44fd571ee62776902b7e1` received
independent Test Reviewer NOT OK for F1. The numeric test compared reordered
input with the original-order inverse-disabled baseline. DK-IRI-07 permits
ordinary collision suffix assignment by deterministic source ordering; A1's raw
ID ordering requirement applies to generated inverses.

The numeric test now serializes each request once and obtains its baseline and
inverse-enabled result from that exact path/content. Source-name-set assertions
are retained inside the same loop. All fixed inverse expectations, original
assertions, parameter IDs and case constants remain. The 33 inventory entries
now document the matching-input comparison. Only the test module and its two
traceability/operating documents change; production, support and fixtures remain.

Temporary native controls verify that a permitted ordinary class-suffix swap
across declaration orders now passes in all three generating modes; the submitted
version rejected those three controls. Same-input identity drift is still
rejected, and both exact F1 collision-group baseline comparisons are verified.
These controls do not simulate missing inverse allocation. The full inverse
module remains **144 passed, 96 failed**: A1 has 46 passes and 64 production-only
failures; the remaining 32 failures are existing binding limits. The corrected
33 parameters have 3 passes and 30 production failures. Collection is unchanged
at 2859; all 2771 behavioral inventory nodes and 110 A1 mappings reconcile.
Eleven native-output mutation controls and 22 input/native baseline controls
also pass. The full project suite was not executed. This same-target correction
awaits independent Test Reviewer review under the existing A1 authority and
owner sequencing exception; no implementation is initiated.


## I1 — Mixed metadata list recovery, Alternative A

The preceding A1 F1 correction received the owner-relayed Test Reviewer OK at
`1e128a4f1b7ac8f69d039a18bacd0b55bbe4ffbd`. This separate TEST CHANGE follows
reviewed Architect registration `b47dd82e3544a045394ccc4c2b2828ccdacb2337`
(Architect Reviewer OK, no findings). DK-GEN-09 now requires every valid member
of contributor, keyword, source and list-valued landingPage to survive invalid
siblings under best-effort. DK-DIAG-04–05 and §15 retain their existing outcomes
and delivery rules. Strict/tolerant abortion, file failures, field shapes,
optional/ignored values and provenance remain unchanged.

The four former undecided-sibling parameters are replaced with 75 exact cases in
the existing ontology/CLI modules. They cover valid-only, both mixed orderings,
invalid-only, simultaneous list recovery, independent title/license and source
mappings, source text/language boundaries, all provenance modes, mandatory source
abortion, structured results and real CLI ontology/report delivery. Python and
CLI both include the exact audit YAML using shared/base_iri, best-effort and
provenance none. The complete canonical JSON is reused; only supported Project
text/language or deliberate duplicate-source-ID variants are temporary. No
stored fixture, module or test configuration changes.

External-contribution observation is now bound through actual Graph.add events
inside the current native external-metadata writer, through Python and the real
CLI. It does not reconstruct expected triples from fixtures. Exact emitted RDF
is checked against fixed expectations and the delivered graph; independently
generated metadata outside that writer remains allowed by DK-GEN-11. A missing
or incomplete observation refuses credit. Native metadata diagnostic categories
are interpreted by the adapter; their internal spellings and prose are not
normative. Existing profile hooks and T5 traces remain active, T2 rejection
handling stays intact, and CLI reports still require independent console mirroring.

Actual results: **43 passed, 32 failed** in the new 75-case selection. All 32 are
production gaps at the unresolved mixed-list read_metadata guard: 27 direct
Python guards and five CLI executions that terminate before the required report.
The latter retain real status/processing/stderr evidence in the missing-report
exception. No new adapter-unavailability failure occurs. Existing metadata
regressions have **68 passes / 17 existing binding limits** (configuration,
permission faults and provenance readers); shared-support regressions **64 pass**.
The inverse module has **208 passes / 32 existing binding limits**, including all
110 A1 cases passing after the intervening A1 implementation. Eight affected
fixture contracts pass. Collection is **2930**, preserving every prior ID except
the four explicitly superseded weak nodes; all 2842 behavioral inventory nodes
and 17 Python files reconcile/parse.

Temporary native controls reject 13 RDF/result/report faults and refuse three
missing-evidence controls. Six independent generated-metadata controls remain
allowed; two hook/trace controls pass and ten uninstrumented CLI runs match the
instrumented status/streams. These controls execute actual supported conversions;
no mixed-list recovery implementation is simulated or granted passing credit.
The full project suite and full provenance conformance were not executed. Exact
node IDs, pairings, commands, controls and execution limitations are in coverage.md.

The execution base is `b47dd82e3544a045394ccc4c2b2828ccdacb2337`. Refreshed main
`9f031398d4c73f6a41415ec35fe5ee6a6b7093b2` adds only four parallel documentation
changes, all preserved. Test/production/specification/fixture hashes are unchanged.
Five test-owned paths change; production, normative files and canonical fixtures
remain untouched. I1 awaits independent Test Reviewer review. No transformation-
engine implementation is initiated and production correctness is not certified.


## A2 — Structural evidence for semantic naming

This TEST CHANGE follows Architect registration and initial main
`4fdef7bbaf8b73bf1ed0ff47fc793494493083dc`, covered by the owner-relayed
Architect Reviewer OK, no findings. The prior I1 test gate is closed at
`438eb677c444f48c57978c1028abd241f1ea63b0`. The current transformation
specification blob is ce1fd740feea0a447e7315c84df53959a16060e3; test structure
remains 250a059d46377360aeecdb5176310bd36bde7825. DK-REL-04's supported
structural evidence controls lexical selection while preserving the other
accepted relation, label, diagnostic and ordinary-mapping rules.

In the existing relation module, 30 table parameters retain their IDs with exact
expectations; eight historical lexical/label cases replace their former bounded
candidates with endpoint fallback. Seven added functions provide 177 cases for
marker states/directions, the complete explicit mode/non-mode set, ambiguity and
unsupported combinations, ignored text/inheritance/custom/restrictedTo hints,
historical fallback, controls/labels and all-policy nonfatal uncertainty. All
reuse complete shared/binary_relation JSON and explicit temporary mutations.
No fixture, module, configuration or stored expected graph is added.

Public conversion/CLI invocation is unchanged. The adapter now interprets the
actual historical limitation warning while retaining raw evidence. A narrow
aggregation-comment reader normalizes only inspected native RDF wording and
returns actual subject/literal/context/value evidence; unknown forms remain
explicitly unavailable. Broader comment and label-origin readers remain unbound.
Exact expectations and all 215 node/parameter mappings belong to coverage.md.

Final relation-module execution: **307 passed, 814 failed**. A2's 215 nodes have
**65 passes and 150 native deferred-direction guards**; the other 664 failures
are existing explicit binding limitations. Related inverse/I1/T1/input checks:
**293 passed, 32 existing inverse binding limitations**. All 110 A1 and 75 I1
cases pass against current production. Temporary controls validate 157 native
disabled-control input/mapping variants, pass nine executable function controls,
reject 15 RDF/diagnostic mutations and refuse one unknown annotation rendering.
These controls neither simulate nor grant passing credit to deferred A2 selection.

Collection is **3107**, retaining all 2930 prior IDs plus 177; 3019 behavioral
inventory nodes and all 17 Python files reconcile/parse. The full project suite,
full provenance conformance and remaining unavailable operations were not run.
Commands, actual failures, canonical pairings and binding limits are recorded in
coverage.md. Four test-owned paths change. Production and normative documents
remain unchanged. A2 awaits independent Test Reviewer review; transformation-
engine implementation is not initiated and must also verify the documentation
gate.


Publication was reconciled onto refreshed main
`29a798666e1e66e5d636ab7ac23905d50394be0d`. Its seven parallel A2 documentation
changes are preserved. Complete tree and snapshot-hash checks confirm identical
production, tests/support, fixtures, packaging, vocabulary and governing
specifications, so the recorded execution remains applicable.


## D3/A4 — Standalone attribute star

One consolidated finding follows the owner-relayed Architect Reviewer OK, no
findings, for the specification NO CHANGE / open issues NO CHANGE assessment
inspected at `4fdef7bbaf8b73bf1ed0ff47fc793494493083dc`. Initial main is
`2af023c6a67c8c205d409b37f00e6b564ad9f1f9`. The earlier pending entry condition
is superseded. The explicit owner exception waives unrelated queue restrictions
only; D3/A4 retains its own independent reviewer gates.

The existing nine null/absent/star nodes retain their IDs and diagnostics. Star
now receives the same exact empty-cardinality assertion, excluding all six OWL
cardinality predicates, redundant zero minima and qualified variants. A new
36-case function checks raw/surrounding-whitespace star across all policies,
both IRI strategies and primitive/custom datatypes. Real 0..*, normalized
zero-unbounded, positive-unbounded and exact-zero controls preserve property
identity/typing/domain/range and a peer's independent 2..5 restrictions. Fixed mapping
RDF comparisons allow descriptive metadata variation; every conversion's peer
cardinalities are checked separately with their permitted representations. Complete canonical
value_types JSON is reused through checked temporary variants; no fixture or
new support module is added.

The adapter interprets actual native missing/invalid-cardinality diagnostics,
retaining raw events and locators. Public invocation remains unchanged. The
supported exporter Cardinality.java and §3.2 / DK-ATT-01–04 / DK-DIAG-05/09–11
supply existing authority; this test work introduces no semantics or production
mapping. Coverage.md records the full pinned source, reviewed derivation and
all 45 exact mappings.

Initial submitted attribute-module execution: **184 passed, 39 native guard failures, 19 existing
binding limits** (18 comments reads, one removed-control inspection). The D3/A4
subset has six passes and 39 guard failures, without assertion or binding
failures. Affected relation/T1/input regressions: **214 passed**. Temporary native
controls complete 144 pre-star conversions and reject 36 forbidden-output or
diagnostic faults; metadata variation passes scoped comparisons before reaching
the real guard. No star conversion is simulated or granted passing credit.
Collection is **3143**, retaining all 3107 prior IDs plus 36; 3055 behavioral
inventory nodes and all 17 Python files reconcile/parse. The full project suite,
full provenance conformance and remaining unavailable operations were not run.

The initial submission changed four test-owned paths and received NOT OK for
F1/F2. Its invocation binding remains unchanged by the correction below.
Production, stored fixtures and governing specifications remain unchanged.
Implementation also requires the applicable Documentation Reviewer OK, including
justified NO CHANGE; no transformation-engine implementation is initiated here.


## D3/A4 — F1/F2 correction

Same-target correction of the independent Test Reviewer NOT OK for
`ac2f2bf943be1f0800931368cd87400eaf614b3d`, also the verified correction base.
Existing D3/A4 architectural authority and reviewer gates remain applicable.

F1 reproduced four false rejections of equivalent qualified peer restrictions.
The RDF comparison now selects fixed class/property mappings and source-class
links. Each conversion independently verifies the peer's positive 2..5 counts,
allowing qualified/unqualified forms. F2 reproduced twelve false passes for
cardinality predicates directly on the focus property. The existing empty-count
helper now rejects all six direct predicates as well as referencing restrictions.
All 45 node IDs/parameters, control inputs, Rules and canonical fixtures remain.

Current module results remain **184 passed, 39 production guards, 19 existing
binding limits**; D3/A4 remains six passes and 39 guards. All **214** affected
regressions pass. Twelve permitted qualified-peer combinations reach the real
star guard after their controls; 60 direct-predicate faults and twelve invalid-
peer cases fail at assertions. The original 36 fault controls and 144 pre-star
conversions remain effective, with permitted metadata variation. Collection
remains **3143**, inventory **3055** behavioral nodes and all **17** Python files
parse. Guarded star output receives no completed-conversion credit.

Only the attribute test module and these two traceability documents change.
Invocation/production/fixtures/specifications remain unchanged. Detailed commands,
before/after controls and all 45 mappings are in coverage.md. The full project
suite, full provenance conformance and unavailable operations were not run.
F1/F2 are corrected in scope; this D3/A4 resubmission awaits independent Test
Reviewer review. No transformation-engine implementation is initiated.

## RD-02 — Repeated generalization-set membership

Initial TEST CHANGE for the owner's unified handoff; architectural registration
`2b427908a7e29d546486a616a22495ea0424f294` received the owner-relayed independent
Architect Reviewer OK with no findings. This test submission awaits its own
independent Test Reviewer. No other downstream disposition is an entry gate.
DK-GEN-12 supersedes only the former unspecified duplicate-membership treatment.
Current governing paths are `documentation/specification/transformation-specification.md`
and `documentation/specification/test-suite-structure.md`.

121 new cases in classes, higher-order and relations reuse their owning canonical
inputs, with explicit synthetic mutations and inline expectations. They assert
repeated-reference equivalence; singleton completeness/INFO; ordinary categorizer
and powertype extension; per-set identity; case/whitespace/Unicode-distinct IDs;
distinct declarations sharing endpoints; fatal duplicate declarations; invalid
same-ID references; partial failures; and inverse/material-chain interactions.
Union members are compared without requiring list order. No stored data is added,
modified, promoted or copied. Version/source evidence and every exact node/parameter,
rule and fixture path are in the final RD-02 section of coverage.md.

The real conversion/CLI binding now interprets six existing generalization/set
diagnostics and their actual equivalence/coverage wording. It retains native raw
events and observed locators. Unbound readers and delivery/fault operations still
raise ImplementationUnavailable; no empty evidence or missing behavior is supplied.

Validated with Python 3.12.14, pytest 9.1.1, RDFLib 7.6.0 and PyYAML 6.0.3:

```bash
python -m pytest --rootdir=. --collect-only -q tests
python -m pytest --rootdir=. -q tests -k repeated_membership --tb=short -rN
python -m pytest --rootdir=. -q tests -k 'generalization or singleton or partial_set or categorizers_pun or duplicate_declaration or fixture_contract or rdf_helper' --tb=no -rN
```

Collection: 3,264, retaining all 3,143 previous nodes. New cases: 15 passes and
106 native production guards (102 repeated memberships; four distinct declarations
with equal endpoints). No assertion failure, skip, xfail or collection error was
observed in the new selection. The same 278 existing regression nodes improve from
148 passes / 130 unbound failures to 201 passes / 77 unbound failures after scoped
diagnostic interpretation; all 88 fixture/helper checks pass and no earlier pass
regresses. Remaining unbound readers are enumerated in coverage.md. Canonical
controls run before repeated inputs in paired cases. Two native CLI controls
produce correct INFO/WARNING JSON reports; both repeated counterparts stop at the
production guard and deliver no artifacts, without completed-conversion credit.

All 17 test/support and 21 production Python files parse; git diff --check passes.
Main advanced to documentation-only commit
`93eae0d771ff11ee49e5d5a881706de51838baf6`; its seven documentation changes were
preserved and all test/production/governing-source blobs remained unchanged.
No production or specification file changes. Full project execution and full
provenance conformance are unperformed. Historical execution notes above retain
their original meaning; this test review does not certify passing production.

## RD-04 — Shared JSON diagnostics contract

Same-target F1 correction following Test Reviewer **NOT OK** for
`021961b767e3bc461708c86671b0f7fbc0a9c5fd`. The owner's unified handoff and
Architect Reviewer **OK, no findings**, at
`37e68764202a2a18e0c54ac264df1536ff47e28c` remain applicable. This correction
awaits independent Test Reviewer review; no review reuse or waiver applies.
The earlier RD-02 test submission is accepted and closed. Current sources are
transformation-specification.md (blob 07c3b20ae236500efd9bf59299c6e31f249fbcd0)
and test-suite-structure.md (unchanged blob
250a059d46377360aeecdb5176310bd36bde7825), under documentation/specification/.
DK-DIAG-04, DK-DIAG-05 and §15 are unchanged from the RD-04 registration. Only
former unspecified JSON-structure qualifications are superseded.

43 native acceptance cases and one reader/harness case cover the required shared
JSON envelope, diagnostic/source members and types, empty/null context, all three
outcomes, explicit Python export, CLI filtering, abortion, consolidation and the
instantiation discarded-value boundary. Required members are a minimum: compatible
extra members and reordered data are accepted; schema_version and an exact code
catalogue/message wording are not imposed. All 44 cases pass. Every exact parameter
ID, rule, canonical input and inline expectation is in the final RD-04 inventory.
No stored JSON/Turtle/YAML, fixture location, dependency or pytest configuration changes.

The adapter now binds real public Python diagnostic export and its actual failure.
Its existing profiler observes automatic export calls during Python conversion.
For CLI mirroring, independent snapshots copy native diagnostics on conversion
return and after delivery, before comparing against the JSON file. Presentation
must retain produced events, including hidden INFO/WARNING. The reader preserves
raw JSON while ignoring compatible members. Three actual native codes are added
to semantic interpretation as binding knowledge; no normative code is registered.
Broader fault, serialization, delivery and semantic readers remain unbound.

```bash
python -m pytest --rootdir=. --collect-only -q tests
python -m pytest --rootdir=. -q tests/transformation/test_input_diagnostics.py tests/cli/test_cli.py -k shared_json_contract --tb=short -rN
python -m pytest --rootdir=. -q tests/transformation/test_input_diagnostics.py tests/cli/test_cli.py -k 'not shared_json_contract' --tb=no -rN
```

Initial submission validation: Python 3.12.14; pytest 9.1.1; RDFLib 7.6.0;
PyYAML 6.0.3. Collection: 3,308,
retaining all 3,264 previous nodes. The same 526 existing diagnostics/CLI nodes
improve from 371 passes / 155 unbound failures to 385 passes / 141 unbound
failures, with no previous pass regressing. Additional adapter regressions: 176
passed. All 88 existing fixture/RDF-helper checks pass. Shape/mirroring controls
reject 27 + 7 faults per checker while accepting four permitted variants. The new
reader/harness case receives no transformation credit. All Python files parse and
git diff --check passes; detailed commands and evidence limits are in coverage.md.
No production/specification changes. Full-suite and full-provenance execution and
unbound operations are unperformed. Historical results above retain their meaning.

Before initial publication, main advanced through documentation-only revision
`c9bd97c970ef6789c0edb35cf0cac757ba3c5c51`. All six intervening root/site changes
are preserved; test, fixture, production and governing-source blobs are unchanged.

**F1 correction validation (2026-11-07):** both successful and failed Python
export checks now use `invoke.read_ontology(result)` after export. A copied
pre-export graph is compared with the live graph by isomorphism; aborted results
must still expose no graph. The existing adapter already binds this reader to
the real result. No adapter, fixture, parameter ID or normative behavior changes.

Six controls performed real exports, then replaced only the live result's graph:
eligible graphs were removed and aborted results acquired a graph. The unchanged
tests falsely passed all six controls; the corrected assertions reject all six.
Normal RD-04 execution: **44 passed**. Directly affected pre-existing diagnostic
access/export checks: **8 passed, 1 existing ImplementationUnavailable failure**
for the unbound required-provenance fault injection. Collection remains **3,308**
with every prior node retained. Inventory, Python parsing and git diff --check
pass. Detailed commands are in coverage.md. Earlier broad regression, fixture,
shape and CLI controls are historical results, not reruns for this correction.
Full-suite execution and unbound operations remain unperformed.

Correction base: `6962d68f972466e7b8d5445cfe1e72cca4a0c282`. The intervening
RD-17 registration and instantiation documentation correction are preserved;
they change no RD-04 clause, test, support, fixture or production blob.

## RD-17 — participation, creation and termination, alternative A

TEST CHANGE for the owner's unified handoff and Architect Reviewer **OK, no
findings**, at `8bfc90fc40d732212ea84e583986c7ae0b96c65b`. This submission is
pending independent Test Reviewer review. The preceding RD-04 F1 correction at
`d74c0e7da378d88abbf5c400d2e7b3d6488dc35a` is accepted and closed; its earlier
pending-review notes describe the historical submission. No review reuse or
procedural waiver applies. Downstream work proceeds independently under the
owner's explicit sequencing instruction.

DK-REL-01 retains ordinary mapping for all three stereotypes, excludes additional
stereotype-only axioms/declaration annotations and preserves independent output.
DK-GEN-11, DK-REL-04 and DK-DIAG-01 align that boundary. Limitation warnings are
required despite successful naming and remain nonfatal under every input policy.
No previous accepted mapping is superseded. `participational` and its per-axiom
compatibility gate retain their existing treatment. Current transformation blob:
`07c3b20ae236500efd9bf59299c6e31f249fbcd0`; structure blob:
`250a059d46377360aeecdb5176310bd36bde7825`.

The existing relations module adds 39 cases and strengthens six existing exact
direction/name cases. Canonical complete inputs remain `shared/binary_relation`
and `relations/hierarchy`. No fixture, stored expectation, dependency or pytest
configuration changes. Fixed RDF/naming assertions cover ordinary output, default
controls, all input policies, named/anonymous inverses, counts, descriptions,
source-ID annotations/omission, source and generated labels, language handling,
disabled stereotype naming and explicit relation hierarchy. Logical graph
comparisons and the audited annotation reader reject additional output while
preserving independently required comments, including authored stereotype text.

The logical-comparison, other-diagnostic and limitation-warning helpers now have
general relation names; every historical consumer is updated without changing
their behavior or node IDs. The adapter's scoped `read_relation_stereotype_annotations`
reuses its existing actual-RDF audit. Unknown annotation forms remain explicitly
unbound; the reader does not assume empty evidence. No diagnostic is fabricated,
and no native identifier, exact message, count, Turtle order or blank-node label
becomes a requirement.

Validation with Python 3.12.14 and the pinned dependencies: **3,347 collected**,
all **3,308 previous exact nodes retained**. Combined affected execution:
**127 passed, 45 failed**. All failures are the missing required limitation
warning: 39 new nodes and six intentionally strengthened naming nodes. Their
preceding mapping/annotation assertions pass; both naming directions execute
before the warning check. All 127 unchanged selected cases retain their passes.
The earlier five-axiom selection remains **90 passed**, including `participational`
asymmetry and per-axiom compatibility. All **88 fixture/RDF-helper checks** pass.

Scratch controls over real outputs reject 21 logical mutations, report 12 unknown
annotation forms as unbound, and accept three timestamp variants and three actual
source descriptions naming the stereotype. These are harness validation, not
passing conversion coverage. No positive warning or replacement conversion is
supplied. Inventory/fixture-path checks, all Python parsing and git diff --check
pass. Full-suite execution, full provenance conformance, positive declaration
annotation interpretation and broader unbound operations remain unperformed.
Actual commands, Catalog/exporter evidence and exact nodes are in coverage.md.

Initial inspection: `d74c0e7da378d88abbf5c400d2e7b3d6488dc35a`. The refreshed
main first advanced through `005185ed9591c42d50e6bc84d036c68b5acfbaf8`, changing
only the diagnostics module's explanatory docstring. Publication base
`dd30b88011638c808bcbfd12a8f22cf55fd1fc68` additionally updates six root/site
documentation paths. All intervening content is preserved; test, fixture and
governing-source blobs are unchanged, with no executable production change.

## RD-17 — participational and manifestation, alternative A

TEST CHANGE for the owner's unified handoff and Architect Reviewer **OK, no
findings**, at `fb05478031e290b123e766ad5188e4cef9935357`. Pending independent
Test Reviewer review; no prior-review reuse or additional waiver applies. The
owner's independent downstream sequencing instruction remains applicable. The
preceding participation/creation/termination test gate is closed at
`363d0d37bb1ae56a0ef3cdc762dd3ca7d4994dc6`; its earlier pending-review and
execution notes above describe that historical submission.

DK-REL-01 preserves ordinary mappings, the existing guarded participational
asymmetry, and independently required output. Manifestation supplies no additional
property characteristic. No further stereotype-only axioms/declaration annotations
are permitted. Both stereotypes require a nonfatal residual-semantics WARNING
under every input policy, whether naming succeeds or the asymmetry is generated
or gate-omitted. DK-GEN-11, DK-REL-04 and DK-DIAG-01 align this boundary. No
accepted mapping is superseded; no code, wording or diagnostic count is fixed.
Current transformation blob: `54510d68a663643db75d7bb4ea8e30329e06c074`;
unchanged structure blob: `250a059d46377360aeecdb5176310bd36bde7825`.

Extend the existing partial-relation tests with **26 parameters**: six ordinary
mapping profiles, sixteen naming/control cases (each checks both directions),
and four hierarchy cases. Add **nine gate/policy cases** using the original gate
assertions, now shared through a helper without changing the old nodes. Strengthen
**18 existing nodes**: four semantic naming cells, eleven whole-marker variants
and three insufficient-role policy cells. Zero, one or two whole markers retain
their accepted lexical treatment and independently required warning.

Canonical complete inputs remain at `shared/binary_relation`, `relations/hierarchy`
and `relations/chain_constraints`; no stored fixture, expectation, dependency or
pytest configuration changes. Logical comparisons admit only the explicitly
expected pre-existing primary asymmetry where compatible. They do not mutate
either actual graph or infer a replacement conversion. Manifestation is compared
with ordinary logic without an added characteristic. Descriptions (including
authored stereotype text), labels, source IDs/omission, counts, inverse forms,
independent flags/end annotations and other diagnostics are retained. The existing
RDF annotation reader remains bound; only its description is generalized.

Python 3.12.14, pytest 9.1.1, RDFLib 7.6.0, PyYAML 6.0.3. Full collection:
**3,382**, retaining all **3,347** previous exact nodes. Combined affected
execution: **216 passed, 53 failed**. Every failure is the missing residual
WARNING: 35 new and 18 deliberately strengthened nodes. Earlier mapping, naming,
annotation and asymmetry-gate assertions pass; both naming directions and every
gate/policy branch execute before the warning assertion. The same pre-existing
selection at the publication baseline yields **234 passed**. All 216 unchanged
selected nodes retain their passes. The 90-case compatibility subset passes;
all **88 fixture/RDF-helper checks** pass.

Scratch actual-RDF controls reject fourteen extra logical mutations and detect
removal of required asymmetry. Eight unfamiliar annotation forms remain explicitly
unbound. Real source text, blank-node relabeling and timestamp variants are
accepted; no positive diagnostic is fabricated. Inventory/path/Rules checks,
Python parsing and whitespace checks pass. Full-suite execution, full provenance
conformance, positive declaration interpretation and broader unbound operations
remain unperformed. This is test-first evidence, not production conformance.
Detailed commands, selected Catalog/exporter evidence and all 53 exact affected
nodes are in coverage.md. Initial inspected main is
`fb05478031e290b123e766ad5188e4cef9935357`.

## RD-17 — Dependency relations and warning consistency

TEST CHANGE for the owner's unified handoff and Architect Reviewer **OK, no
findings**, at `490f209e0d70533bac56674e2844a7463fe77a09`. The Test Reviewer
returned **NOT OK** at `545d995b68fd4f97ca7c0c2183ea02fd53328328`. Review of
`39b20d9cc8f4855a334475ea6d4a0ad6d7ed7d0c` confirmed F1–F3 and returned
**NOT OK** for F4. The F4 correction is pending independent Test Reviewer
review. The owner's independent downstream workflow applies. The preceding
participational/manifestation test gate is closed at
`00f9bf1503b271da1c84728d0ce511efaf505483`; earlier pending-review and execution
records retain their historical meaning.

DK-REL-01 preserves the dependency trio's ordinary mappings, accepted
characteristics/disjointness, compatibility gates, grounding roles, derivation and
optional chains. No further stereotype-only axioms or declaration annotations are
introduced. Residual WARNING reporting is required under every input policy and
independently of naming, accepted-axiom/chain generation or gate-based omission.
The simultaneous owner direction applies that warning treatment to bringsAbout
and triggers in the reviewed registration. DK-GEN-11, DK-REL-04 and DK-DIAG-01
align the boundary, with diagnostic code, wording, and count left open.
The F1–F3 correction builds on `2521e3bde7e26ac06b3abd0b879d165babe07793`, which
separately registers the pair's graph treatment. Its active transformation blob
`8d212d427c0ee7a02ca84f19d9e363b27c9c6d94` retains the warning, naming, and
class-disjointness clauses exercised here. The structure blob is
`250a059d46377360aeecdb5176310bd36bde7825`.

The initial submission added **90 cases** and strengthened **13 existing nodes**.
The F1–F3 correction retained all previous IDs and added one `strict` naming-disabled
case each for `bringsAbout` and `triggers`. Both check the endpoint fallback,
direction, inverse, completed outcome, naming warning, and residual warning.
F4 checks the naming and residual warning meanings for `rFocus` in those two
cases and the three `externalDependence` insufficient-role cases. One native
record can convey both meanings.

The adapter's `read_relation_limitation_source_ids` reader returns the affected
relation IDs identified by actual WARNING events. It resolves reported locators
against the supplied source document and retains distinct declarations of the
same stereotype. The chain tests require both `rLeft` and `rRight` and accept
consolidated evidence. Uninterpretable locators are explicitly unbound.
The adapter reads source-target naming and partial semantics independently
from the observed message and effect for the bound relation-warning codes.
It retains each raw event and its locators. Unfamiliar rendering remains
explicitly unbound.

Canonical complete inputs remain shared/binary_relation, shared/material_pattern,
relations/hierarchy and relations/chain_constraints. No stored fixtures, expected
graphs, dependencies or pytest configuration change. The trio retains explicit
ordinary RDF, names, language, labels, IDs, descriptions, counts, inverses and
independent annotations. Only fixed already-accepted characteristics may differ
from ordinary controls; gate/chain cases preserve the existing exact assertions.
The ordinary comparison checks class disjointness by unordered pairs under
DK-CLS-03/04. Both represented naming directions use distinct temporary files.

Python 3.12.14, pytest 9.1.1, RDFLib 7.6.0 and PyYAML 6.0.3 collected the same
**3,474** IDs at both F4 revisions. Each affected run had **256 passes**,
**78** missing-warning failures and **27** missing-source-attribution failures.
All five fallback cases reach the required residual-warning assertion after
the naming and mapping checks pass. The **90** existing compatibility cases,
**78** additional mapping and naming cases, **88** fixture/RDF-helper cases,
and **48** report and CLI parity cases passed. One comparative naming case and
12 derivation cases encountered the same existing unbound operations at both
revisions.

Controls on real output reproduced F1 and F3 at the reviewed revision. The
corrected reader requires evidence for both relation IDs and accepts either
separate or consolidated coverage. The corrected graph comparison accepts
reversed and reciprocal disjointness statements and rejects missing or added
pairs. F4 controls kept the real conversion graphs and varied only native
diagnostic views. The correction accepted separate and consolidated meanings
in all five cases and rejected missing meanings, wrong sources, and lower
severity. Exact nodes, selected Catalog/exporter evidence and commands are in
`tests/coverage.md`. Full-suite execution, full provenance conformance and
positive end-to-end execution of the five newly required warnings remain
unperformed.

## RD-17 — bringsAbout and triggers graph treatment

TEST CHANGE for the owner's accepted Alternative A and independent Architect
Reviewer **OK, no findings**, at `2521e3bde7e26ac06b3abd0b879d165babe07793`.
The registration settles the pair's graph treatment under DK-REL-01 and
DK-GEN-11. Ordinary mappings and independently required output are retained.
Additional logical axioms and declaration annotations based solely on either
stereotype are excluded. The established nonfatal WARNING contract applies.
The dependency and warning-consistency test assignment closed at
`8c089cecaadd88d612223356bd842df7caaeff6b`. The initial graph submission at
`df6d370956740f952e6014de2cd434c482bb12a7` received **NOT OK** for F1–F3.
The correction is pending its independent Test Reviewer disposition.

Eight existing cases in `tests/transformation/test_relations.py` now check
the ordinary RDF mapping for both stereotypes. These use `shared/binary_relation`
with explicit cardinalities, source and end descriptions, and a target-end
aggregation comment. The successful naming cases still cover all three policies,
and the naming-disabled cases still run under `strict` and allow consolidated
warnings. Four new `relations/hierarchy` cases check exact primary and available
inverse generalizations with both stereotypes. They cover an authored leaf name
and its applicable description with named inverses, and ID-based mapping without
named inverses. Both hierarchy modes require a nonfatal residual warning for the
authored `rLeaf`, allowing consolidation. The input and expectation changes
are inline.

The RDF comparison uses a real ordinary conversion of the matched input.
The binary assertions require the unique `workers` inverse in both conversions.
The hierarchy name-mode assertions check each primary and its dependent inverse
in both graphs before alignment by source-end identity. The comparison permits
blank-node relabeling, unordered class
disjointness and independent typed creation or modification times. Source-authored
descriptions mentioning either stereotype and the existing aggregation-comment
reader provide positive annotation evidence. The existing invocation adapter
reads the actual graphs, warning meanings and reported source locators.

The publication base `49122ec45a38378cf1fac0d6eae82456f4dedd5e` incorporates
the warning implementation and the pair's site documentation. At this base,
all **12** affected cases passed. The combined selection passed **365** cases,
including the **361** pre-existing cases. Collection retained all **3,474**
previous IDs and added four. **88** fixture/RDF-helper and **48** diagnostic
report and CLI parity cases passed. The same nine older cases in the additional
hierarchy/naming selection reached unbound operations at both revisions.
`tests/coverage.md` records the exact nodes, commands, selected Catalog and
VP-plugin evidence, and the graph and warning controls.

The F1–F3 correction builds on `550663e35e9b81d635f7f7b8af22da408a7ef3e7`.
The intervening change is a site documentation reference. The correction
collects the same **3,478** nodes as the reviewed revision. All **12** focused
cases and **365** combined cases pass. Controls reproduce the original false
passes and false rejections and verify the corrected assertions. The existing
RDF and diagnostic controls retain their dispositions.

## Configurable DKGM vocabulary delivery

[Alternative A](https://github.com/pedropaulofb/ontouml-directkg/commit/31ee95dbc43cd411987862a81b80f6f8383e2761)
has independent Architect Reviewer OK. The [inventory](coverage.md#configurable-dkgm-vocabulary-delivery--alternative-a)
records the collected nodes, their fixture pairings and the validation commands.

The tests run the real file-based converter and CLI process. The invocation
adapter routes `--dkgm-vocabulary` to the CLI and uses the test request key
`dkgm_vocabulary` for Python keyword binding. The Python API's spelling is open.
The provenance reader interprets the effective mode from the configuration
entity's YAML using the existing key convention. The CLI and Python assertions
identify the separate source entity by the consumed file's checksum. The
warning reader interprets the native message and effect. The CLI observer
captures the event at conversion return and after delivery, then checks the
requested report against that native evidence.

At base `f6f48f9dc1d1815fc7277370c86e2a96f4ced29a`, the CLI rejects the explicit
flag and the Python converter has no mode control. Real default executions
verify the import and source mapping. The enabled provenance outputs omit the
effective mode.

The F1–F5 resubmission is based on `5578cc009c70bcf94e23b4154c06d849363e1488`.
`tests/support/dkgm.py` shares the scoped vocabulary assertions between
transformation and CLI tests. The correction exercises affirmative source-end
comments, the inverse label, retained asymmetry, an invalid CLI value and
best-effort recovery with a surviving bridge. The converter still lacks the
mode controls and effective-mode provenance. The invalid-value test reaches
the real parser but cannot exercise value rejection until it recognizes the
option. The inventory records the exact nodes and observed limits.
