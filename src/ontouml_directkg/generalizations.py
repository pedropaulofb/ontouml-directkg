"""Explicit class generalizations, set constraints and categorizer punning."""

from collections import defaultdict
from itertools import combinations

from rdflib import BNode, Graph, URIRef
from rdflib.collection import Collection
from rdflib.namespace import OWL, RDF, RDFS

from .diagnostics import DiagnosticCollector
from .source import SourceElement, SourceIndex, input_error, validate_boolean_flags


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
        try:
            member = index.resolve(reference)
        except KeyError:
            continue
        if member.data["type"] == "Generalization" and _relation_generalization(index, member):
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


def _resolve_categorizer(index: SourceIndex, element: SourceElement, resources: dict[str, URIRef],
                         diagnostics: DiagnosticCollector, policy: str) -> SourceElement | None:
    """Validate non-null class-set categorizers before emitting set axioms (DK-HO-04)."""
    data = element.data
    categorizer = data.get("categorizer")
    if categorizer is None:
        return None
    recovery = (
        "Categorizer and powertype assertions from this set omitted; "
        "independent constraints and mappings retained."
    )
    try:
        classifier = index.resolve(categorizer)
    except KeyError as exc:
        input_error(
            diagnostics, policy, "UNUSABLE_CATEGORIZER",
            f"Generalization set {data['id']!r} has an unusable categorizer reference {categorizer!r}: {exc}.",
            (element.location,), recovery,
        )
        return None
    cid = classifier.data.get("id")
    if classifier.data["type"] != "Class":
        input_error(
            diagnostics, policy, "UNUSABLE_CATEGORIZER",
            f"Generalization set {data['id']!r} has an unusable categorizer {cid!r}: "
            f"resolves to {classifier.data['type']!r}, not a Class.",
            (element.location, classifier.location), recovery,
        )
        return None
    if cid not in resources:
        input_error(
            diagnostics, policy, "UNUSABLE_CATEGORIZER",
            f"Generalization set {data['id']!r} has an unusable categorizer {cid!r}: "
            "Class has no generated local OWL class.",
            (element.location, classifier.location), recovery,
        )
        return None
    return classifier


