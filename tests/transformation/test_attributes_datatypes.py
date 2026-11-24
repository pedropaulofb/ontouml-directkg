"""Attributes, bounded primitive recognition, structured values and multiplicity."""

import copy
import pytest
from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, XSD

from tests.support.data import fixture_issues, source_element, write_input
from tests.support.dkgm import assert_dkgm_vocabulary
from tests.support.invocation import (_observed_diagnostics,
                                      absent_attribute_property_type_diagnostic,
                                      absent_attribute_property_type_error,
                                      attribute_owner_without_local_class_diagnostic,
                                      class_properties_container_diagnostic,
                                      diagnostic_record_counts,
                                      diagnostic_signatures,
                                      unresolved_attribute_type_diagnostic)
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


@pytest.mark.parametrize("input_policy", ["strict", "tolerant", "best-effort"])
@pytest.mark.parametrize("iri_strategy", ["id", "name"])
@pytest.mark.parametrize("carrier", ["absent", "null"])
def test_absent_attribute_property_type_is_distinct_from_explicit_null(
        run, source_json, tmp_path, input_policy, iri_strategy, carrier):
    """Rules: DK-ATT-01, DK-ATT-03, DK-DAT-03, DK-GEN-03, DK-DIAG-05. RD-02 Alternative A."""
    document = source_json("shared/core_model")
    focus = source_element(document, "aAge")
    focus.update(description="FOCUS_DESCRIPTION_SENTINEL", cardinality="1")
    if carrier == "absent":
        del focus["propertyType"]
    else:
        focus["propertyType"] = None
    assert not fixture_issues(document)
    options = {"iri_strategy": iri_strategy, "input_policy": input_policy}
    result = run(path=write_input(tmp_path, document), **options)
    assert all(event.code != "INTERNAL_TRANSFORMATION_FAILURE" for event in result.diagnostics)
    if carrier == "null":
        assert result.outcome == "completed"
        assert not any(event.severity == "ERROR" or "absent_attribute_property_type" in event.facts
                       for event in result.diagnostics)
        prop = BASE.aAge if iri_strategy == "id" else one_subject(result.ontology, DCTERMS.identifier, Literal("aAge"))
        owner = BASE.cPerson if iri_strategy == "id" else BASE.Person
        _focus(result.ontology, OWL.DatatypeProperty, None, owner, prop)
        _counts(result.ontology, owner, prop, {("exact", 1)})
        assert (prop, RDFS.comment, Literal("FOCUS_DESCRIPTION_SENTINEL")) in result.ontology
        return

    assert any(absent_attribute_property_type_error(event, "aAge") for event in result.diagnostics), result.diagnostics
    if input_policy != "best-effort":
        assert result.outcome == "aborted" and result.ontology is None
        assert result.provenance is None
        return
    assert result.outcome == "completed-with-errors"
    # The independent graph must be identical to removing only the bad attribute.
    source_element(document, "cPerson")["properties"].remove(focus)
    control = run(path=write_input(tmp_path, document, "control.json"), **options)
    assert control.outcome == "completed"
    assert_graph_equal(result.ontology, control.ontology)
    assert not any(BASE.aAge in triple for triple in result.ontology)
    assert not any("FOCUS_DESCRIPTION_SENTINEL" in str(term) for triple in result.ontology for term in triple)
    owner = BASE.cPerson if iri_strategy == "id" else BASE.Person
    note = BASE.aNote if iri_strategy == "id" else one_subject(result.ontology, DCTERMS.identifier, Literal("aNote"))
    assert (owner, RDF.type, OWL.Class) in result.ontology
    _focus(result.ontology, OWL.DatatypeProperty, None, owner, note)


def test_absent_attribute_property_type_reader_requires_affirmative_absence():
    """Rules: DK-ATT-01, DK-DIAG-04, DK-DIAG-05. Harness: affirmative absence and agreeing subject."""
    from ontouml_directkg.diagnostics import Diagnostic, SourceLocation

    for message in (
        "Attribute 'aAge' is missing the required propertyType field.",
        "Attribute 'aAge' propertyType is absent.",
        "Missing propertyType field on class attribute 'aAge'.",
        "Attribute 'aAge' has no propertyType.",
        "Attribute 'aAge' is missing the required 'propertyType' field.",
    ):
        assert absent_attribute_property_type_diagnostic(message), message
    for message in (
        "Attribute 'aAge' has propertyType.",
        "Attribute 'aAge' propertyType is null.",
        "Attribute 'aAge' propertyType is not missing.",
        "Attribute 'aAge' propertyType is absent or null.",
        "Attribute 'aAge' propertyType is valid; the identifier is missing.",
        "If an attribute lacks propertyType, it is omitted.",
        "Attribute value-type reference cannot be resolved.",
    ):
        assert not absent_attribute_property_type_diagnostic(message), message

    locations = (SourceLocation("$.model.contents[0].properties[0]", "aAge", "Property"),
                 SourceLocation("$.model.contents[0].properties[1]", "aNote", "Property"))
    for message, expected in (
        ("Attribute 'aAge' is missing propertyType.", True),
        ('Attribute "aAge" is missing the `propertyType` field.', True),
        ("Attribute aAge propertyType is absent.", True),
        ("Missing propertyType field on class attribute `aAge`.", True),
        ("Attribute is missing propertyType.", True),
        ("Attribute 'aNote' is missing propertyType.", False),
        ('Attribute "aNote" has no propertyType.', False),
        ("Missing propertyType on attribute aNote.", False),
        ("Attribute 'aage' is missing propertyType.", False),
        ("Attribute 'aAge' propertyType is absent or null.", False),
    ):
        # The contradictory explicit subject cannot be repaired by including
        # the expected ID in either a single locator or a multiple-locator list.
        for sources in ((locations[0],), locations):
            native = Diagnostic("ERROR", "PROVISIONAL_PROBE", message, "Affected attribute omitted.", sources)
            event, = _observed_diagnostics((native,), retain_unclassified=True)
            assert absent_attribute_property_type_error(event, "aAge") == expected, message


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("condition", ["duplicate_id", "rejected_stereotype"])
def test_absent_attribute_property_type_preserves_precedence(run, source_json, tmp_path, input_policy, condition):
    """Rules: DK-ATT-01, DK-DIAG-05, DK-DIAG-06; §3.4. RD-02 Alternative A."""
    document = source_json("shared/core_model")
    focus = source_element(document, "aAge")
    del focus["propertyType"]
    options = {"iri_strategy": "id", "input_policy": input_policy}
    if condition == "duplicate_id":
        source_element(document, "aNote")["id"] = "aAge"
    else:
        focus["stereotype"] = "customProp"
        options["stereotype_policy"] = "allow-missing"
    result = run(path=write_input(tmp_path, document), **options)
    assert result.outcome == "aborted" and result.ontology is None
    expected_kind = "duplicate_id" if condition == "duplicate_id" else "unrecognized_stereotype"
    assert any(event.severity == "ERROR" and event.kind == expected_kind for event in result.diagnostics)
    if condition == "duplicate_id":
        assert any(event.code == "DUPLICATE_SOURCE_ID" for event in result.diagnostics)
    assert not any(event.code == "INTERNAL_TRANSFORMATION_FAILURE" or
                   "absent_attribute_property_type" in event.facts for event in result.diagnostics)


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


_RELATION_AXIOM_TYPES = (
    OWL.AsymmetricProperty, OWL.IrreflexiveProperty, OWL.FunctionalProperty,
    OWL.InverseFunctionalProperty, OWL.SymmetricProperty, OWL.TransitiveProperty,
    OWL.ReflexiveProperty,
)


def _assert_ordinary_class_attribute(graph, prop, owner, target_cls):
    _focus(graph, OWL.ObjectProperty, target_cls, owner, prop)
    for axiom_type in _RELATION_AXIOM_TYPES:
        assert (prop, RDF.type, axiom_type) not in graph
    assert not any(prop in pair for pair in graph.subject_objects(OWL.inverseOf))
    assert not list(graph.objects(prop, OWL.propertyChainAxiom))
    assert not list(graph.objects(owner, OWL.equivalentClass))


