"""Punned class/individual identity, categorizers, and powertype extension."""

import copy

import pytest
from rdflib import Graph, Literal, Namespace
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS

from tests.support.data import source_element, write_input, fixture_issues
from tests.support.invocation import diagnostic_signatures
from tests.support.rdf import assert_contains, assert_selected_equal, load_graph


BASE = Namespace("https://example.test/model#")
POLICIES = ["strict", "tolerant", "best-effort"]
MODELED = {BASE.cBase, BASE.cOne, BASE.cTwo, BASE.cOutside, BASE.cDeep,
           BASE.cCategorizer, BASE.cOtherCategorizer}


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("powertype", [False, None, True], ids=["ordinary_false", "ordinary_null", "powertype_true"])
def test_categorizers_pun_same_iris_and_materialize_only_applicable_extension(run, source_json, source_path, tmp_path, input_policy, powertype):
    """Rules: DK-HO-01, DK-HO-02, DK-HO-03, DK-HO-04, DK-CLS-02, DK-GEN-02.

    The second categorizer classifies One as well, despite ultimate-sortals'
    disjointness. These assertions inspect explicit class and individual facts;
    no reasoner is used to manufacture powertype membership from subclasses.
    """
    document = source_json("higher_order/categorizers")
    source_element(document, "cCategorizer")["isPowertype"] = powertype
    result = run(path=write_input(tmp_path, document), iri_strategy="id", input_policy=input_policy)
    assert result.outcome == "completed"
    assert_contains(result.ontology, load_graph(source_path("higher_order/categorizers", "expected.ttl")))
    extension = {BASE.cOne, BASE.cTwo}
    if powertype is True:
        extension |= {BASE.cBase, BASE.cOutside, BASE.cDeep}
    assert set(result.ontology.subjects(RDF.type, BASE.cCategorizer)) == extension
    assert set(result.ontology.subjects(RDF.type, BASE.cOtherCategorizer)) == {BASE.cOne}
    assert set(result.ontology.subjects(RDF.type, OWL.NamedIndividual)) == extension
    assert set(result.ontology.subjects(RDF.type, OWL.Class)) == MODELED
    for target in extension:
        assert (target, RDF.type, OWL.Class) in result.ontology
        assert (target, RDF.type, OWL.NamedIndividual) in result.ontology
    # No separate representation resource can carry any of these classifications.
    for categorizer in (BASE.cCategorizer, BASE.cOtherCategorizer):
        assert set(result.ontology.subjects(RDF.type, categorizer)) <= MODELED
    assert ((BASE.cCategorizer, OWL.disjointWith, BASE.cOtherCategorizer) in result.ontology or
            (BASE.cOtherCategorizer, OWL.disjointWith, BASE.cCategorizer) in result.ontology)
    assert not any(d.kind == "semantic_validation" or d.severity in {"WARNING", "ERROR"} for d in result.diagnostics)
    assert not any(d.kind == "singleton_completeness" for d in result.diagnostics)


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("powertype", [False, True], ids=["ordinary", "powertype"])
@pytest.mark.parametrize("size", [1, 2], ids=["singleton", "multi_member"])
def test_repeated_membership_preserves_categorizer_and_powertype_extensions(run, source_json, tmp_path, input_policy, powertype, size):
    """Rules: DK-GEN-12, DK-HO-01, DK-HO-02, DK-HO-03, DK-HO-04, DK-GEN-02, DK-DIAG-05.

    RD-02 at 2b427908a7e29d546486a616a22495ea0424f294. Both sets explicitly
    reference gOne; counting is per set and must preserve both classifications.
    """
    document = source_json("higher_order/categorizers")
    source_element(document, "cCategorizer")["isPowertype"] = powertype
    first = source_element(document, "gsFirst")
    first["generalizations"] = first["generalizations"][:size]
    observations = []
    for repeated in (False, True):
        if repeated:
            first["generalizations"].append(copy.deepcopy(first["generalizations"][0]))
        assert not fixture_issues(document)
        result = run(path=write_input(tmp_path, document, f"categorized_{repeated}.json"), iri_strategy="id", input_policy=input_policy)
        observations.append(result)
        assert result.outcome == "completed"
        assert set(result.ontology.subject_objects(RDFS.subClassOf)) == {
            (BASE.cOne, BASE.cBase), (BASE.cTwo, BASE.cBase),
            (BASE.cOutside, BASE.cBase), (BASE.cDeep, BASE.cOutside)}
        extension = {BASE.cOne, BASE.cTwo} if size == 2 else {BASE.cOne}
        if powertype:
            extension = {BASE.cBase, BASE.cOne, BASE.cTwo, BASE.cOutside, BASE.cDeep}
        assert set(result.ontology.subjects(RDF.type, BASE.cCategorizer)) == extension
        assert set(result.ontology.subjects(RDF.type, BASE.cOtherCategorizer)) == {BASE.cOne}
        assert set(result.ontology.subjects(RDF.type, OWL.NamedIndividual)) == extension
        assert set(result.ontology.subjects(RDF.type, OWL.Class)) == MODELED
        assert not list(result.ontology.objects(BASE.cBase, RDFS.subClassOf))
        for subject in extension:
            assert (subject, RDF.type, OWL.Class) in result.ontology
            assert (subject, RDF.type, OWL.NamedIndividual) in result.ontology
        assert not any(event.kind == "singleton_completeness" or event.severity in {"WARNING", "ERROR"}
                       for event in result.diagnostics)
    assert diagnostic_signatures(observations[0].diagnostics) == diagnostic_signatures(observations[1].diagnostics)


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("powertype", [False, True], ids=["ordinary", "powertype"])
@pytest.mark.parametrize("condition,value", [
    ("absent", None), ("null", None), ("non_array", {"id": "gOne", "type": "Generalization"}),
    ("non_array", "gOne"), ("non_array", 1), ("non_array", False),
], ids=["absent", "null", "object", "string", "number", "boolean"])
def test_unusable_membership_container_omits_only_the_affected_set(
        run, source_json, tmp_path, condition, value, powertype, input_policy):
    """Rules: DK-DIAG-12, DK-DIAG-05, DK-GEN-12, DK-CLS-02, DK-CLS-06, DK-CLS-07, DK-HO-01, DK-HO-02, DK-HO-03, DK-HO-04.

    RD-02 Alternative A, 5f8de1888f307c42b55c40bfac82ea07f60836a7.
    Only gsFirst is unusable. The independently supported subclass edges and
    gsSecond's classification must survive when the input policy permits recovery.
    """
    document = source_json("higher_order/categorizers")
    assert not fixture_issues(document)
    source_element(document, "cCategorizer")["isPowertype"] = powertype
    affected = source_element(document, "gsFirst")
    affected.update(isComplete=True, isDisjoint=True, generalizations=value)
    if condition == "absent":
        del affected["generalizations"]
    # This fixture validator flags non-null non-arrays. Absent and null are
    # deliberately supplied above and covered separately by the converter rule.
    defects = {"malformed_membership"} if condition == "non_array" else set()
    assert fixture_issues(document) == defects

    result = run(path=write_input(tmp_path, document), iri_strategy="id", input_policy=input_policy)
    assert any(event.severity == "ERROR" and "gsFirst" in event.identified_sources
               and f"membership_{condition}" in event.facts for event in result.diagnostics), result.diagnostics
    if input_policy != "best-effort":
        assert result.outcome == "aborted" and result.ontology is None
        assert result.provenance is None
        return

    assert result.outcome == "completed-with-errors"
    graph = result.ontology
    assert isinstance(graph, Graph)
    assert set(graph.subjects(RDF.type, OWL.Class)) == MODELED
    assert set(graph.subject_objects(RDFS.subClassOf)) == {
        (BASE.cOne, BASE.cBase), (BASE.cTwo, BASE.cBase),
        (BASE.cOutside, BASE.cBase), (BASE.cDeep, BASE.cOutside),
    }
    assert not list(graph.subjects(RDF.type, BASE.cCategorizer))
    assert set(graph.subjects(RDF.type, BASE.cOtherCategorizer)) == {BASE.cOne}
    assert set(graph.subjects(RDF.type, OWL.NamedIndividual)) == {BASE.cOne}
    assert not any(BASE.gsFirst in triple for triple in graph)
    for predicate in (OWL.unionOf, OWL.disjointUnionOf, OWL.equivalentClass):
        assert not list(graph.triples((None, predicate, None)))
    for left, right in ((BASE.cOne, BASE.cTwo), (BASE.cTwo, BASE.cOne)):
        assert (left, OWL.disjointWith, right) not in graph
    assert not list(graph.subjects(RDF.type, OWL.AllDisjointClasses))


