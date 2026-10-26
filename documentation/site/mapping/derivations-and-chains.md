# Derivations and material chains

This page describes **accepted intended behavior**. No production conversion or OWL-reasoner execution has verified the examples. A derivation connector, a generated domain property, and a property-chain axiom are different constructs.

## Recognized derivations

Recognize the following explicit `derivation` patterns by resolving both endpoints, independently of their serialized order:

| Pattern | Accepted use and limitation |
| --- | --- |
| Material relation–relator class | Transformation-time information for the accepted relator-based naming and optional material-chain mappings |
| Material relation–mode class | Transformation-time information for optional mode-grounded material chains; no special material-name convention is added |
| Comparative relation–quality class | Retain the comparative as an ordinary relation; the connector's comparison semantics are unsupported |

None of these derivation connectors receives its own resource, ordinary/inverse property, or separate grounding annotation. Their endpoint classes and material/comparative properties retain independently applicable transformations. Recognizing either endpoint order is not reversal or source repair, and adds no warning/error solely for that order.

For material–relator and material–mode connectors, intentional non-representation alone adds no warning or error under any input policy. Existing naming, ambiguity, and structural diagnostics remain applicable. If no chain is generated, there is no separate formal grounding link; a relator-derived name does not establish one.

For comparative–quality derivations, emit a **nonfatal unsupported-semantics diagnostic**, including under `strict`, identifying the connector, comparative relation, and available quality. It should explain that the source supplies no comparison rule to preserve. Do not derive a chain, equivalence, comparison function, cardinality, special property name, or transitivity/symmetry/asymmetry/reflexivity/irreflexivity/functionality/inverse-functionality characteristic solely from that grounding. Ordinary comparative naming and other independently applicable diagnostics remain.

