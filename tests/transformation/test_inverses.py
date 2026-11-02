"""Conditional named inverses, end identity, naming precedence and stability."""

import copy
import pytest
from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS

from tests.support.data import fixture_issues, source_element, write_input
from tests.support.invocation import diagnostic_signatures
from tests.support.rdf import assert_contains, load_graph, one_subject

BASE=Namespace('https://example.test/model#')
MODES=['all','informed','named','none']


def _resource(result,identifier,strategy):
    return BASE[identifier] if strategy=='id' else one_subject(result.ontology,DCTERMS.identifier,Literal(identifier))


def _inverse(graph,inverse,primary):
    assert isinstance(inverse,URIRef) and (inverse,RDF.type,OWL.ObjectProperty) in graph
    assert set(graph.objects(inverse,OWL.inverseOf))=={primary}
    assert (primary,OWL.inverseOf,inverse) not in graph
    domain=set(graph.objects(primary,RDFS.domain));range_=set(graph.objects(primary,RDFS.range))
    assert len(domain)==len(range_)==1
    assert set(graph.objects(inverse,RDFS.domain))==range_
    assert set(graph.objects(inverse,RDFS.range))==domain


def _fallback(primary):
    local=str(primary).removeprefix(str(BASE))
    return 'inverseOf'+local[:1].upper()+local[1:]


def _assert_source_backed_identity_preserved(baseline, result):
    for resource, identifier in baseline.ontology.subject_objects(DCTERMS.identifier):
        assert one_subject(result.ontology, DCTERMS.identifier, identifier) == resource


ELIGIBILITY=[
 pytest.param('workers',None,True,True,id='role_without_count'),
 pytest.param(None,None,False,False,id='null_role_null_count'),
 pytest.param('absent','absent',False,False,id='both_fields_absent'),
 pytest.param('',None,False,False,id='empty_role'),
 pytest.param(' \t ',None,False,False,id='whitespace_role'),
 pytest.param(None,'1',False,True,id='count_only'),
 pytest.param(None,'0',False,True,id='zero_count_only'),
 pytest.param(None,'*',False,True,id='star_count_only'),
 pytest.param(None,'0..*',False,True,id='zero_unbounded_count_only'),
 pytest.param(None,'absent',False,False,id='null_role_missing_count'),
 pytest.param('workers','absent',True,True,id='role_over_missing_count'),
 pytest.param('workers','*',True,True,id='role_and_nonnull_count'),
 pytest.param('___',None,True,True,id='unusable_ascii_role_still_present'),
 pytest.param('東京',None,True,True,id='unicode_role_still_present'),
 pytest.param({'en':'  ','nl':'東京'},None,True,True,id='localized_any_nonwhitespace'),
 pytest.param({'en':'  ','nl':'\t'},None,False,False,id='localized_all_whitespace'),
]


@pytest.mark.parametrize('mode',['default']+MODES)
@pytest.mark.parametrize('role,cardinality,named,informed',ELIGIBILITY)
def test_inverse_modes_use_role_presence_or_nonnull_multiplicity_without_name_normalization(run, source_json, tmp_path, mode, role, cardinality, named, informed):
    """Rules: DK-INV-01, DK-INV-02, DK-INV-03, DK-INV-04, DK-INV-05, DK-INV-09, DK-INV-10, DK-INV-11, DK-IRI-06, DK-IRI-10, DK-DIAG-09."""
    document=source_json('shared/binary_relation');end=source_element(document,'sFocus')
    if role=='absent':del end['name']
    else:end['name']=copy.deepcopy(role)
    if cardinality=='absent':del end['cardinality']
    else:end['cardinality']=cardinality
    assert not fixture_issues(document)
    options={} if mode=='default' else {'inverse_properties':mode}
    result=run(path=write_input(tmp_path,document),iri_strategy='id',**options)
    assert result.outcome=='completed'
    expected=mode in {'default','all'} or (mode=='named' and named) or (mode=='informed' and informed)
    assert ((BASE.sFocus,RDF.type,OWL.ObjectProperty) in result.ontology)==expected
    if expected:_inverse(result.ontology,BASE.sFocus,BASE.tFocus)
    else:assert not any(BASE.sFocus in triple for triple in result.ontology)
    assert (BASE.tFocus,RDF.type,OWL.ObjectProperty) in result.ontology
    if mode in {'named','informed'} and not expected:
        assert not any(d.kind=='inverse_omission' for d in result.diagnostics)
        assert not result.inverse_omission_reports
    assert not any(d.severity=='ERROR' for d in result.diagnostics)


@pytest.mark.parametrize('mode',MODES)
@pytest.mark.parametrize('self_relation',[False,True],ids=['binary','self_relation'])
def test_id_strategy_uses_escaped_directional_end_ids_without_rd28_annotations(run, source_json, tmp_path, mode, self_relation):
    """Rules: DK-INV-02, DK-INV-03, DK-INV-04, DK-INV-09, DK-IRI-05, DK-IRI-06, DK-IRI-09, DK-GEN-03."""
    document=source_json('shared/binary_relation')
    source_element(document,'rFocus')['id']='AssociationSentinel'
    source_element(document,'sFocus')['id']='9 src._'
    target=source_element(document,'tFocus');target['id']='T-end'
    if self_relation:target['propertyType']['id']='cA'
    result=run(path=write_input(tmp_path,document),iri_strategy='id',inverse_properties=mode)
    assert result.outcome=='completed'
    primary=BASE.T_x2Dend;inverse=BASE.id_9_x20src_x2E_x5F
    assert (primary,RDF.type,OWL.ObjectProperty) in result.ontology
    assert set(result.ontology.objects(primary,RDFS.domain))=={BASE.cA}
    assert set(result.ontology.objects(primary,RDFS.range))=={BASE.cA if self_relation else BASE.cB}
    assert ((inverse,RDF.type,OWL.ObjectProperty) in result.ontology)==(mode!='none')
    if mode!='none':_inverse(result.ontology,inverse,primary)
    for forbidden in (BASE.AssociationSentinel,BASE.sFocus,BASE.tFocus):assert not any(forbidden in triple for triple in result.ontology)
    for identifier in ('AssociationSentinel','9 src._','T-end'):
        assert not list(result.ontology.subjects(DCTERMS.identifier,Literal(identifier)))


