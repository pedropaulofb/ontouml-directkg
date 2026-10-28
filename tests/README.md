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
Behavioral baseline: [`documentation/specification/2026-10-21 - specification handoff.md`](../documentation/specification/2026-10-21%20-%20specification%20handoff.md)
at `7870042a02e094dca772d6fdd6570ad7b2d02578`.
Organization: [`documentation/specification/2026-10-21 - test suite structure.md`](../documentation/specification/2026-10-21%20-%20test%20suite%20structure.md), same commit.
The single requirement-to-test inventory, source evidence, exact data pairings,
and remaining scope are in [`coverage.md`](coverage.md).

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

Attribute standalone `*` recognition is asserted. Its exact restriction graph
is recorded as blocked: DK-DIAG-11 includes attributes, but DK-REL-12's explicit
`*` to `0..*` mapping is limited to relations; DK-ATT-03 does not state that
single-value mapping. Explicit attribute intervals are tested independently.

The approved exact-name blockers for present-but-unusable inverse roles and
unusable inverse-domain qualifiers remain. Eligibility, labels, direction and
source-backed identity are asserted independently. Five DK-REL-04 rows also lack
an explicit supported-field criterion for their directional semantic roles:
componentOf, historicalDependence, participational, subCollectionOf and
subQuantityOf. Ten direction cells assert only established-candidate safety;
18 assert an exact directional candidate. The inventory quotes the
relevant passages and records the targeted Architect question. Class labels and
aggregation flags are not invented as a semantic orientation convention.

Wave 4 reviewer correction F1 uses the exporter's `mode` stereotype for the
characterization/manifestation inputs and material-mode dependencies. These
positive mode inputs request `require-known`, so custom-stereotype acceptance
cannot stand in for a recognized encoding. The two externalDependence cells
also use `mode`, but assert only primary identity/direction and completion:
the specification does not establish whether this encoding supplies DK-REL-04's
"Extrinsic Mode" role. Exact lexical selection and its naming diagnostics remain
blocked for Architect clarification; no intrinsic/extrinsic alias is assumed.
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

In-memory and stdout clauses are conditional on observed supported capabilities;
no additional public input type, command syntax or entry point is invented. An
unbound inspection raises ImplementationUnavailable before these branches can pass.
A supported in-memory input has no invented original-file byte digest. Automatic
sidecar writing needs a concrete output path. Capability absence is non-applicability,
not certified execution of those clauses. An exact other-format rejection classification
is not added to the contract. Mixed-list invalid-value rejection and independent-field
preservation are asserted; exact valid-sibling retention is recorded as blocked for
Architect clarification in the inventory.

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

With Python 3.12.14 and pinned requirements, collection found 2612 nodes: 81 new
cases and nine necessary aggregation-function node renames. The focused command
in coverage.md executed 90 cases: 14 passed, 76 failed at missing RD-17 addition
assertions in the current transformer. All reached baseline RDF preconditions
passed. The previous combined 324-case regression selection passed. No skips or
xfails were introduced; the full suite and remaining unbound capabilities were not
executed. These are valid test-first production failures, not an accepted review
verdict or a passing implementation claim.
