"""Classifier-owned attributes and their explicit property-inclusion references."""

from collections import defaultdict
from dataclasses import dataclass

from rdflib import BNode, Graph, Literal, URIRef
from rdflib.namespace import OWL, RDF, RDFS

from .annotations import TextAnnotations
from .datatypes import PRIMITIVES, datatype_key
from .diagnostics import DiagnosticCollector
from .identity import class_name_candidate, escape_id, missing_name, naming_text, normalize_name
from .multiplicity import emit_attribute_multiplicity, parse_attribute_multiplicity
from .source import SourceElement, SourceIndex, input_error


@dataclass(frozen=True)
class Attribute:
    source: SourceElement
    owner: SourceElement
    kind: URIRef
    range_type: SourceElement | URIRef | None = None
    void_source: SourceElement | None = None


def collect_attributes(index: SourceIndex, classes: tuple[SourceElement, ...],
                       diagnostics: DiagnosticCollector, policy: str) -> tuple[Attribute, ...]:
    """Resolve source types before allocating property identity; never guess kinds."""
    generated_classes = {element.data["id"] for element in classes}
    attributes = []
    for element in index.elements:
        data = element.data
        if data["type"] != "Property":
            continue
        owner = index.declarations.get(element.owner)
        if owner is not None and owner.data["type"] == "Relation":
            continue
        if owner is None or owner.data["type"] != "Class":
            raise NotImplementedError("Attribute ownership cannot be resolved under the decided baseline")
        if element.owner not in generated_classes:
            raise NotImplementedError("Attribute ownership without a generated local class is outside the decided baseline")
        identifier = data.get("id")
        if not isinstance(identifier, str) or not identifier:
            raise NotImplementedError("Invalid attribute-ID recovery requires the deferred Architect decision")
        try:
            identifier.encode("utf-8")
        except UnicodeError as exc:
            raise NotImplementedError("Invalid source-ID recovery requires the deferred Architect decision") from exc
        for flag in ("isDerived", "isReadOnly", "isOrdered"):
            if data.get(flag) is not None and type(data[flag]) is not bool:
                raise NotImplementedError("Malformed attribute-flag recovery remains outside the decided baseline")
        if "propertyType" not in data:
            raise NotImplementedError("Absent attribute propertyType carrier recovery remains outside the decided baseline")
        reference = data["propertyType"]
        if reference is None:
            attributes.append(Attribute(element, owner, OWL.DatatypeProperty))
            continue
        try:
            value_type = index.resolve(reference)
            if value_type.data["type"] != "Class":
                raise KeyError("Attribute value type does not reference a Class")
        except KeyError as exc:
            input_error(diagnostics, policy, "UNRESOLVED_ATTRIBUTE_TYPE",
                        f"Attribute value-type reference {reference!r} cannot be resolved: {exc}.",
                        (element.location, owner.location),
                        "Affected attribute omitted because its property kind cannot be determined; independent mappings retained.")
            continue
        stereotype = value_type.data.get("stereotype")
        if stereotype == "datatype":
            key = datatype_key(value_type.data.get("name"))
            if key in PRIMITIVES:
                attributes.append(Attribute(element, owner, OWL.DatatypeProperty, PRIMITIVES[key]))
                continue
            if key == "void":
                attributes.append(Attribute(element, owner, OWL.DatatypeProperty, void_source=value_type))
                continue
        elif stereotype != "enumeration":
            raise NotImplementedError("Attribute value kinds outside datatype/enumeration mappings remain unspecified")
        if value_type.data["id"] not in generated_classes:
            raise NotImplementedError("Attribute range without a generated local class remains outside the decided baseline")
        attributes.append(Attribute(element, owner, OWL.ObjectProperty, value_type))
    return tuple(attributes)


def property_candidates(attributes: tuple[Attribute, ...], strategy: str,
                        additional: dict[str, tuple[str, SourceElement]] | None = None,
                        claimed_names: set[str] | None = None) -> dict[str, str]:
    """Qualify attributes and ordinary primaries together, before shared collisions."""
    entries = dict(additional or {})
    groups = defaultdict(list)
    for attribute in attributes:
        data = attribute.source.data
        selected = naming_text(data.get("name")) if strategy == "name" else None
        candidate = normalize_name(selected) if selected is not None else escape_id(data["id"])
        entries[data["id"]] = (candidate, attribute.owner)
    candidates = {identifier: candidate for identifier, (candidate, _) in entries.items()}
    if claimed_names is not None:
        claimed_names.update(candidates.values())
    for identifier, (candidate, owner) in entries.items():
        groups[candidate].append((identifier, owner))
    if strategy == "name":
        for candidate, group in groups.items():
            if len(group) > 1:
                for identifier, source in group:
                    owner = source.data
                    candidates[identifier] = candidate + "_" + class_name_candidate(owner["id"], owner.get("name"))
    if claimed_names is not None:
        claimed_names.update(candidates.values())
    return candidates