@pytest.mark.parametrize("input_policy", POLICIES)
def test_duplicate_declaration_is_fatal_with_unusable_membership(run, source_json, tmp_path, input_policy):
    """Rules: DK-DIAG-12, DK-DIAG-05; §3.4 duplicate declaration IDs.

    RD-02 Alternative A, 5f8de1888f307c42b55c40bfac82ea07f60836a7.
    """
    document = source_json("higher_order/categorizers")
    source_element(document, "gsFirst")["generalizations"] = None
    document["model"]["contents"].append(copy.deepcopy(source_element(document, "cOne")))
    assert fixture_issues(document) == {"duplicate_id:cOne"}
    result = run(path=write_input(tmp_path, document), iri_strategy="id", input_policy=input_policy)
    assert result.outcome == "aborted" and result.ontology is None
    assert any(event.severity == "ERROR" and event.code == "DUPLICATE_SOURCE_ID"
               and "cOne" in event.identified_sources for event in result.diagnostics)
    assert all(not ({"membership_absent", "membership_null", "membership_non_array"} & event.facts)
               for event in result.diagnostics)


def _incomplete_categorized_set(document, *, powertype, survivors, failure):
    """Mutate the existing complete export-style fixture with one stated defect."""
    source_element(document, "cCategorizer")["isPowertype"] = powertype
    affected = source_element(document, "gsFirst")
    members = copy.deepcopy(affected["generalizations"][:survivors])
    if survivors == 1:
        # Repetition cannot turn an incomplete set into a complete singleton.
        members.append(copy.deepcopy(members[0]))
    if failure == "unresolved_member":
        defect, locator = {"unresolved_reference:missingMember"}, "gsFirst"
        failed_id = "missingMember"
    elif failure == "failed_member":
        failed = copy.deepcopy(source_element(document, "gOne"))
        failed.update(id="gFailed", specific=None)
        document["model"]["contents"].append(failed)
        defect, locator = {"malformed_reference"}, "gFailed"
        failed_id = "gFailed"
    else:
        raise AssertionError(f"Unlisted governed member failure: {failure}")
    affected.update(isComplete=True, isDisjoint=True,
                    generalizations=members + [{"id": failed_id, "type": "Generalization"}])
    assert fixture_issues(document) == defect
    return locator


