"""Punned class/individual identity, categorizers, and powertype extension."""

import pytest
from rdflib import Literal, Namespace
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS

from tests.support.data import source_element, write_input
from tests.support.invocation import diagnostic_signatures
from tests.support.rdf import assert_contains, assert_graph_equal, load_graph


BASE = Namespace("https://example.test/model#")
POLICIES = ["strict", "tolerant", "best-effort"]
MODELED = {BASE.cBase, BASE.cOne, BASE.cTwo, BASE.cOutside, BASE.cDeep,
           BASE.cCategorizer, BASE.cOtherCategorizer}


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("powertype", [False, None, True], ids=["ordinary_false", "ordinary_null", "powertype_true"])
def test_categorizers_pun_same_iris_and_materialize_only_applicable_extension(run, source_json, source_path, tmp_path, input_policy, powertype):
    """Rules: DK-HO-01, DK-HO-02, DK-HO-03, DK-HO-04, DK-CLS-02, DK-GEN-02.

    The second categorizer classifies One as well, despite ultimate-sortals'
    disjointness. These assertions inspect explicit class and individual facts;
    no reasoner is used to manufacture powertype membership from subclasses.
    """
    document = source_json("higher_order/categorizers")
    source_element(document, "cCategorizer")["isPowertype"] = powertype
    result = run(path=write_input(tmp_path, document), iri_strategy="id", input_policy=input_policy)
    assert result.outcome == "completed"
    assert_contains(result.ontology, load_graph(source_path("higher_order/categorizers", "expected.ttl")))
    extension = {BASE.cOne, BASE.cTwo}
    if powertype is True:
        extension |= {BASE.cBase, BASE.cOutside, BASE.cDeep}
    assert set(result.ontology.subjects(RDF.type, BASE.cCategorizer)) == extension
    assert set(result.ontology.subjects(RDF.type, BASE.cOtherCategorizer)) == {BASE.cOne}
    assert set(result.ontology.subjects(RDF.type, OWL.NamedIndividual)) == extension
    assert set(result.ontology.subjects(RDF.type, OWL.Class)) == MODELED
    for target in extension:
        assert (target, RDF.type, OWL.Class) in result.ontology
        assert (target, RDF.type, OWL.NamedIndividual) in result.ontology
    # No separate representation resource can carry any of these classifications.
    for categorizer in (BASE.cCategorizer, BASE.cOtherCategorizer):
        assert set(result.ontology.subjects(RDF.type, categorizer)) <= MODELED
    assert ((BASE.cCategorizer, OWL.disjointWith, BASE.cOtherCategorizer) in result.ontology or
            (BASE.cOtherCategorizer, OWL.disjointWith, BASE.cCategorizer) in result.ontology)
    assert not any(d.kind == "semantic_validation" or d.severity in {"WARNING", "ERROR"} for d in result.diagnostics)
    assert not any(d.kind == "singleton_completeness" for d in result.diagnostics)


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("powertype", [False, True], ids=["ordinary", "powertype"])
def test_restricted_to_order_and_stereotype_do_not_validate_higher_order_assertions(run, source_json, tmp_path, input_policy, powertype):
    """Rules: DK-HO-01, DK-HO-02, DK-HO-03, DK-HO-04, DK-CLS-01, DK-CLS-05, DK-GEN-02.

    Event as categorizer and a lower numeric order are intentionally not checked
    for semantic appropriateness. No malformed structural input is introduced.
    """
    document = source_json("higher_order/categorizers")
    categorizer = source_element(document, "cCategorizer")
    categorizer.update(stereotype="event", isPowertype=powertype, order="0")
    source_element(document, "cBase")["order"] = "12"
    baseline = run(path=write_input(tmp_path, document, "without_nature.json"), iri_strategy="id", input_policy=input_policy)
    for identifier in ("cBase", "cOne", "cTwo", "cOutside", "cDeep", "cCategorizer", "cOtherCategorizer"):
        source_element(document, identifier)["restrictedTo"] = ["situation"]
    result = run(path=write_input(tmp_path, document), iri_strategy="id", input_policy=input_policy)
    assert baseline.outcome == result.outcome == "completed"
    extension = {BASE.cOne, BASE.cTwo} | ({BASE.cBase, BASE.cOutside, BASE.cDeep} if powertype else set())
    assert set(result.ontology.subjects(RDF.type, BASE.cCategorizer)) == extension
    assert set(result.ontology.subjects(RDF.type, BASE.cOtherCategorizer)) == {BASE.cOne}
    assert (BASE.cCategorizer, RDFS.comment, Literal("OntoUML classifier order: 0.", lang="en")) in result.ontology
    assert (BASE.cBase, RDFS.comment, Literal("OntoUML classifier order: 12.", lang="en")) in result.ontology
    assert_graph_equal(result.ontology, baseline.ontology)
    assert diagnostic_signatures(result.diagnostics) == diagnostic_signatures(baseline.diagnostics)
    assert not any(d.kind in {"unknown_information", "restricted_to", "semantic_validation"} or d.severity == "ERROR" for d in result.diagnostics)


@pytest.mark.parametrize("iri_strategy", ["name", "id"])
def test_punning_identity_is_the_same_under_both_iri_strategies(run, iri_strategy):
    """Rules: DK-HO-01, DK-HO-02, DK-IRI-02, DK-IRI-09."""
    result = run("higher_order/categorizers", iri_strategy=iri_strategy)
    assert result.outcome == "completed"
    one = BASE.cOne if iri_strategy == "id" else BASE.One
    categorizer = BASE.cCategorizer if iri_strategy == "id" else BASE.Categorizer
    other = BASE.cOtherCategorizer if iri_strategy == "id" else BASE.OtherCategorizer
    assert {OWL.Class, OWL.NamedIndividual, categorizer, other} <= set(result.ontology.objects(one, RDF.type))
    assert set(result.ontology.subjects(DCTERMS.identifier, Literal("cOne"))) == {one}
    assert set(result.ontology.subjects(RDFS.label, Literal("One"))) == {one}
