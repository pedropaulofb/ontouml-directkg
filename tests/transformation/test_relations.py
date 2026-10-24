"""Ordinary relation naming, labels, cardinalities and explicit hierarchies."""

import copy
import pytest
from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, XSD

from tests.support.data import fixture_issues, source_element, write_input
from tests.support.rdf import (assert_contains, cardinality_facts, load_graph,
                               necessary_restrictions, one_subject, property_chains)

BASE = Namespace('https://example.test/model#')
POLICIES = ['strict', 'tolerant', 'best-effort']
NAMING_KINDS = {'relation_naming', 'stereotype_naming', 'comparative_naming',
                'unavailable_grounding_relator', 'relator_naming', 'missing_name',
                'generic_id_fallback', 'owner_qualification'}


def _primary(result, identifier='tFocus', strategy='id'):
    return BASE[identifier] if strategy == 'id' else one_subject(result.ontology, DCTERMS.identifier, Literal(identifier))


def _candidate(graph, prop, candidates, source_name):
    # PROP-02 permits optional owner qualification for unique properties.
    allowed = {BASE[name] for name in candidates} | {BASE[name+'_'+source_name] for name in candidates}
    assert prop in allowed, (prop, allowed)
    assert (prop, RDF.type, OWL.ObjectProperty) in graph


def _direction(graph, prop=BASE.tFocus, source=BASE.cA, target=BASE.cB):
    assert isinstance(prop, URIRef) and (prop, RDF.type, OWL.ObjectProperty) in graph
    assert set(graph.objects(prop, RDFS.domain)) == {source}
    assert set(graph.objects(prop, RDFS.range)) == {target}


def _counts(graph, owner, expression, expected):
    """REL-10/11 require asserted unqualified, separate, necessary counts."""
    facts = cardinality_facts(graph, owner, expression)
    assert {(kind, number) for kind, number, _, _ in facts} == set(expected)
    assert len(facts) == len(expected)
    assert len({node for _, _, _, node in facts}) == len(expected)
    assert all(qualifier is None for _, _, qualifier, _ in facts)
    assert not list(graph.objects(owner, OWL.equivalentClass))
    assert not list(graph.subjects(OWL.equivalentClass, owner))


def _both_counts(graph, side, expected, opposite=() , mode='none', self_relation=False):
    reverse = BASE.sFocus if mode == 'all' else ('inverse', BASE.tFocus)
    target = BASE.cA if self_relation else BASE.cB
    _counts(graph, BASE.cA, BASE.tFocus, expected if side == 'target' else opposite)
    _counts(graph, target, reverse, expected if side == 'source' else opposite)
    if not self_relation:
        _counts(graph, target, BASE.tFocus, ())
        _counts(graph, BASE.cA, reverse, ())
    for _, _, qualifier, node in cardinality_facts(graph, target, reverse):
        assert not list(graph.objects(node, OWL.onClass)) and not list(graph.objects(node, OWL.onDataRange))
    _direction(graph, target=target)
    assert ((BASE.sFocus, RDF.type, OWL.ObjectProperty) in graph) == (mode == 'all')


# The two directions are separate nodes. Five same-role-type families lack an
# input-field criterion selecting their semantic direction; only their bounded
# candidate safety is asserted. The externalDependence mode-role interpretation
# is separately blocked; those two cases assert only independent mappings.
SEMANTIC_ROWS = [
 ('bringsAbout', ('event','Event'), ('situation','Situation'), 'bringsAbout', 'broughtAboutBy', False),
 ('characterization', ('kind','Bearer'), ('mode','Feature'), 'isCharacterizedBy', 'characterizes', False),
 ('componentOf', ('kind','Whole'), ('kind','Component'), 'hasComponent', 'componentOf', True),
 ('creation', ('event','Event'), ('kind','Endurant'), 'creates', 'wasCreatedIn', False),
 ('externalDependence', ('mode','Mode'), ('kind','Endurant'), 'externallyDependsOn', 'isExternalDependencyOf', True),
 ('historicalDependence', ('historicalRole','Dependent'), ('kind','Antecedent'), 'historicallyDependsOn', 'isHistoricalDependencyOf', True),
 ('manifestation', ('mode','Aspect'), ('event','Event'), 'manifestedIn', 'manifests', False),
 ('mediation', ('relator','Relator'), ('kind','Endurant'), 'mediates', 'isMediatedBy', False),
 ('memberOf', ('kind','Member'), ('collective','Collective'), 'memberOf', 'hasMember', False),
 ('participation', ('kind','Participant'), ('event','Event'), 'participatesIn', 'hasParticipant', False),
 ('participational', ('event','PartEvent'), ('event','WholeEvent'), 'participationalPartOf', 'hasParticipationalPart', True),
 ('subCollectionOf', ('collective','Subcollection'), ('collective','Collection'), 'subCollectionOf', 'hasSubCollection', True),
 ('subQuantityOf', ('quantity','Subquantity'), ('quantity','Quantity'), 'subQuantityOf', 'hasSubQuantity', True),
 ('termination', ('kind','Endurant'), ('event','Event'), 'wasTerminatedIn', 'terminates', False),
 ('triggers', ('situation','Situation'), ('event','Event'), 'triggers', 'triggeredBy', False),
]
SEMANTIC_CASES = [pytest.param(stereo, a if not reverse else b, b if not reverse else a,
                    {forward, backward} if blocked else {backward if reverse else forward}, blocked,
                    id=stereo+('_reverse' if reverse else '_forward'))
                  for stereo,a,b,forward,backward,blocked in SEMANTIC_ROWS for reverse in (False,True)]


@pytest.mark.parametrize('stereotype,source,target,candidates,blocked', SEMANTIC_CASES)
def test_stereotype_table_candidates_preserve_established_direction_when_resolvable(run, source_json, tmp_path, stereotype, source, target, candidates, blocked):
    """Rules: DK-REL-01, DK-REL-02, DK-REL-04, DK-GEN-03, DK-PROP-02, DK-DIAG-06.

    blocked=True asserts bounded candidate safety, not a selected semantic
    direction for ten cells. The two externalDependence cells assert no lexical
    candidate or naming-diagnostic expectation until the mode role is clarified.
    """
    document = source_json('shared/binary_relation')
    source_element(document,'cA').update(stereotype=source[0], name=source[1])
    source_element(document,'cB').update(stereotype=target[0], name=target[1])
    source_element(document,'rFocus').update(stereotype=stereotype, name=None)
    source_element(document,'tFocus')['name'] = None
    assert not fixture_issues(document)
    result = run(path=write_input(tmp_path,document),inverse_properties='none',stereotype_policy='require-known')
    assert result.outcome == 'completed'
    prop = _primary(result,strategy='name')
    if stereotype!='externalDependence':
        _candidate(result.ontology,prop,candidates,source[1])
    _direction(result.ontology,prop,BASE[source[1]],BASE[target[1]])
    assert not any(d.severity == 'ERROR' for d in result.diagnostics)
    if stereotype!='externalDependence':
        assert not any(d.kind in NAMING_KINDS for d in result.diagnostics)


PRECEDENCE = [
 pytest.param(' Assigned, To ', 'targetRole', 'mediation', False, 'Assigned_To', False, id='relation_before_role_stereotype'),
 pytest.param(None, 'target role', 'mediation', False, 'target_role', True, id='target_role_before_stereotype'),
 pytest.param(None, None, 'mediation', False, 'mediates', False, id='semantic_before_endpoints'),
 pytest.param(None, None, 'mediation', True, 'hTTPServer_xMLNode', True, id='disabled_stereotype_preserves_initialisms'),
 pytest.param(None, None, 'material', True, 'hTTPServer_xMLNode', True, id='source_role_cannot_name_primary'),
 pytest.param(None, '___', 'mediation', False, 'mediates', False, id='unusable_target_role_skipped'),
 pytest.param(None, None, 'comparative', False, 'hTTPServer_xMLNode', True, id='comparative_domain_specific_warning'),
 pytest.param(None, None, 'comparative', True, 'hTTPServer_xMLNode', True, id='disabled_comparative_step_has_only_generic_warning'),
]


@pytest.mark.parametrize('name,role,stereo,disabled,candidate,warn', PRECEDENCE)
def test_primary_naming_precedence_and_stereotype_control(run, source_json, tmp_path, name, role, stereo, disabled, candidate, warn):
    """Rules: DK-REL-01, DK-REL-02, DK-REL-03, DK-REL-04, DK-REL-06, DK-PROP-02, DK-GEN-03, DK-IRI-03."""
    document=source_json('shared/binary_relation')
    source_element(document,'cA')['stereotype']='relator' if stereo=='mediation' else 'category'
    source_element(document,'rFocus').update(name=name,stereotype=stereo)
    source_element(document,'sFocus')['name']='NeverUseThisSourceRole'
    source_element(document,'tFocus')['name']=role
    options={'no_stereotype_relation_naming':True} if disabled else {}
    result=run(path=write_input(tmp_path,document),inverse_properties='none',**options)
    assert result.outcome=='completed'
    prop=_primary(result,strategy='name')
    _candidate(result.ontology,prop,{candidate},'HTTPServer')
    _direction(result.ontology,prop,BASE.HTTPServer,BASE.XMLNode)
    notices=[d for d in result.diagnostics if d.kind in NAMING_KINDS]
    assert any(d.severity=='WARNING' for d in notices)==warn
    assert not any(d.severity=='ERROR' for d in result.diagnostics)
    if stereo=='comparative' and not disabled:
        assert any(d.kind=='comparative_naming' and d.severity=='WARNING' for d in notices)
    elif stereo=='comparative':assert not any(d.kind=='comparative_naming' for d in notices)


@pytest.mark.parametrize('input_policy',POLICIES)
def test_unnamed_endpoints_and_relation_continue_without_forcing_should_message_separation(run, source_json, tmp_path, input_policy):
    """Rules: DK-IRI-04, DK-REL-03, DK-REL-06, DK-GEN-03, DK-DIAG-05."""
    document=source_json('shared/binary_relation')
    for identifier in ('cA','cB','rFocus','tFocus'): source_element(document,identifier)['name']=None
    result=run(path=write_input(tmp_path,document),input_policy=input_policy,inverse_properties='none',no_stereotype_relation_naming=True)
    assert result.outcome=='completed'
    prop=_primary(result,strategy='name')
    _direction(result.ontology,prop,BASE.unnamedClass_cA,BASE.unnamedClass_cB)
    assert any(d.kind=='relation_naming' and d.severity=='WARNING' for d in result.diagnostics)
    assert not any(d.severity=='ERROR' for d in result.diagnostics)


