"""Classifier-owned attributes and their explicit property-inclusion references."""

from collections import defaultdict
from dataclasses import dataclass

from rdflib import Graph, Literal, URIRef
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
        if owner is None or owner.data["type"] != "Class":
            raise NotImplementedError("Association-end property mapping belongs to BI-W4")
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


def attribute_candidates(attributes: tuple[Attribute, ...], strategy: str) -> dict[str, str]:
    """Qualify colliding source-backed attributes before final shared collisions."""
    candidates = {}
    groups = defaultdict(list)
    for attribute in attributes:
        data = attribute.source.data
        selected = naming_text(data.get("name")) if strategy == "name" else None
        candidate = normalize_name(selected) if selected is not None else escape_id(data["id"])
        candidates[data["id"]] = candidate
        groups[candidate].append(attribute)
    if strategy == "name":
        for candidate, group in groups.items():
            if len(group) > 1:
                for attribute in group:
                    owner = attribute.owner.data
                    candidates[attribute.source.data["id"]] = candidate + "_" + class_name_candidate(owner["id"], owner.get("name"))
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


def emit_attribute_references(graph: Graph, index: SourceIndex, attributes: tuple[Attribute, ...],
                               resources: dict[str, URIRef], diagnostics: DiagnosticCollector, policy: str) -> None:
    generated = {attribute.source.data["id"] for attribute in attributes}
    for attribute in attributes:
        element = attribute.source
        for field in ("subsettedProperties", "redefinedProperties"):
            references = element.data.get(field)
            if references is None:
                continue
            if not isinstance(references, list):
                input_error(diagnostics, policy, "INVALID_PROPERTY_REFERENCES",
                            f"Attribute {field} is not a reference collection.", (element.location,),
                            "Affected reference collection omitted; independent attribute mappings retained.")
                continue
            for reference in references:
                try:
                    target = index.resolve(reference)
                    if target.data["type"] != "Property":
                        raise KeyError("Reference does not identify a UML Property")
                    owner = index.declarations.get(target.owner)
                    if owner is not None and owner.data["type"] == "Relation":
                        raise NotImplementedError("Association-end reference expressions belong to BI-W4")
                    if target.data["id"] not in generated:
                        raise KeyError("Required underlying attribute transformation did not generate a property")
                except KeyError as exc:
                    input_error(diagnostics, policy, "UNRESOLVED_PROPERTY_REFERENCE",
                                f"Attribute {field} reference {reference!r} cannot supply a property expression: {exc}.",
                                (element.location,), "Affected inclusion omitted; other explicit references and attribute mappings retained.")
                    continue
                graph.add((resources[element.data["id"]], RDFS.subPropertyOf, resources[target.data["id"]]))
