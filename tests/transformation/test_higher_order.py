"""Punned class/individual identity, categorizers, and powertype extension."""

import copy
import json
from types import SimpleNamespace

import pytest
from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, XSD

from tests.support.data import source_element, write_input, fixture_issues
from tests.support.invocation import _observed_diagnostics, diagnostic_signatures, unusable_categorizer_diagnostic
from tests.support.rdf import assert_contains, assert_selected_equal, load_graph, one_object, rdf_list


BASE = Namespace("https://example.test/model#")
POLICIES = ["strict", "tolerant", "best-effort"]
MODELED = {BASE.cBase, BASE.cOne, BASE.cTwo, BASE.cOutside, BASE.cDeep,
           BASE.cCategorizer, BASE.cOtherCategorizer}
STABLE_DIAGNOSTIC_CODES = frozenset({
    "PLACEHOLDER_BASE", "UNPROCESSABLE_DOCUMENT", "DUPLICATE_SOURCE_ID", "UNKNOWN_INFORMATION",
    "REQUIRED_PROVENANCE", "INTERNAL_TRANSFORMATION_FAILURE", "ONTOLOGY_DELIVERY", "SIDECAR_DELIVERY",
})


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("powertype", [False, None, True], ids=["ordinary_false", "ordinary_null", "powertype_true"])
def test_categorizers_pun_same_iris_and_materialize_only_applicable_extension(run, source_json, source_path, tmp_path, input_policy, powertype):
    """Rules: DK-HO-01, DK-HO-02, DK-HO-03, DK-HO-04, DK-CLS-02, DK-GEN-02.

    The second categorizer classifies One as well, despite ultimate-sortals'
    disjointness. These assertions inspect explicit class and individual facts;
    no reasoner is used to manufacture powertype membership from subclasses.
    """
    document = source_json("shared/categorizers")
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
    document = source_json("shared/categorizers")
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
    """Rules: DK-DIAG-12, DK-DIAG-05, DK-GEN-12, DK-CLS-02, DK-CLS-03, DK-CLS-06, DK-CLS-07, DK-HO-01, DK-HO-02, DK-HO-03, DK-HO-04.

    RD-02 Alternative A, 5f8de1888f307c42b55c40bfac82ea07f60836a7.
    Only gsFirst is unusable. The independently supported subclass edges and
    gsSecond's classification must survive when the input policy permits recovery.
    """
    document = source_json("shared/categorizers")
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
    # The only independently required pair relates the two «type» classifiers.
    assert {frozenset(pair) for pair in graph.subject_objects(OWL.disjointWith)} == {
        frozenset((BASE.cCategorizer, BASE.cOtherCategorizer)),
    }
    assert not list(graph.subjects(RDF.type, OWL.AllDisjointClasses))


@pytest.mark.parametrize("input_policy", POLICIES)
def test_duplicate_declaration_is_fatal_with_unusable_membership(run, source_json, tmp_path, input_policy):
    """Rules: DK-DIAG-12, DK-DIAG-05; §3.4 duplicate declaration IDs.

    RD-02 Alternative A, 5f8de1888f307c42b55c40bfac82ea07f60836a7.
    """
    document = source_json("shared/categorizers")
    source_element(document, "gsFirst")["generalizations"] = None
    document["model"]["contents"].append(copy.deepcopy(source_element(document, "cOne")))
    assert fixture_issues(document) == {"duplicate_id:cOne"}
    result = run(path=write_input(tmp_path, document), iri_strategy="id", input_policy=input_policy)
    assert result.outcome == "aborted" and result.ontology is None
    assert any(event.severity == "ERROR" and event.code == "DUPLICATE_SOURCE_ID"
               and "cOne" in event.identified_sources for event in result.diagnostics)
    assert all(not ({"membership_absent", "membership_null", "membership_non_array"} & event.facts)
               for event in result.diagnostics)


def test_membership_condition_reader_requires_affirmative_unambiguous_claim():
    """Rules: DK-DIAG-12. Harness only: classify native reasons independently of the code."""
    accepted = {
        "Missing 'generalizations' field.": "membership_absent",
        "Generalization set 'gsFirst' has no `generalizations` field.": "membership_absent",
        "The membership container is not supplied.": "membership_absent",
        "The `generalizations` field is explicitly null.": "membership_null",
        "Generalizations is null, not missing.": "membership_null",
        "GeneralizationSet 'gsFirst': generalizations field: expected an array, got null.": "membership_null",
        "Generalizations is not null; it is an object.": "membership_non_array",
        "The generalizations field is a boolean.": "membership_non_array",
        "Generalizations must be a JSON array; received an integer.": "membership_non_array",
        "The membership container is not a JSON array.": "membership_non_array",
        "Element gsFirst has a non-array 'generalizations' value.": "membership_non_array",
    }
    rejected = (
        "Generalizations is null or an object.",
        "Generalizations is missing or not an array.",
        "It is not true that generalizations is null.",
        "Generalizations is null, or it is a string.",
        "Generalizations is not null.",
        "It is not true that: generalizations is absent.",
        "Generalizations is expected to be an array.",
        "Possibly generalizations is absent.",
        "Generalizations is null?",
        "Generalizations is missing; generalizations is null.",
        "Review example: 'Generalizations is null'.",
    )
    # A real locator and ERROR severity are insufficient without affirmative
    # evidence in the reason. The unrelated effect cannot supply that evidence.
    source = SimpleNamespace(identifier="gsFirst", element_type="GeneralizationSet")
    for message, expected in (accepted | dict.fromkeys(rejected)).items():
        native = SimpleNamespace(severity="ERROR", code="PROVISIONAL_TEST_CODE",
                                 message=message, effect="Generalizations is null.",
                                 sources=(source,), generated_iri=None)
        observed, = _observed_diagnostics((native,), retain_unclassified=True)
        assert observed.identified_sources == ("gsFirst",)
        assert observed.facts == ({expected} if expected else set()), message


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
    document = source_json("shared/categorizers")
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
    document = source_json("shared/categorizers")
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
    document = source_json("shared/categorizers")
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


