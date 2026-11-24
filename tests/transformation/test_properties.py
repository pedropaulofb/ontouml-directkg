"""Shared property identity, property references, and source characteristics."""

import pytest
from rdflib import Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, XSD

from tests.support.rdf import one_subject, cardinality_facts, property_expression, property_chains


BASE = Namespace("https://example.test/model#")


def test_colliding_source_properties_stay_distinct_with_original_kinds(run):
    """Rules: DK-PROP-01, DK-PROP-02, DK-IRI-07, DK-IRI-09, DK-GEN-03, DK-CONF-02."""
    result = run("shared/property_collisions")
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
    first = run("shared/property_collisions")
    again = run("shared/property_collisions")
    assert first.outcome == again.outcome == "completed"
    for identifier in ("a1", "a2", "a3", "eTarget"):
        assert one_subject(first.ontology, DCTERMS.identifier, Literal(identifier)) == one_subject(again.ontology, DCTERMS.identifier, Literal(identifier))


# RD-14 and source flags use ID mode to separate property-expression assertions
# from the naming/inverse naming matrices owned by the other approved waves.
import copy
from rdflib import BNode, Graph
from tests.support.data import fixture_issues, source_element, write_input
from tests.support.rdf import (assert_selected_equal, cardinality_facts,
                               necessary_restrictions, property_expression)
from tests.support.invocation import (_observed_diagnostics, absent_attribute_property_type_error,
                                      diagnostic_signatures, unresolved_property_reference_between)
from tests.support.rdf import assert_graph_equal, rooted_graph, one_object

POLICIES = ['strict', 'tolerant', 'best-effort']
REFERENCE_FIELDS = ['subsettedProperties', 'redefinedProperties']
PROPERTY_TYPES = {OWL.ObjectProperty, OWL.DatatypeProperty, OWL.FunctionalProperty,
                  OWL.InverseFunctionalProperty, OWL.TransitiveProperty, OWL.SymmetricProperty,
                  OWL.AsymmetricProperty, OWL.ReflexiveProperty, OWL.IrreflexiveProperty}


def _reference(identifier):
    return {'id': identifier, 'type': 'Property'}


def _hierarchy(graph):
    result = set()
    for left, right in graph.subject_objects(RDFS.subPropertyOf):
        a, b = property_expression(graph, left), property_expression(graph, right)
        def local(expr):
            value = expr[1] if isinstance(expr, tuple) else expr
            return isinstance(value, URIRef) and str(value).startswith(str(BASE))
        if local(a) or local(b):
            result.add((a, b))
    return result


def _flag_values(result, subject, field):
    values = set()
    for comment in result.comments:
        if comment.subject == subject and comment.field == field:
            assert (comment.subject, RDFS.comment, comment.literal) in result.ontology
            values.add((comment.context, comment.value))
    return values


def _assert_flag_logic_equal(first, second, roots):
    assert_selected_equal(first.ontology, second.ontology,
                          {RDF.type, RDFS.domain, RDFS.range,
                           RDFS.subPropertyOf, OWL.equivalentProperty, OWL.propertyChainAxiom},
                          subjects=roots, type_objects=PROPERTY_TYPES | {OWL.Class})
    for kind in (OWL.ObjectProperty,OWL.DatatypeProperty):
        assert {s for s in first.ontology.subjects(RDF.type,kind) if isinstance(s,URIRef) and str(s).startswith(str(BASE))} == {
            s for s in second.ontology.subjects(RDF.type,kind) if isinstance(s,URIRef) and str(s).startswith(str(BASE))}
    for result in (first, second):
        assert not result.flag_semantic_output
        for root in roots:
            assert (root, RDF.type, RDF.Seq) not in result.ontology
            assert not list(result.ontology.objects(root, RDF.first))
            assert not list(result.ontology.objects(root, RDF.rest))


@pytest.mark.parametrize('field', REFERENCE_FIELDS, ids=['subsets', 'redefines'])
@pytest.mark.parametrize('ends', [('t1','t0'), ('s1','s0'), ('t1','s0'), ('s1','t0')],
                         ids=['target_to_target', 'source_to_source', 'target_to_source', 'source_to_target'])
@pytest.mark.parametrize('named0,named1', [(False,False),(True,False),(False,True),(True,True)],
                         ids=['both_anonymous', 'referenced_named', 'referencing_named', 'both_named'])
def test_each_end_reference_resolves_its_own_named_or_anonymous_expression(run, source_json, tmp_path, field, ends, named0, named1):
    """Rules: DK-PROP-03, DK-GEN-02, DK-IRI-06, DK-INV-01, DK-INV-04."""
    document = source_json('properties/references')
    source_element(document, 's0')['name'] = 'inverseZero' if named0 else None
    source_element(document, 's1')['name'] = 'inverseOne' if named1 else None
    source_element(document, ends[0])[field] = [_reference(ends[1])]
    assert not fixture_issues(document)
    result = run(path=write_input(tmp_path, document), iri_strategy='id', inverse_properties='named')
    assert result.outcome == 'completed'
    mapping = {'t0': BASE.t0, 't1': BASE.t1,
               's0': BASE.s0 if named0 else ('inverse', BASE.t0),
               's1': BASE.s1 if named1 else ('inverse', BASE.t1)}
    assert _hierarchy(result.ontology) == {(mapping[ends[0]], mapping[ends[1]])}
    for named, source, primary in [(named0, BASE.s0, BASE.t0),(named1, BASE.s1, BASE.t1)]:
        assert ((source, RDF.type, OWL.ObjectProperty) in result.ontology) == named
        if named:
            assert (source, OWL.inverseOf, primary) in result.ontology
    assert not any(d.kind in {'semantic_validation', 'redefinition_warning'} or d.severity == 'ERROR' for d in result.diagnostics)


@pytest.mark.parametrize('field', REFERENCE_FIELDS, ids=['subsets', 'redefines'])
@pytest.mark.parametrize('mode', ['all', 'none'])
@pytest.mark.parametrize('left,right', [
    ('pChild', 't0'),
    ('s1', 'pChild'),
    ('pBase', 'tData'),
    ('tData', 'pThird'),
    ('tData', 'tDataPeer'),
], ids=['object_attr_to_primary', 'object_inverse_to_attr', 'datatype_attr_to_rel', 'datatype_rel_to_attr', 'datatype_rel_to_rel'])
def test_same_kind_attribute_and_end_references_ignore_semantic_compatibility(
        run, source_json, tmp_path, field, mode, left, right):
    """Rules: DK-PROP-03, DK-GEN-02, DK-DIAG-02, DK-REL-01; §3.4 semantic compatibility boundary."""
    document = source_json('properties/references')
    uses_data_rel = 'tData' in (left, right)
    if uses_data_rel:
        d_string = copy.deepcopy(source_element(document, 'dInt'))
        d_string.update(id='dString', name='string')
        document['model']['contents'].append(d_string)
        r_data = copy.deepcopy(source_element(document, 'r0'))
        r_data.update(id='rData', name='hasData')
        r_data['properties'][0].update(id='sData', name=None, propertyType={'id': 'cA', 'type': 'Class'})
        r_data['properties'][1].update(id='tData', name='dataVal', propertyType={'id': 'dString', 'type': 'Class'})
        r_data_peer = copy.deepcopy(source_element(document, 'r0'))
        r_data_peer.update(id='rDataPeer', name='hasPeerData')
        r_data_peer['properties'][0].update(id='sDataPeer', name=None, propertyType={'id': 'cB', 'type': 'Class'})
        r_data_peer['properties'][1].update(id='tDataPeer', name='peerDataVal', propertyType={'id': 'dInt', 'type': 'Class'})
        document['model']['contents'].extend([r_data, r_data_peer])
    source_element(document, left)[field] = [_reference(right)]
    assert not fixture_issues(document)
    result = run(path=write_input(tmp_path, document), iri_strategy='id', inverse_properties=mode)
    assert result.outcome == 'completed'
    def expression(identifier):
        return ('inverse', BASE['t'+identifier[1:]]) if identifier.startswith('s') and mode == 'none' else BASE[identifier]
    assert _hierarchy(result.ontology) == {(expression(left), expression(right))}
    assert (BASE.pBase, RDF.type, OWL.DatatypeProperty) in result.ontology
    if uses_data_rel:
        assert (BASE.tData, RDF.type, OWL.DatatypeProperty) in result.ontology
        assert (BASE.tDataPeer, RDF.type, OWL.DatatypeProperty) in result.ontology
    assert (BASE.pThird, RDF.type, OWL.DatatypeProperty) in result.ontology
    assert (BASE.pChild, RDF.type, OWL.ObjectProperty) in result.ontology
    assert not any(d.kind in {'semantic_validation', 'redefinition_warning'} or d.severity == 'ERROR' for d in result.diagnostics)


@pytest.mark.parametrize('input_policy', POLICIES)
@pytest.mark.parametrize('field', REFERENCE_FIELDS, ids=['subsets', 'redefines'])
def test_attribute_inclusion_does_not_merge_replace_or_copy_constraints(run, source_json, tmp_path, input_policy, field):
    """Rules: DK-PROP-01, DK-PROP-03, DK-GEN-03, DK-GEN-02, DK-ATT-03, DK-DIAG-02; §3.4 semantic compatibility."""
    document = source_json('properties/references')
    d_string = copy.deepcopy(source_element(document, 'dInt'))
    d_string.update(id='dString', name='string')
    document['model']['contents'].append(d_string)
    source_element(document, 'pBase')['cardinality'] = '2..5'
    source_element(document, 'pChild').update(
        cardinality='0..1', propertyType={'id': 'dString', 'type': 'Class'}, **{field: [_reference('pBase')]})
    assert not fixture_issues(document)
    result = run(path=write_input(tmp_path, document), iri_strategy='id', input_policy=input_policy, inverse_properties='none')
    assert result.outcome == 'completed'
    assert _hierarchy(result.ontology) == {(BASE.pChild, BASE.pBase)}
    assert (BASE.pBase, RDF.type, OWL.DatatypeProperty) in result.ontology
    assert (BASE.pChild, RDF.type, OWL.DatatypeProperty) in result.ontology
    assert set(result.ontology.objects(BASE.pBase, RDFS.range)) == {XSD.int}
    assert set(result.ontology.objects(BASE.pChild, RDFS.range)) == {XSD.string}
    for prop in (BASE.pBase, BASE.pChild):
        assert set(result.ontology.objects(prop, RDFS.domain)) == {BASE.cOwner}
        assert not list(result.ontology.objects(prop, OWL.equivalentProperty))
        assert not list(result.ontology.objects(prop, OWL.sameAs))
    assert {(kind,n) for kind,n,_,_ in cardinality_facts(result.ontology,BASE.cOwner,BASE.pBase)} == {('min',2),('max',5)}
    assert {(kind,n) for kind,n,_,_ in cardinality_facts(result.ontology,BASE.cOwner,BASE.pChild)} == {('max',1)}
    assert not any(d.kind in {'semantic_validation','redefinition_warning'} or d.severity == 'ERROR' for d in result.diagnostics)


def test_every_reference_is_independent_deduplicated_and_not_transitively_closed(run, source_json, tmp_path):
    """Rules: DK-PROP-03, DK-GEN-02, DK-DIAG-05; §3.4 repeated references are not declarations."""
    document = source_json('properties/references')
    source_element(document,'pBase')['propertyType'] = {'id': 'cA', 'type': 'Class'}
    source_element(document,'pThird')['propertyType'] = {'id': 'dCustom', 'type': 'Class'}
    source_element(document,'pChild')['subsettedProperties'] = [_reference('pThird'),_reference('t0'),_reference('pThird')]
    source_element(document,'pChild')['redefinedProperties'] = [_reference('pThird')]
    source_element(document,'pThird')['redefinedProperties'] = [_reference('pBase')]
    assert not fixture_issues(document)
    result = run(path=write_input(tmp_path,document),iri_strategy='id')
    assert result.outcome == 'completed'
    assert _hierarchy(result.ontology) == {(BASE.pChild,BASE.pThird),(BASE.pChild,BASE.t0),(BASE.pThird,BASE.pBase)}
    assert not any(d.kind == 'duplicate_id' or d.severity == 'ERROR' for d in result.diagnostics)
    assert not list(result.ontology.triples((None,OWL.equivalentProperty,None)))


@pytest.mark.parametrize("field", REFERENCE_FIELDS, ids=["subsets", "redefines"])
@pytest.mark.parametrize("direction", ["towards_omitted", "from_omitted", "both"])
def test_absent_attribute_property_type_retains_only_applicable_reference_diagnostics(
        run, source_json, tmp_path, field, direction):
    """Rules: DK-ATT-01, DK-PROP-03, DK-DIAG-05. RD-02 Alternative A."""
    document = source_json("shared/core_model")
    owner = source_element(document, "cPerson")
    focus = source_element(document, "aAge")
    del focus["propertyType"]
    peer = copy.deepcopy(source_element(document, "aNote"))
    peer.update(id="aPeer", name="peer")
    owner["properties"].append(peer)

    note = source_element(document, "aNote")
    note[field] = [_reference("aPeer")]
    if direction in {"towards_omitted", "both"}:
        note[field].append(_reference("aAge"))
    if direction in {"from_omitted", "both"}:
        focus[field] = [_reference("aPeer")]
    assert not fixture_issues(document)
    result = run(path=write_input(tmp_path, document), iri_strategy="id", input_policy="best-effort")
    assert any(absent_attribute_property_type_error(event, "aAge") for event in result.diagnostics)
    assert result.outcome == "completed-with-errors"
    assert all(event.code != "INTERNAL_TRANSFORMATION_FAILURE" for event in result.diagnostics)
    incoming = [event for event in result.diagnostics if event.kind == "unresolved_property_reference"]
    if direction in {"towards_omitted", "both"}:
        assert incoming
        assert all(unresolved_property_reference_between(event, "aNote", field, "aAge")
                   for event in incoming)
    else:
        assert not incoming
    assert _hierarchy(result.ontology) == {(BASE.aNote, BASE.aPeer)}
    assert not any(BASE.aAge in triple for triple in result.ontology)
    for prop in (BASE.aNote, BASE.aPeer):
        assert (prop, RDF.type, OWL.DatatypeProperty) in result.ontology
        assert (prop, RDFS.domain, BASE.cPerson) in result.ontology


