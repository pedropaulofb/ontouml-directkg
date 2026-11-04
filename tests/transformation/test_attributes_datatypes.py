"""Attributes, bounded primitive recognition, structured values and multiplicity."""

import copy
import pytest
from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, XSD

from tests.support.data import fixture_issues, source_element, write_input
from tests.support.invocation import diagnostic_signatures
from tests.support.rdf import (assert_contains, assert_graph_equal, cardinality_facts, load_graph,
                               necessary_restrictions, one_object, one_subject, rooted_graph)

BASE = Namespace('https://example.test/model#')
POLICIES = ['strict', 'tolerant', 'best-effort']
REGISTRY = [('boolean', XSD.boolean), ('byte', XSD.byte), ('char', XSD.string),
            ('double', XSD.double), ('float', XSD.float), ('int', XSD.int),
            ('long', XSD.long), ('short', XSD.short), ('string', XSD.string)]


def _counts(graph, owner, prop, expected, range_=None):
    """Explicit allowed count forms; no inferred count satisfies an assertion."""
    facts = cardinality_facts(graph, owner, prop)
    for _, _, qualifier, node in facts:
        assert qualifier in {None, range_, RDFS.Literal if (prop, RDF.type, OWL.DatatypeProperty) in graph else OWL.Thing}
        if qualifier is not None:
            required = OWL.onDataRange if (prop,RDF.type,OWL.DatatypeProperty) in graph else OWL.onClass
            other = OWL.onClass if required == OWL.onDataRange else OWL.onDataRange
            assert (node,required,qualifier) in graph
            assert not list(graph.objects(node,other))
    actual = frozenset((kind, value) for kind, value, _, _ in facts)
    alternatives = {frozenset(expected)}
    pairs = dict(expected)
    if 'exact' in pairs:
        n = pairs['exact']
        alternatives.add(frozenset({('min', n), ('max', n)}))
        if n == 0:
            alternatives.add(frozenset({('max', 0)}))
    assert actual in alternatives, (actual, alternatives)
    assert not list(graph.objects(owner, OWL.equivalentClass))
    assert not list(graph.subjects(OWL.equivalentClass, owner))
    # Every cardinality on this property is on its necessary-condition path.
    nodes = {node for _, _, _, node in facts}
    cardinality_predicates = {OWL.cardinality, OWL.minCardinality, OWL.maxCardinality,
                             OWL.qualifiedCardinality, OWL.minQualifiedCardinality, OWL.maxQualifiedCardinality}
    if not expected:
        # Empty means no contribution, including malformed/direct counts on
        # the property resource rather than an owl:onProperty restriction.
        assert not any((prop, predicate, None) in graph for predicate in cardinality_predicates)
    for node in graph.subjects(OWL.onProperty, prop):
        if any(list(graph.objects(node, predicate)) for predicate in cardinality_predicates):
            assert node in nodes


def _focus(graph, kind, range_, owner=BASE.cOwner, prop=BASE.pFocus):
    assert (prop, RDF.type, kind) in graph
    other = OWL.ObjectProperty if kind == OWL.DatatypeProperty else OWL.DatatypeProperty
    assert (prop, RDF.type, other) not in graph
    assert set(graph.objects(prop, RDFS.domain)) == {owner}
    assert set(graph.objects(prop, RDFS.range)) == (set() if range_ is None else {range_})
    assert not list(graph.triples((None, OWL.allValuesFrom, None)))


