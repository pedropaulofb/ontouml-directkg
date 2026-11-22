"""Ordinary relation naming, labels, cardinalities and explicit hierarchies."""

import copy
import json
import socket
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
import pytest
from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, XSD

from tests.support.data import fixture_issues, source_element, write_input
from tests.support.dkgm import DKGM, DKGM_CHAINS, DKGM_STEREOTYPES, assert_dkgm_vocabulary
from tests.support.invocation import (DKGM_CHAIN_WARNING_FACTS, _observed_diagnostics, diagnostic_signatures,
                                      inapplicable_relation_categorizer_diagnostic,
                                      rd02_relation_diagnostic, relation_end_comment_meanings,
                                      relation_properties_container_diagnostic)
from tests.support.rdf import (assert_contains, assert_graph_equal, assert_selected_equal, cardinality_facts, load_graph,
                               necessary_restrictions, one_subject, property_chains, property_expression, rooted_graph)

BASE = Namespace('https://example.test/model#')
ONTOLOGY = URIRef('https://example.test/model')
POLICIES = ['strict', 'tolerant', 'best-effort']
STABLE_DIAGNOSTIC_CODES = frozenset({
    'PLACEHOLDER_BASE', 'UNPROCESSABLE_DOCUMENT', 'DUPLICATE_SOURCE_ID', 'UNKNOWN_INFORMATION',
    'REQUIRED_PROVENANCE', 'INTERNAL_TRANSFORMATION_FAILURE', 'ONTOLOGY_DELIVERY', 'SIDECAR_DELIVERY',
})
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


# A2 resolves the former bounded directions. A whole marker belongs to an
# association-end occurrence; class names below are only lexical source text.
SEMANTIC_ROWS = [
 ('bringsAbout', ('event','Event'), ('situation','Situation'), 'bringsAbout', 'broughtAboutBy', None),
 ('characterization', ('kind','Bearer'), ('mode','Feature'), 'isCharacterizedBy', 'characterizes', None),
 ('componentOf', ('kind','Whole'), ('kind','Component'), 'hasComponent', 'componentOf', 'source'),
 ('creation', ('event','Event'), ('kind','Endurant'), 'creates', 'wasCreatedIn', None),
 ('externalDependence', ('mode','Mode'), ('kind','Endurant'), 'externallyDependsOn', 'isExternalDependencyOf', None),
 ('historicalDependence', ('historicalRole','Dependent'), ('kind','Antecedent'), 'dependent_antecedent', 'antecedent_dependent', None),
 ('manifestation', ('mode','Aspect'), ('event','Event'), 'manifestedIn', 'manifests', None),
 ('mediation', ('relator','Relator'), ('kind','Endurant'), 'mediates', 'isMediatedBy', None),
 ('memberOf', ('kind','Member'), ('collective','Collective'), 'memberOf', 'hasMember', None),
 ('participation', ('kind','Participant'), ('event','Event'), 'participatesIn', 'hasParticipant', None),
 ('participational', ('event','PartEvent'), ('event','WholeEvent'), 'participationalPartOf', 'hasParticipationalPart', 'target'),
 ('subCollectionOf', ('collective','Subcollection'), ('collective','Collection'), 'subCollectionOf', 'hasSubCollection', 'target'),
 ('subQuantityOf', ('quantity','Subquantity'), ('quantity','Quantity'), 'subQuantityOf', 'hasSubQuantity', 'target'),
 ('termination', ('kind','Endurant'), ('event','Event'), 'wasTerminatedIn', 'terminates', None),
 ('triggers', ('situation','Situation'), ('event','Event'), 'triggers', 'triggeredBy', None),
]
SEMANTIC_CASES = [pytest.param(stereo, a if not reverse else b, b if not reverse else a,
                    backward if reverse else forward,
                    ('target' if whole == 'source' else 'source') if reverse and whole else whole,
                    id=stereo+('_reverse' if reverse else '_forward'))
                  for stereo,a,b,forward,backward,whole in SEMANTIC_ROWS for reverse in (False,True)]


@pytest.mark.parametrize('stereotype,source,target,candidate,whole', SEMANTIC_CASES)
def test_stereotype_table_candidates_preserve_established_direction_when_resolvable(run, source_json, tmp_path, stereotype, source, target, candidate, whole):
    """Rules: DK-REL-01, DK-REL-02, DK-REL-03, DK-REL-04, DK-REL-06, DK-GEN-03, DK-PROP-02, DK-DIAG-01, DK-DIAG-06.

    A2 registration 4fdef7bbaf8b73bf1ed0ff47fc793494493083dc: exact
    structural selection, including historical endpoint fallback. Other rows
    retain their established exact expectations. Shared/binary_relation runtime
    variants; fixed RDF assertions, no stored expectation graph.
    RD-17 registration 8bfc90fc40d732212ea84e583986c7ae0b96c65b additionally
    requires each relation's applicable limitation warning, independently of
    these unchanged successful lexical candidates.
    Registration fb05478031e290b123e766ad5188e4cef9935357 extends that
    independent warning requirement to participational and manifestation.
    Registration 490f209e0d70533bac56674e2844a7463fe77a09 additionally covers
    the dependency trio and warning-only bringsAbout/triggers treatment.
    """
    document = source_json('shared/binary_relation')
    source_element(document,'cA').update(stereotype=source[0], name=source[1])
    source_element(document,'cB').update(stereotype=target[0], name=target[1])
    source_element(document,'rFocus').update(stereotype=stereotype, name=None)
    source_element(document,'tFocus')['name'] = None
    if whole:
        source_element(document, 'sFocus' if whole == 'source' else 'tFocus')['aggregationKind'] = 'SHARED'
    assert not fixture_issues(document)
    result = run(path=write_input(tmp_path,document),inverse_properties='none',stereotype_policy='require-known')
    assert result.outcome == 'completed'
    prop = _primary(result,strategy='name')
    _candidate(result.ontology,prop,{candidate},source[1])
    _direction(result.ontology,prop,BASE[source[1]],BASE[target[1]])
    assert not any(d.severity == 'ERROR' for d in result.diagnostics)
    if stereotype == 'historicalDependence':
        assert any(d.kind == 'relation_naming' and d.severity == 'WARNING' for d in result.diagnostics)
        _relation_limitation_warning(result)
    else:
        assert not any(d.kind in NAMING_KINDS for d in result.diagnostics)
    if stereotype in {'participation', 'creation', 'termination', 'participational', 'manifestation',
                      'mediation', 'characterization', 'externalDependence', 'bringsAbout', 'triggers'}:
        _relation_limitation_warning(result)


@pytest.mark.parametrize('stereotype,endpoint_stereotype', [
    pytest.param('memberOf', 'collective', id='memberOf-two-collectives'),
    pytest.param('characterization', 'mode', id='characterization-two-modes'),
])
def test_ambiguous_semantic_roles_keep_primary_with_lexical_fallback(
        run, source_json, tmp_path, stereotype, endpoint_stereotype):
    """Rules: DK-DIAG-05, DK-GEN-03, DK-IRI-03, DK-IRI-09, DK-PROP-02, DK-REL-01, DK-REL-02, DK-REL-03, DK-REL-04, DK-REL-06.

    A1/I1 audit regression for the correction at b038a8e208392753f4999f2d0d1b78f071740fed.
    Complete shared/binary_relation variants make both endpoints plausible for the
    same semantic role and reach the semantic naming step under strict policy.
    """
    document = source_json('shared/binary_relation')
    for identifier in ('cA', 'cB'):
        source_element(document, identifier)['stereotype'] = endpoint_stereotype
    source_element(document, 'rFocus').update(name=None, stereotype=stereotype)
    source_element(document, 'tFocus')['name'] = None
    assert not fixture_issues(document)

    result = run(path=write_input(tmp_path, document), input_policy='strict', iri_strategy='name',
                 inverse_properties='none', stereotype_policy='require-known',
                 no_stereotype_relation_naming=False)
    assert result.outcome == 'completed'
    graph = result.ontology
    prop = _primary(result, 'tFocus', 'name')
    _candidate(graph, prop, {'hTTPServer_xMLNode'}, 'HTTPServer')
    _direction(graph, prop, BASE.HTTPServer, BASE.XMLNode)
    assert set(graph.objects(prop, DCTERMS.identifier)) == {Literal('tFocus')}
    assert set(graph.subjects(RDFS.domain, BASE.HTTPServer)) == {prop}
    _source_target_naming_warning(result, 'rFocus')
    assert not any(d.severity == 'ERROR' for d in result.diagnostics)


# A2 uses the canonical complete VP-plugin fixture and explicit runtime variants.
# These helpers author inputs/check RDF; they do not implement a name selector.
A2_PART_WHOLE = [
    pytest.param('componentOf', 'kind', 'hasComponent', 'componentOf', id='component_of'),
    pytest.param('participational', 'event', 'hasParticipationalPart', 'participationalPartOf', id='participational'),
    pytest.param('subCollectionOf', 'collective', 'hasSubCollection', 'subCollectionOf', id='sub_collection'),
    pytest.param('subQuantityOf', 'quantity', 'hasSubQuantity', 'subQuantityOf', id='sub_quantity'),
]
A2_MARKERS = [
    pytest.param('NONE', 'NONE', None, id='none'),
    pytest.param('absent', 'absent', None, id='absent'),
    pytest.param(None, None, None, id='null'),
    pytest.param('SHARED', 'NONE', 'source', id='source_shared'),
    pytest.param('COMPOSITE', 'NONE', 'source', id='source_composite'),
    pytest.param('NONE', 'SHARED', 'target', id='target_shared'),
    pytest.param('NONE', 'COMPOSITE', 'target', id='target_composite'),
    pytest.param('SHARED', 'SHARED', None, id='both_shared'),
    pytest.param('COMPOSITE', 'COMPOSITE', None, id='both_composite'),
    pytest.param('SHARED', 'COMPOSITE', None, id='shared_composite'),
    pytest.param('COMPOSITE', 'SHARED', None, id='composite_shared'),
]
# Complete accepted non-mode endurant set, not derived from production enums.
A2_NON_MODE_ENDURANTS = ['kind', 'collective', 'quantity', 'relator', 'quality',
    'subkind', 'role', 'phase', 'historicalRole', 'category', 'mixin', 'roleMixin',
    'phaseMixin', 'historicalRoleMixin']


def _a2_document(source_json, stereotype):
    document = source_json('shared/binary_relation')
    document['languages'] = ['nl']
    source_element(document, 'rFocus').update(name=None, stereotype=stereotype, description='A2 relation description.')
    source_element(document, 'sFocus').update(cardinality='1', description='A2 source description.')
    source_element(document, 'tFocus').update(name=None, cardinality='2..3', description='A2 target description.')
    return document


def _assert_a2_id_mapping(result, document):
    """Fixed source direction/counts/inverses and independent ordinary mappings."""
    assert result.outcome == 'completed'
    assert not any(d.severity == 'ERROR' for d in result.diagnostics)
    relation = source_element(document, 'rFocus')
    source, target = (BASE[end['propertyType']['id']] for end in relation['properties'])
    graph = result.ontology
    _direction(graph, BASE.tFocus, source, target)
    _direction(graph, BASE.sFocus, target, source)
    assert (BASE.sFocus, OWL.inverseOf, BASE.tFocus) in graph
    assert (BASE.tFocus, OWL.inverseOf, BASE.sFocus) not in graph
    _counts(graph, source, BASE.tFocus, {('min', 2), ('max', 3)})
    _counts(graph, target, BASE.sFocus, {('exact', 1)})
    assert not list(graph.objects(BASE.tFocus, DCTERMS.identifier))
    assert not list(graph.objects(BASE.sFocus, DCTERMS.identifier))
    assert (BASE.tFocus, RDFS.comment, Literal('A2 relation description.', lang='fr')) in graph
    assert (BASE.tFocus, RDFS.comment, Literal('A2 target description.', lang='fr')) in graph
    assert (BASE.sFocus, RDFS.comment, Literal('A2 source description.', lang='fr')) in graph
    assert not list(graph.triples((None, OWL.propertyChainAxiom, None)))
    stereotype = relation['stereotype']
    bridge = ({URIRef('https://w3id.org/directkg/vocab/dkgm#' + stereotype)}
              if stereotype in {'componentOf', 'subCollectionOf', 'subQuantityOf'} else set())
    assert set(graph.objects(BASE.tFocus, RDFS.subPropertyOf)) == bridge
    assert not list(graph.objects(BASE.sFocus, RDFS.subPropertyOf))
    if stereotype in {'componentOf', 'subCollectionOf', 'subQuantityOf', 'participational'}:
        assert (BASE.tFocus, RDF.type, OWL.AsymmetricProperty) in graph
        assert (BASE.sFocus, RDF.type, OWL.AsymmetricProperty) not in graph
    if stereotype == 'externalDependence':
        assert (BASE.tFocus, RDF.type, OWL.IrreflexiveProperty) in graph
    assert (None, OWL.imports, URIRef('https://w3id.org/directkg/vocab/dkgm')) in graph


@pytest.mark.parametrize('stereotype,class_stereotype,whole_forward,part_forward', A2_PART_WHOLE)
@pytest.mark.parametrize('source_marker,target_marker,whole', A2_MARKERS)
def test_unique_whole_marker_selects_lexical_name_without_changing_primary_mapping(
        run, invoke, source_json, tmp_path, stereotype, class_stereotype,
        whole_forward, part_forward, source_marker, target_marker, whole):
    """Rules: DK-REL-01, DK-REL-02, DK-REL-03, DK-REL-04, DK-REL-06, DK-REL-09, DK-REL-10, DK-REL-11, DK-REL-19, DK-LBL-01, DK-LBL-02, DK-PROP-04, DK-DIAG-01, DK-INV-01, DK-INV-04, DK-IRI-02, DK-GEN-04.

    A2 registration 4fdef7bbaf8b73bf1ed0ff47fc793494493083dc.
    Shared/binary_relation runtime variants; both represented directions per
    node. No stored expectation: fixed lexical and RDF assertions below.
    RD-17 fb05478031e290b123e766ad5188e4cef9935357 additionally requires
    the participational limitation warning with zero, one or two whole markers.
    """
    observations = []
    for reverse in (False, True):
        document = _a2_document(source_json, stereotype)
        for identifier in ('cA', 'cB'): source_element(document, identifier)['stereotype'] = class_stereotype
        relation = source_element(document, 'rFocus')
        for end, marker in zip(relation['properties'], (source_marker, target_marker)):
            if marker == 'absent': end.pop('aggregationKind')
            else: end['aggregationKind'] = marker
        if reverse:
            left, right = relation['properties']
            left['propertyType'], right['propertyType'] = right['propertyType'], left['propertyType']
        assert not fixture_issues(document)
        path = write_input(tmp_path, document)
        options = dict(iri_strategy='id', inverse_properties='all', relation_labels='generated', language='fr')
        baseline = run(path=path, no_stereotype_relation_naming=True, **options)
        result = run(path=path, **options)
        _assert_a2_id_mapping(result, document)
        expected = (whole_forward if whole == 'source' else part_forward if whole == 'target' else
                    'xMLNode_hTTPServer' if reverse else 'hTTPServer_xMLNode')
        assert set(result.ontology.objects(BASE.tFocus, RDFS.label)) == {Literal(expected)}
        _ordinary_relation_mapping_equal(baseline, result)
        assert _other_relation_diagnostics(baseline) == _other_relation_diagnostics(result)
        comments = invoke.read_relation_aggregation_comments(result, path)
        assert all((c.subject, RDFS.comment, c.literal) in result.ontology for c in comments)
        assert {(c.subject, c.context, c.value) for c in comments} == {
            (BASE.tFocus, context, marker) for context, marker in
            (('source_end', source_marker), ('target_end', target_marker))
            if marker in {'SHARED', 'COMPOSITE'}}
        observations.append(result)
    if stereotype == 'participational':
        for result in observations:
            _relation_limitation_warning(result)


@pytest.mark.parametrize('other', A2_NON_MODE_ENDURANTS, ids=A2_NON_MODE_ENDURANTS)
@pytest.mark.parametrize('mode_side', ['source', 'target'])
def test_external_dependence_selects_direction_for_every_supported_non_mode_endurant(
        run, source_json, tmp_path, other, mode_side):
    """Rules: DK-REL-01, DK-REL-02, DK-REL-04, DK-REL-09, DK-REL-10, DK-REL-11, DK-LBL-01, DK-LBL-02, DK-DIAG-01, DK-INV-01, DK-INV-04, DK-IRI-02.

    A2 registration 4fdef7bbaf8b73bf1ed0ff47fc793494493083dc.
    Shared/binary_relation; complete explicit stereotype set and fixed RDF.
    """
    document = _a2_document(source_json, 'externalDependence')
    source_element(document, 'cA')['stereotype'] = 'mode' if mode_side == 'source' else other
    source_element(document, 'cB')['stereotype'] = other if mode_side == 'source' else 'mode'
    assert not fixture_issues(document)
    result = run(path=write_input(tmp_path, document), iri_strategy='id', inverse_properties='all',
                 relation_labels='generated', language='fr', stereotype_policy='require-known')
    _assert_a2_id_mapping(result, document)
    candidate = 'externallyDependsOn' if mode_side == 'source' else 'isExternalDependencyOf'
    assert set(result.ontology.objects(BASE.tFocus, RDFS.label)) == {Literal(candidate)}
    assert not any(d.kind in NAMING_KINDS - {'missing_name'} for d in result.diagnostics)


@pytest.mark.parametrize('left,right', [
    pytest.param('mode', 'mode', id='both_mode'), pytest.param('kind', 'quality', id='neither_mode'),
    pytest.param('mode', 'event', id='event_not_endurant'), pytest.param('situation', 'mode', id='situation_not_endurant'),
    pytest.param('mode', 'type', id='type_not_in_approved_set'),
    pytest.param('mode', None, id='missing_other'), pytest.param(None, 'mode', id='missing_source'),
    pytest.param('extrinsicMode', 'kind', id='custom_extrinsic_is_not_mode'),
    pytest.param('kind', 'intrinsicMode', id='custom_intrinsic_is_not_mode'),
    pytest.param('mode', 'extrinsicMode', id='custom_other_not_supported'),
    pytest.param('intrinsicMode', 'mode', id='custom_source_not_supported'),
])
def test_external_dependence_ambiguous_or_unsupported_roles_use_endpoint_fallback(
        run, source_json, tmp_path, left, right):
    """Rules: DK-REL-01, DK-REL-02, DK-REL-03, DK-REL-04, DK-REL-06, DK-REL-09, DK-REL-10, DK-REL-11, DK-LBL-01, DK-LBL-02, DK-DIAG-01, DK-DIAG-06, DK-INV-01, DK-INV-04, DK-IRI-02.

    A2 registration 4fdef7bbaf8b73bf1ed0ff47fc793494493083dc.
    Shared/binary_relation; alias-like strings are deliberate custom negatives,
    not new supported stereotypes. Fixed endpoint lexical/RDF assertions.
    """
    document = _a2_document(source_json, 'externalDependence')
    source_element(document, 'cA')['stereotype'] = left
    source_element(document, 'cB')['stereotype'] = right
    assert not fixture_issues(document)
    result = run(path=write_input(tmp_path, document), iri_strategy='id', inverse_properties='all',
                 relation_labels='generated', language='fr', stereotype_policy='allow-custom')
    _assert_a2_id_mapping(result, document)
    assert set(result.ontology.objects(BASE.tFocus, RDFS.label)) == {Literal('hTTPServer_xMLNode')}


@pytest.mark.parametrize('stereotype', ['componentOf', 'participational', 'subCollectionOf', 'subQuantityOf', 'externalDependence', 'historicalDependence'])
@pytest.mark.parametrize('hint', ['descriptive_custom', 'inherited_restricted'])
def test_semantic_role_selection_does_not_use_descriptive_inherited_or_custom_hints(
        run, source_json, tmp_path, stereotype, hint):
    """Rules: DK-REL-01, DK-REL-02, DK-REL-03, DK-REL-04, DK-REL-06, DK-LBL-01, DK-DIAG-01, DK-CLS-01, DK-CLS-03, DK-GEN-07.

    A2 registration 4fdef7bbaf8b73bf1ed0ff47fc793494493083dc.
    Shared/binary_relation; supported descriptions/assignments, restrictedTo
    and complete Class/Generalization variants. Fixed endpoint fallback.
    """
    document = _a2_document(source_json, stereotype)
    if hint == 'descriptive_custom':
        # Text can supply fallback components, never semantic-role evidence.
        names = (('Mode', 'Endurant') if stereotype == 'externalDependence' else
                 ('Dependent', 'Antecedent') if stereotype == 'historicalDependence' else ('Whole', 'Part'))
        candidate = ('mode_endurant' if stereotype == 'externalDependence' else
                     'dependent_antecedent' if stereotype == 'historicalDependence' else 'whole_part')
        for identifier, name in zip(('cA', 'cB'), names):
            source_element(document, identifier).update(name=name, description='Claimed whole / mode / dependent role.')
        source_element(document, 'rFocus')['propertyAssignments'] = {'semanticRole': 'whole', 'direction': 'reverse'}
        source_element(document, 'sFocus')['propertyAssignments'] = {'aggregationKind': 'COMPOSITE', 'stereotype': 'mode'}
    else:
        candidate = 'hTTPServer_xMLNode'
        source_element(document, 'cA')['restrictedTo'] = ['mode']
        parent = copy.deepcopy(source_element(document, 'cA'))
        parent.update(id='cHint', name='ClaimedRole', stereotype='mode', restrictedTo=None)
        document['model']['contents'].extend([parent, {'id': 'gHint', 'type': 'Generalization',
            'name': None, 'description': None, 'propertyAssignments': None,
            'specific': {'id': 'cA', 'type': 'Class'}, 'general': {'id': 'cHint', 'type': 'Class'}}])
    assert not fixture_issues(document)
    result = run(path=write_input(tmp_path, document), iri_strategy='id', inverse_properties='none',
                 relation_labels='generated', stereotype_policy='require-known')
    assert result.outcome == 'completed'
    _direction(result.ontology)
    assert set(result.ontology.objects(BASE.tFocus, RDFS.label)) == {Literal(candidate)}
    assert not any(d.severity == 'ERROR' for d in result.diagnostics)
    if hint == 'inherited_restricted': assert (BASE.cA, RDFS.subClassOf, BASE.cHint) in result.ontology
    if stereotype == 'historicalDependence': _relation_limitation_warning(result)


@pytest.mark.parametrize('reverse', [False, True], ids=['modeled_forward', 'modeled_reverse'])
@pytest.mark.parametrize('hints', [False, True], ids=['no_roles', 'historical_role_and_flags'])
def test_historical_semantic_step_uses_exact_endpoint_fallback_and_preserves_ordinary_mapping(
        run, invoke, source_json, tmp_path, reverse, hints):
    """Rules: DK-REL-01, DK-REL-02, DK-REL-03, DK-REL-04, DK-REL-06, DK-REL-09, DK-REL-10, DK-REL-11, DK-LBL-01, DK-LBL-02, DK-PROP-02, DK-PROP-04, DK-DIAG-01, DK-INV-01, DK-INV-04, DK-GEN-11.

    A2 registration 4fdef7bbaf8b73bf1ed0ff47fc793494493083dc.
    Shared/binary_relation; position, historicalRole, read-only, aggregation
    and multiplicities do not assign dependent/antecedent. Fixed RDF checks.
    """
    document = _a2_document(source_json, 'historicalDependence')
    if hints:
        source_element(document, 'cA')['stereotype'] = 'historicalRole'
        source_element(document, 'sFocus').update(isReadOnly=True, aggregationKind='SHARED')
        source_element(document, 'tFocus').update(isReadOnly=True, aggregationKind='COMPOSITE')
    if reverse:
        a, b = source_element(document, 'rFocus')['properties']
        a['propertyType'], b['propertyType'] = b['propertyType'], a['propertyType']
    assert not fixture_issues(document)
    path = write_input(tmp_path, document)
    options = dict(iri_strategy='name', inverse_properties='all', relation_labels='generated', language='fr')
    baseline = run(path=path, no_stereotype_relation_naming=True, **options)
    result = run(path=path, **options)
    assert baseline.outcome == result.outcome == 'completed'
    prop = _primary(result, strategy='name')
    candidate, source, target = (('xMLNode_hTTPServer', BASE.XMLNode, BASE.HTTPServer) if reverse else
                                 ('hTTPServer_xMLNode', BASE.HTTPServer, BASE.XMLNode))
    _candidate(result.ontology, prop, {candidate}, 'XMLNode' if reverse else 'HTTPServer')
    _direction(result.ontology, prop, source, target)
    assert set(result.ontology.objects(prop, RDFS.label)) == {Literal(candidate)}
    _counts(result.ontology, source, prop, {('min', 2), ('max', 3)})
    inverse = _primary(result, 'sFocus', 'name')
    _counts(result.ontology, target, inverse, {('exact', 1)})
    _ordinary_relation_mapping_equal(baseline, result)
    assert _other_relation_diagnostics(baseline) == _other_relation_diagnostics(result)
    assert invoke.read_historical_dependence_annotations(result, path) == ()
    assert any(d.kind == 'relation_naming' and d.severity == 'WARNING' for d in result.diagnostics)
    _relation_limitation_warning(result)


@pytest.mark.parametrize('stereotype', ['componentOf', 'externalDependence', 'historicalDependence'])
@pytest.mark.parametrize('branch', ['relation', 'target_role', 'selected', 'insufficient', 'disabled'])
@pytest.mark.parametrize('strategy', ['name', 'id'])
@pytest.mark.parametrize('label_mode', ['source-only', 'generated'])
def test_structural_naming_preserves_precedence_controls_and_label_modes(
        run, source_json, tmp_path, stereotype, branch, strategy, label_mode):
    """Rules: DK-REL-01, DK-REL-02, DK-REL-03, DK-REL-04, DK-REL-06, DK-REL-09, DK-REL-10, DK-REL-11, DK-LBL-01, DK-LBL-02, DK-PROP-02, DK-IRI-02, DK-IRI-06, DK-DIAG-01, DK-INV-01, DK-INV-04.

    A2 registration 4fdef7bbaf8b73bf1ed0ff47fc793494493083dc.
    Shared/binary_relation; representative aggregation, mode and historical
    selectors. Source labels versus exact generated lexical labels, both IRI
    strategies; fixed RDF expectations and no diagnostic from labels alone.
    """
    document = _a2_document(source_json, stereotype)
    if stereotype == 'componentOf': source_element(document, 'sFocus')['aggregationKind'] = 'SHARED'
    elif stereotype == 'externalDependence': source_element(document, 'cA')['stereotype'] = 'mode'
    else: source_element(document, 'cA')['stereotype'] = 'historicalRole'
    if branch == 'relation':
        source_element(document, 'rFocus')['name'] = ' Assigned, To '
        source_element(document, 'tFocus')['name'] = 'target role'
    elif branch == 'target_role': source_element(document, 'tFocus')['name'] = 'target role'
    elif branch == 'insufficient':
        source_element(document, 'sFocus')['aggregationKind'] = 'NONE'
        source_element(document, 'cA')['stereotype'] = 'category'
    assert not fixture_issues(document)
    path = write_input(tmp_path, document)
    options = dict(iri_strategy=strategy, inverse_properties='all', language='fr',
                   no_stereotype_relation_naming=branch == 'disabled')
    result = run(path=path, relation_labels=label_mode, **options)
    assert result.outcome == 'completed'
    prop = _primary(result, strategy=strategy)
    candidate = ('Assigned_To' if branch == 'relation' else 'target_role' if branch == 'target_role' else
        'hTTPServer_xMLNode' if branch in {'insufficient', 'disabled'} or stereotype == 'historicalDependence' else
        'hasComponent' if stereotype == 'componentOf' else 'externallyDependsOn')
    if strategy == 'name': _candidate(result.ontology, prop, {candidate}, 'HTTPServer')
    source, target = (BASE.cA, BASE.cB) if strategy == 'id' else (BASE.HTTPServer, BASE.XMLNode)
    _direction(result.ontology, prop, source, target)
    assert set(result.ontology.objects(prop, DCTERMS.identifier)) == ({Literal('tFocus')} if strategy == 'name' else set())
    expected = ({Literal(' Assigned, To ', lang='fr')} if branch == 'relation' else
                {Literal('target role', lang='fr')} if branch == 'target_role' else
                {Literal(candidate)} if label_mode == 'generated' else set())
    assert set(result.ontology.objects(prop, RDFS.label)) == expected
    inverse = _primary(result, 'sFocus', strategy)
    _direction(result.ontology, inverse, target, source)
    assert (inverse, OWL.inverseOf, prop) in result.ontology
    assert set(result.ontology.objects(inverse, RDFS.label)) == {Literal('workers', lang='fr')}
    _counts(result.ontology, source, prop, {('min', 2), ('max', 3)})
    _counts(result.ontology, target, inverse, {('exact', 1)})
    assert not any(d.severity == 'ERROR' for d in result.diagnostics)
    if strategy == 'name':
        warning = branch in {'target_role', 'insufficient', 'disabled'} or (stereotype == 'historicalDependence' and branch == 'selected')
        assert any(d.kind == 'relation_naming' and d.severity == 'WARNING' for d in result.diagnostics) == warning
        if not warning: assert not any(d.kind in NAMING_KINDS for d in result.diagnostics)
    if stereotype == 'historicalDependence': _relation_limitation_warning(result)
    if label_mode == 'generated':
        baseline = run(path=path, relation_labels='source-only', **options)
        _ordinary_relation_mapping_equal(baseline, result)
        assert _other_relation_diagnostics(baseline) == _other_relation_diagnostics(result)