@pytest.mark.parametrize('label_mode',['source-only','generated'])
@pytest.mark.parametrize('reverse',[False,True],ids=['relation_first','relator_first'])
@pytest.mark.parametrize('localized',[False,True],ids=['plain','localized'])
def test_material_name_uses_original_grounding_relator_text_without_has_prefix(run, source_json, tmp_path, reverse, localized, label_mode):
    """Rules: DK-REL-02, DK-REL-05, DK-GEN-03, DK-PROP-02, DK-IRI-10, DK-REL-08, DK-LBL-01, DK-LBL-02, DK-IRI-03."""
    document=source_json('relations/material_naming')
    source_element(document,'cGround')['name']={'nl':'Werk','en':'Employment Contract'} if localized else 'Employment Contract'
    # A same-named source class disambiguates the class IRI, not the lexical name.
    other=copy.deepcopy(source_element(document,'cGround'));other.update(id='cOtherGround',stereotype='category')
    document['model']['contents'].append(other)
    if reverse: source_element(document,'rDerivation')['properties'].reverse()
    assert not fixture_issues(document)
    result=run(path=write_input(tmp_path,document),inverse_properties='none',material_property_chains='none',language='nl',relation_labels=label_mode)
    assert result.outcome=='completed'
    prop=_primary(result,strategy='name')
    _candidate(result.ontology,prop,{'employment_Contract'},'HTTPServer')
    assert set(result.ontology.objects(prop,RDFS.label))==({Literal('employment_Contract')} if label_mode=='generated' else set())
    _direction(result.ontology,prop,BASE.HTTPServer,BASE.XMLNode)
    assert not any(d.kind in NAMING_KINDS and d.severity=='WARNING' for d in result.diagnostics)
    assert not any(d.severity=='ERROR' for d in result.diagnostics)
    # Successful provenance INFO is SHOULD, so it is deliberately not required.


@pytest.mark.parametrize('failure',['absent','ambiguous','unnamed','unusable','mode_grounded'])
def test_unavailable_material_grounding_warns_and_uses_endpoint_fallback(run, source_json, tmp_path, failure):
    """Rules: DK-REL-02, DK-REL-03, DK-REL-05, DK-REL-06, DK-PROP-02, DK-GEN-03, DK-DIAG-06."""
    document=source_json('relations/material_naming')
    contents=document['model']['contents']
    if failure=='absent': contents.remove(source_element(document,'rDerivation'))
    elif failure=='ambiguous':
        ground=copy.deepcopy(source_element(document,'cGround'));ground.update(id='cOtherGround',name='OtherGround')
        connector=copy.deepcopy(source_element(document,'rDerivation'));connector['id']='rOtherDerivation'
        connector['properties'][0]['id']='sOtherDerivation';connector['properties'][1].update(id='tOtherDerivation',propertyType={'id':'cOtherGround','type':'Class'})
        contents.extend([ground,connector])
    elif failure in {'unnamed','unusable'}: source_element(document,'cGround')['name']=None if failure=='unnamed' else '___'
    else: source_element(document,'cGround')['stereotype']='mode'
    assert not fixture_issues(document)
    options={'stereotype_policy':'require-known'} if failure=='mode_grounded' else {}
    result=run(path=write_input(tmp_path,document),inverse_properties='none',material_property_chains='none',**options)
    assert result.outcome=='completed'
    prop=_primary(result,strategy='name');_candidate(result.ontology,prop,{'hTTPServer_xMLNode'},'HTTPServer')
    _direction(result.ontology,prop,BASE.HTTPServer,BASE.XMLNode)
    assert any(d.kind=='unavailable_grounding_relator' and d.severity=='WARNING' for d in result.diagnostics)
    assert not any(d.severity=='ERROR' for d in result.diagnostics)


LABEL_CASES=[
 pytest.param('Original, Relation','target role','material','Original, Relation',None,id='relation_source_wording'),
 pytest.param(None,'target role','material','target role',None,id='target_role_source_wording'),
 pytest.param(None,None,'mediation',None,'mediates',id='generated_semantic'),
 pytest.param(None,None,'comparative',None,'hTTPServer_xMLNode',id='generated_endpoint_synthesis'),
 pytest.param({'pt-BR':'Relação','en':'Relation'},'unused','material',{'pt-BR':'Relação','en':'Relation'},None,id='localized_relation'),
 pytest.param(None,{'nl':'werknemers','en':'workers'},'material',{'nl':'werknemers','en':'workers'},None,id='localized_target_role'),
]


@pytest.mark.parametrize('strategy',['name','id'])
@pytest.mark.parametrize('label_mode',['source-only','generated'])
@pytest.mark.parametrize('name,role,stereo,source_value,fallback',LABEL_CASES)
def test_primary_labels_preserve_source_precedence_or_selected_lexical_fallback(run, source_json, tmp_path, strategy, label_mode, name, role, stereo, source_value, fallback):
    """Rules: DK-LBL-01, DK-LBL-02, DK-REL-02, DK-REL-03, DK-REL-04, DK-IRI-02, DK-IRI-10."""
    document=source_json('shared/binary_relation')
    document['languages']=['nl']
    source_element(document,'rFocus').update(name=name,stereotype=stereo)
    source_element(document,'tFocus')['name']=role
    source_element(document,'sFocus')['name']='Wrong primary label'
    if stereo=='mediation': source_element(document,'cA')['stereotype']='relator'
    result=run(path=write_input(tmp_path,document),iri_strategy=strategy,inverse_properties='none',relation_labels=label_mode,language='pt-BR')
    assert result.outcome=='completed'
    prop=_primary(result,strategy=strategy)
    if source_value is not None:
        texts=source_value.values() if isinstance(source_value,dict) else [source_value]
        expected={Literal(value,lang='pt-BR') for value in texts}
    else: expected={Literal(fallback)} if label_mode=='generated' else set()
    assert set(result.ontology.objects(prop,RDFS.label))==expected
    assert not result.relation_label_origin_output


@pytest.mark.parametrize('strategy',['name','id'])
def test_default_primary_label_mode_omits_generated_fallback(run, source_json, tmp_path, strategy):
    """Rules: DK-LBL-01, DK-REL-02, DK-REL-04, DK-IRI-02."""
    document=source_json('shared/binary_relation')
    source_element(document,'rFocus').update(name=None,stereotype='mediation')
    source_element(document,'cA')['stereotype']='relator'
    source_element(document,'tFocus')['name']=None
    result=run(path=write_input(tmp_path,document),iri_strategy=strategy,inverse_properties='none')
    assert result.outcome=='completed'
    prop=_primary(result,strategy=strategy)
    assert (prop,RDF.type,OWL.ObjectProperty) in result.ontology
    assert not list(result.ontology.objects(prop,RDFS.label))
    assert not result.relation_label_origin_output


@pytest.mark.parametrize('strategy',['name','id'])
def test_generated_primary_labels_do_not_include_iri_qualification_or_suffixes(run, source_json, tmp_path, strategy):
    """Rules: DK-LBL-01, DK-REL-03, DK-PROP-02, DK-IRI-07, DK-IRI-09."""
    document=source_json('shared/binary_relation')
    for identifier in ('rFocus','tFocus'):source_element(document,identifier)['name']=None
    other=copy.deepcopy(source_element(document,'rFocus'));other['id']='rOther'
    other['properties'][0]['id']='sOther';other['properties'][1]['id']='tOther'
    document['model']['contents'].append(other)
    result=run(path=write_input(tmp_path,document),iri_strategy=strategy,inverse_properties='none',relation_labels='generated',no_stereotype_relation_naming=True)
    assert result.outcome=='completed'
    properties={_primary(result,identifier,strategy) for identifier in ('tFocus','tOther')}
    assert len(properties)==2
    for prop in properties: assert set(result.ontology.objects(prop,RDFS.label))=={Literal('hTTPServer_xMLNode')}
    if strategy=='name': assert properties=={BASE.hTTPServer_xMLNode_HTTPServer_1,BASE.hTTPServer_xMLNode_HTTPServer_2}
    assert not result.relation_label_origin_output


@pytest.mark.parametrize('field',['name','target_role','endpoints'])
def test_localized_relation_naming_uses_original_key_order_independent_of_language_controls(run, source_json, tmp_path, field):
    """Rules: DK-IRI-10, DK-REL-02, DK-REL-03, DK-LBL-01, DK-LBL-02, DK-PROP-02, DK-IRI-03."""
    for reverse in (False,True):
        document=source_json('shared/binary_relation');document['languages']=['nl']
        names={'EN':'Zulu','en':'Alpha','nl':'Nederlands'}
        if reverse:names=dict(reversed(list(names.items())))
        source_element(document,'rFocus')['name']=names if field=='name' else None
        source_element(document,'tFocus')['name']=names if field=='target_role' else None
        if field=='endpoints':
            source_element(document,'cA')['name']=names;source_element(document,'cB')['name']={'nl':'Boom','en':'XMLNode'}
        result=run(path=write_input(tmp_path,document),inverse_properties='none',language='nl',relation_labels='generated',no_stereotype_relation_naming=True)
        assert result.outcome=='completed'
        prop=_primary(result,strategy='name')
        candidate='alpha_xMLNode' if field=='endpoints' else 'Alpha'
        _candidate(result.ontology,prop,{candidate},'Alpha' if field=='endpoints' else 'HTTPServer')
        if field=='endpoints':assert set(result.ontology.objects(prop,RDFS.label))=={Literal(candidate)}
        else:assert set(result.ontology.objects(prop,RDFS.label))=={Literal(t,lang='nl') for t in names.values()}


VALID_COUNTS=[
 pytest.param('0',{('exact',0)},id='single_zero'),pytest.param('1',{('exact',1)},id='single_one'),
 pytest.param('2',{('exact',2)},id='single_two'),pytest.param('0..0',{('exact',0)},id='equal_zero'),
 pytest.param('2..2',{('exact',2)},id='equal_two'),pytest.param('0..1',{('max',1)},id='optional'),
 pytest.param('2..5',{('min',2),('max',5)},id='bounded'),pytest.param('1..*',{('min',1)},id='positive_unbounded'),
 pytest.param(' 001 .. 003 ',{('min',1),('max',3)},id='trim_leading_zeros'),
 pytest.param(' 01 .. * ',{('min',1)},id='trim_unbounded_upper'),pytest.param(' 00 ',{('exact',0)},id='single_leading_zero')]


@pytest.mark.parametrize('side',['source','target'])
@pytest.mark.parametrize('mode',['all','none'])
@pytest.mark.parametrize('cardinality,expected',VALID_COUNTS)
def test_relation_counts_use_directional_unqualified_necessary_restrictions(run, source_json, tmp_path, side, mode, cardinality, expected):
    """Rules: DK-REL-09, DK-REL-10, DK-REL-11, DK-REL-12, DK-DIAG-11, DK-GEN-03, DK-INV-04."""
    document=source_json('shared/binary_relation')
    source_element(document,'sFocus' if side=='source' else 'tFocus')['cardinality']=cardinality
    result=run(path=write_input(tmp_path,document),iri_strategy='id',inverse_properties=mode)
    assert result.outcome=='completed'
    _both_counts(result.ontology,side,expected,mode=mode)
    assert not any(d.severity in {'WARNING','ERROR'} for d in result.diagnostics)