@pytest.mark.parametrize("powertype", [False, None, True],
                         ids=["ordinary_false", "ordinary_null", "powertype_true"])
@pytest.mark.parametrize("failure", ["unresolved_member", "failed_member"])
@pytest.mark.parametrize("survivors", [0, 1, 2], ids=["no_survivors", "one_survivor", "two_survivors"])
def test_incomplete_categorized_set_preserves_explicit_classifications(run, source_json, tmp_path, powertype, failure, survivors):
    """Rules: DK-HO-01, DK-HO-02, DK-HO-03, DK-HO-04, DK-GEN-12, DK-CLS-02, DK-CLS-06, DK-CLS-09, DK-DIAG-05, DK-DIAG-14.

    RD-02 recovery, c1d6ab323f0980e835fa018e0f2d05e05a400a07. Expected
    classifications come from surviving explicit members, never subclass closure.
    """
    document = source_json("higher_order/categorizers")
    locator = _incomplete_categorized_set(document, powertype=powertype, survivors=survivors, failure=failure)
    result = run(path=write_input(tmp_path, document), iri_strategy="id", input_policy="best-effort")
    assert result.outcome == "completed-with-errors"
    assert any(event.severity == "ERROR" and locator in event.identified_sources for event in result.diagnostics)
    assert not any(event.kind == "singleton_completeness" for event in result.diagnostics)
    graph = result.ontology
    assert isinstance(graph, Graph)
    explicit = {BASE.cOne, BASE.cTwo} if survivors == 2 else {BASE.cOne} if survivors == 1 else set()
    assert set(graph.subjects(RDF.type, BASE.cCategorizer)) == explicit
    assert set(graph.subjects(RDF.type, BASE.cOtherCategorizer)) == {BASE.cOne}
    assert set(graph.subjects(RDF.type, OWL.NamedIndividual)) == explicit | {BASE.cOne}
    assert set(graph.subjects(RDF.type, OWL.Class)) == MODELED
    assert set(graph.subject_objects(RDFS.subClassOf)) == {
        (BASE.cOne, BASE.cBase), (BASE.cTwo, BASE.cBase),
        (BASE.cOutside, BASE.cBase), (BASE.cDeep, BASE.cOutside)}
    # Incomplete coverage cannot close the general over survivors, including one.
    for predicate in (RDFS.subClassOf, OWL.equivalentClass, OWL.disjointUnionOf):
        assert not list(graph.objects(BASE.cBase, predicate))
    survivor_pairs = {frozenset((left, right)) for left, right in graph.subject_objects(OWL.disjointWith)
                      if left in {BASE.cOne, BASE.cTwo} and right in {BASE.cOne, BASE.cTwo}}
    assert survivor_pairs == ({frozenset((BASE.cOne, BASE.cTwo))} if survivors == 2 else set())