@pytest.mark.parametrize('stereotype', ['componentOf', 'participational', 'subCollectionOf', 'subQuantityOf', 'externalDependence', 'historicalDependence'])
@pytest.mark.parametrize('input_policy', POLICIES)
def test_insufficient_structural_roles_remain_nonfatal_under_every_input_policy(
        run, invoke, source_json, tmp_path, stereotype, input_policy):
    """Rules: DK-REL-01, DK-REL-02, DK-REL-03, DK-REL-04, DK-REL-06, DK-LBL-01, DK-PROP-02, DK-DIAG-01, DK-DIAG-05.

    A2 registration 4fdef7bbaf8b73bf1ed0ff47fc793494493083dc.
    Shared/binary_relation; role uncertainty is not a structural error under
    strict, tolerant or best-effort. Fixed endpoint candidate and direction.
    RD-17 fb05478031e290b123e766ad5188e4cef9935357 also requires the
    participational residual warning despite unavailable whole-role evidence.
    Registration 490f209e0d70533bac56674e2844a7463fe77a09 adds the external
    dependence residual warning. Verify both meanings for the focal relation,
    including when one diagnostic reports both.
    """
    document = _a2_document(source_json, stereotype)
    assert not fixture_issues(document)
    path = write_input(tmp_path, document)
    result = run(path=path, input_policy=input_policy,
                 iri_strategy='name', inverse_properties='none', relation_labels='generated')
    assert result.outcome == 'completed'
    prop = _primary(result, strategy='name')
    _candidate(result.ontology, prop, {'hTTPServer_xMLNode'}, 'HTTPServer')
    _direction(result.ontology, prop, BASE.HTTPServer, BASE.XMLNode)
    assert set(result.ontology.objects(prop, RDFS.label)) == {Literal('hTTPServer_xMLNode')}
    if stereotype == 'externalDependence':
        _source_target_naming_warning(result, 'rFocus')
        _relation_limitation_warning(result)
        assert 'rFocus' in invoke.read_relation_limitation_source_ids(result, path)
    else:
        assert any(d.kind == 'relation_naming' and d.severity == 'WARNING' for d in result.diagnostics)
        assert not any(d.severity == 'ERROR' for d in result.diagnostics)
        if stereotype in {'historicalDependence', 'participational'}:
            _relation_limitation_warning(result)


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


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("inverse_mode", ["all", "none"])
@pytest.mark.parametrize("case", ["singleton_complete", "singleton_open", "multi_complete"])
def test_repeated_membership_preserves_relation_set_mappings(run, source_json, tmp_path, input_policy, inverse_mode, case):
    """Rules: DK-GEN-12, DK-REL-14, DK-REL-15, DK-REL-16, DK-REL-20, DK-INV-12, DK-DIAG-14, DK-DIAG-05.

    RD-02 membership identity, reviewed registration 2b427908a7e29d546486a616a22495ea0424f294.
    """
    document = source_json("relations/hierarchy")
    gs = source_element(document, "gsRelations")
    singleton = case != "multi_complete"
    complete = case != "singleton_open"
    gs.update(isComplete=complete, isDisjoint=True, generalizations=gs["generalizations"][:1 if singleton else 2])
    observations = []
    for repeated in (False, True):
        if repeated:
            gs["generalizations"].append(copy.deepcopy(gs["generalizations"][0]))
        assert not fixture_issues(document)
        result = run(path=write_input(tmp_path, document, f"relation_set_{repeated}.json"), iri_strategy="id",
                     input_policy=input_policy, inverse_properties=inverse_mode)
        observations.append(result)
        assert result.outcome == "completed"
        edges = [("Middle", "General"), ("Leaf", "Middle"), ("Sibling", "General")]
        if singleton and complete:
            edges.append(("General", "Middle"))
        named = {"General", "Middle", "Leaf", "Sibling"} if inverse_mode == "all" else set()
        _, _, expected = _hierarchy_expected(result, "id", named, edges)
        assert _edges(result.ontology) == expected
        for key, source, target in [("General", "cA", "cB"), ("Middle", "cB", "cC"),
                                    ("Leaf", "cC", "cA"), ("Sibling", "cD", "cA")]:
            _direction(result.ontology, BASE["t" + key], BASE[source], BASE[target])
        pairs = set() if singleton else {frozenset((BASE.tMiddle, BASE.tSibling))}
        if not singleton and inverse_mode == "all":
            pairs.add(frozenset((BASE.sMiddle, BASE.sSibling)))
        assert _pairs(result.ontology) == pairs
        for predicate in (OWL.equivalentProperty, OWL.unionOf, OWL.disjointUnionOf):
            assert not list(result.ontology.triples((None, predicate, None)))
        notices = [event for event in result.diagnostics if event.kind == "singleton_completeness"]
        if singleton and complete:
            assert any(event.severity == "INFO" and {"gsRelations", "rGeneral", "rMiddle"} <= set(event.identified_sources)
                       and {"extensional_equivalence", "distinct_identifiers"} <= event.facts for event in notices)
        else:
            assert not notices
        coverage = [event for event in result.diagnostics if event.kind == "relation_set_completeness"]
        if not singleton and complete:
            assert any(event.severity == "WARNING" and "gsRelations" in event.identified_sources
                       and "coverage_not_represented" in event.facts for event in coverage)
        else:
            assert not coverage
        assert not any(event.severity == "ERROR" for event in result.diagnostics)
    assert diagnostic_signatures(observations[0].diagnostics) == diagnostic_signatures(observations[1].diagnostics)


@pytest.mark.parametrize("input_policy", POLICIES)
def test_repeated_membership_keeps_distinct_relation_generalization_declarations(run, source_json, tmp_path, input_policy):
    """Rules: DK-GEN-12, DK-REL-14, DK-REL-20, DK-DIAG-14, DK-DIAG-05; §3.4.

    RD-02 at 2b427908a7e29d546486a616a22495ea0424f294. Distinct declaration
    IDs with equal endpoints must not acquire singleton completeness.
    """
    document = source_json("relations/hierarchy")
    first = source_element(document, "gMiddle")
    other = copy.deepcopy(first)
    other["id"] = " gMiddle "
    document["model"]["contents"].append(other)
    gs = source_element(document, "gsRelations")
    gs.update(isComplete=True, isDisjoint=False,
              generalizations=[{"id": identifier, "type": "Generalization"} for identifier in ("gMiddle", " gMiddle ")])
    for repeated in (False, True):
        if repeated:
            gs["generalizations"].append(copy.deepcopy(gs["generalizations"][0]))
        assert not fixture_issues(document)
        result = run(path=write_input(tmp_path, document, f"distinct_relations_{repeated}.json"), iri_strategy="id", input_policy=input_policy)
        assert result.outcome == "completed"
        assert (BASE.tMiddle, RDFS.subPropertyOf, BASE.tGeneral) in result.ontology
        for prefix in ("t", "s"):
            assert (BASE[prefix + "General"], RDFS.subPropertyOf, BASE[prefix + "Middle"]) not in result.ontology
        assert not any(event.kind == "singleton_completeness" for event in result.diagnostics)
        assert not list(result.ontology.triples((None, OWL.equivalentProperty, None)))


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("inverse_mode", ["all", "none"])
@pytest.mark.parametrize("failure", ["unresolved_member", "invalid_reference", "failed_member"])
@pytest.mark.parametrize("survivors", [1, 2], ids=["one_survivor", "two_survivors"])
def test_repeated_membership_preserves_relation_set_failure_boundaries(run, source_json, tmp_path, input_policy, inverse_mode, failure, survivors):
    """Rules: DK-GEN-12, DK-REL-14, DK-REL-15, DK-REL-20, DK-INV-12, DK-DIAG-03, DK-DIAG-05, DK-DIAG-14.

    RD-02 at 2b427908a7e29d546486a616a22495ea0424f294; failed member recovery
    retains errors, independent properties and surviving specific disjointness.
    """
    document = source_json("relations/hierarchy")
    gs = source_element(document, "gsRelations")
    gs.update(isComplete=True, isDisjoint=True)
    if survivors == 2:
        extra = copy.deepcopy(source_element(document, "gMiddle"))
        extra.update(id="gLeafGeneral", specific={"id": "rLeaf", "type": "Relation"})
        document["model"]["contents"].append(extra)
        gs["generalizations"].insert(1, {"id": "gLeafGeneral", "type": "Generalization"})
    if failure == "unresolved_member":
        gs["generalizations"][-1]["id"] = "missingMember"
        expected_defects = {"unresolved_reference:missingMember"}
    elif failure == "invalid_reference":
        gs["generalizations"][-1] = {"id": "gMiddle", "type": "Class"}
        expected_defects = {"reference_type_mismatch:gMiddle"}
    else:
        source_element(document, "tSibling")["propertyType"] = None
        expected_defects = {"unresolved_endpoint"}
    observations = []
    for repeated in (False, True):
        if repeated:
            gs["generalizations"].insert(1, copy.deepcopy(gs["generalizations"][0]))
        assert fixture_issues(document) == expected_defects
        result = run(path=write_input(tmp_path, document, f"partial_relations_{repeated}.json"), iri_strategy="id",
                     input_policy=input_policy, inverse_properties=inverse_mode)
        observations.append(result)
        assert any(event.severity == "ERROR" for event in result.diagnostics)
        assert not any(event.kind == "singleton_completeness" for event in result.diagnostics)
        if input_policy != "best-effort":
            assert result.outcome == "aborted" and result.ontology is None
            continue
        assert result.outcome == "completed-with-errors"
        edges = [("Middle", "General"), ("Leaf", "Middle")]
        if failure != "failed_member":
            edges.append(("Sibling", "General"))
        if survivors == 2:
            edges.append(("Leaf", "General"))
        prefixes = ("t", "s") if inverse_mode == "all" else ("t",)
        assert _edges(result.ontology) == {(BASE[prefix + a], BASE[prefix + b]) for prefix in prefixes for a, b in edges}
        pairs = {frozenset((BASE[prefix + "Middle"], BASE[prefix + "Leaf"])) for prefix in prefixes} if survivors == 2 else set()
        assert _pairs(result.ontology) == pairs
        valid = {"General", "Middle", "Leaf", "Sibling"} - ({"Sibling"} if failure == "failed_member" else set())
        assert {node for node in result.ontology.subjects(RDF.type, OWL.ObjectProperty)
                if isinstance(node, URIRef) and str(node).startswith(str(BASE))} == {
            BASE[prefix + key] for prefix in prefixes for key in valid}
        assert set(result.ontology.subject_objects(OWL.inverseOf)) == (
            {(BASE["s" + key], BASE["t" + key]) for key in valid} if inverse_mode == "all" else set())
        assert (BASE.cD, RDF.type, OWL.Class) in result.ontology
        assert (BASE.tGeneral, RDFS.subPropertyOf, BASE.tMiddle) not in result.ontology
        assert (BASE.sGeneral, RDFS.subPropertyOf, BASE.sMiddle) not in result.ontology
        if failure == "failed_member":
            assert (BASE.tSibling, RDF.type, OWL.ObjectProperty) not in result.ontology
            assert (BASE.sSibling, RDF.type, OWL.ObjectProperty) not in result.ontology
    assert diagnostic_signatures(observations[0].diagnostics) == diagnostic_signatures(observations[1].diagnostics)


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
def test_aggregation_flags_preserve_independent_stereotype_axioms(run,source_json,tmp_path,aggregation,stereotype):
    """Rules: DK-REL-01, DK-REL-19, DK-GEN-04, DK-GEN-11, DK-PROP-04, DK-CLS-01, DK-DIAG-06.

    RD-17 adds mediation asymmetry independently of aggregation/extensionality.
    Compare asserted logical subgraphs rooted at the modeled classes/properties.
    Include properties found through incoming domain/range links to the classes.
    Independently generated descriptive metadata is outside this comparison.
    """
    document=source_json('shared/binary_relation');source_element(document,'rFocus')['stereotype']=stereotype
    source_element(document,'sFocus')['aggregationKind']=aggregation
    source_element(document,'cA')['isExtensional']=True
    baseline=copy.deepcopy(document)
    source_element(baseline,'sFocus')['aggregationKind']='NONE'
    source_element(baseline,'cA')['isExtensional']=False
    unflagged=run(path=write_input(tmp_path,baseline,'unflagged.json'),iri_strategy='id',stereotype_policy='allow-missing')
    result=run(path=write_input(tmp_path,document),iri_strategy='id',stereotype_policy='allow-missing')
    assert result.outcome==unflagged.outcome=='completed';_direction(result.ontology)
    generic_base='https://w3id.org/directkg/vocab/dkgm'
    assert (None,OWL.imports,URIRef(generic_base)) in result.ontology
    generics={URIRef(generic_base+'#'+name) for name in ('memberOf','subCollectionOf','subQuantityOf','componentOf')}
    assert not generics & set(result.ontology.objects(BASE.tFocus,RDFS.subPropertyOf))
    predicates={RDF.type,RDFS.domain,RDFS.range,RDFS.subClassOf,RDFS.subPropertyOf,
                OWL.inverseOf,OWL.equivalentClass,OWL.equivalentProperty,OWL.disjointWith,
                OWL.propertyDisjointWith,OWL.onProperty,OWL.cardinality,OWL.minCardinality,
                OWL.maxCardinality,OWL.qualifiedCardinality,OWL.minQualifiedCardinality,
                OWL.maxQualifiedCardinality,OWL.onClass,OWL.onDataRange,OWL.someValuesFrom,
                OWL.allValuesFrom,OWL.hasValue,OWL.hasSelf,OWL.intersectionOf,OWL.unionOf,
                OWL.complementOf,OWL.oneOf,OWL.propertyChainAxiom,RDF.first,RDF.rest}
    logical_types={OWL.Class,OWL.ObjectProperty,OWL.DatatypeProperty,OWL.Restriction,
                   OWL.AsymmetricProperty,OWL.IrreflexiveProperty,OWL.ReflexiveProperty,
                   OWL.SymmetricProperty,OWL.TransitiveProperty,OWL.FunctionalProperty,
                   OWL.InverseFunctionalProperty}
    graphs=[]
    for observed in (unflagged,result):
        graph=observed.ontology
        roots={BASE.cA,BASE.cB,BASE.tFocus,BASE.sFocus}
        for classifier in (BASE.cA,BASE.cB):
            for predicate in (RDFS.domain,RDFS.range):
                roots.update(graph.subjects(predicate,classifier))
        graphs.append(rooted_graph(graph,roots,predicates,type_objects=logical_types))
    assert_graph_equal(*graphs)
    assert ((BASE.tFocus,RDF.type,OWL.AsymmetricProperty) in result.ontology)==(stereotype=='mediation')


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


@pytest.mark.parametrize("mode", CHAIN_MODES)
@pytest.mark.parametrize("inverse_mode", ["all", "none"])
def test_repeated_membership_preserves_singleton_chain_constraint_propagation(run, source_json, tmp_path, mode, inverse_mode):
    """Rules: DK-GEN-12, DK-REL-07, DK-REL-09, DK-REL-10, DK-REL-11, DK-REL-15, DK-REL-20, DK-INV-12, DK-DIAG-07, DK-DIAG-14.

    RD-02 at 2b427908a7e29d546486a616a22495ea0424f294. Effective singleton
    reverse inclusion must propagate material-chain non-simplicity to Peer.
    """
    document = source_json("relations/chain_constraints")
    gs = source_element(document, "gsSingleton")
    gs["isComplete"] = True
    observations = []
    for repeated in (False, True):
        if repeated:
            gs["generalizations"].append(copy.deepcopy(gs["generalizations"][0]))
        assert not fixture_issues(document)
        result = run(path=write_input(tmp_path, document, f"chain_set_{repeated}.json"), iri_strategy="id",
                     inverse_properties=inverse_mode, material_property_chains=mode)
        observations.append(result)
        assert result.outcome == "completed"
        assert (BASE.tSuper, RDFS.subPropertyOf, BASE.tPeer) in result.ontology
        assert (BASE.tPeer, RDFS.subPropertyOf, BASE.tSuper) in result.ontology
        if inverse_mode == "all":
            assert (BASE.sSuper, RDFS.subPropertyOf, BASE.sPeer) in result.ontology
            assert (BASE.sPeer, RDFS.subPropertyOf, BASE.sSuper) in result.ontology
        else:
            assert (BASE.sPeer, RDF.type, OWL.ObjectProperty) not in result.ontology
            assert (BASE.sSuper, RDF.type, OWL.ObjectProperty) not in result.ontology
        omitted = mode == "omit-conflicting-constraints"
        reverse = BASE.sPeer if inverse_mode == "all" else ("inverse", BASE.tPeer)
        _counts(result.ontology, BASE.cA, BASE.tPeer, set() if omitted else {("exact", 2)})
        _counts(result.ontology, BASE.cB, reverse, set() if omitted else {("exact", 1)})
        _counts(result.ontology, BASE.cA, BASE.tPeerTwo, {("exact", 2)})
        _counts(result.ontology, BASE.cA, BASE.tUnrelated, {("exact", 4)})
        prefixes = ("t", "s") if inverse_mode == "all" else ("t",)
        keys = ["Material", "Peer", "PeerTwo"]
        expected_pairs = set() if omitted else {
            frozenset((BASE[prefix + left], BASE[prefix + right]))
            for prefix in prefixes for index, left in enumerate(keys) for right in keys[index + 1:]}
        assert _pairs(result.ontology) == expected_pairs
        expected_chain = {(('inverse', BASE.tLeft), BASE.tRight)} if mode != "none" else set()
        assert property_chains(result.ontology, BASE.tMaterial) == expected_chain
        _compatibility(result, mode, mode != "none", {"cardinalities_omitted", "property_disjointness_omitted"} if omitted else ())
        assert any(event.kind == "singleton_completeness" and event.severity == "INFO"
                   and {"gsSingleton", "rSuper", "rPeer"} <= set(event.identified_sources)
                   and {"extensional_equivalence", "distinct_identifiers"} <= event.facts for event in result.diagnostics)
        assert not any(event.severity == "ERROR" for event in result.diagnostics)
    assert diagnostic_signatures(observations[0].diagnostics) == diagnostic_signatures(observations[1].diagnostics)


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


def _assert_dkgm_chain_warning(events, required):
    notices = [event for event in events if DKGM_CHAIN_WARNING_FACTS & event.facts]
    if required:
        assert any(event.severity == 'WARNING' and DKGM_CHAIN_WARNING_FACTS <= event.facts
                   for event in notices), 'Expected a DKGM chain-omission warning and consumer guidance'
    else:
        assert not notices


@pytest.mark.parametrize('mode,stereotypes,input_policy', [
    pytest.param(mode, stereotypes, 'strict',
                 id=f'{mode or "default"}-{case}')
    for mode in (None, 'import', 'embed', 'none')
    for case, stereotypes in (('no-bridge', ()), ('all-bridges', DKGM_STEREOTYPES))
] + [
    pytest.param('none', ('memberOf', 'componentOf'), 'strict', id='none-mixed-bridges'),
] + [
    pytest.param('none', (stereotype,), policy, id=f'none-{stereotype}-{policy}')
    for stereotype in DKGM_STEREOTYPES for policy in POLICIES
])
def test_dkgm_vocabulary_delivery_follows_emitted_bridges(
        run, source_json, tmp_path, monkeypatch, mode, stereotypes, input_policy):
    """Rules: DK-GEN-01, DK-GEN-04, DK-REL-19, DK-REL-07, DK-REL-09, DK-REL-11, DK-LBL-01, DK-LBL-02, DK-INV-03, DK-INV-04, DK-INV-05, DK-PROP-04, DK-DIAG-01, DK-DIAG-04, DK-DIAG-05; §15.

    Configurable DKGM vocabulary delivery, Alternative A, 31ee95dbc43cd411987862a81b80f6f8383e2761.
    """
    document = source_json('shared/binary_relation')
    template = source_element(document, 'rFocus')
    template['description'] = 'Authored relation description.'
    template['properties'][0].update(cardinality='1', description='Authored source-end description.', isReadOnly=True)
    template['properties'][1].update(cardinality='2', description='Authored target-end description.')
    expected_bridges = set()
    ends = []
    for index, stereotype in enumerate(stereotypes or ('material',)):
        suffix = 'Focus' if index == 0 else stereotype[0].upper() + stereotype[1:]
        relation = template if index == 0 else copy.deepcopy(template)
        relation.update(id=f'r{suffix}', stereotype=stereotype)
        relation['properties'][0]['id'] = f's{suffix}'
        relation['properties'][1]['id'] = f't{suffix}'
        relation['properties'][1]['aggregationKind'] = (
            'SHARED' if stereotype == 'memberOf' else 'COMPOSITE' if stereotype == 'componentOf' else 'NONE')
        if index:
            document['model']['contents'].append(relation)
        primary, inverse = BASE[f't{suffix}'], BASE[f's{suffix}']
        ends.append((primary, inverse, relation['properties'][1]['aggregationKind']))
        if stereotypes:
            expected_bridges.add((primary, DKGM[stereotype]))
    assert not fixture_issues(document)
    path = write_input(tmp_path, document)
    options = {} if mode is None else {'dkgm_vocabulary': mode}
    network_attempts = []

    def refuse_network(*args, **kwargs):
        network_attempts.append(args)
        raise OSError('Network access is unavailable during embedded core conversion')

    with monkeypatch.context() as offline:
        if mode == 'embed':
            offline.setattr(socket, 'getaddrinfo', refuse_network)
            offline.setattr(socket.socket, 'connect', refuse_network)
            offline.setattr(socket.socket, 'connect_ex', refuse_network)
        result = run(path=path, iri_strategy='id', input_policy=input_policy, **options)
    assert not network_attempts
    assert result.outcome == 'completed'
    assert not any(event.severity == 'ERROR' for event in result.diagnostics)
    graph = result.ontology
    for primary, inverse, aggregation in ends:
        _direction(graph, primary, BASE.cA, BASE.cB)
        _chain_inverse(graph, inverse, primary)
        _counts(graph, BASE.cA, primary, {('exact', 2)})
        _counts(graph, BASE.cB, inverse, {('exact', 1)})
        assert set(graph.objects(primary, RDFS.label)) == {Literal('worksFor')}
        assert (inverse, RDFS.label, Literal('workers')) in graph
        assert (primary, RDFS.comment, Literal('Authored relation description.')) in graph
        assert (primary, RDFS.comment, Literal('Authored target-end description.')) in graph
        assert (inverse, RDFS.comment, Literal('Authored source-end description.')) in graph
        facts = {(comment.context, comment.field, comment.value)
                 for comment in relation_end_comment_meanings(graph, primary)}
        assert ('source_end', 'isReadOnly', True) in facts
        if aggregation != 'NONE':
            assert ('target_end', 'aggregationKind', aggregation) in facts
        assert ((primary, RDF.type, OWL.AsymmetricProperty) in graph) == bool(stereotypes)
        assert (inverse, RDF.type, OWL.AsymmetricProperty) not in graph
    assert {s for s in graph.subjects(OWL.propertyChainAxiom)} == (
        DKGM_CHAINS.keys() if mode == 'embed' else set())
    targets = {target for _, target in expected_bridges}
    assert_dkgm_vocabulary(graph, ONTOLOGY, mode or 'import', bridges=expected_bridges)
    _assert_dkgm_chain_warning(result.diagnostics, mode == 'none' and bool(DKGM_CHAINS.keys() & targets))
    if mode == 'import':
        default = run(path=path, iri_strategy='id', input_policy=input_policy)
        assert default.outcome == result.outcome
        assert diagnostic_signatures(default.diagnostics) == diagnostic_signatures(result.diagnostics)


def test_dkgm_none_uses_emitted_bridges_after_relation_failure(run, source_json, tmp_path):
    """Rules: DK-GEN-04, DK-REL-01, DK-REL-19, DK-DIAG-01, DK-DIAG-03, DK-DIAG-04, DK-DIAG-05; §15.

    Configurable DKGM vocabulary delivery, Alternative A, 31ee95dbc43cd411987862a81b80f6f8383e2761.
    """
    _assert_dkgm_after_relation_failure(run, source_json, tmp_path, survivor=False)


def test_dkgm_none_warns_when_a_chain_bearing_bridge_survives_relation_failure(run, source_json, tmp_path):
    """Rules: DK-GEN-04, DK-REL-01, DK-REL-09, DK-REL-11, DK-REL-19, DK-INV-04, DK-DIAG-01, DK-DIAG-03, DK-DIAG-04, DK-DIAG-05; §15.

    Configurable DKGM vocabulary delivery, Alternative A, 31ee95dbc43cd411987862a81b80f6f8383e2761.
    """
    _assert_dkgm_after_relation_failure(run, source_json, tmp_path, survivor=True)


def _assert_dkgm_after_relation_failure(run, source_json, tmp_path, *, survivor):
    document = source_json('shared/binary_relation')
    failed = source_element(document, 'rFocus')
    failed['stereotype'] = 'memberOf'
    if survivor:
        relation = copy.deepcopy(failed)
        relation.update(id='rSurvivor', stereotype='subCollectionOf')
        relation['properties'][0].update(id='sSurvivor', cardinality='1')
        relation['properties'][1].update(id='tSurvivor', cardinality='2')
        document['model']['contents'].append(relation)
    source_element(document, 'tFocus')['propertyType']['id'] = 'missingEndpoint'
    assert fixture_issues(document) == {'unresolved_reference:missingEndpoint'}
    result = run(path=write_input(tmp_path, document), iri_strategy='id',
                 input_policy='best-effort', dkgm_vocabulary='none')
    assert result.outcome == 'completed-with-errors'
    assert any(event.kind == 'failed_relation' and event.severity == 'ERROR' for event in result.diagnostics)
    graph = result.ontology
    assert {BASE.cA, BASE.cB} <= set(graph.subjects(RDF.type, OWL.Class))
    assert all(not any(graph.triples((prop, None, None))) for prop in (BASE.tFocus, BASE.sFocus))
    bridges = {(BASE.tSurvivor, DKGM.subCollectionOf)} if survivor else set()
    assert_dkgm_vocabulary(graph, ONTOLOGY, 'none', bridges=bridges)
    if survivor:
        _direction(graph, BASE.tSurvivor, BASE.cA, BASE.cB)
        _chain_inverse(graph, BASE.sSurvivor, BASE.tSurvivor)
        _counts(graph, BASE.cA, BASE.tSurvivor, {('exact', 2)})
        _counts(graph, BASE.cB, BASE.sSurvivor, {('exact', 1)})
        assert (BASE.tSurvivor, RDF.type, OWL.AsymmetricProperty) in graph
    _assert_dkgm_chain_warning(result.diagnostics, survivor)


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


# RD-17's five additions. These checks read asserted RDF only: they neither
# repair endpoint roles nor compute a replacement conversion or OWL closure.
ADDITIONAL_CHARACTERISTICS=[
    pytest.param('characterization','kind','mode',OWL.AsymmetricProperty,id='characterization'),
    pytest.param('mediation','relator','kind',OWL.AsymmetricProperty,id='mediation'),
    pytest.param('participational','event','event',OWL.AsymmetricProperty,id='participational'),
    pytest.param('externalDependence','mode','kind',OWL.IrreflexiveProperty,id='external_dependence'),
]


def _expression_pairs(graph):
    # propertyDisjointWith is an unordered pair; anonymous inverses are read
    # through their actual owl:inverseOf edge, never through blank-node labels.
    return {frozenset((property_expression(graph,a),property_expression(graph,b)))
            for a,b in graph.subject_objects(OWL.propertyDisjointWith)}


@pytest.mark.parametrize('stereotype,source_kind,target_kind,characteristic',ADDITIONAL_CHARACTERISTICS)
@pytest.mark.parametrize('reverse',[False,True],ids=['primary_forward','primary_reverse'])
def test_additional_relation_characteristics_preserve_primary_direction(run,source_json,tmp_path,stereotype,source_kind,target_kind,characteristic,reverse):
    """Rules: DK-REL-01, DK-GEN-03, DK-INV-01, DK-INV-04; RD-17 additions 1, 4–5."""
    document=source_json('shared/binary_relation')
    source_element(document,'cA')['stereotype']=source_kind
    source_element(document,'cB')['stereotype']=target_kind
    source_element(document,'rFocus')['stereotype']=stereotype
    if reverse:
        ends=source_element(document,'rFocus')['properties']
        ends[0]['propertyType'],ends[1]['propertyType']=ends[1]['propertyType'],ends[0]['propertyType']
    assert not fixture_issues(document)
    result=run(path=write_input(tmp_path,document),iri_strategy='id',inverse_properties='all')
    assert result.outcome=='completed'
    _direction(result.ontology,BASE.tFocus,BASE.cB if reverse else BASE.cA,BASE.cA if reverse else BASE.cB)
    _chain_inverse(result.ontology,BASE.sFocus,BASE.tFocus)
    assert (BASE.tFocus,RDF.type,characteristic) in result.ontology


PAIR_INVERSES=[
    pytest.param('all',None,None,True,True,'id',id='all_without_information'),
    pytest.param('none','role','count',False,False,'id',id='none_with_information'),
    pytest.param('named','role',None,True,False,'id',id='named_mixed'),
    pytest.param('named',None,None,False,False,'id',id='named_without_roles'),
    pytest.param('informed','role',None,True,False,'id',id='informed_role_only'),
    pytest.param('informed',None,'count',False,True,'id',id='informed_count_only'),
    pytest.param('informed',None,None,False,False,'id',id='informed_without_information'),
    pytest.param('none',None,None,False,False,'name',id='name_strategy_without_inverses'),
]


@pytest.mark.parametrize('inverse_mode,left_info,right_info,left_named,right_named,strategy',PAIR_INVERSES)
@pytest.mark.parametrize('left_reverse,right_reverse',[(False,False),(True,False),(False,True),(True,True)],
                         ids=['both_primary','reverse_characterization','reverse_external','reverse_both'])
def test_feature_disjointness_selects_aligned_expressions_without_forcing_named_inverses(run,source_json,tmp_path,inverse_mode,left_info,right_info,left_named,right_named,strategy,left_reverse,right_reverse):
    """Rules: DK-REL-01, DK-INV-01, DK-INV-04, DK-REL-09, DK-PROP-03, DK-GEN-03, DK-IRI-02; RD-17 additions 2–4."""
    document=source_json('shared/material_pattern');_grounding(document,'mode')
    contents=document['model']['contents']
    for identifier in ('rMaterial','rDerivation','rUnrelated'):contents.remove(source_element(document,identifier))
    for key,info,reverse in [('Left',left_info,left_reverse),('Right',right_info,right_reverse)]:
        ends=source_element(document,'r'+key)['properties']
        ends[0].update(name='inverse'+key if info=='role' else None,cardinality='1' if info=='count' else None)
        ends[1]['cardinality']=None
        if reverse:ends[0]['propertyType'],ends[1]['propertyType']=ends[1]['propertyType'],ends[0]['propertyType']
    assert not fixture_issues(document)
    result=run(path=write_input(tmp_path,document),iri_strategy=strategy,inverse_properties=inverse_mode)
    assert result.outcome=='completed'
    graph=result.ontology
    feature=_primary(result,'cGround',strategy)
    expected=[];named_resources=set()
    primaries={key:_primary(result,'t'+key,strategy) for key in ('Left','Right')}
    for key,reverse,named,endpoint in [('Left',left_reverse,left_named,'cA'),('Right',right_reverse,right_named,'cB')]:
        primary=primaries[key];other=_primary(result,endpoint,strategy)
        _direction(graph,primary,other if reverse else feature,feature if reverse else other)
        inverse=_primary(result,'s'+key,strategy) if named else None
        assert {node for node in graph.subjects(OWL.inverseOf,primary) if isinstance(node,URIRef)}==({inverse} if named else set())
        if named:
            _chain_inverse(graph,inverse,primary);named_resources.add(inverse)
        expected.append(primary if not reverse else inverse if named else ('inverse',primary))
    assert {node for node in graph.subjects(RDF.type,OWL.ObjectProperty)
            if isinstance(node,URIRef) and str(node).startswith(str(BASE))}==set(primaries.values())|named_resources
    assert not list(graph.triples((None,OWL.propertyChainAxiom,None)))
    assert _expression_pairs(graph)=={frozenset(expected)}


