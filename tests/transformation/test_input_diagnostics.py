"""Input-policy, stereotype-policy and programmatic diagnostic contracts."""

import copy
import json
from collections import Counter
from types import SimpleNamespace

import pytest
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS

from tests.support.data import (FIXTURES, fixture_issues, fixture_path, load_json,
                               package_contents_document, source_element, source_elements, write_input)
from tests.support.invocation import (attribute_owner_without_local_class_diagnostic,
                                      class_properties_container_diagnostic,
                                      diagnostic_signatures,
                                      malformed_boolean_flag_diagnostic,
                                      malformed_class_order_diagnostic,
                                      malformed_package_contents_diagnostic,
                                      malformed_stereotype_diagnostic,
                                      non_enum_literals_diagnostic,
                                      package_contents_entry_diagnostic,
                                      project_languages_diagnostic,
                                      relation_properties_container_diagnostic,
                                      textual_carrier_diagnostic, unresolved_property_reference_between)
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
    ("shared/categorizers", "input.json"), ("shared/source_text", "input.json"),
    ("attributes_datatypes/value_types", "input.json"), ("attributes_datatypes/structured", "input.json"),
    ("properties/references", "input.json"), ("properties/source_flags", "input.json"),
    ("shared/omitted_connector", "input.json"),
    ("shared/binary_relation", "input.json"), ("relations/material_naming", "input.json"),
    ("relations/hierarchy", "input.json"), ("inverses/secondary_collisions", "input.json"),
    ("shared/material_pattern", "input.json"), ("relations/chain_constraints", "input.json"),
    ("shared/instantiation", "input.json"),
]
# Preserve existing harness node IDs when their canonical fixture paths move.
VALID_BUNDLE_IDS = {"shared/categorizers": "higher_order_categorizers", "shared/instantiation": "higher_order_instantiation", "shared/base_iri": "iris_base_iri", "shared/property_collisions": "properties_collisions", "shared/omitted_connector": "properties_omitted_connector"}
NEGATIVE_BUNDLES = [
    ("input_diagnostics/unknown_information", "input.json", {"unknown_field:waveOneUnknownField"}),
    ("input_diagnostics/unknown_information", "unknown_element.json", {"unknown_element"}),
] + [("input_diagnostics/duplicates", variant + ".json", {"duplicate_id:" + identifier for identifier in identifiers}) for variant, identifiers in DUPLICATES.items()]
FAILED_ENDS = ["missing_source_id", "null_source_id", "empty_source_id", "numeric_source_id",
               "missing_target_id", "null_source_type", "unresolved_target_type", "malformed_target_type",
               "non_utf8_source_id", "non_utf8_target_id", "non_utf8_endpoint_reference"]
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
    elif defect == "non_utf8_source_id":
        source["id"] = "\ud800"
    elif defect == "non_utf8_target_id":
        target["id"] = "\udfff"
    elif defect == "non_utf8_endpoint_reference":
        target["propertyType"]["id"] = "\ud800"
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
                                       ("inverses/secondary_collisions", "expected.ttl"),
                                       ("relations/material_pattern", "expected_chain.ttl")],
                         ids=["core_ground_assertions", "explicit_generalizations", "class_set_generalizations", "enum_ground_assertions", "categorizer_ground_assertions", "primitive_attribute_ground", "recursive_datatype_ground", "binary_relation_ground", "inverse_secondary_collision_ground", "material_chain_direction"])
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
    higher = load_json("shared/categorizers")
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
    document = load_json("shared/categorizers" if defect in {"generalization_endpoint", "categorizer_reference"} else "classes/enumerations")
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
    result = run(path=write_input(tmp_path, document, ensure_ascii=True), iri_strategy="id", input_policy=input_policy)
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
@pytest.mark.parametrize("scope", ["root", "nested"])
@pytest.mark.parametrize("form", ["absent", "null", "empty"])
def test_empty_package_contents_representations_are_equivalent(run, invoke, tmp_path, input_policy, scope, form):
    """Rules: DK-GEN-06, DK-DIAG-05; §3.2. RD-02 reduced-scope Alternative A."""
    baseline = run(path=write_input(tmp_path, package_contents_document(scope, "empty"), "control.json"),
                   iri_strategy="id", input_policy=input_policy)
    result = run(path=write_input(tmp_path, package_contents_document(scope, form)),
                 iri_strategy="id", input_policy=input_policy)
    assert baseline.outcome == result.outcome == "completed"
    assert_graph_equal(baseline.ontology, result.ontology)
    assert diagnostic_record_counts(invoke.report_content(result).events) == diagnostic_record_counts(
        invoke.report_content(baseline).events)
    assert not any(event.severity in {"WARNING", "ERROR"} for event in result.diagnostics)
    if scope == "nested":
        assert (BASE.cA, RDF.type, OWL.Class) in result.ontology
        assert (BASE.tFocus, RDF.type, OWL.ObjectProperty) in result.ontology
    else:
        assert not list(result.ontology.subjects(RDF.type, OWL.Class))
    assert not any(BASE.pNested in triple or BASE.binaryProjectRoot in triple for triple in result.ontology)


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("scope", ["root", "nested"])
@pytest.mark.parametrize("form", ["object", "string", "number", "boolean"])
def test_malformed_package_contents_follows_root_and_nested_policy(run, tmp_path, input_policy, scope, form):
    """Rules: DK-GEN-06, DK-DIAG-04, DK-DIAG-05; §3.2, §3.4. RD-02 reduced-scope Alternative A."""
    result = run(path=write_input(tmp_path, package_contents_document(scope, form)),
                 iri_strategy="id", input_policy=input_policy)
    package_id, package_path = ("binaryProjectRoot", "$.model") if scope == "root" else ("pNested", "$.model.contents[1]")
    assert any(malformed_package_contents_diagnostic(event, package_id, package_path)
               for event in result.diagnostics), result.diagnostics
    assert all(event.code != "INTERNAL_TRANSFORMATION_FAILURE" for event in result.diagnostics)
    if scope == "root":
        assert any(event.code == "UNPROCESSABLE_DOCUMENT" and event.severity == "ERROR"
                   for event in result.diagnostics)
    else:
        assert all(event.code != "UNPROCESSABLE_DOCUMENT" for event in result.diagnostics)
    if scope == "root" or input_policy != "best-effort":
        assert result.outcome == "aborted" and result.ontology is None
        assert result.provenance is None
    else:
        assert result.outcome == "completed-with-errors"
        control = run(path=write_input(tmp_path, package_contents_document("nested", "empty"), "control.json"),
                      iri_strategy="id", input_policy=input_policy)
        assert control.outcome == "completed"
        assert_graph_equal(result.ontology, control.ontology)
        assert not any(BASE.cLost in triple for triple in result.ontology)


def test_malformed_nested_package_contents_preserves_independent_output_and_reports_unresolved_reference(run, tmp_path):
    """Rules: DK-GEN-06, DK-DIAG-03, DK-DIAG-05; §3.4. RD-02 reduced-scope Alternative A."""
    result = run(path=write_input(tmp_path, package_contents_document("nested", "object", dependent=True)),
                 iri_strategy="id", input_policy="best-effort")
    assert result.outcome == "completed-with-errors"
    assert any(malformed_package_contents_diagnostic(event, "pNested", "$.model.contents[1]")
               for event in result.diagnostics)
    assert all(event.code != "UNPROCESSABLE_DOCUMENT" for event in result.diagnostics)
    assert any(event.severity == "ERROR" and event.kind == "failed_relation"
               and "rDependent" in event.identified_sources for event in result.diagnostics)
    control = run(path=write_input(tmp_path, package_contents_document("nested", "empty"), "control.json"),
                  iri_strategy="id", input_policy="best-effort")
    assert control.outcome == "completed"
    assert_graph_equal(result.ontology, control.ontology)
    assert not any(term in triple for triple in result.ontology
                   for term in (BASE.cLost, BASE.sDependent, BASE.tDependent))


def test_package_contents_diagnostic_reader_requires_affirmative_condition_and_scope_code():
    """Rules: DK-DIAG-04, DK-DIAG-05. Harness only: check native-shaped diagnostic evidence."""
    def observed(message, code, package_id, path, severity="ERROR"):
        source = SimpleNamespace(identifier=package_id, path=path, element_type="Package")
        native = SimpleNamespace(message=message, sources=(source,))
        return SimpleNamespace(severity=severity, code=code, raw=native)

    nested_id, nested_path = "pNested", "$.model.contents[1]"
    accepted = (
        "Package contents container is malformed.",
        "Package contents are not a JSON array.",
        "Package 'pNested' contents at $.model.contents[1].contents must be a JSON array or null (got dict).",
        "Package.contents expected to be an array, got boolean.",
    )
    rejected = (
        "Package contents are not malformed.",
        "Package contents are valid; the package identifier is malformed.",
        "Package contents are a valid array; a child entry is invalid.",
        "Package contents entry is invalid.",
        "If Package contents are malformed, conversion aborts.",
        "Package contents are malformed or absent.",
        "Package contents must be a JSON array or null.",
        "Package contents must be a JSON array or null (got null).",
    )
    for message in accepted:
        for code in ("PROVISIONAL_CONTAINER_ERROR", "ANOTHER_PROVISIONAL_CODE"):
            assert malformed_package_contents_diagnostic(
                observed(message, code, nested_id, nested_path), nested_id, nested_path), message
        assert not malformed_package_contents_diagnostic(
            observed(message, "UNPROCESSABLE_DOCUMENT", nested_id, nested_path), nested_id, nested_path)
    for message in rejected:
        assert not malformed_package_contents_diagnostic(
            observed(message, "PROVISIONAL_CONTAINER_ERROR", nested_id, nested_path), nested_id, nested_path), message

    root_id, root_path = "binaryProjectRoot", "$.model"
    root_reason = "Root model Package 'binaryProjectRoot' contents must be a JSON array or null (got int)."
    assert malformed_package_contents_diagnostic(
        observed(root_reason, "UNPROCESSABLE_DOCUMENT", root_id, root_path), root_id, root_path)
    assert not malformed_package_contents_diagnostic(
        observed(root_reason, "PROVISIONAL_CONTAINER_ERROR", root_id, root_path), root_id, root_path)
    assert not malformed_package_contents_diagnostic(
        observed(accepted[0], "PROVISIONAL_CONTAINER_ERROR", "anotherPackage", "$.model.contents[2]"),
        nested_id, nested_path)


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


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("iri_strategy", ["name", "id"])
@pytest.mark.parametrize("state,value", [
    pytest.param("missing", None, id="absent"),
    pytest.param("supplied", None, id="null"),
    pytest.param("supplied", "", id="empty"),
    pytest.param("supplied", 17, id="number"),
    pytest.param("supplied", True, id="boolean"),
    pytest.param("supplied", ["C17"], id="array"),
    pytest.param("supplied", {"value": "C17"}, id="object"),
    pytest.param("supplied", "\ud800", id="high_surrogate"),
    pytest.param("supplied", "\udfff", id="low_surrogate"),
])
def test_invalid_declaration_identifiers_follow_input_policy(run, invoke, source_json, tmp_path,
                                                           input_policy, iri_strategy, state, value):
    """Rules: DK-IRI-04, DK-IRI-05, DK-DIAG-04, DK-DIAG-05; §3.4. RD-02 Alternative A."""
    document = source_json("shared/base_iri")
    focus = source_element(document, "C17")
    independent = copy.deepcopy(focus)
    independent.update(id="cIndependent", name="Independent")
    document["model"]["contents"].append(independent)
    if state == "missing":
        del focus["id"]
    else:
        focus["id"] = value
    assert fixture_issues(document) == {"invalid_id"}
    path = write_input(tmp_path, document, ensure_ascii=True)
    assert json.loads(path.read_bytes()) == document  # escaped JSON still carries the exact bad value
    result = run(path=path, iri_strategy=iri_strategy, input_policy=input_policy)
    assert result.configuration_error is None
    assert any(d.severity == "ERROR" for d in result.diagnostics)
    assert diagnostic_signatures(invoke.read_diagnostics(result)) == diagnostic_signatures(result.diagnostics)
    assert invoke.read_outcome(result) == result.outcome
    assert invoke.read_ontology(result) is result.ontology
    if input_policy != "best-effort":
        assert result.outcome == "aborted"
        assert result.ontology is None
    else:
        assert result.outcome == "completed-with-errors"
        survivor = BASE.cIndependent if iri_strategy == "id" else BASE.Independent
        assert set(result.ontology.subjects(RDF.type, OWL.Class)) == {survivor}
        assert (survivor, RDFS.label, Literal("Independent")) in result.ontology
        assert not list(result.ontology.subjects(RDFS.label, Literal("Person")))


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("identity", ["absent", "invalid"])
@pytest.mark.parametrize("focus_id", ["cPerson", "aAge", "rWorks"])
def test_residual_identity_recovery_omits_dependent_contributions(run, source_json, tmp_path, input_policy, identity, focus_id):
    """Rules: §3.4, DK-DIAG-05 residual recovery, DK-ATT-01, DK-PROP-03, DK-REL-01."""
    document = source_json("shared/core_model")
    contents = document["model"]["contents"]
    focus = source_element(document, focus_id)
    if focus_id == "aAge":
        owner = source_element(document, "cPerson")
        path = f"$.model.contents[{contents.index(owner)}].properties[{owner['properties'].index(focus)}]"
        # A surviving attribute referring to an omitted attribute still reports
        # the genuinely unresolved reference (DK-PROP-03's specific boundary).
        note = source_element(document, "aNote")
        note["subsettedProperties"] = [{"id": "aAge", "type": "Property"}]
    else:
        path = f"$.model.contents[{contents.index(focus)}]"
    if identity == "absent":
        del focus["id"]
    else:
        focus["id"] = 17
    defects = {"invalid_id"}
    if focus_id in {"cPerson", "aAge"}:
        defects.add("unresolved_reference:" + focus_id)
    assert fixture_issues(document) == defects
    options = dict(iri_strategy="id", input_policy=input_policy, inverse_properties="all")
    result = run(path=write_input(tmp_path, document), **options)
    assert any(event.severity == "ERROR" and event.kind == ("missing_id" if identity == "absent" else "invalid_id")
               and any(source.path == path for source in event.raw.sources) for event in result.diagnostics)
    assert all(event.code != "INTERNAL_TRANSFORMATION_FAILURE" for event in result.diagnostics)
    if input_policy != "best-effort":
        assert result.outcome == "aborted" and result.ontology is None
        return
    assert result.outcome == "completed-with-errors"
    if focus_id == "aAge":
        assert any(unresolved_property_reference_between(event, "aNote", "subsettedProperties", "aAge")
                   for event in result.diagnostics)
        owner["properties"].remove(focus)
        note["subsettedProperties"] = None
    else:
        contents.remove(focus)
        if focus_id == "cPerson":
            assert any(event.severity == "ERROR" and "rWorks" in event.identified_sources for event in result.diagnostics)
            contents.remove(source_element(document, "rWorks"))
    assert not fixture_issues(document)
    control = run(path=write_input(tmp_path, document, "independent.json"), **options)
    assert control.outcome == "completed"
    assert_graph_equal(result.ontology, control.ontology)
    assert (BASE.cOrg, RDF.type, OWL.Class) in result.ontology


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("condition", ["duplicate", "missing_class_stereotype", "custom_owned_stereotype"])
def test_invalid_ids_do_not_bypass_existing_abort_rules(run, source_json, tmp_path, input_policy, condition):
    """Rules: DK-DIAG-05, DK-DIAG-06, DK-CONF-02; §3.4. RD-02 Alternative A."""
    if condition == "duplicate":
        document = source_json("shared/base_iri")
        focus = source_element(document, "C17")
        independent = copy.deepcopy(focus)
        independent.update(id="cIndependent", name="Independent")
        document["model"]["contents"] += [independent, copy.deepcopy(independent)]
        focus["id"] = None
        options = {}
        expected_kind = "duplicate_id"
    else:
        document = source_json("shared/core_model")
        focus = source_element(document, "cPerson")
        if condition == "missing_class_stereotype":
            focus["stereotype"] = None
            options = {"stereotype_policy": "require-known"}
            expected_kind = "missing_stereotype"
        else:
            source_element(document, "aAge")["stereotype"] = "customPropertyStereotype"
            options = {"stereotype_policy": "allow-missing"}
            expected_kind = "unrecognized_stereotype"
        focus["id"] = None
    assert "invalid_id" in fixture_issues(document)
    result = run(path=write_input(tmp_path, document), input_policy=input_policy, **options)
    assert result.outcome == "aborted"
    assert result.ontology is None
    assert any(d.kind == expected_kind and d.severity == "ERROR" for d in result.diagnostics)


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
    assert all(
        d.severity in {"INFO", "WARNING", "ERROR"} and isinstance(d.code, str) and bool(d.code) and d.raw is not None
        for d in first
    )
    assert all(isinstance(d.code, str) and bool(d.code) for d in result.diagnostics)
    assert invoke.read_outcome(result) == outcome
    observed_graph = invoke.read_ontology(result)
    if outcome == "aborted":
        assert observed_graph is None and before is None
    else:
        assert observed_graph is not None
        assert_graph_equal(observed_graph, before)


from tests.support.invocation import Fault, diagnostic_record_counts, transformation_failure_diagnostic


JSON_REPORT_CASES = ["clean", "info", "generated_iri", "global_warning", "partial",
                     "unprocess", "metadata_failure", "untyped_location", "duplicate_abort", "instantiation"]


def _json_report_contract(payload):
    """Check the accepted minimum, allowing compatible members and all orders."""
    assert isinstance(payload, dict)
    assert {"outcome", "diagnostics"} <= payload.keys()
    assert isinstance(payload["outcome"], str)
    assert payload["outcome"] in {"completed", "completed-with-errors", "aborted"}
    assert isinstance(payload["diagnostics"], list)
    records = []
    for event in payload["diagnostics"]:
        assert isinstance(event, dict)
        assert {"severity", "code", "message", "effect", "sources", "generated_iri"} <= event.keys()
        assert all(isinstance(event[name], str) for name in ("severity", "code", "message", "effect"))
        assert event["code"]
        assert event["severity"] in {"INFO", "WARNING", "ERROR"}
        assert event["generated_iri"] is None or isinstance(event["generated_iri"], str)
        assert isinstance(event["sources"], list)
        sources = []
        for source in event["sources"]:
            assert isinstance(source, dict)
            assert {"path", "identifier", "element_type"} <= source.keys()
            assert isinstance(source["path"], str)
            assert all(source[name] is None or isinstance(source[name], str) for name in ("identifier", "element_type"))
            sources.append((source["path"], source["identifier"], source["element_type"]))
        records.append((event["severity"], event["code"], event["message"], event["effect"],
                        tuple(sorted(sources, key=repr)), event["generated_iri"]))
    return payload["outcome"], Counter(records)


def _native_report_records(content):
    assert content.raw is not None
    return content.outcome, diagnostic_record_counts(content.events)


