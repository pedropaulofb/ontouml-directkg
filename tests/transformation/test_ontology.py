"""General domain output and source-container omission checks."""

from urllib.parse import urlsplit

import pytest
from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, XSD

from tests.support.invocation import diagnostic_signatures
from tests.support.data import write_input
from tests.support.rdf import assert_contains, assert_graph_equal, assert_selected_equal, load_graph


BASE = Namespace("https://example.test/model#")
POLICIES = ["strict", "tolerant", "best-effort"]
FIXED_PREDICATES = {RDF.type, RDFS.domain, RDFS.range, RDFS.label, DCTERMS.identifier,
                    RDFS.subClassOf, RDFS.subPropertyOf, OWL.inverseOf,
                    OWL.equivalentClass, OWL.equivalentProperty, OWL.propertyChainAxiom,
                    OWL.propertyDisjointWith}


def test_rdf_helper_checks_graph_identity_and_ordered_lists():
    """Harness check only; this is not coverage of a DirectKG obligation."""
    first = Graph().parse(data='@prefix : <urn:test:> . :s :p [ :q "same" ] .', format="turtle")
    second = Graph().parse(data='@prefix other: <urn:test:> . _:renamed other:q "same" . other:s other:p _:renamed .', format="turtle")
    assert_graph_equal(first, second)
    wrong_literal = Graph().parse(data='@prefix : <urn:test:> . :s :p [ :q "different" ] .', format="turtle")
    with pytest.raises(AssertionError):
        assert_graph_equal(first, wrong_literal)
    forward = Graph().parse(data='@prefix : <urn:test:> . :chain :steps (:a :b) .', format="turtle")
    backward = Graph().parse(data='@prefix : <urn:test:> . :chain :steps (:b :a) .', format="turtle")
    with pytest.raises(AssertionError):
        assert_graph_equal(forward, backward)
    with pytest.raises(ValueError):
        assert_contains(first, second)
    ground = Graph().parse(data='@prefix : <urn:test:> . :a :b :c .', format="turtle")
    with pytest.raises(AssertionError):
        assert_contains(first, ground)
    selected = URIRef("urn:test:fixed")
    flexible = URIRef("urn:test:optional")
    left = Graph().parse(data='<urn:test:s> <urn:test:fixed> "same"; <urn:test:optional> "one".', format="turtle")
    right = Graph().parse(data='<urn:test:s> <urn:test:fixed> "same"; <urn:test:optional> "two".', format="turtle")
    assert_selected_equal(left, right, {selected})
    with pytest.raises(AssertionError):
        assert_selected_equal(left, right, {selected, flexible})
    pair = Graph().parse(data='<urn:test:a> <urn:test:pair> <urn:test:b>.', format="turtle")
    reciprocal = Graph().parse(data='<urn:test:b> <urn:test:pair> <urn:test:a>.', format="turtle")
    assert_selected_equal(pair, reciprocal, set(), {URIRef("urn:test:pair")})


def test_core_asserted_domain_graph(run, source_path):
    """Rules: DK-GEN-01, DK-GEN-03, DK-IRI-02, DK-IRI-06, DK-IRI-09.

    The stored graph is a partial set of fixed ground triples under ID mode,
    not a whole-graph equality claim. Required comments and the import remain
    present in the actual graph; they are not stripped for comparison.
    """
    result = run(iri_strategy="id")
    assert result.outcome == "completed"
    assert result.configuration_error is None
    assert_contains(result.ontology, load_graph(source_path("shared/core_model", "expected.ttl")))
    for property_iri in (BASE.aAge, BASE.aNote, BASE.aAddress, BASE.eTarget, BASE.eSource):
        assert len(set(result.ontology.objects(property_iri, RDFS.domain))) == 1
    assert not list(result.ontology.objects(BASE.aNote, RDFS.range))
    for omitted in (BASE.projectOne, BASE.projectOne_root, BASE.rWorks, BASE.dInt):
        assert not any(result.ontology.triples((omitted, None, None)))
    assert not list(result.ontology.objects(XSD.int, RDFS.comment))
    assert not any(isinstance(t, URIRef) and (str(t).startswith("http://purl.org/nemo/gufo") or str(t).startswith("https://w3id.org/ontouml")) for triple in result.ontology for t in triple)


@pytest.mark.parametrize("input_policy", POLICIES)
def test_generated_ontology_has_import_even_without_mereology(run, input_policy):
    """Rules: DK-GEN-01, DK-GEN-04, DK-IRI-01.

    Only import existence and its no-fragment boundary are asserted. The exact
    stable DKGM target remains blocked; an arbitrary import is not certified
    as the accepted DKGM URI by this test.
    """
    result = run("shared/base_iri", input_policy=input_policy)
    assert result.outcome == "completed"
    ontology = URIRef("https://example.test/model")
    assert (ontology, RDF.type, OWL.Ontology) in result.ontology
    imports = set(result.ontology.objects(ontology, OWL.imports))
    assert imports
    assert any(isinstance(target, URIRef) and urlsplit(str(target)).scheme and not urlsplit(str(target)).fragment and not str(target).endswith("#") for target in imports)