def _apply_unusable_categorizer(document, defect):
    """Apply one explicit unusable-categorizer condition to gsFirst."""
    affected = source_element(document, "gsFirst")
    affected.update(isComplete=True, isDisjoint=True)
    expected_issues = frozenset()
    if defect == "malformed_string":
        affected["categorizer"] = "cCategorizer"
        expected_issues = frozenset({"malformed_reference"})
    elif defect == "malformed_number":
        affected["categorizer"] = 1
        expected_issues = frozenset({"malformed_reference"})
    elif defect == "malformed_boolean":
        affected["categorizer"] = False
        expected_issues = frozenset({"malformed_reference"})
    elif defect == "malformed_array":
        affected["categorizer"] = [{"id": "cCategorizer", "type": "Class"}]
        expected_issues = frozenset({"malformed_reference"})
    elif defect == "malformed_missing_id":
        affected["categorizer"] = {"type": "Class"}
        expected_issues = frozenset({"malformed_reference"})
    elif defect == "malformed_missing_type":
        affected["categorizer"] = {"id": "cCategorizer"}
        expected_issues = frozenset({"malformed_reference"})
    elif defect == "malformed_empty_id":
        affected["categorizer"] = {"id": "", "type": "Class"}
        expected_issues = frozenset({"invalid_reference_id"})
    elif defect == "malformed_non_utf8_id":
        affected["categorizer"] = {"id": "\ud800", "type": "Class"}
        expected_issues = frozenset({"invalid_reference_id"})
    elif defect == "dangling_id":
        affected["categorizer"] = {"id": "missingCategorizer", "type": "Class"}
        expected_issues = frozenset({"unresolved_reference:missingCategorizer"})
    elif defect == "type_mismatch":
        source_element(document, "cCategorizer")["isPowertype"] = True
        affected["categorizer"] = {"id": "cCategorizer", "type": "Relation"}
        expected_issues = frozenset({"reference_type_mismatch:cCategorizer"})
    elif defect == "non_class_generalization":
        affected["categorizer"] = {"id": "gOne", "type": "Generalization"}
    elif defect == "non_class_property":
        source_element(document, "cBase")["properties"] = [{
            "id": "aTag", "name": "tag", "description": None, "type": "Property",
            "propertyAssignments": None, "stereotype": None, "isDerived": False,
            "isReadOnly": False, "isOrdered": False, "cardinality": None,
            "propertyType": None, "subsettedProperties": None,
            "redefinedProperties": None, "aggregationKind": None,
        }]
        affected["categorizer"] = {"id": "aTag", "type": "Property"}
    elif defect == "non_class_relation":
        document["model"]["contents"].append({
            "id": "rLink", "name": "links", "description": None, "type": "Relation",
            "propertyAssignments": None, "stereotype": "material", "isAbstract": False,
            "isDerived": False,
            "properties": [
                {
                    "id": "eLinkSrc", "name": "linkSource", "description": None, "type": "Property",
                    "propertyAssignments": None, "stereotype": None, "isDerived": False,
                    "isReadOnly": False, "isOrdered": False, "cardinality": None,
                    "propertyType": {"id": "cBase", "type": "Class"},
                    "subsettedProperties": None, "redefinedProperties": None, "aggregationKind": "NONE",
                },
                {
                    "id": "eLinkTgt", "name": "linkTarget", "description": None, "type": "Property",
                    "propertyAssignments": None, "stereotype": None, "isDerived": False,
                    "isReadOnly": False, "isOrdered": False, "cardinality": None,
                    "propertyType": {"id": "cOutside", "type": "Class"},
                    "subsettedProperties": None, "redefinedProperties": None, "aggregationKind": "NONE",
                },
            ],
        })
        affected["categorizer"] = {"id": "rLink", "type": "Relation"}
    elif defect == "non_class_package":
        affected["categorizer"] = {"id": "higherProject_root", "type": "Package"}
        expected_issues = frozenset({"unresolved_reference:higherProject_root"})
    elif defect == "primitive_datatype":
        datatype = copy.deepcopy(source_element(document, "cBase"))
        datatype.update(id="dString", name="string", stereotype="datatype", isPowertype=True)
        document["model"]["contents"].append(datatype)
        affected["categorizer"] = {"id": "dString", "type": "Class"}
    elif defect == "void_datatype":
        void_cls = copy.deepcopy(source_element(document, "cBase"))
        void_cls.update(id="dVoid", name="void", stereotype="datatype", isPowertype=True)
        document["model"]["contents"].append(void_cls)
        affected["categorizer"] = {"id": "dVoid", "type": "Class"}
    else:
        raise AssertionError(f"Unlisted unusable-categorizer defect: {defect}")
    return expected_issues


def _assert_unusable_categorizer_error(diagnostics):
    assert any(
        event.severity == "ERROR"
        and "gsFirst" in event.identified_sources
        and "unusable_categorizer" in event.facts
        and event.code
        and event.code not in STABLE_DIAGNOSTIC_CODES
        for event in diagnostics
    ), diagnostics


