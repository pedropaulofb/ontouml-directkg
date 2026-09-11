# Direct KG Transformation Specification — Handoff

**Status:** Working specification handoff  
**Snapshot date:** 2026-09-04  
**Repository:** https://github.com/pedropaulofb/ontouml-directkg

## 1. Document status and purpose

This document is a handoff snapshot of the Direct KG transformation specification as established in the design discussion up to 2026-09-04.

It is **not** the final Direct KG specification. Its purpose is to preserve the current project context, accepted design decisions, unresolved questions, and relevant non-normative recommendations so that the work can be resumed later without reconstructing the discussion from memory.

The source of truth for this handoff is the conversation in which Direct KG was designed. A rule is treated as established only when it was explicitly proposed as a decision or subsequently accepted/refined in the discussion. Items that were proposed but not clearly accepted are kept separate as recommendations or open questions.

The document deliberately distinguishes:

- source OntoUML semantics;
- transformation behavior;
- resulting RDF/OWL/Knowledge Graph semantics;
- serialization or implementation details.

It also distinguishes:

- requirements and accepted design decisions;
- recommendations;
- assumptions;
- unresolved issues.

---

# 2. Project context

## 2.1 Objective

Direct KG is a planned transformation from **OntoUML to a domain-oriented RDF/OWL Knowledge Graph**.

The repository for the project is:

https://github.com/pedropaulofb/ontouml-directkg

The working transformation name is:

```text
Direct KG
```

The objective is to provide a substantially simpler and more directly usable Knowledge Graph than transformations whose primary purpose is to preserve OntoUML metamodel structure or the exact structure of the OntoUML JSON serialization.

## 2.2 Existing approaches discussed

Two existing approaches motivated Direct KG.

### gUFO

gUFO preserves OntoUML's ontological commitments by mapping OntoUML models to the Unified Foundational Ontology (UFO).

Direct KG is not intended to replace that semantic approach. Its goal is different: to expose the **domain concepts explicitly modeled by the user** in a simpler, general-purpose KG.

### OntoUML JSON to Graph

OntoUML JSON to Graph is an earlier transformation developed by the project author. It transforms exported OntoUML JSON into Semantic Web formats such as Turtle while preserving much of the JSON structure and using internal identifiers to identify model elements.

Its result is therefore primarily a graph representation of the OntoUML serialization rather than a clean domain Knowledge Graph.

Direct KG is intentionally different: it should not reproduce OntoUML serialization machinery unless a clear domain-semantic or practical reason requires it.

## 2.3 Relationship to the 2013 transformation

Direct KG builds on the general transformation direction introduced in the 2013 paper:

> **An Automated Transformation from OntoUML to OWL and SWRL** (2013)

That earlier work transformed OntoUML constructs into OWL/SWRL while attempting to preserve selected OntoUML semantics.

Direct KG is not intended to mechanically reproduce the 2013 rules. The new transformation is being reconsidered in light of:

- the current OntoUML metamodel;
- the current OntoUML JSON Schema;
- the evolution of OntoUML since 2013;
- contemporary Semantic Web / Knowledge Graph practice;
- the requirement for a simpler, domain-oriented output.

Older transformation choices are therefore evidence and design precedent, not automatically binding requirements.

---

# 3. Transformation goals

The following goals have been established.

## 3.1 Domain-oriented output

Direct KG MUST target a **domain-oriented Knowledge Graph**, not an RDF serialization of OntoUML's abstract syntax or JSON representation.

OntoUML stereotypes, metamodel constructs, and serialization artifacts MAY influence transformation behavior without appearing as resources in the output.

## 3.2 General-purpose use

The transformation is intended to produce a general-purpose KG whose classes and properties correspond directly to domain concepts and relations modeled by the OntoUML user.

## 3.3 Simplification

Direct KG is intentionally pragmatic and simplified.

Simplification MUST NOT mean arbitrary information loss. Omissions and semantic reductions must be deliberate.

The default transformation should be relatively lightweight. More strongly axiomatized behavior may be offered through explicit options where already decided.

## 3.4 Avoid unnecessary meta-level structure

Direct KG should avoid exposing:

- OntoUML metamodel classes;
- JSON serialization objects;
- internal serialization relationships;
- other meta-level structures;

unless a later rule establishes a concrete semantic or practical reason to preserve them.

## 3.5 Preserve selected semantics

Direct KG preserves selected OntoUML semantics through OWL constructs such as:

- `owl:Class`;
- `rdfs:subClassOf`;
- class disjointness;
- OWL object/datatype properties;
- `rdfs:domain`;
- `rdfs:range`;
- cardinality restrictions;
- optional `owl:allValuesFrom` restrictions.

Not every OntoUML semantic feature has yet been assigned a Direct KG rule.

---

# 4. Scope and design principles

## 4.1 Current scope

The current work is focused on **transformation specification**.

Implementation architecture, programming language, libraries, CI/CD, packaging, deployment, and performance are outside the current discussion unless they directly affect transformation semantics.

## 4.2 Current source references

The conceptual source is the current OntoUML language/metamodel.

The current OntoUML JSON Schema is treated as the serialization and validation representation from which the transformation may resolve source elements and references.

JSON-specific structure MUST NOT be confused with domain semantics.

## 4.3 Current output model

The target is an RDF/OWL Knowledge Graph.

Examples in the discussion use Turtle for readability, but the supported output serialization formats have **not yet been specified**.

## 4.4 Lightweight default versus stronger optional restrictions

Direct KG's default output is intentionally lighter than a fully axiomatized OWL encoding.

In particular, local `owl:allValuesFrom` restrictions for typed attributes are optional and disabled by default, while property domain, property range when resolvable, and cardinality constraints are part of the established transformation contract.

## 4.5 No silent semantic guessing

Several rules embody the same principle:

> Direct KG may normalize syntax aggressively when explicitly defined, but MUST NOT invent semantic mappings not supported by the source model or a controlled Direct KG registry.

This principle applies particularly to:

- datatype recognition;
- custom datatype mapping;
- unnamed relation naming;
- IRI generation.

---

# 5. Terminology and definitions

## 5.1 Direct KG

The transformation specified in this document: a simplified, domain-oriented OntoUML-to-RDF/OWL Knowledge Graph transformation.

## 5.2 Source element

An element from the source OntoUML model / serialization, such as a class, property, relation, generalization, or datatype class.

## 5.3 Domain class

An OntoUML class that represents a domain type and is transformed into an `owl:Class`.

Recognized supported primitive datatype elements and Visual Paradigm `void` are exceptions and do not become domain OWL classes.

Custom OntoUML datatypes are reified as OWL classes and therefore do become generated classes.

## 5.4 Generated property

An OWL property created from an OntoUML attribute or relation.

A generated property is classified as either:

- `owl:DatatypeProperty`; or
- `owl:ObjectProperty`.

## 5.5 Visual Paradigm built-in datatype

A datatype name known to originate from Visual Paradigm's built-in datatype set.

The recognized built-ins established so far are:

```text
boolean
byte
char
double
float
int
long
short
string
void
```

## 5.6 Supported primitive datatype

A datatype whose normalized representation resolves through the controlled Direct KG primitive datatype registry to an XSD datatype.

This concept is broader than "Visual Paradigm built-in datatype" because Direct KG may recognize additional explicitly registered XSD datatype names.

## 5.7 Custom OntoUML datatype

A class stereotyped `datatype` whose normalized datatype name does not resolve to a supported primitive datatype and is not the special Visual Paradigm `void` case.

Custom datatypes are represented as reified OWL classes.

## 5.8 Reified value class

The Direct KG representation of a custom OntoUML datatype as an `owl:Class` whose instances represent structured values.

## 5.9 Usable name

A source name that exists and, when applicable, can be converted by the established name-normalization process into a valid non-empty Direct KG local name.

## 5.10 Name-based IRI strategy

The default IRI strategy in which generated IRIs are primarily based on source names.

## 5.11 ID-based IRI strategy

The optional IRI strategy in which generated IRIs are based on escaped source element IDs.

---

# 6. Established transformation rules

# 6.1 Class transformation

## Rule C-01 — Domain classes become OWL classes

Every OntoUML class representing a domain type MUST be transformed into an `owl:Class`.

The earlier unconditional rule:

```text
Every OntoUML Class → owl:Class
```

has been revoked.

The current exceptions are:

1. classes recognized as supported primitive datatypes;
2. the recognized but unsupported Visual Paradigm `void` datatype.

These exceptions do not generate local OWL classes.

Custom OntoUML datatypes **do** become OWL classes under the reified-value rule.

### Example

```text
«kind» Person
```

becomes conceptually:

```turtle
:Person a owl:Class .
```

### Consequence

Datatype-like source elements must first undergo datatype classification before Direct KG decides whether they become OWL classes.

---

# 6.2 Class generalization

## Rule C-02 — Preserve class hierarchy

For every OntoUML generalization whose specific and general classifiers are classes, Direct KG MUST preserve the hierarchy as:

