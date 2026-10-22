"""Input-policy, stereotype-policy and programmatic diagnostic contracts."""

import copy
import json

import pytest
from rdflib import Graph, Literal, Namespace
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS

from tests.support.data import (FIXTURES, fixture_issues, fixture_path, load_json,
                               source_element, source_elements, write_input)
from tests.support.invocation import diagnostic_signatures
from tests.support.rdf import assert_contains, assert_graph_equal, assert_selected_equal, load_graph, rdf_list


BASE = Namespace("https://example.test/model#")
POLICIES = ["strict", "tolerant", "best-effort"]
DUPLICATES = {
    "different": {"cPerson"}, "identical": {"cPerson", "aAge", "aNote", "aAddress"},
    "attribute": {"aAge"}, "relation": {"rWorks"}, "end": {"eSource"},
    "cross_kind": {"cPerson"}, "decoded_equal": {"cPerson"},
}
VALID_BUNDLES = [
    ("shared/core_model", "input.json"), ("shared/base_iri", "input.json"),
    ("iris/names", "input.json"), ("iris/id_escaping", "input.json"),
    ("iris/collisions", "input.json"), ("iris/fallbacks", "input.json"),
    ("shared/property_collisions", "input.json"), ("properties/unnamed_owner", "input.json"),
    ("ontology/organization", "input.json"), ("ontology/organization", "duplicate_views.json"),
    ("ontology/custom_assignments", "input.json"), ("ontology/explicit_structures", "input.json"),
    ("input_diagnostics/id_comparison", "input.json"),
    ("classes/disjointness", "input.json"), ("classes/generalization_sets", "input.json"),
    ("classes/enumerations", "input.json"), ("classes/flags", "input.json"),
    ("higher_order/categorizers", "input.json"), ("shared/source_text", "input.json"),
    ("attributes_datatypes/value_types", "input.json"), ("attributes_datatypes/structured", "input.json"),
    ("properties/references", "input.json"), ("properties/source_flags", "input.json"),
    ("shared/omitted_connector", "input.json"),
    ("shared/binary_relation", "input.json"), ("relations/material_naming", "input.json"),
    ("relations/hierarchy", "input.json"), ("inverses/secondary_collisions", "input.json"),
]
# Preserve existing harness node IDs when their canonical fixture paths move.
VALID_BUNDLE_IDS = {"shared/base_iri": "iris_base_iri", "shared/property_collisions": "properties_collisions", "shared/omitted_connector": "properties_omitted_connector"}
NEGATIVE_BUNDLES = [
    ("input_diagnostics/unknown_information", "input.json", {"unknown_field:waveOneUnknownField"}),
    ("input_diagnostics/unknown_information", "unknown_element.json", {"unknown_element"}),
] + [("input_diagnostics/duplicates", variant + ".json", {"duplicate_id:" + identifier for identifier in identifiers}) for variant, identifiers in DUPLICATES.items()]
FAILED_ENDS = ["missing_source_id", "null_source_id", "empty_source_id", "numeric_source_id",
               "missing_target_id", "null_source_type", "unresolved_target_type", "malformed_target_type"]
STEREOTYPE_TARGETS = ["class", "relation", "attribute", "source_end", "target_end"]
FIXED_PREDICATES = {RDF.type, RDFS.domain, RDFS.range, RDFS.label, DCTERMS.identifier,
                    RDFS.subClassOf, RDFS.subPropertyOf, OWL.inverseOf,
                    OWL.equivalentClass, OWL.equivalentProperty, OWL.propertyChainAxiom,
                    OWL.propertyDisjointWith}


def _stereotype_target(document, target):
    contents = document["model"]["contents"]
    return {
        "class": contents[1], "relation": contents[-1],
        "attribute": contents[0]["properties"][0],
        "source_end": contents[-1]["properties"][0],
        "target_end": contents[-1]["properties"][1],
    }[target]