@pytest.mark.parametrize('strategy',['name','id'])
@pytest.mark.parametrize('role',['workers',None,{'pt-BR':'trabalhadores','en':'workers'}],ids=['plain_role','absent_role','localized_role'])
def test_inverse_labels_use_only_original_source_end_and_never_synthesize_a_label(run, source_json, tmp_path, strategy, role):
    """Rules: DK-INV-03, DK-INV-04, DK-INV-05, DK-INV-06, DK-INV-11, DK-LBL-01, DK-LBL-02, DK-IRI-10."""
    document=source_json('shared/binary_relation')
    source_element(document,'sFocus')['name']=copy.deepcopy(role)
    source_element(document,'rFocus')['name']='Wrong inverse label'
    source_element(document,'tFocus')['name']='Wrong target role'
    result=run(path=write_input(tmp_path,document),iri_strategy=strategy,inverse_properties='all')
    assert result.outcome=='completed'
    primary=_resource(result,'tFocus',strategy);inverse=_resource(result,'sFocus',strategy)
    _inverse(result.ontology,inverse,primary)
    expected=set() if role is None else ({Literal(v,lang=k) for k,v in role.items()} if isinstance(role,dict) else {Literal(role)})
    assert set(result.ontology.objects(inverse,RDFS.label))==expected
    if strategy=='name':
        assert inverse==(BASE[_fallback(primary)] if role is None else BASE.workers)


@pytest.mark.parametrize('strategy',['name','id'])
@pytest.mark.parametrize('mode',['all','none'])
def test_end_descriptions_have_independent_primary_and_inverse_destinations(run, source_json, tmp_path, strategy, mode):
    """Rules: DK-INV-05, DK-LBL-02, DK-REL-01, DK-INV-01, DK-INV-04."""
    document=source_json('shared/binary_relation')
    source_element(document,'rFocus')['description']='ENCLOSING_RELATION_DESCRIPTION'
    source_element(document,'tFocus')['description']='TARGET_END_DESCRIPTION'
    source_element(document,'sFocus')['description']={'en':'SOURCE_END_DESCRIPTION','pt-BR':'DESCRIÇÃO_ORIGEM'}
    result=run(path=write_input(tmp_path,document),iri_strategy=strategy,inverse_properties=mode,language='nl')
    assert result.outcome=='completed';primary=_resource(result,'tFocus',strategy)
    assert (primary,RDFS.comment,Literal('ENCLOSING_RELATION_DESCRIPTION',lang='nl')) in result.ontology
    assert (primary,RDFS.comment,Literal('TARGET_END_DESCRIPTION',lang='nl')) in result.ontology
    assert not list(result.ontology.triples((None,RDFS.comment,Literal('ENCLOSING_RELATION_DESCRIPTIONTARGET_END_DESCRIPTION',lang='nl'))))
    source_values={Literal('SOURCE_END_DESCRIPTION',lang='nl'),Literal('DESCRIÇÃO_ORIGEM',lang='nl')}
    if mode=='all':
        inverse=_resource(result,'sFocus',strategy)
        assert source_values<=set(result.ontology.objects(inverse,RDFS.comment))
        for value in ('ENCLOSING_RELATION_DESCRIPTION','TARGET_END_DESCRIPTION'):
            assert (inverse,RDFS.comment,Literal(value,lang='nl')) not in result.ontology
    else:
        for value in source_values:assert not list(result.ontology.triples((None,RDFS.comment,value)))
    assert not any(d.kind=='omitted_description' or d.severity=='ERROR' for d in result.diagnostics)


@pytest.mark.parametrize('mode',['informed','named'])
def test_source_description_alone_does_not_generate_a_conditional_inverse(run, source_json, tmp_path, mode):
    """Rules: DK-INV-01, DK-INV-05, DK-INV-10, DK-LBL-02."""
    document=source_json('shared/binary_relation');source_element(document,'sFocus').update(name=None,description='Description alone must not force an inverse')
    result=run(path=write_input(tmp_path,document),iri_strategy='id',inverse_properties=mode)
    assert result.outcome=='completed'
    assert (BASE.sFocus,RDF.type,OWL.ObjectProperty) not in result.ontology
    assert not list(result.ontology.triples((None,RDFS.comment,Literal('Description alone must not force an inverse'))))
    assert not result.inverse_omission_reports
    assert not any(d.kind in {'inverse_omission','omitted_description'} for d in result.diagnostics)


@pytest.mark.parametrize('role,expected_local',[pytest.param('workers','workers',id='plain'),pytest.param('équipe,  bleue','equipe_bleue',id='normalized_role'),pytest.param({'nl':'werknemers','EN':'Zulu','en':'Alpha'},'Alpha',id='localized_key_tie')])
def test_unique_role_candidate_is_used_without_optional_property_qualification(run, source_json, tmp_path, role, expected_local):
    """Rules: DK-INV-05, DK-INV-07, DK-INV-11, DK-IRI-03, DK-IRI-10, DK-LBL-02."""
    for reverse in (False,True):
        document=source_json('shared/binary_relation');document['languages']=['nl']
        source_element(document,'sFocus')['name']=dict(reversed(list(role.items()))) if reverse and isinstance(role,dict) else copy.deepcopy(role)
        result=run(path=write_input(tmp_path,document),inverse_properties='named',language='nl')
        assert result.outcome=='completed'
        inverse=_resource(result,'sFocus','name');assert inverse==BASE[expected_local]
        values=role.values() if isinstance(role,dict) else [role]
        assert set(result.ontology.objects(inverse,RDFS.label))=={Literal(v,lang='nl') for v in values}
        _inverse(result.ontology,inverse,_resource(result,'tFocus','name'))


