"""Explicit enumeration values, closure and inequality (DK-CLS-10–11)."""

from dataclasses import dataclass

from rdflib import BNode, Graph, URIRef
from rdflib.collection import Collection
from rdflib.namespace import OWL, RDF

from .annotations import TextAnnotations
from .diagnostics import DiagnosticCollector, SourceLocation
from .identity import missing_name, naming_text
from .source import SourceElement, input_error


@dataclass(frozen=True)
class Enumeration:
    source: SourceElement
    values: tuple[SourceElement, ...]
    complete: bool


def collect_enumerations(classes: tuple[SourceElement, ...], diagnostics: DiagnosticCollector,
                         policy: str) -> tuple[Enumeration, ...]:
    """Recover only supplied Literal values; never reinterpret Properties."""
    enumerations = []
    for element in classes:
        if element.data.get("stereotype") != "enumeration":
            continue
        raw = element.data.get("literals")
        if raw is None or raw == []:
            clarification = " Owned properties are not interpreted as enumeration values." if element.data.get("properties") else ""
            diagnostics.add("WARNING", "ENUMERATION_VALUES_UNAVAILABLE",
                            "No enumeration values were available; enumeration closure is omitted." + clarification,
                            "Enumeration class and independently applicable mappings are retained.", (element.location,))
            enumerations.append(Enumeration(element, (), False))
            continue
        if not isinstance(raw, list):
            input_error(diagnostics, policy, "MALFORMED_ENUMERATION_VALUES",
                        "Enumeration literals must be a collection of source Literal elements.",
                        (element.location,), "Malformed value list omitted; enumeration class retained without closure.")
            enumerations.append(Enumeration(element, (), False))
            continue
        values = []
        complete = True
        for number, value in enumerate(raw):
            path = f"{element.path}.literals[{number}]"
            identifier = value.get("id") if isinstance(value, dict) else None
            location = SourceLocation(path, identifier if isinstance(identifier, str) else None,
                                      value.get("type") if isinstance(value, dict) else None)
            valid = isinstance(value, dict) and value.get("type") == "Literal" and isinstance(identifier, str) and bool(identifier)
            if valid:
                try:
                    identifier.encode("utf-8")
                except UnicodeError:
                    valid = False
            if not valid:
                input_error(diagnostics, policy, "UNTRANSFORMABLE_ENUMERATION_VALUE",
                            "Supplied enumeration value is not a Literal with a usable source ID.", (location, element.location),
                            "Affected value omitted; successful values and membership retained without enumeration closure.")
                complete = False
                continue
            values.append(SourceElement(value, path, element.data["id"]))
        enumerations.append(Enumeration(element, tuple(values), complete))
    return tuple(enumerations)


def emit_enumerations(graph: Graph, enumerations: tuple[Enumeration, ...], resources: dict[str, URIRef],
                      strategy: str, text: TextAnnotations, diagnostics: DiagnosticCollector) -> None:
    """Use allocated real resources for membership, nonempty closure and difference."""
    for enumeration in enumerations:
        subject = resources[enumeration.source.data["id"]]
        values = []
        for element in sorted(enumeration.values, key=lambda value: value.data["id"]):
            target = resources[element.data["id"]]
            values.append(target)
            graph.add((target, RDF.type, OWL.NamedIndividual))
            graph.add((target, RDF.type, subject))
            text.describe(graph, target, element.data)
            if strategy == "name" and naming_text(element.data.get("name")) is None:
                diagnostics.add("WARNING", "GENERIC_ID_FALLBACK",
                                "Enumeration Literal has no usable name-based candidate; its own source ID supplies the IRI.",
                                "Value retained and counted as successfully transformed.", (element.location,), str(target))
            elif strategy == "id" and missing_name(element.data.get("name")):
                diagnostics.add("INFO", "MISSING_NAME",
                                "Enumeration Literal has missing descriptive name text.",
                                "Value retained using its ordinary own-ID IRI.", (element.location,), str(target))
        if enumeration.complete and values:
            head = BNode()
            Collection(graph, head, values)
            graph.add((subject, OWL.oneOf, head))
        if len(values) >= 2:
            axiom, head = BNode(), BNode()
            Collection(graph, head, values)
            graph.add((axiom, RDF.type, OWL.AllDifferent))
            graph.add((axiom, OWL.distinctMembers, head))
