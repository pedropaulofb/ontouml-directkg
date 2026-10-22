"""Shared property identity, property references, and source characteristics."""

import pytest
from rdflib import Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, XSD

from tests.support.rdf import one_subject


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
@pytest.mark.parametrize('left,right', [('pChild','t0'),('pBase','s0'),('t1','pBase'),('s1','pChild')],
                         ids=['attribute_to_primary', 'attribute_to_inverse', 'primary_to_attribute', 'inverse_to_attribute'])
def test_attribute_and_end_references_ignore_semantic_property_kind_compatibility(run, source_json, tmp_path, field, mode, left, right):
    """Rules: DK-PROP-03, DK-GEN-02, DK-DIAG-02; §3.4 property-kind compatibility boundary."""
    document = source_json('properties/references')
    source_element(document, left)[field] = [_reference(right)]
    result = run(path=write_input(tmp_path, document), iri_strategy='id', inverse_properties=mode)
    assert result.outcome == 'completed'
    def expression(identifier):
        return ('inverse', BASE['t'+identifier[1:]]) if identifier.startswith('s') and mode == 'none' else BASE[identifier]
    assert _hierarchy(result.ontology) == {(expression(left), expression(right))}
    assert (BASE.pBase, RDF.type, OWL.DatatypeProperty) in result.ontology
    assert (BASE.pChild, RDF.type, OWL.ObjectProperty) in result.ontology
    assert not any(d.kind in {'semantic_validation', 'redefinition_warning'} or d.severity == 'ERROR' for d in result.diagnostics)


@pytest.mark.parametrize('input_policy', POLICIES)
@pytest.mark.parametrize('field', REFERENCE_FIELDS, ids=['subsets', 'redefines'])
def test_attribute_inclusion_does_not_merge_replace_or_copy_constraints(run, source_json, tmp_path, input_policy, field):
    """Rules: DK-PROP-01, DK-PROP-03, DK-GEN-03, DK-GEN-02, DK-ATT-03, DK-DIAG-02; §3.4 semantic compatibility."""
    document = source_json('properties/references')
    source_element(document, 'pBase')['cardinality'] = '2..5'
    source_element(document, 'pChild')['cardinality'] = '0..1'
    source_element(document, 'pChild')[field] = [_reference('pBase')]
    result = run(path=write_input(tmp_path, document), iri_strategy='id', input_policy=input_policy, inverse_properties='none')
    assert result.outcome == 'completed'
    assert _hierarchy(result.ontology) == {(BASE.pChild, BASE.pBase)}
    assert (BASE.pBase, RDF.type, OWL.DatatypeProperty) in result.ontology
    assert (BASE.pChild, RDF.type, OWL.ObjectProperty) in result.ontology
    assert set(result.ontology.objects(BASE.pBase, RDFS.range)) == {XSD.int}
    assert set(result.ontology.objects(BASE.pChild, RDFS.range)) == {BASE.dCustom}
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
    source_element(document,'pChild')['subsettedProperties'] = [_reference('pThird'),_reference('t0'),_reference('pThird')]
    source_element(document,'pChild')['redefinedProperties'] = [_reference('pThird')]
    source_element(document,'pThird')['redefinedProperties'] = [_reference('pBase')]
    assert not fixture_issues(document)
    result = run(path=write_input(tmp_path,document),iri_strategy='id')
    assert result.outcome == 'completed'
    assert _hierarchy(result.ontology) == {(BASE.pChild,BASE.pThird),(BASE.pChild,BASE.t0),(BASE.pThird,BASE.pBase)}
    assert not any(d.kind == 'duplicate_id' or d.severity == 'ERROR' for d in result.diagnostics)
    assert not list(result.ontology.triples((None,OWL.equivalentProperty,None)))


@pytest.mark.parametrize('input_policy', POLICIES)
@pytest.mark.parametrize('field', REFERENCE_FIELDS, ids=['subsets', 'redefines'])
@pytest.mark.parametrize('failure', ['unresolved', 'wrong_reference_type', 'referenced_failed', 'referencing_failed'])
def test_unresolved_or_failed_required_property_references_obey_policy(run, source_json, tmp_path, input_policy, field, failure):
    """Rules: DK-PROP-03, DK-DIAG-05, DK-DIAG-03, DK-GEN-03."""
    document = source_json('properties/references')
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
        assert (BASE.pBase,RDF.type,OWL.DatatypeProperty) in result.ontology
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
    document = source_json('properties/omitted_connector')
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
    document=source_json('properties/omitted_connector')
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
