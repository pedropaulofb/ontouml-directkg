# Mereology and DKGM

This page explains the **specified DKGM vocabulary modes and source-relation mappings**. The selected mode governs how the generic vocabulary is supplied. [Persistent identifiers and redirects](../reference/persistent-identifiers.md) explains the registered vocabulary URLs and their HTTP resolution.

## Import and vocabulary identity

The published DirectKG mereology vocabulary is authoritative for the four generic properties and three accepted chains. The same vocabulary and term IRIs apply in all three delivery modes.

The specification fixes `U = https://w3id.org/directkg/vocab/dkgm` as the stable ontology URI representing the vocabulary's latest version. `U` has no fragment component; append `#` for the property namespace `https://w3id.org/directkg/vocab/dkgm#`:

| Resource | Identity pattern |
| --- | --- |
| Vocabulary ontology and target in `import` mode | `U` |
| Generic properties | `U#memberOf`, `U#subCollectionOf`, `U#subQuantityOf`, `U#componentOf` |

In `import` mode, use the stable `U` without the namespace's appended `#` or a property name. A generated import uses this IRI regardless of the version or document address reached by a redirect. DKGM version IRIs use `U/X.Y.Z`. A [caller-supplied version IRI for the generated ontology](../reference/output.md#optional-ontology-version-iri) is independent of vocabulary delivery.

Resolving an unchanged generated ontology's import against a later vocabulary version can bring in changed imported axioms. Its import alone therefore does not record which version was current at conversion time.

### Canonical vocabulary and import

