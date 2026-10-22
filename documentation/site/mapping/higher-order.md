# Higher-order classification

This page explains **specified higher-order mappings**. They use standard RDF/OWL constructs; no production conversion has been executed to produce the illustration below. The [semantic boundary](../concepts/semantics.md#validation-boundary) applies throughout.

## Punning and separate facets

OWL 2 punning lets one IRI denote both a class and a named individual. When classifier `S` is explicitly classified by higher-order classifier `C`, DirectKG keeps `S` as an `owl:Class`, also uses that same IRI as an `owl:NamedIndividual`, and emits `S rdf:type C`. Supported primitives and `void` retain their datatype exceptions; the rule does not create local classes for them.

**The shared IRI has logically separate class and individual facets.** Under OWL 2 punning, axioms about one facet do not automatically entail facts about the other. In particular, `S rdfs:subClassOf B` constrains instances of the class facet of `S`; it does not itself classify the individual facet of `S` or `B` into some higher-order class. Conversely, `S rdf:type C` does not mean that every instance of the class `S` is an instance of `C` (E01 / DK-HO-01).

The following **specification illustration** assumes that `Dog` specializes `Animal` and is an explicit specific in a set categorized by `Species`, with `Species.isPowertype` false. Assume name-based identity without collisions and entity base `https://example.org/classification#`. These selected class/classification assertions form a parseable excerpt, not a complete conversion result; labels, identifier annotations, ontology header/import, and provenance are omitted.

```turtle
@prefix : <https://example.org/classification#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

:Animal a owl:Class .
:Species a owl:Class .
:Dog a owl:Class, owl:NamedIndividual, :Species ;
    rdfs:subClassOf :Animal .
```

Here the class `Dog` specializes `Animal`, while the individual facet of `Dog` is a `Species`. Those statements alone do not entail `Animal rdf:type Species`. Nor do they classify every dog individual as a species. There is no companion IRI such as a separately generated representation of the `Dog` classifier.

The same accepted rule can apply recursively at further classification orders, continuing to reuse the classifier IRI. Classifier-order comments do not supply extra higher-order assertions.

## Categorizers and powertypes

A generalization set's `categorizer` supplies a higher-order classifier. DirectKG emits a classification for **every explicit specific** in that set. Multiple categorizer declarations are all transformed; one classification does not replace another.

| Categorizer setting | Classifiers receiving `rdf:type` of the categorizer from this mapping |
| --- | --- |
| `isPowertype: false` or `null` | Only the set's explicit specific classifiers; not the common general or specializations outside that set. |
| `isPowertype: true`, with member generalizations sharing common general `B` | `B` itself and every modeled direct or indirect specialization of `B`, including modeled specializations outside the explicit set. |

`isPowertype` belongs to the **categorizer classifier**, not to the generalization set. These assertions are explicitly materialized because subclass axioms over class facets do not propagate membership facts over their punned individual facets (DK-HO-03).

For example, if modeled `Dog` and `Cat` specialize `Animal`, an ordinary set listing only `Dog` classifies only `Dog` by its categorizer. If that categorizer is a powertype, the accepted extension also classifies modeled `Animal` and `Cat`, and any modeled indirect specializations. It makes no assertion about unknown, unmodeled, or future specializations.

This is bounded materialization of the modeled extension, not a promise of general inferred closure. Class-set disjointness, coverage, singleton completeness, and recovery retain their [separate mappings](classes.md#generalization-sets).

## No reconciliation

DirectKG does not reconcile explicit `instantiation` declarations with `GeneralizationSet.categorizer`, choose precedence between higher-order sources, suppress multiple classifications, validate classifier orders/stereotype appropriateness, detect their semantic conflicts, or omit an assertion merely because it could contribute to inconsistency. Different higher-order types are not treated as conflicting solely because they classify related elements (DK-HO-04).

`restrictedTo` is recognized and omitted. It does not replace a stereotype, guide powertype membership, or authorize semantic-appropriateness checks. See [Class declarations preserved as comments](classes.md#class-declarations-preserved-as-comments) for its omission boundary and the separate order-comment rule.

Structural processing still matters. Explicitly empty generalization arrays have their defined error handling. Categorizer recovery when a class-set member is unresolved or fails transformation, duplicate-member handling, and missing/malformed membership containers remain unspecified; class-set constraint recovery does not independently establish a categorizer recovery rule. The detailed Instantiation associations page remains assigned to DOC-W3.

---

Governing rules: DK-HO-01–04; DK-CLS-01, 05–09; DK-DIAG-12; baseline consolidated: **2026-10-21**; repository commit: `7364ed8843c565592d4bfa550d90c218988c83ba`; source: [`documentation/specification/2026-10-21 - specification handoff.md`](https://github.com/pedropaulofb/ontouml-directkg/blob/7364ed8843c565592d4bfa550d90c218988c83ba/documentation/specification/2026-10-21%20-%20specification%20handoff.md).