def test_absent_attribute_property_type_reference_reader_distinguishes_direction():
    """Rules: DK-PROP-03, DK-DIAG-04, DK-DIAG-05. Harness: permit relevant target locators."""
    from ontouml_directkg.diagnostics import Diagnostic, SourceLocation

    note, age, peer = (SourceLocation(f"$.model.contents[0].properties[{index}]", identifier, "Property")
                       for index, identifier in enumerate(("aNote", "aAge", "aPeer")))
    for field in REFERENCE_FIELDS:
        incoming = f"Property {field} reference {{'id': 'aAge', 'type': 'Property'}} cannot supply a property expression."
        outgoing = f"Property {field} reference {{'id': 'aPeer', 'type': 'Property'}} cannot supply a property expression."
        for message, sources, expected in (
            (incoming, (note,), True),
            (incoming, (note, age), True),
            (incoming, (age, note), True),
            (f"Property 'aNote' {field} reference to 'aAge' is unresolved.", (note, age), True),
            (incoming, (age,), False),
            (outgoing, (age, peer), False),
            (outgoing, (note, age, peer), False),
            (f"Property 'aAge' {field} reference to 'aAge' is unresolved.", (note, age), False),
            (f"Property {field} reference to 'aAgeOther' is unresolved.", (note, age), False),
        ):
            native = Diagnostic("ERROR", "UNRESOLVED_PROPERTY_REFERENCE", message, "Affected inclusion omitted.", sources)
            event, = _observed_diagnostics((native,))
            assert unresolved_property_reference_between(event, "aNote", field, "aAge") == expected, message


@pytest.mark.parametrize('input_policy', POLICIES)
@pytest.mark.parametrize('field', REFERENCE_FIELDS, ids=['subsets', 'redefines'])
@pytest.mark.parametrize('failure', ['unresolved', 'wrong_reference_type', 'referenced_failed', 'referencing_failed'])
def test_unresolved_or_failed_required_property_references_obey_policy(run, source_json, tmp_path, input_policy, field, failure):
    """Rules: DK-PROP-03, DK-DIAG-05, DK-DIAG-03, DK-GEN-03."""
    document = source_json('properties/references')
    source_element(document,'pBase')['propertyType'] = {'id': 'dCustom', 'type': 'Class'}
    source_element(document,'pChild')[field] = [_reference('pBase')]
    if failure == 'unresolved':
        source_element(document,'pChild')[field].append(_reference('missingProperty'))
        expected = {'unresolved_reference:missingProperty'}
    elif failure == 'wrong_reference_type':
        source_element(document,'pChild')[field].append(_reference('cA'))
        expected = {'reference_type_mismatch:cA'}
    else:
        source_element(document,'t1')['propertyType'] = None
        if failure == 'referenced_failed':
            source_element(document,'pChild')[field].append(_reference('s1'))
        else:
            source_element(document,'s1')[field] = [_reference('pBase')]
        expected = {'unresolved_endpoint'}
    assert fixture_issues(document) == expected
    result = run(path=write_input(tmp_path,document),iri_strategy='id',input_policy=input_policy)
    assert any(d.severity == 'ERROR' for d in result.diagnostics)
    if input_policy != 'best-effort':
        assert result.outcome == 'aborted' and result.ontology is None
    else:
        assert result.outcome == 'completed-with-errors'
        assert _hierarchy(result.ontology) == {(BASE.pChild,BASE.pBase)}
        assert (BASE.pBase,RDF.type,OWL.ObjectProperty) in result.ontology
        assert (BASE.pChild,RDF.type,OWL.ObjectProperty) in result.ontology
        for absent in (BASE.missingProperty,BASE.s1,BASE.t1) if failure in {'referenced_failed','referencing_failed'} else (BASE.missingProperty,):
            assert not any(absent in triple for triple in result.ontology)


@pytest.mark.parametrize('mode', ['all','none'])
def test_repeated_end_references_deduplicate_the_resulting_inclusion_axiom(run, source_json, tmp_path, mode):
    """Rules: DK-PROP-03, DK-GEN-02."""
    document=source_json('properties/references')
    source_element(document,'s1')['subsettedProperties']=[_reference('s0'),_reference('s0')]
    source_element(document,'s1')['redefinedProperties']=[_reference('s0')]
    result=run(path=write_input(tmp_path,document),iri_strategy='id',inverse_properties=mode)
    assert result.outcome=='completed'
    expected=(BASE.s1,BASE.s0) if mode=='all' else (('inverse',BASE.t1),('inverse',BASE.t0))
    edges=[(s,o) for s,o in result.ontology.subject_objects(RDFS.subPropertyOf)
           if (property_expression(result.ontology,s),property_expression(result.ontology,o))==expected]
    assert len(edges)==1
    assert _hierarchy(result.ontology)=={expected}


@pytest.mark.parametrize('input_policy', POLICIES)
@pytest.mark.parametrize('field', REFERENCE_FIELDS, ids=['subsets', 'redefines'])
@pytest.mark.parametrize('side', ['referencing', 'referenced'])
def test_intentionally_unrepresented_end_reference_does_not_create_a_property(run, source_json, tmp_path, input_policy, field, side):
    """Rules: DK-PROP-03, DK-REL-17, DK-INV-04, DK-GEN-01, DK-DIAG-05.

    Only RD-14's unavailable-expression boundary is credited here; the connector
    limitation's complete diagnostic/derivation matrix belongs to Wave 5.
    """
    document = source_json('shared/omitted_connector')
    left,right = ('sConnector','pBase') if side == 'referencing' else ('pChild','sConnector')
    source_element(document,left)[field] = [_reference(right)]
    assert not fixture_issues(document)
    result = run(path=write_input(tmp_path,document),iri_strategy='id',input_policy=input_policy)
    assert result.outcome == 'completed'
    assert not _hierarchy(result.ontology)
    for absent in (BASE.rConnector,BASE.sConnector,BASE.tConnector):
        assert not any(absent in triple for triple in result.ontology)
    assert (BASE.t0,RDF.type,OWL.ObjectProperty) in result.ontology
    assert (BASE.pBase,RDF.type,OWL.DatatypeProperty) in result.ontology
    assert not any(d.severity == 'ERROR' for d in result.diagnostics)


@pytest.mark.parametrize('field,state', [(field,state)
    for field in ('isDerived','isReadOnly','isOrdered')
    for state in ([True,False] if field=='isReadOnly' else [True,False,None,'absent'])],
    ids=[field+'_'+label for field in ('isDerived','isReadOnly','isOrdered')
         for label in (['true','false'] if field=='isReadOnly' else ['true','false','null','absent'])])
def test_attribute_source_flags_preserve_only_their_accepted_meaning(run, source_json, tmp_path, field, state):
    """Rules: DK-GEN-05, DK-PROP-04, DK-PROP-05, DK-DIAG-16, DK-DIAG-18, DK-ATT-01, DK-ATT-03."""
    document = source_json('properties/source_flags')
    source_element(document,'pFocus')['cardinality'] = '2..5'
    baseline = run(path=write_input(tmp_path,document,'baseline.json'),iri_strategy='id')
    focus = source_element(document,'pFocus')
    if state == 'absent': focus.pop(field,None)
    else: focus[field] = state
    result = run(path=write_input(tmp_path,document),iri_strategy='id')
    assert baseline.outcome == result.outcome == 'completed'
    _assert_flag_logic_equal(baseline,result,{BASE.pFocus,BASE.cOwner,BASE.tFlag,BASE.sFlag})
    values = {value for _,value in _flag_values(result,BASE.pFocus,field)}
    if field == 'isDerived' and isinstance(state,bool): assert values == {state}
    elif state is True: assert values == {True}
    elif field in {'isDerived','isOrdered'}: assert not values
    else: assert values <= {False}
    notices = [d for d in result.diagnostics if d.kind == ('derived_status' if field == 'isDerived' else 'ordering')]
    if field in {'isDerived','isOrdered'}:
        if state is True:
            assert any(d.severity == 'INFO' and 'pFocus' in d.identified_sources for d in notices)
            facts = {'preserved_as_annotation','no_derivation_rule_supplied'} if field == 'isDerived' else {'preserved_as_annotation','ordering_not_represented'}
            assert any(facts <= d.facts for d in notices)
        else: assert not notices
    assert {(kind,n) for kind,n,_,_ in cardinality_facts(result.ontology,BASE.cOwner,BASE.pFocus)} == {('min',2),('max',5)}
    assert not list(result.ontology.objects(BASE.cOwner,OWL.equivalentClass))
    for predicate in (OWL.someValuesFrom,OWL.allValuesFrom,OWL.hasValue):
        assert not list(result.ontology.triples((None,predicate,None)))
    assert not any(d.severity == 'ERROR' for d in result.diagnostics)
    assert not any(d.kind in {'derived_status','ordering'} and d.severity == 'WARNING' for d in result.diagnostics)


@pytest.mark.parametrize('kind', ['custom','untyped','void'])
def test_true_attribute_flags_apply_to_every_other_supported_value_kind(run, source_json, tmp_path, kind):
    """Rules: DK-GEN-05, DK-PROP-04, DK-PROP-05, DK-DAT-03, DK-DAT-04, DK-DAT-05, DK-DIAG-16, DK-DIAG-18."""
    document = source_json('properties/source_flags')
    focus=source_element(document,'pFocus')
    focus.update(isDerived=True,isReadOnly=True,isOrdered=True)
    if kind == 'untyped': focus['propertyType']=None
    else: source_element(document,'dValue')['name']='void' if kind == 'void' else 'CustomValue'
    result=run(path=write_input(tmp_path,document),iri_strategy='id')
    assert result.outcome=='completed'
    assert not result.flag_semantic_output
    for field in ('isDerived','isReadOnly','isOrdered'):
        assert {v for _,v in _flag_values(result,BASE.pFocus,field)}=={True}
    for category,fact in [('derived_status','no_derivation_rule_supplied'),('ordering','ordering_not_represented')]:
        assert any(d.kind==category and d.severity=='INFO' and 'pFocus' in d.identified_sources
                   and {'preserved_as_annotation',fact} <= d.facts for d in result.diagnostics)
    assert (BASE.pFocus,RDF.type,OWL.ObjectProperty if kind=='custom' else OWL.DatatypeProperty) in result.ontology
    assert set(result.ontology.objects(BASE.pFocus,RDFS.range))==({BASE.dValue} if kind=='custom' else set())
    assert not any(d.severity=='ERROR' for d in result.diagnostics)


@pytest.mark.parametrize('mode', ['all','none'])
@pytest.mark.parametrize('scenario', ['derived','read_only','aggregation','ordering','combined'])
def test_relation_and_end_flag_occurrences_stay_on_primary_without_changing_logic(run, source_json, tmp_path, mode, scenario):
    """Rules: DK-GEN-05, DK-PROP-04, DK-PROP-05, DK-DIAG-16, DK-DIAG-18, DK-GEN-03, DK-IRI-06."""
    document=source_json('properties/source_flags')
    baseline=run(path=write_input(tmp_path,document,'baseline.json'),iri_strategy='id',inverse_properties=mode)
    relation=source_element(document,'rFlag');source=source_element(document,'sFlag');target=source_element(document,'tFlag')
    expected={}
    if scenario in {'derived','combined'}:
        relation['isDerived']=scenario=='derived'
        source['isDerived']=scenario=='combined'
        target['isDerived']=True
        expected['isDerived']={('relation',relation['isDerived']),('source_end',source['isDerived']),('target_end',True)}
    if scenario in {'read_only','combined'}:
        source['isReadOnly']=target['isReadOnly']=True
        expected['isReadOnly']={('source_end',True),('target_end',True)}
    if scenario in {'aggregation','combined'}:
        source['aggregationKind']='SHARED';target['aggregationKind']='COMPOSITE'
        expected['aggregationKind']={('source_end','SHARED'),('target_end','COMPOSITE')}
    if scenario in {'ordering','combined'}:
        source['isOrdered']=target['isOrdered']=True
        expected['isOrdered']={('source_end',True),('target_end',True)}
    result=run(path=write_input(tmp_path,document),iri_strategy='id',inverse_properties=mode)
    assert baseline.outcome==result.outcome=='completed'
    _assert_flag_logic_equal(baseline,result,{BASE.pFocus,BASE.cOwner,BASE.cOther,BASE.tFlag,BASE.sFlag})
    assert set(result.ontology.objects(BASE.tFlag,RDFS.domain))=={BASE.cOwner}
    assert set(result.ontology.objects(BASE.tFlag,RDFS.range))=={BASE.cOther}
    for field,values in expected.items():
        assert _flag_values(result,BASE.tFlag,field)==values
        if field=='isDerived': assert not _flag_values(result,BASE.sFlag,field)
    assert ((BASE.sFlag,RDF.type,OWL.ObjectProperty) in result.ontology)==(mode=='all')
    for owner in (BASE.cOwner,BASE.cOther):
        assert not necessary_restrictions(result.ontology,owner)
        assert not list(result.ontology.objects(owner,OWL.equivalentClass))
    for field,kind,fact in [('isDerived','derived_status','no_derivation_rule_supplied'),('isOrdered','ordering','ordering_not_represented')]:
        sources=[item['id'] for item in (relation,source,target) if item.get(field) is True]
        events=[d for d in result.diagnostics if d.kind==kind]
        for identifier in sources:
            assert any(d.severity=='INFO' and identifier in d.identified_sources and {'preserved_as_annotation',fact} <= d.facts for d in events)
        if field=='isOrdered': assert len(events)>=len(sources)
        if not sources: assert not events
    assert not any(d.severity == 'ERROR' for d in result.diagnostics)
    assert not any(d.kind in {'derived_status','ordering'} and d.severity == 'WARNING' for d in result.diagnostics)


