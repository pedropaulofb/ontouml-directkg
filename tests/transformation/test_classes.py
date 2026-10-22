"""Class mappings, set constraints, enumeration identity, and class flags."""

import copy
from itertools import combinations

import pytest
from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, XSD

from tests.support.data import fixture_issues, source_element, write_input
from tests.support.invocation import diagnostic_signatures
from tests.support.rdf import (assert_contains, assert_graph_equal, load_graph,
                               one_object, one_subject, rdf_list)


BASE = Namespace("https://example.test/model#")
POLICIES = ["strict", "tolerant", "best-effort"]
ULTIMATE = {"collective", "kind", "mode", "quality", "quantity", "relator", "type"}
GROUPS = [
    {"abstract", "datatype", "enumeration"}, {"event"}, {"situation"},
    {"kind", "collective", "quantity", "relator", "mode", "quality", "subkind", "role",
     "phase", "category", "mixin", "roleMixin", "phaseMixin", "historicalRole",
     "historicalRoleMixin", "type"},
]


def _pairs(graph):
    return {frozenset((s, o)) for s, o in graph.subject_objects(OWL.disjointWith)}


def _pair_set(values):
    return {frozenset(pair) for pair in combinations(values, 2)}


def _assert_values(graph, enum, values, *, complete):
    """Inspect asserted membership, closure and inequality, never entailments.

    OWL permits equivalent anonymous enumeration expressions and either
    members/distinctMembers on AllDifferent. Collection order is immaterial.
    Several AllDifferent groups may establish the required pairs.
    """
    values = set(values)
    assert (enum, RDF.type, OWL.Class) in graph
    assert set(graph.subjects(RDF.type, enum)) == values
    for value in values:
        assert (value, RDF.type, OWL.NamedIndividual) in graph
    expressions = {enum} | set(graph.objects(enum, OWL.equivalentClass)) | set(graph.subjects(OWL.equivalentClass, enum))
    closures = [rdf_list(graph, head) for expr in expressions for head in graph.objects(expr, OWL.oneOf)]
    if complete:
        assert closures
        assert all(len(members) == len(values) and set(members) == values for members in closures)
    else:
        assert not closures
    difference_pairs = set()
    for axiom in graph.subjects(RDF.type, OWL.AllDifferent):
        heads = set(graph.objects(axiom, OWL.members)) | set(graph.objects(axiom, OWL.distinctMembers))
        assert heads
        for head in heads:
            members = rdf_list(graph, head)
            assert len(members) >= 2 and len(set(members)) == len(members)
            assert set(members) <= values
            difference_pairs |= _pair_set(members)
    assert difference_pairs == _pair_set(values)
    assert not (enum, OWL.equivalentClass, OWL.Nothing) in graph
    assert not (OWL.Nothing, OWL.equivalentClass, enum) in graph
    assert not (enum, RDFS.subClassOf, OWL.Nothing) in graph


def _assert_comment(result, target, field, value):
    meanings = [c for c in result.comments if c.subject == target and c.field == field]
    assert {c.value for c in meanings} == {value}
    for meaning in meanings:
        assert isinstance(meaning.literal, Literal)
        assert (target, RDFS.comment, meaning.literal) in result.ontology


def _logic(graph):
    """For the flag-only single-class input, ignore only annotation/header data.

    Every other asserted triple participates, including unexpected properties,
    anonymous restrictions and auxiliary resources. This is not a reasoner.
    """
    output = Graph()
    for s, p, o in graph:
        if p == RDF.type and o == OWL.AnnotationProperty:
            continue  # annotation vocabulary declarations add no class constraint
        if s != URIRef("https://example.test/model") and p not in {RDFS.comment, RDFS.label, DCTERMS.identifier}:
            output.add((s, p, o))
    return output


@pytest.mark.parametrize("members_predicate", ["members", "distinctMembers"])
@pytest.mark.parametrize("expression", ["direct", "equivalent_anonymous"])
def test_rdf_helper_enum_assertions_accept_unordered_owl_list_forms(members_predicate, expression):
    """Harness only: validate the assertion helper, not a simulated conversion."""
    closure = ":E owl:oneOf (:b :a)." if expression == "direct" else ":E owl:equivalentClass [a owl:Class; owl:oneOf (:b :a)]."
    graph = Graph().parse(data='''@prefix : <urn:helper:> .
        @prefix owl: <http://www.w3.org/2002/07/owl#> .
        :E a owl:Class . :a a owl:NamedIndividual, :E .
        :b a owl:NamedIndividual, :E .
        [] a owl:AllDifferent; owl:''' + members_predicate + ''' (:a :b).
        ''' + closure, format="turtle")
    _assert_values(graph, URIRef("urn:helper:E"), {URIRef("urn:helper:a"), URIRef("urn:helper:b")}, complete=True)
    with pytest.raises(AssertionError):
        _assert_values(graph, URIRef("urn:helper:E"), {URIRef("urn:helper:a"), URIRef("urn:helper:b")}, complete=False)
    graph.remove((URIRef("urn:helper:b"), RDF.type, URIRef("urn:helper:E")))
    with pytest.raises(AssertionError):
        _assert_values(graph, URIRef("urn:helper:E"), {URIRef("urn:helper:a"), URIRef("urn:helper:b")}, complete=True)