@pytest.mark.parametrize('variant',[
    'without_material','without_derivation','multiple_matches','names_only','subclass_feature','superclass_feature',
    'ambiguous_characterization','ambiguous_external','no_feature','failed_characterization','failed_external'])
def test_feature_pairing_uses_exact_successful_role_identity_independently_of_chain_eligibility(run,source_json,tmp_path,variant):
    """Rules: DK-REL-01, DK-REL-07, DK-INV-04, DK-GEN-02, DK-DIAG-02, DK-DIAG-03, DK-DIAG-05; §3.4; RD-17 additions 2, 5."""
    document=source_json('shared/material_pattern');_grounding(document,'mode')
    contents=document['model']['contents'];expected={frozenset((BASE.tLeft,BASE.tRight))}
    if variant=='without_material':
        for identifier in ('rMaterial','rDerivation'):contents.remove(source_element(document,identifier))
    elif variant=='without_derivation':contents.remove(source_element(document,'rDerivation'))
    elif variant=='multiple_matches':
        for key in ('Left','Right'):
            extra=copy.deepcopy(source_element(document,'r'+key));extra['id']='r'+key+'Extra'
            extra['properties'][0]['id']='s'+key+'Extra';extra['properties'][1]['id']='t'+key+'Extra'
            contents.append(extra)
        expected={frozenset((BASE[a],BASE[b])) for a in ('tLeft','tLeftExtra') for b in ('tRight','tRightExtra')}
    elif variant in {'names_only','subclass_feature','superclass_feature'}:
        source_element(document,'cExtra').update(stereotype='mode',name=source_element(document,'cGround')['name'])
        source_element(document,'sRight')['propertyType']['id']='cExtra'
        if variant!='names_only':
            a,b=('cExtra','cGround') if variant=='subclass_feature' else ('cGround','cExtra')
            contents.append({'id':'gFeature','name':None,'description':None,'type':'Generalization','propertyAssignments':None,
                             'specific':{'id':a,'type':'Class'},'general':{'id':b,'type':'Class'}})
        expected=set()
    elif variant in {'ambiguous_characterization','ambiguous_external'}:
        source_element(document,'cA' if variant=='ambiguous_characterization' else 'cB')['stereotype']='mode'
        expected=set()
    elif variant=='no_feature':
        source_element(document,'cGround')['stereotype']='kind'
        contents.remove(source_element(document,'rDerivation'));expected=set()
    else:
        source_element(document,'sLeft' if variant=='failed_characterization' else 'sRight')['propertyType']['id']='missingFeature'
        expected=set()
    failed=variant.startswith('failed_')
    assert fixture_issues(document)==(frozenset({'unresolved_reference:missingFeature'}) if failed else frozenset())
    result=run(path=write_input(tmp_path,document),iri_strategy='id',inverse_properties='none',
               input_policy='best-effort' if failed else 'strict',material_property_chains='preserve-conflicting-constraints')
    assert result.outcome==('completed-with-errors' if failed else 'completed')
    graph=result.ontology
    for key,endpoint in [('Left','cA'),('Right','cB')]:
        missing=variant==('failed_characterization' if key=='Left' else 'failed_external')
        assert ((BASE['t'+key],RDF.type,OWL.ObjectProperty) in graph)==(not missing)
        if not missing:_direction(graph,BASE['t'+key],BASE.cExtra if key=='Right' and variant in {'names_only','subclass_feature','superclass_feature'} else BASE.cGround,BASE[endpoint])
    if variant in {'without_material','without_derivation','multiple_matches','names_only','subclass_feature','superclass_feature','no_feature'} or failed:
        assert not list(graph.triples((None,OWL.propertyChainAxiom,None)))
    if failed:assert any(d.severity=='ERROR' for d in result.diagnostics)
    else:assert not any(d.severity=='ERROR' for d in result.diagnostics)
    assert _expression_pairs(graph)==expected


@pytest.mark.parametrize('grounding',GROUNDINGS)
@pytest.mark.parametrize('mode',CHAIN_MODES)
def test_chain_body_participation_does_not_suppress_compatible_relation_additions(run,source_json,tmp_path,grounding,mode):
    """Rules: DK-REL-01, DK-REL-07, DK-REL-09, DK-REL-10, DK-REL-11, DK-INV-01, DK-INV-04; RD-17 additions 1–5."""
    _assert_chain_body_additions(run, source_json, tmp_path, grounding, mode)

def _assert_chain_body_additions(run, source_json, tmp_path, grounding, mode, input_policy=None):
    """Shared original chain/addition assertions, with unchanged default options."""
    document=source_json('shared/material_pattern');_grounding(document,grounding)
    assert not fixture_issues(document)
    path = write_input(tmp_path, document)
    policy_options = {} if input_policy is None else {'input_policy': input_policy}
    result=run(path=path,iri_strategy='id',inverse_properties='all',material_property_chains=mode,**policy_options)
    assert result.outcome=='completed';graph=result.ontology
    assert property_chains(graph,BASE.tMaterial)==({(('inverse',BASE.tLeft),BASE.tRight)} if mode!='none' else set())
    for key,target in [('Left','cA'),('Right','cB')]:
        _direction(graph,BASE['t'+key],BASE.cGround,BASE[target]);_chain_inverse(graph,BASE['s'+key],BASE['t'+key])
        _counts(graph,BASE.cGround,BASE['t'+key],{('exact',1)})
    _counts(graph,BASE.cA,BASE.tMaterial,set() if mode=='omit-conflicting-constraints' else {('min',2),('max',5)})
    _counts(graph,BASE.cB,BASE.sMaterial,set() if mode=='omit-conflicting-constraints' else {('exact',1)})
    _counts(graph,BASE.cA,BASE.tUnrelated,{('exact',4)})
    assert (BASE.tLeft,RDF.type,OWL.AsymmetricProperty) in graph
    assert (BASE.tRight,RDF.type,OWL.IrreflexiveProperty if grounding=='mode' else OWL.AsymmetricProperty) in graph
    assert _expression_pairs(graph)==({frozenset((BASE.tLeft,BASE.tRight))} if grounding=='mode' else set())
    return result, path



@pytest.mark.parametrize('mode',CHAIN_MODES)
@pytest.mark.parametrize('case',[
    'characterization','external_dependence','mediation','participational','inverse_named','inverse_anonymous','below_non_simple'])
def test_new_relation_axioms_apply_simplicity_per_axiom_without_repairing_existing_constraints(run,source_json,tmp_path,mode,case):
    """Rules: DK-REL-01, DK-REL-07, DK-REL-09, DK-REL-11, DK-REL-14, DK-REL-15, DK-INV-01, DK-INV-04, DK-INV-12, DK-PROP-03, DK-DIAG-02; §3.4; RD-17 additions 3–5."""
    _assert_relation_axiom_gate(run, source_json, tmp_path, mode, case)

def _assert_relation_axiom_gate(run, source_json, tmp_path, mode, case, input_policy=None, **controls):
    """Shared fixed gate assertions; retain the original caller's default options."""
    document=source_json('relations/chain_constraints');_grounding(document,'mode')
    source_element(document,'rPeer')['stereotype']='mediation'
    source_element(document,'rPeerTwo')['stereotype']='participational'
    inverse_mode='none' if case=='inverse_anonymous' else 'all'
    target={'characterization':'Left','external_dependence':'Right','mediation':'Peer','participational':'PeerTwo',
            'inverse_named':'Left','inverse_anonymous':'Left','below_non_simple':None}[case]
    inverse_case=case.startswith('inverse_')
    if inverse_case:
        ends=source_element(document,'rLeft')['properties']
        ends[0]['propertyType'],ends[1]['propertyType']=ends[1]['propertyType'],ends[0]['propertyType']
        source_element(document,'sMaterial')['subsettedProperties']=[{'id':'sLeft','type':'Property'}]
    else:
        specific,general=('rLeft','rGrand') if case=='below_non_simple' else ('rGrand','r'+target)
        document['model']['contents'].append({'id':'gAddition','name':None,'description':None,'type':'Generalization','propertyAssignments':None,
                                              'specific':{'id':specific,'type':'Relation'},'general':{'id':general,'type':'Relation'}})
    assert not fixture_issues(document)
    path = write_input(tmp_path, document)
    policy_options = {} if input_policy is None else {'input_policy': input_policy}
    result=run(path=path,iri_strategy='id',inverse_properties=inverse_mode,material_property_chains=mode,
               **policy_options, **controls)
    assert result.outcome=='completed';graph=result.ontology
    first=BASE.tLeft if inverse_case else ('inverse',BASE.tLeft)
    assert property_chains(graph,BASE.tMaterial)==({(first,BASE.tRight)} if mode!='none' else set())
    if inverse_case:
        reverse_material=BASE.sMaterial if inverse_mode=='all' else ('inverse',BASE.tMaterial)
        reverse_left=BASE.sLeft if inverse_mode=='all' else ('inverse',BASE.tLeft)
        assert (reverse_material,reverse_left) in {(property_expression(graph,a),property_expression(graph,b)) for a,b in graph.subject_objects(RDFS.subPropertyOf)}
    else:
        assert (BASE['t'+specific[1:]],RDFS.subPropertyOf,BASE['t'+general[1:]]) in graph
    affected={'Material','Super','Grand'}|({target} if target else set()) if mode!='none' else set()
    # Preserve the established REL-07/15 policies, even when preservation leaves
    # existing non-simple cardinalities/disjointness in the output.
    omitted=affected if mode=='omit-conflicting-constraints' else set()
    for key in ('Material','Super','Grand','Peer','PeerTwo','Left','Right'):
        domain,range_=(('cA','cGround') if inverse_case else ('cGround','cA')) if key=='Left' else ('cGround','cB') if key=='Right' else ('cA','cB')
        _direction(graph,BASE['t'+key],BASE[domain],BASE[range_])
        if inverse_mode=='all':_chain_inverse(graph,BASE['s'+key],BASE['t'+key])
        else:assert not {node for node in graph.subjects(OWL.inverseOf,BASE['t'+key]) if isinstance(node,URIRef)}
        expected={('min',2),('max',5)} if key=='Material' else {('exact',1 if key in {'Left','Right'} else 2)}
        _counts(graph,BASE[domain],BASE['t'+key],set() if key in omitted else expected)
        reverse=BASE['s'+key] if inverse_mode=='all' else ('inverse',BASE['t'+key])
        _counts(graph,BASE[range_],reverse,set() if key in omitted else {('exact',1)})
    _counts(graph,BASE.cA,BASE.tUnrelated,{('exact',4)})
    expected_pairs={frozenset((BASE[prefix+a],BASE[prefix+b]))
                    for prefix in (['t','s'] if inverse_mode=='all' else ['t'])
                    for a,b in [('Material','Peer'),('Material','PeerTwo'),('Peer','PeerTwo')]
                    if not ({a,b}&omitted)}
    established_properties={BASE[prefix+key] for prefix in ('t','s') for key in ('Material','Peer','PeerTwo')}
    assert {pair for pair in _expression_pairs(graph) if pair<=established_properties}==expected_pairs
    if not ({'Left','Right'}&affected):
        aligned_left=(BASE.sLeft if inverse_mode=='all' else ('inverse',BASE.tLeft)) if inverse_case else BASE.tLeft
        expected_pairs.add(frozenset((aligned_left,BASE.tRight)))
    # Per-axiom expectation: an incompatible new declaration cannot suppress a
    # compatible addition on another property or remove an established axiom.
    for key,characteristic in [('Left',OWL.AsymmetricProperty),('Right',OWL.IrreflexiveProperty),
                               ('Peer',OWL.AsymmetricProperty),('PeerTwo',OWL.AsymmetricProperty)]:
        assert ((BASE['t'+key],RDF.type,characteristic) in graph)==(key not in affected)
    assert _expression_pairs(graph)==expected_pairs
    return result, path



@pytest.mark.parametrize('mode',CHAIN_MODES)
def test_imported_non_simple_superproperties_do_not_suppress_simple_source_additions_or_mereology(run,source_json,tmp_path,mode):
    """Rules: DK-REL-01, DK-REL-07, DK-REL-14, DK-REL-19, DK-GEN-04, DK-INV-04, DK-DIAG-01, DK-DIAG-04; §15.

    RD-17 additions 4–5 and configurable DKGM vocabulary delivery, Alternative A,
    31ee95dbc43cd411987862a81b80f6f8383e2761.
    """
    _assert_simple_source_additions_below_mereology(run, source_json, tmp_path, mode)


@pytest.mark.parametrize('vocabulary', ['embed', 'none'])
@pytest.mark.parametrize('mode', CHAIN_MODES)
def test_dkgm_vocabulary_keeps_simple_source_additions_and_material_chains(run, source_json, tmp_path, mode, vocabulary):
    """Rules: DK-GEN-04, DK-REL-01, DK-REL-07, DK-REL-14, DK-REL-19, DK-INV-04, DK-DIAG-01, DK-DIAG-04, DK-DIAG-07; §15.

    Configurable DKGM vocabulary delivery, Alternative A, 31ee95dbc43cd411987862a81b80f6f8383e2761.
    """
    _assert_simple_source_additions_below_mereology(run, source_json, tmp_path, mode, vocabulary)


def _assert_simple_source_additions_below_mereology(run, source_json, tmp_path, mode, vocabulary=None):
    document=source_json('shared/material_pattern');_grounding(document,'mode')
    source_element(document,'rUnrelated')['stereotype']='subCollectionOf'
    document['model']['contents'].append({'id':'gMereology','name':None,'description':None,'type':'Generalization','propertyAssignments':None,
                                          'specific':{'id':'rLeft','type':'Relation'},'general':{'id':'rUnrelated','type':'Relation'}})
    assert not fixture_issues(document)
    options = {} if vocabulary is None else {'dkgm_vocabulary': vocabulary}
    result=run(path=write_input(tmp_path,document),iri_strategy='id',inverse_properties='none',
               material_property_chains=mode, **options)
    assert result.outcome=='completed';graph=result.ontology
    generic = DKGM.subCollectionOf
    assert_dkgm_vocabulary(graph, ONTOLOGY, vocabulary or 'import',
                           bridges={(BASE.tUnrelated, generic)})
    if vocabulary is None:
        published = load_graph(Path(__file__).resolve().parents[2] / 'vocabulary/latest/dkgm-vocabulary.ttl')
        assert property_chains(published, generic) == {(generic, generic)}
    assert (BASE.tLeft,RDFS.subPropertyOf,BASE.tUnrelated) in graph
    assert (BASE.tUnrelated,RDFS.subPropertyOf,generic) in graph
    _direction(graph,BASE.tLeft,BASE.cGround,BASE.cA);_direction(graph,BASE.tRight,BASE.cGround,BASE.cB)
    _direction(graph,BASE.tUnrelated,BASE.cA,BASE.cExtra)
    _counts(graph,BASE.cA,BASE.tUnrelated,{('exact',4)})
    assert property_chains(graph,BASE.tMaterial)==({(('inverse',BASE.tLeft),BASE.tRight)} if mode!='none' else set())
    assert (BASE.tUnrelated,RDF.type,OWL.AsymmetricProperty) in graph
    assert (BASE.tLeft,RDF.type,OWL.AsymmetricProperty) in graph
    assert (BASE.tRight,RDF.type,OWL.IrreflexiveProperty) in graph
    assert _expression_pairs(graph)=={frozenset((BASE.tLeft,BASE.tRight))}
    if vocabulary is not None:
        _compatibility(result, mode, mode != 'none')
    _assert_dkgm_chain_warning(result.diagnostics, vocabulary == 'none')


@pytest.mark.parametrize('vocabulary', ['embed', 'none'])
@pytest.mark.parametrize('mode', CHAIN_MODES)
def test_dkgm_vocabulary_preserves_gate_for_non_simple_source_properties(run, source_json, tmp_path, mode, vocabulary):
    """Rules: DK-GEN-04, DK-REL-01, DK-REL-07, DK-REL-09, DK-REL-11, DK-REL-14, DK-REL-15, DK-INV-01, DK-INV-04, DK-INV-12, DK-PROP-03, DK-DIAG-02; §15.

    Configurable DKGM vocabulary delivery, Alternative A, 31ee95dbc43cd411987862a81b80f6f8383e2761.
    """
    result, _ = _assert_relation_axiom_gate(run, source_json, tmp_path, mode, 'external_dependence',
                                           dkgm_vocabulary=vocabulary)
    assert_dkgm_vocabulary(result.ontology, ONTOLOGY, vocabulary)


@pytest.mark.parametrize('mode',CHAIN_MODES[1:])
def test_existing_mereological_asymmetry_survives_non_simple_material_superproperty(run,source_json,tmp_path,mode):
    """Rules: DK-REL-07, DK-REL-09, DK-REL-11, DK-REL-14, DK-REL-19, DK-GEN-04, DK-INV-04; RD-17 addition 5."""
    _assert_mereological_asymmetry_survives_material_chain(run, source_json, tmp_path, mode)


@pytest.mark.parametrize('vocabulary', ['embed', 'none'])
@pytest.mark.parametrize('mode', CHAIN_MODES[1:])
def test_dkgm_keeps_existing_asymmetry_on_a_non_simple_source_property(run, source_json, tmp_path, mode, vocabulary):
    """Rules: DK-GEN-04, DK-REL-07, DK-REL-09, DK-REL-11, DK-REL-14, DK-REL-19, DK-INV-04, DK-DIAG-01, DK-DIAG-04; §15.

    Configurable DKGM vocabulary delivery, Alternative A, 31ee95dbc43cd411987862a81b80f6f8383e2761.
    """
    _assert_mereological_asymmetry_survives_material_chain(run, source_json, tmp_path, mode, vocabulary)


def _assert_mereological_asymmetry_survives_material_chain(run, source_json, tmp_path, mode, vocabulary=None):
    document=source_json('shared/material_pattern')
    source_element(document,'rUnrelated')['stereotype']='componentOf'
    document['model']['contents'].append({'id':'gMereology','name':None,'description':None,'type':'Generalization','propertyAssignments':None,
                                          'specific':{'id':'rMaterial','type':'Relation'},'general':{'id':'rUnrelated','type':'Relation'}})
    assert not fixture_issues(document)
    options = {} if vocabulary is None else {'dkgm_vocabulary': vocabulary}
    result=run(path=write_input(tmp_path,document),iri_strategy='id',inverse_properties='all',
               material_property_chains=mode, **options)
    assert result.outcome=='completed';graph=result.ontology
    # This actual chain and specialization make the source-specific mereology
    # property non-simple; it is not merely below a non-simple generic property.
    assert property_chains(graph,BASE.tMaterial)=={(('inverse',BASE.tLeft),BASE.tRight)}
    assert (BASE.tMaterial,RDFS.subPropertyOf,BASE.tUnrelated) in graph
    assert (BASE.tUnrelated, RDFS.subPropertyOf, DKGM.componentOf) in graph
    _direction(graph,BASE.tMaterial,BASE.cA,BASE.cB);_direction(graph,BASE.tUnrelated,BASE.cA,BASE.cExtra)
    _chain_inverse(graph,BASE.sUnrelated,BASE.tUnrelated)
    omitted=mode=='omit-conflicting-constraints'
    _counts(graph,BASE.cA,BASE.tMaterial,set() if omitted else {('min',2),('max',5)})
    _counts(graph,BASE.cB,BASE.sMaterial,set() if omitted else {('exact',1)})
    _counts(graph,BASE.cA,BASE.tUnrelated,set() if omitted else {('exact',4)})
    _counts(graph,BASE.cExtra,BASE.sUnrelated,set() if omitted else {('exact',1)})
    _counts(graph,BASE.cGround,BASE.tLeft,{('exact',1)});_counts(graph,BASE.cGround,BASE.tRight,{('exact',1)})
    assert (BASE.tUnrelated,RDF.type,OWL.AsymmetricProperty) in graph
    if vocabulary is not None:
        assert_dkgm_vocabulary(graph, ONTOLOGY, vocabulary,
                               bridges={(BASE.tUnrelated, DKGM.componentOf)})
        _assert_dkgm_chain_warning(result.diagnostics, False)


# These shared observations originated in the accepted historicalDependence
# decision and also apply to RD-17's settled partial relation stereotypes.
# The earlier five relation-axiom additions retain their independent treatment.
def _ordinary_relation_mapping_equal(first, second, *, expected_additions=()):
    """Compare logic, allowing independent metadata and fixed accepted additions.

    DK-CLS-03/04 class disjointness is compared as unordered pairs.
    Callers supply explicit expected RDF, never inferred production behavior.
    The ordinary observation and the actual graph remain untouched.
    """
    types = {OWL.Class, RDFS.Datatype, OWL.ObjectProperty, OWL.DatatypeProperty,
             OWL.Restriction, OWL.AsymmetricProperty, OWL.IrreflexiveProperty,
             OWL.ReflexiveProperty, OWL.SymmetricProperty, OWL.TransitiveProperty,
             OWL.FunctionalProperty, OWL.InverseFunctionalProperty,
             OWL.AllDifferent, OWL.AllDisjointClasses, OWL.AllDisjointProperties}
    predicates = {RDF.type, RDFS.domain, RDFS.range, RDFS.subClassOf, RDFS.subPropertyOf,
                  OWL.inverseOf, OWL.equivalentClass, OWL.equivalentProperty,
                  OWL.disjointWith, OWL.propertyDisjointWith, OWL.disjointUnionOf,
                  OWL.onProperty, OWL.cardinality, OWL.minCardinality, OWL.maxCardinality,
                  OWL.qualifiedCardinality, OWL.minQualifiedCardinality, OWL.maxQualifiedCardinality,
                  OWL.onClass, OWL.onDataRange, OWL.someValuesFrom, OWL.allValuesFrom,
                  OWL.hasValue, OWL.hasSelf, OWL.unionOf, OWL.intersectionOf,
                  OWL.complementOf, OWL.oneOf, OWL.members, OWL.distinctMembers,
                  OWL.propertyChainAxiom, OWL.hasKey, OWL.sameAs, OWL.differentFrom,
                  OWL.onDatatype, OWL.withRestrictions, OWL.datatypeComplementOf,
                  RDF.first, RDF.rest}
    projections = []
    for index, result in enumerate((first, second)):
        graph = result.ontology
        if index == 0 and expected_additions:
            graph = Graph() + graph
            for triple in expected_additions:
                graph.add(triple)
        roots = {subject for subject, kind in graph.subject_objects(RDF.type) if kind in types}
        # Include even untyped/foreign-namespace properties connected to domain
        # classes, plus anonymous restrictions and complete RDF collections.
        for classifier in tuple(roots):
            for predicate in (RDFS.domain, RDFS.range):
                roots.update(graph.subjects(predicate, classifier))
        for left, right in graph.subject_objects(OWL.disjointWith):
            roots.update((left, right))
        projections.append(rooted_graph(graph, roots, predicates, type_objects=types,
                                        unordered_predicates={OWL.disjointWith}))
    assert_graph_equal(*projections)


def _source_target_naming_warning(result, relation_id):
    assert any(d.severity == 'WARNING' and 'source_target_naming' in d.facts
               and relation_id in d.identified_sources for d in result.diagnostics), result.diagnostics


def _relation_limitation_warning(result):
    assert any(d.severity == 'WARNING' and 'residual_relation_semantics' in d.facts
               for d in result.diagnostics), result.diagnostics
    assert not any(d.severity == 'ERROR' for d in result.diagnostics)


def _other_relation_diagnostics(result):
    """Preserve observed meaning/source information and event multiplicity.

    Human wording remains in Diagnostic.message/raw for inspection. Neither
    prose nor the presentation order of source locators is an acceptance rule.
    """
    return Counter((d.severity, d.kind, d.facts, tuple(sorted(d.source_ids)),
                    tuple(sorted(d.source_types)), tuple(sorted(d.identified_sources)),
                    tuple(sorted(d.generated_iris)))
                   for d in result.diagnostics if d.kind != 'unmapped_relation_stereotype')


# RD-17 alternative A, registration 8bfc90fc40d732212ea84e583986c7ae0b96c65b.
# Fixed lexical candidates come from DK-REL-04, never from production selectors.
PARTIAL_SEMANTIC_RELATIONS = [
    pytest.param('participation', 'participatesIn', 'hasParticipant', id='participation'),
    pytest.param('creation', 'wasCreatedIn', 'creates', id='creation'),
    pytest.param('termination', 'wasTerminatedIn', 'terminates', id='termination'),
    pytest.param('participational', 'participationalPartOf', 'hasParticipationalPart', id='participational'),
    pytest.param('manifestation', 'manifestedIn', 'manifests', id='manifestation'),
    pytest.param('mediation', 'mediates', 'isMediatedBy', id='mediation'),
    pytest.param('characterization', 'isCharacterizedBy', 'characterizes', id='characterization'),
    pytest.param('externalDependence', 'externallyDependsOn', 'isExternalDependencyOf', id='externalDependence'),
]

PARTIAL_RELATION_ENDPOINTS = {
    'participational': (('event', 'PartEvent'), ('event', 'WholeEvent')),
    'manifestation': (('mode', 'Aspect'), ('event', 'Event')),
    'mediation': (('relator', 'Relator'), ('kind', 'Endurant')),
    'characterization': (('kind', 'Bearer'), ('mode', 'Feature')),
    'externalDependence': (('mode', 'Mode'), ('kind', 'Endurant')),
}

DEPENDENCY_RELATIONS = ['mediation', 'characterization', 'externalDependence']
PARTIAL_RELATION_CHARACTERISTICS = {
    'participational': OWL.AsymmetricProperty,
    'mediation': OWL.AsymmetricProperty,
    'characterization': OWL.AsymmetricProperty,
    'externalDependence': OWL.IrreflexiveProperty,
}


@pytest.mark.parametrize('stereotype', ['participation', 'creation', 'termination', 'participational', 'manifestation'] + DEPENDENCY_RELATIONS)
@pytest.mark.parametrize('profile', ['defaults', 'id-none-strict', 'name-none-best-effort'])
def test_partial_semantic_relations_preserve_ordinary_mapping_and_limitation_warning(
        run, invoke, source_json, tmp_path, stereotype, profile):
    """Rules: DK-REL-01, DK-REL-02, DK-REL-09, DK-REL-10, DK-REL-11, DK-LBL-01, DK-LBL-02, DK-IRI-06, DK-IRI-09, DK-INV-01, DK-INV-04, DK-PROP-04, DK-PROP-05, DK-PROP-06, DK-DIAG-01, DK-DIAG-05, DK-DIAG-18, DK-GEN-11.

    RD-17 at 8bfc90fc40d732212ea84e583986c7ae0b96c65b: adding one of the
    three stereotypes preserves ordinary output and independent annotations.
    Defaults and every input policy retain a nonfatal limitation warning.
    Complete shared/binary_relation input; inline mutations/expectations only.
    Registration fb05478031e290b123e766ad5188e4cef9935357 adds participational
    and manifestation; retain only the former's accepted compatible asymmetry.
    Registration 490f209e0d70533bac56674e2844a7463fe77a09 adds the dependency
    trio, retaining only their independently accepted primary characteristics.
    """
    document = source_json('shared/binary_relation')
    document['languages'] = ['nl']
    (source_kind, source_name), (target_kind, target_name) = PARTIAL_RELATION_ENDPOINTS.get(
        stereotype, (('kind', 'Endurant'), ('event', 'Event')))
    source_element(document, 'cA').update(name=source_name, stereotype=source_kind)
    source_element(document, 'cB').update(name=target_name, stereotype=target_kind)
    description = f'The author explicitly mentions {stereotype}.'
    source_element(document, 'rFocus').update(name='Declared link', stereotype=None, description=description)
    source_element(document, 'tFocus').update(
        name='target role', description='Target-end description.', cardinality='2..5',
        isReadOnly=True, stereotype='end')
    source_element(document, 'sFocus').update(
        name='source role', description='Source-end description.', cardinality='1',
        isOrdered=True, stereotype='begin')
    options = {'stereotype_policy': 'allow-missing'}
    if profile == 'id-none-strict':
        options.update(iri_strategy='id', inverse_properties='none', input_policy='strict', language='fr')
    elif profile == 'name-none-best-effort':
        options.update(inverse_properties='none', input_policy='best-effort', omit_identifiers=True, language='fr')
    strategy = 'id' if profile == 'id-none-strict' else 'name'
    named_inverse = profile == 'defaults'
    tag = 'nl' if profile == 'defaults' else 'fr'
    assert not fixture_issues(document)
    ordinary = run(path=write_input(tmp_path, document, 'ordinary.json'), **options)
    source_element(document, 'rFocus')['stereotype'] = stereotype
    assert not fixture_issues(document)
    path = write_input(tmp_path, document, 'stereotyped.json')
    result = run(path=path, **options)
    assert ordinary.outcome == result.outcome == 'completed'
    # Identifier omission is checked using the independently labeled ordinary
    # primary rather than inventing an IRI from an optional owner qualifier.
    if profile == 'name-none-best-effort':
        primary = one_subject(result.ontology, RDFS.label, Literal('Declared link', lang=tag))
        assert primary == one_subject(ordinary.ontology, RDFS.label, Literal('Declared link', lang=tag))
    else:
        primary = _primary(result, strategy=strategy)
        assert primary == _primary(ordinary, strategy=strategy)
    graph = result.ontology
    source, target = (BASE.cA, BASE.cB) if strategy == 'id' else (BASE[source_name], BASE[target_name])
    _direction(graph, primary, source, target)
    assert set(graph.objects(primary, RDFS.label)) == {Literal('Declared link', lang=tag)}
    assert set(graph.objects(primary, DCTERMS.identifier)) == ({Literal('tFocus')} if profile == 'defaults' else set())
    for text in (description, 'Target-end description.'):
        assert (primary, RDFS.comment, Literal(text, lang=tag)) in graph
    reverse = one_subject(graph, OWL.inverseOf, primary) if named_inverse else ('inverse', primary)
    _counts(graph, source, primary, {('min', 2), ('max', 5)})
    _counts(graph, target, reverse, {('exact', 1)})
    if named_inverse:
        _direction(graph, reverse, target, source)
        assert (primary, OWL.inverseOf, reverse) not in graph
        assert set(graph.objects(reverse, DCTERMS.identifier)) == {Literal('sFocus')}
        assert set(graph.objects(reverse, RDFS.label)) == {Literal('source role', lang=tag)}
        assert (reverse, RDFS.comment, Literal('Source-end description.', lang=tag)) in graph
    else:
        assert not any(isinstance(node, URIRef) for node in graph.subjects(OWL.inverseOf, primary))
        assert not list(graph.subjects(RDFS.comment, Literal('Source-end description.', lang=tag)))
    if profile == 'name-none-best-effort':
        assert not list(graph.triples((None, DCTERMS.identifier, None)))
    # Independent flag and begin/end wording is interpreted by the adapter's
    # inspected RDF audit; no generated prose template is required here.
    assert set(ordinary.ontology.objects(primary, RDFS.comment)) == set(graph.objects(primary, RDFS.comment))
    # These complete binary inputs have no non-simple property: only the
    # applicable accepted primary characteristic may differ from ordinary RDF.
    characteristic = PARTIAL_RELATION_CHARACTERISTICS.get(stereotype)
    expected_additions = ((primary, RDF.type, characteristic),) if characteristic else ()
    _ordinary_relation_mapping_equal(ordinary, result, expected_additions=expected_additions)
    assert invoke.read_relation_stereotype_annotations(result, path) == ()
    assert _other_relation_diagnostics(result) == _other_relation_diagnostics(ordinary)
    assert any(d.kind == 'ordering' and d.severity == 'INFO' for d in result.diagnostics)
    _relation_limitation_warning(result)
    if stereotype in DEPENDENCY_RELATIONS:
        assert 'rFocus' in invoke.read_relation_limitation_source_ids(result, path)