@pytest.mark.parametrize('state', [False,None,'absent'], ids=['false','null','absent'])
@pytest.mark.parametrize('mode', ['all','none'])
def test_absent_null_or_false_end_ordering_never_infers_order_or_loss_info(run, source_json, tmp_path, state, mode):
    """Rules: DK-PROP-05, DK-DIAG-18."""
    document=source_json('properties/source_flags')
    for identifier in ('sFlag','tFlag'):
        source=source_element(document,identifier)
        if state=='absent': source.pop('isOrdered')
        else: source['isOrdered']=state
    result=run(path=write_input(tmp_path,document),iri_strategy='id',inverse_properties=mode)
    assert result.outcome=='completed'
    assert not result.flag_semantic_output
    assert not _flag_values(result,BASE.tFlag,'isOrdered')
    assert not _flag_values(result,BASE.sFlag,'isOrdered')
    assert not any(d.kind=='ordering' for d in result.diagnostics)


@pytest.mark.parametrize('input_policy', POLICIES)
def test_source_flags_with_no_generated_target_do_not_create_resources_or_flag_info(run, source_json, tmp_path, input_policy):
    """Rules: DK-GEN-05, DK-PROP-04, DK-PROP-05, DK-DIAG-16, DK-DIAG-18, DK-REL-17."""
    document=source_json('shared/omitted_connector')
    for identifier in ('rConnector','sConnector','tConnector'):
        source_element(document,identifier)['isDerived']=True
    for identifier in ('sConnector','tConnector'):
        source_element(document,identifier).update(isReadOnly=True,isOrdered=True,aggregationKind='COMPOSITE')
    result=run(path=write_input(tmp_path,document),iri_strategy='id',input_policy=input_policy)
    assert result.outcome=='completed'
    assert not result.flag_semantic_output
    for absent in (BASE.rConnector,BASE.sConnector,BASE.tConnector): assert not any(absent in triple for triple in result.ontology)
    assert not any(d.kind in {'derived_status','ordering'} for d in result.diagnostics)
    assert not any(c.field in {'isReadOnly','isOrdered','aggregationKind'} for c in result.comments)
    assert not any(c.field=='isDerived' and c.value is True for c in result.comments)


def test_primitive_class_derived_flag_has_no_xsd_or_invented_annotation_target(run, source_json, tmp_path):
    """Rules: DK-GEN-05, DK-DIAG-16, DK-DAT-01, DK-ATT-01."""
    document=source_json('properties/source_flags')
    source_element(document,'dValue')['isDerived']=True
    source_element(document,'pFocus')['isDerived']=True
    result=run(path=write_input(tmp_path,document),iri_strategy='id')
    assert result.outcome=='completed'
    assert not result.flag_semantic_output
    assert {v for _,v in _flag_values(result,BASE.pFocus,'isDerived')}=={True}
    # Independent metadata is permitted; a primitive has no derived-status target.
    assert not _flag_values(result,XSD.int,"isDerived")
    assert not any(BASE.dValue in triple for triple in result.ontology)
    events=[d for d in result.diagnostics if d.kind=='derived_status']
    assert events and all('dValue' not in d.identified_sources for d in events)
    assert any('pFocus' in d.identified_sources for d in events)


def test_rdf_helper_property_expressions_require_an_actual_inverse_edge():
    """Harness only: inverse expressions are RDF evidence, not inferred aliases."""
    graph=Graph();inverse=BNode()
    graph.add((inverse,OWL.inverseOf,BASE.t0))
    assert property_expression(graph,inverse)==('inverse',BASE.t0)
    assert property_expression(graph,BASE.s0)==BASE.s0
    graph.add((inverse,OWL.inverseOf,BASE.t1))
    with pytest.raises(AssertionError): property_expression(graph,inverse)


@pytest.mark.parametrize('reference',['subsettedProperties','redefinedProperties'],ids=['subsets','redefines'])
@pytest.mark.parametrize('target,inverse_mode',[('attribute','all'),('target_end','none'),('source_end','all'),('source_end','none')],
                         ids=['attribute_superproperty','target_superproperty','named_inverse_superproperty','anonymous_inverse_superproperty'])
@pytest.mark.parametrize('mode',['none','omit-conflicting-constraints','preserve-conflicting-constraints'])
def test_emitted_chain_nonsimplicity_follows_property_references_without_materializing_inverse_edges(run,source_json,tmp_path,reference,target,inverse_mode,mode):
    """Rules: DK-PROP-03, DK-REL-07, DK-REL-09, DK-REL-10, DK-INV-04, DK-GEN-02, DK-DIAG-07, DK-ATT-01, DK-DAT-05.

    T4: use the supported custom-datatype attribute mapping while preserving
    the material pattern. RD-14 does not require matching property ranges.
    """
    import copy
    from tests.support.data import source_element,write_input,fixture_issues
    document=source_json('shared/material_pattern')
    datatype=copy.deepcopy(source_element(document,'cB'))
    datatype.update(id='dAffected',name='StructuredValue',stereotype='datatype')
    document['model']['contents'].append(datatype)
    attribute=copy.deepcopy(source_element(document,'sUnrelated'))
    attribute.update(id='pAffected',name='affectedValue',propertyType={'id':'dAffected','type':'Class'},cardinality='1..*',aggregationKind=None)
    safe=copy.deepcopy(attribute);safe.update(id='pSafe',name='safeValue',propertyType=None)
    source_element(document,'cExtra')['properties']=[attribute,safe]
    target_id='pAffected' if target=='attribute' else 'tUnrelated' if target=='target_end' else 'sUnrelated'
    source_element(document,'tMaterial')[reference]=[{'id':target_id,'type':'Property'}]
    assert not fixture_issues(document)
    result=run(path=write_input(tmp_path,document),iri_strategy='id',inverse_properties=inverse_mode,material_property_chains=mode)
    assert result.outcome=='completed'
    graph=result.ontology
    assert (BASE.dAffected,RDF.type,OWL.Class) in graph
    assert (BASE.pAffected,RDF.type,OWL.ObjectProperty) in graph
    assert (BASE.pAffected,RDFS.range,BASE.dAffected) in graph
    expected=BASE.pAffected if target=='attribute' else BASE.tUnrelated if target=='target_end' else (
        BASE.sUnrelated if inverse_mode=='all' else ('inverse',BASE.tUnrelated))
    edges={(property_expression(graph,a),property_expression(graph,b)) for a,b in graph.subject_objects(RDFS.subPropertyOf)}
    assert edges=={(BASE.tMaterial,expected)}
    assert bool(property_chains(graph,BASE.tMaterial))==(mode!='none')
    omit=mode=='omit-conflicting-constraints'
    facts=cardinality_facts(graph,BASE.cA,BASE.tMaterial)
    assert {(kind,n) for kind,n,_,_ in facts}==(set() if omit else {('min',2),('max',5)})
    assert all(q is None for _,_,q,_ in facts)
    if target=='attribute':
        facts=cardinality_facts(graph,BASE.cExtra,BASE.pAffected)
        assert {(kind,n) for kind,n,_,_ in facts}==(set() if omit else {('min',1)})
        assert (BASE.pAffected,RDF.type,OWL.ObjectProperty) in graph
        # An unaffected ordinary material relation must retain its restriction.
        assert {(k,n) for k,n,_,_ in cardinality_facts(graph,BASE.cA,BASE.tUnrelated)}=={('exact',4)}
    else:
        reverse=BASE.sUnrelated if inverse_mode=='all' else ('inverse',BASE.tUnrelated)
        assert {(k,n) for k,n,_,_ in cardinality_facts(graph,BASE.cA,BASE.tUnrelated)}==(set() if omit else {('exact',4)})
        assert {(k,n) for k,n,_,_ in cardinality_facts(graph,BASE.cExtra,reverse)}==(set() if omit else {('exact',1)})
    assert {(k,n) for k,n,_,_ in cardinality_facts(graph,BASE.cExtra,BASE.pSafe)}=={('min',1)}
    assert (BASE.pSafe,RDF.type,OWL.DatatypeProperty) in graph
    assert {(k,n) for k,n,_,_ in cardinality_facts(graph,BASE.cGround,BASE.tLeft)}=={('exact',1)}
    assert ((BASE.sMaterial,RDF.type,OWL.ObjectProperty) in graph)==(inverse_mode=='all')
    # The single RD-14 inclusion remains: no inferred inverse counterpart or
    # closure edge is emitted merely to perform non-simplicity propagation.
    if omit:
        assert any(d.kind=='chain_compatibility' and 'cardinalities_omitted' in d.facts for d in result.diagnostics)


def test_reference_superproperty_counts_remain_when_candidate_chain_is_not_emitted(run,source_json,tmp_path):
    """Rules: DK-PROP-03, DK-REL-07, DK-DIAG-07."""
    from tests.support.data import source_element,write_input
    document=source_json('shared/material_pattern')
    document['model']['contents'].remove(source_element(document,'rDerivation'))
    source_element(document,'tMaterial')['subsettedProperties']=[{'id':'sUnrelated','type':'Property'}]
    result=run(path=write_input(tmp_path,document),iri_strategy='id',inverse_properties='none',material_property_chains='omit-conflicting-constraints')
    assert result.outcome=='completed'
    assert not property_chains(result.ontology,BASE.tMaterial)
    assert {(k,n) for k,n,_,_ in cardinality_facts(result.ontology,BASE.cA,BASE.tUnrelated)}=={('exact',4)}
    assert {(k,n) for k,n,_,_ in cardinality_facts(result.ontology,BASE.cExtra,('inverse',BASE.tUnrelated))}=={('exact',1)}
    assert not any(d.kind=='chain_compatibility' for d in result.diagnostics)


@pytest.mark.parametrize('reference',['subsettedProperties','redefinedProperties'],ids=['subsets','redefines'])
@pytest.mark.parametrize('case,inverse_mode',[('inverse_origin','all'),('inverse_origin','none'),('simple_child','all')],
                         ids=['named_inverse_origin','anonymous_inverse_origin','simple_child_below_chain'])
def test_chain_propagation_uses_inverse_origins_but_does_not_spread_down_to_simple_children(run,source_json,tmp_path,reference,case,inverse_mode):
    """Rules: DK-PROP-03, DK-REL-07, DK-REL-09, DK-INV-04, DK-GEN-02."""
    from tests.support.data import source_element,write_input
    document=source_json('shared/material_pattern')
    if case=='inverse_origin':source_element(document,'sMaterial')[reference]=[{'id':'tUnrelated','type':'Property'}]
    else:source_element(document,'tUnrelated')[reference]=[{'id':'tMaterial','type':'Property'}]
    result=run(path=write_input(tmp_path,document),iri_strategy='id',inverse_properties=inverse_mode,material_property_chains='omit-conflicting-constraints')
    assert result.outcome=='completed'
    graph=result.ontology
    origin=BASE.sMaterial if inverse_mode=='all' else ('inverse',BASE.tMaterial)
    expected=(origin,BASE.tUnrelated) if case=='inverse_origin' else (BASE.tUnrelated,BASE.tMaterial)
    assert {(property_expression(graph,a),property_expression(graph,b)) for a,b in graph.subject_objects(RDFS.subPropertyOf)}=={expected}
    assert property_chains(graph,BASE.tMaterial)
    assert not cardinality_facts(graph,BASE.cA,BASE.tMaterial)
    assert {(k,n) for k,n,_,_ in cardinality_facts(graph,BASE.cA,BASE.tUnrelated)}==(set() if case=='inverse_origin' else {('exact',4)})
    reverse=BASE.sUnrelated if inverse_mode=='all' else ('inverse',BASE.tUnrelated)
    assert {(k,n) for k,n,_,_ in cardinality_facts(graph,BASE.cExtra,reverse)}==(set() if case=='inverse_origin' else {('exact',1)})


# RD-18 owns these integrated attribute/end annotation cases in the properties
# topic. Requests and RDF expectations do not prescribe comment prose.
_BOUNDARY_COUNTS={OWL.cardinality,OWL.minCardinality,OWL.maxCardinality,
                  OWL.qualifiedCardinality,OWL.minQualifiedCardinality,OWL.maxQualifiedCardinality}
_BOUNDARY_LOGIC={RDF.type,RDFS.domain,RDFS.range,RDFS.subClassOf,RDFS.subPropertyOf,
                 OWL.equivalentClass,OWL.equivalentProperty,OWL.disjointWith,OWL.propertyDisjointWith,
                 OWL.inverseOf,OWL.onProperty,OWL.onClass,OWL.onDataRange,OWL.someValuesFrom,
                 OWL.allValuesFrom,OWL.hasValue,OWL.hasSelf,OWL.intersectionOf,OWL.unionOf,
                 OWL.complementOf,OWL.oneOf,OWL.members,OWL.distinctMembers,OWL.propertyChainAxiom,
                 RDF.first,RDF.rest}|_BOUNDARY_COUNTS


def _boundary_resource(result,identifier,strategy):
    return BASE[identifier] if strategy=='id' else one_subject(result.ontology,DCTERMS.identifier,Literal(identifier))