@pytest.mark.parametrize('iri_strategy', ['name', 'id'])
@pytest.mark.parametrize('name,target', REGISTRY, ids=[p[0] for p in REGISTRY])
def test_all_nine_registered_primitives_have_their_exact_ranges(run, source_json, tmp_path, iri_strategy, name, target):
    """Rules: DK-DAT-01, DK-DAT-02, DK-ATT-01, DK-GEN-03, DK-GEN-05, DK-ATT-04, DK-IRI-09."""
    document = source_json('attributes_datatypes/value_types')
    source_element(document, 'dValue')['name'] = name
    result = run(path=write_input(tmp_path, document), iri_strategy=iri_strategy)
    assert result.outcome == 'completed'
    prop = BASE.pFocus if iri_strategy == 'id' else one_subject(result.ontology, DCTERMS.identifier, Literal('pFocus'))
    owner = BASE.cOwner if iri_strategy == 'id' else BASE.Owner
    _focus(result.ontology, OWL.DatatypeProperty, target, owner, prop)
    assert not any(BASE.dValue in triple for triple in result.ontology)
    assert not list(result.ontology.subjects(DCTERMS.identifier, Literal('dValue')))
    # GEN-05 omits source derived-status comments, not independent metadata.
    assert not any(c.subject == target and c.field == "isDerived" for c in result.comments)
    if name == 'char':
        assert not list(result.ontology.triples((None, OWL.withRestrictions, None)))
    assert not any(d.severity in {'WARNING', 'ERROR'} for d in result.diagnostics)


EXCLUDED = ['integer', 'decimal', 'date', 'dateTime', 'time', 'anyURI', 'nonNegativeInteger',
            'positiveInteger', 'bool', 'str', 'wholeNumber', 'integer32', 'Intt', 'ints',
            'entier', 'TimeInterval', 'duration', 'xsd:integer',
            'http://www.w3.org/2001/XMLSchema#integer', 'xsd:dateTime']


@pytest.mark.parametrize('name', EXCLUDED, ids=EXCLUDED)
def test_unregistered_aliases_fuzzy_matches_and_xsd_routes_remain_custom(run, source_json, tmp_path, name):
    """Rules: DK-DAT-02, DK-DAT-05, DK-ATT-01, DK-GEN-03, DK-ATT-04."""
    document = source_json('attributes_datatypes/value_types')
    source_element(document, 'dValue')['name'] = name
    result = run(path=write_input(tmp_path, document), iri_strategy='id')
    assert result.outcome == 'completed'
    _focus(result.ontology, OWL.ObjectProperty, BASE.dValue)
    assert (BASE.dValue, RDF.type, OWL.Class) in result.ontology
    assert (BASE.dValue, RDFS.label, Literal(name)) in result.ontology
    assert not any(d.severity == 'ERROR' for d in result.diagnostics)


@pytest.mark.parametrize('name,target', [(' INT ', XSD.int), ('xsd:int', XSD.int),
    ('http://www.w3.org/2001/XMLSchema#int', XSD.int), ('i-n_t', XSD.int),
    ('ｉｎｔ', XSD.int)], ids=['trim_case_fold', 'known_prefix', 'full_namespace', 'separators', 'unicode'])
def test_recommended_primitive_normalization_does_not_expand_the_registry(run, source_json, tmp_path, name, target):
    """Rules: DK-DAT-02, DK-DAT-05, DK-ATT-01.

    Normalization mechanisms are SHOULD. Accept custom treatment if the
    implementation declines that recommendation; if recognized, only the exact
    registered target is allowed. This does not certify the recommendation.
    """
    document = source_json('attributes_datatypes/value_types')
    source_element(document, 'dValue')['name'] = name
    result = run(path=write_input(tmp_path, document), iri_strategy='id')
    assert result.outcome == 'completed'
    actual = one_object(result.ontology, BASE.pFocus, RDFS.range)
    assert actual in {target, BASE.dValue}
    _focus(result.ontology, OWL.DatatypeProperty if actual == target else OWL.ObjectProperty, actual)
    assert ((BASE.dValue, RDF.type, OWL.Class) in result.ontology) == (actual == BASE.dValue)


MULTILINGUAL = [
    pytest.param({'de': 'Ganzzahl', 'en': 'int'}, 'custom', id='selected_custom_no_translation'),
    pytest.param({'en': 'int', 'nl': 'float'}, 'int', id='selected_int_no_conflict'),
    pytest.param({'EN': 'int', 'en': 'float'}, 'float', id='original_text_tie'),
    pytest.param({'': 'void', 'en': 'int'}, 'void', id='empty_key_first_void'),
    pytest.param({'de': '___', 'en': 'int'}, 'int', id='skip_unusable'),
    pytest.param({'en': '___', 'nl': '東京'}, 'custom', id='no_eligible_candidate'),
]


