"""General identity rules. Enumeration/inverse-specific naming belongs elsewhere."""

import copy

import pytest
from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, XSD

from tests.support.data import fixture_issues, write_input
from tests.support.invocation import diagnostic_signatures
from tests.support.rdf import assert_selected_equal, one_subject


BASE = Namespace("https://example.test/model#")
POLICIES = ["strict", "tolerant", "best-effort"]
NAMES = [
    ("cCafe", "Cafe_au_lait"), ("cLeading", "_9_lives"),
    ("cPunctuation", "A_B_C"), ("cPeople", "People"),
    ("cAbbreviation", "PCR"), ("cSpelling", "teh"),
    ("cPortuguese", "carro"), ("cCase", "PERSON"),
    ("cSlash", "before_after"), ("cAccent", "alcool"),
]
ESCAPED_IDS = [
    ("CaseID", "CaseID"), ("caseID", "caseID"), ("A_B", "A_x5FB"),
    ("A_x5FB", "A_x5Fx5FB"), ("A.B", "A_x2EB"),
    ("9start", "id_9start"), (" é ", "_x20_xC3_xA9_x20"),
    ("東京", "_xE6_x9D_xB1_xE4_xBA_xAC"),
    (" e\u0301 ", "_x20e_xCC_x81_x20"), ("id_9start", "id_x5F9start"),
]
NAME_STATES = [
    pytest.param("absent", None, id="absent"), pytest.param("value", None, id="null"),
    pytest.param("value", "", id="empty"), pytest.param("value", "  \t", id="whitespace"),
    pytest.param("value", "___", id="punctuation"), pytest.param("value", "東京", id="non_ascii_only"),
]
MISSING_STATES = NAME_STATES[:4]
ELIGIBLE_IDS = ("cPerson", "cOrg", "cAddress", "aAge", "aNote", "aAddress", "eTarget", "eSource")
FIXED_PREDICATES = {RDF.type, RDFS.domain, RDFS.range, RDFS.label, DCTERMS.identifier,
                    RDFS.subClassOf, RDFS.subPropertyOf, OWL.inverseOf,
                    OWL.equivalentClass, OWL.equivalentProperty, OWL.propertyChainAxiom,
                    OWL.propertyDisjointWith}


def _set_name(element, state, value):
    if state == "absent":
        element.pop("name", None)
    else:
        element["name"] = value


