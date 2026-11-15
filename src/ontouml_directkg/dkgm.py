"""Vocabulary delivery for the DKGM 0.1.1 core specified by DK-GEN-04."""

from rdflib import BNode, Graph, Namespace, URIRef
from rdflib.collection import Collection
from rdflib.namespace import OWL, RDF

from .diagnostics import DiagnosticCollector, SourceLocation

DKGM_ONTOLOGY = URIRef("https://w3id.org/directkg/vocab/dkgm")
DKGM = Namespace(f"{DKGM_ONTOLOGY}#")
DKGM_MODES = ("import", "embed", "none")
DKGM_PROPERTIES = {name: DKGM[name] for name in ("memberOf", "subCollectionOf", "subQuantityOf", "componentOf")}
DKGM_CHAINS = {
    DKGM.memberOf: (DKGM.memberOf, DKGM.subCollectionOf),
    DKGM.subCollectionOf: (DKGM.subCollectionOf, DKGM.subCollectionOf),
    DKGM.subQuantityOf: (DKGM.subQuantityOf, DKGM.subQuantityOf),
}


def emit_dkgm(graph: Graph, ontology: URIRef, mode: str,
              bridges: list[tuple[URIRef, SourceLocation]], diagnostics: DiagnosticCollector) -> None:
    """Supply the selected vocabulary using only bridges actually mapped."""
    if mode == "import":
        graph.add((ontology, OWL.imports, DKGM_ONTOLOGY))
        return

    if mode == "embed":
        for target in DKGM_PROPERTIES.values():
            graph.add((target, RDF.type, OWL.ObjectProperty))
        for conclusion, members in DKGM_CHAINS.items():
            head = BNode()
            Collection(graph, head, members)
            graph.add((conclusion, OWL.propertyChainAxiom, head))
        return

    for target, _ in bridges:
        graph.add((target, RDF.type, OWL.ObjectProperty))
    affected = tuple(source for target, source in bridges if target in DKGM_CHAINS)
    if affected:
        diagnostics.add("WARNING", "DKGM_CHAINS_OMITTED",
                        "The generic DKGM property chains are omitted from the generated ontology.",
                        "Consumers who need those entailments must supply the chain axioms or equivalent rules "
                        "to their reasoner.", affected)
