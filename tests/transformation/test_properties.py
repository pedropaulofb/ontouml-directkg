"""Shared property identity/qualification. Later waves add property references."""

import pytest
from rdflib import Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, XSD

from tests.support.rdf import one_subject


BASE = Namespace("https://example.test/model#")


def test_colliding_source_properties_stay_distinct_with_original_kinds(run):
    """Rules: DK-PROP-01, DK-PROP-02, DK-IRI-07, DK-IRI-09, DK-GEN-03, DK-CONF-02."""
    result = run("properties/collisions")
    assert result.outcome == "completed"
    resources = {identifier: one_subject(result.ontology, DCTERMS.identifier, Literal(identifier)) for identifier in ("a1", "a2", "a3", "eTarget")}
    assert len(set(resources.values())) == 4
    assert {resources[i] for i in ("a1", "a2", "eTarget")} == {BASE.code_Person_1, BASE.code_Person_2, BASE.code_Person_3}
    assert resources["a3"] == BASE.code_Organization
    assert not any(result.ontology.triples((BASE.code, None, None)))
    assert not any(result.ontology.triples((BASE.code_Person, None, None)))
    assert (resources["a1"], RDF.type, OWL.DatatypeProperty) in result.ontology
    assert (resources["a2"], RDF.type, OWL.ObjectProperty) in result.ontology
    assert (resources["a3"], RDF.type, OWL.DatatypeProperty) in result.ontology
    assert (resources["eTarget"], RDF.type, OWL.ObjectProperty) in result.ontology
    assert set(result.ontology.objects(resources["a1"], RDFS.domain)) == {BASE.Person}
    assert set(result.ontology.objects(resources["a1"], RDFS.range)) == {XSD.int}
    assert set(result.ontology.objects(resources["a2"], RDFS.range)) == {BASE.Address}
    assert set(result.ontology.objects(resources["a2"], RDFS.domain)) == {BASE.Person}
    assert set(result.ontology.objects(resources["a3"], RDFS.domain)) == {BASE.Organization}
    assert not list(result.ontology.objects(resources["a3"], RDFS.range))
    assert set(result.ontology.objects(resources["eTarget"], RDFS.domain)) == {BASE.Person}
    assert set(result.ontology.objects(resources["eTarget"], RDFS.range)) == {BASE.Organization}
    assert not list(result.ontology.triples((None, OWL.unionOf, None)))


@pytest.mark.parametrize("input_policy", ["strict", "tolerant", "best-effort"])
def test_owner_qualification_uses_escaped_fallback_before_class_suffixes(run, input_policy):
    """Rules: DK-PROP-02, DK-IRI-04, DK-IRI-05, DK-IRI-07, DK-IRI-09, DK-DIAG-01, DK-CONF-02."""
    result = run("properties/unnamed_owner", input_policy=input_policy)
    assert result.outcome == "completed"
    first_class = one_subject(result.ontology, DCTERMS.identifier, Literal("C_1"))
    other_claim = one_subject(result.ontology, DCTERMS.identifier, Literal("cClaim"))
    assert {first_class, other_claim} == {BASE.unnamedClass_C_x5F1_1, BASE.unnamedClass_C_x5F1_2}
    property_one = one_subject(result.ontology, DCTERMS.identifier, Literal("p1"))
    property_two = one_subject(result.ontology, DCTERMS.identifier, Literal("p2"))
    assert property_one == BASE.code_unnamedClass_C_x5F1
    assert property_two == BASE.code_Other
    assert (property_one, RDFS.domain, first_class) in result.ontology
    assert (property_one, RDF.type, OWL.DatatypeProperty) in result.ontology
    assert not any(d.kind == "owner_qualification" for d in result.diagnostics)
    assert any(d.kind == "missing_name" and d.severity == "WARNING" and "C_1" in d.source_ids for d in result.diagnostics)


def test_collision_mapping_is_repeatable_without_fixed_suffix_allocation(run):
    """Rules: DK-PROP-01, DK-PROP-02, DK-IRI-07, DK-CONF-01, DK-CONF-02."""
    first = run("properties/collisions")
    again = run("properties/collisions")
    assert first.outcome == again.outcome == "completed"
    for identifier in ("a1", "a2", "a3", "eTarget"):
        assert one_subject(first.ontology, DCTERMS.identifier, Literal(identifier)) == one_subject(again.ontology, DCTERMS.identifier, Literal(identifier))
