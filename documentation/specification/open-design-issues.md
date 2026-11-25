# OntoUML DirectKG — Open Design Issues

## Purpose, sources, and reconciliation boundary

This is a **non-normative state document** for the next OntoUML DirectKG Architect conversation. It records unresolved design questions, not requirements or an implementation backlog. Use it together with the current Architect-maintained specification retrieved from GitHub. It is not a specification. The Architect maintains unresolved state alongside accepted specification registration; an independent Architect Reviewer verifies both documents.

**Compacted ledger (2026-11-25):** Following the 2026-11-25 closures of RD-02 and RD-04 (Decision 1 and Decision 2), all previously tracked design issues are closed. Per owner instruction (2026-11-25), the detailed targeted-maintenance log, historical 2026-10-29 reconciliation notes, and dated bounded-inspection research snapshots were archived to [`documentation/specification/archive/open-design-issues-20261125T154603Z.md`](archive/open-design-issues-20261125T154603Z.md) (predecessor commit `ade0de86886c9da316dfbcf2ea5e6d4a3a3447cc`, `2026-11-25T15:46:03Z`), leaving this concise state ledger.

**RD-27 historical evidence reconciliation (owner-reviewed, 2026-11-21).** Disposition: *Historical evidence reconciled — no outstanding in-scope requirement established.* The owner reports that the investigation recovered the relevant historical candidates, including descriptions, alternative names, editorial notes, and creators/contributors, and assessed them against the VP-plugin 0.5.3 export contract, the explicitly accepted input extensions, and the current normative specification. No concrete descriptive field was identified that is both within the accepted input scope and lacks an established transformation disposition.

The current specification retains the bounded input extension under §3.2, supported descriptions and language treatment under DK-LBL-02, naming and primitive-recognition rules under DK-IRI-10 and DK-DAT-02, deliberate omissions under DK-GEN-06–07, and project-name and external metadata mappings under DK-GEN-08–09. The owner approved closure on this evidence. The original Architect discussions could not be fully recovered, so this is a bounded historical reconciliation and does not claim reconstruction of every missing source or earlier acceptance. Any subsequently recovered evidence of a specific unresolved field is to be assessed independently. The older handoff's access warnings concerning named questions already settled in the current specification do not reopen those questions.

Alternatives and the advisory prioritization below are non-normative. No new mapping, recovery policy, or conformance guarantee is selected by preparing this document.

## Current open design issues

No unresolved design issues remain open following the 2026-11-25 closures of RD-02 and RD-04 (Decision 1 and Decision 2). Authoritative transformation, diagnostic, configuration, and delivery requirements reside in `documentation/specification/transformation-specification.md`. Raise a subsequent concrete issue independently only if an established requirement does not unambiguously determine behavior or a substantive change to semantics, input scope, or public behavior is requested.

## Advisory prioritization and dependencies

This is non-normative guidance for choosing future Architect discussions. It does not establish transformation requirements, an implementation plan, or completion claims.

Following the owner's 2026-11-06 direction, prioritize decisions that materially affect completion of the first transformation implementation and demonstrated supported use cases. Give hypothetical malformed-input and edge-case questions lower priority unless a concrete blocker or observed need establishes their relevance. An unresolved entry alone does not make its resolution a prerequisite for the first implementation.

The owner's 2026-11-17 direction prioritizes concluding the first-release transformation specification. Prefer minimal, well-bounded decisions. Defer deeper edge-case investigation and additional recovery frameworks, configuration options, validation mechanisms, or extensive handling unless concrete evidence establishes a demonstrated failure in supported inputs, a significant correctness risk, or a genuine implementation blocker.

The owner's 2026-11-22 direction is to prefer applying existing specification rules to hypothetical or unobserved edge cases whenever they adequately determine the required behavior. Treat incorrect handling of already governed cases as implementation gaps. Where a consequential behavior remains unspecified, register only the minimum necessary normative addition; use non-normative examples where helpful. An existing implementation guard alone does not justify a specialized requirement, exception, diagnostic identifier, or design decision.