@pytest.mark.parametrize("supplied,effective,ontology", [
    pytest.param(None, "https://example.org/directkg#", "https://example.org/directkg", id="omitted"),
    pytest.param("https://example.test/ns", "https://example.test/ns#", "https://example.test/ns", id="append_hash"),
    pytest.param("https://example.test/ns#", "https://example.test/ns#", "https://example.test/ns", id="keep_hash"),
    pytest.param("https://example.test/ns/", "https://example.test/ns/", "https://example.test/ns/", id="keep_slash"),
    pytest.param("urn:example:directkg", "urn:example:directkg#", "urn:example:directkg", id="non_http_absolute"),
    pytest.param("https://例え.テスト/é#", "https://例え.テスト/é#", "https://例え.テスト/é", id="unicode"),
    pytest.param("https://base-check.invalid/model", "https://base-check.invalid/model#", "https://base-check.invalid/model", id="no_availability_requirement"),
])
def test_effective_base_and_ontology_identity(invoke, source_path, tmp_path, supplied, effective, ontology):
    """Rules: DK-IRI-01, DK-IRI-02, DK-DIAG-01, DK-DIAG-05; §15.

    An invalid-domain host is a syntactically valid base; no dereference is
    needed. A supplied delimiter is retained and the default strategy is name.
    """
    options = {"provenance": "none"}
    if supplied is not None:
        options["base_iri"] = supplied
    result = invoke.convert(source_path("shared/base_iri"), options=options, workdir=tmp_path)
    assert result.outcome == "completed"
    assert result.configuration_error is None
    assert (URIRef(ontology), RDF.type, OWL.Ontology) in result.ontology
    assert (URIRef(effective + "Person"), RDF.type, OWL.Class) in result.ontology
    notices = [d for d in result.diagnostics if d.kind == "placeholder_base"]
    if supplied is None:
        assert notices and all(d.severity == "WARNING" for d in notices)
        assert {"placeholder_namespace", "not_recommended_for_publication"} <= set().union(*(d.facts for d in notices))
    else:
        assert not notices


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("supplied", [
    pytest.param("", id="empty"), pytest.param(" \t", id="whitespace"),
    pytest.param("relative-model", id="relative"), pytest.param("../model", id="relative_path"),
    pytest.param(" https://example.test/model", id="no_trimming"),
    pytest.param("https://example.test/a b", id="no_space_encoding_repair"),
    pytest.param("https://example.test/a%ZZ", id="bad_percent_escape"),
    pytest.param("https://example.test/model#part", id="effective_base_invalid"),
])
def test_invalid_supplied_base_is_rejected_before_conversion(invoke, source_path, tmp_path, input_policy, supplied):
    """Rules: DK-IRI-01, DK-DIAG-01, DK-DIAG-05; §15 supplied-base rejection.

    Missing production must fail the invocation, not satisfy a broad
    pytest.raises(Exception) assertion intended for configuration errors.
    """
    result = invoke.convert(source_path("shared/base_iri"), options={"base_iri": supplied, "input_policy": input_policy, "provenance": "none"}, workdir=tmp_path)
    assert result.configuration_error is not None
    assert result.outcome is None
    assert result.ontology is None
    assert result.diagnostics == ()  # no conversion diagnostics for a rejected configuration


@pytest.mark.parametrize("identifier,local", NAMES, ids=[x[0] for x in NAMES])
def test_name_normalization_preserves_lexical_identity(run, identifier, local):
    """Rules: DK-IRI-02, DK-IRI-03, DK-IRI-07, DK-CONF-01, DK-CONF-03."""
    result = run("iris/names")
    assert result.outcome == "completed"
    resource = one_subject(result.ontology, DCTERMS.identifier, Literal(identifier))
    assert resource == BASE[local]
    assert (resource, RDF.type, OWL.Class) in result.ontology


@pytest.mark.parametrize("identifier,local", ESCAPED_IDS, ids=["ascii_upper", "ascii_lower", "underscore", "escape_lookalike", "punctuation", "leading_digit", "utf8_spaces", "utf8_multibyte", "no_unicode_normalization", "digit_prefix_lookalike"])
def test_ids_use_injective_byte_escaping(run, identifier, local):
    """Rules: DK-IRI-02, DK-IRI-05, DK-IRI-07, DK-CONF-02, DK-CONF-03."""
    result = run("iris/id_escaping", iri_strategy="id")
    assert result.outcome == "completed"
    assert (BASE[local], RDF.type, OWL.Class) in result.ontology
    expected = {BASE[candidate] for _, candidate in ESCAPED_IDS}
    assert set(result.ontology.subjects(RDF.type, OWL.Class)) == expected
    assert len(expected) == len(ESCAPED_IDS)


def test_id_strategy_is_independent_of_source_names(run, source_json, tmp_path):
    """Rules: DK-IRI-02, DK-IRI-05, DK-CONF-01, DK-CONF-03."""
    document = source_json("iris/id_escaping")
    for index, element in enumerate(document["model"]["contents"]):
        element["name"] = "Completely changed name " + str(index)
    assert not fixture_issues(document)
    before = run("iris/id_escaping", iri_strategy="id")
    after = run(path=write_input(tmp_path, document), iri_strategy="id")
    assert before.outcome == after.outcome == "completed"
    assert set(before.ontology.subjects(RDF.type, OWL.Class)) == set(after.ontology.subjects(RDF.type, OWL.Class))


