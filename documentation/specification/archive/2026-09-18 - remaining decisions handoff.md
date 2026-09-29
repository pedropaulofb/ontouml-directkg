# OntoUML DirectKG — Open Design Issues

## Purpose, baseline, and reconciliation limits

This is a non-normative state document for the next Architect conversation. Use it together with the current Documenter-maintained specification. It is not a specification and must not be supplied as required input to the Documenter. Alternatives and recommendations below remain unaccepted unless explicitly identified as existing constraints.

Reconciled on 2026-09-18 against:

- `ontouml-directkg-specification.md`, titled **OntoUML DirectKG Specification Handoff**, snapshot date **2026-09-11**, working update **2026-09-18**, stored file version **26**. The storage version is not a project release number.
- `ontouml-directkg-remaining-decisions-handoff.md`, stored version **1**, and the byte-identical supplied copy `2026-09-12 - remaining decisions handoff.md`.
- The accessible Architect discussion and decision messages through message 190, including the complete consolidated **RD-09 — Enumeration representation, value identity, and input handling** transfer in message 188.
- The actual RD-09 follow-up acceptance in `Pasted markdown(20260918-100606).md`.
- The Architect operating protocol in `documentation/specification/prompts/03-architect-operating-protocol.md`, available in the supplied diff `Pasted text(20260913-212620).txt`.

**Reconciliation status: complete for the inspected prior issue inventory, but incomplete as an audit of the entire Architect session.** The supplied conversation excerpt omits earlier messages. The current specification establishes the rules visibly integrated there; it does not prove that every earlier accepted message was transferred. Missing original discussion, acceptance, or integration evidence has not been reconstructed from memory. Before treating this as an exhaustive session handoff, supply the omitted session material or an authoritative confirmation accounting for those transfers. This limitation does not reopen decisions already visible in the specification.

The next Architect session must pair this handoff with the specification consolidated after the separately identified pending transfers. Any substantive conflict exposed during integration must return to the Architect for the user's decision; this handoff does not resolve such conflicts.

Existing RD identifiers are retained. Additional descriptive `ODI-…` identifiers identify explicit gaps in the inspected specification that lacked an RD entry; they do not renumber the earlier inventory.

## Discussion depth and evidence discipline

Prioritize materially relevant specification coverage over recursively decomposing narrow defensive cases. The user explicitly requested this boundary when accepting partial class-generalization-set recovery. Keep residual structural cases grouped under RD-02 unless a concrete material choice requires separate discussion. No dedicated validation subsystem or survivor-count-specific feature is implied by the enumeration recovery rules.

The supported input commitment is VP-plugin **0.5.3**. Do not turn historical adapters, automatic exporter-version detection, arbitrary schema input, n-ary relations, or general implementation architecture into new requirements. A recorded future objective is not an active current-input design task.

Source URLs below preserve research anchors from the inspected material. This handoff did not rerun repository or corpus research. Reported corpus findings are snapshot evidence, not proof about all possible input.

## Source processing and output contracts

### RD-02 — Residual structural recovery

**Status:** Partially resolved; remaining recovery questions grouped for later discussion.

**Decision still needed:** Determine any material omission boundaries not already specified when `best-effort` encounters structurally unusable elements, especially invalid or duplicate identifiers and interacting unresolved references. Clarify when a failure prevents meaningful document processing, only to the extent required for unambiguous in-scope behavior.

**Resolved boundary:** DK-DIAG-05 fixes policy severity and continuation, requires valid delivered RDF, and prohibits invented information. DK-DIAG-03 fixes failure of ordinary directional relations. Cardinality parsing/recovery, empty generalization sets, partial class-set coverage/disjointness, and enumeration recovery are already decided; they are not open cases here. Stereotype acceptance is governed separately by DK-DIAG-06.

**Residual set cases:** The specification explicitly leaves missing or malformed membership containers, duplicate-member handling, and categorizer recovery after partial class-set failure unspecified. Retain them as grouped boundaries, not a sequence of increasingly narrow topics. DK-HO-02–03 governs fully transformable categorizers and powertypes; DK-CLS-09 settles only recovery of disjointness and coverage.

**Why it matters / constraints:** Recovery must not attach axioms to the wrong source identity, guess endpoints, introduce semantic validation, or close a class over an incomplete set. RD-04 must separately define how partial output is reported to callers.