@pytest.mark.parametrize('side',['source','target'])
@pytest.mark.parametrize('mode',['all','none'])
@pytest.mark.parametrize('input_policy',POLICIES)
@pytest.mark.parametrize('cardinality,expected',[pytest.param('5..2',{('min',5),('max',2)},id='lower_exceeds_upper'),pytest.param('1..0',{('min',1),('max',0)},id='contradictory_zero_upper')])
def test_contradictory_relation_bounds_are_both_asserted_under_every_policy(run, source_json, tmp_path, side, mode, input_policy, cardinality, expected):
    """Rules: DK-REL-09, DK-REL-10, DK-REL-11, DK-DIAG-05, DK-DIAG-11; §3.4 contradictory numeric bounds."""
    document=source_json('shared/binary_relation')
    source_element(document,'sFocus' if side=='source' else 'tFocus')['cardinality']=cardinality
    result=run(path=write_input(tmp_path,document),iri_strategy='id',inverse_properties=mode,input_policy=input_policy)
    assert result.outcome=='completed';_both_counts(result.ontology,side,expected,mode=mode)
    assert not any(d.severity in {'WARNING','ERROR'} for d in result.diagnostics)


@pytest.mark.parametrize('side',['source','target'])
@pytest.mark.parametrize('mode',['all','none'])
@pytest.mark.parametrize('input_policy',POLICIES)
@pytest.mark.parametrize('state',['null','absent','star','zero_unbounded'])
def test_relation_null_missing_and_zero_unbounded_counts_preserve_other_mappings(run, source_json, tmp_path, side, mode, input_policy, state):
    """Rules: DK-REL-09, DK-REL-10, DK-REL-12, DK-REL-13, DK-DIAG-09, DK-DIAG-05, DK-GEN-03."""
    document=source_json('shared/binary_relation');end=source_element(document,'sFocus' if side=='source' else 'tFocus')
    if state=='absent':del end['cardinality']
    elif state in {'star','zero_unbounded'}:end['cardinality']='*' if state=='star' else '0..*'
    result=run(path=write_input(tmp_path,document),iri_strategy='id',inverse_properties=mode,input_policy=input_policy)
    assert result.outcome=='completed';_both_counts(result.ontology,side,(),mode=mode)
    notices=[d for d in result.diagnostics if d.kind=='missing_cardinality']
    if state=='absent':assert any(d.severity=='WARNING' and end['id'] in d.identified_sources for d in notices)
    else:assert not notices and not any(d.severity in {'WARNING','ERROR'} for d in result.diagnostics)


INVALID_COUNTS=[
 pytest.param('n',set(),id='symbolic_single'),pytest.param('n..m',set(),id='both_symbolic'),
 pytest.param('n..*',set(),id='invalid_lower_unbounded_upper'),pytest.param('n..3',{('max',3)},id='symbolic_lower'),
 pytest.param('n..0',{('max',0)},id='invalid_lower_zero_upper'),pytest.param('2..n',{('min',2)},id='symbolic_upper'),
 pytest.param('0..n',set(),id='zero_lower_invalid_upper'),pytest.param('..3',{('max',3)},id='empty_lower'),
 pytest.param('2..',{('min',2)},id='empty_upper'),pytest.param('..',set(),id='both_empty'),
 pytest.param('-1..3',{('max',3)},id='signed_lower'),pytest.param('2..+3',{('min',2)},id='signed_upper'),
 pytest.param('1.5..3',{('max',3)},id='decimal_lower'),pytest.param('2..3e1',{('min',2)},id='exponent_upper'),
 pytest.param('２..3',{('max',3)},id='non_ascii_digits'),pytest.param('2...*',set(),id='extra_dot'),
 pytest.param('1..2..3',set(),id='repeated_delimiter'),pytest.param('2,,3',set(),id='comma'),
 pytest.param('2:3',set(),id='colon'),pytest.param('',set(),id='empty_string'),pytest.param(' \t ',set(),id='blank_string'),
 pytest.param(1,set(),id='json_number'),pytest.param(True,set(),id='json_boolean'),pytest.param(1.5,set(),id='json_fraction'),
 pytest.param([],set(),id='json_array'),pytest.param({},set(),id='json_object')]


@pytest.mark.parametrize('side',['source','target'])
@pytest.mark.parametrize('input_policy',POLICIES)
@pytest.mark.parametrize('cardinality,expected',INVALID_COUNTS)
def test_relation_invalid_counts_preserve_errors_valid_bounds_and_opposite_end(run, source_json, tmp_path, side, input_policy, cardinality, expected):
    """Rules: DK-DIAG-05, DK-DIAG-10, DK-DIAG-11, DK-REL-09, DK-REL-10, DK-REL-11, DK-GEN-03."""
    document=source_json('shared/binary_relation')
    source_element(document,'sFocus' if side=='source' else 'tFocus')['cardinality']=cardinality
    source_element(document,'tFocus' if side=='source' else 'sFocus')['cardinality']='4'
    assert fixture_issues(document)==(frozenset() if isinstance(cardinality,str) else {'invalid_cardinality_type'})
    result=run(path=write_input(tmp_path,document),iri_strategy='id',inverse_properties='none',input_policy=input_policy)
    assert any(d.kind=='invalid_cardinality' and d.severity=='ERROR' for d in result.diagnostics)
    if input_policy!='best-effort':assert result.outcome=='aborted' and result.ontology is None
    else:
        assert result.outcome=='completed-with-errors'
        _both_counts(result.ontology,side,expected,{('exact',4)})
        assert (BASE.cA,RDF.type,OWL.Class) in result.ontology and (BASE.cB,RDF.type,OWL.Class) in result.ontology


@pytest.mark.parametrize('side',['source','target'])
@pytest.mark.parametrize('cardinality,expected',[pytest.param('n..3',{('max',3)},id='recover_upper'),pytest.param('2..n',{('min',2)},id='recover_lower'),pytest.param('2...*',set(),id='no_ambiguous_repair')])
def test_partial_count_recovery_uses_generated_named_inverse_when_present(run, source_json, tmp_path, side, cardinality, expected):
    """Rules: DK-DIAG-10, DK-DIAG-11, DK-REL-09, DK-REL-10, DK-REL-11, DK-INV-04."""
    document=source_json('shared/binary_relation')
    source_element(document,'sFocus' if side=='source' else 'tFocus')['cardinality']=cardinality
    source_element(document,'tFocus' if side=='source' else 'sFocus')['cardinality']='1'
    result=run(path=write_input(tmp_path,document),iri_strategy='id',inverse_properties='all',input_policy='best-effort')
    assert result.outcome=='completed-with-errors'
    assert any(d.kind=='invalid_cardinality' and d.severity=='ERROR' for d in result.diagnostics)
    _both_counts(result.ontology,side,expected,{('exact',1)},mode='all')


@pytest.mark.parametrize('mode',['all','none'])
def test_self_relation_cardinalities_keep_distinct_end_directions(run, source_json, tmp_path, mode):
    """Rules: DK-REL-01, DK-REL-09, DK-REL-10, DK-REL-11, DK-IRI-06, DK-INV-02, DK-INV-03."""
    document=source_json('shared/binary_relation')
    source_element(document,'tFocus').update(propertyType={'id':'cA','type':'Class'},cardinality='1')
    source_element(document,'sFocus')['cardinality']='2..5'
    result=run(path=write_input(tmp_path,document),iri_strategy='id',inverse_properties=mode)
    assert result.outcome=='completed';_both_counts(result.ontology,'source',{('min',2),('max',5)},{('exact',1)},mode=mode,self_relation=True)


@pytest.mark.parametrize('feature',['omit_without_named_inverse','qualified'])
def test_relation_cardinality_representation_is_not_an_optional_python_control(invoke, feature):
    """Rules: DK-REL-09, DK-REL-10; Python surface, CLI counterpart Wave 6."""
    assert invoke.has_relation_cardinality_control(feature) is False


def _edges(graph):
    return {(s,o) for s,o in graph.subject_objects(RDFS.subPropertyOf)
            if isinstance(s,URIRef) and isinstance(o,URIRef) and str(s).startswith(str(BASE)) and str(o).startswith(str(BASE))}


def _hierarchy_expected(result,strategy,named,edges):
    mapped={key:_primary(result,'t'+key,strategy) for key in ('General','Middle','Leaf','Sibling')}
    inverses={key:_primary(result,'s'+key,strategy) for key in named}
    graph=result.ontology
    for key,primary in mapped.items():
        assert (primary,RDF.type,OWL.ObjectProperty) in graph
        observed={node for node in graph.subjects(OWL.inverseOf,primary) if isinstance(node,URIRef)}
        assert observed==({inverses[key]} if key in named else set())
        if key in named:
            inverse=inverses[key]
            assert set(graph.objects(inverse,OWL.inverseOf))=={primary}
            assert (primary,OWL.inverseOf,inverse) not in graph
            assert set(graph.objects(primary,RDFS.domain)) and set(graph.objects(primary,RDFS.range))
            assert set(graph.objects(inverse,RDFS.domain))==set(graph.objects(primary,RDFS.range))
            assert set(graph.objects(inverse,RDFS.range))==set(graph.objects(primary,RDFS.domain))
    local_properties={node for node in graph.subjects(RDF.type,OWL.ObjectProperty)
                      if isinstance(node,URIRef) and str(node).startswith(str(BASE))}
    assert local_properties==set(mapped.values())|set(inverses.values())
    # These models have null counts, no RD-14 refs and no emitted chains.
    assert not any(isinstance(node,BNode) for node in graph.subjects(OWL.inverseOf,None))
    expected={(mapped[a],mapped[b]) for a,b in edges}
    expected|={(inverses[a],inverses[b]) for a,b in edges if a in named and b in named}
    return mapped,inverses,expected