@pytest.mark.parametrize('iri_strategy', ['name', 'id'])
@pytest.mark.parametrize('names,selected', MULTILINGUAL)
def test_multilingual_primitive_lookup_uses_only_selected_original_text(run, source_json, tmp_path, iri_strategy, names, selected):
    """Rules: DK-DAT-02, DK-DAT-04, DK-DAT-05, DK-IRI-10, DK-ATT-01, DK-LBL-01, DK-LBL-02."""
    for reverse, override in [(False, None), (True, None), (False, 'nl')]:
        document = source_json('attributes_datatypes/value_types')
        document['languages'] = ['nl']
        source_element(document, 'dValue')['name'] = dict(reversed(list(names.items()))) if reverse else copy.deepcopy(names)
        # Even a source ID resembling another primitive must not supply lookup.
        source_element(document, 'dValue')['id'] = 'double'
        source_element(document, 'pFocus')['propertyType']['id'] = 'double'
        options = {} if override is None else {'language': override}
        result = run(path=write_input(tmp_path, document), iri_strategy=iri_strategy, **options)
        assert result.outcome == 'completed'
        prop = BASE.pFocus if iri_strategy == 'id' else one_subject(result.ontology, DCTERMS.identifier, Literal('pFocus'))
        owner = BASE.cOwner if iri_strategy == 'id' else BASE.Owner
        if selected in {'int', 'float'}:
            _focus(result.ontology, OWL.DatatypeProperty, XSD[selected], owner, prop)
        elif selected == 'void':
            _focus(result.ontology, OWL.DatatypeProperty, None, owner, prop)
            assert any(d.kind == 'void_datatype' and d.severity == 'WARNING' for d in result.diagnostics)
        else:
            custom = one_object(result.ontology, prop, RDFS.range)
            _focus(result.ontology, OWL.ObjectProperty, custom, owner, prop)
            assert (custom, RDF.type, OWL.Class) in result.ontology
            expected = {Literal(text, lang=override or key or 'nl') for key, text in names.items()}
            assert expected <= set(result.ontology.objects(custom, RDFS.label))
        assert not any(d.kind == 'multilingual_primitive_conflict' or d.severity == 'ERROR' for d in result.diagnostics)


def test_primitive_normalization_does_not_reclassify_domain_classes(run, source_json, tmp_path):
    """Rules: DK-DAT-02, DK-CLS-01."""
    document = source_json('attributes_datatypes/value_types')
    source_element(document, 'cOther')['name'] = 'int'
    result = run(path=write_input(tmp_path, document), iri_strategy='id')
    assert result.outcome == 'completed'
    assert (BASE.cOther, RDF.type, OWL.Class) in result.ontology
    assert (BASE.cOther, RDFS.label, Literal('int')) in result.ontology
    assert (BASE.pFocus, RDFS.range, XSD.int) in result.ontology


