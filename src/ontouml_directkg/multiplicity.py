"""Attribute multiplicity parsing and necessary cardinalities (DK-ATT/DIAG)."""

from dataclasses import dataclass
import re

from rdflib import BNode, Graph, Literal, URIRef
from rdflib.namespace import OWL, RDF, RDFS, XSD

from .diagnostics import DiagnosticCollector
from .source import SourceElement, input_error


@dataclass(frozen=True)
class Multiplicity:
    lower: int | None = None
    upper: int | None = None
    standalone_star: bool = False


def _number(text: str) -> int | None:
    return int(text) if re.fullmatch(r"[0-9]+", text) else None


def parse_attribute_multiplicity(source: SourceElement, diagnostics: DiagnosticCollector,
                                 policy: str) -> Multiplicity:
    """Normalize only accepted lexical forms and retain valid independent bounds."""
    if "cardinality" not in source.data:
        diagnostics.add("WARNING", "MISSING_CARDINALITY",
                        "Attribute cardinality field is absent; no explicit multiplicity is available.",
                        "Property retained without a default cardinality restriction.", (source.location,))
        return Multiplicity()
    value = source.data["cardinality"]
    if value is None:
        return Multiplicity()
    parsed = Multiplicity()
    valid = False
    if isinstance(value, str):
        text = value.strip()
        if text == "*":
            return Multiplicity(standalone_star=True)
        if ".." not in text:
            number = _number(text)
            if number is not None:
                return Multiplicity(number, number)
        elif text.count("..") == 1:
            lower, upper = (part.strip() for part in text.split(".."))
            # An extra dot adjoining the delimiter is ambiguous notation,
            # unlike a decimal/symbolic bound at an otherwise clear position.
            if not lower.endswith(".") and not upper.startswith("."):
                low, high = _number(lower), _number(upper)
                parsed = Multiplicity(low, high)
                valid = low is not None and (high is not None or upper == "*")
    if not valid:
        input_error(diagnostics, policy, "INVALID_CARDINALITY",
                    f"Attribute cardinality {value!r} is not wholly translatable under the accepted syntax.",
                    (source.location,),
                    "Property retained; only independently valid numeric bounds are preserved, without guessed bounds.")
    return parsed


def emit_attribute_multiplicity(graph: Graph, owner: URIRef, property_iri: URIRef,
                                bounds: Multiplicity) -> None:
    """Use unqualified necessary restrictions; ranges remain global axioms."""
    if bounds.standalone_star:
        raise NotImplementedError("Standalone attribute '*' is recognized; its exact restriction output remains deferred")
    lower, upper = bounds.lower, bounds.upper
    if lower is not None and upper is not None and lower == upper:
        restrictions = [(OWL.cardinality, lower)]
    else:
        restrictions = []
        if lower is not None and lower > 0:
            restrictions.append((OWL.minCardinality, lower))
        if upper is not None:
            restrictions.append((OWL.maxCardinality, upper))
    for predicate, value in restrictions:
        node = BNode()
        graph.add((node, RDF.type, OWL.Restriction))
        graph.add((node, OWL.onProperty, property_iri))
        graph.add((node, predicate, Literal(value, datatype=XSD.nonNegativeInteger)))
        graph.add((owner, RDFS.subClassOf, node))