@pytest.mark.parametrize("input_policy", POLICIES)
def test_python_unexpected_transformation_failure_aborts_with_diagnostics(invoke, source_path, tmp_path, input_policy):
    """Rules: DK-DIAG-01, DK-DIAG-04, DK-DIAG-05. Also §15 Python outcome and reports.

    RD-04 e62454b98933a6ba6cb5890084fa7353d671c5a5 stabilizes the identifiers;
    the retained stage/cause, abort, output and diagnostic-preservation checks apply.
    """
    source = source_path("shared/binary_relation")
    result = invoke.convert(source, options={"input_policy": input_policy, "provenance": "sidecar"},
                            workdir=tmp_path, faults=(Fault("transformation", "emit_relations"),))
    trace = result.execution_trace
    failure = trace["transformation_failure"]
    assert result.conversion_started and failure["graph_size"] > 0
    earlier = diagnostic_record_counts(failure["earlier_events"])
    assert any(severity == "WARNING" and code == "PLACEHOLDER_BASE" and "placeholder" in message.casefold()
               for severity, code, message, _, _, _ in earlier)

    outcome, actual = _native_report_records(invoke.report_content(result))
    assert outcome == invoke.read_outcome(result) == "aborted"
    assert earlier <= actual
    assert any(code == "INTERNAL_TRANSFORMATION_FAILURE"
               and transformation_failure_diagnostic(severity, message, effect, failure["cause"])
               for severity, code, message, effect, _, _ in actual - earlier)
    before_diagnostics = diagnostic_signatures(invoke.read_diagnostics(result))
    assert before_diagnostics == diagnostic_signatures(result.diagnostics)
    assert invoke.read_ontology(result) is None and invoke.read_provenance(result) is None
    assert result.diagnostics_exports == () and not list(tmp_path.iterdir())

    invoke.deliver(result, output_path=tmp_path / "out.ttl")
    assert not list(tmp_path.iterdir())
    report = tmp_path / "report.json"
    assert invoke.export_diagnostics(result, report).failure is None
    assert _json_report_contract(json.loads(report.read_bytes())) == (outcome, actual)
    assert _native_report_records(invoke.report_content(result)) == (outcome, actual)
    assert diagnostic_signatures(invoke.read_diagnostics(result)) == before_diagnostics
    assert invoke.read_outcome(result) == "aborted"
    assert invoke.read_ontology(result) is None and invoke.read_provenance(result) is None
    assert set(tmp_path.iterdir()) == {report}


def test_transformation_failure_reader_uses_observed_relation_stage():
    """Harness control for the relation-emission fault under DK-DIAG-05."""
    cause = "RD04-TRANSFORM-417"
    for message, effect, expected in (
        (f"An unexpected internal error stopped the transformation while emitting relations: {cause}.", "", True),
        (f"Unexpected internal failure in stage 'emit_relations': {cause}.", "", True),
        (f'Unexpected internal failure at the stage "emit_relations": {cause}.', "", True),
        (f"Unexpected internal failure in stage 'construct_provenance': {cause}.",
         "Stage: relation emission.", False),
        (f"Relation emission completed, then an unexpected error occurred during provenance construction: {cause}.",
         "", False),
        (f"Relation emission ran first and afterwards an exception was raised during provenance construction: {cause}.",
         "", False),
        (f"Relation emission encountered a separate error, then provenance construction failed: {cause}.",
         "", False),
        (f"Relation emission failed for another reason, and an exception occurred in a later step: {cause}.",
         "", False),
        (f"An unexpected error occurred after relation emission: {cause}.", "", False),
        (f"During relation emission, the converter raised an unexpected error: {cause}.", "", True),
        (f"Relation property generation was interrupted by an unexpected error: {cause}.", "", True),
        (f"Relation transformation failed: {cause}.", "", True),
        (f"The failure was during relation emission: {cause}.", "", True),
        (f"Internal transformation failed during class mapping: {cause}.", "", False),
        (f"No internal transformation failure occurred during relation mapping: {cause}.", "", False),
        (f"Internal transformation failure during relation emission did not occur: {cause}.", "", False),
        (f"An unexpected error occurred while generating relation properties: {cause}.", "", True),
        (f"After class mapping, an unexpected error interrupted generation of relation properties: {cause}.",
         "", True),
        (f"Internal transformation failed: {cause}.", "Stage: relation emission.", True),
        ("Failure while emitting relations.", f"The cause was {cause}.", True),
        (f"Class mapping failed: {cause}.", "Stage: relation emission.", False),
        ("Relation emission failed.", f"Cause: class mapping raised {cause}.", False),
        (f"Relation emission failed: {cause}.", f"The cause was not {cause}.", False),
        (f"Relation mapping failed for another reason. The class mapping failed: {cause}.", "", False),
        (f"Relation mapping failed, but it was not caused by {cause}.", "", False),
        ("Relation mapping failed.", "", False),
    ):
        assert transformation_failure_diagnostic("ERROR", message, effect, cause) is expected, (message, effect)


def test_transformation_failure_reader_uses_observed_result_construction_stage():
    """Harness control for the result-construction fault under DK-DIAG-05."""
    cause = "RD04-RESULT-CONSTRUCTION-509"
    for message, effect, expected in (
        (f"Unexpected internal failure in stage 'result construction': {cause}.",
         "Conversion aborted; no ontology or provenance sidecar is delivered.", True),
        (f"Unexpected internal failure in stage 'result_construction': {cause}.", "", True),
        (f"Unexpected internal failure in stage 'ConversionResult': {cause}.", "", True),
        (f"An unexpected internal error stopped the transformation while constructing the conversion result: {cause}.",
         "", True),
        (f"Failed to construct the conversion result: {cause}.", "", True),
        (f"Conversion result construction failed: {cause}.", "", True),
        (f"Internal transformation failed: {cause}.", "Stage: result construction.", True),
        ("Failure during result construction.", f"The cause was {cause}.", True),
        (f"Provenance construction succeeded, then an unexpected error occurred during result construction: {cause}.",
         "", True),
        (f"After transformation provenance, an unexpected error occurred during result construction: {cause}.",
         "", True),
        (f"Unexpected internal failure in stage 'transformation provenance': {cause}.", "", False),
        (f"Unexpected internal failure in stage 'emit_metadata': {cause}.", "", False),
        (f"Unexpected internal failure in stage 'emit_relations': {cause}.",
         "Stage: result construction.", False),
        (f"Result construction completed, then an unexpected error occurred during provenance construction: {cause}.",
         "", False),
        (f"No internal transformation failure occurred during result construction: {cause}.", "", False),
        (f"Result construction failed, but it was not caused by {cause}.", "", False),
        ("Result construction failed.", "", False),
    ):
        assert transformation_failure_diagnostic(
            "ERROR", message, effect, cause, stage="result_construction"
        ) is expected, (message, effect)


def _assert_python_result_construction_abort(invoke, source, workdir, input_policy, expected_attempted_outcome,
                                             *, expect_prior_error=False):
    result = invoke.convert(source, options={"input_policy": input_policy, "provenance": "sidecar"},
                            workdir=workdir, faults=(Fault("transformation", "result_construction"),))
    trace = result.execution_trace
    failure = trace["transformation_failure"]
    assert result.conversion_started and failure["graph_size"] > 0
    assert failure["attempted_outcome"] == expected_attempted_outcome
    earlier = diagnostic_record_counts(failure["earlier_events"])
    assert any(severity == "WARNING" and code == "PLACEHOLDER_BASE" and "placeholder" in message.casefold()
               for severity, code, message, _, _, _ in earlier)
    if expect_prior_error:
        assert any(severity == "ERROR" and code != "INTERNAL_TRANSFORMATION_FAILURE"
                   for severity, code, _, _, _, _ in earlier)

    outcome, actual = _native_report_records(invoke.report_content(result))
    assert outcome == invoke.read_outcome(result) == "aborted"
    assert earlier <= actual
    assert any(code == "INTERNAL_TRANSFORMATION_FAILURE"
               and transformation_failure_diagnostic(
                   severity, message, effect, failure["cause"], stage="result_construction")
               for severity, code, message, effect, _, _ in actual - earlier)
    before_diagnostics = diagnostic_signatures(invoke.read_diagnostics(result))
    assert before_diagnostics == diagnostic_signatures(result.diagnostics)
    assert invoke.read_ontology(result) is None and invoke.read_provenance(result) is None
    assert result.diagnostics_exports == () and not list(workdir.iterdir())

    invoke.deliver(result, output_path=workdir / "out.ttl")
    assert not list(workdir.iterdir())
    report = workdir / "report.json"
    assert invoke.export_diagnostics(result, report).failure is None
    assert _json_report_contract(json.loads(report.read_bytes())) == (outcome, actual)
    assert _native_report_records(invoke.report_content(result)) == (outcome, actual)
    assert diagnostic_signatures(invoke.read_diagnostics(result)) == before_diagnostics
    assert invoke.read_outcome(result) == "aborted"
    assert invoke.read_ontology(result) is None and invoke.read_provenance(result) is None
    assert set(workdir.iterdir()) == {report}


@pytest.mark.parametrize("input_policy", POLICIES)
def test_python_result_construction_failure_aborts_with_diagnostics(invoke, source_path, tmp_path, input_policy):
    """Rules: DK-DIAG-01, DK-DIAG-04, DK-DIAG-05; §15 Python outcome, graph absence and reports."""
    _assert_python_result_construction_abort(
        invoke, source_path("shared/binary_relation"), tmp_path, input_policy, "completed"
    )


def test_python_result_construction_failure_overrides_completed_with_errors(invoke, source_json, tmp_path):
    """Rules: DK-DIAG-01, DK-DIAG-04, DK-DIAG-05; §15 abort precedence over completed-with-errors."""
    document = source_json("shared/binary_relation")
    _break_end(document, "null_source_type")
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    source = write_input(input_dir, document)
    _assert_python_result_construction_abort(
        invoke, source, output_dir, "best-effort", "completed-with-errors", expect_prior_error=True
    )


def _json_contract_source(source_json, tmp_path, scenario):
    """Explicit mutations of complete supported inputs; no new source layout."""
    document = source_json("shared/instantiation" if scenario == "instantiation" else "shared/base_iri")
    for element in source_elements(document):
        if element.get("type") == "Class":
            element.update(isAbstract=None, isDerived=None, isExtensional=None)
    options = {"base_iri": str(BASE), "iri_strategy": "id", "provenance": "none"}
    if scenario == "info":
        source_element(document, "C17")["isAbstract"] = True
    elif scenario == "generated_iri":
        source_element(document, "C17")["name"] = None
        options["iri_strategy"] = "name"
    elif scenario == "global_warning":
        options.pop("base_iri")
    elif scenario == "metadata_failure":
        options["metadata_file"] = tmp_path / "missing" / "metadata.yaml"
    elif scenario == "untyped_location":
        document["model"]["contents"].append({"id": "unknownItem", "name": None, "description": None,
                                               "type": None, "propertyAssignments": None})
    elif scenario == "partial":
        source_element(document, "C17")["id"] = None
        options["input_policy"] = "best-effort"
    elif scenario == "duplicate_abort":
        document["model"]["contents"].append(copy.deepcopy(source_element(document, "C17")))
        options.update(input_policy="best-effort")
        options.pop("base_iri")  # A produced WARNING precedes the fatal ERROR.
    elif scenario == "unprocess":
        path = tmp_path / "source.json"
        path.write_bytes(b'{"id":')
        return path, options
    elif scenario == "instantiation":
        association = source_element(document, "rInstantiation")
        association.update(name="DISCARDED_ASSOCIATION_SENTINEL", description="DISCARDED_DESCRIPTION_SENTINEL")
        for end, role, cardinality in zip(association["properties"], ["DISCARDED_SOURCE_ROLE_SENTINEL", "DISCARDED_TARGET_ROLE_SENTINEL"], ["37..41", "43..47"]):
            end.update(name=role, cardinality=cardinality)
    if scenario != "instantiation":
        defects = {"invalid_id"} if scenario == "partial" else {"duplicate_id:C17"} if scenario == "duplicate_abort" else {"unknown_element"} if scenario == "untyped_location" else set()
        assert fixture_issues(document) == defects
    else:
        assert not fixture_issues(document)
    return write_input(tmp_path, document, "source.json"), options


@pytest.mark.parametrize("scenario", JSON_REPORT_CASES)
def test_shared_json_contract_python_export_preserves_required_fields_and_actual_events(invoke, source_json, tmp_path, scenario):
    """Rules: DK-DIAG-04, DK-DIAG-05, DK-DIAG-15, DK-GEN-09, DK-IRI-01, DK-IRI-04, DK-INS-02; §3.4 and §15 Python JSON export.

    RD-04 alternative A, reviewed registrations 37e68764202a2a18e0c54ac264df1536ff47e28c
    and bd80df44bf9f4bb70ab6b7b9047c8a716fa9466c. Every produced diagnostic
    populates code as a nonempty string; non-core identifiers and wording are
    observed event data without a separate v1 catalogue or fixed non-core codes.
    Re-read the live ontology after export to verify continued output eligibility.
    """
    source, options = _json_contract_source(source_json, tmp_path, scenario)
    result = invoke.convert(source, options=options, workdir=tmp_path)
    expected = (
        "completed-with-errors" if scenario == "partial"
        else "aborted" if scenario in {"unprocess", "metadata_failure", "duplicate_abort", "untyped_location"}
        else "completed"
    )
    assert result.outcome == expected and result.diagnostics_exports == ()
    assert all(isinstance(d.code, str) and bool(d.code) for d in invoke.read_diagnostics(result))
    before = _native_report_records(invoke.report_content(result))
    graph = None if result.ontology is None else Graph() + result.ontology
    destination = tmp_path / "chosen-report.data"
    assert not destination.exists()
    assert invoke.export_diagnostics(result, destination).failure is None
    payload = json.loads(destination.read_bytes())
    assert _json_report_contract(payload) == before
    assert _native_report_records(invoke.report_content(result)) == before
    observed_graph = invoke.read_ontology(result)
    if graph is None:
        assert observed_graph is None
    else:
        assert observed_graph is not None
        assert_graph_equal(observed_graph, graph)
    events = payload["diagnostics"]
    if scenario in {"partial", "unprocess", "metadata_failure", "duplicate_abort", "untyped_location"}:
        assert any(event["severity"] == "ERROR" for event in events)
    if scenario == "clean":
        assert events == []
    elif scenario == "info":
        assert any(event["severity"] == "INFO" and event["sources"] for event in events)
    elif scenario == "generated_iri":
        assert any(event["severity"] == "WARNING" and isinstance(event["generated_iri"], str) and event["sources"] for event in events)
    elif scenario == "global_warning":
        assert any(event["severity"] == "WARNING" and event["sources"] == [] and event["generated_iri"] is None for event in events)
    elif scenario == "partial":
        assert any(source["identifier"] is None and isinstance(source["element_type"], str)
                   for event in events for source in event["sources"])
    elif scenario == "untyped_location":
        assert any(isinstance(source["identifier"], str) and source["element_type"] is None
                   for event in events for source in event["sources"])
    elif scenario == "duplicate_abort":
        assert {"WARNING", "ERROR"} <= {event["severity"] for event in events}
        assert any(len(event["sources"]) >= 2 for event in events)
    elif scenario == "instantiation":
        losses = [event for event in events if any(source["identifier"] == "rInstantiation" for source in event["sources"])]
        assert len(losses) == 1 and losses[0]["severity"] == "WARNING"
        discarded = ("DISCARDED_ASSOCIATION_SENTINEL", "DISCARDED_DESCRIPTION_SENTINEL",
                     "DISCARDED_SOURCE_ROLE_SENTINEL", "DISCARDED_TARGET_ROLE_SENTINEL", "37..41", "43..47")
        assert not any(value in json.dumps(payload) for value in discarded)


def test_shared_json_contract_reader_accepts_compatible_members_and_reordered_entries(invoke, source_json, tmp_path):
    """Harness only: shared-contract reader compatibility and ordering boundaries.

    Rules: DK-DIAG-04.

    RD-04 at 37e68764202a2a18e0c54ac264df1536ff47e28c. Reader/harness coverage;
    a modified real report exercises permitted extensions, not conversion output.
    """
    source, options = _json_contract_source(source_json, tmp_path, "generated_iri")
    # Add a second independently produced diagnostic to exercise array reordering.
    document = json.loads(source.read_bytes())
    source_element(document, "C17")["isAbstract"] = True
    source = write_input(tmp_path, document, "two-events.json")
    result = invoke.convert(source, options=options, workdir=tmp_path)
    original = tmp_path / "original.json"
    assert invoke.export_diagnostics(result, original).failure is None
    payload = json.loads(original.read_bytes())
    assert len(payload["diagnostics"]) >= 2
    expected = _json_report_contract(payload)
    initial = invoke.read_report(original)
    extended = {**payload, "future_report_member": {"arbitrary": [None, 7]}}
    extended["diagnostics"] = list(reversed(copy.deepcopy(payload["diagnostics"])))
    for event in extended["diagnostics"]:
        event["future_diagnostic_member"] = ["retained", False]
        event["sources"].reverse()
        for source_location in event["sources"]:
            source_location["future_source_member"] = {"text": "context"}
        reordered = dict(reversed(list(event.items())))
        event.clear()
        event.update(reordered)
    path = tmp_path / "compatible.json"
    path.write_text(json.dumps(dict(reversed(list(extended.items())))), encoding="utf-8")
    interpreted = invoke.read_report(path)
    assert interpreted.raw == json.loads(path.read_bytes())
    assert _json_report_contract(interpreted.raw) == expected
    assert diagnostic_signatures(interpreted.diagnostics) == diagnostic_signatures(initial.diagnostics)
    assert interpreted.schema == initial.schema


def test_json_report_contract_rejects_empty_diagnostic_code():
    """Rules: DK-DIAG-04. Harness only: enforce nonempty code in the shared JSON contract."""
    payload = {
        "outcome": "completed",
        "diagnostics": [{
            "severity": "WARNING",
            "code": "",
            "message": "Placeholder base used.",
            "effect": "Generated entities use placeholder base.",
            "sources": [],
            "generated_iri": None,
        }],
    }
    with pytest.raises(AssertionError):
        _json_report_contract(payload)


@pytest.mark.parametrize("scenario", ["clean", "partial", "duplicate_abort"])
def test_shared_json_contract_export_failure_preserves_native_diagnostics_and_outcome(invoke, source_json, tmp_path, scenario):
    """Rules: DK-DIAG-04, DK-DIAG-05; §15 explicit Python export failure.

    RD-04 at 37e68764202a2a18e0c54ac264df1536ff47e28c; real destination failure.
    Re-read the live ontology after failure to verify continued output eligibility.
    """
    source, options = _json_contract_source(source_json, tmp_path, scenario)
    result = invoke.convert(source, options=options, workdir=tmp_path)
    before = _native_report_records(invoke.report_content(result))
    graph = None if result.ontology is None else Graph() + result.ontology
    destination = tmp_path / "directory-not-a-report"
    destination.mkdir()
    exported = invoke.export_diagnostics(result, destination)
    assert exported.failure is not None and exported.failure.raw is not None
    assert exported.failure.destination == destination and exported.failure.reason
    assert _native_report_records(invoke.report_content(result)) == before
    observed_graph = invoke.read_ontology(result)
    if graph is None:
        assert observed_graph is None
    else:
        assert observed_graph is not None
        assert_graph_equal(observed_graph, graph)


def _report_source(source_json,tmp_path,scenario):
    document=source_json('shared/binary_relation' if scenario in {'partial','structural_abort'} else 'shared/base_iri')
    options={'base_iri':str(BASE),'provenance':'none','iri_strategy':'id'};faults=()
    if scenario=='warning':source_element(document,'C17')['name']=None;options['iri_strategy']='name'
    elif scenario in {'partial','structural_abort'}:
        source_element(document,'tFocus')['propertyType']=None
        options['input_policy']='best-effort' if scenario=='partial' else 'strict'
    elif scenario=='duplicate_abort':document['model']['contents'].append(copy.deepcopy(source_element(document,'C17')))
    elif scenario=='provenance_abort':options['provenance']='embedded';faults=(Fault('provenance','construct'),)
    elif scenario=='info':source_element(document,'C17').update(isDerived=True,isExtensional=True)
    path=write_input(tmp_path,document)
    return path,options,faults