@pytest.mark.parametrize('input_policy', POLICIES)
@pytest.mark.parametrize('kind', ['untyped', 'void', 'enumeration', 'primitive', 'custom'])
def test_attribute_kind_range_and_no_local_value_type_restriction(run, source_json, source_path, tmp_path, input_policy, kind):
    """Rules: DK-ATT-01, DK-ATT-02, DK-ATT-03, DK-ATT-04, DK-DAT-03, DK-DAT-04, DK-DAT-05, DK-CLS-10, DK-GEN-03."""
    document = source_json('attributes_datatypes/value_types')
    value = source_element(document, 'dValue')
    source_element(document, 'pFocus')['cardinality'] = '1'
    range_, prop_kind = XSD.int, OWL.DatatypeProperty
    if kind == 'untyped':
        source_element(document, 'pFocus')['propertyType'] = None
        range_ = None
    elif kind == 'void':
        value['name'] = 'void'
        range_ = None
    elif kind in {'custom', 'enumeration'}:
        value.update(name='StructuredValue', stereotype='datatype' if kind == 'custom' else 'enumeration')
        if kind == 'enumeration':
            value['literals'] = [{'id': 'vOne', 'name': 'One', 'description': None, 'type': 'Literal', 'propertyAssignments': None}]
        range_, prop_kind = BASE.dValue, OWL.ObjectProperty
    assert not fixture_issues(document)
    result = run(path=write_input(tmp_path, document), iri_strategy='id', input_policy=input_policy)
    assert result.outcome == 'completed'
    _focus(result.ontology, prop_kind, range_)
    _counts(result.ontology, BASE.cOwner, BASE.pFocus, {('exact', 1)}, range_)
    if kind in {'custom', 'enumeration'}:
        assert (BASE.dValue, RDF.type, OWL.Class) in result.ontology
    elif kind == 'void':
        assert not any(BASE.dValue in triple for triple in result.ontology)
        notices = [d for d in result.diagnostics if d.kind == 'void_datatype']
        assert notices and all(d.severity == 'WARNING' for d in notices)
        assert any({'pFocus', 'cOwner'} <= set(d.identified_sources) and {'void', 'range_omitted'} <= d.facts for d in notices)
        forbidden = {OWL.Nothing, OWL.bottomDataProperty, XSD.anySimpleType, XSD.anyAtomicType, RDFS.Literal}
        assert not any((BASE.pFocus, RDFS.range, term) in result.ontology for term in forbidden)
    else:
        assert not any(d.kind == 'void_datatype' for d in result.diagnostics)
    assert not any(d.severity == 'ERROR' for d in result.diagnostics)


def test_recursive_custom_datatypes_keep_owned_properties_and_cycles(run, source_json, source_path, tmp_path):
    """Rules: DK-DAT-05, DK-ATT-01, DK-GEN-03, DK-ATT-04."""
    for cycle in (False, True):
        document = source_json('attributes_datatypes/structured')
        if cycle:
            loop = copy.deepcopy(source_element(document, 'pLocation'))
            loop.update(id='pBack', name='back', propertyType={'id': 'dAddress', 'type': 'Class'})
            source_element(document, 'dLocation')['properties'].append(loop)
        assert not fixture_issues(document)
        result = run(path=write_input(tmp_path, document), iri_strategy='id')
        assert result.outcome == 'completed'
        assert_contains(result.ontology, load_graph(source_path('attributes_datatypes/structured', 'expected.ttl')))
        assert set(result.ontology.objects(BASE.pStreet, RDFS.domain)) == {BASE.dAddress}
        assert set(result.ontology.objects(BASE.pLatitude, RDFS.domain)) == {BASE.dLocation}
        assert (BASE.pAddress, RDFS.range, XSD.duration) not in result.ontology
        assert (BASE.pLocation, RDFS.domain, BASE.cOwner) not in result.ontology
        assert (BASE.pLatitude, RDFS.domain, BASE.cOwner) not in result.ontology
        if cycle:
            assert (BASE.pBack, RDFS.range, BASE.dAddress) in result.ontology
            assert set(result.ontology.objects(BASE.pBack, RDFS.domain)) == {BASE.dLocation}
        assert not list(result.ontology.triples((None, OWL.allValuesFrom, None)))


def test_an_eligible_explicit_relation_can_target_a_reified_custom_datatype(run, source_json, tmp_path):
    """Rules: DK-DAT-05, DK-GEN-03, DK-IRI-06."""
    document=source_json('attributes_datatypes/structured')
    source=copy.deepcopy(source_element(document,'pAddress'))
    target=copy.deepcopy(source)
    source.update(id='sCustom',name='owners',propertyType={'id':'cOwner','type':'Class'},aggregationKind='NONE')
    target.update(id='tCustom',name='values',aggregationKind='NONE')
    document['model']['contents'].append({'id':'rCustom','name':'hasCustomValue','description':None,
        'type':'Relation','propertyAssignments':None,'stereotype':'material',
        'isAbstract':False,'isDerived':False,'properties':[source,target]})
    assert not fixture_issues(document)
    result=run(path=write_input(tmp_path,document),iri_strategy='id',inverse_properties='none')
    assert result.outcome=='completed'
    assert (BASE.dAddress,RDF.type,OWL.Class) in result.ontology
    assert (BASE.tCustom,RDF.type,OWL.ObjectProperty) in result.ontology
    assert set(result.ontology.objects(BASE.tCustom,RDFS.domain))=={BASE.cOwner}
    assert set(result.ontology.objects(BASE.tCustom,RDFS.range))=={BASE.dAddress}