def _assert_complete_multi_member_graph_without_gsfirst_categorizer(graph, *, modeled, disjoint_pairs):
    assert isinstance(graph, Graph)
    assert {s for s in graph.subjects(RDF.type, OWL.Class) if isinstance(s, URIRef)} == modeled
    named_subclasses = {(s, o) for s, o in graph.subject_objects(RDFS.subClassOf) if not isinstance(o, BNode)}
    assert named_subclasses == {
        (BASE.cOne, BASE.cBase), (BASE.cTwo, BASE.cBase),
        (BASE.cOutside, BASE.cBase), (BASE.cDeep, BASE.cOutside),
    }
    bnode_subclasses = [(s, o) for s, o in graph.subject_objects(RDFS.subClassOf) if isinstance(o, BNode)]
    assert len(bnode_subclasses) == 1 and bnode_subclasses[0][0] == BASE.cBase
    union_node = bnode_subclasses[0][1]
    assert {s for s in graph.subjects(RDF.type, OWL.Class) if isinstance(s, BNode)} == {union_node}
    union_members = rdf_list(graph, one_object(graph, union_node, OWL.unionOf))
    assert len(union_members) == 2 and set(union_members) == {BASE.cOne, BASE.cTwo}
    for predicate in (OWL.disjointUnionOf, OWL.equivalentClass):
        assert not list(graph.triples((None, predicate, None)))
    assert not list(graph.subjects(RDF.type, OWL.AllDisjointClasses))
    assert {frozenset(pair) for pair in graph.subject_objects(OWL.disjointWith)} == disjoint_pairs
    assert set(graph.subjects(RDF.type, OWL.NamedIndividual)) == {BASE.cOne}
    for cls in modeled:
        expected_types = ({OWL.Class, OWL.NamedIndividual, BASE.cOtherCategorizer}
                          if cls == BASE.cOne else {OWL.Class})
        assert set(graph.objects(cls, RDF.type)) == expected_types
    assert not any(BASE.gsFirst in triple for triple in graph)


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("categorizer_state", ["absent", "null"])
def test_absent_or_null_categorizer_remains_uncategorized_without_error(
        run, source_json, tmp_path, categorizer_state, input_policy):
    """Rules: DK-HO-01, DK-HO-02, DK-HO-03, DK-HO-04, DK-CLS-02, DK-CLS-03, DK-CLS-06, DK-CLS-07, DK-DIAG-05.

    RD-02 Alternative A, 0f290d3afb830418297af13c30c4c65be1e13ca8. Absent and
    explicit null categorizers remain uncategorized sets with no error.
    """
    document = source_json("shared/categorizers")
    affected = source_element(document, "gsFirst")
    affected.update(isComplete=True, isDisjoint=True)
    if categorizer_state == "absent":
        del affected["categorizer"]
    else:
        affected["categorizer"] = None
    assert fixture_issues(document) == frozenset()

    result = run(path=write_input(tmp_path, document), iri_strategy="id", input_policy=input_policy)
    assert result.outcome == "completed"
    assert not any(event.severity in {"WARNING", "ERROR"} or "unusable_categorizer" in event.facts
                   or event.kind == "singleton_completeness" for event in result.diagnostics)
    _assert_complete_multi_member_graph_without_gsfirst_categorizer(
        result.ontology, modeled=MODELED,
        disjoint_pairs={frozenset((BASE.cOne, BASE.cTwo)), frozenset((BASE.cCategorizer, BASE.cOtherCategorizer))},
    )


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("defect", [
    "malformed_string", "malformed_number", "malformed_boolean", "malformed_array",
    "malformed_missing_id", "malformed_missing_type", "malformed_empty_id", "malformed_non_utf8_id",
    "dangling_id", "type_mismatch",
    "non_class_generalization", "non_class_property", "non_class_relation", "non_class_package",
    "primitive_datatype", "void_datatype",
])
def test_unusable_categorizer_aborts_or_preserves_complete_membership_constraints(
        run, source_json, tmp_path, defect, input_policy):
    """Rules: DK-HO-01, DK-HO-02, DK-HO-03, DK-HO-04, DK-CLS-01, DK-CLS-02, DK-CLS-03, DK-CLS-06, DK-CLS-07, DK-ATT-01, DK-DAT-01, DK-REL-01, DK-DIAG-05.

    RD-02 Alternative A, 0f290d3afb830418297af13c30c4c65be1e13ca8. Exercises
    malformed references, unresolved references, non-Class declarations, and
    Classes without a generated local owl:Class without inventing a substitute.
    """
    document = source_json("shared/categorizers")
    expected_issues = _apply_unusable_categorizer(document, defect)
    assert fixture_issues(document) == expected_issues
    path = write_input(tmp_path, document, ensure_ascii=(defect == "malformed_non_utf8_id"))
    if defect == "malformed_non_utf8_id":
        assert json.loads(path.read_bytes()) == document

    result = run(path=path, iri_strategy="id", input_policy=input_policy)
    _assert_unusable_categorizer_error(result.diagnostics)
    assert not any(event.kind == "singleton_completeness" for event in result.diagnostics)
    if input_policy != "best-effort":
        assert result.outcome == "aborted" and result.ontology is None and result.provenance is None
        return

    assert result.outcome == "completed-with-errors"
    graph = result.ontology
    _assert_complete_multi_member_graph_without_gsfirst_categorizer(
        graph, modeled=MODELED,
        disjoint_pairs={frozenset((BASE.cOne, BASE.cTwo)), frozenset((BASE.cCategorizer, BASE.cOtherCategorizer))},
    )
    if defect == "dangling_id":
        assert not any(BASE.missingCategorizer in triple for triple in graph)
    elif defect == "non_class_generalization":
        assert not any(BASE.gOne in triple for triple in graph)
    elif defect == "non_class_property":
        assert (BASE.aTag, RDF.type, OWL.DatatypeProperty) in graph
        assert (BASE.aTag, RDFS.domain, BASE.cBase) in graph
        assert not list(graph.subjects(RDF.type, BASE.aTag))
    elif defect == "non_class_relation":
        assert (BASE.eLinkTgt, RDF.type, OWL.ObjectProperty) in graph
        assert (BASE.eLinkSrc, RDF.type, OWL.ObjectProperty) in graph
        assert not any(BASE.rLink in triple for triple in graph)
        assert not list(graph.subjects(RDF.type, BASE.eLinkTgt))
        assert not list(graph.subjects(RDF.type, BASE.eLinkSrc))
    elif defect == "non_class_package":
        assert not any(BASE.higherProject_root in triple for triple in graph)
    elif defect == "primitive_datatype":
        assert not any(term in {BASE.dString, XSD.string} for triple in graph for term in triple)
    elif defect == "void_datatype":
        assert not any(BASE.dVoid in triple or "void" in str(term).casefold()
                       for triple in graph for term in triple)


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("powertype", [False, True], ids=["ordinary", "powertype"])
def test_categorizer_omitted_earlier_under_best_effort_preserves_set_constraints(
        run, source_json, tmp_path, powertype, input_policy):
    """Rules: DK-HO-01, DK-HO-02, DK-HO-03, DK-HO-04, DK-CLS-02, DK-CLS-03, DK-CLS-06, DK-CLS-07, DK-IRI-04, DK-DIAG-05; §3.4.

    RD-02 Alternative A, 0f290d3afb830418297af13c30c4c65be1e13ca8. A target
    class omitted earlier under best-effort makes the categorizer unresolved.
    """
    document = source_json("shared/categorizers")
    source_element(document, "cCategorizer").update(id=None, isPowertype=powertype)
    source_element(document, "gsFirst").update(isComplete=True, isDisjoint=True)
    assert fixture_issues(document) == {"invalid_id", "unresolved_reference:cCategorizer"}

    result = run(path=write_input(tmp_path, document), iri_strategy="id", input_policy=input_policy)
    assert any(event.severity == "ERROR" and event.kind == "invalid_id" for event in result.diagnostics)
    if input_policy != "best-effort":
        assert result.outcome == "aborted" and result.ontology is None and result.provenance is None
        return

    assert result.outcome == "completed-with-errors"
    _assert_unusable_categorizer_error(result.diagnostics)
    assert not any(event.kind == "singleton_completeness" for event in result.diagnostics)
    graph = result.ontology
    _assert_complete_multi_member_graph_without_gsfirst_categorizer(
        graph, modeled=MODELED - {BASE.cCategorizer},
        disjoint_pairs={frozenset((BASE.cOne, BASE.cTwo))},
    )
    assert not any(BASE.cCategorizer in triple for triple in graph)