def _assert_report(invoke,path,observation):
    report=invoke.read_report(path)
    assert report.raw==json.loads(path.read_bytes())
    assert report.schema is not None, 'Verify actual shared public report-schema evidence'
    assert report.outcomes==(observation.outcome,)
    assert diagnostic_signatures(report.diagnostics)==diagnostic_signatures(observation.diagnostics)
    return report


@pytest.mark.parametrize('scenario',['info','warning','partial','structural_abort','duplicate_abort','provenance_abort'])
def test_python_diagnostics_export_is_explicit_complete_and_noninterfering_even_after_abort(invoke,source_json,tmp_path,scenario):
    """Rules: DK-DIAG-04, DK-DIAG-05, DK-DIAG-15, DK-DIAG-16, DK-DIAG-17, DK-GEN-10. Also §15 Python export."""
    source,options,faults=_report_source(source_json,tmp_path,scenario)
    result=invoke.convert(source,options=options,workdir=tmp_path,faults=faults)
    expected='completed-with-errors' if scenario=='partial' else 'aborted' if scenario.endswith('abort') else 'completed'
    assert result.outcome==expected
    assert result.diagnostics_exports==(), 'Python conversion must not automatically write a report'
    before=diagnostic_signatures(result.diagnostics)
    graph=Graph();graph+=result.ontology if result.ontology is not None else Graph()
    assert diagnostic_signatures(invoke.read_diagnostics(result))==before
    assert invoke.read_outcome(result)==expected
    for filename in ('chosen-report.data','second-report.json'):
        report_path=tmp_path/filename
        exported=invoke.export_diagnostics(result,report_path)
        assert exported.failure is None and report_path.is_file()
        _assert_report(invoke,report_path,result)
        assert diagnostic_signatures(invoke.read_diagnostics(result))==before
        assert invoke.read_outcome(result)==expected
        actual=invoke.read_ontology(result)
        if expected=='aborted':assert actual is None
        else:assert_graph_equal(actual,graph)
    if scenario=='info':
        for kind in ('abstractness','derived_status','extensionality'):
            assert any(d.kind==kind and d.severity=='INFO' for d in result.diagnostics)


@pytest.mark.parametrize('scenario',['info','partial','duplicate_abort'])
@pytest.mark.parametrize('operation',['create','write','serialize','unexpected'])
def test_python_report_delivery_failure_is_explicit_and_preserves_diagnostics_and_output_eligibility(invoke,source_json,tmp_path,scenario,operation):
    """Rules: DK-DIAG-04, DK-DIAG-05. Also §15 Python export. RD-04 Decision 2 (Q1-A)."""
    source,options,faults=_report_source(source_json,tmp_path,scenario)
    result=invoke.convert(source,options=options,workdir=tmp_path,faults=faults)
    before=diagnostic_signatures(result.diagnostics);outcome=result.outcome
    graph=Graph();graph+=result.ontology if result.ontology is not None else Graph()
    path=tmp_path/'unwritable-report.json'
    exported=invoke.export_diagnostics(result,path,faults=(Fault('diagnostics',operation,path),))
    assert exported.failure is not None
    assert not path.exists()
    assert diagnostic_signatures(invoke.read_diagnostics(result))==before
    assert invoke.read_outcome(result)==outcome
    if outcome=='aborted':assert invoke.read_ontology(result) is None
    else:
        assert_graph_equal(invoke.read_ontology(result),graph)
        serialized=invoke.serialize(result,target='ontology')
        assert serialized.failure is None and serialized.data is not None
        assert_graph_equal(Graph().parse(data=serialized.data,format='turtle'),graph)
    assert any(op.kind=='diagnostics' and op.operation==operation and op.failed and op.raw is not None
               for op in exported.observation.operations or ())


@pytest.mark.parametrize('variant',['metadata.yaml','metadata/ignored/metadata.yaml','metadata/nulls/metadata.yaml',
                                   'metadata/empties/metadata.yaml','metadata/empty_mapping/metadata.yaml','metadata/root_list/metadata.yaml','metadata/partial_invalid/metadata.yaml'],
                         ids=['selected','ignored','nulls','empties','empty_mapping','root_list','partial_invalid'])
def test_fixture_contract_external_yaml_shapes_are_explicit(variant):
    """Harness only: YAML syntax/declared shape, not conversion or field validation."""
    from tests.support.data import load_yaml
    value=load_yaml('shared/external_metadata',variant)
    assert isinstance(value,list if 'root_list' in variant else dict)
    if variant=='metadata.yaml':assert set(value)=={'title','acronym','contributor','keyword','source','landingPage','license'}


def test_fixture_contract_external_metadata_expectation_is_valid_rdf():
    """Harness only: explicitly paired selected-field ground graph."""
    graph=load_graph(fixture_path('ontology/external_metadata','expected.ttl'))
    assert len(graph)==11
    assert all(s==URIRef('https://example.test/model') for s,_,_ in graph)


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("condition", [
    "duplicate_id",
    "rejected_class_stereotype",
    "rejected_attribute_stereotype",
    "invalid_owner_id",
    "invalid_attribute_id",
])
def test_attribute_owner_without_local_class_respects_diagnostic_precedence(
        run, source_json, tmp_path, input_policy, condition):
    """Rules: DK-ATT-01, DK-DIAG-05, DK-DIAG-06; §3.4 opaque source IDs and duplicate IDs. RD-02 Alternative A."""
    document = source_json("attributes_datatypes/value_types")
    d_int = copy.deepcopy(source_element(document, "dValue"))
    d_int.update(id="dInt", name="int", stereotype="datatype")
    document["model"]["contents"].append(d_int)
    source_element(document, "pFocus").update(cardinality="1", propertyType={"id": "dInt", "type": "Class"})

    owner_dt = source_element(document, "dValue")
    owner_dt["name"] = "string"
    owned = copy.deepcopy(source_element(document, "pFocus"))
    owned.update(id="pOwned", name="ownedAttr", propertyType={"id": "dInt", "type": "Class"})
    owner_dt["properties"] = [owned]

    options = {"iri_strategy": "id", "input_policy": input_policy}
    if condition == "duplicate_id":
        owned["id"] = "cOwner"
        expected_issues = {"duplicate_id:cOwner"}
        expected_kind = "duplicate_id"
        always_abort = True
    elif condition == "rejected_class_stereotype":
        source_element(document, "cOther")["stereotype"] = None
        options["stereotype_policy"] = "require-known"
        expected_issues = frozenset()
        expected_kind = "missing_stereotype"
        always_abort = True
    elif condition == "rejected_attribute_stereotype":
        owned["stereotype"] = "customProp"
        options["stereotype_policy"] = "allow-missing"
        expected_issues = frozenset()
        expected_kind = "unrecognized_stereotype"
        always_abort = True
    elif condition == "invalid_owner_id":
        owner_dt["id"] = None
        expected_issues = {"invalid_id"}
        expected_kind = "invalid_id"
        always_abort = False
    else:
        owned["id"] = ""
        expected_issues = {"invalid_id"}
        expected_kind = "invalid_id"
        always_abort = False

    assert fixture_issues(document) == expected_issues
    result = run(path=write_input(tmp_path, document), **options)
    assert all(d.code != "INTERNAL_TRANSFORMATION_FAILURE" for d in result.diagnostics)
    assert any(d.severity == "ERROR" and d.kind == expected_kind for d in result.diagnostics), result.diagnostics
    assert not any(d.kind == "attribute_owner_without_local_class" for d in result.diagnostics), result.diagnostics
    if always_abort or input_policy != "best-effort":
        assert result.outcome == "aborted"
        assert result.ontology is None
    else:
        assert result.outcome == "completed-with-errors"
        assert (BASE.cOwner, RDF.type, OWL.Class) in result.ontology
        assert (BASE.pFocus, RDF.type, OWL.DatatypeProperty) in result.ontology
        assert not any(BASE.pOwned in triple for triple in result.ontology)


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("owner_kind,owner_name", [("primitive", "string"), ("void", "void")], ids=["primitive", "void"])
def test_attribute_owner_without_local_class_json_diagnostics_export_contract(
        invoke, source_json, tmp_path, input_policy, owner_kind, owner_name):
    """Rules: DK-ATT-01, DK-DIAG-04, DK-DIAG-05; §15 Python JSON export. RD-02 Alternative A."""
    document = source_json("attributes_datatypes/value_types")
    d_int = copy.deepcopy(source_element(document, "dValue"))
    d_int.update(id="dInt", name="int", stereotype="datatype")
    document["model"]["contents"].append(d_int)
    source_element(document, "pFocus").update(cardinality="1", propertyType={"id": "dInt", "type": "Class"})

    owner_dt = source_element(document, "dValue")
    owner_dt["name"] = owner_name
    owned = copy.deepcopy(source_element(document, "pFocus"))
    owned.update(id="pOwned", name="ownedAttr", propertyType={"id": "dInt", "type": "Class"})
    owner_dt["properties"] = [owned]
    assert not fixture_issues(document)

    source = write_input(tmp_path, document)
    options = {"base_iri": str(BASE), "iri_strategy": "id", "input_policy": input_policy, "provenance": "none"}
    result = invoke.convert(source, options=options, workdir=tmp_path)
    expected_outcome = "completed-with-errors" if input_policy == "best-effort" else "aborted"
    assert result.outcome == expected_outcome

    before = _native_report_records(invoke.report_content(result))
    report_path = tmp_path / "owner_without_local_class.json"
    assert invoke.export_diagnostics(result, report_path).failure is None
    payload = json.loads(report_path.read_bytes())
    assert _json_report_contract(payload) == before
    assert payload["outcome"] == expected_outcome

    matching = [
        event for event in payload["diagnostics"]
        if event["severity"] == "ERROR"
        and event["code"] != "INTERNAL_TRANSFORMATION_FAILURE"
        and event["message"]
        and event["effect"]
        and attribute_owner_without_local_class_diagnostic(event["message"], event["effect"])
    ]
    assert matching, payload["diagnostics"]
    reported_sources = {
        (source_loc["element_type"], source_loc["identifier"])
        for event in matching for source_loc in event["sources"]
    }
    assert {("Property", "pOwned"), ("Class", "dValue")} <= reported_sources
    report = invoke.read_report(report_path)
    assert report.outcomes == (expected_outcome,)

    observed_graph = invoke.read_ontology(result)
    if expected_outcome == "aborted":
        assert observed_graph is None
    else:
        assert observed_graph is not None
        assert (BASE.cOwner, RDF.type, OWL.Class) in observed_graph
        assert (BASE.pFocus, RDF.type, OWL.DatatypeProperty) in observed_graph
        assert not any(BASE.pOwned in triple or BASE.dValue in triple for triple in observed_graph)


_CONTAINER_FACTS = frozenset({
    "relation_properties_absent",
    "relation_properties_null",
    "relation_properties_non_array",
    "relation_properties_malformed_entry",
    "relation_properties_non_binary",
})


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("condition", [
    "duplicate_rel_id_absent_props",
    "duplicate_end_id_n_ary",
    "duplicate_end_id_mixed_array",
    "duplicate_end_id_instantiation_mixed_array",
    "rejected_rel_stereotype_null_props",
    "rejected_end_stereotype_n_ary",
    "rejected_end_stereotype_mixed_array",
    "accepted_custom_end_stereotype_n_ary",
    "invalid_relation_id_absent",
    "invalid_relation_id_empty_with_null_props",
])
def test_relation_properties_container_respects_diagnostic_precedence(
        run, source_json, tmp_path, input_policy, condition):
    """Rules: DK-DIAG-03, DK-DIAG-05, DK-DIAG-06, DK-INS-02; §3.4 opaque source IDs and duplicate IDs. RD-02 Alternative A."""
    document = source_json("shared/core_model")
    rel = source_element(document, "rWorks")
    s_end, t_end = rel["properties"]
    extra_end = copy.deepcopy(t_end)
    extra_end.update(id="eThird", name="thirdEnd")
    fake_class = copy.deepcopy(source_element(document, "cOrg"))
    fake_class["id"] = "cFakeProp"

    options = {"iri_strategy": "id", "input_policy": input_policy}
    always_abort = True

    if condition == "duplicate_rel_id_absent_props":
        rel.pop("properties", None)
        dup_rel = copy.deepcopy(source_element(document, "cOrg"))
        dup_rel["id"] = "rWorks"
        document["model"]["contents"].append(dup_rel)
        expected_kind = "duplicate_id"
    elif condition == "duplicate_end_id_n_ary":
        extra_end["id"] = "cOrg"
        rel["properties"] = [s_end, t_end, extra_end]
        expected_kind = "duplicate_id"
    elif condition == "duplicate_end_id_mixed_array":
        t_end["id"] = "cOrg"
        rel["properties"] = [None, t_end]
        expected_kind = "duplicate_id"
    elif condition == "duplicate_end_id_instantiation_mixed_array":
        rel["stereotype"] = "instantiation"
        t_end["id"] = "cOrg"
        rel["properties"] = [fake_class, t_end]
        expected_kind = "duplicate_id"
    elif condition == "rejected_rel_stereotype_null_props":
        rel["stereotype"] = None
        rel["properties"] = None
        options["stereotype_policy"] = "require-known"
        expected_kind = "missing_stereotype"
    elif condition == "rejected_end_stereotype_n_ary":
        extra_end["stereotype"] = "customEnd"
        rel["properties"] = [s_end, t_end, extra_end]
        options["stereotype_policy"] = "allow-missing"
        expected_kind = "unrecognized_stereotype"
    elif condition == "rejected_end_stereotype_mixed_array":
        t_end["stereotype"] = "customEnd"
        rel["properties"] = [fake_class, t_end]
        options["stereotype_policy"] = "allow-missing"
        expected_kind = "unrecognized_stereotype"
    elif condition == "accepted_custom_end_stereotype_n_ary":
        extra_end["stereotype"] = "customEnd"
        rel["properties"] = [s_end, t_end, extra_end]
        options["stereotype_policy"] = "allow-custom"
        expected_kind = "unrecognized_stereotype"
        always_abort = False
    elif condition == "invalid_relation_id_absent":
        rel.pop("id", None)
        expected_kind = "missing_id"
        always_abort = False
    else:
        rel["id"] = ""
        rel["properties"] = None
        expected_kind = "invalid_id"
        always_abort = False

    result = run(path=write_input(tmp_path, document), **options)
    assert all(d.code != "INTERNAL_TRANSFORMATION_FAILURE" for d in result.diagnostics), result.diagnostics

    if condition == "accepted_custom_end_stereotype_n_ary":
        assert any(d.severity == "WARNING" and d.kind == "unrecognized_stereotype" for d in result.diagnostics)
        assert any(d.severity == "ERROR" and "relation_properties_non_binary" in d.facts
                   and "rWorks" in d.identified_sources for d in result.diagnostics)
    else:
        assert any(d.severity == "ERROR" and d.kind == expected_kind for d in result.diagnostics), result.diagnostics
        if expected_kind == "duplicate_id":
            assert any(d.code == "DUPLICATE_SOURCE_ID" and {"competing_declarations", "conversion_aborted"} <= d.facts
                       for d in result.diagnostics if d.kind == "duplicate_id")
        assert not any(_CONTAINER_FACTS & d.facts for d in result.diagnostics), result.diagnostics

    if always_abort or input_policy != "best-effort":
        assert result.outcome == "aborted"
        assert result.ontology is None
    else:
        assert result.outcome == "completed-with-errors"
        assert (BASE.cPerson, RDF.type, OWL.Class) in result.ontology
        assert (BASE.cOrg, RDF.type, OWL.Class) in result.ontology
        assert (BASE.aAge, RDF.type, OWL.DatatypeProperty) in result.ontology
        for absent in (BASE.rWorks, BASE.eSource, BASE.eTarget, BASE.eThird):
            assert not any(absent in triple for triple in result.ontology)


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("case,expected_fact", [
    ("non_instantiation_n_ary", "relation_properties_non_binary"),
    ("non_instantiation_null", "relation_properties_null"),
    ("instantiation_non_array", "relation_properties_non_array"),
])
def test_relation_properties_container_json_diagnostics_export_contract(
        invoke, source_json, tmp_path, input_policy, case, expected_fact):
    """Rules: DK-DIAG-03, DK-DIAG-04, DK-DIAG-05, DK-INS-02; §15 Python JSON export. RD-02 Alternative A."""
    document = source_json("shared/core_model")
    rel = source_element(document, "rWorks")
    s_end, t_end = rel["properties"]
    if case == "non_instantiation_n_ary":
        e_third = copy.deepcopy(t_end)
        e_third["id"] = "eThird"
        rel["properties"] = [s_end, t_end, e_third]
    elif case == "non_instantiation_null":
        rel["properties"] = None
    else:
        rel["stereotype"] = "instantiation"
        rel["properties"] = 0

    source = write_input(tmp_path, document)
    options = {"base_iri": str(BASE), "iri_strategy": "id", "input_policy": input_policy, "provenance": "none"}
    result = invoke.convert(source, options=options, workdir=tmp_path)
    expected_outcome = "completed-with-errors" if input_policy == "best-effort" else "aborted"
    assert result.outcome == expected_outcome

    before = _native_report_records(invoke.report_content(result))
    report_path = tmp_path / "relation_container.json"
    assert invoke.export_diagnostics(result, report_path).failure is None
    payload = json.loads(report_path.read_bytes())
    assert _json_report_contract(payload) == before
    assert payload["outcome"] == expected_outcome

    matching = [
        event for event in payload["diagnostics"]
        if event["severity"] == "ERROR"
        and event["code"] != "INTERNAL_TRANSFORMATION_FAILURE"
        and event["code"] not in {"PLACEHOLDER_BASE", "UNPROCESSABLE_DOCUMENT", "DUPLICATE_SOURCE_ID",
                                   "UNKNOWN_INFORMATION", "REQUIRED_PROVENANCE", "ONTOLOGY_DELIVERY", "SIDECAR_DELIVERY"}
        and event["message"]
        and event["effect"]
        and expected_fact in relation_properties_container_diagnostic(event["message"])
    ]
    assert matching, payload["diagnostics"]
    reported_sources = {
        (source_loc["element_type"], source_loc["identifier"])
        for event in matching for source_loc in event["sources"]
    }
    assert ("Relation", "rWorks") in reported_sources
    report = invoke.read_report(report_path)
    assert report.outcomes == (expected_outcome,)

    observed_graph = invoke.read_ontology(result)
    if expected_outcome == "aborted":
        assert observed_graph is None
    else:
        assert observed_graph is not None
        assert (BASE.cPerson, RDF.type, OWL.Class) in observed_graph
        assert (BASE.cOrg, RDF.type, OWL.Class) in observed_graph
        assert (BASE.aAge, RDF.type, OWL.DatatypeProperty) in observed_graph
        assert not any(BASE.rWorks in triple or BASE.eSource in triple or BASE.eTarget in triple
                       for triple in observed_graph)