@pytest.mark.parametrize('strategy',['name','id'])
@pytest.mark.parametrize('general,middle',[(False,False),(True,False),(False,True),(True,True)],ids=['neither_named','general_only','specific_only','both_named'])
def test_explicit_relation_generalizations_mirror_only_available_named_inverse_edges(run, source_json, tmp_path, strategy, general, middle):
    """Rules: DK-REL-14, DK-INV-12, DK-GEN-02, DK-GEN-03, DK-DIAG-02, DK-INV-01."""
    document=source_json('relations/hierarchy');named=set()
    for key,present in [('General',general),('Middle',middle),('Leaf',False),('Sibling',False)]:
        source_element(document,'s'+key)['name']='inverse'+key if present else None
        if present:named.add(key)
    result=run(path=write_input(tmp_path,document),iri_strategy=strategy,inverse_properties='named')
    assert result.outcome=='completed'
    props,inverses,expected=_hierarchy_expected(result,strategy,named,[('Middle','General'),('Leaf','Middle'),('Sibling','General')])
    assert _edges(result.ontology)==expected
    for key,a,b in [('General','A','B'),('Middle','B','C'),('Leaf','C','A'),('Sibling','D','A')]:
        _direction(result.ontology,props[key],BASE['c'+a] if strategy=='id' else BASE[a],BASE['c'+b] if strategy=='id' else BASE[b])
    assert not any(isinstance(s,BNode) for s in result.ontology.subjects(OWL.inverseOf,None))
    assert not result.inverse_omission_reports
    assert not any(d.kind in {'semantic_validation','inverse_omission'} or d.severity=='ERROR' for d in result.diagnostics)


def _pairs(graph):return {frozenset((s,o)) for s,o in graph.subject_objects(OWL.propertyDisjointWith)}


@pytest.mark.parametrize('mode',['all','none'])
@pytest.mark.parametrize('input_policy',POLICIES)
@pytest.mark.parametrize('complete',[False,True],ids=['incomplete','complete'])
@pytest.mark.parametrize('disjoint',[False,True],ids=['overlapping','disjoint'])
def test_relation_set_disjointness_and_multi_member_completeness_are_independent(run, source_json, tmp_path, mode, input_policy, complete, disjoint):
    """Rules: DK-REL-14, DK-REL-15, DK-REL-16, DK-INV-12, DK-DIAG-05, DK-GEN-02."""
    document=source_json('relations/hierarchy');source_element(document,'gsRelations').update(isComplete=complete,isDisjoint=disjoint)
    result=run(path=write_input(tmp_path,document),iri_strategy='id',inverse_properties=mode,input_policy=input_policy)
    assert result.outcome=='completed'
    names={'General','Middle','Leaf','Sibling'} if mode=='all' else set()
    props,inverses,edges=_hierarchy_expected(result,'id',names,[('Middle','General'),('Leaf','Middle'),('Sibling','General')])
    assert _edges(result.ontology)==edges
    pairs={frozenset((props['Middle'],props['Sibling']))} if disjoint else set()
    if disjoint and mode=='all':pairs.add(frozenset((inverses['Middle'],inverses['Sibling'])))
    assert _pairs(result.ontology)==pairs
    assert not result.relation_completeness_output
    assert not list(result.ontology.triples((None,OWL.equivalentProperty,None)))
    assert not list(result.ontology.triples((None,OWL.unionOf,None)))
    notices=[d for d in result.diagnostics if d.kind=='relation_set_completeness']
    if complete:assert any(d.severity=='WARNING' and 'gsRelations' in d.identified_sources and 'coverage_not_represented' in d.facts for d in notices)
    else:assert not notices
    assert not any(d.severity=='ERROR' for d in result.diagnostics)


@pytest.mark.parametrize('named_specific',['Middle','Sibling'],ids=['only_first_inverse','only_second_inverse'])
def test_relation_disjointness_omits_inverse_pair_when_only_one_inverse_is_available(run, source_json, tmp_path, named_specific):
    """Rules: DK-REL-14, DK-REL-15, DK-INV-01, DK-INV-10, DK-INV-12, DK-DIAG-05."""
    document=source_json('relations/hierarchy')
    source_element(document,'gsRelations').update(isDisjoint=True,isComplete=False)
    for key in ('General','Middle','Leaf','Sibling'):
        source_element(document,'s'+key)['name']='inverse'+key if key==named_specific else None
    assert not fixture_issues(document)
    result=run(path=write_input(tmp_path,document),iri_strategy='id',inverse_properties='named',input_policy='strict')
    assert result.outcome=='completed'
    props,_,edges=_hierarchy_expected(result,'id',{named_specific},[('Middle','General'),('Leaf','Middle'),('Sibling','General')])
    assert _edges(result.ontology)==edges
    assert _pairs(result.ontology)=={frozenset((props['Middle'],props['Sibling']))}
    assert not result.inverse_omission_reports
    assert not any(d.kind=='inverse_omission' or d.severity in {'WARNING','ERROR'} for d in result.diagnostics)


def test_relation_disjointness_emits_every_explicit_three_member_pair(run, source_json, tmp_path):
    """Rules: DK-REL-14, DK-REL-15, DK-INV-12, DK-GEN-02."""
    document=source_json('relations/hierarchy')
    general=copy.deepcopy(source_element(document,'gMiddle'));general.update(id='gLeafGeneral',specific={'id':'rLeaf','type':'Relation'})
    document['model']['contents'].append(general)
    source_element(document,'gsRelations').update(isDisjoint=True,generalizations=[{'id':i,'type':'Generalization'} for i in ('gMiddle','gSibling','gLeafGeneral')])
    assert not fixture_issues(document)
    result=run(path=write_input(tmp_path,document),iri_strategy='id')
    assert result.outcome=='completed'
    _,_,edges=_hierarchy_expected(result,'id',{'General','Middle','Leaf','Sibling'},[('Middle','General'),('Leaf','Middle'),('Sibling','General'),('Leaf','General')])
    assert _edges(result.ontology)==edges
    keys=['Middle','Sibling','Leaf']
    expected={frozenset((BASE[prefix+a],BASE[prefix+b])) for prefix in ('t','s') for i,a in enumerate(keys) for b in keys[i+1:]}
    assert _pairs(result.ontology)==expected


@pytest.mark.parametrize('input_policy',POLICIES)
@pytest.mark.parametrize('disjoint',[False,True],ids=['overlapping','disjoint'])
@pytest.mark.parametrize('complete',[False,True],ids=['incomplete','complete'])
@pytest.mark.parametrize('general,middle',[(False,False),(True,False),(False,True),(True,True)],ids=['neither_named','general_only','specific_only','both_named'])
def test_singleton_relation_completeness_adds_only_required_reverse_inclusions(run, source_json, tmp_path, input_policy, disjoint, complete, general, middle):
    """Rules: DK-REL-14, DK-REL-15, DK-REL-20, DK-INV-12, DK-DIAG-14, DK-DIAG-05, DK-GEN-02."""
    document=source_json('relations/hierarchy')
    source_element(document,'gsRelations').update(isComplete=complete,isDisjoint=disjoint,generalizations=[{'id':'gMiddle','type':'Generalization'}])
    named=set()
    for key,present in [('General',general),('Middle',middle),('Leaf',False),('Sibling',False)]:
        source_element(document,'s'+key)['name']='inverse'+key if present else None
        if present:named.add(key)
    result=run(path=write_input(tmp_path,document),iri_strategy='id',inverse_properties='named',input_policy=input_policy)
    assert result.outcome=='completed'
    edges=[('Middle','General'),('Leaf','Middle'),('Sibling','General')]+([('General','Middle')] if complete else [])
    _,_,expected=_hierarchy_expected(result,'id',named,edges)
    assert _edges(result.ontology)==expected and not _pairs(result.ontology)
    assert not list(result.ontology.triples((None,OWL.equivalentProperty,None)))
    assert not any(isinstance(s,BNode) for s in result.ontology.subjects(OWL.inverseOf,None))
    notices=[d for d in result.diagnostics if d.kind=='singleton_completeness']
    if complete:
        assert any(d.severity=='INFO' and {'gsRelations','rGeneral','rMiddle'}<=set(d.identified_sources)
                   and {'extensional_equivalence','distinct_identifiers'}<=d.facts for d in notices)
    else:assert not notices
    assert not any(d.severity in {'WARNING','ERROR'} for d in result.diagnostics)
    assert not result.inverse_omission_reports


@pytest.mark.parametrize('mode',['all','none'])
@pytest.mark.parametrize('input_policy',POLICIES)
@pytest.mark.parametrize('failure',['unresolved_member','failed_specific','unresolved_general','failed_general','failed_specific_three_members'])
def test_relation_set_partial_failures_never_turn_survivors_into_singleton_coverage(run, source_json, tmp_path, mode, input_policy, failure):
    """Rules: DK-REL-14, DK-REL-15, DK-REL-16, DK-REL-20, DK-INV-12, DK-DIAG-03, DK-DIAG-05, DK-DIAG-14."""
    document=source_json('relations/hierarchy');source_element(document,'gsRelations').update(isComplete=True,isDisjoint=True)
    expected=[('Middle','General'),('Leaf','Middle'),('Sibling','General')]
    if failure=='unresolved_member':source_element(document,'gsRelations')['generalizations'][1]['id']='gMissing'
    elif failure in {'failed_specific','failed_specific_three_members'}:
        source_element(document,'tSibling')['propertyType']=None;expected.remove(('Sibling','General'))
        if failure=='failed_specific_three_members':
            extra=copy.deepcopy(source_element(document,'gMiddle'));extra.update(id='gLeafGeneral',specific={'id':'rLeaf','type':'Relation'})
            document['model']['contents'].append(extra)
            source_element(document,'gsRelations')['generalizations'].append({'id':'gLeafGeneral','type':'Generalization'})
            expected.append(('Leaf','General'))
    elif failure=='unresolved_general':
        source_element(document,'gMiddle')['general']['id']='rMissing';expected.remove(('Middle','General'))
    else:
        source_element(document,'tGeneral')['propertyType']=None;expected=[('Leaf','Middle')]
    result=run(path=write_input(tmp_path,document),iri_strategy='id',inverse_properties=mode,input_policy=input_policy)
    assert any(d.severity=='ERROR' for d in result.diagnostics)
    if input_policy!='best-effort':assert result.outcome=='aborted' and result.ontology is None
    else:
        assert result.outcome=='completed-with-errors'
        edges={(BASE['t'+a],BASE['t'+b]) for a,b in expected}
        if mode=='all':edges|={(BASE['s'+a],BASE['s'+b]) for a,b in expected}
        assert _edges(result.ontology)==edges
        valid={'General','Middle','Leaf','Sibling'}
        if failure in {'failed_specific','failed_specific_three_members'}:valid.remove('Sibling')
        if failure=='failed_general':valid.remove('General')
        expected_inverses={(BASE['s'+key],BASE['t'+key]) for key in valid} if mode=='all' else set()
        assert set(result.ontology.subject_objects(OWL.inverseOf))==expected_inverses
        expected_properties={BASE['t'+key] for key in valid}
        if mode=='all':expected_properties|={BASE['s'+key] for key in valid}
        assert {node for node in result.ontology.subjects(RDF.type,OWL.ObjectProperty)
                if isinstance(node,URIRef) and str(node).startswith(str(BASE))}==expected_properties
        # Disjointness selects successfully mapped explicit specifics; it does
        # not require their general relation or its hierarchy edge to survive.
        specific_pair=('Middle','Leaf') if failure=='failed_specific_three_members' else (
            ('Middle','Sibling') if failure in {'unresolved_general','failed_general'} else None)
        pairs={frozenset(BASE['t'+key] for key in specific_pair)} if specific_pair else set()
        if specific_pair and mode=='all':pairs.add(frozenset(BASE['s'+key] for key in specific_pair))
        assert _pairs(result.ontology)==pairs and not result.relation_completeness_output
        assert not any(d.kind=='singleton_completeness' for d in result.diagnostics)
        assert (BASE.cD,RDF.type,OWL.Class) in result.ontology