@pytest.mark.parametrize("input_policy", POLICIES)
def test_domain_classes_and_exact_stereotype_disjointness(run, source_json, input_policy):
    """Rules: DK-CLS-01, DK-CLS-03, DK-CLS-04, DK-DIAG-15, DK-GEN-02.

    No hierarchy exists here, so the permission to omit redundant inherited
    pairs cannot hide a missing pair. Every group member and same-stereotype
    ultimate pair is represented in this one bounded matrix.
    """
    source = source_json("classes/disjointness")
    classes = [c for c in source["model"]["contents"] if c["id"] not in {"dInt", "dVoid"}]
    result = run("classes/disjointness", iri_strategy="id", input_policy=input_policy)
    assert result.outcome == "completed"
    assert {s for s in result.ontology.subjects(RDF.type, OWL.Class) if isinstance(s, URIRef) and str(s).startswith(str(BASE))} == {BASE[c["id"]] for c in classes}
    required = set()
    for left, right in combinations(classes, 2):
        ls, rs = left["stereotype"], right["stereotype"]
        if (ls in ULTIMATE and rs in ULTIMATE) or next(i for i, g in enumerate(GROUPS) if ls in g) != next(i for i, g in enumerate(GROUPS) if rs in g):
            required.add(frozenset((BASE[left["id"]], BASE[right["id"]])))
    assert _pairs(result.ontology) == required
    assert not list(result.ontology.subjects(RDF.type, OWL.AllDisjointClasses))
    for omitted in (BASE.dInt, BASE.dVoid):
        assert not any(omitted in triple for triple in result.ontology)
    assert not any(XSD.int in pair for pair in _pairs(result.ontology))
    assert not any(d.severity in {"WARNING", "ERROR"} for d in result.diagnostics)
    abstract = [d for d in result.diagnostics if d.kind == "abstractness"]
    assert abstract and all(d.severity == "INFO" for d in abstract)
    assert not any("stereotype_disjointness_omitted" in d.facts for d in abstract)