VALID_COUNTS = [
    pytest.param('1', {('exact', 1)}, id='single_one'),
    pytest.param('0', {('exact', 0)}, id='single_zero'),
    pytest.param('0..0', {('exact', 0)}, id='equal_zero'),
    pytest.param('2..2', {('exact', 2)}, id='equal_two'),
    pytest.param('0..1', {('max', 1)}, id='optional'),
    pytest.param('2..5', {('min', 2), ('max', 5)}, id='bounded'),
    pytest.param('5..2', {('min', 5), ('max', 2)}, id='contradictory'),
    pytest.param('1..0', {('min', 1), ('max', 0)}, id='contradictory_zero_upper'),
    pytest.param('1..*', {('min', 1)}, id='positive_unbounded'),
    pytest.param('0..*', set(), id='zero_unbounded'),
    pytest.param(' 001 .. 003 ', {('min', 1), ('max', 3)}, id='trim_leading_zeros'),
    pytest.param(' 01 .. * ', {('min', 1)}, id='trim_unbounded_upper'),
    pytest.param(' 00 ', {('exact', 0)}, id='single_leading_zero'),
]


@pytest.mark.parametrize('input_policy', POLICIES)
@pytest.mark.parametrize('cardinality,expected', VALID_COUNTS)
def test_attribute_counts_are_necessary_and_preserve_numeric_boundaries(run, source_json, tmp_path, input_policy, cardinality, expected):
    """Rules: DK-ATT-02, DK-ATT-03, DK-ATT-04, DK-DIAG-11, DK-DIAG-05; §3.4 contradictory numeric bounds."""
    document = source_json('attributes_datatypes/value_types')
    source_element(document, 'pFocus')['cardinality'] = cardinality
    result = run(path=write_input(tmp_path, document), iri_strategy='id', input_policy=input_policy)
    assert result.outcome == 'completed'
    _focus(result.ontology, OWL.DatatypeProperty, XSD.int)
    _counts(result.ontology, BASE.cOwner, BASE.pFocus, expected, XSD.int)
    assert not any(d.severity in {'WARNING', 'ERROR'} for d in result.diagnostics)


@pytest.mark.parametrize('input_policy', POLICIES)
@pytest.mark.parametrize('condition', ['null', 'absent', 'standalone_star'])
def test_null_absent_and_unbounded_attribute_cardinality_are_distinguished(run, source_json, tmp_path, input_policy, condition):
    """Rules: DK-ATT-01, DK-ATT-02, DK-ATT-03, DK-ATT-04, DK-DIAG-09, DK-DIAG-11, DK-DIAG-05.

    D3/A4 reviewed NO CHANGE assessment at 4fdef7bbaf8b73bf1ed0ff47fc793494493083dc:
    the supported exporter gives * bounds (0, unbounded), so ATT-03 requires
    an empty contribution. Canonical value_types input; fixed RDF assertions.
    """
    document = source_json('attributes_datatypes/value_types')
    focus = source_element(document, 'pFocus')
    if condition == 'absent':
        del focus['cardinality']
    elif condition == 'standalone_star':
        focus['cardinality'] = '*'
    result = run(path=write_input(tmp_path, document), iri_strategy='id', input_policy=input_policy)
    assert result.outcome == 'completed'
    _focus(result.ontology, OWL.DatatypeProperty, XSD.int)
    # The existing reader checks all six OWL cardinality predicates, including
    # qualified forms, direct property triples and restrictions outside the
    # owner's necessary path.
    _counts(result.ontology, BASE.cOwner, BASE.pFocus, set())
    if condition == 'standalone_star':
        assert not any(d.kind == 'invalid_cardinality' for d in result.diagnostics)
    missing = [d for d in result.diagnostics if d.kind == 'missing_cardinality']
    if condition == 'absent':
        assert missing and all(d.severity == 'WARNING' for d in missing)
        assert any('pFocus' in d.identified_sources for d in missing)
    else:
        assert not missing
        assert not any(d.severity in {'WARNING', 'ERROR'} for d in result.diagnostics)