@pytest.mark.parametrize('collision',['class','attribute','primary_candidate_claim'])
def test_role_collision_preserves_source_backed_candidates_and_falls_back_from_primary(run, source_json, tmp_path, collision):
    """Rules: DK-INV-06, DK-INV-07, DK-INV-10, DK-IRI-07, DK-IRI-09, DK-PROP-02."""
    document=source_json('shared/binary_relation')
    source_element(document,'sFocus')['name']={'class':'HTTPServer','attribute':'focus','primary_candidate_claim':'worksFor'}[collision]
    if collision=='attribute':
        attribute=copy.deepcopy(source_element(document,'tFocus'))
        attribute.update(id='pAttribute',name='focus',propertyType=None,aggregationKind=None)
        source_element(document,'cA')['properties']=[attribute]
    baseline=run(path=write_input(tmp_path,document,'without.json'),inverse_properties='none')
    result=run(path=write_input(tmp_path,document),inverse_properties='all')
    assert baseline.outcome==result.outcome=='completed'
    ids=['cA','cB','tFocus']+(['pAttribute'] if collision=='attribute' else [])
    for identifier in ids:assert _resource(baseline,identifier,'name')==_resource(result,identifier,'name')
    primary=_resource(result,'tFocus','name');inverse=_resource(result,'sFocus','name')
    assert inverse==BASE[_fallback(primary)]
    assert set(result.ontology.objects(inverse,RDFS.label))=={Literal(source_element(document,'sFocus')['name'])}
    _inverse(result.ontology,inverse,primary)


def test_every_inverse_sharing_a_role_candidate_abandons_it_without_merging(run, source_json, tmp_path):
    """Rules: DK-INV-05, DK-INV-06, DK-INV-07, DK-INV-10, DK-PROP-01."""
    document=source_json('shared/binary_relation');source_element(document,'sFocus')['name']='staff'
    other=copy.deepcopy(source_element(document,'rFocus'));other.update(id='rOther',name='belongsTo')
    other['properties'][0]['id']='sOther';other['properties'][1]['id']='tOther';document['model']['contents'].append(other)
    result=run(path=write_input(tmp_path,document),inverse_properties='all')
    assert result.outcome=='completed'
    inverses=[]
    for source,target in [('sFocus','tFocus'),('sOther','tOther')]:
        inverse=_resource(result,source,'name');primary=_resource(result,target,'name');inverses.append(inverse)
        assert inverse==BASE[_fallback(primary)] and inverse!=BASE.staff
        assert set(result.ontology.objects(inverse,RDFS.label))=={Literal('staff')}
        _inverse(result.ontology,inverse,primary)
    assert len(set(inverses))==2


@pytest.mark.parametrize('localized',[False,True],ids=['plain_domain','localized_domain'])
def test_secondary_fallback_collision_qualifies_only_inverse_with_its_domain(run, source_json, tmp_path, localized):
    """Rules: DK-INV-06, DK-INV-07, DK-INV-08, DK-INV-10, DK-IRI-10, DK-PROP-02."""
    document=source_json('shared/binary_relation');source_element(document,'sFocus')['name']=None
    source_element(document,'cB')['name']={'nl':'Boom','en':'XMLNode'} if localized else 'XMLNode'
    for i,name in enumerate(('inverseOfWorksFor','inverseOfWorksFor_HTTPServer')):
        claim=copy.deepcopy(source_element(document,'cA'));claim.update(id='cClaim'+str(i),name=name);document['model']['contents'].append(claim)
    baseline=run(path=write_input(tmp_path,document,'without.json'),inverse_properties='none',language='nl')
    result=run(path=write_input(tmp_path,document),inverse_properties='all',language='nl')
    assert baseline.outcome==result.outcome=='completed'
    primary=_resource(result,'tFocus','name');inverse=_resource(result,'sFocus','name')
    assert inverse==BASE[_fallback(primary)+'_XMLNode']
    for identifier in ('tFocus','cA','cB','cClaim0','cClaim1'):
        assert _resource(result,identifier,'name')==_resource(baseline,identifier,'name')
    _inverse(result.ontology,inverse,primary)
    assert not list(result.ontology.objects(inverse,RDFS.label))


def test_residual_inverse_collision_suffixes_follow_source_end_ids_not_serialized_order(run, source_json, source_path, tmp_path):
    """Rules: DK-INV-06, DK-INV-07, DK-INV-08, DK-INV-10, DK-IRI-07, DK-IRI-09, DK-PROP-02, DK-CONF-01, DK-DIAG-01. A1.3 free-slot regression."""
    document=source_json('inverses/secondary_collisions')
    baseline=run(path=write_input(tmp_path,document,'without.json'),inverse_properties='none')
    for reverse in (False,True):
        if reverse:document['model']['contents'].reverse()
        result=run(path=write_input(tmp_path,document),inverse_properties='all')
        assert result.outcome==baseline.outcome=='completed'
        assert_contains(result.ontology,load_graph(source_path('inverses/secondary_collisions','expected.ttl')))
        for identifier in ('tLower','tUpper','pLower','pUpper','cSource','cOrganization','cClaim'):
            assert _resource(result,identifier,'name')==_resource(baseline,identifier,'name')
        assert _resource(result,'a_source','name')==BASE.inverseOfWorksFor_Source_Organization_1
        assert _resource(result,'z_source','name')==BASE.inverseOfWorksFor_Source_Organization_2
        assert diagnostic_signatures(result.diagnostics) == diagnostic_signatures(baseline.diagnostics)