@pytest.mark.parametrize("powertype", [False, True], ids=["ordinary", "powertype"])
@pytest.mark.parametrize("failure", ["unresolved_member", "failed_member"])
@pytest.mark.parametrize("input_policy", ["strict", "tolerant"])
def test_incomplete_categorized_set_aborts_without_recoverable_output(run, source_json, tmp_path, powertype, failure, input_policy):
    """Rules: DK-HO-04, DK-GEN-12, DK-CLS-09, DK-DIAG-04, DK-DIAG-05.

    RD-02 recovery, c1d6ab323f0980e835fa018e0f2d05e05a400a07. Recovery is
    limited to best-effort; the existing member ERROR and abort remain observable.
    """
    document = source_json("higher_order/categorizers")
    locator = _incomplete_categorized_set(document, powertype=powertype, survivors=1, failure=failure)
    result = run(path=write_input(tmp_path, document), iri_strategy="id", input_policy=input_policy)
    assert result.outcome == "aborted"
    assert result.ontology is None
    assert result.provenance is None
    assert any(event.severity == "ERROR" and locator in event.identified_sources for event in result.diagnostics)
    assert not any(event.kind == "singleton_completeness" for event in result.diagnostics)


@pytest.mark.parametrize("powertype", [False, True], ids=["ordinary", "powertype"])
@pytest.mark.parametrize("survivors", [0, 1], ids=["no_survivors", "one_survivor"])
def test_incomplete_categorized_set_keeps_independent_classifications(run, source_json, tmp_path, powertype, survivors):
    """Rules: DK-HO-01, DK-HO-02, DK-HO-03, DK-HO-04, DK-GEN-12, DK-CLS-09, DK-DIAG-05.

    RD-02 recovery, c1d6ab323f0980e835fa018e0f2d05e05a400a07. A separate
    fully resolved set establishes ordinary or powertype facts for the SAME C.
    Omitting expansion for the incomplete set must not erase those facts.
    """
    document = source_json("higher_order/categorizers")
    locator = _incomplete_categorized_set(document, powertype=powertype, survivors=survivors,
                                         failure="unresolved_member")
    independent = copy.deepcopy(source_element(document, "gsSecond"))
    independent.update(id="gsIndependent", name="Independent", categorizer={"id": "cCategorizer", "type": "Class"},
                       generalizations=[{"id": "gOutside", "type": "Generalization"}])
    document["model"]["contents"].append(independent)
    assert fixture_issues(document) == {"unresolved_reference:missingMember"}
    explicit = {BASE.cOne} if survivors else set()
    expected = ({BASE.cBase, BASE.cOne, BASE.cTwo, BASE.cOutside, BASE.cDeep}
                if powertype else explicit | {BASE.cOutside})
    result = run(path=write_input(tmp_path, document), iri_strategy="id", input_policy="best-effort")
    assert result.outcome == "completed-with-errors"
    assert any(event.severity == "ERROR" and locator in event.identified_sources for event in result.diagnostics)
    graph = result.ontology
    assert isinstance(graph, Graph)
    assert set(graph.subjects(RDF.type, BASE.cCategorizer)) == expected
    assert set(graph.subjects(RDF.type, BASE.cOtherCategorizer)) == {BASE.cOne}
    assert set(graph.subjects(RDF.type, OWL.NamedIndividual)) == expected | {BASE.cOne}
    assert set(graph.subjects(RDF.type, OWL.Class)) == MODELED
    assert not list(graph.objects(BASE.cBase, RDFS.subClassOf))
    assert not any(event.kind == "singleton_completeness" for event in result.diagnostics)


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("powertype", [False, True], ids=["ordinary", "powertype"])
def test_restricted_to_order_and_stereotype_do_not_validate_higher_order_assertions(run, source_json, tmp_path, input_policy, powertype):
    """Rules: DK-HO-01, DK-HO-02, DK-HO-03, DK-HO-04, DK-CLS-01, DK-CLS-05, DK-GEN-02.

    Event as categorizer and a lower numeric order are intentionally not checked
    for semantic appropriateness. No malformed structural input is introduced.
    """
    document = source_json("higher_order/categorizers")
    categorizer = source_element(document, "cCategorizer")
    categorizer.update(stereotype="event", isPowertype=powertype, order="0")
    source_element(document, "cBase")["order"] = "12"
    baseline = run(path=write_input(tmp_path, document, "without_nature.json"), iri_strategy="id", input_policy=input_policy)
    for identifier in ("cBase", "cOne", "cTwo", "cOutside", "cDeep", "cCategorizer", "cOtherCategorizer"):
        source_element(document, identifier)["restrictedTo"] = ["situation"]
    result = run(path=write_input(tmp_path, document), iri_strategy="id", input_policy=input_policy)
    assert baseline.outcome == result.outcome == "completed"
    extension = {BASE.cOne, BASE.cTwo} | ({BASE.cBase, BASE.cOutside, BASE.cDeep} if powertype else set())
    assert set(result.ontology.subjects(RDF.type, BASE.cCategorizer)) == extension
    assert set(result.ontology.subjects(RDF.type, BASE.cOtherCategorizer)) == {BASE.cOne}
    assert (BASE.cCategorizer, RDFS.comment, Literal("OntoUML classifier order: 0.", lang="en")) in result.ontology
    assert (BASE.cBase, RDFS.comment, Literal("OntoUML classifier order: 12.", lang="en")) in result.ontology
    assert_selected_equal(result.ontology, baseline.ontology,
                          {RDF.type, RDFS.subClassOf, RDFS.domain, RDFS.range,
                           OWL.equivalentClass, OWL.disjointUnionOf},
                          {OWL.disjointWith}, subjects=MODELED,
                          type_objects={OWL.Class, OWL.NamedIndividual} | MODELED)
    for observation in (baseline, result):
        assert not observation.restricted_to_output
        assert all((c.subject, RDFS.comment, c.literal) in observation.ontology for c in observation.comments)
    assert {(c.subject, c.field, c.value) for c in result.comments} == {(c.subject, c.field, c.value) for c in baseline.comments}
    assert diagnostic_signatures(result.diagnostics) == diagnostic_signatures(baseline.diagnostics)
    assert not any(d.kind in {"unknown_information", "restricted_to", "semantic_validation"} or d.severity == "ERROR" for d in result.diagnostics)