@pytest.mark.parametrize('input_policy',POLICIES)
@pytest.mark.parametrize('complete,disjoint',[(False,False),(False,True),(True,False),(True,True)],ids=['neither_flag','disjoint_only','complete_only','both_flags'])
def test_empty_relation_generalization_set_is_structural_under_every_flag_combination(run, source_json, tmp_path, input_policy, complete, disjoint):
    """Rules: DK-DIAG-12, DK-DIAG-05, DK-REL-14, DK-REL-15, DK-REL-20."""
    document=source_json('relations/hierarchy');source_element(document,'gsRelations').update(isComplete=complete,isDisjoint=disjoint,generalizations=[])
    result=run(path=write_input(tmp_path,document),iri_strategy='id',input_policy=input_policy)
    assert any(d.kind=='empty_generalization_set' and d.severity=='ERROR' for d in result.diagnostics)
    if input_policy!='best-effort':assert result.outcome=='aborted' and result.ontology is None
    else:
        assert result.outcome=='completed-with-errors'
        _,_,expected=_hierarchy_expected(result,'id',{'General','Middle','Leaf','Sibling'},[('Middle','General'),('Leaf','Middle'),('Sibling','General')])
        assert _edges(result.ontology)==expected and not _pairs(result.ontology)
        assert not result.relation_completeness_output
        assert not any(d.kind=='singleton_completeness' for d in result.diagnostics)


@pytest.mark.parametrize('state',[True,False,'absent'],ids=['true','false','absent'])
@pytest.mark.parametrize('mode',['all','none'])
def test_relation_abstractness_is_comment_only_and_keeps_counts_and_direction(run, source_json, tmp_path, state, mode):
    """Rules: DK-CLS-01, DK-DIAG-15, DK-REL-01, DK-REL-09, DK-REL-10, DK-REL-11, DK-GEN-03."""
    document=source_json('shared/binary_relation');relation=source_element(document,'rFocus')
    # Isolate the relation's INFO from otherwise applicable class INFO events.
    for identifier in ('cA','cB'):source_element(document,identifier).pop('isAbstract')
    if state=='absent':relation.pop('isAbstract')
    else:relation['isAbstract']=state
    source_element(document,'tFocus')['cardinality']='2..5';source_element(document,'sFocus')['cardinality']='0..1'
    result=run(path=write_input(tmp_path,document),iri_strategy='id',inverse_properties=mode)
    assert result.outcome=='completed';_both_counts(result.ontology,'target',{('min',2),('max',5)},{('max',1)},mode=mode)
    meanings=[c for c in result.comments if c.subject==BASE.tFocus and c.field=='isAbstract']
    for c in meanings:assert (c.subject,RDFS.comment,c.literal) in result.ontology
    assert {c.value for c in meanings}==({state} if isinstance(state,bool) else set())
    if isinstance(state,bool):
        assert any(d.kind=='abstractness' and d.severity=='INFO' and {'preserved_as_annotation','not_logically_enforced'}<=d.facts for d in result.diagnostics)
    else:assert not any(d.kind=='abstractness' for d in result.diagnostics)
    assert not result.flag_semantic_output
    assert not any(d.severity in {'WARNING','ERROR'} for d in result.diagnostics)


def test_binary_id_partial_graph_includes_ontology_and_explicit_inverse_declarations(run, source_path):
    """Rules: DK-REL-01, DK-INV-03, DK-INV-04, DK-LBL-01, DK-GEN-01, DK-GEN-03, DK-IRI-06."""
    result=run('shared/binary_relation',iri_strategy='id')
    assert result.outcome=='completed'
    assert_contains(result.ontology,load_graph(source_path('shared/binary_relation','expected.ttl')))


def test_rdf_helper_relation_exact_zero_rejects_attribute_alternatives_and_qualified_counts():
    """Harness only: required relation serialization differs from attributes."""
    graph=Graph();node=BNode()
    graph.add((BASE.cA,RDFS.subClassOf,node));graph.add((node,RDF.type,OWL.Restriction));graph.add((node,OWL.onProperty,BASE.tFocus))
    graph.add((node,OWL.cardinality,Literal(0,datatype=XSD.nonNegativeInteger)))
    _counts(graph,BASE.cA,BASE.tFocus,{('exact',0)})
    graph.remove((node,OWL.cardinality,None));graph.add((node,OWL.maxCardinality,Literal(0,datatype=XSD.nonNegativeInteger)))
    with pytest.raises(AssertionError):_counts(graph,BASE.cA,BASE.tFocus,{('exact',0)})
    graph.remove((node,OWL.maxCardinality,None));graph.add((node,OWL.qualifiedCardinality,Literal(0,datatype=XSD.nonNegativeInteger)));graph.add((node,OWL.onClass,BASE.cB))
    with pytest.raises(AssertionError):_counts(graph,BASE.cA,BASE.tFocus,{('exact',0)})


def test_rdf_helper_hierarchy_rejects_forced_named_inverse_resources():
    """Harness only: an expected edge set must not hide forced inverses."""
    from tests.support.invocation import Observation
    graph=Graph()
    for key in ('General','Middle','Leaf','Sibling'):
        primary=BASE['t'+key]
        graph.add((primary,RDF.type,OWL.ObjectProperty));graph.add((primary,RDFS.domain,BASE.cA));graph.add((primary,RDFS.range,BASE.cB))
    sample=Observation(graph,None,())
    _hierarchy_expected(sample,'id',set(),[])
    graph.add((BASE.sGeneral,RDF.type,OWL.ObjectProperty))
    with pytest.raises(AssertionError):_hierarchy_expected(sample,'id',set(),[])
    graph.add((BASE.sGeneral,OWL.inverseOf,BASE.tGeneral));graph.add((BASE.sGeneral,RDFS.domain,BASE.cB));graph.add((BASE.sGeneral,RDFS.range,BASE.cA))
    _hierarchy_expected(sample,'id',{'General'},[])
    with pytest.raises(AssertionError):_hierarchy_expected(sample,'id',set(),[])
    graph.add((BASE.tGeneral,OWL.inverseOf,BASE.sGeneral))
    with pytest.raises(AssertionError):_hierarchy_expected(sample,'id',{'General'},[])


# Chain expectations use original source identifiers and observed RDF lists;
# no converter, inference engine or semantic-orientation repair lives here.
CHAIN_MODES=['none','omit-conflicting-constraints','preserve-conflicting-constraints']
GROUNDINGS=['relator','mode']


def _grounding(document, grounding):
    source_element(document,'cGround')['stereotype']=grounding
    source_element(document,'rLeft')['stereotype']='characterization' if grounding=='mode' else 'mediation'
    source_element(document,'rRight')['stereotype']='externalDependence' if grounding=='mode' else 'mediation'


def _no_connector(result, identifiers=('rDerivation','sDerivation','tDerivation')):
    assert result.unrepresented_connector_output==(), "Read actual connector output; an unbound reader is not evidence of omission"
    for identifier in identifiers:
        assert not any(BASE[identifier] in triple for triple in result.ontology)


def _pattern_resources(result, named=True):
    graph=result.ontology
    for key,source,target in [('Material','cA','cB'),('Left','cGround','cA'),('Right','cGround','cB'),('Unrelated','cA','cExtra')]:
        _direction(graph,BASE['t'+key],BASE[source],BASE[target])
        assert ((BASE['s'+key],RDF.type,OWL.ObjectProperty) in graph)==named
        observed={node for node in graph.subjects(OWL.inverseOf,BASE['t'+key]) if isinstance(node,URIRef)}
        assert observed==({BASE['s'+key]} if named else set())
        if named:_chain_inverse(graph,BASE['s'+key],BASE['t'+key])
    _no_connector(result)


def _chain_inverse(graph,inverse,primary):
    assert (inverse,RDF.type,OWL.ObjectProperty) in graph
    assert set(graph.objects(inverse,OWL.inverseOf))=={primary}
    assert (primary,OWL.inverseOf,inverse) not in graph
    assert set(graph.objects(inverse,RDFS.domain))==set(graph.objects(primary,RDFS.range))
    assert set(graph.objects(inverse,RDFS.range))==set(graph.objects(primary,RDFS.domain))


def _compatibility(result, mode, emitted, omitted=()):
    notices=[d for d in result.diagnostics if d.kind=='chain_compatibility']
    if not emitted:
        assert not notices
        return
    assert notices and all(d.severity in {'INFO','WARNING'} for d in notices)
    facts=set().union(*(d.facts for d in notices))
    assert not {'all_chains_outside_dl','all_semantics_preserved','global_dl_guarantee'} & facts
    if mode=='omit-conflicting-constraints':
        assert {'not_dl_guarantee','omission_policy_applied',*omitted}<=facts
    else:
        assert {'constraints_preserved','possible_owl_dl_incompatibility'}<=facts


@pytest.mark.parametrize('grounding',GROUNDINGS)
@pytest.mark.parametrize('reverse',[False,True],ids=['relation_first','classifier_first'])
@pytest.mark.parametrize('input_policy',POLICIES)
def test_recognized_material_derivation_uses_both_orders_without_separate_output(run,source_json,tmp_path,grounding,reverse,input_policy):
    """Rules: DK-REL-07, DK-REL-08, DK-DIAG-08, DK-DIAG-05, DK-GEN-05, DK-LBL-02."""
    document=source_json('shared/material_pattern');_grounding(document,grounding)
    connector=source_element(document,'rDerivation')
    connector.update(description='CONNECTOR_DESCRIPTION_SENTINEL',isDerived=True)
    if reverse:connector['properties'].reverse()
    assert not fixture_issues(document)
    result=run(path=write_input(tmp_path,document),iri_strategy='id',stereotype_policy='require-known',
               input_policy=input_policy,material_property_chains='preserve-conflicting-constraints')
    assert result.outcome=='completed';_pattern_resources(result)
    assert property_chains(result.ontology,BASE.tMaterial)=={(('inverse',BASE.tLeft),BASE.tRight)}
    assert not list(result.ontology.triples((None,RDFS.comment,Literal('CONNECTOR_DESCRIPTION_SENTINEL'))))
    assert not any(d.kind in {'unsupported_connector','derivation_omission','orientation_repair','derived_status'}
                   or d.severity=='ERROR' for d in result.diagnostics)
    _compatibility(result,'preserve-conflicting-constraints',True)


