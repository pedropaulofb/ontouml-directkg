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

A generalization set's `categorizer` supplies a higher-order classifier. An absent or explicit `null` `categorizer` denotes an uncategorized generalization set without error. In a fully resolved class set with a usable categorizer, DirectKG emits a classification for **every explicit specific** in that set. Multiple categorizer declarations are all transformed; one classification does not replace another.

The [generalization-set membership rule](../reference/input.md#generalization-set-membership) counts repeated references to the same declaration once within each set before applying these existing categorizer and powertype mappings. That reference also distinguishes the accepted rule from its implementation status.

| Categorizer setting in a fully resolved class set | Classifiers receiving `rdf:type` of the categorizer from this mapping |
| --- | --- |
| `isPowertype: false` or `null` | Only the set's explicit specific classifiers; not the common general or specializations outside that set. |
| `isPowertype: true`, with member generalizations sharing common general `B` | `B` itself and every modeled direct or indirect specialization of `B`, including modeled specializations outside the explicit set. |

`isPowertype` belongs to the **categorizer classifier**, not to the generalization set. These assertions are explicitly materialized because subclass axioms over class facets do not propagate membership facts over their punned individual facets (DK-HO-03).

For example, if modeled `Dog` and `Cat` specialize `Animal`, an ordinary set listing only `Dog` classifies only `Dog` by its categorizer. If that categorizer is a powertype, the accepted extension also classifies modeled `Animal` and `Cat`, and any modeled indirect specializations. It makes no assertion about unknown, unmodeled, or future specializations.

This is bounded materialization of the modeled extension, not a promise of general inferred closure. Class-set disjointness, coverage, singleton completeness, and recovery retain their [separate mappings](classes.md#generalization-sets).

`isPowertype` is a defined `Class` Boolean flag governed by `DK-DIAG-05` (`RD-02`, Alternative 1): any non-`null`, non-boolean value (`type(val) is not bool`) emits a structural **ERROR** (`strict` and `tolerant` abort). Under `best-effort`, DirectKG retains **ERROR** severity, omits only the malformed `isPowertype` field (treating it as absent so no `DK-HO-03` powertype-extension assertions are emitted from it), and preserves the owning `Class`, valid sibling flags, and ordinary `DK-HO-02` `S rdf:type C` classifications when `C` serves as a usable generalization-set categorizer. See [Malformed Boolean flags](../reference/diagnostics.md#malformed-boolean-flags) for policy outcomes and current `NotImplementedError` status.

### Recovery for incomplete categorized class sets

This rule applies when a class set has a nonempty `generalizations` array, at least one member reference fails to resolve or a required member transformation fails, and the categorizer `C` resolves to an eligible classifier with a generated local OWL class (DK-HO-04).

Under `best-effort`, each distinct specific `S` of the successfully transformed explicit members receives `S rdf:type C` using the existing [punning rules](#punning-and-separate-facets). If no members survive, the set contributes no categorizer assertions. When `C.isPowertype` is true, omit the expansion to the common general and other specializations for this incomplete set. Classifications established independently by other mappings still apply.

For example, suppose `VehicleType` categorizes a set with explicit `Car` and `Truck` members and the `Truck` member fails. The accepted `best-effort` result retains `Car rdf:type VehicleType`. Even if `VehicleType.isPowertype` is true, the incomplete set supplies no classification of `Vehicle` or other specializations solely through powertype expansion.

The existing member ERROR remains. `strict` and `tolerant` abort. Under `best-effort`, [class-set recovery](classes.md#singleton-and-recovery-boundaries) still omits coverage, preserves applicable disjointness among surviving specifics, and preserves independent output. [Membership identity](../reference/input.md#generalization-set-membership) and the fully resolved mappings above retain their existing rules.

**Implementation status.** At [development revision `3e45c2da9ac935a7b760bd6910ab89268200a138`](https://github.com/pedropaulofb/ontouml-directkg/blob/3e45c2da9ac935a7b760bd6910ab89268200a138/src/ontouml_directkg/generalizations.py#L153), incomplete categorized class sets that reach the categorizer branch still raise `NotImplementedError`. This subsection describes the accepted recovery.

### Recovery for an unusable categorizer

This rule applies to a class generalization set with a nonempty `generalizations` array and a present, non-null `categorizer` value that cannot supply a generated local `owl:Class` (DK-HO-04). An unusable categorizer includes:

- a malformed reference value;
- an unresolved reference, including a dangling identifier, a reference-type mismatch, or a target class omitted earlier under `best-effort`;
- a reference resolving to a non-`Class` declaration; or
- a reference resolving to a `Class` without a generated local `owl:Class` under DK-CLS-01, such as a supported primitive datatype or Visual Paradigm `void`.

An absent or explicit `null` `categorizer` continues to denote an uncategorized generalization set without error.

DirectKG reports a structural **ERROR** identifying the affected generalization set and the unusable-categorizer condition. This rule selects no new stable diagnostic identifier; its code remains [provisional](../reference/diagnostics.md#stable-first-release-diagnostic-core). Under `strict` or `tolerant` (the default), conversion aborts under DK-DIAG-05 and delivers no ontology. Under `best-effort`, DirectKG retains ERROR severity, omits all categorizer assertions (DK-HO-02) and powertype-extension assertions (DK-HO-03) derived from that generalization set, and continues processing. See [unusable-categorizer diagnostics](../reference/diagnostics.md#unusable-categorizer-in-class-generalization-sets) for the outcome, delivery, and CLI exit-code contract.

Under `best-effort`, an unusable categorizer alone does not suppress:

- the set's independently valid membership-based constraints: `isDisjoint: true` pairwise disjointness (DK-CLS-06 or DK-CLS-09) and, when membership is complete, `isComplete: true` multi-member coverage (DK-CLS-07) or singleton completeness with its required DK-DIAG-14 INFO diagnostic (DK-CLS-08);
- independent class generalizations (DK-CLS-02); or
- higher-order classifications established independently by other rules.

When a class generalization set has both an unresolved or failed member under DK-CLS-09 and an unusable categorizer, both rules apply together under `best-effort`: coverage and all categorizer/powertype assertions from that set are omitted, while applicable pairwise disjointness among surviving specifics and independent mappings are retained. See [Class-set recovery](classes.md#singleton-and-recovery-boundaries).

DirectKG must not invent a substitute categorizer class, assert `rdf:type` against a shared XSD datatype IRI or `void`, or perform DK-HO-03 powertype expansion without a usable categorizer.

For example (**specification illustration**, not observed converter output), if a complete, disjoint class generalization set specializes `Vehicle` into `Car` and `Truck`, but its `categorizer` references the primitive datatype `string` or a dangling ID, `strict` and `tolerant` report a structural ERROR and abort. Under `best-effort`, DirectKG retains ERROR severity, omits all categorizer and powertype-extension assertions derived from that set, and retains `Car owl:disjointWith Truck`, the covering axiom for `Vehicle`, and the subclass axioms `Car rdfs:subClassOf Vehicle` and `Truck rdfs:subClassOf Vehicle`.

[DK-DIAG-12](../reference/diagnostics.md#missing-or-malformed-generalization-set-membership) continues to govern explicitly empty, absent, `null`, or other non-array `generalizations` containers, and the fatal [duplicate-declaration-ID rule](../reference/diagnostics.md#input-policy) (§3.4 / DK-DIAG-05) retains precedence under every input policy, including `best-effort`. Non-null categorizers on relation generalization sets are outside this class-set rule and are governed by [Non-null categorizer on relation generalization sets](#non-null-categorizer-on-relation-generalization-sets) below.

**Implementation status.** At the [reviewed registration revision `0f290d3afb830418297af13c30c4c65be1e13ca8`](https://github.com/pedropaulofb/ontouml-directkg/blob/0f290d3afb830418297af13c30c4c65be1e13ca8/src/ontouml_directkg/generalizations.py#L153-L162), unresolved or malformed categorizers, non-`Class` targets, and `Class` targets without a generated local `owl:Class` still raise `NotImplementedError`, caught in [`conversion.py`](https://github.com/pedropaulofb/ontouml-directkg/blob/0f290d3afb830418297af13c30c4c65be1e13ca8/src/ontouml_directkg/conversion.py#L246-L250) as `INTERNAL_TRANSFORMATION_FAILURE` and aborting under every input policy, including `best-effort`. This subsection describes the accepted intended recovery.

### Non-null categorizer on relation generalization sets

This rule applies to a relation generalization set (a `GeneralizationSet` with a nonempty `generalizations` array containing relation generalization(s)) carrying a present, non-null `categorizer` value—regardless of whether that value is malformed, unresolved, resolves to a non-`Class` declaration, or resolves to a `Class` (with or without a generated local `owl:Class`) (DK-HO-04). An absent or explicit `null` `categorizer` on a relation generalization set continues to denote an uncategorized relation generalization set without error.

DirectKG reports a structural **ERROR** identifying the affected generalization set and the inapplicable non-null `categorizer` condition. This rule selects no new stable diagnostic identifier; `DK-DIAG-04`'s eight-code core remains unchanged and its code remains [provisional](../reference/diagnostics.md#stable-first-release-diagnostic-core). Under `strict` or `tolerant` (the default), conversion aborts under DK-DIAG-05 (`aborted` outcome, no ontology delivered). Under `best-effort`, DirectKG retains ERROR severity, emits no categorizer (DK-HO-02), powertype-extension (DK-HO-03), or property-typing assertions derived from that set, and continues processing. See [relation-set categorizer diagnostics](../reference/diagnostics.md#non-null-categorizer-in-relation-generalization-sets) for the outcome, delivery, and CLI exit-code contract.

Under `best-effort`, a non-null `categorizer` on a relation generalization set alone does not suppress:

- independently valid membership-based relation-set behavior: `isDisjoint: true` pairwise `owl:propertyDisjointWith` on primary and matching named-inverse properties (DK-REL-15, subject to DK-REL-07's mode-specific omission), [singleton `isComplete: true`](relations.md#fully-resolved-singleton) with its required DK-DIAG-14 INFO diagnostic (DK-REL-20), or the multi-member `isComplete: true` [limitation warning](relations.md#relation-set-completeness) (DK-REL-16);
- independent relation generalizations (DK-REL-14, DK-INV-12); or
- independent relations and classes (including the referenced `Class` if independently declared).

When a relation generalization set with a nonempty `generalizations` array and a present, non-null `categorizer` also has an unresolved member reference or failed member transformation under `best-effort`, both structural ERRORs are retained and apply together:

- omit all DK-HO-02 categorizer, DK-HO-03 powertype-extension, and property-typing assertions derived from that set;
- do not apply singleton completeness under DK-REL-20 or emit DK-DIAG-14 INFO (including when partial failure of a larger set leaves one surviving member);
- emit no completeness axiom for multi-member `isComplete` while retaining any applicable DK-REL-16 limitation warning when its conditions hold; and
- when `isDisjoint: true`, retain applicable pairwise `owl:propertyDisjointWith` statements among the successfully generated primary properties (and corresponding generated named inverses) of surviving explicit specific relations under DK-REL-15 (subject to DK-REL-07's mode-specific omission), together with independent relation generalizations, relations, and classes.

DirectKG must not invent a property-categorizer mapping or emit `rdf:type` assertions targeting relation properties from `categorizer`.

For example (**specification illustration**, not observed converter output), if a disjoint relation generalization set specializes `:relates` into `:approves` and `:rejects` and its `categorizer` references an independently declared `Class` `RelationType` (or a dangling ID), `strict` and `tolerant` report a structural ERROR and abort. Under `best-effort`, DirectKG retains ERROR severity, omits all DK-HO-02 categorizer, DK-HO-03 powertype-extension, and property-typing assertions derived from that set, and retains `:approves rdfs:subPropertyOf :relates`, `:rejects rdfs:subPropertyOf :relates`, `:approves owl:propertyDisjointWith :rejects` (and the corresponding named-inverse axioms when applicable), and the independently declared `RelationType` class.

[DK-DIAG-12](../reference/diagnostics.md#missing-or-malformed-generalization-set-membership) retains precedence for empty, absent, `null`, or other non-array `generalizations` containers (which already omit any categorizer or powertype output from the affected set), and the fatal [duplicate-declaration-ID rule](../reference/diagnostics.md#input-policy) (§3.4 / DK-DIAG-05) retains precedence under every input policy, including `best-effort`. Mixed class/relation generalizations and mixed class/relation generalization sets remain outside scope.

**Implementation status.** At the [reviewed registration revision `cc562c49a8274367e3a52d95c368abb484bfa713`](https://github.com/pedropaulofb/ontouml-directkg/blob/cc562c49a8274367e3a52d95c368abb484bfa713/src/ontouml_directkg/generalizations.py#L266-L267), `emit_relation_generalizations` still raises `NotImplementedError("Categorizer treatment for relation sets remains unspecified")` whenever `data.get("categorizer") is not None` on a relation generalization set, caught in [`conversion.py`](https://github.com/pedropaulofb/ontouml-directkg/blob/cc562c49a8274367e3a52d95c368abb484bfa713/src/ontouml_directkg/conversion.py#L247-L251) as `INTERNAL_TRANSFORMATION_FAILURE` and aborting under every input policy, including `best-effort`. This subsection describes the accepted intended behavior.

## No reconciliation

DirectKG does not reconcile explicit `instantiation` declarations with `GeneralizationSet.categorizer`, choose precedence between higher-order sources, suppress multiple classifications, validate classifier orders/stereotype appropriateness, detect their semantic conflicts, or omit an assertion merely because it could contribute to inconsistency. Different higher-order types are not treated as conflicting solely because they classify related elements (DK-HO-04).

`restrictedTo` is recognized and omitted. It does not replace a stereotype, guide powertype membership, or authorize semantic-appropriateness checks. See [Class declarations preserved as comments](classes.md#class-declarations-preserved-as-comments) for its omission boundary and the separate order-comment rule.

Explicitly empty generalization arrays have their defined error handling. Under `best-effort`, a [missing or malformed membership container](../reference/diagnostics.md#missing-or-malformed-generalization-set-membership) contributes no categorizer assertions or powertype expansion. Independently supported classifications still apply. Unusable categorizers on class sets with a nonempty `generalizations` array follow the [unusable-categorizer recovery rule](#recovery-for-an-unusable-categorizer) above, and non-null categorizers on relation generalization sets with a nonempty `generalizations` array follow the [relation-set categorizer error and recovery rule](#non-null-categorizer-on-relation-generalization-sets). Malformed `GeneralizationSet.isComplete` and `GeneralizationSet.isDisjoint` values on sets with nonempty `generalizations` arrays follow [uniform field-level omission](../reference/diagnostics.md#malformed-boolean-flags) under `best-effort`, preserving valid sibling flags and independently applicable `DK-HO-02`/`DK-HO-03` categorizer and set-constraint mappings (`DK-DIAG-12` retains precedence). [Instantiation associations](instantiation.md#no-reconciliation) explains the separate declaration and discarded-data boundary.

---

Governing rules: DK-HO-01–04; DK-GEN-12; DK-CLS-01–02, 05–09; DK-REL-14–16, 20; DK-INV-12; DK-DIAG-01, 04–05, 12, 14; §3.4; §15; baseline consolidated: **2026-11-24**; repository commit: `15eff98eb9dfeed69694ff81f099e0b9785e700f`; source: [`documentation/specification/transformation-specification.md`](https://github.com/pedropaulofb/ontouml-directkg/blob/15eff98eb9dfeed69694ff81f099e0b9785e700f/documentation/specification/transformation-specification.md).

Accepted update: **RD-02 — Malformed Boolean flags (Alternative 1 — Uniform field-level omission)** (project-owner formalization included in the cited consolidation).