@pytest.mark.parametrize('stereotype,forward,backward', PARTIAL_SEMANTIC_RELATIONS)
@pytest.mark.parametrize('branch,strategy,label_mode,input_policy', [
    pytest.param('target_role', 'name', 'source-only', 'tolerant', id='target-role-name'),
    pytest.param('target_role', 'id', 'generated', 'strict', id='target-role-id-generated'),
    pytest.param('semantic', 'name', 'source-only', 'tolerant', id='semantic-name'),
    pytest.param('semantic', 'name', 'generated', 'strict', id='semantic-name-generated-strict'),
    pytest.param('semantic', 'id', 'source-only', 'best-effort', id='semantic-id'),
    pytest.param('semantic', 'id', 'generated', 'tolerant', id='semantic-id-generated'),
    pytest.param('disabled', 'name', 'generated', 'best-effort', id='disabled-name-generated'),
    pytest.param('disabled', 'id', 'generated', 'strict', id='disabled-id-generated'),
])
def test_partial_semantic_relations_keep_naming_labels_and_warning_independent(
        run, invoke, source_json, tmp_path, stereotype, forward, backward,
        branch, strategy, label_mode, input_policy):
    """Rules: DK-REL-01, DK-REL-02, DK-REL-03, DK-REL-04, DK-REL-06, DK-LBL-01, DK-LBL-02, DK-IRI-06, DK-IRI-09, DK-PROP-02, DK-INV-01, DK-INV-04, DK-DIAG-01, DK-DIAG-05, DK-GEN-11.

    RD-17 at 8bfc90fc40d732212ea84e583986c7ae0b96c65b. Both represented
    directions retain fixed lexical selection and independent labels. Naming
    success, ID strategy and disabled stereotype naming cannot hide the warning.
    Complete shared/binary_relation input; no stored expectation graph.
    Registration fb05478031e290b123e766ad5188e4cef9935357 adds participational
    with explicit whole-marker evidence and manifestation without a new characteristic.
    Registration 490f209e0d70533bac56674e2844a7463fe77a09 extends these checks
    to the dependency trio without changing established names or characteristics.
    """
    observations = []
    for reverse_direction in (False, True):
        document = source_json('shared/binary_relation')
        document['languages'] = ['nl']
        (source_kind, source_name), (target_kind, target_name) = PARTIAL_RELATION_ENDPOINTS.get(
            stereotype, (('kind', 'Endurant'), ('event', 'Event')))
        source_element(document, 'cA').update(name=source_name, stereotype=source_kind)
        source_element(document, 'cB').update(name=target_name, stereotype=target_kind)
        relation = source_element(document, 'rFocus')
        relation.update(name=None, stereotype=stereotype)
        source_element(document, 'tFocus')['name'] = 'target role' if branch == 'target_role' else None
        if reverse_direction:
            ends = relation['properties']
            ends[0]['propertyType'], ends[1]['propertyType'] = ends[1]['propertyType'], ends[0]['propertyType']
        if stereotype == 'participational':
            # Explicit whole-end occurrence, independent of class names. When
            # direction reverses, the same WholeEvent remains whole-marked.
            source_element(document, 'sFocus')['aggregationKind'] = 'SHARED' if reverse_direction else 'NONE'
            source_element(document, 'tFocus')['aggregationKind'] = 'NONE' if reverse_direction else 'SHARED'
        assert not fixture_issues(document)
        path = write_input(tmp_path, document, 'reverse.json' if reverse_direction else 'forward.json')
        result = run(path=path, iri_strategy=strategy, inverse_properties='named',
                     relation_labels=label_mode, input_policy=input_policy,
                     no_stereotype_relation_naming=branch == 'disabled', language='fr')
        assert result.outcome == 'completed'
        primary = _primary(result, strategy=strategy)
        source, target = (BASE.cA, BASE.cB) if strategy == 'id' else (BASE[source_name], BASE[target_name])
        if reverse_direction:
            source, target = target, source
        _direction(result.ontology, primary, source, target)
        assert set(result.ontology.objects(primary, DCTERMS.identifier)) == ({Literal('tFocus')} if strategy == 'name' else set())
        fallbacks = {'participational': ('partEvent_wholeEvent', 'wholeEvent_partEvent'),
                     'manifestation': ('aspect_event', 'event_aspect'),
                     'mediation': ('relator_endurant', 'endurant_relator'),
                     'characterization': ('bearer_feature', 'feature_bearer'),
                     'externalDependence': ('mode_endurant', 'endurant_mode')}.get(
                         stereotype, ('endurant_event', 'event_endurant'))
        candidate = ('target_role' if branch == 'target_role' else
                     fallbacks[int(reverse_direction)] if branch == 'disabled' else
                     backward if reverse_direction else forward)
        if strategy == 'name':
            _candidate(result.ontology, primary, {candidate}, target_name if reverse_direction else source_name)
        labels = set(result.ontology.objects(primary, RDFS.label))
        if branch == 'target_role':
            assert labels == {Literal('target role', lang='fr')}
        elif label_mode == 'source-only':
            assert not labels
        else:
            assert labels == {Literal(candidate)}
        inverse = _primary(result, 'sFocus', strategy)
        _direction(result.ontology, inverse, target, source)
        assert (inverse, OWL.inverseOf, primary) in result.ontology
        assert set(result.ontology.objects(inverse, RDFS.label)) == {Literal('workers', lang='fr')}
        characteristic = PARTIAL_RELATION_CHARACTERISTICS.get(stereotype)
        assert ((primary, RDF.type, OWL.AsymmetricProperty) in result.ontology) == (characteristic == OWL.AsymmetricProperty)
        if characteristic is not None:
            assert (primary, RDF.type, characteristic) in result.ontology
        assert invoke.read_relation_stereotype_annotations(result, path) == ()
        if branch == 'semantic' and strategy == 'name':
            assert not any(d.kind in NAMING_KINDS for d in result.diagnostics)
        observations.append((result, path))
    # Check only after both directions, so all output/annotation checks run
    # even while production still lacks the independently required warning.
    for result, path in observations:
        _relation_limitation_warning(result)
        if stereotype in DEPENDENCY_RELATIONS:
            assert 'rFocus' in invoke.read_relation_limitation_source_ids(result, path)


@pytest.mark.parametrize('stereotype', ['participation', 'creation', 'termination', 'participational', 'manifestation'] + DEPENDENCY_RELATIONS)
@pytest.mark.parametrize('mode', ['all', 'none'])
def test_partial_semantic_relations_preserve_explicit_hierarchy_without_additional_output(
        run, invoke, source_json, tmp_path, stereotype, mode):
    """Rules: DK-REL-01, DK-REL-14, DK-INV-01, DK-INV-12, DK-DIAG-01, DK-GEN-11.

    RD-17 at 8bfc90fc40d732212ea84e583986c7ae0b96c65b. Canonical
    relations/hierarchy preserves asserted primary/available inverse hierarchy
    and independent annotations; no additional stereotype-only output.
    Registration fb05478031e290b123e766ad5188e4cef9935357 adds participational
    and manifestation while retaining the former's applicable existing asymmetry.
    Registration 490f209e0d70533bac56674e2844a7463fe77a09 adds the trio with
    their compatible existing primary characteristic, never further axioms.
    """
    document = source_json('relations/hierarchy')
    source_element(document, 'rLeaf')['stereotype'] = None
    options = dict(iri_strategy='id', inverse_properties=mode, stereotype_policy='allow-missing')
    assert not fixture_issues(document)
    ordinary = run(path=write_input(tmp_path, document, 'ordinary.json'), **options)
    source_element(document, 'rLeaf')['stereotype'] = stereotype
    assert not fixture_issues(document)
    path = write_input(tmp_path, document, 'stereotyped.json')
    result = run(path=path, **options)
    assert result.outcome == ordinary.outcome == 'completed'
    _, _, expected = _hierarchy_expected(result, 'id',
        {'General', 'Middle', 'Leaf', 'Sibling'} if mode == 'all' else set(),
        [('Middle', 'General'), ('Leaf', 'Middle'), ('Sibling', 'General')])
    assert _edges(result.ontology) == expected
    for identifier in ('cA', 'cB', 'cC', 'cD', 'tGeneral', 'tMiddle', 'tLeaf', 'tSibling') + (
            ('sGeneral', 'sMiddle', 'sLeaf', 'sSibling') if mode == 'all' else ()):
        for predicate in (RDFS.label, DCTERMS.identifier):
            assert set(result.ontology.objects(BASE[identifier], predicate)) == set(ordinary.ontology.objects(BASE[identifier], predicate))
    characteristic = PARTIAL_RELATION_CHARACTERISTICS.get(stereotype)
    expected_additions = ((BASE.tLeaf, RDF.type, characteristic),) if characteristic else ()
    _ordinary_relation_mapping_equal(ordinary, result, expected_additions=expected_additions)
    assert invoke.read_relation_stereotype_annotations(result, path) == ()
    assert _other_relation_diagnostics(result) == _other_relation_diagnostics(ordinary)
    _relation_limitation_warning(result)
    if stereotype in DEPENDENCY_RELATIONS:
        assert 'rLeaf' in invoke.read_relation_limitation_source_ids(result, path)


@pytest.mark.parametrize('mode', CHAIN_MODES)
@pytest.mark.parametrize('input_policy', POLICIES)
def test_participational_limitation_warning_survives_asymmetry_gate_under_every_policy(
        run, invoke, source_json, tmp_path, mode, input_policy):
    """Rules: DK-REL-01, DK-REL-07, DK-REL-09, DK-REL-11, DK-REL-14, DK-REL-15, DK-INV-01, DK-INV-04, DK-INV-12, DK-PROP-03, DK-DIAG-01, DK-DIAG-02, DK-DIAG-05, DK-GEN-11.

    RD-17 at fb05478031e290b123e766ad5188e4cef9935357: residual reporting
    survives generated and gate-omitted asymmetry under every input policy.
    Canonical relations/chain_constraints; accepted existing gate assertions
    run unchanged, with no repaired graph or inferred diagnostic count.
    """
    result, path = _assert_relation_axiom_gate(
        run, source_json, tmp_path, mode, 'participational', input_policy)
    # Compare with a real ordinary conversion of the same document. The sole
    # permitted logical difference is the pre-existing, compatible asymmetry.
    document = json.loads(path.read_bytes())
    source_element(document, 'rPeerTwo')['stereotype'] = None
    assert not fixture_issues(document)
    ordinary = run(path=write_input(tmp_path, document, 'ordinary-gate.json'), iri_strategy='id',
                   inverse_properties='all', material_property_chains=mode,
                   input_policy=input_policy, stereotype_policy='allow-missing')
    assert ordinary.outcome == result.outcome == 'completed'
    expected_additions = ((BASE.tPeerTwo, RDF.type, OWL.AsymmetricProperty),) if mode == 'none' else ()
    _ordinary_relation_mapping_equal(ordinary, result, expected_additions=expected_additions)
    assert invoke.read_relation_stereotype_annotations(result, path) == ()
    assert _other_relation_diagnostics(result) == _other_relation_diagnostics(ordinary)
    _relation_limitation_warning(result)


@pytest.mark.parametrize('stereotype', DEPENDENCY_RELATIONS)
@pytest.mark.parametrize('mode', CHAIN_MODES)
@pytest.mark.parametrize('input_policy', POLICIES)
def test_dependency_residual_warnings_survive_accepted_axiom_gates(
        run, invoke, source_json, tmp_path, stereotype, mode, input_policy):
    """Rules: DK-REL-01, DK-REL-07, DK-REL-09, DK-REL-11, DK-REL-14, DK-REL-15, DK-INV-01, DK-INV-04, DK-INV-12, DK-PROP-03, DK-DIAG-01, DK-DIAG-02, DK-DIAG-05, DK-GEN-11.

    RD-17 registration 490f209e0d70533bac56674e2844a7463fe77a09.
    Canonical relations/chain_constraints: retain every original gate assertion
    across modes/policies and identify the affected relation from actual
    reported diagnostics, independently of another relation's warning.
    """
    case, relation_id = {
        'mediation': ('mediation', 'rPeer'),
        'characterization': ('characterization', 'rLeft'),
        'externalDependence': ('external_dependence', 'rRight'),
    }[stereotype]
    result, path = _assert_relation_axiom_gate(run, source_json, tmp_path, mode, case, input_policy)
    assert invoke.read_relation_stereotype_annotations(result, path) == ()
    _relation_limitation_warning(result)
    assert relation_id in invoke.read_relation_limitation_source_ids(result, path)


@pytest.mark.parametrize('grounding', GROUNDINGS)
@pytest.mark.parametrize('mode', CHAIN_MODES)
@pytest.mark.parametrize('input_policy', POLICIES)
def test_dependency_residual_warnings_survive_material_chain_generation(
        run, invoke, source_json, tmp_path, grounding, mode, input_policy):
    """Rules: DK-REL-01, DK-REL-07, DK-REL-09, DK-REL-10, DK-REL-11, DK-INV-01, DK-INV-04, DK-DIAG-01, DK-DIAG-05, DK-GEN-11.

    RD-17 registration 490f209e0d70533bac56674e2844a7463fe77a09.
    Canonical shared/material_pattern preserves grounding, ordered chains,
    accepted characteristics/disjointness and mode-specific counts. Actual
    warnings must identify both grounding relations, including both mediations
    in the relator variant. A consolidated warning may cover both.
    """
    result, path = _assert_chain_body_additions(run, source_json, tmp_path, grounding, mode, input_policy)
    assert invoke.read_relation_stereotype_annotations(result, path) == ()
    _relation_limitation_warning(result)
    assert {'rLeft', 'rRight'} <= invoke.read_relation_limitation_source_ids(result, path)


def _assert_event_situation_mapping_equal(ordinary, stereotyped, *, property_iris=None):
    """Compare matched ordinary graphs after allowing the selected lexical IRIs."""
    def mapping(graph, iris):
        projected = Graph()
        for subject, predicate, value in graph:
            # Independently generated execution dates may vary across runs.
            if (predicate in {DCTERMS.created, DCTERMS.modified}
                    and isinstance(value, Literal) and value.datatype == XSD.dateTime):
                continue
            projected.add(tuple(iris.get(term, term) for term in (subject, predicate, value)))
        return projected

    actual = mapping(stereotyped, {})
    expected = mapping(ordinary, property_iris or {})
    predicates = set(actual.predicates()) | set(expected.predicates())
    assert_selected_equal(actual, expected, predicates, unordered_predicates={OWL.disjointWith})


@pytest.mark.parametrize('stereotype,source_kind,source_name,target_kind,target_name,semantic_name,fallback_name', [
    pytest.param('bringsAbout', 'event', 'Event', 'situation', 'Situation',
                 'bringsAbout', 'event_situation', id='bringsAbout'),
    pytest.param('triggers', 'situation', 'Situation', 'event', 'Event',
                 'triggers', 'situation_event', id='triggers'),
])
@pytest.mark.parametrize('input_policy,naming_disabled', [
    *(pytest.param(policy, False, id=policy) for policy in POLICIES),
    pytest.param('strict', True, id='strict-naming-disabled'),
])
def test_remaining_event_relations_report_nonfatal_residual_warning(
        run, invoke, source_json, tmp_path, stereotype, source_kind, source_name,
        target_kind, target_name, semantic_name, fallback_name, input_policy, naming_disabled):
    """Rules: DK-CLS-04, DK-DIAG-01, DK-DIAG-05, DK-DIAG-06, DK-GEN-03, DK-GEN-11, DK-INV-01, DK-INV-03, DK-INV-04, DK-INV-05, DK-INV-07, DK-IRI-06, DK-LBL-01, DK-LBL-02, DK-PROP-02, DK-PROP-04, DK-REL-01, DK-REL-02, DK-REL-03, DK-REL-04, DK-REL-06, DK-REL-09, DK-REL-10, DK-REL-11.

    RD-17 registration 490f209e0d70533bac56674e2844a7463fe77a09 applies the
    owner's warning-consistency direction. Registration
    2521e3bde7e26ac06b3abd0b879d165babe07793 settles ordinary graph treatment.
    Complete shared/binary_relation variants preserve independent annotations
    and axioms. Require the unique workers inverse in both conversions and
    align their primary IRIs after checking their lexical candidates.
    Naming-disabled warnings may share one diagnostic.
    """
    document = source_json('shared/binary_relation')
    source_element(document, 'cA').update(stereotype=source_kind, name=source_name)
    source_element(document, 'cB').update(stereotype=target_kind, name=target_name)
    description = f'The author mentions {stereotype} in this description.'
    source_element(document, 'rFocus').update(stereotype=None, name=None, description=description)
    source_element(document, 'tFocus').update(
        name=None, description='Target-end description.', cardinality='2..5', aggregationKind='SHARED')
    source_element(document, 'sFocus').update(description='Source-end description.', cardinality='1')
    naming_options = {'no_stereotype_relation_naming': True} if naming_disabled else {}
    assert not fixture_issues(document)
    ordinary = run(path=write_input(tmp_path, document, 'ordinary.json'), input_policy=input_policy,
                   stereotype_policy='allow-missing', **naming_options)
    source_element(document, 'rFocus')['stereotype'] = stereotype
    assert not fixture_issues(document)
    path = write_input(tmp_path, document)
    result = run(path=path, input_policy=input_policy, stereotype_policy='require-known', **naming_options)
    assert result.outcome == ordinary.outcome == 'completed'

    graph = result.ontology
    primary = _primary(result, strategy='name')
    inverse = _primary(result, 'sFocus', 'name')
    source, target = BASE[source_name], BASE[target_name]
    _candidate(graph, primary, {fallback_name if naming_disabled else semantic_name}, source_name)
    assert inverse == BASE.workers
    _direction(graph, primary, source, target)
    _chain_inverse(graph, inverse, primary)
    _counts(graph, source, primary, {('min', 2), ('max', 5)})
    _counts(graph, target, inverse, {('exact', 1)})
    assert {frozenset(pair) for pair in graph.subject_objects(OWL.disjointWith)} == {frozenset((source, target))}
    assert not list(graph.objects(primary, RDFS.label))
    assert set(graph.objects(inverse, RDFS.label)) == {Literal('workers')}
    assert (primary, RDFS.comment, Literal(description)) in graph
    assert (primary, RDFS.comment, Literal('Target-end description.')) in graph
    assert (inverse, RDFS.comment, Literal('Source-end description.')) in graph

    ordinary_primary = _primary(ordinary, strategy='name')
    _candidate(ordinary.ontology, ordinary_primary, {fallback_name}, source_name)
    assert _primary(ordinary, 'sFocus', 'name') == BASE.workers
    _assert_event_situation_mapping_equal(
        ordinary.ontology, graph, property_iris={ordinary_primary: primary})
    comments = invoke.read_relation_aggregation_comments(result, path)
    assert {(comment.subject, comment.context, comment.value) for comment in comments} == {
        (primary, 'target_end', 'SHARED'),
    }

    if naming_disabled:
        _source_target_naming_warning(result, 'rFocus')
    else:
        assert not any(d.kind in NAMING_KINDS for d in result.diagnostics)
    _relation_limitation_warning(result)
    assert 'rFocus' in invoke.read_relation_limitation_source_ids(result, path)


@pytest.mark.parametrize('stereotype', ['bringsAbout', 'triggers'])
@pytest.mark.parametrize('inverse_mode', ['all', 'none'])
def test_event_situation_relations_preserve_explicit_hierarchy(
        run, invoke, source_json, tmp_path, stereotype, inverse_mode):
    """Rules: DK-DIAG-01, DK-DIAG-04, DK-DIAG-05, DK-GEN-11, DK-INV-01, DK-INV-03, DK-INV-04, DK-INV-07, DK-INV-12, DK-IRI-06, DK-LBL-01, DK-LBL-02, DK-PROP-02, DK-REL-01, DK-REL-02, DK-REL-14.

    RD-17 registration 2521e3bde7e26ac06b3abd0b879d165babe07793.
    Canonical relations/hierarchy variant with event and situation endpoints.
    Preserve the explicit primary and available inverse specialization edges,
    the authored leaf name, and the applicable source-end description. Check
    primary and inverse IRI pairs before alignment and require the residual
    warning for the authored relation.
    """
    document = source_json('relations/hierarchy')
    source_kind, target_kind = ('event', 'situation') if stereotype == 'bringsAbout' else ('situation', 'event')
    source_element(document, 'cC')['stereotype'] = source_kind
    source_element(document, 'cA')['stereotype'] = target_kind
    description = 'Leaf source-end description.'
    source_element(document, 'sLeaf')['description'] = description
    relation = source_element(document, 'rLeaf')
    relation['stereotype'] = None
    strategy = 'name' if inverse_mode == 'all' else 'id'
    options = dict(iri_strategy=strategy, inverse_properties=inverse_mode, stereotype_policy='allow-missing')
    assert not fixture_issues(document)
    ordinary = run(path=write_input(tmp_path, document, 'ordinary.json'), **options)
    relation['stereotype'] = stereotype
    assert not fixture_issues(document)
    path = write_input(tmp_path, document)
    result = run(path=path, **options)
    assert result.outcome == ordinary.outcome == 'completed'
    named = {'General', 'Middle', 'Leaf', 'Sibling'} if inverse_mode == 'all' else set()
    specializations = [('Middle', 'General'), ('Leaf', 'Middle'), ('Sibling', 'General')]
    primary, inverse, edges = _hierarchy_expected(result, strategy, named, specializations)
    graph = result.ontology
    assert _edges(graph) == edges
    assert set(graph.objects(primary['Leaf'], RDFS.label)) == {Literal('leaf')}
    property_iris = {}
    if inverse_mode == 'all':
        _direction(graph, primary['Leaf'], BASE.C, BASE.A)
        assert set(graph.subjects(RDFS.comment, Literal(description))) == {inverse['Leaf']}
        ordinary_primary, ordinary_inverse, _ = _hierarchy_expected(ordinary, strategy, named, specializations)
        # The four workers role candidates collide. Each inverse uses the
        # resolved primary local name, including any source qualifier.
        for key, source_name in (('General', 'A'), ('Middle', 'B'), ('Leaf', 'C'), ('Sibling', 'D')):
            allowed_pairs = {
                (BASE[key.lower()], BASE[f'inverseOf{key}']),
                (BASE[f'{key.lower()}_{source_name}'], BASE[f'inverseOf{key}_{source_name}']),
            }
            assert (primary[key], inverse[key]) in allowed_pairs
            assert (ordinary_primary[key], ordinary_inverse[key]) in allowed_pairs
            property_iris[ordinary_primary[key]] = primary[key]
            property_iris[ordinary_inverse[key]] = inverse[key]
    else:
        _direction(graph, primary['Leaf'], BASE.cC, BASE.cA)
        assert not list(graph.subjects(RDFS.comment, Literal(description)))
    _assert_event_situation_mapping_equal(ordinary.ontology, graph, property_iris=property_iris)
    assert invoke.read_relation_stereotype_annotations(result, path) == ()
    _relation_limitation_warning(result)
    assert 'rLeaf' in invoke.read_relation_limitation_source_ids(result, path)


@pytest.mark.parametrize('strategy,mode,input_policy', [
    pytest.param('id', 'all', 'strict', id='id-all-strict'),
    pytest.param('name', 'none', 'tolerant', id='name-none-tolerant'),
    pytest.param('id', 'none', 'best-effort', id='id-none-best-effort'),
])
def test_historical_dependence_preserves_ordinary_mapping_and_applicable_diagnostics(
        run, invoke, source_json, tmp_path, strategy, mode, input_policy):
    """Rules: DK-REL-01, DK-REL-02, DK-REL-09, DK-REL-10, DK-REL-11, DK-LBL-01, DK-LBL-02, DK-IRI-06, DK-IRI-09, DK-INV-01, DK-INV-04, DK-PROP-04, DK-PROP-05, DK-PROP-06, DK-DIAG-01, DK-DIAG-18, DK-GEN-11.

    RD-17 historicalDependence Alternative A: naming success does not suppress
    the limitation warning. Author descriptions may themselves name the
    stereotype; the omission must not erase that independent source text.
    """
    document = source_json('shared/binary_relation')
    document['languages'] = ['nl']
    source_element(document, 'cA')['stereotype'] = 'historicalRole'
    source_element(document, 'cB')['stereotype'] = 'kind'
    source_element(document, 'rFocus').update(
        name='History link', stereotype=None,
        description='The author describes historicalDependence here.')
    source_element(document, 'tFocus').update(
        description='Target-end description.', cardinality='2..5', isReadOnly=True, stereotype='end')
    source_element(document, 'sFocus').update(
        name='antecedents', description='Source-end description.', cardinality='1', isOrdered=True, stereotype='begin')
    language = 'fr' if strategy == 'name' else None
    options = dict(iri_strategy=strategy, inverse_properties=mode, input_policy=input_policy,
                   stereotype_policy='allow-missing', language=language)
    assert not fixture_issues(document)
    ordinary = run(path=write_input(tmp_path, document, 'ordinary.json'), **options)
    source_element(document, 'rFocus')['stereotype'] = 'historicalDependence'
    assert not fixture_issues(document)
    path = write_input(tmp_path, document, 'historical.json')
    result = run(path=path, **options)
    assert ordinary.outcome == result.outcome == 'completed'
    primary = _primary(result, strategy=strategy)
    assert primary == _primary(ordinary, strategy=strategy)
    source = BASE.cA if strategy == 'id' else BASE.HTTPServer
    target = BASE.cB if strategy == 'id' else BASE.XMLNode
    _direction(result.ontology, primary, source, target)
    assert set(result.ontology.objects(primary, DCTERMS.identifier)) == ({Literal('tFocus')} if strategy == 'name' else set())
    tag = language or 'nl'
    assert set(result.ontology.objects(primary, RDFS.label)) == {Literal('History link', lang=tag)}
    for text in ('The author describes historicalDependence here.', 'Target-end description.'):
        assert (primary, RDFS.comment, Literal(text, lang=tag)) in result.ontology
    inverse = _primary(result, 'sFocus', strategy) if mode == 'all' else ('inverse', primary)
    _counts(result.ontology, source, primary, {('min', 2), ('max', 5)})
    _counts(result.ontology, target, inverse, {('exact', 1)})
    if mode == 'all':
        _direction(result.ontology, inverse, target, source)
        assert (inverse, OWL.inverseOf, primary) in result.ontology
        assert (primary, OWL.inverseOf, inverse) not in result.ontology
        assert set(result.ontology.objects(inverse, DCTERMS.identifier)) == ({Literal('sFocus')} if strategy == 'name' else set())
        assert set(result.ontology.objects(inverse, RDFS.label)) == {Literal('antecedents', lang=tag)}
        assert (inverse, RDFS.comment, Literal('Source-end description.', lang=tag)) in result.ontology
    else:
        assert not any(isinstance(node, URIRef) for node in result.ontology.subjects(OWL.inverseOf, primary))
        assert not list(result.ontology.subjects(RDFS.comment, Literal('Source-end description.', lang=tag)))
    # Independent comments are preserved without requiring a prose template.
    assert set(ordinary.ontology.objects(_primary(ordinary, strategy=strategy), RDFS.comment)) <= set(
        result.ontology.objects(primary, RDFS.comment))
    _ordinary_relation_mapping_equal(ordinary, result)
    assert invoke.read_historical_dependence_annotations(result, path) == ()
    assert _other_relation_diagnostics(result) == _other_relation_diagnostics(ordinary)
    assert any(d.kind == 'ordering' and d.severity == 'INFO' for d in result.diagnostics)
    _relation_limitation_warning(result)


@pytest.mark.parametrize('branch,strategy,label_mode', [
    pytest.param('target_role', 'name', 'source-only', id='target_role-name-source-only'),
    pytest.param('target_role', 'id', 'generated', id='target_role-id-generated'),
    pytest.param('semantic', 'name', 'source-only', id='semantic-name-source-only'),
    pytest.param('semantic', 'name', 'generated', id='semantic-name-generated'),
    pytest.param('semantic', 'id', 'source-only', id='semantic-id-source-only'),
    pytest.param('semantic', 'id', 'generated', id='semantic-id-generated'),
    pytest.param('disabled', 'name', 'generated', id='disabled-name-generated'),
    pytest.param('disabled', 'id', 'generated', id='disabled-id-generated'),
])
def test_historical_dependence_keeps_lexical_naming_and_labels_without_stereotype_annotations(
        run, invoke, source_json, tmp_path, branch, strategy, label_mode):
    """Rules: DK-REL-01, DK-REL-02, DK-REL-03, DK-REL-04, DK-REL-06, DK-LBL-01, DK-LBL-02, DK-PROP-02, DK-IRI-06, DK-IRI-09, DK-INV-01, DK-INV-04, DK-DIAG-01, DK-GEN-11.

    A2 registration 4fdef7bbaf8b73bf1ed0ff47fc793494493083dc resolves
    the former bound: the semantic step uses dependent_antecedent. Preserve
    source precedence, generated labels and the historical limitation warning.
    """
    document = source_json('shared/binary_relation')
    document['languages'] = ['nl']
    source_element(document, 'cA').update(name='Dependent', stereotype='historicalRole')
    source_element(document, 'cB').update(name='Antecedent', stereotype='kind')
    source_element(document, 'rFocus').update(name=None, stereotype='historicalDependence')
    source_element(document, 'tFocus')['name'] = 'historical role' if branch == 'target_role' else None
    assert not fixture_issues(document)
    path = write_input(tmp_path, document)
    result = run(path=path, iri_strategy=strategy, inverse_properties='named',
                 relation_labels=label_mode, no_stereotype_relation_naming=branch == 'disabled', language='fr')
    assert result.outcome == 'completed'
    primary = _primary(result, strategy=strategy)
    _direction(result.ontology, primary, BASE.cA if strategy == 'id' else BASE.Dependent,
               BASE.cB if strategy == 'id' else BASE.Antecedent)
    assert set(result.ontology.objects(primary, DCTERMS.identifier)) == ({Literal('tFocus')} if strategy == 'name' else set())
    candidates = ({'historical_role'} if branch == 'target_role' else
                  {'dependent_antecedent'})
    if strategy == 'name': _candidate(result.ontology, primary, candidates, 'Dependent')
    labels = set(result.ontology.objects(primary, RDFS.label))
    if branch == 'target_role':
        assert labels == {Literal('historical role', lang='fr')}
    elif label_mode == 'source-only':
        assert not labels
    else:
        assert len(labels) == 1
        label = next(iter(labels))
        assert label.language is None and str(label) in candidates
        if strategy == 'name': _candidate(result.ontology, primary, {str(label)}, 'Dependent')
    inverse = _primary(result, 'sFocus', strategy)
    assert (inverse, OWL.inverseOf, primary) in result.ontology
    assert set(result.ontology.objects(inverse, RDFS.label)) == {Literal('workers', lang='fr')}
    assert invoke.read_historical_dependence_annotations(result, path) == ()
    # The condition is the semantic limitation, independent of primary naming,
    # ID strategy, label mode, or disabled stereotype-derived naming.
    if strategy == 'name':
        assert any(d.kind == 'relation_naming' and d.severity == 'WARNING' for d in result.diagnostics)
    _relation_limitation_warning(result)