@pytest.mark.parametrize("repeated", [False, True], ids=["single_ref", "repeated_ref"])
@pytest.mark.parametrize("defect", ["dangling_id", "primitive_datatype", "non_class_generalization", "malformed_string"])
def test_unusable_categorizer_preserves_singleton_completeness_and_info(
        run, source_json, tmp_path, defect, repeated):
    """Rules: DK-HO-01, DK-HO-02, DK-HO-03, DK-HO-04, DK-GEN-12, DK-CLS-02, DK-CLS-03, DK-CLS-06, DK-CLS-08, DK-DIAG-05, DK-DIAG-14.

    RD-02 Alternative A, 0f290d3afb830418297af13c30c4c65be1e13ca8. An unusable
    categorizer alone must not suppress DK-CLS-08 singleton completeness or its
    DK-DIAG-14 INFO diagnostic when membership is complete.
    """
    document = source_json("shared/categorizers")
    expected_issues = _apply_unusable_categorizer(document, defect)
    affected = source_element(document, "gsFirst")
    affected["generalizations"] = [{"id": "gOne", "type": "Generalization"}] * (2 if repeated else 1)
    assert fixture_issues(document) == expected_issues

    result = run(path=write_input(tmp_path, document), iri_strategy="id", input_policy="best-effort")
    assert result.outcome == "completed-with-errors"
    _assert_unusable_categorizer_error(result.diagnostics)
    singleton = [event for event in result.diagnostics if event.kind == "singleton_completeness"]
    assert singleton and all(event.severity == "INFO" for event in singleton)
    assert any({"gsFirst", "cBase", "cOne"} <= set(event.identified_sources)
               and {"extensional_equivalence", "distinct_identifiers"} <= event.facts
               for event in singleton)
    graph = result.ontology
    assert isinstance(graph, Graph)
    assert {s for s in graph.subjects(RDF.type, OWL.Class) if isinstance(s, URIRef)} == MODELED
    assert not any(isinstance(s, BNode) for s in graph.subjects(RDF.type, OWL.Class))
    assert set(graph.subject_objects(RDFS.subClassOf)) == {
        (BASE.cOne, BASE.cBase), (BASE.cBase, BASE.cOne),
        (BASE.cTwo, BASE.cBase), (BASE.cOutside, BASE.cBase), (BASE.cDeep, BASE.cOutside),
    }
    for predicate in (OWL.unionOf, OWL.disjointUnionOf, OWL.equivalentClass):
        assert not list(graph.triples((None, predicate, None)))
    assert not list(graph.subjects(RDF.type, OWL.AllDisjointClasses))
    assert {frozenset(pair) for pair in graph.subject_objects(OWL.disjointWith)} == {
        frozenset((BASE.cCategorizer, BASE.cOtherCategorizer)),
    }
    assert set(graph.subjects(RDF.type, OWL.NamedIndividual)) == {BASE.cOne}
    for cls in MODELED:
        expected_types = ({OWL.Class, OWL.NamedIndividual, BASE.cOtherCategorizer}
                          if cls == BASE.cOne else {OWL.Class})
        assert set(graph.objects(cls, RDF.type)) == expected_types
    assert not any(term in {BASE.gsFirst, BASE.dString, XSD.string, BASE.missingCategorizer, BASE.gOne}
                   for triple in graph for term in triple)


@pytest.mark.parametrize("defect", ["dangling_id", "primitive_datatype"])
@pytest.mark.parametrize("failure", ["unresolved_member", "failed_member"])
@pytest.mark.parametrize("survivors", [0, 1, 2], ids=["no_survivors", "one_survivor", "two_survivors"])
def test_unusable_categorizer_with_failed_member_best_effort_applies_both_rules(
        run, source_json, tmp_path, defect, failure, survivors):
    """Rules: DK-HO-01, DK-HO-02, DK-HO-03, DK-HO-04, DK-GEN-12, DK-CLS-02, DK-CLS-03, DK-CLS-06, DK-CLS-09, DK-DIAG-05, DK-DIAG-14.

    RD-02 Alternative A, 0f290d3afb830418297af13c30c4c65be1e13ca8. Combined
    member failure and unusable categorizer omit coverage and all categorizer
    or powertype assertions from gsFirst while keeping surviving disjointness.
    """
    document = source_json("shared/categorizers")
    member_locator = _incomplete_categorized_set(document, powertype=False, survivors=survivors, failure=failure)
    member_issues = set(fixture_issues(document))
    categorizer_issues = set(_apply_unusable_categorizer(document, defect))
    assert fixture_issues(document) == member_issues | categorizer_issues

    result = run(path=write_input(tmp_path, document), iri_strategy="id", input_policy="best-effort")
    assert result.outcome == "completed-with-errors"
    assert any(event.severity == "ERROR" and member_locator in event.identified_sources
               and "unusable_categorizer" not in event.facts for event in result.diagnostics), result.diagnostics
    _assert_unusable_categorizer_error(result.diagnostics)
    assert not any(event.kind == "singleton_completeness" for event in result.diagnostics)
    graph = result.ontology
    assert isinstance(graph, Graph)
    assert {s for s in graph.subjects(RDF.type, OWL.Class) if isinstance(s, URIRef)} == MODELED
    assert not any(isinstance(s, BNode) for s in graph.subjects(RDF.type, OWL.Class))
    assert set(graph.subject_objects(RDFS.subClassOf)) == {
        (BASE.cOne, BASE.cBase), (BASE.cTwo, BASE.cBase),
        (BASE.cOutside, BASE.cBase), (BASE.cDeep, BASE.cOutside),
    }
    for predicate in (OWL.unionOf, OWL.disjointUnionOf, OWL.equivalentClass):
        assert not list(graph.triples((None, predicate, None)))
    assert not list(graph.subjects(RDF.type, OWL.AllDisjointClasses))
    expected_disjoint = {frozenset((BASE.cCategorizer, BASE.cOtherCategorizer))}
    if survivors == 2:
        expected_disjoint.add(frozenset((BASE.cOne, BASE.cTwo)))
    assert {frozenset(pair) for pair in graph.subject_objects(OWL.disjointWith)} == expected_disjoint
    assert set(graph.subjects(RDF.type, OWL.NamedIndividual)) == {BASE.cOne}
    for cls in MODELED:
        expected_types = ({OWL.Class, OWL.NamedIndividual, BASE.cOtherCategorizer}
                          if cls == BASE.cOne else {OWL.Class})
        assert set(graph.objects(cls, RDF.type)) == expected_types
    assert not any(term in {BASE.gsFirst, BASE.gFailed, BASE.dString, XSD.string, BASE.missingCategorizer}
                   for triple in graph for term in triple)


@pytest.mark.parametrize("defect", ["dangling_id", "primitive_datatype"])
@pytest.mark.parametrize("failure", ["unresolved_member", "failed_member"])
@pytest.mark.parametrize("input_policy", ["strict", "tolerant"])
def test_unusable_categorizer_with_failed_member_aborts_under_strict_and_tolerant(
        run, source_json, tmp_path, defect, failure, input_policy):
    """Rules: DK-HO-04, DK-CLS-09, DK-DIAG-04, DK-DIAG-05.

    RD-02 Alternative A, 0f290d3afb830418297af13c30c4c65be1e13ca8. Either the
    member failure or unusable categorizer may abort first under strict/tolerant.
    """
    document = source_json("shared/categorizers")
    member_locator = _incomplete_categorized_set(document, powertype=False, survivors=1, failure=failure)
    member_issues = set(fixture_issues(document))
    categorizer_issues = set(_apply_unusable_categorizer(document, defect))
    assert fixture_issues(document) == member_issues | categorizer_issues

    result = run(path=write_input(tmp_path, document), iri_strategy="id", input_policy=input_policy)
    assert result.outcome == "aborted" and result.ontology is None and result.provenance is None
    assert any(
        event.severity == "ERROR"
        and event.code != "INTERNAL_TRANSFORMATION_FAILURE"
        and (member_locator in event.identified_sources
             or ("gsFirst" in event.identified_sources and "unusable_categorizer" in event.facts))
        for event in result.diagnostics
    ), result.diagnostics
    assert not any(event.kind == "singleton_completeness" for event in result.diagnostics)