@pytest.mark.parametrize('input_policy', POLICIES)
@pytest.mark.parametrize('iri_strategy', ['id', 'name'])
@pytest.mark.parametrize('target_case', [
    'kind', 'category', 'relator', 'mode', 'quality', 'event', 'situation',
    'collective', 'quantity', 'abstract', 'type', 'self_owner',
    'kind_named_int', 'null_stereotype', 'custom_stereotype',
])
def test_class_valued_attribute_maps_to_ordinary_object_property_without_inferred_relation_semantics(
        run, source_json, tmp_path, input_policy, iri_strategy, target_case):
    """Rules: DK-ATT-01, DK-GEN-03, DK-CLS-01, DK-DAT-02, DK-ATT-04, DK-GEN-04, DK-REL-19, DK-INV-02, DK-IRI-02, DK-IRI-06, DK-DIAG-01, DK-DIAG-05, DK-DIAG-06, DK-DIAG-15.

    RD-23 / RD-02 Alternative A (4f9a9ccfa016a052a9b955afb0f9d863e3df8222):
    class-valued attributes generate ordinary owl:ObjectProperty mappings with
    no inferred relation stereotypes, relation axioms, mereology bridges, or
    flattened target attributes.
    """
    document = source_json('attributes_datatypes/value_types')
    focus = source_element(document, 'pFocus')
    other = source_element(document, 'cOther')
    target_owned = copy.deepcopy(focus)
    target_owned.update(id='pTargetOwned', name='targetOwned', cardinality='1',
                        propertyType={'id': 'dValue', 'type': 'Class'})

    if target_case == 'self_owner':
        focus['propertyType'] = {'id': 'cOwner', 'type': 'Class'}
        source_element(document, 'cOwner')['properties'].append(target_owned)
        target_id = 'cOwner'
        stereotype_policy = 'require-known'
    else:
        focus['propertyType'] = {'id': 'cOther', 'type': 'Class'}
        other['properties'] = [target_owned]
        target_id = 'cOther'
        if target_case == 'kind_named_int':
            other.update(name='int', stereotype='kind')
            stereotype_policy = 'require-known'
        elif target_case == 'null_stereotype':
            other['stereotype'] = None
            stereotype_policy = 'allow-missing'
        elif target_case == 'custom_stereotype':
            other['stereotype'] = 'customDomainClass'
            stereotype_policy = 'allow-custom'
        else:
            other['stereotype'] = target_case
            stereotype_policy = 'require-known'

    assert not fixture_issues(document)
    result = run(path=write_input(tmp_path, document), iri_strategy=iri_strategy,
                 input_policy=input_policy, stereotype_policy=stereotype_policy)
    assert result.outcome == 'completed'
    graph = result.ontology
    assert isinstance(graph, Graph)

    if iri_strategy == 'id':
        owner_iri = BASE.cOwner
        target_cls = BASE[target_id]
        prop_iri = BASE.pFocus
        owned_iri = BASE.pTargetOwned
    else:
        owner_iri = one_subject(graph, DCTERMS.identifier, Literal('cOwner'))
        target_cls = one_subject(graph, DCTERMS.identifier, Literal(target_id))
        prop_iri = one_subject(graph, DCTERMS.identifier, Literal('pFocus'))
        owned_iri = one_subject(graph, DCTERMS.identifier, Literal('pTargetOwned'))

    assert (owner_iri, RDF.type, OWL.Class) in graph
    assert (target_cls, RDF.type, OWL.Class) in graph
    _assert_ordinary_class_attribute(graph, prop_iri, owner_iri, target_cls)
    assert not list(graph.subject_objects(OWL.inverseOf))
    assert not list(graph.triples((None, OWL.propertyChainAxiom, None)))
    ontology_iri = one_subject(graph, RDF.type, OWL.Ontology)
    assert_dkgm_vocabulary(graph, ontology_iri, 'import', bridges=())

    _focus(graph, OWL.DatatypeProperty, XSD.int, target_cls, owned_iri)
    _counts(graph, target_cls, owned_iri, {('exact', 1)}, XSD.int)
    if target_case != 'self_owner':
        assert not any((node, OWL.onProperty, owned_iri) in graph
                       for node in graph.objects(owner_iri, RDFS.subClassOf))
    if target_case == 'kind_named_int':
        assert (target_cls, RDFS.label, Literal('int')) in graph
        assert (prop_iri, RDFS.range, XSD.int) not in graph

    assert not any(d.severity == 'ERROR' for d in result.diagnostics)
    assert not any(d.kind in {'unmapped_relation_stereotype', 'chain_compatibility', 'chain_ambiguity'}
                   for d in result.diagnostics)
    if target_case == 'abstract':
        assert any(d.kind == 'abstractness' and d.severity == 'INFO' and target_id in d.identified_sources
                   for d in result.diagnostics)
        assert not any(d.severity == 'WARNING' for d in result.diagnostics)
    elif target_case == 'custom_stereotype':
        warnings = [d for d in result.diagnostics if d.severity == 'WARNING']
        assert warnings and all(d.kind == 'unrecognized_stereotype' and target_id in d.identified_sources
                                and 'pFocus' not in d.identified_sources for d in warnings)
    else:
        assert not any(d.severity == 'WARNING' for d in result.diagnostics)


@pytest.mark.parametrize('dkgm_mode', ['import', 'embed', 'none'])
@pytest.mark.parametrize('chain_mode', ['none', 'omit-conflicting-constraints', 'preserve-conflicting-constraints'])
@pytest.mark.parametrize('inverse_mode', ['all', 'informed', 'named', 'none'])
def test_class_valued_attribute_respects_dkgm_chain_and_inverse_controls(
        run, source_json, tmp_path, dkgm_mode, chain_mode, inverse_mode):
    """Rules: DK-ATT-01, DK-ATT-02, DK-ATT-03, DK-GEN-03, DK-GEN-04, DK-REL-07, DK-REL-19, DK-INV-01, DK-INV-02, DK-CLS-11."""
    document = source_json('attributes_datatypes/value_types')
    owner_cls = source_element(document, 'cOwner')
    owner_cls['stereotype'] = 'kind'
    base_prop = copy.deepcopy(source_element(document, 'pFocus'))
    targets = [
        ('cRelator', 'RelatorTarget', 'relator', 'pRelator', 'relatorAttr', '1'),
        ('cMode', 'ModeTarget', 'mode', 'pMode', 'modeAttr', '0..1'),
        ('cCollective', 'CollectiveTarget', 'collective', 'pCollective', 'collectiveAttr', '1..*'),
        ('cQuantity', 'QuantityTarget', 'quantity', 'pQuantity', 'quantityAttr', '2..5'),
        ('cSubkind', 'SubkindTarget', 'subkind', 'pSubkind', 'subkindAttr', '1'),
    ]
    new_classes = []
    new_props = []
    for cls_id, cls_name, stereotype, prop_id, prop_name, card in targets:
        cls = copy.deepcopy(source_element(document, 'cOther'))
        cls.update(id=cls_id, name=cls_name, stereotype=stereotype)
        new_classes.append(cls)
        prop = copy.deepcopy(base_prop)
        prop.update(id=prop_id, name=prop_name, cardinality=card, propertyType={'id': cls_id, 'type': 'Class'})
        new_props.append(prop)
    self_prop = copy.deepcopy(base_prop)
    self_prop.update(id='pSelf', name='selfAttr', cardinality='*', propertyType={'id': 'cOwner', 'type': 'Class'})
    new_props.append(self_prop)

    document['model']['contents'].extend(new_classes)
    owner_cls['properties'] = new_props
    assert not fixture_issues(document)

    result = run(path=write_input(tmp_path, document), iri_strategy='id',
                 dkgm_vocabulary=dkgm_mode, material_property_chains=chain_mode,
                 inverse_properties=inverse_mode)
    assert result.outcome == 'completed'
    graph = result.ontology
    ontology_iri = one_subject(graph, RDF.type, OWL.Ontology)
    assert_dkgm_vocabulary(graph, ontology_iri, dkgm_mode, bridges=())
    assert not list(graph.subject_objects(OWL.inverseOf))
    for subject in set(graph.subjects(OWL.propertyChainAxiom)):
        assert not str(subject).startswith(str(BASE))

    expected_counts = {
        'pRelator': (BASE.cRelator, {('exact', 1)}),
        'pMode': (BASE.cMode, {('max', 1)}),
        'pCollective': (BASE.cCollective, {('min', 1)}),
        'pQuantity': (BASE.cQuantity, {('min', 2), ('max', 5)}),
        'pSubkind': (BASE.cSubkind, {('exact', 1)}),
        'pSelf': (BASE.cOwner, set()),
    }
    for prop_id, (target_iri, counts) in expected_counts.items():
        prop_iri = BASE[prop_id]
        _assert_ordinary_class_attribute(graph, prop_iri, BASE.cOwner, target_iri)
        _counts(graph, BASE.cOwner, prop_iri, counts, target_iri)

    assert not any(d.severity == 'ERROR' for d in result.diagnostics)
    assert not any(d.kind in {'unmapped_relation_stereotype', 'chain_compatibility', 'chain_ambiguity'}
                   or 'dkgm_chains_absent' in d.facts for d in result.diagnostics)


CLASS_ATTR_COUNTS = [
    pytest.param('1', {('exact', 1)}, True, id='exact_one'),
    pytest.param('0', {('exact', 0)}, True, id='exact_zero'),
    pytest.param('0..1', {('max', 1)}, True, id='optional'),
    pytest.param('2..5', {('min', 2), ('max', 5)}, True, id='bounded'),
    pytest.param('1..*', {('min', 1)}, True, id='positive_unbounded'),
    pytest.param('*', set(), True, id='standalone_star'),
    pytest.param(None, set(), True, id='explicit_null'),
    pytest.param('absent', set(), True, id='absent_field'),
    pytest.param('1..n', {('min', 1)}, False, id='invalid_upper_recovers_min'),
    pytest.param('..3', {('max', 3)}, False, id='empty_lower_recovers_max'),
    pytest.param('2...*', set(), False, id='ambiguous_recovers_none'),
]