def _break_end(document, defect):
    source, target = document["model"]["contents"][-1]["properties"]
    if defect == "missing_source_id":
        del source["id"]
    elif defect == "null_source_id":
        source["id"] = None
    elif defect == "empty_source_id":
        source["id"] = ""
    elif defect == "numeric_source_id":
        source["id"] = 123
    elif defect == "missing_target_id":
        del target["id"]
    elif defect == "null_source_type":
        source["propertyType"] = None
    elif defect == "unresolved_target_type":
        target["propertyType"] = {"id": "missingClass", "type": "Class"}
    elif defect == "malformed_target_type":
        target["propertyType"] = "cOrg"
    else:
        raise AssertionError("Unlisted governed defect: " + defect)


@pytest.mark.parametrize("key,filename", VALID_BUNDLES, ids=[VALID_BUNDLE_IDS.get(key, key.replace("/", "_")) + ("_duplicate_views" if name != "input.json" else "") for key, name in VALID_BUNDLES])
def test_fixture_contract_valid_inputs(key, filename):
    """Harness/source-format check only; no transformation coverage credit."""
    document = load_json(key, filename)
    assert fixture_issues(document) == frozenset()


@pytest.mark.parametrize("key,filename,expected", NEGATIVE_BUNDLES, ids=[key.replace("/", "_") + "_" + name.removesuffix(".json") for key, name, _ in NEGATIVE_BUNDLES])
def test_fixture_contract_governed_negatives(key, filename, expected):
    """Harness check: each declared invalid fixture has exactly its reviewed defects."""
    assert fixture_issues(load_json(key, filename)) == expected


def test_fixture_contract_malformed_json_is_intentional():
    """Harness check only: this single malformed file exercises parse failure."""
    with pytest.raises(json.JSONDecodeError):
        load_json("input_diagnostics/unprocessable")


def test_fixture_contract_register_covers_all_stored_inputs():
    """Harness integrity scan only; globbing does not pair inputs with RDF expectations."""
    listed = {fixture_path(key, filename) for key, filename in VALID_BUNDLES}
    listed |= {fixture_path(key, filename) for key, filename, _ in NEGATIVE_BUNDLES}
    listed.add(fixture_path("input_diagnostics/unprocessable"))
    assert set(FIXTURES.rglob("*.json")) == listed


@pytest.mark.parametrize("key,filename", [("shared/core_model", "expected.ttl"), ("ontology/explicit_structures", "expected.ttl"),
                                       ("classes/generalization_sets", "expected.ttl"), ("classes/enumerations", "expected.ttl"),
                                       ("higher_order/categorizers", "expected.ttl"),
                                       ("attributes_datatypes/value_types", "expected.ttl"),
                                       ("attributes_datatypes/structured", "expected.ttl"),
                                       ("shared/binary_relation", "expected.ttl"),
                                       ("inverses/secondary_collisions", "expected.ttl")],
                         ids=["core_ground_assertions", "explicit_generalizations", "class_set_generalizations", "enum_ground_assertions", "categorizer_ground_assertions", "primitive_attribute_ground", "recursive_datatype_ground", "binary_relation_ground", "inverse_secondary_collision_ground"])
def test_fixture_contract_turtle_expectations(key, filename):
    """Harness parsing only; each expectation is paired explicitly in its consumer."""
    expected = load_graph(fixture_path(key, filename))
    assert len(expected) > 0


def test_fixture_contract_new_declarations_and_references_are_not_confused():
    """Harness only: literals are declarations, repeated GS refs are references."""
    enum = load_json("classes/enumerations")
    assert {item["id"] for item in source_elements(enum) if item["type"] == "Literal"} == {"vPending", "vApproved", "vClosed"}
    assert source_element(enum, "vPending")["type"] == "Literal"
    source_element(enum, "vPending")["id"] = "vApproved"
    assert fixture_issues(enum) == {"duplicate_id:vApproved"}
    higher = load_json("higher_order/categorizers")
    assert not fixture_issues(higher)  # gOne is legitimately referenced twice.
    source_element(higher, "gsFirst")["generalizations"][0]["id"] = "missingGen"
    assert fixture_issues(higher) == {"unresolved_reference:missingGen"}
    assert fixture_issues(load_json("classes/enumerations")) == frozenset()  # no mutation leaks