ROLE_NAMING = {
    'punctuation': '___', 'non_ascii': '東京',
    'localized_unusable': {'en': '___', 'nl': '東京'},
    'localized_usable': {'en': '___', 'nl': 'werknemers'},
    'absent_role': None,
}
ROLE_REQUESTS = [(mode, strategy, case) for mode in ['default'] + MODES
                 for strategy in ['name', 'id'] for case in ROLE_NAMING]
ROLE_REQUEST_IDS = [mode if strategy == 'name' and case == 'localized_unusable'
                   and mode in {'all', 'informed', 'named'} else f'{mode}-{strategy}-{case}'
                   for mode, strategy, case in ROLE_REQUESTS]


@pytest.mark.parametrize('mode,strategy,case', ROLE_REQUESTS, ids=ROLE_REQUEST_IDS)
def test_unusable_present_role_retains_eligibility_and_labels_without_inventing_exact_name(
        run, source_json, tmp_path, mode, strategy, case):
    """Rules: DK-INV-01, DK-INV-02, DK-INV-03, DK-INV-04, DK-INV-05, DK-INV-06, DK-INV-09, DK-INV-10, DK-INV-11, DK-IRI-07, DK-IRI-10, DK-LBL-02, DK-DIAG-01.

    A1.1 now supplies the exact fallback; retain the three historical node IDs.
    Source roles remain present, including named mode. Lexical selection and
    source text survive dictionary order and explicit literal-language override.
    The absent-role control confirms that descriptions do not force generation.
    """
    document = source_json('shared/binary_relation')
    language = None if case == 'localized_unusable' else 'fr'
    document['languages'] = [] if language is None else ['nl', 'de']
    source_element(document, 'sFocus').update(name=copy.deepcopy(ROLE_NAMING[case]),
        description={'en': 'SOURCE_END_DESCRIPTION', 'nl': 'BRONBESCHRIJVING'})
    source_element(document, 'tFocus')['description'] = 'TARGET_DESCRIPTION'
    source_element(document, 'rFocus')['description'] = 'RELATION_DESCRIPTION'
    baseline = run(path=write_input(tmp_path, document, 'without.json'), iri_strategy=strategy,
                   inverse_properties='none', language=language)
    assert baseline.outcome == 'completed'
    for reverse in (False, True):
        request = copy.deepcopy(document)
        role = source_element(request, 'sFocus')['name']
        if reverse and isinstance(role, dict):
            source_element(request, 'sFocus')['name'] = dict(reversed(list(role.items())))
        assert not fixture_issues(request)
        options = {} if mode == 'default' else {'inverse_properties': mode}
        result = run(path=write_input(tmp_path, request), iri_strategy=strategy, language=language, **options)
        assert result.outcome == 'completed'
        _assert_source_backed_identity_preserved(baseline, result)
        if strategy == 'id':
            for resource, kind in [(BASE.cA, OWL.Class), (BASE.cB, OWL.Class), (BASE.tFocus, OWL.ObjectProperty)]:
                assert (resource, RDF.type, kind) in baseline.ontology
                assert (resource, RDF.type, kind) in result.ontology
        assert diagnostic_signatures(result.diagnostics) == diagnostic_signatures(baseline.diagnostics)
        primary = _resource(result, 'tFocus', strategy)
        generated = mode in {'default', 'all'} or (mode in {'informed', 'named'} and case != 'absent_role')
        if not generated:
            assert not list(result.ontology.subject_objects(OWL.inverseOf))
            assert not list(result.ontology.subjects(DCTERMS.identifier, Literal('sFocus')))
            for text, local in [('SOURCE_END_DESCRIPTION', 'en'), ('BRONBESCHRIJVING', 'nl')]:
                assert not list(result.ontology.subjects(RDFS.comment, Literal(text, lang=language or local)))
            continue
        inverse = _resource(result, 'sFocus', strategy)
        expected = BASE.sFocus if strategy == 'id' else BASE[
            'werknemers' if case == 'localized_usable' else _fallback(primary)]
        assert inverse == expected and inverse != primary
        _inverse(result.ontology, inverse, primary)
        labels = (set() if role is None else
                  {Literal(v, lang=language or local) for local, v in role.items()} if isinstance(role, dict) else
                  {Literal(role, lang=language)})
        assert set(result.ontology.objects(inverse, RDFS.label)) == labels
        assert {Literal('SOURCE_END_DESCRIPTION', lang=language or 'en'),
                Literal('BRONBESCHRIJVING', lang=language or 'nl')} <= set(
            result.ontology.objects(inverse, RDFS.comment))
        for text in ('TARGET_DESCRIPTION', 'RELATION_DESCRIPTION'):
            assert (inverse, RDFS.comment, Literal(text, lang=language)) not in result.ontology


def test_unusable_inverse_domain_does_not_lose_property_or_change_source_backed_identity(run, source_json, tmp_path):
    """Rules: DK-INV-03, DK-INV-07, DK-INV-08, DK-INV-10, DK-IRI-04, DK-IRI-10, DK-DIAG-01.

    A1.2 resolves the exact qualifier while retaining this historical node.
    """
    document=source_json('shared/binary_relation');source_element(document,'sFocus')['name']=None
    source_element(document,'cB')['name']='___'
    for i,name in enumerate(('inverseOfWorksFor','inverseOfWorksFor_HTTPServer')):
        claim=copy.deepcopy(source_element(document,'cA'));claim.update(id='cClaim'+str(i),name=name);document['model']['contents'].append(claim)
    baseline=run(path=write_input(tmp_path,document,'without.json'),inverse_properties='none')
    result=run(path=write_input(tmp_path,document),inverse_properties='all')
    assert baseline.outcome==result.outcome=='completed'
    inverse=_resource(result,'sFocus','name');primary=_resource(result,'tFocus','name');_inverse(result.ontology,inverse,primary)
    assert inverse == BASE.inverseOfWorksFor_unnamedClass_cB
    assert diagnostic_signatures(result.diagnostics) == diagnostic_signatures(baseline.diagnostics)
    assert inverse not in {_resource(result,i,'name') for i in ('cA','cB','cClaim0','cClaim1','tFocus')}
    for identifier in ('cA','cB','tFocus','cClaim0','cClaim1'):
        assert _resource(result,identifier,'name')==_resource(baseline,identifier,'name')