Following the owner's 2026-11-10 direction, the Architect applies previously accepted residual-semantics warning treatment to demonstrably similar remaining related cases without seeking owner approval case by case. A concrete reason for different treatment is brought forward as a proposal. This authorization concerns warning treatment; it does not settle other logical-mapping or declaration-annotation choices, override explicit accepted diagnostic exceptions, or bypass independent Architect review.

The owner reports that repeated generalization-set membership does not occur in any of the over 200 models in the OntoUML/UFO Catalog. This corpus-wide absence is owner-reported; this registration does not claim a new Catalog-wide audit. Prior bounded Catalog inspections and owner-reported counts preserved in the archived snapshot likewise establish selected examples or historical scope observations only, not Catalog-wide frequency, verified exporter provenance, or end-to-end compatibility.

The owner's 2026-11-25 direction closes RD-02 as a standing generic structural-recovery design issue: the two remaining broad questions (affected and dependent output, and meaningful document-level processing) are addressed by the existing policies and the supplementary DK-DIAG-05 rule, and the explicitly outstanding mixed class/relation boundary is resolved in DK-GEN-12. The bounded review found no concrete unresolved architectural ambiguity within those recorded questions. This is not a claim of exhaustive malformed-input coverage or implementation/test completion. Raise a subsequent concrete issue independently only if established requirements do not unambiguously determine safe recovery or a substantive change to semantics, input scope, or public behavior is needed. Subsequent 2026-11-25 owner acceptance also closed RD-04 (Decision 1 and Decision 2); ordinary implementation and testing gaps are not design issues.

Accepted scope exclusions and registrations awaiting independent review are not unresolved design alternatives.

## Canonical references and archived research snapshots

These are canonical external reference URLs retained for future Architect investigations; listing them here is not a fresh execution or exhaustive review of those repositories or specifications.

- **Supported exporter release (`ontouml-vp-plugin` 0.5.3):** https://github.com/OntoUML/ontouml-vp-plugin/releases/tag/0.5.3
- **Exporter repository (`ontouml-vp-plugin`):** https://github.com/OntoUML/ontouml-vp-plugin
- **Foundational metamodel (`ontouml-metamodel`):** https://github.com/OntoUML/ontouml-metamodel
- **JSON schema reference (`ontouml-schema`):** https://github.com/OntoUML/ontouml-schema
- **JavaScript representation (`ontouml-js`):** https://github.com/OntoUML/ontouml-js
- **OntoUML/UFO Catalog (`ontouml-models`):** https://github.com/OntoUML/ontouml-models
- **OWL 2 Structural Specification (Second Edition, §§3.4, 5.8.1, 11.1–11.2):** https://www.w3.org/TR/2012/REC-owl2-syntax-20121211/
- **Standard provenance and metadata vocabularies:**
  - **PROV-O:** https://www.w3.org/TR/prov-o/
  - **DCMI Terms:** https://www.dublincore.org/specifications/dublin-core/dcmi-terms/
  - **SPDX:** https://spdx.org/rdf/terms/
- **Archived research snapshots and prior issue records:**
  - Full pre-compaction research snapshot (2026-11-25): [`documentation/specification/archive/open-design-issues-20261125T154603Z.md`](archive/open-design-issues-20261125T154603Z.md) — preserves the detailed dated bounded-inspection notes (ODI-IRI, event/dependence relations, RD-02, DKGM delivery, RD-04, ODI-INSTANCES), Catalog/exporter commit anchors, 2026-10-29 reconciliation details, and targeted-maintenance history.
  - Earlier archived snapshots: `documentation/specification/archive/`.

At continuation, the Architect retrieves this record and the current consolidated specification directly from GitHub. Registration and independent review status are reported separately from unresolved design state. A substantive integration conflict needs an explicit owner decision in the Architect workflow; it must not be silently resolved during record maintenance or independent review.
