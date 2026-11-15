# OntoUML DirectKG — Documentation Structure and Location Specification

**Document version:** 2.0  
**Status:** Proposed structure; applicable after project-owner approval.  
**Prepared:** 21 October 2026.  
**Repository:** [pedropaulofb/ontouml-directkg](https://github.com/pedropaulofb/ontouml-directkg).  
**Inspected default branch:** `main`.  
**Inspected commit:** `7870042a02e094dca772d6fdd6570ad7b2d02578`.  
**Normative baseline:** `documentation/specification/2026-10-21 - specification handoff.md`, titled *OntoUML DirectKG Current Specification*, **Status: Consolidated normative baseline**, **Consolidated: 2026-10-21**. No numbered specification revision or DirectKG release version is asserted by that header.

**Workflow maintenance — 2026-10-30:** Current role references follow the [agent workflow](../prompts/README.md). The evidence inventory and commit-pinned sources below retain their historical inspection context; discover the latest accepted specification directly from GitHub for new work. This maintenance changes workflow references only, not page responsibilities or transformation behavior.

## 1. Purpose, authority, and scope

This document governs the organization, repository locations, page responsibilities, navigation, content traceability, and maintenance conventions of DirectKG documentation. It supplies a page-level plan for subsequent documentation work. It does not create the pages or establish a working documentation website.

Four kinds of material have separate authority:

| Material | Authority and responsibility |
| --- | --- |
| Current normative DirectKG specification | Defines transformation behavior, accepted controls, defaults, diagnostics, and product boundaries. The Architect owns its consolidation and registration, subject to independent Architect Reviewer validation. Its §1 identifies §§2–16 as accepted scope and behavior. |
| This structure specification | Defines where and how that behavior is documented. Its organizational choices take effect when approved. It cannot amend transformation semantics, select unspecified APIs, or resolve a pending product decision. |
| Public user and developer documentation | Explains the accepted behavior and, where verified, its implemented use. It is derived guidance and reference material, not a second transformation specification. |
| Historical handoffs, open-design-issues notes, and workflow prompts | Preserve history or govern their respective workflows. Their proposals and alternatives do not establish accepted transformation requirements. |

An owner-approved decision becomes eligible for documentation/testing assessment after the Architect registers it in the current specification and/or open issues and the Architect Reviewer returns OK. Documentation and testing may proceed in parallel; implementation follows both reviewers' accepted dispositions, including no-change. Retrieve authoritative repository files directly from GitHub. If the decision and registered baseline conflict, identify exact passages and obtain an explicit resolution through the Architect; documentation authors must not reconstruct or edit the normative baseline. [N1] §1; [W1]; [W2]

This document excludes documentation-page drafting, website configuration or deployment, source-code implementation, package design, test-suite design, and changes to Documentation Engineer or Reviewer prompts. It establishes no implementation waves, release schedule, or new software functionality.

## 2. Evidence baseline and source authority

### 2.1 Repository findings

The complete recursive tree at the inspected commit was available and was not truncated. GitHub identified `main` as the default branch. The commit is dated 21 October 2026 and adds the October 21 handoffs while archiving earlier ones. Authority is established by the specification's own status and §1, supported at that historical revision by the then-active specification-maintenance workflow; the filename and commit date alone are insufficient. [R1]; [N1]; [P1]; [P2]

| Observed material | Finding and consequence |
| --- | --- |
| `documentation/specification/2026-10-21 - specification handoff.md` | Current repository consolidated normative baseline. Documentation requirements include DOC-FRAMEWORK in §2.3 and explicit explanation obligations throughout the rule sections. |
| `documentation/specification/2026-10-21 - remaining decisions handoff.md` | Identifies itself as non-normative and incompletely reconciled. It is not a source of additional accepted requirements and cannot override the consolidated baseline. |
| `documentation/specification/2026-10-21 - test suite structure.md` | Separate proposed test-organization specification, conditional on approval. It records an earlier inspection commit. Its historical paths and observations are not current-repository facts. |
| `documentation/specification/archive/` | Earlier specification and remaining-decisions handoffs. Retain as history. |
| `documentation/specification/prompts/` | Historical prompt location at this inspected revision. Current role-specific prompts are in `documentation/prompts/`; retired workflow instructions remain only as history. |
| `dkgm-vocabulary-v0.1.0.ttl` | Historical baseline artifact; its concrete URI did not settle the then-unselected normative import target. The 2026-10-24 decision now fixes the identity under DK-GEN-04 and corrects the current versioned artifact in place. See §11. |
| `logos/`; `LICENSE`; `.gitignore` | Existing branding, repository license, and ignore rules. The ignore rules already cover root `/site`; template comments about documentation tools do not establish an implemented toolchain. |

There is no README, public documentation source tree, Zensical/MkDocs configuration, Python source/package, package/dependency manifest, CLI implementation, test suite, or GitHub Actions workflow in this tree. GitHub repository metadata reported `has_pages: false` and no homepage on the inspection date. No repository-hosted documentation website was identified. These observations do not establish whether unrelated external documentation exists. [R1]; [R2]

No usable local checkout of this project was available in the accessible workspace. A local-versus-remote comparison was therefore unavailable; all repository conclusions are pinned to the remote commit above. No newer consolidated specification was supplied in this task. The baseline's authority is its explicit current normative designation, not an assumption that unseen later decisions cannot exist.

### 2.2 Citation conventions

Rule IDs and section numbers in this document refer to [N1] at the inspected commit. The source register at the end supplies immutable repository links and official tooling references. When a later consolidated baseline is adopted, refresh the baseline identification and affected traceability entries; do not silently reinterpret an old citation as a different revision.

## 3. Accepted foundations and organizational choices

### 3.1 Accepted project requirements

| Foundation | Accepted requirement and boundary | Source |
| --- | --- | --- |
| Website generator | Zensical provides the documentation website. | DOC-FRAMEWORK, §2.3 |
| Python API reference | mkdocstrings automatically generates Python API references from source code and docstrings. | DOC-FRAMEWORK, §2.3 |
| Repository integration | Documentation is maintained alongside source code in the project's GitHub repository. | DOC-FRAMEWORK, §2.3 |
| Publication | Documentation is automatically published through GitHub Pages. | DOC-FRAMEWORK, §2.3 |
| Product interfaces | Both a Python library and CLI are required. Exact package structure, supported Python versions, packaging, and most Python API names and types are unspecified. | §§2.2, 15 |
| Input and output scope | VP-plugin 0.5.3-style JSON with the bounded language enrichment is the supported baseline. RDF 1.1 Turtle is the sole officially supported ontology serialization; provenance sidecars use Turtle and diagnostic exports use JSON. | §§3.2–3.3; DK-GEN-10; DK-DIAG-04 |
| Semantic boundaries | DirectKG transforms structurally processable source information without becoming an OntoUML semantic validator. No general OWL profile guarantee is established. | §§3.3–3.4; DK-DIAG-02, 07 |

No separate theme, custom visual design, documentation dependency versions, configuration filename, public-source subdirectory, navigation scheme, or publication-workflow filename is selected by §2.3. None is inferred from archived notes or the existing ignore-file template. General application CI/CD and deployment remain unspecified under §2.2; the explicit documentation-publication obligation is an exception to that general boundary.

### 3.2 Choices made by this structure specification

Adopt a restrained hybrid: a short starting path, task-oriented CLI/Python guides, shared contracts and reference, and mapping pages grouped by coherent source concepts. This gives both interfaces a common semantic reference while allowing modelers to find transformation consequences directly.

Use `documentation/site/` for public site sources, alongside the existing internal `documentation/specification/`. Use root `zensical.toml` as the single authoritative site configuration and navigation definition. Reserve `.github/workflows/docs.yml` for the eventual documentation publication connection. These are proposed organizational choices, not previously accepted transformation decisions.

Use Zensical's ordinary presentation without requiring theme customization or additional navigation/generation plugins. This specification adds no alternative framework, API generator, hosting service, versioned-site system, or documentation extension stack.

### 3.3 Verified tooling feasibility

Official documentation checked on 21 October 2026 confirms that Zensical supports a configured source directory and separate output directory, and explicit nested navigation with paths relative to the source directory. It documents mkdocstrings integration and automatic publication through GitHub Actions to GitHub Pages. The Python handler supports API-object directives in Markdown and configurable source discovery. [T1]–[T4]

These are verified tooling capabilities, not evidence of installed dependencies or a successful DirectKG build. The selected versions and the real package layout still require validation during authorized implementation. A curated Markdown API entry page with mkdocstrings directives is sufficient; automatic module-tree discovery and an additional page-generation plugin are not required by this plan.

## 4. Audiences and reading paths

| Audience | Primary need | Entry path |
| --- | --- | --- |
| First-time OntoUML modeler | Understand the product, input scope, and first conversion when runnable usage exists. | Home → Getting started → Input contract → relevant mapping topic. |
| CLI operator | Run conversions, select controls, retain diagnostics, and interpret delivery failures. | CLI guide → Controls → Diagnostics; metadata/provenance guide when needed. |
| Python integrator | Integrate conversion, equivalent transformation controls, diagnostics, and separate exports. | Python guide → Controls → generated API reference. |
| Ontology engineer or output consumer | Understand the domain graph, inferential semantics, identity, preservation limits, and reasoning consequences. | Semantics and limitations → mapping reference → Output contract. |
| Contributor or maintainer | Find authoritative sources and verified development/documentation practices. | Contributing → current specification and this structure specification in the repository. |

Installation belongs in Getting started, conditional on a real supported installation mechanism. Do not create separate installation, tutorial, FAQ, troubleshooting, architecture, or release-documentation sections without a distinct content need. Initial troubleshooting belongs with the relevant guide or diagnostic reference.

## 5. Repository-relative location specification

### 5.1 Status notation

- **E — existing:** observed at the inspected commit.
- **P — planned:** destination selected here; no file or working feature is implied.
- **C — conditional:** a planned file or asset whose usable content depends on implementation or a further accepted decision.
- **G — generated:** eventual build output, not an authored source tree.

All public Markdown pages below are planned. The tree specifies destinations; it does not instruct authors to create empty files. Directories marked P include their displayed planned contents. Example-data filenames and future API subdivisions follow the conventions in §§8–9 and are not fabricated package/module names.

```text
README.md                                                   [P]
zensical.toml                                               [P]
.github/workflows/docs.yml                                  [P]
.gitignore                                                  [E]
LICENSE                                                     [E]
dkgm-vocabulary-v0.1.0.ttl                                   [E]
logos/                                                      [E: retain existing branding files]
documentation/                                             [E]
  specification/                                           [E]
    2026-10-21 - specification handoff.md                    [E: normative baseline]
    2026-10-21 - remaining decisions handoff.md              [E: non-normative state]
    2026-10-21 - test suite structure.md                     [E: separate structural proposal]
    archive/                                               [E: retain historical handoffs]
    prompts/                                               [E: retain workflow prompts]
    ontouml-directkg-documentation-structure.md              [P: approved home for this document]
  site/                                                    [P: public source root]
    index.md                                               [P]
    getting-started.md                                     [P/C]
    guides/                                                [P]
      cli.md                                               [P/C]
      python.md                                            [P/C]
      metadata-and-provenance.md                            [P/C]
    concepts/                                              [P]
      semantics.md                                         [P]
    mapping/                                               [P]
      classes.md                                           [P]
      higher-order.md                                      [P]
      attributes-and-datatypes.md                           [P]
      relations.md                                         [P]
      inverses.md                                          [P]
      property-features.md                                 [P]
      derivations-and-chains.md                             [P]
      mereology.md                                         [P: concrete vocabulary URI selected]
      instantiation.md                                     [P]
    reference/                                             [P]
      input.md                                             [P]
      output.md                                            [P]
      controls.md                                          [P]
      identifiers.md                                       [P]
      persistent-identifiers.md                            [P: approved PID reference]
      text.md                                              [P]
      diagnostics.md                                       [P]
      api/                                                 [P]
        index.md                                           [P/C: curated API-generation entry point]
    examples/                                              [P]
      index.md                                             [P/C]
      files/                                               [P/C: downloadable example data]
    assets/                                                [P]
      images/                                              [P/C: published images only as needed]
    development/                                           [P]
      contributing.md                                      [P/C]
site/                                                      [G: eventual rendered site output]
```

### 5.2 Responsibilities outside public pages

| Path | Responsibility |
| --- | --- |
| `README.md` | Brief repository entry: product purpose, truthful implementation/release status, links to Getting started and the published site when available, and a direct link to the current normative source following §8.1's source-note/link convention. Link to detailed controls and mappings rather than copying them. |
| `zensical.toml` | Own site identity, source/output roots, explicit navigation, approved rendering settings, and mkdocstrings connection to real Python source. No parallel independent `mkdocs.yml` or distributed navigation files are needed. |
| `.github/workflows/docs.yml` | Own the eventual automated documentation build/publication connection to GitHub Pages. Workflow internals, triggers, permissions, and versions are for a later implementation task. |
| `documentation/specification/documentation-structure.md` | Stable repository destination for the approved structural plan and its obligation/location traceability. Saving the deliverable elsewhere for review does not create this repository path. |
| Existing handoffs, archives, and workflow prompts | Retain handoffs and `archive/` in `documentation/specification/`. Active workflow prompts reside in the adviser, architect, documentation, test, and implementation directories under `documentation/prompts/`, each with its own archive, outside the public documentation build. The repository inventory and tree in §§2.1 and 5.1 describe the historical inspected revision. |
| Existing vocabulary and `branding/` | Retain canonical repository artifacts. Public pages can link to the vocabulary as repository evidence; website prose does not edit it or finalize its persistent identity. Reuse branding; any image copy needed under public assets is derived from the existing original. |
| Root `site/` | Rendered HTML, generated API output, and copied publication assets. Keep outside the source root and out of committed documentation sources. Existing `/site` ignore coverage supports this placement. |

The public build root is `documentation/site/`, not all of `documentation/`. Excluding internal material from navigation alone is insufficient: it must remain outside the public content source and any broad include mechanism.

## 6. Navigation and page inventory

### 6.1 Navigation contract

The intended top-level order is **Home**, **Getting started**, **Guides**, **Semantics and limitations**, **Mapping reference**, **Reference**, **Examples**, **Contributing**. Guides, Mapping reference, and Reference are navigation groups; the other entries are pages. Use a normal hierarchical sidebar; no extra landing pages or navigation plugin are required.

The tables below define page order within each group and the complete target inventory. Their paths are repository-relative. Configuration entries remove the `documentation/site/` prefix because Zensical navigation paths are relative to `docs_dir`. The entry page is `index.md` within that source root.

Section names shown in bold are planned page sections. Preserve their meaning and stable heading anchors, particularly where §7 cites them. Other headings can be added inside the assigned topic boundaries.

### 6.2 Orientation and guides

| ID / navigation title | Repository-relative path | Audience and distinct purpose | Principal content and source boundary |
| --- | --- | --- | --- |
| P01 · Home | `documentation/site/index.md` | All readers; orientation and route selection. | Domain-oriented conversion purpose, CLI/library targets, current availability, concise input/output scope, links to the starting path, semantic limits, and reference. Keep related-approach comparisons brief and faithful to §§2–3. |
| P02 · Getting started | `documentation/site/getting-started.md` | New users; shortest verified end-to-end path. | **Installation status**, **First conversion**, **Inspecting the result**. Add actual Python requirements, installation method, executable/import names, and one runnable conversion only when verified. Link to the complete input contract, controls, and example pair; do not duplicate their reference material. |
| P03 · CLI guide | `documentation/site/guides/cli.md` | CLI users and automation authors; operating procedure. | **Invocation**, **Files and console**, **Exit codes and delivery failures**. Document actual invocation mechanics when implemented; show supported control use by linking to P18. Own the complete accepted CLI exit-code table and precedence, including codes 0–6 and the defined scope of failures ([N1] §15, “CLI exit codes (RD-04)”). Link to P21 for outcomes and diagnostic policies. |
| P04 · Python guide | `documentation/site/guides/python.md` | Application integrators; practical library use. | **Conversion and configuration**, **Diagnostics and aborts**, **Separate exports**. Explain semantic control parity, structured diagnostic access after abort, explicit JSON export, and separate provenance graph access. Add verified calls and concrete result/error handling only from the actual public API; link to P22. §§15, DK-DIAG-04, DK-GEN-10. |
| P05 · Metadata and provenance | `documentation/site/guides/metadata-and-provenance.md` | Users enriching or tracing conversions. | **Descriptive metadata**, **Provenance modes**, **Artifacts and digests**, **Failure boundaries**. Own the seven-field external YAML mapping, source-project/external-title distinction, ignored fields and language boundary, provenance representation, sidecar naming, digest scope, and construction-versus-delivery behavior. DK-GEN-08–11; link to P03/P21 for codes/policies. |
| P06 · Semantics and limitations | `documentation/site/concepts/semantics.md` | Modelers and RDF/OWL consumers; conceptual interpretation. | **Key terms**, **Domain graph and inferential axioms**, **Validation boundary**, **Preservation boundaries**, **Reasoner and profile expectations**. Define recurring terms from [N1] §4 and the applicable governing rules. Explain inferential domain/range, necessary conditions, and the absence of general consistency/profile guarantees. Preservation boundaries is a linked limitation index. Summarize risks from material chains and link to P13's OWL compatibility section for detail. §§3–5, DK-DIAG-02, 07. |

### 6.3 Mapping reference

| ID / navigation title | Repository-relative path | Audience and distinct purpose | Principal content and source boundary |
| --- | --- | --- | --- |
| P07 · Classes and enumerations | `documentation/site/mapping/classes.md` | Modelers/ontology engineers; classifier output. | **Classes and disjointness**, **Generalization sets**, **Enumerations and closure**, **Class declarations preserved as comments**. Cover class mappings, stereotype disjointness, classifier order, complete/singleton sets, recovery, enumeration individuals and inequality, and closure only for fully transformed nonempty value lists. Explain abstractness, extensionality, and recognized omission of `restrictedTo`. DK-CLS-01–11; cross-reference higher order and identifiers. |
| P08 · Higher-order classification | `documentation/site/mapping/higher-order.md` | Advanced modelers and OWL consumers. | **Punning and separate facets**, **Categorizers and powertypes**, **No reconciliation**. Explain shared-IRI class/individual facets, explicit categorizer membership, modeled powertype extension, and absence of semantic reconciliation/validation. DK-HO-01–04. |
| P09 · Attributes and datatypes | `documentation/site/mapping/attributes-and-datatypes.md` | Modelers and Python/CLI users interpreting attributes. | **Property kinds and ranges**, **Primitive registry**, **Untyped and void**, **Cardinalities and structured datatypes**. Cover all nine registered primitives, `char` loss, custom datatype classes, enumeration-valued properties, necessary cardinality restrictions, and removal of redundant local `allValuesFrom` behavior. Distinguish null typing and unsupported `void`; link to P21 for malformed multiplicity handling. DK-ATT-01–04, DK-DAT-01–05. |
| P10 · Binary relations | `documentation/site/mapping/relations.md` | Modelers; ordinary relation and relation-set output. | **Primary direction and naming**, **Relation cardinalities**, **Generalization and disjointness**, **Relation-set completeness**, **Relation-valued endpoints**. Cover lexical/semantic naming precedence, unqualified cardinalities and reverse-side property selection, generalization, property disjointness, multi-member coverage omission, singleton completeness, and unsupported resolved connectors. DK-REL-01–06, 09–17, 20; delegate specialized derivations/mereology to P13/P14. |
| P11 · Inverse properties | `documentation/site/mapping/inverses.md` | Users selecting inverse modes; ontology engineers. | **Generation and eligibility**, **Direction and anonymous inverses**, **Inverse naming**, **Explicit inverse specialization**. Cover named-inverse modes, inverse domain/range and `owl:inverseOf`, mode-independent anonymous expressions, inverse-specific naming/collisions and source-backed precedence, multilingual role handling, and explicit specialization. DK-INV-01–12. Link to P19 for general identity rules. |
| P12 · Property features | `documentation/site/mapping/property-features.md` | Modelers using UML property relationships and qualifiers. | **Subsetting**, **Partial redefinition**, **Read-only and aggregation comments**, **Ordering without ordered values**. Explain property inclusion, association-end expression selection, contextual semantics not preserved by redefinition, and comment-only qualifiers without added logical enforcement. DK-PROP-03–05; §§3.3–3.4. |
| P13 · Derivations and material chains | `documentation/site/mapping/derivations-and-chains.md` | Advanced modelers; users enabling material chains. | **Recognized derivations**, **Derivation multiplicities**, **Material-chain modes**, **Ambiguity**, **OWL compatibility**. Cover material–relator/mode patterns, comparative–quality limitations, transformation-time connectors, all three chain modes and targeted constraint treatment, same-class/other ambiguity, exporter multiplicity loss and its conditional future objective, and reasoner/property-simplicity consequences. DK-REL-07–08, 18; DK-DIAG-07–08; cross-reference DK-REL-15. |
| P14 · Mereology and DKGM | `documentation/site/mapping/mereology.md` | Ontology engineers and modelers using part–whole relations. | **Import and vocabulary identity**, **Source-specific properties**, **Generic chains and direction**. Explain complete mandatory import, stable latest-version import policy, four generic properties, three generic chains, source-specific bridges/asymmetry, direction preservation, and independence from material-chain controls. DK-GEN-04, DK-REL-19. Use the accepted stable URI `https://w3id.org/directkg/vocab/dkgm` and its derived hash namespace under §11. |
| P15 · Instantiation associations | `documentation/site/mapping/instantiation.md` | Modelers interpreting explicit `instantiation` declarations. | **Declaration and concrete links**, **Discarded association information**, **No reconciliation**. Explain the current declaration boundary, canonical `rdf:type` representation, absent ordinary property output, and warning/diagnostic content boundary for discarded data. Future concrete-link support is conditional normative context, not an existing feature or API. DK-INS-01–03. |

### 6.4 Shared reference and supporting pages

| ID / navigation title | Repository-relative path | Audience and distinct purpose | Principal content and source boundary |
| --- | --- | --- | --- |
| P16 · Input contract | `documentation/site/reference/input.md` | Exporters, modelers, and integrators; accepted input boundary. | **Exporter contract**, **Language enrichment**, **Structural requirements**, **Intentional omissions**. Cover VP-plugin 0.5.3-style structures, bounded multilingual carriers, IDs/references and duplicate-declaration distinction, binary scope, and recognized package/diagram/custom-assignment omissions. §§3.2, 3.4; DK-GEN-06–07. Link to P21 for policies; do not advertise arbitrary schema-conformant JSON. |
| P17 · Output contract | `documentation/site/reference/output.md` | Consumers and integrators; graph/artifact contract. | **Artifacts and serialization**, **Ontology header**, **Graph and text stability**, **Delivery boundaries**. Own a concise artifact overview: ontology Turtle, conditional provenance Turtle sidecar, optional diagnostic JSON. Cover derived ontology identity, mandatory import, source project annotations, prefix flexibility, graph preservation and ordered RDF lists, absence of textual-repeatability guarantees, and provenance variability. Delivery boundaries is an artifact-level summary only: link to P03 for CLI codes and delivery failures, P05 for metadata/provenance failure details, and P21 for outcomes and output eligibility. §§3.3, 5, 16; link to P05/P14/P19/P21 for other details. |
| P18 · Controls | `documentation/site/reference/controls.md` | Both interfaces; canonical shared control catalog. | **Established controls**, **Interface parity**, **Control boundaries**. Own one table of all §15 established controls, values, defaults, effects, and topic links; distinguish transformation controls, console filtering, and diagnostic persistence. Record the specifically prescribed Python `relation_labels` name and leave other unspecified Python names unresolved. Do not invent an executable, positional arguments, format/prefix/sorting switches, or the removed `allValuesFrom` control. [N1] §15, including “Semantic parity of transformation controls (ODI-CONTROLS)”; DK-LBL-01 / RD-26. |
| P19 · Identifiers and naming | `documentation/site/reference/identifiers.md` | Users choosing namespaces/identity behavior; ontology engineers. | **Base and ontology IRIs**, **Strategy and renaming**, **Names, escaping, and collisions**, **Source identifiers**, **Multilingual naming**. Cover base validation and placeholder warning, `name`/`id` trade-offs, designated relation-end IDs, owner qualification, generic source-ID fallback, enumeration identity, identifier annotations/opt-out, and the deterministic original-text selector. DK-IRI-01–10, DK-PROP-01–02, DK-CONF-01–03. P11 owns inverse-specific algorithms. |
| P25 · Persistent identifiers and redirects | `documentation/site/reference/persistent-identifiers.md` | Website users and semantic-web developers navigating registered project and vocabulary PIDs. | **Overview**, **Which identifier should I use?**, **Registered identifiers**, **Vocabulary ontology and term IRIs**, **HTTP resolution and content negotiation**, **URL patterns and edge cases**, **Practical examples**, **Authority and maintenance**. Own the single user-facing inventory of registered W3ID rewrite families and align vocabulary identity and the accepted normative converter import target, while keeping document URLs distinct. The external `.htaccess` remains technical authority; place P25 after P19 in navigation without renumbering established page IDs. |
| P20 · Labels, comments, and language | `documentation/site/reference/text.md` | Modelers and consumers; human-readable text treatment. | **Labels and descriptions**, **Language resolution**, **Derived-status comments**. Cover relation-label modes, lexical preservation, source project text, language carriers and override precedence, untagged fallbacks, generated/built-in text exclusions, and absence of fallback-label origin markers. Own cross-cutting `isDerived` annotation treatment; P07/P12 own other feature-specific comments. DK-LBL-01–02, DK-GEN-05, 08; link to P19 for naming selection and P05 for external metadata text. |
| P21 · Diagnostics and recovery | `documentation/site/reference/diagnostics.md` | CLI/Python users; interpreting processing and loss reports. | **Policies and precedence**, **Outcomes and output eligibility**, **Diagnostic collection and export**, **Diagnostic conditions and intentional silence**, **Multiplicity parsing and recovery**. Cover input/stereotype policies and their interaction, fatal duplicate IDs, three outcomes, console thresholds, complete JSON/Python mirrors, abort access, and diagnostic conditions grouped by source topic. Cover syntax/recovery in DK-DIAG-09–13 and INFO/language rules in 14–19. Source rule IDs are not invented runtime diagnostic codes. §14; §15 for cross-links to interface-specific delivery details. |
| P22 · Python API | `documentation/site/reference/api/index.md` | Python developers; automatically rendered API details. | Curated handwritten entry and mkdocstrings directives targeting real public Python objects, when available. Generated signatures/docstrings belong here; usage narrative belongs in P04 and shared semantics in P18/mapping pages. No fictional module hierarchy, result type, exception class, or directives to unresolved objects. DOC-FRAMEWORK; §15. |
| P23 · Examples | `documentation/site/examples/index.md` | Users learning by inspecting paired data. | **Examples and evidence status**, **Downloadable pairs**. Index reusable JSON/Turtle examples by the question they illustrate and link to their owning guide/mapping page. Start with a small supported model when data can be verified; add focused examples only to serve documented topics. Clearly distinguish specification illustrations from output verified against an implementation revision. |
| P24 · Contributing | `documentation/site/development/contributing.md` | Code and documentation contributors. | **Contributing**, **Documentation maintenance**, **Verified development checks**. Explain source authority, link to the current normative source using §8.1's convention, and cover the public/internal split, this structural plan, and actual contribution, docstring, preview/build, and testing practices as they become available. Link to the separate test-structure document with its actual approval/applicability status. Do not infer configured tools, production architecture, or CI from that proposal. §§2.2–2.3; DK-CONF-04. |

No developer architecture or internal module reference is planned before an implementation supplies a useful subject. The API entry may later be divided by real public API areas under `reference/api/`; such a division requires an inventory/navigation update, not speculative module pages now.

## 7. Documentation-obligation traceability

The destinations below identify pages to be authored later. They are not claims of fulfilled documentation obligations. Section fragments are planned stable anchors derived from the corresponding §6 heading names. Mapping explanations own precise conditions; P06 supplies discovery links and conceptual context.

### 7.1 Explicit public-documentation obligations

Every identified explicit public explanation requirement in [N1] has a primary destination. The DOC-FRAMEWORK obligations are covered separately by §§3, 5, and 9.

| ID | Governing rule | Required explanation | Primary destination within `documentation/site/` |
| --- | --- | --- | --- |
| E01 | DK-HO-01 | A shared IRI has logically separate class and individual facets under OWL 2 punning; axioms about one facet do not automatically entail facts about the other. | `mapping/higher-order.md#punning-and-separate-facets` |
| E02 | DK-DAT-04 | VP `void` is recognized and unsupported. Explain the retained property/domain/cardinality, missing range/type mapping, warning, and distinction from unspecified `null`. | `mapping/attributes-and-datatypes.md#untyped-and-void` |
| E03 | DK-PROP-03 | Redefinition is a partial translation preserving property inclusion without UML's complete contextual replacement semantics. Its limitation alone requires no runtime warning. | `mapping/property-features.md#partial-redefinition` |
| E04 | DK-REL-08, derivation-multiplicity documentation requirements | Derivation multiplicities can be meaningful; the inspected VP-plugin 0.5.3 association-class path exports default `"1"` values rather than independently specified connector-end multiplicities; those values cannot reliably establish author intent; DirectKG currently does not preserve these constraints. Also state the accepted objective: if reliable export becomes available, support SHOULD be added in future DirectKG versions supporting that exporter. No future mapping or delivery commitment is selected. | `mapping/derivations-and-chains.md#derivation-multiplicities` |
| E05 | DK-REL-16 | Coverage of complete relation sets with at least two distinct specifics is not represented and is a mapping limitation. Preserve the distinction from class coverage and fully resolved singleton relation completeness. | `mapping/relations.md#relation-set-completeness` |
| E06 | DK-IRI-02 | Renaming a source element MAY change its IRI under the default name strategy. Explain the ID-strategy identity trade-off. | `reference/identifiers.md#strategy-and-renaming` |
| E07 | DK-DIAG-07 | Combining chains with other axioms can cause reasoners to reject the ontology or disregard unsupported axioms. A chain is not inherently an OWL 2 DL violation; neither generating mode guarantees general conformance. | `mapping/derivations-and-chains.md#owl-compatibility` |
| E08 | DK-DIAG-07; DK-REL-15 | OWL 2 DL property-disjointness axioms require simple properties; chains that make participating properties non-simple can move the result outside OWL 2 DL. Explain relevant constraint omission/preservation. | `mapping/derivations-and-chains.md#owl-compatibility`; link from `mapping/relations.md#generalization-and-disjointness` |

### 7.2 Other material contracts and limitations

These grouped topics are necessary content coverage for this plan, rather than claims that every cited rule contains an explicit “MUST document” requirement. They add no transformation functionality or independent runtime warning.

| Governing source | User-facing boundary or consequence | Primary destination(s) within `documentation/site/` |
| --- | --- | --- |
| §3.2; RD-01; RD-27 | Exporter commitment is bounded to the specified VP 0.5.3 structure plus language enrichment; other versions and arbitrary schema-conformant JSON are not guaranteed. Binary scope does not establish n-ary support. | `reference/input.md#exporter-contract`, `#language-enrichment` |
| §§3.3–3.4; DK-GEN-03; DK-ATT-02; DK-DIAG-02 | Domain/range are inferential; restrictions are necessary conditions. Structural processing does not imply OntoUML validation, consistency, or general OWL profile guarantees. Contradictory numeric bounds remain stated constraints. | `concepts/semantics.md#domain-graph-and-inferential-axioms`, `#validation-boundary`; detailed cardinalities in P09/P10 |
| §3.3; DK-CONF-01–03; DK-GEN-10 | Turtle-only ontology serialization, flexible prefixes/text order/blank-node labels, graph and RDF-list preservation, deterministic identity, and execution-specific provenance have different guarantees. | `reference/output.md#graph-and-text-stability`; `guides/metadata-and-provenance.md#artifacts-and-digests` |
| DK-GEN-04; DK-REL-19 | Complete mandatory DKGM import uses its stable latest-version URI; imported axioms can change when that URI resolves to a newer vocabulary. Generic chains, source bridges/asymmetry, and direction preservation differ from material chains. Concrete URI is `https://w3id.org/directkg/vocab/dkgm`. | `mapping/mereology.md#import-and-vocabulary-identity`, `#generic-chains-and-direction` |
| DK-GEN-06–07; DK-CLS-01 / RD-22 | Package/diagram/presentation data, custom assignments, and `restrictedTo` are deliberately omitted without diagnostics solely for the defined omission. Packages still allow discovery of supported elements. | `reference/input.md#intentional-omissions`; `mapping/classes.md#class-declarations-preserved-as-comments` for `restrictedTo` |
| DK-GEN-05; DK-CLS-01 / RD-19, RD-21; DK-PROP-04–05; DK-DIAG-15–18 | Derived status, abstractness, extensionality, read-only/aggregation declarations, and ordering have bounded comment preservation. Comments do not implement the corresponding extra logical semantics, derivation rules, or value order. Preserve each rule's diagnostic conditions. | `reference/text.md#derived-status-comments`; `mapping/classes.md#class-declarations-preserved-as-comments`; `mapping/property-features.md#read-only-and-aggregation-comments`, `#ordering-without-ordered-values` |
| DK-DAT-01–05; DK-ATT-01, 04 | Nine-entry exact primitive registry; `char` loses the one-character restriction; untyped attributes receive no guessed range; custom datatypes become structured classes. No redundant local `allValuesFrom` option or inferred aliases. | `mapping/attributes-and-datatypes.md#primitive-registry`, `#untyped-and-void`, `#cardinalities-and-structured-datatypes` |
| DK-ATT-03; DK-REL-09–13; DK-DIAG-09–11; §3.4 | Null, absent, unbounded, malformed, and contradictory cardinalities differ. Ordinary relation constraints use the specified direction/unqualified forms and can require anonymous inverses. Best-effort recovery preserves only permitted independent bounds. | `mapping/attributes-and-datatypes.md#cardinalities-and-structured-datatypes`; `mapping/relations.md#relation-cardinalities`; `reference/diagnostics.md#multiplicity-parsing-and-recovery` |
| DK-CLS-06–11; DK-REL-20; DK-DIAG-12–14 | Complete/singleton/empty/partially recovered sets differ. Enumeration closure cannot be asserted over a surviving subset; distinct value IRIs alone do not establish inequality. One survivor after failure does not authorize singleton completeness. | `mapping/classes.md#generalization-sets`, `#enumerations-and-closure`; `mapping/relations.md#relation-set-completeness` |
| DK-REL-07–08, 17–18; DK-DIAG-07–08 | Material derivations lack a separate output resource; comparative derivations lack a supplied comparison rule; unsupported resolved relation-valued connectors differ from unresolved endpoints. Chain ambiguities omit affected chains with specified nonfatal diagnostics. | `mapping/derivations-and-chains.md#recognized-derivations`, `#ambiguity`; `mapping/relations.md#relation-valued-endpoints` |
| DK-REL-07; DK-DIAG-07 | Chain modes affect only eligible emitted material chains and targeted simplicity-dependent constraints. Omission propagates through accepted property hierarchies; unrelated constraints survive. Preservation mode does not mean full OntoUML preservation. | `mapping/derivations-and-chains.md#material-chain-modes`, `#owl-compatibility` |
| DK-INV-01–12; DK-PROP-03; DK-REL-09; DK-CONF-02 | Named inverse generation differs from anonymous inverse expressions. Inverse-mode changes do not change source-backed IRIs; explicit inverse hierarchy materialization has bounded scope. | `mapping/inverses.md#generation-and-eligibility`, `#direction-and-anonymous-inverses`, `#explicit-inverse-specialization` |
| DK-INS-01–03 | An instantiation declaration does not create an ordinary property or establish concrete instance links. Discarded association values cannot reappear as output, provenance, or diagnostic payload; the source ID can locate the warning. | `mapping/instantiation.md#declaration-and-concrete-links`, `#discarded-association-information` |
| DK-LBL-01–02; DK-IRI-10; DK-DAT-02 | Language override/tagging differs from deterministic original-text selection for naming/primitive recognition. Generated text and external YAML have their own exclusions; custom assignments supply no language. No RDF marker distinguishes fallback relation labels solely by origin. | `reference/text.md#labels-and-descriptions`, `#language-resolution`; `reference/identifiers.md#multilingual-naming` |
| DK-IRI-01, 04–09; DK-PROP-01–02 | Placeholder namespace warning, invalid supplied-base rejection before conversion, source-ID fallback and collisions, designated end IDs, and source-identifier annotations/opt-out. Unspecified exceptional collisions remain unspecified. | `reference/identifiers.md#base-and-ontology-iris`, `#names-escaping-and-collisions`, `#source-identifiers` |
| DK-GEN-08–11 | Source project text, seven-field external `metadata.yaml`, and transformation provenance are distinct. No metadata autodiscovery, expanded field whitelist, or indirect ingestion of ignored fields. | `guides/metadata-and-provenance.md#descriptive-metadata`; `reference/text.md#labels-and-descriptions` |
| DK-GEN-09–10; DK-DIAG-04–05; §15 | Provenance modes, exact-byte digests and exclusions, sidecar path prerequisite, whole-file metadata failures, required-provenance construction abort, and sidecar/ontology delivery failure have different effects. | `guides/metadata-and-provenance.md#artifacts-and-digests`, `#failure-boundaries`; `guides/cli.md#exit-codes-and-delivery-failures` |
| DK-DIAG-04–06; §15, “CLI exit codes (RD-04)” | Input/stereotype policy precedence; fatal duplicate IDs under every policy; completed error recovery versus abort; console filtering versus complete diagnostic access/export; delivery failures versus transformation outcomes. | `reference/diagnostics.md#policies-and-precedence`, `#outcomes-and-output-eligibility`, `#diagnostic-collection-and-export`; `guides/cli.md#exit-codes-and-delivery-failures` |
| DK-DIAG-01, 04, 07–19 | JSON mirrors produced diagnostics, not every known loss. Runtime diagnostic codes and JSON member/schema details are not prescribed. Intentional silence must not be presented as warning absence proving full preservation. | `reference/diagnostics.md#diagnostic-conditions-and-intentional-silence`, `#diagnostic-collection-and-export` |
| §15; DOC-FRAMEWORK | Established transformation controls have semantic parity and identical defaults across CLI/Python. Most Python names, signatures, types, and exceptions remain unspecified; generated API describes real source. | `reference/controls.md#interface-parity`; `guides/python.md`; `reference/api/index.md` |
| DK-GEN-02; DK-HO-03; DK-INV-12; DK-PROP-03 | Explicit structures and specifically required materializations differ from emitting all inferred closure. Do not promise general inference materialization. | `concepts/semantics.md#domain-graph-and-inferential-axioms`; details in the relevant mapping pages |

## 8. Writing and content conventions

### 8.1 Page structure and terminology

Use one H1 matching the page title. Use short H2/H3 headings reflecting the page's task or reference topics. Use the lowercase, hyphen-separated section IDs listed in §7 and verify them in the rendered site. Preserve the planned obligation-section anchors; when a heading must change, update all inbound links and this document's traceability together.

Use the normative specification's terms consistently, particularly *source-backed resource*, *generated auxiliary resource*, *primary property*, *named inverse property*, *anonymous inverse expression*, *ontology IRI*, *effective entity base*, *descriptive metadata*, *transformation provenance*, and the three transformation outcomes. Distinguish an OntoUML class, an OWL class, and a datatype when that distinction changes the mapping. P06's Key terms section owns brief definitions of recurring terms used across pages. Define specialized mapping terms where first explained and link to the shared definitions instead of duplicating a glossary.

Guide pages explain a task, prerequisites, actions, and interpretation of results. Mapping pages explain supported input conditions, generated constructs, important exceptions/loss, and associated diagnostic behavior. Shared reference pages own exact catalogs. Avoid copying entire normative passages or making source rule numbers the reader's only explanation.

Give each substantive mapping/reference page a brief source note identifying governing rule IDs, the baseline's **Consolidated** date, the full repository commit SHA, and the specification path at that commit. Link directly to that commit-pinned file; a numbered specification revision is not required when none exists. A suggested note is: `Governing rules: <IDs>; baseline consolidated: <YYYY-MM-DD>; repository commit: <full SHA>; source: <path at that commit>`. Record the implementation revision or release used to verify runnable examples. This can be ordinary author-maintained text or a comment; it requires no new metadata plugin or traceability database.

Current-source links in README and P24 must name and link directly to the current normative file at its adopted commit, and be refreshed when a later consolidation is adopted. Commit-pinned historical citations remain attached to the source actually consulted; later movement of files on the default branch does not invalidate those pinned links.

### 8.2 Examples and reusable data

- Use fenced blocks with `json`, `turtle`, `yaml`, `python`, or `text` as appropriate. Mark incomplete fragments explicitly; a fragment is not a complete supported input file.
- Put reusable downloadable data in `documentation/site/examples/files/`. Use lowercase hyphenated stems: `<topic>.json` for the complete input and `<topic>.ttl` for its ontology example. Add `<topic>.provenance.ttl` or `<topic>-diagnostics.json` only when that example needs the corresponding artifact. These are filename conventions, not generated files already present.
- Identify the effective configuration and the intended lesson. Use bounded, internally consistent source IDs and resolvable references within complete examples. Preserve RDF-list order where meaningful.
- Distinguish **specification illustration** from **verified implementation output**. A specification illustration must follow accepted rules; it need not pretend to be a captured conversion. Do not label expected Turtle as byte-exact output or promise fixed prefixes/blank-node labels. Explain omitted execution-specific provenance in an illustrative excerpt when relevant.
- Do not invent API calls, CLI executable names, JSON report schemas, vocabulary identifiers, or complete output artifacts to make an example look runnable. Use the accepted concrete DKGM URI for import examples; distinguish illustrative excerpts from complete conversion results.
- Keep one canonical downloadable copy per example. Link or use verified framework-supported inclusion rather than maintaining competing copies. Existing future test fixtures may be reused only when their purpose, validity, and ownership align; this plan does not establish a test corpus or alter the separate test structure.

### 8.3 Notices and cross-references

Place a limitation beside the affected explanation. State the triggering input/setting, what is preserved or omitted, the practical consequence, and its actual diagnostic behavior. Distinguish unsupported input, recognized omission, comment-only preservation, unspecified behavior, and behavior specified but not yet implemented or verified. Do not convert a documentation notice into a new runtime warning.

Link to the owning page/section instead of repeating complete control tables, policy matrices, primitive registries, or mapping algorithms. In particular: P18 owns control values/defaults; P21 owns diagnostic policies/outcomes; P03 owns CLI codes; P19 owns general identity construction; P11 owns inverse-specific construction; P05 owns external metadata/provenance detail. P13 owns the detailed material-chain and OWL property-simplicity explanation. P06 provides conceptual summaries and links to their mapping owners; P17 summarizes artifact delivery and links to P03, P05, and P21 for the detailed contracts.

Use relative Markdown links between public source pages, including the `.md` path and a stable fragment where useful. Use explicit repository links for normative/internal sources outside `docs_dir`. Use verified API-object cross-references only when the target exists. Give images descriptive alternative text. Do not expose uncreated planned pages as working links in a published build.

## 9. Documentation build and API-reference boundaries

### 9.1 Framework connections

| Connection | Convention selected by this plan |
| --- | --- |
| Configuration | Root `zensical.toml` is the single site configuration. |
| Public source | `docs_dir` points to `documentation/site`, relative to that root configuration. |
| Build output | `site_dir` points to root `site`, separate from sources and internal specifications. |
| Navigation | Explicit navigation follows §6 and contains only available pages. Paths are relative to `documentation/site/`. |
| API renderer | Configure approved mkdocstrings integration and the Python handler against the actual package/source layout. Do not select a fictitious package path. |
| Publication | The eventual `.github/workflows/docs.yml` connects the documentation build to automatic GitHub Pages publication. This plan supplies a location and responsibility, not workflow code. |

The source/output/navigation conventions are supported by [T1] and [T2]. Zensical's documented mkdocstrings support and the Python handler's object directives support the curated API entry-point design. [T3]; [T4]

When documentation dependencies are introduced, record them in the real project dependency mechanism selected for the implementation. This plan prescribes neither a nonexistent `pyproject.toml` nor a second dependency manifest. Record and verify compatible versions as part of that work.

### 9.2 Handwritten material and generated API

`reference/api/index.md` is an authored wrapper: title, scope, useful links, and curated mkdocstrings directives. Source code/docstrings remain the authority for rendered signatures and implemented API descriptions. Rendered API content is generated during the documentation build into `site/`; do not commit copied generated signatures or a parallel manually maintained API catalog.

Document the actual public entry points and their intended use. Do not expose all internal modules automatically or invent module-specific pages to match a presumed architecture. If real API size warrants multiple wrapper pages, keep them under `reference/api/`, choose names from verified public API areas, and amend the inventory/navigation accordingly.

Keep narrative usage in the Python guide and transformation semantics in shared reference/mapping pages. Correct a generated API description through its source/docstring, subject to the separate authorization for code changes, rather than editing rendered output. Documentation authors must report a real implementation/specification disagreement instead of describing either side as conforming without evidence.

### 9.3 Conditional implementation details

The following remain conditional: installation/distribution names and channels; supported Python versions; executable and input/output invocation mechanics; Python imports, call signatures, representations and exception types; concrete JSON report fields/runtime diagnostic codes; package discovery settings; documentation dependency versions; the actual Pages URL and publication settings.

Accepted CLI option spellings/defaults and the specifically prescribed Python `relation_labels` parameter are already normative in §15. Their presence in the specification is distinct from implementation verification. Record that distinction when pages are written.

Do not put unresolved object directives or nonexistent page paths into an active build. An API reference without source cannot yet satisfy the generation obligation; mark that connection pending rather than fabricating output. A practical incompatibility with the mandated generator/API integration/hosting choices must be raised as a precise project issue. It does not authorize switching technologies.

## 10. Incremental maintenance

1. **Establish the current accepted baseline.** Retrieve the Architect-maintained consolidated source from GitHub, checking its header, authority, registered revision and applicable Architect Reviewer OK. Historical open-issue notes and memory do not fill missing normative wording.
2. **Locate the content owner.** Use §§6–7 to select the existing primary page. Update that explanation and link to it from guides, conceptual summaries, and related mappings. Add a page only for a distinct reader task or coherent reference subject that no longer fits its owner.
3. **Propagate the accepted change.** Update affected examples, control/default tables, diagnostic explanations, API docstrings where separately authorized, cross-references, and the obligation map. Preserve qualifications, defaults, exceptions, and requirement strength. Do not describe an accepted behavior as implemented until verified.
4. **Preserve navigation and paths.** Keep existing public paths stable. Amend the tree, inventory, and navigation together when organization changes. Avoid renaming a page merely because a rule gains a new ID or a baseline gets a new date. Preserve old anchors or provide a verified redirect when a published target must move.
5. **Keep evidence current.** Refresh source-revision notes and runnable-example verification information for the affected material. Update this document's baseline register and traceability when adoption of a new consolidated specification changes their meaning. Refresh the consolidated date, full SHA, source path, and current-source links on affected pages only after checking them against the adopted baseline, following §8.1.
6. **Verify the affected documentation.** Apply §12 to the changed pages and their dependencies. Report unavailable checks and remaining conditional content precisely.

This target layout supports staged implementation without prescribing waves. Authors can publish self-contained, specification-derived explanations before a runnable package exists if the availability status is explicit. Reserve implementation-dependent pages until they contain useful verified material; avoid empty placeholders in public navigation. A missing planned page is pending coverage, not a completed obligation. No public link may rely on a reserved destination that has not been created.

Use the existing public content owners as the maintenance index; a separate workflow dashboard, duplicated normative rulebook, machine-readable coverage registry, or generated navigation system is not required.

## 11. Exceptions and unresolved boundaries

### 11.1 Structural deviations

Routine wording changes, source-note refreshes, additional examples, and new subsections within a page's assigned responsibility need no separate structural approval. A justified page addition/split within an existing group can be proposed with its inventory/navigation/traceability amendment and a clear content owner.

Obtain an explicit project-owner structural decision before changing the public source root, replacing the configuration/navigation ownership convention, reorganizing top-level navigation groups, moving published paths without a preservation plan, or abandoning an obligation's destination. Explain the concrete need and the effect on links, duplication, and maintenance. Changes to accepted framework, hosting, API-generation technology, or transformation semantics require the relevant owner-approved decision, Architect registration and Architect Reviewer OK; approval of a layout exception alone cannot authorize them.

### 11.2 Specific unresolved or implementation-dependent matters

| Matter | Evidence and treatment |
| --- | --- |
| Concrete persistent DKGM URI | The project-owner decision of 2026-10-24 selects `U = https://w3id.org/directkg/vocab/dkgm` and the derived namespace `U#`. DK-GEN-04, import examples and tests use that identity. Versions 0.1.0 and 0.1.1 are corrected in place under the explicit pre-release exception; unrelated versioning decisions remain open. |
| Installation and public interface mechanics | No implementation or package metadata exists at the inspected commit. Use the reserved guide/API destinations; fill concrete details from verified implementation and applicable accepted decisions. |
| Diagnostic representation | Outcome names and diagnostic capabilities are specified, while exact JSON schema/member names, runtime codes, and Python representations remain unspecified. Explain the accepted contract without designing these missing representations. |
| Build and publication realization | Tool versions, source discovery, workflow details, Pages settings and final URL are unconfigured. Their future validation does not reopen DOC-FRAMEWORK. No site build or deployment was performed for this structural design. |
| Styling and optional features | A separate theme, custom templates, multilingual site, versioned documentation, analytics, and extra plugins have no requirement in this plan. Absence is not a product backlog or a reason to add infrastructure. |

The accessible normative baseline establishes the documentation foundations; no missing authoritative text blocks this structural proposal. Its authority and completeness are bounded to that identified baseline. If a newer current consolidation is provided, assess it before treating this plan as current for the new baseline.

## 12. Minimum verification for subsequent documentation work

Apply checks appropriate to what actually exists. Before a build exists, perform source/inventory checks and state that build/API/publication validation is pending. Once the relevant implementation exists, verify the actual connections rather than recording them as assumed.

| Check | Minimum evidence |
| --- | --- |
| Structure agreement | Every created public Markdown page has one inventory responsibility; tree, inventory, and active navigation agree. The target inventory may contain pending pages, but active navigation contains no nonexistent targets. Example-data and image directories are assets, not phantom pages. |
| Authority and traceability | Consulted baseline revision is identified; every E01–E08 obligation has its planned explanation when the corresponding material is delivered. Relevant §7.2 topics are covered or explicitly pending. Changes preserve the governing rule's conditions and strength. |
| Links and anchors | Check internal links, planned stable anchors, example downloads, image paths, and API cross-references. Inspect links under the actual Pages base path when available. Check normative-source notes and README/P24 links against §8.1's consolidated-date, commit-SHA, source-path, and direct-link convention. |
| Content boundaries | No duplicate canonical tables/algorithms; no inferred feature, blanket compatibility promise, unknown package/API name, fabricated diagnostic schema, or invented vocabulary identity. Specified and verified implementation behavior are distinguishable. |
| Examples | Complete JSON examples satisfy the supported structure and internal references; Turtle examples parse and express the intended accepted graph. Validate against the implementation only when claimed. Comparison respects blank-node renaming, list order, and provenance variability instead of assuming byte equality. |
| Framework/API feasibility | With real dependencies/source available, build the actual Zensical project, resolve all curated mkdocstrings targets, and inspect representative guide, mapping, API, code-block, and download rendering. Use the configured tool's link/navigation checks; do not assume that a successful build validates transformation semantics. |
| Publication boundary | When publication is authorized and implemented, confirm automated delivery through GitHub Pages, correct base-path links/assets, and exclusion of internal specifications/prompts and build caches. Verify that Pages is configured to publish through GitHub Actions and that the uploaded artifact directory matches the configured `site_dir` (`site/` in this layout). [T4] Configuration text alone is not deployment evidence. |

Completion of this structure specification does not require creating a website, implementation, test suite, API reference, or publication workflow. Those are later authorized tasks governed by the accepted project requirements and this approved organization.

## Source register

Repository sources below are pinned to `7870042a02e094dca772d6fdd6570ad7b2d02578` unless noted. Tooling pages were checked on 21 October 2026; later implementation should verify compatibility with its actual selected versions.

- **[R1]** [Complete inspected repository tree](https://github.com/pedropaulofb/ontouml-directkg/tree/7870042a02e094dca772d6fdd6570ad7b2d02578), retrieved through GitHub's recursive Git-tree API with `truncated: false`.
- **[R2]** [Repository metadata](https://api.github.com/repos/pedropaulofb/ontouml-directkg), inspected 21 October 2026; default branch, homepage, and Pages state are time-specific metadata rather than immutable commit content.
- **[N1]** [Current normative specification](https://github.com/pedropaulofb/ontouml-directkg/blob/7870042a02e094dca772d6fdd6570ad7b2d02578/documentation/specification/2026-10-21%20-%20specification%20handoff.md), especially §§1–3, rule sections 5–14, §15, and §16.
- **[W1]** [Current Architect registration workflow](../prompts/architect/architect.md).
- **[W2]** [Current independent Architect Reviewer](../prompts/architect/architect-reviewer.md).
- **[P1]** [Historical retired Documenter initialization/operation](https://github.com/pedropaulofb/ontouml-directkg/blob/7870042a02e094dca772d6fdd6570ad7b2d02578/documentation/specification/prompts/documenter-01-initialize-and-operate.md), source authority and integration responsibilities.
- **[P2]** [Historical retired Documenter consolidation handoff](https://github.com/pedropaulofb/ontouml-directkg/blob/7870042a02e094dca772d6fdd6570ad7b2d02578/documentation/specification/prompts/documenter-99-session-consolidated-specification.md), consolidated-baseline and incomplete-consolidation conventions.
- **[H1]** [Remaining-decisions handoff](https://github.com/pedropaulofb/ontouml-directkg/blob/7870042a02e094dca772d6fdd6570ad7b2d02578/documentation/specification/2026-10-21%20-%20remaining%20decisions%20handoff.md), opening authority/incomplete-reconciliation statement only; not accepted-requirement authority.
- **[H2]** [Test-suite structure proposal](https://github.com/pedropaulofb/ontouml-directkg/blob/7870042a02e094dca772d6fdd6570ad7b2d02578/documentation/specification/2026-10-21%20-%20test%20suite%20structure.md), separate structural scope, status, and earlier inspection baseline.
- **[V1]** [Existing DKGM vocabulary artifact](https://github.com/pedropaulofb/ontouml-directkg/blob/7870042a02e094dca772d6fdd6570ad7b2d02578/dkgm-vocabulary-v0.1.0.ttl), historical pre-migration artifact identity/namespace; does not supersede [N1] or the 2026-10-24 identity correction.
- **[T1]** [Zensical basics](https://zensical.org/docs/setup/basics/), configuration scope and source/output directory settings.
- **[T2]** [Zensical navigation](https://zensical.org/docs/setup/navigation/), explicit nested navigation and source-relative paths.
- **[T3]** [Zensical MkDocs-plugin compatibility](https://zensical.org/docs/compatibility/mkdocs/plugins/), documented mkdocstrings integration; [mkdocstrings Python usage](https://mkdocstrings.github.io/python/usage/), object directives and source discovery.
- **[T4]** [Zensical publication](https://zensical.org/docs/publish-your-site/), documented automatic GitHub Pages publication through GitHub Actions.

[R1]: https://github.com/pedropaulofb/ontouml-directkg/tree/7870042a02e094dca772d6fdd6570ad7b2d02578
[R2]: https://api.github.com/repos/pedropaulofb/ontouml-directkg
[N1]: https://github.com/pedropaulofb/ontouml-directkg/blob/7870042a02e094dca772d6fdd6570ad7b2d02578/documentation/specification/2026-10-21%20-%20specification%20handoff.md
[W1]: ../prompts/architect/architect.md
[W2]: ../prompts/architect/architect-reviewer.md
[P1]: https://github.com/pedropaulofb/ontouml-directkg/blob/7870042a02e094dca772d6fdd6570ad7b2d02578/documentation/specification/prompts/documenter-01-initialize-and-operate.md
[P2]: https://github.com/pedropaulofb/ontouml-directkg/blob/7870042a02e094dca772d6fdd6570ad7b2d02578/documentation/specification/prompts/documenter-99-session-consolidated-specification.md
[H1]: https://github.com/pedropaulofb/ontouml-directkg/blob/7870042a02e094dca772d6fdd6570ad7b2d02578/documentation/specification/2026-10-21%20-%20remaining%20decisions%20handoff.md
[H2]: https://github.com/pedropaulofb/ontouml-directkg/blob/7870042a02e094dca772d6fdd6570ad7b2d02578/documentation/specification/2026-10-21%20-%20test%20suite%20structure.md
[V1]: https://github.com/pedropaulofb/ontouml-directkg/blob/7870042a02e094dca772d6fdd6570ad7b2d02578/dkgm-vocabulary-v0.1.0.ttl
[T1]: https://zensical.org/docs/setup/basics/
[T2]: https://zensical.org/docs/setup/navigation/
[T3]: https://zensical.org/docs/compatibility/mkdocs/plugins/
[T4]: https://zensical.org/docs/publish-your-site/