**Evidence and next step:** The prior handoff records real null relation-end `propertyType` values. The supplied partial-set investigation found no clear present example of mixed usable/unusable members, but used searches and spot checks rather than an exhaustive integrity join. No new recovery alternative has been accepted. Review a concrete uncovered case against the existing generic rules before asking for another decision. Dependencies: ODI-IRI and, for categorizer recovery, the settled DK-HO rules; operational reporting belongs to RD-04.

### RD-04 — Output, profile, determinism, and diagnostic delivery

**Status:** Open; constrained by accepted mapping and diagnostic rules.

**Decisions still needed:** Default and supported RDF serializations; default prefixes; statement-order determinism; the declared OWL profile or conformance guarantees; diagnostic channels and formats; externally observable failure and partial-output status. Specify the public diagnostic/result contract without prescribing ordinary internal architecture.

**Context / constraints:** Turtle examples do not establish a default. IRI/collision determinism already follows DK-CONF-01–03. Punning is settled. DK-DIAG-07 already requires a nonfatal compatibility notice when material chains are emitted, and chain interactions must not suppress accepted cardinalities or property disjointness. An unconditional OWL 2 DL guarantee cannot simply disregard those accepted mappings. Existing warning/error severity and silence requirements must survive any reporting format; discarded instantiation-association data cannot be restored through reports (DK-INS-02).

**Alternatives retained:** stderr, logs, structured reports, or a combination were identified for diagnostic delivery; none is selected. Other choices require a focused proposal rather than inferring a decision from examples.

**Dependencies / next step:** Coordinate result status with RD-02, metadata/prefixes with RD-05 and RD-27–31, and profile wording with the remaining semantic mappings. Set the supported output contract and observable reporting behavior; no new validation feature is implied.

### ODI-CONTROLS — Remaining transformation-control interface choices

**Status:** Open; explicit gaps in specification §15 and DK-ATT-04.

**Decision still needed:** Exact argument spelling for the settled inverse-generation modes; the name of the existing default-off typed-attribute value-restriction option; and how established transformation controls are exposed through the CLI and Python library, including whether option parity is required.

**Boundary / significance:** The controls' already-settled behavior and defaults are not open. Public control availability affects whether callers can request the specified transformations. Function/class names, internal configuration objects, dependencies, packaging, performance, CI, and test framework design are ordinary implementation work outside this handoff. Dependency: ODI-VALUE-RESTRICTIONS for the unresolved enabled behavior and scope of that option; RD-04 for results/diagnostics.

## Hierarchies, properties, and relation semantics

### RD-13 — Remaining generalization-set boundaries

**Status:** Partially resolved.

**Decision still needed:** Completeness behavior for a fully resolved singleton **relation** generalization set, including whether and how its generated inverses participate.

**Resolved boundary:** Class-set disjointness and coverage, fully resolved class singletons, empty sets, partial class-set constraint recovery, relation-property disjointness and inverse pairs, and the multi-member relation-completeness limitation are settled (DK-CLS-06–09, DK-DIAG-12, DK-REL-15–16). The class-singleton rule does not automatically decide relation-singleton behavior. The multi-member coverage warning likewise does not establish a singleton limitation.