The [repository Turtle artifact](https://github.com/pedropaulofb/ontouml-directkg/blob/main/vocabulary/latest/dkgm-vocabulary.ttl) declares ontology URI `https://w3id.org/directkg/vocab/dkgm` and namespace `https://w3id.org/directkg/vocab/dkgm#`. This partial **specification illustration** shows the ontology declaration and import in default `import` mode for entity base `https://example.org/model#`.

```turtle
@prefix owl: <http://www.w3.org/2002/07/owl#> .
<https://example.org/model> a owl:Ontology ;
    owl:imports <https://w3id.org/directkg/vocab/dkgm> .
```

Both existing vocabulary releases, 0.1.0 and 0.1.1, use the corrected identities. The pre-release correction preserves their versions and axioms.

The core vocabulary remains independent of gUFO. It neither imports gUFO nor adds equivalence, subproperty, or other alignment axioms between these generic terms and gUFO as part of this mapping. The generic terms are vocabulary resources, not JSON/metamodel mirrors or source-specific properties with a particular model's class domains/ranges.

### Vocabulary delivery modes

The specified CLI control is `--dkgm-vocabulary {import,embed,none}`. Python requires an equivalent control with the same choices, default and graph effects. See [Controls](../reference/controls.md#established-controls).

| Mode | Vocabulary contribution to the generated ontology |
| --- | --- |
| `import` (default) | Import the complete vocabulary at the stable `U`, even when no covered relation is mapped. All four generic object-property declarations and all three ordered chains come from the import closure. The generated graph omits local copies and the import always refers to the complete vocabulary. |
| `embed` | Supply the complete fixed core locally without network retrieval, even when no covered relation is mapped. The core consists of the four generic `owl:ObjectProperty` declarations and the three chains with their ordered RDF lists. Omit the DKGM import, the vocabulary's own ontology header, ontology annotations and term annotations. |
| `none` | Omit the DKGM import and generic chains. Add a local `owl:ObjectProperty` declaration for each generic property targeted by a bridge actually emitted under DK-REL-19. A graph without such a bridge receives no generic declarations. |

The embedded core is pinned to [DKGM 0.1.1](https://github.com/pedropaulofb/ontouml-directkg/blob/49122ec45a38378cf1fac0d6eae82456f4dedd5e/vocabulary/versioned/dkgm-vocabulary-v0.1.1.ttl), with version IRI `https://w3id.org/directkg/vocab/dkgm/0.1.1`. Embedding supplies its core axioms for consumers that cannot resolve the DKGM import. The generated ontology retains its own header and applicable mappings.

In `none`, consumers who need the generic entailments must supply the chain axioms or equivalent rules to their reasoner. An emitted bridge to `dkgm:memberOf`, `dkgm:subCollectionOf` or `dkgm:subQuantityOf` triggers a **nonfatal WARNING under every input policy, including `strict`**. The warning explains the absent chains and the need to supply them for those entailments. A `componentOf`-only graph gets its local declaration without this warning. With no emitted bridge, this warning does not apply. See [Diagnostics and recovery](../reference/diagnostics.md#structural-failures-sets-and-connectors) for the condition and reporting rules.

The default preserves the established domain axioms, stable import and diagnostic behavior. Enabled provenance records the effective vocabulary mode, including default `import`, so the configuration YAML can differ on a default run. [Effective configuration record](../guides/metadata-and-provenance.md#required-provenance-representation)

**Implementation status.** At `3d38f6018002bc060a907ed909e6398f0332bfe3`, the converter emits the stable import unconditionally. The CLI parser and Python conversion signature lack the vocabulary mode control, and the provenance configuration lacks the mode setting. The table and warning above describe accepted behavior. [CLI parser](https://github.com/pedropaulofb/ontouml-directkg/blob/3d38f6018002bc060a907ed909e6398f0332bfe3/src/ontouml_directkg/cli.py) · [Conversion source](https://github.com/pedropaulofb/ontouml-directkg/blob/3d38f6018002bc060a907ed909e6398f0332bfe3/src/ontouml_directkg/conversion.py)

## Source-specific properties

In every vocabulary mode, an eligible ordinary class-to-class relation carrying one of the recognized stereotypes retains its distinct primary object property and gains the corresponding direct bridge:

| Source stereotype | Generic superproperty of the primary property |
| --- | --- |
| `memberOf` | `dkgm:memberOf` |
| `subCollectionOf` | `dkgm:subCollectionOf` |
| `subQuantityOf` | `dkgm:subQuantityOf` |
| `componentOf` | `dkgm:componentOf` |

Here `dkgm:` is the **`U#` namespace**, `https://w3id.org/directkg/vocab/dkgm#`. The bridge is `Primary rdfs:subPropertyOf Generic`, not replacement or merging of source relations. Each covered primary property is also explicitly an `owl:AsymmetricProperty`. Asymmetry entails irreflexivity, so no separate irreflexivity declaration is required. Do not additionally declare its generated named inverse asymmetric solely from this stereotype; the inverse relationship already entails the corresponding consequence.

!!! warning "Source orientation is retained even when unintended"

    The recognized stereotype alone selects the bridge. Use the already established **primary direction**, even when it fails to express the author's intended part–whole orientation. Do not use `aggregationKind` to determine eligibility/direction, repair or reverse the relation, substitute a named/anonymous inverse, or create an inverse solely for the bridge. Source-specific naming, identity, domains/ranges, inverses, multiplicities, and generalizations retain their independently applicable mappings.

`isExtensional` adds no mereological logical axioms beyond its [comment mapping](classes.md#class-declarations-preserved-as-comments). Read-only and aggregation declarations retain their [comment mappings](property-features.md#read-only-and-aggregation-comments). The separate [lexical naming use of a unique aggregation marker](relations.md#structural-evidence-for-semantic-naming) changes neither this bridge's eligibility nor its direction.

## Generic chains and direction

The reusable vocabulary defines the following **ordered compositions**. A reasoner can obtain them through the import closure in `import` or the local core in `embed`. In `none`, they require consumer-supplied axioms or equivalent rules.

| Chain body, first step then second | Generic conclusion |
| --- | --- |
| `subCollectionOf`, `subCollectionOf` | `subCollectionOf` |
| `subQuantityOf`, `subQuantityOf` | `subQuantityOf` |
| `memberOf`, `subCollectionOf` | `memberOf` |

There is no generic `componentOf` transitivity or `componentOf` chain solely from the stereotype. None of the four generic properties is asymmetric by default, and no additional generic asymmetric superproperty is introduced.

In a symbolic semantic illustration, distinct source properties `r1` and `r2` both specialize `dkgm:subQuantityOf`. With the generic chain available to the reasoner, `a r1 b` and `b r2 c` entail `a dkgm:subQuantityOf c`. Those facts alone do **not** entail `a r1 c` or `a r2 c`.

Do not construct arbitrary source-specific chains merely because their stereotypes appear compatible, or materialize source-specific assertions solely for these generic consequences. A wrongly oriented source relation can therefore produce unintended generic consequences; DirectKG does not validate or fix that orientation.

### Simplicity and controls

In an axiom closure containing the accepted chains, `dkgm:memberOf`, `dkgm:subCollectionOf` and `dkgm:subQuantityOf` are non-simple because they are chain conclusions. A source-specific subproperty does **not** become non-simple merely by being beneath a non-simple generic superproperty. Source-specific asymmetry and cardinalities follow their own mapping rules. Other axioms can independently affect simplicity and OWL 2 DL compatibility. The [per-axiom compatibility gate](relations.md#compatibility-of-each-addition) for the five additional relation axioms accounts for the selected vocabulary mode. The [OWL profile contract](../reference/output.md#owl-profile-conformance) describes conformance assessment for each mode.

The vocabulary mode and `--material-property-chains` are independent controls. Selecting `none` for material chains disables only those chains. Their [targeted constraint treatment](derivations-and-chains.md#owl-compatibility) remains tied to emitted material chains. DK-REL-19's bridges and primary-property asymmetry and DK-PROP-04's source annotations apply in all vocabulary modes.

---

Governing rules: §3.3; DK-GEN-04; DK-REL-01, 04, 07, 19; DK-CLS-01; DK-PROP-04; DK-DIAG-01, 04; §15; baseline consolidated: **2026-11-13**, including the **2026-10-24** accepted DKGM identity correction; repository commit: `5578cc009c70bcf94e23b4154c06d849363e1488`; source: [`documentation/specification/transformation-specification.md`](https://github.com/pedropaulofb/ontouml-directkg/blob/5578cc009c70bcf94e23b4154c06d849363e1488/documentation/specification/transformation-specification.md).

Accepted update: **RD-05 — Optional caller-supplied ontology version IRI** (project-owner formalization, Option B, included in the cited consolidation).