_PKG_ENTRY_CASES = [
    ("non_object_null", None, "package_contents_non_object_entry"),
    ("non_object_string", "BAD_ENTRY_SENTINEL", "package_contents_non_object_entry"),
    ("non_object_number", 0, "package_contents_non_object_entry"),
    ("non_object_boolean", False, "package_contents_non_object_entry"),
    ("non_object_array", [], "package_contents_non_object_entry"),
    ("missing_type", {"id": "uBad", "name": "Bad", "description": None, "propertyAssignments": None}, "package_contents_invalid_type"),
    ("null_type", {"id": "uBad", "name": "Bad", "description": None, "type": None, "propertyAssignments": None}, "package_contents_invalid_type"),
    ("number_type", {"id": "uBad", "name": "Bad", "description": None, "type": 42, "propertyAssignments": None}, "package_contents_invalid_type"),
    ("empty_type", {"id": "uBad", "name": "Bad", "description": None, "type": "", "propertyAssignments": None}, "package_contents_invalid_type"),
    ("whitespace_type", {"id": "uBad", "name": "Bad", "description": None, "type": " \t\n", "propertyAssignments": None}, "package_contents_invalid_type"),
    ("misplaced_project", "project", "package_contents_misplaced_declaration"),
    ("misplaced_property", "property", "package_contents_misplaced_declaration"),
    ("misplaced_literal", "literal", "package_contents_misplaced_declaration"),
]


def _pkg_entry_document(scope, entry_spec):
    document = load_json("shared/core_model")
    if entry_spec == "project":
        entry = {
            "id": "projInner", "name": "InnerProject", "description": None, "type": "Project",
            "model": {
                "id": "projInner_root", "name": None, "description": None, "type": "Package",
                "propertyAssignments": None,
                "contents": [copy.deepcopy(source_element(document, "cOrg"))],
            },
            "diagrams": None,
        }
        entry["model"]["contents"][0].update(id="cInsideProject", name="InsideProject")
    elif entry_spec == "property":
        entry = copy.deepcopy(source_element(document, "aAge"))
        entry.update(id="pMisplaced", name="misplacedAttr", cardinality="1")
    elif entry_spec == "literal":
        entry = {
            "id": "vMisplaced", "name": "MisplacedLiteral", "description": None,
            "type": "Literal", "propertyAssignments": None,
        }
    else:
        entry = copy.deepcopy(entry_spec)

    if scope == "root":
        document["model"]["contents"].insert(1, entry)
        target_path = "$.model.contents[1]"
        pkg_id = document["model"]["id"]
    else:
        nested_cls = copy.deepcopy(source_element(document, "cOrg"))
        nested_cls.update(id="cNestedSibling", name="NestedSibling")
        nested_pkg = {
            "id": "pNested", "name": "NestedPkg", "description": None,
            "type": "Package", "propertyAssignments": None,
            "contents": [nested_cls, entry],
        }
        document["model"]["contents"].insert(1, nested_pkg)
        target_path = "$.model.contents[1].contents[1]"
        pkg_id = "pNested"
    return document, target_path, pkg_id


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("scope", ["root", "nested"])
@pytest.mark.parametrize("case,entry_spec,expected_fact", _PKG_ENTRY_CASES, ids=[item[0] for item in _PKG_ENTRY_CASES])
def test_package_contents_invalid_entries_and_misplaced_declarations_follow_policy(
        run, tmp_path, input_policy, scope, case, entry_spec, expected_fact):
    """Rules: DK-GEN-06, DK-DIAG-01, DK-DIAG-04, DK-DIAG-05; §3.2, §3.4. RD-02 Alternatives 1A + 2A."""
    document, target_path, pkg_id = _pkg_entry_document(scope, entry_spec)
    result = run(path=write_input(tmp_path, document), iri_strategy="id", input_policy=input_policy)
    assert all(d.code != "INTERNAL_TRANSFORMATION_FAILURE" for d in result.diagnostics), result.diagnostics
    assert not any(d.code == "UNKNOWN_INFORMATION" for d in result.diagnostics), result.diagnostics
    assert any(
        d.severity == "ERROR"
        and expected_fact in d.facts
        and d.code not in {"INTERNAL_TRANSFORMATION_FAILURE", "UNKNOWN_INFORMATION"}
        and (
            any(s.path.startswith(target_path) or s.identifier in {pkg_id, "projInner", "pMisplaced", "vMisplaced", "uBad"}
                for s in d.raw.sources)
        )
        for d in result.diagnostics
    ), result.diagnostics

    if input_policy != "best-effort":
        assert result.outcome == "aborted" and result.ontology is None and result.provenance is None
        return

    assert result.outcome == "completed-with-errors"
    control_doc = load_json("shared/core_model")
    if scope == "nested":
        nested_cls = copy.deepcopy(source_element(control_doc, "cOrg"))
        nested_cls.update(id="cNestedSibling", name="NestedSibling")
        control_doc["model"]["contents"].insert(1, {
            "id": "pNested", "name": "NestedPkg", "description": None,
            "type": "Package", "propertyAssignments": None,
            "contents": [nested_cls],
        })
    control = run(path=write_input(tmp_path, control_doc, "control.json"),
                  iri_strategy="id", input_policy=input_policy)
    assert control.outcome == "completed"
    assert_graph_equal(result.ontology, control.ontology)
    assert (BASE.cPerson, RDF.type, OWL.Class) in result.ontology
    assert (BASE.cOrg, RDF.type, OWL.Class) in result.ontology
    assert (BASE.aAge, RDF.type, OWL.DatatypeProperty) in result.ontology
    assert (BASE.eTarget, RDF.type, OWL.ObjectProperty) in result.ontology
    if scope == "nested":
        assert (BASE.cNestedSibling, RDF.type, OWL.Class) in result.ontology
    assert not list(result.ontology.subjects(RDF.type, OWL.NamedIndividual))
    for omitted in (BASE.projInner, BASE.cInsideProject, BASE.pMisplaced, BASE.vMisplaced, BASE.uBad):
        assert not any(omitted in triple for triple in result.ontology)
    for omitted_id in ("projInner", "cInsideProject", "pMisplaced", "vMisplaced", "uBad"):
        assert not list(result.ontology.subjects(DCTERMS.identifier, Literal(omitted_id)))


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("scope", ["root", "nested"])
@pytest.mark.parametrize("unknown_type", ["Diagram", "CustomNode"])
def test_package_contents_unknown_string_type_retains_unknown_information(
        run, source_json, tmp_path, input_policy, scope, unknown_type):
    """Rules: DK-GEN-06, DK-DIAG-04, DK-DIAG-05; §3.2. RD-02 Alternative 2A boundary."""
    document = source_json("shared/core_model")
    foreign = {
        "id": "unknownCustom", "name": "UNKNOWN_CUSTOM_SENTINEL",
        "description": None, "type": unknown_type, "propertyAssignments": None,
    }
    if scope == "root":
        document["model"]["contents"].append(foreign)
    else:
        document["model"]["contents"].append({
            "id": "pNested", "name": "Nested", "description": None,
            "type": "Package", "propertyAssignments": None,
            "contents": [foreign],
        })
    assert fixture_issues(document) == {"unknown_element"}
    result = run(path=write_input(tmp_path, document), iri_strategy="id", input_policy=input_policy)
    unknown_events = [d for d in result.diagnostics if d.kind == "unknown_information" and d.code == "UNKNOWN_INFORMATION"]
    assert unknown_events
    assert not any(d.kind == "invalid_package_contents_entry" for d in result.diagnostics)
    if input_policy == "strict":
        assert result.outcome == "aborted" and result.ontology is None
        assert all(d.severity == "ERROR" for d in unknown_events)
    else:
        assert result.outcome == "completed"
        assert all(d.severity == "WARNING" for d in unknown_events)
        assert not any(d.severity == "ERROR" for d in result.diagnostics)
        assert (BASE.cPerson, RDF.type, OWL.Class) in result.ontology
        assert not any(BASE.unknownCustom in triple for triple in result.ontology)


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("condition", [
    "duplicate_misplaced_property_id",
    "duplicate_misplaced_literal_id",
    "duplicate_misplaced_property_after_non_object",
    "rejected_misplaced_property_stereotype",
    "accepted_custom_misplaced_property_stereotype",
    "missing_misplaced_property_id",
    "invalid_misplaced_property_id",
])
def test_package_contents_entries_respect_diagnostic_precedence(
        run, source_json, tmp_path, input_policy, condition):
    """Rules: DK-GEN-06, DK-DIAG-05, DK-DIAG-06; §3.4 opaque source IDs and duplicate IDs. RD-02 Alternatives 1A + 2A."""
    document = source_json("shared/core_model")
    misplaced_prop = copy.deepcopy(source_element(document, "aAge"))
    misplaced_prop.update(id="pMisplaced", name="misplacedAttr")
    misplaced_lit = {
        "id": "vMisplaced", "name": "MisplacedLit", "description": None,
        "type": "Literal", "propertyAssignments": None,
    }
    options = {"iri_strategy": "id", "input_policy": input_policy}
    always_abort = True

    if condition == "duplicate_misplaced_property_id":
        misplaced_prop["id"] = "cOrg"
        document["model"]["contents"].append(misplaced_prop)
        expected_kind = "duplicate_id"
    elif condition == "duplicate_misplaced_literal_id":
        misplaced_lit["id"] = "cOrg"
        document["model"]["contents"].append(misplaced_lit)
        expected_kind = "duplicate_id"
    elif condition == "duplicate_misplaced_property_after_non_object":
        misplaced_prop["id"] = "cOrg"
        document["model"]["contents"].extend([None, misplaced_prop])
        expected_kind = "duplicate_id"
    elif condition == "rejected_misplaced_property_stereotype":
        misplaced_prop["stereotype"] = "customProp"
        document["model"]["contents"].append(misplaced_prop)
        options["stereotype_policy"] = "allow-missing"
        expected_kind = "unrecognized_stereotype"
    elif condition == "accepted_custom_misplaced_property_stereotype":
        misplaced_prop["stereotype"] = "customProp"
        document["model"]["contents"].append(misplaced_prop)
        options["stereotype_policy"] = "allow-custom"
        expected_kind = "unrecognized_stereotype"
        always_abort = False
    elif condition == "missing_misplaced_property_id":
        misplaced_prop.pop("id", None)
        document["model"]["contents"].append(misplaced_prop)
        expected_kind = "missing_id"
        always_abort = False
    else:
        misplaced_prop["id"] = ""
        document["model"]["contents"].append(misplaced_prop)
        expected_kind = "invalid_id"
        always_abort = False

    result = run(path=write_input(tmp_path, document), **options)
    assert all(d.code != "INTERNAL_TRANSFORMATION_FAILURE" for d in result.diagnostics), result.diagnostics
    if condition == "accepted_custom_misplaced_property_stereotype":
        assert any(d.severity == "WARNING" and d.kind == "unrecognized_stereotype" and "pMisplaced" in d.identified_sources
                   for d in result.diagnostics), result.diagnostics
        assert any(d.severity == "ERROR" and "package_contents_misplaced_declaration" in d.facts
                   for d in result.diagnostics), result.diagnostics
    else:
        assert any(d.severity == "ERROR" and d.kind == expected_kind for d in result.diagnostics), result.diagnostics
        if expected_kind == "duplicate_id":
            assert any(d.code == "DUPLICATE_SOURCE_ID" and {"competing_declarations", "conversion_aborted"} <= d.facts
                       for d in result.diagnostics if d.kind == "duplicate_id")

    if always_abort or input_policy != "best-effort":
        assert result.outcome == "aborted" and result.ontology is None
    else:
        assert result.outcome == "completed-with-errors"
        assert (BASE.cPerson, RDF.type, OWL.Class) in result.ontology
        assert (BASE.cOrg, RDF.type, OWL.Class) in result.ontology
        assert not any(BASE.pMisplaced in triple for triple in result.ontology)


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("case,expected_fact", [
    ("package_non_object_entry", "package_contents_non_object_entry"),
    ("package_missing_type_entry", "package_contents_invalid_type"),
    ("package_misplaced_property", "package_contents_misplaced_declaration"),
    ("package_misplaced_literal", "package_contents_misplaced_declaration"),
    ("package_misplaced_project", "package_contents_misplaced_declaration"),
    ("class_properties_non_array", "class_properties_non_array"),
    ("class_properties_non_property", "class_properties_invalid_entry"),
    ("non_enum_literals_non_array", "non_enum_literals_non_array"),
    ("non_enum_literals_non_literal", "non_enum_literals_invalid_entry"),
    ("non_enum_literals_valid_literal", "non_enum_literals_disallowed_literal"),
])
def test_declaration_containers_json_diagnostics_export_contract(
        invoke, source_json, tmp_path, input_policy, case, expected_fact):
    """Rules: DK-GEN-06, DK-ATT-01, DK-CLS-11, DK-DIAG-04, DK-DIAG-05; §15 Python JSON export. RD-02 Alts 1A+2A+3A+4A."""
    document = source_json("shared/core_model")
    if case == "package_non_object_entry":
        document["model"]["contents"].append(None)
    elif case == "package_missing_type_entry":
        document["model"]["contents"].append({"id": "uBad", "name": "Bad", "description": None, "propertyAssignments": None})
    elif case == "package_misplaced_property":
        misplaced = copy.deepcopy(source_element(document, "aAge"))
        misplaced["id"] = "pMisplaced"
        document["model"]["contents"].append(misplaced)
    elif case == "package_misplaced_literal":
        document["model"]["contents"].append({"id": "vMisplaced", "name": "Misplaced", "description": None, "type": "Literal", "propertyAssignments": None})
    elif case == "package_misplaced_project":
        document["model"]["contents"].append({
            "id": "projInner", "name": "Inner", "description": None, "type": "Project",
            "model": {"id": "projInner_root", "name": None, "description": None, "type": "Package", "propertyAssignments": None, "contents": []},
            "diagrams": None,
        })
    elif case == "class_properties_non_array":
        source_element(document, "cOrg")["properties"] = {"id": "notList"}
    elif case == "class_properties_non_property":
        source_element(document, "cOrg")["properties"] = [{"id": "customEntry", "type": "CustomNode"}]
    elif case == "non_enum_literals_non_array":
        source_element(document, "cOrg")["literals"] = "bad"
    elif case == "non_enum_literals_non_literal":
        source_element(document, "cOrg")["literals"] = [{"id": "notLit", "type": "Class"}]
    else:
        source_element(document, "cOrg")["literals"] = [
            {"id": "vBadLit", "name": "BadLit", "description": None, "type": "Literal", "propertyAssignments": None}
        ]

    source = write_input(tmp_path, document)
    options = {"base_iri": str(BASE), "iri_strategy": "id", "input_policy": input_policy, "provenance": "none"}
    result = invoke.convert(source, options=options, workdir=tmp_path)
    expected_outcome = "completed-with-errors" if input_policy == "best-effort" else "aborted"
    assert result.outcome == expected_outcome

    before = _native_report_records(invoke.report_content(result))
    report_path = tmp_path / "container_report.json"
    assert invoke.export_diagnostics(result, report_path).failure is None
    payload = json.loads(report_path.read_bytes())
    assert _json_report_contract(payload) == before
    assert payload["outcome"] == expected_outcome

    if case.startswith("package_"):
        reader = lambda msg, srcs: package_contents_entry_diagnostic(msg, srcs)
    elif case.startswith("class_properties_"):
        reader = lambda msg, _srcs: class_properties_container_diagnostic(msg)
    else:
        reader = lambda msg, _srcs: non_enum_literals_diagnostic(msg)

    matching = [
        event for event in payload["diagnostics"]
        if event["severity"] == "ERROR"
        and event["code"] not in {"INTERNAL_TRANSFORMATION_FAILURE", "UNKNOWN_INFORMATION",
                                   "PLACEHOLDER_BASE", "UNPROCESSABLE_DOCUMENT", "DUPLICATE_SOURCE_ID",
                                   "REQUIRED_PROVENANCE", "ONTOLOGY_DELIVERY", "SIDECAR_DELIVERY"}
        and event["message"]
        and event["effect"]
        and expected_fact in reader(event["message"], [type("Loc", (), s)() for s in event["sources"]])
    ]
    assert matching, payload["diagnostics"]
    report = invoke.read_report(report_path)
    assert report.outcomes == (expected_outcome,)

    observed_graph = invoke.read_ontology(result)
    if expected_outcome == "aborted":
        assert observed_graph is None
    else:
        assert observed_graph is not None
        assert (BASE.cPerson, RDF.type, OWL.Class) in observed_graph
        assert (BASE.cOrg, RDF.type, OWL.Class) in observed_graph
        assert not list(observed_graph.subjects(RDF.type, OWL.NamedIndividual))


def test_declaration_container_entry_readers_require_affirmative_conditions():
    """Harness only: verify affirmative container/entry readers reject guard, negated, and unrelated wording."""
    assert "package_contents_non_object_entry" in package_contents_entry_diagnostic(
        "Package.contents entry at $.model.contents[1] must be a JSON object, got NoneType."
    )
    assert "package_contents_invalid_type" in package_contents_entry_diagnostic(
        "Package.contents entry at $.model.contents[1] lacks a valid nonempty string 'type'."
    )
    assert "package_contents_misplaced_declaration" in package_contents_entry_diagnostic(
        "Misplaced Property declaration 'pMisplaced' is not permitted in Package.contents."
    )
    assert not package_contents_entry_diagnostic("Malformed declaration-container recovery is outside BI-W1")
    assert not package_contents_entry_diagnostic("Recovery of misplaced declarations is outside BI-W1")
    assert not package_contents_entry_diagnostic("If Package.contents has a misplaced Property, conversion aborts.")
    assert not package_contents_entry_diagnostic("Class.properties entry is not a Property.")

    assert "class_properties_non_array" in class_properties_container_diagnostic(
        "Class 'cOrg' properties container is not a JSON array."
    )
    assert "class_properties_invalid_entry" in class_properties_container_diagnostic(
        "Class 'cOrg' properties entry at $.model.contents[0].properties[0] is not a Property object."
    )
    assert not class_properties_container_diagnostic("Relation 'r0' properties container is not a JSON array.")
    assert not class_properties_container_diagnostic("Class 'cOrg' properties container is valid.")
    assert not class_properties_container_diagnostic("Not implemented for Class.properties.")

    assert "non_enum_literals_non_array" in non_enum_literals_diagnostic(
        "Non-enumeration Class 'cOrg' literals must be a JSON array or null."
    )
    assert "non_enum_literals_invalid_entry" in non_enum_literals_diagnostic(
        "Non-enumeration Class 'cOrg' literals entry is not a Literal object."
    )
    assert "non_enum_literals_disallowed_literal" in non_enum_literals_diagnostic(
        "Literal declaration 'vBad' is not permitted on non-enumeration Class 'cOrg'."
    )
    assert not non_enum_literals_diagnostic("Enumeration literals must be a collection of source Literal elements.")
    assert not non_enum_literals_diagnostic("Literal declarations outside enumerations have no assigned baseline mapping")
    assert not non_enum_literals_diagnostic("Class 'eStatus' is an enumeration with valid literals.")


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("case", [
    "package_and_diagram",
    "property_assignments",
    "generalization_and_set",
    "instantiation_relation",
    "derivation_relation",
    "unsupported_relation_connector",
])
def test_excluded_and_omitted_elements_do_not_emit_textual_carrier_errors(run, source_json, tmp_path, input_policy, case):
    """Rules: DK-GEN-06, DK-GEN-07, DK-INS-02, DK-LBL-02, DK-REL-08, DK-REL-17, DK-DIAG-05; §3.2. RD-02 Alts 1A+2A."""
    if case == "package_and_diagram":
        document = source_json("ontology/organization")
        document["model"]["name"] = 123
        document["model"]["description"] = {"bad tag": "IgnoredPkg"}
        for item in source_elements(document):
            if item.get("type") == "Package":
                item["name"] = {"en": 42}
                item["description"] = ["bad"]
        for diagram in document.get("diagrams") or []:
            diagram["name"] = 999
            diagram["description"] = {"bad tag": "IgnoredDiagram"}
    elif case == "property_assignments":
        document = source_json("shared/core_model")
        document["model"]["propertyAssignments"] = {"language": 123, "name": {"bad tag": "IgnoredPA"}}
        source_element(document, "cPerson")["propertyAssignments"] = {"description": ["bad"]}
    elif case == "generalization_and_set":
        document = source_json("shared/categorizers")
        source_element(document, "gOne")["name"] = 123
        source_element(document, "gOne")["description"] = {"bad tag": "IgnoredGen"}
        source_element(document, "gsFirst")["name"] = ["bad"]
        source_element(document, "gsFirst")["description"] = {"en": 42}
    elif case == "instantiation_relation":
        document = source_json("shared/instantiation")
        inst = next(item for item in source_elements(document)
                    if item.get("type") == "Relation" and item.get("stereotype") == "instantiation")
        inst["name"] = 123
        inst["description"] = {"bad tag": "IgnoredInst"}
        inst["properties"][0]["name"] = {"bad tag": "IgnoredInstEnd"}
        inst["properties"][1]["description"] = 456
    elif case == "derivation_relation":
        document = source_json("relations/material_naming")
        deriv = next(item for item in source_elements(document)
                     if item.get("type") == "Relation" and item.get("stereotype") == "derivation")
        deriv["name"] = 123
        deriv["description"] = {"bad tag": "IgnoredDeriv"}
        deriv["properties"][0]["name"] = {"en": 42}
        deriv["properties"][1]["description"] = ["bad"]
    else:
        document = source_json("shared/omitted_connector")
        conn = source_element(document, "rConnector")
        conn["name"] = 123
        conn["description"] = {"bad tag": "IgnoredConnector"}
        conn["properties"][0]["name"] = {"bad tag": "IgnoredEnd"}
        conn["properties"][1]["description"] = 456

    result = run(path=write_input(tmp_path, document), iri_strategy="id", input_policy=input_policy)
    assert all(d.code != "INTERNAL_TRANSFORMATION_FAILURE" for d in result.diagnostics), result.diagnostics
    assert result.outcome == "completed"
    assert not any(
        d.severity == "ERROR" or "malformed_textual_carrier" in d.facts or "invalid_language_string_entry" in d.facts
        for d in result.diagnostics
    ), result.diagnostics