@pytest.mark.parametrize("size", [2, 3], ids=["two_members", "three_members"])
@pytest.mark.parametrize("complete,disjoint", [(False, False), (False, True), (True, False), (True, True)], ids=["neither", "disjoint_only", "complete_only", "both"])
def test_generalization_set_flags_are_independent(run, source_json, source_path, tmp_path, size, complete, disjoint):
    """Rules: DK-CLS-02, DK-CLS-06, DK-CLS-07, DK-GEN-02."""
    document = source_json("classes/generalization_sets")
    gs = source_element(document, "gsMain")
    gs.update(isComplete=complete, isDisjoint=disjoint, generalizations=gs["generalizations"][:size])
    result = run(path=write_input(tmp_path, document), iri_strategy="id")
    assert result.outcome == "completed"
    assert_contains(result.ontology, load_graph(source_path("classes/generalization_sets", "expected.ttl")))
    specifics = [BASE.cB, BASE.cC, BASE.cD][:size]
    assert _pairs(result.ontology) == (_pair_set(specifics) if disjoint else set())
    unions = list(result.ontology.objects(BASE.cA, RDFS.subClassOf))
    unions = [node for node in unions if isinstance(node, BNode)]
    if complete:
        assert len(unions) == 1
        assert (unions[0], RDF.type, OWL.Class) in result.ontology
        members = rdf_list(result.ontology, one_object(result.ontology, unions[0], OWL.unionOf))
        assert len(members) == size and set(members) == set(specifics)
    else:
        assert not unions
        assert not list(result.ontology.triples((None, OWL.unionOf, None)))
    assert not list(result.ontology.triples((None, OWL.disjointUnionOf, None)))
    assert not any(d.kind == "semantic_validation" or d.severity in {"WARNING", "ERROR"} for d in result.diagnostics)


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("complete,disjoint", [(False, False), (False, True), (True, False), (True, True)], ids=["neither", "disjoint_only", "complete_only", "both"])
def test_singleton_completeness_has_reverse_edge_and_explanatory_info(run, source_json, tmp_path, input_policy, complete, disjoint):
    """Rules: DK-CLS-02, DK-CLS-06, DK-CLS-08, DK-DIAG-14, DK-DIAG-05."""
    document = source_json("classes/generalization_sets")
    gs = source_element(document, "gsMain")
    gs.update(isComplete=complete, isDisjoint=disjoint, generalizations=gs["generalizations"][:1])
    result = run(path=write_input(tmp_path, document), iri_strategy="id", input_policy=input_policy)
    assert result.outcome == "completed"
    assert (BASE.cB, RDFS.subClassOf, BASE.cA) in result.ontology
    assert ((BASE.cA, RDFS.subClassOf, BASE.cB) in result.ontology) == complete
    assert not _pairs(result.ontology)
    for predicate in (OWL.unionOf, OWL.equivalentClass, OWL.disjointUnionOf):
        assert not list(result.ontology.triples((None, predicate, None)))
    events = [d for d in result.diagnostics if d.kind == "singleton_completeness"]
    if complete:
        assert events
        assert any({"gsMain", "cA", "cB"} <= set(d.identified_sources) and
                   {"extensional_equivalence", "distinct_identifiers"} <= d.facts for d in events)
        assert all(d.severity == "INFO" for d in events)
    else:
        assert not events
    assert not any(d.severity in {"WARNING", "ERROR"} for d in result.diagnostics)


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("complete,disjoint", [(False, False), (False, True), (True, False), (True, True)], ids=["neither", "disjoint_only", "complete_only", "both"])
def test_explicit_empty_generalization_set_is_error_regardless_of_flags(run, source_json, source_path, tmp_path, input_policy, complete, disjoint):
    """Rules: DK-DIAG-12, DK-DIAG-05, DK-CLS-02, DK-CLS-06, DK-CLS-07."""
    document = source_json("classes/generalization_sets")
    source_element(document, "gsMain").update(generalizations=[], isComplete=complete, isDisjoint=disjoint)
    result = run(path=write_input(tmp_path, document), iri_strategy="id", input_policy=input_policy)
    assert any(d.kind == "empty_generalization_set" and d.severity == "ERROR" for d in result.diagnostics)
    if input_policy != "best-effort":
        assert result.outcome == "aborted" and result.ontology is None
    else:
        assert result.outcome == "completed-with-errors"
        assert_contains(result.ontology, load_graph(source_path("classes/generalization_sets", "expected.ttl")))
        assert not _pairs(result.ontology)
        assert not list(result.ontology.objects(BASE.cA, RDFS.subClassOf))
        for predicate in (OWL.unionOf, OWL.disjointUnionOf, OWL.equivalentClass):
            assert not list(result.ontology.triples((None, predicate, None)))
        assert not any(d.kind == "singleton_completeness" for d in result.diagnostics)


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("survivors", [2, 1, 0], ids=["two_survivors", "one_survivor", "no_survivors"])
@pytest.mark.parametrize("failure", ["unresolved_reference", "failed_generalization"])
def test_partial_set_retains_only_valid_disjoint_pairs_never_coverage(run, source_json, tmp_path, input_policy, survivors, failure):
    """Rules: DK-CLS-02, DK-CLS-06, DK-CLS-09, DK-DIAG-05, DK-DIAG-14.

    Categorizer is explicitly null: its partial recovery is not specified.
    """
    document = source_json("classes/generalization_sets")
    gs = source_element(document, "gsMain")
    gs.update(isDisjoint=True, isComplete=True)
    for index in range(survivors, 3):
        member = gs["generalizations"][index]
        if failure == "unresolved_reference":
            member["id"] = "missingGen" + str(index)
        else:
            source_element(document, member["id"])["specific"] = None
    assert fixture_issues(document)
    result = run(path=write_input(tmp_path, document), iri_strategy="id", input_policy=input_policy)
    assert any(d.severity == "ERROR" for d in result.diagnostics)
    if input_policy != "best-effort":
        assert result.outcome == "aborted" and result.ontology is None
        return
    assert result.outcome == "completed-with-errors"
    specifics = [BASE.cB, BASE.cC, BASE.cD][:survivors]
    assert _pairs(result.ontology) == _pair_set(specifics)
    for name in ("cA", "cB", "cC", "cD", "cE", "cF"):
        assert (BASE[name], RDF.type, OWL.Class) in result.ontology
    for gen in document["model"]["contents"]:
        if gen["type"] == "Generalization" and gen["specific"] is not None:
            assert (BASE[gen["specific"]["id"]], RDFS.subClassOf, BASE[gen["general"]["id"]]) in result.ontology
    assert not list(result.ontology.objects(BASE.cA, RDFS.subClassOf))
    for predicate in (OWL.unionOf, OWL.equivalentClass, OWL.disjointUnionOf):
        assert not list(result.ontology.triples((None, predicate, None)))
    assert not any(d.kind == "singleton_completeness" for d in result.diagnostics)