def _boundary_logic_equal(first,second,strategy='id'):
    """Compare actual domain logic, allowing metadata and permitted count syntax."""
    projections=[];count_sets=[]
    types=PROPERTY_TYPES|{OWL.Class,OWL.NamedIndividual,OWL.Restriction,OWL.AllDifferent,OWL.AllDisjointClasses,OWL.AllDisjointProperties}
    for result in (first,second):
        graph=result.ontology
        identifiers=('cOwner','cOther','dValue','pFocus','tFlag','sFlag','vBoundary')
        roots={BASE[key] for key in identifiers} if strategy=='id' else {
            node for key in identifiers for node in graph.subjects(DCTERMS.identifier,Literal(key))}
        owners={node for node in roots if (node,RDF.type,OWL.Class) in graph}
        for owner in owners:
            for predicate in (RDFS.domain,RDFS.range):roots.update(graph.subjects(predicate,owner))
        count_nodes=set();counts=set()
        for owner in owners:
            expressions={property_expression(graph,one_object(graph,node,OWL.onProperty))
                         for node in necessary_restrictions(graph,owner)
                         if any((node,p,None) in graph for p in _BOUNDARY_COUNTS)}
            for expression in expressions:
                primary=expression[1] if isinstance(expression,tuple) else expression
                ranges=set(graph.objects(primary,RDFS.domain if isinstance(expression,tuple) else RDFS.range))
                universal=RDFS.Literal if (primary,RDF.type,OWL.DatatypeProperty) in graph else OWL.Thing
                for kind,number,qualifier,node in cardinality_facts(graph,owner,expression):
                    assert qualifier in ranges|{None,universal}
                    counts.add((owner,expression,kind,number));count_nodes.add(node)
        selected=rooted_graph(graph,roots,_BOUNDARY_LOGIC,type_objects=types)
        # Count meaning is compared separately. Retain any additional logical
        # statements on a count node instead of hiding an extra constraint.
        for node in count_nodes:
            selected.remove((None,RDFS.subClassOf,node))
            selected.remove((node,RDF.type,OWL.Restriction))
            for predicate in _BOUNDARY_COUNTS|{OWL.onProperty,OWL.onClass,OWL.onDataRange}:
                selected.remove((node,predicate,None))
        projections.append(selected);count_sets.append(counts)
    assert count_sets[0]==count_sets[1]
    assert_graph_equal(*projections)


def _boundary_annotations(invoke,result,expected):
    meanings=invoke.read_property_stereotype_comments(result)
    actual=set()
    for meaning in meanings:
        assert meaning.field=='stereotype' and meaning.value in {'begin','end'}
        assert isinstance(meaning.literal,Literal) and meaning.english is True
        assert meaning.literal.language is None or meaning.literal.language.lower().split('-')[0]=='en'
        assert (meaning.subject,RDFS.comment,meaning.literal) in result.ontology
        context='attribute' if meaning.context is None else meaning.context
        actual.add((meaning.subject,context,meaning.value))
    assert actual==set(expected)


@pytest.mark.parametrize('strategy,language',[('id','fr'),('name',None)],ids=['id_override','name_project_language'])
@pytest.mark.parametrize('kind',['primitive','untyped','custom','enumeration','void'])
@pytest.mark.parametrize('stereotype',['begin','end'])
def test_boundary_attribute_stereotypes_preserve_comments_and_existing_value_mappings(run,invoke,source_json,tmp_path,strategy,language,kind,stereotype):
    """Rules: DK-ATT-01, DK-ATT-03, DK-ATT-04, DK-DAT-01, DK-DAT-03, DK-DAT-04, DK-DAT-05, DK-PROP-04, DK-PROP-06, DK-LBL-02, DK-DIAG-06; RD-18 rules 1–5."""
    document=source_json('properties/source_flags');document['languages']=['nl']
    focus=source_element(document,'pFocus');focus.update(name='startTime',cardinality='2..5',stereotype=None)
    value=source_element(document,'dValue')
    if kind=='untyped':focus['propertyType']=None
    elif kind=='custom':value['name']='BoundaryValue'
    elif kind=='void':value['name']='void'
    elif kind=='enumeration':
        value.update(name='BoundaryState',stereotype='enumeration',literals=[{
            'id':'vBoundary','name':'recorded','description':None,'type':'Literal','propertyAssignments':None}])
    assert not fixture_issues(document)
    options={'iri_strategy':strategy,'language':language,'stereotype_policy':'require-known','inverse_properties':'none'}
    baseline=run(path=write_input(tmp_path,document,'baseline.json'),**options)
    focus['stereotype']=stereotype
    assert not fixture_issues(document)
    result=run(path=write_input(tmp_path,document),**options)
    assert result.outcome==baseline.outcome=='completed'
    _boundary_logic_equal(baseline,result,strategy)
    prop=_boundary_resource(result,'pFocus',strategy);owner=_boundary_resource(result,'cOwner',strategy)
    assert prop==_boundary_resource(baseline,'pFocus',strategy)
    assert set(baseline.ontology.objects(prop,RDFS.label))<=set(result.ontology.objects(prop,RDFS.label))
    object_kind=kind in {'custom','enumeration'}
    assert (prop,RDF.type,OWL.ObjectProperty if object_kind else OWL.DatatypeProperty) in result.ontology
    assert (prop,RDF.type,OWL.DatatypeProperty if object_kind else OWL.ObjectProperty) not in result.ontology
    expected_range={_boundary_resource(result,'dValue',strategy)} if object_kind else {XSD.int} if kind=='primitive' else set()
    assert set(result.ontology.objects(prop,RDFS.domain))=={owner}
    assert set(result.ontology.objects(prop,RDFS.range))==expected_range
    assert {(k,n) for k,n,_,_ in cardinality_facts(result.ontology,owner,prop)}=={('min',2),('max',5)}
    assert diagnostic_signatures(result.diagnostics)==diagnostic_signatures(baseline.diagnostics)
    assert any(d.kind=='void_datatype' and d.severity=='WARNING' for d in result.diagnostics)==(kind=='void')
    _boundary_annotations(invoke,result,{(prop,'attribute',stereotype)})


_BOUNDARY_END_PATTERNS=[('source_begin','begin',None),('source_end','end',None),
                        ('target_begin',None,'begin'),('target_end',None,'end'),
                        ('begin_end','begin','end'),('end_begin','end','begin'),
                        ('begin_begin','begin','begin'),('end_end','end','end')]
_BOUNDARY_END_CASES=[pytest.param(source,target,mode,'role',mode=='all',id=key+'-'+mode)
                     for key,source,target in _BOUNDARY_END_PATTERNS for mode in ('all','none')]
_BOUNDARY_END_CASES += [pytest.param('begin','end',mode,information,generated,id=mode+'-'+information)
                       for mode,information,generated in [('named','role',True),('named','absent',False),
                                                          ('informed','count',True),('informed','absent',False)]]


@pytest.mark.parametrize('source_stereo,target_stereo,mode,information,generated',_BOUNDARY_END_CASES)
def test_boundary_end_occurrences_stay_on_primary_independently_of_inverse_generation(run,invoke,source_json,tmp_path,source_stereo,target_stereo,mode,information,generated):
    """Rules: DK-REL-01, DK-REL-09, DK-REL-10, DK-REL-11, DK-REL-13, DK-INV-01, DK-INV-04, DK-PROP-04, DK-PROP-06, DK-PROP-05, DK-LBL-02; RD-18 rules 1–5."""
    document=source_json('properties/source_flags');document['languages']=['nl']
    source=source_element(document,'sFlag');target=source_element(document,'tFlag')
    source.update(stereotype=None,name='fromBoundary' if information=='role' else None,
                  cardinality='1' if information=='count' or mode in {'all','none'} else None)
    target.update(stereotype=None,name='toBoundary',cardinality='2..5')
    assert not fixture_issues(document)
    options={'iri_strategy':'id','language':'fr','inverse_properties':mode,'stereotype_policy':'require-known'}
    baseline=run(path=write_input(tmp_path,document,'baseline.json'),**options)
    source['stereotype']=source_stereo;target['stereotype']=target_stereo
    assert not fixture_issues(document)
    result=run(path=write_input(tmp_path,document),**options)
    assert result.outcome==baseline.outcome=='completed';graph=result.ontology
    _boundary_logic_equal(baseline,result)
    assert set(graph.objects(BASE.tFlag,RDFS.domain))=={BASE.cOwner}
    assert set(graph.objects(BASE.tFlag,RDFS.range))=={BASE.cOther}
    assert (BASE.tFlag,RDF.type,OWL.ObjectProperty) in graph
    assert set(baseline.ontology.objects(BASE.tFlag,RDFS.label))<=set(graph.objects(BASE.tFlag,RDFS.label))
    assert {node for node in graph.subjects(OWL.inverseOf,BASE.tFlag) if isinstance(node,URIRef)}==({BASE.sFlag} if generated else set())
    assert ((BASE.sFlag,RDF.type,OWL.ObjectProperty) in graph)==generated
    reverse=BASE.sFlag if generated else ('inverse',BASE.tFlag)
    if generated:
        assert set(graph.objects(BASE.sFlag,RDFS.domain))=={BASE.cOther}
        assert set(graph.objects(BASE.sFlag,RDFS.range))=={BASE.cOwner}
        assert (BASE.tFlag,OWL.inverseOf,BASE.sFlag) not in graph
    assert {(k,n) for k,n,q,_ in cardinality_facts(graph,BASE.cOwner,BASE.tFlag) if q is None}=={('min',2),('max',5)}
    source_counts=cardinality_facts(graph,BASE.cOther,reverse)
    assert {(k,n) for k,n,q,_ in source_counts}==({('exact',1)} if source['cardinality']=='1' else set())
    assert all(q is None for _,_,q,_ in source_counts)
    assert diagnostic_signatures(result.diagnostics)==diagnostic_signatures(baseline.diagnostics)
    expected={(BASE.tFlag,context,stereo) for context,stereo in [('source_end',source_stereo),('target_end',target_stereo)] if stereo is not None}
    _boundary_annotations(invoke,result,expected)


@pytest.mark.parametrize('identifier,state',[(None,'null'),('pFocus','absent'),('sFlag','absent'),('tFlag','absent')],
                         ids=['all_null','attribute_absent','source_end_absent','target_end_absent'])
def test_boundary_stereotypes_are_not_reconstructed_from_names_or_missing_fields(run,invoke,source_json,tmp_path,identifier,state):
    """Rules: DK-ATT-01, DK-REL-01, DK-PROP-04, DK-PROP-06, DK-LBL-02, DK-DIAG-06; RD-18 rules 3–5."""
    document=source_json('properties/source_flags')
    for key,name in [('pFocus','begin'),('sFlag','begin'),('tFlag','end')]:
        source_element(document,key).update(name=name,stereotype=None)
    baseline=run(path=write_input(tmp_path,document,'baseline.json'),iri_strategy='id',inverse_properties='all')
    if state=='absent':source_element(document,identifier).pop('stereotype')
    assert not fixture_issues(document)
    result=run(path=write_input(tmp_path,document),iri_strategy='id',inverse_properties='all')
    assert result.outcome==baseline.outcome=='completed'
    _boundary_logic_equal(baseline,result)
    assert diagnostic_signatures(result.diagnostics)==diagnostic_signatures(baseline.diagnostics)
    _boundary_annotations(invoke,result,set())


@pytest.mark.parametrize('occurrence',['attribute','ends'])
def test_boundary_preservation_adds_no_diagnostic_and_retains_existing_ordering_notice(run,invoke,source_json,tmp_path,occurrence):
    """Rules: DK-ATT-01, DK-REL-01, DK-PROP-04, DK-PROP-06, DK-PROP-05, DK-DIAG-18, DK-LBL-02; RD-18 rules 1–5."""
    document=source_json('properties/source_flags')
    identifier='pFocus' if occurrence=='attribute' else 'tFlag'
    source_element(document,identifier)['isOrdered']=True
    baseline=run(path=write_input(tmp_path,document,'baseline.json'),iri_strategy='id',inverse_properties='none')
    if occurrence=='attribute':
        source_element(document,'pFocus')['stereotype']='begin';expected={(BASE.pFocus,'attribute','begin')}
    else:
        source_element(document,'sFlag')['stereotype']='begin';source_element(document,'tFlag')['stereotype']='end'
        expected={(BASE.tFlag,'source_end','begin'),(BASE.tFlag,'target_end','end')}
    assert not fixture_issues(document)
    result=run(path=write_input(tmp_path,document),iri_strategy='id',inverse_properties='none')
    assert result.outcome==baseline.outcome=='completed'
    _boundary_logic_equal(baseline,result)
    assert any(d.kind=='ordering' and d.severity=='INFO' and identifier in d.identified_sources for d in result.diagnostics)
    assert diagnostic_signatures(result.diagnostics)==diagnostic_signatures(baseline.diagnostics)
    _boundary_annotations(invoke,result,expected)


@pytest.mark.parametrize('input_policy', POLICIES)
def test_class_valued_attribute_participates_in_owner_qualification_and_collisions(
        run, source_json, tmp_path, input_policy):
    """Rules: DK-ATT-01, DK-GEN-03, DK-PROP-01, DK-PROP-02, DK-REL-02, DK-IRI-07, DK-IRI-09, DK-INV-02."""
    document = source_json('properties/references')
    source_element(document, 'cA')['stereotype'] = 'kind'
    source_element(document, 'cB')['stereotype'] = 'category'
    attr_owner = source_element(document, 'pBase')
    attr_owner.update(name='related', propertyType={'id': 'cA', 'type': 'Class'})
    source_element(document, 'r0')['name'] = 'related'
    source_element(document, 't0')['name'] = 'related'
    attr_other = copy.deepcopy(attr_owner)
    attr_other.update(id='pOtherRel', name='related', propertyType={'id': 'cB', 'type': 'Class'})
    source_element(document, 'cA')['properties'] = [attr_other]
    assert not fixture_issues(document)

    result = run(path=write_input(tmp_path, document), iri_strategy='name', input_policy=input_policy)
    assert result.outcome == 'completed'
    graph = result.ontology
    p_base = one_subject(graph, DCTERMS.identifier, Literal('pBase'))
    p_other = one_subject(graph, DCTERMS.identifier, Literal('pOtherRel'))
    t_zero = one_subject(graph, DCTERMS.identifier, Literal('t0'))
    assert len({p_base, p_other, t_zero}) == 3
    assert {p_base, t_zero} == {BASE.related_Owner_1, BASE.related_Owner_2}
    assert p_other == BASE.related_A
    assert (p_base, RDF.type, OWL.ObjectProperty) in graph
    assert (p_other, RDF.type, OWL.ObjectProperty) in graph
    assert set(graph.objects(p_base, RDFS.domain)) == {BASE.Owner}
    assert set(graph.objects(p_base, RDFS.range)) == {BASE.A}
    assert set(graph.objects(p_other, RDFS.domain)) == {BASE.A}
    assert set(graph.objects(p_other, RDFS.range)) == {BASE.B}
    for attr in (p_base, p_other):
        assert not any(attr in pair for pair in graph.subject_objects(OWL.inverseOf))
    assert not any(d.severity in {'WARNING', 'ERROR'} for d in result.diagnostics)


