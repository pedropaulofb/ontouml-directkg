"""General domain output and source-container omission checks."""

from urllib.parse import urlsplit
from pathlib import Path
import io
import json

import pytest
from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, XSD

from tests.support.invocation import diagnostic_signatures
from tests.support.data import write_input, fixture_issues
from tests.support.rdf import assert_contains, assert_graph_equal, assert_selected_equal, load_graph, property_chains


BASE = Namespace("https://example.test/model#")
DKGM_ONTOLOGY = URIRef("https://w3id.org/directkg/vocab/dkgm")
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

    The 2026-10-24 identity decision fixes the exact unversioned DKGM target.
    """
    result = run("shared/base_iri", input_policy=input_policy)
    assert result.outcome == "completed"
    ontology = URIRef("https://example.test/model")
    assert (ontology, RDF.type, OWL.Ontology) in result.ontology
    imports = set(result.ontology.objects(ontology, OWL.imports))
    assert DKGM_ONTOLOGY in imports
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


@pytest.mark.parametrize('resource',['vocabulary/latest/dkgm-vocabulary.ttl','vocabulary/versioned/dkgm-vocabulary-v0.1.0.ttl',
                                     'vocabulary/versioned/dkgm-vocabulary-v0.1.1.ttl'],
                         ids=['latest_vocabulary','versioned_vocabulary','versioned_0_1_1_vocabulary'])
def test_existing_mereology_vocabulary_has_relative_identity_complete_generic_axioms_and_no_gufo_alignment(resource):
    """Rules: DK-GEN-04.

    Read-only conformance of the actual resource to the accepted concrete URI,
    namespace and retained release versions. No network resolution claim.
    """
    graph=load_graph(Path(__file__).resolve().parents[2]/resource)
    ontologies=set(graph.subjects(RDF.type,OWL.Ontology));assert len(ontologies)==1
    ontology=next(iter(ontologies));assert isinstance(ontology,URIRef) and not urlsplit(str(ontology)).fragment
    assert ontology == DKGM_ONTOLOGY
    version = '0.1.0' if 'v0.1.0' in resource else '0.1.1'
    assert set(graph.objects(ontology,OWL.versionIRI)) == {URIRef(str(DKGM_ONTOLOGY)+'/'+version)}
    vann=Namespace('http://purl.org/vocab/vann/')
    assert set(graph.objects(ontology,vann.preferredNamespacePrefix)) == {Literal('dkgm')}
    assert set(graph.objects(ontology,vann.preferredNamespaceUri)) == {Literal(str(DKGM_ONTOLOGY)+'#')}
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
    assert u == DKGM_ONTOLOGY
    assert isinstance(u,URIRef) and not urlsplit(str(u)).fragment
    assert (ontology,OWL.imports,u) in result.ontology
    for name in ('memberOf','subCollectionOf','subQuantityOf','componentOf'):
        term=URIRef(str(u)+'#'+name)
        assert (term,RDF.type,OWL.ObjectProperty) not in result.ontology
        assert (term,RDF.type,OWL.AsymmetricProperty) not in result.ontology
        assert not list(result.ontology.objects(term,OWL.propertyChainAxiom))
    # Read actual import evidence; external redirect behavior is a separate check.


def test_rdf_helper_property_chains_keep_order_and_anonymous_direction():
    """Harness only: real RDF lists, not a simulated conversion."""
    graph=Graph().parse(data='''@prefix : <urn:chain:> .
        @prefix owl: <http://www.w3.org/2002/07/owl#> .
        :p owl:propertyChainAxiom ([owl:inverseOf :left] :right).''',format='turtle')
    assert property_chains(graph,URIRef('urn:chain:p'))=={(('inverse',URIRef('urn:chain:left')),URIRef('urn:chain:right'))}
    assert property_chains(graph,URIRef('urn:chain:p'))!={(URIRef('urn:chain:right'),('inverse',URIRef('urn:chain:left')))}


# Wave provenance is recorded in the inventory, not in case or module names.
import hashlib
from datetime import datetime, timedelta, timezone
import yaml
from tests.support.data import fixture_path, load_yaml, source_element
from tests.support.invocation import Fault
from tests.support.rdf import one_object, rooted_graph

PROV = Namespace('http://www.w3.org/ns/prov#')
SPDX = Namespace('http://spdx.org/rdf/terms#')
DCAT = Namespace('http://www.w3.org/ns/dcat#')
MOD = Namespace('https://w3id.org/mod#')
ONTOLOGY = URIRef('https://example.test/model')
METADATA = 'shared/external_metadata'
SELECTED_METADATA = {'title':DCTERMS.title,'acronym':MOD.acronym,'contributor':DCTERMS.contributor,
                     'keyword':DCAT.keyword,'source':DCTERMS.source,'landingPage':DCAT.landingPage,'license':DCTERMS.license}
PROVENANCE_DEFAULTS = {'iri_strategy':'name','input_policy':'tolerant','stereotype_policy':'allow-custom',
                       'inverse_properties':'all','material_property_chains':'none','relation_labels':'source-only',
                       'omit_identifiers':False,'stereotype_relation_naming':True,'provenance':'embedded'}


def _external_graph(result):
    assert result.external_metadata_output is not None, 'Bind actual external-annotation evidence'
    graph=Graph()
    for triple in result.external_metadata_output:
        assert triple in result.ontology
        graph.add(triple)
    return graph


def _checksum(graph, entity, data):
    checksums=[node for node in graph.objects(entity,SPDX.checksum)
               if (node,SPDX.algorithm,SPDX.checksumAlgorithm_sha256) in graph]
    assert checksums, 'Missing SHA-256 SPDX checksum structure'
    for node in checksums:
        value=one_object(graph,node,SPDX.checksumValue)
        assert isinstance(value,Literal)
        assert str(value).lower()==hashlib.sha256(data).hexdigest()


def _role(result, name):
    assert result.provenance_roles is not None, 'Read roles from actual provenance evidence'
    values=result.provenance_roles.get(name,())
    assert values, name
    return values[0]


def _provenance(result, mode, source_bytes=None, metadata=None):
    graph=result.ontology if mode=='embedded' else result.provenance
    assert isinstance(graph,Graph) and len(graph)>0
    activity=_role(result,'activity')
    assert isinstance(activity,(URIRef,BNode))
    assert (ONTOLOGY,PROV.wasGeneratedBy,activity) in graph
    assert (activity,RDF.type,PROV.Activity) in graph
    agents=set(graph.objects(activity,PROV.wasAssociatedWith))
    software=[_role(result,'software')]
    assert software[0] in agents and (software[0],RDF.type,PROV.SoftwareAgent) in graph
    assert any((agent,RDF.type,URIRef(namespace+'SoftwareApplication')) in graph
               for agent in software for namespace in ('http://schema.org/','https://schema.org/'))
    assert any('directkg' in str(term).lower() for agent in software
               for triple in graph.triples((agent,None,None)) for term in (agent,triple[2]))
    versions=[value for agent in software for namespace in ('http://schema.org/','https://schema.org/')
              for value in graph.objects(agent,URIRef(namespace+'softwareVersion'))]
    assert versions and all(isinstance(value,Literal) and str(value) for value in versions)
    timestamps=list(graph.objects(activity,PROV.endedAtTime))
    assert timestamps
    for timestamp in timestamps:
        assert isinstance(timestamp,Literal)
        assert datetime.fromisoformat(str(timestamp).replace('Z','+00:00')).utcoffset().total_seconds()==0
    source=_role(result,'source');configuration=_role(result,'configuration')
    assert source!=configuration
    for entity in (source,configuration):
        assert (entity,RDF.type,PROV.Entity) in graph and (activity,PROV.used,entity) in graph
    if source_bytes is not None:_checksum(graph,source,source_bytes)
    text=result.configuration_literal
    assert (configuration,PROV.value,text) in graph
    assert isinstance(text,Literal) and isinstance(yaml.safe_load(str(text)),dict)
    assert list(graph.objects(configuration,DCTERMS.format)) and result.configuration_format=='yaml'
    assert result.configuration_controls is not None
    if metadata is not None:
        entity=_role(result,'metadata')
        assert entity not in {source,configuration}
        assert (entity,RDF.type,PROV.Entity) in graph and (activity,PROV.used,entity) in graph
        _checksum(graph,entity,metadata.read_bytes())
    return graph,activity,str(text)


@pytest.mark.parametrize('mode',['none','embedded','sidecar'])
@pytest.mark.parametrize('language',[None,'fr'],ids=['source_languages','override'])
def test_external_selected_metadata_is_untagged_separate_and_independent_of_provenance(run,source_json,tmp_path,mode,language):
    """Rules: DK-GEN-08, DK-GEN-09, DK-GEN-10, DK-LBL-02."""
    document=source_json('shared/base_iri');document.update(name='Source Project',description='Source description',languages=['nl'])
    options={'language':language} if language else {}
    result=run(path=write_input(tmp_path,document),metadata_file=fixture_path(METADATA,'metadata.yaml'),provenance=mode,**options)
    assert result.outcome=='completed'
    expected=load_graph(fixture_path('ontology/external_metadata','expected.ttl'))
    assert_contains(result.ontology,expected);assert_graph_equal(_external_graph(result),expected)
    assert (ONTOLOGY,RDFS.label,Literal('Source Project',lang=language or 'nl')) in result.ontology
    assert (ONTOLOGY,RDFS.comment,Literal('Source description',lang=language or 'nl')) in result.ontology
    assert not list(result.ontology.triples((None,RDFS.label,Literal('External Ontology Title'))))
    for _,_,value in expected:
        if isinstance(value,Literal):assert value.language is None
    if mode=='none':assert result.transformation_provenance_output==()
    else:_provenance(result,mode,metadata=fixture_path(METADATA,'metadata.yaml'))


@pytest.mark.parametrize('field',list(SELECTED_METADATA))
@pytest.mark.parametrize('state',['absent','null','empty'])
def test_optional_metadata_values_have_no_fabricated_annotation(run,source_json,tmp_path,field,state):
    """Rules: DK-GEN-09, DK-GEN-11."""
    data=load_yaml(METADATA);data.pop(field)
    if state!='absent':data[field]=None if state=='null' else ([] if field in {'contributor','keyword','source','landingPage'} else '')
    path=tmp_path/'metadata.yaml';path.write_text(yaml.safe_dump(data,allow_unicode=True))
    result=run('shared/base_iri',metadata_file=path)
    assert result.outcome=='completed'
    external=_external_graph(result)
    assert not list(external.objects(ONTOLOGY,SELECTED_METADATA[field]))
    assert all(subject==ONTOLOGY for subject,_,_ in external)
    assert (BASE.Person,RDF.type,OWL.Class) in result.ontology


@pytest.mark.parametrize('landing',['https://example.test/single',['https://example.test/one','https://example.test/two']],ids=['single_iri','list_iris'])
@pytest.mark.parametrize('project_name',[None,'Project Name'],ids=['no_project_name','project_name'])
def test_external_title_does_not_supply_project_label_and_landing_page_accepts_both_shapes(run,source_json,tmp_path,landing,project_name):
    """Rules: DK-GEN-08, DK-GEN-09."""
    document=source_json('shared/base_iri');document['name']=project_name
    path=tmp_path/'metadata.yaml';path.write_text(yaml.safe_dump({'title':'Title Only','landingPage':landing}))
    result=run(path=write_input(tmp_path,document),metadata_file=path)
    assert result.outcome=='completed'
    assert (ONTOLOGY,DCTERMS.title,Literal('Title Only')) in result.ontology
    assert not list(result.ontology.triples((None,RDFS.label,Literal('Title Only'))))
    if project_name:assert (ONTOLOGY,RDFS.label,Literal(project_name)) in result.ontology
    values=[landing] if isinstance(landing,str) else landing
    assert set(_external_graph(result).objects(ONTOLOGY,DCAT.landingPage))=={URIRef(value) for value in values}


@pytest.mark.parametrize('input_policy',['strict','tolerant','best-effort'])
def test_ignored_metadata_fields_do_not_affect_languages_settings_or_validation(run,source_json,tmp_path,input_policy):
    """Rules: DK-GEN-09, DK-GEN-11, DK-LBL-02, DK-DIAG-05."""
    document=source_json('shared/base_iri');document['name']='Project Text';document['languages']=['nl']
    result=run(path=write_input(tmp_path,document),metadata_file=fixture_path(METADATA,'metadata/ignored/metadata.yaml'),input_policy=input_policy,provenance='embedded')
    assert result.outcome=='completed'
    assert (ONTOLOGY,RDFS.label,Literal('Project Text',lang='nl')) in result.ontology
    assert set(_external_graph(result))=={(ONTOLOGY,DCTERMS.title,Literal('Selected Title'))}
    assert not any('IGNORED_' in str(term) for triple in result.ontology for term in triple)
    assert not any(d.kind=='metadata_field' for d in result.diagnostics)
    for key,value in {**PROVENANCE_DEFAULTS,'input_policy':input_policy}.items():assert result.configuration_controls[key]==value
    assert (BASE.Person,RDF.type,OWL.Class) in result.ontology


@pytest.mark.parametrize('location',['source_parent','working_directory'])
def test_metadata_is_never_discovered_without_an_explicit_request(run,source_json,tmp_path,location):
    """Rules: DK-GEN-09."""
    directory=tmp_path if location=='working_directory' else tmp_path/'input_folder';directory.mkdir(exist_ok=True)
    (directory/'metadata.yaml').write_bytes(fixture_path(METADATA,'metadata.yaml').read_bytes())
    result=run(path=write_input(directory,source_json('shared/base_iri')))
    assert result.outcome=='completed' and result.external_metadata_output==()


@pytest.mark.parametrize('field,invalid',[('title',['not a string']),('acronym',{'bad':'shape'}),('contributor','https://example.test/person'),('contributor',['ALICE_NAME_NOT_AN_IRI']),
                                        ('keyword',[17]),('source',['not an IRI']),('landingPage',17),('license','not an IRI')],ids=['title','acronym','contributor','contributor_name','keyword','source','landingPage','license'])
@pytest.mark.parametrize('input_policy',['strict','tolerant','best-effort'])
def test_invalid_selected_metadata_follows_policy_without_losing_independent_fields(run,tmp_path,field,invalid,input_policy):
    """Rules: DK-GEN-09, DK-DIAG-04, DK-DIAG-05."""
    data={field:invalid,('acronym' if field=='title' else 'title'):'KEPT_VALID_TEXT'}
    path=tmp_path/'metadata.yaml';path.write_text(yaml.safe_dump(data))
    result=run('shared/base_iri',metadata_file=path,input_policy=input_policy)
    assert any(d.severity=='ERROR' and d.kind=='metadata_field' for d in result.diagnostics)
    if input_policy!='best-effort':assert result.outcome=='aborted' and result.ontology is None
    else:
        assert result.outcome=='completed-with-errors'
        assert not list(_external_graph(result).objects(ONTOLOGY,SELECTED_METADATA[field]))
        assert (ONTOLOGY,MOD.acronym if field=='title' else DCTERMS.title,Literal('KEPT_VALID_TEXT')) in result.ontology
        assert (BASE.Person,RDF.type,OWL.Class) in result.ontology


@pytest.mark.parametrize('failure',['missing','permission','malformed','root_list','root_null','root_scalar'])
@pytest.mark.parametrize('input_policy',['strict','tolerant','best-effort'])
def test_metadata_file_failure_aborts_or_omits_every_external_contribution_without_salvage(invoke,source_json,tmp_path,failure,input_policy):
    """Rules: DK-GEN-09, DK-GEN-10, DK-DIAG-04, DK-DIAG-05."""
    document=source_json('shared/base_iri');document.update(name='Kept Project',description='Kept Description')
    metadata=tmp_path/'metadata.yaml';faults=()
    if failure=='permission':metadata.write_text('title: NOT_INGESTED');faults=(Fault('metadata','read',metadata),)
    elif failure=='malformed':metadata.write_text('title: NOT_INGESTED\nlicense: [')
    elif failure=='root_list':metadata.write_bytes(fixture_path(METADATA,'metadata/root_list/metadata.yaml').read_bytes())
    elif failure=='root_null':metadata.write_text('null\n')
    elif failure=='root_scalar':metadata.write_text('42\n')
    source=write_input(tmp_path,document)
    result=invoke.convert(source,options={'base_iri':str(BASE),'metadata_file':metadata,'provenance':'embedded','input_policy':input_policy},workdir=tmp_path,faults=faults)
    assert any(d.kind=='metadata_input' and d.severity=='ERROR' and
               ('conversion_aborted' if input_policy!='best-effort' else 'external_metadata_omitted') in d.facts for d in result.diagnostics)
    if input_policy!='best-effort':assert result.outcome=='aborted' and result.ontology is None
    else:
        assert result.outcome=='completed-with-errors' and result.external_metadata_output==()
        assert (BASE.Person,RDF.type,OWL.Class) in result.ontology
        assert (ONTOLOGY,RDFS.label,Literal('Kept Project')) in result.ontology
        assert (ONTOLOGY,RDFS.comment,Literal('Kept Description')) in result.ontology
        _provenance(result,'embedded',source.read_bytes())
        # A parsed non-mapping root fails metadata validation; it does not
        # establish that the input artifact was never read or parsed.
        if failure in {'missing','permission','malformed'}:
            assert not result.provenance_roles.get('metadata',())
    if faults:assert any(op.kind=='metadata' and op.operation=='read' and op.failed and op.raw is not None for op in result.operations or ())


@pytest.mark.parametrize('suffix',['json','ttl','ion'])
def test_external_metadata_mechanism_does_not_accept_other_file_formats(run,tmp_path,suffix):
    """Rules: DK-GEN-09."""
    path=tmp_path/('metadata.'+suffix);path.write_text('{"title":"UNSUPPORTED_FORMAT_TITLE"}')
    result=run('shared/base_iri',metadata_file=path,input_policy='best-effort')
    if result.ontology is not None:assert result.external_metadata_output==()
    else:assert result.configuration_error is not None or result.outcome=='aborted'


@pytest.mark.parametrize('mode',[None,'none','embedded','sidecar'],ids=['default_embedded','none','embedded','sidecar'])
def test_provenance_modes_keep_domain_output_and_expose_actual_execution_records(invoke,source_path,tmp_path,mode):
    """Rules: DK-GEN-09, DK-GEN-10, DK-GEN-11."""
    options={'base_iri':str(BASE),'metadata_file':fixture_path(METADATA,'metadata.yaml')}
    if mode is not None:options['provenance']=mode
    before=datetime.now(timezone.utc).replace(microsecond=0)
    result=invoke.convert(source_path('shared/base_iri'),options=options,workdir=tmp_path)
    after=datetime.now(timezone.utc).replace(microsecond=0)+timedelta(seconds=1)
    assert result.outcome=='completed'
    assert (BASE.Person,RDF.type,OWL.Class) in result.ontology
    assert_contains(result.ontology,load_graph(fixture_path('ontology/external_metadata','expected.ttl')))
    assert result.directkg_metadata_predicates==()
    if mode=='none':assert result.transformation_provenance_output==()
    else:
        actual=mode or 'embedded'
        graph,_,_=_provenance(result,actual,source_path('shared/base_iri').read_bytes(),fixture_path(METADATA,'metadata.yaml'))
        version=invoke.inspect_controls().software_version
        assert version and result.software_version==version
        completion=list(graph.objects(_role(result,'activity'),PROV.endedAtTime))
        assert any(before<=datetime.fromisoformat(str(t).replace('Z','+00:00'))<=after for t in completion)
        if actual=='sidecar':
            assert result.transformation_provenance_output is not None
            assert not list(result.ontology.objects(ONTOLOGY,PROV.wasGeneratedBy))
            assert result.sidecar_writes==()
            assert not list(tmp_path.glob('*.provenance.ttl'))
            serialized=invoke.serialize(result,target='provenance')
            assert serialized.failure is None and serialized.data is not None
            assert_graph_equal(Graph().parse(data=serialized.data,format='turtle'),graph)
        else:
            assert result.output_artifact_output==() and result.embedded_output_configuration==()


@pytest.mark.parametrize('mode',['embedded','sidecar'])
def test_input_digests_use_exact_bytes_and_configuration_is_deterministic_in_distinct_executions(invoke,source_json,tmp_path,mode):
    """Rules: DK-GEN-10, DK-CONF-01."""
    import json
    document=source_json('shared/base_iri')
    source=tmp_path/'input.json';source.write_bytes(json.dumps(document,ensure_ascii=False,separators=(',',':')).encode()+b'\r\n')
    options={'base_iri':str(BASE),'provenance':mode}
    results=[];records=[]
    for _ in range(2):
        result=invoke.convert(source,options=options,workdir=tmp_path)
        results.append(result);records.append(_provenance(result,mode,source.read_bytes()))
    # Named activities are globally comparable. Blank-node labels belong to
    # their own output graph scopes and must not be compared across executions.
    if all(isinstance(record[1],URIRef) for record in records):assert records[0][1]!=records[1][1]
    assert records[0][2]==records[1][2]  # only the configuration literal, not whole RDF/text
    for result in results:
        for key,value in {**PROVENANCE_DEFAULTS,'provenance':mode,'base_iri':str(BASE)}.items():assert result.configuration_controls[key]==value
    changed=source.read_bytes()+b' \n';source.write_bytes(changed)
    third=invoke.convert(source,options=options,workdir=tmp_path)
    _provenance(third,mode,changed)
    assert third.configuration_controls==results[0].configuration_controls
    configured={**options,'iri_strategy':'id','input_policy':'best-effort','stereotype_policy':'require-known',
                'inverse_properties':'none','stereotype_relation_naming':False,'relation_labels':'generated',
                'material_property_chains':'preserve-conflicting-constraints','language':'fr','omit_identifiers':True}
    fourth=invoke.convert(source,options=configured,workdir=tmp_path)
    assert fourth.outcome=='completed'
    _provenance(fourth,mode,changed)
    for key,value in configured.items():assert fourth.configuration_controls[key]==value


@pytest.mark.parametrize('mode', ['none', 'embedded', 'sidecar'])
@pytest.mark.parametrize('path_form', ['path_object', 'path_string'])
def test_file_source_preserves_exact_consumed_bytes_and_programmatic_graphs(invoke, source_json, tmp_path, mode, path_form):
    """Rules: DK-GEN-10, DK-CLS-01; §3.2, §15. RD-05 file-only input rules 1–4.

    Equivalent parsed JSON has different whitespace, escaping and byte digests.
    A later change to the file must not replace the bytes actually consumed.
    Provenance content is checked independently of whether a programmatic
    graph view is exposed alongside the ontology.
    """
    document = source_json('shared/base_iri')
    source_element(document, 'C17')['name'] = 'Málaga'
    assert not fixture_issues(document)
    variants = (
        json.dumps(document, ensure_ascii=False, separators=(',', ':')).encode('utf-8') + b'\n',
        json.dumps(document, ensure_ascii=True, indent=2).replace('\n', '\r\n').encode('utf-8') + b'\r\n \t',
    )
    assert variants[0] != variants[1] and json.loads(variants[0]) == json.loads(variants[1]) == document
    for index, payload in enumerate(variants):
        path = tmp_path / f'source_{index}.json'
        path.write_bytes(payload)
        source = str(path) if path_form == 'path_string' else path
        result = invoke.convert(source, options={'base_iri': str(BASE), 'iri_strategy': 'id', 'provenance': mode}, workdir=tmp_path)
        assert result.outcome == 'completed'
        assert (BASE.C17, RDF.type, OWL.Class) in result.ontology
        assert (BASE.C17, RDFS.label, Literal('Málaga')) in result.ontology
        assert not any(event.severity == 'ERROR' for event in result.diagnostics)
        path.write_bytes(payload + b' \n')  # change after completed conversion, before reading provenance
        if mode == 'none':
            for graph in (result.ontology, result.provenance):
                if graph is not None:
                    assert isinstance(graph, Graph)
                    assert not list(graph.subjects(RDF.type, PROV.Activity))
                    assert not list(graph.triples((None, PROV.used, None)))
                    assert not invoke.read_source_artifacts(graph)
        else:
            graph = result.ontology if mode == 'embedded' else result.provenance
            assert isinstance(graph, Graph)
            artifacts = invoke.read_source_artifacts(graph)
            assert artifacts, 'Actual provenance must identify the consumed source file'
            for artifact in artifacts:
                assert (artifact, RDF.type, PROV.Entity) in graph
                assert any((activity, RDF.type, PROV.Activity) in graph for activity in graph.subjects(PROV.used, artifact))
                _checksum(graph, artifact, payload)
            if mode == 'sidecar':
                assert not list(result.ontology.subjects(RDF.type, PROV.Activity))
        assert not list(tmp_path.glob('*.provenance.ttl'))  # programmatic output stays available without automatic delivery


@pytest.mark.parametrize('mode', ['none', 'embedded', 'sidecar'])
@pytest.mark.parametrize('representation', ['mapping', 'json_text', 'json_bytes', 'text_stream', 'byte_stream', 'missing'])
def test_fileless_source_substitutes_are_rejected_in_every_provenance_mode(invoke, source_json, tmp_path, mode, representation):
    """Rules: DK-GEN-10; §3.2, §15. RD-05 file-only input rules 1–2, 4.

    Rejection may be programmatic or an aborted result; no new exception class,
    diagnostic text, checksum fallback, or source-failure policy is prescribed.
    """
    document = source_json('shared/base_iri')
    assert not fixture_issues(document)
    payload = json.dumps(document, ensure_ascii=False).encode('utf-8')
    (tmp_path / 'input.json').write_bytes(payload)  # an unrelated file cannot substitute for the supplied input
    forms = {'mapping': document, 'json_text': payload.decode('utf-8'), 'json_bytes': payload,
             'text_stream': io.StringIO(payload.decode('utf-8')), 'byte_stream': io.BytesIO(payload), 'missing': None}
    attempt = invoke.attempt_source_input(forms[representation],
        options={'base_iri': str(BASE), 'provenance': mode}, workdir=tmp_path)
    if attempt.rejection is not None:
        assert isinstance(attempt.rejection, Exception) and attempt.observation is None
    else:
        result = attempt.observation
        assert result is not None and result.ontology is None
        assert result.configuration_error is not None or result.outcome == 'aborted'
        if result.configuration_error is None:
            assert any(event.severity == 'ERROR' for event in result.diagnostics)
    assert not list(tmp_path.glob('*.provenance.ttl'))


def test_source_input_surface_has_no_fileless_or_checksum_extension(invoke):
    """Rules: DK-GEN-10; §3.2, §15. RD-05 file-only input rules 2, 4."""
    surface = invoke.inspect_source_input_surface()
    assert surface.raw is not None
    assert surface.extensions == ()


@pytest.mark.parametrize('mode',['embedded','sidecar'])
@pytest.mark.parametrize('input_policy',['strict','tolerant','best-effort'])
def test_required_provenance_failure_aborts_independently_of_input_policy(invoke,source_path,tmp_path,mode,input_policy):
    """Rules: DK-GEN-10, DK-DIAG-04, DK-DIAG-05."""
    fault=Fault('provenance','construct')
    result=invoke.convert(source_path('shared/base_iri'),options={'base_iri':str(BASE),'provenance':mode,'input_policy':input_policy},workdir=tmp_path,faults=(fault,))
    assert result.outcome=='aborted' and result.ontology is None
    assert any(d.kind=='required_provenance' and d.severity=='ERROR' for d in result.diagnostics)
    assert any(op.kind=='provenance' and op.failed and op.raw is not None for op in result.operations or ())
    assert invoke.read_outcome(result)=='aborted'
    assert invoke.read_ontology(result) is None
    assert diagnostic_signatures(invoke.read_diagnostics(result))==diagnostic_signatures(result.diagnostics)


@pytest.mark.parametrize('fault_kind',['provenance','optional_enrichment'])
def test_none_avoids_provenance_only_operations_and_optional_enrichment_failure_is_nonfatal(invoke,source_path,tmp_path,fault_kind):
    """Rules: DK-GEN-10, DK-GEN-11."""
    operation='construct' if fault_kind=='provenance' else 'enrich'
    result=invoke.convert(source_path('shared/base_iri'),options={'base_iri':str(BASE),'provenance':'none'},workdir=tmp_path,faults=(Fault(fault_kind,operation),))
    assert result.outcome in {'completed','completed-with-errors'} and result.ontology is not None
    assert result.operations is not None
    if fault_kind=='provenance':assert not any(op.kind=='provenance' for op in result.operations)
    assert result.transformation_provenance_output==()


@pytest.mark.parametrize('mode',['embedded','sidecar'])
def test_optional_enrichment_failure_keeps_required_provenance(invoke,source_path,tmp_path,mode):
    """Rules: DK-GEN-10, DK-GEN-11."""
    result=invoke.convert(source_path('shared/base_iri'),options={'base_iri':str(BASE),'provenance':mode},workdir=tmp_path,faults=(Fault('optional_enrichment','enrich'),))
    assert result.outcome in {'completed','completed-with-errors'} and result.ontology is not None
    assert any(op.kind=='optional_enrichment' and op.failed and op.raw is not None for op in result.operations or ())
    _provenance(result,mode,source_path('shared/base_iri').read_bytes())


@pytest.mark.parametrize('mode',['embedded','sidecar'])
def test_python_turtle_serialization_preserves_the_entire_observed_graph_and_ordered_lists(invoke,source_path,tmp_path,mode):
    """Rules: DK-GEN-10, DK-REL-07, DK-INV-04. Also §3.3 serialization."""
    result=invoke.convert(source_path('shared/material_pattern'),options={'base_iri':str(BASE),'iri_strategy':'id','provenance':mode,'material_property_chains':'preserve-conflicting-constraints'},workdir=tmp_path)
    assert result.outcome=='completed'
    before=Graph();before+=result.ontology
    serialized=invoke.serialize(result,target='ontology')
    assert serialized.failure is None and serialized.data is not None
    parsed=Graph().parse(data=serialized.data,format='turtle')
    assert_graph_equal(parsed,result.ontology)
    assert property_chains(parsed,BASE.tMaterial)=={(('inverse',BASE.tLeft),BASE.tRight)}
    assert_graph_equal(result.ontology,before)
    if mode=='sidecar':
        artifact=invoke.serialize(result,target='provenance')
        assert artifact.failure is None and artifact.data is not None
        assert_graph_equal(Graph().parse(data=artifact.data,format='turtle'),result.provenance)


@pytest.mark.parametrize('filename',['hospital.ttl','hospital.part.ttl','no_extension'])
def test_python_explicit_delivery_places_sidecar_and_checks_final_ontology_bytes(invoke,source_path,tmp_path,filename):
    """Rules: DK-GEN-10, DK-DIAG-04. Also §3.3 serialization."""
    result=invoke.convert(source_path('shared/base_iri'),options={'base_iri':str(BASE),'provenance':'sidecar'},workdir=tmp_path)
    destination=tmp_path/filename
    delivered=invoke.deliver(result,output_path=destination)
    assert delivered.failure is None and not delivered.observation.delivery_failures
    assert destination.is_file()
    sidecar=destination.with_name(destination.stem+'.provenance.ttl')
    assert sidecar.is_file()
    graph=Graph().parse(sidecar,format='turtle')
    assert_graph_equal(Graph().parse(destination,format='turtle'),delivered.observation.ontology)
    output=_role(delivered.observation,'output')
    assert (output,DCTERMS.isFormatOf,ONTOLOGY) in graph
    assert (output,RDF.type,PROV.Entity) in graph
    assert list(graph.objects(output,PROV.wasGeneratedBy))
    assert Path(delivered.observation.output_filename).name==destination.name
    assert delivered.observation.output_format=='turtle'
    assert delivered.observation.output_artifact_evidence
    assert all(triple in graph for triple in delivered.observation.output_artifact_evidence)
    _checksum(graph,output,destination.read_bytes())


@pytest.mark.parametrize('kind,operation',[('ontology','create'),('ontology','write'),('sidecar','serialize'),('sidecar','create'),('sidecar','write')],ids=['ontology_create','ontology_write','sidecar_serialize','sidecar_create','sidecar_write'])
@pytest.mark.parametrize('old_file',[False,True],ids=['new_destination','old_destination'])
def test_python_delivery_failure_is_explicit_without_graph_mode_or_outcome_substitution(invoke,source_path,tmp_path,kind,operation,old_file):
    """Rules: DK-GEN-10, DK-DIAG-04, DK-DIAG-05."""
    result=invoke.convert(source_path('shared/base_iri'),options={'base_iri':str(BASE),'provenance':'sidecar'},workdir=tmp_path)
    destination=tmp_path/'model.ttl';sidecar=tmp_path/'model.provenance.ttl'
    failed_path=destination if kind=='ontology' else sidecar
    if old_file:failed_path.write_bytes(b'OLD_ARTIFACT')
    delivered=invoke.deliver(result,output_path=destination,faults=(Fault(kind,operation,failed_path),))
    actual=delivered.observation
    assert delivered.failure is not None and actual.outcome=='completed'
    assert actual.pre_delivery_ontology is not None
    assert_graph_equal(actual.ontology,actual.pre_delivery_ontology)
    assert actual.configuration_controls['provenance']=='sidecar'
    assert actual.valid_artifacts is not None and failed_path not in actual.valid_artifacts
    failures=[failure for failure in actual.delivery_failures if failure.kind==kind]
    assert failures and all(failure.destination==failed_path and failure.reason and failure.raw is not None for failure in failures)
    if old_file and failed_path.exists() and failed_path.read_bytes()==b'OLD_ARTIFACT':assert all(failure.old_file_not_updated for failure in failures)
    assert any(op.kind==kind and op.failed and op.raw is not None for op in actual.operations or ())
    if kind=='ontology':assert not sidecar.exists()
    else:assert destination.is_file() and len(Graph().parse(destination,format='turtle'))>0
    assert any(d.kind==kind+'_delivery' and d.severity=='ERROR' for d in actual.diagnostics)


def test_rdf_helper_rooted_projection_keeps_list_connections_without_freezing_metadata():
    """Harness only: RDF subgraph selection, not conversion."""
    a=Graph().parse(data='''@prefix : <urn:r:>. @prefix owl: <http://www.w3.org/2002/07/owl#>.
      @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>.
      :p owl:propertyChainAxiom ([owl:inverseOf :left] :right); rdfs:comment "metadata".''',format='turtle')
    predicates={OWL.propertyChainAxiom,OWL.inverseOf,RDF.first,RDF.rest}
    result=rooted_graph(a,{URIRef('urn:r:p')},predicates)
    assert property_chains(result,URIRef('urn:r:p'))=={(('inverse',URIRef('urn:r:left')),URIRef('urn:r:right'))}
    assert not list(result.triples((None,RDFS.comment,None)))


def test_embedded_explicit_delivery_excludes_serialization_artifact_and_self_digest(invoke,source_path,tmp_path):
    """Rules: DK-GEN-10."""
    result=invoke.convert(source_path('shared/base_iri'),options={'base_iri':str(BASE),'provenance':'embedded'},workdir=tmp_path)
    delivered=invoke.deliver(result,output_path=tmp_path/'embedded.ttl')
    assert delivered.failure is None
    actual=delivered.observation
    assert actual.output_artifact_output==() and actual.embedded_output_configuration==()
    assert not actual.provenance_roles.get('output',())
    assert not list(actual.ontology.objects(ONTOLOGY,SPDX.checksum))
    assert not (tmp_path/'embedded.provenance.ttl').exists()
    assert_graph_equal(Graph().parse(tmp_path/'embedded.ttl',format='turtle'),actual.ontology)


@pytest.mark.parametrize('variant',['nulls','empties','empty_mapping','partial_invalid'])
def test_external_metadata_companion_inputs_preserve_independent_enrichment_under_best_effort(run,variant):
    """Rules: DK-GEN-09, DK-DIAG-05."""
    result=run('shared/base_iri',metadata_file=fixture_path(METADATA,'metadata/'+variant+'/metadata.yaml'),input_policy='best-effort')
    assert (BASE.Person,RDF.type,OWL.Class) in result.ontology
    if variant=='partial_invalid':
        assert result.outcome=='completed-with-errors'
        expected={(ONTOLOGY,DCTERMS.title,Literal('Kept Valid Title')),
                  (ONTOLOGY,DCAT.keyword,Literal('kept keyword')),
                  (ONTOLOGY,DCTERMS.license,URIRef('https://example.test/kept-license'))}
        assert set(_external_graph(result))==expected
        assert any(d.kind=='metadata_field' and d.severity=='ERROR' for d in result.diagnostics)
    else:assert result.outcome=='completed' and result.external_metadata_output==()


def test_rdf_helper_provenance_accepts_additional_activity_and_agent_but_rejects_wrong_checksum():
    """Harness only: explicit RDF sample, no source transformation or simulated API."""
    from tests.support.invocation import Observation
    graph=Graph().parse(data='''
      @prefix : <urn:evidence:>. @prefix prov: <http://www.w3.org/ns/prov#>.
      @prefix schema: <https://schema.org/>. @prefix dct: <http://purl.org/dc/terms/>.
      @prefix spdx: <http://spdx.org/rdf/terms#>.
      <https://example.test/model> prov:wasGeneratedBy :run, :serialization.
      :run a prov:Activity; prov:wasAssociatedWith :directkg, :runtime;
        prov:endedAtTime "2026-10-23T10:00:00Z"; prov:used :source, :configuration.
      :serialization a prov:Activity. :runtime a prov:SoftwareAgent.
      :directkg a prov:SoftwareAgent, schema:SoftwareApplication; schema:softwareVersion "1.2.3".
      :source a prov:Entity; spdx:checksum :checksum.
      :checksum spdx:algorithm spdx:checksumAlgorithm_sha256.
      :configuration a prov:Entity; prov:value "iri_strategy: id"; dct:format "application/yaml".
    ''',format='turtle')
    ns=Namespace('urn:evidence:');artifact=b'harness byte artifact; not a source export'
    graph.add((ns.checksum,SPDX.checksumValue,Literal(hashlib.sha256(artifact).hexdigest())))
    sample=Observation(graph,'completed',(),provenance_roles={'activity':(ns.run,),'software':(ns.directkg,),
        'source':(ns.source,),'configuration':(ns.configuration,)},configuration_literal=Literal('iri_strategy: id'),
        configuration_controls={'iri_strategy':'id'},configuration_format='yaml')
    _provenance(sample,'embedded',artifact)
    graph.set((ns.checksum,SPDX.checksumValue,Literal('0'*64)))
    with pytest.raises(AssertionError):_provenance(sample,'embedded',artifact)


def test_rdf_helper_external_annotation_evidence_allows_independent_metadata():
    """Harness only: observation evidence, never a fabricated converter result."""
    from tests.support.invocation import Observation
    graph=Graph();graph.add((ONTOLOGY,DCTERMS.title,Literal('Independently generated title')))
    sample=Observation(graph,'completed',(),external_metadata_output=())
    assert len(_external_graph(sample))==0
    sample.external_metadata_output=((ONTOLOGY,DCTERMS.title,Literal('Unproduced external value')),)
    with pytest.raises(AssertionError):_external_graph(sample)


@pytest.mark.parametrize('field,valid,invalid',[
    ('contributor','https://example.test/valid-person','NOT_AN_IRI'),
    ('keyword','valid keyword',17),('source','https://example.test/valid-citation',False),
    ('landingPage','https://example.test/valid-landing',17)],ids=['contributor','keyword','source','landing_page'])
def test_mixed_metadata_lists_omit_invalid_values_and_keep_independent_fields_without_deciding_sibling_recovery(run,tmp_path,field,valid,invalid):
    """Rules: DK-GEN-09, DK-DIAG-05.

    Exact valid-sibling retention is blocked for Architect clarification; both
    whole-field and entry-level omission satisfy only these bounded assertions.
    """
    metadata=tmp_path/'metadata.yaml';metadata.write_text(yaml.safe_dump({field:[valid,invalid],'title':'Independent valid title'}))
    result=run('shared/base_iri',metadata_file=metadata,input_policy='best-effort')
    assert result.outcome=='completed-with-errors'
    assert any(d.kind=='metadata_field' and d.severity=='ERROR' for d in result.diagnostics)
    graph=_external_graph(result)
    assert (ONTOLOGY,DCTERMS.title,Literal('Independent valid title')) in graph
    permitted=Literal(valid) if field=='keyword' else URIRef(valid)
    assert set(graph.objects(ONTOLOGY,SELECTED_METADATA[field]))<={permitted}
    assert (BASE.Person,RDF.type,OWL.Class) in result.ontology

def _version_source_resources(result, strategy):
    """Read the fixture's source-backed resources, excluding execution metadata."""
    from tests.support.rdf import one_subject
    kinds = {key: OWL.Class for key in ('cPerson', 'cOrg', 'cAddress')}
    kinds.update(aAge=OWL.DatatypeProperty, aNote=OWL.DatatypeProperty,
                 aAddress=OWL.ObjectProperty, eTarget=OWL.ObjectProperty, eSource=OWL.ObjectProperty)
    resources = {}
    for identifier, kind in kinds.items():
        resource = (BASE[identifier] if strategy == 'id' else
                    one_subject(result.ontology, DCTERMS.identifier, Literal(identifier)))
        assert isinstance(resource, URIRef) and (resource, RDF.type, kind) in result.ontology
        resources[identifier] = resource
    assert len(set(resources.values())) == len(resources)
    return resources


