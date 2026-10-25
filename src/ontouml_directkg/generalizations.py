"""Explicit class generalizations, set constraints and categorizer punning."""

from collections import defaultdict
from itertools import combinations

from rdflib import BNode, Graph, URIRef
from rdflib.collection import Collection
from rdflib.namespace import OWL, RDF, RDFS

from .diagnostics import DiagnosticCollector
from .source import SourceElement, SourceIndex, input_error


def _relation_generalization(index: SourceIndex, element: SourceElement) -> bool:
    """Route by available declarations; mapping still validates every reference."""
    references = [element.data.get(field) for field in ("specific", "general")]
    kinds = set()
    for reference in references:
        try:
            endpoint = index.resolve(reference)
        except KeyError:
            continue
        if endpoint.data["type"] in {"Class", "Relation"}:
            kinds.add(endpoint.data["type"])
    if not kinds:
        for reference in references:
            identifier = reference.get("id") if isinstance(reference, dict) else None
            endpoint = index.declarations.get(identifier) if isinstance(identifier, str) else None
            if endpoint is not None and endpoint.data["type"] in {"Class", "Relation"}:
                kinds.add(endpoint.data["type"])
    if kinds:
        return "Relation" in kinds
    return any(isinstance(reference, dict) and reference.get("type") == "Relation"
               for reference in references)


def _relation_set(index: SourceIndex, element: SourceElement) -> bool:
    members = element.data.get("generalizations")
    if not isinstance(members, list):
        return False
    for reference in members:
        member = index.declarations.get(reference.get("id")) if isinstance(reference, dict) and isinstance(reference.get("id"), str) else None
        if member is not None and member.data["type"] == "Generalization" and _relation_generalization(index, member):
            return True
    return False


def emit_generalizations(graph: Graph, index: SourceIndex, resources: dict[str, URIRef],
                         diagnostics: DiagnosticCollector, policy: str) -> None:
    """Keep source edges separate from coverage edges and powertype traversal."""
    edges: dict[str, tuple[SourceElement, SourceElement]] = {}
    children: dict[str, set[str]] = defaultdict(set)
    for element in index.elements:
        if element.data["type"] != "Generalization":
            continue
        if _relation_generalization(index, element):
            continue
        identifier = element.data.get("id")
        if not isinstance(identifier, str) or not identifier:
            raise NotImplementedError("Invalid generalization-ID recovery requires the deferred Architect decision")
        try:
            specific = index.resolve(element.data.get("specific"))
            general = index.resolve(element.data.get("general"))
        except KeyError as exc:
            input_error(diagnostics, policy, "FAILED_CLASS_GENERALIZATION",
                        f"Generalization {identifier!r} has an invalid or unresolved classifier reference: {exc}.",
                        (element.location,), "Affected generalization omitted; independently transformable classes and edges retained.")
            continue
        if specific.data["type"] != "Class" or general.data["type"] != "Class":
            raise NotImplementedError("Non-class generalization mapping belongs to BI-W4")
        sid, gid = specific.data["id"], general.data["id"]
        if sid not in resources or gid not in resources:
            input_error(diagnostics, policy, "FAILED_CLASS_GENERALIZATION",
                        f"Generalization {identifier!r} has no generated local OWL class for an endpoint.",
                        (element.location, specific.location, general.location),
                        "Affected generalization omitted; independently transformable classes and edges retained.")
            continue
        edges[identifier] = (specific, general)
        children[gid].add(sid)
        graph.add((resources[sid], RDFS.subClassOf, resources[gid]))

    for element in index.elements:
        if element.data["type"] == "GeneralizationSet" and not _relation_set(index, element):
            _emit_set(graph, index, element, resources, edges, children, diagnostics, policy)