@pytest.mark.parametrize('input_policy', POLICIES)
@pytest.mark.parametrize('cardinality,expected,valid', CLASS_ATTR_COUNTS)
def test_class_valued_attribute_preserves_multiplicity_and_partial_recovery(
        run, source_json, tmp_path, input_policy, cardinality, expected, valid):
    """Rules: DK-ATT-01, DK-ATT-02, DK-ATT-03, DK-ATT-04, DK-GEN-03, DK-INV-02, DK-DIAG-05, DK-DIAG-09, DK-DIAG-10, DK-DIAG-11."""
    document = source_json('attributes_datatypes/value_types')
    source_element(document, 'cOther')['stereotype'] = 'kind'
    focus = source_element(document, 'pFocus')
    focus['propertyType'] = {'id': 'cOther', 'type': 'Class'}
    if cardinality == 'absent':
        del focus['cardinality']
    else:
        focus['cardinality'] = cardinality
    peer = copy.deepcopy(source_element(document, 'pFocus'))
    peer.update(id='pPeer', name='peerClassAttr', cardinality='2..5', propertyType={'id': 'cOther', 'type': 'Class'})
    source_element(document, 'cOwner')['properties'].append(peer)

    expected_issues = frozenset() if (valid or isinstance(cardinality, str)) else {'invalid_cardinality_type'}
    assert fixture_issues(document) == expected_issues

    result = run(path=write_input(tmp_path, document), iri_strategy='id', input_policy=input_policy)
    if valid:
        assert result.outcome == 'completed'
        assert not any(d.severity == 'ERROR' for d in result.diagnostics)
        missing = [d for d in result.diagnostics if d.kind == 'missing_cardinality']
        if cardinality == 'absent':
            assert missing and all(d.severity == 'WARNING' for d in missing)
            assert any('pFocus' in d.identified_sources for d in missing)
        else:
            assert not missing
            assert not any(d.severity == 'WARNING' for d in result.diagnostics)
    else:
        assert any(d.kind == 'invalid_cardinality' and d.severity == 'ERROR' for d in result.diagnostics)
        if input_policy != 'best-effort':
            assert result.outcome == 'aborted' and result.ontology is None
            return
        assert result.outcome == 'completed-with-errors'

    graph = result.ontology
    _assert_ordinary_class_attribute(graph, BASE.pFocus, BASE.cOwner, BASE.cOther)
    _counts(graph, BASE.cOwner, BASE.pFocus, expected, BASE.cOther)
    _assert_ordinary_class_attribute(graph, BASE.pPeer, BASE.cOwner, BASE.cOther)
    _counts(graph, BASE.cOwner, BASE.pPeer, {('min', 2), ('max', 5)}, BASE.cOther)


@pytest.mark.parametrize('iri_strategy', ['id', 'name'])
@pytest.mark.parametrize('prop_stereotype', [None, 'begin', 'end'])
@pytest.mark.parametrize('omit_identifiers', [False, True], ids=['keep_ids', 'omit_ids'])
def test_class_valued_attribute_preserves_flags_stereotypes_labels_and_fallback_iris(
        run, invoke, source_json, tmp_path, iri_strategy, prop_stereotype, omit_identifiers):
    """Rules: DK-ATT-01, DK-GEN-03, DK-GEN-05, DK-PROP-04, DK-PROP-05, DK-PROP-06, DK-LBL-01, DK-LBL-02, DK-IRI-04, DK-IRI-09, DK-DIAG-16, DK-DIAG-18."""
    document = source_json('attributes_datatypes/value_types')
    source_element(document, 'cOther')['stereotype'] = 'role'
    focus = source_element(document, 'pFocus')
    focus.update(
        name={'en': 'Primary Target'},
        description=None,
        stereotype=prop_stereotype,
        isDerived=True,
        isReadOnly=True,
        isOrdered=True,
        cardinality='1',
        propertyType={'id': 'cOther', 'type': 'Class'},
    )
    unnamed = copy.deepcopy(source_element(document, 'pFocus'))
    unnamed.update(id='pUnnamed', name=None, description=None, stereotype=None,
                   isDerived=False, isReadOnly=False, isOrdered=False, cardinality=None)
    source_element(document, 'cOwner')['properties'].append(unnamed)
    assert not fixture_issues(document)

    result = run(path=write_input(tmp_path, document), iri_strategy=iri_strategy, omit_identifiers=omit_identifiers)
    assert result.outcome == 'completed'
    graph = result.ontology
    if iri_strategy == 'id':
        owner_iri, target_iri, prop_iri, unnamed_iri = BASE.cOwner, BASE.cOther, BASE.pFocus, BASE.pUnnamed
    else:
        owner_iri = one_subject(graph, DCTERMS.identifier, Literal('cOwner')) if not omit_identifiers else BASE.Owner
        target_iri = one_subject(graph, DCTERMS.identifier, Literal('cOther')) if not omit_identifiers else BASE.Other
        prop_iri = one_subject(graph, DCTERMS.identifier, Literal('pFocus')) if not omit_identifiers else BASE.Primary_Target
        unnamed_iri = one_subject(graph, DCTERMS.identifier, Literal('pUnnamed')) if not omit_identifiers else BASE.pUnnamed

    _assert_ordinary_class_attribute(graph, prop_iri, owner_iri, target_iri)
    _assert_ordinary_class_attribute(graph, unnamed_iri, owner_iri, target_iri)
    _counts(graph, owner_iri, prop_iri, {('exact', 1)}, target_iri)
    assert Literal('Primary Target', lang='en') in set(graph.objects(prop_iri, RDFS.label))
    assert not list(graph.objects(unnamed_iri, RDFS.label))
    comments = set(graph.objects(prop_iri, RDFS.comment))
    assert any('isderived' in str(c).casefold() and 'true' in str(c).casefold() for c in comments)
    assert any('read-only' in str(c).casefold() for c in comments)
    assert any('ordered' in str(c).casefold() for c in comments)
    assert not list(graph.subjects(RDF.type, RDF.Seq))

    if iri_strategy == 'name' and not omit_identifiers:
        assert set(graph.objects(prop_iri, DCTERMS.identifier)) == {Literal('pFocus')}
        assert set(graph.objects(unnamed_iri, DCTERMS.identifier)) == {Literal('pUnnamed')}
    else:
        assert not list(graph.objects(prop_iri, DCTERMS.identifier))
        assert not list(graph.objects(unnamed_iri, DCTERMS.identifier))

    stereo_comments = [c for c in invoke.read_property_stereotype_comments(result) if c.subject == prop_iri]
    if prop_stereotype is None:
        assert not stereo_comments
    else:
        assert {(c.field, c.value) for c in stereo_comments} == {('stereotype', prop_stereotype)}

    assert any(d.kind == 'derived_status' and d.severity == 'INFO' and 'pFocus' in d.identified_sources
               for d in result.diagnostics)
    assert any(d.kind == 'ordering' and d.severity == 'INFO' and 'pFocus' in d.identified_sources
               for d in result.diagnostics)
    if iri_strategy == 'name':
        assert any(d.kind == 'generic_id_fallback' and d.severity == 'WARNING' and 'pUnnamed' in d.identified_sources
                   for d in result.diagnostics)
    else:
        assert any(d.kind == 'missing_name' and d.severity == 'INFO' and 'pUnnamed' in d.identified_sources
                   for d in result.diagnostics)
    assert not any(d.severity == 'ERROR' for d in result.diagnostics)

    focus['description'] = {'en': 'Assigned target.', 'pt': 'Alvo atribuído.'}
    described = run(path=write_input(tmp_path, document, 'described.json'),
                    iri_strategy=iri_strategy, omit_identifiers=omit_identifiers)
    assert described.outcome == 'completed'
    described_graph = described.ontology
    _assert_ordinary_class_attribute(described_graph, prop_iri, owner_iri, target_iri)
    assert Literal('Primary Target', lang='en') in set(described_graph.objects(prop_iri, RDFS.label))
    described_comments = set(described_graph.objects(prop_iri, RDFS.comment))
    assert Literal('Assigned target.', lang='en') in described_comments
    assert Literal('Alvo atribuído.', lang='pt') in described_comments
    assert not any(d.severity == 'ERROR' for d in described.diagnostics)


@pytest.mark.parametrize('input_policy', POLICIES)
@pytest.mark.parametrize('scenario,stereotype,policy', [
    ('null_under_require_known', None, 'require-known'),
    ('custom_under_allow_missing', 'customDomainClass', 'allow-missing'),
    ('custom_under_require_known', 'customDomainClass', 'require-known'),
], ids=['null_require_known', 'custom_allow_missing', 'custom_require_known'])
def test_class_valued_attribute_rejects_disallowed_target_class_stereotype(
        run, source_json, tmp_path, input_policy, scenario, stereotype, policy):
    """Rules: DK-ATT-01, DK-DIAG-05, DK-DIAG-06."""
    document = source_json('attributes_datatypes/value_types')
    source_element(document, 'cOther')['stereotype'] = stereotype
    source_element(document, 'pFocus')['propertyType'] = {'id': 'cOther', 'type': 'Class'}
    assert not fixture_issues(document)

    result = run(path=write_input(tmp_path, document), iri_strategy='id',
                 input_policy=input_policy, stereotype_policy=policy)
    assert result.outcome == 'aborted'
    assert result.ontology is None
    expected_kind = 'missing_stereotype' if stereotype is None else 'unrecognized_stereotype'
    assert any(d.severity == 'ERROR' and d.kind == expected_kind and 'cOther' in d.identified_sources
               for d in result.diagnostics)