@pytest.mark.parametrize('strategy', ['id', 'name'])
@pytest.mark.parametrize('mode', ['none', 'embedded', 'sidecar'])
def test_ontology_version_iri_preserves_identity_and_records_effective_setting(
        invoke, source_path, tmp_path, strategy, mode):
    """Rules: DK-IRI-01, DK-IRI-02, DK-IRI-06, DK-IRI-09, DK-GEN-04, DK-GEN-10, DK-CONF-01; RD-05 Option B replacement Rule 5; §15.

    Entity identity is compared through source resources, while execution
    records may change. The semantic version option does not prescribe a
    Python parameter or a YAML key in the production interface.
    """
    source = source_path('shared/core_model')
    identities = None
    observations = []
    for version in (None, 'https://example.test/versions/one', 'urn:directkg:test:version:two'):
        options = {'base_iri': str(BASE), 'iri_strategy': strategy, 'provenance': mode}
        if version is not None: options['ontology_version_iri'] = version
        result = invoke.convert(source, options=options, workdir=tmp_path)
        assert result.outcome == 'completed'
        assert (ONTOLOGY, RDF.type, OWL.Ontology) in result.ontology
        assert (ONTOLOGY, OWL.imports, DKGM_ONTOLOGY) in result.ontology
        assert set(result.ontology.objects(ONTOLOGY, OWL.versionIRI)) == (
            set() if version is None else {URIRef(version)})
        resources = _version_source_resources(result, strategy)
        if identities is None: identities = resources
        else: assert resources == identities
        observations.append(result)
        if version is not None and mode != 'none':
            _provenance(result, mode, source.read_bytes())
            assert result.configuration_controls.get('ontology_version_iri') == version
    if mode != 'none':
        _provenance(observations[0], mode, source.read_bytes())
        assert observations[0].configuration_controls.get('ontology_version_iri') is None
    else:
        for result in observations: assert result.transformation_provenance_output == ()