def _emit_set(graph: Graph, index: SourceIndex, element: SourceElement, resources: dict[str, URIRef],
              edges: dict[str, tuple[SourceElement, SourceElement]], children: dict[str, set[str]],
              diagnostics: DiagnosticCollector, policy: str) -> None:
    data = element.data
    members = data.get("generalizations")
    if not isinstance(members, list):
        raise NotImplementedError("Missing/malformed generalization-set membership handling remains unspecified")
    if not members:
        input_error(diagnostics, policy, "EMPTY_GENERALIZATION_SET",
                    "Generalization set has an explicitly empty generalizations array.", (element.location,),
                    "Empty set contributes no axioms; independently applicable mappings are retained.")
        return
    for flag in ("isComplete", "isDisjoint"):
        if data.get(flag) is not None and type(data[flag]) is not bool:
            raise NotImplementedError("Malformed generalization-set flag recovery remains unspecified")
    seen = set()
    resolved = []
    complete = True
    for reference in members:
        try:
            member = index.resolve(reference)
            if member.data["type"] != "Generalization":
                raise KeyError("Set member does not reference a Generalization")
        except KeyError as exc:
            input_error(diagnostics, policy, "UNRESOLVED_GENERALIZATION_SET_MEMBER",
                        f"Generalization-set member {reference!r} cannot be resolved: {exc}.", (element.location,),
                        "Coverage omitted; disjointness among successful explicit specifics and independent mappings retained.")
            complete = False
            continue
        identifier = member.data["id"]
        if identifier in seen:
            raise NotImplementedError("Duplicate generalization-set member handling remains unspecified")
        seen.add(identifier)
        if identifier not in edges:
            # The underlying transformation already produced its ERROR. Do not
            # manufacture another failure just to count surviving members.
            complete = False
        else:
            resolved.append(edges[identifier])
    specifics = {specific.data["id"]: specific for specific, _ in resolved}
    if len(specifics) != len(resolved):
        raise NotImplementedError("Repeated-specific generalization-set membership handling remains unspecified")
    general_ids = {general.data["id"] for _, general in resolved}
    if data.get("isDisjoint") is True:
        for left, right in combinations(sorted(specifics), 2):
            graph.add((resources[left], OWL.disjointWith, resources[right]))
    if complete and data.get("isComplete") is True and len(general_ids) == 1:
        general = resolved[0][1]
        gid = general.data["id"]
        if len(members) == 1:
            specific = resolved[0][0]
            graph.add((resources[gid], RDFS.subClassOf, resources[specific.data["id"]]))
            diagnostics.add("INFO", "SINGLETON_COMPLETENESS",
                            "Applying singleton completeness makes the generated general and specific classes "
                            "extensionally equivalent while their identifiers remain distinct.",
                            "Reverse subclass axiom emitted; existing forward subclass axiom retained.",
                            (element.location, general.location, specific.location))
        else:
            expression, head = BNode(), BNode()
            Collection(graph, head, [resources[sid] for sid in sorted(specifics)])
            graph.add((expression, RDF.type, OWL.Class))
            graph.add((expression, OWL.unionOf, head))
            graph.add((resources[gid], RDFS.subClassOf, expression))
    categorizer = data.get("categorizer")
    if categorizer is None:
        return
    if not complete:
        raise NotImplementedError("Categorizer recovery after a failed class-set member remains unspecified")
    try:
        classifier = index.resolve(categorizer)
    except KeyError as exc:
        raise NotImplementedError("Unresolved categorizer recovery remains outside the decided baseline") from exc
    cid = classifier.data.get("id")
    if classifier.data["type"] != "Class" or cid not in resources:
        raise NotImplementedError("Categorizer without a generated local class remains outside the decided baseline")
    extension = set(specifics)
    if classifier.data.get("isPowertype") is True and len(general_ids) == 1:
        pending = list(general_ids)
        visited = set()
        while pending:
            identifier = pending.pop()
            if identifier in visited:
                continue
            visited.add(identifier)
            extension.add(identifier)
            pending.extend(children.get(identifier, set()) - visited)
    for identifier in extension:
        subject = resources[identifier]
        graph.add((subject, RDF.type, OWL.NamedIndividual))
        graph.add((subject, RDF.type, resources[cid]))


