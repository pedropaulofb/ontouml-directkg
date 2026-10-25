"""Explicit class generalizations, set constraints and categorizer punning."""

from collections import defaultdict
from itertools import combinations

from rdflib import BNode, Graph, URIRef
from rdflib.collection import Collection
from rdflib.namespace import OWL, RDF, RDFS

from .diagnostics import DiagnosticCollector
from .source import SourceElement, SourceIndex, input_error


def emit_generalizations(graph: Graph, index: SourceIndex, resources: dict[str, URIRef],
                         diagnostics: DiagnosticCollector, policy: str) -> None:
    """Keep source edges separate from coverage edges and powertype traversal."""
    edges: dict[str, tuple[SourceElement, SourceElement]] = {}
    children: dict[str, set[str]] = defaultdict(set)
    for element in index.elements:
        if element.data["type"] != "Generalization":
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
        if element.data["type"] == "GeneralizationSet":
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