def test_false_set_disjointness_does_not_cancel_stereotype_disjointness(run, source_json, tmp_path):
    """Rules: DK-CLS-03, DK-CLS-06, DK-CLS-07, DK-GEN-02."""
    document = source_json("classes/generalization_sets")
    for identifier in ("cB", "cC"):
        source_element(document, identifier)["stereotype"] = "kind"
    source_element(document, "gsMain")["isComplete"] = True
    result = run(path=write_input(tmp_path, document), iri_strategy="id")
    assert result.outcome == "completed"
    assert _pairs(result.ontology) == {frozenset((BASE.cB, BASE.cC))}
    head = one_object(result.ontology, BASE.cA, RDFS.subClassOf)
    assert set(rdf_list(result.ontology, one_object(result.ontology, head, OWL.unionOf))) == {BASE.cB, BASE.cC, BASE.cD}
    assert not any(d.severity == "ERROR" or d.kind == "semantic_validation" for d in result.diagnostics)


@pytest.mark.parametrize("failure", ["unresolved_reference", "failed_generalization"])
def test_partial_non_disjoint_set_does_not_invent_disjointness(run, source_json, tmp_path, failure):
    """Rules: DK-CLS-06, DK-CLS-09, DK-DIAG-05."""
    document = source_json("classes/generalization_sets")
    gs = source_element(document, "gsMain")
    gs.update(isComplete=True, isDisjoint=False)
    if failure == "unresolved_reference":
        gs["generalizations"][-1]["id"] = "missingGen"
    else:
        source_element(document, "gD")["specific"] = None
    result = run(path=write_input(tmp_path, document), iri_strategy="id", input_policy="best-effort")
    assert result.outcome == "completed-with-errors"
    assert any(d.severity == "ERROR" for d in result.diagnostics)
    assert not _pairs(result.ontology)
    assert not list(result.ontology.objects(BASE.cA, RDFS.subClassOf))
    assert (BASE.cB, RDFS.subClassOf, BASE.cA) in result.ontology
    assert (BASE.cC, RDFS.subClassOf, BASE.cA) in result.ontology