**Why it matters / evidence:** The accepted relation completeness discussion explicitly excluded the singleton because it does not require property union. No singleton proposal or acceptance is present in the accessible state. The previous OWL source anchor was [OWL 2 object-property axioms](https://www.w3.org/TR/owl2-syntax/#Object_Property_Axioms).

**Next step / dependencies:** Discuss the singleton boundary as one decision under the settled primary-property and inverse-specialization rules (DK-REL-14, DK-INV-12). Residual malformed/duplicate membership and partial categorizer recovery are grouped under RD-02, not additional RD-13 subtopics. No alternative is promoted to a recommendation here.

### RD-14 — Property subsetting and redefinition

**Status:** Open.

**Decision still needed:** Map or explicitly limit `subsettedProperties` and `redefinedProperties` for attributes and association ends. Determine whether explicit subsetting yields `rdfs:subPropertyOf`, how end references select a property direction, and what happens when a referenced source end corresponds to an inverse omitted by the selected mode. Determine whether any part of redefinition can be represented by subproperty semantics, requires separate range/cardinality treatment, or is instead annotated or diagnosed.

**Why it matters / constraints:** End identity and direction are already settled: target end identifies the primary property; source end identifies the named inverse in ID mode. RD-12's accepted mapping of relation generalization does not independently settle end subsetting or redefinition. Do not force inverse generation or borrow anonymous-inverse permission from cardinalities/chains without an accepted rule for this use.

**Alternatives / next step:** Direct subproperty treatment versus explicit limitation/annotation remains to be analyzed separately for the two source features. Preserve the accepted cardinality and relation-generalization mappings. Inspect actual VP-plugin 0.5.3 field production and reference direction before proposing behavior. Dependencies: RD-02 for unusable references; RD-04 if a chosen representation changes the profile.

### RD-16 — Other non-class relation endpoints

**Status:** Partially resolved; current-input remainder only.

**Decision still needed:** Establish treatment of other supported relation endpoints not represented as ordinary domain classes, beyond custom-datatype targets and the specific material–relator derivation case. Determine which actual 0.5.3 constructs require this decision before selecting a representation.

**Resolved boundary:** DK-DAT-05 covers custom datatype targets. DK-REL-08 fully determines current material–relator derivation handling; it is not an open output-representation choice. The conditional future objective for reliable derivation multiplicities is documented there and is not a current backlog item requiring a new mapping now.

**Alternatives retained from the prior issue:** Omission, annotation, punning/metamodeling, or reification were identified before the derivation-specific decision. Their applicability to other actual endpoint cases remains unassessed; none is an accepted general fallback.

**Evidence / next step:** The baseline reports that the 0.5.3 association-class export path defaults derivation ends to `"1"`. It cites `guizzardi2005ontological` at catalog commit `8ea0398cc273a49d9ea28aa534b1bb0316c6687c` as evidence of lost authored multiplicities. Do not infer support for those constraints from JSON defaults. Inspect remaining endpoint cases in the supported exporter; coordinate only genuine current cases with RD-02 and RD-04.

### RD-17 — Additional semantics of recognized relation stereotypes

**Status:** Partially resolved.

**Decision still needed:** Whether recognized stereotypes require additional semantic axioms beyond naming and the accepted material-chain pattern: parthood characteristics; characterization, mediation and dependence; event/historical relations; comparative relations; and any genuinely distinct remaining material semantics.

**Questions retained:** Transitivity, asymmetry, irreflexivity, functionality/inverse functionality, generic superproperties, and other stereotype-derived constraints or rules. Determine supported semantics or explicit limitations, without treating every conceivable axiom as a requested feature.

**Resolved boundary:** DK-REL-04–08 and DK-INV rules settle naming, ordinary inverses, material–relator connector omission, chain scope, default-off configuration, and backward steps. Do not reopen them or propose a parallel rule system merely because the historical 2013 transformation used SWRL. Characteristics cannot be inferred from intuitive names alone.

**Evidence / next step:** Consult the specific language semantics and 0.5.3 representations for a coherent stereotype group. The 2013 *An Automated Transformation from OntoUML to OWL and SWRL* remains precedent, not authority for a DirectKG rule. Dependencies: RD-24–25 where dependence/aggregation overlaps; RD-04 for profile implications. The baseline's general temporal-semantics gap is retained here and under RD-18 for actual supported constructs, not expanded into a temporal reasoning subsystem.

### RD-18 — Property stereotypes `begin` and `end`

**Status:** Open.

**Decision still needed:** Their supported source uses and effects on naming, annotations, diagnostics, or event-boundary/temporal semantics. No property-stereotype behavior may be borrowed automatically from relation-stereotype rules.

**Alternatives / next step:** Semantic mapping, annotation, or explicit non-representation with a defined diagnostic policy remain unselected. First verify how VP-plugin 0.5.3 exports them and what their language semantics support. This is mapping analysis, not a new semantic-validation pass. Dependencies: RD-17 for temporal/event overlap, RD-27 for annotation vocabulary, RD-04 for output constraints.

### ODI-DISJOINT — Serialization of stereotype-based class disjointness

**Status:** Open; semantics resolved, serialization only.

**Decision still needed:** Encode DK-CLS-03 ultimate-sortal and DK-CLS-04 cross-group disjointness without changing which pairs are disjoint.

**Alternatives / trade-offs:** Pairwise `owl:disjointWith` is directly inspectable; grouped encodings require careful grouping and list traversal. One `owl:AllDisjointClasses` list over all cross-group classes would incorrectly add intra-group disjointness.

**Unaccepted recommendation:** The specification §16 retains pairwise encoding as a recommendation for cross-group disjointness, not an accepted rule. RD-13's pairwise set encoding does not settle these other mappings. Next step: select the representation for the existing constraints; no additional semantic disjointness is being proposed.

### ODI-VALUE-RESTRICTIONS — Enabled `owl:allValuesFrom` behavior and scope

**Status:** Partially resolved (DK-ATT-04; specification §18 item 3).

**Decision still needed:** Whether enabling the existing typed-attribute option requires generation whenever the type is resolvable, rather than merely permitting it; and whether the same option applies to ordinary relations.

**Boundary / trade-off:** Default-off behavior, absence of restrictions for untyped/`void` attributes, and independence of cardinality requirements are settled. Mandatory enabled generation makes output predictable; retaining permissive generation leaves discretion. A default-off option for attributes is not acceptance of relation-wide scope.

**Unaccepted recommendation:** §16 recommends deterministic generation for resolvable types in enabled mode, but it was not adopted. Coordinate option spelling with ODI-CONTROLS and output expectations with RD-04. Discuss only the remaining strength and scope choices.

## Classifier and property metaproperties

The following retain their prior IDs and unresolved status. Shared constraints: no invented stereotype semantics; no semantic-validation requirement; preserve accepted mappings and use the supported exporter as the source contract. Annotation choices coordinate with RD-27; any added axioms coordinate with RD-04.

### RD-19 — `abstract` stereotype versus `isAbstract`

**Status / decision:** Open. Decide separately whether the class stereotype and the classifier flag (including on relations) are ignored, annotated, diagnosed, or receive a justified semantic representation.

**Context / next step:** DK-CLS-04 already uses the stereotype for cross-group disjointness; this does not decide further semantics. The earlier handoff notes the lack of a direct OWL construct for prohibiting direct instances except through specialization. Evaluate that source meaning against the settled higher-order model (DK-HO-01–04) without conflating stereotype and flag.

### RD-20 — `isDerived`

**Status / decision:** Open. Determine whether the classifier/property flag is ignored, annotated, used diagnostically, or given target semantics.

**Boundary / next step:** The flag is distinct from an explicit `derivation` relation and does not inherit RD-16 automatically. Inspect actual uses and discuss one consistent policy for the supported fields.

### RD-21 — `isExtensional`

**Status / decision:** Open, with source-shape evidence still needed. Decide whether the flag generates an axiom, annotation, no output, or is recognized only for input compatibility.

**Next step:** Verify its actual shape and availability in VP-plugin 0.5.3 before proposing semantic behavior. The supported version is settled; legacy-dialect support is not a prerequisite to reopen.

### RD-22 — `restrictedTo`

**Status / decision:** Open. Decide whether the field is internal transformation information, an annotation, or a source of additional semantic constraints/disjointness beyond the stereotype rules.

**Material boundary:** An effective set may be broader than the stereotype's usual default and may include `type`. Any treatment must respect the settled punning/order/powertype rules and the prohibition on OntoUML semantic validation. Next step: inspect exported values and distinguish any proposed transformation condition from a semantic appropriateness check.

### RD-23 — `isOrdered`

**Status / decision:** Open. Select treatment of ordered property values, which ordinary property assertions do not themselves preserve.

**Alternatives / trade-offs:** Ignore the flag, annotate it, warn when true, or represent ordered values through a list/sequence pattern. Structural representation preserves more ordering information but changes the output model.

**Unaccepted recommendation:** Lightweight annotation/diagnostic treatment was previously preferred over structural reification, but not adopted. Next step: decide the required preservation level before considering representation details.

### RD-24 — `isReadOnly` and existential dependence

**Status / decision:** Open. Define separate treatments for relation ends and class attributes.

**Context / questions:** The prior handoff identifies the exporter's opposite-end encoding of existential dependence. Determine whether it supports a semantic axiom, overlaps with stereotype semantics, requires handling when no corresponding stereotype is present, or should be annotated. Attribute read-only treatment independently remains undecided.

**Constraint / next step:** Do not infer OntoUML existential dependence from UML mutability alone. Reinspect the exporter encoding and language meaning before choosing a mapping. Dependency: RD-17 for overlapping dependence semantics.

### RD-25 — `aggregationKind` beyond orientation and naming

**Status / decision:** Open. Decide whether `COMPOSITE`, `SHARED`, and `NONE` are transformation-only information, annotations, or sources of further constraints/characteristics.

**Boundary / next step:** Existing use to identify the whole end is settled. No standard OWL characteristic follows from UML aggregation without explicit justification. Analyze remaining meaning together with the relevant RD-17 parthood semantics.

## Names, identifiers, labels, and datatypes

### ODI-IRI — Generic unnamed-element policy and remaining IRI boundaries

**Status:** Open; the generic unnamed-element question is explicitly deferred beyond the now-resolved RD-09, alongside explicit gaps in DK-IRI-01, DK-IRI-07, and DK-PROP-02.

**Decisions still needed:** Complete the generic policy for unnamed or unusably named source elements where existing element-specific rules do not already answer it, including IRI construction, diagnostics, and transformability. Also decide behavior for an invalid/unusable supplied base IRI, the exceptional disposition of an escaped-source-ID collision, and name-mode owner/source qualification when the owner/source is unnamed.

**Resolved boundary:** RD-09 is fully resolved for enumerations: representation, named-value IRIs and labels, identity/collisions, enumeration-owned properties, absent/null/empty lists, and incomplete-value recovery are settled. It rejects `unnamedLiteral_<escaped-source-id>` as an enumeration-specific fallback and does not authorize invented labels or silent omission of unnamed literals. No further enumeration-specific topic is required. DK-IRI-04 already supplies unnamed-class behavior and ID-mode diagnostics; primary relations and inverses have their own naming rules.

**Constraints:** Complete the uncovered generic boundary without replacing those element-specific rules. Preserve established base delimiters/default behavior, escaping, deterministic collision handling, distinct source identity, and source-backed precedence. Exceptional ID collisions must not be silently treated as ordinary name collisions. There is no accepted new generic fallback in the accessible record.

**Evidence / next step:** The RD-09 acceptance reports 202 catalog JSON files, 84 enumerations and 290 direct literals at commit `2a60b2f77f9e43734d1fdd98ebdec954a840dc18`, with no malformed/untransformable direct literals or partial-survivor examples. This supports proportionate treatment of the generic question; it does not prove such input cannot occur. Discuss a compact generic identity/failure policy with RD-02 and coordinate ontology-versus-namespace identity with RD-05. No new alternative has been accepted for these residual cases.

### RD-26 — Labels for unnamed generated resources

**Status:** Open only for remaining non-inverse relation labels.

**Decision still needed:** Whether an unnamed direct relation whose IRI comes from a target role, stereotype mapping, grounding relator, or source-target synthesis receives a generated label; if yes, whether/how it is distinguished from a source label.

**Constraints / trade-off:** Source names of named properties are retained. Unnamed classes receive no invented labels; inverse role labels and the no-synthetic-label inverse fallback are settled. Named enumeration literals require labels under RD-09. Source fidelity favors leaving absent names absent; usability may favor meaningful generated labels. These are alternatives, not a decision. Coordinate with RD-27 and the generic unnamed-element discussion.

### RD-27 — Multilingual names, descriptions, and general annotations

**Status:** Open, narrowed by the current exporter boundary.

**Decisions still needed:** Treatment of descriptions and supported project metadata; language-tag preservation; deterministic selection and label emission if supported source fields actually supply multiple language variants. Also settle the explicit MUST-versus-SHOULD conflict for named class and other still-unsettled non-property labels in DK-LBL-01.

**Boundary:** Named properties, inverse labels, and named enumeration literals have accepted requirements. DK-INV-11 does not require multilingual inverse-role selection for the current VP extraction path. Do not generalize standalone-schema multilingual capability into an input-support requirement.

**Alternatives / next step:** The prior handoff raised language preference order versus deterministic fallback, all source-language labels, and `rdfs:comment` versus another description annotation. Verify which fields the 0.5.3 export path actually supplies before selecting among them. Decide the label-strength conflict explicitly; do not silently strengthen SHOULD to MUST. Dependencies: RD-05 for header placement, RD-26 for generated labels, RD-28/30/31 for provenance and metadata scope.

### RD-28 — Source-ID provenance in name-based output

**Status:** Open.

**Decision still needed:** Whether name-mode resources receive source-ID annotations; if so, vocabulary, lexical form, multiplicity, and which IDs are preserved.

**Material directional case:** For relation properties, choose whether to record the target/source association-end ID, the enclosing association ID, or both. End-based directional identity is already settled and must not be replaced. Names may change while source IDs support tracing results across renames.

**Alternatives / constraints:** A DirectKG annotation and `dct:identifier` were discussed but not selected. Annotation benefits must be balanced against the lightweight output goal. DK-INS-02's deliberately discarded instantiation-association data must not reappear through this feature. Dependencies: RD-27 for annotations, RD-05 for ontology-level provenance. Next step: decide whether provenance is required before its representation.

### ODI-DATATYPES — Primitive and alias registry boundary

**Status:** Open; explicit in DK-DAT-02 and specification §18 item 25.

**Decision still needed:** The supported registry's completeness boundary and any explicitly admitted semantic aliases; define maintenance expectations only where they affect the public mapping contract.

**Constraints / next step:** Preserve accepted mappings, normalization-plus-exact-lookup behavior, distinct XSD meanings, `void` handling, and custom datatype reification. Illustrative aliases (`bool`, `str`, `wholeNumber`, `integer32`) are not activated by being mentioned. Establish whether the currently listed entries suffice for the supported contract or whether evidence requires additional explicit entries. Do not introduce fuzzy resolution or ordinary registry implementation architecture.

## Metadata, packages, and presentation structures

### RD-05 — Ontology identity and header metadata

**Status:** Open.

**Decisions still needed:** Whether an `owl:Ontology` resource is always emitted; its IRI relative to the entity base/namespace, including `#` and `/`; and treatment of version IRIs, imports, title, description, creators, provenance, licenses, and source-project metadata.

**Why it matters / constraints:** Header identity and resource namespace serve different roles. No gUFO import follows from using gUFO as conceptual background. Do not infer metadata not supplied by the source or user.

**Dependencies / next step:** Coordinate RD-27, RD-28, and RD-31 to place metadata at the proper level, and ODI-IRI for invalid-base behavior. Inspect available source-project fields before proposing a minimal header contract. No header alternative is adopted in the accessible state.

### RD-30 — `propertyAssignments`

**Status / decision:** Open. Determine whether custom tagged values are ignored, annotated, diagnosed, handled by an explicit whitelist, or exposed through user-defined mappings.

**Constraint / trade-off:** Arbitrary tags cannot be converted blindly into OWL properties without a namespace, datatype, and semantic policy. Retention can improve fidelity but may expand the mapping surface. User-defined mapping machinery is an unaccepted prior alternative, not a feature commitment. Inspect actual supported export content, then decide the preservation boundary; coordinate with RD-27 and RD-04.

### RD-31 — Package semantics and namespaces

**Status / decision:** Open. Determine whether source packages are ignored, retained as provenance/annotations, represented as modules or ontologies, or explicitly allowed to influence IRIs.

**Constraint / trade-off:** Package paths must not silently enter IRIs; package refactoring would then affect resource identity. Module/ontology treatment depends on RD-05. Next step: choose the intended semantic/provenance role before proposing namespace behavior. Coordinate with RD-27–28.

### RD-32 — Diagrams, views, and geometry

**Status / decision:** Open. Define explicit treatment of diagrams/views and concrete-syntax data supplied by the supported exporter: silent omission, separate provenance, or selected annotations. Determine whether visual topology has any diagnostic role when semantic references fail.

**Constraints / next step:** Layout, paths, coordinates, and placement must not change the ontology from valid model elements. Diagram topology is not an authorized repair source. Standalone-schema-only note/anchor structures are outside the current input contract. Inspect actual 0.5.3 exported structures and decide the preservation boundary without adding a repair mechanism implicitly. Dependencies: RD-02, RD-27–28, RD-04 if separate output is proposed.

## Remaining source-scope evidence boundary

### ODI-INSTANCES — Applicability of the recorded general instance-data gap

**Status:** Blocked on source-scope evidence; not an accepted feature expansion.

**Question retained:** Specification §18 item 13 records general instance-data transformation as unspecified. Determine whether any such data actually belongs to the supported VP-plugin 0.5.3 input and requires a current mapping, beyond higher-order classification and enumeration values.

**Boundary:** DK-HO rules, DK-INS-01–03, and RD-09 already govern their respective cases. DK-INS-01 describes concrete instantiation links as future support; that conditional statement must not be converted into a current requirement.

**Next step:** Verify applicability before opening a design topic. No representation alternatives or new instance-loading feature are proposed here. If there is no in-scope source construct requiring a decision, this evidence check does not justify expanding the backlog. Dependency: RD-16 only if an actual endpoint/representation interaction is found.

## Dependency order and continuation

This order is advisory, not a new project requirement:

1. Resume substantive mapping breadth: RD-14, remaining RD-16 input cases, and coherent RD-17–25 groups. Accepted cardinalities, relation generalization, and higher-order representation are prerequisites already satisfied, not topics to reopen.
2. Complete the limited hierarchy/value choices: remaining RD-13 singleton relation coverage, ODI-DISJOINT, and ODI-VALUE-RESTRICTIONS.
3. Address generic naming and metadata together: ODI-IRI, including the generic dependency referenced by resolved RD-09; RD-26–28; then RD-30–31 with RD-05. Check supported-source evidence before multilingual or instance-data design.
4. Consolidate only materially necessary residual RD-02 recovery questions. Do not recursively enumerate defensive variants. Coordinate diagnostic/result reporting with RD-04.
5. Finalize RD-32, ODI-CONTROLS, the required datatype-registry boundary, and RD-04's output/profile contract against the selected semantic scope.

The principal remaining dependency links are:

| Dependent topic | Relevant prerequisite or coordination |
|---|---|
| RD-14 | Settled RD-11/RD-12; RD-02 for structural failures |
| Remaining RD-13 | Settled relation-generalization/inverse rules; grouped RD-02 recovery |
| RD-17, RD-24, RD-25 | Joint dependence/parthood interpretation |
| ODI-IRI | Generic naming and identity treatment, including the dependency referenced by resolved RD-09; preserve existing fallbacks |
| RD-26–28, RD-30–31, RD-05 | Joint annotation, provenance, package, and ontology identity choices |
| ODI-CONTROLS | ODI-VALUE-RESTRICTIONS and RD-04 |
| RD-04 | Final semantic mappings, metadata scope, and RD-02 result behavior |

## Retained research anchors

- [VP-plugin 0.5.3 release](https://github.com/OntoUML/ontouml-vp-plugin/releases/tag/0.5.3): current supported export commitment.
- [VP-plugin source repository](https://github.com/OntoUML/ontouml-vp-plugin): earlier source study referenced `IAssociationTransformer.java`, `IGeneralizationTransformer.java`, `IGeneralizationSetTransformer.java`, `IClassTransformer.java`, `ClassSerializer.java`, and `ModelElementSerializer.java` under `src/main/java/it/unibz/inf/ontouml/vp/model/`.
- [Enumeration literal transformer, 0.5.3](https://github.com/OntoUML/ontouml-vp-plugin/blob/0.5.3/src/main/java/it/unibz/inf/ontouml/vp/model/vp2ontouml/IEnumerationLiteralTransformer.java) and [class transformer, 0.5.3](https://github.com/OntoUML/ontouml-vp-plugin/blob/0.5.3/src/main/java/it/unibz/inf/ontouml/vp/model/vp2ontouml/IClassTransformer.java): previously inspected separate literal/attribute paths. No historical-convention inference is warranted merely by enumeration-owned properties.
- [OntoUML metamodel](https://github.com/OntoUML/ontouml-metamodel), [OntoUML Schema](https://github.com/OntoUML/ontouml-schema/blob/master/src/ontouml-schema.yaml), and [OntoUML Vocabulary](https://dev.ontouml.org/ontouml-vocabulary/): baseline reference versions were Schema 1.0.2 and Vocabulary 1.1.1; these do not override the exporter contract.
- [Catalog](https://github.com/OntoUML/ontouml-models): earlier inspected snapshot `8ea0398cc273a49d9ea28aa534b1bb0316c6687c` contained 198 JSON models; the RD-09 acceptance reports 202 at `2a60b2f77f9e43734d1fdd98ebdec954a840dc18`. Preserve those distinct scopes.

No unresolved issue is resolved by this document. No optional recommendation is promoted to a requirement. The incomplete-session-evidence limitation at the start remains applicable when resuming.