@pytest.mark.parametrize("iri_strategy", ["name", "id"])
def test_punning_identity_is_the_same_under_both_iri_strategies(run, iri_strategy):
    """Rules: DK-HO-01, DK-HO-02, DK-IRI-02, DK-IRI-09."""
    result = run("higher_order/categorizers", iri_strategy=iri_strategy)
    assert result.outcome == "completed"
    one = BASE.cOne if iri_strategy == "id" else BASE.One
    categorizer = BASE.cCategorizer if iri_strategy == "id" else BASE.Categorizer
    other = BASE.cOtherCategorizer if iri_strategy == "id" else BASE.OtherCategorizer
    assert {OWL.Class, OWL.NamedIndividual, categorizer, other} <= set(result.ontology.objects(one, RDF.type))
    if iri_strategy == "name":
        assert set(result.ontology.subjects(DCTERMS.identifier, Literal("cOne"))) == {one}
    else:
        assert not list(result.ontology.subjects(DCTERMS.identifier, Literal("cOne")))
    assert set(result.ontology.subjects(RDFS.label, Literal("One"))) == {one}


INSTANTIATION_SENTINELS=['DISCARDED_ASSOCIATION_SENTINEL','DISCARDED_SOURCE_ROLE_SENTINEL',
                         'DISCARDED_TARGET_ROLE_SENTINEL','DISCARDED_DESCRIPTION_SENTINEL','37..41','43..47']


