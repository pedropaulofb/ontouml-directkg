# OntoUML DirectKG

[![License: Apache-2.0](https://img.shields.io/github/license/pedropaulofb/ontouml-directkg?style=flat-square)](LICENSE)
[![Project stage: specification and tests](https://img.shields.io/badge/status-specification%20%26%20tests-blue?style=flat-square)](tests/README.md)
[![Last commit on main](https://img.shields.io/github/last-commit/pedropaulofb/ontouml-directkg/main?style=flat-square)](https://github.com/pedropaulofb/ontouml-directkg/commits/main)

<p align="center"><img src="branding/ontouml-directkg-logo-transparent.png" alt="OntoUML DirectKG logo" width="480"></p>

**OntoUML DirectKG** is an open-source project to transform [OntoUML](https://ontouml.org/) conceptual models into **domain-oriented RDF/OWL ontologies**. The intended output describes the modeled domain—its classes, properties, and selected logical constraints—rather than reproducing the OntoUML metamodel, diagrams, or JSON export structure.

It is intended for OntoUML modelers, ontology engineers, knowledge-graph developers, and contributors implementing the transformation.

> **Current status: specification and initial tests, not a working converter.** This repository contains an accepted transformation specification, a reusable mereology vocabulary, and development tests. It **does not yet provide an installable DirectKG Python library or executable CLI**. The transformation features below are *specified*, not available for use.

## Authorship and independence

OntoUML DirectKG was independently conceived and developed by **[Pedro Paulo Favato Barcelos](https://w3id.org/pedropaulofb)**, its sole creator, author, and developer. Profiles: [GitHub](https://github.com/pedropaulofb), [ORCID](https://orcid.org/0000-0003-2736-7817), and [LinkedIn](https://www.linkedin.com/in/pedro-paulo-favato-barcelos/).

The project is a personal contribution to the OntoUML community and its broader ecosystem. It is **not an official OntoUML project, tool, or implementation**, and it is not endorsed by the OntoUML maintainers.

## Intended transformation

| Aspect | Specified behavior |
| --- | --- |
| **Input** | OntoUML JSON exported by the Visual Paradigm [`ontouml-vp-plugin` 0.5.3](https://github.com/OntoUML/ontouml-vp-plugin/releases/tag/0.5.3), with bounded support for localized text. Other exporter versions are not guaranteed. |
| **Output** | Domain-oriented RDF/OWL ontology; **RDF 1.1 Turtle** is the sole officially specified ontology serialization. |
| **Interfaces** | A Python library and CLI with equivalent transformation behavior; their production entry points do not yet exist. |

The [normative specification](documentation/specification/2026-10-21%20-%20specification%20handoff.md) defines mappings for:

- **Domain structure:** classes, generalizations, attributes, datatypes, binary relations, and applicable cardinality or generalization-set constraints.
- **Selected OntoUML semantics:** higher-order classification, enumerations, named inverse properties, and controlled material-relation property chains.
- **Mereology:** source-specific properties linked to generic `memberOf`, `subCollectionOf`, `subQuantityOf`, and `componentOf` properties in a reusable DirectKG vocabulary.
- **Identity and reporting:** generated IRIs, multilingual labels, configurable input-handling policies, diagnostics, outcomes, and provenance.

The design intentionally **does not perform general OntoUML semantic validation** or guarantee a particular OWL profile. It does not require gUFO or OntoUML-metamodel imports. Diagram layout, package organization, and custom `propertyAssignments` are outside the domain-graph output scope.

## Explore the repository

| Resource | What it provides |
| --- | --- |
| [Current specification](documentation/specification/2026-10-21%20-%20specification%20handoff.md) | Authoritative requirements for mappings, controls, and intended behavior. |
| [Mereology vocabulary](vocabulary/latest/dkgm-vocabulary.ttl) | Current Turtle representation of the four generic mereological properties and their accepted generic chains; archived releases and PyLODE documentation are maintained under [`vocabulary/`](vocabulary/README.md). **Not** conversion output. |
| [Tests](tests/README.md) and [coverage inventory](tests/coverage.md) | Initial executable tests, fixtures, traceability, and the missing production-integration boundary. |
| [Open design issues](documentation/specification/2026-10-21%20-%20remaining%20decisions%20handoff.md) | Non-normative, incomplete record of unresolved questions. |
| [Documentation structure](documentation/specification/2026-10-21%20-%20documentation%20structure.md) | Approved page organization and responsibilities; public website sources are under `documentation/site/`. |

## Getting started with the current repository

**Converter installation and usage are not available yet.** The following commands clone the repository, install **test-only** dependencies (`pytest` and `rdflib`), collect the tests, and run checks that do not require production conversion code:

```bash
git clone https://github.com/pedropaulofb/ontouml-directkg.git
cd ontouml-directkg
python -m pip install -r tests/requirements.txt
python -m pytest --rootdir=. --collect-only -q tests
python -m pytest --rootdir=. -q tests -k 'fixture_contract or rdf_helper'
```

These commands **do not install or run DirectKG**. The conversion-facing tests currently call an unbound adapter in [`tests/support/invocation.py`](tests/support/invocation.py) and fail until a real public conversion interface is connected. Refer to the [test instructions](tests/README.md) before attempting a full test run. The observed test environment uses Python 3.12; no supported production Python-version range has been established.

## Documentation and development

The current source of truth is the [consolidated specification](https://github.com/pedropaulofb/ontouml-directkg/blob/9e52a66af43e39b374d0a642298b1117d12be4d8/documentation/specification/2026-10-21%20-%20specification%20handoff.md), not the archived specifications or unresolved-issues record. Baseline consolidated: **2026-10-21**; repository commit: `9e52a66af43e39b374d0a642298b1117d12be4d8`; source path: `documentation/specification/2026-10-21 - specification handoff.md`. Development tests document expected behavior but **do not demonstrate a working implementation**.

The [documentation website](https://w3id.org/directkg/docs) uses **Zensical**, with **mkdocstrings** configured for future source-derived API references. Start with [Home](documentation/site/index.md), [Semantics and limitations](documentation/site/concepts/semantics.md), [Input contract](documentation/site/reference/input.md), [Output contract](documentation/site/reference/output.md), and [Controls](documentation/site/reference/controls.md). [Examples](documentation/site/examples/index.md) provides a checked Catalog adaptation and illustrative Turtle excerpt. [Contributing](documentation/site/development/contributing.md) covers documentation maintenance, build/preview, and available development checks. No production installation command, Python API example, CLI invocation, or generated API reference can be verified at this stage; Getting started and generated API pages remain pending implementation.

Available mapping pages cover [Classes and enumerations](documentation/site/mapping/classes.md), [Higher-order classification](documentation/site/mapping/higher-order.md), and [Attributes and datatypes](documentation/site/mapping/attributes-and-datatypes.md). Further mappings explain [Binary relations](documentation/site/mapping/relations.md), [Inverse properties](documentation/site/mapping/inverses.md), [Property features](documentation/site/mapping/property-features.md), [Derivations and material chains](documentation/site/mapping/derivations-and-chains.md), [Mereology and DKGM](documentation/site/mapping/mereology.md), and [Instantiation associations](documentation/site/mapping/instantiation.md). Shared references explain [Identifiers and naming](documentation/site/reference/identifiers.md) and [Labels, comments, and language](documentation/site/reference/text.md).

Contract-based guides explain the [CLI](documentation/site/guides/cli.md), [Python integration](documentation/site/guides/python.md), and [Metadata and provenance](documentation/site/guides/metadata-and-provenance.md). [Diagnostics and recovery](documentation/site/reference/diagnostics.md) covers accepted policies, outcomes, and diagnostic conditions; these pages do not establish runnable interfaces.

Root `zensical.toml` owns the site configuration and navigation. `.github/workflows/docs.yml` builds public sources from `documentation/site/` into `site/` and includes the existing vocabulary publications. The vocabulary workflow calls this single publisher after preparing its artifacts. Internal specifications and prompts stay outside the public source root. GitHub Pages publication still depends on repository settings and a successful deployment; configured workflows alone do not establish a live website.

## Persistent identifiers

DirectKG registers persistent URLs under `https://w3id.org/directkg/` so its resource identifiers can remain stable when hosting destinations change. Useful entry points include:

- [Documentation](https://w3id.org/directkg/docs) — `https://w3id.org/directkg/docs`
- [Source repository](https://w3id.org/directkg/git) — `https://w3id.org/directkg/git`
- [Current DKGM ontology](https://w3id.org/directkg/vocab/dkgm) — `https://w3id.org/directkg/vocab/dkgm`
- [Turtle representation](https://w3id.org/directkg/vocab/dkgm/ttl) — `https://w3id.org/directkg/vocab/dkgm/ttl`

See [Persistent identifiers and redirects](documentation/site/reference/persistent-identifiers.md) for the **canonical inventory of all 14 redirect-rule families**, vocabulary term IRIs, HTTP behavior, version patterns, and examples. The [official W3ID configuration](https://github.com/perma-id/w3id.org/blob/master/ids/directkg/.htaccess) controls the redirects; registration does not guarantee published destinations. The accepted mandatory DKGM import is `https://w3id.org/directkg/vocab/dkgm`. The new DKGM routes await review and integration of the coordinated W3ID branch; these source changes do not establish live availability.

## License

The repository includes the [Apache License 2.0](LICENSE). The [mereology vocabulary](vocabulary/latest/dkgm-vocabulary.ttl) separately declares **CC BY 4.0** in its RDF metadata.
