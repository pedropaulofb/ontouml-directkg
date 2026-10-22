# DirectKG executable development tests

Wave 1 — Executable foundation, input policies, and general identity — received
the forwarded independent OK for `7364ed8843c565592d4bfa550d90c218988c83ba`.
Wave 2 — Classes, enumerations, higher-order classification, and source text —
received the forwarded independent OK for
`196d16b056668f3292e8309d545e6aaa49c90497`, verified reachable from remote main.
Wave 3 — Attributes, datatypes, property references, and source flags — is
submitted for independent review. Waves 4–6 remain unimplemented.
Behavioral baseline: [`documentation/specification/2026-10-21 - specification handoff.md`](../documentation/specification/2026-10-21%20-%20specification%20handoff.md)
at `7870042a02e094dca772d6fdd6570ad7b2d02578`.
Organization: [`documentation/specification/2026-10-21 - test suite structure.md`](../documentation/specification/2026-10-21%20-%20test%20suite%20structure.md), same commit.
The single requirement-to-test inventory, source evidence, exact data pairings,
and remaining scope are in [`coverage.md`](coverage.md).

## Run from the repository root

Use an isolated Python environment if desired. The observed environment is
Python 3.12; this does not establish production Python-version support.

```bash
python -m pip install -r tests/requirements.txt
python -m pytest --rootdir=. --collect-only -q tests
python -m pytest --rootdir=. -q tests -k 'fixture_contract or rdf_helper'
python -m pytest --rootdir=. -q tests --tb=short
```

For a focused run, replace `tests` with a repository-relative module or node
listed in `coverage.md`, keeping `--rootdir=.`. Running inside a test subdirectory
is not the supported convention. No pytest configuration is currently needed.
Dependencies are test-only; no production packaging is selected.

The fixture/harness subset runs independently of production. Intentionally
invalid source files are checked against their declared defects; one malformed
JSON file is expected not to parse. These passes do not certify transformation
behavior. The seven Turtle files are **partial ground-triple expectations**, not
complete conversion outputs. Pairings are explicit; integrity scans never infer
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

## Actual invocation binding

**Unbound:** the inspected repository has no production Python code, public
entry point, CLI command, or diagnostic API. Every conversion call currently
raises `tests.support.invocation.ImplementationUnavailable`. This is an ordinary
test failure, never a pass, skip or expected failure. No fake converter is used.

`tests/support/invocation.py` is the only implementation-dependent binding point.
Its protocol/dataclasses are test-side observation formats, **not proposed
production signatures, return types, exception classes, diagnostic codes or JSON
keys**. Once a real interface exists, implement the binding there and record the
verified public imports/calls here. Tests and fixtures keep their locations.

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
  or sequence output induced solely by GEN-05/PROP-04/05 characteristics, such
  as extra logical axioms, dependence, direction changes, value-order sequences,
  or properties generated solely to represent a flag. Exclude independently
  required mappings and permitted independent metadata. Document the actual
  RDF/interface evidence; never infer absence from the expected behavior.
- Bind `has_local_value_restriction_control()` to inspection of the real public
  Python controls for an optional local allValuesFrom feature. It is a test-side
  question, not a proposed production method or parameter spelling. The CLI
  counterpart remains in Wave 6. An unavailable interface must raise the
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
unless selected by the case. Default embedded provenance and file deliveries
belong to the already-planned later wave; this subset does not certify them.
Stored expectations are partial ground graphs. Checks between separate
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

The concrete stable DKGM URI is still unspecified. Import existence/no-fragment
checks do not certify a concrete target. Detailed vocabulary/bridge checks and
the remaining approved waves are recorded in the inventory. Wave 1/2 approvals
do not certify Wave 3, the concrete DKGM identity, or unavailable production
behavior. Wave 3 requires its own independent verdict before progression.

Attribute standalone `*` recognition is asserted. Its exact restriction graph
is recorded as blocked: DK-DIAG-11 includes attributes, but DK-REL-12's explicit
`*` to `0..*` mapping is limited to relations; DK-ATT-03 does not state that
single-value mapping. Explicit attribute intervals are tested independently.