@pytest.mark.parametrize("defect,expected", [
    ("literal_id", {"invalid_id"}), ("literal_collection", {"malformed_literals"}),
    ("generalization_endpoint", {"malformed_reference"}),
    ("categorizer_reference", {"unresolved_reference:missingCategorizer"}),
    ("language_value", {"invalid_text:name"}), ("language_collection", {"invalid_languages"}),
    ("numeric_order", {"invalid_order_type"}),
], ids=["null_literal_id", "malformed_literal_collection", "failed_class_generalization", "unresolved_categorizer_audit_only", "invalid_localized_value_audit_only", "invalid_project_languages_audit_only", "exporter_order_is_string"])
def test_fixture_contract_runtime_mutations_have_only_declared_defects(defect, expected):
    """Harness only: invalid carriers/categorizer recovery have no behavior claim."""
    document = load_json("higher_order/categorizers" if defect in {"generalization_endpoint", "categorizer_reference"} else "classes/enumerations")
    if defect == "literal_id":
        source_element(document, "vPending")["id"] = None
    elif defect == "literal_collection":
        source_element(document, "eStatus")["literals"] = "Pending"
    elif defect == "generalization_endpoint":
        source_element(document, "gOne")["specific"] = None
    elif defect == "categorizer_reference":
        source_element(document, "gsFirst")["categorizer"]["id"] = "missingCategorizer"
    elif defect == "language_value":
        source_element(document, "vPending")["name"] = {"en": 42}
    elif defect == "language_collection":
        document["languages"] = "en"
    elif defect == "numeric_order":
        source_element(document, "eStatus")["order"] = 2
    assert fixture_issues(document) == expected


def test_rdf_helper_rejects_broken_or_cyclic_collections():
    """Harness only; collection reading does not impose semantic member order."""
    from rdflib import BNode
    head, tail = BNode(), BNode()
    graph = Graph()
    graph.add((head, RDF.first, BASE.one))
    graph.add((head, RDF.rest, tail))
    graph.add((tail, RDF.first, BASE.two))
    graph.add((tail, RDF.rest, RDF.nil))
    assert rdf_list(graph, head) == (BASE.one, BASE.two)
    assert rdf_list(graph, RDF.nil) == ()
    graph.remove((tail, RDF.rest, RDF.nil))
    with pytest.raises(AssertionError):
        rdf_list(graph, head)
    graph.add((tail, RDF.rest, head))
    with pytest.raises(AssertionError, match="Cyclic"):
        rdf_list(graph, head)
    graph.set((tail, RDF.rest, RDF.nil))
    graph.add((head, RDF.first, BASE.extra))
    with pytest.raises(AssertionError):
        rdf_list(graph, head)


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("filename", ["input.json", "unknown_element.json"], ids=["unknown_field", "unknown_element_type"])
def test_unknown_information_follows_input_policy(run, source_path, input_policy, filename):
    """Rules: DK-DIAG-01, DK-DIAG-04, DK-DIAG-05, DK-GEN-01."""
    result = run("input_diagnostics/unknown_information", filename, iri_strategy="id", input_policy=input_policy)
    events = [d for d in result.diagnostics if d.kind == "unknown_information"]
    assert events
    if input_policy == "strict":
        assert result.outcome == "aborted"
        assert result.ontology is None
        assert all(d.severity == "ERROR" for d in events)
    else:
        assert result.outcome == "completed"
        assert all(d.severity == "WARNING" for d in events)
        assert not any(d.severity == "ERROR" for d in result.diagnostics)
        assert_contains(result.ontology, load_graph(source_path("shared/core_model", "expected.ttl")))
        for triple in result.ontology:
            for term in triple:
                assert "UNRECOGNIZED_FIELD_SENTINEL" not in str(term)
                assert "UNKNOWN_ELEMENT_SENTINEL" not in str(term)
        assert not any(result.ontology.triples((BASE.unknownOne, None, None)))