@pytest.mark.parametrize('grounding',GROUNDINGS)
@pytest.mark.parametrize('orientation',[(a,b,c) for a in (False,True) for b in (False,True) for c in (False,True)],
                         ids=['left'+str(int(a))+'_right'+str(int(b))+'_material'+str(int(c)) for a in (False,True) for b in (False,True) for c in (False,True)])
@pytest.mark.parametrize('mode',CHAIN_MODES[1:])
@pytest.mark.parametrize('inverse_mode',['all','none'])
def test_material_chain_order_and_anonymous_backward_steps_follow_primary_directions(run,source_json,source_path,tmp_path,grounding,orientation,mode,inverse_mode):
    """Rules: DK-REL-07, DK-REL-08, DK-INV-01, DK-INV-04, DK-GEN-03, DK-DIAG-07."""
    document=source_json('shared/material_pattern');_grounding(document,grounding)
    left,right,material=orientation
    for key,reverse in [('Left',left),('Right',right),('Material',material)]:
        if reverse:
            ends=source_element(document,'r'+key)['properties']
            ends[0]['propertyType'],ends[1]['propertyType']=ends[1]['propertyType'],ends[0]['propertyType']
    assert not fixture_issues(document)
    result=run(path=write_input(tmp_path,document),iri_strategy='id',stereotype_policy='require-known',
               inverse_properties=inverse_mode,material_property_chains=mode)
    assert result.outcome=='completed'
    expected=((BASE.tLeft if left else ('inverse',BASE.tLeft)),(('inverse',BASE.tRight) if right else BASE.tRight))
    if material:expected=((BASE.tRight if right else ('inverse',BASE.tRight)),(('inverse',BASE.tLeft) if left else BASE.tLeft))
    assert property_chains(result.ontology,BASE.tMaterial)=={expected}
    assert set(result.ontology.subjects(OWL.propertyChainAxiom,None))=={BASE.tMaterial}
    for key,reverse,a,b in [('Left',left,'cGround','cA'),('Right',right,'cGround','cB'),('Material',material,'cA','cB')]:
        _direction(result.ontology,BASE['t'+key],BASE[b if reverse else a],BASE[a if reverse else b])
        assert ((BASE['s'+key],RDF.type,OWL.ObjectProperty) in result.ontology)==(inverse_mode=='all')
        if inverse_mode=='all':_chain_inverse(result.ontology,BASE['s'+key],BASE['t'+key])
    if not any(orientation):
        assert property_chains(result.ontology,BASE.tMaterial)==property_chains(load_graph(source_path('relations/material_pattern','expected_chain.ttl')),BASE.tMaterial)
    _no_connector(result);_compatibility(result,mode,True)


@pytest.mark.parametrize('grounding',GROUNDINGS)
@pytest.mark.parametrize('explicit',[False,True],ids=['default_none','explicit_none'])
def test_disabled_material_chains_keep_both_direction_counts_and_all_other_properties(run,source_json,tmp_path,grounding,explicit):
    """Rules: DK-REL-07, DK-REL-08, DK-REL-09, DK-REL-10, DK-REL-11, DK-DIAG-07."""
    document=source_json('shared/material_pattern');_grounding(document,grounding)
    options={'material_property_chains':'none'} if explicit else {}
    result=run(path=write_input(tmp_path,document),iri_strategy='id',inverse_properties='all',**options)
    assert result.outcome=='completed';_pattern_resources(result)
    assert not list(result.ontology.triples((None,OWL.propertyChainAxiom,None)))
    _counts(result.ontology,BASE.cA,BASE.tMaterial,{('min',2),('max',5)})
    _counts(result.ontology,BASE.cB,BASE.sMaterial,{('exact',1)})
    _compatibility(result,'none',False)


@pytest.mark.parametrize('grounding',GROUNDINGS)
@pytest.mark.parametrize('defect',['no_derivation','no_left','no_right','inherited_left','names_only','participant_is_grounder','participant_relator','unrelated_extra','unrelated_right_extra'])
@pytest.mark.parametrize('mode',CHAIN_MODES)
def test_only_complete_direct_identifier_patterns_produce_chains(run,source_json,tmp_path,grounding,defect,mode):
    """Rules: DK-REL-07, DK-REL-08, DK-GEN-02, DK-REL-11, DK-DIAG-07."""
    document=source_json('shared/material_pattern');_grounding(document,grounding);contents=document['model']['contents']
    if defect.startswith('no_'):
        key={'no_derivation':'rDerivation','no_left':'rLeft','no_right':'rRight'}[defect]
        contents.remove(source_element(document,key))
    elif defect in {'inherited_left','names_only'}:
        source_element(document,'rLeft')['properties'][1]['propertyType']['id']='cExtra'
        if defect=='names_only':source_element(document,'cExtra')['name']=source_element(document,'cA')['name']
        else:contents.append({'id':'gParticipant','name':None,'description':None,'type':'Generalization','propertyAssignments':None,'specific':{'id':'cA','type':'Class'},'general':{'id':'cExtra','type':'Class'}})
    elif defect=='participant_is_grounder':
        source_element(document,'rMaterial')['properties'][0]['propertyType']['id']='cGround'
    elif defect=='participant_relator':
        source_element(document,'cA')['stereotype']='relator'
    else:
        extra=copy.deepcopy(source_element(document,'rRight' if defect=='unrelated_right_extra' else 'rLeft'));extra['id']='rExtraComponent'
        extra['properties'][0]['id']='sExtraComponent';extra['properties'][1].update(id='tExtraComponent',propertyType={'id':'cExtra','type':'Class'})
        contents.append(extra)
    assert not fixture_issues(document)
    result=run(path=write_input(tmp_path,document),iri_strategy='id',material_property_chains=mode)
    assert result.outcome=='completed'
    # A relator cannot be a participant in the relator pattern. The mode
    # pattern with that edit also has no complete matching characterization.
    emitted=(defect in {'unrelated_extra','unrelated_right_extra'} or (defect=='participant_relator' and grounding=='mode')) and mode!='none'
    assert property_chains(result.ontology,BASE.tMaterial)==({(('inverse',BASE.tLeft),BASE.tRight)} if emitted else set())
    assert (BASE.tMaterial,RDF.type,OWL.ObjectProperty) in result.ontology
    if not emitted:
        owner=BASE.cGround if defect=='participant_is_grounder' else BASE.cA
        _counts(result.ontology,owner,BASE.tMaterial,{('min',2),('max',5)})
        _counts(result.ontology,BASE.cB,BASE.sMaterial,{('exact',1)})
    _no_connector(result);_compatibility(result,mode,emitted)


@pytest.mark.parametrize('grounding',GROUNDINGS)
@pytest.mark.parametrize('side',['left','right'])
@pytest.mark.parametrize('input_policy',POLICIES)
@pytest.mark.parametrize('mode',CHAIN_MODES[1:])
def test_ambiguity_on_either_pattern_side_is_nonfatal_and_retains_constraints(run,source_json,tmp_path,grounding,side,input_policy,mode):
    """Rules: DK-REL-07, DK-REL-08, DK-DIAG-07, DK-DIAG-08, DK-DIAG-05."""
    document=source_json('shared/material_pattern');_grounding(document,grounding)
    extra=copy.deepcopy(source_element(document,'rLeft' if side=='left' else 'rRight'))
    extra['id']='rDuplicateComponent';extra['properties'][0]['id']='sDuplicateComponent';extra['properties'][1]['id']='tDuplicateComponent'
    document['model']['contents'].append(extra)
    assert not fixture_issues(document)
    result=run(path=write_input(tmp_path,document),iri_strategy='id',input_policy=input_policy,material_property_chains=mode)
    assert result.outcome=='completed';_pattern_resources(result)
    assert not property_chains(result.ontology,BASE.tMaterial)
    notices=[d for d in result.diagnostics if d.kind=='chain_ambiguity' and 'rMaterial' in d.identified_sources]
    assert notices and any('ambiguous_correspondence' in d.facts for d in notices)
    if grounding=='relator':assert any(d.severity=='WARNING' for d in notices)
    else:assert all(d.severity in {'INFO','WARNING'} for d in notices)
    _counts(result.ontology,BASE.cA,BASE.tMaterial,{('min',2),('max',5)})
    _counts(result.ontology,BASE.cB,BASE.sMaterial,{('exact',1)})
    assert (BASE.tDuplicateComponent,RDF.type,OWL.ObjectProperty) in result.ontology
    _compatibility(result,mode,False)


@pytest.mark.parametrize('aggregation',['NONE','SHARED','COMPOSITE'])
@pytest.mark.parametrize('stereotype',['material','mediation',None],ids=['ordinary_material','ordinary_mediation','missing_relation_stereotype'])
def test_aggregation_flags_do_not_create_a_mereology_bridge_or_asymmetry(run,source_json,tmp_path,aggregation,stereotype):
    """Rules: DK-REL-19, DK-PROP-04, DK-CLS-01, DK-DIAG-06."""
    document=source_json('shared/binary_relation');source_element(document,'rFocus')['stereotype']=stereotype
    source_element(document,'sFocus')['aggregationKind']=aggregation
    source_element(document,'cA')['isExtensional']=True
    result=run(path=write_input(tmp_path,document),iri_strategy='id',stereotype_policy='allow-missing')
    assert result.outcome=='completed';_direction(result.ontology)
    generics={URIRef(str(result.mereology_import)+'#'+name) for name in ('memberOf','subCollectionOf','subQuantityOf','componentOf')}
    assert not generics & set(result.ontology.objects(BASE.tFocus,RDFS.subPropertyOf))
    assert (BASE.tFocus,RDF.type,OWL.AsymmetricProperty) not in result.ontology
    assert not result.flag_semantic_output