@pytest.mark.parametrize('field', REFERENCE_FIELDS, ids=['subsets', 'redefines'])
@pytest.mark.parametrize('inverse_mode', ['all', 'none'])
def test_class_valued_attribute_property_references_resolve_object_properties_without_merging(
        run, source_json, tmp_path, field, inverse_mode):
    """Rules: DK-ATT-01, DK-PROP-01, DK-PROP-03, DK-GEN-02, DK-GEN-03, DK-ATT-03, DK-INV-02."""
    document = source_json('properties/references')
    source_element(document, 'cA')['stereotype'] = 'kind'
    source_element(document, 'cB')['stereotype'] = 'relator'
    source_element(document, 'pBase').update(
        cardinality='2..5', propertyType={'id': 'cA', 'type': 'Class'})
    source_element(document, 'pChild').update(
        cardinality='0..1', propertyType={'id': 'cB', 'type': 'Class'}, **{field: [_reference('pBase')]})
    source_element(document, 'pThird').update(
        cardinality='1', propertyType={'id': 'cA', 'type': 'Class'}, **{field: [_reference('s0')]})
    assert not fixture_issues(document)

    result = run(path=write_input(tmp_path, document), iri_strategy='id', inverse_properties=inverse_mode)
    assert result.outcome == 'completed'
    graph = result.ontology
    expected_s0 = BASE.s0 if inverse_mode == 'all' else ('inverse', BASE.t0)
    assert _hierarchy(graph) == {(BASE.pChild, BASE.pBase), (BASE.pThird, expected_s0)}
    for prop, target in ((BASE.pBase, BASE.cA), (BASE.pChild, BASE.cB), (BASE.pThird, BASE.cA)):
        assert (prop, RDF.type, OWL.ObjectProperty) in graph
        assert set(graph.objects(prop, RDFS.domain)) == {BASE.cOwner}
        assert set(graph.objects(prop, RDFS.range)) == {target}
        assert not any(prop in pair for pair in graph.subject_objects(OWL.inverseOf))
        assert not list(graph.objects(prop, OWL.equivalentProperty))
    assert {(kind, n) for kind, n, _, _ in cardinality_facts(graph, BASE.cOwner, BASE.pBase)} == {('min', 2), ('max', 5)}
    assert {(kind, n) for kind, n, _, _ in cardinality_facts(graph, BASE.cOwner, BASE.pChild)} == {('max', 1)}
    assert {(kind, n) for kind, n, _, _ in cardinality_facts(graph, BASE.cOwner, BASE.pThird)} == {('exact', 1)}
    assert not any(d.severity in {'WARNING', 'ERROR'} for d in result.diagnostics)


_MIXED_PROP_PAIRS = [
    pytest.param('pBase', 'pChild', id='attr_data_to_attr_obj'),
    pytest.param('pChild', 'pBase', id='attr_obj_to_attr_data'),
    pytest.param('pBase', 't0', id='attr_data_to_rel_obj_primary'),
    pytest.param('t1', 'pBase', id='rel_obj_primary_to_attr_data'),
    pytest.param('pBase', 's0', id='attr_data_to_rel_obj_inverse'),
    pytest.param('s1', 'pBase', id='rel_obj_inverse_to_attr_data'),
    pytest.param('tData', 't0', id='rel_data_to_rel_obj_primary'),
    pytest.param('t0', 'tData', id='rel_obj_primary_to_rel_data'),
    pytest.param('s0', 'tData', id='rel_obj_inverse_to_rel_data'),
]


@pytest.mark.parametrize('input_policy', POLICIES)
@pytest.mark.parametrize('field', REFERENCE_FIELDS, ids=['subsets', 'redefines'])
@pytest.mark.parametrize('mode', ['all', 'none'])
@pytest.mark.parametrize('left,right', _MIXED_PROP_PAIRS)
def test_mixed_kind_property_references_report_error_and_omit_only_incompatible_inclusion(
        run, source_json, tmp_path, input_policy, field, mode, left, right):
    """Rules: DK-PROP-03, DK-DIAG-02, DK-DIAG-04, DK-DIAG-05, DK-GEN-02, DK-GEN-03, DK-REL-01, DK-INV-04; §3.3, §3.4.

    RD-02 global DK-PROP-03 supersession: mixed owl:ObjectProperty /
    owl:DatatypeProperty inclusions fail with structural ERROR across
    attributes and relations; best-effort omits only the incompatible axiom
    while preserving independently valid properties and homogeneous inclusions.
    """
    document = source_json('properties/references')
    uses_data_rel = 'tData' in (left, right)
    if uses_data_rel:
        r_data = copy.deepcopy(source_element(document, 'r0'))
        r_data.update(id='rData', name='hasData')
        r_data['properties'][0].update(id='sData', name=None, propertyType={'id': 'cA', 'type': 'Class'})
        r_data['properties'][1].update(id='tData', name='dataVal', propertyType={'id': 'dInt', 'type': 'Class'})
        document['model']['contents'].append(r_data)
    # Keep a valid homogeneous inclusion alongside to verify partial recovery.
    source_element(document, 'pThird')[field] = [_reference('pBase')]
    source_element(document, left)[field] = list(source_element(document, left).get(field) or []) + [_reference(right)]
    assert not fixture_issues(document)

    result = run(path=write_input(tmp_path, document), iri_strategy='id',
                 input_policy=input_policy, inverse_properties=mode)
    assert any(
        d.severity == 'ERROR'
        and 'mixed_property_kind_inclusion' in d.facts
        and left in d.identified_sources
        and d.code != 'INTERNAL_TRANSFORMATION_FAILURE'
        for d in result.diagnostics
    ), result.diagnostics

    if input_policy != 'best-effort':
        assert result.outcome == 'aborted' and result.ontology is None
        return

    assert result.outcome == 'completed-with-errors'
    graph = result.ontology
    assert _hierarchy(graph) == {(BASE.pThird, BASE.pBase)}
    for prop in (BASE.pBase, BASE.pThird) + ((BASE.tData,) if uses_data_rel else ()):
        assert (prop, RDF.type, OWL.DatatypeProperty) in graph
        assert (prop, RDF.type, OWL.ObjectProperty) not in graph
    for prop in (BASE.pChild, BASE.t0, BASE.t1):
        assert (prop, RDF.type, OWL.ObjectProperty) in graph
        assert (prop, RDF.type, OWL.DatatypeProperty) not in graph
    # No orphaned anonymous inverse blank node may be emitted solely for a failed mixed inclusion.
    if mode == 'none':
        assert not any(isinstance(subj, BNode) for subj in graph.subjects(OWL.inverseOf, None))
    assert not any(BASE.sData in triple for triple in graph)


@pytest.mark.parametrize('input_policy', POLICIES)
@pytest.mark.parametrize('field', REFERENCE_FIELDS, ids=['subsets', 'redefines'])
@pytest.mark.parametrize('mode', ['all', 'none'])
@pytest.mark.parametrize('left,right', [
    ('sData', 'pBase'),
    ('sData', 't0'),
    ('pBase', 'sData'),
    ('t0', 'sData'),
    ('tData', 'sData'),
], ids=['source_to_data_attr', 'source_to_obj_primary', 'data_attr_to_source', 'obj_primary_to_source', 'data_target_to_source'])
def test_datatype_relation_source_end_in_property_reference_is_rejected_without_forcing_inverse(
        run, source_json, tmp_path, input_policy, field, mode, left, right):
    """Rules: DK-PROP-03, DK-REL-01, DK-INV-01, DK-INV-02, DK-INV-04, DK-DIAG-04, DK-DIAG-05.

    RD-02 Q5a: referencing or referenced source association end of a
    datatype-valued relation has no named or anonymous inverse and produces
    a structural ERROR; best-effort omits the incompatible inclusion while
    preserving the primary datatype property and valid homogeneous inclusions.
    """
    document = source_json('properties/references')
    r_data = copy.deepcopy(source_element(document, 'r0'))
    r_data.update(id='rData', name='hasData')
    r_data['properties'][0].update(id='sData', name=None, propertyType={'id': 'cA', 'type': 'Class'})
    r_data['properties'][1].update(id='tData', name='dataVal', propertyType={'id': 'dInt', 'type': 'Class'})
    document['model']['contents'].append(r_data)
    source_element(document, 'pThird')[field] = [_reference('pBase')]
    source_element(document, left)[field] = [_reference(right)]
    assert not fixture_issues(document)

    result = run(path=write_input(tmp_path, document), iri_strategy='id',
                 input_policy=input_policy, inverse_properties=mode)
    assert any(
        d.severity == 'ERROR'
        and 'unavailable_datatype_inverse_reference' in d.facts
        and left in d.identified_sources
        and d.code != 'INTERNAL_TRANSFORMATION_FAILURE'
        for d in result.diagnostics
    ), result.diagnostics

    if input_policy != 'best-effort':
        assert result.outcome == 'aborted' and result.ontology is None
        return

    assert result.outcome == 'completed-with-errors'
    graph = result.ontology
    assert _hierarchy(graph) == {(BASE.pThird, BASE.pBase)}
    assert (BASE.tData, RDF.type, OWL.DatatypeProperty) in graph
    assert set(graph.objects(BASE.tData, RDFS.domain)) == {BASE.cA}
    assert set(graph.objects(BASE.tData, RDFS.range)) == {XSD.int}
    assert not any(BASE.sData in triple for triple in graph)
    assert not any(
        obj == BASE.tData for subj, obj in graph.subject_objects(OWL.inverseOf)
    )


@pytest.mark.parametrize('mode', ['all', 'none'])
@pytest.mark.parametrize('strategy', ['id', 'name'])
def test_datatype_valued_relation_source_flags_and_boundary_stereotypes_stay_on_primary(
        run, invoke, source_json, tmp_path, mode, strategy):
    """Rules: DK-REL-01, DK-GEN-05, DK-CLS-01, DK-PROP-04, DK-PROP-05, DK-PROP-06, DK-DIAG-15, DK-DIAG-16, DK-DIAG-18, DK-INV-02.

    RD-02 Q7: compatible datatype-valued relations retain relation isAbstract,
    isDerived (relation/source/target), isReadOnly, comment-only SHARED/COMPOSITE
    aggregation on non-mereological relations, isOrdered + INFO, and begin/end
    stereotypes on the primary owl:DatatypeProperty without generating inverses.
    """
    document = source_json('properties/source_flags')
    for identifier in ('cOwner', 'cOther'):
        source_element(document, identifier).pop('isAbstract', None)
    source_element(document, 'rFlag').update(name='flagLink', stereotype='material', isAbstract=True, isDerived=True)
    source_element(document, 'sFlag').update(
        name=None, isDerived=False, isReadOnly=True, isOrdered=True,
        aggregationKind='SHARED', stereotype='begin')
    source_element(document, 'tFlag').update(
        name='targetFlag', propertyType={'id': 'dValue', 'type': 'Class'},
        isDerived=True, isReadOnly=True, isOrdered=True,
        aggregationKind='COMPOSITE', stereotype='end')
    assert not fixture_issues(document)

    result = run(path=write_input(tmp_path, document), iri_strategy=strategy, inverse_properties=mode)
    assert result.outcome == 'completed'
    assert not any(d.severity in {'WARNING', 'ERROR'} for d in result.diagnostics), result.diagnostics
    graph = result.ontology
    primary = BASE.tFlag if strategy == 'id' else one_subject(graph, DCTERMS.identifier, Literal('tFlag'))
    owner = BASE.cOwner if strategy == 'id' else BASE.Owner
    assert (primary, RDF.type, OWL.DatatypeProperty) in graph
    assert (primary, RDF.type, OWL.ObjectProperty) not in graph
    assert set(graph.objects(primary, RDFS.domain)) == {owner}
    assert set(graph.objects(primary, RDFS.range)) == {XSD.int}
    assert not any(primary in pair for pair in graph.subject_objects(OWL.inverseOf))
    assert not any(BASE.sFlag in triple for triple in graph)
    assert not any(BASE.dValue in triple for triple in graph)
    assert not list(graph.objects(primary, RDFS.subPropertyOf))
    assert (primary, RDF.type, OWL.AsymmetricProperty) not in graph
    assert not result.flag_semantic_output

    assert _flag_values(result, primary, 'isAbstract') == {('relation', True)}
    assert _flag_values(result, primary, 'isDerived') == {
        ('relation', True), ('source_end', False), ('target_end', True)}
    assert _flag_values(result, primary, 'isReadOnly') == {('source_end', True), ('target_end', True)}
    assert _flag_values(result, primary, 'aggregationKind') == {
        ('source_end', 'SHARED'), ('target_end', 'COMPOSITE')}
    assert _flag_values(result, primary, 'isOrdered') == {('source_end', True), ('target_end', True)}

    boundary = invoke.read_property_stereotype_comments(result)
    assert {(c.subject, c.context, c.value) for c in boundary if c.subject == primary} == {
        (primary, 'source_end', 'begin'), (primary, 'target_end', 'end')}
    assert any(d.kind == 'abstractness' and d.severity == 'INFO' and 'rFlag' in d.identified_sources
               for d in result.diagnostics)
    for source_id in ('rFlag', 'tFlag'):
        assert any(d.kind == 'derived_status' and d.severity == 'INFO' and source_id in d.identified_sources
                   for d in result.diagnostics)
    for source_id in ('sFlag', 'tFlag'):
        assert any(d.kind == 'ordering' and d.severity == 'INFO' and source_id in d.identified_sources
                   for d in result.diagnostics)


