# Mereology and DKGM

This page explains **specified vocabulary/import and source-relation mappings**. The repository vocabulary is a real artifact; it does not establish a working converter or settle the pending normative choice of its persistent import URI.

## Import and vocabulary identity

Every generated ontology must import the **complete reusable DirectKG mereology vocabulary**, even when its source model has no covered mereological relation. The four generic properties and three accepted generic chains belong to that imported vocabulary. Do not copy them into each generated ontology or publish a model-specific subset instead.

The current specification uses symbolic `U` for the stable ontology URI representing the vocabulary's latest version. **Its concrete value remains unselected.** `U` has no fragment component; append `#` for the property namespace. These are symbolic identifier patterns, not runnable Turtle imports:

| Resource | Identity pattern |
| --- | --- |
| Vocabulary ontology and mandatory import target | `U` |
| Generic properties | `U#memberOf`, `U#subCollectionOf`, `U#subQuantityOf`, `U#componentOf` |

Import the stable `U`, without the namespace's appended `#` or a property name. Do not pin a generated import to a vocabulary release or substitute the document address reached by a redirect. Redirecting to a newer document changes neither ontology identity nor property IRIs. Other version-IRI matters remain unspecified by this baseline.

Resolving an unchanged generated ontology's import against a later vocabulary version can bring in changed imported axioms. Its import alone therefore does not record which version was current at conversion time.

### Existing artifact and unresolved decision

The inspected [repository Turtle artifact](https://github.com/pedropaulofb/ontouml-directkg/blob/0307dd346c91346fa38bda2f8d57c9930b00751f/vocabulary/latest/dkgm-vocabulary.ttl) uses ontology URI `https://w3id.org/directkg/vocab` and namespace `https://w3id.org/directkg/vocab#`. Its relocation/publication does not select that address as the converter's accepted final import target. An accepted identity decision and normative integration are still needed before documenting a deployable converter import with that concrete URI. No placeholder import is offered as executable output here.

The core vocabulary remains independent of gUFO. It neither imports gUFO nor adds equivalence, subproperty, or other alignment axioms between these generic terms and gUFO as part of this mapping. The generic terms are vocabulary resources, not JSON/metamodel mirrors or source-specific properties with a particular model's class domains/ranges.

## Source-specific properties

An eligible ordinary class-to-class relation carrying one of the recognized stereotypes retains its distinct primary object property and gains the corresponding direct bridge:

| Source stereotype | Generic superproperty of the primary property |
| --- | --- |
| `memberOf` | `dkgm:memberOf` |
| `subCollectionOf` | `dkgm:subCollectionOf` |
| `subQuantityOf` | `dkgm:subQuantityOf` |
| `componentOf` | `dkgm:componentOf` |

Here `dkgm:` is the **symbolic `U#` namespace**. The bridge is `Primary rdfs:subPropertyOf Generic`, not replacement or merging of source relations. Each covered primary property is also explicitly an `owl:AsymmetricProperty`. Asymmetry entails irreflexivity, so no separate irreflexivity declaration is required. Do not additionally declare its generated named inverse asymmetric solely from this stereotype; the inverse relationship already entails the corresponding consequence.

The recognized stereotype alone selects the bridge. Use the already established **primary direction**, even when it fails to express the author's intended part–whole orientation. Do not use `aggregationKind` to determine eligibility/direction, repair or reverse the relation, substitute a named/anonymous inverse, or create an inverse solely for the bridge. Source-specific naming, identity, domains/ranges, inverses, multiplicities, and generalizations retain their independently applicable mappings.

`isExtensional` adds no mereological logical axioms beyond its [comment mapping](classes.md#class-declarations-preserved-as-comments). Read-only and aggregation declarations similarly have [comment-only preservation](property-features.md#read-only-and-aggregation-comments); they do not redefine this mapping's orientation.

## Generic chains and direction

The complete imported vocabulary contains the following **ordered compositions**:

| Chain body, first step then second | Generic conclusion |
| --- | --- |
| `subCollectionOf`, `subCollectionOf` | `subCollectionOf` |
| `subQuantityOf`, `subQuantityOf` | `subQuantityOf` |
| `memberOf`, `subCollectionOf` | `memberOf` |

There is no generic `componentOf` transitivity or `componentOf` chain solely from the stereotype. None of the four generic properties is asymmetric by default, and no additional generic asymmetric superproperty is introduced.

For example, if distinct source properties `r1` and `r2` are both beneath generic `subQuantityOf`, facts `a r1 b` and `b r2 c` support the generic conclusion `a subQuantityOf c` through the imported axiom. Those facts alone do **not** establish `a r1 c` or `a r2 c`. This is a symbolic semantic illustration, not an executed conversion/reasoner result or a concrete import example.

Do not construct arbitrary source-specific chains merely because their stereotypes appear compatible, or materialize source-specific assertions solely for these generic consequences. A wrongly oriented source relation can therefore produce unintended generic consequences; DirectKG does not validate or fix that orientation.

### Simplicity and controls

The three chain-conclusion generic properties are non-simple. A source-specific subproperty does **not** become non-simple merely by being beneath a non-simple generic superproperty; accepted source-specific asymmetry and cardinality restrictions remain applicable on that basis. Other axioms can independently affect simplicity, so this is not a general OWL 2 DL guarantee.

These imports, generic chains, bridges, and source-specific asymmetry are part of the default mapping, independent of `--material-property-chains`. Selecting `none` disables only the accepted material chains. Their [targeted constraint treatment](derivations-and-chains.md#owl-compatibility) does not create a generic mereology control or discard constraints merely because the imported vocabulary contains chains.

---

Governing rules: DK-GEN-04; DK-REL-19; DK-CLS-01; DK-PROP-04; baseline consolidated: **2026-10-21**; repository commit: `0307dd346c91346fa38bda2f8d57c9930b00751f`; source: [`documentation/specification/2026-10-21 - specification handoff.md`](https://github.com/pedropaulofb/ontouml-directkg/blob/0307dd346c91346fa38bda2f8d57c9930b00751f/documentation/specification/2026-10-21%20-%20specification%20handoff.md).