@pytest.mark.parametrize("iri_strategy", ["id", "name"])
@pytest.mark.parametrize("powertype", [False, True], ids=["ordinary", "powertype"])
@pytest.mark.parametrize("defect", ["dangling_id", "primitive_datatype"])
def test_unusable_categorizer_keeps_independent_higher_order_classifications(
        run, source_json, tmp_path, iri_strategy, powertype, defect):
    """Rules: DK-HO-01, DK-HO-02, DK-HO-03, DK-HO-04, DK-CLS-03, DK-CLS-06, DK-CLS-07, DK-IRI-02, DK-IRI-09, DK-DIAG-05.

    RD-02 Alternative A, 0f290d3afb830418297af13c30c4c65be1e13ca8. A separate
    valid categorized set over gDeep (general cOutside) retains its ordinary or
    powertype classifications while gsFirst omits only its own categorizer facts.
    """
    document = source_json("shared/categorizers")
    expected_issues = _apply_unusable_categorizer(document, defect)
    source_element(document, "cCategorizer")["isPowertype"] = powertype
    independent = copy.deepcopy(source_element(document, "gsSecond"))
    independent.update(id="gsIndependent", name="Independent",
                       categorizer={"id": "cCategorizer", "type": "Class"},
                       generalizations=[{"id": "gDeep", "type": "Generalization"}])
    document["model"]["contents"].append(independent)
    assert fixture_issues(document) == expected_issues

    result = run(path=write_input(tmp_path, document), iri_strategy=iri_strategy, input_policy="best-effort")
    assert result.outcome == "completed-with-errors"
    _assert_unusable_categorizer_error(result.diagnostics)
    graph = result.ontology
    assert isinstance(graph, Graph)
    iris = {
        key: BASE[key if iri_strategy == "id" else name]
        for key, name in (("cBase", "Base"), ("cOne", "One"), ("cTwo", "Two"),
                          ("cOutside", "Outside"), ("cDeep", "Deep"),
                          ("cCategorizer", "Categorizer"), ("cOtherCategorizer", "OtherCategorizer"))
    }
    assert {s for s in graph.subjects(RDF.type, OWL.Class) if isinstance(s, URIRef)} == set(iris.values())
    expected_cat = {iris["cOutside"], iris["cDeep"]} if powertype else {iris["cDeep"]}
    assert set(graph.subjects(RDF.type, iris["cCategorizer"])) == expected_cat
    assert set(graph.subjects(RDF.type, iris["cOtherCategorizer"])) == {iris["cOne"]}
    assert set(graph.subjects(RDF.type, OWL.NamedIndividual)) == expected_cat | {iris["cOne"]}
    assert set(graph.objects(iris["cBase"], RDF.type)) == {OWL.Class}
    assert set(graph.objects(iris["cTwo"], RDF.type)) == {OWL.Class}
    assert {frozenset(pair) for pair in graph.subject_objects(OWL.disjointWith)} == {
        frozenset((iris["cOne"], iris["cTwo"])),
        frozenset((iris["cCategorizer"], iris["cOtherCategorizer"])),
    }
    bnode_subclasses = [o for o in graph.objects(iris["cBase"], RDFS.subClassOf) if isinstance(o, BNode)]
    assert len(bnode_subclasses) == 1
    assert set(rdf_list(graph, one_object(graph, bnode_subclasses[0], OWL.unionOf))) == {iris["cOne"], iris["cTwo"]}
    assert not any(term in {BASE.dString, BASE.string, XSD.string, BASE.missingCategorizer}
                   for triple in graph for term in triple)
    if iri_strategy == "name":
        assert not list(graph.subjects(DCTERMS.identifier, Literal("dString")))
        assert not list(graph.subjects(DCTERMS.identifier, Literal("missingCategorizer")))


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("precedence", [
    "empty_members", "null_members", "absent_members", "non_array_members", "duplicate_id",
])
def test_unusable_categorizer_respects_dk_diag_12_and_duplicate_id_precedence(
        run, source_json, tmp_path, precedence, input_policy):
    """Rules: DK-HO-04, DK-DIAG-12, DK-DIAG-05, DK-CLS-02, DK-CLS-03; §3.4 duplicate declaration IDs.

    RD-02 Alternative A, 0f290d3afb830418297af13c30c4c65be1e13ca8. DK-DIAG-12
    governs empty/missing/malformed membership containers and fatal duplicate
    declaration IDs retain precedence even when categorizer is also unusable.
    """
    document = source_json("shared/categorizers")
    affected = source_element(document, "gsFirst")
    affected.update(isComplete=True, isDisjoint=True,
                    categorizer={"id": "missingCategorizer", "type": "Class"})
    expected_issues = {"unresolved_reference:missingCategorizer"}
    if precedence == "empty_members":
        affected["generalizations"] = []
    elif precedence == "null_members":
        affected["generalizations"] = None
    elif precedence == "absent_members":
        del affected["generalizations"]
    elif precedence == "non_array_members":
        affected["generalizations"] = {"id": "gOne", "type": "Generalization"}
        expected_issues.add("malformed_membership")
    elif precedence == "duplicate_id":
        document["model"]["contents"].append(copy.deepcopy(source_element(document, "cOne")))
        expected_issues.add("duplicate_id:cOne")
    assert fixture_issues(document) == expected_issues

    result = run(path=write_input(tmp_path, document), iri_strategy="id", input_policy=input_policy)
    assert all("unusable_categorizer" not in event.facts for event in result.diagnostics), result.diagnostics
    if precedence == "duplicate_id":
        assert result.outcome == "aborted" and result.ontology is None and result.provenance is None
        assert any(event.severity == "ERROR" and event.code == "DUPLICATE_SOURCE_ID"
                   and "cOne" in event.identified_sources for event in result.diagnostics)
        return
    if precedence == "empty_members":
        assert any(event.severity == "ERROR" and event.kind == "empty_generalization_set"
                   and "gsFirst" in event.identified_sources for event in result.diagnostics)
    else:
        fact = {"null_members": "membership_null", "absent_members": "membership_absent",
                "non_array_members": "membership_non_array"}[precedence]
        assert any(event.severity == "ERROR" and "gsFirst" in event.identified_sources
                   and fact in event.facts for event in result.diagnostics), result.diagnostics
    if input_policy != "best-effort":
        assert result.outcome == "aborted" and result.ontology is None and result.provenance is None
        return
    assert result.outcome == "completed-with-errors"
    graph = result.ontology
    assert isinstance(graph, Graph)
    assert set(graph.subjects(RDF.type, OWL.Class)) == MODELED
    assert set(graph.subject_objects(RDFS.subClassOf)) == {
        (BASE.cOne, BASE.cBase), (BASE.cTwo, BASE.cBase),
        (BASE.cOutside, BASE.cBase), (BASE.cDeep, BASE.cOutside),
    }
    assert {frozenset(pair) for pair in graph.subject_objects(OWL.disjointWith)} == {
        frozenset((BASE.cCategorizer, BASE.cOtherCategorizer)),
    }
    assert set(graph.subjects(RDF.type, OWL.NamedIndividual)) == {BASE.cOne}
    assert set(graph.subjects(RDF.type, BASE.cOtherCategorizer)) == {BASE.cOne}
    assert not list(graph.subjects(RDF.type, BASE.cCategorizer))
    for predicate in (OWL.unionOf, OWL.disjointUnionOf, OWL.equivalentClass):
        assert not list(graph.triples((None, predicate, None)))
    assert not any(term in {BASE.gsFirst, BASE.missingCategorizer} for triple in graph for term in triple)


