"""Ordinary binary relations and transformation-time connector recognition."""

from collections import defaultdict
from dataclasses import dataclass

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import OWL, RDF, RDFS

from .annotations import TextAnnotations, source_text
from .datatypes import PRIMITIVES, datatype_key
from .diagnostics import DiagnosticCollector, SourceLocation, _AbortConversion
from .dkgm import DKGM_PROPERTIES
from .identity import class_name_candidate, escape_id, missing_name, naming_text, normalize_name
from .multiplicity import (emit_attribute_multiplicity, parse_relation_multiplicity,
                           parse_relation_multiplicity_raw, report_invalid_multiplicity,
                           report_missing_multiplicity)
from .properties import PropertyExpressions
from .source import SourceElement, SourceIndex, input_error

_REJECTED_DATATYPE_STEREOTYPES = frozenset({
    "componentOf", "memberOf", "subCollectionOf", "subQuantityOf",
    "characterization", "mediation", "participational", "externalDependence",
})


@dataclass(frozen=True)
class Relation:
    source: SourceElement
    source_end: SourceElement
    target_end: SourceElement
    domain: SourceElement
    range: SourceElement
    kind: URIRef = OWL.ObjectProperty
    datatype: URIRef | None = None


def _discard_instantiation(element: SourceElement, diagnostics: DiagnosticCollector, policy: str) -> None:
    """Report categories only; discarded values never enter the diagnostic."""
    data = element.data
    identifier = data.get("id")
    if "properties" in data and data["properties"] is not None:
        ends = data["properties"]
        if not isinstance(ends, list):
            input_error(
                diagnostics,
                policy,
                "FAILED_RELATION",
                f"Instantiation relation {identifier!r} properties field is not a JSON array (got {type(ends).__name__}).",
                (element.location,),
                "Affected instantiation relation omitted without generating discard output; independent mappings retained.",
            )
            return
        if any(not isinstance(end, dict) or end.get("type") != "Property" for end in ends):
            input_error(
                diagnostics,
                policy,
                "FAILED_RELATION",
                f"Instantiation relation {identifier!r} properties array contains a non-object or non-Property entry.",
                (element.location,),
                "Affected instantiation relation omitted without generating discard output; independent mappings retained.",
            )
            return
    else:
        ends = []
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
    comparative_derivations: dict[str, list[tuple[SourceElement, SourceElement]]] = defaultdict(list)
    omitted = set()
    for element in index.elements:
        data = element.data
        if data["type"] != "Relation":
            continue
        identifier = data.get("id")
        if not isinstance(identifier, str) or not identifier:
            raise NotImplementedError("Invalid relation-ID recovery remains unspecified")
        if data.get("stereotype") == "instantiation":
            _discard_instantiation(element, diagnostics, policy)
            omitted.add(identifier)
            continue
        if "properties" not in data:
            input_error(
                diagnostics, policy, "FAILED_RELATION",
                f"Relation {identifier!r} is missing its 'properties' field.",
                (element.location,),
                "Affected relation and dependent output omitted; independent mappings retained.",
            )
            omitted.add(identifier)
            continue
        ends = data["properties"]
        if ends is None:
            input_error(
                diagnostics, policy, "FAILED_RELATION",
                f"Relation {identifier!r} properties field is explicitly null.",
                (element.location,),
                "Affected relation and dependent output omitted; independent mappings retained.",
            )
            omitted.add(identifier)
            continue
        if not isinstance(ends, list):
            input_error(
                diagnostics, policy, "FAILED_RELATION",
                f"Relation {identifier!r} properties field is not a JSON array (got {type(ends).__name__}).",
                (element.location,),
                "Affected relation and dependent output omitted; independent mappings retained.",
            )
            omitted.add(identifier)
            continue
        if any(not isinstance(end, dict) or end.get("type") != "Property" for end in ends):
            input_error(
                diagnostics, policy, "FAILED_RELATION",
                f"Relation {identifier!r} properties array contains a non-object or non-Property entry.",
                (element.location,),
                "Affected relation and dependent output omitted; independent mappings retained.",
            )
            omitted.add(identifier)
            continue
        if len(ends) != 2:
            input_error(
                diagnostics, policy, "FAILED_RELATION",
                f"Non-instantiation relation {identifier!r} has non-binary properties array (length {len(ends)}, expected 2).",
                (element.location,),
                "Affected relation and dependent output omitted; independent mappings retained.",
            )
            omitted.add(identifier)
            continue
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
                        groundings[relation.data["id"]][classifier.data["id"]] = classifier
                    elif pattern == ("comparative", "quality"):
                        recognized = True
                        comparative_derivations[relation.data["id"]].append((element, classifier))
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
        for source in (element,) + declarations:
            for flag in ("isAbstract", "isDerived", "isReadOnly", "isOrdered"):
                if source.data.get(flag) is not None and type(source.data[flag]) is not bool:
                    raise NotImplementedError("Malformed relation/end flag recovery remains unspecified")
        source_cls, target_cls = endpoints
        if source_cls.data["id"] not in generated:
            input_error(
                diagnostics, policy, "FAILED_RELATION",
                f"Relation {identifier!r} source {source_cls.data['id']!r} has no generated local owl:Class.",
                (element.location, declarations[0].location, source_cls.location),
                "Affected relation omitted without reversing direction or inventing a local OWL class; independent mappings retained.",
            )
            omitted.add(identifier)
            continue
        if target_cls.data["id"] not in generated:
            key = datatype_key(target_cls.data.get("name")) if target_cls.data.get("stereotype") == "datatype" else None
            if key == "void":
                input_error(
                    diagnostics, policy, "INCOMPATIBLE_DATATYPE_RELATION",
                    f"Ordinary binary relation {identifier!r} targets Visual Paradigm 'void', which has no registered datatype mapping.",
                    (element.location, declarations[1].location, target_cls.location),
                    "Affected relation omitted without generating a rangeless datatype property; independent mappings retained.",
                )
                omitted.add(identifier)
                continue
            if key not in PRIMITIVES:
                input_error(
                    diagnostics, policy, "FAILED_RELATION",
                    f"Relation {identifier!r} target {target_cls.data['id']!r} has no generated local owl:Class.",
                    (element.location, declarations[1].location, target_cls.location),
                    "Affected relation omitted; independent mappings retained.",
                )
                omitted.add(identifier)
                continue
            stereotype = data.get("stereotype")
            if stereotype in _REJECTED_DATATYPE_STEREOTYPES:
                input_error(
                    diagnostics, policy, "INCOMPATIBLE_DATATYPE_RELATION",
                    f"Datatype-valued relation {identifier!r} cannot use stereotype {stereotype!r}, which requires an owl:ObjectProperty.",
                    (element.location,),
                    "Affected datatype-valued relation omitted without bridge, characteristic, or cardinality output; independent mappings retained.",
                )
                omitted.add(identifier)
                continue
            source_end = declarations[0]
            bounds, missing, invalid = parse_relation_multiplicity_raw(source_end)
            requires_inverse = (bounds.lower is not None and bounds.lower > 0) or bounds.upper is not None
            if missing:
                report_missing_multiplicity(source_end, diagnostics, "Relation end")
            elif invalid:
                report_invalid_multiplicity(source_end, diagnostics, policy, "Relation end", defer_abort=True)
                if requires_inverse:
                    input_error(
                        diagnostics, policy, "INCOMPATIBLE_DATATYPE_RELATION",
                        f"Datatype-valued relation {identifier!r} source-end multiplicity {source_end.data['cardinality']!r} requires an unavailable inverse datatype property.",
                        (element.location, source_end.location),
                        "Affected datatype-valued relation omitted; inverse unavailability takes precedence over recoverable source-end bounds.",
                    )
                    omitted.add(identifier)
                    continue
                if policy != "best-effort":
                    raise _AbortConversion
            elif requires_inverse:
                input_error(
                    diagnostics, policy, "INCOMPATIBLE_DATATYPE_RELATION",
                    f"Datatype-valued relation {identifier!r} source-end multiplicity {source_end.data['cardinality']!r} requires an unavailable inverse datatype property.",
                    (element.location, source_end.location),
                    "Affected datatype-valued relation omitted without generating an inverse or discarding constraints; independent mappings retained.",
                )
                omitted.add(identifier)
                continue
            relations.append(Relation(element, *declarations, *endpoints, kind=OWL.DatatypeProperty, datatype=PRIMITIVES[key]))
            continue
        relations.append(Relation(element, *declarations, *endpoints))

    filtered: list[Relation] = []
    for relation in relations:
        rid = relation.source.data["id"]
        if relation.kind == OWL.DatatypeProperty and rid in comparative_derivations:
            for derivation, quality in comparative_derivations[rid]:
                input_error(
                    diagnostics, policy, "INCOMPATIBLE_DATATYPE_RELATION",
                    f"Datatype-valued relation {rid!r} conflicts with recognized comparative-quality derivation {derivation.data['id']!r}, which requires an owl:ObjectProperty.",
                    (relation.source.location, derivation.location, quality.location),
                    "Affected comparative relation and dependent output omitted; quality class and independent mappings retained.",
                )
            omitted.add(rid)
            continue
        filtered.append(relation)
    return tuple(filtered), {key: tuple(values.values()) for key, values in groundings.items()}, omitted