@pytest.mark.parametrize('mode', ['all', 'none'])
def test_historical_dependence_preserves_explicit_relation_hierarchy(run, invoke, source_json, tmp_path, mode):
    """Rules: DK-REL-01, DK-REL-14, DK-INV-01, DK-INV-12, DK-DIAG-01, DK-GEN-11.

    RD-17 historicalDependence Alternative A retains asserted primary and
    available named-inverse generalizations, without temporal repair axioms.
    """
    document = source_json('relations/hierarchy')
    source_element(document, 'rLeaf')['stereotype'] = None
    options = dict(iri_strategy='id', inverse_properties=mode, stereotype_policy='allow-missing')
    assert not fixture_issues(document)
    ordinary = run(path=write_input(tmp_path, document, 'ordinary.json'), **options)
    source_element(document, 'rLeaf')['stereotype'] = 'historicalDependence'
    assert not fixture_issues(document)
    path = write_input(tmp_path, document, 'historical.json')
    result = run(path=path, **options)
    assert result.outcome == ordinary.outcome == 'completed'
    _, _, expected = _hierarchy_expected(result, 'id',
        {'General', 'Middle', 'Leaf', 'Sibling'} if mode == 'all' else set(),
        [('Middle', 'General'), ('Leaf', 'Middle'), ('Sibling', 'General')])
    assert _edges(result.ontology) == expected
    # Label/identifier preservation is independent of the annotation audit and
    # of metadata on unrelated resources; do not hide extra declaration labels.
    for identifier in ('cA', 'cB', 'cC', 'cD', 'tGeneral', 'tMiddle', 'tLeaf', 'tSibling') + (
            ('sGeneral', 'sMiddle', 'sLeaf', 'sSibling') if mode == 'all' else ()):
        for predicate in (RDFS.label, DCTERMS.identifier):
            assert set(result.ontology.objects(BASE[identifier], predicate)) == set(
                ordinary.ontology.objects(BASE[identifier], predicate))
    _ordinary_relation_mapping_equal(ordinary, result)
    assert invoke.read_historical_dependence_annotations(result, path) == ()
    assert _other_relation_diagnostics(result) == _other_relation_diagnostics(ordinary)
    _relation_limitation_warning(result)


def _apply_relation_set_categorizer(document, defect):
    """Apply one explicit non-null categorizer condition to gsRelations."""
    affected = source_element(document, 'gsRelations')
    affected.update(isComplete=True, isDisjoint=True)
    expected_issues = frozenset()
    if defect in {'valid_class_ordinary', 'valid_class_powertype'}:
        rel_type = copy.deepcopy(source_element(document, 'cA'))
        rel_type.update(id='cRelType', name='RelationType', stereotype='type',
                        isPowertype=(defect == 'valid_class_powertype'))
        document['model']['contents'].append(rel_type)
        affected['categorizer'] = {'id': 'cRelType', 'type': 'Class'}
    elif defect == 'omitted_class':
        rel_type = copy.deepcopy(source_element(document, 'cA'))
        rel_type.update(id=None, name='RelationType', stereotype='type', isPowertype=True)
        document['model']['contents'].append(rel_type)
        affected['categorizer'] = {'id': 'cRelType', 'type': 'Class'}
        expected_issues = frozenset({'invalid_id', 'unresolved_reference:cRelType'})
    elif defect == 'primitive_datatype':
        datatype = copy.deepcopy(source_element(document, 'cA'))
        datatype.update(id='dString', name='string', stereotype='datatype', isPowertype=True)
        document['model']['contents'].append(datatype)
        affected['categorizer'] = {'id': 'dString', 'type': 'Class'}
    elif defect == 'void_datatype':
        void_cls = copy.deepcopy(source_element(document, 'cA'))
        void_cls.update(id='dVoid', name='void', stereotype='datatype', isPowertype=True)
        document['model']['contents'].append(void_cls)
        affected['categorizer'] = {'id': 'dVoid', 'type': 'Class'}
    elif defect == 'dangling_id':
        affected['categorizer'] = {'id': 'missingCategorizer', 'type': 'Class'}
        expected_issues = frozenset({'unresolved_reference:missingCategorizer'})
    elif defect == 'type_mismatch':
        rel_type = copy.deepcopy(source_element(document, 'cA'))
        rel_type.update(id='cRelType', name='RelationType', stereotype='type', isPowertype=True)
        document['model']['contents'].append(rel_type)
        affected['categorizer'] = {'id': 'cRelType', 'type': 'Relation'}
        expected_issues = frozenset({'reference_type_mismatch:cRelType'})
    elif defect == 'non_class_generalization':
        affected['categorizer'] = {'id': 'gMiddle', 'type': 'Generalization'}
    elif defect == 'non_class_property':
        source_element(document, 'cA')['properties'] = [{
            'id': 'aTag', 'name': 'tag', 'description': None, 'type': 'Property',
            'propertyAssignments': None, 'stereotype': None, 'isDerived': False,
            'isReadOnly': False, 'isOrdered': False, 'cardinality': None,
            'propertyType': None, 'subsettedProperties': None,
            'redefinedProperties': None, 'aggregationKind': None,
        }]
        affected['categorizer'] = {'id': 'aTag', 'type': 'Property'}
    elif defect == 'non_class_relation':
        affected['categorizer'] = {'id': 'rMiddle', 'type': 'Relation'}
    elif defect == 'non_class_package':
        affected['categorizer'] = {'id': 'hierarchyProjectRoot', 'type': 'Package'}
        expected_issues = frozenset({'unresolved_reference:hierarchyProjectRoot'})
    elif defect == 'malformed_string':
        affected['categorizer'] = 'cRelType'
        expected_issues = frozenset({'malformed_reference'})
    elif defect == 'malformed_number':
        affected['categorizer'] = 1
        expected_issues = frozenset({'malformed_reference'})
    elif defect == 'malformed_boolean':
        affected['categorizer'] = False
        expected_issues = frozenset({'malformed_reference'})
    elif defect == 'malformed_array':
        affected['categorizer'] = [{'id': 'cRelType', 'type': 'Class'}]
        expected_issues = frozenset({'malformed_reference'})
    elif defect == 'malformed_missing_id':
        affected['categorizer'] = {'type': 'Class'}
        expected_issues = frozenset({'malformed_reference'})
    elif defect == 'malformed_missing_type':
        affected['categorizer'] = {'id': 'cRelType'}
        expected_issues = frozenset({'malformed_reference'})
    elif defect == 'malformed_empty_id':
        affected['categorizer'] = {'id': '', 'type': 'Class'}
        expected_issues = frozenset({'invalid_reference_id'})
    elif defect == 'malformed_non_utf8_id':
        affected['categorizer'] = {'id': '\ud800', 'type': 'Class'}
        expected_issues = frozenset({'invalid_reference_id'})
    else:
        raise AssertionError(f'Unlisted relation-set categorizer defect: {defect}')
    return expected_issues


def _assert_inapplicable_relation_categorizer_error(diagnostics, set_id='gsRelations'):
    assert any(
        event.severity == 'ERROR'
        and set_id in event.identified_sources
        and 'inapplicable_relation_categorizer' in event.facts
        and event.code
        and event.code not in STABLE_DIAGNOSTIC_CODES
        for event in diagnostics
    ), diagnostics


@pytest.mark.parametrize('input_policy', POLICIES)
@pytest.mark.parametrize('categorizer_state', ['absent', 'null'])
@pytest.mark.parametrize('singleton', [False, True], ids=['multi_member', 'singleton'])
def test_absent_or_null_categorizer_on_relation_set_remains_uncategorized_without_error(
        run, source_json, tmp_path, input_policy, categorizer_state, singleton):
    """Rules: DK-HO-04, DK-REL-14, DK-REL-15, DK-REL-16, DK-REL-20, DK-INV-12, DK-DIAG-05, DK-DIAG-14.

    RD-02 Alternative A, cc562c49a8274367e3a52d95c368abb484bfa713. Absent and
    explicit null categorizers on relation sets remain uncategorized with no error.
    """
    document = source_json('relations/hierarchy')
    affected = source_element(document, 'gsRelations')
    affected.update(isComplete=True, isDisjoint=True)
    if singleton:
        affected['generalizations'] = affected['generalizations'][:1]
    if categorizer_state == 'absent':
        del affected['categorizer']
    else:
        affected['categorizer'] = None
    assert fixture_issues(document) == frozenset()

    result = run(path=write_input(tmp_path, document), iri_strategy='id', input_policy=input_policy)
    assert result.outcome == 'completed'
    assert not any(event.severity == 'ERROR' or 'inapplicable_relation_categorizer' in event.facts
                   for event in result.diagnostics)
    edges = [('Middle', 'General'), ('Leaf', 'Middle'), ('Sibling', 'General')] + (
        [('General', 'Middle')] if singleton else [])
    _, _, expected = _hierarchy_expected(result, 'id', {'General', 'Middle', 'Leaf', 'Sibling'}, edges)
    assert _edges(result.ontology) == expected
    expected_pairs = set() if singleton else {
        frozenset((BASE.tMiddle, BASE.tSibling)), frozenset((BASE.sMiddle, BASE.sSibling))}
    assert _pairs(result.ontology) == expected_pairs
    assert not list(result.ontology.subjects(RDF.type, OWL.NamedIndividual))
    assert not any(BASE.gsRelations in triple for triple in result.ontology)
    if singleton:
        assert any(event.kind == 'singleton_completeness' and event.severity == 'INFO'
                   and {'gsRelations', 'rGeneral', 'rMiddle'} <= set(event.identified_sources)
                   and {'extensional_equivalence', 'distinct_identifiers'} <= event.facts
                   for event in result.diagnostics)
    else:
        assert any(event.kind == 'relation_set_completeness' and event.severity == 'WARNING'
                   and 'gsRelations' in event.identified_sources
                   and 'coverage_not_represented' in event.facts
                   for event in result.diagnostics)


@pytest.mark.parametrize('input_policy', POLICIES)
@pytest.mark.parametrize('inverse_mode', ['all', 'none'])
@pytest.mark.parametrize('defect', [
    'valid_class_ordinary', 'valid_class_powertype', 'omitted_class',
    'primitive_datatype', 'void_datatype',
    'dangling_id', 'type_mismatch',
    'non_class_generalization', 'non_class_property', 'non_class_relation', 'non_class_package',
    'malformed_string', 'malformed_number', 'malformed_boolean', 'malformed_array',
    'malformed_missing_id', 'malformed_missing_type', 'malformed_empty_id', 'malformed_non_utf8_id',
])
def test_non_null_categorizer_on_relation_set_aborts_or_omits_categorizer_while_keeping_disjointness_and_warning(
        run, source_json, tmp_path, input_policy, inverse_mode, defect):
    """Rules: DK-HO-02, DK-HO-03, DK-HO-04, DK-REL-14, DK-REL-15, DK-REL-16, DK-INV-12, DK-CLS-01, DK-ATT-01, DK-DAT-01, DK-DIAG-05.

    RD-02 Alternative A, cc562c49a8274367e3a52d95c368abb484bfa713. Exercises
    valid classes, datatypes without local classes, non-Class declarations,
    unresolved references, and malformed values on a relation generalization set.
    """
    document = source_json('relations/hierarchy')
    expected_issues = _apply_relation_set_categorizer(document, defect)
    assert fixture_issues(document) == expected_issues
    path = write_input(tmp_path, document, ensure_ascii=(defect == 'malformed_non_utf8_id'))
    if defect == 'malformed_non_utf8_id':
        assert json.loads(path.read_bytes()) == document

    result = run(path=path, iri_strategy='id', inverse_properties=inverse_mode, input_policy=input_policy)
    if defect == 'omitted_class':
        assert any(event.severity == 'ERROR' and event.kind == 'invalid_id' for event in result.diagnostics)
        if input_policy != 'best-effort':
            assert result.outcome == 'aborted' and result.ontology is None and result.provenance is None
            return
    _assert_inapplicable_relation_categorizer_error(result.diagnostics)
    assert not any(event.kind == 'singleton_completeness' for event in result.diagnostics)
    if input_policy != 'best-effort':
        assert result.outcome == 'aborted' and result.ontology is None and result.provenance is None
        return

    assert result.outcome == 'completed-with-errors'
    graph = result.ontology
    assert isinstance(graph, Graph)
    named = {'General', 'Middle', 'Leaf', 'Sibling'} if inverse_mode == 'all' else set()
    _, _, expected = _hierarchy_expected(
        result, 'id', named, [('Middle', 'General'), ('Leaf', 'Middle'), ('Sibling', 'General')])
    assert _edges(graph) == expected
    expected_pairs = {frozenset((BASE.tMiddle, BASE.tSibling))}
    if inverse_mode == 'all':
        expected_pairs.add(frozenset((BASE.sMiddle, BASE.sSibling)))
    assert _pairs(graph) == expected_pairs
    assert any(event.kind == 'relation_set_completeness' and event.severity == 'WARNING'
               and 'gsRelations' in event.identified_sources
               and 'coverage_not_represented' in event.facts
               for event in result.diagnostics)
    expected_classes = {BASE.cA, BASE.cB, BASE.cC, BASE.cD}
    if defect in {'valid_class_ordinary', 'valid_class_powertype', 'type_mismatch'}:
        expected_classes.add(BASE.cRelType)
    assert {s for s in graph.subjects(RDF.type, OWL.Class) if isinstance(s, URIRef)} == expected_classes
    assert not list(graph.subjects(RDF.type, OWL.NamedIndividual))
    assert not list(graph.subjects(RDF.type, BASE.cRelType))
    for prefix in ('t', 's'):
        for key in ('General', 'Middle', 'Leaf', 'Sibling'):
            prop = BASE[prefix + key]
            expected_types = {OWL.ObjectProperty} if (prefix == 't' or inverse_mode == 'all') else set()
            assert set(graph.objects(prop, RDF.type)) == expected_types
    for predicate in (OWL.equivalentProperty, OWL.unionOf, OWL.disjointUnionOf):
        assert not list(graph.triples((None, predicate, None)))
    assert not any(BASE.gsRelations in triple for triple in graph)
    if defect == 'dangling_id':
        assert not any(BASE.missingCategorizer in triple for triple in graph)
    elif defect == 'non_class_property':
        assert (BASE.aTag, RDF.type, OWL.DatatypeProperty) in graph
        assert (BASE.aTag, RDFS.domain, BASE.cA) in graph
        assert not list(graph.subjects(RDF.type, BASE.aTag))
    elif defect == 'non_class_package':
        assert not any(BASE.hierarchyProjectRoot in triple for triple in graph)
    elif defect == 'primitive_datatype':
        assert not any(term in {BASE.dString, XSD.string} for triple in graph for term in triple)
    elif defect == 'void_datatype':
        assert not any(BASE.dVoid in triple or 'void' in str(term).casefold()
                       for triple in graph for term in triple)
    elif defect == 'omitted_class':
        assert not any(BASE.cRelType in triple for triple in graph)


@pytest.mark.parametrize('iri_strategy', ['id', 'name'])
@pytest.mark.parametrize('powertype', [False, True], ids=['ordinary', 'powertype'])
@pytest.mark.parametrize('is_complete', [True, False], ids=['complete', 'open'])
def test_non_null_categorizer_on_relation_set_preserves_name_mode_and_independent_class_classifications(
        run, source_json, tmp_path, iri_strategy, powertype, is_complete):
    """Rules: DK-HO-01, DK-HO-02, DK-HO-03, DK-HO-04, DK-REL-14, DK-REL-15, DK-REL-16, DK-INV-12, DK-IRI-02, DK-IRI-09, DK-DIAG-05.

    RD-02 Alternative A, cc562c49a8274367e3a52d95c368abb484bfa713. A separate
    valid categorized class set using the same Class retains its ordinary or
    powertype classifications while gsRelations omits only property-typing output.
    """
    document = source_json('relations/hierarchy')
    rel_type = copy.deepcopy(source_element(document, 'cA'))
    rel_type.update(id='cRelType', name='RelationType', stereotype='type', isPowertype=powertype)
    cls_base = copy.deepcopy(source_element(document, 'cA'))
    cls_base.update(id='cClsBase', name='EntityBase')
    cls_one = copy.deepcopy(source_element(document, 'cA'))
    cls_one.update(id='cClsOne', name='EntityOne', stereotype='kind')
    cls_two = copy.deepcopy(source_element(document, 'cA'))
    cls_two.update(id='cClsTwo', name='EntityTwo', stereotype='kind')
    g_cls_one = {
        'id': 'gClsOne', 'name': None, 'description': None, 'type': 'Generalization',
        'propertyAssignments': None, 'specific': {'id': 'cClsOne', 'type': 'Class'},
        'general': {'id': 'cClsBase', 'type': 'Class'},
    }
    g_cls_two = {
        'id': 'gClsTwo', 'name': None, 'description': None, 'type': 'Generalization',
        'propertyAssignments': None, 'specific': {'id': 'cClsTwo', 'type': 'Class'},
        'general': {'id': 'cClsBase', 'type': 'Class'},
    }
    gs_class = {
        'id': 'gsClass', 'name': 'ClassKinds', 'description': None, 'type': 'GeneralizationSet',
        'propertyAssignments': None, 'isDisjoint': False, 'isComplete': False,
        'categorizer': {'id': 'cRelType', 'type': 'Class'},
        'generalizations': [{'id': 'gClsOne', 'type': 'Generalization'}],
    }
    document['model']['contents'].extend([rel_type, cls_base, cls_one, cls_two, g_cls_one, g_cls_two, gs_class])
    source_element(document, 'gsRelations').update(
        isComplete=is_complete, isDisjoint=True, categorizer={'id': 'cRelType', 'type': 'Class'})
    assert fixture_issues(document) == frozenset()

    result = run(path=write_input(tmp_path, document), iri_strategy=iri_strategy, input_policy='best-effort')
    assert result.outcome == 'completed-with-errors'
    _assert_inapplicable_relation_categorizer_error(result.diagnostics)
    graph = result.ontology
    assert isinstance(graph, Graph)
    iris = {
        key: BASE[key if iri_strategy == 'id' else name]
        for key, name in (('cA', 'A'), ('cB', 'B'), ('cC', 'C'), ('cD', 'D'),
                          ('cRelType', 'RelationType'), ('cClsBase', 'EntityBase'),
                          ('cClsOne', 'EntityOne'), ('cClsTwo', 'EntityTwo'))
    }
    assert {s for s in graph.subjects(RDF.type, OWL.Class) if isinstance(s, URIRef)} == set(iris.values())
    expected_classified = {iris['cClsBase'], iris['cClsOne'], iris['cClsTwo']} if powertype else {iris['cClsOne']}
    assert set(graph.subjects(RDF.type, iris['cRelType'])) == expected_classified
    assert set(graph.subjects(RDF.type, OWL.NamedIndividual)) == expected_classified
    for cls_id in ('cA', 'cB', 'cC', 'cD'):
        assert set(graph.objects(iris[cls_id], RDF.type)) == {OWL.Class}
    _, _, expected_edges = _hierarchy_expected(
        result, iri_strategy, {'General', 'Middle', 'Leaf', 'Sibling'},
        [('Middle', 'General'), ('Leaf', 'Middle'), ('Sibling', 'General')])
    assert _edges(graph) == expected_edges
    t_middle, t_sibling = _primary(result, 'tMiddle', iri_strategy), _primary(result, 'tSibling', iri_strategy)
    s_middle, s_sibling = _primary(result, 'sMiddle', iri_strategy), _primary(result, 'sSibling', iri_strategy)
    assert _pairs(graph) == {frozenset((t_middle, t_sibling)), frozenset((s_middle, s_sibling))}
    completeness_warnings = [event for event in result.diagnostics if event.kind == 'relation_set_completeness']
    if is_complete:
        assert any(event.severity == 'WARNING' and 'gsRelations' in event.identified_sources
                   for event in completeness_warnings)
    else:
        assert not completeness_warnings
    assert not any(BASE.gsRelations in triple for triple in graph)
    if iri_strategy == 'name':
        assert not list(graph.subjects(DCTERMS.identifier, Literal('gsRelations')))


@pytest.mark.parametrize('repeated', [False, True], ids=['single_ref', 'repeated_ref'])
@pytest.mark.parametrize('inverse_mode', ['all', 'none'])
@pytest.mark.parametrize('categorizer_kind', [
    'valid_class_ordinary', 'valid_class_powertype', 'dangling_id', 'primitive_datatype', 'malformed_string',
])
def test_non_null_categorizer_on_singleton_relation_set_preserves_completeness_and_info(
        run, source_json, tmp_path, repeated, inverse_mode, categorizer_kind):
    """Rules: DK-HO-02, DK-HO-03, DK-HO-04, DK-GEN-12, DK-REL-14, DK-REL-15, DK-REL-20, DK-INV-12, DK-DIAG-05, DK-DIAG-14.

    RD-02 Alternative A, cc562c49a8274367e3a52d95c368abb484bfa713. A non-null
    categorizer alone must not suppress DK-REL-20 singleton completeness or its
    DK-DIAG-14 INFO diagnostic when membership is complete.
    """
    document = source_json('relations/hierarchy')
    expected_issues = _apply_relation_set_categorizer(document, categorizer_kind)
    affected = source_element(document, 'gsRelations')
    affected['generalizations'] = [{'id': 'gMiddle', 'type': 'Generalization'}] * (2 if repeated else 1)
    assert fixture_issues(document) == expected_issues

    result = run(path=write_input(tmp_path, document), iri_strategy='id',
                 inverse_properties=inverse_mode, input_policy='best-effort')
    assert result.outcome == 'completed-with-errors'
    _assert_inapplicable_relation_categorizer_error(result.diagnostics)
    singleton = [event for event in result.diagnostics if event.kind == 'singleton_completeness']
    assert singleton and all(event.severity == 'INFO' for event in singleton)
    assert any({'gsRelations', 'rGeneral', 'rMiddle'} <= set(event.identified_sources)
               and {'extensional_equivalence', 'distinct_identifiers'} <= event.facts
               for event in singleton)
    graph = result.ontology
    assert isinstance(graph, Graph)
    named = {'General', 'Middle', 'Leaf', 'Sibling'} if inverse_mode == 'all' else set()
    _, _, expected = _hierarchy_expected(
        result, 'id', named,
        [('Middle', 'General'), ('General', 'Middle'), ('Leaf', 'Middle'), ('Sibling', 'General')])
    assert _edges(graph) == expected
    assert not _pairs(graph)
    assert not list(graph.triples((None, OWL.equivalentProperty, None)))
    assert not list(graph.subjects(RDF.type, OWL.NamedIndividual))
    assert not list(graph.subjects(RDF.type, BASE.cRelType))
    if categorizer_kind in {'valid_class_ordinary', 'valid_class_powertype'}:
        assert (BASE.cRelType, RDF.type, OWL.Class) in graph
    assert not any(term in {BASE.gsRelations, BASE.dString, XSD.string, BASE.missingCategorizer}
                   for triple in graph for term in triple)


@pytest.mark.parametrize('mode', CHAIN_MODES)
@pytest.mark.parametrize('inverse_mode', ['all', 'none'])
def test_non_null_categorizer_on_singleton_relation_set_preserves_chain_propagation(
        run, source_json, tmp_path, mode, inverse_mode):
    """Rules: DK-HO-04, DK-REL-07, DK-REL-09, DK-REL-10, DK-REL-11, DK-REL-14, DK-REL-15, DK-REL-20, DK-INV-12, DK-DIAG-07, DK-DIAG-14.

    RD-02 Alternative A, cc562c49a8274367e3a52d95c368abb484bfa713. Under
    best-effort, a non-null categorizer on a singleton complete relation set
    retains reverse subproperty inclusion and DK-REL-07 non-simplicity propagation.
    """
    document = source_json('relations/chain_constraints')
    rel_type = copy.deepcopy(source_element(document, 'cA'))
    rel_type.update(id='cRelType', name='RelationType', stereotype='type', isPowertype=True)
    document['model']['contents'].append(rel_type)
    source_element(document, 'gsSingleton').update(
        isComplete=True, isDisjoint=False, categorizer={'id': 'cRelType', 'type': 'Class'})
    assert fixture_issues(document) == frozenset()

    result = run(path=write_input(tmp_path, document), iri_strategy='id',
                 inverse_properties=inverse_mode, material_property_chains=mode, input_policy='best-effort')
    assert result.outcome == 'completed-with-errors'
    _assert_inapplicable_relation_categorizer_error(result.diagnostics, set_id='gsSingleton')
    assert any(event.kind == 'singleton_completeness' and event.severity == 'INFO'
               and {'gsSingleton', 'rSuper', 'rPeer'} <= set(event.identified_sources)
               and {'extensional_equivalence', 'distinct_identifiers'} <= event.facts
               for event in result.diagnostics)
    graph = result.ontology
    assert (BASE.tSuper, RDFS.subPropertyOf, BASE.tPeer) in graph
    assert (BASE.tPeer, RDFS.subPropertyOf, BASE.tSuper) in graph
    if inverse_mode == 'all':
        assert (BASE.sSuper, RDFS.subPropertyOf, BASE.sPeer) in graph
        assert (BASE.sPeer, RDFS.subPropertyOf, BASE.sSuper) in graph
    omitted = mode == 'omit-conflicting-constraints'
    reverse = BASE.sPeer if inverse_mode == 'all' else ('inverse', BASE.tPeer)
    _counts(graph, BASE.cA, BASE.tPeer, set() if omitted else {('exact', 2)})
    _counts(graph, BASE.cB, reverse, set() if omitted else {('exact', 1)})
    prefixes = ('t', 's') if inverse_mode == 'all' else ('t',)
    keys = ['Material', 'Peer', 'PeerTwo']
    expected_pairs = set() if omitted else {
        frozenset((BASE[prefix + left], BASE[prefix + right]))
        for prefix in prefixes for index, left in enumerate(keys) for right in keys[index + 1:]}
    assert _pairs(graph) == expected_pairs
    assert (BASE.cRelType, RDF.type, OWL.Class) in graph
    assert not list(graph.subjects(RDF.type, BASE.cRelType))
    assert not list(graph.subjects(RDF.type, OWL.NamedIndividual))
    _compatibility(result, mode, mode != 'none', {'cardinalities_omitted', 'property_disjointness_omitted'} if omitted else ())


@pytest.mark.parametrize('input_policy', POLICIES)
@pytest.mark.parametrize('inverse_mode', ['all', 'none'])
@pytest.mark.parametrize('categorizer_kind', ['valid_class_powertype', 'dangling_id'])
@pytest.mark.parametrize('failure', ['unresolved_member_one_survivor', 'failed_specific_three_members', 'failed_general'])
def test_non_null_categorizer_with_failed_relation_member_applies_both_rules(
        run, source_json, tmp_path, input_policy, inverse_mode, categorizer_kind, failure):
    """Rules: DK-HO-02, DK-HO-03, DK-HO-04, DK-GEN-12, DK-REL-14, DK-REL-15, DK-REL-16, DK-REL-20, DK-INV-12, DK-DIAG-03, DK-DIAG-05, DK-DIAG-14.

    RD-02 Alternative A, cc562c49a8274367e3a52d95c368abb484bfa713. Combined
    member failure and non-null categorizer on a relation set retain both
    structural ERRORs, omit singleton completeness and property typing, and keep
    surviving specific disjointness and multi-member DK-REL-16 warnings.
    """
    document = source_json('relations/hierarchy')
    expected_issues = set(_apply_relation_set_categorizer(document, categorizer_kind))
    gs = source_element(document, 'gsRelations')
    expected_edges = [('Middle', 'General'), ('Leaf', 'Middle'), ('Sibling', 'General')]
    if failure == 'unresolved_member_one_survivor':
        gs['generalizations'][1]['id'] = 'gMissing'
        member_locator = 'gsRelations'
        expected_issues.add('unresolved_reference:gMissing')
    elif failure == 'failed_specific_three_members':
        extra = copy.deepcopy(source_element(document, 'gMiddle'))
        extra.update(id='gLeafGeneral', specific={'id': 'rLeaf', 'type': 'Relation'})
        document['model']['contents'].append(extra)
        gs['generalizations'].append({'id': 'gLeafGeneral', 'type': 'Generalization'})
        source_element(document, 'tSibling')['propertyType'] = None
        expected_edges.remove(('Sibling', 'General'))
        expected_edges.append(('Leaf', 'General'))
        member_locator = 'tSibling'
        expected_issues.add('unresolved_endpoint')
    else:
        source_element(document, 'tGeneral')['propertyType'] = None
        expected_edges = [('Leaf', 'Middle')]
        member_locator = 'tGeneral'
        expected_issues.add('unresolved_endpoint')
    assert fixture_issues(document) == expected_issues

    result = run(path=write_input(tmp_path, document), iri_strategy='id',
                 inverse_properties=inverse_mode, input_policy=input_policy)
    assert not any(event.kind == 'singleton_completeness' for event in result.diagnostics)
    if input_policy != 'best-effort':
        assert result.outcome == 'aborted' and result.ontology is None and result.provenance is None
        assert any(
            event.severity == 'ERROR'
            and event.code != 'INTERNAL_TRANSFORMATION_FAILURE'
            and (member_locator in event.identified_sources
                 or ('gsRelations' in event.identified_sources and 'inapplicable_relation_categorizer' in event.facts))
            for event in result.diagnostics
        ), result.diagnostics
        return

    assert result.outcome == 'completed-with-errors'
    assert any(event.severity == 'ERROR' and member_locator in event.identified_sources
               and 'inapplicable_relation_categorizer' not in event.facts
               for event in result.diagnostics), result.diagnostics
    _assert_inapplicable_relation_categorizer_error(result.diagnostics)
    graph = result.ontology
    assert isinstance(graph, Graph)
    prefixes = ('t', 's') if inverse_mode == 'all' else ('t',)
    assert _edges(graph) == {(BASE[prefix + a], BASE[prefix + b]) for prefix in prefixes for a, b in expected_edges}
    specific_pair = (('Middle', 'Leaf') if failure == 'failed_specific_three_members' else
                     ('Middle', 'Sibling') if failure == 'failed_general' else None)
    expected_pairs = {frozenset(BASE[prefix + key] for key in specific_pair)
                      for prefix in prefixes} if specific_pair else set()
    assert _pairs(graph) == expected_pairs
    for predicate in (OWL.equivalentProperty, OWL.unionOf, OWL.disjointUnionOf,
                      OWL.intersectionOf, OWL.oneOf, OWL.complementOf):
        assert not list(graph.triples((None, predicate, None)))
    completeness_warnings = [event for event in result.diagnostics if event.kind == 'relation_set_completeness']
    if failure == 'unresolved_member_one_survivor':
        assert not completeness_warnings
    else:
        assert any(event.severity == 'WARNING' and 'gsRelations' in event.identified_sources
                   and 'coverage_not_represented' in event.facts for event in completeness_warnings)
    assert not list(graph.subjects(RDF.type, OWL.NamedIndividual))
    assert not list(graph.subjects(RDF.type, BASE.cRelType))
    if categorizer_kind == 'valid_class_powertype':
        assert (BASE.cRelType, RDF.type, OWL.Class) in graph
    assert not any(term in {BASE.gsRelations, BASE.missingCategorizer} for triple in graph for term in triple)