def _instantiation_warning_and_nonrepresentation(result,categories):
    warnings=[d for d in result.diagnostics if d.kind=='discarded_instantiation_data']
    assert len(warnings)==1
    warning=warnings[0]
    assert warning.severity=='WARNING'
    assert 'rInstantiation' in warning.source_ids and 'Relation' in warning.source_types
    assert {'association_data_not_materialized',*categories}<=warning.facts
    assert warning.raw is not None  # retain real payload evidence for the audit
    assert result.discarded_instantiation_output==(), "Read actual output/payloads; an unbound reader is not evidence of non-leakage"
    for diagnostic in result.diagnostics:
        text=diagnostic.message+repr(diagnostic.raw)+repr(diagnostic.facts)+repr(diagnostic.generated_iris)
        assert not any(value in text for value in INSTANTIATION_SENTINELS)
        assert not {str(BASE.rInstantiation),str(BASE.sInstantiation),str(BASE.tInstantiation)} & set(diagnostic.generated_iris)
    graphs=[result.ontology]+([result.provenance] if result.provenance is not None else [])
    for graph in graphs:
        for triple in graph:
            assert not any(value in str(term) for term in triple for value in INSTANTIATION_SENTINELS)
            assert not any(term in {BASE.rInstantiation,BASE.sInstantiation,BASE.tInstantiation} for term in triple)
    assert not any(d.kind=='semantic_validation' or d.severity=='ERROR' for d in result.diagnostics)


@pytest.mark.parametrize('strategy',['name','id'])
@pytest.mark.parametrize('provenance',['none','embedded','sidecar'])
@pytest.mark.parametrize('input_policy',POLICIES)
def test_instantiation_discard_warning_is_consolidated_and_values_do_not_leak_into_any_output(run,source_json,tmp_path,strategy,provenance,input_policy):
    """Rules: DK-INS-01, DK-INS-02, DK-INS-03, DK-HO-01, DK-HO-02, DK-DIAG-05, DK-GEN-05, DK-LBL-02, DK-GEN-10."""
    document=source_json('shared/instantiation')
    assert not fixture_issues(document)
    result=run(path=write_input(tmp_path,document),iri_strategy=strategy,provenance=provenance,input_policy=input_policy)
    assert result.outcome=='completed'
    if provenance=='sidecar':assert isinstance(result.provenance,Graph) and len(result.provenance)>0
    _instantiation_warning_and_nonrepresentation(result,{'discarded_identifier','discarded_association_name','discarded_role_names','discarded_multiplicities','discarded_characteristics'})
    specific=BASE.cSpecific if strategy=='id' else BASE.Specific
    categorizer=BASE.cCategorizer if strategy=='id' else BASE.Categorizer
    other=BASE.cOtherCategorizer if strategy=='id' else BASE.OtherCategorizer
    outside=BASE.cOutside if strategy=='id' else BASE.Outside
    assert {OWL.Class,OWL.NamedIndividual,categorizer,other}<=set(result.ontology.objects(specific,RDF.type))
    assert (outside,RDF.type,categorizer) not in result.ontology
    assert not any(d.kind=='derived_status' for d in result.diagnostics)
    # No other construct in this source has multiplicities or an OWL property.
    counts={OWL.minCardinality,OWL.maxCardinality,OWL.cardinality,OWL.minQualifiedCardinality,OWL.maxQualifiedCardinality,OWL.qualifiedCardinality}
    assert not any(p in counts for _,p,_ in result.ontology)