```text
specific rdfs:subClassOf general
```

### Example

```text
Student → Person
```

becomes:

```turtle
:Student rdfs:subClassOf :Person .
```

### Notes

The discussion treated explicit generalizations as sufficient; Direct KG is not required to materialize the transitive closure of the subclass hierarchy.

Relation-to-relation generalization has not yet been specified.

---

# 6.3 Class disjointness

Two independent disjointness mechanisms have been established.

## Rule C-03 — Ultimate-sortal mutual disjointness

The following stereotypes form the ultimate-sortal set for this rule:

```text
{
    collective,
    kind,
    mode,
    quality,
    quantity,
    relator,
    type
}
```

Any two distinct generated OWL classes directly stereotyped with any stereotype in this set MUST be disjoint.

This applies even when both classes have the **same** ultimate-sortal stereotype.

### Examples

```text
A «kind»
B «kind»
→ A ⟂ B
```

```text
A «kind»
B «relator»
→ A ⟂ B
```

### Subclass consequence

If a subclass inherits disjointness through the generated class hierarchy, Direct KG need not redundantly assert the inferred disjointness.

Example:

```text
A «kind»
B «kind»
C «subkind»
C ⊑ A
A ⟂ B
```

OWL already entails:

```text
C ⟂ B
```

The extra assertion is not required.

## Rule C-04 — Cross-group stereotype disjointness

The following four stereotype groups have been established.

### Group 1

```text
{
    abstract,
    datatype,
    enumeration
}
```

### Group 2

```text
{
    event
}
```

### Group 3

```text
{
    situation
}
```

### Group 4

```text
{
    kind,
    collective,
    quantity,
    relator,
    mode,
    quality,
    subkind,
    role,
    phase,
    category,
    mixin,
    roleMixin,
    phaseMixin,
    historicalRole,
    historicalRoleMixin,
    type
}
```

Two generated OWL classes MUST be disjoint when their OntoUML stereotypes belong to **different groups**.

This rule is **inter-group**, not intra-group.

### Examples that imply disjointness

```text
«abstract» vs «kind»
«datatype» vs «event»
«enumeration» vs «situation»
«event» vs «situation»
«event» vs «role»
«situation» vs «relator»
```

### Examples that do not imply disjointness from this rule alone

```text
«event» vs «event»
«situation» vs «situation»
«role» vs «kind»
«datatype» vs «enumeration»
```

Another rule may nevertheless make two same-group classes disjoint, especially Rule C-03 for ultimate sortals.

### Primitive datatype exception

Recognized primitive datatype elements and `void` do not participate as OWL classes in these disjointness rules because they do not generate local `owl:Class` resources.

### Unresolved serialization detail

The semantic disjointness requirements are settled.

The exact OWL encoding strategy, e.g. pairwise `owl:disjointWith` versus suitable `owl:AllDisjointClasses` structures, has not yet been made normative.

---

# 6.4 Attribute transformation

## Rule A-01 — Attribute property kind

An OntoUML class attribute is classified according to its resolved `propertyType`.

```text
propertyType → supported primitive datatype
→ owl:DatatypeProperty
```

```text
propertyType → custom «datatype»
→ owl:ObjectProperty
```

```text
propertyType = null
→ owl:DatatypeProperty
```

```text
propertyType → void
→ owl:DatatypeProperty
→ unsupported datatype semantics
→ warning
```

The attribute's domain is always the owning class.

## Rule A-02 — Attributes express necessary conditions

Attribute class constraints are expressed through `rdfs:subClassOf` restrictions, not `owl:equivalentClass`.

This decision preserves attributes as necessary conditions on class instances rather than using them to define the owning class exhaustively.

---

# 6.5 Attribute cardinality

## Rule A-03 — Preserve explicit multiplicity as OWL cardinality restrictions

For an attribute with an explicit multiplicity, Direct KG MUST preserve that multiplicity using OWL cardinality restrictions.

Established mappings:

### `[1]`

```text
C ⊑ X exactly 1
```

### `[1..*]`

```text
C ⊑ X min 1
```

### `[0..1]`

```text
C ⊑ X max 1
```

### `[2..5]`

```text
C ⊑ X min 2
C ⊑ X max 5
```

### General `[l..u]`

```text
C ⊑ X min l
```

if `l > 0`, and:

```text
C ⊑ X max u
```

if `u` is finite.

When `l = u = n`, Direct KG MAY use an exact-cardinality restriction instead of separate minimum and maximum restrictions.

### Important independence

Cardinality constraints are independent from value-type restrictions.

A datatype or object-property range may be known even when local `only` restrictions are disabled, and cardinality restrictions remain required.

### Open case

The meaning of:

```text
cardinality = null
```

has not yet been specified.

---

# 6.6 Optional value-type restrictions

## Rule A-04 — `owl:allValuesFrom` is optional and disabled by default

The previously mandatory rule:

```text
C ⊑ X only Y
```

was revoked.

Direct KG's default transformation MUST remain lightweight and need not generate local `owl:allValuesFrom` restrictions for typed attributes.

A single explicit configuration option will control this behavior for both:

- attributes typed by supported primitive datatypes;
- attributes typed by custom OntoUML datatypes.

The exact option name has not yet been defined.

### Default

```text
value-type restriction option OFF
→ do not generate C ⊑ X only Y
```

### Option enabled

For a supported primitive:

```text
Person.age : int
→ Person ⊑ age only xsd:int
```

For a custom datatype:

```text
Person.age : AgeValue
→ Person ⊑ age only AgeValue
```

When the option is enabled and the type is resolvable, Direct KG MAY generate the corresponding restriction. The stronger proposal that enabling the option should make generation mandatory/deterministic was a recommendation, not an accepted requirement.

### Untyped attributes

If:

```text
propertyType = null
```

there is no `Y` to preserve, so no `only` restriction is generated.

### `void`

If the datatype is `void`, no `only` restriction is generated because Direct KG has no supported semantic range for `void`.

### Scope not yet extended

The discussion has established this optional behavior for typed **attributes**. Whether an equivalent local `only` restriction should be generated for ordinary OntoUML relations under the same option has not yet been specified.

---

# 6.7 Property domain generation

## Rule P-01 — Every generated OWL property has an `rdfs:domain`

Direct KG MUST generate an `rdfs:domain` axiom for every generated:

```text
owl:ObjectProperty
owl:DatatypeProperty
```

The domain is determined as follows:

```text
attribute
→ owning OntoUML class
```

```text
ordinary relation
→ source-end OntoUML class
```

### Examples

```text
Person.age : int
```

becomes:

```turtle
:age
    a owl:DatatypeProperty ;
    rdfs:domain :Person .
```

A custom-datatype-valued attribute:

```text
Person.age : AgeValue
```

becomes:

```turtle
:age
    a owl:ObjectProperty ;
    rdfs:domain :Person .
```

An ordinary relation:

```text
Person --employer--> Organization
```

becomes:

```turtle
:employer
    a owl:ObjectProperty ;
    rdfs:domain :Person .
```

### Semantic consequence

`rdfs:domain` has global inferential semantics. Using the property entails membership in the declared domain class. Direct KG deliberately adopts that semantics.

---

# 6.8 Property range generation

## Rule P-02 — Generate `rdfs:range` whenever the target is unambiguously resolvable

Direct KG MUST generate an `rdfs:range` axiom whenever the source property type or relation target can be unambiguously resolved to a supported Direct KG range.

### Supported primitive attribute

```text
Person.age : int
```

becomes:

```turtle
:age
    a owl:DatatypeProperty ;
    rdfs:domain :Person ;
    rdfs:range xsd:int .
```

### Custom datatype attribute

```text
Person.age : AgeValue
```

becomes:

```turtle
:age
    a owl:ObjectProperty ;
    rdfs:domain :Person ;
    rdfs:range :AgeValue .
```

### Ordinary relation

```text
Person --employer--> Organization
```

becomes:

```turtle
:employer
    a owl:ObjectProperty ;
    rdfs:domain :Person ;
    rdfs:range :Organization .
```

### Untyped attribute

```text
propertyType = null
→ no rdfs:range
```

### `void`

```text
propertyType → void
→ no rdfs:range
→ warning
```

### General principle

```text
resolvable supported target/type
→ MUST generate rdfs:range
```

```text
unresolvable / unsupported target/type
→ MUST NOT invent rdfs:range
```

---

# 6.9 Untyped attributes

## Rule A-05 — `propertyType = null` means no datatype specified

When:

```json
"propertyType": null
```

Direct KG MUST interpret this as:

> the source model does not specify the attribute's value datatype.

Direct KG MUST NOT guess or infer a datatype.

The attribute MUST still become an `owl:DatatypeProperty`.

If multiplicity is defined, its cardinality restriction MUST still be generated.

No datatype range or value-type restriction is generated.

### Forbidden substitutions

Direct KG MUST NOT map the missing type to:

```text
rdfs:Literal
xsd:string
```

