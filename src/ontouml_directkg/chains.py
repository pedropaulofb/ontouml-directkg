"""Explicit material grounding chains and their targeted constraint treatment.

Matching uses source identifiers and successfully transformable relations only.
Simplicity propagation inspects generated hierarchy/inverse axioms without
materializing inferred edges or making a general OWL-profile claim.
"""

from collections import defaultdict

from rdflib import BNode, Graph, URIRef
from rdflib.collection import Collection
from rdflib.namespace import OWL, RDFS

from .diagnostics import DiagnosticCollector, SourceLocation
from .properties import Attribute, PropertyExpressions
from .relations import Relation
from .source import SourceElement


def _ambiguity(material: Relation, grounds: tuple[SourceElement, ...],
               diagnostics: DiagnosticCollector, reason: str) -> None:
    diagnostics.add("WARNING", "MATERIAL_CHAIN_AMBIGUITY", reason,
                    "Affected material-property chain omitted; independently applicable properties, "
                    "inverses and constraints are retained unless affected by another emitted chain.",
                    (material.source.location,) + tuple(ground.location for ground in grounds))


def _non_simple(graph: Graph, conclusions: set[URIRef]) -> set[URIRef | BNode]:
    """Propagate upwards and across inverses, never downwards or from bodies."""
    successors = defaultdict(set)
    for child, parent in graph.subject_objects(RDFS.subPropertyOf):
        successors[child].add(parent)
    for inverse, primary in graph.subject_objects(OWL.inverseOf):
        successors[inverse].add(primary)
        successors[primary].add(inverse)
    affected = set(conclusions)
    pending = list(conclusions)
    while pending:
        for expression in successors[pending.pop()] - affected:
            affected.add(expression)
            pending.append(expression)
    return affected


def _omit_constraints(graph: Graph, affected: set[URIRef | BNode]
                      ) -> tuple[set[URIRef | BNode], bool, bool]:
    """Remove only generated necessary cardinalities and affected disjoint pairs."""
    cardinalities = {OWL.cardinality, OWL.minCardinality, OWL.maxCardinality}
    omitted = set()
    counts_omitted = disjointness_omitted = False
    for restriction, expression in list(graph.subject_objects(OWL.onProperty)):
        if expression in affected and any((restriction, predicate, None) in graph
                                          for predicate in cardinalities):
            omitted.add(expression)
            counts_omitted = True
            graph.remove((None, RDFS.subClassOf, restriction))
            graph.remove((restriction, None, None))
    for left, right in list(graph.subject_objects(OWL.propertyDisjointWith)):
        if left in affected or right in affected:
            omitted.update((left, right))
            disjointness_omitted = True
            graph.remove((left, OWL.propertyDisjointWith, right))
    # A reverse expression used by an omitted restriction may still be needed
    # by an ordered chain or explicit property reference. Preserve such uses.
    for expression in affected:
        if (isinstance(expression, BNode) and (expression, OWL.inverseOf, None) in graph
                and not any(graph.triples((None, None, expression)))
                and all(predicate == OWL.inverseOf
                        for _, predicate, _ in graph.triples((expression, None, None)))):
            graph.remove((expression, None, None))
    return omitted, counts_omitted, disjointness_omitted


def _source_locations(nodes: set[URIRef | BNode], relations: tuple[Relation, ...],
                      attributes: tuple[Attribute, ...], expressions: PropertyExpressions
                      ) -> tuple[SourceLocation, ...]:
    locations = {}
    for relation in relations:
        primary = expressions.resources[relation.target_end.data["id"]]
        inverse = expressions.inverses.get(relation.source_end.data["id"])
        anonymous = expressions.anonymous.get(primary)
        if any(node in nodes for node in (primary, inverse, anonymous) if node is not None):
            for source in (relation.source, relation.source_end, relation.target_end):
                locations[source.path] = source.location
    for attribute in attributes:
        if expressions.resources[attribute.source.data["id"]] in nodes:
            for source in (attribute.source, attribute.owner):
                locations[source.path] = source.location
    return tuple(locations[path] for path in sorted(locations))