@pytest.mark.parametrize('state,value', [
    ('absent', None), ('null', None), ('whitespace', ' \t '),
    ('punctuation', '___'), ('non_ascii', '東京'),
    ('localized', {'en': '___', 'nl': '東京'}),
], ids=['absent', 'null', 'whitespace', 'punctuation', 'non_ascii', 'localized'])
@pytest.mark.parametrize('mode', ['all', 'informed', 'named'])
def test_inverse_domain_fallback_uses_escaped_own_id_before_classifier_collision_suffixes(
        run, source_json, tmp_path, state, value, mode):
    """Rules: DK-INV-03, DK-INV-04, DK-INV-05, DK-INV-06, DK-INV-07, DK-INV-08, DK-INV-10, DK-IRI-04, DK-IRI-05, DK-IRI-07, DK-IRI-10, DK-DIAG-01.

    A1.2: the safe prefix means a leading source-ID digit needs no id_ prefix.
    Ordinary classifier collision suffixes must not enter the inverse qualifier.
    """
    document = source_json('shared/binary_relation')
    domain = source_element(document, 'cB')
    domain.update(id='9 domain._', name=copy.deepcopy(value))
    if state == 'absent': domain.pop('name')
    source_element(document, 'tFocus')['propertyType']['id'] = domain['id']
    source_element(document, 'sFocus')['description'] = 'DOMAIN_FALLBACK_SOURCE_DESCRIPTION'
    candidate = 'unnamedClass_9_x20domain_x2E_x5F'
    for index, name in enumerate(('workers', 'inverseOfWorksFor', candidate, candidate)):
        claim = copy.deepcopy(source_element(document, 'cA'))
        claim.update(id=f'cReserved{index}', name=name)
        document['model']['contents'].append(claim)
    assert not fixture_issues(document)
    baseline = run(path=write_input(tmp_path, document, 'without.json'), inverse_properties='none', language='fr')
    result = run(path=write_input(tmp_path, document), inverse_properties=mode, language='fr')
    assert baseline.outcome == result.outcome == 'completed'
    _assert_source_backed_identity_preserved(baseline, result)
    classifier = _resource(result, domain['id'], 'name')
    assert {_resource(result, identifier, 'name') for identifier in (domain['id'], 'cReserved2', 'cReserved3')} == {
        BASE[candidate + suffix] for suffix in ('_1', '_2', '_3')}
    assert classifier != BASE[candidate]
    primary = _resource(result, 'tFocus', 'name')
    inverse = _resource(result, 'sFocus', 'name')
    assert inverse == BASE['inverseOfWorksFor_' + candidate]
    _inverse(result.ontology, inverse, primary)
    assert set(result.ontology.objects(inverse, RDFS.label)) == {Literal('workers', lang='fr')}
    assert (inverse, RDFS.comment, Literal('DOMAIN_FALLBACK_SOURCE_DESCRIPTION', lang='fr')) in result.ontology
    assert any(d.kind == 'missing_name' and d.severity == 'WARNING' and domain['id'] in d.source_ids
               and str(classifier) in d.generated_iris for d in result.diagnostics)
    assert diagnostic_signatures(result.diagnostics) == diagnostic_signatures(baseline.diagnostics)


NUMERIC_Q = 'inverseOfWorksFor_Source_Organization'
# Fixed expected names are derived from the registered rules, not a second allocator.
NUMERIC_CASES = {
    'lone': (1, (NUMERIC_Q,), (NUMERIC_Q + '_1',)),
    'lone_blocked': (1, (NUMERIC_Q, NUMERIC_Q + '_1'), (NUMERIC_Q + '_2',)),
    'lone_gap': (1, (NUMERIC_Q, NUMERIC_Q + '_1', NUMERIC_Q + '_3'), (NUMERIC_Q + '_2',)),
    'shared_free': (2, (), (NUMERIC_Q + '_1', NUMERIC_Q + '_2')),
    'shared_blocked': (2, (NUMERIC_Q + '_1',), (NUMERIC_Q + '_2', NUMERIC_Q + '_3')),
    'shared_occupied_prefix': (2, (NUMERIC_Q + '_1', NUMERIC_Q + '_2'), (NUMERIC_Q + '_3', NUMERIC_Q + '_4')),
    'shared_gap': (2, (NUMERIC_Q + '_2',), (NUMERIC_Q + '_1', NUMERIC_Q + '_3')),
    'source_final_slots': (2, (NUMERIC_Q, NUMERIC_Q), (NUMERIC_Q + '_3', NUMERIC_Q + '_4')),
    'source_candidate_slot': (2, (NUMERIC_Q + '_1', NUMERIC_Q + '_1'), (NUMERIC_Q + '_2', NUMERIC_Q + '_3')),
    'original_numeric_text': (2, (NUMERIC_Q + '_1_1',), (NUMERIC_Q + '_1_2', NUMERIC_Q + '_1_3')),
    'retained_inverse_slot': (2, (), (NUMERIC_Q + '_2', NUMERIC_Q + '_3')),
}