or any other guessed datatype.

---

# 6.10 Visual Paradigm primitive datatypes

## Rule D-01 — Recognized Visual Paradigm built-ins

The recognized Visual Paradigm built-in datatype names established so far are:

```text
boolean
byte
char
double
float
int
long
short
string
void
```

`void` is recognized but unsupported.

## Rule D-02 — Core supported VP-to-XSD mappings

The following mappings are established:

```text
boolean → xsd:boolean
byte    → xsd:byte
char    → xsd:string
double  → xsd:double
float   → xsd:float
int     → xsd:int
long    → xsd:long
short   → xsd:short
string  → xsd:string
```

The mapping:

```text
char → xsd:string
```

intentionally loses the one-character constraint.

---

# 6.11 Primitive datatype normalization and registry resolution

## Rule D-03 — Normalize lexically, resolve semantically through an explicit registry

Direct KG MUST normalize datatype names before primitive resolution.

The adopted strategy is:

```text
aggressive lexical normalization
+
strict registry-based semantic resolution
```

Normalization MUST NOT itself determine semantics.

Primitive-datatype resolution applies to source elements being interpreted as datatype classes: conceptually, a source element of type `Class` with stereotype `datatype`. An ordinary domain class MUST NOT be classified as a primitive datatype merely because its human-readable name happens to match a primitive registry key.

### Normalization steps

For primitive-datatype recognition, Direct KG SHOULD:

1. apply Unicode normalization;
2. trim leading/trailing whitespace;
3. case-fold the datatype name;
4. recognize known XSD prefix or namespace forms before ordinary local-name normalization;
5. ignore common lexical separators:
   - whitespace;
   - hyphen (`-`);
   - underscore (`_`);
6. perform an exact lookup using the resulting normalized key.

### Examples

```text
PositiveInteger
Positive Integer
positive_integer
positive-integer
POSITIVE_INTEGER
```

normalize to:

```text
positiveinteger
```

Likewise:

```text
Non Negative Integer
non-negative-integer
non_negative_integer
```

normalize to:

```text
nonnegativeinteger
```

## Rule D-04 — Controlled primitive registry

After normalization, Direct KG MUST perform exact lookup in a controlled registry.

The discussion explicitly established / illustrated the following canonical mappings for that registry:

```text
boolean            → xsd:boolean
byte               → xsd:byte
char               → xsd:string
double             → xsd:double
float              → xsd:float
int                → xsd:int
integer            → xsd:integer
long               → xsd:long
short              → xsd:short
string             → xsd:string
decimal            → xsd:decimal
date               → xsd:date
datetime           → xsd:dateTime
positiveinteger    → xsd:positiveInteger
nonnegativeinteger → xsd:nonNegativeInteger
unsignedint        → xsd:unsignedInt
```

The registry was specified with `SHOULD` language and examples rather than as an explicitly closed exhaustive list.

Semantically distinct XSD datatypes MUST remain distinct.

In particular:

```text
int     → xsd:int
integer → xsd:integer
```

MUST NOT be collapsed.

## Rule D-05 — Explicit XSD identifiers

Direct KG SHOULD recognize standard XSD datatype identifiers directly.

Examples:

```text
xsd:int
XSD:int
xsd:Int
```

should resolve to:

```text
xsd:int
```

The full standard XSD datatype IRI SHOULD also be recognized.

Recognition of a known XSD namespace/prefix happens before lexical normalization of the local datatype name.

## Rule D-06 — Semantic aliases are explicit only

Lexical normalization and semantic aliases are separate mechanisms.

Aliases such as:

```text
bool → boolean
str → string
wholeNumber → integer
integer32 → int
```

MUST only be accepted when explicitly registered in a separate alias registry.

Direct KG MUST NOT infer such aliases automatically.

## Rule D-07 — Forbidden automatic datatype guessing

Direct KG MUST NOT use:

```text
fuzzy matching
edit-distance correction
stemming
singular/plural normalization
automatic abbreviation expansion
automatic translation
semantic synonym detection
```

for primitive datatype recognition.

Examples:

```text
Integar
```

MUST NOT silently become `xsd:integer`.

```text
whole number
```

MUST NOT become `xsd:integer` unless explicitly registered as an alias.

---

# 6.12 Visual Paradigm `void`

## Rule D-08 — `void` is recognized but unsupported

Visual Paradigm `void` MUST be treated as an unsupported datatype.

For a source class:

```text
type = Class
stereotype = datatype
name = void
```

Direct KG MUST:

- recognize it as VP `void`;
- NOT map it to an XSD datatype;
- NOT generate an OWL datatype for it;
- NOT generate an OWL class for it.

Direct KG MUST NOT map `void` to:

```text
rdfs:Literal
owl:Nothing
owl:bottomDataProperty
xsd:anySimpleType
xsd:anyAtomicType
```

or to a locally invented empty datatype.

## Rule D-09 — Attribute using `void`

An attribute typed by `void`:

- still becomes an `owl:DatatypeProperty`;
- still receives its `rdfs:domain`;
- still preserves defined cardinality;
- receives no `rdfs:range` from `void`;
- receives no local `only` datatype restriction;
- MUST emit a warning;
- MUST NOT stop the transformation by itself.

The warning SHOULD identify at least:

- the attribute;
- the owning class;
- the source datatype `void`;
- that `void` is unsupported;
- that no datatype mapping/range can be generated.

The distinction from `propertyType = null` is normative:

```text
null
→ no datatype was specified
```

```text
void
→ a datatype was explicitly selected, recognized, but unsupported
```

The unsupported status of `void` MUST be explicitly documented in the eventual specification and user-facing documentation.

---

# 6.13 Custom OntoUML datatypes

## Rule D-10 — Custom datatypes become reified value classes

A custom OntoUML datatype is a class stereotyped `datatype` whose normalized name does not resolve through the supported primitive registry and is not `void`.

It MUST be transformed into an `owl:Class`.

### Example

```text
«datatype» AgeValue
-------------------
ageInYears  : int [1]
ageInMonths : int [1]
ageInDays   : int [1]
```

becomes fundamentally:

```text
AgeValue       → owl:Class
ageInYears     → owl:DatatypeProperty
ageInMonths    → owl:DatatypeProperty
ageInDays      → owl:DatatypeProperty
```

with applicable domain, range, and cardinality rules.

## Rule D-11 — References to custom datatypes become object properties

If a class attribute has a custom datatype as `propertyType`, the attribute MUST become an `owl:ObjectProperty`.

Example:

```text
Person.age : AgeValue
```

becomes:

```text
Person   → owl:Class
AgeValue → owl:Class
age      → owl:ObjectProperty
```

with:

```text
rdfs:domain Person
rdfs:range  AgeValue
```

and applicable cardinality restrictions.

## Rule D-12 — Do not flatten custom datatypes

Direct KG MUST preserve the explicit structured value.

For example:

```text
Person
   |
   | age
   v
AgeValue
   ├── ageInYears
   ├── ageInMonths
   └── ageInDays
```

MUST NOT be flattened into:

```text
Person
   ├── ageInYears
   ├── ageInMonths
   └── ageInDays
```

## Rule D-13 — Explicit relations to custom datatypes use the same representation

If the connection to a custom datatype is represented as an explicit OntoUML relation rather than an attribute, the custom datatype still becomes an `owl:Class`, and the generated connection is an `owl:ObjectProperty` whose range is that class.

The syntactic choice between an attribute and an explicit relation MUST NOT cause Direct KG to flatten or discard the custom datatype structure.

## Rule D-14 — Recursive transformation

The internal properties of a custom datatype MUST be transformed recursively under the same property classification rules.

Example:

```text
«datatype» AgeValue
years     : int
precision : PrecisionValue

«datatype» PrecisionValue
amount : double
unit   : string
```

becomes conceptually:

```text
AgeValue       → owl:Class
PrecisionValue → owl:Class

years     → owl:DatatypeProperty
precision → owl:ObjectProperty

amount → owl:DatatypeProperty
unit   → owl:DatatypeProperty
```

## Rule D-15 — No XSD guessing from custom datatype names

Direct KG MUST NOT infer an XSD datatype from a custom datatype's name.

Example:

```text
«datatype» TimeInterval
```

MUST NOT automatically become:

```text
xsd:duration
```

unless a future explicit transformation rule establishes that mapping.

---

# 6.14 Property identity

## Rule P-03 — Distinct source properties/relations remain distinct OWL properties

Each distinct OntoUML source property or relation MUST be transformed into a distinct OWL property IRI.

Direct KG MUST NOT automatically merge different source properties merely because they have the same name.

This is the single established property-identity strategy. There is no configurable "merge same-name properties" mode.

## Rule P-04 — No union-based repair for merged properties

Direct KG MUST NOT merge same-name properties and then use constructs such as:

```text
ObjectUnionOf(...)
DataUnionOf(...)
```

merely to reconcile different ranges.

Example:

```text
Person.age   : int
Building.age : AgeValue
```