def _semantic_name(relation: Relation) -> str | None:
    """Select lexical roles only, preserving primary direction and property logic."""
    stereotype = relation.source.data.get("stereotype")
    part_whole = {
        "componentOf": ("hasComponent", "componentOf"),
        "participational": ("hasParticipationalPart", "participationalPartOf"),
        "subCollectionOf": ("hasSubCollection", "subCollectionOf"),
        "subQuantityOf": ("hasSubQuantity", "subQuantityOf"),
    }
    if stereotype in part_whole:
        source_whole = relation.source_end.data.get("aggregationKind") in {"SHARED", "COMPOSITE"}
        target_whole = relation.target_end.data.get("aggregationKind") in {"SHARED", "COMPOSITE"}
        if source_whole != target_whole:
            return part_whole[stereotype][0 if source_whole else 1]
        return None
    a, b = relation.domain.data.get("stereotype"), relation.range.data.get("stereotype")
    if stereotype == "externalDependence":
        endurants = {"kind", "collective", "quantity", "relator", "quality", "subkind", "role",
                     "phase", "historicalRole", "category", "mixin", "roleMixin", "phaseMixin",
                     "historicalRoleMixin"}
        if a == "mode" and b in endurants:
            return "externallyDependsOn"
        if b == "mode" and a in endurants:
            return "isExternalDependencyOf"
        return None
    if stereotype == "historicalDependence":
        # No supported explicit discriminator assigns dependent/antecedent roles.
        return None
    if stereotype in {"bringsAbout", "triggers"} and (a, b) not in (
        ("event", "situation"), ("situation", "event")
    ):
        return None
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
    if stereotype == "characterization":
        left, right = a in {"mode", "quality"}, b in {"mode", "quality"}
        if left != right:
            return "characterizes" if left else "isCharacterizedBy"
    if stereotype in selectors:
        role, forward, backward = selectors[stereotype]
        if (a == role) != (b == role):
            return forward if a == role else backward
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
                    grounds = tuple(ground for ground in groundings.get(source.data["id"], ())
                                    if ground.data.get("stereotype") == "relator")
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
                    expressions: PropertyExpressions) -> list[tuple[URIRef, SourceLocation]]:
    """Emit ordinary mappings and return the generic targets and sources of emitted bridges."""
    bridges: list[tuple[URIRef, SourceLocation]] = []
    for relation in relations:
        source, start, end = relation.source, relation.source_end, relation.target_end
        primary = resources[end.data["id"]]
        domain = resources[relation.domain.data["id"]]
        range_ = relation.datatype if relation.kind == OWL.DatatypeProperty else resources[relation.range.data["id"]]
        graph.add((primary, RDF.type, relation.kind))
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
        elif relation.kind == OWL.DatatypeProperty and any(value.strip() for _, value in source_text(start.data.get("name"))):
            diagnostics.add(
                "WARNING", "UNREPRESENTABLE_SOURCE_ROLE",
                "Source-end role name on datatype-valued relation cannot be represented because no inverse property exists.",
                "Primary datatype property retained; source-end role name and source-end description omitted without generating an inverse.",
                (source.location, start.location), str(primary),
            )
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
            stereotype = occurrence.data.get("stereotype")
            if stereotype in {"begin", "end"}:
                graph.add((primary, RDFS.comment, Literal(
                    f"Declared OntoUML property stereotype on the {context} association end: {stereotype}.", lang="en")))
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
            if occurrence is start and relation.kind == OWL.DatatypeProperty:
                continue
            bounds = parse_relation_multiplicity(occurrence, diagnostics, policy)
            if (bounds.lower is not None and bounds.lower > 0) or bounds.upper is not None:
                expression = expressions.resolve(occurrence)
                emit_attribute_multiplicity(graph, owner, expression, bounds)
        stereotype = source.data.get("stereotype")
        generic = DKGM_PROPERTIES.get(stereotype)
        if generic is not None:
            graph.add((primary, RDFS.subPropertyOf, generic))
            graph.add((primary, RDF.type, OWL.AsymmetricProperty))
            bridges.append((generic, source.location))
        elif stereotype in {"historicalDependence", "participation", "creation", "termination",
                            "participational", "manifestation"}:
            stereotype_label = "Historical-dependence" if stereotype == "historicalDependence" else stereotype.capitalize()
            diagnostics.add("WARNING", "UNMAPPED_RELATION_STEREOTYPE",
                            f"{stereotype_label} semantics are only partially translated.",
                            ("Ordinary relation mappings and the accepted asymmetry compatibility gate remain applicable; "
                             "no further stereotype-only axioms or declaration annotations are supplied."
                             if stereotype == "participational" else
                             "Ordinary relation mappings are retained; no additional axioms or "
                             "stereotype-declaration annotations are supplied solely by this stereotype."),
                            (source.location,), str(primary))
        elif stereotype in {"mediation", "characterization", "externalDependence", "bringsAbout", "triggers"}:
            diagnostics.add("WARNING", "UNMAPPED_RELATION_STEREOTYPE",
                            f"The {stereotype} relation semantics are only partially translated.",
                            "Ordinary relation mappings and applicable axioms are retained.",
                            (source.location,), str(primary))
    return bridges