@pytest.mark.parametrize("count", [1, 2, 3], ids=["one_value", "two_values", "three_values"])
@pytest.mark.parametrize("iri_strategy", ["name", "id"])
def test_complete_enumeration_membership_closure_and_difference(run, source_json, source_path, tmp_path, count, iri_strategy):
    """Rules: DK-CLS-10, DK-CLS-11, DK-IRI-08, DK-LBL-01, DK-GEN-03."""
    document = source_json("classes/enumerations")
    enum = source_element(document, "eStatus")
    enum["literals"] = enum["literals"][:count]
    result = run(path=write_input(tmp_path, document), iri_strategy=iri_strategy)
    assert result.outcome == "completed"
    target = BASE.eStatus if iri_strategy == "id" else BASE.Status
    values = [BASE[v["id"] if iri_strategy == "id" else "Status_" + v["name"]] for v in enum["literals"]]
    _assert_values(result.ontology, target, values, complete=True)
    for value, source in zip(values, enum["literals"]):
        assert (value, RDFS.label, Literal(source["name"])) in result.ontology
    attribute = BASE.pStatus if iri_strategy == "id" else BASE.status
    assert (attribute, RDF.type, OWL.ObjectProperty) in result.ontology
    assert (attribute, RDFS.range, target) in result.ontology
    legacy = BASE.pLegacy if iri_strategy == "id" else BASE.Pending
    assert (legacy, RDF.type, OWL.DatatypeProperty) in result.ontology
    assert (legacy, RDFS.domain, target) in result.ontology
    assert not list(result.ontology.objects(legacy, RDFS.range))
    assert (legacy, RDF.type, OWL.NamedIndividual) not in result.ontology
    if count == 3 and iri_strategy == "id":
        assert_contains(result.ontology, load_graph(source_path("classes/enumerations", "expected.ttl")))


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("condition", ["absent", "null", "empty"])
def test_unavailable_enum_values_warn_without_reinterpreting_owned_properties(run, source_json, tmp_path, input_policy, condition):
    """Rules: DK-CLS-10, DK-CLS-11, DK-DIAG-13, DK-DIAG-05."""
    document = source_json("classes/enumerations")
    enum = source_element(document, "eStatus")
    if condition == "absent":
        del enum["literals"]
    else:
        enum["literals"] = None if condition == "null" else []
    result = run(path=write_input(tmp_path, document), iri_strategy="id", input_policy=input_policy)
    assert result.outcome == "completed"
    _assert_values(result.ontology, BASE.eStatus, set(), complete=False)
    assert (BASE.pLegacy, RDF.type, OWL.DatatypeProperty) in result.ontology
    assert (BASE.pLegacy, RDFS.domain, BASE.eStatus) in result.ontology
    assert (BASE.pLegacy, RDF.type, OWL.NamedIndividual) not in result.ontology
    assert (BASE.pStatus, RDFS.range, BASE.eStatus) in result.ontology
    notices = [d for d in result.diagnostics if d.kind == "enumeration_values_unavailable"]
    assert notices and all(d.severity == "WARNING" for d in notices)
    assert any({"no_values_available", "closure_omitted"} <= d.facts for d in notices)
    assert not any(d.severity == "ERROR" for d in result.diagnostics)
    # Clarification that owned Properties are not values is SHOULD, not MUST.


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("malformed", ["string", "object"], ids=["string_collection", "object_collection"])
def test_malformed_enumeration_collection_obeys_error_policy(run, source_json, tmp_path, input_policy, malformed):
    """Rules: DK-CLS-11, DK-DIAG-13, DK-DIAG-05."""
    document = source_json("classes/enumerations")
    source_element(document, "eStatus")["literals"] = "Pending" if malformed == "string" else {"value": "Pending"}
    assert fixture_issues(document) == {"malformed_literals"}
    result = run(path=write_input(tmp_path, document), iri_strategy="id", input_policy=input_policy)
    assert any(d.severity == "ERROR" for d in result.diagnostics)
    if input_policy != "best-effort":
        assert result.outcome == "aborted" and result.ontology is None
    else:
        assert result.outcome == "completed-with-errors"
        _assert_values(result.ontology, BASE.eStatus, set(), complete=False)
        assert (BASE.pLegacy, RDF.type, OWL.DatatypeProperty) in result.ontology
        assert (BASE.pStatus, RDFS.range, BASE.eStatus) in result.ontology


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("survivors", [2, 1, 0], ids=["two_survivors", "one_survivor", "no_survivors"])
def test_incomplete_enumeration_never_closes_over_survivors(run, source_json, tmp_path, input_policy, survivors):
    """Rules: DK-CLS-10, DK-CLS-11, DK-DIAG-13, DK-DIAG-05."""
    document = source_json("classes/enumerations")
    for value in source_element(document, "eStatus")["literals"][survivors:]:
        value["id"] = None
    assert fixture_issues(document) == {"invalid_id"}
    result = run(path=write_input(tmp_path, document), iri_strategy="id", input_policy=input_policy)
    assert any(d.severity == "ERROR" for d in result.diagnostics)
    if input_policy != "best-effort":
        assert result.outcome == "aborted" and result.ontology is None
    else:
        assert result.outcome == "completed-with-errors"
        values = [BASE.vPending, BASE.vApproved, BASE.vClosed][:survivors]
        _assert_values(result.ontology, BASE.eStatus, values, complete=False)
        assert (BASE.pLegacy, RDF.type, OWL.DatatypeProperty) in result.ontology
        assert (BASE.pStatus, RDFS.range, BASE.eStatus) in result.ontology


@pytest.mark.parametrize("names", [("Same", "Same"), ("a-b", "a b")], ids=["identical_names", "normalization_collision"])
def test_distinct_enum_values_survive_name_collisions(run, source_json, tmp_path, names):
    """Rules: DK-IRI-08, DK-IRI-07, DK-CLS-10, DK-LBL-01."""
    document = source_json("classes/enumerations")
    enum = source_element(document, "eStatus")
    enum["literals"] = enum["literals"][:2]
    for value, name in zip(enum["literals"], names):
        value["name"] = name
    result = run(path=write_input(tmp_path, document))
    assert result.outcome == "completed"
    stem = "Status_Same" if names[0] == "Same" else "Status_a_b"
    values = {BASE[stem + "_1"], BASE[stem + "_2"]}
    _assert_values(result.ontology, BASE.Status, values, complete=True)
    targets = []
    for source in enum["literals"]:
        target = one_subject(result.ontology, DCTERMS.identifier, Literal(source["id"]))
        assert target in values
        assert (target, RDFS.label, Literal(source["name"])) in result.ontology
        targets.append(target)
    assert len(set(targets)) == 2


def test_value_prefix_uses_already_resolved_enum_class_name(run, source_json, tmp_path):
    """Rules: DK-IRI-08, DK-IRI-07, DK-CLS-10."""
    document = source_json("classes/enumerations")
    source_element(document, "cOwner")["name"] = "Status"
    result = run(path=write_input(tmp_path, document))
    assert result.outcome == "completed"
    # The typed attribute identifies the enum independently of an ID annotation.
    enum = one_object(result.ontology, BASE.status, RDFS.range)
    owner = one_object(result.ontology, BASE.status, RDFS.domain)
    assert {enum, owner} == {BASE.Status_1, BASE.Status_2}
    stem = str(enum).removeprefix(str(BASE))
    values = {BASE[stem + "_" + name] for name in ("Pending", "Approved", "Closed")}
    _assert_values(result.ontology, enum, values, complete=True)