MUST remain two distinct properties.

## Rule P-05 — Property kind is independent from property identity

Disambiguating the IRI does not change whether the property is an object property or datatype property.

Example:

```text
Person.age : int
→ owl:DatatypeProperty
→ rdfs:range xsd:int
```

```text
Building.age : AgeValue
→ owl:ObjectProperty
→ rdfs:range AgeValue
```

---

# 6.15 General IRI configuration

## Rule I-01 — Two IRI strategies

Direct KG MUST support:

```text
--iri-strategy name
--iri-strategy id
```

The default MUST be:

```text
--iri-strategy name
```

## Rule I-02 — Configurable base IRI

Direct KG MUST support:

```text
--base-iri <IRI>
```

If no base IRI is provided, Direct KG MUST use:

```text
https://example.org/directkg#
```

and MUST emit a non-fatal warning.

The default namespace is a placeholder, not the recommended namespace for publication.

## Rule I-03 — Base delimiter normalization

If the user-provided base IRI ends with:

```text
#
```

or:

```text
/
```

Direct KG MUST preserve that delimiter.

If the base IRI ends in neither `#` nor `/`, Direct KG MUST append:

```text
#
```

No warning is required merely for appending the missing delimiter.

---

# 6.16 Name-based IRI strategy

## Rule I-04 — Name strategy prioritizes readability

In:

```text
--iri-strategy name
```

generated IRIs are based primarily on human-readable source names.

Example:

```text
name = Person
```

with base:

```text
https://example.org/directkg#
```

generates:

```text
https://example.org/directkg#Person
```

Renaming a source element may therefore change its generated IRI even if the source ID remains unchanged.

The eventual documentation MUST make this stability consequence clear.

---

# 6.17 Name-based IRI normalization

## Rule I-05 — Lexical, deterministic, non-semantic normalization

The established name-normalization pipeline is:

```text
source name
→ Unicode normalization
→ trim
→ remove diacritics
→ replace whitespace/punctuation with "_"
→ collapse "_"
→ strip leading/trailing "_"
→ restrict to ASCII letters/digits/underscore
→ prefix "_" if necessary
→ collision handling
```

A canonical decomposition-based Unicode normalization SHOULD be used before diacritic removal.

### Examples

```text
Número   → Numero
Situação → Situacao
João     → Joao
```

```text
Birth Date             → Birth_Date
birth-date             → birth_date
Person / Organization  → Person_Organization
```

Consecutive underscores are collapsed.

## Rule I-06 — Conservative safe character set

Normal generated local names use:

```text
A-Z
a-z
0-9
_
```

Conceptually:

```text
[A-Za-z_][A-Za-z0-9_]*
```

## Rule I-07 — Leading digit for name-based local names

If the normalized local name begins with a digit, Direct KG MUST prefix:

```text
_
```

Example:

```text
3D Model
→ _3D_Model
```

## Rule I-08 — Preserve terminology; no semantic normalization

Direct KG MUST NOT:

- translate;
- singularize/pluralize;
- expand abbreviations;
- spell-correct;
- substitute synonyms;
- fuzzy-match;
- infer semantic equivalence;
- rewrite terminology merely for vocabulary preference.

Example:

```text
Pessoa Jurídica
→ Pessoa_Juridica
```

MUST NOT automatically become:

```text
Legal_Person
```

---

# 6.18 Unusable and unnamed names

## Rule I-09 — Unusable normalized names use the unnamed-element fallback

If a source name exists but normalization produces no usable local name, Direct KG MUST treat the name as unusable for IRI generation.

Example:

```text
!!!
```

may normalize to an empty value.

Direct KG then uses the relevant unnamed-element fallback and emits a warning.

The original source name, if present, MAY still be preserved as `rdfs:label`.

---

# 6.19 Unnamed classes

## Rule I-10 — Synthetic IRI for unnamed classes in name-based mode

If a class has no usable name, Direct KG MUST generate:

```text
unnamedClass_<escaped-source-id>
```

Example:

```text
id = aB92xK
name = null
```

becomes:

```text
unnamedClass_aB92xK
```

under the selected base IRI.

The class stereotype MUST NOT be inserted into the synthetic IRI.

Thus:

```text
unnamedClass_aB92xK
```

is correct, while:

```text
unnamedClass_Kind_aB92xK
```

is not.

This preserves IRI stability if the stereotype changes while source identity remains the same.

## Rule I-11 — No invented label for unnamed class

Direct KG MUST NOT invent an `rdfs:label` such as:

```text
"Unnamed Class"
```

for an unnamed class unless such text actually exists in the source.

## Rule I-12 — Warn on unnamed class fallback

Whenever Direct KG generates the synthetic unnamed-class IRI, it MUST emit a non-fatal warning identifying, where available:

- source element type;
- source element ID;
- stereotype;
- generated IRI.

Transformation MUST continue.

---

# 6.20 ID-based IRI strategy

## Rule I-13 — Source ID forms the IRI local name

Under:

```text
--iri-strategy id
```

Direct KG MUST use the escaped source element ID as the basis of the generated IRI.

Example:

```text
id = aB92xK
```

becomes:

```text
https://example.org/directkg#aB92xK
```

if that is the configured base.

The source human-readable name remains available separately through `rdfs:label` according to the labeling rules.

## Rule I-14 — Unnamed elements still generate diagnostics in ID mode

Because ID-based IRI generation does not depend on names, an unnamed element does not require the synthetic `unnamed<Type>_...` fallback.

However, the diagnostic policy remains: Direct KG MUST still warn that the source element is unnamed.

---

# 6.21 Source ID escaping

## Rule I-15 — Names and IDs use different normalization mechanisms

Human-readable source names use the name-normalization algorithm.

Source IDs MUST undergo only deterministic technical escaping.

Source IDs MUST NOT be:

- lowercased;
- uppercased;
- trimmed;
- translated;
- spell-corrected;
- Unicode-transliterated;
- stripped of diacritics;
- semantically normalized;
- rewritten for readability.

## Rule I-16 — Exact source-ID escaping algorithm

For each source ID:

1. preserve ASCII letters `A-Z` and `a-z`;
2. preserve ASCII digits `0-9`;
3. encode every other UTF-8 byte as:

   ```text
   _xHH
   ```

   where `HH` is the uppercase hexadecimal byte value;
4. process non-ASCII characters byte-by-byte after UTF-8 encoding;
5. do not preserve `_` literally; encode it as:

   ```text
   _x5F
   ```

### Examples

```text
aB92xK
→ aB92xK
```

```text
A3Jb3OGFS_j2pBF8
→ A3Jb3OGFS_x5Fj2pBF8
```

```text
9rqa._6AUB1CSiNo
→ 9rqa_x2E_x5F6AUB1CSiNo
```

Escaping `_` makes the transformation reversible and prevents ambiguity with Direct KG's own `_xHH` escape syntax.

## Rule I-17 — Use escaped IDs inside synthetic identifiers

Whenever a source ID is embedded into another local name, the escaped form MUST be used.

Example:

```text
id = 9rqa._6AUB1CSiNo
```

in an unnamed class becomes:

```text
unnamedClass_9rqa_x2E_x5F6AUB1CSiNo
```

## Rule I-18 — Leading digit in ID-based local names

If the escaped source ID itself is the complete local name and begins with a digit, Direct KG MUST prefix:

```text
id_
```

Example:

```text
9rqa._6AUB1CSiNo
```

becomes:

```text
id_9rqa_x2E_x5F6AUB1CSiNo
```

This prefix is unnecessary when the escaped ID already appears after a safe prefix.

Correct:

```text
unnamedClass_9rqa_x2E_x5F6AUB1CSiNo
```

Incorrect:

```text
unnamedClass_id_9rqa_x2E_x5F6AUB1CSiNo
```

## Rule I-19 — Escaping must preserve ID distinctions

The escaping algorithm MUST be injective with respect to source-ID byte sequences.

It SHOULD be reversible.

Ordinary name-based numeric collision suffixes are not expected merely because two source IDs were escaped.

If distinct source IDs nevertheless produce a generated-IRI collision, Direct KG MUST treat that as an exceptional condition rather than silently merging elements.

---

# 6.22 IRI collision handling

## Rule I-20 — All members of a name-based collision set receive suffixes

In name-based IRI generation, after all applicable name/fallback generation and property owner/source disambiguation, Direct KG MUST check for generated local-name collisions. This ordinary numeric collision mechanism does not replace the separate ID-based rule: a collision between distinct escaped source IDs is exceptional and MUST NOT be silently repaired as an ordinary name collision.

If a generated base name is unique:

```text
<base>
```

is used unchanged.

If `N` distinct source elements collide on the same final candidate base:

```text
<base>_1
<base>_2
...
<base>_N
```

MUST be used.

Direct KG MUST NOT use:

```text
<base>
<base>_1
<base>_2
```

for a collision set.

Suffix assignment MUST be deterministic and stable across repeated transformations of an unchanged source model.