@pytest.mark.parametrize('input_policy', POLICIES)
@pytest.mark.parametrize('precedence', [
    'empty_members', 'null_members', 'absent_members', 'non_array_members', 'duplicate_id',
])
def test_non_null_categorizer_on_relation_set_respects_dk_diag_12_and_duplicate_id_precedence(
        run, source_json, tmp_path, input_policy, precedence):
    """Rules: DK-HO-04, DK-DIAG-12, DK-DIAG-05, DK-REL-14; §3.4 duplicate declaration IDs.

    RD-02 Alternative A, cc562c49a8274367e3a52d95c368abb484bfa713. DK-DIAG-12
    governs empty/missing/malformed membership containers and fatal duplicate
    declaration IDs retain precedence even when categorizer is also non-null.
    """
    document = source_json('relations/hierarchy')
    rel_type = copy.deepcopy(source_element(document, 'cA'))
    rel_type.update(id='cRelType', name='RelationType', stereotype='type', isPowertype=True)
    document['model']['contents'].append(rel_type)
    affected = source_element(document, 'gsRelations')
    affected.update(isComplete=True, isDisjoint=True, categorizer={'id': 'cRelType', 'type': 'Class'})
    expected_issues = set()
    if precedence == 'empty_members':
        affected['generalizations'] = []
    elif precedence == 'null_members':
        affected['generalizations'] = None
    elif precedence == 'absent_members':
        del affected['generalizations']
    elif precedence == 'non_array_members':
        affected['generalizations'] = {'id': 'gMiddle', 'type': 'Generalization'}
        expected_issues.add('malformed_membership')
    elif precedence == 'duplicate_id':
        dup = copy.deepcopy(source_element(document, 'rMiddle'))
        dup['properties'][0]['id'] = 'sMiddleDup'
        dup['properties'][1]['id'] = 'tMiddleDup'
        document['model']['contents'].append(dup)
        expected_issues.add('duplicate_id:rMiddle')
    assert fixture_issues(document) == expected_issues

    result = run(path=write_input(tmp_path, document), iri_strategy='id', input_policy=input_policy)
    assert all('inapplicable_relation_categorizer' not in event.facts and 'unusable_categorizer' not in event.facts
               for event in result.diagnostics), result.diagnostics
    if precedence == 'duplicate_id':
        assert result.outcome == 'aborted' and result.ontology is None and result.provenance is None
        assert any(event.severity == 'ERROR' and event.code == 'DUPLICATE_SOURCE_ID'
                   and 'rMiddle' in event.identified_sources for event in result.diagnostics)
        return
    if precedence == 'empty_members':
        assert any(event.severity == 'ERROR' and event.kind == 'empty_generalization_set'
                   and 'gsRelations' in event.identified_sources for event in result.diagnostics)
    else:
        fact = {'null_members': 'membership_null', 'absent_members': 'membership_absent',
                'non_array_members': 'membership_non_array'}[precedence]
        assert any(event.severity == 'ERROR' and 'gsRelations' in event.identified_sources
                   and fact in event.facts for event in result.diagnostics), result.diagnostics
    if input_policy != 'best-effort':
        assert result.outcome == 'aborted' and result.ontology is None and result.provenance is None
        return

    assert result.outcome == 'completed-with-errors'
    graph = result.ontology
    assert isinstance(graph, Graph)
    _, _, expected = _hierarchy_expected(
        result, 'id', {'General', 'Middle', 'Leaf', 'Sibling'},
        [('Middle', 'General'), ('Leaf', 'Middle'), ('Sibling', 'General')])
    assert _edges(graph) == expected
    assert not _pairs(graph)
    for predicate in (OWL.equivalentProperty, OWL.unionOf, OWL.disjointUnionOf,
                      OWL.intersectionOf, OWL.oneOf, OWL.complementOf):
        assert not list(graph.triples((None, predicate, None)))
    assert not any(event.kind in {'singleton_completeness', 'relation_set_completeness'} for event in result.diagnostics)
    assert (BASE.cRelType, RDF.type, OWL.Class) in graph
    assert not list(graph.subjects(RDF.type, OWL.NamedIndividual))
    assert not list(graph.subjects(RDF.type, BASE.cRelType))
    assert not any(BASE.gsRelations in triple for triple in graph)


def test_inapplicable_relation_categorizer_reader_requires_affirmative_condition():
    """Harness only: verify affirmative relation-set categorizer wording without fixing provisional codes."""
    accepted = (
        "Relation generalization set 'gsRelations' has an inapplicable non-null categorizer {'id': 'cRelType', 'type': 'Class'}.",
        "Relation generalization set 'gsRelations' has a non-null categorizer {'id': 'cRelType', 'type': 'Class'}, which applies only to class generalization sets.",
        "Relation generalization set 'gsRelations' cannot have a non-null categorizer.",
        "Generalization set 'gsRelations' is a relation generalization set and cannot have a categorizer.",
        "Inapplicable non-null categorizer on relation generalization set 'gsRelations'.",
        "Categorizer {'id': 'cRelType', 'type': 'Class'} on relation generalization set 'gsRelations' is inapplicable.",
        "Categorizer on relation generalization set 'gsRelations' is not applicable.",
        "Relation generalization set 'gsRelations' does not support a non-null categorizer.",
        "Relation generalization set 'gsRelations' has a disallowed categorizer value.",
        "Relation generalization set 'gsRelations' has an unusable categorizer {'id': 'cRelType', 'type': 'Class'}: relation sets do not support categorizers.",
        "Relation generalization set 'gsRelations' has an inapplicable non-null categorizer; relation generalization sets must have a null or absent categorizer.",
    )
    rejected = (
        "Categorizer treatment for relation sets remains unspecified.",
        "Non-null categorizer on relation generalization set remains outside the decided baseline.",
        "Unexpected internal failure while inspecting categorizer.",
        "Relation generalization set 'gsRelations' categorizer is null.",
        "Relation generalization set 'gsRelations' categorizer is absent.",
        "Relation generalization set 'gsRelations' has no categorizer.",
        "Relation generalization set 'gsRelations' has a valid categorizer.",
        "Relation generalization set 'gsRelations' categorizer is not inapplicable.",
        "Relation generalization set 'gsRelations' has an inapplicable or absent categorizer.",
        "Relation generalization set 'gsRelations' has a valid or inapplicable categorizer.",
        "If a relation generalization set has a non-null categorizer, conversion aborts.",
        "Relation generalization set 'gsRelations' may have an inapplicable categorizer.",
        "Categorizers apply only to class generalization sets.",
        "Relation generalization set 'gsRelations' categorizer must be null or absent.",
        "Generalization set 'gsFirst': the categorizer is not null, and member 'missingMember' failed.",
        "Relation generalization set 'gsRelations' member 'gMissing' cannot be resolved; categorizer was not checked.",
        "Relation generalization set 'gsRelations' has an invalid generalizations container, not an inapplicable categorizer.",
    )
    for message in accepted:
        assert inapplicable_relation_categorizer_diagnostic(message), message
    for message in rejected:
        assert not inapplicable_relation_categorizer_diagnostic(message), message


_RD02_PRIMITIVES = [
    ('boolean', XSD.boolean),
    ('byte', XSD.byte),
    ('char', XSD.string),
    ('double', XSD.double),
    ('float', XSD.float),
    ('int', XSD.int),
    ('long', XSD.long),
    ('short', XSD.short),
    ('string', XSD.string),
]


def _datatype_class(document, identifier='dValue', name='int'):
    cls = copy.deepcopy(source_element(document, 'cB'))
    cls.update(id=identifier, name=name, stereotype='datatype')
    return cls


def _assert_no_relation_triples(graph, *identifiers):
    for identifier in identifiers:
        assert not any(BASE[identifier] in triple for triple in graph), identifier
    assert not list(graph.subjects(DCTERMS.identifier, Literal('tFocus')))
    assert not list(graph.subjects(DCTERMS.identifier, Literal('sFocus')))


@pytest.mark.parametrize('iri_strategy', ['name', 'id'])
@pytest.mark.parametrize('case,name,expected_target', [
    *(pytest.param('primitive', prim_name, xsd_iri, id=prim_name) for prim_name, xsd_iri in _RD02_PRIMITIVES),
    pytest.param('localized_primitive', {'en': 'int', 'nl': 'float'}, XSD.int, id='localized_int'),
    pytest.param('localized_custom', {'de': 'Ganzzahl', 'en': 'int'}, None, id='localized_custom'),
    pytest.param('custom_unregistered', 'integer', None, id='unregistered_integer_remains_custom'),
])
def test_datatype_valued_relations_map_all_nine_primitives_and_retain_custom_datatypes(
        run, source_json, tmp_path, iri_strategy, case, name, expected_target):
    """Rules: DK-REL-01, DK-DAT-02, DK-DAT-05, DK-GEN-03, DK-IRI-06, DK-IRI-09, DK-IRI-10, DK-INV-01, DK-INV-02, DK-LBL-01, DK-LBL-02, DK-REL-10, DK-REL-11.

    RD-02 Alternative B: Class -> Primitive ordinary binary relations map to
    owl:DatatypeProperty with DK-DAT-02 XSD ranges and no inverses, while
    unregistered/localized-custom datatypes retain custom owl:Class + owl:ObjectProperty.
    """
    document = source_json('shared/binary_relation')
    document['languages'] = ['nl']
    source_element(document, 'cB').update(name=copy.deepcopy(name), stereotype='datatype')
    source_element(document, 'rFocus').update(name='hasValue', description='Relation description.')
    source_element(document, 'sFocus').update(name=None, cardinality=None, description='Omitted source description.')
    source_element(document, 'tFocus').update(name='valueRole', cardinality='1', description='Target description.')
    assert not fixture_issues(document)

    result = run(path=write_input(tmp_path, document), iri_strategy=iri_strategy, inverse_properties='all')
    assert result.outcome == 'completed'
    assert not any(d.severity in {'WARNING', 'ERROR'} for d in result.diagnostics), result.diagnostics
    graph = result.ontology
    primary = _primary(result, 'tFocus', iri_strategy)
    domain = BASE.cA if iri_strategy == 'id' else BASE.HTTPServer

    if expected_target is not None:
        assert (primary, RDF.type, OWL.DatatypeProperty) in graph
        assert (primary, RDF.type, OWL.ObjectProperty) not in graph
        assert set(graph.objects(primary, RDFS.domain)) == {domain}
        assert set(graph.objects(primary, RDFS.range)) == {expected_target}
        assert not any(BASE.cB in triple for triple in graph)
        assert not list(graph.subjects(DCTERMS.identifier, Literal('cB')))
        assert not any(primary in pair for pair in graph.subject_objects(OWL.inverseOf))
        assert not any(BASE.sFocus in triple for triple in graph)
        assert not list(graph.subjects(DCTERMS.identifier, Literal('sFocus')))
        if case == 'primitive' and name == 'char':
            assert not list(graph.triples((None, OWL.withRestrictions, None)))
    else:
        custom = BASE.cB if iri_strategy == 'id' else one_subject(graph, DCTERMS.identifier, Literal('cB'))
        assert (custom, RDF.type, OWL.Class) in graph
        assert (primary, RDF.type, OWL.ObjectProperty) in graph
        assert (primary, RDF.type, OWL.DatatypeProperty) not in graph
        assert set(graph.objects(primary, RDFS.domain)) == {domain}
        assert set(graph.objects(primary, RDFS.range)) == {custom}
        inverse = _primary(result, 'sFocus', iri_strategy)
        assert (inverse, OWL.inverseOf, primary) in graph

    assert set(graph.objects(primary, RDFS.label)) == {Literal('hasValue', lang='nl')}
    assert (primary, RDFS.comment, Literal('Relation description.', lang='nl')) in graph
    assert (primary, RDFS.comment, Literal('Target description.', lang='nl')) in graph
    if expected_target is not None:
        assert not list(graph.triples((None, RDFS.comment, Literal('Omitted source description.', lang='nl'))))
    assert not any(d.kind == 'omitted_description' for d in result.diagnostics)
    _counts(graph, domain, primary, {('exact', 1)})


@pytest.mark.parametrize('input_policy', POLICIES)
@pytest.mark.parametrize('source_card,target_card,expected_counts,valid', [
    ('*', '0', {('exact', 0)}, True),
    ('0..*', '1', {('exact', 1)}, True),
    (' \t* ', '0..1', {('max', 1)}, True),
    (' 00 .. * ', '2..5', {('min', 2), ('max', 5)}, True),
    (None, '5..2', {('min', 5), ('max', 2)}, True),
    (None, '1..*', {('min', 1)}, True),
    ('*', '0..*', set(), True),
    ('0..*', '*', set(), True),
    (None, None, set(), True),
    ('absent', 'absent', set(), True),
    ('*', '1..n', {('min', 1)}, False),
    ('0..*', '..3', {('max', 3)}, False),
    (None, '2...*', set(), False),
], ids=[
    'star_to_zero', 'zero_unbounded_to_one', 'padded_star_to_optional',
    'padded_zero_unbounded_to_bounded', 'null_to_contradictory', 'null_to_pos_unbounded',
    'star_to_zero_unbounded', 'zero_unbounded_to_star', 'both_null', 'both_absent',
    'target_invalid_upper_recovers_min', 'target_empty_lower_recovers_max', 'target_ambiguous_recovers_none',
])
def test_datatype_valued_relation_compatible_counts_and_target_recovery(
        run, source_json, tmp_path, input_policy, source_card, target_card, expected_counts, valid):
    """Rules: DK-REL-01, DK-REL-10, DK-REL-11, DK-REL-12, DK-REL-13, DK-DIAG-05, DK-DIAG-09, DK-DIAG-10, DK-DIAG-11; §3.4.

    RD-02 Q3a/Q3b: compatible source multiplicities (*, 0..*, null, absent)
    keep target-end unqualified necessary counts and target-end DK-DIAG-10 recovery.
    """
    document = source_json('shared/binary_relation')
    source_element(document, 'cB').update(name='int', stereotype='datatype')
    source_end = source_element(document, 'sFocus')
    target_end = source_element(document, 'tFocus')
    source_end['name'] = None
    if source_card == 'absent':
        del source_end['cardinality']
    else:
        source_end['cardinality'] = source_card
    if target_card == 'absent':
        del target_end['cardinality']
    else:
        target_end['cardinality'] = target_card
    assert not fixture_issues(document)

    result = run(path=write_input(tmp_path, document), iri_strategy='id',
                 inverse_properties='all', input_policy=input_policy)
    if valid:
        assert result.outcome == 'completed'
        assert not any(d.severity == 'ERROR' for d in result.diagnostics)
        missing = [d for d in result.diagnostics if d.kind == 'missing_cardinality']
        if source_card == 'absent':
            assert any(d.severity == 'WARNING' and 'sFocus' in d.identified_sources for d in missing)
            assert any(d.severity == 'WARNING' and 'tFocus' in d.identified_sources for d in missing)
        else:
            assert not missing
            assert not any(d.severity == 'WARNING' for d in result.diagnostics)
    else:
        assert any(d.kind == 'invalid_cardinality' and d.severity == 'ERROR'
                   and 'tFocus' in d.identified_sources for d in result.diagnostics)
        if input_policy != 'best-effort':
            assert result.outcome == 'aborted' and result.ontology is None
            return
        assert result.outcome == 'completed-with-errors'

    graph = result.ontology
    assert (BASE.tFocus, RDF.type, OWL.DatatypeProperty) in graph
    assert set(graph.objects(BASE.tFocus, RDFS.domain)) == {BASE.cA}
    assert set(graph.objects(BASE.tFocus, RDFS.range)) == {XSD.int}
    assert not any(BASE.sFocus in triple for triple in graph)
    _counts(graph, BASE.cA, BASE.tFocus, expected_counts)


@pytest.mark.parametrize('strategy', ['name', 'id'])
@pytest.mark.parametrize('label_mode', ['source-only', 'generated'])
@pytest.mark.parametrize('branch', ['relation', 'target_role', 'relator_grounding', 'endpoints'])
@pytest.mark.parametrize('dkgm_mode', ['import', 'none'])
def test_datatype_valued_relation_naming_labels_identifiers_and_dkgm_modes(
        run, source_json, tmp_path, strategy, label_mode, branch, dkgm_mode):
    """Rules: DK-REL-01, DK-REL-02, DK-REL-03, DK-REL-05, DK-REL-06, DK-REL-08, DK-LBL-01, DK-LBL-02, DK-IRI-06, DK-IRI-09, DK-GEN-04.

    RD-02 Q1/Q7: compatible datatype-valued relations follow relation-naming
    precedence, primary-relation label modes, omit-identifiers, and DKGM modes.
    """
    document = source_json('relations/material_naming' if branch == 'relator_grounding' else 'shared/binary_relation')
    document['languages'] = ['nl']
    source_element(document, 'cB').update(name='int', stereotype='datatype')
    source_element(document, 'sFocus')['name'] = None
    if branch == 'relation':
        source_element(document, 'rFocus')['name'] = ' Assigned, Count '
        source_element(document, 'tFocus')['name'] = 'target count'
    elif branch == 'target_role':
        source_element(document, 'rFocus')['name'] = None
        source_element(document, 'tFocus')['name'] = 'target count'
    elif branch == 'endpoints':
        source_element(document, 'rFocus')['name'] = None
        source_element(document, 'tFocus')['name'] = None
    assert not fixture_issues(document)

    result = run(path=write_input(tmp_path, document), iri_strategy=strategy,
                 relation_labels=label_mode, dkgm_vocabulary=dkgm_mode, language='pt-BR')
    assert result.outcome == 'completed'
    assert not any(d.severity == 'ERROR' for d in result.diagnostics)
    assert not any(DKGM_CHAIN_WARNING_FACTS & d.facts for d in result.diagnostics)
    graph = result.ontology
    primary = _primary(result, 'tFocus', strategy)
    domain = BASE.cA if strategy == 'id' else BASE.HTTPServer
    assert (primary, RDF.type, OWL.DatatypeProperty) in graph
    assert set(graph.objects(primary, RDFS.domain)) == {domain}
    assert set(graph.objects(primary, RDFS.range)) == {XSD.int}
    assert not list(graph.objects(primary, RDFS.subPropertyOf))

    expected_candidate = {
        'relation': 'Assigned_Count',
        'target_role': 'target_count',
        'relator_grounding': 'employment',
        'endpoints': 'hTTPServer_int',
    }[branch]
    if strategy == 'name':
        assert primary == BASE[expected_candidate]
        assert set(graph.objects(primary, DCTERMS.identifier)) == {Literal('tFocus')}
    else:
        assert not list(graph.objects(primary, DCTERMS.identifier))

    if branch == 'relation':
        assert set(graph.objects(primary, RDFS.label)) == {Literal(' Assigned, Count ', lang='pt-BR')}
    elif branch == 'target_role':
        assert set(graph.objects(primary, RDFS.label)) == {Literal('target count', lang='pt-BR')}
    else:
        assert set(graph.objects(primary, RDFS.label)) == (
            {Literal(expected_candidate)} if label_mode == 'generated' else set())
    if branch == 'endpoints' and strategy == 'name':
        _source_target_naming_warning(result, 'rFocus')
    elif branch == 'target_role' and strategy == 'name':
        assert any(d.kind == 'relation_naming' and d.severity == 'WARNING' for d in result.diagnostics)
    if strategy == 'name':
        omitted = run(path=write_input(tmp_path, document, 'omit.json'), iri_strategy='name',
                      relation_labels=label_mode, dkgm_vocabulary=dkgm_mode, omit_identifiers=True)
        assert omitted.outcome == 'completed'
        assert not list(omitted.ontology.triples((None, DCTERMS.identifier, None)))


@pytest.mark.parametrize('input_policy', POLICIES)
@pytest.mark.parametrize('strategy', ['name', 'id'])
@pytest.mark.parametrize('endpoint_case', [
    'class_to_void',
    'primitive_to_class',
    'void_to_class',
    'primitive_to_primitive',
    'primitive_to_void',
    'void_to_void',
])
def test_datatype_valued_relation_endpoint_rejections_and_pre_naming_omission(
        run, source_json, tmp_path, input_policy, strategy, endpoint_case):
    """Rules: DK-REL-01, DK-DAT-04, DK-DAT-05, DK-DIAG-03, DK-DIAG-04, DK-DIAG-05.

    RD-02 Q1a/Q1b & Conflict H: Class -> void and relations whose source lacks
    a generated local owl:Class fail with structural ERROR before naming/IRI
    allocation; best-effort omits only the failed relation without reversing
    direction or inventing a local class, while void attributes keep DK-DAT-04.
    """
    document = source_json('shared/binary_relation')
    d_int = _datatype_class(document, 'dInt', 'int')
    d_void = _datatype_class(document, 'dVoid', 'void')
    c_peer = copy.deepcopy(source_element(document, 'cA'))
    c_peer.update(id='cPeer', name='PeerClass')
    document['model']['contents'].extend([d_int, d_void, c_peer])

    # Include an independent void-typed attribute on cA to confirm DK-DAT-04 remains separate.
    void_attr = {
        'id': 'pVoidAttr', 'name': 'voidAttr', 'description': None, 'type': 'Property',
        'propertyAssignments': None, 'stereotype': None, 'isDerived': False,
        'isReadOnly': False, 'isOrdered': False, 'cardinality': '1',
        'propertyType': {'id': 'dVoid', 'type': 'Class'},
        'subsettedProperties': None, 'redefinedProperties': None, 'aggregationKind': None,
    }
    source_element(document, 'cA')['properties'] = [void_attr]

    # Add a peer same-named relation cA -> cPeer to verify failed rFocus claims no IRI.
    peer_rel = copy.deepcopy(source_element(document, 'rFocus'))
    peer_rel.update(id='rPeer', name='sharedName')
    peer_rel['properties'][0].update(id='sPeer', name=None, propertyType={'id': 'cA', 'type': 'Class'})
    peer_rel['properties'][1].update(id='tPeer', name=None, propertyType={'id': 'cPeer', 'type': 'Class'})
    document['model']['contents'].append(peer_rel)

    source_map = {
        'class_to_void': ('cA', 'dVoid', 'void_relation_target'),
        'primitive_to_class': ('dInt', 'cB', 'non_class_relation_source'),
        'void_to_class': ('dVoid', 'cB', 'non_class_relation_source'),
        'primitive_to_primitive': ('dInt', 'dInt', 'non_class_relation_source'),
        'primitive_to_void': ('dInt', 'dVoid', 'non_class_relation_source'),
        'void_to_void': ('dVoid', 'dVoid', 'non_class_relation_source'),
    }
    src_id, tgt_id, expected_fact = source_map[endpoint_case]
    source_element(document, 'rFocus')['name'] = None
    source_element(document, 'sFocus').update(name=None, cardinality='1', propertyType={'id': src_id, 'type': 'Class'})
    source_element(document, 'tFocus').update(name=None, cardinality='2', propertyType={'id': tgt_id, 'type': 'Class'})
    # Clear sharedName from rFocus so if naming ran it would warn; verify no naming diagnostic fires for rFocus.
    assert not fixture_issues(document)

    result = run(path=write_input(tmp_path, document), iri_strategy=strategy,
                 input_policy=input_policy, inverse_properties='none')
    assert any(
        d.severity == 'ERROR'
        and expected_fact in d.facts
        and d.code != 'INTERNAL_TRANSFORMATION_FAILURE'
        and d.code not in STABLE_DIAGNOSTIC_CODES
        and {'rFocus', 'sFocus', 'tFocus'} & set(d.identified_sources)
        for d in result.diagnostics
    ), result.diagnostics
    assert not any(
        d.kind in NAMING_KINDS and {'rFocus', 'sFocus', 'tFocus'} & set(d.identified_sources)
        for d in result.diagnostics
    )

    if input_policy != 'best-effort':
        assert result.outcome == 'aborted' and result.ontology is None
        return

    assert result.outcome == 'completed-with-errors'
    graph = result.ontology
    _assert_no_relation_triples(graph, 'rFocus', 'sFocus', 'tFocus', 'dInt', 'dVoid')
    assert not list(graph.subjects(DCTERMS.identifier, Literal('dInt')))
    assert not list(graph.subjects(DCTERMS.identifier, Literal('dVoid')))
    c_a = BASE.cA if strategy == 'id' else BASE.HTTPServer
    c_peer_iri = BASE.cPeer if strategy == 'id' else BASE.PeerClass
    assert (c_a, RDF.type, OWL.Class) in graph
    assert (c_peer_iri, RDF.type, OWL.Class) in graph
    # Peer relation keeps its uncollided name/IRI without suffix from failed rFocus.
    t_peer = _primary(result, 'tPeer', strategy)
    assert (t_peer, RDF.type, OWL.ObjectProperty) in graph
    if strategy == 'name':
        assert t_peer == BASE.sharedName
    # DK-DAT-04 void-typed attribute still retains rangeless owl:DatatypeProperty + VOID_DATATYPE warning.
    p_void = BASE.pVoidAttr if strategy == 'id' else one_subject(graph, DCTERMS.identifier, Literal('pVoidAttr'))
    assert (p_void, RDF.type, OWL.DatatypeProperty) in graph
    assert not list(graph.objects(p_void, RDFS.range))
    assert any(d.kind == 'void_datatype' and d.severity == 'WARNING'
               and 'pVoidAttr' in d.identified_sources for d in result.diagnostics)


@pytest.mark.parametrize('target_kind', ['class', 'primitive'])
def test_custom_datatype_source_retains_local_class_for_object_and_datatype_relations(
        run, source_json, tmp_path, target_kind):
    """Rules: DK-REL-01, DK-DAT-05, DK-GEN-03.

    RD-02 Q1b: custom <<datatype>> classifiers already receive a local
    owl:Class and remain valid sources for both object and datatype relations.
    """
    document = source_json('shared/binary_relation')
    source_element(document, 'cA').update(name='CustomSource', stereotype='datatype')
    if target_kind == 'primitive':
        source_element(document, 'cB').update(name='int', stereotype='datatype')
    assert not fixture_issues(document)

    result = run(path=write_input(tmp_path, document), iri_strategy='id', inverse_properties='all')
    assert result.outcome == 'completed'
    graph = result.ontology
    assert (BASE.cA, RDF.type, OWL.Class) in graph
    expected_kind = OWL.DatatypeProperty if target_kind == 'primitive' else OWL.ObjectProperty
    expected_range = XSD.int if target_kind == 'primitive' else BASE.cB
    assert (BASE.tFocus, RDF.type, expected_kind) in graph
    assert set(graph.objects(BASE.tFocus, RDFS.domain)) == {BASE.cA}
    assert set(graph.objects(BASE.tFocus, RDFS.range)) == {expected_range}
    assert ((BASE.sFocus, RDF.type, OWL.ObjectProperty) in graph) == (target_kind == 'class')


@pytest.mark.parametrize('input_policy', POLICIES)
@pytest.mark.parametrize('strategy', ['name', 'id'])
@pytest.mark.parametrize('stereotype', [
    'componentOf', 'memberOf', 'subCollectionOf', 'subQuantityOf',
    'characterization', 'mediation', 'participational', 'externalDependence',
])
def test_datatype_valued_relation_rejects_eight_incompatible_stereotypes_before_naming(
        run, source_json, tmp_path, input_policy, strategy, stereotype):
    """Rules: DK-REL-01, DK-REL-19, DK-GEN-04, DK-DIAG-04, DK-DIAG-05.

    RD-02 Q2 & Conflict H: the eight object-property-only stereotypes fail with
    structural ERROR before IRI/naming; best-effort omits only the relation
    with no DKGM bridge, asymmetry/irreflexivity, cardinality, or annotations.
    """
    document = source_json('shared/binary_relation')
    source_element(document, 'cB').update(name='int', stereotype='datatype')
    source_element(document, 'rFocus').update(name=None, stereotype=stereotype, description='Should be omitted.')
    source_element(document, 'sFocus').update(name=None, cardinality=None, isReadOnly=True)
    source_element(document, 'tFocus').update(name=None, cardinality='2', aggregationKind='COMPOSITE')
    c_peer = copy.deepcopy(source_element(document, 'cA'))
    c_peer.update(id='cPeer', name='PeerClass')
    peer_rel = copy.deepcopy(source_element(document, 'rFocus'))
    peer_rel.update(id='rPeer', name='peerLink', stereotype='material', description=None)
    peer_rel['properties'][0].update(id='sPeer', name=None, cardinality=None, isReadOnly=False,
                                     propertyType={'id': 'cA', 'type': 'Class'})
    peer_rel['properties'][1].update(id='tPeer', name=None, cardinality='1', aggregationKind='NONE',
                                     propertyType={'id': 'cPeer', 'type': 'Class'})
    document['model']['contents'].extend([c_peer, peer_rel])
    assert not fixture_issues(document)

    result = run(path=write_input(tmp_path, document), iri_strategy=strategy,
                 input_policy=input_policy, inverse_properties='none')
    assert any(
        d.severity == 'ERROR'
        and 'incompatible_datatype_relation_stereotype' in d.facts
        and 'rFocus' in d.identified_sources
        and d.code != 'INTERNAL_TRANSFORMATION_FAILURE'
        and d.code not in STABLE_DIAGNOSTIC_CODES
        for d in result.diagnostics
    ), result.diagnostics
    assert not any(
        d.kind in NAMING_KINDS and {'rFocus', 'sFocus', 'tFocus'} & set(d.identified_sources)
        for d in result.diagnostics
    )

    if input_policy != 'best-effort':
        assert result.outcome == 'aborted' and result.ontology is None
        return

    assert result.outcome == 'completed-with-errors'
    graph = result.ontology
    _assert_no_relation_triples(graph, 'rFocus', 'sFocus', 'tFocus', 'cB')
    assert not list(graph.subjects(RDFS.subPropertyOf, None))
    assert not list(graph.subjects(RDF.type, OWL.AsymmetricProperty))
    assert not list(graph.subjects(RDF.type, OWL.IrreflexiveProperty))
    assert not list(graph.triples((None, RDFS.comment, Literal('Should be omitted.'))))
    t_peer = _primary(result, 'tPeer', strategy)
    assert (t_peer, RDF.type, OWL.ObjectProperty) in graph
    _counts(graph, BASE.cA if strategy == 'id' else BASE.HTTPServer, t_peer, {('exact', 1)})