These specific mappings replace the generic [unsupported resolved connector](relations.md#relation-valued-endpoints) warning for their patterns. Do not infer a missing stereotype or reinterpret endpoints to manufacture a match. Malformed or unresolved endpoints remain structural errors.

An `isDerived` flag alone supplies no connector, calculation, or chain. Its [derived-status comment](../reference/text.md#derived-status-comments) remains a separate mapping.

## Derivation multiplicities

For material–relator derivations, the following exporter limitation and conditional future objective apply.

**Derivation multiplicities can express meaningful OntoUML constraints, but the current mapping does not preserve them** (E04 / DK-REL-08).

!!! warning "Exported derivation multiplicities do not establish author intent"

    The inspected VP-plugin **0.5.3 association-class export path** creates derivation ends with default cardinality `"1"` instead of extracting independently specified connector-end multiplicities. Consequently, those exported values are not reliable evidence of the original author's intended derivation constraints. They must not be presented as faithfully captured multiplicities or transformed as ordinary relation-end restrictions for the connector.

The accepted future objective is conditional: **if the exporter gains reliable preservation of author-specified derivation multiplicities, support should be added in future DirectKG versions supporting that exporter version**. This objective neither selects future transformation semantics/output representation nor promises a release or delivery date. It does not change the current mapping automatically. The loss is not evidence that the constraints lack meaning or should remain unsupported permanently.

This exporter limitation is specific evidence recorded by the governing specification. It does not establish a general compatibility claim for other plugin versions, or a reason to discard independently supplied ordinary material/mediation relation multiplicities.

## Material-chain modes

The [canonical controls](../reference/controls.md#established-controls) define `--material-property-chains`, with default `none`. The mode controls only accepted material–relator and material–mode chains, not the [imported generic mereology chains](mereology.md#generic-chains-and-direction).

| Mode | Material chains | Treatment of otherwise applicable cardinality/disjointness mappings |
| --- | --- | --- |
| `none` | None | Retain independently applicable mappings; no compatibility notice solely for disabling chains |
| `omit-conflicting-constraints` | Every eligible, unambiguous chain | Omit only specified constraints on expressions made non-simple by chains actually emitted, including propagated effects |
| `preserve-conflicting-constraints` | Every eligible, unambiguous chain | Preserve otherwise applicable cardinalities and property-disjointness axioms, including affected ones |

Preservation mode does not promise full OntoUML semantics or complete source-model preservation. Omission mode does not guarantee OWL 2 DL conformance. Pattern eligibility, source-element transformation, direction, and ambiguity rules remain the same for both generating modes.

### Eligible direct patterns

For a **relator-grounded** material relation from class `A` to a distinct class `C`, require an explicit material–relator derivation to relator `R`, exactly one mediation between `R` and `A`, and exactly one **distinct** mediation between `R` and `C`. Both participant classes are non-relators. Match endpoint class IDs directly, without inheritance search, names, or serialization order. Evaluate uniqueness separately on each participant side; extra mediations to other classes do not disqualify it.

For a **mode-grounded** material relation with distinct endpoint class IDs, require the explicit material–mode derivation to mode `Q`, exactly one characterization connecting `Q` to one participant, and exactly one external-dependence relation connecting `Q` to the other, forming a complete direct pattern by source IDs. Do not match by inheritance, names, or diagram/serialization order. Additional relations outside the candidate pattern do not disqualify a unique complete pattern. No complete direct pattern means no chain.

In either case, compose the path from the material property's **source to target** and use that primary material property as conclusion. A path step following an ordinary property's primary direction uses it directly; a backward step always uses an **anonymous inverse of the primary property**, even if a named inverse exists. Chain construction never forces named inverse generation.

The following **specification illustration** assumes material `worksFor` from `Person` to `Organization`, grounded in relator `Employment`; exactly one mediation named `employee` from `Employment` to `Person` and another named `employer` from `Employment` to `Organization`; a chain-generating mode; and name-based identity without collisions using entity base `https://example.org/employment#`. Named inverse mode is immaterial to this chain representation. The parseable excerpt shows the ordered chain and ordinary property declarations, not executed output. Class declarations, restrictions, text, identifiers, ontology header/import, and provenance are omitted.

```turtle
@prefix : <https://example.org/employment#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

:worksFor a owl:ObjectProperty ;
    rdfs:domain :Person ;
    rdfs:range :Organization ;
    owl:propertyChainAxiom ( [ owl:inverseOf :employee ] :employer ) .
:employee a owl:ObjectProperty ;
    rdfs:domain :Employment ;
    rdfs:range :Person .
:employer a owl:ObjectProperty ;
    rdfs:domain :Employment ;
    rdfs:range :Organization .
```

The first list member traverses `employee` backwards from person to employment; the second follows `employer` to organization. Swapping the RDF-list members would change the axiom. This excerpt does not assert that every chain body property becomes non-simple.

## Ambiguity

If multiple matching mediations occur on **either** participant side of a relator pattern, omit the affected chain and issue a warning identifying the material relation and ambiguity. Both sides need not be ambiguous. For mode patterns, multiple matching relations or complete matching patterns likewise require omission and a nonfatal chain-ambiguity diagnostic.

### Same-class endpoints

When both material association ends resolve to the **same classifier ID**, their distinct end IDs, role names, or multiplicities do not identify which occurrence corresponds to which grounding role. Sharing a classifier does not mean the two relata are the same individual.

Under either generating mode, omit the chain for both relator- and mode-grounded same-class patterns and emit a nonfatal ambiguity diagnostic identifying the material relation and unassignable roles, including under `strict`. For mode grounding, omit **both** characterization-first and external-dependence-first candidates. Do not arbitrarily select a path, emit both alternatives, or use names, end IDs, diagram order, or JSON order to break the ambiguity.

With `none`, same-class endpoints alone produce no warning. The connector remains recognized transformation-time information and receives no generic unsupported-pattern warning merely for this ambiguity.

Omitting a chain does not itself suppress or modify its classes, material property, grounding relations, end properties, or independently applicable domains, ranges, inverse/naming/cardinality mappings. Structural failures still follow their own rules. Constraint omission depends on chains **actually emitted**, including any other emitted chains whose propagated effects reach these properties.

## OWL compatibility

!!! warning "Combining chains and constraints can affect reasoner compatibility"

    **A property chain does not inherently violate OWL 2 DL.** OWL 2 DL does require simple object properties in cardinality restrictions and property-disjointness axioms. A chain makes its conclusion property non-simple; applicable inverse and hierarchy relationships can propagate that status. Combining axioms can therefore put output outside OWL 2 DL, cause a reasoner to reject the ontology, or cause it to disregard unsupported axioms (E07–E08 / DK-DIAG-07; DK-REL-15).

### Targeted constraint treatment

After determining emitted material chains, omission mode evaluates the affected object-property expressions:

- The conclusion property and its anonymous inverse.
- Corresponding generated named inverses.
- Generated superproperties made non-simple through the accepted subproperty/inverse hierarchy, including relation specialization, both singleton-completeness directions, and UML subsetting/redefinition.

A property used only in a chain **body** does not become non-simple solely for that participation. Likewise, being a subproperty of a non-simple generic mereological property alone does not propagate non-simplicity downwards.

For affected expressions, omit every multiplicity-derived restriction whose `owl:onProperty` uses that expression, whether primary, named inverse, or anonymous inverse. Also omit every property-disjointness axiom containing an affected participant; for pairwise output, omit only the affected pairs. Retain unrelated restrictions, unrelated disjointness pairs, and other applicable mappings. Do not omit merely because a relation is material or belongs to a candidate grounding pattern. The hierarchy axioms used for propagation remain; they are not the targeted constraints.

This treatment qualifies the otherwise applicable [attribute cardinalities](attributes-and-datatypes.md#cardinalities-and-structured-datatypes), [relation cardinalities](relations.md#relation-cardinalities), and [relation-set disjointness](relations.md#generalization-and-disjointness). Preservation mode keeps those independently applicable constraints without recalculating, weakening, or dropping them to accommodate chains. Neither generating mode guarantees general OWL 2 DL conformance; accepted source relationships and other axioms retain their own boundaries.

### Compatibility notice

Whenever **at least one material chain is emitted**, either generating mode requires the nonfatal compatibility notice, even if no cardinality or disjointness constraint ultimately conflicts. Omission mode's notice identifies the applied policy, actual omitted constraint categories where applicable, and affected source elements; it explains that removing known conflicts supplies no general profile guarantee. Preservation mode's notice explains that simplicity-dependent constraints were retained and their combination with chains may leave OWL 2 DL.

No emitted material chain means no notice triggered solely by this rule. The notice does not replace ambiguity, unsupported-semantics, or structural diagnostics, and does not claim every chain violates OWL 2 DL. [Semantics and limitations](../concepts/semantics.md#reasoner-and-profile-expectations) provides the conceptual entry point.

---

Governing rules: DK-REL-07–08, 15, 18; DK-DIAG-07–08; DK-GEN-04–05; DK-INV-04; baseline consolidated: **2026-10-21**; repository commit: `0307dd346c91346fa38bda2f8d57c9930b00751f`; source: [`documentation/specification/2026-10-21 - specification handoff.md`](https://github.com/pedropaulofb/ontouml-directkg/blob/0307dd346c91346fa38bda2f8d57c9930b00751f/documentation/specification/2026-10-21%20-%20specification%20handoff.md).
