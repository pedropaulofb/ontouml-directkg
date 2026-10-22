# Inverse properties

These are **specified mappings**, without a verified converter implementation. A separately named inverse is an auxiliary resource; an anonymous inverse expression traverses an existing property backwards. The two serve different purposes.

## Generation and eligibility

The [canonical control catalog](../reference/controls.md#established-controls) owns `--inverse-properties`, its four values, and default `all`. `all` generates every eligible named inverse; `informed` needs an inverse-facing role or non-null multiplicity; `named` needs that role; `none` generates no named inverses. This control does not disable accepted anonymous inverse expressions.

A relation is eligible exactly when its supported binary primary transformation successfully produces an IRI-identified `owl:ObjectProperty` with two resolved classifier endpoints suitable as domain/range. Self-relations, supported stereotypes, and unnamed relations receiving generated IRIs remain eligible.

Instantiation declarations, covered derivation connectors, unsupported resolved relation-valued connectors, generalizations/sets, unsupported n-ary relations, and constructs represented only as assertions, annotations, or reified structures do not qualify. Datatype attributes do not qualify. Malformed relations must be diagnosed for their underlying structural problem, rather than silently called ineligible. Independently generated material/comparative relation properties retain their ordinary eligibility.

The inverse-facing end is the **source association end**: for primary `A → B`, its classifier `A` is the inverse's range. Under `informed`, `*` and `0..*` qualify as non-null multiplicities even though no numeric restriction results. Explicit null and an absent cardinality field do not qualify; a role can independently trigger generation. Field absence retains its own warning.

A role is present when it contains a non-whitespace character. In supported localized text, **any** such value is sufficient; successful ASCII normalization is not an extra eligibility condition. Lexical selection for naming and [language tagging](../reference/text.md#language-resolution) remain separate.

## Direction and anonymous inverses

A named inverse of primary `A → B` has explicit domain `B` and range `A`, and exactly one directed assertion `Inverse owl:inverseOf Primary`. Do not emit the redundant reciprocal assertion. The explicit domain/range declarations support inspection without reasoning, even though inverse semantics already entail them.

This **specification illustration** assumes a named `worksFor` relation from `Person` to `Organization`, source-end role `employee`, inverse mode `all`, name-based identity without collisions, and entity base `https://example.org/employment#`. It shows selected property/label assertions, not executed output; class declarations, other text, identifiers, header/import, cardinalities, and provenance are outside the excerpt.

```turtle
@prefix : <https://example.org/employment#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

:worksFor a owl:ObjectProperty ;
    rdfs:domain :Person ;
    rdfs:range :Organization .
:employee a owl:ObjectProperty ;
    rdfs:domain :Organization ;
    rdfs:range :Person ;
    owl:inverseOf :worksFor ;
    rdfs:label "employee" .
```

The example's untagged source label assumes no explicit override, local language, or single applicable project language.

| Use of an inverse direction | Required expression |
| --- | --- |
| Reverse-side ordinary relation cardinality | Corresponding named inverse when generated; anonymous inverse of the primary otherwise |
| Source association end in explicit UML subsetting/redefinition | Corresponding named inverse when generated; anonymous inverse of the primary otherwise |
| Backward material-chain step | **Always an anonymous inverse of the primary**, even when a named inverse exists |

These uses do not force named inverse generation, and do not establish anonymous-inverse mappings for other transformations. An unsupported connector cannot gain an inverse through this permission. See [Relation cardinalities](relations.md#relation-cardinalities), [Subsetting](property-features.md#subsetting), and [Material-chain modes](derivations-and-chains.md#material-chain-modes).

## Inverse naming

### Role and structural fallback

In name mode, only the inverse-facing role supplies the preferred role-based candidate. Select supported localized role text using [Multilingual naming](../reference/identifiers.md#multilingual-naming). Under either IRI strategy, retain applicable original role labels. With no role, do not synthesize an inverse label, including when generated primary-relation labels are enabled.

When no inverse-facing role is present, the name-strategy fallback is `inverseOf<ResolvedPrimaryPropertyLocalName>`; for example, resolved primary `employs` yields `inverseOfEmploys`. It uses the resolved primary name, not a new inverse role. This path serves `all` and multiplicity-triggered `informed`; `named` has no role-free generation path.

Source-end descriptions annotate the generated named inverse; they do not cause generation. Do not automatically copy the relation description to it. Description and role language rules remain owned by [Labels and descriptions](../reference/text.md#labels-and-descriptions).

### Collisions and source-backed precedence

Resolve **all source-backed candidates and final IRIs first**. Enabling auxiliary inverses must not rename those resources.

1. Keep a unique role-derived inverse candidate unchanged.
2. If it collides with a source-backed resource, a source-backed candidate claim, or another inverse candidate, **every** colliding inverse abandons that role candidate for its own primary-based `inverseOf<ResolvedPrimaryPropertyLocalName>` fallback. Its role label remains unchanged; inverses are not merged.
3. If the primary-based fallback collides, further qualify only the inverse as `inverseOf<ResolvedPrimaryPropertyLocalName>_<InverseDomain>`. The inverse domain is the primary range; supported localized domain names use the original-text selector.
4. If distinct inverses still share the qualified candidate, suffix every member deterministically `_1` through `_N`, ordered by the inverse-facing association-end ID. That ordering ID does not enter the IRI merely because it orders the group.

Do not silently extend these rules to unspecified exceptional cases. General name normalization and technical ID escaping remain distinct processes.

### ID mode and stability

ID mode uses the **source association-end ID**, processed by established escaping and exceptional-collision rules. Do not substitute the association ID, target-end ID, or the name-mode `inverseOf…` form. The [designated-ID table](../reference/identifiers.md#strategy-and-renaming) also explains primary-property identity.

Changing inverse mode can change generated inverse IRIs through inverse–inverse collisions, and changing the inverse-facing role can change a name-based inverse IRI. Source-backed IRIs remain unaffected by inverse-mode changes. Intentional omission under `informed` or `named` produces no warning, INFO, or element-level report entry. This silence does not cover malformed input, unresolved endpoints, or a failed primary transformation.

The VP-plugin export path supplies at most one role name per end; the bounded language enrichment additionally supports localized fields. It does not establish arbitrary schema-conformant input or additional multilingual inverse algorithms.

## Explicit inverse specialization

For every successfully mapped **explicit relation generalization**, emit `SpecificInverse rdfs:subPropertyOf GeneralInverse` when both named inverses exist. If either is absent, omit this additional edge without a warning; do not create a named or anonymous inverse solely for it. Mirror explicit edges, not their transitive closure, and do not add semantic endpoint/domain/range compatibility checks.

[Complete singleton relation sets](relations.md#fully-resolved-singleton) also require the reverse general-inverse-to-specific-inverse inclusion when both inverses exist. Their added hierarchy participates in material-chain non-simplicity propagation.

This required mirroring is specific to relation generalizations. UML `subsets` and `redefines` produce their independently selected inclusion axioms, without additionally materializing inverse counterparts. Named-inverse disjointness pairs follow [Generalization and disjointness](relations.md#generalization-and-disjointness).

---

Governing rules: DK-INV-01–12; DK-REL-09, 14–15, 20; DK-PROP-03; DK-IRI-05–06, 10; DK-CONF-02; baseline consolidated: **2026-10-21**; repository commit: `0307dd346c91346fa38bda2f8d57c9930b00751f`; source: [`documentation/specification/2026-10-21 - specification handoff.md`](https://github.com/pedropaulofb/ontouml-directkg/blob/0307dd346c91346fa38bda2f8d57c9930b00751f/documentation/specification/2026-10-21%20-%20specification%20handoff.md).