@pytest.mark.parametrize('input_policy', POLICIES)
@pytest.mark.parametrize('iri_strategy', ['name', 'id'])
@pytest.mark.parametrize('value_kind', ['primitive', 'custom'])
@pytest.mark.parametrize('star', [pytest.param('*', id='bare'),
    pytest.param(' \t* \n', id='spaces_tab_newline'), pytest.param('\n *\t ', id='newline_spaces_tab')])
def test_standalone_star_matches_zero_unbounded_without_losing_attribute_or_independent_counts(
        run, source_json, tmp_path, input_policy, iri_strategy, value_kind, star):
    """Rules: DK-ATT-01, DK-ATT-02, DK-ATT-03, DK-ATT-04, DK-DAT-01, DK-DAT-05, DK-GEN-03, DK-IRI-02, DK-IRI-06, DK-DIAG-05, DK-DIAG-11.

    D3/A4 reviewed NO CHANGE assessment at 4fdef7bbaf8b73bf1ed0ff47fc793494493083dc.
    Complete attributes_datatypes/value_types runtime variants; no stored
    expectation. Compare fixed mapping RDF by isomorphism; verify the peer's
    finite counts separately, allowing qualified/unqualified alternatives.
    D3/A4 F1/F2 correction of ac2f2bf943be1f0800931368cd87400eaf614b3d.
    """
    template = source_json('attributes_datatypes/value_types')
    if value_kind == 'custom': source_element(template, 'dValue')['name'] = 'Address'
    peer = copy.deepcopy(source_element(template, 'pFocus'))
    peer.update(id='pPeer', name='independent', cardinality='2..5')
    source_element(template, 'cOwner')['properties'].append(peer)
    owner, other = (BASE.cOwner, BASE.cOther) if iri_strategy == 'id' else (BASE.Owner, BASE.Other)
    kind = OWL.DatatypeProperty if value_kind == 'primitive' else OWL.ObjectProperty
    range_ = XSD.int if value_kind == 'primitive' else BASE.dValue if iri_strategy == 'id' else BASE.Address
    classifiers = {owner, other} | ({range_} if value_kind == 'custom' else set())

    def mapping_scope(graph, prop, independent):
        # Class/property declarations and source-class links are fixed here.
        # Restriction representations are checked by _counts, not frozen.
        selected = rooted_graph(graph, classifiers | {prop, independent},
            {RDF.type, RDFS.domain, RDFS.range},
            type_objects={OWL.Class, OWL.ObjectProperty, OWL.DatatypeProperty})
        for classifier in classifiers:
            for parent in set(graph.objects(classifier, RDFS.subClassOf)) & classifiers:
                selected.add((classifier, RDFS.subClassOf, parent))
        return selected

    reference = identity = diagnostics = None
    controls = [('0..*', set()), (' \t00 .. *\n', set()),
                ('1..*', {('min', 1)}), ('0', {('exact', 0)}), (star, set())]
    for cardinality, expected in controls:
        document = copy.deepcopy(template)
        source_element(document, 'pFocus')['cardinality'] = cardinality
        assert not fixture_issues(document)
        result = run(path=write_input(tmp_path, document), iri_strategy=iri_strategy, input_policy=input_policy)
        assert result.outcome == 'completed'
        assert not any(d.severity in {'WARNING', 'ERROR'} for d in result.diagnostics)
        graph = result.ontology
        prop, independent = ((BASE.pFocus, BASE.pPeer) if iri_strategy == 'id' else
            (one_subject(graph, DCTERMS.identifier, Literal('pFocus')),
             one_subject(graph, DCTERMS.identifier, Literal('pPeer'))))
        _focus(graph, kind, range_, owner, prop)
        _focus(graph, kind, range_, owner, independent)
        _counts(graph, owner, prop, expected, range_)
        _counts(graph, owner, independent, {('min', 2), ('max', 5)}, range_)
        assert (owner, RDF.type, OWL.Class) in graph and (other, RDF.type, OWL.Class) in graph
        if value_kind == 'custom': assert (range_, RDF.type, OWL.Class) in graph
        if reference is None:
            identity = (prop, independent)
            diagnostics = diagnostic_signatures(result.diagnostics)
            reference = mapping_scope(graph, prop, independent)
        else:
            assert (prop, independent) == identity
            assert diagnostic_signatures(result.diagnostics) == diagnostics
            if not expected:
                assert_graph_equal(mapping_scope(graph, prop, independent), reference)


