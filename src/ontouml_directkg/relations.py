"""Ordinary binary relations and transformation-time connector recognition."""

from collections import defaultdict
from dataclasses import dataclass

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import OWL, RDF, RDFS

from .annotations import TextAnnotations, source_text
from .diagnostics import DiagnosticCollector
from .identity import class_name_candidate, escape_id, missing_name, naming_text, normalize_name
from .multiplicity import emit_attribute_multiplicity, parse_relation_multiplicity
from .properties import PropertyExpressions
from .source import SourceElement, SourceIndex, input_error


@dataclass(frozen=True)
class Relation:
    source: SourceElement
    source_end: SourceElement
    target_end: SourceElement
    domain: SourceElement
    range: SourceElement


def _discard_instantiation(element: SourceElement, diagnostics: DiagnosticCollector) -> None:
    """Report categories only; discarded values never enter the diagnostic."""
    data = element.data
    ends = data.get("properties") or []
    if not isinstance(ends, list) or not all(isinstance(end, dict) for end in ends):
        raise NotImplementedError("Malformed instantiation-container recovery remains unspecified")
    categories = []
    for field, label in (("id", "association identifier"), ("name", "association name"),
                         ("description", "association description")):
        if data.get(field) is not None and data[field] != "":
            categories.append(label)
    if any(end.get("name") is not None and end["name"] != "" for end in ends):
        categories.append("role names")
    if any(end.get("cardinality") is not None for end in ends):
        categories.append("multiplicities")
    if (any(data.get(flag) is not None for flag in ("isAbstract", "isDerived"))
            or any(end.get(flag) is not None for end in ends
                   for flag in ("isDerived", "isReadOnly", "isOrdered", "aggregationKind"))):
        categories.append("association-level characteristics")
    if categories:
        diagnostics.add("WARNING", "DISCARDED_INSTANTIATION_INFORMATION",
                        "Instantiation association information is discarded: " + ", ".join(categories) + ".",
                        "No association or property resource, annotations, or instantiation fact is generated.",
                        (element.location,))