@pytest.mark.parametrize('input_policy', POLICIES)
@pytest.mark.parametrize('owner_kind', ['primitive', 'void'])
@pytest.mark.parametrize('field', REFERENCE_FIELDS, ids=['subsets', 'redefines'])
@pytest.mark.parametrize('scenario', [
    'surviving_attr_to_omitted',
    'surviving_end_to_omitted',
    'surviving_inverse_to_omitted',
    'omitted_to_surviving',
    'omitted_to_dangling',
    'omitted_malformed_container',
])
def test_best_effort_cleanly_omits_property_references_involving_primitive_or_void_owned_attributes(
        run, source_json, tmp_path, input_policy, owner_kind, field, scenario):
    """Rules: DK-PROP-03, DK-ATT-01, DK-CLS-01, DK-DAT-02, DK-DAT-04, DK-DIAG-01, DK-DIAG-05; RD-02 Alternative A."""
    document = source_json('properties/references')
    owner_dt = source_element(document, 'dInt')
    if owner_kind == 'void':
        owner_dt['name'] = 'void'
    owned = copy.deepcopy(source_element(document, 'pChild'))
    owned.update(id='pOwned', name='ownedAttr', propertyType={'id': 'dCustom', 'type': 'Class'})
    owner_dt['properties'] = [owned]

    expected_issues = set()
    if scenario == 'surviving_attr_to_omitted':
        source_element(document, 'pChild')[field] = [_reference('t0'), _reference('pOwned')]
        expected_hierarchy = {(BASE.pChild, BASE.t0)}
    elif scenario == 'surviving_end_to_omitted':
        source_element(document, 't0')[field] = [_reference('t1'), _reference('pOwned')]
        expected_hierarchy = {(BASE.t0, BASE.t1)}
    elif scenario == 'surviving_inverse_to_omitted':
        source_element(document, 's0')[field] = [_reference('s1'), _reference('pOwned')]
        expected_hierarchy = {(BASE.s0, BASE.s1)}
    elif scenario == 'omitted_to_surviving':
        owned[field] = [_reference('pChild')]
        expected_hierarchy = set()
    elif scenario == 'omitted_to_dangling':
        owned[field] = [_reference('missingProp')]
        expected_issues = {'unresolved_reference:missingProp'}
        expected_hierarchy = set()
    else:
        owned[field] = 'not-a-list'
        expected_issues = {'malformed_reference'}
        expected_hierarchy = set()

    assert fixture_issues(document) == expected_issues
    result = run(path=write_input(tmp_path, document), iri_strategy='id', input_policy=input_policy)
    assert all(d.code != 'INTERNAL_TRANSFORMATION_FAILURE' for d in result.diagnostics)
    assert any(
        d.severity == 'ERROR'
        and d.kind == 'attribute_owner_without_local_class'
        and 'attribute_owner_without_local_class' in d.facts
        and {'pOwned', 'dInt'} <= set(d.identified_sources)
        for d in result.diagnostics
    ), result.diagnostics
    assert not any(
        d.kind in {'unresolved_property_reference', 'invalid_property_references', 'property_inclusion_incompatibility'}
        or d.code in {'UNRESOLVED_PROPERTY_REFERENCE', 'INVALID_PROPERTY_REFERENCES', 'INCOMPATIBLE_PROPERTY_INCLUSION'}
        for d in result.diagnostics
    ), result.diagnostics

    if input_policy != 'best-effort':
        assert result.outcome == 'aborted' and result.ontology is None
        return

    assert result.outcome == 'completed-with-errors'
    graph = result.ontology
    assert _hierarchy(graph) == expected_hierarchy
    assert not any(BASE.pOwned in triple or BASE.dInt in triple for triple in graph)
    for prop in (BASE.pBase, BASE.pChild, BASE.t0, BASE.t1):
        assert any((prop, RDF.type, kind) in graph for kind in (OWL.ObjectProperty, OWL.DatatypeProperty))


@pytest.mark.parametrize('input_policy', POLICIES)
@pytest.mark.parametrize('field', REFERENCE_FIELDS, ids=['subsets', 'redefines'])
@pytest.mark.parametrize('boundary', [
    'target_omitted_by_unresolved_attribute_type',
    'surviving_dangling_with_omitted_owner_attr',
    'surviving_non_property_with_omitted_owner_attr',
    'surviving_malformed_container_with_omitted_owner_attr',
])
def test_best_effort_retains_property_reference_errors_outside_owner_omission_scope(
        run, source_json, tmp_path, input_policy, field, boundary):
    """Rules: DK-PROP-03, DK-ATT-01, DK-DIAG-01, DK-DIAG-05; RD-02 Alternative A."""
    document = source_json('properties/references')
    if boundary == 'target_omitted_by_unresolved_attribute_type':
        source_element(document, 'pBase')['propertyType'] = {'id': 'missingType', 'type': 'Class'}
        source_element(document, 'pChild')[field] = [_reference('t0'), _reference('pBase')]
        expected_issues = {'unresolved_reference:missingType'}
    else:
        owned = copy.deepcopy(source_element(document, 'pChild'))
        owned.update(id='pOwned', name='ownedAttr', propertyType={'id': 'dCustom', 'type': 'Class'})
        source_element(document, 'dInt')['properties'] = [owned]
        if boundary == 'surviving_dangling_with_omitted_owner_attr':
            source_element(document, 'pChild')[field] = [_reference('t0'), _reference('missingProp')]
            expected_issues = {'unresolved_reference:missingProp'}
        elif boundary == 'surviving_non_property_with_omitted_owner_attr':
            source_element(document, 'pChild')[field] = [_reference('t0'), _reference('cA')]
            expected_issues = {'reference_type_mismatch:cA'}
        else:
            source_element(document, 'pChild')[field] = 'not-a-list'
            expected_issues = {'malformed_reference'}

    assert fixture_issues(document) == expected_issues
    result = run(path=write_input(tmp_path, document), iri_strategy='id', input_policy=input_policy)
    assert all(d.code != 'INTERNAL_TRANSFORMATION_FAILURE' for d in result.diagnostics)

    if boundary == 'target_omitted_by_unresolved_attribute_type':
        assert any(d.severity == 'ERROR' and d.kind == 'unresolved_attribute_type'
                   and 'pBase' in d.identified_sources for d in result.diagnostics)
    else:
        assert any(d.severity == 'ERROR' and d.kind == 'attribute_owner_without_local_class'
                   and {'pOwned', 'dInt'} <= set(d.identified_sources) for d in result.diagnostics)

    if input_policy != 'best-effort':
        assert result.outcome == 'aborted' and result.ontology is None
        return

    assert result.outcome == 'completed-with-errors'
    expected_ref_kind = ('invalid_property_references'
                         if boundary == 'surviving_malformed_container_with_omitted_owner_attr'
                         else 'unresolved_property_reference')
    assert any(
        d.severity == 'ERROR' and d.kind == expected_ref_kind and 'pChild' in d.identified_sources
        for d in result.diagnostics
    ), result.diagnostics
    expected_hierarchy = (set() if boundary == 'surviving_malformed_container_with_omitted_owner_attr'
                          else {(BASE.pChild, BASE.t0)})
    assert _hierarchy(result.ontology) == expected_hierarchy


@pytest.mark.parametrize('input_policy', POLICIES)
@pytest.mark.parametrize('field', REFERENCE_FIELDS, ids=['subsets', 'redefines'])
@pytest.mark.parametrize('container_case', [
    'unary', 'n_ary', 'mixed_null_entry', 'mixed_class_entry', 'instantiation_malformed',
])
@pytest.mark.parametrize('scenario', [
    'surviving_attr_to_end',
    'surviving_end_to_end',
    'surviving_inverse_to_end',
    'end_to_surviving',
    'end_without_id_to_surviving',
    'end_without_id_dangling',
    'end_without_id_malformed_container',
])
def test_best_effort_cleanly_omits_property_references_involving_omitted_container_relations(
        run, source_json, tmp_path, input_policy, field, container_case, scenario):
    """Rules: DK-PROP-03, DK-DIAG-03, DK-DIAG-05, DK-INS-02, DK-INV-04. RD-02 Alternative A."""
    document = source_json('properties/references')
    r_omitted = copy.deepcopy(source_element(document, 'r0'))
    r_omitted.update(id='rOmitted', name='omittedLink')
    s_omitted, t_omitted = r_omitted['properties']
    s_omitted.update(id='sOmitted', name='omittedSrc')
    t_omitted.update(id='tOmitted', name='omittedTgt')
    e_third = copy.deepcopy(t_omitted)
    e_third.update(id='eThird', name='omittedThird')

    if scenario == 'surviving_attr_to_end':
        source_element(document, 'pChild')[field] = [_reference('t0'), _reference('tOmitted')]
        expected_hierarchy = {(BASE.pChild, BASE.t0)}
    elif scenario == 'surviving_end_to_end':
        source_element(document, 't0')[field] = [_reference('t1'), _reference('tOmitted')]
        expected_hierarchy = {(BASE.t0, BASE.t1)}
    elif scenario == 'surviving_inverse_to_end':
        source_element(document, 's0')[field] = [_reference('s1'), _reference('tOmitted')]
        expected_hierarchy = {(BASE.s0, BASE.s1)}
    elif scenario == 'end_to_surviving':
        source_element(document, 'pChild')[field] = [_reference('t0')]
        t_omitted[field] = [_reference('t0')]
        expected_hierarchy = {(BASE.pChild, BASE.t0)}
    elif scenario == 'end_without_id_to_surviving':
        source_element(document, 'pChild')[field] = [_reference('t0')]
        t_omitted.pop('id', None)
        t_omitted[field] = [_reference('t0')]
        expected_hierarchy = {(BASE.pChild, BASE.t0)}
    elif scenario == 'end_without_id_dangling':
        source_element(document, 'pChild')[field] = [_reference('t0')]
        t_omitted.pop('id', None)
        t_omitted[field] = [_reference('missingProp')]
        expected_hierarchy = {(BASE.pChild, BASE.t0)}
    else:
        source_element(document, 'pChild')[field] = [_reference('t0')]
        t_omitted.pop('id', None)
        t_omitted[field] = 'not-a-list'
        expected_hierarchy = {(BASE.pChild, BASE.t0)}

    if container_case == 'unary':
        r_omitted['properties'] = [t_omitted]
        expected_fact = 'relation_properties_non_binary'
    elif container_case == 'n_ary':
        r_omitted['properties'] = [s_omitted, t_omitted, e_third]
        expected_fact = 'relation_properties_non_binary'
    elif container_case == 'mixed_null_entry':
        r_omitted['properties'] = [None, t_omitted]
        expected_fact = 'relation_properties_malformed_entry'
    elif container_case == 'mixed_class_entry':
        fake_class = copy.deepcopy(source_element(document, 'cA'))
        fake_class['id'] = 'cFakeProp'
        r_omitted['properties'] = [fake_class, t_omitted]
        expected_fact = 'relation_properties_malformed_entry'
    else:
        r_omitted['stereotype'] = 'instantiation'
        r_omitted['properties'] = [None, t_omitted]
        expected_fact = 'relation_properties_malformed_entry'

    document['model']['contents'].append(r_omitted)
    result = run(path=write_input(tmp_path, document), iri_strategy='id',
                 input_policy=input_policy, inverse_properties='all')
    assert all(d.code != 'INTERNAL_TRANSFORMATION_FAILURE' for d in result.diagnostics), result.diagnostics
    assert any(
        d.severity == 'ERROR'
        and expected_fact in d.facts
        and 'rOmitted' in d.identified_sources
        for d in result.diagnostics
    ), result.diagnostics
    assert not any(
        d.kind in {'unresolved_property_reference', 'invalid_property_references',
                   'property_inclusion_incompatibility', 'discarded_instantiation_data'}
        or d.code in {'UNRESOLVED_PROPERTY_REFERENCE', 'INVALID_PROPERTY_REFERENCES', 'INCOMPATIBLE_PROPERTY_INCLUSION'}
        for d in result.diagnostics
    ), result.diagnostics

    if input_policy != 'best-effort':
        assert result.outcome == 'aborted' and result.ontology is None
        return

    assert result.outcome == 'completed-with-errors'
    graph = result.ontology
    assert _hierarchy(graph) == expected_hierarchy
    for absent in (BASE.rOmitted, BASE.sOmitted, BASE.tOmitted, BASE.eThird, BASE.cFakeProp):
        assert not any(absent in triple for triple in graph), absent
    for prop in (BASE.pBase, BASE.pChild, BASE.t0, BASE.s0, BASE.t1, BASE.s1):
        assert any((prop, RDF.type, kind) in graph for kind in (OWL.ObjectProperty, OWL.DatatypeProperty))