@pytest.mark.parametrize('input_policy', POLICIES)
@pytest.mark.parametrize('failure', ['dangling_target', 'type_mismatch_relation', 'omitted_target_invalid_id'])
def test_class_valued_attribute_handles_unresolved_or_omitted_target_class_boundary(
        run, source_json, tmp_path, input_policy, failure):
    """Rules: DK-ATT-01, DK-GEN-03, DK-DIAG-05; §3.4 opaque source-ID recovery boundary."""
    document = source_json('attributes_datatypes/value_types')
    peer_cls = copy.deepcopy(source_element(document, 'cOther'))
    peer_cls.update(id='cValidPeer', name='ValidPeer', stereotype='kind')
    document['model']['contents'].append(peer_cls)
    peer_attr = copy.deepcopy(source_element(document, 'pFocus'))
    peer_attr.update(id='pPeer', name='peerAttr', cardinality='1', propertyType={'id': 'cValidPeer', 'type': 'Class'})
    source_element(document, 'cOwner')['properties'].append(peer_attr)

    focus = source_element(document, 'pFocus')
    other = source_element(document, 'cOther')
    other['stereotype'] = 'kind'
    if failure == 'dangling_target':
        focus['propertyType'] = {'id': 'missingClass', 'type': 'Class'}
        expected_issues = {'unresolved_reference:missingClass'}
    elif failure == 'type_mismatch_relation':
        relation = {
            'id': 'rOther', 'name': 'rel', 'description': None, 'type': 'Relation',
            'propertyAssignments': None, 'stereotype': 'material', 'isAbstract': False, 'isDerived': False,
            'properties': [
                {'id': 'sOther', 'name': None, 'description': None, 'type': 'Property', 'propertyAssignments': None,
                 'stereotype': None, 'isDerived': False, 'isReadOnly': False, 'isOrdered': False,
                 'cardinality': None, 'propertyType': {'id': 'cOwner', 'type': 'Class'},
                 'subsettedProperties': None, 'redefinedProperties': None, 'aggregationKind': 'NONE'},
                {'id': 'tOther', 'name': None, 'description': None, 'type': 'Property', 'propertyAssignments': None,
                 'stereotype': None, 'isDerived': False, 'isReadOnly': False, 'isOrdered': False,
                 'cardinality': None, 'propertyType': {'id': 'cValidPeer', 'type': 'Class'},
                 'subsettedProperties': None, 'redefinedProperties': None, 'aggregationKind': 'NONE'},
            ],
        }
        document['model']['contents'].append(relation)
        focus['propertyType'] = {'id': 'rOther', 'type': 'Class'}
        expected_issues = {'reference_type_mismatch:rOther'}
    else:
        other['id'] = None
        focus['propertyType'] = {'id': 'cOther', 'type': 'Class'}
        expected_issues = {'invalid_id', 'unresolved_reference:cOther'}

    assert fixture_issues(document) == expected_issues
    result = run(path=write_input(tmp_path, document), iri_strategy='id', input_policy=input_policy)
    assert all(d.code != 'INTERNAL_TRANSFORMATION_FAILURE' for d in result.diagnostics)
    assert any(d.severity == 'ERROR' and d.kind == 'unresolved_attribute_type'
               and 'pFocus' in d.identified_sources and 'unresolved_attribute_type' in d.facts
               for d in result.diagnostics) or (failure == 'omitted_target_invalid_id' and input_policy != 'best-effort')
    if failure == 'omitted_target_invalid_id':
        assert any(d.severity == 'ERROR' and d.kind == 'invalid_id' for d in result.diagnostics)
    if input_policy != 'best-effort':
        assert result.outcome == 'aborted' and result.ontology is None
        return

    assert result.outcome == 'completed-with-errors'
    assert any(d.severity == 'ERROR' and d.kind == 'unresolved_attribute_type'
               and {'pFocus', 'cOwner'} <= set(d.identified_sources)
               for d in result.diagnostics)
    graph = result.ontology
    assert not any(BASE.pFocus in triple or BASE.missingClass in triple for triple in graph)
    assert (BASE.cOwner, RDF.type, OWL.Class) in graph
    assert (BASE.cValidPeer, RDF.type, OWL.Class) in graph
    _assert_ordinary_class_attribute(graph, BASE.pPeer, BASE.cOwner, BASE.cValidPeer)
    _counts(graph, BASE.cOwner, BASE.pPeer, {('exact', 1)}, BASE.cValidPeer)


def test_unresolved_attribute_type_reader_requires_affirmative_condition():
    """Harness only: verify affirmative unresolved-attribute-type wording without fixing provisional codes."""
    accepted = (
        "Attribute value-type reference {'id': 'missingClass', 'type': 'Class'} cannot be resolved: Unresolved source reference.",
        "Attribute 'pFocus' propertyType reference is unresolved.",
        "Attribute target class 'cOther' has no generated local owl:Class.",
        "Unresolved attribute value-type reference for 'pFocus'.",
    )
    rejected = (
        "Attribute value kinds outside datatype/enumeration mappings remain unspecified.",
        "Attribute range without a generated local class remains outside the decided baseline.",
        "Unexpected internal failure while resolving attribute value type.",
        "Not implemented for class-valued attributes.",
        "Attribute value-type reference is resolved.",
        "Attribute target class is not unresolved.",
        "If an attribute value-type reference is unresolved, conversion aborts.",
    )
    for message in accepted:
        assert unresolved_attribute_type_diagnostic(message), message
    for message in rejected:
        assert not unresolved_attribute_type_diagnostic(message), message


@pytest.mark.parametrize('input_policy', POLICIES)
@pytest.mark.parametrize('iri_strategy', ['id', 'name'])
@pytest.mark.parametrize('owner_kind,owner_name', [
    ('plain_primitive', 'string'),
    ('localized_primitive', {'en': 'int'}),
    ('void', 'void'),
], ids=['plain_primitive', 'localized_primitive', 'void'])
def test_attribute_owned_by_primitive_or_void_reports_error_and_omits_cleanly(
        run, source_json, tmp_path, input_policy, iri_strategy, owner_kind, owner_name):
    """Rules: DK-ATT-01, DK-CLS-01, DK-DAT-02, DK-DAT-04, DK-GEN-03, DK-IRI-10, DK-PROP-02, DK-DIAG-01, DK-DIAG-02, DK-DIAG-05; RD-02 Alternative A."""
    document = source_json('attributes_datatypes/value_types')
    d_int = copy.deepcopy(source_element(document, 'dValue'))
    d_int.update(id='dInt', name='int', stereotype='datatype')
    document['model']['contents'].append(d_int)
    source_element(document, 'pFocus').update(cardinality='1', propertyType={'id': 'dInt', 'type': 'Class'})

    owner_dt = source_element(document, 'dValue')
    owner_dt['name'] = owner_name
    owned = copy.deepcopy(source_element(document, 'pFocus'))
    owned.update(
        id='pOwned', name='focus', description='Omitted owned description.',
        stereotype='begin', isDerived=True, isReadOnly=True, isOrdered=True,
        cardinality='2..5', propertyType={'id': 'dValue', 'type': 'Class'},
    )
    owner_dt['properties'] = [owned]
    assert not fixture_issues(document)

    result = run(path=write_input(tmp_path, document), iri_strategy=iri_strategy, input_policy=input_policy)
    assert all(d.code != 'INTERNAL_TRANSFORMATION_FAILURE' for d in result.diagnostics)
    assert any(
        d.severity == 'ERROR'
        and d.kind == 'attribute_owner_without_local_class'
        and 'attribute_owner_without_local_class' in d.facts
        and {'pOwned', 'dValue'} <= set(d.identified_sources)
        for d in result.diagnostics
    ), result.diagnostics

    if input_policy != 'best-effort':
        assert result.outcome == 'aborted' and result.ontology is None
        return

    assert result.outcome == 'completed-with-errors'
    graph = result.ontology
    owner_iri = BASE.cOwner if iri_strategy == 'id' else BASE.Owner
    other_iri = BASE.cOther if iri_strategy == 'id' else BASE.Other
    prop_iri = BASE.pFocus if iri_strategy == 'id' else BASE.focus
    assert set(graph.subjects(RDF.type, OWL.Class)) == {owner_iri, other_iri}
    assert (owner_iri, RDF.type, OWL.Class) in graph
    assert (other_iri, RDF.type, OWL.Class) in graph
    _focus(graph, OWL.DatatypeProperty, XSD.int, owner_iri, prop_iri)
    _counts(graph, owner_iri, prop_iri, {('exact', 1)}, XSD.int)
    local_props = {
        s for kind in (OWL.ObjectProperty, OWL.DatatypeProperty)
        for s in graph.subjects(RDF.type, kind)
        if str(s).startswith(str(BASE))
    }
    assert local_props == {prop_iri}
    assert all(list(graph.objects(p, RDFS.domain)) for p in local_props)
    assert not any(BASE.dValue in triple or BASE.pOwned in triple for triple in graph)
    assert not list(graph.subjects(DCTERMS.identifier, Literal('pOwned')))
    assert not list(graph.subjects(DCTERMS.identifier, Literal('dValue')))
    assert not any('Omitted owned description.' in str(o) for o in graph.objects(None, RDFS.comment))
    assert not any('pOwned' in d.identified_sources and d.kind != 'attribute_owner_without_local_class'
                   for d in result.diagnostics)


