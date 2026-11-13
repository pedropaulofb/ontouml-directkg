"""Shared DK-GEN-04 assertions for the transformed DKGM contribution."""

from pathlib import Path
from urllib.parse import urlsplit

from rdflib import Namespace, URIRef
from rdflib.namespace import OWL, RDF, RDFS

from tests.support.rdf import load_graph, one_object, property_chains


DKGM_ONTOLOGY = URIRef('https://w3id.org/directkg/vocab/dkgm')
DKGM = Namespace(f'{DKGM_ONTOLOGY}#')
DKGM_STEREOTYPES = ('memberOf', 'subCollectionOf', 'subQuantityOf', 'componentOf')
DKGM_CHAINS = {
    DKGM.memberOf: (DKGM.memberOf, DKGM.subCollectionOf),
    DKGM.subCollectionOf: (DKGM.subCollectionOf, DKGM.subCollectionOf),
    DKGM.subQuantityOf: (DKGM.subQuantityOf, DKGM.subQuantityOf),
}
DKGM_CORE = Path(__file__).resolve().parents[2] / 'vocabulary/versioned/dkgm-vocabulary-v0.1.1.ttl'


def _is_dkgm_resource(node):
    return isinstance(node, URIRef) and (
        node == DKGM_ONTOLOGY or str(node).startswith((str(DKGM), f'{DKGM_ONTOLOGY}/'))
    )


def _is_gufo_resource(node):
    return isinstance(node, URIRef) and 'purl.org/nemo/gufo' in str(node).casefold()


def _is_dkgm_import(node):
    return _is_dkgm_resource(node) or (
        isinstance(node, URIRef) and urlsplit(str(node)).path.rsplit('/', 1)[-1].startswith('dkgm-vocabulary')
    )


def assert_dkgm_vocabulary(graph, ontology, mode, *, bridges=()):
    """Check the selected vocabulary contribution and explicit source bridges."""
    assert (ontology, RDF.type, OWL.Ontology) in graph
    imports = {(s, o) for s, o in graph.subject_objects(OWL.imports) if _is_dkgm_import(o)}
    assert imports == ({(ontology, DKGM_ONTOLOGY)} if mode == 'import' else set())
    assert not any(_is_gufo_resource(o) for o in graph.objects(None, OWL.imports))

    assert {(s, o) for s, o in graph.subject_objects(RDFS.subPropertyOf)
            if _is_dkgm_resource(o)} == set(bridges)
    for predicate in (OWL.equivalentProperty, OWL.propertyDisjointWith, OWL.inverseOf, OWL.sameAs,
                      RDFS.domain, RDFS.range, OWL.onProperty):
        assert not any(_is_dkgm_resource(o) for o in graph.objects(None, predicate)), predicate
    assert not any(_is_dkgm_resource(p) for p in graph.predicates())
    if mode == 'embed':
        terms = {DKGM[name] for name in DKGM_STEREOTYPES}
    elif mode == 'none':
        terms = {target for _, target in bridges}
    else:
        terms = set()
    assert {s for s in graph.subjects() if _is_dkgm_resource(s)} == terms
    core_list_nodes = set()
    for term in terms:
        expected = DKGM_CHAINS.get(term) if mode == 'embed' else None
        assert property_chains(graph, term) == ({expected} if expected else set())
        for head in graph.objects(term, OWL.propertyChainAxiom):
            node = head
            while node != RDF.nil:
                core_list_nodes.add(node)
                assert {p for p, _ in graph.predicate_objects(node)} <= {RDF.first, RDF.rest, RDF.type}
                assert set(graph.objects(node, RDF.type)) <= {RDF.List}
                node = one_object(graph, node, RDF.rest)
        assert {p for p, _ in graph.predicate_objects(term)} <= {RDF.type, OWL.propertyChainAxiom}
        assert set(graph.objects(term, RDF.type)) == {OWL.ObjectProperty}
    assert all(node in core_list_nodes for node, member in graph.subject_objects(RDF.first)
               if _is_dkgm_resource(member))
    # A Turtle round trip may write a shared list tail as a separate list.
    # Check chain members as well as incoming edges to the core list nodes.
    for subject in set(graph.subjects(OWL.propertyChainAxiom)) - DKGM_CHAINS.keys():
        chains = property_chains(graph, subject)
        members = {expression[1] if isinstance(expression, tuple) else expression
                   for chain in chains for expression in chain}
        assert not any(_is_dkgm_resource(member) for member in members), (
            'Unexpected DKGM chain conclusion', subject
        )
    for node in core_list_nodes:
        for subject, predicate in graph.subject_predicates(node):
            assert ((predicate == OWL.propertyChainAxiom and subject in DKGM_CHAINS)
                    or (predicate == RDF.rest and subject in core_list_nodes)), (
                'Unexpected reference to a DKGM chain list', (subject, predicate, node)
            )

    if mode in {'embed', 'none'}:
        vocabulary = load_graph(DKGM_CORE)
        vocabulary_resources = {DKGM[name] for name in DKGM_STEREOTYPES} | {DKGM_ONTOLOGY}
        metadata = {(p, o) for term in vocabulary_resources
                    for p, o in vocabulary.predicate_objects(term) if p not in {RDF.type, OWL.propertyChainAxiom}}
        assert not any((p, o) in metadata for _, p, o in graph), 'Copied vocabulary metadata'
        assert not any(triple in graph for triple in vocabulary
                       if isinstance(triple[0], URIRef) and triple[0] not in vocabulary_resources)