@pytest.mark.parametrize('input_policy', POLICIES)
@pytest.mark.parametrize('field', REFERENCE_FIELDS, ids=['subsets', 'redefines'])
@pytest.mark.parametrize('boundary', [
    'surviving_to_dangling',
    'surviving_to_non_property',
    'surviving_to_missing_end_of_null_rel',
    'surviving_malformed_container',
])
def test_best_effort_retains_property_reference_errors_alongside_omitted_container_relations(
        run, source_json, tmp_path, input_policy, field, boundary):
    """Rules: DK-PROP-03, DK-DIAG-03, DK-DIAG-05. RD-02 Alternative A."""
    document = source_json('properties/references')
    r_omitted = copy.deepcopy(source_element(document, 'r0'))
    r_omitted.update(id='rOmitted', name='omittedLink')
    s_omitted, t_omitted = r_omitted['properties']
    s_omitted['id'] = 'sOmitted'
    t_omitted['id'] = 'tOmitted'

    if boundary == 'surviving_to_missing_end_of_null_rel':
        r_omitted['properties'] = None
        source_element(document, 'pChild')[field] = [_reference('t0'), _reference('tOmitted')]
        expected_container_fact = 'relation_properties_null'
    else:
        e_third = copy.deepcopy(t_omitted)
        e_third['id'] = 'eThird'
        r_omitted['properties'] = [s_omitted, t_omitted, e_third]
        expected_container_fact = 'relation_properties_non_binary'
        if boundary == 'surviving_to_dangling':
            source_element(document, 'pChild')[field] = [_reference('t0'), _reference('missingProp')]
        elif boundary == 'surviving_to_non_property':
            source_element(document, 'pChild')[field] = [_reference('t0'), _reference('cA')]
        else:
            source_element(document, 'pChild')[field] = 'not-a-list'

    document['model']['contents'].append(r_omitted)
    result = run(path=write_input(tmp_path, document), iri_strategy='id',
                 input_policy=input_policy, inverse_properties='all')
    assert all(d.code != 'INTERNAL_TRANSFORMATION_FAILURE' for d in result.diagnostics), result.diagnostics
    assert any(
        d.severity == 'ERROR'
        and expected_container_fact in d.facts
        and 'rOmitted' in d.identified_sources
        for d in result.diagnostics
    ), result.diagnostics

    if input_policy != 'best-effort':
        assert result.outcome == 'aborted' and result.ontology is None
        return

    assert result.outcome == 'completed-with-errors'
    expected_ref_kind = ('invalid_property_references'
                         if boundary == 'surviving_malformed_container'
                         else 'unresolved_property_reference')
    assert any(
        d.severity == 'ERROR'
        and (d.kind == expected_ref_kind or d.code in {'UNRESOLVED_PROPERTY_REFERENCE', 'INVALID_PROPERTY_REFERENCES'})
        and 'pChild' in d.identified_sources
        for d in result.diagnostics
    ), result.diagnostics
    expected_hierarchy = set() if boundary == 'surviving_malformed_container' else {(BASE.pChild, BASE.t0)}
    assert _hierarchy(result.ontology) == expected_hierarchy
    assert not any(BASE.rOmitted in triple or BASE.tOmitted in triple for triple in result.ontology)


@pytest.mark.parametrize('input_policy', POLICIES)
@pytest.mark.parametrize('scope', ['root', 'nested'])
@pytest.mark.parametrize('field', REFERENCE_FIELDS, ids=['subsets', 'redefines'])
@pytest.mark.parametrize('scenario', [
    'surviving_attr_to_misplaced',
    'surviving_end_to_misplaced',
    'surviving_inverse_to_misplaced',
    'misplaced_to_surviving',
    'misplaced_to_dangling',
    'misplaced_malformed_container',
])
def test_best_effort_cleanly_omits_property_references_involving_misplaced_package_property(
        run, source_json, tmp_path, input_policy, scope, field, scenario):
    """Rules: DK-PROP-03, DK-GEN-06, DK-DIAG-01, DK-DIAG-05; RD-02 Alternatives 1A + 2A."""
    document = source_json('properties/references')
    misplaced = copy.deepcopy(source_element(document, 'pChild'))
    misplaced.update(id='pMisplaced', name='misplacedProp', propertyType={'id': 'dCustom', 'type': 'Class'})

    if scenario == 'surviving_attr_to_misplaced':
        source_element(document, 'pChild')[field] = [_reference('t0'), _reference('pMisplaced')]
        expected_hierarchy = {(BASE.pChild, BASE.t0)}
    elif scenario == 'surviving_end_to_misplaced':
        source_element(document, 't0')[field] = [_reference('t1'), _reference('pMisplaced')]
        expected_hierarchy = {(BASE.t0, BASE.t1)}
    elif scenario == 'surviving_inverse_to_misplaced':
        source_element(document, 's0')[field] = [_reference('s1'), _reference('pMisplaced')]
        expected_hierarchy = {(BASE.s0, BASE.s1)}
    elif scenario == 'misplaced_to_surviving':
        source_element(document, 'pChild')[field] = [_reference('t0')]
        misplaced[field] = [_reference('pChild')]
        expected_hierarchy = {(BASE.pChild, BASE.t0)}
    elif scenario == 'misplaced_to_dangling':
        source_element(document, 'pChild')[field] = [_reference('t0')]
        misplaced[field] = [_reference('missingProp')]
        expected_hierarchy = {(BASE.pChild, BASE.t0)}
    else:
        source_element(document, 'pChild')[field] = [_reference('t0')]
        misplaced[field] = 'not-a-list'
        expected_hierarchy = {(BASE.pChild, BASE.t0)}

    if scope == 'root':
        document['model']['contents'].append(misplaced)
    else:
        document['model']['contents'].append({
            'id': 'pNested', 'name': 'Nested', 'description': None,
            'type': 'Package', 'propertyAssignments': None,
            'contents': [misplaced],
        })

    result = run(path=write_input(tmp_path, document), iri_strategy='id',
                 input_policy=input_policy, inverse_properties='all')
    assert all(d.code != 'INTERNAL_TRANSFORMATION_FAILURE' for d in result.diagnostics), result.diagnostics
    assert any(
        d.severity == 'ERROR'
        and 'package_contents_misplaced_declaration' in d.facts
        for d in result.diagnostics
    ), result.diagnostics
    assert not any(
        d.kind in {'unresolved_property_reference', 'invalid_property_references', 'property_inclusion_incompatibility'}
        or d.code in {'UNRESOLVED_PROPERTY_REFERENCE', 'INVALID_PROPERTY_REFERENCES', 'INCOMPATIBLE_PROPERTY_INCLUSION'}
        for d in result.diagnostics
    ), result.diagnostics

    if input_policy != 'best-effort':
        assert result.outcome == 'aborted' and result.ontology is None
        return

    assert result.outcome == 'completed-with-errors'
    graph = result.ontology
    assert _hierarchy(graph) == expected_hierarchy
    assert not any(BASE.pMisplaced in triple for triple in graph)
    for prop in (BASE.pBase, BASE.pChild, BASE.t0, BASE.s0, BASE.t1, BASE.s1):
        assert any((prop, RDF.type, kind) in graph for kind in (OWL.ObjectProperty, OWL.DatatypeProperty))


@pytest.mark.parametrize('input_policy', POLICIES)
@pytest.mark.parametrize('field', REFERENCE_FIELDS, ids=['subsets', 'redefines'])
@pytest.mark.parametrize('boundary', [
    'non_property_in_class_properties',
    'misplaced_literal_in_package_contents',
    'untyped_entry_in_package_contents',
])
def test_best_effort_retains_unresolved_property_reference_for_unindexed_container_entries(
        run, source_json, tmp_path, input_policy, field, boundary):
    """Rules: DK-PROP-03, DK-GEN-06, DK-ATT-01, DK-DIAG-01, DK-DIAG-05; RD-02 Alts 2A + 3A."""
    document = source_json('properties/references')
    if boundary == 'non_property_in_class_properties':
        fake = copy.deepcopy(source_element(document, 'cA'))
        fake['id'] = 'fakeAttr'
        source_element(document, 'cOwner')['properties'].append(fake)
        source_element(document, 'pChild')[field] = [_reference('t0'), _reference('fakeAttr')]
        expected_entry_fact = 'class_properties_invalid_entry'
    elif boundary == 'misplaced_literal_in_package_contents':
        document['model']['contents'].append({
            'id': 'vMisplaced', 'name': 'MisplacedLit', 'description': None,
            'type': 'Literal', 'propertyAssignments': None,
        })
        source_element(document, 'pChild')[field] = [_reference('t0'), _reference('vMisplaced')]
        expected_entry_fact = 'package_contents_misplaced_declaration'
    else:
        document['model']['contents'].append({
            'id': 'uBad', 'name': 'Untyped', 'description': None,
            'type': None, 'propertyAssignments': None,
        })
        source_element(document, 'pChild')[field] = [_reference('t0'), _reference('uBad')]
        expected_entry_fact = 'package_contents_invalid_type'

    result = run(path=write_input(tmp_path, document), iri_strategy='id',
                 input_policy=input_policy, inverse_properties='all')
    assert all(d.code != 'INTERNAL_TRANSFORMATION_FAILURE' for d in result.diagnostics), result.diagnostics
    assert any(
        d.severity == 'ERROR' and expected_entry_fact in d.facts
        for d in result.diagnostics
    ), result.diagnostics

    if input_policy != 'best-effort':
        assert result.outcome == 'aborted' and result.ontology is None
        return

    assert result.outcome == 'completed-with-errors'
    assert any(
        d.severity == 'ERROR'
        and (d.kind == 'unresolved_property_reference' or d.code == 'UNRESOLVED_PROPERTY_REFERENCE')
        and 'pChild' in d.identified_sources
        for d in result.diagnostics
    ), result.diagnostics
    assert _hierarchy(result.ontology) == {(BASE.pChild, BASE.t0)}
    for omitted in (BASE.fakeAttr, BASE.vMisplaced, BASE.uBad):
        assert not any(omitted in triple for triple in result.ontology)


@pytest.mark.parametrize('input_policy', POLICIES)
@pytest.mark.parametrize('target', ['attribute', 'source_end', 'target_end'])
@pytest.mark.parametrize('bad_value', [pytest.param(False, id='bool_false'), pytest.param('', id='empty_string')])
def test_property_malformed_stereotype_omits_only_boundary_comment_and_preserves_inclusions(
        run, invoke, source_json, tmp_path, input_policy, target, bad_value):
    """Rules: DK-PROP-03, DK-PROP-04, DK-PROP-05, DK-PROP-06, DK-ATT-01, DK-REL-01, DK-DIAG-05; §3.2. RD-02 Alt 1C + Sub-option 2A."""
    document = source_json('properties/references')
    source_element(document, 'pChild').update(
        cardinality='1', isDerived=True, isReadOnly=True, isOrdered=True,
        subsettedProperties=[_reference('t0')],
    )
    source_element(document, 'pThird')['subsettedProperties'] = [_reference('pBase')]
    source_element(document, 's0').update(isDerived=True, isReadOnly=True, isOrdered=True, cardinality='0..1')
    source_element(document, 't0').update(isDerived=True, isReadOnly=True, isOrdered=True, cardinality='1..*')
    source_element(document, 's1')['stereotype'] = 'begin'
    source_element(document, 't1')['stereotype'] = 'end'

    target_id = {'attribute': 'pChild', 'source_end': 's0', 'target_end': 't0'}[target]
    source_element(document, target_id)['stereotype'] = bad_value

    result = run(path=write_input(tmp_path, document), iri_strategy='id',
                 input_policy=input_policy, inverse_properties='all')
    assert all(d.code != 'INTERNAL_TRANSFORMATION_FAILURE' for d in result.diagnostics), result.diagnostics
    assert any(
        d.severity == 'ERROR' and 'malformed_stereotype' in d.facts and target_id in d.identified_sources
        and d.code not in {'MISSING_STEREOTYPE', 'UNRECOGNIZED_STEREOTYPE', 'INTERNAL_TRANSFORMATION_FAILURE'}
        for d in result.diagnostics
    ), result.diagnostics

    if input_policy != 'best-effort':
        assert result.outcome == 'aborted' and result.ontology is None
        return

    assert result.outcome == 'completed-with-errors'
    graph = result.ontology
    assert _hierarchy(graph) == {(BASE.pChild, BASE.t0), (BASE.pThird, BASE.pBase)}
    assert (BASE.pChild, RDF.type, OWL.ObjectProperty) in graph
    assert (BASE.t0, RDF.type, OWL.ObjectProperty) in graph
    assert (BASE.s0, RDF.type, OWL.ObjectProperty) in graph
    _boundary_annotations(invoke, result, {(BASE.t1, 'source_end', 'begin'), (BASE.t1, 'target_end', 'end')})
    expected_subj = BASE.pChild if target == 'attribute' else BASE.t0
    assert len(list(graph.objects(expected_subj, RDFS.comment))) >= (3 if target == 'attribute' else 6)
    assert any(d.kind == 'derived_status' and d.severity == 'INFO' and target_id in d.identified_sources
               for d in result.diagnostics)
    assert any(d.kind == 'ordering' and d.severity == 'INFO' and target_id in d.identified_sources
               for d in result.diagnostics)


