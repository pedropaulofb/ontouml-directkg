# OntoUML DirectKG — Test Suite Structure and Location Specification

**Document version:** v2.
**Status:** Recommended structure; applicable when approved for the Test Engineer.
**Repository:** [pedropaulofb/ontouml-directkg](https://github.com/pedropaulofb/ontouml-directkg)
**Inspection date:** 21 October 2026.
**Inspected revision:** `main` at `8d11774e5cffd4d1678d75ba1fc43815714daad6`.

## 1. Purpose, scope, authority, and applicability

This document governs the locations, naming, shared support boundaries, and traceability records of the future executable DirectKG test suite. The Test Engineer and Test Reviewer retrieve this document directly from GitHub; their active instructions are in `documentation/prompts/test/`. It governs placement rather than the scope of an approved assignment. The [agent workflow](../prompts/README.md) requires Architect Reviewer OK before parallel documentation/testing assessment and both respective reviewer OKs before implementation; reviewed no-change results also close their own gates.

The current normative DirectKG specification remains authoritative for transformation behavior and acceptance criteria. At the inspected revision, that source is `documentation/specification/2026-10-05 - specification handoff.md`, titled *OntoUML DirectKG Current Specification*, with **Consolidated: 2026-10-04** in its header. The filename date and consolidation date are distinct. For new work, retrieve the current registered specification and applicable reviewed decision directly from GitHub; the dated source and repository inventory describe the historical inspection, not permanent current-source paths. Behavioral updates do not themselves change this layout.

Structural requirements in this document apply only to test organization. They establish no individual cases, assertion inventory, transformation mappings, diagnostic requirements, coverage quota, CI workflow, or production architecture. A folder, filename, inventory entry, or illustrative example is not evidence of required DirectKG behavior and must not resolve an open design issue.

Use `pytest` for executable tests and `rdflib` for RDF loading and comparison support. This is a suite-design choice, not a claim that either dependency is already configured. Apply the same structure to the approved baseline waves and later incremental additions.

## 2. Inspected repository baseline

The complete recursive tree of the inspected commit was available. No local project checkout was provided or found in the active workspace; this specification is grounded in remote `main`, with no local-versus-remote comparison available.

| Inspected path or area | Organizational significance |
| --- | --- |
| `documentation/specification/2026-10-05 - specification handoff.md` | Current repository normative baseline; §§5–14 organize general output, classes, higher-order classification, attributes/datatypes, properties/text, relations, inverses, instantiation, IRIs, and input/diagnostics. §15 establishes library/CLI targets without specifying a complete Python interface. §16 includes conformance matters and explicitly leaves detailed test-suite design unspecified. |
| `documentation/specification/2026-09-28 - specification handoff.md`; `documentation/specification/archive/` | Earlier handoffs and historical material; not the current baseline for new expectations. |
| `documentation/specification/2026-10-05 - remaining decisions handoff.md`; earlier remaining-decisions handoffs | Non-normative open-design-issues material; not an independent source of accepted test expectations. |
| `documentation/specification/prompts/` | Workflow prompts 01–06 exist; prompts 07–09 are absent from the inspected tree. Prompts are distinct from transformation requirements. |
| `dkgm-vocabulary-v1.0.0.ttl` | Existing vocabulary resource, not an expected graph for a conversion case. |
| `.gitignore` | Includes Python caches and test/coverage artifact exclusions; this does not establish an installed framework or working suite. |

No Python source files, package directory, CLI implementation, test directory, JSON test inputs, expected-output fixture collection, `pyproject.toml`, `pytest.ini`, `setup.cfg`, `tox.ini`, or dependency manifest exists in that tree. The layout below is therefore proposed rather than a description of implemented tests.

Repository evidence is pinned to [the inspected commit tree](https://github.com/pedropaulofb/ontouml-directkg/tree/8d11774e5cffd4d1678d75ba1fc43815714daad6). The authoritative source can be opened at [its inspected revision](https://github.com/pedropaulofb/ontouml-directkg/blob/8d11774e5cffd4d1678d75ba1fc43815714daad6/documentation/specification/2026-10-05%20-%20specification%20handoff.md).

## 3. Repository-relative layout

Use one top-level `tests/` directory. Organize transformation-facing modules by topic and keep process-facing CLI tests in a separate area. Keep reusable data and support code shared across those areas.

Legend: **E** = exists at the inspected revision; **P** = planned location, created only when approved work needs it; **C** = conditional planned location, subject to the stated condition. Angle-bracket names are path patterns, not literal directories or files. This is the relevant tree, not a complete listing of existing repository assets. Nothing marked P or C has been created by this specification.

```text
.
├── .gitignore                                      [E]
├── dkgm-vocabulary-v1.0.0.ttl                        [E]
├── documentation/                                  [E]
│   └── specification/                              [E; existing sources stay here]
│       ├── 2026-10-05 - specification handoff.md     [E]
│       └── test-suite-structure.md                  [P; approved copy of this attachment]
├── pytest.ini                                      [C; §7]
└── tests/                                          [P]
    ├── __init__.py                                 [P; test-support import namespace]
    ├── README.md                                   [P; operating notes]
    ├── coverage.md                                 [P; requirement-to-test inventory]
    ├── conftest.py                                 [P; shared pytest fixtures/wiring]
    ├── transformation/                             [P]
    │   ├── test_ontology.py                        [P]
    │   ├── test_classes.py                         [P]
    │   ├── test_higher_order.py                    [P]
    │   ├── test_attributes_datatypes.py            [P]
    │   ├── test_properties.py                      [P]
    │   ├── test_relations.py                       [P]
    │   ├── test_inverses.py                        [P]
    │   ├── test_iris.py                            [P]
    │   ├── test_labels.py                          [P]
    │   └── test_input_diagnostics.py               [P]
    ├── cli/                                        [C; approved CLI-facing work]
    │   └── test_cli.py                             [C]
    ├── support/                                    [P]
    │   ├── __init__.py                             [P; importable helper package]
    │   ├── data.py                                 [P; fixture paths and loading]
    │   ├── rdf.py                                  [P; RDF loading/comparison helpers]
    │   └── invocation.py                           [P; replaceable integration boundary]
    └── fixtures/                                   [P; versioned test data only]
        ├── transformation/                         [P]
        │   └── <topic>/<case_slug>/                 [P; topics from §4]
        │       ├── input.json                      [P; stored source input, when needed]
        │       ├── <input_slug>.json               [C; additional source input]
        │       ├── expected.ttl                    [P; stored graph expectation, when needed]
        │       ├── expected_<suffix>.ttl           [C; variant or companion graph]
        │       ├── metadata.yaml                   [C; single metadata input]
        │       └── metadata/<variant_slug>/metadata.yaml
        │                                           [C; multiple metadata inputs]
        ├── cli/                                    [C; CLI-specific data only]
        │   └── <case_slug>/                        [C; same artifact naming rules]
        └── shared/                                 [C; data reused across modules/areas]
            └── <fixture_slug>/                     [C; same artifact naming rules]
```

Do not pre-create unused modules, helper files, directories, or placeholder data to fill this tree. The two `__init__.py` files provide the test-support namespace used with the invocation convention in §7; they do not select a production package layout. Data directories are not Python packages.

## 4. Test placement and topic ownership

Choose the module by the behavior being examined, not by which production function happens to implement it. The following table allocates locations; it is not a list of required cases or implementation-wave contents.

| Module under `tests/transformation/` | Fixture topic | Responsibility |
| --- | --- | --- |
| `test_ontology.py` | `ontology` | Overall output organization, ontology-level information, external descriptive metadata, provenance, and general source-container omissions. |
| `test_classes.py` | `classes` | Classes, class generalization/disjointness/generalization sets, enumeration representation and enumeration-specific literal identity/IRIs/labels, and class-specific characteristics. |
| `test_higher_order.py` | `higher_order` | Higher-order classification, categorizers, powertypes, and explicit instantiation associations. |
| `test_attributes_datatypes.py` | `attributes_datatypes` | Attribute transformation, attribute constraints, and primitive/custom datatype handling. |
| `test_properties.py` | `properties` | Shared property identity requirements, subsetting/redefinition, and property-specific characteristics. |
| `test_relations.py` | `relations` | Primary relation transformation, relation-specific lexical naming and primary-relation label modes, relation constraints/generalizations, derivations, chains, and mereology. |
| `test_inverses.py` | `inverses` | Generated inverses and their particular naming, identity, and relationship behavior. |
| `test_iris.py` | `iris` | General IRI construction, normalization/escaping, collision resolution, source-ID annotations, and identity/determinism matters spanning domains. |
| `test_labels.py` | `labels` | Shared label, source-description, and language conventions across resource kinds. |
| `test_input_diagnostics.py` | `input_diagnostics` | Cross-cutting input/stereotype-policy handling, transformation outcomes, and programmatic diagnostic/report access. |

An entity's domain/range, annotations, control effects, and accompanying diagnostics may be examined with its owning transformation behavior. Keep such integrated checks together. Use `test_labels.py`, `test_iris.py`, or `test_input_diagnostics.py` when the shared convention itself is the focus. Generated-inverse naming stays with inverses. Primary-relation lexical name selection and tests centered on primary-relation label modes (`--relation-labels`, DK-LBL-01) stay with relations. Tests centered on enumeration-specific literal identity, IRIs, and labels (DK-IRI-08) stay with classes. General IRI processing stays with IRIs; shared label and language conventions across resource kinds stay with labels, including when enumeration values participate. These rules prevent a single scenario from being duplicated simply because it cites several rule families.

Cross-domain work belongs in the module whose behavior motivates it. Record all applicable authoritative references in the inventory rather than adding a generic `integration/`, `misc/`, or per-rule directory. A coherent module may contain several related rules and multiple functions.

`tests/cli/test_cli.py` contains approved tests whose distinguishing target is the command-line process interface or delivery through that interface. Transformation semantics remain in their topical modules. CLI tests may reuse transformation bundles under the promotion rule in §8; use `fixtures/cli/` only for data particular to CLI-facing work. CLI inclusion is conditional on the approved wave, not a statement that DirectKG's normative CLI obligations are optional.

Tests of public Python-library behavior use the topical transformation modules. No `unit/` hierarchy mirroring unconfirmed production internals is prescribed.

## 5. Naming, data pairing, and traceability

### Test identifiers

Use `test_<topic>.py` modules and `test_<behavior_slug>` function names, with lowercase snake_case identifiers. Do not put wave numbers, specification revision dates, or one rule ID per filename into the layout. Use explicit, stable parameter IDs for parametrized cases.

Give each stored bundle a key with the following repository-relative path mapping:

| Bundle key | Directory |
| --- | --- |
| `<topic>/<case_slug>` | `tests/fixtures/transformation/<topic>/<case_slug>/` |
| `cli/<case_slug>` | `tests/fixtures/cli/<case_slug>/` |
| `shared/<fixture_slug>` | `tests/fixtures/shared/<fixture_slug>/` |

Reserve `cli` and `shared` for those key prefixes, not transformation-topic names. Slugs describe their purpose and use lowercase snake_case. A module may reference several bundles, and a bundle may support several related tests.

### Fixture filenames and pairing

Store an input and its expected RDF graphs together under the relevant case directory, except when inputs or expectations are reused from `shared/` under §8. For cross-bundle pairings, identify all bundle keys and the exact input/expectation paths explicitly. Use `input.json` for the principal OntoUML source and `expected.ttl` for a single principal graph expectation. Turtle is the default representation of stored RDF expectations; this choice imposes no new production serialization requirement.

When one input supports multiple configurations or companion graph artifacts, use distinct descriptive names of the form `expected_<suffix>.ttl`. Select the precise input, expectation, and variant explicitly in the test and inventory; never infer pairing solely by directory globbing. A companion provenance expectation, when needed by approved work, can use `expected_provenance.ttl`. Additional source JSON documents use descriptive `<input_slug>.json` names in the same bundle, with their roles recorded explicitly. Use `metadata.yaml` at the bundle root for a single stored external metadata input. When the same source input needs several metadata inputs, store each as `metadata/<variant_slug>/metadata.yaml`, preserving the basename rather than suffixing it. Select each metadata path explicitly in the test and inventory; these paths do not prescribe which metadata cases must be implemented.

These are storage conventions only. A case need not have a stored JSON input or a complete expected graph when its approved design does not need one. The existence of `expected.ttl` does not establish whole-graph equality, byte-for-byte Turtle equality, inference, or a policy for variable values. The normative specification and approved test design determine the appropriate comparison.

### Requirement-to-test inventory

Maintain one inventory at `tests/coverage.md`. Its header identifies the behavioral baseline by repository path and commit, or by the exact supplied authoritative document revision, and identifies any subsequently accepted decision references actually used.

For each implemented behavioral test, record:

- Authoritative rule IDs, or an exact normative section reference where no stable rule ID exists.
- Repository-relative pytest node ID, including parameter ID when the mapping differs between parameter rows.
- Case key and exact fixture paths, or an explicit indication that no stored fixture is used.
- The approved wave or later decision reference that introduced or revised the entry.

Record the same rule IDs in a `Rules:` line in the test function's docstring. A function-wide list may cover several parameter rows; the inventory must distinguish rows when their rule associations differ. `RD-*` and `ODI-*` decision references may supplement normative references but must not substitute for an available normative rule ID. Do not invent IDs for unnumbered requirements.

The inventory maps requirements to executable locations; it is not another specification, an assertion checklist, or a coverage target. It may grow with the approved waves. Distinguish any planned entries from implemented ones; an implemented location does not by itself certify passing execution or complete coverage of a rule. Keep node IDs, paths, and references synchronized when tests move or change.

## 6. Shared support boundaries

| Location | Boundary |
| --- | --- |
| `tests/conftest.py` | Common pytest fixtures and wiring of data paths, temporary locations, and the invocation adapter. Keep ordinary reusable logic in `support/`. Keep fixtures used only by one module local to that module. |
| `tests/support/data.py` | Repository-independent resolution of fixture paths relative to the suite and loading of stored inputs/expectations. It must not depend on the caller's working directory or silently repair input data. |
| `tests/support/rdf.py` | Shared `rdflib` graph-loading and comparison utilities. Keep DirectKG-specific expected behavior in tests and reviewed fixture data rather than embedding transformation rules in this helper. |
| `tests/support/invocation.py` | The replaceable test-side boundary for actual public-library imports/calls and CLI invocation. Confine implementation-dependent entry-point knowledge and response adaptation here. |

Use absolute imports with the `tests.support` prefix for shared helper modules, under the invocation convention in §7.

Test modules express requests and inspect observed results through the test-side invocation boundary. Bind it to the real supported interface available for the approved wave. This document prescribes no DirectKG module name, import path, function signature, return type, exception hierarchy, or CLI executable command. Public-interface details explicitly established by the authoritative specification remain applicable when the binding is implemented.

Replacing the binding must not require relocating topical tests or fixtures. The boundary may adapt interface representations; it must not fabricate a converter or implement transformation mappings to supply missing production behavior. Record the actual binding and any unavailable target in `tests/README.md`. This layout does not choose a skip, expected-failure, or other execution policy for an implementation that is not yet available.

Shared data means checked-in input/expectation files under `fixtures/`; shared pytest fixtures mean runtime objects declared through pytest. Keep these concepts and their locations distinct. Do not add helper modules to data directories or collect support files as `test_*.py`.

## 7. Test documentation and configuration

After approval, the repository copy of this document belongs at `documentation/specification/test-suite-structure.md`. Maintain a single canonical copy there.

`tests/README.md` contains concise operating notes: the active behavioral baseline and inventory links, how to run the currently implemented suite, the actual invocation binding, any test configuration location, and justified structural exceptions. It must not duplicate transformation requirements or become a second coverage inventory.

No new pytest configuration is required merely to adopt this layout. Run the implemented suite from the repository root using `python -m pytest --rootdir=. tests`. For a subset, replace `tests` with the selected repository-relative path or node ID while retaining `--rootdir=.`. Record the supported command in `tests/README.md`; invocation from inside a test subdirectory is not the supported convention. The `python -m` invocation makes the working directory available to Python imports, while `--rootdir=.` fixes the root for inventory node IDs; setting `rootdir` alone does not configure imports. See the [pytest import documentation](https://docs.pytest.org/en/stable/explanation/pythonpath.html) and [rootdir documentation](https://docs.pytest.org/en/stable/reference/customize.html#initialization-determining-rootdir-and-configfile).

If approved executable work needs configuration before a repository-wide pytest configuration exists, place the single standalone configuration at root `pytest.ini`. If the repository already has an authoritative pytest configuration when that work starts, use it instead and record its location in `tests/README.md`. Do not introduce competing pytest configurations or per-wave configuration files. Dependency declarations follow the repository's actual dependency mechanism when established; this document does not choose production packaging or dependency versions.

## 8. Reuse and generated artifacts

A bundle stays under its owning topic in `tests/fixtures/transformation/` while it is referenced only by that topic's module(s), including modules split from it under §10. When a different topic or `tests/cli/` needs one or more of its files, move those reused files into a canonical bundle at `tests/fixtures/shared/<fixture_slug>/`. Leave consumer-specific files, including expectations that differ between consumers, in their owning case directories. Apply the same promotion rule to CLI-specific data needed by a transformation module. Update every affected reference and inventory entry in the same change, explicitly pairing inputs and expectations across affected bundles under §5. Reuse the canonical shared data rather than copying it into another area or a new wave.

Keep case-specific companions in their case directory and name their roles explicitly. Inline small case-specific values may remain in the test module. Do not introduce a builder framework or a fixture catalogue beyond these locations unless approved work demonstrates a concrete need.

`tests/fixtures/` holds reviewed, versioned test data, not converter output from test runs. Write generated ontologies, sidecars, exports, logs, and scratch files to pytest-managed temporary locations. Do not write runtime output into fixture directories, overwrite expectations as a side effect of test execution, or commit generated caches and reports as fixture data. This document creates no additional artifacts/report directory.

The existing root vocabulary stays at its current location. If approved work uses it as an input resource, refer to that resource explicitly; do not rename it or treat it as an entire case's expected conversion output.

## 9. Applying the structure across waves

Each approved baseline assignment and later incremental decision uses the same suite root, topical ownership table, data naming, support boundary, and inventory. Extend existing topical modules or bundles where the new work belongs. Create only the additional files needed for that approved work.

Record wave and decision provenance in `tests/coverage.md`, not in directory names or duplicate copies. Do not create `wave_1/`, separate baseline/incremental suites, temporary parallel layouts, or replacement suites for review/correction rounds. Active role prompts govern execution and review; this structure document governs placement only.

When a test or fixture is superseded, revise or remove it in its canonical location as authorized and update the inventory. Preserve meaningful existing case and parameter IDs where possible. Any necessary move must update imports, data references, and inventory links in the same change.

## 10. Extensions and exceptions

Routine additions of cases, functions, parameter rows, or companion data within these locations need no separate structural approval beyond the approval governing their wave or decision.

A module that becomes difficult to navigate may be split into coherent `test_<topic>_<subtopic>.py` files in the same area. Retain the original fixture topic and update the inventory; do not split mechanically by rule ID. An additional topical module may be introduced for an accepted behavioral area that genuinely does not fit the table, using the same naming and data pattern. Record a brief placement justification and the new topic in `tests/README.md`; no unused categories are needed in advance.

Changing the suite root, the transformation/CLI separation, the fixture pairing scheme, or the shared-support boundary requires an explicitly approved structural revision before implementation. Document the rationale and the approved replacement convention, and update this specification and affected references together. Do not establish an alternative layout through an undocumented exception.