## Rule I-21 — Deterministic numbering in name-based collision sets

For name-based collision sets, the implementation SHOULD use stable source-model information, preferably source element IDs or another deterministic source order, to assign `_1 ... _N`.

The same source element MUST receive the same suffix across repeated transformations of the unchanged model.

---

# 6.23 Property IRI disambiguation

## Rule P-06 — Use the lexical property name directly when unique

Under name-based generation, if a property/relation base name is unique, Direct KG MAY use that normalized property name directly as the IRI local name.

Example:

```text
Person.name
→ :name
```

## Rule P-07 — Owner/source qualification for ordinary same-name properties

Under name-based IRI generation, if distinct source properties or relations would otherwise receive the same property IRI, Direct KG MUST first disambiguate them using the owning or source class. ID-based generation instead uses the escaped source ID directly and does not use owner/source qualification for ordinary identity preservation.

The preferred pattern is:

```text
<propertyName>_<ownerOrSourceName>
```

not:

```text
<ownerOrSourceName>_<propertyName>
```

Example:

```text
Person.age
Building.age
```

becomes:

```text
age_Person
age_Building
```

before generic final collision handling.

## Rule P-08 — Remaining name-based collisions use numeric suffixes

Under name-based IRI generation, if owner/source qualification still produces a collision, the previous source-ID-in-IRI fallback has been superseded.

All members of the collision set receive deterministic numeric suffixes.

Example:

```text
Person.code
Person.code
```

becomes:

```text
code_Person_1
code_Person_2
```

The source IDs MAY be used internally to determine deterministic numbering, but need not appear in the final IRI.

---

# 6.24 Labels

## Rule L-01 — Preserve original source property/relation names

For a named source property or relation, Direct KG MUST preserve the original source name as `rdfs:label`.

This applies even when IRI disambiguation changes the local name.

Example:

```turtle
:age_Person
    rdfs:label "age" .
```

## Rule L-02 — No label invention for unnamed source elements

An unnamed class MUST NOT receive an invented label.

For fallback-generated relation/property identifiers, the conversation has not established a general rule that the fallback string itself becomes a label.

---

# 6.25 Relation transformation baseline

The relation rules established so far concern ordinary forward relation properties and relation naming.

## Rule R-01 — Ordinary class-to-class relation becomes object property

For an ordinary binary relation whose source and target are OntoUML classes transformed into OWL classes, the generated relation property MUST be an `owl:ObjectProperty`.

It MUST receive:

```text
rdfs:domain = source class
rdfs:range  = target class
```

### Example

```text
Person --employer--> Organization
```

becomes:

```turtle
:employer
    a owl:ObjectProperty ;
    rdfs:domain :Person ;
    rdfs:range :Organization .
```

Detailed relation cardinality behavior has not yet been specified.

---

# 6.26 Relation naming precedence

## Rule R-02 — Default relation naming precedence

With stereotype-derived relation naming enabled, Direct KG MUST determine the forward property base name using:

```text
1. relation name, if usable

2. target-end role name, if usable

3. stereotype-derived semantic naming,
   when a Direct KG mapping exists

4. synthesized <source>_<target>

5. deterministic collision resolution
```

Collision resolution is a final phase, not a semantic naming source.

## Rule R-03 — Stereotype-derived relation naming is enabled by default

Direct KG SHOULD use mapped OntoUML relation stereotypes to generate a semantic property name when:

- the relation itself has no usable name;
- the target-end role has no usable name;
- a Direct KG mapping exists.

This behavior is enabled by default.

The user MAY disable it with:

```text
--no-stereotype-relation-naming
```

When disabled, the effective precedence is:

```text
1. relation name
2. target-end role name
3. synthesized <source>_<target>
4. collision resolution
```

## Rule R-04 — Do not use source-end role as the forward-property fallback

The source-end role name MUST NOT be used as the fallback name for the forward property.

The target-end role is preferred because it describes the value reached from the source classifier.

## Rule R-05 — Do not invent generic semantic prefixes

When no semantic name is available, Direct KG MUST NOT invent expressions such as:

```text
has
isRelatedTo
relatedTo
```

unless they are actually present in the source or defined by a Direct KG stereotype mapping.

---

# 6.27 Synthesized source-target relation names

## Rule R-06 — Lowercase only the first character of synthesized endpoint components

When Direct KG synthesizes a relation name from source and target classifier names:

```text
source component =
    lowerFirst(normalize(source.name))

target component =
    lowerFirst(normalize(target.name))

base =
    <source component>_<target component>
```

`lowerFirst` changes only the first character and preserves the remaining capitalization.

### Examples

```text
Person + Quality
→ person_quality
```

```text
Customer + PostalAddress
→ customer_postalAddress
```

```text
LegalPerson + Organization
→ legalPerson_organization
```

Direct KG MUST NOT lowercase complete classifier names merely for this purpose.

This rule affects synthesized property names only and does not alter class IRI capitalization.

---

# 6.28 Accepted stereotype-derived relation names

## Rule R-07 — Direction-specific stereotype mapping table

When the stereotype-naming step is reached and stereotype-derived naming is enabled, the following mappings are established.

| Stereotype | Semantic orientation | Generated base name |
|---|---|---|
| `bringsAbout` | Event → Situation | `bringsAbout` |
| `bringsAbout` | Situation → Event | `broughtAboutBy` |
| `characterization` | Bearer → Feature | `isCharacterizedBy` |
| `characterization` | Feature → Bearer | `characterizes` |
| `componentOf` | Whole → Component | `hasComponent` |
| `componentOf` | Component → Whole | `componentOf` |
| `creation` | Event → Endurant | `creates` |
| `creation` | Endurant → Event | `wasCreatedIn` |
| `externalDependence` | Extrinsic Mode → Endurant | `externallyDependsOn` |
| `externalDependence` | Endurant → Extrinsic Mode | `isExternalDependencyOf` |
| `historicalDependence` | Dependent → Antecedent | `historicallyDependsOn` |
| `historicalDependence` | Antecedent → Dependent | `isHistoricalDependencyOf` |
| `manifestation` | Aspect/Disposition → Event | `manifestedIn` |
| `manifestation` | Event → Aspect/Disposition | `manifests` |
| `mediation` | Relator → Endurant | `mediates` |
| `mediation` | Endurant → Relator | `isMediatedBy` |
| `memberOf` | Member → Collective | `memberOf` |
| `memberOf` | Collective → Member | `hasMember` |
| `participation` | Participant → Event | `participatesIn` |
| `participation` | Event → Participant | `hasParticipant` |
| `participational` | Part Event → Whole Event | `participationalPartOf` |
| `participational` | Whole Event → Part Event | `hasParticipationalPart` |
| `subCollectionOf` | Subcollection → Collection | `subCollectionOf` |
| `subCollectionOf` | Collection → Subcollection | `hasSubCollection` |
| `subQuantityOf` | Subquantity → Quantity | `subQuantityOf` |
| `subQuantityOf` | Quantity → Subquantity | `hasSubQuantity` |
| `termination` | Endurant → Event | `wasTerminatedIn` |
| `termination` | Event → Endurant | `terminates` |
| `triggers` | Situation → Event | `triggers` |
| `triggers` | Event → Situation | `triggeredBy` |

The selected `characterization` mapping is specifically:

```text
Bearer → Feature
→ isCharacterizedBy
```

not `hasFeature`.

---

# 6.29 Relation stereotypes deliberately without generic names

## Rule R-08 — `comparative` has no generic semantic name

`comparative` MUST NOT receive a fixed stereotype-derived name.

The stereotype alone cannot choose among domain-specific predicates such as:

```text
heavierThan
olderThan
closerThan
moreExpensiveThan
```

If the stereotype-naming step is reached, Direct KG skips semantic mapping and continues to the source-target fallback.

## Rule R-09 — `derivation` has no generic relation-property name for now

`derivation` has no generic Direct KG property-name mapping at this stage.

Its transformation has meta-modeling consequences and must be handled separately.

## Rule R-10 — `instantiation` has no generic relation-property name for now

`instantiation` has no generic property-name mapping at this stage.

Direct KG MUST NOT generate generic names such as:

```text
classifiedBy
classifies
instanceOf
hasInstance
```

merely because the relation is stereotyped `instantiation`.

Higher-order modeling and possible OWL punning are explicitly deferred.

---

# 6.30 Special `material` relation naming

## Rule R-11 — Do not use a fixed generic `material` predicate

`material` MUST NOT receive a fixed name such as:

```text
materiallyRelatedTo
```

## Rule R-12 — Prefer the grounding relator name

When Direct KG reaches the stereotype-derived naming step for an unnamed `material` relation with no usable target-end role, it MUST attempt to identify a grounding `relator` through an OntoUML `derivation`.

If a usable named grounding relator is resolved:

```text
property base =
    lowerFirst(normalize(relator.name))
```

### Examples

```text
Enrollment       → enrollment
Employment       → employment
Marriage         → marriage
Rental Agreement → rental_Agreement
```