def test_all_members_of_name_collision_group_are_suffixed_deterministically(run):
    """Rules: DK-IRI-07, DK-CONF-01, DK-CONF-02."""
    first = run("iris/collisions")
    second = run("iris/collisions")
    assert first.outcome == second.outcome == "completed"
    actual = {one_subject(first.ontology, DCTERMS.identifier, Literal(i)) for i in ("c1", "c2", "c3")}
    assert actual == {BASE.Shared_1, BASE.Shared_2, BASE.Shared_3}
    assert (BASE.Shared, RDF.type, OWL.Class) not in first.ontology
    for identifier in ("c1", "c2", "c3"):
        assert one_subject(first.ontology, DCTERMS.identifier, Literal(identifier)) == one_subject(second.ontology, DCTERMS.identifier, Literal(identifier))


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("state,value", NAME_STATES)
def test_unnamed_class_uses_type_specific_fallback(run, source_json, tmp_path, input_policy, state, value):
    """Rules: DK-IRI-04, DK-IRI-05, DK-IRI-09, DK-LBL-01, DK-DIAG-01, DK-DIAG-05."""
    document = source_json("iris/fallbacks")
    _set_name(document["model"]["contents"][0], state, value)
    assert not fixture_issues(document)
    result = run(path=write_input(tmp_path, document), input_policy=input_policy)
    assert result.outcome == "completed"
    resource = one_subject(result.ontology, DCTERMS.identifier, Literal("cOwner"))
    assert resource == BASE.unnamedClass_cOwner
    warnings = [d for d in result.diagnostics if d.kind == "missing_name" and "cOwner" in d.source_ids]
    assert warnings and all(d.severity == "WARNING" for d in warnings)
    assert any("Class" in d.source_types and str(resource) in d.generated_iris and "stereotype:category" in d.facts for d in warnings)
    labels = set(result.ontology.objects(resource, RDFS.label))
    if value and value.strip():
        assert Literal(value) in labels  # retain unusable source wording
    elif value is not None:
        assert labels <= {Literal(value)}  # never require an invented replacement
    else:
        assert not labels


@pytest.mark.parametrize("state,value", MISSING_STATES)
def test_unnamed_class_in_id_mode_keeps_warning(run, source_json, tmp_path, state, value):
    """Rules: DK-IRI-02, DK-IRI-04, DK-DIAG-01."""
    document = source_json("iris/fallbacks")
    _set_name(document["model"]["contents"][0], state, value)
    result = run(path=write_input(tmp_path, document), iri_strategy="id")
    assert result.outcome == "completed"
    assert (BASE.cOwner, RDF.type, OWL.Class) in result.ontology
    assert any(d.kind == "missing_name" and d.severity == "WARNING" and "cOwner" in d.source_ids for d in result.diagnostics)


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("state,value", NAME_STATES)
def test_generic_attribute_fallback_keeps_name_strategy(run, source_json, tmp_path, input_policy, state, value):
    """Rules: DK-IRI-02, DK-IRI-04, DK-IRI-05, DK-IRI-09, DK-LBL-01, DK-DIAG-05."""
    document = source_json("iris/fallbacks")
    _set_name(document["model"]["contents"][0]["properties"][0], state, value)
    assert not fixture_issues(document)
    result = run(path=write_input(tmp_path, document), input_policy=input_policy)
    assert result.outcome == "completed"
    resource = one_subject(result.ontology, DCTERMS.identifier, Literal("aFallback"))
    assert resource == BASE.aFallback
    assert (BASE.Owner, RDF.type, OWL.Class) in result.ontology  # strategy did not switch
    assert (resource, RDF.type, OWL.DatatypeProperty) in result.ontology
    assert (resource, RDFS.domain, BASE.Owner) in result.ontology
    notices = [d for d in result.diagnostics if d.kind == "missing_name" and "aFallback" in d.identified_sources]
    assert notices and all(d.severity == "WARNING" for d in notices)
    assert any(str(resource) in d.generated_iris for d in notices)
    if value and value.strip():
        assert Literal(value) in set(result.ontology.objects(resource, RDFS.label))
    elif value is not None:
        assert set(result.ontology.objects(resource, RDFS.label)) <= {Literal(value)}
    else:
        assert not list(result.ontology.objects(resource, RDFS.label))


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("state,value", MISSING_STATES)
def test_generic_missing_name_in_id_mode_is_info(run, source_json, tmp_path, input_policy, state, value):
    """Rules: DK-IRI-02, DK-IRI-04, DK-DIAG-01, DK-DIAG-05."""
    document = source_json("iris/fallbacks")
    _set_name(document["model"]["contents"][0]["properties"][0], state, value)
    result = run(path=write_input(tmp_path, document), iri_strategy="id", input_policy=input_policy)
    assert result.outcome == "completed"
    assert (BASE.aFallback, RDF.type, OWL.DatatypeProperty) in result.ontology
    events = [d for d in result.diagnostics if d.kind == "missing_name" and "aFallback" in d.identified_sources]
    assert events and all(d.severity == "INFO" for d in events)