@pytest.mark.parametrize("filename", ["input.json", "duplicate_views.json"])
@pytest.mark.parametrize("input_policy", POLICIES)
def test_organization_and_views_do_not_change_domain_output(run, filename, input_policy):
    """Rules: DK-GEN-01, DK-GEN-06, DK-IRI-09, DK-DIAG-05; §3.4 duplicate-ID scope."""
    plain = run(input_policy=input_policy)
    decorated = run("ontology/organization", filename, input_policy=input_policy)
    assert plain.outcome == decorated.outcome == "completed"
    assert (BASE.Person, RDF.type, OWL.Class) in plain.ontology
    # Compare fixed domain output, not optional metadata or unspecified generated
    # comment text across executions. Disjointness permits either pair direction.
    assert_selected_equal(decorated.ontology, plain.ontology, FIXED_PREDICATES, {OWL.disjointWith})
    assert diagnostic_signatures(decorated.diagnostics) == diagnostic_signatures(plain.diagnostics)
    assert not any(d.kind in {"omitted_package", "omitted_diagram", "unknown_information", "duplicate_id"} for d in decorated.diagnostics)
    for triple in decorated.ontology:
        for term in triple:
            assert "sentinel" not in str(term).casefold()
    for identifier in ("pkgNested", "pkgInner", "diagramOne", "viewOne", "shapeOne", "viewTwo", "shapeTwo", "viewOrg", "shapeOrg", "viewRelation", "pathRelation"):
        assert not list(decorated.ontology.subjects(DCTERMS.identifier, Literal(identifier)))


@pytest.mark.parametrize("input_policy", POLICIES)
def test_custom_assignments_are_omitted_and_cannot_supply_language(run, source_json, tmp_path, input_policy):
    """Rules: DK-GEN-07, DK-LBL-02, DK-DIAG-05, DK-CLS-01, DK-DIAG-17.

    One integrated dedicated-flag case checks that ignoring custom assignments
    does not disable the separately exported field. Its full matrix is Wave 2.
    """
    no_flag = run(input_policy=input_policy)
    document = source_json("shared/core_model")
    document["model"]["contents"][0]["isExtensional"] = True
    plain = run(path=write_input(tmp_path, document), input_policy=input_policy)
    assigned = run("ontology/custom_assignments", input_policy=input_policy)
    assert no_flag.outcome == plain.outcome == assigned.outcome == "completed"
    assert_selected_equal(assigned.ontology, plain.ontology, FIXED_PREDICATES, {OWL.disjointWith})
    assert diagnostic_signatures(assigned.diagnostics) == diagnostic_signatures(plain.diagnostics)
    assert set(plain.ontology.objects(BASE.Person, RDFS.comment)) != set(no_flag.ontology.objects(BASE.Person, RDFS.comment))
    assert_selected_equal(plain.ontology, no_flag.ontology, FIXED_PREDICATES, {OWL.disjointWith})
    assert any(d.kind == "extensionality" and d.severity == "INFO" and "cPerson" in d.identified_sources for d in assigned.diagnostics)
    assert not any(d.kind in {"omitted_custom_assignments", "unknown_information", "ambiguous_language"} for d in assigned.diagnostics)
    assert Literal("Person") in set(assigned.ontology.objects(BASE.Person, RDFS.label))
    assert not any(isinstance(term, Literal) and "CUSTOM_" in str(term) for triple in assigned.ontology for term in triple)


@pytest.mark.parametrize("input_policy", POLICIES)
def test_explicit_structures_are_mapped_without_semantic_validation(run, source_path, input_policy):
    """Rules: DK-GEN-01, DK-GEN-02, DK-DIAG-02, DK-DIAG-05; §3.4.

    All three classes are kinds with explicit specialization edges. The
    semantic tension with ultimate-sortal disjointness must not cause rejection.
    Class transitive closure is not required or forbidden by this assertion.
    """
    result = run("ontology/explicit_structures", iri_strategy="id", input_policy=input_policy)
    assert result.outcome == "completed"
    assert_contains(result.ontology, load_graph(source_path("ontology/explicit_structures", "expected.ttl")))
    assert not any(d.severity == "ERROR" or d.kind == "semantic_validation" for d in result.diagnostics)
    for identifier in ("gAlphaBeta", "gBetaGamma"):
        assert not any(result.ontology.triples((BASE[identifier], None, None)))
        assert not list(result.ontology.subjects(DCTERMS.identifier, Literal(identifier)))