def _numeric_collision_input(source_json, case, member_ids=('a_source', 'z_source')):
    """Bounded runtime adaptations of the canonical collision input; no conversion."""
    document = source_json('inverses/secondary_collisions')
    members, claims, _ = NUMERIC_CASES[case]
    if members == 1:
        document['model']['contents'].remove(source_element(document, 'rUpper'))
    for index, relation_id in enumerate(('rLower', 'rUpper')[:members]):
        source_element(document, relation_id)['properties'][0].update(
            id=member_ids[index], description='SOURCE_' + member_ids[index])
    if case == 'original_numeric_text':
        source_element(document, 'cOrganization')['name'] = 'Organization_1'
    for index, name in enumerate(('staff',) + claims):
        claim = copy.deepcopy(source_element(document, 'cSource'))
        claim.update(id=f'cReserved{index}', name=name)
        document['model']['contents'].append(claim)
    if case == 'retained_inverse_slot':
        retained = copy.deepcopy(source_element(document, 'rLower'))
        retained.update(id='rRetained', name='observes')
        retained['properties'][0].update(id='sRetained', name=NUMERIC_Q + '_1')
        retained['properties'][1]['id'] = 'tRetained'
        document['model']['contents'].append(retained)
    assert not fixture_issues(document)
    return document


@pytest.mark.parametrize('case', NUMERIC_CASES)
@pytest.mark.parametrize('mode', ['all', 'informed', 'named'])
def test_inverse_numeric_allocation_skips_reserved_names_from_original_qualified_candidate(
        run, source_json, tmp_path, case, mode):
    """Rules: DK-INV-03, DK-INV-04, DK-INV-05, DK-INV-06, DK-INV-07, DK-INV-08, DK-INV-10, DK-IRI-07, DK-IRI-09, DK-DIAG-01, DK-CONF-01.

    A1.3: fixed outcomes cover lone/shared candidates, holes, candidate claims,
    final source names, retained inverses and original numeric source text.
    F1: ordinary source collision numbering may depend on declaration order;
    compare source identities and diagnostics for the exact same request.
    """
    document = _numeric_collision_input(source_json, case)
    members, _, expected_names = NUMERIC_CASES[case]
    for reverse in (False, True):
        request = copy.deepcopy(document)
        if reverse: request['model']['contents'].reverse()
        source = write_input(tmp_path, request)
        baseline = run(path=source, inverse_properties='none', language='fr')
        assert baseline.outcome == 'completed'
        if case in {'source_final_slots', 'source_candidate_slot'}:
            expected_source = ({NUMERIC_Q + '_1', NUMERIC_Q + '_2'} if case == 'source_final_slots' else
                               {NUMERIC_Q + '_1_1', NUMERIC_Q + '_1_2'})
            assert {_resource(baseline, identifier, 'name') for identifier in ('cReserved1', 'cReserved2')} == {
                BASE[name] for name in expected_source}
        result = run(path=source, inverse_properties=mode, language='fr')
        assert result.outcome == 'completed'
        _assert_source_backed_identity_preserved(baseline, result)
        actual = set()
        for index, source_id in enumerate(('a_source', 'z_source')[:members]):
            inverse = _resource(result, source_id, 'name')
            assert inverse == BASE[expected_names[index]]
            _inverse(result.ontology, inverse, _resource(result, ('tLower', 'tUpper')[index], 'name'))
            assert set(result.ontology.objects(inverse, RDFS.label)) == {Literal('staff', lang='fr')}
            assert (inverse, RDFS.comment, Literal('SOURCE_' + source_id, lang='fr')) in result.ontology
            actual.add(inverse)
        if case == 'retained_inverse_slot':
            inverse = _resource(result, 'sRetained', 'name')
            assert inverse == BASE[NUMERIC_Q + '_1']
            _inverse(result.ontology, inverse, _resource(result, 'tRetained', 'name'))
            assert set(result.ontology.objects(inverse, RDFS.label)) == {Literal(NUMERIC_Q + '_1', lang='fr')}
            actual.add(inverse)
        assert set(result.ontology.subjects(OWL.inverseOf, None)) == actual
        assert len(actual) == members + (case == 'retained_inverse_slot')
        assert diagnostic_signatures(result.diagnostics) == diagnostic_signatures(baseline.diagnostics)


@pytest.mark.parametrize('member_ids', [(' a', 'A'), ('Z', 'a'), ('z', 'é'), ('e\u0301', 'é')],
                         ids=['no_trimming', 'no_casefolding', 'no_id_escaping', 'no_unicode_normalization'])
def test_inverse_numeric_member_order_uses_original_end_id_code_points(run, source_json, tmp_path, member_ids):
    """Rules: DK-INV-07, DK-INV-08, DK-INV-10, DK-IRI-07, DK-IRI-09, DK-DIAG-01, DK-CONF-01. A1.3.

    The table lists raw Unicode ordering explicitly, including canonical variants.
    IDs determine membership order without becoming part of the resulting name.
    """
    document = _numeric_collision_input(source_json, 'shared_free', member_ids)
    baseline = run(path=write_input(tmp_path, document, 'without.json'), inverse_properties='none')
    assert baseline.outcome == 'completed'
    for reverse in (False, True):
        request = copy.deepcopy(document)
        if reverse: request['model']['contents'].reverse()
        result = run(path=write_input(tmp_path, request), inverse_properties='all')
        assert result.outcome == 'completed'
        _assert_source_backed_identity_preserved(baseline, result)
        for identifier, target_id, expected in zip(member_ids, ('tLower', 'tUpper'), (NUMERIC_Q + '_1', NUMERIC_Q + '_2')):
            inverse = _resource(result, identifier, 'name')
            assert inverse == BASE[expected]
            _inverse(result.ontology, inverse, _resource(result, target_id, 'name'))
        assert diagnostic_signatures(result.diagnostics) == diagnostic_signatures(baseline.diagnostics)