@pytest.mark.parametrize("fallback", [False, True], ids=["named_literal", "generic_literal_fallback"])
def test_literal_collisions_with_other_source_resources_preserve_both(run, source_json, tmp_path, fallback):
    """Rules: DK-IRI-08, DK-IRI-04, DK-IRI-07, DK-CLS-10, DK-CLS-11."""
    document = source_json("classes/enumerations")
    stem = "vPending" if fallback else "Status_Pending"
    source_element(document, "cOwner")["name"] = stem
    if fallback:
        source_element(document, "vPending")["name"] = None
    result = run(path=write_input(tmp_path, document))
    assert result.outcome == "completed"
    owner = one_object(result.ontology, BASE.status, RDFS.domain)
    values = set(result.ontology.subjects(RDF.type, BASE.Status))
    pending_candidates = values - {BASE.Status_Approved, BASE.Status_Closed}
    assert len(pending_candidates) == 1
    pending = next(iter(pending_candidates))
    assert {pending, owner} == {BASE[stem + "_1"], BASE[stem + "_2"]}
    assert (owner, RDF.type, OWL.Class) in result.ontology
    assert (pending, RDF.type, OWL.Class) not in result.ontology
    _assert_values(result.ontology, BASE.Status, values, complete=True)
    assert len(values) == 3
    if fallback:
        assert any(d.severity == "WARNING" and "vPending" in d.identified_sources and str(pending) in d.generated_iris for d in result.diagnostics)


def test_literal_id_strategy_uses_own_escaped_id_without_enum_prefix(run, source_json, tmp_path):
    """Rules: DK-IRI-08, DK-IRI-05, DK-IRI-09, DK-CLS-10."""
    document = source_json("classes/enumerations")
    source_element(document, "vPending")["id"] = "9literal_é"
    result = run(path=write_input(tmp_path, document), iri_strategy="id")
    assert result.outcome == "completed"
    target = BASE.id_9literal_x5F_xC3_xA9
    _assert_values(result.ontology, BASE.eStatus, {target, BASE.vApproved, BASE.vClosed}, complete=True)
    assert (target, RDFS.label, Literal("Pending")) in result.ontology
    assert set(result.ontology.subjects(DCTERMS.identifier, Literal("9literal_é"))) == {target}


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("iri_strategy", ["name", "id"])
@pytest.mark.parametrize("condition", ["absent", "null", "empty", "whitespace", "punctuation", "non_ascii"])
def test_literal_generic_fallback_is_nonfatal_and_counts_as_complete(run, source_json, tmp_path, input_policy, iri_strategy, condition):
    """Rules: DK-IRI-08, DK-IRI-04, DK-CLS-10, DK-CLS-11, DK-DIAG-13, DK-LBL-01."""
    document = source_json("classes/enumerations")
    literal = source_element(document, "vPending")
    if condition == "absent":
        del literal["name"]
    else:
        literal["name"] = {"null": None, "empty": "", "whitespace": "  \t", "punctuation": "___", "non_ascii": "東京"}[condition]
    result = run(path=write_input(tmp_path, document), iri_strategy=iri_strategy, input_policy=input_policy)
    assert result.outcome == "completed"
    enum = BASE.eStatus if iri_strategy == "id" else BASE.Status
    others = {BASE.vApproved, BASE.vClosed} if iri_strategy == "id" else {BASE.Status_Approved, BASE.Status_Closed}
    _assert_values(result.ontology, enum, others | {BASE.vPending}, complete=True)
    assert not any("unnamedLiteral_" in str(term) for triple in result.ontology for term in triple)
    source_name = literal.get("name")
    labels = set(result.ontology.objects(BASE.vPending, RDFS.label))
    if source_name is not None and source_name.strip():
        assert Literal(source_name) in labels
    elif source_name is not None:
        assert labels <= {Literal(source_name)}
    else:
        assert not labels
    events = [d for d in result.diagnostics if d.kind in {"missing_name", "generic_id_fallback"} and "vPending" in d.identified_sources]
    if iri_strategy == "name":
        assert events and all(d.severity == "WARNING" for d in events)
        assert any(str(BASE.vPending) in d.generated_iris for d in events)
    elif condition in {"absent", "null", "empty", "whitespace"}:
        assert events and all(d.severity == "INFO" for d in events)
        assert any("missing_name" in d.facts for d in events)
    else:
        assert not events
    assert not any(d.severity == "ERROR" or d.kind in {"ordinary_id_use", "enumeration_values_unavailable"} for d in result.diagnostics)


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("field,kind,condition", [
    pytest.param(field, kind, condition, id=label + "_" + condition)
    for field, kind, label in [("isAbstract", "abstractness", "abstract_flag"),
                               ("isDerived", "derived_status", "derived_flag"),
                               ("isExtensional", "extensionality", "extensional_flag")]
    for condition in (["true", "false", "absent"] if field == "isAbstract" else ["true", "false", "absent", "null"])
])
def test_class_flags_preserve_only_explicit_values_without_logical_approximation(run, source_json, tmp_path, input_policy, field, kind, condition):
    """Rules: DK-CLS-01, DK-GEN-05, DK-DIAG-15, DK-DIAG-16, DK-DIAG-17.

    Null isAbstract is not used: that input treatment is not established.
    Other explicit false exporter defaults remain real declarations.
    """
    document = source_json("classes/flags")
    focus = source_element(document, "cFocus")
    for flag in ("isAbstract", "isDerived", "isExtensional"):
        focus.pop(flag, None)
    if condition == "absent":
        focus.pop(field, None)
    else:
        focus[field] = {"true": True, "false": False, "null": None}[condition]
    result = run(path=write_input(tmp_path, document), iri_strategy="id", input_policy=input_policy)
    assert result.outcome == "completed"
    supplied = field in focus and isinstance(focus[field], bool)
    if supplied:
        _assert_comment(result, BASE.cFocus, field, focus[field])
    else:
        assert not [c for c in result.comments if c.subject == BASE.cFocus and c.field == field]
    expected = Graph()
    expected.add((BASE.cFocus, RDF.type, OWL.Class))
    assert_graph_equal(_logic(result.ontology), expected)
    events = [d for d in result.diagnostics if d.kind == kind]
    required = supplied and (field == "isAbstract" or focus[field] is True)
    if required:
        assert events and all(d.severity == "INFO" for d in events)
        facts = {"preserved_as_annotation", {"isAbstract": "not_logically_enforced", "isDerived": "no_derivation_rule_supplied", "isExtensional": "essential_parthood_not_enforced"}[field]}
        assert any(facts <= d.facts for d in events)
        if field != "isAbstract":
            assert any("cFocus" in d.identified_sources for d in events)
    else:
        assert not events
    assert not any(d.severity in {"WARNING", "ERROR"} for d in result.diagnostics)