def emit_attributes(graph: Graph, attributes: tuple[Attribute, ...], resources: dict[str, URIRef],
                     strategy: str, text: TextAnnotations, diagnostics: DiagnosticCollector, policy: str) -> None:
    for attribute in attributes:
        element, owner = attribute.source, attribute.owner
        data = element.data
        subject, domain = resources[data["id"]], resources[owner.data["id"]]
        graph.add((subject, RDF.type, attribute.kind))
        graph.add((subject, RDFS.domain, domain))
        value_type = attribute.range_type
        if isinstance(value_type, SourceElement):
            graph.add((subject, RDFS.range, resources[value_type.data["id"]]))
        elif value_type is not None:
            graph.add((subject, RDFS.range, value_type))
        text.describe(graph, subject, data)
        if strategy == "name" and naming_text(data.get("name")) is None:
            diagnostics.add("WARNING", "GENERIC_ID_FALLBACK",
                            "Attribute has no usable name-based candidate; its own source ID supplies the IRI.",
                            "Attribute retained with its generated IRI.", (element.location,), str(subject))
        elif strategy == "id" and missing_name(data.get("name")):
            diagnostics.add("INFO", "MISSING_NAME", "Attribute has missing descriptive name text.",
                            "Attribute retained using its ordinary own-ID IRI.", (element.location,), str(subject))
        if attribute.void_source is not None:
            diagnostics.add("WARNING", "VOID_DATATYPE",
                            "Attribute explicitly uses recognized unsupported Visual Paradigm void; no mapping or range is supplied.",
                            "Attribute and domain retained without a range or local value-type restriction.",
                            (element.location, owner.location, attribute.void_source.location))
        derived = data.get("isDerived")
        if type(derived) is bool:
            graph.add((subject, RDFS.comment, Literal(f"OntoUML attribute isDerived: {str(derived).lower()}.", lang="en")))
            if derived:
                diagnostics.add("INFO", "DERIVED_STATUS_ANNOTATION",
                                "isDerived=true is preserved as an annotation; the annotation itself supplies no derivation rule.",
                                "Attribute and annotation retained.", (element.location,))
        if data.get("isReadOnly") is True:
            graph.add((subject, RDFS.comment, Literal("OntoUML source metadata: this attribute is read-only.", lang="en")))
        if data.get("isOrdered") is True:
            graph.add((subject, RDFS.comment, Literal("OntoUML source metadata: this attribute is ordered.", lang="en")))
            diagnostics.add("INFO", "ORDERING_ANNOTATION",
                            "Ordering is preserved as an annotation, but value order is not represented by the generated property mapping.",
                            "Attribute and annotation retained without sequence structures or additional logical semantics.",
                            (element.location,))
        bounds = parse_attribute_multiplicity(element, diagnostics, policy)
        emit_attribute_multiplicity(graph, domain, subject, bounds)


class PropertyExpressions:
    """Resolve actual generated properties, creating anonymous inverses only on demand."""

    def __init__(self, graph: Graph, attributes: tuple[Attribute, ...],
                 resources: dict[str, URIRef], ends: dict[str, tuple[str, bool]],
                 inverses: dict[str, URIRef], omitted_relations: set[str]) -> None:
        self.graph, self.resources = graph, resources
        self.attributes = {attribute.source.data["id"] for attribute in attributes}
        self.ends, self.inverses, self.omitted = ends, inverses, omitted_relations
        self.anonymous: dict[str, BNode] = {}

    def resolve(self, element: SourceElement, *, emit_inverse: bool = True) -> URIRef | BNode | None:
        identifier = element.data["id"]
        if identifier in self.attributes:
            return self.resources[identifier]
        if element.owner in self.omitted:
            return None
        if identifier not in self.ends:
            raise KeyError("Required underlying property transformation did not generate an expression")
        primary_id, reverse = self.ends[identifier]
        primary = self.resources[primary_id]
        if not reverse:
            return primary
        if identifier in self.inverses:
            return self.inverses[identifier]
        if primary_id not in self.anonymous:
            self.anonymous[primary_id] = BNode()
        if emit_inverse:
            self.graph.add((self.anonymous[primary_id], OWL.inverseOf, primary))
        return self.anonymous[primary_id]


def emit_property_references(graph: Graph, index: SourceIndex, expressions: PropertyExpressions,
                              diagnostics: DiagnosticCollector, policy: str) -> None:
    for element in index.elements:
        if element.data["type"] != "Property":
            continue
        if all(element.data.get(field) is None or element.data[field] == []
               for field in ("subsettedProperties", "redefinedProperties")):
            continue
        try:
            subject = expressions.resolve(element, emit_inverse=False)
        except KeyError:
            # Its underlying transformation already reported the failure.
            continue
        if subject is None:
            continue
        for field in ("subsettedProperties", "redefinedProperties"):
            references = element.data.get(field)
            if references is None:
                continue
            if not isinstance(references, list):
                input_error(diagnostics, policy, "INVALID_PROPERTY_REFERENCES",
                            f"Property {field} is not a reference collection.", (element.location,),
                            "Affected reference collection omitted; independent property mappings retained.")
                continue
            for reference in references:
                try:
                    target = index.resolve(reference)
                    if target.data["type"] != "Property":
                        raise KeyError("Reference does not identify a UML Property")
                    superproperty = expressions.resolve(target, emit_inverse=False)
                except KeyError as exc:
                    input_error(diagnostics, policy, "UNRESOLVED_PROPERTY_REFERENCE",
                                f"Property {field} reference {reference!r} cannot supply a property expression: {exc}.",
                                (element.location,), "Affected inclusion omitted; other explicit references and property mappings retained.")
                    continue
                if superproperty is not None:
                    expressions.resolve(element)
                    expressions.resolve(target)
                    graph.add((subject, RDFS.subPropertyOf, superproperty))
