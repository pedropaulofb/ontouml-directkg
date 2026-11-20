"""RD-17's five additions, gated after the established constraint policies."""

from collections import defaultdict
from itertools import product

from rdflib import Graph
from rdflib.namespace import OWL, RDF

from .chains import _non_simple
from .dkgm import DKGM_CHAINS, DKGM_ONTOLOGY
from .properties import PropertyExpressions
from .relations import Relation

_CHARACTERISTICS = {
    "characterization": OWL.AsymmetricProperty,
    "mediation": OWL.AsymmetricProperty,
    "participational": OWL.AsymmetricProperty,
    "externalDependence": OWL.IrreflexiveProperty,
}


def emit_relation_axioms(graph: Graph, relations: tuple[Relation, ...],
                         expressions: PropertyExpressions) -> None:
    """Add only individually compatible characteristics and aligned pairs.

    Local chain conclusions include the embedded DKGM core when present.
    The stable DKGM import adds its known chain conclusions to the analysis.
    """
    composite = {OWL.topObjectProperty, OWL.bottomObjectProperty}
    composite.update(graph.subjects(OWL.propertyChainAxiom))
    composite.update(graph.subjects(RDF.type, OWL.TransitiveProperty))
    if (None, OWL.imports, DKGM_ONTOLOGY) in graph:
        composite.update(DKGM_CHAINS)
    non_simple = _non_simple(graph, composite)

    characterizations, external_dependencies = defaultdict(list), defaultdict(list)
    for relation in relations:
        if relation.kind != OWL.ObjectProperty:
            continue
        stereotype = relation.source.data.get("stereotype")
        primary = expressions.resources[relation.target_end.data["id"]]
        characteristic = _CHARACTERISTICS.get(stereotype)
        if characteristic is not None and primary not in non_simple:
            graph.add((primary, RDF.type, characteristic))
        if stereotype not in {"characterization", "externalDependence"}:
            continue
        # Reuse explicit feature recognition, without searching inheritance or
        # names. Two feature-typed ends (including a self-relation) are ambiguous.
        features = [(endpoint.data["id"], end)
                    for endpoint, end in ((relation.domain, relation.target_end),
                                          (relation.range, relation.source_end))
                    if endpoint.data.get("stereotype") in {"mode", "quality"}]
        if len(features) != 1:
            continue
        feature, end = features[0]
        group = characterizations if stereotype == "characterization" else external_dependencies
        group[feature].append((primary, end))

    for feature, characterizations_of_feature in characterizations.items():
        for left, right in product(characterizations_of_feature,
                                   external_dependencies.get(feature, ())):
            # A primary and its inverse have the same simplicity status. Check
            # before creating any anonymous expression solely for this addition.
            if left[0] in non_simple or right[0] in non_simple:
                continue
            graph.add((expressions.resolve(left[1]), OWL.propertyDisjointWith,
                       expressions.resolve(right[1])))
