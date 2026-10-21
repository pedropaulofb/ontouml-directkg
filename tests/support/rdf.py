"""Generic RDF assertions; no DirectKG transformation/expectation logic."""

from pathlib import Path

from rdflib import BNode, Graph
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


def assert_selected_equal(actual: Graph, expected: Graph, predicates, unordered_predicates=()) -> None:
    """Compare explicitly selected graph predicates, allowing named-node pairs.

    Callers own the selection and must justify any unordered pair treatment.
    This helper has no vocabulary-specific defaults or transformation rules.
    It is not a reasoner or a replacement for whole-graph isomorphism.
    """
    def selected(graph):
        projected = Graph()
        for subject, predicate, obj in graph:
            if predicate in unordered_predicates:
                if isinstance(subject, BNode) or isinstance(obj, BNode):
                    raise ValueError("Unordered pair projection requires named endpoints")
                first, second = sorted((subject, obj), key=str)
                projected.add((first, predicate, second))
            elif predicate in predicates:
                projected.add((subject, predicate, obj))
        return projected
    assert_graph_equal(selected(actual), selected(expected))