@pytest.mark.parametrize('input_policy', POLICIES)
@pytest.mark.parametrize('field', REFERENCE_FIELDS, ids=['subsets', 'redefines'])
@pytest.mark.parametrize('bad_value', [pytest.param(True, id='bool_true'), pytest.param('   ', id='whitespace_only')])
@pytest.mark.parametrize('scenario', [
    'surviving_attr_to_end',
    'surviving_end_to_end',
    'surviving_inverse_to_end',
    'end_to_surviving',
    'end_to_dangling',
])
def test_best_effort_cleanly_omits_property_references_involving_relation_omitted_for_malformed_stereotype(
        run, source_json, tmp_path, input_policy, field, bad_value, scenario):
    """Rules: DK-PROP-03, DK-DIAG-05, DK-INV-04. RD-02 Alt 1C + Sub-option 2A."""
    document = source_json('properties/references')
    r_omitted = copy.deepcopy(source_element(document, 'r0'))
    r_omitted.update(id='rOmitted', name='omittedLink', stereotype=bad_value)
    s_omitted, t_omitted = r_omitted['properties']
    s_omitted.update(id='sOmitted', name='omittedSrc')
    t_omitted.update(id='tOmitted', name='omittedTgt')

    if scenario == 'surviving_attr_to_end':
        source_element(document, 'pChild')[field] = [_reference('t0'), _reference('tOmitted')]
        expected_hierarchy = {(BASE.pChild, BASE.t0)}
    elif scenario == 'surviving_end_to_end':
        source_element(document, 't0')[field] = [_reference('t1'), _reference('tOmitted')]
        expected_hierarchy = {(BASE.t0, BASE.t1)}
    elif scenario == 'surviving_inverse_to_end':
        source_element(document, 's0')[field] = [_reference('s1'), _reference('tOmitted')]
        expected_hierarchy = {(BASE.s0, BASE.s1)}
    elif scenario == 'end_to_surviving':
        source_element(document, 'pChild')[field] = [_reference('t0')]
        t_omitted[field] = [_reference('t0')]
        expected_hierarchy = {(BASE.pChild, BASE.t0)}
    else:
        source_element(document, 'pChild')[field] = [_reference('t0')]
        t_omitted[field] = [_reference('missingProp')]
        expected_hierarchy = {(BASE.pChild, BASE.t0)}

    document['model']['contents'].append(r_omitted)
    result = run(path=write_input(tmp_path, document), iri_strategy='id',
                 input_policy=input_policy, inverse_properties='all')
    assert all(d.code != 'INTERNAL_TRANSFORMATION_FAILURE' for d in result.diagnostics), result.diagnostics
    assert any(
        d.severity == 'ERROR' and 'malformed_stereotype' in d.facts and 'rOmitted' in d.identified_sources
        for d in result.diagnostics
    ), result.diagnostics
    assert not any(
        d.kind in {'unresolved_property_reference', 'invalid_property_references', 'property_inclusion_incompatibility'}
        or d.code in {'UNRESOLVED_PROPERTY_REFERENCE', 'INVALID_PROPERTY_REFERENCES', 'INCOMPATIBLE_PROPERTY_INCLUSION'}
        for d in result.diagnostics
    ), result.diagnostics

    if input_policy != 'best-effort':
        assert result.outcome == 'aborted' and result.ontology is None
        return

    assert result.outcome == 'completed-with-errors'
    graph = result.ontology
    assert _hierarchy(graph) == expected_hierarchy
    for absent in (BASE.rOmitted, BASE.sOmitted, BASE.tOmitted):
        assert not any(absent in triple for triple in graph), absent
    for prop in (BASE.pBase, BASE.pChild, BASE.t0, BASE.s0, BASE.t1, BASE.s1):
        assert any((prop, RDF.type, kind) in graph for kind in (OWL.ObjectProperty, OWL.DatatypeProperty))


@pytest.mark.parametrize('input_policy', POLICIES)
@pytest.mark.parametrize('malformed_flag', ['isDerived', 'isReadOnly', 'isOrdered'])
@pytest.mark.parametrize('bad_value', [pytest.param('true', id='str_true'), pytest.param(1, id='int_one')])
def test_attribute_malformed_boolean_flag_omits_only_flag_and_preserves_siblings_and_inclusions(
        run, invoke, source_json, tmp_path, input_policy, malformed_flag, bad_value):
    """Rules: DK-GEN-05, DK-PROP-03, DK-PROP-04, DK-PROP-05, DK-PROP-06, DK-ATT-01, DK-ATT-03, DK-DIAG-05, DK-DIAG-16, DK-DIAG-18; §3.2. RD-02 Alternative 1."""
    document = source_json('properties/references')
    child = source_element(document, 'pChild')
    child.update(
        cardinality='2..5',
        stereotype='begin',
        isDerived=True,
        isReadOnly=True,
        isOrdered=True,
        subsettedProperties=[_reference('t0')],
    )
    source_element(document, 'pThird')['redefinedProperties'] = [_reference('pBase')]

    baseline_doc = copy.deepcopy(document)
    source_element(baseline_doc, 'pChild').pop(malformed_flag, None)
    child[malformed_flag] = bad_value

    result = run(path=write_input(tmp_path, document), iri_strategy='id',
                 input_policy=input_policy, inverse_properties='all')
    assert all(d.code != 'INTERNAL_TRANSFORMATION_FAILURE' for d in result.diagnostics), result.diagnostics
    assert any(
        d.severity == 'ERROR' and 'malformed_boolean_flag' in d.facts and 'pChild' in d.identified_sources
        for d in result.diagnostics
    ), result.diagnostics

    if input_policy != 'best-effort':
        assert result.outcome == 'aborted' and result.ontology is None
        return

    assert result.outcome == 'completed-with-errors'
    baseline = run(path=write_input(tmp_path, baseline_doc, 'baseline.json'),
                   iri_strategy='id', input_policy='tolerant', inverse_properties='all')
    assert baseline.outcome == 'completed'
    assert_graph_equal(result.ontology, baseline.ontology)

    graph = result.ontology
    assert (BASE.pChild, RDF.type, OWL.ObjectProperty) in graph
    assert _hierarchy(graph) == {(BASE.pChild, BASE.t0), (BASE.pThird, BASE.pBase)}
    assert {(kind, n) for kind, n, _, _ in cardinality_facts(graph, BASE.cOwner, BASE.pChild)} == {('min', 2), ('max', 5)}
    _boundary_annotations(invoke, result, {(BASE.pChild, 'attribute', 'begin')})

    derived_events = [d for d in result.diagnostics if d.kind == 'derived_status' and 'pChild' in d.identified_sources]
    ordering_events = [d for d in result.diagnostics if d.kind == 'ordering' and 'pChild' in d.identified_sources]
    assert bool(derived_events) == (malformed_flag != 'isDerived')
    assert bool(ordering_events) == (malformed_flag != 'isOrdered')


@pytest.mark.parametrize('input_policy', POLICIES)
@pytest.mark.parametrize('mode', ['all', 'none'])
@pytest.mark.parametrize('target_id,malformed_flag', [
    ('rFlag', 'isAbstract'),
    ('rFlag', 'isDerived'),
    ('sFlag', 'isDerived'),
    ('sFlag', 'isReadOnly'),
    ('sFlag', 'isOrdered'),
    ('tFlag', 'isDerived'),
    ('tFlag', 'isReadOnly'),
    ('tFlag', 'isOrdered'),
], ids=[
    'relation-isAbstract', 'relation-isDerived',
    'source_end-isDerived', 'source_end-isReadOnly', 'source_end-isOrdered',
    'target_end-isDerived', 'target_end-isReadOnly', 'target_end-isOrdered',
])
def test_relation_and_end_malformed_boolean_flag_omits_only_flag_and_preserves_siblings(
        run, invoke, source_json, tmp_path, input_policy, mode, target_id, malformed_flag):
    """Rules: DK-CLS-01, DK-GEN-05, DK-PROP-04, DK-PROP-05, DK-PROP-06, DK-REL-01, DK-REL-09, DK-REL-10, DK-DIAG-05, DK-DIAG-15, DK-DIAG-16, DK-DIAG-18; §3.2. RD-02 Alternative 1."""
    document = source_json('properties/source_flags')
    for cid in ('cOwner', 'cOther'):
        source_element(document, cid).pop('isAbstract', None)
    source_element(document, 'rFlag').update(isAbstract=True, isDerived=True, description='REL_DESC')
    source_element(document, 'sFlag').update(
        isDerived=True, isReadOnly=True, isOrdered=True,
        aggregationKind='SHARED', stereotype='begin', cardinality='1',
    )
    source_element(document, 'tFlag').update(
        isDerived=True, isReadOnly=True, isOrdered=True,
        aggregationKind='COMPOSITE', stereotype='end', cardinality='2..5',
    )

    baseline_doc = copy.deepcopy(document)
    source_element(baseline_doc, target_id).pop(malformed_flag, None)
    source_element(document, target_id)[malformed_flag] = 'true' if malformed_flag != 'isOrdered' else 1

    input_path = write_input(tmp_path, document)
    result = run(path=input_path, iri_strategy='id', input_policy=input_policy, inverse_properties=mode)
    assert all(d.code != 'INTERNAL_TRANSFORMATION_FAILURE' for d in result.diagnostics), result.diagnostics
    assert any(
        d.severity == 'ERROR' and 'malformed_boolean_flag' in d.facts and target_id in d.identified_sources
        for d in result.diagnostics
    ), result.diagnostics

    if input_policy != 'best-effort':
        assert result.outcome == 'aborted' and result.ontology is None
        return

    assert result.outcome == 'completed-with-errors'
    baseline = run(path=write_input(tmp_path, baseline_doc, 'baseline.json'),
                   iri_strategy='id', input_policy='tolerant', inverse_properties=mode)
    assert baseline.outcome == 'completed'
    assert_graph_equal(result.ontology, baseline.ontology)

    graph = result.ontology
    assert (BASE.tFlag, RDF.type, OWL.ObjectProperty) in graph
    assert ((BASE.sFlag, RDF.type, OWL.ObjectProperty) in graph) == (mode == 'all')
    assert Literal('REL_DESC') in set(graph.objects(BASE.tFlag, RDFS.comment))
    assert {(kind, n) for kind, n, _, _ in cardinality_facts(graph, BASE.cOwner, BASE.tFlag)} == {('min', 2), ('max', 5)}
    _boundary_annotations(invoke, result, {(BASE.tFlag, 'source_end', 'begin'), (BASE.tFlag, 'target_end', 'end')})
    agg_comments = invoke.read_relation_aggregation_comments(result, input_path)
    assert {(c.subject, c.context, c.value) for c in agg_comments} == {
        (BASE.tFlag, 'source_end', 'SHARED'),
        (BASE.tFlag, 'target_end', 'COMPOSITE'),
    }

    abstract_events = [d for d in result.diagnostics if d.kind == 'abstractness' and 'rFlag' in d.identified_sources]
    assert bool(abstract_events) != (target_id == 'rFlag' and malformed_flag == 'isAbstract')
    for occ_id in ('rFlag', 'sFlag', 'tFlag'):
        occ_derived = [d for d in result.diagnostics if d.kind == 'derived_status' and occ_id in d.identified_sources]
        assert bool(occ_derived) != (target_id == occ_id and malformed_flag == 'isDerived')
    for end_id in ('sFlag', 'tFlag'):
        occ_ordered = [d for d in result.diagnostics if d.kind == 'ordering' and end_id in d.identified_sources]
        assert bool(occ_ordered) != (target_id == end_id and malformed_flag == 'isOrdered')


@pytest.mark.parametrize('input_policy', POLICIES)
@pytest.mark.parametrize('target_id,malformed_flag', [
    ('sFlag', 'isDerived'),
    ('sFlag', 'isReadOnly'),
    ('sFlag', 'isOrdered'),
    ('tFlag', 'isDerived'),
    ('tFlag', 'isReadOnly'),
    ('tFlag', 'isOrdered'),
], ids=[
    'source_end-isDerived', 'source_end-isReadOnly', 'source_end-isOrdered',
    'target_end-isDerived', 'target_end-isReadOnly', 'target_end-isOrdered',
])
def test_datatype_valued_relation_end_malformed_boolean_flag_omits_only_flag_and_preserves_primary(
        run, source_json, tmp_path, input_policy, target_id, malformed_flag):
    """Rules: DK-REL-01, DK-GEN-05, DK-CLS-01, DK-PROP-04, DK-PROP-05, DK-DIAG-05, DK-DIAG-15, DK-DIAG-16, DK-DIAG-18; §3.2. RD-02 Alternative 1."""
    document = source_json('properties/source_flags')
    for cid in ('cOwner', 'cOther'):
        source_element(document, cid).pop('isAbstract', None)
    source_element(document, 'rFlag').update(name='flagLink', stereotype='material', isAbstract=True, isDerived=True)
    source_element(document, 'sFlag').update(
        name=None, isDerived=True, isReadOnly=True, isOrdered=True, aggregationKind='SHARED')
    source_element(document, 'tFlag').update(
        name='targetFlag', propertyType={'id': 'dValue', 'type': 'Class'},
        isDerived=True, isReadOnly=True, isOrdered=True, aggregationKind='COMPOSITE')

    baseline_doc = copy.deepcopy(document)
    source_element(baseline_doc, target_id).pop(malformed_flag, None)
    source_element(document, target_id)[malformed_flag] = 0

    result = run(path=write_input(tmp_path, document), iri_strategy='id',
                 input_policy=input_policy, inverse_properties='all')
    assert all(d.code != 'INTERNAL_TRANSFORMATION_FAILURE' for d in result.diagnostics), result.diagnostics
    assert any(
        d.severity == 'ERROR' and 'malformed_boolean_flag' in d.facts and target_id in d.identified_sources
        for d in result.diagnostics
    ), result.diagnostics

    if input_policy != 'best-effort':
        assert result.outcome == 'aborted' and result.ontology is None
        return

    assert result.outcome == 'completed-with-errors'
    baseline = run(path=write_input(tmp_path, baseline_doc, 'baseline.json'),
                   iri_strategy='id', input_policy='tolerant', inverse_properties='all')
    assert baseline.outcome == 'completed'
    assert_graph_equal(result.ontology, baseline.ontology)

    graph = result.ontology
    assert (BASE.tFlag, RDF.type, OWL.DatatypeProperty) in graph
    assert set(graph.objects(BASE.tFlag, RDFS.domain)) == {BASE.cOwner}
    assert set(graph.objects(BASE.tFlag, RDFS.range)) == {XSD.int}
    assert not any(BASE.sFlag in triple for triple in graph)
    assert any(d.kind == 'abstractness' and 'rFlag' in d.identified_sources for d in result.diagnostics)
    for end_id in ('sFlag', 'tFlag'):
        occ_derived = [d for d in result.diagnostics if d.kind == 'derived_status' and end_id in d.identified_sources]
        occ_ordered = [d for d in result.diagnostics if d.kind == 'ordering' and end_id in d.identified_sources]
        assert bool(occ_derived) != (target_id == end_id and malformed_flag == 'isDerived')
        assert bool(occ_ordered) != (target_id == end_id and malformed_flag == 'isOrdered')