def test_default_input_policy_is_tolerant(run):
    """Rules: DK-DIAG-05; §15 input-policy default."""
    default = run("input_diagnostics/unknown_information")
    explicit = run("input_diagnostics/unknown_information", input_policy="tolerant")
    assert default.outcome == explicit.outcome == "completed"
    assert any(d.kind == "unknown_information" and d.severity == "WARNING" for d in default.diagnostics)
    assert_selected_equal(default.ontology, explicit.ontology, FIXED_PREDICATES, {OWL.disjointWith})
    assert diagnostic_signatures(default.diagnostics) == diagnostic_signatures(explicit.diagnostics)


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("defect", FAILED_ENDS)
def test_failed_relation_never_delivers_either_direction(run, source_json, tmp_path, input_policy, defect):
    """Rules: DK-DIAG-01, DK-DIAG-03, DK-DIAG-04, DK-DIAG-05, DK-GEN-03."""
    document = source_json("shared/core_model")
    _break_end(document, defect)
    assert fixture_issues(document)
    result = run(path=write_input(tmp_path, document), iri_strategy="id", input_policy=input_policy)
    assert result.configuration_error is None
    assert any(d.severity == "ERROR" for d in result.diagnostics)
    if input_policy != "best-effort":
        assert result.outcome == "aborted"
        assert result.ontology is None
    else:
        assert result.outcome == "completed-with-errors"
        assert (BASE.cPerson, RDF.type, OWL.Class) in result.ontology
        assert (BASE.aAge, RDF.type, OWL.DatatypeProperty) in result.ontology
        assert (BASE.cOrg, RDF.type, OWL.Class) in result.ontology
        named_local_properties = {
            subject for kind in (OWL.ObjectProperty, OWL.DatatypeProperty)
            for subject in result.ontology.subjects(RDF.type, kind)
            if str(subject).startswith(str(BASE))
        }
        assert named_local_properties == {BASE.aAge, BASE.aNote, BASE.aAddress}
        for omitted in (BASE.eSource, BASE.eTarget, BASE.rWorks, BASE.missingClass):
            assert not any(result.ontology.triples((omitted, None, None)))
        # A delivered partial graph must still serialize and parse as RDF.
        parsed = Graph().parse(data=result.ontology.serialize(format="turtle"), format="turtle")
        assert_graph_equal(parsed, result.ontology)


@pytest.mark.parametrize("input_policy", POLICIES)
def test_unprocessable_document_aborts_in_every_policy(run, input_policy):
    """Rules: DK-DIAG-01, DK-DIAG-04, DK-DIAG-05; §3.4."""
    result = run("input_diagnostics/unprocessable", input_policy=input_policy)
    assert result.configuration_error is None
    assert result.outcome == "aborted"
    assert result.ontology is None
    assert any(d.severity == "ERROR" for d in result.diagnostics)


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("variant", list(DUPLICATES))
def test_duplicate_declaration_ids_always_abort(run, invoke, input_policy, variant):
    """Rules: DK-DIAG-01, DK-DIAG-04, DK-DIAG-05, DK-CONF-02; §3.4 duplicate source-element IDs."""
    result = run("input_diagnostics/duplicates", variant + ".json", input_policy=input_policy)
    assert result.outcome == "aborted"
    assert result.ontology is None
    errors = [d for d in result.diagnostics if d.kind == "duplicate_id"]
    assert errors
    assert all(d.severity == "ERROR" and set(d.source_ids) & DUPLICATES[variant] for d in errors)
    assert any({"competing_declarations", "conversion_aborted"} <= d.facts for d in errors)
    assert diagnostic_signatures(invoke.read_diagnostics(result)) == diagnostic_signatures(result.diagnostics)
    assert invoke.read_outcome(result) == "aborted"