def emit_relation_generalizations(graph: Graph, index: SourceIndex, primaries: dict[str, URIRef],
                                   inverses: dict[str, URIRef], diagnostics: DiagnosticCollector,
                                   policy: str) -> None:
    """Keep surviving specifics for disjointness even when their general fails."""
    declared = {}
    mapped = set()
    for element in index.elements:
        if element.data["type"] != "Generalization" or not _relation_generalization(index, element):
            continue
        identifier = element.data.get("id")
        if not isinstance(identifier, str) or not identifier:
            raise NotImplementedError("Invalid generalization-ID recovery remains unspecified")
        endpoints = []
        failures = []
        for field in ("specific", "general"):
            try:
                endpoint = index.resolve(element.data.get(field))
            except KeyError as exc:
                endpoint = None
                failures.append(f"{field}: {exc}")
            if endpoint is not None and endpoint.data["type"] != "Relation":
                raise NotImplementedError("Mixed class/relation generalization mappings remain unspecified")
            endpoints.append(endpoint)
        specific, general = declared[identifier] = tuple(endpoints)
        if (specific is None or general is None or specific.data["id"] not in primaries
                or general.data["id"] not in primaries):
            input_error(diagnostics, policy, "FAILED_RELATION_GENERALIZATION",
                        "Relation generalization lacks both generated primary properties"
                        + (": " + "; ".join(failures) if failures else "") + ".",
                        (element.location,) + tuple(endpoint.location for endpoint in endpoints if endpoint is not None),
                        "Affected hierarchy edge omitted; independent properties, edges and specific-set disjointness retained.")
            continue
        sid, gid = specific.data["id"], general.data["id"]
        graph.add((primaries[sid], RDFS.subPropertyOf, primaries[gid]))
        if sid in inverses and gid in inverses:
            graph.add((inverses[sid], RDFS.subPropertyOf, inverses[gid]))
        mapped.add(identifier)

    for element in index.elements:
        data = element.data
        if data["type"] != "GeneralizationSet" or not _relation_set(index, element):
            continue
        members = data.get("generalizations")
        if not isinstance(members, list):
            raise NotImplementedError("Malformed generalization-set membership remains unspecified")
        if data.get("categorizer") is not None:
            raise NotImplementedError("Categorizer treatment for relation sets remains unspecified")
        for flag in ("isComplete", "isDisjoint"):
            if data.get(flag) is not None and type(data[flag]) is not bool:
                raise NotImplementedError("Malformed generalization-set flag recovery remains unspecified")
        seen, specific_ids = set(), set()
        specifics, resolved = {}, []
        complete = True
        for reference in members:
            try:
                member = index.resolve(reference)
                if member.data["type"] != "Generalization":
                    raise KeyError("Set member does not identify a Generalization")
            except KeyError as exc:
                input_error(diagnostics, policy, "UNRESOLVED_GENERALIZATION_SET_MEMBER",
                            f"Relation-set member {reference!r} cannot resolve: {exc}.", (element.location,),
                            "Completeness omitted; surviving explicit-specific disjointness and independent mappings retained.")
                complete = False
                continue
            if not _relation_generalization(index, member):
                raise NotImplementedError("Mixed class/relation set membership remains unspecified")
            identifier = member.data["id"]
            if identifier in seen:
                raise NotImplementedError("Duplicate generalization-set membership remains unspecified")
            seen.add(identifier)
            specific, general = declared[identifier]
            if specific is not None:
                sid = specific.data["id"]
                if sid in specific_ids:
                    raise NotImplementedError("Repeated-specific generalization-set membership remains unspecified")
                specific_ids.add(sid)
                if sid in primaries:
                    specifics[sid] = specific
            if identifier not in mapped:
                complete = False
            else:
                resolved.append((specific, general))
        if data.get("isDisjoint") is True:
            for sid, other in combinations(sorted(specifics), 2):
                graph.add((primaries[sid], OWL.propertyDisjointWith, primaries[other]))
                if sid in inverses and other in inverses:
                    graph.add((inverses[sid], OWL.propertyDisjointWith, inverses[other]))
        if data.get("isComplete") is not True:
            continue
        if complete and len(members) == 1:
            specific, general = resolved[0]
            sid, gid = specific.data["id"], general.data["id"]
            graph.add((primaries[gid], RDFS.subPropertyOf, primaries[sid]))
            if sid in inverses and gid in inverses:
                graph.add((inverses[gid], RDFS.subPropertyOf, inverses[sid]))
            diagnostics.add("INFO", "SINGLETON_COMPLETENESS",
                            "Singleton completeness makes the general and specific relation extensions equivalent "
                            "while their identifiers remain distinct.",
                            "Reverse subproperty inclusion emitted; forward inclusion retained.",
                            (element.location, general.location, specific.location))
        elif len(specific_ids) >= 2:
            diagnostics.add("WARNING", "RELATION_SET_COMPLETENESS",
                            "Multi-member relation-set coverage is not represented by this mapping.",
                            "No completeness axiom or substitute validation constraint emitted; other mappings retained.",
                            (element.location,))
