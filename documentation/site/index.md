# Home

OntoUML DirectKG transforms supported OntoUML models into a domain-oriented RDF/OWL graph. Its classes and properties represent the modeled domain, rather than the OntoUML metamodel, Visual Paradigm diagrams, or the JSON document structure.

## Current availability

**These pages describe accepted intended behavior.** At the reviewed repository revision, `c2262aff7ce41a874875e354c9842fd97c8c879b`, no production conversion library, CLI, or supported installation mechanism exists. Python test material is present; that does not establish a working converter. Runnable installation, conversion, and Python API guidance is pending implementation and verification.

The website currently provides shared contracts and conceptual guidance. Detailed mapping pages, operational guides, and verified examples will be added through the approved documentation waves. Navigation links only to pages that exist.

## Scope at a glance

| Question | Accepted boundary |
| --- | --- |
| What input is supported? | VP-plugin 0.5.3-style OntoUML JSON, with the explicitly bounded language enrichment. Other exporter versions may work, but compatibility is not guaranteed. |
| What is generated? | Domain-oriented RDF/OWL; RDF 1.1 Turtle is the sole officially supported ontology serialization. |
| Which interfaces are required? | A Python library and a CLI with semantically equivalent transformation controls. |
| Does conversion validate OntoUML semantics? | No. Structural processability is required, while semantic mistakes and possible ontology inconsistency are not repaired. |
| Is information preserved without loss? | No. Some constructs have partial mappings, comment-only preservation, or intentional omission. |
| Is an OWL profile guaranteed? | No general OWL profile guarantee is established. |

## Find the relevant contract

- Start with [Semantics and limitations](concepts/semantics.md) to interpret the graph and its preservation boundaries.
- Read the [Input contract](reference/input.md) before preparing an export.
- Read the [Output contract](reference/output.md) to understand ontology identity, artifact formats, and graph-versus-text guarantees.
- Use [Controls](reference/controls.md) for the accepted option values, defaults, and interface boundaries.

## Relationship to other approaches

DirectKG aims for a comparatively lightweight graph of domain concepts and relations. It does not adopt gUFO imports or its UFO-based representation merely because gUFO is a related approach. It also avoids reproducing the source JSON's serialization machinery. This simplification does not authorize inventing semantics or discarding information beyond the accepted rules.

---

Governing source: §§2–3; baseline consolidated: **2026-10-21**; repository commit: `c2262aff7ce41a874875e354c9842fd97c8c879b`; source: [`documentation/specification/2026-10-21 - specification handoff.md`](https://github.com/pedropaulofb/ontouml-directkg/blob/c2262aff7ce41a874875e354c9842fd97c8c879b/documentation/specification/2026-10-21%20-%20specification%20handoff.md).