@pytest.mark.parametrize("flag", [True, False, "absent"], ids=["explicit_true", "explicit_false", "no_flag"])
def test_abstract_stereotype_is_independent_of_abstract_flag(run, source_json, tmp_path, flag):
    """Rules: DK-CLS-01, DK-CLS-04, DK-DIAG-15."""
    document = source_json("classes/flags")
    focus = source_element(document, "cFocus")
    focus["stereotype"] = "abstract"
    if flag == "absent":
        del focus["isAbstract"]
    else:
        focus["isAbstract"] = flag
    other = copy.deepcopy(focus)
    other.update(id="cEvent", name="Event", stereotype="event")
    other.pop("isAbstract", None)
    document["model"]["contents"].append(other)
    result = run(path=write_input(tmp_path, document), iri_strategy="id")
    assert result.outcome == "completed"
    _assert_comment(result, BASE.cFocus, "stereotype", "abstract")
    if flag == "absent":
        assert not [c for c in result.comments if c.subject == BASE.cFocus and c.field == "isAbstract"]
    else:
        _assert_comment(result, BASE.cFocus, "isAbstract", flag)
    assert _pairs(result.ontology) == {frozenset((BASE.cFocus, BASE.cEvent))}
    actual = _logic(result.ontology)
    actual.remove((None, OWL.disjointWith, None))
    expected = Graph()
    expected.add((BASE.cFocus, RDF.type, OWL.Class))
    expected.add((BASE.cEvent, RDF.type, OWL.Class))
    assert_graph_equal(actual, expected)
    events = [d for d in result.diagnostics if d.kind == "abstractness"]
    assert events and all(d.severity == "INFO" for d in events)
    assert any({"preserved_as_annotation", "not_logically_enforced"} <= d.facts for d in events)
    assert not any("stereotype_disjointness_omitted" in d.facts for d in events)
    assert not any(d.severity in {"WARNING", "ERROR"} for d in result.diagnostics)