def collect_relations(index: SourceIndex, classes: tuple[SourceElement, ...],
                      diagnostics: DiagnosticCollector, policy: str
                      ) -> tuple[tuple[Relation, ...], dict[str, tuple[SourceElement, ...]], set[str]]:
    """Require both endpoints before producing either directional property."""
    generated = {element.data["id"] for element in classes}
    relations = []
    groundings: dict[str, dict[str, SourceElement]] = defaultdict(dict)
    omitted = set()
    for element in index.elements:
        data = element.data
        if data["type"] != "Relation":
            continue
        identifier = data.get("id")
        if not isinstance(identifier, str) or not identifier:
            raise NotImplementedError("Invalid relation-ID recovery remains unspecified")
        if data.get("stereotype") == "instantiation":
            _discard_instantiation(element, diagnostics)
            omitted.add(identifier)
            continue
        ends = data.get("properties")
        if not isinstance(ends, list) or len(ends) != 2:
            raise NotImplementedError("Non-binary/malformed relation-container handling is outside this increment")
        declarations = tuple(SourceElement(end, element.path + f".properties[{n}]", identifier)
                             for n, end in enumerate(ends))
        try:
            for end in declarations:
                end_id = end.data.get("id")
                if not isinstance(end_id, str) or not end_id:
                    raise KeyError("Missing or invalid association-end ID")
                try:
                    end_id.encode("utf-8")
                except UnicodeError as exc:
                    raise KeyError("Invalid association-end ID encoding") from exc
            endpoints = tuple(index.resolve(end.data.get("propertyType")) for end in declarations)
            if any(endpoint.data["type"] not in {"Class", "Relation"} for endpoint in endpoints):
                raise KeyError("Endpoint does not identify a classifier")
        except KeyError as exc:
            input_error(diagnostics, policy, "FAILED_RELATION",
                        f"Relation endpoints cannot support transformation: {exc}.",
                        (element.location,) + tuple(end.location for end in declarations),
                        "Neither directional property is generated; independent source mappings are retained.")
            continue
        if any(endpoint.data["type"] == "Relation" for endpoint in endpoints):
            recognized = False
            if data.get("stereotype") == "derivation":
                for relation, classifier in (endpoints, endpoints[::-1]):
                    if relation.data["type"] != "Relation" or classifier.data["type"] != "Class":
                        continue
                    pattern = (relation.data.get("stereotype"), classifier.data.get("stereotype"))
                    if pattern in {("material", "relator"), ("material", "mode")}:
                        recognized = True
                        if pattern[1] == "relator":
                            groundings[relation.data["id"]][classifier.data["id"]] = classifier
                    elif pattern == ("comparative", "quality"):
                        recognized = True
                        diagnostics.add("WARNING", "UNSUPPORTED_COMPARATIVE_DERIVATION",
                                        "Comparative-quality derivation semantics are not represented: the supported "
                                        "source supplies no comparison rule.",
                                        "Connector omitted; independent comparative and quality mappings retained.",
                                        (element.location, relation.location, classifier.location))
            if not recognized:
                diagnostics.add("WARNING", "UNSUPPORTED_RELATION_CONNECTOR",
                                "No accepted mapping exists for this resolved relation-valued endpoint pattern.",
                                "Connector omitted without a resource, inverse, grounding annotation or constraints; "
                                "independent endpoint transformations retained.", (element.location,))
            omitted.add(identifier)
            continue
        if any(endpoint.data["id"] not in generated for endpoint in endpoints):
            raise NotImplementedError("Ordinary relation endpoints without local class representations remain unspecified")
        for source in (element,) + declarations:
            for flag in ("isAbstract", "isDerived", "isReadOnly", "isOrdered"):
                if source.data.get(flag) is not None and type(source.data[flag]) is not bool:
                    raise NotImplementedError("Malformed relation/end flag recovery remains unspecified")
        relations.append(Relation(element, *declarations, *endpoints))
    return tuple(relations), {key: tuple(values.values()) for key, values in groundings.items()}, omitted


def _semantic_name(relation: Relation) -> str | None:
    """Use only settled, distinguishable roles; never guess ambiguous directions."""
    stereotype = relation.source.data.get("stereotype")
    if stereotype in {"componentOf", "historicalDependence", "participational",
                      "subCollectionOf", "subQuantityOf", "externalDependence"}:
        raise NotImplementedError("This stereotype's directional naming criterion requires the deferred Architect decision")
    selectors = {
        "bringsAbout": ("event", "bringsAbout", "broughtAboutBy"),
        "creation": ("event", "creates", "wasCreatedIn"),
        "manifestation": ("event", "manifests", "manifestedIn"),
        "mediation": ("relator", "mediates", "isMediatedBy"),
        "memberOf": ("collective", "hasMember", "memberOf"),
        "participation": ("event", "hasParticipant", "participatesIn"),
        "termination": ("event", "terminates", "wasTerminatedIn"),
        "triggers": ("situation", "triggers", "triggeredBy"),
    }
    a, b = relation.domain.data.get("stereotype"), relation.range.data.get("stereotype")
    if stereotype == "characterization":
        left, right = a in {"mode", "quality"}, b in {"mode", "quality"}
        if left != right:
            return "characterizes" if left else "isCharacterizedBy"
        raise NotImplementedError("The supported input does not distinguish these characterization naming roles")
    if stereotype in selectors:
        role, forward, backward = selectors[stereotype]
        if (a == role) != (b == role):
            return forward if a == role else backward
        raise NotImplementedError("The supported input does not distinguish these semantic naming roles")
    return None