@pytest.mark.parametrize('grounding',GROUNDINGS)
@pytest.mark.parametrize('mode',CHAIN_MODES)
@pytest.mark.parametrize('input_policy',POLICIES)
def test_same_class_grounding_never_chooses_occurrences_or_substitutes_both_chains(run,source_json,tmp_path,grounding,mode,input_policy):
    """Rules: DK-REL-07, DK-REL-08, DK-DIAG-07, DK-DIAG-08, DK-DIAG-05."""
    document=source_json('shared/material_pattern');_grounding(document,grounding)
    source_element(document,'tMaterial')['propertyType']['id']='cA'
    source_element(document,'tRight')['propertyType']['id']='cA'
    # Different end IDs, roles and bounds do not distinguish occurrences.
    result=run(path=write_input(tmp_path,document),iri_strategy='id',input_policy=input_policy,material_property_chains=mode)
    assert result.outcome=='completed'
    assert not list(result.ontology.triples((None,OWL.propertyChainAxiom,None)))
    for key in ('Material','Left','Right','Unrelated'):assert (BASE['t'+key],RDF.type,OWL.ObjectProperty) in result.ontology
    _counts(result.ontology,BASE.cA,BASE.tMaterial,{('min',2),('max',5)})
    _counts(result.ontology,BASE.cA,BASE.sMaterial,{('exact',1)})
    notices=[d for d in result.diagnostics if d.kind=='chain_ambiguity']
    if mode=='none':assert not notices
    else:assert any('rMaterial' in d.identified_sources and 'same_class_occurrences_unassigned' in d.facts and d.severity in {'INFO','WARNING'} for d in notices)
    _no_connector(result);_compatibility(result,mode,False)
    assert not any(d.kind=='unsupported_connector' or d.severity=='ERROR' for d in result.diagnostics)


@pytest.mark.parametrize('mode',CHAIN_MODES)
@pytest.mark.parametrize('inverse_mode',['all','none'])
@pytest.mark.parametrize('singleton',[False,True],ids=['ordinary_hierarchy','singleton_reverse_propagation'])
def test_chain_constraint_policy_propagates_only_through_actual_generated_hierarchy(run,source_json,tmp_path,mode,inverse_mode,singleton):
    """Rules: DK-REL-07, DK-REL-09, DK-REL-10, DK-REL-11, DK-REL-14, DK-REL-15, DK-REL-20, DK-INV-12, DK-DIAG-07, DK-DIAG-14."""
    document=source_json('relations/chain_constraints')
    source_element(document,'gsSingleton')['isComplete']=singleton
    result=run(path=write_input(tmp_path,document),iri_strategy='id',inverse_properties=inverse_mode,material_property_chains=mode)
    assert result.outcome=='completed'
    _pattern_resources(result,inverse_mode=='all')
    affected={'Material','Super','Grand'}|({'Peer'} if singleton else set())
    omitted=mode=='omit-conflicting-constraints'
    for key in ('Material','Super','Grand','Peer','PeerTwo'):
        _direction(result.ontology,BASE['t'+key],BASE.cA,BASE.cB)
        if inverse_mode=='all':_chain_inverse(result.ontology,BASE['s'+key],BASE['t'+key])
        expected={('min',2),('max',5)} if key=='Material' else {('exact',2)}
        _counts(result.ontology,BASE.cA,BASE['t'+key],set() if omitted and key in affected else expected)
        reverse=BASE['s'+key] if inverse_mode=='all' else ('inverse',BASE['t'+key])
        _counts(result.ontology,BASE.cB,reverse,set() if omitted and key in affected else {('exact',1)})
    # Chain-body-only and unrelated material properties keep their counts.
    _counts(result.ontology,BASE.cGround,BASE.tLeft,{('exact',1)})
    _counts(result.ontology,BASE.cGround,BASE.tRight,{('exact',1)})
    _counts(result.ontology,BASE.cA,BASE.tUnrelated,{('exact',4)})
    edges=[('Material','Super'),('Super','Grand'),('Peer','Super'),('PeerTwo','Super')]+([('Super','Peer')] if singleton else [])
    expected_edges={(BASE['t'+a],BASE['t'+b]) for a,b in edges}
    if inverse_mode=='all':expected_edges|={(BASE['s'+a],BASE['s'+b]) for a,b in edges}
    assert _edges(result.ontology)==expected_edges
    keys=['Material','Peer','PeerTwo']
    pairs={frozenset((BASE[p+a],BASE[p+b])) for p in (['t','s'] if inverse_mode=='all' else ['t'])
           for i,a in enumerate(keys) for b in keys[i+1:] if not omitted or not ({a,b}&affected)}
    assert _pairs(result.ontology)==pairs
    assert bool(property_chains(result.ontology,BASE.tMaterial))==(mode!='none')
    _compatibility(result,mode,mode!='none',{'cardinalities_omitted','property_disjointness_omitted'} if omitted else ())
    if omitted:
        reported=set().union(*(set(d.identified_sources) for d in result.diagnostics if d.kind=='chain_compatibility'))
        assert all({'r'+key,'t'+key,'s'+key}&reported for key in affected)
    notices=[d for d in result.diagnostics if d.kind=='singleton_completeness']
    if singleton:
        assert any(d.severity=='INFO' and {'gsSingleton','rSuper','rPeer'}<=set(d.identified_sources)
                   and {'extensional_equivalence','distinct_identifiers'}<=d.facts for d in notices)
    else:assert not notices
    _no_connector(result)


@pytest.mark.parametrize('grounding',GROUNDINGS)
@pytest.mark.parametrize('mode',CHAIN_MODES[1:])
def test_emitted_chain_without_conflicting_constraints_still_reports_compatibility(run,source_json,tmp_path,grounding,mode):
    """Rules: DK-REL-07, DK-DIAG-07."""
    document=source_json('shared/material_pattern');_grounding(document,grounding)
    for relation in document['model']['contents']:
        if relation['type']=='Relation':
            for end in relation['properties']:end['cardinality']=None
    result=run(path=write_input(tmp_path,document),iri_strategy='id',material_property_chains=mode)
    assert result.outcome=='completed'
    assert property_chains(result.ontology,BASE.tMaterial)=={(('inverse',BASE.tLeft),BASE.tRight)}
    _compatibility(result,mode,True)
    facts=set().union(*(d.facts for d in result.diagnostics if d.kind=='chain_compatibility'))
    assert not {'cardinalities_omitted','property_disjointness_omitted'} & facts


@pytest.mark.parametrize('derived',[False,True],ids=['not_derived','derived'])
@pytest.mark.parametrize('connector',[False,True],ids=['flag_without_derivation','explicit_derivation'])
def test_derived_flag_neither_creates_nor_suppresses_an_explicit_material_chain(run,source_json,tmp_path,derived,connector):
    """Rules: DK-GEN-05, DK-REL-07, DK-REL-08, DK-DIAG-16."""
    document=source_json('shared/material_pattern');source_element(document,'rMaterial')['isDerived']=derived
    if not connector:document['model']['contents'].remove(source_element(document,'rDerivation'))
    result=run(path=write_input(tmp_path,document),iri_strategy='id',material_property_chains='preserve-conflicting-constraints')
    assert result.outcome=='completed'
    assert bool(property_chains(result.ontology,BASE.tMaterial))==connector
    meanings=[c for c in result.comments if c.subject==BASE.tMaterial and c.field=='isDerived']
    assert {(c.context,c.value) for c in meanings}=={('relation',derived),('source_end',False),('target_end',False)}
    assert all((c.subject,RDFS.comment,c.literal) in result.ontology for c in meanings)
    if derived:
        events=[d for d in result.diagnostics if d.kind=='derived_status']
        assert any(d.severity=='INFO' for d in events)
        if connector:assert not any('explicit_derivation_omitted' in d.facts for d in events)
    else:assert not any(d.kind=='derived_status' for d in result.diagnostics)
    assert not result.flag_semantic_output


@pytest.mark.parametrize('mode',CHAIN_MODES[1:])
@pytest.mark.parametrize('input_policy',POLICIES)
def test_multiple_complete_mode_groundings_are_ambiguous_without_a_selected_chain(run,source_json,tmp_path,mode,input_policy):
    """Rules: DK-REL-07, DK-REL-08, DK-DIAG-05, DK-DIAG-08."""
    document=source_json('shared/material_pattern');_grounding(document,'mode')
    source_element(document,'cExtra')['stereotype']='mode'
    for original,new in [('rLeft','OtherLeft'),('rRight','OtherRight'),('rDerivation','OtherDerivation')]:
        relation=copy.deepcopy(source_element(document,original));relation['id']='r'+new
        relation['properties'][0]['id']='s'+new;relation['properties'][1]['id']='t'+new
        relation['properties'][1 if original=='rDerivation' else 0]['propertyType']={'id':'cExtra','type':'Class'}
        document['model']['contents'].append(relation)
    assert not fixture_issues(document)
    result=run(path=write_input(tmp_path,document),iri_strategy='id',input_policy=input_policy,material_property_chains=mode)
    assert result.outcome=='completed'
    assert not property_chains(result.ontology,BASE.tMaterial)
    assert any(d.kind=='chain_ambiguity' and 'rMaterial' in d.identified_sources and d.severity in {'INFO','WARNING'} for d in result.diagnostics)
    _counts(result.ontology,BASE.cA,BASE.tMaterial,{('min',2),('max',5)})
    _no_connector(result,('rDerivation','sDerivation','tDerivation','rOtherDerivation','sOtherDerivation','tOtherDerivation'))


@pytest.mark.parametrize('grounding',GROUNDINGS)
@pytest.mark.parametrize('variant',['renamed','reordered','renamed_reordered'])
def test_chain_matching_uses_source_ids_independently_of_names_and_serialized_declaration_order(run,source_json,tmp_path,grounding,variant):
    """Rules: DK-REL-07, DK-REL-08, DK-CONF-01."""
    document=source_json('shared/material_pattern');_grounding(document,grounding)
    if variant!='reordered':
        for item in document['model']['contents']:
            if item['type']=='Class' or (item['type']=='Relation' and item['id']!='rDerivation'):item['name']='SameName'
    if variant!='renamed':document['model']['contents'].reverse()
    assert not fixture_issues(document)
    result=run(path=write_input(tmp_path,document),iri_strategy='id',material_property_chains='preserve-conflicting-constraints')
    assert result.outcome=='completed';_pattern_resources(result)
    assert property_chains(result.ontology,BASE.tMaterial)=={(('inverse',BASE.tLeft),BASE.tRight)}


@pytest.mark.parametrize('pattern',['material_to_quality','comparative_to_relator','ordinary_to_mode','missing_relation_stereotype',
                                    'missing_classifier_stereotype','missing_connector_stereotype','non_derivation_connector','relation_to_relation'])
