# Semantics and limitations

This page explains the **accepted transformation contract**. Product implementation and runtime conformance have not been verified; no production converter exists at the reviewed revision.

## Key terms

| Term | Meaning in this documentation |
| --- | --- |
| Source-backed resource | A generated resource corresponding directly to a source element, such as a class, enumeration literal, attribute, or primary relation property. |
| Generated auxiliary resource | A resource without its own separate source element; a generated named inverse is an example. |
| Domain class | A modeled type represented as an `owl:Class`. Supported primitives and VP `void` are exceptions; custom OntoUML datatypes become reified classes. |
| Primary property | The source-specific object property generated for an eligible ordinary relation, following its established source-to-target direction. |
| Named inverse property | A separately identified property for the reverse direction, connected to its primary property by `owl:inverseOf`. |
| Anonymous inverse expression | An OWL expression that traverses a property backwards without introducing a separately named property. |
| Effective entity base | The selected base after the accepted delimiter handling; generated entity local names are appended to it. |
| Ontology IRI | The identity of the generated ontology, derived from the effective entity base. It differs from a serialization file's location. |
| Descriptive metadata | Information describing the ontology, such as its source-project name or an explicitly supplied external title. |
| Transformation provenance | Information about the execution, software, inputs, and configuration that produced an ontology. |

The names `completed`, `completed-with-errors`, and `aborted` describe transformation outcomes. Output delivery has separate failure conditions; an outcome alone does not prove that requested files were written.

## Domain graph and inferential axioms

DirectKG represents supported domain concepts and properties. It does not create resources merely to mirror JSON containers, diagrams, or the OntoUML metamodel. The reusable DKGM mereology vocabulary is an explicitly required import, distinct from such a metamodel reproduction.

### Domains and ranges infer types

An RDF/OWL domain or range declaration supports inference. It is not a rule that rejects a triple because an explicit type assertion is missing.

The following **specification illustration** is a parseable graph excerpt, not a captured conversion or a complete ontology output. Its example entity base is `https://example.org/employment#`; ontology-header and execution-provenance statements are outside the excerpt.

```turtle
@prefix : <https://example.org/employment#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

:employs a owl:ObjectProperty ;
    rdfs:domain :Employer ;
    rdfs:range :Person .

:Acme :employs :Ana .
```

Under RDFS semantics, these statements entail that `:Acme` is an `:Employer` and `:Ana` is a `:Person`. The domain and range do not operate as a closed list of previously typed permitted subjects and objects.

### Restrictions express necessary conditions

Attribute and ordinary relation cardinalities constrain their classes through `rdfs:subClassOf` restrictions. They do not define those classes exhaustively through `owl:equivalentClass`. Under OWL semantics, a missing assertion in an inspected file does not by itself establish a violated minimum cardinality. Different individual IRIs do not, by themselves, establish inequality.

