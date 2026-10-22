"""General domain output and source-container omission checks."""

from urllib.parse import urlsplit
from pathlib import Path

import pytest
from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, XSD

from tests.support.invocation import diagnostic_signatures
from tests.support.data import write_input
from tests.support.rdf import assert_contains, assert_graph_equal, assert_selected_equal, load_graph, property_chains


BASE = Namespace("https://example.test/model#")
POLICIES = ["strict", "tolerant", "best-effort"]
FIXED_PREDICATES = {RDF.type, RDFS.domain, RDFS.range, RDFS.label, DCTERMS.identifier,
                    RDFS.subClassOf, RDFS.subPropertyOf, OWL.inverseOf,
                    OWL.equivalentClass, OWL.equivalentProperty, OWL.propertyChainAxiom,
                    OWL.propertyDisjointWith}


def _assert_project_description_omitted(graph, annotations):
    """Actual source-project/fallback annotations, not all ontology comments.

    The binding reads their meaning from actual output; this helper only checks
    its RDF evidence. Independent generated metadata is outside this selection.
    """
    assert all(triple in graph for triple in annotations), "Description evidence is absent from the actual graph"
    assert not annotations, "Unexpected source-project description or fabricated fallback annotation"


def test_rdf_helper_project_description_omission_allows_independent_metadata():
    """Harness only: actual converter/semantic-reader execution is not claimed."""
    ontology = URIRef("urn:helper:ontology")
    graph = Graph()
    metadata = (ontology, RDFS.comment, Literal("The ontology contains one modeled class."))
    graph.add(metadata)
    _assert_project_description_omitted(graph, ())
    assert metadata in graph  # permitted metadata remains in the observed graph
    for text in ("", "sentinel_filename", "Fabricated project description"):
        value = Literal(text)
        triple = (ontology, RDFS.comment, value)
        graph.add(triple)
        observed = (triple,)
        with pytest.raises(AssertionError):
            _assert_project_description_omitted(graph, observed)
        graph.remove(triple)
    with pytest.raises(AssertionError):
        _assert_project_description_omitted(graph, observed)  # reject invented RDF evidence


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
    # Optional descriptive resources/types and unfixed comment text may vary
    # while the selected named-resource mapping remains the same.
    left = Graph().parse(data='''@prefix : <urn:test:> .
        @prefix owl: <http://www.w3.org/2002/07/owl#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
        :a a owl:Class; rdfs:comment "first wording"; owl:disjointWith :b.
        :b a owl:Class. :metadata1 a :FirstMetadataType.''', format="turtle")
    right = Graph().parse(data='''@prefix : <urn:test:> .
        @prefix owl: <http://www.w3.org/2002/07/owl#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
        :a a owl:Class, :AdditionalMetadataType; rdfs:comment "second wording".
        :b a owl:Class; owl:disjointWith :a. :metadata2 a :SecondMetadataType.''', format="turtle")
    roots = {URIRef("urn:test:a"), URIRef("urn:test:b")}
    for predicates in ({RDF.type}, {RDF.type, RDFS.subClassOf}):
        assert_selected_equal(left, right, predicates, {OWL.disjointWith},
                              subjects=roots, type_objects={OWL.Class})
    right.add((URIRef("urn:test:a"), RDFS.subClassOf, URIRef("urn:test:b")))
    with pytest.raises(AssertionError):
        assert_selected_equal(left, right, {RDF.type, RDFS.subClassOf}, {OWL.disjointWith},
                              subjects=roots, type_objects={OWL.Class})
    right.remove((URIRef("urn:test:b"), RDF.type, OWL.Class))
    with pytest.raises(AssertionError):
        assert_selected_equal(left, right, {RDF.type}, {OWL.disjointWith},
                              subjects=roots, type_objects={OWL.Class})


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