@pytest.mark.parametrize("name", [pytest.param("original", id="named"), pytest.param("東京", id="unusable_but_not_missing")])
def test_ordinary_id_use_has_no_diagnostic(run, source_json, tmp_path, name):
    """Rules: DK-IRI-04, DK-DIAG-01."""
    document = source_json("iris/fallbacks")
    document["model"]["contents"][0]["properties"][0]["name"] = name
    result = run(path=write_input(tmp_path, document), iri_strategy="id")
    assert result.outcome == "completed"
    assert not any(d.kind == "ordinary_id_use" for d in result.diagnostics)
    # This fixture has no other missing name. A forbidden event must not escape
    # the assertion merely because it omits a particular locator representation.
    assert not any(d.kind == "missing_name" for d in result.diagnostics)


@pytest.mark.parametrize("self_relation", [pytest.param(False,id="different_classes"), pytest.param(True,id="self_relation")])
@pytest.mark.parametrize("mode", ["all", "none"])
def test_relation_identity_uses_directional_end_ids(run, source_json, tmp_path, self_relation, mode):
    """Rules: DK-IRI-02, DK-IRI-06, DK-IRI-09, DK-INV-09, DK-CONF-02, DK-CONF-03."""
    document = source_json("shared/core_model")
    if self_relation:
        document["model"]["contents"][-1]["properties"][1]["propertyType"]["id"] = "cPerson"
    assert not fixture_issues(document)
    result = run(path=write_input(tmp_path, document), iri_strategy="id", inverse_properties=mode)
    assert result.outcome == "completed"
    assert (BASE.eTarget, RDF.type, OWL.ObjectProperty) in result.ontology
    assert (BASE.eTarget, RDFS.domain, BASE.cPerson) in result.ontology
    assert (BASE.eTarget, RDFS.range, BASE.cPerson if self_relation else BASE.cOrg) in result.ontology
    assert not any(result.ontology.triples((BASE.rWorks, None, None)))
    if mode == "all":
        assert (BASE.eSource, RDF.type, OWL.ObjectProperty) in result.ontology
        assert (BASE.eSource, OWL.inverseOf, BASE.eTarget) in result.ontology
        assert BASE.eTarget != BASE.eSource
    else:
        assert not any(result.ontology.triples((BASE.eSource, None, None)))