def relation_names(relations: tuple[Relation, ...], groundings: dict[str, tuple[SourceElement, ...]],
                    strategy: str, labels: str, disable_stereotypes: bool,
                    diagnostics: DiagnosticCollector) -> tuple[dict[str, str], dict[str, str]]:
    """Keep lexical fallback labels independent of IRI qualification and suffixes."""
    candidates, lexical = {}, {}
    for relation in relations:
        source, target = relation.source, relation.target_end
        source_name = naming_text(source.data.get("name"))
        role = naming_text(target.data.get("name"))
        has_source_label = bool(source_text(source.data.get("name"))) or role is not None
        needs_lexical = strategy == "name" or (labels == "generated" and not has_source_label)
        candidate = None
        if needs_lexical:
            if source_name is not None:
                candidate = normalize_name(source_name)
            elif role is not None:
                candidate = normalize_name(role)
                if strategy == "name":
                    diagnostics.add("WARNING", "RELATION_NAMING",
                                    "Relation has no usable name; the target-end role supplies its lexical name.",
                                    "Ordinary primary-property mapping retained.", (source.location, target.location))
            elif not disable_stereotypes:
                stereotype = source.data.get("stereotype")
                if stereotype == "material":
                    grounds = groundings.get(source.data["id"], ())
                    selected = naming_text(grounds[0].data.get("name")) if len(grounds) == 1 else None
                    if selected is not None:
                        normalized = normalize_name(selected)
                        candidate = normalized[:1].lower() + normalized[1:]
                        if strategy == "name":
                            diagnostics.add("INFO", "RELATOR_NAMING",
                                            "The resolved grounding relator supplies the lexical material-property name.",
                                            "Property retains the material relation's original source and target.",
                                            (source.location, grounds[0].location))
                    else:
                        if strategy == "name":
                            diagnostics.add("WARNING", "UNAVAILABLE_GROUNDING_RELATOR",
                                            "A usable unique grounding relator name is unavailable.",
                                            "Material property retained with source-target naming.", (source.location,))
                elif stereotype == "comparative":
                    if strategy == "name":
                        diagnostics.add("WARNING", "COMPARATIVE_NAMING",
                                        "Comparative naming requires a domain-specific predicate unavailable here.",
                                        "Property retained with source-target naming.", (source.location,))
                else:
                    candidate = _semantic_name(relation)
            if candidate is None:
                components = [class_name_candidate(endpoint.data["id"], endpoint.data.get("name"))
                              for endpoint in (relation.domain, relation.range)]
                candidate = "_".join(part[:1].lower() + part[1:] for part in components)
                # Material/comparative branches already supplied their specific warning.
                if strategy == "name" and (disable_stereotypes or source.data.get("stereotype") not in {"material", "comparative"}):
                    diagnostics.add("WARNING", "RELATION_NAMING",
                                    "Relation has no usable name or target role; source-target naming is used.",
                                    "Ordinary primary-property mapping retained.", (source.location,))
            lexical[source.data["id"]] = candidate
        if strategy == "id" and missing_name(source.data.get("name")):
            diagnostics.add("WARNING", "MISSING_RELATION_NAME",
                            "Relation has missing descriptive name text.",
                            "Primary property retained using the target association-end ID.", (source.location,))
        candidates[target.data["id"]] = escape_id(target.data["id"]) if strategy == "id" else candidate
    return candidates, lexical