@pytest.mark.parametrize('input_policy', POLICIES)
@pytest.mark.parametrize('strategy', ['name', 'id'])
@pytest.mark.parametrize('stereotype,expected_kind', [
    ('historicalDependence', 'unmapped_relation_stereotype'),
    ('participation', 'unmapped_relation_stereotype'),
    ('creation', 'unmapped_relation_stereotype'),
    ('termination', 'unmapped_relation_stereotype'),
    ('manifestation', 'unmapped_relation_stereotype'),
    ('bringsAbout', 'unmapped_relation_stereotype'),
    ('triggers', 'unmapped_relation_stereotype'),
    (None, None),
    ('customDatatypeRel', 'unrecognized_stereotype'),
])
def test_datatype_valued_relation_allows_compatible_stereotypes_with_warnings(
        run, source_json, tmp_path, input_policy, strategy, stereotype, expected_kind):
    """Rules: DK-REL-01, DK-DIAG-01, DK-DIAG-05, DK-DIAG-06, DK-REL-10, DK-REL-11.

    RD-02 Q2: compatible recognized stereotypes, missing stereotypes, and custom
    stereotypes retain owl:DatatypeProperty mapping and nonfatal warnings.
    """
    document = source_json('shared/binary_relation')
    source_element(document, 'cB').update(name='int', stereotype='datatype')
    source_element(document, 'rFocus').update(name='relLink', stereotype=stereotype)
    source_element(document, 'sFocus').update(name=None, cardinality=None)
    source_element(document, 'tFocus').update(name=None, cardinality='1')
    assert not fixture_issues(document)

    stereotype_policy = 'allow-missing' if stereotype is None else 'allow-custom' if expected_kind == 'unrecognized_stereotype' else 'require-known'
    result = run(path=write_input(tmp_path, document), iri_strategy=strategy,
                 input_policy=input_policy, stereotype_policy=stereotype_policy, inverse_properties='all')
    assert result.outcome == 'completed'
    assert not any(d.severity == 'ERROR' for d in result.diagnostics)
    graph = result.ontology
    primary = _primary(result, 'tFocus', strategy)
    domain = BASE.cA if strategy == 'id' else BASE.HTTPServer
    assert (primary, RDF.type, OWL.DatatypeProperty) in graph
    assert set(graph.objects(primary, RDFS.domain)) == {domain}
    assert set(graph.objects(primary, RDFS.range)) == {XSD.int}
    _counts(graph, domain, primary, {('exact', 1)})
    assert not any(primary in pair for pair in graph.subject_objects(OWL.inverseOf))
    if expected_kind is not None:
        assert any(d.kind == expected_kind and d.severity == 'WARNING' for d in result.diagnostics)


@pytest.mark.parametrize('mode', CHAIN_MODES)
@pytest.mark.parametrize('input_policy', POLICIES)
@pytest.mark.parametrize('case', [
    'standalone_material',
    'incomplete_grounding',
    'failed_grounding_mediation',
    'failed_grounding_characterization',
])
def test_datatype_valued_material_relation_with_chain_modes_preserves_compatible_property(
        run, source_json, tmp_path, mode, input_policy, case):
    """Rules: DK-REL-01, DK-REL-07, DK-REL-08, DK-DIAG-05, DK-DIAG-07.

    RD-02 Q2 & Conflict F: enabling --material-property-chains alone does not
    conflict with a datatype-valued material relation; under best-effort, failed
    grounding mediation/characterization does not reject the material property.
    """
    document = source_json('shared/material_pattern')
    source_element(document, 'cB').update(name='int', stereotype='datatype')
    source_element(document, 'sMaterial').update(name=None, cardinality=None)
    source_element(document, 'sLeft')['name'] = None
    source_element(document, 'sRight')['name'] = None
    if case in {'standalone_material', 'incomplete_grounding', 'failed_grounding_mediation'}:
        _grounding(document, 'relator')
    else:
        _grounding(document, 'mode')
    contents = document['model']['contents']
    if case == 'standalone_material':
        for key in ('rLeft', 'rRight', 'rDerivation'):
            contents.remove(source_element(document, key))
    elif case == 'incomplete_grounding':
        contents.remove(source_element(document, 'rRight'))
    assert not fixture_issues(document)

    result = run(path=write_input(tmp_path, document), iri_strategy='id',
                 input_policy=input_policy, material_property_chains=mode)
    grounding_fails = case in {'failed_grounding_mediation', 'failed_grounding_characterization'}
    if grounding_fails and input_policy != 'best-effort':
        assert result.outcome == 'aborted' and result.ontology is None
        assert any(d.severity == 'ERROR' and 'incompatible_datatype_relation_stereotype' in d.facts
                   and 'rRight' in d.identified_sources for d in result.diagnostics)
        return

    assert result.outcome == ('completed-with-errors' if grounding_fails else 'completed')
    graph = result.ontology
    assert (BASE.tMaterial, RDF.type, OWL.DatatypeProperty) in graph
    assert set(graph.objects(BASE.tMaterial, RDFS.domain)) == {BASE.cA}
    assert set(graph.objects(BASE.tMaterial, RDFS.range)) == {XSD.int}
    _counts(graph, BASE.cA, BASE.tMaterial, {('min', 2), ('max', 5)})
    assert not list(graph.triples((None, OWL.propertyChainAxiom, None)))
    assert not any(d.kind == 'chain_compatibility' for d in result.diagnostics)
    assert not any('incompatible_material_chain' in d.facts for d in result.diagnostics)
    if grounding_fails:
        assert any(d.severity == 'ERROR' and 'rRight' in d.identified_sources for d in result.diagnostics)
        _assert_no_relation_triples(graph, 'rRight', 'sRight', 'tRight')


@pytest.mark.parametrize('input_policy', POLICIES)
@pytest.mark.parametrize('case', ['without_derivation', 'comparative_first', 'quality_first'])
def test_datatype_valued_comparative_relation_conflicts_only_with_quality_derivation(
        run, source_json, tmp_path, input_policy, case):
    """Rules: DK-REL-01, DK-REL-18, DK-REL-06, DK-DIAG-05.

    RD-02 Q2 & Conflict E: standalone comparative Class -> Primitive stays an
    owl:DatatypeProperty, while pairing with a recognized DK-REL-18 derivation
    to a quality class reports a structural compatibility ERROR.
    """
    document = source_json('shared/material_pattern')
    source_element(document, 'cB').update(name='int', stereotype='datatype')
    source_element(document, 'rMaterial').update(name=None, stereotype='comparative')
    source_element(document, 'sMaterial').update(name=None, cardinality=None)
    source_element(document, 'tMaterial')['name'] = None
    source_element(document, 'cGround')['stereotype'] = 'quality'
    for key in ('rLeft', 'rRight'):
        document['model']['contents'].remove(source_element(document, key))
    if case == 'without_derivation':
        document['model']['contents'].remove(source_element(document, 'rDerivation'))
    elif case == 'quality_first':
        source_element(document, 'rDerivation')['properties'].reverse()
    assert not fixture_issues(document)

    result = run(path=write_input(tmp_path, document), iri_strategy='name', input_policy=input_policy)
    if case == 'without_derivation':
        assert result.outcome == 'completed'
        assert not any(d.severity == 'ERROR' for d in result.diagnostics)
        prop = _primary(result, 'tMaterial', 'name')
        assert (prop, RDF.type, OWL.DatatypeProperty) in result.ontology
        assert set(result.ontology.objects(prop, RDFS.range)) == {XSD.int}
        assert any(d.kind == 'comparative_naming' and d.severity == 'WARNING' for d in result.diagnostics)
        return

    assert any(
        d.severity == 'ERROR'
        and 'incompatible_comparative_derivation' in d.facts
        and 'rMaterial' in d.identified_sources
        and d.code != 'INTERNAL_TRANSFORMATION_FAILURE'
        for d in result.diagnostics
    ), result.diagnostics
    if input_policy != 'best-effort':
        assert result.outcome == 'aborted' and result.ontology is None
        return

    assert result.outcome == 'completed-with-errors'
    graph = result.ontology
    assert not list(graph.subjects(DCTERMS.identifier, Literal('tMaterial')))
    assert not any(BASE.tMaterial in triple or BASE.sMaterial in triple for triple in graph)
    assert not any(BASE.cB in triple for triple in graph)
    assert (BASE.Ground, RDF.type, OWL.Class) in graph
    assert (BASE.ParticipantA, RDF.type, OWL.Class) in graph
    unrelated = _primary(result, 'tUnrelated', 'name')
    assert (unrelated, RDF.type, OWL.ObjectProperty) in graph


@pytest.mark.parametrize('input_policy', POLICIES)
@pytest.mark.parametrize('strategy', ['name', 'id'])
@pytest.mark.parametrize('cardinality', ['0', '0..0', '1', '0..1', '2..5', '1..*', '5..2', '1..0'])
def test_datatype_valued_relation_meaningful_source_multiplicities_fail_before_naming(
        run, source_json, tmp_path, input_policy, strategy, cardinality):
    """Rules: DK-REL-01, DK-REL-11, DK-REL-12, DK-INV-02, DK-DIAG-04, DK-DIAG-05.

    RD-02 Q3a & Conflict H: valid meaningful source-end multiplicities on a
    datatype-valued relation require an unavailable inverse and fail with a
    structural ERROR before naming/IRI allocation.
    """
    document = source_json('shared/binary_relation')
    source_element(document, 'cB').update(name='int', stereotype='datatype')
    source_element(document, 'rFocus')['name'] = None
    source_element(document, 'sFocus').update(name=None, cardinality=cardinality)
    source_element(document, 'tFocus').update(name=None, cardinality='1')
    assert not fixture_issues(document)

    result = run(path=write_input(tmp_path, document), iri_strategy=strategy,
                 input_policy=input_policy, inverse_properties='none')
    assert any(
        d.severity == 'ERROR'
        and 'incompatible_source_multiplicity' in d.facts
        and {'rFocus', 'sFocus'} & set(d.identified_sources)
        and d.code != 'INTERNAL_TRANSFORMATION_FAILURE'
        for d in result.diagnostics
    ), result.diagnostics
    assert not any(
        d.kind in NAMING_KINDS and {'rFocus', 'sFocus', 'tFocus'} & set(d.identified_sources)
        for d in result.diagnostics
    )
    if input_policy != 'best-effort':
        assert result.outcome == 'aborted' and result.ontology is None
        return

    assert result.outcome == 'completed-with-errors'
    graph = result.ontology
    _assert_no_relation_triples(graph, 'rFocus', 'sFocus', 'tFocus', 'cB')
    assert (BASE.cA if strategy == 'id' else BASE.HTTPServer, RDF.type, OWL.Class) in graph


@pytest.mark.parametrize('input_policy', POLICIES)
@pytest.mark.parametrize('cardinality,recoverable_reverse', [
    pytest.param('1..n', True, id='recoverable_lower_positive'),
    pytest.param('..3', True, id='recoverable_upper_finite'),
    pytest.param('n..0', True, id='recoverable_upper_zero'),
    pytest.param('-1..3', True, id='recoverable_signed_lower_finite_upper'),
    pytest.param('2..+3', True, id='recoverable_positive_lower_signed_upper'),
    pytest.param('1..', True, id='recoverable_open_upper'),
    pytest.param('1.5..3', True, id='recoverable_decimal_lower_finite_upper'),
    pytest.param('2..3e1', True, id='recoverable_exponent_upper'),
    pytest.param('２..3', True, id='recoverable_non_ascii_lower_finite_upper'),
    pytest.param('n', False, id='unrecoverable_symbolic_single'),
    pytest.param('0..n', False, id='unrecoverable_zero_lower'),
    pytest.param('n..*', False, id='unrecoverable_unbounded_upper'),
    pytest.param('..', False, id='unrecoverable_both_empty'),
    pytest.param('n..m', False, id='unrecoverable_both_symbolic'),
    pytest.param('2...*', False, id='unrecoverable_ambiguous_dots'),
    pytest.param('1..2..3', False, id='unrecoverable_repeated_delimiter'),
    pytest.param('2,,3', False, id='unrecoverable_comma'),
    pytest.param('2:3', False, id='unrecoverable_colon'),
    pytest.param('', False, id='unrecoverable_empty_string'),
    pytest.param(' \t ', False, id='unrecoverable_blank_string'),
    pytest.param(1, False, id='unrecoverable_json_number'),
    pytest.param(True, False, id='unrecoverable_json_boolean'),
    pytest.param([], False, id='unrecoverable_json_array'),
    pytest.param({}, False, id='unrecoverable_json_object'),
])
def test_datatype_valued_relation_invalid_source_multiplicity_dk_diag_10_precedence(
        run, source_json, tmp_path, input_policy, cardinality, recoverable_reverse):
    """Rules: DK-REL-01, DK-DIAG-10, DK-DIAG-11, DK-DIAG-05, DK-INV-02.

    RD-02 Q3a + Conflict A: invalid source-end bounds retain INVALID_CARDINALITY;
    under best-effort, inverse unavailability takes precedence when a meaningful
    recoverable reverse bound exists (omitting the relation), whereas cases
    without recoverable reverse constraints preserve the compatible datatype property.
    """
    document = source_json('shared/binary_relation')
    source_element(document, 'cB').update(name='int', stereotype='datatype')
    source_element(document, 'sFocus').update(name=None, cardinality=cardinality)
    source_element(document, 'tFocus')['cardinality'] = '2..5'
    assert fixture_issues(document) == (frozenset() if isinstance(cardinality, str) else {'invalid_cardinality_type'})

    result = run(path=write_input(tmp_path, document), iri_strategy='id',
                 input_policy=input_policy, inverse_properties='none')
    assert any(d.kind == 'invalid_cardinality' and d.severity == 'ERROR'
               and 'sFocus' in d.identified_sources for d in result.diagnostics)
    if recoverable_reverse:
        assert any(
            d.severity == 'ERROR'
            and 'incompatible_source_multiplicity' in d.facts
            and d.code != 'INTERNAL_TRANSFORMATION_FAILURE'
            for d in result.diagnostics
        ), result.diagnostics

    if input_policy != 'best-effort':
        assert result.outcome == 'aborted' and result.ontology is None
        return

    assert result.outcome == 'completed-with-errors'
    graph = result.ontology
    assert (BASE.cA, RDF.type, OWL.Class) in graph
    assert not any(BASE.sFocus in triple or BASE.cB in triple for triple in graph)
    if recoverable_reverse:
        _assert_no_relation_triples(graph, 'rFocus', 'sFocus', 'tFocus', 'cB')
    else:
        assert (BASE.tFocus, RDF.type, OWL.DatatypeProperty) in graph
        assert set(graph.objects(BASE.tFocus, RDFS.domain)) == {BASE.cA}
        assert set(graph.objects(BASE.tFocus, RDFS.range)) == {XSD.int}
        _counts(graph, BASE.cA, BASE.tFocus, {('min', 2), ('max', 5)})


@pytest.mark.parametrize('inverse_mode', ['all', 'informed', 'named', 'none'])
@pytest.mark.parametrize('input_policy', POLICIES)
@pytest.mark.parametrize('role_value,expect_warning', [
    pytest.param('workers', True, id='plain_nonempty'),
    pytest.param({'en': '  ', 'nl': '東京'}, True, id='localized_any_nonwhitespace'),
    pytest.param('___', True, id='unusable_ascii_nonempty'),
    pytest.param('', False, id='empty_string'),
    pytest.param(' \t ', False, id='whitespace_only'),
    pytest.param({'en': '  ', 'nl': '\t'}, False, id='localized_all_whitespace'),
    pytest.param(None, False, id='explicit_null'),
    pytest.param('absent', False, id='absent_field'),
])
def test_datatype_valued_relation_inverse_modes_and_source_role_warning(
        run, source_json, tmp_path, inverse_mode, input_policy, role_value, expect_warning):
    """Rules: DK-REL-01, DK-INV-01, DK-INV-02, DK-INV-05, DK-LBL-02, DK-DIAG-05.

    RD-02 Q4a/Q4b: --inverse-properties never errors or generates an inverse on
    a datatype-valued relation; an explicit nonempty source-end role name emits
    a nonfatal WARNING under every policy including strict while omitting source
    descriptions without extra diagnostics.
    """
    document = source_json('shared/binary_relation')
    source_element(document, 'cB').update(name='int', stereotype='datatype')
    source_end = source_element(document, 'sFocus')
    source_end.update(cardinality='*', description='Omitted source description.')
    if role_value == 'absent':
        source_end.pop('name', None)
    else:
        source_end['name'] = copy.deepcopy(role_value)
    assert not fixture_issues(document)

    result = run(path=write_input(tmp_path, document), iri_strategy='id',
                 inverse_properties=inverse_mode, input_policy=input_policy)
    assert result.outcome == 'completed'
    assert not any(d.severity == 'ERROR' for d in result.diagnostics)
    graph = result.ontology
    assert (BASE.tFocus, RDF.type, OWL.DatatypeProperty) in graph
    assert set(graph.objects(BASE.tFocus, RDFS.domain)) == {BASE.cA}
    assert set(graph.objects(BASE.tFocus, RDFS.range)) == {XSD.int}
    assert not any(BASE.sFocus in triple for triple in graph)
    assert not list(graph.subject_objects(OWL.inverseOf))
    assert not list(graph.triples((None, RDFS.comment, Literal('Omitted source description.'))))
    assert not any(d.kind == 'omitted_description' for d in result.diagnostics)

    role_warnings = [d for d in result.diagnostics if 'unrepresentable_source_role' in d.facts]
    if expect_warning:
        assert role_warnings and all(
            d.severity == 'WARNING' and {'rFocus', 'sFocus'} & set(d.identified_sources)
            for d in role_warnings
        ), result.diagnostics
    else:
        assert not role_warnings
        assert not any(d.severity == 'WARNING' for d in result.diagnostics)


@pytest.mark.parametrize('input_policy', POLICIES)
@pytest.mark.parametrize('inverse_mode', ['all', 'none'])
@pytest.mark.parametrize('set_case', ['open', 'disjoint', 'singleton_complete', 'multi_complete'])
def test_homogeneous_datatype_relation_hierarchies_and_generalization_sets(
        run, source_json, tmp_path, input_policy, inverse_mode, set_case):
    """Rules: DK-REL-01, DK-REL-14, DK-REL-15, DK-REL-16, DK-REL-20, DK-INV-12, DK-DIAG-14, DK-DIAG-05.

    RD-02 Q6a/Q6b: homogeneous owl:DatatypeProperty relation generalizations,
    disjoint sets, singleton completeness (+ INFO), and multi-member completeness
    warnings apply without inverse axioms or absent-inverse warnings.
    """
    document = source_json('relations/hierarchy')
    d_int = _datatype_class(document, 'dInt', 'int')
    d_str = _datatype_class(document, 'dString', 'string')
    document['model']['contents'].extend([d_int, d_str])
    for key, target_dt in (('General', 'dInt'), ('Middle', 'dString'), ('Leaf', 'dString'), ('Sibling', 'dInt')):
        source_element(document, 's' + key)['name'] = None
        source_element(document, 't' + key)['propertyType'] = {'id': target_dt, 'type': 'Class'}
    gs = source_element(document, 'gsRelations')
    if set_case == 'open':
        gs.update(isComplete=False, isDisjoint=False)
    elif set_case == 'disjoint':
        gs.update(isComplete=False, isDisjoint=True)
    elif set_case == 'singleton_complete':
        gs.update(isComplete=True, isDisjoint=False, generalizations=[{'id': 'gMiddle', 'type': 'Generalization'}])
    else:
        gs.update(isComplete=True, isDisjoint=True)
    assert not fixture_issues(document)

    result = run(path=write_input(tmp_path, document), iri_strategy='id',
                 inverse_properties=inverse_mode, input_policy=input_policy)
    assert result.outcome == 'completed'
    assert not any(d.severity == 'ERROR' for d in result.diagnostics)
    graph = result.ontology

    expected_edges = {(BASE.tMiddle, BASE.tGeneral), (BASE.tLeaf, BASE.tMiddle), (BASE.tSibling, BASE.tGeneral)}
    if set_case == 'singleton_complete':
        expected_edges.add((BASE.tGeneral, BASE.tMiddle))
    assert _edges(graph) == expected_edges
    for key, dt_iri in (('General', XSD.int), ('Middle', XSD.string), ('Leaf', XSD.string), ('Sibling', XSD.int)):
        prop = BASE['t' + key]
        assert (prop, RDF.type, OWL.DatatypeProperty) in graph
        assert set(graph.objects(prop, RDFS.range)) == {dt_iri}
        assert not any(BASE['s' + key] in triple for triple in graph)
    assert not list(graph.subject_objects(OWL.inverseOf))
    assert not list(graph.triples((None, OWL.equivalentProperty, None)))

    expected_pairs = ({frozenset((BASE.tMiddle, BASE.tSibling))}
                      if set_case in {'disjoint', 'multi_complete'} else set())
    assert _pairs(graph) == expected_pairs

    if set_case == 'singleton_complete':
        assert any(d.kind == 'singleton_completeness' and d.severity == 'INFO'
                   and {'gsRelations', 'rGeneral', 'rMiddle'} <= set(d.identified_sources)
                   and {'extensional_equivalence', 'distinct_identifiers'} <= d.facts
                   for d in result.diagnostics)
        assert not any(d.severity == 'WARNING' for d in result.diagnostics)
    elif set_case == 'multi_complete':
        assert any(d.kind == 'relation_set_completeness' and d.severity == 'WARNING'
                   and 'gsRelations' in d.identified_sources
                   and 'coverage_not_represented' in d.facts
                   for d in result.diagnostics)
    else:
        assert not any(d.severity == 'WARNING' for d in result.diagnostics)


@pytest.mark.parametrize('input_policy', POLICIES)
@pytest.mark.parametrize('direction', ['obj_sub_data_super', 'data_sub_obj_super'])
@pytest.mark.parametrize('singleton_complete', [False, True], ids=['open', 'singleton_complete'])
def test_mixed_kind_relation_generalization_reports_error_and_never_activates_singleton(
        run, source_json, tmp_path, input_policy, direction, singleton_complete):
    """Rules: DK-REL-01, DK-REL-14, DK-REL-20, DK-DIAG-14, DK-DIAG-05.

    RD-02 Q6b & Conflict I: mixed object/data relation generalizations report
    a structural ERROR; best-effort omits only the incompatible hierarchy edge
    without activating singleton completeness or DK-DIAG-14 INFO.
    """
    document = source_json('relations/hierarchy')
    document['model']['contents'].append(_datatype_class(document, 'dInt', 'int'))
    if direction == 'obj_sub_data_super':
        source_element(document, 'sGeneral')['name'] = None
        source_element(document, 'tGeneral')['propertyType'] = {'id': 'dInt', 'type': 'Class'}
    else:
        source_element(document, 'sMiddle')['name'] = None
        source_element(document, 'tMiddle')['propertyType'] = {'id': 'dInt', 'type': 'Class'}
    source_element(document, 'gsRelations').update(
        isComplete=singleton_complete, isDisjoint=False,
        generalizations=[{'id': 'gMiddle', 'type': 'Generalization'}])
    assert not fixture_issues(document)

    result = run(path=write_input(tmp_path, document), iri_strategy='id',
                 inverse_properties='all', input_policy=input_policy)
    assert any(
        d.severity == 'ERROR'
        and 'mixed_property_kind_generalization' in d.facts
        and 'gMiddle' in d.identified_sources
        and d.code != 'INTERNAL_TRANSFORMATION_FAILURE'
        for d in result.diagnostics
    ), result.diagnostics
    assert not any(d.kind == 'singleton_completeness' for d in result.diagnostics)

    if input_policy != 'best-effort':
        assert result.outcome == 'aborted' and result.ontology is None
        return

    assert result.outcome == 'completed-with-errors'
    graph = result.ontology
    expected_edges = set()
    if direction == 'obj_sub_data_super':
        # rMiddle/rLeaf/rSibling are all ObjectProperties; rGeneral is DatatypeProperty.
        expected_edges |= {(BASE.tLeaf, BASE.tMiddle), (BASE.sLeaf, BASE.sMiddle)}
        assert (BASE.tGeneral, RDF.type, OWL.DatatypeProperty) in graph
        assert (BASE.tMiddle, RDF.type, OWL.ObjectProperty) in graph
    else:
        # rMiddle is DatatypeProperty; rGeneral/rLeaf/rSibling are ObjectProperties.
        expected_edges |= {(BASE.tSibling, BASE.tGeneral), (BASE.sSibling, BASE.sGeneral)}
        assert (BASE.tMiddle, RDF.type, OWL.DatatypeProperty) in graph
        assert (BASE.tGeneral, RDF.type, OWL.ObjectProperty) in graph
    assert _edges(graph) == expected_edges
    assert (BASE.tMiddle, RDFS.subPropertyOf, BASE.tGeneral) not in graph
    assert (BASE.tGeneral, RDFS.subPropertyOf, BASE.tMiddle) not in graph
    assert (BASE.sGeneral, RDFS.subPropertyOf, BASE.sMiddle) not in graph


@pytest.mark.parametrize('input_policy', POLICIES)
@pytest.mark.parametrize('inverse_mode', ['all', 'none'])
@pytest.mark.parametrize('case', ['multi_disjoint_mixed', 'two_member_mixed_complete_no_singleton'])
def test_cross_kind_disjoint_relation_generalization_set_retains_only_homogeneous_pairs(
        run, source_json, tmp_path, input_policy, inverse_mode, case):
    """Rules: DK-REL-01, DK-REL-14, DK-REL-15, DK-REL-16, DK-REL-20, DK-INV-12, DK-DIAG-14, DK-DIAG-05.

    RD-02 Q6b & Conflict I: cross-kind disjointness pairs report structural
    ERROR; best-effort omits only cross-kind pairs and mixed edges while keeping
    homogeneous disjointness pairs (and inverses) and never promoting a sole
    surviving member to singleton completeness.
    """
    document = source_json('relations/hierarchy')
    document['model']['contents'].append(_datatype_class(document, 'dInt', 'int'))
    source_element(document, 'sSibling')['name'] = None
    source_element(document, 'tSibling')['propertyType'] = {'id': 'dInt', 'type': 'Class'}

    if case == 'multi_disjoint_mixed':
        peer = copy.deepcopy(source_element(document, 'rMiddle'))
        peer.update(id='rPeer', name='peer')
        peer['properties'][0]['id'] = 'sPeer'
        peer['properties'][1]['id'] = 'tPeer'
        g_peer = copy.deepcopy(source_element(document, 'gMiddle'))
        g_peer.update(id='gPeer', specific={'id': 'rPeer', 'type': 'Relation'})
        document['model']['contents'].extend([peer, g_peer])
        source_element(document, 'gsRelations').update(
            isDisjoint=True, isComplete=True,
            generalizations=[{'id': i, 'type': 'Generalization'} for i in ('gMiddle', 'gPeer', 'gSibling')])
    else:
        # 2-member set where gSibling is mixed-kind leaving only gMiddle surviving: must NOT become singleton.
        source_element(document, 'gsRelations').update(
            isDisjoint=True, isComplete=True,
            generalizations=[{'id': 'gMiddle', 'type': 'Generalization'}, {'id': 'gSibling', 'type': 'Generalization'}])
    assert not fixture_issues(document)

    result = run(path=write_input(tmp_path, document), iri_strategy='id',
                 inverse_properties=inverse_mode, input_policy=input_policy)
    assert any(
        d.severity == 'ERROR'
        and 'mixed_property_kind_disjointness' in d.facts
        and 'gsRelations' in d.identified_sources
        and d.code != 'INTERNAL_TRANSFORMATION_FAILURE'
        for d in result.diagnostics
    ), result.diagnostics
    assert any(
        d.severity == 'ERROR'
        and 'mixed_property_kind_generalization' in d.facts
        and 'gSibling' in d.identified_sources
        for d in result.diagnostics
    ), result.diagnostics
    assert not any(d.kind == 'singleton_completeness' for d in result.diagnostics)

    if input_policy != 'best-effort':
        assert result.outcome == 'aborted' and result.ontology is None
        return

    assert result.outcome == 'completed-with-errors'
    graph = result.ontology
    assert (BASE.tSibling, RDF.type, OWL.DatatypeProperty) in graph
    assert (BASE.tSibling, RDFS.subPropertyOf, BASE.tGeneral) not in graph
    assert (BASE.tGeneral, RDFS.subPropertyOf, BASE.tMiddle) not in graph
    assert (BASE.sGeneral, RDFS.subPropertyOf, BASE.sMiddle) not in graph

    edges = {(BASE.tMiddle, BASE.tGeneral), (BASE.tLeaf, BASE.tMiddle)}
    if case == 'multi_disjoint_mixed':
        edges.add((BASE.tPeer, BASE.tGeneral))
    if inverse_mode == 'all':
        edges |= {(BASE.sMiddle, BASE.sGeneral), (BASE.sLeaf, BASE.sMiddle)}
        if case == 'multi_disjoint_mixed':
            edges.add((BASE.sPeer, BASE.sGeneral))
    assert _edges(graph) == edges

    expected_pairs = set()
    if case == 'multi_disjoint_mixed':
        expected_pairs.add(frozenset((BASE.tMiddle, BASE.tPeer)))
        if inverse_mode == 'all':
            expected_pairs.add(frozenset((BASE.sMiddle, BASE.sPeer)))
    assert _pairs(graph) == expected_pairs