@pytest.mark.parametrize("input_policy", POLICIES)
def test_repeated_references_are_not_duplicate_declarations(run, input_policy):
    """Rules: DK-DIAG-05; §3.4 duplicate source-element IDs."""
    result = run(input_policy=input_policy)
    assert result.outcome == "completed"
    assert not any(d.kind == "duplicate_id" for d in result.diagnostics)
    assert (BASE.Person, RDF.type, OWL.Class) in result.ontology


@pytest.mark.parametrize("input_policy", POLICIES)
def test_ids_differing_only_by_surrounding_whitespace_remain_distinct(run, input_policy):
    """Rules: DK-DIAG-05, DK-IRI-02, DK-IRI-05, DK-CONF-02; §3.4 duplicate source-element IDs.

    Both declarations coexist in the same complete input. This tests duplicate
    detection independently of the separate byte-escaping parameter cases.
    """
    result = run("input_diagnostics/id_comparison", iri_strategy="id", input_policy=input_policy)
    assert result.configuration_error is None
    assert result.outcome == "completed"
    assert not any(d.kind == "duplicate_id" or d.severity == "ERROR" for d in result.diagnostics)
    expected = {BASE.C17, BASE._x20C17_x20}
    assert set(result.ontology.subjects(RDF.type, OWL.Class)) == expected
    assert (BASE.C17, RDFS.label, Literal("Original")) in result.ontology
    assert (BASE._x20C17_x20, RDFS.label, Literal("Spaced")) in result.ontology


@pytest.mark.parametrize("target", STEREOTYPE_TARGETS)
@pytest.mark.parametrize("condition", ["null", "absent", "custom"])
@pytest.mark.parametrize("stereotype_policy", ["require-known", "allow-missing", "allow-custom"])
def test_stereotype_acceptance_matrix(run, source_json, source_path, tmp_path, target, condition, stereotype_policy):
    """Rules: DK-DIAG-01, DK-DIAG-05, DK-DIAG-06, DK-GEN-01.

    Default tolerant input handling covers every stereotype table cell. The
    separate precedence test supplies strict/best-effort counterexamples.
    """
    document = source_json("shared/core_model")
    selected = _stereotype_target(document, target)
    if condition == "absent":
        selected.pop("stereotype", None)
    else:
        selected["stereotype"] = "waveOneCustom" if condition == "custom" else None
    assert not fixture_issues(document)
    rejected = (condition == "custom" and stereotype_policy != "allow-custom") or (condition != "custom" and target in {"class", "relation"} and stereotype_policy == "require-known")
    result = run(path=write_input(tmp_path, document, "selected.json"), iri_strategy="id", stereotype_policy=stereotype_policy)
    kind = "unrecognized_stereotype" if condition == "custom" else "missing_stereotype"
    events = [d for d in result.diagnostics if d.kind == kind]
    if rejected:
        assert result.outcome == "aborted"
        assert result.ontology is None
        assert events and all(d.severity == "ERROR" for d in events)
    else:
        assert result.outcome == "completed"
        assert_contains(result.ontology, load_graph(source_path("shared/core_model", "expected.ttl")))
        if condition == "custom":
            assert events and all(d.severity == "WARNING" for d in events)
            # Accepted custom stereotypes must add no stereotype-specific semantics.
            baseline = copy.deepcopy(document)
            _stereotype_target(baseline, target)["stereotype"] = None
            ordinary = run(path=write_input(tmp_path, baseline, "ordinary.json"), iri_strategy="id", stereotype_policy="allow-custom")
            assert ordinary.outcome == "completed"
            assert_selected_equal(result.ontology, ordinary.ontology, FIXED_PREDICATES, {OWL.disjointWith})
        else:
            assert not events


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("target,value,stereotype_policy,outcome", [
    pytest.param("class", "waveOneCustom", "allow-custom", "completed", id="accept_custom_even_strict"),
    pytest.param("class", None, "require-known", "aborted", id="reject_missing_even_best_effort"),
    pytest.param("relation", "waveOneCustom", "allow-missing", "aborted", id="reject_custom_even_best_effort"),
])
def test_stereotype_policy_takes_precedence(run, source_json, tmp_path, input_policy, target, value, stereotype_policy, outcome):
    """Rules: DK-DIAG-05, DK-DIAG-06."""
    document = source_json("shared/core_model")
    _stereotype_target(document, target)["stereotype"] = value
    result = run(path=write_input(tmp_path, document), input_policy=input_policy, stereotype_policy=stereotype_policy)
    assert result.outcome == outcome
    relevant = [d for d in result.diagnostics if d.kind in {"missing_stereotype", "unrecognized_stereotype"}]
    assert relevant
    assert all(d.severity == ("WARNING" if outcome == "completed" else "ERROR") for d in relevant)
    if outcome == "aborted":
        assert result.ontology is None
    else:
        assert (BASE.Organization, RDF.type, OWL.Class) in result.ontology