@pytest.mark.parametrize("input_policy", ["strict", "best-effort"])
@pytest.mark.parametrize("scenario", ["primitive_with_attribute", "void_with_attribute", "enumeration_literal"])
def test_unusable_categorizer_preserves_independent_target_mappings(
        run, source_json, tmp_path, scenario, input_policy):
    """Rules: DK-HO-01, DK-HO-02, DK-HO-03, DK-HO-04, DK-CLS-01, DK-CLS-02, DK-CLS-03, DK-CLS-04, DK-CLS-06, DK-CLS-07, DK-CLS-10, DK-ATT-01, DK-DAT-01, DK-DIAG-05.

    RD-02 Alternative A, 0f290d3afb830418297af13c30c4c65be1e13ca8. An unusable
    categorizer target that independently participates in attribute typing or
    enumeration-literal generation retains its valid mapping without acting as
    a categorizer class or XSD rdf:type target.
    """
    document = source_json("shared/categorizers")
    source_element(document, "gsFirst").update(isComplete=True, isDisjoint=True)
    if scenario in {"primitive_with_attribute", "void_with_attribute"}:
        target_id = "dString" if scenario == "primitive_with_attribute" else "dVoid"
        attr_id = "aLabel" if scenario == "primitive_with_attribute" else "aGap"
        datatype = copy.deepcopy(source_element(document, "cBase"))
        datatype.update(id=target_id, name="string" if scenario == "primitive_with_attribute" else "void",
                        stereotype="datatype", isPowertype=True)
        document["model"]["contents"].append(datatype)
        source_element(document, "cBase")["properties"] = [{
            "id": attr_id, "name": attr_id[1:].lower(), "description": None, "type": "Property",
            "propertyAssignments": None, "stereotype": None, "isDerived": False,
            "isReadOnly": False, "isOrdered": False, "cardinality": None,
            "propertyType": {"id": target_id, "type": "Class"}, "subsettedProperties": None,
            "redefinedProperties": None, "aggregationKind": None,
        }]
        source_element(document, "gsFirst")["categorizer"] = {"id": target_id, "type": "Class"}
    else:
        enumeration = copy.deepcopy(source_element(document, "cBase"))
        enumeration.update(
            id="eStatus", name="Status", stereotype="enumeration",
            literals=[{"id": "vPending", "name": "Pending", "description": None,
                       "type": "Literal", "propertyAssignments": None}],
        )
        document["model"]["contents"].append(enumeration)
        source_element(document, "gsFirst")["categorizer"] = {"id": "vPending", "type": "Literal"}
    assert fixture_issues(document) == frozenset()

    result = run(path=write_input(tmp_path, document), iri_strategy="id", input_policy=input_policy)
    _assert_unusable_categorizer_error(result.diagnostics)
    assert not any(event.kind == "singleton_completeness" for event in result.diagnostics)
    if input_policy != "best-effort":
        assert result.outcome == "aborted" and result.ontology is None and result.provenance is None
        return

    assert result.outcome == "completed-with-errors"
    graph = result.ontology
    assert isinstance(graph, Graph)
    expected_modeled = MODELED | ({BASE.eStatus} if scenario == "enumeration_literal" else set())
    assert {s for s in graph.subjects(RDF.type, OWL.Class) if isinstance(s, URIRef)} == expected_modeled
    assert {(s, o) for s, o in graph.subject_objects(RDFS.subClassOf) if not isinstance(o, BNode)} == {
        (BASE.cOne, BASE.cBase), (BASE.cTwo, BASE.cBase),
        (BASE.cOutside, BASE.cBase), (BASE.cDeep, BASE.cOutside),
    }
    bnode_subclasses = [(s, o) for s, o in graph.subject_objects(RDFS.subClassOf) if isinstance(o, BNode)]
    assert len(bnode_subclasses) == 1 and bnode_subclasses[0][0] == BASE.cBase
    assert set(rdf_list(graph, one_object(graph, bnode_subclasses[0][1], OWL.unionOf))) == {BASE.cOne, BASE.cTwo}
    actual_disjoint = {frozenset(pair) for pair in graph.subject_objects(OWL.disjointWith)}
    base_disjoint = {
        frozenset((BASE.cOne, BASE.cTwo)),
        frozenset((BASE.cCategorizer, BASE.cOtherCategorizer)),
    }
    if scenario == "enumeration_literal":
        required_disjoint = base_disjoint | {
            frozenset((BASE.eStatus, cls)) for cls in (BASE.cBase, BASE.cCategorizer, BASE.cOtherCategorizer)
        }
        optional_inherited = {
            frozenset((BASE.eStatus, cls)) for cls in (BASE.cOne, BASE.cTwo, BASE.cOutside, BASE.cDeep)
        }
        assert required_disjoint <= actual_disjoint <= required_disjoint | optional_inherited
    else:
        assert actual_disjoint == base_disjoint
    assert set(graph.subjects(RDF.type, BASE.cOtherCategorizer)) == {BASE.cOne}
    assert not list(graph.subjects(RDF.type, BASE.cCategorizer))
    assert not any(BASE.gsFirst in triple for triple in graph)
    if scenario == "primitive_with_attribute":
        assert (BASE.aLabel, RDF.type, OWL.DatatypeProperty) in graph
        assert (BASE.aLabel, RDFS.domain, BASE.cBase) in graph
        assert (BASE.aLabel, RDFS.range, XSD.string) in graph
        assert set(graph.subjects(RDF.type, OWL.NamedIndividual)) == {BASE.cOne}
        assert not list(graph.subjects(RDF.type, XSD.string))
        assert not any(BASE.dString in triple for triple in graph)
    elif scenario == "void_with_attribute":
        assert any(event.kind == "void_datatype" and event.severity == "WARNING"
                   and "aGap" in event.identified_sources for event in result.diagnostics)
        assert (BASE.aGap, RDF.type, OWL.DatatypeProperty) in graph
        assert (BASE.aGap, RDFS.domain, BASE.cBase) in graph
        assert not list(graph.objects(BASE.aGap, RDFS.range))
        assert set(graph.subjects(RDF.type, OWL.NamedIndividual)) == {BASE.cOne}
        assert not any(BASE.dVoid in triple or "void" in str(term).casefold() for triple in graph for term in triple)
    else:
        assert set(graph.subjects(RDF.type, OWL.NamedIndividual)) == {BASE.cOne, BASE.vPending}
        assert set(graph.objects(BASE.vPending, RDF.type)) == {OWL.NamedIndividual, BASE.eStatus}
        closures = [
            rdf_list(graph, head)
            for expr in ({BASE.eStatus}
                         | set(graph.objects(BASE.eStatus, OWL.equivalentClass))
                         | set(graph.subjects(OWL.equivalentClass, BASE.eStatus)))
            for head in graph.objects(expr, OWL.oneOf)
        ]
        assert closures == [(BASE.vPending,)]
        assert not list(graph.subjects(RDF.type, OWL.AllDifferent))
        assert not list(graph.subjects(RDF.type, BASE.vPending))