def emit_relations(graph: Graph, relations: tuple[Relation, ...], resources: dict[str, URIRef],
                    inverses: dict[str, URIRef], lexical: dict[str, str], label_mode: str,
                    text: TextAnnotations, diagnostics: DiagnosticCollector, policy: str,
                    expressions: PropertyExpressions) -> None:
    for relation in relations:
        source, start, end = relation.source, relation.source_end, relation.target_end
        primary = resources[end.data["id"]]
        domain, range_ = resources[relation.domain.data["id"]], resources[relation.range.data["id"]]
        graph.add((primary, RDF.type, OWL.ObjectProperty))
        graph.add((primary, RDFS.domain, domain))
        graph.add((primary, RDFS.range, range_))
        if source_text(source.data.get("name")):
            text.add(graph, primary, RDFS.label, source.data.get("name"))
        elif naming_text(end.data.get("name")) is not None:
            text.add(graph, primary, RDFS.label, end.data.get("name"))
        elif label_mode == "generated":
            graph.add((primary, RDFS.label, Literal(lexical[source.data["id"]])))
        text.add(graph, primary, RDFS.comment, source.data.get("description"))
        text.add(graph, primary, RDFS.comment, end.data.get("description"))
        inverse = inverses.get(start.data["id"])
        if inverse is not None:
            graph.add((inverse, RDF.type, OWL.ObjectProperty))
            graph.add((inverse, OWL.inverseOf, primary))
            graph.add((inverse, RDFS.domain, range_))
            graph.add((inverse, RDFS.range, domain))
            if any(value.strip() for _, value in source_text(start.data.get("name"))):
                text.add(graph, inverse, RDFS.label, start.data.get("name"))
            text.add(graph, inverse, RDFS.comment, start.data.get("description"))
        for occurrence, context in ((source, "relation"), (start, "source association end"),
                                     (end, "target association end")):
            derived = occurrence.data.get("isDerived")
            if type(derived) is bool:
                graph.add((primary, RDFS.comment,
                           Literal(f"OntoUML {context} isDerived: {str(derived).lower()}.", lang="en")))
                if derived:
                    diagnostics.add("INFO", "DERIVED_STATUS_ANNOTATION",
                                    "isDerived=true is preserved as an annotation; the annotation itself supplies no derivation rule.",
                                    "Primary property and comment retained.", (occurrence.location,))
        abstract = source.data.get("isAbstract")
        if type(abstract) is bool:
            graph.add((primary, RDFS.comment, Literal(f"OntoUML relation isAbstract: {str(abstract).lower()}.", lang="en")))
            diagnostics.add("INFO", "ABSTRACTNESS_ANNOTATION",
                            f"Explicit isAbstract={str(abstract).lower()} is preserved as an annotation; its meaning "
                            "is not additionally enforced through OWL logical constraints.",
                            "Primary property and comment retained.", (source.location,))
        for occurrence, context, owner in ((start, "source", range_), (end, "target", domain)):
            if occurrence.data.get("isReadOnly") is True:
                graph.add((primary, RDFS.comment,
                           Literal(f"OntoUML source metadata: the {context} association end is read-only.", lang="en")))
            aggregation = occurrence.data.get("aggregationKind")
            if aggregation in {"SHARED", "COMPOSITE"}:
                graph.add((primary, RDFS.comment, Literal(
                    f"OntoUML source metadata: the {context} association end has {aggregation.lower()} aggregation.", lang="en")))
            if occurrence.data.get("isOrdered") is True:
                graph.add((primary, RDFS.comment,
                           Literal(f"OntoUML source metadata: the {context} association end is ordered.", lang="en")))
                diagnostics.add("INFO", "ORDERING_ANNOTATION",
                                "Ordering is documented, but value order is not represented by the generated property mapping.",
                                "Primary property and comment retained without sequence structures or added logical semantics.",
                                (occurrence.location,))
            bounds = parse_relation_multiplicity(occurrence, diagnostics, policy)
            if (bounds.lower is not None and bounds.lower > 0) or bounds.upper is not None:
                expression = expressions.resolve(occurrence)
                emit_attribute_multiplicity(graph, owner, expression, bounds)
        stereotype = source.data.get("stereotype")
        if stereotype in {"memberOf", "subCollectionOf", "subQuantityOf", "componentOf"}:
            graph.add((primary, RDFS.subPropertyOf, URIRef("https://w3id.org/directkg/vocab/dkgm#" + stereotype)))
            graph.add((primary, RDF.type, OWL.AsymmetricProperty))