def test_rd02_relation_diagnostic_reader_requires_affirmative_conditions():
    """Harness only: verify affirmative RD-02 datatype-relation and mixed-kind wording without fixing provisional codes."""
    accepted = {
        'void_relation_target': (
            "Relation 'rFocus' target resolves to Visual Paradigm 'void', which has no registered datatype mapping.",
            "Ordinary binary relation 'rFocus' targets void (no datatype mapping exists).",
        ),
        'non_class_relation_source': (
            "Relation 'rFocus' source resolves to primitive datatype 'dInt', which lacks a generated local owl:Class.",
            "Primitive source 'dInt' has no local OWL class for relation 'rFocus'.",
        ),
        'incompatible_datatype_relation_stereotype': (
            "Datatype-valued relation 'rFocus' cannot use stereotype 'mediation', which requires an owl:ObjectProperty.",
            "Stereotype 'componentOf' is incompatible with owl:DatatypeProperty mapping on relation 'rFocus'.",
        ),
        'incompatible_material_chain': (
            "Material property chain on 'rMaterial' requires an owl:ObjectProperty and is incompatible with a datatype-valued relation.",
            "Datatype-valued relation 'rMaterial' conflicts with eligible material-property chain.",
        ),
        'incompatible_comparative_derivation': (
            "Comparative-quality derivation on 'rDerivation' requires an owl:ObjectProperty and is incompatible with datatype-valued relation 'rMaterial'.",
            "Datatype-valued relation 'rMaterial' conflicts with recognized comparative-quality derivation.",
        ),
        'incompatible_source_multiplicity': (
            "Datatype-valued relation 'rFocus' source-end multiplicity '1' requires an unavailable inverse datatype property.",
            "Source-end cardinality on datatype-valued relation 'rFocus' cannot be represented without an inverse.",
        ),
        'unrepresentable_source_role': (
            "Source-end role name 'workers' on datatype-valued relation 'rFocus' cannot be represented because no inverse property exists.",
            "Unrepresentable source-end role name on datatype relation 'rFocus': omitted without an inverse.",
        ),
        'unavailable_datatype_inverse_reference': (
            "Property subsettedProperties reference on 'sData' requires an unavailable inverse of datatype property 'tData'.",
            "Source association end 'sData' of datatype-valued relation has no inverse for subsetting.",
        ),
        'mixed_property_kind_inclusion': (
            "Property inclusion in subsettedProperties mixes owl:ObjectProperty 'pChild' and owl:DatatypeProperty 'pBase'.",
            "Mixed object/data property-kind incompatibility in redefinedProperties on 'pChild'.",
        ),
        'mixed_property_kind_generalization': (
            "Relation generalization 'gMiddle' has mixed owl:ObjectProperty and owl:DatatypeProperty kinds.",
            "Subproperty generalization 'gMiddle' cannot connect owl:ObjectProperty and owl:DatatypeProperty.",
        ),
        'mixed_property_kind_disjointness': (
            "Disjoint relation generalization set 'gsRelations' contains a cross-kind pair of owl:ObjectProperty and owl:DatatypeProperty.",
            "Mixed property-kind incompatibility for disjointness pair in generalization set 'gsRelations'.",
        ),
    }
    for expected_fact, messages in accepted.items():
        severity = 'WARNING' if expected_fact == 'unrepresentable_source_role' else 'ERROR'
        for message in messages:
            assert expected_fact in rd02_relation_diagnostic(severity, message), (expected_fact, message)

    rejected = (
        ('ERROR', "Ordinary relation endpoints without local class representations remain unspecified."),
        ('ERROR', "Unexpected internal failure while transforming relation."),
        ('ERROR', "Attribute explicitly uses recognized unsupported Visual Paradigm void; no mapping or range is supplied."),
        ('ERROR', "Relation end cardinality 'n..m' is not wholly translatable under the accepted syntax."),
        ('ERROR', "If a datatype-valued relation has stereotype 'mediation', conversion aborts."),
        ('ERROR', "Property inclusion is not mixed and has no property-kind incompatibility."),
        ('WARNING', "Source-end role name is represented on the inverse property."),
        ('ERROR', "Relation 'rFocus' stereotype 'mediation' is not incompatible with owl:ObjectProperty."),
    )
    for severity, message in rejected:
        assert not rd02_relation_diagnostic(severity, message), (severity, message)


def _third_relation_end():
    return {
        'id': 'eThird', 'name': 'thirdRole', 'description': 'Third end description.',
        'type': 'Property', 'propertyAssignments': None, 'stereotype': 'end',
        'isDerived': True, 'isReadOnly': True, 'isOrdered': True, 'cardinality': '1..*',
        'propertyType': {'id': 'cExtra', 'type': 'Class'},
        'subsettedProperties': None, 'redefinedProperties': None, 'aggregationKind': 'SHARED',
    }


def _mutate_relation_properties(relation, source_end, target_end, container_case):
    if container_case == 'absent':
        relation.pop('properties', None)
        return {'nonbinary_relation'}, {'relation_properties_absent'}
    if container_case == 'null':
        relation['properties'] = None
        return {'nonbinary_relation'}, {'relation_properties_null'}
    if container_case == 'non_array_object':
        relation['properties'] = copy.deepcopy(source_end)
        return {'nonbinary_relation', 'malformed_properties'}, {'relation_properties_non_array'}
    if container_case == 'non_array_string':
        relation['properties'] = 'bad'
        return {'nonbinary_relation', 'malformed_properties'}, {'relation_properties_non_array'}
    if container_case == 'non_array_empty_string':
        relation['properties'] = ''
        return {'nonbinary_relation', 'malformed_properties'}, {'relation_properties_non_array'}
    if container_case == 'non_array_zero':
        relation['properties'] = 0
        return {'nonbinary_relation', 'malformed_properties'}, {'relation_properties_non_array'}
    if container_case == 'non_array_number':
        relation['properties'] = 42
        return {'nonbinary_relation', 'malformed_properties'}, {'relation_properties_non_array'}
    if container_case == 'non_array_false':
        relation['properties'] = False
        return {'nonbinary_relation', 'malformed_properties'}, {'relation_properties_non_array'}
    if container_case == 'non_array_true':
        relation['properties'] = True
        return {'nonbinary_relation', 'malformed_properties'}, {'relation_properties_non_array'}
    if container_case == 'non_object_null_entry':
        relation['properties'] = [None, copy.deepcopy(target_end)]
        return {'unresolved_endpoint', 'malformed_declaration'}, {'relation_properties_malformed_entry'}
    if container_case == 'non_object_string_entry':
        relation['properties'] = [copy.deepcopy(source_end), 'bad']
        return {'unresolved_endpoint', 'malformed_declaration'}, {'relation_properties_malformed_entry'}
    if container_case == 'non_object_number_entry':
        relation['properties'] = [123]
        return {'nonbinary_relation', 'unresolved_endpoint', 'malformed_declaration'}, {
            'relation_properties_malformed_entry', 'relation_properties_non_binary',
        }
    if container_case == 'non_property_class_entry':
        relation['properties'] = [{'id': 'cA', 'type': 'Class'}, copy.deepcopy(target_end)]
        return {'unresolved_endpoint', 'wrong_container_type', 'unknown_field:stereotype',
                'unknown_field:isAbstract', 'unknown_field:isExtensional', 'unknown_field:isPowertype',
                'unknown_field:order', 'unknown_field:literals', 'unknown_field:restrictedTo'}, {
            'relation_properties_malformed_entry',
        }
    if container_case == 'empty':
        relation['properties'] = []
        return {'nonbinary_relation'}, {'relation_properties_non_binary'}
    if container_case == 'unary':
        relation['properties'] = [copy.deepcopy(source_end)]
        return {'nonbinary_relation'}, {'relation_properties_non_binary'}
    if container_case == 'n_ary':
        relation['properties'] = [copy.deepcopy(source_end), copy.deepcopy(target_end), _third_relation_end()]
        return {'nonbinary_relation'}, {'relation_properties_non_binary'}
    raise AssertionError(f'Unknown container case: {container_case}')


_RELATION_CONTAINER_CASES = [
    'absent', 'null', 'non_array_object', 'non_array_string', 'non_array_empty_string',
    'non_array_zero', 'non_array_number', 'non_array_false', 'non_array_true',
    'non_object_null_entry', 'non_object_string_entry', 'non_object_number_entry', 'non_property_class_entry',
    'empty', 'unary', 'n_ary',
]


@pytest.mark.parametrize('input_policy', POLICIES)
@pytest.mark.parametrize('strategy', ['name', 'id'])
@pytest.mark.parametrize('relation_kind', ['ordinary', 'derivation'])
@pytest.mark.parametrize('container_case', _RELATION_CONTAINER_CASES)
def test_non_instantiation_relation_rejects_missing_malformed_or_non_binary_properties(
        run, source_json, tmp_path, input_policy, strategy, relation_kind, container_case):
    """Rules: DK-DIAG-03, DK-DIAG-05, DK-DIAG-01, DK-INV-02, DK-DIAG-04, DK-REL-08, DK-REL-17, DK-REL-18; §3.2. RD-02 Alternative A."""
    document = source_json('shared/binary_relation')
    c_extra = copy.deepcopy(source_element(document, 'cA'))
    c_extra.update(id='cExtra', name='ExtraClass')
    c_peer = copy.deepcopy(source_element(document, 'cA'))
    c_peer.update(id='cPeer', name='PeerClass')
    peer_rel = copy.deepcopy(source_element(document, 'rFocus'))
    peer_rel.update(id='rPeer', name='worksFor', stereotype='material')
    peer_rel['properties'][0].update(id='sPeer', name=None, propertyType={'id': 'cA', 'type': 'Class'})
    peer_rel['properties'][1].update(id='tPeer', name=None, cardinality='1', propertyType={'id': 'cPeer', 'type': 'Class'})
    document['model']['contents'].extend([c_extra, c_peer, peer_rel])

    focus = source_element(document, 'rFocus')
    s_focus = copy.deepcopy(source_element(document, 'sFocus'))
    t_focus = copy.deepcopy(source_element(document, 'tFocus'))
    if relation_kind == 'derivation':
        focus.update(stereotype='derivation', name=None)
        s_focus['propertyType'] = {'id': 'rPeer', 'type': 'Relation'}
        t_focus['propertyType'] = {'id': 'cA', 'type': 'Class'}
    expected_issues, expected_facts = _mutate_relation_properties(focus, s_focus, t_focus, container_case)
    if container_case == 'non_property_class_entry':
        focus['properties'][0] = copy.deepcopy(source_element(document, 'cA'))
        focus['properties'][0]['id'] = 'cFakeProp'
        assert expected_issues <= fixture_issues(document)
    else:
        assert fixture_issues(document) == expected_issues

    result = run(path=write_input(tmp_path, document), iri_strategy=strategy,
                 input_policy=input_policy, inverse_properties='all')
    assert any(
        d.severity == 'ERROR'
        and (expected_facts & d.facts)
        and 'rFocus' in d.identified_sources
        and d.code != 'INTERNAL_TRANSFORMATION_FAILURE'
        and isinstance(d.code, str) and d.code
        and d.code not in STABLE_DIAGNOSTIC_CODES
        for d in result.diagnostics
    ), result.diagnostics
    assert not any(
        d.kind in NAMING_KINDS and {'rFocus', 'sFocus', 'tFocus', 'eThird'} & set(d.identified_sources)
        for d in result.diagnostics
    )
    assert not any(d.kind in {'unsupported_connector', 'comparative_derivation_semantics'}
                   or d.code in {'UNSUPPORTED_RELATION_CONNECTOR', 'UNSUPPORTED_COMPARATIVE_DERIVATION'}
                   for d in result.diagnostics)

    if input_policy != 'best-effort':
        assert result.outcome == 'aborted' and result.ontology is None and result.provenance is None
        return

    assert result.outcome == 'completed-with-errors'
    graph = result.ontology
    _assert_no_relation_triples(graph, 'rFocus', 'sFocus', 'tFocus', 'eThird', 'cFakeProp')
    for omitted_id in ('rFocus', 'eThird', 'cFakeProp'):
        assert not list(graph.subjects(DCTERMS.identifier, Literal(omitted_id)))
    c_a = BASE.cA if strategy == 'id' else BASE.HTTPServer
    c_peer_iri = BASE.cPeer if strategy == 'id' else BASE.PeerClass
    assert (c_a, RDF.type, OWL.Class) in graph
    assert (c_peer_iri, RDF.type, OWL.Class) in graph
    t_peer = _primary(result, 'tPeer', strategy)
    s_peer = _primary(result, 'sPeer', strategy)
    assert {s for s in graph.subjects(RDF.type, OWL.ObjectProperty)
            if str(s).startswith(str(BASE))} == {t_peer, s_peer}
    assert not list(graph.subjects(RDF.type, OWL.DatatypeProperty))
    if strategy == 'name':
        # Omitted rFocus must not claim worksFor or workers and force a suffix on peer_rel.
        assert t_peer == BASE.worksFor
        assert s_peer == BASE.inverseOfWorksFor
    _counts(graph, c_a, t_peer, {('exact', 1)})


@pytest.mark.parametrize('scenario', [
    'mereology_n_ary',
    'mereology_unary',
    'mereology_null',
    'mereology_mixed_entry',
    'material_n_ary_with_chains',
    'derivation_absent_breaks_grounding',
    'derivation_null_breaks_grounding',
    'derivation_unary_breaks_grounding',
    'derivation_n_ary_breaks_grounding',
    'comparative_derivation_n_ary',
])
def test_best_effort_omitted_non_binary_or_malformed_relation_suppresses_all_dependent_outputs(
        run, source_json, tmp_path, scenario):
    """Rules: DK-DIAG-03, DK-DIAG-05, DK-REL-07, DK-REL-08, DK-REL-18, DK-REL-19, DK-GEN-04, DK-PROP-04, DK-PROP-05, DK-PROP-06, DK-DIAG-15, DK-DIAG-16, DK-DIAG-18. RD-02 Alternative A."""
    if scenario.startswith('mereology_'):
        document = source_json('shared/binary_relation')
        c_extra = copy.deepcopy(source_element(document, 'cA'))
        c_extra.update(id='cExtra', name='ExtraClass')
        c_peer = copy.deepcopy(source_element(document, 'cA'))
        c_peer.update(id='cPeer', name='PeerClass')
        p_indep = {
            'id': 'pIndep', 'name': 'indepAttr', 'description': None, 'type': 'Property',
            'propertyAssignments': None, 'stereotype': None, 'isDerived': False,
            'isReadOnly': False, 'isOrdered': False, 'cardinality': '1',
            'propertyType': None, 'subsettedProperties': None, 'redefinedProperties': None,
            'aggregationKind': None,
        }
        source_element(document, 'cA')['properties'] = [p_indep]
        peer_rel = copy.deepcopy(source_element(document, 'rFocus'))
        peer_rel.update(id='rPeer', name='peerLink', stereotype='material')
        peer_rel['properties'][0].update(id='sPeer', name=None, propertyType={'id': 'cA', 'type': 'Class'})
        peer_rel['properties'][1].update(id='tPeer', name=None, cardinality='1', propertyType={'id': 'cPeer', 'type': 'Class'})
        document['model']['contents'].extend([c_extra, c_peer, peer_rel])

        focus = source_element(document, 'rFocus')
        focus.update(stereotype='componentOf', isAbstract=True, isDerived=True, description='OMITTED_REL_DESC')
        s_focus = copy.deepcopy(source_element(document, 'sFocus'))
        t_focus = copy.deepcopy(source_element(document, 'tFocus'))
        for end, desc in ((s_focus, 'OMITTED_SRC_DESC'), (t_focus, 'OMITTED_TGT_DESC')):
            end.update(description=desc, stereotype='begin', isDerived=True, isReadOnly=True,
                       isOrdered=True, cardinality='2..5', aggregationKind='COMPOSITE')
        case = scenario.removeprefix('mereology_')
        if case == 'n_ary':
            focus['properties'] = [s_focus, t_focus, _third_relation_end()]
            expected_fact = 'relation_properties_non_binary'
        elif case == 'unary':
            focus['properties'] = [s_focus]
            expected_fact = 'relation_properties_non_binary'
        elif case == 'null':
            focus['properties'] = None
            expected_fact = 'relation_properties_null'
        else:
            focus['properties'] = [None, t_focus]
            expected_fact = 'relation_properties_malformed_entry'

        result = run(path=write_input(tmp_path, document), iri_strategy='id',
                     input_policy='best-effort', dkgm_vocabulary='none')
        assert result.outcome == 'completed-with-errors'
        assert any(d.severity == 'ERROR' and expected_fact in d.facts and 'rFocus' in d.identified_sources
                   for d in result.diagnostics), result.diagnostics
        assert not any(d.kind in {'abstractness', 'derived_status', 'ordering'}
                       and {'rFocus', 'sFocus', 'tFocus', 'eThird'} & set(d.identified_sources)
                       for d in result.diagnostics)
        assert not any(DKGM_CHAIN_WARNING_FACTS & d.facts for d in result.diagnostics)
        graph = result.ontology
        _assert_no_relation_triples(graph, 'rFocus', 'sFocus', 'tFocus', 'eThird')
        assert not any(s == DKGM.componentOf or o == DKGM.componentOf for s, _, o in graph)
        assert not list(graph.subjects(RDF.type, OWL.AsymmetricProperty))
        for text_val in ('OMITTED_REL_DESC', 'OMITTED_SRC_DESC', 'OMITTED_TGT_DESC', 'Third end description.'):
            assert not list(graph.triples((None, RDFS.comment, Literal(text_val))))
        assert not any(isinstance(s, BNode) and (BASE.cB, RDFS.subClassOf, s) in graph for s in graph.subjects())
        assert not any(isinstance(s, BNode) and (BASE.cExtra, RDFS.subClassOf, s) in graph for s in graph.subjects())
        assert {s for s in graph.subjects(RDF.type, OWL.DatatypeProperty)
                if str(s).startswith(str(BASE))} == {BASE.pIndep}
        assert {s for s in graph.subjects(RDF.type, OWL.ObjectProperty)
                if str(s).startswith(str(BASE))} == {BASE.tPeer, BASE.sPeer}
        _counts(graph, BASE.cA, BASE.tPeer, {('exact', 1)})
        return

    document = source_json('shared/material_pattern')
    c_extra = copy.deepcopy(source_element(document, 'cA'))
    c_extra.update(id='cExtra', name='ExtraClass')
    document['model']['contents'].append(c_extra)
    if scenario == 'comparative_derivation_n_ary':
        source_element(document, 'cGround')['stereotype'] = 'quality'
        source_element(document, 'rMaterial').update(stereotype='comparative', name='compRel')
        source_element(document, 'tMaterial')['name'] = None
        deriv = source_element(document, 'rDerivation')
        deriv['properties'].append(_third_relation_end())
        expected_id, expected_fact = 'rDerivation', 'relation_properties_non_binary'
    else:
        _grounding(document, 'relator')
        if scenario == 'material_n_ary_with_chains':
            mat = source_element(document, 'rMaterial')
            mat['properties'].append(_third_relation_end())
            expected_id, expected_fact = 'rMaterial', 'relation_properties_non_binary'
        else:
            deriv = source_element(document, 'rDerivation')
            s_der, t_der = deriv['properties']
            sub = scenario.removeprefix('derivation_').removesuffix('_breaks_grounding')
            sub_case = {'absent': 'absent', 'null': 'null', 'unary': 'unary', 'n_ary': 'n_ary'}[sub]
            _, facts = _mutate_relation_properties(deriv, s_der, t_der, sub_case)
            expected_id, expected_fact = 'rDerivation', next(iter(facts))
            # Clear rMaterial name so if rDerivation were recognized, relator naming would apply.
            source_element(document, 'rMaterial')['name'] = None
            source_element(document, 'tMaterial')['name'] = None

    result = run(path=write_input(tmp_path, document), iri_strategy='name',
                 input_policy='best-effort', material_property_chains='omit-conflicting-constraints')
    assert result.outcome == 'completed-with-errors'
    assert any(d.severity == 'ERROR' and expected_fact in d.facts and expected_id in d.identified_sources
               and d.code != 'INTERNAL_TRANSFORMATION_FAILURE'
               for d in result.diagnostics), result.diagnostics
    graph = result.ontology
    assert not list(graph.triples((None, OWL.propertyChainAxiom, None)))
    assert not any(d.kind == 'chain_compatibility' for d in result.diagnostics)
    assert not any(d.kind in {'unsupported_connector', 'relator_naming', 'comparative_derivation_semantics'}
                   or d.code in {'UNSUPPORTED_RELATION_CONNECTOR', 'UNSUPPORTED_COMPARATIVE_DERIVATION'}
                   for d in result.diagnostics)
    assert not list(graph.subjects(DCTERMS.identifier, Literal('eThird')))
    t_left = one_subject(graph, DCTERMS.identifier, Literal('tLeft'))
    t_right = one_subject(graph, DCTERMS.identifier, Literal('tRight'))
    t_unrelated = one_subject(graph, DCTERMS.identifier, Literal('tUnrelated'))
    assert (t_left, RDF.type, OWL.ObjectProperty) in graph
    assert (t_right, RDF.type, OWL.ObjectProperty) in graph
    assert (t_unrelated, RDF.type, OWL.ObjectProperty) in graph
    if scenario == 'material_n_ary_with_chains':
        assert not list(graph.subjects(DCTERMS.identifier, Literal('tMaterial')))
        assert not list(graph.subjects(DCTERMS.identifier, Literal('sMaterial')))
    else:
        t_mat = one_subject(graph, DCTERMS.identifier, Literal('tMaterial'))
        if scenario == 'comparative_derivation_n_ary':
            assert t_mat == BASE.compRel
        else:
            assert t_mat == BASE.participantA_participantB
        assert not list(graph.subjects(DCTERMS.identifier, Literal('rDerivation')))
        assert not list(graph.subjects(DCTERMS.identifier, Literal('sDerivation')))
        assert not list(graph.subjects(DCTERMS.identifier, Literal('tDerivation')))


@pytest.mark.parametrize('input_policy', POLICIES)
@pytest.mark.parametrize('mode', ['all', 'none'])
@pytest.mark.parametrize('container_case', ['absent', 'null', 'non_array_object', 'non_object_null_entry', 'empty', 'unary', 'n_ary'])
@pytest.mark.parametrize('hierarchy_case', [
    'failed_specific_two_member_complete_no_singleton',
    'failed_specific_three_member_disjoint',
    'failed_general_disjoint',
    'failed_singleton_complete',
])
def test_relation_generalization_and_sets_treat_non_binary_or_malformed_relations_as_failed(
        run, source_json, tmp_path, input_policy, mode, container_case, hierarchy_case):
    """Rules: DK-REL-14, DK-REL-15, DK-REL-20, DK-INV-12, DK-DIAG-03, DK-DIAG-05, DK-DIAG-14. RD-02 Alternative A."""
    document = source_json('relations/hierarchy')
    c_extra = copy.deepcopy(source_element(document, 'cA'))
    c_extra.update(id='cExtra', name='ExtraClass')
    document['model']['contents'].append(c_extra)

    gs = source_element(document, 'gsRelations')
    if hierarchy_case == 'failed_specific_two_member_complete_no_singleton':
        gs.update(isComplete=True, isDisjoint=True)
        target_rel = source_element(document, 'rSibling')
        expected_failed_gens = {'gSibling'}
    elif hierarchy_case == 'failed_specific_three_member_disjoint':
        extra = copy.deepcopy(source_element(document, 'gMiddle'))
        extra.update(id='gLeafGeneral', specific={'id': 'rLeaf', 'type': 'Relation'})
        document['model']['contents'].append(extra)
        gs.update(isComplete=True, isDisjoint=True,
                  generalizations=[{'id': i, 'type': 'Generalization'} for i in ('gMiddle', 'gLeafGeneral', 'gSibling')])
        target_rel = source_element(document, 'rSibling')
        expected_failed_gens = {'gSibling'}
    elif hierarchy_case == 'failed_general_disjoint':
        gs.update(isComplete=True, isDisjoint=True)
        target_rel = source_element(document, 'rGeneral')
        expected_failed_gens = {'gMiddle', 'gSibling'}
    else:
        gs.update(isComplete=True, isDisjoint=False, generalizations=[{'id': 'gMiddle', 'type': 'Generalization'}])
        target_rel = source_element(document, 'rMiddle')
        expected_failed_gens = {'gMiddle', 'gLeaf'}

    s_end, t_end = target_rel['properties']
    _, expected_facts = _mutate_relation_properties(target_rel, s_end, t_end, container_case)

    result = run(path=write_input(tmp_path, document), iri_strategy='id',
                 inverse_properties=mode, input_policy=input_policy)
    assert any(
        d.severity == 'ERROR' and (expected_facts & d.facts)
        and target_rel['id'] in d.identified_sources
        and d.code != 'INTERNAL_TRANSFORMATION_FAILURE'
        for d in result.diagnostics
    ), result.diagnostics
    assert not any(d.kind == 'singleton_completeness' for d in result.diagnostics)

    if input_policy != 'best-effort':
        assert result.outcome == 'aborted' and result.ontology is None
        return

    assert result.outcome == 'completed-with-errors'
    for gen_id in expected_failed_gens:
        assert any(
            d.severity == 'ERROR' and d.kind == 'failed_relation_generalization'
            and gen_id in d.identified_sources
            for d in result.diagnostics
        ), (gen_id, result.diagnostics)

    graph = result.ontology
    assert not list(graph.triples((None, OWL.equivalentProperty, None)))
    prefixes = ('t', 's') if mode == 'all' else ('t',)
    if hierarchy_case == 'failed_specific_two_member_complete_no_singleton':
        edges = [('Middle', 'General'), ('Leaf', 'Middle')]
        pairs = set()
        valid = {'General', 'Middle', 'Leaf'}
    elif hierarchy_case == 'failed_specific_three_member_disjoint':
        edges = [('Middle', 'General'), ('Leaf', 'Middle'), ('Leaf', 'General')]
        pairs = {frozenset((BASE[p + 'Middle'], BASE[p + 'Leaf'])) for p in prefixes}
        valid = {'General', 'Middle', 'Leaf'}
    elif hierarchy_case == 'failed_general_disjoint':
        edges = [('Leaf', 'Middle')]
        pairs = {frozenset((BASE[p + 'Middle'], BASE[p + 'Sibling'])) for p in prefixes}
        valid = {'Middle', 'Leaf', 'Sibling'}
    else:
        edges = [('Sibling', 'General')]
        pairs = set()
        valid = {'General', 'Leaf', 'Sibling'}

    assert _edges(graph) == {(BASE[p + a], BASE[p + b]) for p in prefixes for a, b in edges}
    assert _pairs(graph) == pairs
    assert {node for node in graph.subjects(RDF.type, OWL.ObjectProperty)
            if isinstance(node, URIRef) and str(node).startswith(str(BASE))} == {
        BASE[p + key] for p in prefixes for key in valid}
    assert (BASE.cD, RDF.type, OWL.Class) in graph


def test_relation_properties_container_reader_requires_affirmative_conditions():
    """Rules: DK-DIAG-03, DK-INS-02. Harness only: verify affirmative Relation.properties wording without fixing provisional codes."""
    accepted = {
        'relation_properties_absent': (
            "Relation 'rFocus' is missing its 'properties' field.",
            "Non-instantiation relation 'rFocus' has no properties container.",
            "The 'properties' field on relation 'rFocus' is absent.",
            "Relation 'rFocus' does not supply a properties field.",
            "Relation 'rFocus' lacks a 'properties' array.",
        ),
        'relation_properties_null': (
            "Relation 'rFocus' properties field is explicitly null.",
            "The 'properties' field on relation 'rFocus': expected a JSON array, got null.",
            "Relation 'rFocus' has null properties.",
        ),
        'relation_properties_non_array': (
            "Relation 'rFocus' properties field must be a JSON array, got dict.",
            "Relation 'rFocus' properties field must be a JSON array, not int.",
            "The 'properties' field on relation 'rFocus': expected a JSON array, got ''.",
            "Relation 'rFocus' has a non-array properties value.",
            "The 'properties' field on instantiation relation 'rInstantiation' is not a JSON array.",
            "Relation 'rFocus' properties is not null; it is a string.",
        ),
        'relation_properties_malformed_entry': (
            "Relation 'rFocus' properties[0] must be a Property object, got null.",
            "Relation 'rFocus' properties array contains a non-object entry.",
            "Relation 'rFocus' properties array contains a non-Property entry ('Class').",
            "Relation 'rFocus' properties[0] has type 'Class', expected 'Property'.",
            "Non-Property entry at relation 'rFocus' properties[0].",
            "Instantiation relation 'rInstantiation' properties contains a non-object or non-Property entry.",
        ),
        'relation_properties_non_binary': (
            "Non-instantiation relation 'rFocus' has non-binary properties array (length 3, expected 2).",
            "Relation 'rFocus' properties array is empty; expected 2 association ends.",
            "Unary relation 'rFocus' has 1 association end; binary (2 ends) is required.",
            "Unsupported n-ary relation 'rFocus' has 3 association ends.",
            "Relation 'rFocus' must have exactly 2 association ends, got 0.",
        ),
    }
    for expected_fact, messages in accepted.items():
        for message in messages:
            observed = relation_properties_container_diagnostic(message)
            assert expected_fact in observed, (expected_fact, message, observed)
            source = SimpleNamespace(identifier='rFocus', element_type='Relation')
            native = SimpleNamespace(severity='ERROR', code='PROVISIONAL_TEST_CODE',
                                     message=message, effect='Aborted.',
                                     sources=(source,), generated_iri=None)
            diag, = _observed_diagnostics((native,), retain_unclassified=True)
            assert expected_fact in diag.facts

    rejected = (
        "Non-binary/malformed relation-container handling is outside this increment.",
        "Malformed instantiation-container recovery remains unspecified.",
        "Unexpected internal failure while transforming relation.",
        "Relation 'rFocus' properties is absent or null.",
        "Relation 'rFocus' properties is missing or not an array.",
        "Relation 'rFocus' properties is null or non-binary.",
        "Relation 'rFocus' properties is not absent.",
        "Relation 'rFocus' properties is not null.",
        "Relation 'rFocus' properties is not non-binary.",
        "Relation 'rFocus' properties is binary.",
        "If a relation has non-binary properties, conversion aborts.",
        "Relation 'rFocus' properties may be empty.",
        "Class 'cA' has a non-array properties field.",
        "GeneralizationSet 'gsFirst' generalizations is null.",
    )
    for message in rejected:
        assert not relation_properties_container_diagnostic(message), message