def test_unusable_categorizer_reader_requires_affirmative_condition():
    """Harness only: verify affirmative unusable-categorizer wording without fixing provisional codes."""
    accepted = (
        "Generalization set 'gsFirst' has an unusable categorizer reference {'id': 'dString', 'type': 'Class'}.",
        "Generalization set 'gsFirst' has an invalid or unresolved categorizer reference: 'Unresolved source reference'.",
        "Generalization set 'gsFirst' categorizer {'id': 'dString', 'type': 'Class'} has no generated local OWL class.",
        "Generalization set 'gsFirst' categorizer 'dString' resolves to a Class without a generated local OWL class.",
        "Generalization set 'gsFirst' categorizer 'dString' resolves to a datatype without a generated local OWL class.",
        "Generalization set 'gsFirst' categorizer 'dVoid' is Visual Paradigm void.",
        "Generalization set 'gsFirst' categorizer 'dString' is a supported primitive datatype.",
        "Generalization set 'gsFirst' categorizer 'gOne' is a Generalization, not a Class.",
        "Generalization set 'gsFirst' categorizer 'gOne' resolves to a non-Class declaration.",
        "Generalization set 'gsFirst' categorizer 'gOne' resolves to 'Generalization', not a Class.",
        "Categorizer 'dString' on generalization set 'gsFirst' has no generated local OWL class.",
        "Generalization set 'gsFirst' categorizer {'id': 'cCategorizer', 'type': 'Relation'} has a reference-type mismatch.",
        "Generalization set 'gsFirst': categorizer reference type does not match its declaration.",
        "Categorizer of generalization set 'gsFirst' cannot be resolved.",
        "Generalization set 'gsFirst' has a non-null categorizer that does not identify a generated local OWL class.",
    )
    rejected = (
        "Categorizer without a generated local class remains outside the decided baseline.",
        "Unresolved categorizer recovery remains outside the decided baseline.",
        "Unexpected internal failure while inspecting categorizer.",
        "Categorizer must resolve to a local OWL class.",
        "Categorizer 'cCategorizer' is expected to be a Class.",
        "Categorizer is expected to be a Class, got null.",
        "Generalization set 'gsFirst' categorizer is null.",
        "Generalization set 'gsFirst' categorizer is absent.",
        "Generalization set 'gsFirst' has no categorizer.",
        "Generalization set 'gsFirst' categorizer is valid.",
        "Generalization set 'gsFirst' categorizer is not unusable.",
        "Generalization set 'gsFirst' categorizer is neither invalid nor unresolved.",
        "Generalization set 'gsFirst' categorizer is malformed or missing.",
        "Generalization set 'gsFirst' has a usable or invalid categorizer.",
        "If the categorizer is unusable, conversion aborts.",
        "Generalization set 'gsFirst' member 'gOne' cannot be resolved; categorizer was not checked.",
        "Generalization set 'gsFirst' has an invalid generalizations container, not an unusable categorizer.",
        "Generalization set 'gsFirst': the categorizer is not null, and member 'missingMember' failed.",
        "Categorizer 'cCategorizer' on generalization set 'gsFirst' is valid.",
        "Generalization set 'gsFirst' categorizer 'dString' may resolve to a datatype without a local OWL class.",
    )
    for message in accepted:
        assert unusable_categorizer_diagnostic(message), message
    for message in rejected:
        assert not unusable_categorizer_diagnostic(message), message



@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("powertype", [False, True], ids=["ordinary", "powertype"])
def test_restricted_to_order_and_stereotype_do_not_validate_higher_order_assertions(run, source_json, tmp_path, input_policy, powertype):
    """Rules: DK-HO-01, DK-HO-02, DK-HO-03, DK-HO-04, DK-CLS-01, DK-CLS-05, DK-GEN-02.

    Event as categorizer and a lower numeric order are intentionally not checked
    for semantic appropriateness. No malformed structural input is introduced.
    """
    document = source_json("shared/categorizers")
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
    result = run("shared/categorizers", iri_strategy=iri_strategy)
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


_INSTANTIATION_EXTRA_SENTINELS = tuple(INSTANTIATION_SENTINELS) + (
    'DISCARDED_THIRD_ROLE_SENTINEL', '49..53',
)


def _third_instantiation_end():
    return {
        'id': 'eThirdInstantiation',
        'name': 'DISCARDED_THIRD_ROLE_SENTINEL',
        'description': None,
        'type': 'Property',
        'propertyAssignments': None,
        'stereotype': None,
        'isDerived': True,
        'isReadOnly': True,
        'isOrdered': True,
        'cardinality': '49..53',
        'propertyType': {'id': 'cOutside', 'type': 'Class'},
        'subsettedProperties': None,
        'redefinedProperties': None,
        'aggregationKind': 'COMPOSITE',
    }


@pytest.mark.parametrize('input_policy', POLICIES)
@pytest.mark.parametrize('container_case', [
    'absent', 'null', 'empty', 'unary', 'binary', 'n_ary', 'n_ary_third_end_only',
])
def test_instantiation_relation_accepts_absent_null_and_any_length_property_arrays(
        run, source_json, tmp_path, input_policy, container_case):
    """Rules: DK-INS-01, DK-INS-02, DK-HO-01, DK-HO-02, DK-DIAG-03, DK-DIAG-05. RD-02 Alternative A."""
    document = source_json('shared/instantiation')
    association = source_element(document, 'rInstantiation')
    s_end, t_end = copy.deepcopy(association['properties'])
    expected_categories = {'discarded_identifier', 'discarded_association_name', 'discarded_characteristics'}
    if container_case == 'absent':
        association.pop('properties', None)
    elif container_case == 'null':
        association['properties'] = None
    elif container_case == 'empty':
        association['properties'] = []
    elif container_case == 'unary':
        association['properties'] = [s_end]
        expected_categories |= {'discarded_role_names', 'discarded_multiplicities'}
    elif container_case == 'binary':
        association['properties'] = [s_end, t_end]
        expected_categories |= {'discarded_role_names', 'discarded_multiplicities'}
    elif container_case == 'n_ary':
        association['properties'] = [s_end, t_end, _third_instantiation_end()]
        expected_categories |= {'discarded_role_names', 'discarded_multiplicities'}
    else:
        for end in (s_end, t_end):
            end.update(name=None, description=None, cardinality=None)
            for key in ('isReadOnly', 'isOrdered', 'isDerived', 'aggregationKind'):
                end.pop(key, None)
        association['properties'] = [s_end, t_end, _third_instantiation_end()]
        expected_categories |= {'discarded_role_names', 'discarded_multiplicities'}

    result = run(path=write_input(tmp_path, document), iri_strategy='id', input_policy=input_policy)
    assert result.outcome == 'completed'
    assert not any(d.severity == 'ERROR' for d in result.diagnostics), result.diagnostics

    warnings = [d for d in result.diagnostics if d.kind == 'discarded_instantiation_data']
    assert len(warnings) == 1
    warning = warnings[0]
    assert warning.severity == 'WARNING'
    assert 'rInstantiation' in warning.source_ids and 'Relation' in warning.source_types
    assert {'association_data_not_materialized', *expected_categories} <= warning.facts

    for diagnostic in result.diagnostics:
        text = diagnostic.message + repr(diagnostic.raw) + repr(diagnostic.facts) + repr(diagnostic.generated_iris)
        assert not any(value in text for value in _INSTANTIATION_EXTRA_SENTINELS)
        assert not {
            str(BASE.rInstantiation), str(BASE.sInstantiation),
            str(BASE.tInstantiation), str(BASE.eThirdInstantiation),
        } & set(diagnostic.generated_iris)

    graph = result.ontology
    for triple in graph:
        assert not any(value in str(term) for term in triple for value in _INSTANTIATION_EXTRA_SENTINELS)
        assert not any(term in {
            BASE.rInstantiation, BASE.sInstantiation, BASE.tInstantiation, BASE.eThirdInstantiation,
        } for term in triple)
    assert not list(graph.subjects(RDF.type, OWL.ObjectProperty))
    assert not list(graph.subjects(RDF.type, OWL.DatatypeProperty))
    assert {OWL.Class, OWL.NamedIndividual, BASE.cCategorizer, BASE.cOtherCategorizer} <= set(
        graph.objects(BASE.cSpecific, RDF.type))
    assert (BASE.cOutside, RDF.type, BASE.cCategorizer) not in graph