@pytest.mark.parametrize("case", [
    "failed_relation_null_endpoint",
    "malformed_non_binary_relation",
    "primitive_owned_attribute",
    "misplaced_package_property",
    "unknown_information_element",
    "non_enum_disallowed_literal",
    "untransformable_enum_literal_id",
])
def test_elements_omitted_before_textual_validation_do_not_add_textual_errors(run, source_json, tmp_path, case):
    """Rules: DK-LBL-02, DK-DIAG-03, DK-DIAG-05, DK-ATT-01, DK-GEN-06, DK-CLS-11, DK-DIAG-13; §3.2. RD-02 Alt 1A."""
    if case == "failed_relation_null_endpoint":
        document = source_json("shared/binary_relation")
        source_element(document, "tFocus")["propertyType"] = None
        source_element(document, "rFocus")["name"] = 123
        source_element(document, "sFocus")["name"] = {"bad tag": "OmittedEnd"}
        allowed_codes = {"FAILED_RELATION"}
    elif case == "malformed_non_binary_relation":
        document = source_json("shared/binary_relation")
        source_element(document, "rFocus")["name"] = 123
        source_element(document, "rFocus")["properties"] = [source_element(document, "rFocus")["properties"][0]]
        allowed_codes = set()
    elif case == "primitive_owned_attribute":
        document = source_json("attributes_datatypes/value_types")
        prop = copy.deepcopy(source_element(document, "pFocus"))
        prop.update(id="pOmittedAttr", name=123, description={"bad tag": "OmittedAttr"})
        source_element(document, "dValue")["properties"] = [prop]
        allowed_codes = set()
    elif case == "misplaced_package_property":
        document = source_json("shared/core_model")
        misplaced = copy.deepcopy(source_element(document, "aAge"))
        misplaced.update(id="pMisplaced", name=123, description={"bad tag": "OmittedMisplaced"})
        document["model"]["contents"].append(misplaced)
        allowed_codes = set()
    elif case == "unknown_information_element":
        document = source_json("shared/core_model")
        document["model"]["contents"].append({
            "id": "uCustom", "name": 123, "description": {"bad tag": "OmittedUnknown"},
            "type": "CustomNode", "propertyAssignments": None,
        })
        allowed_codes = {"UNKNOWN_INFORMATION"}
    elif case == "non_enum_disallowed_literal":
        document = source_json("shared/core_model")
        source_element(document, "cOrg")["literals"] = [{
            "id": "vDisallowed", "name": 123, "description": {"bad tag": "OmittedLit"},
            "type": "Literal", "propertyAssignments": None,
        }]
        allowed_codes = set()
    else:
        document = source_json("classes/enumerations")
        source_element(document, "vPending").update(id="", name=123)
        allowed_codes = {"UNTRANSFORMABLE_ENUMERATION_VALUE"}

    result = run(path=write_input(tmp_path, document), iri_strategy="id", input_policy="best-effort")
    assert all(d.code != "INTERNAL_TRANSFORMATION_FAILURE" for d in result.diagnostics), result.diagnostics
    expected_outcome = "completed" if case == "unknown_information_element" else "completed-with-errors"
    assert result.outcome == expected_outcome
    assert not any(
        "malformed_textual_carrier" in d.facts or "invalid_language_string_entry" in d.facts
        for d in result.diagnostics
    ), result.diagnostics
    if allowed_codes:
        assert any(d.code in allowed_codes for d in result.diagnostics), result.diagnostics


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("condition", [
    "duplicate_id_with_malformed_text_and_languages",
    "rejected_missing_stereotype_with_malformed_text",
    "rejected_custom_stereotype_with_malformed_languages",
    "invalid_class_id_with_malformed_name",
    "invalid_attribute_id_with_malformed_name",
    "invalid_relation_id_with_malformed_name",
    "owning_class_with_malformed_properties_and_malformed_name",
])
def test_textual_and_project_languages_respect_diagnostic_precedence(
        run, source_json, tmp_path, input_policy, condition):
    """Rules: DK-LBL-02, DK-DIAG-05, DK-DIAG-06, DK-GEN-06, DK-ATT-01; §§3.2, 3.4. RD-02 Alts 1A+2A."""
    document = source_json("shared/core_model")
    options = {"iri_strategy": "id", "input_policy": input_policy}
    always_abort = True

    if condition == "duplicate_id_with_malformed_text_and_languages":
        dup = copy.deepcopy(source_element(document, "cOrg"))
        dup.update(id="cPerson", name=123)
        document["model"]["contents"].append(dup)
        document["languages"] = "en"
        expected_kinds = {"duplicate_id"}
    elif condition == "rejected_missing_stereotype_with_malformed_text":
        source_element(document, "cPerson").update(stereotype=None, name={"bad tag": "Bad"})
        options["stereotype_policy"] = "require-known"
        expected_kinds = {"missing_stereotype"}
    elif condition == "rejected_custom_stereotype_with_malformed_languages":
        source_element(document, "cPerson")["stereotype"] = "customKind"
        document["languages"] = ["en", 42]
        options["stereotype_policy"] = "allow-missing"
        expected_kinds = {"unrecognized_stereotype"}
    elif condition in {"invalid_class_id_with_malformed_name", "invalid_attribute_id_with_malformed_name", "invalid_relation_id_with_malformed_name"}:
        target_id = {"invalid_class_id_with_malformed_name": "cOrg",
                     "invalid_attribute_id_with_malformed_name": "aAge",
                     "invalid_relation_id_with_malformed_name": "rWorks"}[condition]
        source_element(document, target_id).update(id="", name=123)
        expected_kinds = {"invalid_id"}
        always_abort = False
    else:
        source_element(document, "cOrg").update(name=123, properties="bad")
        expected_kinds = {"malformed_class_properties", "malformed_textual_carrier"}
        always_abort = False

    result = run(path=write_input(tmp_path, document), **options)
    assert all(d.code != "INTERNAL_TRANSFORMATION_FAILURE" for d in result.diagnostics), result.diagnostics

    for kind in expected_kinds:
        if kind == "malformed_class_properties":
            assert any(d.severity == "ERROR" and "class_properties_non_array" in d.facts for d in result.diagnostics)
        elif kind == "malformed_textual_carrier":
            if input_policy == "best-effort":
                assert any(d.severity == "ERROR" and "malformed_textual_carrier" in d.facts for d in result.diagnostics)
        else:
            assert any(d.severity == "ERROR" and d.kind == kind for d in result.diagnostics), result.diagnostics

    if condition in {"invalid_class_id_with_malformed_name", "invalid_attribute_id_with_malformed_name", "invalid_relation_id_with_malformed_name"}:
        assert not any(
            "malformed_textual_carrier" in d.facts or "invalid_language_string_entry" in d.facts
            for d in result.diagnostics
        ), result.diagnostics

    if always_abort or input_policy != "best-effort":
        assert result.outcome == "aborted" and result.ontology is None
    else:
        assert result.outcome == "completed-with-errors"
        assert (BASE.cPerson, RDF.type, OWL.Class) in result.ontology


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("case,expected_fact", [
    ("whole_field_class_name", "malformed_textual_carrier"),
    ("whole_field_property_description", "malformed_textual_carrier"),
    ("invalid_langstring_tag_relation", "invalid_language_string_entry"),
    ("invalid_langstring_value_literal", "invalid_language_string_entry"),
    ("project_languages_non_array", "project_languages_non_array"),
    ("project_languages_invalid_entry", "project_languages_invalid_entry"),
])
def test_textual_and_project_languages_json_diagnostics_export_contract(
        invoke, source_json, tmp_path, input_policy, case, expected_fact):
    """Rules: DK-LBL-02, DK-GEN-08, DK-DIAG-01, DK-DIAG-04, DK-DIAG-05; §15 Python JSON export. RD-02 Alts 1A+2A."""
    document = source_json("shared/source_text")
    if case == "whole_field_class_name":
        source_element(document, "cPerson")["name"] = 123
    elif case == "whole_field_property_description":
        source_element(document, "aAge")["description"] = ["bad"]
    elif case == "invalid_langstring_tag_relation":
        source_element(document, "rWorks")["name"] = {"bad tag": "WrongRel", "en": "worksFor"}
    elif case == "invalid_langstring_value_literal":
        source_element(document, "vPending")["name"] = {"en": 42}
    elif case == "project_languages_non_array":
        document["languages"] = "en"
    else:
        document["languages"] = ["en", "bad tag"]

    source = write_input(tmp_path, document)
    options = {"base_iri": str(BASE), "iri_strategy": "id", "input_policy": input_policy, "provenance": "none"}
    result = invoke.convert(source, options=options, workdir=tmp_path)
    expected_outcome = "completed-with-errors" if input_policy == "best-effort" else "aborted"
    assert result.outcome == expected_outcome

    before = _native_report_records(invoke.report_content(result))
    report_path = tmp_path / "textual_report.json"
    assert invoke.export_diagnostics(result, report_path).failure is None
    payload = json.loads(report_path.read_bytes())
    assert _json_report_contract(payload) == before
    assert payload["outcome"] == expected_outcome

    reader = (lambda msg, _srcs: project_languages_diagnostic(msg)) if case.startswith("project_languages_") else (
        lambda msg, srcs: textual_carrier_diagnostic(msg, srcs)
    )
    matching = [
        event for event in payload["diagnostics"]
        if event["severity"] == "ERROR"
        and event["code"] not in {"INTERNAL_TRANSFORMATION_FAILURE", "UNKNOWN_INFORMATION",
                                   "PLACEHOLDER_BASE", "UNPROCESSABLE_DOCUMENT", "DUPLICATE_SOURCE_ID",
                                   "REQUIRED_PROVENANCE", "ONTOLOGY_DELIVERY", "SIDECAR_DELIVERY"}
        and event["message"]
        and event["effect"]
        and expected_fact in reader(event["message"], [type("Loc", (), s)() for s in event["sources"]])
    ]
    assert matching, payload["diagnostics"]
    report = invoke.read_report(report_path)
    assert report.outcomes == (expected_outcome,)

    observed_graph = invoke.read_ontology(result)
    if expected_outcome == "aborted":
        assert observed_graph is None
    else:
        assert observed_graph is not None
        assert (BASE.cOrg, RDF.type, OWL.Class) in observed_graph


def test_textual_and_project_languages_readers_require_affirmative_conditions():
    """Harness only: verify affirmative textual/language readers reject guard, negated, and unrelated wording."""
    assert "malformed_textual_carrier" in textual_carrier_diagnostic(
        "Class 'cPerson' name must be a string, languageString object, or null, got int."
    )
    assert "invalid_language_string_entry" in textual_carrier_diagnostic(
        "Invalid language tag 'bad tag' in Class 'cPerson' name languageString."
    )
    assert "invalid_language_string_entry" in textual_carrier_diagnostic(
        "Class 'cPerson' description languageString entry 'en' must be a string, got int."
    )
    assert not textual_carrier_diagnostic("Malformed textual-carrier recovery is outside BI-W1")
    assert not textual_carrier_diagnostic("Malformed name-carrier recovery is outside BI-W1")
    assert not textual_carrier_diagnostic("If a languageString entry is invalid, conversion aborts.")
    assert not textual_carrier_diagnostic("Class 'cPerson' name is valid.")
    assert not textual_carrier_diagnostic("Project.languages must be a JSON array or null, got str.")

    assert "project_languages_non_array" in project_languages_diagnostic(
        "Project.languages must be a JSON array or null, got str."
    )
    assert "project_languages_invalid_entry" in project_languages_diagnostic(
        "Invalid language tag 'bad tag' in Project.languages."
    )
    assert "project_languages_invalid_entry" in project_languages_diagnostic(
        "Project.languages entry must be a nonempty string language tag, got int."
    )
    assert not project_languages_diagnostic("Malformed project-language recovery is outside BI-W1")
    assert not project_languages_diagnostic("Language assignment is unresolved because multiple project languages are declared.")
    assert not project_languages_diagnostic("Project.languages is valid.")
    assert not project_languages_diagnostic("Invalid language tag 'bad tag' in Class 'cPerson' name languageString.")


_STABLE_DIAGNOSTIC_CODES = frozenset({
    "PLACEHOLDER_BASE", "UNPROCESSABLE_DOCUMENT", "DUPLICATE_SOURCE_ID", "UNKNOWN_INFORMATION",
    "REQUIRED_PROVENANCE", "INTERNAL_TRANSFORMATION_FAILURE", "ONTOLOGY_DELIVERY", "SIDECAR_DELIVERY",
})

_MALFORMED_STEREOTYPE_VALUES = [
    pytest.param(True, id="bool_true"),
    pytest.param(False, id="bool_false"),
    pytest.param(42, id="int"),
    pytest.param(1.5, id="float"),
    pytest.param(["kind"], id="list"),
    pytest.param({"value": "kind"}, id="dict"),
    pytest.param("", id="empty_string"),
    pytest.param(" \t\n\u00a0", id="whitespace_only"),
]


def _prepare_malformed_stereotype_target(document, target, value):
    if target == "class":
        malformed = copy.deepcopy(source_element(document, "cOrg"))
        malformed.update(id="cMalformed", name="MalformedClass", stereotype=copy.deepcopy(value))
        document["model"]["contents"].append(malformed)
        return "cMalformed"
    if target == "relation":
        source_element(document, "rWorks")["stereotype"] = copy.deepcopy(value)
        return "rWorks"
    if target == "attribute":
        source_element(document, "aAge")["stereotype"] = copy.deepcopy(value)
        return "aAge"
    if target == "source_end":
        source_element(document, "eSource")["stereotype"] = copy.deepcopy(value)
        return "eSource"
    if target == "target_end":
        source_element(document, "eTarget")["stereotype"] = copy.deepcopy(value)
        return "eTarget"
    if target == "misplaced_property":
        misplaced = copy.deepcopy(source_element(document, "aAge"))
        misplaced.update(id="pMisplaced", name="misplacedAttr", stereotype=copy.deepcopy(value))
        document["model"]["contents"].append(misplaced)
        return "pMisplaced"
    raise AssertionError(f"Unlisted malformed stereotype target: {target}")


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("stereotype_policy", ["require-known", "allow-missing", "allow-custom"])
@pytest.mark.parametrize("target", ["class", "relation", "attribute", "source_end", "target_end", "misplaced_property"])
@pytest.mark.parametrize("value", _MALFORMED_STEREOTYPE_VALUES)
def test_malformed_stereotype_values_emit_structural_error_independently_of_stereotype_policy(
        run, source_json, source_path, tmp_path, input_policy, stereotype_policy, target, value):
    """Rules: DK-DIAG-05, DK-DIAG-06, DK-PROP-06, DK-GEN-06, DK-DIAG-04; §§3.2, 3.4, 15. RD-02 Alt 1C + Sub-option 2A."""
    document = source_json("shared/core_model")
    target_id = _prepare_malformed_stereotype_target(document, target, value)

    result = run(path=write_input(tmp_path, document), iri_strategy="id",
                 input_policy=input_policy, stereotype_policy=stereotype_policy)
    assert all(d.code != "INTERNAL_TRANSFORMATION_FAILURE" for d in result.diagnostics), result.diagnostics
    assert not any(
        d.code in {"MISSING_STEREOTYPE", "UNRECOGNIZED_STEREOTYPE", "UNKNOWN_INFORMATION"}
        or d.kind in {"missing_stereotype", "unrecognized_stereotype", "unknown_information"}
        for d in result.diagnostics
    ), result.diagnostics

    matching = [
        d for d in result.diagnostics
        if d.severity == "ERROR"
        and "malformed_stereotype" in d.facts
        and target_id in d.identified_sources
        and d.code and d.code not in _STABLE_DIAGNOSTIC_CODES
    ]
    assert matching, result.diagnostics

    if input_policy != "best-effort":
        assert result.outcome == "aborted"
        assert result.ontology is None
        assert result.provenance is None
        if target == "misplaced_property":
            assert not any("package_contents_misplaced_declaration" in d.facts for d in result.diagnostics)
        return

    assert result.outcome == "completed-with-errors"
    graph = result.ontology
    assert (BASE.cPerson, RDF.type, OWL.Class) in graph
    assert (BASE.cOrg, RDF.type, OWL.Class) in graph
    assert (BASE.aAge, RDF.type, OWL.DatatypeProperty) in graph
    if target == "class":
        assert_contains(graph, load_graph(source_path("shared/core_model", "expected.ttl")))
        assert not any(BASE.cMalformed in triple for triple in graph)
        assert not list(graph.subjects(DCTERMS.identifier, Literal("cMalformed")))
    elif target == "relation":
        for omitted in (BASE.rWorks, BASE.eSource, BASE.eTarget):
            assert not any(omitted in triple for triple in graph)
    elif target == "misplaced_property":
        assert_contains(graph, load_graph(source_path("shared/core_model", "expected.ttl")))
        assert any(d.severity == "ERROR" and "package_contents_misplaced_declaration" in d.facts
                   for d in result.diagnostics)
        assert not any(BASE.pMisplaced in triple for triple in graph)
    else:
        assert_contains(graph, load_graph(source_path("shared/core_model", "expected.ttl")))
        assert not any(
            d.severity == "ERROR" and target_id in d.identified_sources and "malformed_stereotype" not in d.facts
            for d in result.diagnostics
        )


