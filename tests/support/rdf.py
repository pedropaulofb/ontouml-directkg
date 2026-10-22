"""Generic RDF assertions; no DirectKG transformation/expectation logic."""

from pathlib import Path

from rdflib import BNode, Graph
from rdflib.namespace import RDF
from rdflib.compare import graph_diff, isomorphic, to_isomorphic


def load_graph(path: Path) -> Graph:
    return Graph().parse(path, format="turtle")


def assert_graph_equal(actual: Graph, expected: Graph) -> None:
    """RDF graph equality modulo blank-node identifiers, not OWL entailment."""
    if not isomorphic(actual, expected):
        _, extra, missing = graph_diff(to_isomorphic(actual), to_isomorphic(expected))
        raise AssertionError(
            "RDF graphs differ\nUnexpected:\n"
            + extra.serialize(format="turtle")
            + "\nMissing:\n"
            + missing.serialize(format="turtle")
        )


def assert_contains(actual: Graph, expected: Graph) -> None:
    """An explicitly partial expectation of ground triples.

    Blank-node subgraph matching is not supplied by simple RDF membership.
    Reject that misuse instead of accidentally comparing blank-node labels.
    """
    if any(isinstance(term, BNode) for triple in expected for term in triple):
        raise ValueError("Use an isomorphic graph comparison for blank-node expectations")
    missing = set(expected) - set(actual)
    assert not missing, "Missing asserted triples: " + repr(sorted(missing, key=str))


def one_subject(graph: Graph, predicate, obj):
    values = set(graph.subjects(predicate, obj))
    assert len(values) == 1, (predicate, obj, values)
    return next(iter(values))


def one_object(graph: Graph, subject, predicate):
    values = set(graph.objects(subject, predicate))
    assert len(values) == 1, (subject, predicate, values)
    return next(iter(values))


def rdf_list(graph: Graph, head):
    """Read a well-formed finite RDF collection, retaining its actual order.

    Callers decide whether order is meaningful. Reject broken, branching and
    cyclic lists instead of silently returning a convenient partial result.
    """
    values, seen = [], set()
    while head != RDF.nil:
        assert head not in seen, "Cyclic RDF collection"
        seen.add(head)
        values.append(one_object(graph, head, RDF.first))
        head = one_object(graph, head, RDF.rest)
    return tuple(values)


def assert_selected_equal(actual: Graph, expected: Graph, predicates, unordered_predicates=(),
                          *, subjects=None, type_objects=None) -> None:
    """Compare explicitly selected graph predicates, allowing named-node pairs.

    Callers own the selection and must justify any unordered pair treatment.
    Optional subject/type-object selections limit a comparison to the promised
    mapping, leaving unrelated metadata resources and their types unconstrained.
    These selections do not follow blank-node edges or infer missing triples.
    This helper has no vocabulary-specific defaults or transformation rules.
    It is not a reasoner or a replacement for whole-graph isomorphism.
    """
    def selected(graph):
        projected = Graph()
        for subject, predicate, obj in graph:
            if subjects is not None and subject not in subjects:
                continue
            if predicate == RDF.type and type_objects is not None and obj not in type_objects:
                continue
            if predicate in unordered_predicates:
                if isinstance(subject, BNode) or isinstance(obj, BNode):
                    raise ValueError("Unordered pair projection requires named endpoints")
                first, second = sorted((subject, obj), key=str)
                projected.add((first, predicate, second))
            elif predicate in predicates:
                projected.add((subject, predicate, obj))
        return projected
    assert_graph_equal(selected(actual), selected(expected))