The property MUST NOT automatically be prefixed with `has`.

Example:

```text
Student --«material»--> University
```

grounded by:

```text
«relator» Enrollment
```

uses:

```text
:enrollment
```

The generated property still connects:

```text
Student → University
```

and does not point to an `Enrollment` individual.

---

# 6.31 Material relation fallback diagnostics

## Rule R-13 — Successful relator-based material naming

If a usable named grounding relator is resolved:

```text
material relation
+ grounding relator available
→ use relator-derived property name
→ SHOULD emit INFO
→ no WARNING
```

An informational diagnostic SHOULD record the provenance of the name.

Conceptually:

```text
INFO:
Generated property 'enrollment' for unnamed «material» relation 'R123'
from grounding relator 'Enrollment'.
```

## Rule R-14 — No usable grounding relator

If Direct KG reaches the material naming step but cannot resolve a usable grounding relator, it MUST:

1. emit a warning;
2. skip relator-based naming;
3. continue to the normal source-target fallback.

Example:

```text
Student --«material»--> University
```

with no usable grounding relator becomes:

```text
student_university
```

and must emit a warning explaining that the semantic naming mechanism could not be applied.

## Rule R-15 — Coarse initial material diagnostics

The initial specification does not require Direct KG to distinguish among:

```text
no derivation exists
derivation target has no usable name
multiple candidate derivations exist
resolved target is not usable as grounding relator
```

For now, all are treated uniformly as:

```text
usable grounding relator unavailable
→ WARNING
→ source-target fallback
```

More granular diagnostics MAY be added later.

---

# 6.32 Relation naming diagnostics

## Rule R-16 — Successful ordinary stereotype mapping is silent

A successful ordinary stereotype-derived mapping produces:

```text
no WARNING
no INFO
```

## Rule R-17 — Successful material relator naming SHOULD produce INFO only

A successful material relator-derived name SHOULD produce an informational diagnostic and MUST NOT produce a warning merely because the relator-based naming succeeded:

```text
INFO (SHOULD)
no WARNING
```

This later, specific rule refines the earlier generic unnamed-relation warning behavior.

## Rule R-18 — Deliberately unmapped stereotype produces warning when the semantic naming step is reached

If Direct KG reaches stereotype-derived naming for:

```text
comparative
derivation
instantiation
```

and no mapping is defined, Direct KG MUST:

```text
emit WARNING
→ continue to normal fallback
```

The warning indicates that Direct KG had to use a weaker lexical fallback because no semantic mapping is defined.

## Rule R-19 — Target-role and source-target fallback warnings

For an unnamed relation whose naming is resolved through the target-end role fallback, Direct KG MUST emit a non-fatal warning.

For an unnamed relation that reaches the source-target synthesized fallback, Direct KG MUST emit a non-fatal warning.

The later stereotype-specific diagnostic policy takes precedence when semantic stereotype naming succeeds.

## Rule R-20 — No defensive orientation recovery for now

The initial Direct KG specification assumes valid OntoUML relation orientation and sufficient source information for the predefined direction-sensitive stereotype mappings.

Direct KG does not currently need a recovery branch that attempts to repair malformed semantic orientation.

Such recovery MAY be considered in a future version if practical use justifies it.

---

# 6.33 Unnamed relation endpoints

## Rule R-21 — Resolve unnamed endpoint classes before relation fallback naming

If an unnamed relation involves an unnamed source or target class, the class first receives its synthetic identifier according to the unnamed-class rule.

If the relation then requires source-target synthesized naming, the generated endpoint identifiers may be used as naming input.

Example:

```text
unnamed Class id=A1
    -- unnamed relation -->
Car
```

may use:

```text
unnamedClass_A1_car
```

subject to normalization and collision handling.

Separate diagnostics should identify the unnamed class and the unnamed relation when both conditions apply, except where a later stereotype-specific diagnostic rule explicitly replaces the generic relation warning.

---

# 6.34 Diagnostics established so far

The following diagnostic behaviors are established.

| Condition | Diagnostic | Fatal? |
|---|---|---:|
| No `--base-iri` supplied | WARNING; placeholder base IRI used | No |
| Unnamed class fallback in name mode | WARNING | No |
| Unusable source name requiring unnamed fallback | WARNING | No |
| Unnamed element in ID mode | WARNING that source has no name | No |
| Attribute typed by `void` | WARNING; no datatype mapping/range | No |
| Unnamed relation using target-role fallback | WARNING | No |
| Unnamed relation using source-target fallback | WARNING | No |
| Successful ordinary stereotype-derived relation naming | none | No |
| Successful material name from grounding relator | INFO (SHOULD); no warning | No |
| Material semantic naming unavailable | WARNING; lexical fallback | No |
| Deliberately unmapped relation stereotype when semantic naming step is reached | WARNING; lexical fallback | No |
| Unexpected collision after injective ID escaping | exceptional condition; behavior beyond "do not silently merge" is not yet specified | TBD |

---

# 7. Explicitly rejected or superseded alternatives

This section records alternatives that the discussion clearly rejected or replaced.

## 7.1 Unconditional class-to-OWL-class mapping

### Rejected

```text
Every OntoUML Class → owl:Class
```

### Replaced by

Domain classes and custom datatypes become OWL classes, while supported primitive datatype elements and `void` do not.

---

## 7.2 Mandatory `only` restrictions

### Rejected

Always generate:

```text
C ⊑ X only Y
```

for typed attributes.

### Reason

The desired default is a lighter, more general-purpose KG.

### Replaced by

Optional value-type restriction generation, disabled by default.

---

## 7.3 `owl:equivalentClass` for attribute semantics

### Rejected

Treating the attribute restrictions as an equivalence definition of the owning class.

### Replaced by

Necessary conditions expressed through `rdfs:subClassOf` restrictions.

---

## 7.4 Guessing a datatype for `propertyType = null`

### Rejected

Mapping unknown type to:

```text
rdfs:Literal
xsd:string
```

or another fallback datatype.

### Replaced by

Datatype property with domain and cardinality when present, but no range.

---

## 7.5 Mapping `void` to an RDF/OWL/XSD construct

### Rejected

Mappings such as:

```text
rdfs:Literal
owl:Nothing
owl:bottomDataProperty
xsd:anySimpleType
xsd:anyAtomicType
```

or a locally invented empty datatype.

### Replaced by

Recognized but unsupported `void`, warning, and omission of datatype range semantics.

---

## 7.6 Guessing XSD semantics for custom datatype names

### Rejected

For example:

```text
TimeInterval → xsd:duration
```

based only on lexical similarity.

### Replaced by

Custom datatypes are reified as OWL classes unless an explicit primitive/alias registry mapping applies.

---

## 7.7 Flattening custom datatype structure

### Rejected

Moving internal custom-datatype properties directly onto the owning domain class.

### Replaced by

Reified value-class structure connected through object properties.

---

## 7.8 Same-name property merging

### Rejected

Automatically merging distinct source properties because they share a name.

### Replaced by

Distinct source properties/relations always receive distinct OWL property IRIs.

---

## 7.9 Union-based range repair caused by property merging

### Rejected

Using `ObjectUnionOf(...)`, `DataUnionOf(...)`, or similar constructs merely to reconcile ranges of source properties that should have remained distinct.

### Replaced by

Distinct property identity with owner/source disambiguation and collision handling.

---

## 7.10 Source-ID suffix in final property collision names

### Superseded

The earlier idea:

```text
code_Person_<short-source-id>
```

for unresolved same-owner collisions.

### Replaced by

All members of the collision set receive deterministic numeric suffixes:

```text
code_Person_1
code_Person_2
```

Source IDs may still determine stable ordering internally.

---

## 7.11 Generic semantic relation prefixes for unnamed relations

### Rejected

Inventing:

```text
hasCar
relatedToCar
isAssociatedWithCar
```

when no such semantics is available.

### Replaced by

Target role, mapped stereotype semantics, or lexical source-target synthesis.

---

## 7.12 Source-end role as forward-property fallback

### Rejected

Using the source-end role as the fallback name for the forward property.

### Replaced by

Target-end role as the role-name fallback.

---

## 7.13 `hasFeature` for `characterization`

### Rejected

```text
Bearer → Feature
→ hasFeature
```

### Replaced by

```text
Bearer → Feature
→ isCharacterizedBy
```

---

## 7.14 Generic `materiallyRelatedTo`

### Rejected

A fixed generic predicate for `material`.

### Replaced by

Grounding-relator-derived naming when possible, otherwise source-target fallback.

---

## 7.15 `has<RelatorName>` for material relation name

### Rejected

For example:

```text
Enrollment → hasEnrollment
```

### Reason

The generated material property connects the material-relation endpoints, not the subject to an Enrollment individual.

### Replaced by

```text
Enrollment → enrollment
```

---

## 7.16 Fuzzy primitive datatype matching

### Rejected