@pytest.mark.parametrize("strategy,omit", [pytest.param("name",False,id="name_default"),pytest.param("name",True,id="name_omit"),pytest.param("id",False,id="id_default"),pytest.param("id",True,id="id_omit_noop")])
def test_identifier_annotations_use_designated_targets_and_raw_values(run, strategy, omit):
    """Rules: DK-IRI-02, DK-IRI-06, DK-IRI-09; §15 identifier opt-out."""
    options = {"iri_strategy": strategy}
    if omit:
        options["omit_identifiers"] = True
    result = run(**options)
    assert result.outcome == "completed"
    if strategy == "name" and not omit:
        # Establish destinations without consulting any identifier annotation.
        # Property labels/relationships avoid choosing an optional qualification
        # convention for otherwise unique property names (DK-PROP-02).
        targets = {"cPerson": BASE.Person, "cOrg": BASE.Organization, "cAddress": BASE.Address}
        for identifier, label in (("aAge", "age"), ("aNote", "note"), ("aAddress", "address"), ("eTarget", "worksFor")):
            targets[identifier] = one_subject(result.ontology, RDFS.label, Literal(label))
        targets["eSource"] = one_subject(result.ontology, OWL.inverseOf, targets["eTarget"])
        assert len(set(targets.values())) == len(ELIGIBLE_IDS)
        assert all(isinstance(resource, URIRef) for resource in targets.values())
        for identifier in ("cPerson", "cOrg", "cAddress"):
            assert (targets[identifier], RDF.type, OWL.Class) in result.ontology
        for identifier, kind, domain, value_range in (
            ("aAge", OWL.DatatypeProperty, BASE.Person, XSD.int),
            ("aNote", OWL.DatatypeProperty, BASE.Person, None),
            ("aAddress", OWL.ObjectProperty, BASE.Person, BASE.Address),
            ("eTarget", OWL.ObjectProperty, BASE.Person, BASE.Organization),
            ("eSource", OWL.ObjectProperty, BASE.Organization, BASE.Person),
        ):
            resource = targets[identifier]
            assert (resource, RDF.type, kind) in result.ontology
            assert set(result.ontology.objects(resource, RDFS.domain)) == {domain}
            assert set(result.ontology.objects(resource, RDFS.range)) == (set() if value_range is None else {value_range})
    for identifier in ELIGIBLE_IDS:
        if strategy == "name" and not omit:
            assert set(result.ontology.subjects(DCTERMS.identifier, Literal(identifier))) == {targets[identifier]}
        elif strategy == "id":
            assert (BASE[identifier], DCTERMS.identifier, Literal(identifier)) not in result.ontology
        else:
            assert not list(result.ontology.subjects(DCTERMS.identifier, Literal(identifier)))
    for excluded in ("projectOne", "projectOne_root", "rWorks", "dInt"):
        assert not list(result.ontology.subjects(DCTERMS.identifier, Literal(excluded)))


@pytest.mark.parametrize("language", [pytest.param(None,id="no_override"),pytest.param("nl",id="override_excluded")])
def test_identifiers_are_unescaped_untagged_source_strings(run, language):
    """Rules: DK-IRI-05, DK-IRI-09, DK-LBL-02."""
    options = {} if language is None else {"language": language}
    result = run("iris/id_escaping", **options)
    assert result.outcome == "completed"
    for identifier, _ in ESCAPED_IDS:
        subject = one_subject(result.ontology, DCTERMS.identifier, Literal(identifier))
        assert (subject, DCTERMS.identifier, Literal(identifier)) in result.ontology


@pytest.mark.parametrize("strategy", ["name", "id"])
def test_omit_identifiers_changes_only_rd28_annotations(run, strategy):
    """Rules: DK-IRI-09, DK-CONF-01; §15 identifier opt-out."""
    enabled = run(iri_strategy=strategy)
    omitted = run(iri_strategy=strategy, omit_identifiers=True)
    assert enabled.outcome == omitted.outcome == "completed"
    assert diagnostic_signatures(enabled.diagnostics) == diagnostic_signatures(omitted.diagnostics)
    expected = Graph()
    for triple in enabled.ontology:
        if triple[1] != DCTERMS.identifier or triple[2] not in {Literal(i) for i in ELIGIBLE_IDS}:
            expected.add(triple)
    assert_selected_equal(omitted.ontology, expected, FIXED_PREDICATES, {OWL.disjointWith})