def test_ontology_version_iri_reuse_allows_changed_source_content(invoke, source_json, tmp_path):
    """Rules: DK-IRI-01, DK-LBL-01; RD-05 Option B replacement Rule 5; §15.

    Reusing a caller-assigned identifier does not establish content identity or
    authorize a cross-run registry that rejects a second valid transformation.
    """
    document = source_json('shared/core_model')
    version = 'https://example.test/versions/reused'
    options = {'base_iri': str(BASE), 'iri_strategy': 'id', 'provenance': 'none',
               'ontology_version_iri': version}
    for index, label in enumerate(('First source label', 'Changed source label')):
        source_element(document, 'cPerson')['name'] = label
        assert not fixture_issues(document)
        path = write_input(tmp_path, document, f'source_{index}.json')
        result = invoke.convert(path, options=options, workdir=tmp_path)
        assert result.outcome == 'completed'
        assert (ONTOLOGY, OWL.versionIRI, URIRef(version)) in result.ontology
        assert set(result.ontology.objects(BASE.cPerson, RDFS.label)) == {Literal(label)}


def test_ontology_version_iri_sidecar_hashes_final_delivered_bytes(invoke, source_path, tmp_path):
    """Rules: DK-IRI-01, DK-GEN-04, DK-GEN-10, DK-DIAG-04; RD-05 Option B replacement Rule 5; §15.

    Parse the delivered ontology as RDF; hash its actual bytes, including the
    version statement. No invariant checksum or provenance graph is required.
    """
    source = source_path('shared/core_model')
    for index, version in enumerate(('https://example.test/versions/one', 'urn:directkg:test:version:two')):
        result = invoke.convert(source, options={'base_iri': str(BASE), 'iri_strategy': 'id',
            'provenance': 'sidecar', 'ontology_version_iri': version}, workdir=tmp_path)
        assert result.outcome == 'completed'
        destination = tmp_path / f'versioned_{index}.ttl'
        delivered = invoke.deliver(result, output_path=destination)
        assert delivered.failure is None and not delivered.observation.delivery_failures
        ontology = Graph().parse(destination, format='turtle')
        assert (ONTOLOGY, OWL.versionIRI, URIRef(version)) in ontology
        assert (ONTOLOGY, OWL.imports, DKGM_ONTOLOGY) in ontology
        sidecar = Graph().parse(destination.with_name(destination.stem + '.provenance.ttl'), format='turtle')
        observed = delivered.observation
        output = _role(observed, 'output')
        assert (output, DCTERMS.isFormatOf, ONTOLOGY) in sidecar
        _checksum(sidecar, output, destination.read_bytes())
        configuration = _role(observed, 'configuration')
        assert (configuration, PROV.value, observed.configuration_literal) in sidecar
        assert isinstance(observed.configuration_literal, Literal)
        assert isinstance(yaml.safe_load(str(observed.configuration_literal)), dict)
        assert observed.configuration_controls is not None
        assert observed.configuration_controls.get('ontology_version_iri') == version