@pytest.mark.parametrize("target", ["class", "relation", "attribute", "source_end", "target_end"])
@pytest.mark.parametrize("value", [pytest.param(123, id="int"), pytest.param("   ", id="whitespace_only")])
def test_malformed_stereotype_default_input_policy_aborts(run, source_json, tmp_path, target, value):
    """Rules: DK-DIAG-05, DK-DIAG-06; §15 default input-policy. RD-02 Alt 1C + Sub-option 2A."""
    document = source_json("shared/core_model")
    target_id = _prepare_malformed_stereotype_target(document, target, value)
    result = run(path=write_input(tmp_path, document), iri_strategy="id")
    assert result.outcome == "aborted"
    assert result.ontology is None
    assert any(
        d.severity == "ERROR"
        and "malformed_stereotype" in d.facts
        and target_id in d.identified_sources
        and d.code not in {"MISSING_STEREOTYPE", "UNRECOGNIZED_STEREOTYPE", "INTERNAL_TRANSFORMATION_FAILURE"}
        for d in result.diagnostics
    ), result.diagnostics


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("condition", [
    "duplicate_class_id_with_malformed_stereotype",
    "duplicate_relation_id_with_malformed_stereotype",
    "duplicate_attribute_id_with_malformed_stereotype",
    "duplicate_end_id_with_malformed_stereotype",
    "duplicate_misplaced_property_id_with_malformed_stereotype",
    "omitted_class_suppresses_id_container_and_textual_errors",
    "omitted_relation_suppresses_id_container_and_textual_errors",
    "omitted_relation_with_malformed_end_suppresses_end_id_and_textual_errors",
    "surviving_attribute_retains_downstream_invalid_id",
    "surviving_attribute_retains_downstream_textual_error",
    "surviving_end_retains_downstream_invalid_end_id",
    "surviving_end_retains_downstream_non_binary_relation_error",
    "surviving_misplaced_property_retains_downstream_misplaced_error",
    "surviving_misplaced_property_retains_downstream_invalid_id_precedence",
])
def test_malformed_stereotype_respects_duplicate_id_and_downstream_precedence(
        run, source_json, tmp_path, input_policy, condition):
    """Rules: DK-DIAG-05, DK-DIAG-06, DK-GEN-06, DK-ATT-01, DK-CLS-11, DK-DIAG-03, DK-LBL-02; §§3.2, 3.4. RD-02 Alt 1C + Sub-option 2A."""
    document = source_json("shared/core_model")
    options = {"iri_strategy": "id", "input_policy": input_policy}
    always_abort = False

    if condition == "duplicate_class_id_with_malformed_stereotype":
        dup = copy.deepcopy(source_element(document, "cOrg"))
        dup["stereotype"] = 123
        document["model"]["contents"].append(dup)
        always_abort = True
    elif condition == "duplicate_relation_id_with_malformed_stereotype":
        dup = copy.deepcopy(source_element(document, "cOrg"))
        dup["id"] = "rWorks"
        source_element(document, "rWorks")["stereotype"] = ""
        document["model"]["contents"].append(dup)
        always_abort = True
    elif condition == "duplicate_attribute_id_with_malformed_stereotype":
        dup = copy.deepcopy(source_element(document, "aAge"))
        dup["stereotype"] = False
        source_element(document, "cOrg")["properties"] = [dup]
        always_abort = True
    elif condition == "duplicate_end_id_with_malformed_stereotype":
        dup = copy.deepcopy(source_element(document, "cOrg"))
        dup["id"] = "eSource"
        source_element(document, "eSource")["stereotype"] = "  "
        document["model"]["contents"].append(dup)
        always_abort = True
    elif condition == "duplicate_misplaced_property_id_with_malformed_stereotype":
        misplaced = copy.deepcopy(source_element(document, "aAge"))
        misplaced.update(id="cOrg", stereotype=["prop"])
        document["model"]["contents"].append(misplaced)
        always_abort = True
    elif condition == "omitted_class_suppresses_id_container_and_textual_errors":
        bad_cls = copy.deepcopy(source_element(document, "cOrg"))
        bad_cls.update(id="", name=123, description={"bad tag": "BadDesc"},
                       stereotype=True, properties="bad", literals="bad")
        document["model"]["contents"].append(bad_cls)
    elif condition == "omitted_relation_suppresses_id_container_and_textual_errors":
        source_element(document, "rWorks").update(id="", name=123, description=["bad"],
                                                  stereotype="   ", properties=None)
    elif condition == "omitted_relation_with_malformed_end_suppresses_end_id_and_textual_errors":
        rel = source_element(document, "rWorks")
        rel.update(stereotype=42, name=123)
        rel["properties"][0].update(id="", name=123)
        rel["properties"][1].update(description={"bad tag": "BadEnd"})
    elif condition == "surviving_attribute_retains_downstream_invalid_id":
        source_element(document, "aAge").update(id="", stereotype=False)
    elif condition == "surviving_attribute_retains_downstream_textual_error":
        source_element(document, "aAge").update(name=123, stereotype=" \t ")
    elif condition == "surviving_end_retains_downstream_invalid_end_id":
        source_element(document, "eSource").update(id="", stereotype="")
    elif condition == "surviving_end_retains_downstream_non_binary_relation_error":
        rel = source_element(document, "rWorks")
        third = copy.deepcopy(source_element(document, "eTarget"))
        third.update(id="eThird", stereotype=True)
        rel["properties"].append(third)
    elif condition == "surviving_misplaced_property_retains_downstream_misplaced_error":
        misplaced = copy.deepcopy(source_element(document, "aAge"))
        misplaced.update(id="pMisplaced", stereotype="")
        document["model"]["contents"].append(misplaced)
    else:
        misplaced = copy.deepcopy(source_element(document, "aAge"))
        misplaced.update(id="", name="misplacedAttr", stereotype=0)
        document["model"]["contents"].append(misplaced)

    result = run(path=write_input(tmp_path, document), **options)
    assert all(d.code != "INTERNAL_TRANSFORMATION_FAILURE" for d in result.diagnostics), result.diagnostics

    if always_abort:
        assert result.outcome == "aborted" and result.ontology is None
        assert any(d.code == "DUPLICATE_SOURCE_ID" and d.severity == "ERROR" for d in result.diagnostics)
        assert not any("malformed_stereotype" in d.facts for d in result.diagnostics)
        return

    assert any(d.severity == "ERROR" and "malformed_stereotype" in d.facts for d in result.diagnostics), result.diagnostics

    if input_policy != "best-effort":
        assert result.outcome == "aborted" and result.ontology is None
        # Malformed stereotype precedes apply_identifier_policy, validate_containers, and validate_textual_carriers.
        assert not any(
            d.kind in {"invalid_id", "missing_id", "malformed_class_properties", "invalid_non_enumeration_literals",
                       "invalid_package_contents_entry", "malformed_textual_carrier", "failed_relation"}
            for d in result.diagnostics
        ), result.diagnostics
        return

    assert result.outcome == "completed-with-errors"
    assert (BASE.cPerson, RDF.type, OWL.Class) in result.ontology
    assert (BASE.cOrg, RDF.type, OWL.Class) in result.ontology

    if condition in {
        "omitted_class_suppresses_id_container_and_textual_errors",
        "omitted_relation_suppresses_id_container_and_textual_errors",
        "omitted_relation_with_malformed_end_suppresses_end_id_and_textual_errors",
    }:
        assert not any(
            d.kind in {"invalid_id", "missing_id", "malformed_class_properties", "invalid_non_enumeration_literals",
                       "failed_relation", "malformed_textual_carrier"}
            or "malformed_textual_carrier" in d.facts
            or "invalid_language_string_entry" in d.facts
            or "relation_properties_null" in d.facts
            for d in result.diagnostics
        ), result.diagnostics
    elif condition == "surviving_attribute_retains_downstream_invalid_id":
        assert any(d.severity == "ERROR" and d.kind == "invalid_id" for d in result.diagnostics)
        assert not any(BASE.aAge in triple for triple in result.ontology)
    elif condition == "surviving_attribute_retains_downstream_textual_error":
        assert any(d.severity == "ERROR" and "malformed_textual_carrier" in d.facts for d in result.diagnostics)
        assert (BASE.aAge, RDF.type, OWL.DatatypeProperty) in result.ontology
    elif condition == "surviving_end_retains_downstream_invalid_end_id":
        assert any(d.severity == "ERROR" and d.kind == "failed_relation" for d in result.diagnostics)
        assert not any(BASE.eTarget in triple for triple in result.ontology)
    elif condition == "surviving_end_retains_downstream_non_binary_relation_error":
        assert any(d.severity == "ERROR" and "relation_properties_non_binary" in d.facts for d in result.diagnostics)
        assert not any(BASE.eTarget in triple for triple in result.ontology)
    elif condition == "surviving_misplaced_property_retains_downstream_misplaced_error":
        assert any(d.severity == "ERROR" and "package_contents_misplaced_declaration" in d.facts for d in result.diagnostics)
        assert not any(BASE.pMisplaced in triple for triple in result.ontology)
    else:
        assert any(d.severity == "ERROR" and d.kind == "invalid_id" for d in result.diagnostics)
        assert not any("package_contents_misplaced_declaration" in d.facts for d in result.diagnostics)
        assert not any(
            d.severity == "ERROR" and d.kind not in {"malformed_stereotype", "invalid_id"}
            for d in result.diagnostics
        ), result.diagnostics
        assert not list(result.ontology.subjects(RDFS.label, Literal("misplacedAttr")))
        assert not any("misplacedAttr" in str(term) for triple in result.ontology for term in triple)


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("case,target_kind,target_id", [
    ("class_bool", "Class", "cMalformed"),
    ("relation_empty_string", "Relation", "rWorks"),
    ("attribute_whitespace", "Property", "aAge"),
    ("source_end_int", "Property", "eSource"),
    ("target_end_list", "Property", "eTarget"),
    ("misplaced_property_dict", "Property", "pMisplaced"),
])
def test_malformed_stereotype_json_diagnostics_export_contract(
        invoke, source_json, tmp_path, input_policy, case, target_kind, target_id):
    """Rules: DK-DIAG-04, DK-DIAG-05, DK-DIAG-06; §15 Python JSON export. RD-02 Alt 1C + Sub-option 2A."""
    document = source_json("shared/core_model")
    value_map = {
        "class_bool": ("class", True),
        "relation_empty_string": ("relation", ""),
        "attribute_whitespace": ("attribute", "   "),
        "source_end_int": ("source_end", 7),
        "target_end_list": ("target_end", ["end"]),
        "misplaced_property_dict": ("misplaced_property", {"stereotype": "begin"}),
    }
    target_role, bad_value = value_map[case]
    _prepare_malformed_stereotype_target(document, target_role, bad_value)

    source = write_input(tmp_path, document)
    options = {"base_iri": str(BASE), "iri_strategy": "id", "input_policy": input_policy, "provenance": "none"}
    result = invoke.convert(source, options=options, workdir=tmp_path)
    expected_outcome = "completed-with-errors" if input_policy == "best-effort" else "aborted"
    assert result.outcome == expected_outcome

    before = _native_report_records(invoke.report_content(result))
    report_path = tmp_path / "malformed_stereotype.json"
    assert invoke.export_diagnostics(result, report_path).failure is None
    payload = json.loads(report_path.read_bytes())
    assert _json_report_contract(payload) == before
    assert payload["outcome"] == expected_outcome

    matching = [
        event for event in payload["diagnostics"]
        if event["severity"] == "ERROR"
        and event["code"] not in _STABLE_DIAGNOSTIC_CODES | {"MISSING_STEREOTYPE", "UNRECOGNIZED_STEREOTYPE"}
        and event["message"]
        and event["effect"]
        and "malformed_stereotype" in malformed_stereotype_diagnostic(
            event["message"], [type("Loc", (), s)() for s in event["sources"]]
        )
    ]
    assert matching, payload["diagnostics"]
    reported_sources = {
        (source_loc["element_type"], source_loc["identifier"])
        for event in matching for source_loc in event["sources"]
    }
    assert (target_kind, target_id) in reported_sources
    report = invoke.read_report(report_path)
    assert report.outcomes == (expected_outcome,)

    observed_graph = invoke.read_ontology(result)
    if expected_outcome == "aborted":
        assert observed_graph is None
    else:
        assert observed_graph is not None
        assert (BASE.cPerson, RDF.type, OWL.Class) in observed_graph
        assert (BASE.cOrg, RDF.type, OWL.Class) in observed_graph


def test_malformed_stereotype_reader_requires_affirmative_conditions():
    """Harness only: verify affirmative malformed-stereotype reader rejects guard, missing/unrecognized, negated, and unrelated wording."""
    accepted = (
        "Class 'cPerson' stereotype must be a nonempty string or null, got bool.",
        "Malformed stereotype value on Relation 'rWorks': expected a non-whitespace string or null, got int.",
        "Property 'aAge' has an empty or whitespace-only stereotype string.",
        "Invalid stereotype '' on Class 'cPerson'.",
        "Whitespace-only stereotype '   ' on Property 'eSource' is not permitted.",
        "Relation 'rWorks' has a non-string stereotype (got list).",
        "Class 'cPerson' stereotype is malformed.",
        "Property 'aAge' stereotype cannot be empty or whitespace-only.",
    )
    for message in accepted:
        assert "malformed_stereotype" in malformed_stereotype_diagnostic(message), message

    rejected = (
        "Malformed stereotype-value recovery is outside BI-W1",
        "Unexpected internal failure while validating stereotype.",
        "Missing stereotype on Class.",
        "Class 'cPerson' stereotype is null.",
        "Absent stereotype on Relation 'rWorks'.",
        "Unrecognized stereotype 'waveOneCustom' on Class.",
        "Class 'cPerson' stereotype 'customKind' is unrecognized.",
        "Datatype-valued relation 'rFocus' cannot use stereotype 'mediation', which requires an owl:ObjectProperty.",
        "Class 'cPerson' stereotype is valid.",
        "Class 'cPerson' stereotype is not malformed.",
        "If a stereotype is empty, conversion aborts.",
        "Class 'cPerson' stereotype may be malformed.",
        "Class 'cPerson' stereotype is null or empty.",
        "Stereotype must be a nonempty string.",
        "Class 'cPerson' name must be a string, languageString object, or null, got int.",
    )
    for message in rejected:
        assert not malformed_stereotype_diagnostic(message), message


_MALFORMED_BOOLEAN_VALUES = [
    pytest.param("true", id="str_true"),
    pytest.param("false", id="str_false"),
    pytest.param(1, id="int_one"),
    pytest.param(0, id="int_zero"),
    pytest.param(1.5, id="float"),
    pytest.param([], id="list"),
    pytest.param({}, id="dict"),
]

_DEFINED_BOOLEAN_TARGETS = [
    ("class", "isAbstract"),
    ("class", "isDerived"),
    ("class", "isExtensional"),
    ("class", "isPowertype"),
    ("relation", "isAbstract"),
    ("relation", "isDerived"),
    ("attribute", "isDerived"),
    ("attribute", "isReadOnly"),
    ("attribute", "isOrdered"),
    ("source_end", "isDerived"),
    ("source_end", "isReadOnly"),
    ("source_end", "isOrdered"),
    ("target_end", "isDerived"),
    ("target_end", "isReadOnly"),
    ("target_end", "isOrdered"),
    ("class_gs", "isComplete"),
    ("class_gs", "isDisjoint"),
    ("relation_gs", "isComplete"),
    ("relation_gs", "isDisjoint"),
]


def _prepare_malformed_boolean_flag_target(target_role, flag, value):
    if target_role in {"class", "relation", "attribute", "source_end", "target_end"}:
        document = load_json("shared/core_model")
        element_id = {
            "class": "cOrg",
            "relation": "rWorks",
            "attribute": "aAge",
            "source_end": "eSource",
            "target_end": "eTarget",
        }[target_role]
        source_element(document, element_id)[flag] = copy.deepcopy(value)
        return document, element_id
    if target_role == "class_gs":
        document = load_json("classes/generalization_sets")
        source_element(document, "gsMain")[flag] = copy.deepcopy(value)
        return document, "gsMain"
    if target_role == "relation_gs":
        document = load_json("relations/hierarchy")
        source_element(document, "gsRelations")[flag] = copy.deepcopy(value)
        return document, "gsRelations"
    raise AssertionError(f"Unlisted malformed boolean-flag target: {target_role}")


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("target_role,flag", _DEFINED_BOOLEAN_TARGETS,
                         ids=[f"{role}-{flag}" for role, flag in _DEFINED_BOOLEAN_TARGETS])
@pytest.mark.parametrize("value", [pytest.param("true", id="str_true"), pytest.param(1, id="int_one")])
def test_malformed_boolean_flags_defined_per_element_type_emit_structural_error(
        run, tmp_path, input_policy, target_role, flag, value):
    """Rules: DK-DIAG-05, DK-GEN-05, DK-CLS-01, DK-CLS-06, DK-CLS-07, DK-HO-03, DK-HO-04, DK-PROP-04, DK-PROP-05, DK-REL-01, DK-REL-15, DK-REL-16, DK-DIAG-04; §§3.2, 15. RD-02 Alternative 1."""
    document, target_id = _prepare_malformed_boolean_flag_target(target_role, flag, value)
    result = run(path=write_input(tmp_path, document), iri_strategy="id", input_policy=input_policy)
    assert all(d.code != "INTERNAL_TRANSFORMATION_FAILURE" for d in result.diagnostics), result.diagnostics
    assert not any(
        d.code == "UNKNOWN_INFORMATION" or d.kind == "unknown_information"
        for d in result.diagnostics
    ), result.diagnostics
    assert any(
        d.severity == "ERROR"
        and "malformed_boolean_flag" in d.facts
        and target_id in d.identified_sources
        and d.code and d.code not in _STABLE_DIAGNOSTIC_CODES
        for d in result.diagnostics
    ), result.diagnostics

    if input_policy != "best-effort":
        assert result.outcome == "aborted"
        assert result.ontology is None
        assert result.provenance is None
        return

    assert result.outcome == "completed-with-errors"
    graph = result.ontology
    assert graph is not None
    if target_role in {"class", "relation", "attribute", "source_end", "target_end"}:
        assert (BASE.cPerson, RDF.type, OWL.Class) in graph
        assert (BASE.cOrg, RDF.type, OWL.Class) in graph
        assert (BASE.aAge, RDF.type, OWL.DatatypeProperty) in graph
        assert (BASE.eTarget, RDF.type, OWL.ObjectProperty) in graph
        assert (BASE.eSource, RDF.type, OWL.ObjectProperty) in graph
    elif target_role == "class_gs":
        assert (BASE.cB, RDFS.subClassOf, BASE.cA) in graph
        assert (BASE.cC, RDFS.subClassOf, BASE.cA) in graph
    else:
        assert (BASE.tMiddle, RDFS.subPropertyOf, BASE.tGeneral) in graph
        assert (BASE.tSibling, RDFS.subPropertyOf, BASE.tGeneral) in graph


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("target_role,flag", [
    ("class", "isAbstract"),
    ("relation", "isDerived"),
    ("attribute", "isOrdered"),
    ("class_gs", "isComplete"),
], ids=["class-isAbstract", "relation-isDerived", "attribute-isOrdered", "class_gs-isComplete"])
@pytest.mark.parametrize("value", _MALFORMED_BOOLEAN_VALUES)
def test_malformed_boolean_flag_value_kinds_across_element_types(
        run, tmp_path, input_policy, target_role, flag, value):
    """Rules: DK-DIAG-05, DK-GEN-05, DK-CLS-01, DK-CLS-07, DK-PROP-05, DK-DIAG-04; §3.2. RD-02 Alternative 1."""
    document, target_id = _prepare_malformed_boolean_flag_target(target_role, flag, value)
    result = run(path=write_input(tmp_path, document), iri_strategy="id", input_policy=input_policy)
    assert all(d.code != "INTERNAL_TRANSFORMATION_FAILURE" for d in result.diagnostics), result.diagnostics
    assert any(
        d.severity == "ERROR"
        and "malformed_boolean_flag" in d.facts
        and target_id in d.identified_sources
        and d.code and d.code not in _STABLE_DIAGNOSTIC_CODES
        for d in result.diagnostics
    ), result.diagnostics
    if input_policy != "best-effort":
        assert result.outcome == "aborted" and result.ontology is None
    else:
        assert result.outcome == "completed-with-errors" and result.ontology is not None