@pytest.mark.parametrize("field,predicate", [("name", RDFS.label), ("description", RDFS.comment)], ids=["project_name", "project_description"])
@pytest.mark.parametrize("carrier", ["plain", "localized", "project_language", "override"])
def test_project_text_is_preserved_on_ontology_with_language_resolution(run, source_json, tmp_path, field, predicate, carrier):
    """Rules: DK-GEN-08, DK-LBL-01, DK-LBL-02, DK-IRI-09."""
    document = source_json("shared/source_text")
    first, second = "  <p>Project & café</p>\nOriginal.\t ", "\n<p>Projeto & original</p>  "
    options = {}
    if carrier in {"plain", "project_language"}:
        document[field] = first
        if carrier == "project_language":
            document["languages"] = ["pt-BR"]
        expected = {Literal(first, lang="pt-BR" if carrier == "project_language" else None)}
    else:
        document[field] = {"en": first, "pt-BR": second}
        document["languages"] = ["fr", "de"]
        if carrier == "override":
            options["language"] = "nl"
        expected = {Literal(first, lang="nl" if options else "en"), Literal(second, lang="nl" if options else "pt-BR")}
    result = run(path=write_input(tmp_path, document), iri_strategy="id", **options)
    assert result.outcome == "completed"
    ontology = URIRef("https://example.test/model")
    assert (ontology, RDF.type, OWL.Ontology) in result.ontology
    lexical = {first, second}
    assert {v for v in result.ontology.objects(ontology, predicate) if str(v) in lexical} == expected
    for value in expected:
        assert set(result.ontology.subjects(predicate, value)) == {ontology}
    if field == "description":
        assert set(result.project_description_output) == {
            (ontology, RDFS.comment, value) for value in expected
        }
    assert not any(BASE.projectOne in triple for triple in result.ontology)
    assert not list(result.ontology.subjects(DCTERMS.identifier, Literal("projectOne")))


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("field,predicate", [("name", RDFS.label), ("description", RDFS.comment)], ids=["project_name", "project_description"])
@pytest.mark.parametrize("condition", ["absent", "null", "empty"])
def test_missing_project_text_has_no_fallback_annotation_or_diagnostic(run, source_json, tmp_path, input_policy, field, predicate, condition):
    """Rules: DK-GEN-08, DK-LBL-02, DK-DIAG-05."""
    document = source_json("shared/base_iri")
    # Shared single-class input isolates source-project text from domain mapping.
    for key in ("name", "description"):
        document.pop(key, None)
    baseline = run(path=write_input(tmp_path, document, "absent_project_text.json"), iri_strategy="id", input_policy=input_policy)
    if condition != "absent":
        document[field] = None if condition == "null" else ""
    result = run(path=write_input(tmp_path, document, "sentinel_filename.json"), iri_strategy="id", input_policy=input_policy)
    assert baseline.outcome == result.outcome == "completed"
    ontology = URIRef("https://example.test/model")
    if field == "description":
        _assert_project_description_omitted(result.ontology, result.project_description_output)
        assert not any(d.kind == "omitted_description" for d in result.diagnostics)
    else:
        assert not list(result.ontology.objects(ontology, predicate))
    assert diagnostic_signatures(result.diagnostics) == diagnostic_signatures(baseline.diagnostics)
    assert_selected_equal(result.ontology, baseline.ontology,
                          {RDF.type, RDFS.subClassOf, OWL.equivalentClass},
                          {OWL.disjointWith}, subjects={BASE.C17},
                          type_objects={OWL.Class, OWL.NamedIndividual, BASE.C17})
    for observation in (baseline, result):
        assert (BASE.C17, RDF.type, OWL.Class) in observation.ontology
        assert (BASE.C17, RDFS.label, Literal("Person")) in observation.ontology


@pytest.mark.parametrize("iri_strategy", ["name", "id"])
def test_project_name_changes_only_ontology_label(run, source_json, tmp_path, iri_strategy):
    """Rules: DK-GEN-08, DK-IRI-01, DK-IRI-02, DK-IRI-09."""
    document = source_json("shared/base_iri")
    document["name"] = "Original project"
    first = run(path=write_input(tmp_path, document, "first.json"), iri_strategy=iri_strategy)
    document["name"] = "Completely different project"
    second = run(path=write_input(tmp_path, document, "renamed.json"), iri_strategy=iri_strategy)
    assert first.outcome == second.outcome == "completed"
    ontology = URIRef("https://example.test/model")
    for result, text in [(first, "Original project"), (second, "Completely different project")]:
        assert set(result.ontology.subjects(RDF.type, OWL.Ontology)) == {ontology}
        assert set(result.ontology.objects(ontology, RDFS.label)) == {Literal(text)}
        assert not list(result.ontology.subjects(DCTERMS.identifier, Literal(document["id"])))
    target = BASE.C17 if iri_strategy == "id" else BASE.Person
    for observation in (first, second):
        assert (target, RDF.type, OWL.Class) in observation.ontology
        assert (target, RDFS.label, Literal("Person")) in observation.ontology
        assert {s for s in observation.ontology.subjects(RDF.type, OWL.Class) if isinstance(s, URIRef) and str(s).startswith(str(BASE))} == {target}
        identifiers = set(observation.ontology.subjects(DCTERMS.identifier, Literal("C17")))
        assert identifiers == ({target} if iri_strategy == "name" else set())
    assert_selected_equal(first.ontology, second.ontology,
                          {RDF.type, RDFS.subClassOf, OWL.equivalentClass,
                           RDFS.domain, RDFS.range}, {OWL.disjointWith},
                          subjects={target}, type_objects={OWL.Class, OWL.NamedIndividual, target})
    assert diagnostic_signatures(first.diagnostics) == diagnostic_signatures(second.diagnostics)