def _emit_set(graph: Graph, index: SourceIndex, element: SourceElement, resources: dict[str, URIRef],
              edges: dict[str, tuple[SourceElement, SourceElement]], children: dict[str, set[str]],
              diagnostics: DiagnosticCollector, policy: str) -> None:
    data = element.data
    members = data.get("generalizations")
    if not isinstance(members, list):
        if "generalizations" not in data:
            condition = "is absent"
        elif members is None:
            condition = "is explicitly null"
        else:
            condition = "is not a JSON array"
        input_error(diagnostics, policy, "UNUSABLE_GENERALIZATION_SET_MEMBERSHIP",
                    f"The generalizations field {condition}.", (element.location,),
                    "Affected set contributes no axioms or classifications. Independently applicable mappings are retained.")
        return
    if not members:
        input_error(diagnostics, policy, "EMPTY_GENERALIZATION_SET",
                    "Generalization set has an explicitly empty generalizations array.", (element.location,),
                    "Empty set contributes no axioms; independently applicable mappings are retained.")
        return
    validate_boolean_flags(element, ("isComplete", "isDisjoint"), diagnostics, policy)
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
            # Validate each reference before counting its exact declaration ID
            # once within this set (DK-GEN-12).
            continue
        seen.add(identifier)
        if identifier not in edges:
            # The underlying transformation already produced its ERROR. Do not
            # manufacture another failure just to count surviving members.
            complete = False
        else:
            resolved.append(edges[identifier])
    specifics = {specific.data["id"]: specific for specific, _ in resolved}
    general_ids = {general.data["id"] for _, general in resolved}
    classifier = _resolve_categorizer(index, element, resources, diagnostics, policy)
    if data.get("isDisjoint") is True:
        for left, right in combinations(sorted(specifics), 2):
            graph.add((resources[left], OWL.disjointWith, resources[right]))
    if complete and data.get("isComplete") is True and len(general_ids) == 1:
        general = resolved[0][1]
        gid = general.data["id"]
        if len(seen) == 1:
            specific = resolved[0][0]
            graph.add((resources[gid], RDFS.subClassOf, resources[specific.data["id"]]))
            diagnostics.add("INFO", "SINGLETON_COMPLETENESS",
                            "Applying singleton completeness makes the generated general and specific classes "
                            "extensionally equivalent while their identifiers remain distinct.",
                            "Reverse subclass axiom emitted; existing forward subclass axiom retained.",
                            (element.location, general.location, specific.location))
        elif len(specifics) >= 2:
            expression, head = BNode(), BNode()
            Collection(graph, head, [resources[sid] for sid in sorted(specifics)])
            graph.add((expression, RDF.type, OWL.Class))
            graph.add((expression, OWL.unionOf, head))
            graph.add((resources[gid], RDFS.subClassOf, expression))
    if classifier is None:
        return
    cid = classifier.data["id"]
    extension = set(specifics)
    if complete and classifier.data.get("isPowertype") is True and len(general_ids) == 1:
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
                                  policy: str, kinds: dict[str, URIRef] | None = None) -> None:
    """Keep surviving specifics for disjointness even when their general fails."""
    from .diagnostics import _AbortConversion

    declared = {}
    mapped = set()
    abort_pending = False

    def deferred_error(code: str, message: str, sources: tuple, recovery: str) -> None:
        nonlocal abort_pending
        abort = policy != "best-effort"
        diagnostics.add(
            "ERROR", code, message,
            "Conversion aborted; no ontology is delivered." if abort else recovery,
            sources,
        )
        if abort:
            abort_pending = True

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
        if kinds is not None and kinds.get(sid) != kinds.get(gid):
            deferred_error(
                "INCOMPATIBLE_RELATION_GENERALIZATION",
                f"Relation generalization {identifier!r} has mixed owl:ObjectProperty and owl:DatatypeProperty kinds.",
                (element.location, specific.location, general.location),
                "Incompatible hierarchy edge omitted; independent properties and valid homogeneous mappings retained.",
            )
            continue
        graph.add((primaries[sid], RDFS.subPropertyOf, primaries[gid]))
        if sid in inverses and gid in inverses:
            graph.add((inverses[sid], RDFS.subPropertyOf, inverses[gid]))
        mapped.add(identifier)

    for element in index.elements:
        data = element.data
        if data["type"] != "GeneralizationSet" or not _relation_set(index, element):
            continue
        members = data["generalizations"]
        validate_boolean_flags(element, ("isComplete", "isDisjoint"), diagnostics, policy)
        categorizer = data.get("categorizer")
        if categorizer is not None:
            input_error(
                diagnostics,
                policy,
                "INAPPLICABLE_RELATION_CATEGORIZER",
                f"Relation generalization set {data['id']!r} has an inapplicable non-null categorizer {categorizer!r}.",
                (element.location,),
                "Categorizer and property-typing assertions from this set omitted; "
                "independent relation-set constraints and mappings retained.",
            )
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
                # Reference validation above still applies to every occurrence.
                continue
            seen.add(identifier)
            specific, general = declared[identifier]
            if specific is not None:
                sid = specific.data["id"]
                specific_ids.add(sid)
                if sid in primaries:
                    specifics[sid] = specific
            if identifier not in mapped:
                complete = False
            else:
                resolved.append((specific, general))
        if data.get("isDisjoint") is True:
            for sid, other in combinations(sorted(specifics), 2):
                if kinds is not None and kinds.get(sid) != kinds.get(other):
                    deferred_error(
                        "INCOMPATIBLE_RELATION_DISJOINTNESS",
                        f"Disjoint relation generalization set {data['id']!r} contains a cross-kind pair of owl:ObjectProperty and owl:DatatypeProperty ({sid!r}, {other!r}).",
                        (element.location, specifics[sid].location, specifics[other].location),
                        "Cross-kind disjointness pair omitted; valid homogeneous disjointness pairs and independent properties retained.",
                    )
                    continue
                graph.add((primaries[sid], OWL.propertyDisjointWith, primaries[other]))
                if sid in inverses and other in inverses:
                    graph.add((inverses[sid], OWL.propertyDisjointWith, inverses[other]))
        if data.get("isComplete") is not True:
            continue
        if complete and len(seen) == 1:
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

    if abort_pending:
        raise _AbortConversion