def test_default_stereotype_policy_accepts_custom(run, source_json, tmp_path):
    """Rules: DK-DIAG-06; §15 stereotype-policy default."""
    document = source_json("shared/core_model")
    _stereotype_target(document, "class")["stereotype"] = "waveOneCustom"
    path = write_input(tmp_path, document)
    default = run(path=path, input_policy="strict")
    explicit = run(path=path, input_policy="strict", stereotype_policy="allow-custom")
    assert default.outcome == explicit.outcome == "completed"
    assert any(d.kind == "unrecognized_stereotype" and d.severity == "WARNING" for d in default.diagnostics)
    assert_selected_equal(default.ontology, explicit.ontology, FIXED_PREDICATES, {OWL.disjointWith})
    assert diagnostic_signatures(default.diagnostics) == diagnostic_signatures(explicit.diagnostics)


@pytest.mark.parametrize("input_policy", POLICIES)
def test_nonfatal_warnings_do_not_change_completed_outcome(invoke, source_path, tmp_path, input_policy):
    """Rules: DK-IRI-01, DK-DIAG-01, DK-DIAG-05; §15 outcome classification."""
    result = invoke.convert(source_path("shared/base_iri"), options={"input_policy": input_policy, "provenance": "none"}, workdir=tmp_path)
    assert result.outcome == "completed"
    assert result.ontology is not None
    assert any(d.kind == "placeholder_base" and d.severity == "WARNING" for d in result.diagnostics)
    assert not any(d.severity == "ERROR" for d in result.diagnostics)


@pytest.mark.parametrize("scenario,policy,outcome", [
    pytest.param("unknown", "tolerant", "completed", id="completed_with_warning"),
    pytest.param("failed_relation", "best-effort", "completed-with-errors", id="partial_with_error"),
    pytest.param("malformed", "strict", "aborted", id="aborted_with_error"),
])
def test_programmatic_diagnostic_access_is_complete_and_noninterfering(run, invoke, source_json, tmp_path, scenario, policy, outcome):
    """Rules: DK-DIAG-04, DK-DIAG-05; §15 Python diagnostic access and outcomes."""
    if scenario == "unknown":
        result = run("input_diagnostics/unknown_information", input_policy=policy)
    elif scenario == "malformed":
        result = run("input_diagnostics/unprocessable", input_policy=policy)
    else:
        document = source_json("shared/core_model")
        _break_end(document, "unresolved_target_type")
        result = run(path=write_input(tmp_path, document), input_policy=policy)
    assert result.outcome == outcome
    before = None if result.ontology is None else Graph()
    if before is not None:
        for triple in result.ontology:
            before.add(triple)
    original_events = diagnostic_signatures(result.diagnostics)
    assert original_events
    first = invoke.read_diagnostics(result)
    second = invoke.read_diagnostics(result)
    assert diagnostic_signatures(first) == diagnostic_signatures(second) == original_events
    assert all(d.severity in {"INFO", "WARNING", "ERROR"} and d.raw is not None for d in first)
    assert invoke.read_outcome(result) == outcome
    observed_graph = invoke.read_ontology(result)
    if outcome == "aborted":
        assert observed_graph is None and before is None
    else:
        assert observed_graph is not None
        assert_graph_equal(observed_graph, before)
