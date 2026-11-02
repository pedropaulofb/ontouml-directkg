# Inverse properties

These are **specified mappings**. The A1 role/domain fallbacks and numeric allocation below describe accepted intended behavior; converter conformance for these newly resolved cases has not been verified here. A separately named inverse is an auxiliary resource; an anonymous inverse expression traverses an existing property backwards. The two serve different purposes.

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
| Feature-facing expression in characterization–external-dependence disjointness | Primary when already aligned; otherwise its generated named inverse, or an anonymous inverse of the primary when none is generated |
| Backward material-chain step | **Always an anonymous inverse of the primary**, even when a named inverse exists |

These uses do not force named inverse generation, and do not establish anonymous-inverse mappings for other transformations. An unsupported connector cannot gain an inverse through this permission. See [Relation cardinalities](relations.md#relation-cardinalities), [Subsetting](property-features.md#subsetting), [Characterization and external dependence](relations.md#characterization-and-external-dependence), and [Material-chain modes](derivations-and-chains.md#material-chain-modes).

## Inverse naming

### Role and structural fallback

In name mode, only the inverse-facing role supplies the preferred role-based candidate. Select supported localized role text using [Multilingual naming](../reference/identifiers.md#multilingual-naming). Under either IRI strategy, retain applicable original role labels. With no role, do not synthesize an inverse label, including when generated primary-relation labels are enabled.

When the inverse-facing role is absent, or is present but yields no usable naming candidate, the name-strategy fallback is `inverseOf<ResolvedPrimaryPropertyLocalName>`; for example, resolved primary `employs` yields `inverseOfEmploys`. It uses the resolved primary name, not a new inverse role.

An unusable naming candidate does not make a present role absent. Keep its applicable original role labels and any applicable source-end description; the structural fallback supplies no invented label. An absent role still receives no synthetic label.

Apply this fallback whenever the selected mode requires the eligible inverse: `all`; `informed` when role presence or multiplicity triggers generation; and `named` when a role is present but unusable for naming. With an absent role, `named` still omits the inverse. Subsequent collisions follow the rules below.

Source-end descriptions annotate the generated named inverse; they do not cause generation. Do not automatically copy the relation description to it. Description and role language rules remain owned by [Labels and descriptions](../reference/text.md#labels-and-descriptions).

### Collisions and source-backed precedence

Resolve **all source-backed candidates and final IRIs first**. Enabling auxiliary inverses must not rename those resources.

1. Keep a unique role-derived inverse candidate unchanged.
2. If it collides with a source-backed resource, a source-backed candidate claim, or another inverse candidate, **every** colliding inverse abandons that role candidate for its own primary-based `inverseOf<ResolvedPrimaryPropertyLocalName>` fallback. Its role label remains unchanged; inverses are not merged.
3. If the primary-based fallback collides, further qualify only the inverse as `inverseOf<ResolvedPrimaryPropertyLocalName>_<InverseDomain>`. The inverse domain is the primary range. Use its normalized name when usable, with the original-text selector for supported localized names. Otherwise use `unnamedClass_<escaped-domain-class-id>`, based on that **domain classifier's own ID** and the established [technical escaping](../reference/identifiers.md#technical-source-id-escaping). Reuse this fallback candidate before classifier collision handling; do not include subsequently assigned classifier collision suffixes.
4. If that qualified candidate collides with a source-backed candidate claim, a final source-backed local name, or another remaining inverse candidate, apply [numeric allocation](#numeric-allocation). A unique candidate without such collisions stays unchanged.

### Numeric allocation

Use one shared reservation set containing all source-backed candidate claims and final source-backed local names, plus names of inverses retained without numeric allocation.

Group the inverses needing allocation by their **original qualified candidate**. Process those groups in ascending lexicographic order of the candidate strings, comparing Unicode code points. Within each group, process inverses in ascending lexicographic order of their **original inverse-facing association-end IDs**, also by Unicode code points. Do not trim, normalize, case-fold or escape those ordering IDs, or use JSON/source traversal order instead.

For each inverse, choose the smallest positive integer `n` for which `<original-qualified-candidate>_<n>` is not reserved. Reserve the assigned name immediately. Share reservations across all groups, including retained inverse names and every earlier allocation. Every inverse in a shared-candidate collision group receives a suffix; a lone inverse colliding with a source-backed name does too. Source-backed resources are not numbered group members and retain their IRIs.

Available slots give the usual `_1` through `_N` numbering. Occupied slots are skipped, so generated-inverse numbering may contain gaps. This is the narrow exception to [ordinary collision-group numbering](../reference/identifiers.md#qualification-and-collision-groups); it does not change source-backed numbering.

Keep the original qualified candidate throughout allocation. Preserve any numeric text already in it: do not reconstruct the base by stripping numbers or append a further suffix to an already allocated name to evade a blocked slot. The association-end ID supplies ordering only and does not enter the IRI merely for that purpose. Naming preserves inverse eligibility, distinct identities, direction, domains, ranges and applicable original role labels.

These are **specification illustrations, not captured converter output**. `Q` denotes an original qualified candidate, multiple inverses are listed in source-end-ID order, and all unlisted numeric slots are free.

| Original qualified candidate | Already reserved names | Inverses needing allocation | Assigned names |
| --- | --- | ---: | --- |
| `Q` | `Q` | 1 | `Q_1` |
| `Q` | `Q`, `Q_1` | 1 | `Q_2` |
| `Q` | `Q_1` | 2 | `Q_2`, `Q_3` |
| `Q` | `Q_1`, `Q_2` | 2 | `Q_3`, `Q_4` |
| `Q_1` | `Q_1` | 1 | `Q_1_1` |

The last row preserves numeric text in the original candidate. By contrast, when the original candidate is `Q` and slot `Q_1` is occupied, use `Q_2`, not `Q_1_1`. An inverse retained at `Q_1` reserves that name before allocation for a group using `Q`.

General name normalization and technical ID escaping remain distinct processes. These rules do not resolve the separate exceptional collision question for distinct escaped source IDs.

### ID mode and stability

ID mode uses the **source association-end ID**, processed by established escaping and exceptional-collision rules. Do not substitute the association ID, target-end ID, or the name-mode `inverseOf…` form. The [designated-ID table](../reference/identifiers.md#strategy-and-renaming) also explains primary-property identity.

Changing inverse mode can change generated inverse IRIs through inverse–inverse collisions, and changing the inverse-facing role can change a name-based inverse IRI. Source-backed IRIs remain unaffected by inverse-mode changes. Intentional omission under `informed` or `named` produces no warning, INFO, or element-level report entry. This silence does not cover malformed input, unresolved endpoints, or a failed primary transformation.

Structural role fallback, inverse-domain qualification and numeric allocation add **no diagnostic solely for those naming steps**. Existing missing-name, input and other independently applicable diagnostics still apply. See [Diagnostic conditions](../reference/diagnostics.md#names-typing-and-source-text).

The VP-plugin export path supplies at most one role name per end; the bounded language enrichment additionally supports localized fields. It does not establish arbitrary schema-conformant input or additional multilingual inverse algorithms.

## Explicit inverse specialization

For every successfully mapped **explicit relation generalization**, emit `SpecificInverse rdfs:subPropertyOf GeneralInverse` when both named inverses exist. If either is absent, omit this additional edge without a warning; do not create a named or anonymous inverse solely for it. Mirror explicit edges, not their transitive closure, and do not add semantic endpoint/domain/range compatibility checks.

[Complete singleton relation sets](relations.md#fully-resolved-singleton) also require the reverse general-inverse-to-specific-inverse inclusion when both inverses exist. Their added hierarchy participates in material-chain non-simplicity propagation.

This required mirroring is specific to relation generalizations. UML `subsets` and `redefines` produce their independently selected inclusion axioms, without additionally materializing inverse counterparts. Named-inverse disjointness pairs follow [Generalization and disjointness](relations.md#generalization-and-disjointness).

---

Governing rules: DK-INV-01–12; DK-REL-09, 14–15, 20; DK-PROP-03; DK-IRI-05–07, 10; DK-CONF-02; DK-DIAG-01; baseline consolidated: **2026-11-02**; repository commit: `0328ae1300e99eafbce7d5f32d2476c4aa5db71f`; source: [`documentation/specification/transformation-specification.md`](https://github.com/pedropaulofb/ontouml-directkg/blob/0328ae1300e99eafbce7d5f32d2476c4aa5db71f/documentation/specification/transformation-specification.md). A1.1, A1.2 and revised A1.3 are the accepted inverse-naming resolutions in this revision; architectural acceptance does not establish their implementation.

Accepted update: **RD-17 — Five relation-axiom additions with per-axiom OWL 2 DL compatibility** (project-owner formalization supplied after this baseline).