@pytest.mark.parametrize("target_role,flag", [
    ("class", "isAbstract"),
    ("relation", "isDerived"),
    ("attribute", "isReadOnly"),
    ("target_end", "isOrdered"),
    ("class_gs", "isComplete"),
    ("relation_gs", "isDisjoint"),
], ids=["class-isAbstract", "relation-isDerived", "attribute-isReadOnly",
        "target_end-isOrdered", "class_gs-isComplete", "relation_gs-isDisjoint"])
@pytest.mark.parametrize("value", [pytest.param("true", id="str_true"), pytest.param(1, id="int_one")])
def test_malformed_boolean_flag_default_input_policy_aborts(run, tmp_path, target_role, flag, value):
    """Rules: DK-DIAG-05, DK-DIAG-04; §15 default input-policy. RD-02 Alternative 1."""
    document, target_id = _prepare_malformed_boolean_flag_target(target_role, flag, value)
    result = run(path=write_input(tmp_path, document), iri_strategy="id")
    assert result.outcome == "aborted"
    assert result.ontology is None
    assert any(
        d.severity == "ERROR"
        and "malformed_boolean_flag" in d.facts
        and target_id in d.identified_sources
        and d.code and d.code not in _STABLE_DIAGNOSTIC_CODES
        for d in result.diagnostics
    ), result.diagnostics


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("target_role,extra_field,value", [
    ("relation", "isReadOnly", True),
    ("relation", "isReadOnly", "true"),
    ("relation", "isOrdered", True),
    ("relation", "isOrdered", 1),
    ("relation", "isExtensional", True),
    ("relation", "isPowertype", True),
    ("relation", "isComplete", True),
    ("relation", "isDisjoint", True),
    ("attribute", "isAbstract", True),
    ("attribute", "isAbstract", "true"),
    ("attribute", "isExtensional", True),
    ("attribute", "isPowertype", True),
    ("attribute", "isComplete", True),
    ("attribute", "isDisjoint", True),
    ("source_end", "isAbstract", True),
    ("source_end", "isAbstract", "true"),
    ("target_end", "isAbstract", 1),
    ("class", "isReadOnly", True),
    ("class", "isOrdered", "true"),
    ("class", "isComplete", True),
    ("class", "isDisjoint", True),
    ("class_gs", "isAbstract", True),
    ("class_gs", "isDerived", "true"),
    ("class_gs", "isReadOnly", True),
    ("class_gs", "isOrdered", True),
    ("project", "isAbstract", True),
    ("package", "isDerived", "true"),
    ("generalization", "isDisjoint", True),
    ("literal", "isDerived", 1),
], ids=[
    "relation-isReadOnly-bool", "relation-isReadOnly-str",
    "relation-isOrdered-bool", "relation-isOrdered-int",
    "relation-isExtensional", "relation-isPowertype",
    "relation-isComplete", "relation-isDisjoint",
    "attribute-isAbstract-bool", "attribute-isAbstract-str",
    "attribute-isExtensional", "attribute-isPowertype",
    "attribute-isComplete", "attribute-isDisjoint",
    "source_end-isAbstract-bool", "source_end-isAbstract-str",
    "target_end-isAbstract-int",
    "class-isReadOnly", "class-isOrdered",
    "class-isComplete", "class-isDisjoint",
    "class_gs-isAbstract", "class_gs-isDerived",
    "class_gs-isReadOnly", "class_gs-isOrdered",
    "project-isAbstract", "package-isDerived",
    "generalization-isDisjoint", "literal-isDerived",
])
def test_unrecognized_boolean_flag_fields_outside_element_type_use_unknown_information(
        run, source_json, tmp_path, input_policy, target_role, extra_field, value):
    """Rules: DK-DIAG-05, DK-PROP-04, DK-PROP-05, DK-CLS-01, DK-REL-01, DK-DIAG-04; §3.2. RD-02 Alternative 1."""
    if target_role == "class_gs":
        document = source_json("classes/generalization_sets")
        target = source_element(document, "gsMain")
        target_id = "gsMain"
    elif target_role == "generalization":
        document = source_json("classes/generalization_sets")
        target = source_element(document, "gB")
        target_id = "gB"
    elif target_role == "literal":
        document = source_json("classes/enumerations")
        target = source_element(document, "vPending")
        target_id = "vPending"
    else:
        document = source_json("shared/core_model")
        if target_role == "project":
            target = document
            target_id = document["id"]
        elif target_role == "package":
            target = document["model"]
            target_id = target["id"]
        else:
            target_id = {
                "relation": "rWorks",
                "attribute": "aAge",
                "source_end": "eSource",
                "target_end": "eTarget",
                "class": "cOrg",
            }[target_role]
            target = source_element(document, target_id)
    target[extra_field] = value

    result = run(path=write_input(tmp_path, document), iri_strategy="id", input_policy=input_policy)
    assert all(d.code != "INTERNAL_TRANSFORMATION_FAILURE" for d in result.diagnostics), result.diagnostics
    assert not any("malformed_boolean_flag" in d.facts for d in result.diagnostics), result.diagnostics
    expected_severity = "ERROR" if input_policy == "strict" else "WARNING"
    assert any(
        d.code == "UNKNOWN_INFORMATION"
        and d.severity == expected_severity
        and target_id in d.identified_sources
        for d in result.diagnostics
    ), result.diagnostics
    if input_policy == "strict":
        assert result.outcome == "aborted" and result.ontology is None
    else:
        assert result.outcome == "completed" and result.ontology is not None


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("condition", [
    "duplicate_class_id_with_malformed_flag",
    "duplicate_relation_id_with_malformed_flag",
    "duplicate_attribute_id_with_malformed_flag",
    "duplicate_gs_id_with_malformed_flag",
    "rejected_missing_stereotype_class_with_malformed_flag",
    "rejected_custom_stereotype_relation_with_malformed_flag",
    "malformed_stereotype_class_omitted_suppresses_flag_error",
    "malformed_stereotype_relation_omitted_suppresses_flag_error",
    "surviving_property_after_malformed_stereotype_still_validates_flag",
    "invalid_class_id_with_malformed_flag",
    "invalid_attribute_id_with_malformed_flag",
    "invalid_gs_id_with_malformed_flag",
    "malformed_class_properties_entry_suppresses_flag_error",
    "non_enum_class_literals_suppresses_flag_error",
    "non_binary_relation_properties_suppresses_end_flag_error",
    "gs_empty_generalizations_precedes_gs_flag_validation",
    "gs_null_generalizations_precedes_gs_flag_validation",
    "instantiation_relation_with_malformed_flags",
    "unsupported_connector_with_malformed_flags",
    "material_derivation_connector_with_malformed_flags",
    "attribute_owner_without_local_class_suppresses_flag_error",
])
def test_malformed_boolean_flag_respects_precedence_and_omitted_element_boundaries(
        run, source_json, tmp_path, input_policy, condition):
    """Rules: DK-DIAG-05, DK-DIAG-06, DK-GEN-06, DK-ATT-01, DK-CLS-11, DK-DIAG-03, DK-DIAG-12, DK-INS-01, DK-INS-02, DK-REL-08, DK-REL-17; §§3.2, 3.4. RD-02 Alternative 1."""
    options = {"iri_strategy": "id", "input_policy": input_policy}
    always_abort = False

    if condition in {
        "duplicate_class_id_with_malformed_flag",
        "duplicate_relation_id_with_malformed_flag",
        "duplicate_attribute_id_with_malformed_flag",
        "rejected_missing_stereotype_class_with_malformed_flag",
        "rejected_custom_stereotype_relation_with_malformed_flag",
        "malformed_stereotype_class_omitted_suppresses_flag_error",
        "malformed_stereotype_relation_omitted_suppresses_flag_error",
        "surviving_property_after_malformed_stereotype_still_validates_flag",
        "invalid_class_id_with_malformed_flag",
        "invalid_attribute_id_with_malformed_flag",
        "malformed_class_properties_entry_suppresses_flag_error",
        "non_enum_class_literals_suppresses_flag_error",
        "non_binary_relation_properties_suppresses_end_flag_error",
        "attribute_owner_without_local_class_suppresses_flag_error",
    }:
        document = source_json("shared/core_model")
    elif condition in {
        "duplicate_gs_id_with_malformed_flag",
        "invalid_gs_id_with_malformed_flag",
        "gs_empty_generalizations_precedes_gs_flag_validation",
        "gs_null_generalizations_precedes_gs_flag_validation",
    }:
        document = source_json("classes/generalization_sets")
    elif condition == "instantiation_relation_with_malformed_flags":
        document = source_json("shared/instantiation")
    elif condition == "unsupported_connector_with_malformed_flags":
        document = source_json("shared/omitted_connector")
    else:
        document = source_json("shared/material_pattern")

    if condition == "duplicate_class_id_with_malformed_flag":
        dup = copy.deepcopy(source_element(document, "cOrg"))
        dup["isAbstract"] = "true"
        document["model"]["contents"].append(dup)
        always_abort = True
    elif condition == "duplicate_relation_id_with_malformed_flag":
        dup = copy.deepcopy(source_element(document, "cOrg"))
        dup["id"] = "rWorks"
        source_element(document, "rWorks")["isDerived"] = 1
        document["model"]["contents"].append(dup)
        always_abort = True
    elif condition == "duplicate_attribute_id_with_malformed_flag":
        dup = copy.deepcopy(source_element(document, "aAge"))
        dup["isReadOnly"] = "true"
        source_element(document, "cOrg")["properties"] = [dup]
        always_abort = True
    elif condition == "duplicate_gs_id_with_malformed_flag":
        dup = copy.deepcopy(source_element(document, "gsMain"))
        dup["isComplete"] = "true"
        document["model"]["contents"].append(dup)
        always_abort = True
    elif condition == "rejected_missing_stereotype_class_with_malformed_flag":
        options["stereotype_policy"] = "require-known"
        source_element(document, "cOrg").update(stereotype=None, isAbstract="true", isExtensional=1)
        always_abort = True
    elif condition == "rejected_custom_stereotype_relation_with_malformed_flag":
        options["stereotype_policy"] = "allow-missing"
        source_element(document, "rWorks").update(stereotype="customRel", isDerived=1)
        always_abort = True
    elif condition == "malformed_stereotype_class_omitted_suppresses_flag_error":
        bad = copy.deepcopy(source_element(document, "cOrg"))
        bad.update(id="cMalformed", stereotype=True, isAbstract="true", isPowertype=1)
        document["model"]["contents"].append(bad)
    elif condition == "malformed_stereotype_relation_omitted_suppresses_flag_error":
        rel = source_element(document, "rWorks")
        rel.update(stereotype="", isAbstract="true", isDerived=1)
        rel["properties"][0].update(isReadOnly="true", isOrdered=0)
    elif condition == "surviving_property_after_malformed_stereotype_still_validates_flag":
        source_element(document, "aAge").update(stereotype=False, isReadOnly="true")
    elif condition == "invalid_class_id_with_malformed_flag":
        bad = copy.deepcopy(source_element(document, "cOrg"))
        bad.update(id="", isAbstract="true", isDerived=1)
        document["model"]["contents"].append(bad)
    elif condition == "invalid_attribute_id_with_malformed_flag":
        source_element(document, "aAge").update(id="", isOrdered="true")
    elif condition == "invalid_gs_id_with_malformed_flag":
        source_element(document, "gsMain").update(id="", isComplete="true", isDisjoint=1)
    elif condition == "malformed_class_properties_entry_suppresses_flag_error":
        bad_entry = copy.deepcopy(source_element(document, "cOrg"))
        bad_entry.update(id="cNotAProp", isAbstract="true", isDerived=1)
        source_element(document, "cOrg")["properties"] = [bad_entry]
    elif condition == "non_enum_class_literals_suppresses_flag_error":
        lit = {"id": "vDisallowed", "name": "Disallowed", "description": None,
               "type": "Literal", "propertyAssignments": None}
        source_element(document, "cOrg")["literals"] = [lit]
    elif condition == "non_binary_relation_properties_suppresses_end_flag_error":
        rel = source_element(document, "rWorks")
        rel.update(isAbstract="true")
        rel["properties"][0].update(isReadOnly="true")
        rel["properties"] = rel["properties"][:1]
    elif condition == "gs_empty_generalizations_precedes_gs_flag_validation":
        source_element(document, "gsMain").update(generalizations=[], isComplete="true", isDisjoint=1)
    elif condition == "gs_null_generalizations_precedes_gs_flag_validation":
        source_element(document, "gsMain").update(generalizations=None, isComplete="true", isDisjoint=1)
    elif condition == "instantiation_relation_with_malformed_flags":
        rel = source_element(document, "rInstantiation")
        rel.update(isAbstract="true", isDerived=1)
        rel["properties"][0].update(isDerived="true", isReadOnly=1, isOrdered=[])
        rel["properties"][1].update(isDerived=0, isReadOnly="false", isOrdered={})
    elif condition == "unsupported_connector_with_malformed_flags":
        rel = source_element(document, "rConnector")
        rel.update(isAbstract="true", isDerived=1)
        rel["properties"][0].update(isDerived="true", isReadOnly=1, isOrdered=[])
        rel["properties"][1].update(isDerived=0, isReadOnly="false", isOrdered={})
    elif condition == "material_derivation_connector_with_malformed_flags":
        rel = source_element(document, "rDerivation")
        rel.update(isAbstract="true", isDerived=1)
        rel["properties"][0].update(isDerived="true", isReadOnly=1, isOrdered=[])
        rel["properties"][1].update(isDerived=0, isReadOnly="false", isOrdered={})
    else:
        attr = copy.deepcopy(source_element(document, "aAge"))
        attr.update(id="aPrimBad", name="primBad", isDerived="true", isReadOnly=1, isOrdered=[])
        source_element(document, "dInt")["properties"] = [attr]

    result = run(path=write_input(tmp_path, document), **options)
    assert all(d.code != "INTERNAL_TRANSFORMATION_FAILURE" for d in result.diagnostics), result.diagnostics

    if condition in {
        "instantiation_relation_with_malformed_flags",
        "unsupported_connector_with_malformed_flags",
        "material_derivation_connector_with_malformed_flags",
    }:
        assert result.outcome == "completed"
        assert not any("malformed_boolean_flag" in d.facts for d in result.diagnostics)
        assert not any(d.severity == "ERROR" for d in result.diagnostics)
        if condition == "instantiation_relation_with_malformed_flags":
            assert any(d.kind == "discarded_instantiation_data" and d.severity == "WARNING"
                       for d in result.diagnostics)
        elif condition == "unsupported_connector_with_malformed_flags":
            assert any(d.kind == "unsupported_connector" and d.severity == "WARNING"
                       for d in result.diagnostics)
        return

    if always_abort:
        assert result.outcome == "aborted" and result.ontology is None
        assert not any("malformed_boolean_flag" in d.facts for d in result.diagnostics)
        if condition.startswith("duplicate_"):
            assert any(d.code == "DUPLICATE_SOURCE_ID" and d.severity == "ERROR" for d in result.diagnostics)
        elif condition == "rejected_missing_stereotype_class_with_malformed_flag":
            assert any(d.code == "MISSING_STEREOTYPE" and d.severity == "ERROR" for d in result.diagnostics)
        else:
            assert any(d.code == "UNRECOGNIZED_STEREOTYPE" and d.severity == "ERROR" for d in result.diagnostics)
        return

    if condition == "surviving_property_after_malformed_stereotype_still_validates_flag":
        assert any(d.severity == "ERROR" and "malformed_stereotype" in d.facts for d in result.diagnostics)
        if input_policy != "best-effort":
            assert result.outcome == "aborted" and result.ontology is None
            assert not any("malformed_boolean_flag" in d.facts for d in result.diagnostics)
        else:
            assert result.outcome == "completed-with-errors"
            assert any(
                d.severity == "ERROR" and "malformed_boolean_flag" in d.facts and "aAge" in d.identified_sources
                for d in result.diagnostics
            ), result.diagnostics
            assert (BASE.aAge, RDF.type, OWL.DatatypeProperty) in result.ontology
        return

    assert not any("malformed_boolean_flag" in d.facts for d in result.diagnostics), result.diagnostics

    if input_policy != "best-effort":
        assert result.outcome == "aborted" and result.ontology is None
    else:
        assert result.outcome == "completed-with-errors" and result.ontology is not None

    if condition == "attribute_owner_without_local_class_suppresses_flag_error":
        assert any(
            d.severity == "ERROR" and d.kind == "attribute_owner_without_local_class" and "aPrimBad" in d.identified_sources
            for d in result.diagnostics
        ), result.diagnostics
        if input_policy == "best-effort":
            assert not any(BASE.aPrimBad in triple or BASE.dInt in triple for triple in result.ontology)


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("case,target_kind,target_id", [
    ("class_str", "Class", "cOrg"),
    ("relation_int", "Relation", "rWorks"),
    ("attribute_list", "Property", "aAge"),
    ("source_end_dict", "Property", "eSource"),
    ("target_end_str", "Property", "eTarget"),
    ("class_gs_int", "GeneralizationSet", "gsMain"),
    ("relation_gs_str", "GeneralizationSet", "gsRelations"),
])
def test_malformed_boolean_flag_json_diagnostics_export_contract(
        invoke, tmp_path, input_policy, case, target_kind, target_id):
    """Rules: DK-DIAG-04, DK-DIAG-05; §15 Python JSON export. RD-02 Alternative 1."""
    case_map = {
        "class_str": ("class", "isAbstract", "true"),
        "relation_int": ("relation", "isDerived", 1),
        "attribute_list": ("attribute", "isOrdered", ["true"]),
        "source_end_dict": ("source_end", "isReadOnly", {"value": True}),
        "target_end_str": ("target_end", "isDerived", "false"),
        "class_gs_int": ("class_gs", "isComplete", 1),
        "relation_gs_str": ("relation_gs", "isDisjoint", "true"),
    }
    target_role, flag, bad_value = case_map[case]
    document, _ = _prepare_malformed_boolean_flag_target(target_role, flag, bad_value)

    source = write_input(tmp_path, document)
    options = {"base_iri": str(BASE), "iri_strategy": "id", "input_policy": input_policy, "provenance": "none"}
    result = invoke.convert(source, options=options, workdir=tmp_path)
    expected_outcome = "completed-with-errors" if input_policy == "best-effort" else "aborted"
    assert result.outcome == expected_outcome

    before = _native_report_records(invoke.report_content(result))
    report_path = tmp_path / "malformed_boolean_flag.json"
    assert invoke.export_diagnostics(result, report_path).failure is None
    payload = json.loads(report_path.read_bytes())
    assert _json_report_contract(payload) == before
    assert payload["outcome"] == expected_outcome

    matching = [
        event for event in payload["diagnostics"]
        if event["severity"] == "ERROR"
        and event["code"] not in _STABLE_DIAGNOSTIC_CODES
        and event["message"]
        and event["effect"]
        and "malformed_boolean_flag" in malformed_boolean_flag_diagnostic(
            event["message"], [type("Loc", (), s)() for s in event["sources"]]
        )
    ]
    assert matching, payload["diagnostics"]
    reported_sources = {
        (source_loc["element_type"], source_loc["identifier"])
        for event in matching for source_loc in event["sources"]
    }
    assert (target_kind, target_id) in reported_sources
    report = invoke.read_report(report_path)
    assert report.outcomes == (expected_outcome,)

    observed_graph = invoke.read_ontology(result)
    if expected_outcome == "aborted":
        assert observed_graph is None
    else:
        assert observed_graph is not None