The accepted mappings use explicit source structures. They do not promise general materialization of inferred closure. Specifically required materializations, such as modeled powertype membership and selected named-inverse hierarchy edges, are bounded exceptions. Class and individual facets sharing an IRI through [OWL punning](../mapping/higher-order.md#punning-and-separate-facets) also remain logically separate.

## Validation boundary

DirectKG is a transformation, not an OntoUML semantic validator. It does not check classifier-order appropriateness, reconcile higher-order classification sources, repair relation orientation, or reject otherwise transformable structures merely because the resulting ontology may be inconsistent.

Structural processability remains necessary. Malformed JSON, unresolved required references, or untransformable endpoints are different from semantic disagreements. Their continuation or abortion follows the accepted policies. Duplicate declaration IDs within the transformation/reference-resolution scope require abortion under every input policy. See [Structural requirements](../reference/input.md#structural-requirements).

Contradictory nonnegative numeric bounds, such as `5..2`, remain stated constraints: both the minimum and maximum are generated, with no warning or error solely for the contradiction. Such restrictions can make a class unsatisfiable; that does not alone make the whole ontology inconsistent unless other axioms require an instance. Separately, the selected material-chain mode can require omission of restrictions affected by emitted chains. It does not repair the source bounds.

## Preservation boundaries

Preservation depends on the construct, rather than on conversion completing without errors.

| Boundary | What readers should expect | Available reference |
| --- | --- | --- |
| Organizational and presentation information | Packages support traversal, while package organization, diagrams, and layout are intentionally absent from output. Their defined omission alone produces no diagnostic. | [Input omissions](../reference/input.md#intentional-omissions) |
| Serialization and identity | Graph identity and ordered RDF lists have guarantees distinct from textual layout, prefix choices, and blank-node labels. | [Graph and text stability](../reference/output.md#graph-and-text-stability) |
| Readable and source-based identity | Renaming or a changed selected translation can change a name-based IRI; ID-based construction uses the designated source ID. | [Strategy and renaming](../reference/identifiers.md#strategy-and-renaming) |
| Classifiers and values | Enumeration closure requires a complete nonempty value list; `void` is recognized but unsupported, while null typing is unspecified. | [Enumerations and closure](../mapping/classes.md#enumerations-and-closure); [Untyped and void](../mapping/attributes-and-datatypes.md#untyped-and-void) |
| Configurable output | Accepted controls have defined effects and defaults; stronger-looking output does not imply complete semantic preservation. | [Controls](../reference/controls.md) |
| Partial mappings | UML redefinition preserves property inclusion, without its complete contextual replacement semantics. Multi-member relation-set completeness is not represented. | [Partial redefinition](../mapping/property-features.md#partial-redefinition); [Relation-set completeness](../mapping/relations.md#relation-set-completeness) |
| Comment-only preservation | Abstractness, derived status, extensionality, ordering, and specified read-only/aggregation information have bounded annotation mappings. Comments do not enforce the additional source semantics or reconstruct ordered values. Diagnostic conditions differ by feature. | [Class declarations](../mapping/classes.md#class-declarations-preserved-as-comments); [Derived-status comments](../reference/text.md#derived-status-comments); [Read-only and aggregation](../mapping/property-features.md#read-only-and-aggregation-comments); [Ordering](../mapping/property-features.md#ordering-without-ordered-values) |
| Derivation limitations | Recognized connectors can inform transformation without receiving a separate output resource. Exported derivation multiplicities do not reliably record author intent. | [Recognized derivations](../mapping/derivations-and-chains.md#recognized-derivations); [Derivation multiplicities](../mapping/derivations-and-chains.md#derivation-multiplicities) |
| Inverse directions | Named inverse generation differs from anonymous inverse expressions required for selected restrictions, property references, and chains. | [Direction and anonymous inverses](../mapping/inverses.md#direction-and-anonymous-inverses) |
| Mereology | The complete vocabulary is imported independently of material-chain settings; source-specific direction remains authoritative and the stable import URI is `https://w3id.org/directkg/vocab/dkgm`. | [Mereology and DKGM](../mapping/mereology.md) |
| Instantiation declarations | A declaration supplies no concrete instance links; discarded association values cannot reappear in output, provenance, or diagnostic payloads. | [Instantiation associations](../mapping/instantiation.md) |

This index is conceptual guidance. Pending topic pages and their explicit explanation obligations are not claimed as delivered by naming them here.

## Reasoner and profile expectations

No general OWL profile or consistency guarantee is established. Even a `completed` transformation can preserve a semantically problematic source or make deliberate partial mappings.

An emitted material-property chain can make properties non-simple, including through applicable property hierarchies and inverse relationships. OWL 2 DL requires simple properties in cardinality restrictions and property-disjointness axioms. Depending on the selected chain mode, affected constraints are omitted or preserved. Neither generating mode guarantees general OWL 2 DL conformance.

Combining chains with other axioms can cause a reasoner to reject an ontology or disregard unsupported axioms. A property chain is not inherently an OWL 2 DL violation. See [OWL compatibility](../mapping/derivations-and-chains.md#owl-compatibility) for propagated constraint treatment and the required notices, and [Ambiguity](../mapping/derivations-and-chains.md#ambiguity) for patterns that produce no chain. The available [control catalog](../reference/controls.md#established-controls) identifies the accepted modes.

---

Governing rules: §§3–5; DK-GEN-02–04; DK-ATT-02; DK-HO-01, 03; DK-PROP-03–05; DK-REL-07–08, 16; DK-DIAG-02, 05, 07; baseline consolidated: **2026-10-21**; repository commit: `0307dd346c91346fa38bda2f8d57c9930b00751f`; source: [`documentation/specification/2026-10-21 - specification handoff.md`](https://github.com/pedropaulofb/ontouml-directkg/blob/0307dd346c91346fa38bda2f8d57c9930b00751f/documentation/specification/2026-10-21%20-%20specification%20handoff.md).