@pytest.mark.parametrize('iri_strategy', ['id', 'name'])
@pytest.mark.parametrize('scenario', [
    'missing_card_and_name_and_unresolved_type',
    'invalid_card_and_void_type_and_flags',
])
def test_omitted_primitive_or_void_owned_attribute_suppresses_attribute_level_diagnostics(
        run, source_json, tmp_path, iri_strategy, scenario):
    """Rules: DK-ATT-01, DK-DIAG-01, DK-DIAG-05; RD-02 Alternative A."""
    document = source_json('attributes_datatypes/value_types')
    d_int = copy.deepcopy(source_element(document, 'dValue'))
    d_int.update(id='dInt', name='int', stereotype='datatype')
    d_void = copy.deepcopy(source_element(document, 'dValue'))
    d_void.update(id='dVoid', name='void', stereotype='datatype')
    document['model']['contents'].extend([d_int, d_void])
    source_element(document, 'pFocus').update(cardinality='1', propertyType={'id': 'dInt', 'type': 'Class'})

    owner_dt = source_element(document, 'dValue')
    owner_dt['name'] = 'string' if scenario == 'missing_card_and_name_and_unresolved_type' else 'void'
    owned = copy.deepcopy(source_element(document, 'pFocus'))
    if scenario == 'missing_card_and_name_and_unresolved_type':
        owned.update(id='pOwned', name=None, propertyType={'id': 'missingType', 'type': 'Class'})
        del owned['cardinality']
        expected_issues = {'unresolved_reference:missingType'}
    else:
        owned.update(id='pOwned', name='badOwned', isDerived=True, isReadOnly=True, isOrdered=True,
                     cardinality='bad..bounds', propertyType={'id': 'dVoid', 'type': 'Class'})
        expected_issues = frozenset()
    owner_dt['properties'] = [owned]
    assert fixture_issues(document) == expected_issues

    result = run(path=write_input(tmp_path, document), iri_strategy=iri_strategy, input_policy='best-effort')
    assert result.outcome == 'completed-with-errors'
    owned_events = [d for d in result.diagnostics if 'pOwned' in d.identified_sources]
    assert owned_events and all(
        d.severity == 'ERROR' and d.kind == 'attribute_owner_without_local_class' for d in owned_events
    ), owned_events
    suppressed_kinds = {
        'void_datatype', 'unresolved_attribute_type', 'missing_cardinality',
        'invalid_cardinality', 'generic_id_fallback', 'missing_name',
        'derived_status', 'ordering',
    }
    assert not any(d.kind in suppressed_kinds for d in result.diagnostics), result.diagnostics


@pytest.mark.parametrize('input_policy', POLICIES)
@pytest.mark.parametrize('case', [
    'custom_datatype_name',
    'custom_localized_datatype',
    'kind_owned_primitive_typed',
    'kind_owned_void_typed',
])
def test_custom_datatype_owned_attribute_and_primitive_or_void_typed_attribute_remain_preserved(
        run, source_json, tmp_path, input_policy, case):
    """Rules: DK-ATT-01, DK-CLS-01, DK-DAT-02, DK-DAT-04, DK-DAT-05, DK-GEN-03, DK-IRI-10, DK-DIAG-05."""
    document = source_json('attributes_datatypes/value_types')
    if case in {'custom_datatype_name', 'custom_localized_datatype'}:
        d_custom = source_element(document, 'dValue')
        d_custom['name'] = 'TimeInterval' if case == 'custom_datatype_name' else {'de': 'Ganzzahl', 'en': 'int'}
        d_prim = copy.deepcopy(d_custom)
        d_prim.update(id='dPrim', name='int', stereotype='datatype')
        document['model']['contents'].append(d_prim)
        owned = copy.deepcopy(source_element(document, 'pFocus'))
        owned.update(id='pCustomOwned', name='seconds', cardinality='1', propertyType={'id': 'dPrim', 'type': 'Class'})
        d_custom['properties'] = [owned]
        source_element(document, 'pFocus')['cardinality'] = '1'
    elif case == 'kind_owned_primitive_typed':
        source_element(document, 'cOwner')['stereotype'] = 'kind'
        source_element(document, 'dValue')['name'] = 'string'
        source_element(document, 'pFocus')['cardinality'] = '1'
    else:
        source_element(document, 'cOwner')['stereotype'] = 'kind'
        source_element(document, 'dValue')['name'] = 'void'
        source_element(document, 'pFocus')['cardinality'] = '1'

    assert not fixture_issues(document)
    result = run(path=write_input(tmp_path, document), iri_strategy='id', input_policy=input_policy)
    assert result.outcome == 'completed'
    assert not any(d.severity == 'ERROR' or d.kind == 'attribute_owner_without_local_class'
                   for d in result.diagnostics)
    graph = result.ontology
    if case in {'custom_datatype_name', 'custom_localized_datatype'}:
        assert (BASE.dValue, RDF.type, OWL.Class) in graph
        _focus(graph, OWL.ObjectProperty, BASE.dValue, BASE.cOwner, BASE.pFocus)
        _focus(graph, OWL.DatatypeProperty, XSD.int, BASE.dValue, BASE.pCustomOwned)
        _counts(graph, BASE.dValue, BASE.pCustomOwned, {('exact', 1)}, XSD.int)
    elif case == 'kind_owned_primitive_typed':
        _focus(graph, OWL.DatatypeProperty, XSD.string, BASE.cOwner, BASE.pFocus)
        _counts(graph, BASE.cOwner, BASE.pFocus, {('exact', 1)}, XSD.string)
    else:
        _focus(graph, OWL.DatatypeProperty, None, BASE.cOwner, BASE.pFocus)
        _counts(graph, BASE.cOwner, BASE.pFocus, {('exact', 1)}, None)
        assert any(d.kind == 'void_datatype' and d.severity == 'WARNING' for d in result.diagnostics)


def test_attribute_owner_without_local_class_reader_requires_affirmative_conditions():
    """Harness only: verify affirmative owner-lacks-local-class wording without fixing provisional codes."""
    accepted = (
        "Attribute 'pOwned' owner 'dValue' has no generated local owl:Class.",
        "Attribute 'pOwned' is owned by Class 'dValue' without a generated local owl:Class representation.",
        "Owning Class 'dValue' of attribute 'pOwned' lacks a generated local OWL class.",
        "Attribute 'pOwned' cannot be transformed because its owning datatype 'dValue' does not generate a local owl:Class.",
    )
    rejected = (
        "Attribute ownership without a generated local class is outside the decided baseline.",
        "Unexpected internal failure while collecting attributes: NotImplementedError.",
        "Not implemented for primitive-owned attributes.",
        "Attribute 'pOwned' owner 'dCustom' has a generated local owl:Class.",
        "Attribute 'pOwned' owner 'dCustom' does not lack a local owl:Class.",
        "If an attribute owner lacks a local owl:Class, conversion aborts.",
        "Attribute target class 'cOther' has no generated local owl:Class.",
        "Attribute 'pFocus' value-type reference 'dValue' has no local owl:Class.",
        "Relation 'r0' source 'dValue' has no generated local owl:Class.",
        "Generalization set categorizer 'dValue' has no generated local owl:Class.",
    )
    for message in accepted:
        assert attribute_owner_without_local_class_diagnostic(message), message
    for message in rejected:
        assert not attribute_owner_without_local_class_diagnostic(message), message


def _class_properties_target(document, class_kind):
    target = source_element(document, 'cOther')
    if class_kind == 'kind':
        target['stereotype'] = 'kind'
    elif class_kind == 'custom_datatype':
        target.update(name='CustomType', stereotype='datatype')
    else:
        target.update(
            name='StatusEnum',
            stereotype='enumeration',
            literals=[
                {'id': 'vOne', 'name': 'One', 'description': None, 'type': 'Literal', 'propertyAssignments': None},
                {'id': 'vTwo', 'name': 'Two', 'description': None, 'type': 'Literal', 'propertyAssignments': None},
            ],
        )
    return target


@pytest.mark.parametrize('input_policy', POLICIES)
@pytest.mark.parametrize('class_kind', ['kind', 'custom_datatype', 'enumeration'])
@pytest.mark.parametrize('form', ['absent', 'null', 'empty'])
def test_empty_class_properties_representations_are_equivalent(
        run, invoke, source_json, tmp_path, input_policy, class_kind, form):
    """Rules: DK-ATT-01, DK-DIAG-05; §3.2. RD-02 Alternative 3A."""
    control_doc = source_json('attributes_datatypes/value_types')
    _class_properties_target(control_doc, class_kind)['properties'] = []
    document = source_json('attributes_datatypes/value_types')
    target = _class_properties_target(document, class_kind)
    if form == 'absent':
        target.pop('properties', None)
    else:
        target['properties'] = None if form == 'null' else []

    baseline = run(path=write_input(tmp_path, control_doc, 'control.json'),
                   iri_strategy='id', input_policy=input_policy)
    result = run(path=write_input(tmp_path, document),
                 iri_strategy='id', input_policy=input_policy)
    assert baseline.outcome == result.outcome == 'completed'
    assert_graph_equal(baseline.ontology, result.ontology)
    assert diagnostic_record_counts(invoke.report_content(result).events) == diagnostic_record_counts(
        invoke.report_content(baseline).events)
    assert not any(d.severity in {'WARNING', 'ERROR'} for d in result.diagnostics)
    assert (BASE.cOther, RDF.type, OWL.Class) in result.ontology


