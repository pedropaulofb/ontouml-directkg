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

A generalization set's `categorizer` supplies a higher-order classifier. In a fully resolved class set, DirectKG emits a classification for **every explicit specific** in that set. Multiple categorizer declarations are all transformed; one classification does not replace another.

The [generalization-set membership rule](../reference/input.md#generalization-set-membership) counts repeated references to the same declaration once within each set before applying these existing categorizer and powertype mappings. That reference also distinguishes the accepted rule from its implementation status.

| Categorizer setting in a fully resolved class set | Classifiers receiving `rdf:type` of the categorizer from this mapping |
| --- | --- |
| `isPowertype: false` or `null` | Only the set's explicit specific classifiers; not the common general or specializations outside that set. |
| `isPowertype: true`, with member generalizations sharing common general `B` | `B` itself and every modeled direct or indirect specialization of `B`, including modeled specializations outside the explicit set. |

`isPowertype` belongs to the **categorizer classifier**, not to the generalization set. These assertions are explicitly materialized because subclass axioms over class facets do not propagate membership facts over their punned individual facets (DK-HO-03).

For example, if modeled `Dog` and `Cat` specialize `Animal`, an ordinary set listing only `Dog` classifies only `Dog` by its categorizer. If that categorizer is a powertype, the accepted extension also classifies modeled `Animal` and `Cat`, and any modeled indirect specializations. It makes no assertion about unknown, unmodeled, or future specializations.

This is bounded materialization of the modeled extension, not a promise of general inferred closure. Class-set disjointness, coverage, singleton completeness, and recovery retain their [separate mappings](classes.md#generalization-sets).

### Recovery for incomplete categorized class sets

This rule applies when a class set has a nonempty `generalizations` array, at least one member reference fails to resolve or a required member transformation fails, and the categorizer `C` resolves to an eligible classifier with a generated local OWL class (DK-HO-04).

Under `best-effort`, each distinct specific `S` of the successfully transformed explicit members receives `S rdf:type C` using the existing [punning rules](#punning-and-separate-facets). If no members survive, the set contributes no categorizer assertions. When `C.isPowertype` is true, omit the expansion to the common general and other specializations for this incomplete set. Classifications established independently by other mappings still apply.

For example, suppose `VehicleType` categorizes a set with explicit `Car` and `Truck` members and the `Truck` member fails. The accepted `best-effort` result retains `Car rdf:type VehicleType`. Even if `VehicleType.isPowertype` is true, the incomplete set supplies no classification of `Vehicle` or other specializations solely through powertype expansion.

The existing member ERROR remains. `strict` and `tolerant` abort. Under `best-effort`, [class-set recovery](classes.md#singleton-and-recovery-boundaries) still omits coverage, preserves applicable disjointness among surviving specifics, and preserves independent output. [Membership identity](../reference/input.md#generalization-set-membership) and the fully resolved mappings above retain their existing rules.

**Implementation status.** At [development revision `3e45c2da9ac935a7b760bd6910ab89268200a138`](https://github.com/pedropaulofb/ontouml-directkg/blob/3e45c2da9ac935a7b760bd6910ab89268200a138/src/ontouml_directkg/generalizations.py#L153), incomplete categorized class sets that reach the categorizer branch still raise `NotImplementedError`. This subsection describes the accepted recovery.

## No reconciliation

DirectKG does not reconcile explicit `instantiation` declarations with `GeneralizationSet.categorizer`, choose precedence between higher-order sources, suppress multiple classifications, validate classifier orders/stereotype appropriateness, detect their semantic conflicts, or omit an assertion merely because it could contribute to inconsistency. Different higher-order types are not treated as conflicting solely because they classify related elements (DK-HO-04).

`restrictedTo` is recognized and omitted. It does not replace a stereotype, guide powertype membership, or authorize semantic-appropriateness checks. See [Class declarations preserved as comments](classes.md#class-declarations-preserved-as-comments) for its omission boundary and the separate order-comment rule.

Structural processing still matters. Explicitly empty generalization arrays have their defined error handling. Recovery for missing or malformed membership containers or an unusable categorizer remains unspecified. [Instantiation associations](instantiation.md#no-reconciliation) explains the separate declaration and discarded-data boundary.

---

Governing rules: DK-HO-01–04; DK-GEN-12; DK-CLS-01, 05–09; DK-DIAG-01, 05, 12; baseline consolidated: **2026-11-17**; repository commit: `c1d6ab323f0980e835fa018e0f2d05e05a400a07`; source: [`documentation/specification/transformation-specification.md`](https://github.com/pedropaulofb/ontouml-directkg/blob/c1d6ab323f0980e835fa018e0f2d05e05a400a07/documentation/specification/transformation-specification.md).