- edit-distance correction;
- spelling correction;
- synonym detection;
- translation;
- automatic abbreviation expansion;
- stemming;
- plural normalization.

### Replaced by

Lexical normalization plus exact registry lookup and explicitly registered aliases only.

---

## 7.17 Stereotype in unnamed-class synthetic IRI

### Rejected

```text
unnamedClass_Kind_<id>
```

### Replaced by

```text
unnamedClass_<escaped-id>
```

to preserve identity if the stereotype changes.

---

# 8. Open questions and unresolved issues

The following matters remain unresolved and must not be treated as settled requirements.

## 8.1 Missing cardinality

What does:

```text
cardinality = null
```

mean for Direct KG?

Possible behaviors have not been decided.

In particular, Direct KG has not decided whether to:

- emit no cardinality restriction; or
- interpret a tool/default multiplicity such as `[1]`.

No assumption should be made.

## 8.2 Configuration and enabled-mode strength for `owl:allValuesFrom`

The default behavior is settled: the value-type restriction mode is optional and disabled by default, and one option must control it for both primitive-valued and custom-datatype-valued attributes.

Two details remain unresolved:

- the exact configuration option name;
- whether enabling the option makes generation mandatory/deterministic whenever the value type is resolvable, or merely permits generation. The deterministic/MUST behavior was recommended but not explicitly accepted.

## 8.3 Relation cardinalities

The discussion states that relation multiplicities should be preserved, but no complete normative mapping from OntoUML relation-end cardinalities to OWL restrictions has yet been defined.

Questions include:

- which endpoint multiplicity constrains which class;
- how lower/upper/exact cardinalities are generated;
- how this interacts with relation orientation and inverse directions.

## 8.4 `owl:allValuesFrom` for ordinary relations

The optional `only` behavior is established for typed attributes.

It has not yet been decided whether the same option should create:

```text
Source ⊑ relation only Target
```

for ordinary OntoUML relations.

## 8.5 Relation inverse properties

The 2013 transformation created direct and inverse OWL properties.

Direct KG has not yet decided whether inverse properties should be generated at all.

## 8.6 Relation hierarchy

Current rules cover class-to-class generalization.

Transformation of generalizations between relations has not been decided.

## 8.7 Generalization sets

No current Direct KG rule has yet been established for:

- `isDisjoint`;
- `isComplete`;
- covering/complete partitions;
- categorizer semantics.

This remains a major open transformation area.

## 8.8 Disjointness OWL serialization

The required class-disjointness semantics are settled.

The exact RDF/OWL representation is not.

Possible encodings such as:

- pairwise `owl:disjointWith`;
- `owl:AllDisjointClasses`;

remain implementation/specification choices to settle.

## 8.9 Enumerations and literals

The `enumeration` stereotype participates in cross-group disjointness, but the transformation of enumeration classes and their literals has not yet been designed.

## 8.10 `abstract` stereotype semantics

`abstract` participates in cross-group disjointness, but no additional transformation semantics have been specified for it.

## 8.11 OntoUML class metaproperties

No Direct KG rules have yet been established for source features such as:

- `isAbstract`;
- `isDerived`;
- `restrictedTo`;
- `isPowertype`;
- `order`.

## 8.12 Property metaproperties

No transformation rules have yet been established for:

- `subsettedProperties`;
- `redefinedProperties`;
- `aggregationKind`;
- `isOrdered`;
- `isReadOnly`;
- property stereotypes.

## 8.13 Semantic transformation of relation stereotypes

The current relation-stereotype rules primarily establish **property naming**.

They do not yet define all semantic OWL consequences of stereotypes such as:

- `componentOf`;
- `memberOf`;
- `subCollectionOf`;
- `subQuantityOf`;
- `mediation`;
- `characterization`;
- `participation`;
- `creation`;
- `termination`;
- etc.

For example, Direct KG has not yet decided whether to generate:

- transitivity axioms;
- property chains;
- inverse-property axioms;
- SWRL rules;
- other UFO-derived constraints.

## 8.14 `material` relation semantics

The current `material` rules specify naming and diagnostics.

The actual semantic transformation of material relations and their derivation from relators has not yet been defined.

In particular, the 2013 SWRL-style derivation behavior has not yet been adopted or rejected for Direct KG.

## 8.15 `derivation` semantics

`derivation` has deliberately no generic relation-property name for now.

Its actual transformation is still open.

## 8.16 `instantiation`, higher-order modeling, and punning

The treatment of `instantiation` is explicitly deferred.

Questions include:

- whether and how higher-order OntoUML `type` classes map to OWL;
- whether OWL punning is appropriate;
- how instantiation relations should be represented.

## 8.17 `comparative` semantics

`comparative` has no generic stereotype-derived name.

No generic semantic transformation beyond ordinary relation handling has been established.

## 8.18 N-ary relations

The current relation rules are effectively binary/source-target oriented.

The current OntoUML Schema supports n-ary relations, but their Direct KG transformation has not yet been designed.

## 8.19 Relation endpoints that are not ordinary classes

Special cases such as derivation relations that involve another relation/classifier require separate treatment.

No general rule has yet been established for arbitrary non-class relation endpoints.

## 8.20 Instances / individuals

No general Direct KG transformation rules have yet been established for OntoUML instances or individuals.

## 8.21 Packages

No transformation rule has been established for OntoUML packages.

Absence of a rule does not mean packages are intentionally omitted; the topic has not yet been decided.

## 8.22 Project metadata and annotations

No complete transformation policy has been established for:

- project metadata;
- descriptions;
- alternative names;
- editorial notes;
- creators/contributors;
- license;
- project namespace;
- source references;
- bibliographic citations;
- keywords;
- other schema metadata.

## 8.23 Notes, anchors, diagrams, views, and shapes

No Direct KG rules have yet been established for OntoUML concrete syntax or note/anchor constructs.

The domain-oriented design suggests that much concrete syntax may ultimately be omitted, but omission has not yet been adopted as a normative rule for each construct.

## 8.24 Multilingual `name` values

The current OntoUML JSON Schema represents names as language strings rather than necessarily as a single scalar string.

Direct KG has not yet decided:

- which language value determines the name-based IRI when multiple names are present;
- how multiple language-tagged labels are emitted;
- how primitive datatype recognition behaves when a datatype has multiple lexical names/languages;
- how target-end role names with multiple language forms affect relation naming.

## 8.25 Labeling beyond named source properties/relations

Named source properties/relations MUST preserve their original source name as `rdfs:label`.

For other named generated resources, the IRI-generation decision contains two formulations that were not explicitly reconciled: one statement says that the source name MUST be preserved as `rdfs:label` in name-based mode, while the later general labels section says Direct KG SHOULD generate `rdfs:label` whenever a usable source name exists. The normative strength for named classes and other non-property resources therefore remains unresolved in this handoff rather than being silently promoted to either MUST or SHOULD.

No general rule has yet been established for whether an unnamed relation whose IRI was generated from:

- a target-end role;
- a stereotype-derived semantic mapping;
- a grounding relator name;
- a source-target synthetic name;

should receive a corresponding generated `rdfs:label`.

## 8.26 Owner/source qualification when owner/source class is unnamed

The generic unnamed endpoint rule covers synthesized source-target relation names.

A complete explicit rule for owner/source qualification of same-name **attributes/properties** when the owner/source class is unnamed has not yet been written.

## 8.27 Primitive registry completeness

The controlled primitive registry mechanism is settled, and several canonical mappings are established.

The registry has not been declared a permanently closed exhaustive set.

Future discussion may add explicitly supported XSD datatype names and semantic aliases.

## 8.28 Alias registry contents

The mechanism is established, but the actual accepted semantic alias set has not yet been fixed.

The examples:

```text
bool
str
wholeNumber
integer32
```

illustrate the mechanism and are not automatically enabled merely by appearing in the discussion.

## 8.29 Invalid base IRIs

Direct KG has rules for appending `#` when the base lacks `#` or `/`.

Behavior for a syntactically invalid or otherwise unusable `--base-iri` value has not yet been specified.

## 8.30 Output serialization formats

Turtle is used in examples, but the supported RDF serialization formats have not yet been decided.

## 8.31 Source-ID collision exceptional behavior

The escaping algorithm is intended to be injective.

If an implementation nevertheless detects an ID-based IRI collision, it must not silently merge elements, but the exact error/warning/fallback behavior is not yet specified.

## 8.32 Malformed OntoUML input

Except for the specific warnings already defined, Direct KG's general policy for invalid, incomplete, or semantically inconsistent input has not yet been designed.

The initial relation orientation rule explicitly defers defensive semantic-orientation recovery.

## 8.33 Source provenance / source IDs in name-based output

The discussion has not yet decided whether Direct KG should emit provenance annotations linking generated resources back to OntoUML source IDs when using name-based IRIs.

---

# 9. Working recommendations not yet accepted as normative requirements

The following recommendations were proposed during the discussion but were not explicitly made normative.

## 9.1 Pairwise disjointness encoding