_NON_ARRAY_CLASS_PROPERTIES = [
    ('object', lambda prop: copy.deepcopy(prop)),
    ('string', lambda _prop: 'BAD_PROPERTIES_SENTINEL'),
    ('empty_string', lambda _prop: ''),
    ('zero', lambda _prop: 0),
    ('false', lambda _prop: False),
    ('true', lambda _prop: True),
]


@pytest.mark.parametrize('input_policy', POLICIES)
@pytest.mark.parametrize('class_kind', ['kind', 'custom_datatype', 'enumeration'])
@pytest.mark.parametrize('form,builder', _NON_ARRAY_CLASS_PROPERTIES, ids=[item[0] for item in _NON_ARRAY_CLASS_PROPERTIES])
def test_malformed_class_properties_container_follows_policy(
        run, source_json, tmp_path, input_policy, class_kind, form, builder):
    """Rules: DK-ATT-01, DK-CLS-01, DK-DIAG-04, DK-DIAG-05; §3.2, §3.4. RD-02 Alternative 3A."""
    document = source_json('attributes_datatypes/value_types')
    source_element(document, 'pFocus')['cardinality'] = '1'
    target = _class_properties_target(document, class_kind)
    sample_prop = copy.deepcopy(source_element(document, 'pFocus'))
    sample_prop.update(id='pIgnored', name='ignoredAttr')
    target['properties'] = builder(sample_prop)

    result = run(path=write_input(tmp_path, document), iri_strategy='id', input_policy=input_policy)
    assert all(d.code != 'INTERNAL_TRANSFORMATION_FAILURE' for d in result.diagnostics), result.diagnostics
    assert not any(d.code == 'UNKNOWN_INFORMATION' for d in result.diagnostics), result.diagnostics
    assert any(
        d.severity == 'ERROR'
        and 'class_properties_non_array' in d.facts
        and 'cOther' in d.identified_sources
        for d in result.diagnostics
    ), result.diagnostics

    if input_policy != 'best-effort':
        assert result.outcome == 'aborted' and result.ontology is None
        return

    assert result.outcome == 'completed-with-errors'
    graph = result.ontology
    assert (BASE.cOwner, RDF.type, OWL.Class) in graph
    assert (BASE.cOther, RDF.type, OWL.Class) in graph
    _focus(graph, OWL.DatatypeProperty, XSD.int, BASE.cOwner, BASE.pFocus)
    _counts(graph, BASE.cOwner, BASE.pFocus, {('exact', 1)}, XSD.int)
    assert not any(BASE.pIgnored in triple for triple in graph)
    assert not list(graph.subjects(DCTERMS.identifier, Literal('pIgnored')))
    if class_kind == 'enumeration':
        assert (BASE.vOne, RDF.type, OWL.NamedIndividual) in graph
        assert (BASE.vTwo, RDF.type, OWL.NamedIndividual) in graph


_INVALID_CLASS_PROPERTY_ENTRIES = [
    ('null_entry', None),
    ('string_entry', 'BAD_PROPERTY_ENTRY_SENTINEL'),
    ('zero_entry', 0),
    ('false_entry', False),
    ('array_entry', []),
    ('known_class', {'id': 'fakeClassProp', 'name': 'Fake', 'description': None, 'type': 'Class', 'propertyAssignments': None}),
    ('known_literal', {'id': 'fakeLitProp', 'name': 'FakeLit', 'description': None, 'type': 'Literal', 'propertyAssignments': None}),
    ('unknown_string_type', {'id': 'fakeUnknownProp', 'name': 'FakeUnknown', 'description': None, 'type': 'Diagram', 'propertyAssignments': None}),
    ('missing_type', {'id': 'fakeMissingType', 'name': 'FakeMissing', 'description': None, 'propertyAssignments': None}),
    ('null_type', {'id': 'fakeNullType', 'name': 'FakeNull', 'description': None, 'type': None, 'propertyAssignments': None}),
    ('empty_type', {'id': 'fakeEmptyType', 'name': 'FakeEmpty', 'description': None, 'type': '', 'propertyAssignments': None}),
    ('whitespace_type', {'id': 'fakeBlankType', 'name': 'FakeBlank', 'description': None, 'type': ' \t ', 'propertyAssignments': None}),
]


@pytest.mark.parametrize('input_policy', POLICIES)
@pytest.mark.parametrize('iri_strategy', ['id', 'name'])
@pytest.mark.parametrize('entry_case,bad_entry', _INVALID_CLASS_PROPERTY_ENTRIES, ids=[item[0] for item in _INVALID_CLASS_PROPERTY_ENTRIES])
def test_invalid_class_properties_entries_preserve_owner_and_valid_siblings(
        run, source_json, tmp_path, input_policy, iri_strategy, entry_case, bad_entry):
    """Rules: DK-ATT-01, DK-ATT-03, DK-GEN-03, DK-CLS-01, DK-DIAG-04, DK-DIAG-05; §3.2. RD-02 Alternative 3A."""
    document = source_json('attributes_datatypes/value_types')
    focus = source_element(document, 'pFocus')
    focus['cardinality'] = '1'
    sibling_after = copy.deepcopy(focus)
    sibling_after.update(id='pAfter', name='afterAttr', cardinality='2..5')
    source_element(document, 'cOwner')['properties'] = [focus, copy.deepcopy(bad_entry), sibling_after]

    result = run(path=write_input(tmp_path, document), iri_strategy=iri_strategy, input_policy=input_policy)
    assert all(d.code != 'INTERNAL_TRANSFORMATION_FAILURE' for d in result.diagnostics), result.diagnostics
    assert not any(d.code == 'UNKNOWN_INFORMATION' for d in result.diagnostics), result.diagnostics
    assert any(
        d.severity == 'ERROR'
        and 'class_properties_invalid_entry' in d.facts
        and (
            {'cOwner', 'fakeClassProp', 'fakeLitProp', 'fakeUnknownProp', 'fakeMissingType',
             'fakeNullType', 'fakeEmptyType', 'fakeBlankType'} & set(d.identified_sources)
            or any(s.path.startswith('$.model.contents[0].properties[1]') for s in d.raw.sources)
        )
        for d in result.diagnostics
    ), result.diagnostics

    if input_policy != 'best-effort':
        assert result.outcome == 'aborted' and result.ontology is None
        return

    assert result.outcome == 'completed-with-errors'
    graph = result.ontology
    owner_iri = BASE.cOwner if iri_strategy == 'id' else BASE.Owner
    other_iri = BASE.cOther if iri_strategy == 'id' else BASE.Other
    p_focus = BASE.pFocus if iri_strategy == 'id' else one_subject(graph, DCTERMS.identifier, Literal('pFocus'))
    p_after = BASE.pAfter if iri_strategy == 'id' else one_subject(graph, DCTERMS.identifier, Literal('pAfter'))
    assert (owner_iri, RDF.type, OWL.Class) in graph
    assert (other_iri, RDF.type, OWL.Class) in graph
    _focus(graph, OWL.DatatypeProperty, XSD.int, owner_iri, p_focus)
    _focus(graph, OWL.DatatypeProperty, XSD.int, owner_iri, p_after)
    _counts(graph, owner_iri, p_focus, {('exact', 1)}, XSD.int)
    _counts(graph, owner_iri, p_after, {('min', 2), ('max', 5)}, XSD.int)
    local_props = {
        s for kind in (OWL.ObjectProperty, OWL.DatatypeProperty)
        for s in graph.subjects(RDF.type, kind)
        if str(s).startswith(str(BASE))
    }
    assert local_props == {p_focus, p_after}
    for fake_id in ('fakeClassProp', 'fakeLitProp', 'fakeUnknownProp',
                    'fakeMissingType', 'fakeNullType', 'fakeEmptyType', 'fakeBlankType'):
        assert not any(BASE[fake_id] in triple for triple in graph)
        assert not list(graph.subjects(DCTERMS.identifier, Literal(fake_id)))