def test_malformed_boolean_flag_reader_requires_affirmative_conditions():
    """Harness only: verify affirmative malformed-boolean-flag reader rejects guard, unknown-field, null/valid, negated, and unrelated wording."""
    accepted = (
        "Class 'cPerson' isAbstract must be a boolean or null, got str.",
        "Malformed boolean flag isDerived on Relation 'rWorks': expected bool or null, got int.",
        "Property 'aAge' has a non-boolean isOrdered value (got list).",
        "Invalid isReadOnly value 'true' on Property 'eSource'.",
        "GeneralizationSet 'gsMain' isComplete is not a JSON boolean (got dict).",
        "Class 'cPerson' isPowertype must be a boolean or null, got int.",
        "GeneralizationSet 'gsRelations' isDisjoint is malformed.",
        "Property 'eTarget' isDerived cannot be non-boolean.",
    )
    for message in accepted:
        assert "malformed_boolean_flag" in malformed_boolean_flag_diagnostic(message), message

    rejected = (
        "Malformed class-flag recovery is outside the decided baseline",
        "Malformed relation/end flag recovery remains unspecified",
        "Unexpected internal failure while validating isAbstract.",
        "Unrecognized input fields on Relation: isReadOnly.",
        "Unrecognized input field isAbstract on Property.",
        "Class 'cPerson' isAbstract is null.",
        "Class 'cPerson' isAbstract is absent.",
        "Class 'cPerson' isAbstract is true.",
        "Class 'cPerson' isAbstract is false.",
        "Explicit isAbstract=true is preserved as an annotation; its meaning is not additionally enforced.",
        "Class 'cPerson' isAbstract is valid.",
        "Class 'cPerson' isAbstract is not malformed.",
        "If isAbstract is non-boolean, conversion aborts.",
        "Class 'cPerson' isDerived may be malformed.",
        "Class 'cPerson' isAbstract is null or malformed.",
        "Class 'cPerson' isAbstract must be a boolean or null.",
        "Class 'cPerson' stereotype must be a nonempty string or null, got int.",
    )
    for message in rejected:
        assert not malformed_boolean_flag_diagnostic(message), message


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("target_role", [
    "project", "package", "relation", "attribute", "source_end", "target_end",
    "generalization", "generalization_set", "literal",
])
@pytest.mark.parametrize("value", [pytest.param("1", id="str"), pytest.param(2, id="int")])
def test_non_class_order_field_routes_through_unknown_information(
        run, source_json, tmp_path, input_policy, target_role, value):
    """Rules: DK-CLS-05, DK-DIAG-01, DK-DIAG-04, DK-DIAG-05; §3.2. RD-02 V4 + R1."""
    if target_role == "generalization_set":
        document = source_json("classes/generalization_sets")
        target = source_element(document, "gsMain")
        target_id = "gsMain"
    elif target_role == "generalization":
        document = source_json("classes/generalization_sets")
        target = source_element(document, "gB")
        target_id = "gB"
    elif target_role == "literal":
        document = source_json("classes/enumerations")
        target = source_element(document, "vPending")
        target_id = "vPending"
    else:
        document = source_json("shared/core_model")
        if target_role == "project":
            target = document
            target_id = document["id"]
        elif target_role == "package":
            target = document["model"]
            target_id = target["id"]
        else:
            target_id = {
                "relation": "rWorks",
                "attribute": "aAge",
                "source_end": "eSource",
                "target_end": "eTarget",
            }[target_role]
            target = source_element(document, target_id)
    target["order"] = value

    result = run(path=write_input(tmp_path, document), iri_strategy="id", input_policy=input_policy)
    assert all(d.code != "INTERNAL_TRANSFORMATION_FAILURE" for d in result.diagnostics), result.diagnostics
    assert not any("malformed_class_order" in d.facts for d in result.diagnostics), result.diagnostics
    expected_severity = "ERROR" if input_policy == "strict" else "WARNING"
    assert any(
        d.code == "UNKNOWN_INFORMATION"
        and d.severity == expected_severity
        and target_id in d.identified_sources
        for d in result.diagnostics
    ), result.diagnostics
    if input_policy == "strict":
        assert result.outcome == "aborted" and result.ontology is None
    else:
        assert result.outcome == "completed" and result.ontology is not None
        assert not any(
            str(comment).startswith("OntoUML classifier order:")
            for _, _, comment in result.ontology.triples((None, RDFS.comment, None))
        )


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("condition", [
    "duplicate_class_id_with_malformed_order",
    "rejected_missing_stereotype_class_with_malformed_order",
    "rejected_custom_stereotype_class_with_malformed_order",
    "malformed_stereotype_class_omitted_suppresses_order_error",
    "missing_class_id_with_malformed_order",
    "invalid_class_id_with_malformed_order",
    "nested_package_non_array_contents_suppresses_class_order_error",
    "package_contents_invalid_entry_suppresses_class_order_error",
])
def test_malformed_class_order_respects_precedence_and_omitted_element_boundaries(
        run, source_json, tmp_path, input_policy, condition):
    """Rules: DK-CLS-05, DK-DIAG-05, DK-DIAG-06, DK-GEN-06; §§3.2, 3.4. RD-02 V4 + R1."""
    document = source_json("shared/core_model")
    options = {"iri_strategy": "id", "input_policy": input_policy}
    always_abort = False

    if condition == "duplicate_class_id_with_malformed_order":
        dup = copy.deepcopy(source_element(document, "cOrg"))
        dup["order"] = 2
        document["model"]["contents"].append(dup)
        always_abort = True
    elif condition == "rejected_missing_stereotype_class_with_malformed_order":
        options["stereotype_policy"] = "require-known"
        source_element(document, "cOrg").update(stereotype=None, order=2)
        always_abort = True
    elif condition == "rejected_custom_stereotype_class_with_malformed_order":
        options["stereotype_policy"] = "allow-missing"
        source_element(document, "cOrg").update(stereotype="customKind", order=True)
        always_abort = True
    elif condition == "malformed_stereotype_class_omitted_suppresses_order_error":
        bad = copy.deepcopy(source_element(document, "cOrg"))
        bad.update(id="cBadStereo", stereotype="", order=2)
        document["model"]["contents"].append(bad)
    elif condition == "missing_class_id_with_malformed_order":
        bad = copy.deepcopy(source_element(document, "cOrg"))
        del bad["id"]
        bad["order"] = 2
        document["model"]["contents"].append(bad)
    elif condition == "invalid_class_id_with_malformed_order":
        bad = copy.deepcopy(source_element(document, "cOrg"))
        bad.update(id="", order=2)
        document["model"]["contents"].append(bad)
    elif condition == "nested_package_non_array_contents_suppresses_class_order_error":
        lost = copy.deepcopy(source_element(document, "cOrg"))
        lost.update(id="cLost", name="LostClass", order=2)
        document["model"]["contents"].append({
            "id": "pNested", "name": "Nested", "description": None,
            "type": "Package", "propertyAssignments": None,
            "contents": lost,
        })
    else:
        bad = copy.deepcopy(source_element(document, "cOrg"))
        bad.update(id="cMissingType", type="", order=2)
        document["model"]["contents"].append(bad)

    result = run(path=write_input(tmp_path, document), **options)
    assert all(d.code != "INTERNAL_TRANSFORMATION_FAILURE" for d in result.diagnostics), result.diagnostics
    assert not any("malformed_class_order" in d.facts for d in result.diagnostics), result.diagnostics

    if always_abort:
        assert result.outcome == "aborted" and result.ontology is None
        if condition == "duplicate_class_id_with_malformed_order":
            assert any(d.code == "DUPLICATE_SOURCE_ID" and d.severity == "ERROR" for d in result.diagnostics)
        elif condition == "rejected_missing_stereotype_class_with_malformed_order":
            assert any(d.code == "MISSING_STEREOTYPE" and d.severity == "ERROR" for d in result.diagnostics)
        else:
            assert any(d.code == "UNRECOGNIZED_STEREOTYPE" and d.severity == "ERROR" for d in result.diagnostics)
        return

    expected_kind = {
        "malformed_stereotype_class_omitted_suppresses_order_error": "malformed_stereotype",
        "missing_class_id_with_malformed_order": "missing_id",
        "invalid_class_id_with_malformed_order": "invalid_id",
        "nested_package_non_array_contents_suppresses_class_order_error": "malformed_package_contents",
        "package_contents_invalid_entry_suppresses_class_order_error": "invalid_package_contents_entry",
    }[condition]
    assert any(d.severity == "ERROR" and d.kind == expected_kind for d in result.diagnostics), result.diagnostics
    if input_policy != "best-effort":
        assert result.outcome == "aborted" and result.ontology is None
    else:
        assert result.outcome == "completed-with-errors" and result.ontology is not None
        assert (BASE.cPerson, RDF.type, OWL.Class) in result.ontology
        assert (BASE.cOrg, RDF.type, OWL.Class) in result.ontology


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("case,bad_value", [
    pytest.param("ordinary_int", 2, id="ordinary_int"),
    pytest.param("ordinary_float", 1.5, id="ordinary_float"),
    pytest.param("ordinary_bool", True, id="ordinary_bool"),
    pytest.param("ordinary_list", [1], id="ordinary_list"),
    pytest.param("ordinary_dict", {"order": "1"}, id="ordinary_dict"),
    pytest.param("primitive_int", 2, id="primitive_int"),
])
def test_malformed_class_order_json_diagnostics_export_contract(
        invoke, source_json, tmp_path, input_policy, case, bad_value):
    """Rules: DK-CLS-05, DK-DIAG-04, DK-DIAG-05; §15 Python JSON export. RD-02 V4 + R1."""
    if case == "primitive_int":
        document = source_json("classes/enumerations")
        owner = source_element(document, "cOwner")
        owner["properties"] = None
        target = source_element(document, "eStatus")
        target.update(stereotype="datatype", name="int", properties=None, literals=None, order=bad_value)
        document["model"]["contents"] = [owner, target]
        target_id = "eStatus"
    else:
        document = source_json("shared/core_model")
        source_element(document, "cOrg")["order"] = copy.deepcopy(bad_value)
        target_id = "cOrg"

    source = write_input(tmp_path, document)
    options = {"base_iri": str(BASE), "iri_strategy": "id", "input_policy": input_policy, "provenance": "none"}
    result = invoke.convert(source, options=options, workdir=tmp_path)
    expected_outcome = "completed-with-errors" if input_policy == "best-effort" else "aborted"
    assert result.outcome == expected_outcome

    before = _native_report_records(invoke.report_content(result))
    report_path = tmp_path / "malformed_class_order.json"
    assert invoke.export_diagnostics(result, report_path).failure is None
    payload = json.loads(report_path.read_bytes())
    assert _json_report_contract(payload) == before
    assert payload["outcome"] == expected_outcome

    matching = [
        event for event in payload["diagnostics"]
        if event["severity"] == "ERROR"
        and event["code"] not in _STABLE_DIAGNOSTIC_CODES
        and event["message"]
        and event["effect"]
        and "malformed_class_order" in malformed_class_order_diagnostic(
            event["message"], [type("Loc", (), s)() for s in event["sources"]]
        )
    ]
    assert matching, payload["diagnostics"]
    reported_sources = {
        (source_loc["element_type"], source_loc["identifier"])
        for event in matching for source_loc in event["sources"]
    }
    assert ("Class", target_id) in reported_sources
    report = invoke.read_report(report_path)
    assert report.outcomes == (expected_outcome,)

    observed_graph = invoke.read_ontology(result)
    if expected_outcome == "aborted":
        assert observed_graph is None
    else:
        assert observed_graph is not None


def test_malformed_class_order_reader_requires_affirmative_conditions():
    """Harness only: verify affirmative malformed-class-order reader rejects guard, unknown-field, isOrdered, null/valid, negated, and unrelated wording."""
    accepted = (
        "Class 'cPerson' order must be a string or null, got int.",
        "Malformed Class.order on 'cPerson': expected str or null, got float.",
        "Class 'cPerson' has a non-string order value (got list).",
        "Invalid order value '2' on Class 'cPerson'.",
        "Class 'cPerson' order is a boolean (got True).",
        "Class 'cPerson' order is not a JSON string.",
        "Class 'cPerson' order has invalid type dict.",
        "Class 'cPerson' order cannot be non-string.",
    )
    for message in accepted:
        assert "malformed_class_order" in malformed_class_order_diagnostic(message), message

    order_loc = (SimpleNamespace(path="$.model.contents[0].order", identifier="cPerson", element_type="Class"),)
    assert "malformed_class_order" in malformed_class_order_diagnostic("Invalid value (got int).", order_loc)

    rejected = (
        "Malformed classifier-order recovery is outside the decided baseline",
        "Unexpected internal failure while validating order.",
        "Unrecognized input fields on Relation: order.",
        "Unrecognized input field order on Property.",
        "Order is not a defined field on Relation.",
        "Property 'aAge' value order is not represented.",
        "Property 'aAge' isOrdered must be a boolean or null, got int.",
        "Class 'cPerson' order is null.",
        "Class 'cPerson' order is absent.",
        "Class 'cPerson' order is a string.",
        "Class 'cPerson' order is preserved as an annotation.",
        "Class 'cPerson' order is valid.",
        "Class 'cPerson' order is not malformed.",
        "If order is non-string, conversion aborts.",
        "Class 'cPerson' order may be malformed.",
        "Class 'cPerson' order is null or malformed.",
        "Class 'cPerson' order must be a string or null.",
        "Class 'cPerson' order must be a string or null, got str.",
        "Class 'cPerson' isAbstract must be a boolean or null, got int.",
        "Class 'cPerson' stereotype must be a nonempty string or null, got int.",
    )
    for message in rejected:
        assert not malformed_class_order_diagnostic(message), message


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("bad_case,bad_value", [
    ("base_iri", "relative/base"),
    ("base_iri", 123),
    ("ontology_version_iri", "relative/version"),
    ("ontology_version_iri", 123),
    ("iri_strategy", "INVALID"),
    ("iri_strategy", 123),
    ("stereotype_policy", "INVALID"),
    ("stereotype_policy", 123),
    ("inverse_properties", "INVALID"),
    ("inverse_properties", 123),
    ("relation_labels", "INVALID"),
    ("relation_labels", 123),
    ("material_property_chains", "INVALID"),
    ("material_property_chains", 123),
    ("dkgm_vocabulary", "INVALID"),
    ("dkgm_vocabulary", 123),
    ("provenance", "INVALID"),
    ("provenance", 123),
    ("omit_identifiers", "true"),
    ("omit_identifiers", 1),
    ("omit_identifiers", None),
    ("stereotype_relation_naming", "false"),
    ("stereotype_relation_naming", 0),
    ("stereotype_relation_naming", None),
    ("language", "bad tag"),
    ("language", 123),
    ("metadata_file", 123),
    ("metadata_file", "wrong.yaml"),
    ("metadata_file", "metadata.json"),
    ("source", None),
    ("source", 123),
    ("source", {"type": "Project"}),
], ids=[
    "base_iri_str", "base_iri_int", "version_iri_str", "version_iri_int",
    "iri_strategy_str", "iri_strategy_int", "stereotype_policy_str", "stereotype_policy_int",
    "inverse_properties_str", "inverse_properties_int", "relation_labels_str", "relation_labels_int",
    "material_chains_str", "material_chains_int", "dkgm_vocabulary_str", "dkgm_vocabulary_int",
    "provenance_str", "provenance_int", "omit_identifiers_str", "omit_identifiers_int", "omit_identifiers_none",
    "stereo_rel_naming_str", "stereo_rel_naming_int", "stereo_rel_naming_none",
    "language_bad_tag", "language_int", "metadata_file_int", "metadata_file_wrong_name", "metadata_file_wrong_ext",
    "source_none", "source_int", "source_dict",
])
def test_python_pre_conversion_configuration_validation_uniform_across_controls_and_policies(
        invoke, source_path, tmp_path, input_policy, bad_case, bad_value):
    """Rules: DK-IRI-01, DK-LBL-02, DK-GEN-09, DK-DIAG-01, DK-DIAG-04, DK-DIAG-05; §§3.2, 15. RD-04 Decision 2 (Q3-A)."""
    source = source_path("shared/base_iri")
    options = {"base_iri": str(BASE), "input_policy": input_policy}
    if bad_case == "source":
        source = bad_value
    elif bad_case == "metadata_file" and isinstance(bad_value, str):
        meta = tmp_path / bad_value
        meta.write_text("title: Valid Title\n", encoding="utf-8")
        options["metadata_file"] = meta
    else:
        options[bad_case] = bad_value

    result = invoke.convert(source, options=options, workdir=tmp_path)
    assert result.configuration_error is not None
    assert result.conversion_started is False
    assert result.native is None
    assert result.outcome is None and result.ontology is None and result.diagnostics == ()
    assert result.diagnostics_exports == ()


@pytest.mark.parametrize("bad_policy", ["INVALID", 123], ids=["str", "int"])
def test_python_pre_conversion_rejects_invalid_input_policy(invoke, source_path, tmp_path, bad_policy):
    """Rules: DK-DIAG-01, DK-DIAG-05; §15. RD-04 Decision 2 (Q3-A)."""
    result = invoke.convert(
        source_path("shared/base_iri"),
        options={"base_iri": str(BASE), "input_policy": bad_policy},
        workdir=tmp_path,
    )
    assert result.configuration_error is not None
    assert result.conversion_started is False
    assert result.outcome is None and result.ontology is None and result.diagnostics == ()


def test_python_preserves_distinction_between_configuration_rejection_and_input_or_metadata_failures(
        invoke, source_path, tmp_path):
    """Rules: DK-GEN-09, DK-DIAG-04, DK-DIAG-05; §§3.2, 15. RD-04 Decision 2 (Q3-A)."""
    r_src = invoke.convert(
        tmp_path / "missing_source.json",
        options={"base_iri": str(BASE), "provenance": "none", "input_policy": "best-effort"},
        workdir=tmp_path,
    )
    assert r_src.configuration_error is None
    assert r_src.conversion_started is True
    assert r_src.outcome == "aborted"
    assert any(d.code == "UNPROCESSABLE_DOCUMENT" and d.severity == "ERROR" for d in r_src.diagnostics)

    r_meta = invoke.convert(
        source_path("shared/base_iri"),
        options={"base_iri": str(BASE), "provenance": "none",
                 "metadata_file": tmp_path / "metadata.yaml", "input_policy": "best-effort"},
        workdir=tmp_path,
    )
    assert r_meta.configuration_error is None
    assert r_meta.conversion_started is True
    assert r_meta.outcome == "completed-with-errors"
    assert any(d.kind == "metadata_input" and d.severity == "ERROR" for d in r_meta.diagnostics)