@pytest.mark.parametrize('resource',['vocabulary/latest/dkgm-vocabulary.ttl','vocabulary/versioned/dkgm-vocabulary-v0.1.0.ttl'],
                         ids=['latest_vocabulary','versioned_vocabulary'])
def test_existing_mereology_vocabulary_has_relative_identity_complete_generic_axioms_and_no_gufo_alignment(resource):
    """Rules: DK-GEN-04.

    Read-only conformance of the actual resource, not proof that its concrete
    URI has been adopted. No network redirect/version-pinning expectation.
    """
    graph=load_graph(Path(__file__).resolve().parents[2]/resource)
    ontologies=set(graph.subjects(RDF.type,OWL.Ontology));assert len(ontologies)==1
    ontology=next(iter(ontologies));assert isinstance(ontology,URIRef) and not urlsplit(str(ontology)).fragment
    terms={name:URIRef(str(ontology)+'#'+name) for name in ('memberOf','subCollectionOf','subQuantityOf','componentOf')}
    for term in terms.values():
        assert (term,RDF.type,OWL.ObjectProperty) in graph
        assert (term,RDF.type,OWL.AsymmetricProperty) not in graph
        assert not any((parent,RDF.type,OWL.AsymmetricProperty) in graph for parent in graph.transitive_objects(term,RDFS.subPropertyOf))
    assert property_chains(graph,terms['memberOf'])=={(terms['memberOf'],terms['subCollectionOf'])}
    assert property_chains(graph,terms['subCollectionOf'])=={(terms['subCollectionOf'],terms['subCollectionOf'])}
    assert property_chains(graph,terms['subQuantityOf'])=={(terms['subQuantityOf'],terms['subQuantityOf'])}
    assert not property_chains(graph,terms['componentOf'])
    assert (terms['componentOf'],RDF.type,OWL.TransitiveProperty) not in graph
    logical={OWL.imports,OWL.equivalentProperty,OWL.equivalentClass,RDFS.subPropertyOf,
             RDFS.subClassOf,RDFS.domain,RDFS.range,OWL.inverseOf,OWL.sameAs,RDF.type,RDF.first}
    for s,p,o in graph:
        if p in logical or str(p).startswith(str(OWL)) or 'purl.org/nemo/gufo' in str(p).lower():
            assert not any(isinstance(term,URIRef) and 'purl.org/nemo/gufo' in str(term).lower() for term in (s,p,o))


@pytest.mark.parametrize('key',['shared/base_iri','shared/binary_relation'],ids=['no_relations','ordinary_relation'])
def test_generated_ontology_uses_observed_core_import_without_copying_generic_axioms(run,key):
    """Rules: DK-GEN-04, DK-GEN-01, DK-IRI-01."""
    result=run(key,iri_strategy='id')
    assert result.outcome=='completed'
    ontology=URIRef('https://example.test/model');u=result.mereology_import
    assert isinstance(u,URIRef) and not urlsplit(str(u)).fragment
    assert (ontology,OWL.imports,u) in result.ontology
    for name in ('memberOf','subCollectionOf','subQuantityOf','componentOf'):
        term=URIRef(str(u)+'#'+name)
        assert (term,RDF.type,OWL.ObjectProperty) not in result.ontology
        assert (term,RDF.type,OWL.AsymmetricProperty) not in result.ontology
        assert not list(result.ontology.objects(term,OWL.propertyChainAxiom))
    # This identifies the actual import from binding/publication evidence. The
    # concrete accepted U and external redirect behavior remain blocked.


def test_rdf_helper_property_chains_keep_order_and_anonymous_direction():
    """Harness only: real RDF lists, not a simulated conversion."""
    graph=Graph().parse(data='''@prefix : <urn:chain:> .
        @prefix owl: <http://www.w3.org/2002/07/owl#> .
        :p owl:propertyChainAxiom ([owl:inverseOf :left] :right).''',format='turtle')
    assert property_chains(graph,URIRef('urn:chain:p'))=={(('inverse',URIRef('urn:chain:left')),URIRef('urn:chain:right'))}
    assert property_chains(graph,URIRef('urn:chain:p'))!={(URIRef('urn:chain:right'),('inverse',URIRef('urn:chain:left')))}
