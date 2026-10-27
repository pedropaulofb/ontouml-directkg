# Contributing

Community contributions to OntoUML DirectKG are welcome. Use [GitHub Issues](https://github.com/pedropaulofb/ontouml-directkg/issues) to report problems, ask project-related questions, or suggest improvements, and [Pull Requests](https://github.com/pedropaulofb/ontouml-directkg/pulls) to contribute documentation, fixes, or new functionality. See the [complete contribution guide](https://github.com/pedropaulofb/ontouml-directkg/blob/28b05b60e725dab3366a8019deb031626d9ab22d/CONTRIBUTING.md) for practical guidance.

The software uses the [Apache License 2.0](https://github.com/pedropaulofb/ontouml-directkg/blob/28b05b60e725dab3366a8019deb031626d9ab22d/LICENSE). The [mereology vocabulary](https://github.com/pedropaulofb/ontouml-directkg/blob/28b05b60e725dab3366a8019deb031626d9ab22d/vocabulary/latest/dkgm-vocabulary.ttl) adopts the [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/) license.

OntoUML DirectKG is independently maintained as a personal side project. The maintainer welcomes constructive feedback and works to address issues, review contributions, and maintain and improve the project as time and resources permit. Response times and continuous support are not guaranteed.

The repository currently contains documentation, the mereology vocabulary and its publication tools, and development tests. It has no production conversion library, CLI, or supported installation mechanism at the consulted revision. The checks below concern the available repository material.

## Contributing

Use the current accepted sources before changing a documented behavior:

| Source | Responsibility |
| --- | --- |
| [Current consolidated specification](https://github.com/pedropaulofb/ontouml-directkg/blob/9e52a66af43e39b374d0a642298b1117d12be4d8/documentation/specification/2026-10-21%20-%20specification%20handoff.md) | Product behavior, supported inputs, limitations, controls, and documentation requirements. Consolidated **2026-10-21**; consulted commit `9e52a66af43e39b374d0a642298b1117d12be4d8`; source path `documentation/specification/2026-10-21 - specification handoff.md`. |
| [Approved documentation structure v2.0](https://github.com/pedropaulofb/ontouml-directkg/blob/9e52a66af43e39b374d0a642298b1117d12be4d8/documentation/specification/ontouml-directkg-documentation-structure.md) | Public page inventory, paths, navigation, content ownership, and writing/maintenance conventions. |
| [Test Suite Structure and Location Specification v2](https://github.com/pedropaulofb/ontouml-directkg/blob/9e52a66af43e39b374d0a642298b1117d12be4d8/documentation/specification/2026-10-21%20-%20test%20suite%20structure.md) | Separate test-organization document. Its header states “Recommended structure; applicable when approved for the Test Engineer.” Current [test instructions](https://github.com/pedropaulofb/ontouml-directkg/blob/9e52a66af43e39b374d0a642298b1117d12be4d8/tests/README.md) record its use and test-review status. It does not define product mappings or production architecture. |

Archived specifications, unresolved-decision records, prompts, and observed implementation behavior do not silently amend the accepted baseline. Bring a material conflict to the project owner with the exact passages and revision. Keep accepted intended behavior, verified functionality, and pending implementation-dependent guidance distinct.

## AI-assisted development and prompts

For human and AI responsibilities, see [Authorship and independence](../index.md#authorship-and-independence). Published workflow instructions are available in [`documentation/prompts/`](https://github.com/pedropaulofb/ontouml-directkg/tree/1dcdc76137a617a737e30aef7899e7ed769e2538/documentation/prompts).

These files contain role instructions, not a complete history of development prompts or conversations. They do not identify which prompt revision produced each artifact.

## Documentation maintenance

Public sources live in `documentation/site/`. Internal specifications live in `documentation/specification/`, and AI workflow prompts live in `documentation/prompts/`. Both remain outside the website build root. Root `zensical.toml` owns navigation and the `site/` output directory. Keep generated HTML out of committed sources.

Update the existing content owner: [Controls](../reference/controls.md) for selectable behavior/defaults, [Diagnostics](../reference/diagnostics.md) for policies/outcomes, [CLI](../guides/cli.md) for exit codes, [Identifiers](../reference/identifiers.md) for identity, and the relevant mapping/metadata page for its transformation detail. Link from related pages rather than copying canonical tables or algorithms.

Preserve public paths and required section anchors. Use relative Markdown links between public pages and commit-pinned repository links for internal sources. Navigation must contain only pages that exist. Structural changes follow the approved structure's exception process.

When adopting a new consolidated baseline, verify the affected explanations, defaults, exceptions, examples, and links. Refresh their governing-rule notes with the consolidation date, full consulted SHA, and direct source-file link. Refresh the current-source links in this page and the README; retain valid historical citations on unaffected material.

Maintain one canonical [downloadable example pair](../examples/index.md#downloadable-pairs). Parse complete JSON, check declaration-ID uniqueness and reference resolution, and compare the chosen structures with the supported exporter contract. Parse Turtle and check its claimed mappings. State configuration, source provenance, adaptations, omitted content, and whether a converter actually produced it. An RDF parser pass alone does not validate DirectKG semantics or an OWL profile.

### Docstrings and API generation

Zensical builds the site; mkdocstrings and its Python handler are configured in `zensical.toml`. No public production modules/docstrings currently exist to render. The reserved Getting started and Python API pages are pending and absent from navigation; this is an implementation dependency, not completed API coverage.

Once real public source and installation/conversion mechanics are available and verified, populate the approved destinations. Curated mkdocstrings directives must resolve actual public objects and derive signatures/docstrings from source during the build. Keep usage narrative in the Python guide. Correct source/docstring defects through separately authorized code work; do not hand-copy signatures, expose test helpers as the product API, or add unresolved imports to obtain an API page.

### Build and preview

Run from the repository root in an isolated Python environment. The documentation workflow uses Python **3.12**; this is tooling evidence, not a supported production Python-version range. `requirements-docs.txt` pins documentation dependencies only.

```bash
python -m pip install -r requirements-docs.txt
python -m zensical build --clean --strict
```

For a local preview:

```bash
python -m zensical serve
```

Open the URL printed by the server and stop it with Ctrl+C. Inspect the changed pages, code blocks, navigation, anchors, and downloads. A successful build does not execute the converter or prove publication.

The [vocabulary publication workflow](https://github.com/pedropaulofb/ontouml-directkg/blob/9e52a66af43e39b374d0a642298b1117d12be4d8/.github/workflows/publish-vocabulary.yml) validates vocabulary artifacts and calls the [documentation workflow](https://github.com/pedropaulofb/ontouml-directkg/blob/9e52a66af43e39b374d0a642298b1117d12be4d8/.github/workflows/docs.yml). The latter builds Zensical, copies existing `vocabulary/latest/` and `vocabulary/versioned/` into `site/vocabulary/`, and uploads only `site/` before deployment. A standalone local Zensical command does not perform that additional asset-copy step. Verify the actual Actions run, uploaded artifact, and live routes when reporting publication.

## Verified development checks

The current development-test instructions provide these independent collection and fixture/RDF-helper checks:

```bash
python -m pip install -r tests/requirements.txt
python -m pytest --rootdir=. --collect-only -q tests
python -m pytest --rootdir=. -q tests -k 'fixture_contract or rdf_helper'
```

They check available test scaffolding and fixture integrity; they do not certify transformation behavior. Conversion-facing tests use an unbound adapter and cannot exercise a production converter yet. A full-suite pass is not claimed. Follow the [current test instructions](https://github.com/pedropaulofb/ontouml-directkg/blob/9e52a66af43e39b374d0a642298b1117d12be4d8/tests/README.md) and [coverage inventory](https://github.com/pedropaulofb/ontouml-directkg/blob/9e52a66af43e39b374d0a642298b1117d12be4d8/tests/coverage.md) for actual case ownership, pairings, review status, and pending bindings.

The publisher also runs the vocabulary unit checks:

```bash
python -m pip install -r vocabulary/scripts/requirements.txt
python -m unittest discover -s vocabulary/scripts/tests -v
```

See the [vocabulary maintenance instructions](https://github.com/pedropaulofb/ontouml-directkg/blob/main/vocabulary/README.md) before any vocabulary release work, including the narrowly scoped pre-release identity correction. The [accepted DKGM import identity](../mapping/mereology.md#import-and-vocabulary-identity) is fixed; publication tests do not certify unavailable converter behavior or live resolution. DK-CONF-04 establishes no separate coverage threshold or detailed testing framework requirement.

---

Governing rules: §§2.2–2.3, 15; DOC-FRAMEWORK; DK-CONF-04; approved documentation structure §§8–12; baseline consolidated: **2026-10-21**; repository commit: `9e52a66af43e39b374d0a642298b1117d12be4d8`; source: [`documentation/specification/2026-10-21 - specification handoff.md`](https://github.com/pedropaulofb/ontouml-directkg/blob/9e52a66af43e39b374d0a642298b1117d12be4d8/documentation/specification/2026-10-21%20-%20specification%20handoff.md).