def test_source_backed_iris_stay_fixed_across_inverse_modes(run, source_json, tmp_path):
    """Rules: DK-IRI-07, DK-IRI-09, DK-INV-07, DK-INV-10, DK-CONF-01, DK-CONF-02."""
    document = source_json("shared/property_collisions")
    claim = copy.deepcopy(document["model"]["contents"][1])
    claim.update(id="cWorkers", name="workers", properties=None)
    document["model"]["contents"].append(claim)
    assert not fixture_issues(document)
    path = write_input(tmp_path, document)
    source_ids = ("cPerson", "cOrg", "cAddress", "cWorkers", "a1", "a2", "a3", "eTarget")
    observations = [run(path=path, inverse_properties=mode) for mode in ("none", "named", "informed", "all")]
    assert all(r.outcome == "completed" for r in observations)
    baseline = {i: one_subject(observations[0].ontology, DCTERMS.identifier, Literal(i)) for i in source_ids}
    for result in observations[1:]:
        assert {i: one_subject(result.ontology, DCTERMS.identifier, Literal(i)) for i in source_ids} == baseline


def test_fallbacks_reuse_id_escaping_with_prefix_specific_digit_protection(run, source_json, tmp_path):
    """Rules: DK-IRI-04, DK-IRI-05, DK-IRI-09, DK-CONF-03."""
    document = source_json("iris/fallbacks")
    owner = document["model"]["contents"][0]
    owner.update(id="9.owner", name=None)
    owner["properties"][0].update(id="9_A", name=None)
    assert not fixture_issues(document)
    result = run(path=write_input(tmp_path, document))
    assert result.outcome == "completed"
    assert one_subject(result.ontology, DCTERMS.identifier, Literal("9.owner")) == BASE.unnamedClass_9_x2Eowner
    assert one_subject(result.ontology, DCTERMS.identifier, Literal("9_A")) == BASE.id_9_x5FA


def test_anonymous_constraints_and_containers_get_no_source_id_resources(run, source_json, tmp_path):
    """Rules: DK-IRI-09, DK-GEN-01, DK-GEN-06; DK-ATT-03 for the fixture's restriction."""
    document = source_json("shared/core_model")
    document["model"]["contents"][0]["properties"][0]["cardinality"] = "1"
    result = run(path=write_input(tmp_path, document))
    assert result.outcome == "completed"
    restrictions = set(result.ontology.subjects(RDF.type, OWL.Restriction))
    assert restrictions
    for node in restrictions:
        assert not list(result.ontology.objects(node, DCTERMS.identifier))
    for excluded in ("projectOne", "projectOne_root", "rWorks", "dInt"):
        assert not list(result.ontology.subjects(DCTERMS.identifier, Literal(excluded)))


def test_generic_fallback_collisions_do_not_merge_source_backed_resources(run, source_json, tmp_path):
    """Rules: DK-IRI-04, DK-IRI-07, DK-IRI-09, DK-CONF-01, DK-CONF-02."""
    document = source_json("iris/fallbacks")
    owner = document["model"]["contents"][0]
    owner["properties"][0]["name"] = None
    claim = copy.deepcopy(owner)
    claim.update(id="cClaim", name="aFallback", properties=None)
    document["model"]["contents"].append(claim)
    assert not fixture_issues(document)
    path = write_input(tmp_path, document)
    first = run(path=path)
    again = run(path=path)
    assert first.outcome == again.outcome == "completed"
    generated_property = one_subject(first.ontology, DCTERMS.identifier, Literal("aFallback"))
    generated_class = one_subject(first.ontology, DCTERMS.identifier, Literal("cClaim"))
    assert generated_property != generated_class
    assert (generated_property, RDF.type, OWL.DatatypeProperty) in first.ontology
    assert (generated_class, RDF.type, OWL.Class) in first.ontology
    for identifier in ("aFallback", "cClaim"):
        assert one_subject(first.ontology, DCTERMS.identifier, Literal(identifier)) == one_subject(again.ontology, DCTERMS.identifier, Literal(identifier))