INVALID_COUNTS = [
    pytest.param('n', set(), id='symbolic_single'), pytest.param('n..m', set(), id='both_symbolic'),
    pytest.param('n..*', set(), id='invalid_lower_unbounded_upper'),
    pytest.param('n..3', {('max', 3)}, id='symbolic_lower'),
    pytest.param('n..0', {('max', 0)}, id='invalid_lower_zero_upper'),
    pytest.param('2..n', {('min', 2)}, id='symbolic_upper'),
    pytest.param('0..n', set(), id='zero_lower_invalid_upper'),
    pytest.param('..3', {('max', 3)}, id='empty_lower'),
    pytest.param('2..', {('min', 2)}, id='empty_upper'),
    pytest.param('..', set(), id='both_empty'),
    pytest.param('-1..3', {('max', 3)}, id='signed_lower'),
    pytest.param('2..+3', {('min', 2)}, id='signed_upper'),
    pytest.param('1.5..3', {('max', 3)}, id='decimal_lower'),
    pytest.param('2..3e1', {('min', 2)}, id='exponent_upper'),
    pytest.param('２..3', {('max', 3)}, id='non_ascii_digits'),
    pytest.param('2...*', set(), id='extra_dot'), pytest.param('1..2..3', set(), id='repeated_delimiter'),
    pytest.param('2,,3', set(), id='comma'), pytest.param('2:3', set(), id='colon'),
    pytest.param('', set(), id='empty_string'), pytest.param(' \t ', set(), id='blank_string'),
    pytest.param(1, set(), id='json_number'), pytest.param(True, set(), id='json_boolean'),
    pytest.param(1.5, set(), id='json_fraction'),
    pytest.param([], set(), id='json_array'), pytest.param({}, set(), id='json_object'),
]


@pytest.mark.parametrize('input_policy', POLICIES)
@pytest.mark.parametrize('cardinality,expected', INVALID_COUNTS)
def test_invalid_attribute_counts_retain_errors_and_only_valid_numeric_bounds(run, source_json, tmp_path, input_policy, cardinality, expected):
    """Rules: DK-DIAG-10, DK-DIAG-11, DK-DIAG-05, DK-ATT-02, DK-ATT-03, DK-GEN-03."""
    document = source_json('attributes_datatypes/value_types')
    source_element(document, 'pFocus')['cardinality'] = cardinality
    assert fixture_issues(document) == (frozenset() if isinstance(cardinality, str) else {'invalid_cardinality_type'})
    result = run(path=write_input(tmp_path, document), iri_strategy='id', input_policy=input_policy)
    assert any(d.severity == 'ERROR' for d in result.diagnostics)
    if input_policy != 'best-effort':
        assert result.outcome == 'aborted' and result.ontology is None
    else:
        assert result.outcome == 'completed-with-errors'
        _focus(result.ontology, OWL.DatatypeProperty, XSD.int)
        _counts(result.ontology, BASE.cOwner, BASE.pFocus, expected, XSD.int)
        assert (BASE.cOther, RDF.type, OWL.Class) in result.ontology


def test_removed_optional_local_value_restriction_control_is_not_exposed(invoke):
    """Rules: DK-ATT-04; Python public-control surface (CLI counterpart is Wave 6)."""
    assert invoke.has_local_value_restriction_control() is False