@pytest.mark.parametrize("kind", ["custom_datatype", "enumeration", "primitive", "void"])
@pytest.mark.parametrize("derived", [True, False], ids=["derived", "not_derived"])
def test_class_derived_status_uses_only_eligible_local_target(run, source_json, tmp_path, kind, derived):
    """Rules: DK-GEN-05, DK-CLS-01, DK-CLS-10, DK-DIAG-16."""
    document = source_json("classes/enumerations")
    focus = source_element(document, "eStatus")
    document["model"]["contents"] = [focus]
    focus["properties"] = None
    focus.update(isDerived=derived, stereotype="enumeration" if kind == "enumeration" else "datatype",
                 name={"custom_datatype": "Address", "enumeration": "Status", "primitive": "int", "void": "void"}[kind])
    if kind != "enumeration":
        focus["literals"] = None
    result = run(path=write_input(tmp_path, document), iri_strategy="id")
    assert result.outcome == "completed"
    events = [d for d in result.diagnostics if d.kind == "derived_status"]
    if kind in {"custom_datatype", "enumeration"}:
        assert (BASE.eStatus, RDF.type, OWL.Class) in result.ontology
        _assert_comment(result, BASE.eStatus, "isDerived", derived)
        if derived:
            assert events and any(d.severity == "INFO" and "eStatus" in d.identified_sources and {"preserved_as_annotation", "no_derivation_rule_supplied"} <= d.facts for d in events)
        else:
            assert not events
        if kind == "enumeration":
            _assert_values(result.ontology, BASE.eStatus, {BASE.vPending, BASE.vApproved, BASE.vClosed}, complete=True)
            assert not [c for c in result.comments if c.field == "isDerived" and c.subject in {BASE.vPending, BASE.vApproved, BASE.vClosed}]
    else:
        assert not events
        assert not any(BASE.eStatus in triple for triple in result.ontology)
        assert not [c for c in result.comments if c.field == "isDerived"]
        assert not list(result.ontology.objects(XSD.int, RDFS.comment))
        assert not set(result.ontology.subjects(RDF.type, OWL.Class))
    for predicate in (OWL.propertyChainAxiom, OWL.equivalentProperty):
        assert not list(result.ontology.triples((None, predicate, None)))


@pytest.mark.parametrize("value", ["0", "1", "12", "*", None, "absent"], ids=["zero", "one", "multi_digit", "orderless", "null", "absent"])
def test_order_is_only_the_fixed_english_comment(run, source_json, tmp_path, value):
    """Rules: DK-CLS-05, DK-LBL-02, DK-HO-04."""
    document = source_json("classes/flags")
    focus = source_element(document, "cFocus")
    if value == "absent":
        del focus["order"]
    else:
        focus["order"] = value
    result = run(path=write_input(tmp_path, document), iri_strategy="id", language="pt-BR")
    assert result.outcome == "completed"
    comments = {c for c in result.ontology.objects(BASE.cFocus, RDFS.comment) if str(c).startswith("OntoUML classifier order:")}
    if value is None or value == "absent":
        assert not comments
    else:
        text = "OntoUML classifier order: orderless (*)." if value == "*" else "OntoUML classifier order: " + value + "."
        assert comments == {Literal(text, lang="en")}
    assert not {p for p in result.ontology.predicates(BASE.cFocus) if p not in {RDF.type, RDFS.comment, RDFS.label, DCTERMS.identifier}}
    expected = Graph()
    expected.add((BASE.cFocus, RDF.type, OWL.Class))
    assert_graph_equal(_logic(result.ontology), expected)
    assert not any(d.kind == "semantic_validation" for d in result.diagnostics)


@pytest.mark.parametrize("input_policy", POLICIES)
def test_restricted_to_is_recognized_but_wholly_omitted(run, source_json, tmp_path, input_policy):
    """Rules: DK-CLS-01, DK-CLS-03, DK-CLS-04, DK-CLS-05, DK-DIAG-05, DK-GEN-02."""
    document = source_json("classes/disjointness")
    baseline = run("classes/disjointness", iri_strategy="id", input_policy=input_policy)
    for item in document["model"]["contents"]:
        item["restrictedTo"] = ["event"]
        item["order"] = "12"
    with_order = copy.deepcopy(document)
    for item in with_order["model"]["contents"]:
        item["restrictedTo"] = None
    ordered = run(path=write_input(tmp_path, with_order, "ordered.json"), iri_strategy="id", input_policy=input_policy)
    result = run(path=write_input(tmp_path, document), iri_strategy="id", input_policy=input_policy)
    assert baseline.outcome == ordered.outcome == result.outcome == "completed"
    assert_graph_equal(result.ontology, ordered.ontology)
    assert diagnostic_signatures(result.diagnostics) == diagnostic_signatures(ordered.diagnostics)
    assert _pairs(result.ontology) == _pairs(baseline.ontology)
    assert not any(d.kind in {"restricted_to", "unknown_information", "semantic_validation"} for d in result.diagnostics)