@pytest.mark.parametrize('mode', ['all', 'informed', 'named'])
def test_inverse_numeric_groups_share_reservations_and_preserve_numeric_candidate_text(
        run, source_json, tmp_path, mode):
    """Rules: DK-INV-03, DK-INV-04, DK-INV-05, DK-INV-06, DK-INV-07, DK-INV-08, DK-INV-10, DK-IRI-07, DK-IRI-09, DK-DIAG-01, DK-CONF-01. A1.3.

    Two qualified groups have overlapping numeric text; a fifth inverse retains
    a reserved slot. Group/source serialization cannot change fixed allocation.
    """
    document = source_json('shared/binary_relation')
    source_element(document, 'cA')['name'] = 'Source'
    source_element(document, 'cB')['name'] = 'A'
    second_range = copy.deepcopy(source_element(document, 'cB'))
    second_range.update(id='cSecondRange', name='P_A_1')
    document['model']['contents'].append(second_range)
    template = copy.deepcopy(source_element(document, 'rFocus'))
    document['model']['contents'].remove(source_element(document, 'rFocus'))
    q = 'inverseOfWorksFor_P_A'
    declarations = [
        ('rQ0', 'worksFor_P', 'Z_q', 'tQ0', 'cB', 'staff', q + '_1'),
        ('rQ1', 'WorksFor_P', 'a_q', 'tQ1', 'cB', 'staff', q + '_3'),
        ('rR0', 'worksFor', ' z_r', 'tR0', 'cSecondRange', 'staff', q + '_1_1'),
        ('rR1', 'WorksFor', 'A_r', 'tR1', 'cSecondRange', 'staff', q + '_1_2'),
        ('rRetained', 'keeps', 'sRetained', 'tRetained', 'cB', q + '_2', q + '_2'),
    ]
    for relation_id, name, source_id, target_id, range_id, role, _ in declarations:
        relation = copy.deepcopy(template)
        relation.update(id=relation_id, name=name)
        relation['properties'][0].update(id=source_id, name=role, description='SOURCE_' + source_id)
        relation['properties'][1].update(id=target_id, propertyType={'id': range_id, 'type': 'Class'})
        document['model']['contents'].append(relation)
    for index, name in enumerate(('staff', 'inverseOfWorksFor_P', 'inverseOfWorksFor')):
        claim = copy.deepcopy(source_element(document, 'cA'))
        claim.update(id=f'cReserved{index}', name=name)
        document['model']['contents'].append(claim)
    assert not fixture_issues(document)
    baseline = run(path=write_input(tmp_path, document, 'without.json'), inverse_properties='none', language='fr')
    assert baseline.outcome == 'completed'
    for reverse in (False, True):
        request = copy.deepcopy(document)
        if reverse: request['model']['contents'].reverse()
        result = run(path=write_input(tmp_path, request), inverse_properties=mode, language='fr')
        assert result.outcome == 'completed'
        _assert_source_backed_identity_preserved(baseline, result)
        actual = set()
        for _, _, source_id, target_id, _, role, expected in declarations:
            inverse = _resource(result, source_id, 'name')
            assert inverse == BASE[expected]
            _inverse(result.ontology, inverse, _resource(result, target_id, 'name'))
            assert set(result.ontology.objects(inverse, RDFS.label)) == {Literal(role, lang='fr')}
            assert (inverse, RDFS.comment, Literal('SOURCE_' + source_id, lang='fr')) in result.ontology
            actual.add(inverse)
        assert len(actual) == 5 and set(result.ontology.subjects(OWL.inverseOf, None)) == actual
        assert diagnostic_signatures(result.diagnostics) == diagnostic_signatures(baseline.diagnostics)


@pytest.mark.parametrize('role',['workers','changed role',None],ids=['initial_role','changed_role','absent_role'])
def test_source_backed_iris_remain_stable_across_every_inverse_mode(run, source_json, tmp_path, role):
    """Rules: DK-INV-07, DK-INV-10, DK-IRI-09, DK-CONF-01."""
    document=source_json('shared/binary_relation')
    baseline=run(path=write_input(tmp_path,document,'initial_role.json'),inverse_properties='all')
    source_element(document,'sFocus')['name']=role
    results=[baseline]+[run(path=write_input(tmp_path,document,mode+'.json'),inverse_properties=mode) for mode in MODES]
    assert all(r.outcome=='completed' for r in results)
    for identifier in ('cA','cB','tFocus'):
        assert len({_resource(result,identifier,'name') for result in results})==1