A pairwise `owl:disjointWith` representation was suggested as a straightforward encoding for the broad cross-group disjointness rule because a single `owl:AllDisjointClasses` over all grouped classes would incorrectly introduce intra-group disjointness.

The semantic requirement is settled; the concrete OWL encoding remains open.

## 9.2 Cycle-safe custom-datatype processing

Because custom datatype transformation is recursive, an implementation should process source elements in a way that terminates even if custom datatype references are cyclic.

This is an implementation-safety recommendation, not a newly established semantic rule.

## 9.3 Deterministic behavior when optional value-type restrictions are enabled

A recommendation was proposed that, once the optional `owl:allValuesFrom` mode is enabled, Direct KG should generate the corresponding restriction deterministically whenever the value type is resolvable. This stronger behavior was not explicitly accepted. The established rule only makes `owl:allValuesFrom` generation optional and disabled by default; the exact normative strength of the enabled mode remains to be settled.

---

# 10. Dependencies and reference material

The specification discussion relies principally on the following sources.

## 10.1 2013 paper

**An Automated Transformation from OntoUML to OWL and SWRL** (2013).

The paper provided the historical transformation baseline, especially for:

- class transformation;
- class hierarchy;
- disjointness;
- attribute/datatype transformation;
- relation handling;
- material relation derivation;
- part-whole semantics.

Direct KG intentionally reconsiders those rules rather than copying them automatically.

## 10.2 Current OntoUML metamodel

Repository:

https://github.com/OntoUML/ontouml-metamodel

The preceding study inspected the authoritative Visual Paradigm metamodel artifact and its exported XML, including current class stereotypes, relation stereotypes, abstract syntax, and concrete syntax.

## 10.3 Current OntoUML JSON Schema

Repository:

https://github.com/ontouml/ontouml-schema

The preceding study inspected the current schema in depth, including:

- `Class`;
- `Property`;
- `Relation`;
- `Generalization`;
- `GeneralizationSet`;
- project structure;
- IDs and references;
- abstract and concrete syntax.

At the time of study, the schema identified itself as version `1.0.2`.

## 10.4 Supporting OntoUML model examples

Examples from the OntoUML model catalog were consulted during earlier investigation of actual JSON exports and datatype usage.

Repository:

https://github.com/OntoUML/ontouml-models

These examples are supporting evidence, not the normative Direct KG specification.

---

# 11. Current specification coverage

| Topic | Status | Current state |
|---|---|---|
| Basic class → OWL class | **Decided** | Domain/custom datatype classes become `owl:Class`; supported primitive/void exceptions established |
| Class generalization | **Decided** | Class-to-class generalization → `rdfs:subClassOf` |
| Ultimate-sortal disjointness | **Decided** | Pairwise semantic disjointness across directly stereotyped ultimate sortals |
| Broad stereotype-group disjointness | **Decided** | Inter-group disjointness among four established groups |
| OWL syntax for disjointness | **Open** | Exact encoding not normative |
| Class attributes | **Decided / partial** | Property kind, domain, range, cardinality, null/void behavior established |
| Missing attribute cardinality | **Open** | `cardinality = null` unresolved |
| Optional local value restrictions | **Decided / partial / open** | Default off and single-option scope established; exact option name and enabled-mode normative strength unresolved |
| Primitive datatypes | **Decided / extensible** | Registry mechanism and core mappings established; registry may grow |
| Primitive datatype normalization | **Decided** | Aggressive lexical normalization + exact registry lookup |
| Primitive semantic aliases | **Partially decided** | Explicit-only mechanism established; alias contents not fixed |
| `void` | **Decided** | Recognized unsupported datatype, warning, no range |
| Custom datatypes | **Decided** | Reified OWL classes, object-property references, recursive structure |
| Property domain | **Decided** | Mandatory for every generated OWL property |
| Property range | **Decided** | Mandatory when target/type is resolvable and supported |
| Property identity | **Decided** | Distinct source property/relation → distinct OWL property IRI |
| Name-based IRI strategy | **Decided** | Default |
| ID-based IRI strategy | **Decided** | Optional |
| Base IRI | **Decided** | Configurable; placeholder default + warning |
| Name normalization | **Decided** | Deterministic ASCII-safe lexical normalization |
| Source ID escaping | **Decided** | Exact reversible `_xHH` byte escaping rule |
| IRI collisions | **Decided** | All collision members get deterministic `_1..._N` |
| Unnamed classes | **Decided** | Synthetic `unnamedClass_<escaped-id>` + warning in name mode |
| Labels | **Partially decided / open** | Named properties/relations MUST preserve source name; normative strength for other named resources and labels for fallback-generated unnamed relations remain unresolved |
| Basic ordinary binary relation property | **Decided** | `owl:ObjectProperty` + source domain + target range |
| Relation naming precedence | **Decided** | name → target role → stereotype mapping → source-target → collision |
| Stereotype-derived relation names | **Decided** | Direction-specific mapping table established |
| Material relation naming/diagnostics | **Decided** | grounding relator when usable; INFO on success; warning + lexical fallback otherwise |
| Relation cardinalities | **Open** | Detailed OWL mapping not specified |
| Inverse properties | **Open** | Historical 2013 behavior was noted, but Direct KG has no accepted rule |
| Relation generalization | **Open** | Current schema capability was identified; no Direct KG rule yet |
| Generalization sets | **Open** | Identified as a major unresolved transformation area |
| Relation semantic axioms beyond naming/domain/range | **Partially decided / open** | Most UFO-specific semantics unresolved |
| `derivation` transformation | **Open** | No generic name; semantics deferred |
| `instantiation` / higher-order / punning | **Open** | Explicitly deferred |
| `comparative` generic semantics | **Open** | No generic name; domain-specific |
| N-ary relations | **Open** | Current schema support was identified; transformation explicitly deferred |
| Enumerations / literals | **Partially discussed / open** | `enumeration` participates in a disjointness group, but its actual transformation/literals are unspecified |
| `isAbstract`, `isDerived`, `restrictedTo`, `isPowertype`, `order` | **Not yet discussed** | No rule |
| Property subsetting/redefinition/ordering/read-only/aggregation | **Not yet discussed** | No rule |
| Packages | **Not yet discussed** | No rule |
| Notes / anchors | **Not yet discussed** | No rule |
| Diagrams / views / shapes | **Not yet discussed** | No rule |
| Project metadata | **Not yet discussed** | No rule |
| Instances / individuals | **Not yet discussed** | No rule |
| Multilingual naming/labels | **Open** | Language-selection behavior unresolved |
| Output RDF serialization(s) | **Open** | Turtle used only in examples |
| General invalid-input policy | **Open** | Only specific warning/error cases defined |

---

# 12. Supersession and decision precedence notes

When resuming the specification, the later decisions in this handoff take precedence over earlier superseded formulations.

Important precedence points:

1. **Class mapping:** the unconditional `Class → owl:Class` rule is revoked; datatype classification occurs first.
2. **Value-type restrictions:** `only Y` is optional and disabled by default, not mandatory.
3. **Primitive detection:** fixed-name VP detection was generalized into lexical normalization + controlled registry resolution.
4. **Custom datatypes:** previously unresolved non-primitive datatype classes are now explicitly supported as reified value classes.
5. **Property collision fallback:** stable source-ID suffixes in property IRIs were superseded by deterministic numeric suffixes applied to every member of a collision set.
6. **Relation naming:** the old `name → target role → source-target` precedence was extended to include stereotype-derived naming before source-target synthesis.
7. **Unnamed relation diagnostics:** later stereotype-specific diagnostic rules refine the earlier generic warning rule:
   - successful ordinary stereotype mapping → no diagnostic;
   - successful material grounding-relator naming → INFO only;
   - semantic mapping failure → WARNING + weaker fallback.
8. **Source ID normalization:** generic "technical escaping if necessary" was replaced by the exact `_xHH` UTF-8-byte escaping algorithm.

---

# 13. Resume instructions

A future conversation should use this handoff as the current Direct KG specification baseline.

The future assistant must:

1. treat the **Established transformation rules** as the current accepted specification unless the user explicitly revises them;
2. preserve distinctions between OntoUML source semantics, transformation behavior, RDF/OWL semantics, and serialization/implementation details;
3. treat all items in **Open questions and unresolved issues** as unresolved;
4. keep **Working recommendations** non-normative unless the user explicitly accepts them;
5. not promote examples, suggestions, or historical 2013 behavior into Direct KG requirements without approval;
6. not infer that an OntoUML construct is intentionally omitted merely because no rule has yet been defined for it;
7. continue the specification incrementally rather than regenerating the entire design from scratch after each new decision;
8. record later decisions in a way that clearly notes when they refine, supersede, or conflict with earlier rules;
9. preserve the project's core objective: a pragmatic, simplified, domain-oriented Knowledge Graph rather than a structural RDF serialization of OntoUML.

This document should be updated or regenerated after substantial new specification decisions so that it remains a reliable offline handoff.