@pytest.mark.parametrize('category',['identifier_only','association_name','role_names','multiplicities','characteristics','description'])
def test_each_discarded_instantiation_category_is_reported_without_copying_its_values(run,source_json,tmp_path,category):
    """Rules: DK-INS-01, DK-INS-02, DK-DIAG-05."""
    document=source_json('shared/instantiation');association=source_element(document,'rInstantiation');original=copy.deepcopy(association)
    association.update(name=None,description=None)
    for key in ('isAbstract','isDerived'):association.pop(key,None)
    for end in association['properties']:
        end.update(name=None,description=None,cardinality=None)
        for key in ('isReadOnly','isOrdered','isDerived','aggregationKind'):end.pop(key,None)
    expected={'discarded_identifier'}
    if category=='association_name':association['name']=original['name'];expected.add('discarded_association_name')
    elif category=='role_names':
        for end,old in zip(association['properties'],original['properties']):end['name']=old['name']
        expected.add('discarded_role_names')
    elif category=='multiplicities':
        for end,old in zip(association['properties'],original['properties']):end['cardinality']=old['cardinality']
        expected.add('discarded_multiplicities')
    elif category=='characteristics':association['isAbstract']=True;expected.add('discarded_characteristics')
    elif category=='description':association['description']=original['description'];expected.add('discarded_characteristics')
    assert not fixture_issues(document)
    result=run(path=write_input(tmp_path,document),iri_strategy='id',input_policy='strict')
    assert result.outcome=='completed'
    _instantiation_warning_and_nonrepresentation(result,expected)


@pytest.mark.parametrize('powertype',[False,True],ids=['ordinary_categorizer','powertype'])
@pytest.mark.parametrize('input_policy',POLICIES)
def test_instantiation_declaration_does_not_invent_membership_or_reconcile_categorizers(run,source_json,tmp_path,powertype,input_policy):
    """Rules: DK-INS-01, DK-INS-03, DK-HO-01, DK-HO-02, DK-HO-03, DK-HO-04, DK-GEN-02, DK-DIAG-02."""
    document=source_json('shared/instantiation');source_element(document,'cCategorizer')['isPowertype']=powertype
    # These ultimate sortals are disjoint, yet the explicit categorizers
    # classify Specific under both. No consistency check may suppress either.
    source_element(document,'cCategorizer')['stereotype']='mode'
    source_element(document,'cOtherCategorizer')['stereotype']='quality'
    result=run(path=write_input(tmp_path,document),iri_strategy='id',input_policy=input_policy)
    assert result.outcome=='completed'
    expected={BASE.cSpecific}|({BASE.cBase} if powertype else set())
    assert set(result.ontology.subjects(RDF.type,BASE.cCategorizer))==expected
    assert set(result.ontology.subjects(RDF.type,BASE.cOtherCategorizer))=={BASE.cSpecific}
    modeled_class_iris={BASE[item['id']] for item in document['model']['contents'] if item['type']=='Class'}
    assert set(result.ontology.subjects(RDF.type,OWL.NamedIndividual)) & modeled_class_iris==expected
    assert ((BASE.cCategorizer,OWL.disjointWith,BASE.cOtherCategorizer) in result.ontology or
            (BASE.cOtherCategorizer,OWL.disjointWith,BASE.cCategorizer) in result.ontology)
    for instance in expected:
        assert (instance,RDF.type,OWL.Class) in result.ontology
    assert (BASE.cOutside,RDF.type,BASE.cCategorizer) not in result.ontology
    assert not any(d.kind=='semantic_validation' or d.severity=='ERROR' for d in result.diagnostics)