@pytest.mark.parametrize('input_policy', POLICIES)
@pytest.mark.parametrize('condition', [
    'duplicate_sibling_after_invalid_entry',
    'rejected_sibling_stereotype_after_invalid_entry',
    'accepted_custom_sibling_stereotype_after_invalid_entry',
    'invalid_sibling_id_after_invalid_entry',
    'duplicate_owner_id_with_malformed_properties',
    'rejected_owner_stereotype_with_malformed_properties',
])
def test_class_properties_container_and_entries_respect_diagnostic_precedence(
        run, source_json, tmp_path, input_policy, condition):
    """Rules: DK-ATT-01, DK-DIAG-05, DK-DIAG-06; §3.4 opaque source IDs and duplicate IDs. RD-02 Alternative 3A."""
    document = source_json('attributes_datatypes/value_types')
    owner = source_element(document, 'cOwner')
    focus = source_element(document, 'pFocus')
    focus['cardinality'] = '1'
    sibling = copy.deepcopy(focus)
    sibling.update(id='pSibling', name='siblingAttr')
    options = {'iri_strategy': 'id', 'input_policy': input_policy}
    always_abort = True

    if condition == 'duplicate_sibling_after_invalid_entry':
        sibling['id'] = 'cOther'
        owner['properties'] = [None, sibling]
        expected_kind = 'duplicate_id'
    elif condition == 'rejected_sibling_stereotype_after_invalid_entry':
        sibling['stereotype'] = 'customProp'
        owner['properties'] = [None, sibling]
        options['stereotype_policy'] = 'allow-missing'
        expected_kind = 'unrecognized_stereotype'
    elif condition == 'accepted_custom_sibling_stereotype_after_invalid_entry':
        sibling['stereotype'] = 'customProp'
        owner['properties'] = [None, sibling]
        options['stereotype_policy'] = 'allow-custom'
        expected_kind = 'unrecognized_stereotype'
        always_abort = False
    elif condition == 'invalid_sibling_id_after_invalid_entry':
        sibling['id'] = ''
        owner['properties'] = [None, sibling]
        expected_kind = 'invalid_id'
        always_abort = False
    elif condition == 'duplicate_owner_id_with_malformed_properties':
        dup = copy.deepcopy(source_element(document, 'cOther'))
        dup['id'] = 'cOwner'
        owner['properties'] = 'bad'
        document['model']['contents'].append(dup)
        expected_kind = 'duplicate_id'
    else:
        owner['stereotype'] = None
        owner['properties'] = 'bad'
        options['stereotype_policy'] = 'require-known'
        expected_kind = 'missing_stereotype'

    result = run(path=write_input(tmp_path, document), **options)
    assert all(d.code != 'INTERNAL_TRANSFORMATION_FAILURE' for d in result.diagnostics), result.diagnostics
    if condition == 'accepted_custom_sibling_stereotype_after_invalid_entry':
        assert any(d.severity == 'WARNING' and d.kind == 'unrecognized_stereotype' and 'pSibling' in d.identified_sources
                   for d in result.diagnostics), result.diagnostics
        assert any(d.severity == 'ERROR' and 'class_properties_invalid_entry' in d.facts
                   for d in result.diagnostics), result.diagnostics
    else:
        assert any(d.severity == 'ERROR' and d.kind == expected_kind for d in result.diagnostics), result.diagnostics
        if expected_kind == 'duplicate_id':
            assert any(d.code == 'DUPLICATE_SOURCE_ID' and {'competing_declarations', 'conversion_aborted'} <= d.facts
                       for d in result.diagnostics if d.kind == 'duplicate_id')

    if always_abort or input_policy != 'best-effort':
        assert result.outcome == 'aborted' and result.ontology is None
    else:
        assert result.outcome == 'completed-with-errors'
        assert (BASE.cOwner, RDF.type, OWL.Class) in result.ontology
        assert (BASE.cOther, RDF.type, OWL.Class) in result.ontology
        if condition == 'accepted_custom_sibling_stereotype_after_invalid_entry':
            _focus(result.ontology, OWL.DatatypeProperty, XSD.int, BASE.cOwner, BASE.pSibling)
        else:
            assert not any(BASE.pSibling in triple for triple in result.ontology)


_DATATYPE_CARRIER_CASES = [
    ('invalid_earlier_int_does_not_beat_float', {'a_': 'int', 'en': 'float'}, 'float', 'invalid_language_string_entry'),
    ('invalid_earlier_custom_keeps_int', {'a_': 'Ganzzahl', 'en': 'int'}, 'int', 'invalid_language_string_entry'),
    ('invalid_earlier_int_keeps_void', {'a_': 'int', 'en': 'void'}, 'void', 'invalid_language_string_entry'),
    ('zero_valid_langstring_entries_become_custom', {'a_': 'int', 'en': 42}, 'custom', 'invalid_language_string_entry'),
    ('wrong_whole_field_type_becomes_custom', 123, 'custom', 'malformed_textual_carrier'),
]


@pytest.mark.parametrize('input_policy', POLICIES)
@pytest.mark.parametrize('iri_strategy', ['name', 'id'])
@pytest.mark.parametrize('case,name_value,expected_kind,expected_fact', _DATATYPE_CARRIER_CASES,
                         ids=[row[0] for row in _DATATYPE_CARRIER_CASES])
def test_datatype_name_carrier_validation_and_primitive_selection_under_policy(
        run, source_json, tmp_path, input_policy, iri_strategy, case, name_value, expected_kind, expected_fact):
    """Rules: DK-DAT-02, DK-DAT-04, DK-DAT-05, DK-ATT-01, DK-IRI-04, DK-IRI-10, DK-LBL-01, DK-LBL-02, DK-DIAG-01, DK-DIAG-05; §§3.2, 15. RD-02 Alt 1A."""
    document = source_json('attributes_datatypes/value_types')
    document['languages'] = ['de']
    source_element(document, 'dValue')['name'] = copy.deepcopy(name_value)

    result = run(path=write_input(tmp_path, document), iri_strategy=iri_strategy,
                 input_policy=input_policy, language='nl')
    assert all(d.code != 'INTERNAL_TRANSFORMATION_FAILURE' for d in result.diagnostics), result.diagnostics
    assert any(d.severity == 'ERROR' and expected_fact in d.facts for d in result.diagnostics), result.diagnostics

    if input_policy != 'best-effort':
        assert result.outcome == 'aborted' and result.ontology is None
        return

    assert result.outcome == 'completed-with-errors'
    owner = BASE.cOwner if iri_strategy == 'id' else BASE.Owner
    prop = BASE.pFocus if iri_strategy == 'id' else one_subject(result.ontology, DCTERMS.identifier, Literal('pFocus'))
    if expected_kind in {'int', 'float'}:
        _focus(result.ontology, OWL.DatatypeProperty, XSD[expected_kind], owner, prop)
        assert not list(result.ontology.subjects(DCTERMS.identifier, Literal('dValue')))
    elif expected_kind == 'void':
        _focus(result.ontology, OWL.DatatypeProperty, None, owner, prop)
        assert any(d.kind == 'void_datatype' and d.severity == 'WARNING' for d in result.diagnostics)
        assert not list(result.ontology.subjects(DCTERMS.identifier, Literal('dValue')))
    else:
        custom = BASE.dValue if iri_strategy == 'id' else BASE.unnamedClass_dValue
        _focus(result.ontology, OWL.ObjectProperty, custom, owner, prop)
        assert (custom, RDF.type, OWL.Class) in result.ontology
        assert not list(result.ontology.objects(custom, RDFS.label))
        assert any(d.kind == 'missing_name' and d.severity == 'WARNING' and 'dValue' in d.source_ids
                   for d in result.diagnostics)


@pytest.mark.parametrize('input_policy', POLICIES)
@pytest.mark.parametrize('iri_strategy', ['id', 'name'])
@pytest.mark.parametrize('value_kind', ['primitive', 'custom', 'enumeration', 'untyped'])
@pytest.mark.parametrize('bad_value', [pytest.param(42, id='int'), pytest.param(' \t ', id='whitespace_only')])
def test_attribute_malformed_stereotype_omits_field_and_preserves_mapping(
        run, invoke, source_json, tmp_path, input_policy, iri_strategy, value_kind, bad_value):
    """Rules: DK-ATT-01, DK-ATT-03, DK-DAT-01, DK-DAT-05, DK-CLS-10, DK-PROP-04, DK-PROP-05, DK-PROP-06, DK-GEN-03, DK-DIAG-05; §3.2. RD-02 Alt 1C + Sub-option 2A."""
    document = source_json('attributes_datatypes/value_types')
    focus = source_element(document, 'pFocus')
    focus.update(
        stereotype=bad_value,
        cardinality='2..5',
        isDerived=True,
        isReadOnly=True,
        isOrdered=True,
    )
    value_cls = source_element(document, 'dValue')
    if value_kind == 'untyped':
        focus['propertyType'] = None
        prop_kind, expected_range = OWL.DatatypeProperty, None
    elif value_kind == 'primitive':
        prop_kind, expected_range = OWL.DatatypeProperty, XSD.int
    elif value_kind == 'custom':
        value_cls['name'] = 'StructuredValue'
        prop_kind = OWL.ObjectProperty
        expected_range = BASE.dValue if iri_strategy == 'id' else BASE.StructuredValue
    else:
        value_cls.update(
            name='Status', stereotype='enumeration',
            literals=[{'id': 'vOne', 'name': 'One', 'description': None, 'type': 'Literal', 'propertyAssignments': None}],
        )
        prop_kind = OWL.ObjectProperty
        expected_range = BASE.dValue if iri_strategy == 'id' else BASE.Status

    result = run(path=write_input(tmp_path, document), iri_strategy=iri_strategy, input_policy=input_policy)
    assert all(d.code != 'INTERNAL_TRANSFORMATION_FAILURE' for d in result.diagnostics), result.diagnostics
    assert any(
        d.severity == 'ERROR' and 'malformed_stereotype' in d.facts and 'pFocus' in d.identified_sources
        and d.code not in {'MISSING_STEREOTYPE', 'UNRECOGNIZED_STEREOTYPE', 'INTERNAL_TRANSFORMATION_FAILURE'}
        for d in result.diagnostics
    ), result.diagnostics

    if input_policy != 'best-effort':
        assert result.outcome == 'aborted' and result.ontology is None
        return

    assert result.outcome == 'completed-with-errors'
    graph = result.ontology
    owner = BASE.cOwner if iri_strategy == 'id' else BASE.Owner
    prop = BASE.pFocus if iri_strategy == 'id' else one_subject(graph, DCTERMS.identifier, Literal('pFocus'))
    _focus(graph, prop_kind, expected_range, owner, prop)
    _counts(graph, owner, prop, {('min', 2), ('max', 5)}, expected_range)
    assert (prop, RDFS.label, Literal('focus')) in graph
    assert invoke.read_property_stereotype_comments(result) == ()
    assert any(d.kind == 'derived_status' and d.severity == 'INFO' and 'pFocus' in d.identified_sources
               for d in result.diagnostics)
    assert any(d.kind == 'ordering' and d.severity == 'INFO' and 'pFocus' in d.identified_sources
               for d in result.diagnostics)