def emit_material_chains(graph: Graph, relations: tuple[Relation, ...],
                         groundings: dict[str, tuple[SourceElement, ...]],
                         attributes: tuple[Attribute, ...], expressions: PropertyExpressions,
                         mode: str, diagnostics: DiagnosticCollector) -> None:
    """Emit eligible ordered paths, then apply the requested constraint policy."""
    if mode == "none":
        return
    matches = defaultdict(list)
    for relation in relations:
        key = (relation.source.data.get("stereotype"),
               frozenset((relation.domain.data["id"], relation.range.data["id"])))
        matches[key].append(relation)

    conclusions = set()
    for material in relations:
        if material.source.data.get("stereotype") != "material":
            continue
        grounds = groundings.get(material.source.data["id"], ())
        if not grounds:
            continue
        start, finish = material.domain.data["id"], material.range.data["id"]
        if start == finish:
            _ambiguity(material, grounds, diagnostics,
                       "Same-class material endpoints cannot be assigned uniquely to the grounding relations' "
                       "semantic roles; distinct association-end IDs or roles do not resolve the ambiguity.")
            continue
        paths, mode_paths = [], []
        mode_ambiguous = False
        for ground in grounds:
            ground_id = ground.data["id"]
            relator = ground.data["stereotype"] == "relator"
            if relator:
                if any(endpoint.data.get("stereotype") == "relator"
                       for endpoint in (material.domain, material.range)):
                    continue
                stereotypes = (("mediation", "mediation"),)
            else:
                stereotypes = (("characterization", "externalDependence"),
                               ("externalDependence", "characterization"))
            candidates = []
            ambiguous = False
            for first_kind, second_kind in stereotypes:
                first = matches[first_kind, frozenset((ground_id, start))]
                second = matches[second_kind, frozenset((ground_id, finish))]
                if not first or not second:
                    continue
                if len(first) > 1 or len(second) > 1:
                    ambiguous = True
                elif first[0] is not second[0]:
                    candidates.append((first[0], second[0], ground_id))
            if relator:
                if ambiguous:
                    _ambiguity(material, (ground,), diagnostics,
                               "Multiple matching mediations prevent unique correspondence against this grounding relator.")
                else:
                    paths.extend(candidates)
            else:
                mode_ambiguous |= ambiguous
                mode_paths.extend(candidates)
        if mode_ambiguous or len(mode_paths) > 1:
            _ambiguity(material, tuple(ground for ground in grounds if ground.data["stereotype"] == "mode"),
                       diagnostics, "Multiple matching grounding relations or complete mode patterns prevent unique chain correspondence.")
        else:
            paths.extend(mode_paths)
        for first, second, middle in paths:
            steps = []
            for relation, origin in ((first, start), (second, middle)):
                primary = expressions.resources[relation.target_end.data["id"]]
                steps.append(primary if relation.domain.data["id"] == origin
                             else expressions.anonymous_inverse(primary))
            conclusion = expressions.resources[material.target_end.data["id"]]
            head = BNode()
            Collection(graph, head, steps)
            graph.add((conclusion, OWL.propertyChainAxiom, head))
            conclusions.add(conclusion)

    if not conclusions:
        return
    omitted = set()
    if mode == "omit-conflicting-constraints":
        omitted, counts, disjointness = _omit_constraints(graph, _non_simple(graph, conclusions))
        categories = []
        if counts:
            categories.append("multiplicity-derived cardinality restrictions")
        if disjointness:
            categories.append("property-disjointness axioms")
        effect = ("Omission policy applied. Omitted affected " + " and ".join(categories) + "."
                  if categories else "Omission policy applied; no cardinality or property-disjointness constraints required omission.")
        message = ("Emitted material-property chains use the omit-conflicting-constraints policy. "
                   "Removing these known simplicity conflicts does not guarantee OWL 2 DL conformance.")
    else:
        message = ("Emitted material-property chains preserve applicable simplicity-dependent cardinality and "
                   "property-disjointness constraints; their combination may place the output outside OWL 2 DL.")
        effect = "Applicable constraints preserved; OWL 2 DL conformance is not guaranteed."
    diagnostics.add("INFO", "MATERIAL_CHAIN_COMPATIBILITY", message, effect,
                    _source_locations(conclusions | omitted, relations, attributes, expressions))
