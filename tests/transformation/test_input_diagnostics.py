"""Input-policy, stereotype-policy and programmatic diagnostic contracts."""

import copy
import json

import pytest
from rdflib import Graph, Literal, Namespace
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS

from tests.support.data import FIXTURES, fixture_issues, fixture_path, load_json, write_input
from tests.support.invocation import diagnostic_signatures
from tests.support.rdf import assert_contains, assert_graph_equal, assert_selected_equal, load_graph


BASE = Namespace("https://example.test/model#")
POLICIES = ["strict", "tolerant", "best-effort"]
DUPLICATES = {
    "different": {"cPerson"}, "identical": {"cPerson", "aAge", "aNote", "aAddress"},
    "attribute": {"aAge"}, "relation": {"rWorks"}, "end": {"eSource"},
    "cross_kind": {"cPerson"}, "decoded_equal": {"cPerson"},
}
VALID_BUNDLES = [
    ("shared/core_model", "input.json"), ("iris/base_iri", "input.json"),
    ("iris/names", "input.json"), ("iris/id_escaping", "input.json"),
    ("iris/collisions", "input.json"), ("iris/fallbacks", "input.json"),
    ("properties/collisions", "input.json"), ("properties/unnamed_owner", "input.json"),
    ("ontology/organization", "input.json"), ("ontology/organization", "duplicate_views.json"),
    ("ontology/custom_assignments", "input.json"), ("ontology/explicit_structures", "input.json"),
]
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


@pytest.mark.parametrize("key,filename", VALID_BUNDLES, ids=[key.replace("/", "_") + ("_duplicate_views" if name != "input.json" else "") for key, name in VALID_BUNDLES])
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


@pytest.mark.parametrize("key,filename", [("ontology/core_model", "expected.ttl"), ("ontology/explicit_structures", "expected.ttl")], ids=["core_ground_assertions", "explicit_generalizations"])
def test_fixture_contract_turtle_expectations(key, filename):
    """Harness parsing only; each expectation is paired explicitly in its consumer."""
    expected = load_graph(fixture_path(key, filename))
    assert len(expected) > 0


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
        assert_contains(result.ontology, load_graph(source_path("ontology/core_model", "expected.ttl")))
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
        assert_contains(result.ontology, load_graph(source_path("ontology/core_model", "expected.ttl")))
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
    result = invoke.convert(source_path("iris/base_iri"), options={"input_policy": input_policy, "provenance": "none"}, workdir=tmp_path)
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