@pytest.mark.parametrize('input_policy', POLICIES)
@pytest.mark.parametrize('container_case', [
    'non_array_object', 'non_array_string', 'non_array_empty_string',
    'non_array_zero', 'non_array_number', 'non_array_false', 'non_array_true',
    'non_object_null_entry', 'non_object_string_entry', 'non_object_number_entry',
    'non_property_class_entry', 'mixed_valid_and_non_property',
])
def test_instantiation_relation_rejects_non_array_or_malformed_properties_containers(
        run, source_json, tmp_path, input_policy, container_case):
    """Rules: DK-DIAG-03, DK-DIAG-05, DK-INS-01, DK-INS-02, DK-HO-01, DK-HO-02, DK-DIAG-04. RD-02 Alternative A."""
    document = source_json('shared/instantiation')
    peer_rel = {
        'id': 'rPeer', 'name': 'peerLink', 'description': None, 'type': 'Relation',
        'propertyAssignments': None, 'stereotype': 'material', 'isAbstract': False, 'isDerived': False,
        'properties': [
            {'id': 'sPeer', 'name': None, 'description': None, 'type': 'Property',
             'propertyAssignments': None, 'stereotype': None, 'isDerived': False, 'isReadOnly': False,
             'isOrdered': False, 'cardinality': None, 'propertyType': {'id': 'cOutside', 'type': 'Class'},
             'subsettedProperties': None, 'redefinedProperties': None, 'aggregationKind': 'NONE'},
            {'id': 'tPeer', 'name': None, 'description': None, 'type': 'Property',
             'propertyAssignments': None, 'stereotype': None, 'isDerived': False, 'isReadOnly': False,
             'isOrdered': False, 'cardinality': '1', 'propertyType': {'id': 'cBase', 'type': 'Class'},
             'subsettedProperties': None, 'redefinedProperties': None, 'aggregationKind': 'NONE'},
        ],
    }
    document['model']['contents'].append(peer_rel)

    association = source_element(document, 'rInstantiation')
    s_end, t_end = copy.deepcopy(association['properties'])
    fake_class = copy.deepcopy(source_element(document, 'cOutside'))
    fake_class['id'] = 'cFakeEnd'
    if container_case == 'non_array_object':
        association['properties'] = s_end
        expected_fact = 'relation_properties_non_array'
    elif container_case == 'non_array_string':
        association['properties'] = 'bad'
        expected_fact = 'relation_properties_non_array'
    elif container_case == 'non_array_empty_string':
        association['properties'] = ''
        expected_fact = 'relation_properties_non_array'
    elif container_case == 'non_array_zero':
        association['properties'] = 0
        expected_fact = 'relation_properties_non_array'
    elif container_case == 'non_array_number':
        association['properties'] = 42
        expected_fact = 'relation_properties_non_array'
    elif container_case == 'non_array_false':
        association['properties'] = False
        expected_fact = 'relation_properties_non_array'
    elif container_case == 'non_array_true':
        association['properties'] = True
        expected_fact = 'relation_properties_non_array'
    elif container_case == 'non_object_null_entry':
        association['properties'] = [None, t_end]
        expected_fact = 'relation_properties_malformed_entry'
    elif container_case == 'non_object_string_entry':
        association['properties'] = [s_end, 'bad']
        expected_fact = 'relation_properties_malformed_entry'
    elif container_case == 'non_object_number_entry':
        association['properties'] = [123]
        expected_fact = 'relation_properties_malformed_entry'
    elif container_case == 'non_property_class_entry':
        association['properties'] = [fake_class, t_end]
        expected_fact = 'relation_properties_malformed_entry'
    else:
        association['properties'] = [s_end, {'id': 'lFakeEnd', 'name': 'Fake', 'description': None,
                                             'type': 'Literal', 'propertyAssignments': None}, t_end]
        expected_fact = 'relation_properties_malformed_entry'

    result = run(path=write_input(tmp_path, document), iri_strategy='id',
                 input_policy=input_policy, inverse_properties='none')
    assert any(
        d.severity == 'ERROR'
        and expected_fact in d.facts
        and 'rInstantiation' in d.identified_sources
        and d.code != 'INTERNAL_TRANSFORMATION_FAILURE'
        and isinstance(d.code, str) and d.code
        and d.code not in STABLE_DIAGNOSTIC_CODES
        for d in result.diagnostics
    ), result.diagnostics
    assert not any(d.kind == 'discarded_instantiation_data' for d in result.diagnostics)
    for diagnostic in result.diagnostics:
        text = diagnostic.message + repr(diagnostic.raw) + repr(diagnostic.facts) + repr(diagnostic.generated_iris)
        assert not any(value in text for value in _INSTANTIATION_EXTRA_SENTINELS)

    if input_policy != 'best-effort':
        assert result.outcome == 'aborted' and result.ontology is None and result.provenance is None
        return

    assert result.outcome == 'completed-with-errors'
    graph = result.ontology
    for triple in graph:
        assert not any(value in str(term) for term in triple for value in _INSTANTIATION_EXTRA_SENTINELS)
        assert not any(term in {
            BASE.rInstantiation, BASE.sInstantiation, BASE.tInstantiation, BASE.cFakeEnd, BASE.lFakeEnd,
        } for term in triple)
    assert {s for s in graph.subjects(RDF.type, OWL.ObjectProperty)
            if str(s).startswith(str(BASE))} == {BASE.tPeer}
    assert not list(graph.subjects(RDF.type, OWL.DatatypeProperty))
    assert {OWL.Class, OWL.NamedIndividual, BASE.cCategorizer, BASE.cOtherCategorizer} <= set(
        graph.objects(BASE.cSpecific, RDF.type))
    assert (BASE.cOutside, RDF.type, BASE.cCategorizer) not in graph