@pytest.mark.parametrize('pattern',['instantiation','datatype_attribute','custom_attribute','generalization_set','unrepresented_connector','material_relator','material_mode','comparative_quality'])
def test_ineligible_constructs_do_not_receive_named_or_anonymous_inverse_properties(run, source_json, tmp_path, pattern):
    """Rules: DK-INV-02, DK-INV-04, DK-INS-01, DK-REL-08, DK-REL-17, DK-REL-18, DK-GEN-01, DK-DIAG-06.

    Dependency-only eligibility assertions; full discarded-information,
    derivation and non-representation diagnostics remain Wave 5.
    """
    document=source_json('shared/omitted_connector' if pattern=='unrepresented_connector' else 'shared/binary_relation')
    forbidden=set()
    if pattern=='instantiation':
        source_element(document,'rFocus')['stereotype']='instantiation';forbidden={BASE.sFocus,BASE.tFocus}
    elif pattern in {'datatype_attribute','custom_attribute'}:
        attribute=copy.deepcopy(source_element(document,'sFocus'));attribute.update(id='pAttribute',name='value',propertyType=None,aggregationKind=None)
        source_element(document,'cA')['properties']=[attribute];forbidden={BASE.pAttribute}
        if pattern=='custom_attribute':
            custom=copy.deepcopy(source_element(document,'cB'));custom.update(id='cCustom',name='CustomValue',stereotype='datatype')
            document['model']['contents'].append(custom);attribute['propertyType']={'id':'cCustom','type':'Class'}
    elif pattern=='generalization_set':
        gen={'id':'gClass','name':None,'description':None,'type':'Generalization','propertyAssignments':None,'specific':{'id':'cA','type':'Class'},'general':{'id':'cB','type':'Class'}}
        gs={'id':'gsClass','name':None,'description':None,'type':'GeneralizationSet','propertyAssignments':None,'isDisjoint':False,'isComplete':False,'categorizer':None,'generalizations':[{'id':'gClass','type':'Generalization'}]}
        document['model']['contents'].extend([gen,gs]);forbidden={BASE.gClass,BASE.gsClass}
    elif pattern=='unrepresented_connector':forbidden={BASE.sConnector,BASE.tConnector,BASE.rConnector}
    else:
        ground=copy.deepcopy(source_element(document,'cA'));ground.update(id='cGround',name='Ground',stereotype={'material_relator':'relator','material_mode':'mode','comparative_quality':'quality'}[pattern])
        if pattern=='comparative_quality':source_element(document,'rFocus')['stereotype']='comparative'
        connector=copy.deepcopy(source_element(document,'rFocus'));connector.update(id='rDerivation',name=None,stereotype='derivation')
        connector['properties'][0].update(id='sDerivation',propertyType={'id':'rFocus','type':'Relation'})
        connector['properties'][1].update(id='tDerivation',propertyType={'id':'cGround','type':'Class'})
        document['model']['contents'].extend([ground,connector]);forbidden={BASE.rDerivation,BASE.sDerivation,BASE.tDerivation}
    assert not fixture_issues(document)
    options={'stereotype_policy':'require-known'} if pattern=='material_mode' else {}
    result=run(path=write_input(tmp_path,document),iri_strategy='id',inverse_properties='all',material_property_chains='none',**options)
    assert result.outcome=='completed'
    expected_edges=({(BASE.s0,BASE.t0),(BASE.s1,BASE.t1)} if pattern=='unrepresented_connector' else
                    set() if pattern=='instantiation' else {(BASE.sFocus,BASE.tFocus)})
    assert set(result.ontology.subject_objects(OWL.inverseOf))==expected_edges
    for s,o in result.ontology.subject_objects(OWL.inverseOf):assert s not in forbidden and o not in forbidden
    if pattern in {'datatype_attribute','custom_attribute'}:
        assert (BASE.pAttribute,RDF.type,OWL.DatatypeProperty if pattern=='datatype_attribute' else OWL.ObjectProperty) in result.ontology
    else:
        for term in forbidden:assert not any(term in triple for triple in result.ontology)
    if pattern not in {'instantiation','unrepresented_connector'}:_inverse(result.ontology,BASE.sFocus,BASE.tFocus)
    if pattern=='unrepresented_connector':
        _inverse(result.ontology,BASE.s0,BASE.t0);_inverse(result.ontology,BASE.s1,BASE.t1)


@pytest.mark.parametrize('input_policy',['strict','tolerant','best-effort'])
@pytest.mark.parametrize('failure',['null_endpoint','unresolved_endpoint','missing_end_id'])
def test_malformed_relation_is_reported_as_structural_instead_of_silent_inverse_ineligibility(run, source_json, tmp_path, input_policy, failure):
    """Rules: DK-INV-02, DK-INV-10, DK-DIAG-03, DK-DIAG-05."""
    document=source_json('shared/binary_relation')
    if failure=='null_endpoint':source_element(document,'tFocus')['propertyType']=None
    elif failure=='unresolved_endpoint':source_element(document,'tFocus')['propertyType']['id']='cMissing'
    else:source_element(document,'sFocus').pop('id')
    result=run(path=write_input(tmp_path,document),iri_strategy='id',inverse_properties='all',input_policy=input_policy)
    assert any(d.severity=='ERROR' for d in result.diagnostics)
    if input_policy!='best-effort':assert result.outcome=='aborted' and result.ontology is None
    else:
        assert result.outcome=='completed-with-errors'
        assert not list(result.ontology.triples((None,OWL.inverseOf,None)))
        assert (BASE.tFocus,RDF.type,OWL.ObjectProperty) not in result.ontology
        assert (BASE.cB,RDF.type,OWL.Class) in result.ontology


def test_rdf_helper_inverse_requires_explicit_reversed_domains_and_one_directed_axiom():
    """Harness only: inspect explicit RDF; entailment cannot fill declarations."""
    graph=Graph()
    for p,a,b in [(BASE.tFocus,BASE.cA,BASE.cB),(BASE.sFocus,BASE.cB,BASE.cA)]:
        graph.add((p,RDF.type,OWL.ObjectProperty));graph.add((p,RDFS.domain,a));graph.add((p,RDFS.range,b))
    graph.add((BASE.sFocus,OWL.inverseOf,BASE.tFocus));_inverse(graph,BASE.sFocus,BASE.tFocus)
    graph.add((BASE.tFocus,OWL.inverseOf,BASE.sFocus))
    with pytest.raises(AssertionError):_inverse(graph,BASE.sFocus,BASE.tFocus)
    graph.remove((BASE.tFocus,OWL.inverseOf,BASE.sFocus))
    graph.remove((BASE.sFocus,RDFS.domain,BASE.cB))
    with pytest.raises(AssertionError):_inverse(graph,BASE.sFocus,BASE.tFocus)
    graph.remove((BASE.tFocus,RDFS.range,BASE.cB))
    with pytest.raises(AssertionError):_inverse(graph,BASE.sFocus,BASE.tFocus)