@pytest.mark.parametrize('input_policy', POLICIES)
@pytest.mark.parametrize('role', ['target_class', 'owner_class'])
@pytest.mark.parametrize('bad_value', [pytest.param(True, id='bool_true'), pytest.param('', id='empty_string')])
def test_attribute_referencing_or_owned_by_malformed_stereotype_class_follows_policy(
        run, source_json, tmp_path, input_policy, role, bad_value):
    """Rules: DK-ATT-01, DK-DIAG-05; §3.2. RD-02 Alt 1C + Sub-option 2A."""
    document = source_json('attributes_datatypes/value_types')
    if role == 'target_class':
        source_element(document, 'cOther')['stereotype'] = bad_value
        source_element(document, 'pFocus')['propertyType'] = {'id': 'cOther', 'type': 'Class'}
        bad_cls_id = 'cOther'
    else:
        owned = copy.deepcopy(source_element(document, 'pFocus'))
        owned.update(id='pOwned', name='ownedAttr')
        source_element(document, 'cOther').update(stereotype=bad_value, properties=[owned])
        bad_cls_id = 'cOther'

    result = run(path=write_input(tmp_path, document), iri_strategy='id', input_policy=input_policy)
    assert all(d.code != 'INTERNAL_TRANSFORMATION_FAILURE' for d in result.diagnostics), result.diagnostics
    assert any(
        d.severity == 'ERROR' and 'malformed_stereotype' in d.facts and bad_cls_id in d.identified_sources
        for d in result.diagnostics
    ), result.diagnostics

    if input_policy != 'best-effort':
        assert result.outcome == 'aborted' and result.ontology is None
        assert not any(d.kind in {'unresolved_attribute_type', 'attribute_owner_without_local_class'}
                       for d in result.diagnostics)
        return

    assert result.outcome == 'completed-with-errors'
    graph = result.ontology
    assert (BASE.cOwner, RDF.type, OWL.Class) in graph
    assert not any(BASE.cOther in triple for triple in graph)
    if role == 'target_class':
        assert any(
            d.severity == 'ERROR' and d.kind == 'unresolved_attribute_type' and 'pFocus' in d.identified_sources
            for d in result.diagnostics
        ), result.diagnostics
        assert not any(BASE.pFocus in triple for triple in graph)
    else:
        _focus(graph, OWL.DatatypeProperty, XSD.int, BASE.cOwner, BASE.pFocus)
        assert not any(BASE.pOwned in triple for triple in graph)
        assert not any(d.kind == 'attribute_owner_without_local_class' for d in result.diagnostics)


@pytest.mark.parametrize('input_policy', POLICIES)
@pytest.mark.parametrize('iri_strategy', ['id', 'name'])
@pytest.mark.parametrize('value_kind', ['primitive', 'custom', 'enumeration', 'untyped'])
@pytest.mark.parametrize('malformed_flag', ['isDerived', 'isReadOnly', 'isOrdered'])
def test_attribute_malformed_boolean_flag_preserves_value_kind_mapping_and_siblings(
        run, source_json, tmp_path, input_policy, iri_strategy, value_kind, malformed_flag):
    """Rules: DK-ATT-01, DK-ATT-03, DK-DAT-01, DK-DAT-03, DK-DAT-05, DK-CLS-10, DK-GEN-03, DK-GEN-05, DK-PROP-04, DK-PROP-05, DK-DIAG-05, DK-DIAG-16, DK-DIAG-18; §3.2. RD-02 Alternative 1."""
    document = source_json('attributes_datatypes/value_types')
    focus = source_element(document, 'pFocus')
    focus.update(cardinality='2..5', isDerived=True, isReadOnly=True, isOrdered=True)
    value_cls = source_element(document, 'dValue')
    if value_kind == 'untyped':
        focus['propertyType'] = None
        prop_kind, expected_range = OWL.DatatypeProperty, None
    elif value_kind == 'primitive':
        prop_kind, expected_range = OWL.DatatypeProperty, XSD.int
    elif value_kind == 'custom':
        value_cls['name'] = 'StructuredValue'
        prop_kind = OWL.ObjectProperty
        expected_range = BASE.dValue if iri_strategy == 'id' else BASE.StructuredValue
    else:
        value_cls.update(
            name='Status', stereotype='enumeration',
            literals=[{'id': 'vOne', 'name': 'One', 'description': None, 'type': 'Literal', 'propertyAssignments': None}],
        )
        prop_kind = OWL.ObjectProperty
        expected_range = BASE.dValue if iri_strategy == 'id' else BASE.Status

    baseline_doc = copy.deepcopy(document)
    source_element(baseline_doc, 'pFocus').pop(malformed_flag, None)
    focus[malformed_flag] = 'true' if malformed_flag != 'isOrdered' else 1

    result = run(path=write_input(tmp_path, document), iri_strategy=iri_strategy, input_policy=input_policy)
    assert all(d.code != 'INTERNAL_TRANSFORMATION_FAILURE' for d in result.diagnostics), result.diagnostics
    assert any(
        d.severity == 'ERROR' and 'malformed_boolean_flag' in d.facts and 'pFocus' in d.identified_sources
        for d in result.diagnostics
    ), result.diagnostics

    if input_policy != 'best-effort':
        assert result.outcome == 'aborted' and result.ontology is None
        return

    assert result.outcome == 'completed-with-errors'
    baseline = run(path=write_input(tmp_path, baseline_doc, 'baseline.json'),
                   iri_strategy=iri_strategy, input_policy='tolerant')
    assert baseline.outcome == 'completed'
    assert_graph_equal(result.ontology, baseline.ontology)

    graph = result.ontology
    owner = BASE.cOwner if iri_strategy == 'id' else BASE.Owner
    prop = BASE.pFocus if iri_strategy == 'id' else one_subject(graph, DCTERMS.identifier, Literal('pFocus'))
    _focus(graph, prop_kind, expected_range, owner, prop)
    _counts(graph, owner, prop, {('min', 2), ('max', 5)}, expected_range)
    assert (prop, RDFS.label, Literal('focus')) in graph
    assert bool([d for d in result.diagnostics if d.kind == 'derived_status' and 'pFocus' in d.identified_sources]) == (malformed_flag != 'isDerived')
    assert bool([d for d in result.diagnostics if d.kind == 'ordering' and 'pFocus' in d.identified_sources]) == (malformed_flag != 'isOrdered')


@pytest.mark.parametrize('input_policy', POLICIES)
@pytest.mark.parametrize('owner_kind', ['primitive', 'void'])
def test_attribute_owned_by_class_without_local_class_precedes_malformed_boolean_flag(
        run, source_json, tmp_path, input_policy, owner_kind):
    """Rules: DK-ATT-01, DK-DIAG-05; §3.2. RD-02 Alternative 1."""
    document = source_json('attributes_datatypes/value_types')
    owner_cls = source_element(document, 'dValue')
    if owner_kind == 'void':
        owner_cls['name'] = 'void'
        source_element(document, 'pFocus')['propertyType'] = None
    bad_attr = copy.deepcopy(source_element(document, 'pFocus'))
    bad_attr.update(id='pOwnedByNoClass', name='ownedByNoClass', isDerived='true', isReadOnly=1, isOrdered=[])
    owner_cls['properties'] = [bad_attr]

    result = run(path=write_input(tmp_path, document), iri_strategy='id', input_policy=input_policy)
    assert all(d.code != 'INTERNAL_TRANSFORMATION_FAILURE' for d in result.diagnostics), result.diagnostics
    assert any(
        d.severity == 'ERROR'
        and d.kind == 'attribute_owner_without_local_class'
        and 'pOwnedByNoClass' in d.identified_sources
        for d in result.diagnostics
    ), result.diagnostics
    assert not any('malformed_boolean_flag' in d.facts for d in result.diagnostics), result.diagnostics
    if input_policy != 'best-effort':
        assert result.outcome == 'aborted' and result.ontology is None
    else:
        assert result.outcome == 'completed-with-errors'
        _focus(result.ontology, OWL.DatatypeProperty, None if owner_kind == 'void' else XSD.int, BASE.cOwner, BASE.pFocus)
        assert not any(BASE.pOwnedByNoClass in triple or BASE.dValue in triple for triple in result.ontology)