@pytest.mark.parametrize('reverse',[False,True],ids=['relation_first','relation_last'])
@pytest.mark.parametrize('input_policy',POLICIES)
def test_resolved_unmapped_connectors_warn_without_inferred_pattern_or_representation(run,source_json,tmp_path,pattern,reverse,input_policy):
    """Rules: DK-REL-17, DK-REL-08, DK-REL-18, DK-DIAG-05, DK-DIAG-06, DK-INV-02, DK-INV-04."""
    document=source_json('shared/material_pattern')
    if pattern=='material_to_quality':source_element(document,'cGround')['stereotype']='quality'
    elif pattern=='comparative_to_relator':source_element(document,'rMaterial')['stereotype']='comparative'
    elif pattern=='ordinary_to_mode':
        source_element(document,'rMaterial')['stereotype']='mediation';source_element(document,'cGround')['stereotype']='mode'
    elif pattern=='missing_relation_stereotype':source_element(document,'rMaterial')['stereotype']=None
    elif pattern=='missing_classifier_stereotype':source_element(document,'cGround')['stereotype']=None
    elif pattern=='missing_connector_stereotype':source_element(document,'rDerivation')['stereotype']=None
    elif pattern=='non_derivation_connector':source_element(document,'rDerivation')['stereotype']='material'
    else:source_element(document,'tDerivation')['propertyType']={'id':'rLeft','type':'Relation'}
    if reverse:source_element(document,'rDerivation')['properties'].reverse()
    assert not fixture_issues(document)
    result=run(path=write_input(tmp_path,document),iri_strategy='id',input_policy=input_policy,
               stereotype_policy='allow-missing',material_property_chains='preserve-conflicting-constraints')
    assert result.outcome=='completed';_pattern_resources(result)
    assert not list(result.ontology.triples((None,OWL.propertyChainAxiom,None)))
    assert any(d.kind=='unsupported_connector' and d.severity=='WARNING' and 'rDerivation' in d.identified_sources
               and 'no_accepted_endpoint_mapping' in d.facts for d in result.diagnostics)
    assert not any(d.kind in {'semantic_validation','comparative_derivation_semantics'} or d.severity=='ERROR' for d in result.diagnostics)
    _counts(result.ontology,BASE.cA,BASE.tMaterial,{('min',2),('max',5)})
    _counts(result.ontology,BASE.cB,BASE.sMaterial,{('exact',1)})


@pytest.mark.parametrize('failure',['null','malformed','unresolved'])
@pytest.mark.parametrize('input_policy',POLICIES)
def test_unresolved_connector_endpoint_remains_structural_instead_of_an_unsupported_pattern(run,source_json,tmp_path,failure,input_policy):
    """Rules: DK-REL-17, DK-REL-08, DK-DIAG-03, DK-DIAG-05, DK-DIAG-08."""
    document=source_json('shared/material_pattern')
    source_element(document,'tDerivation')['propertyType']={'null':None,'malformed':'cGround','unresolved':{'id':'cMissing','type':'Class'}}[failure]
    result=run(path=write_input(tmp_path,document),iri_strategy='id',input_policy=input_policy,material_property_chains='omit-conflicting-constraints')
    assert any(d.severity=='ERROR' for d in result.diagnostics)
    assert not any(d.kind=='unsupported_connector' for d in result.diagnostics)
    if input_policy!='best-effort':assert result.outcome=='aborted' and result.ontology is None
    else:
        assert result.outcome=='completed-with-errors';_pattern_resources(result)
        assert not property_chains(result.ontology,BASE.tMaterial)
        _counts(result.ontology,BASE.cA,BASE.tMaterial,{('min',2),('max',5)})


@pytest.mark.parametrize('mode',CHAIN_MODES)
@pytest.mark.parametrize('reverse',[False,True],ids=['comparative_first','quality_first'])
@pytest.mark.parametrize('input_policy',POLICIES)
def test_comparative_quality_derivation_has_no_comparison_semantics_and_a_distinct_nonfatal_notice(run,source_json,tmp_path,mode,reverse,input_policy):
    """Rules: DK-REL-18, DK-REL-17, DK-REL-01, DK-INV-02, DK-DIAG-05, DK-LBL-02."""
    document=source_json('shared/material_pattern')
    source_element(document,'rMaterial')['stereotype']='comparative'
    source_element(document,'cGround')['stereotype']='quality'
    if reverse:source_element(document,'rDerivation')['properties'].reverse()
    result=run(path=write_input(tmp_path,document),iri_strategy='id',input_policy=input_policy,material_property_chains=mode)
    assert result.outcome=='completed';_pattern_resources(result)
    assert result.comparative_semantic_output==(), "Read actual comparative output; do not presume absent semantics"
    assert not list(result.ontology.triples((None,OWL.propertyChainAxiom,None)))
    assert not list(result.ontology.objects(BASE.tMaterial,OWL.equivalentProperty))
    assert not list(result.ontology.subjects(OWL.equivalentProperty,BASE.tMaterial))
    forbidden={OWL.TransitiveProperty,OWL.SymmetricProperty,OWL.AsymmetricProperty,OWL.ReflexiveProperty,
               OWL.IrreflexiveProperty,OWL.FunctionalProperty,OWL.InverseFunctionalProperty}
    assert not forbidden & set(result.ontology.objects(BASE.tMaterial,RDF.type))
    _counts(result.ontology,BASE.cA,BASE.tMaterial,{('min',2),('max',5)})
    _counts(result.ontology,BASE.cB,BASE.sMaterial,{('exact',1)})
    assert any(d.kind=='comparative_derivation_semantics' and d.severity in {'INFO','WARNING'}
               and {'rDerivation','rMaterial','cGround'}<=set(d.identified_sources) for d in result.diagnostics)
    assert not any(d.kind=='unsupported_connector' or d.severity=='ERROR' for d in result.diagnostics)
    _compatibility(result,mode,False)


@pytest.mark.parametrize('stereotype',['memberOf','subCollectionOf','subQuantityOf','componentOf'])
@pytest.mark.parametrize('reverse',[False,True],ids=['modeled_forward','modeled_reverse'])
@pytest.mark.parametrize('inverse_mode',['all','none'])
@pytest.mark.parametrize('mode',CHAIN_MODES)
def test_mereology_uses_primary_direction_generic_bridge_and_primary_only_asserted_asymmetry(run,source_json,tmp_path,stereotype,reverse,inverse_mode,mode):
    """Rules: DK-GEN-04, DK-REL-19, DK-REL-07, DK-PROP-04, DK-REL-09, DK-REL-10, DK-REL-11, DK-INV-04."""
    document=source_json('shared/binary_relation');source_element(document,'rFocus')['stereotype']=stereotype
    source_element(document,'sFocus').update(cardinality='1',aggregationKind='COMPOSITE' if reverse else 'NONE')
    source_element(document,'tFocus')['cardinality']='2'
    if reverse:
        a=source_element(document,'sFocus');b=source_element(document,'tFocus')
        a['propertyType'],b['propertyType']=b['propertyType'],a['propertyType']
    result=run(path=write_input(tmp_path,document),iri_strategy='id',inverse_properties=inverse_mode,material_property_chains=mode)
    assert result.outcome=='completed'
    source,target=(BASE.cB,BASE.cA) if reverse else (BASE.cA,BASE.cB)
    _direction(result.ontology,BASE.tFocus,source,target)
    u=result.mereology_import
    assert u == URIRef('https://w3id.org/directkg/vocab/dkgm')
    assert isinstance(u,URIRef) and '#' not in str(u)
    generic=URIRef(str(u)+'#'+stereotype)
    assert (BASE.tFocus,RDFS.subPropertyOf,generic) in result.ontology
    assert (BASE.tFocus,RDF.type,OWL.AsymmetricProperty) in result.ontology
    assert (BASE.sFocus,RDF.type,OWL.AsymmetricProperty) not in result.ontology
    assert not list(result.ontology.objects(BASE.sFocus,RDFS.subPropertyOf))
    _counts(result.ontology,source,BASE.tFocus,{('exact',2)})
    _counts(result.ontology,target,BASE.sFocus if inverse_mode=='all' else ('inverse',BASE.tFocus),{('exact',1)})
    assert ((BASE.sFocus,RDF.type,OWL.ObjectProperty) in result.ontology)==(inverse_mode=='all')
    assert not list(result.ontology.triples((None,OWL.propertyChainAxiom,None)))
    assert not result.flag_semantic_output
    _compatibility(result,mode,False)


@pytest.mark.parametrize('mode',CHAIN_MODES)
def test_compatible_source_mereologies_do_not_create_arbitrary_source_chains_or_mappings(run,source_json,tmp_path,mode):
    """Rules: DK-REL-19, DK-GEN-04, DK-REL-07."""
    document=source_json('shared/binary_relation')
    source_element(document,'rFocus')['stereotype']='subQuantityOf'
    other=copy.deepcopy(source_element(document,'rFocus'));other.update(id='rNext',name='nextPart')
    other['properties'][0].update(id='sNext',propertyType={'id':'cB','type':'Class'})
    other['properties'][1].update(id='tNext',propertyType={'id':'cA','type':'Class'})
    document['model']['contents'].append(other)
    result=run(path=write_input(tmp_path,document),iri_strategy='id',material_property_chains=mode)
    assert result.outcome=='completed'
    assert result.mereology_import == URIRef('https://w3id.org/directkg/vocab/dkgm')
    generic=URIRef(str(result.mereology_import)+'#subQuantityOf')
    for prop in (BASE.tFocus,BASE.tNext):
        assert (prop,RDFS.subPropertyOf,generic) in result.ontology
        assert (prop,RDF.type,OWL.AsymmetricProperty) in result.ontology
        assert (prop,RDF.type,OWL.TransitiveProperty) not in result.ontology
    assert not list(result.ontology.triples((None,OWL.propertyChainAxiom,None)))
    _compatibility(result,mode,False)


@pytest.mark.parametrize('grounding',GROUNDINGS)
@pytest.mark.parametrize('inverse_mode',['all','none'])
def test_material_chain_modes_keep_name_strategy_source_identity_and_use_anonymous_backward_steps(run,source_json,tmp_path,grounding,inverse_mode):
    """Rules: DK-REL-07, DK-REL-08, DK-INV-04, DK-INV-07, DK-IRI-09, DK-CONF-02."""
    document=source_json('shared/material_pattern');_grounding(document,grounding)
    path=write_input(tmp_path,document)
    observations=[run(path=path,iri_strategy='name',inverse_properties=inverse_mode,material_property_chains=mode) for mode in CHAIN_MODES]
    assert all(result.outcome=='completed' for result in observations)
    source_ids=['cA','cB','cGround','cExtra','tMaterial','tLeft','tRight','tUnrelated']
    resources=[{identifier:one_subject(result.ontology,DCTERMS.identifier,Literal(identifier)) for identifier in source_ids} for result in observations]
    assert resources[0]==resources[1]==resources[2]
    for mode,result,mapped in zip(CHAIN_MODES,observations,resources):
        expected=(('inverse',mapped['tLeft']),mapped['tRight'])
        assert property_chains(result.ontology,mapped['tMaterial'])==({expected} if mode!='none' else set())
        assert result.unrepresented_connector_output==(), "Bind the actual connector-output reader"
