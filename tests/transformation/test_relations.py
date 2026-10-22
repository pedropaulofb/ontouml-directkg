"""Ordinary relation naming, labels, cardinalities and explicit hierarchies."""

import copy
import pytest
from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, XSD

from tests.support.data import fixture_issues, source_element, write_input
from tests.support.rdf import (assert_contains, cardinality_facts, load_graph,
                               necessary_restrictions, one_subject)

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