def test_id_primitive_partial_ground_graph_includes_ontology_and_labels(run, source_path):
    """Rules: DK-ATT-01, DK-GEN-01, DK-GEN-03, DK-DAT-01, DK-LBL-01."""
    result = run('attributes_datatypes/value_types', iri_strategy='id')
    assert result.outcome == 'completed'
    assert_contains(result.ontology, load_graph(source_path('attributes_datatypes/value_types', 'expected.ttl')))


@pytest.mark.parametrize('qualified', [False, True], ids=['unqualified', 'qualified'])
@pytest.mark.parametrize('combined', [False, True], ids=['direct_subclasses', 'intersection'])
def test_rdf_helper_attribute_counts_accept_asserted_alternative_forms(qualified, combined):
    """Harness only: validate RDF assertions, never simulate DirectKG execution."""
    graph = Graph()
    graph.add((BASE.pFocus, RDF.type, OWL.DatatypeProperty))
    nodes=[]
    for predicate,n in [(OWL.minQualifiedCardinality if qualified else OWL.minCardinality,2),
                        (OWL.maxQualifiedCardinality if qualified else OWL.maxCardinality,5)]:
        node=BNode();nodes.append(node)
        graph.add((node,RDF.type,OWL.Restriction));graph.add((node,OWL.onProperty,BASE.pFocus))
        graph.add((node,predicate,Literal(n,datatype=XSD.nonNegativeInteger)))
        if qualified: graph.add((node,OWL.onDataRange,XSD.int))
    if combined:
        from rdflib.collection import Collection
        expression,head=BNode(),BNode()
        graph.add((BASE.cOwner,RDFS.subClassOf,expression));graph.add((expression,OWL.intersectionOf,head))
        Collection(graph,head,nodes)
    else:
        for node in nodes: graph.add((BASE.cOwner,RDFS.subClassOf,node))
    _counts(graph,BASE.cOwner,BASE.pFocus,{('min',2),('max',5)},XSD.int)
    with pytest.raises(AssertionError): _counts(graph,BASE.cOwner,BASE.pFocus,{('exact',3)},XSD.int)
    if qualified:
        graph.remove((nodes[0],OWL.onDataRange,XSD.int))
        graph.add((nodes[0],OWL.onClass,XSD.int))
        with pytest.raises(AssertionError): _counts(graph,BASE.cOwner,BASE.pFocus,{('min',2),('max',5)},XSD.int)
        graph.remove((nodes[0],OWL.onClass,XSD.int))
        graph.add((nodes[0],OWL.onDataRange,XSD.int))
    graph.remove((BASE.cOwner,RDFS.subClassOf,None))
    graph.add((BASE.cOwner,OWL.equivalentClass,nodes[0]))
    with pytest.raises(AssertionError): _counts(graph,BASE.cOwner,BASE.pFocus,{('min',2),('max',5)},XSD.int)


def test_rdf_helper_equal_attribute_counts_accept_exact_bounds_and_zero_maximum():
    """Harness only: check allowed attribute alternatives, including zero."""
    for number in (0,2):
        forms=[[(OWL.cardinality,number)],[(OWL.minCardinality,number),(OWL.maxCardinality,number)]]
        if number==0: forms.append([(OWL.maxCardinality,0)])
        for form in forms:
            graph=Graph();graph.add((BASE.pFocus,RDF.type,OWL.DatatypeProperty))
            for predicate,n in form:
                node=BNode();graph.add((BASE.cOwner,RDFS.subClassOf,node))
                graph.add((node,RDF.type,OWL.Restriction));graph.add((node,OWL.onProperty,BASE.pFocus))
                graph.add((node,predicate,Literal(n,datatype=XSD.nonNegativeInteger)))
            _counts(graph,BASE.cOwner,BASE.pFocus,{('exact',number)},XSD.int)
            with pytest.raises(AssertionError): _counts(graph,BASE.cOwner,BASE.pFocus,{('exact',number+1)},XSD.int)
