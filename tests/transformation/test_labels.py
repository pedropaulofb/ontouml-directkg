"""Shared source-text placement, language carriers, and multilingual selection."""

import copy

import pytest
from rdflib import Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, XSD

from tests.support.data import fixture_issues, source_element, source_elements, write_input
from tests.support.invocation import diagnostic_record_counts, diagnostic_signatures
from tests.support.rdf import assert_graph_equal, assert_selected_equal, one_subject


BASE = Namespace("https://example.test/model#")
ONTOLOGY = URIRef("https://example.test/model")
POLICIES = ["strict", "tolerant", "best-effort"]
TEXT_TARGETS = [
    ("class_name", "cPerson", "name", RDFS.label, BASE.cPerson),
    ("custom_datatype_name", "cAddress", "name", RDFS.label, BASE.cAddress),
    ("enum_name", "eStatus", "name", RDFS.label, BASE.eStatus),
    ("attribute_name", "aAge", "name", RDFS.label, BASE.aAge),
    ("relation_name", "rWorks", "name", RDFS.label, BASE.eTarget),
    ("target_role_name", "eTarget", "name", RDFS.label, BASE.eTarget),
    ("inverse_role_name", "eSource", "name", RDFS.label, BASE.eSource),
    ("literal_name", "vPending", "name", RDFS.label, BASE.vPending),
    ("class_description", "cPerson", "description", RDFS.comment, BASE.cPerson),
    ("custom_datatype_description", "cAddress", "description", RDFS.comment, BASE.cAddress),
    ("enum_description", "eStatus", "description", RDFS.comment, BASE.eStatus),
    ("attribute_description", "aAge", "description", RDFS.comment, BASE.aAge),
    ("relation_description", "rWorks", "description", RDFS.comment, BASE.eTarget),
    ("target_end_description", "eTarget", "description", RDFS.comment, BASE.eTarget),
    ("source_end_description", "eSource", "description", RDFS.comment, BASE.eSource),
    ("literal_description", "vPending", "description", RDFS.comment, BASE.vPending),
]
FIXED = {RDF.type, RDFS.domain, RDFS.range, RDFS.label, DCTERMS.identifier,
         RDFS.subClassOf, RDFS.subPropertyOf, OWL.inverseOf, OWL.equivalentClass,
         OWL.equivalentProperty, OWL.propertyChainAxiom}


def _localize_other_text(document):
    """Explicit case edit: prevent unrelated plain text causing ambiguity.

    This does not change loader behavior or assign languages in production.
    The root remains the VP Project/model structure, with only RD-27 carriers.
    """
    for item in source_elements(document):
        for field in ("name", "description"):
            if isinstance(item.get(field), str) and item[field]:
                item[field] = {"en": item[field]}


def _assert_source_values(graph, target, predicate, values, *, exclusive=True):
    """Match source lexical values exactly while allowing generated comments."""
    lexical = {str(value) for value in values}
    actual = {value for value in graph.objects(target, predicate) if str(value) in lexical}
    assert actual == set(values)
    if exclusive:
        for value in values:
            assert set(graph.subjects(predicate, value)) == {target}


@pytest.mark.parametrize("case,identifier,field,predicate,target", TEXT_TARGETS, ids=[row[0] for row in TEXT_TARGETS])
@pytest.mark.parametrize("carrier", ["plain", "localized", "override"])
def test_source_text_has_exact_lexical_value_and_designated_target(run, source_json, tmp_path, case, identifier, field, predicate, target, carrier):
    """Rules: DK-LBL-01, DK-LBL-02, DK-IRI-08.

    Labels/descriptions use ID mode so the target is established without the
    literal under test. Markup, ampersand, line break and Unicode are retained.
    """
    document = source_json("shared/source_text")
    _localize_other_text(document)
    if identifier == "eTarget" and field == "name":
        source_element(document, "rWorks")["name"] = None
    first = "  <em>" + case + " & café</em>\nOriginal line.\t "
    second = "\n<p>" + case + " & português</p>  "
    selected = source_element(document, identifier)
    if carrier == "plain":
        selected[field] = first
        values = {Literal(first)}
        options = {}
    else:
        selected[field] = {"en": first, "pt-BR": second}
        options = {"language": "nl"} if carrier == "override" else {}
        values = {Literal(first, lang="nl" if options else "en"), Literal(second, lang="nl" if options else "pt-BR")}
    assert not fixture_issues(document)
    result = run(path=write_input(tmp_path, document), iri_strategy="id", **options)
    assert result.outcome == "completed"
    _assert_source_values(result.ontology, target, predicate, values)
    assert not any(d.kind == "ambiguous_language" or d.severity == "ERROR" for d in result.diagnostics)


LANGUAGE_CASES = [
    pytest.param("Texto français, 日本語", None, None, {Literal("Texto français, 日本語")}, False, id="plain_no_guess_or_exporter_english"),
    pytest.param("Single language", ["fr"], None, {Literal("Single language", lang="fr")}, False, id="single_project_language"),
    pytest.param("Multiple choices", ["en", "pt-BR"], None, {Literal("Multiple choices")}, True, id="ambiguous_plain"),
    pytest.param({"en": "Local English", "pt-BR": "Local Português"}, None, None, {Literal("Local English", lang="en"), Literal("Local Português", lang="pt-BR")}, False, id="independent_local_values"),
    pytest.param({"": "Unknown local"}, ["de"], None, {Literal("Unknown local", lang="de")}, False, id="empty_key_inherits_single_project"),
    pytest.param({"": "Unknown multiple"}, ["en", "pt-BR"], None, {Literal("Unknown multiple")}, True, id="ambiguous_empty_key"),
    pytest.param({"": "Unknown only"}, None, None, {Literal("Unknown only")}, False, id="empty_key_is_not_language"),
    pytest.param({"": "Unknown mixed", "en": "Known mixed"}, ["de"], None, {Literal("Unknown mixed", lang="de"), Literal("Known mixed", lang="en")}, False, id="mixed_local_and_unknown_single_project"),
    pytest.param({"": "Unknown mixed", "en": "Known mixed"}, ["en", "de"], None, {Literal("Unknown mixed"), Literal("Known mixed", lang="en")}, True, id="mixed_local_and_unknown_multiple_project"),
    pytest.param({"en": "Explicit local"}, ["fr"], None, {Literal("Explicit local", lang="en")}, False, id="local_over_project"),
    pytest.param({"en": "Explicit local"}, ["fr", "de"], None, {Literal("Explicit local", lang="en")}, False, id="localized_over_multiple_project"),
    pytest.param({"en": "Overridden English", "pt-BR": "Overridden Português"}, ["de"], "nl", {Literal("Overridden English", lang="nl"), Literal("Overridden Português", lang="nl")}, False, id="override_over_local_and_project"),
    pytest.param({"": "Override unknown"}, ["en", "pt-BR"], "nl", {Literal("Override unknown", lang="nl")}, False, id="override_resolves_multiple"),
    pytest.param("No declared choices", [], None, {Literal("No declared choices")}, False, id="empty_project_languages"),
]


@pytest.mark.parametrize("field,predicate", [("name", RDFS.label), ("description", RDFS.comment)], ids=["name", "description"])
@pytest.mark.parametrize("text,languages,override,values,ambiguous", LANGUAGE_CASES)
def test_language_precedence_preserves_each_source_value(run, source_json, tmp_path, field, predicate, text, languages, override, values, ambiguous):
    """Rules: DK-LBL-01, DK-LBL-02, DK-DIAG-19; §3.2 bounded language enrichment."""
    document = source_json("shared/source_text")
    _localize_other_text(document)
    source_element(document, "cPerson")[field] = text
    if languages is not None:
        document["languages"] = languages
    result = run(path=write_input(tmp_path, document), iri_strategy="id", **({"language": override} if override else {}))
    assert result.outcome == "completed"
    _assert_source_values(result.ontology, BASE.cPerson, predicate, values)
    notices = [d for d in result.diagnostics if d.kind == "ambiguous_language"]
    if ambiguous:
        assert notices and all(d.severity == "WARNING" for d in notices)
        assert any({"multiple_project_languages", "language_unresolved"} <= d.facts for d in notices)
    else:
        assert not notices
    assert not any(d.severity == "ERROR" for d in result.diagnostics)


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("empty_key", [False, True], ids=["plain", "unknown_key"])
def test_language_ambiguity_is_nonfatal_under_every_input_policy(run, source_json, tmp_path, input_policy, empty_key):
    """Rules: DK-LBL-02, DK-DIAG-19, DK-DIAG-05."""
    document = source_json("shared/source_text")
    _localize_other_text(document)
    document["languages"] = ["en", "pt-BR"]
    for identifier in ("cPerson", "aAge", "vPending"):
        text = "Ambiguous " + identifier
        source_element(document, identifier)["description"] = {"": text} if empty_key else text
    result = run(path=write_input(tmp_path, document), iri_strategy="id", input_policy=input_policy)
    assert result.outcome == "completed"
    for identifier in ("cPerson", "aAge", "vPending"):
        _assert_source_values(result.ontology, BASE[identifier], RDFS.comment, {Literal("Ambiguous " + identifier)})
    notices = [d for d in result.diagnostics if d.kind == "ambiguous_language"]
    assert notices and all(d.severity == "WARNING" for d in notices)
    assert any({"multiple_project_languages", "language_unresolved"} <= d.facts for d in notices)
    # Consolidation is permitted; there is deliberately no per-literal count.
    assert not any(d.severity == "ERROR" for d in result.diagnostics)


@pytest.mark.parametrize("identifier,target", [("cPerson", BASE.cPerson), ("aAge", BASE.aAge), ("rWorks", BASE.eTarget), ("eTarget", BASE.eTarget), ("eSource", BASE.eSource), ("vPending", BASE.vPending)], ids=["class", "attribute", "relation", "target_end", "source_end", "literal"])
@pytest.mark.parametrize("condition", ["absent", "null", "empty"])
def test_missing_descriptions_add_neither_annotation_nor_diagnostic(run, source_json, tmp_path, identifier, target, condition):
    """Rules: DK-LBL-02."""
    document = source_json("shared/source_text")
    selected = source_element(document, identifier)
    original = selected["description"]
    baseline = run("shared/source_text", iri_strategy="id")
    if condition == "absent":
        del selected["description"]
    else:
        selected["description"] = None if condition == "null" else ""
    result = run(path=write_input(tmp_path, document), iri_strategy="id")
    assert baseline.outcome == result.outcome == "completed"
    assert not list(result.ontology.subjects(RDFS.comment, Literal(original)))
    assert not (target, RDFS.comment, Literal("")) in result.ontology
    assert diagnostic_signatures(result.diagnostics) == diagnostic_signatures(baseline.diagnostics)
    assert_selected_equal(result.ontology, baseline.ontology, FIXED, {OWL.disjointWith})


@pytest.mark.parametrize("inverse_mode", ["named", "none"])
def test_relation_and_end_descriptions_are_independent_and_do_not_force_inverse(run, source_json, inverse_mode):
    """Rules: DK-LBL-02."""
    document = source_json("shared/source_text")
    result = run("shared/source_text", iri_strategy="id", inverse_properties=inverse_mode)
    assert result.outcome == "completed"
    for identifier in ("rWorks", "eTarget"):
        value = Literal(source_element(document, identifier)["description"])
        assert set(result.ontology.subjects(RDFS.comment, value)) == {BASE.eTarget}
    source_value = Literal(source_element(document, "eSource")["description"])
    assert set(result.ontology.subjects(RDFS.comment, source_value)) == ({BASE.eSource} if inverse_mode == "named" else set())
    if inverse_mode == "none":
        assert not list(result.ontology.triples((None, OWL.inverseOf, None)))
        assert not any(BASE.eSource in triple for triple in result.ontology)
    assert not any(d.kind == "omitted_description" for d in result.diagnostics)


def test_primitive_description_has_no_external_or_synthetic_host(run, source_json):
    """Rules: DK-LBL-02, DK-CLS-01."""
    source = source_json("shared/source_text")
    result = run("shared/source_text", iri_strategy="id")
    assert result.outcome == "completed"
    value = Literal(source_element(source, "dInt")["description"])
    assert not list(result.ontology.subjects(RDFS.comment, value))
    assert not list(result.ontology.objects(XSD.int, RDFS.comment))
    assert not any(BASE.dInt in triple for triple in result.ontology)
    assert not list(result.ontology.subjects(DCTERMS.identifier, Literal("dInt")))
    assert (BASE.aAge, RDFS.range, XSD.int) in result.ontology


SELECTOR_CASES = [
    pytest.param({"pt-BR": "Pessoa", "en": "Person"}, "Person", id="language_key_order"),
    pytest.param({"": "Unknown first", "en": "English second"}, "Unknown_first", id="empty_key_first"),
    pytest.param({"": "東京", "de": "Nutzer", "en": "Person"}, "Nutzer", id="skip_unusable_earlier_key"),
    pytest.param({"EN": "Zebra", "en": "Alfa"}, "Alfa", id="ascii_case_fold_text_tie"),
    pytest.param({"eN": "alpha", "En": "Beta"}, "Beta", id="original_text_case_order"),
    pytest.param({"EN": "z", "en": "Longer"}, "Longer", id="text_order_not_length"),
    pytest.param({"EN": "éclair", "en": "zoo"}, "zoo", id="unicode_text_before_normalization"),
    pytest.param({"EN": "Same", "en": "Same"}, "Same", id="identical_text_no_further_tie"),
    pytest.param({"de": "___", "en": "Café au lait"}, "Cafe_au_lait", id="normalize_selected_original"),
]


@pytest.mark.parametrize("identifier,prefix", [("cPerson", ""), ("aAge", ""), ("vPending", "Status_")], ids=["class", "attribute", "enum_value"])
@pytest.mark.parametrize("text,selected", SELECTOR_CASES)
def test_multilingual_selector_uses_original_keys_text_and_usable_candidates(run, source_json, tmp_path, identifier, prefix, text, selected):
    """Rules: DK-IRI-10, DK-IRI-03, DK-IRI-08, DK-PROP-02, DK-LBL-01, DK-LBL-02.

    Expected local names are explicit case data, not a test-side transformer.
    Check JSON order, user override and project languages independently of
    naming, retaining every original label in each observation.
    """
    for context, options in [("default", {}), ("override", {"language": "nl"}), ("project", {})]:
        for reverse in (False, True):
            document = source_json("shared/source_text")
            _localize_other_text(document)
            if identifier == "aAge":
                # Force owner qualification, whose spelling is required by
                # DK-PROP-02; a unique unqualified candidate is only optional.
                source_element(document, "cPerson")["name"] = {"en": "AttributeOwner"}
            source_element(document, identifier)["name"] = dict(reversed(list(text.items()))) if reverse else copy.deepcopy(text)
            if identifier == "aAge":
                peer = copy.deepcopy(source_element(document, "aAge"))
                peer["id"] = "pSelectorPeer"
                source_element(document, "cOrg")["properties"] = [peer]
            assert not fixture_issues(document)
            if context == "project":
                document["languages"] = ["pt-BR", "en"]
            result = run(path=write_input(tmp_path, document, context + str(reverse) + ".json"), **options)
            assert result.outcome == "completed"
            target = BASE[selected + "_AttributeOwner"] if identifier == "aAge" else BASE[prefix + selected]
            assert (target, RDF.type, OWL.NamedIndividual if identifier == "vPending" else OWL.DatatypeProperty if identifier == "aAge" else OWL.Class) in result.ontology
            if identifier == "aAge":
                assert (target, RDFS.domain, BASE.AttributeOwner) in result.ontology
                assert (BASE[selected + "_Organization"], RDF.type, OWL.DatatypeProperty) in result.ontology
                assert (BASE[selected + "_Organization"], RDFS.domain, BASE.Organization) in result.ontology
            expected = set()
            for key, value in text.items():
                language = "nl" if context == "override" else key or None
                expected.add(Literal(value, lang=language))
            _assert_source_values(result.ontology, target, RDFS.label, expected, exclusive=False)
            assert not any(d.severity == "ERROR" for d in result.diagnostics)
            if "" not in text:
                assert not any(d.kind == "ambiguous_language" for d in result.diagnostics)


@pytest.mark.parametrize("identifier", ["cPerson", "aAge", "vPending"], ids=["class", "attribute", "enum_value"])
def test_localized_name_selection_does_not_replace_id_strategy(run, source_json, tmp_path, identifier):
    """Rules: DK-IRI-02, DK-IRI-08, DK-IRI-09, DK-IRI-10, DK-LBL-01, DK-LBL-02."""
    document = source_json("shared/source_text")
    _localize_other_text(document)
    source_element(document, identifier)["name"] = {"pt-BR": "Pessoa", "en": "Person"}
    result = run(path=write_input(tmp_path, document), iri_strategy="id", language="nl")
    assert result.outcome == "completed"
    target = BASE[identifier]
    _assert_source_values(result.ontology, target, RDFS.label, {Literal("Pessoa", lang="nl"), Literal("Person", lang="nl")}, exclusive=False)
    assert (target, RDF.type, OWL.NamedIndividual if identifier == "vPending" else OWL.DatatypeProperty if identifier == "aAge" else OWL.Class) in result.ontology
    assert not list(result.ontology.subjects(DCTERMS.identifier, Literal(identifier)))


def test_language_override_does_not_propagate_to_generated_comments_or_identifiers(run, source_json, tmp_path):
    """Rules: DK-LBL-02, DK-CLS-05, DK-IRI-09."""
    document = source_json("shared/source_text")
    source_element(document, "cPerson")["order"] = "*"
    path = write_input(tmp_path, document)
    ordinary = run(path=path, iri_strategy="id")
    overridden = run(path=path, iri_strategy="id", language="nl")
    assert ordinary.outcome == overridden.outcome == "completed"
    for result in (ordinary, overridden):
        assert (BASE.cPerson, RDFS.comment, Literal("OntoUML classifier order: orderless (*).", lang="en")) in result.ontology
        assert all(value.language is None for value in result.ontology.objects(None, DCTERMS.identifier))
    # Normalize only meanings of actual produced comments; no fixed wording or
    # default language for the otherwise unspecified flag comments is imposed.
    ordinary_comments = {(c.subject, c.field, c.value, c.literal) for c in ordinary.comments}
    overridden_comments = {(c.subject, c.field, c.value, c.literal) for c in overridden.comments}
    assert ordinary_comments
    for result in (ordinary, overridden):
        assert all((c.subject, RDFS.comment, c.literal) in result.ontology for c in result.comments)
    assert overridden_comments == ordinary_comments
    assert (BASE.cPerson, RDFS.label, Literal("Person", lang="nl")) in overridden.ontology


_SIMPLIFIED_LEXICAL_TAGS = [
    pytest.param("qqq", True, id="non_iana_alpha"),
    pytest.param("en-123456789", True, id="long_alnum_subtag"),
    pytest.param("a-0", True, id="short_alnum_subtag"),
    pytest.param("Z-0-aB9", True, id="mixed_case_multi_subtag"),
    pytest.param("en\n", False, id="trailing_newline"),
    pytest.param("123", False, id="leading_digit"),
    pytest.param("en_US", False, id="underscore"),
    pytest.param("en ", False, id="trailing_space"),
    pytest.param(" en", False, id="leading_space"),
    pytest.param("en--US", False, id="double_hyphen"),
    pytest.param("-en", False, id="leading_hyphen"),
    pytest.param("en-", False, id="trailing_hyphen"),
    pytest.param("en@latn", False, id="at_sign"),
    pytest.param("bad tag", False, id="interior_space"),
    pytest.param("   ", False, id="whitespace_only"),
]


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("carrier_kind", ["language_string", "project_languages"])
@pytest.mark.parametrize("tag,valid", _SIMPLIFIED_LEXICAL_TAGS)
def test_simplified_lexical_language_tags_accept_turtle_langtag_and_reject_invalid_tags(
        run, source_json, tmp_path, input_policy, carrier_kind, tag, valid):
    """Rules: DK-LBL-02, DK-LBL-01, DK-GEN-08, DK-DIAG-01, DK-DIAG-04, DK-DIAG-05; §3.2. RD-02 Alts 1A+2A."""
    document = source_json("shared/source_text")
    _localize_other_text(document)
    if carrier_kind == "language_string":
        source_element(document, "cPerson")["name"] = {tag: "Person"}
        expected_fact = "invalid_language_string_entry"
    else:
        document["languages"] = [tag]
        source_element(document, "cPerson")["name"] = "Person"
        expected_fact = "project_languages_invalid_entry"

    result = run(path=write_input(tmp_path, document), iri_strategy="id", input_policy=input_policy)
    assert all(d.code != "INTERNAL_TRANSFORMATION_FAILURE" for d in result.diagnostics), result.diagnostics
    assert not any(d.code == "UNKNOWN_INFORMATION" for d in result.diagnostics), result.diagnostics

    if valid:
        assert result.outcome == "completed"
        assert not any(d.severity == "ERROR" for d in result.diagnostics)
        assert (BASE.cPerson, RDFS.label, Literal("Person", lang=tag)) in result.ontology
        return

    assert any(d.severity == "ERROR" and expected_fact in d.facts for d in result.diagnostics), result.diagnostics
    if input_policy != "best-effort":
        assert result.outcome == "aborted" and result.ontology is None
        return

    assert result.outcome == "completed-with-errors"
    assert (BASE.cPerson, RDF.type, OWL.Class) in result.ontology
    if carrier_kind == "language_string":
        assert not list(result.ontology.objects(BASE.cPerson, RDFS.label))
    else:
        assert set(result.ontology.objects(BASE.cPerson, RDFS.label)) == {Literal("Person")}


@pytest.mark.parametrize("input_policy", POLICIES)
def test_empty_string_values_and_empty_key_in_language_string_keep_existing_behavior(
        run, source_json, tmp_path, input_policy):
    """Rules: DK-LBL-01, DK-LBL-02, DK-DIAG-05; §3.2. RD-02 Alternative 1A."""
    document = source_json("shared/source_text")
    _localize_other_text(document)
    source_element(document, "cPerson")["name"] = {"": "Person", "en": ""}
    source_element(document, "cPerson")["description"] = {"en": "", "fr": ""}
    result = run(path=write_input(tmp_path, document), iri_strategy="id", input_policy=input_policy)
    assert result.outcome == "completed"
    assert not any(d.severity == "ERROR" for d in result.diagnostics)
    assert set(result.ontology.objects(BASE.cPerson, RDFS.label)) == {Literal("Person")}
    assert not [v for v in result.ontology.objects(BASE.cPerson, RDFS.comment)
                if "Description" in str(v) or str(v) == ""]


_CARRIER_TARGETS = [
    ("project_name", "projectOne", "name", RDFS.label, ONTOLOGY),
    ("project_description", "projectOne", "description", RDFS.comment, ONTOLOGY),
    ("class_name", "cPerson", "name", RDFS.label, BASE.cPerson),
    ("class_description", "cPerson", "description", RDFS.comment, BASE.cPerson),
    ("custom_datatype_name", "cAddress", "name", RDFS.label, BASE.cAddress),
    ("custom_datatype_description", "cAddress", "description", RDFS.comment, BASE.cAddress),
    ("attribute_name", "aAge", "name", RDFS.label, BASE.aAge),
    ("attribute_description", "aAge", "description", RDFS.comment, BASE.aAge),
    ("relation_name", "rWorks", "name", RDFS.label, BASE.eTarget),
    ("relation_description", "rWorks", "description", RDFS.comment, BASE.eTarget),
    ("target_end_name", "eTarget", "name", RDFS.label, BASE.eTarget),
    ("source_end_description", "eSource", "description", RDFS.comment, BASE.eSource),
    ("literal_name", "vPending", "name", RDFS.label, BASE.vPending),
    ("literal_description", "vPending", "description", RDFS.comment, BASE.vPending),
]


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("bad_value", [123, True, ["bad"]], ids=["int", "bool", "array"])
@pytest.mark.parametrize("case,identifier,field,predicate,target", _CARRIER_TARGETS,
                         ids=[row[0] for row in _CARRIER_TARGETS])
def test_malformed_textual_carrier_whole_field_types_follow_policy(
        run, source_json, tmp_path, input_policy, bad_value,
        case, identifier, field, predicate, target):
    """Rules: DK-LBL-01, DK-LBL-02, DK-GEN-08, DK-IRI-04, DK-DIAG-01, DK-DIAG-04, DK-DIAG-05; §§3.2, 15. RD-02 Alt 1A."""
    document = source_json("shared/source_text")
    _localize_other_text(document)
    if case == "relation_name":
        source_element(document, "eTarget")["name"] = None
    elif case == "target_end_name":
        source_element(document, "rWorks")["name"] = None
    elif case == "relation_description":
        source_element(document, "eTarget")["description"] = None

    source_element(document, identifier)[field] = copy.deepcopy(bad_value)
    use_override = bad_value == 123
    options = {"iri_strategy": "id", "input_policy": input_policy}
    if use_override:
        options["language"] = "nl"

    result = run(path=write_input(tmp_path, document), **options)
    assert all(d.code != "INTERNAL_TRANSFORMATION_FAILURE" for d in result.diagnostics), result.diagnostics
    assert not any(d.code == "UNKNOWN_INFORMATION" for d in result.diagnostics), result.diagnostics
    assert any(
        d.severity == "ERROR" and "malformed_textual_carrier" in d.facts
        for d in result.diagnostics
    ), result.diagnostics

    if input_policy != "best-effort":
        assert result.outcome == "aborted" and result.ontology is None
        return

    assert result.outcome == "completed-with-errors"
    assert (BASE.cOrg, RDF.type, OWL.Class) in result.ontology
    assert (BASE.cOrg, RDFS.label, Literal("Organization", lang="nl" if use_override else "en")) in result.ontology
    if identifier != "projectOne":
        assert any(target in triple for triple in result.ontology)
    if predicate == RDFS.label:
        assert not list(result.ontology.objects(target, RDFS.label))
    else:
        forbidden_fragments = ("Project", "Pending", "Description " + identifier, str(bad_value))
        assert not [v for v in result.ontology.objects(target, RDFS.comment)
                    if str(v) == "" or any(fragment in str(v) for fragment in forbidden_fragments)]


_LANGSTRING_MUTATIONS = [
    ("sibling_invalid_key", {"bad tag": "WrongSibling", "en": "ValidSibling"}, "ValidSibling", "en"),
    ("sibling_non_string_value", {"en": 42, "pt-BR": "TextoValido"}, "TextoValido", "pt-BR"),
    ("zero_valid_invalid_key", {"bad tag": "OnlyWrong"}, None, None),
]

_ZERO_VALID_EDGE_MUTATIONS = [
    ("newline_key", {"en\n": "NewlineWrong"}),
    ("blank_key", {"   ": "BlankWrong"}),
    ("non_string_and_empty", {"en": 42, "fr": ""}),
    ("null_value", {"en": None}),
    ("bool_value", {"en": True}),
    ("list_value", {"en": ["nested"]}),
    ("dict_value", {"en": {"nested": "bad"}}),
]

_REPRESENTATIVE_CARRIERS = [
    ("project_name", "projectOne", "name", RDFS.label, ONTOLOGY),
    ("project_description", "projectOne", "description", RDFS.comment, ONTOLOGY),
    ("class_name", "cPerson", "name", RDFS.label, BASE.cPerson),
    ("custom_datatype_description", "cAddress", "description", RDFS.comment, BASE.cAddress),
    ("attribute_name", "aAge", "name", RDFS.label, BASE.aAge),
    ("relation_name", "rWorks", "name", RDFS.label, BASE.eTarget),
    ("source_end_description", "eSource", "description", RDFS.comment, BASE.eSource),
    ("literal_name", "vPending", "name", RDFS.label, BASE.vPending),
]


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("iri_strategy", ["name", "id"])
@pytest.mark.parametrize("entry_case,payload,surviving_text,surviving_lang", _LANGSTRING_MUTATIONS,
                         ids=[row[0] for row in _LANGSTRING_MUTATIONS])
@pytest.mark.parametrize("target_case,identifier,field,predicate,id_target", _REPRESENTATIVE_CARRIERS,
                         ids=[row[0] for row in _REPRESENTATIVE_CARRIERS])
def test_invalid_language_string_entries_follow_policy_and_preserve_siblings(
        run, source_json, tmp_path, input_policy, iri_strategy,
        entry_case, payload, surviving_text, surviving_lang,
        target_case, identifier, field, predicate, id_target):
    """Rules: DK-LBL-01, DK-LBL-02, DK-GEN-08, DK-IRI-04, DK-IRI-08, DK-IRI-10, DK-DIAG-01, DK-DIAG-04, DK-DIAG-05; §§3.2, 15. RD-02 Alt 1A."""
    for use_override in (False, True):
        document = source_json("shared/source_text")
        _localize_other_text(document)
        if target_case == "relation_name":
            source_element(document, "eTarget")["name"] = None
        source_element(document, identifier)[field] = copy.deepcopy(payload)
        options = {"iri_strategy": iri_strategy, "input_policy": input_policy}
        if use_override:
            options["language"] = "nl"

        result = run(path=write_input(tmp_path, document, f"{use_override}.json"), **options)
        assert all(d.code != "INTERNAL_TRANSFORMATION_FAILURE" for d in result.diagnostics), result.diagnostics
        assert not any(d.code == "UNKNOWN_INFORMATION" for d in result.diagnostics), result.diagnostics
        assert any(
            d.severity == "ERROR" and "invalid_language_string_entry" in d.facts
            for d in result.diagnostics
        ), result.diagnostics

        if input_policy != "best-effort":
            assert result.outcome == "aborted" and result.ontology is None
            continue

        assert result.outcome == "completed-with-errors"
        if identifier == "projectOne":
            target = ONTOLOGY
        elif iri_strategy == "id":
            target = id_target
        else:
            target = one_subject(result.ontology, DCTERMS.identifier, Literal(id_target.removeprefix(str(BASE))))

        for bad_val in ("WrongSibling", "OnlyWrong"):
            assert not any(bad_val in str(term) for triple in result.ontology for term in triple)

        expected_lang = "nl" if use_override else surviving_lang
        if surviving_text is not None:
            assert Literal(surviving_text, lang=expected_lang) in set(result.ontology.objects(target, predicate))
        else:
            if predicate == RDFS.label:
                assert not list(result.ontology.objects(target, RDFS.label))
            else:
                forbidden_fragments = ("Project", "Pending", "Description " + identifier, "OnlyWrong")
                assert not [v for v in result.ontology.objects(target, RDFS.comment)
                            if str(v) == "" or any(fragment in str(v) for fragment in forbidden_fragments)]
            if field == "name" and identifier == "cPerson" and iri_strategy == "name":
                assert target == BASE.unnamedClass_cPerson


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("entry_case,payload", _ZERO_VALID_EDGE_MUTATIONS,
                         ids=[row[0] for row in _ZERO_VALID_EDGE_MUTATIONS])
def test_invalid_language_string_edge_values_and_keys_follow_policy(
        run, source_json, tmp_path, input_policy, entry_case, payload):
    """Rules: DK-LBL-01, DK-LBL-02, DK-IRI-04, DK-DIAG-01, DK-DIAG-04, DK-DIAG-05; §§3.2, 15. RD-02 Alt 1A."""
    document = source_json("shared/source_text")
    _localize_other_text(document)
    source_element(document, "cPerson")["name"] = copy.deepcopy(payload)
    result = run(path=write_input(tmp_path, document), iri_strategy="name", input_policy=input_policy, language="nl")
    assert all(d.code != "INTERNAL_TRANSFORMATION_FAILURE" for d in result.diagnostics), result.diagnostics
    assert any(d.severity == "ERROR" and "invalid_language_string_entry" in d.facts for d in result.diagnostics)
    if input_policy != "best-effort":
        assert result.outcome == "aborted" and result.ontology is None
        return
    assert result.outcome == "completed-with-errors"
    assert (BASE.unnamedClass_cPerson, RDF.type, OWL.Class) in result.ontology
    assert not list(result.ontology.objects(BASE.unnamedClass_cPerson, RDFS.label))


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("form", ["absent", "null", "empty"])
def test_empty_project_languages_representations_are_accepted(run, invoke, source_json, tmp_path, input_policy, form):
    """Rules: DK-LBL-02, DK-DIAG-05, DK-DIAG-19; §3.2. RD-02 Alternative 2A."""
    control_doc = source_json("shared/source_text")
    control_doc.pop("languages", None)
    document = source_json("shared/source_text")
    if form == "absent":
        document.pop("languages", None)
    elif form == "null":
        document["languages"] = None
    else:
        document["languages"] = []

    baseline = run(path=write_input(tmp_path, control_doc, "control.json"), iri_strategy="id", input_policy=input_policy)
    result = run(path=write_input(tmp_path, document), iri_strategy="id", input_policy=input_policy)
    assert baseline.outcome == result.outcome == "completed"
    assert_graph_equal(baseline.ontology, result.ontology)
    assert diagnostic_record_counts(invoke.report_content(result).events) == diagnostic_record_counts(
        invoke.report_content(baseline).events)
    assert not any(d.severity == "ERROR" or d.kind == "ambiguous_language" for d in result.diagnostics)
    assert (BASE.cPerson, RDFS.label, Literal("Person")) in result.ontology


_MALFORMED_PROJECT_LANGUAGES = [
    ("non_array_string", "en", "project_languages_non_array"),
    ("non_array_int", 123, "project_languages_non_array"),
    ("non_array_object", {"en": True}, "project_languages_non_array"),
    ("non_array_bool", True, "project_languages_non_array"),
    ("entry_non_string_int", ["en", 42], "project_languages_invalid_entry"),
    ("entry_non_string_null", ["en", None], "project_languages_invalid_entry"),
    ("entry_empty_string", ["en", ""], "project_languages_invalid_entry"),
    ("entry_whitespace_string", ["en", "   "], "project_languages_invalid_entry"),
    ("entry_invalid_tag_space", ["en", "bad tag"], "project_languages_invalid_entry"),
    ("entry_invalid_tag_underscore", ["en", "en_US"], "project_languages_invalid_entry"),
    ("entry_invalid_tag_newline", ["en", "en\n"], "project_languages_invalid_entry"),
    ("multi_plus_non_string", ["en", "pt-BR", 42], "project_languages_invalid_entry"),
    ("multi_plus_invalid_tag", ["en", "pt-BR", "bad tag"], "project_languages_invalid_entry"),
]


@pytest.mark.parametrize("input_policy", POLICIES)
@pytest.mark.parametrize("use_override", [False, True], ids=["no_override", "with_override"])
@pytest.mark.parametrize("case,languages_value,expected_fact", _MALFORMED_PROJECT_LANGUAGES,
                         ids=[row[0] for row in _MALFORMED_PROJECT_LANGUAGES])
def test_malformed_project_languages_follows_policy_and_omits_as_a_whole(
        run, source_json, tmp_path, input_policy, use_override, case, languages_value, expected_fact):
    """Rules: DK-LBL-02, DK-DIAG-01, DK-DIAG-04, DK-DIAG-05, DK-DIAG-19; §§3.2, 15. RD-02 Alternative 2A."""
    document = source_json("shared/source_text")
    _localize_other_text(document)
    document["languages"] = copy.deepcopy(languages_value)
    source_element(document, "cPerson")["name"] = "Person"
    source_element(document, "cOrg")["description"] = {"": "Unknown org description"}
    source_element(document, "cAddress")["description"] = {"fr": "Adresse"}
    options = {"iri_strategy": "id", "input_policy": input_policy}
    if use_override:
        options["language"] = "nl"

    result = run(path=write_input(tmp_path, document), **options)
    assert all(d.code != "INTERNAL_TRANSFORMATION_FAILURE" for d in result.diagnostics), result.diagnostics
    assert not any(d.code == "UNKNOWN_INFORMATION" for d in result.diagnostics), result.diagnostics
    assert any(
        d.severity == "ERROR" and expected_fact in d.facts
        for d in result.diagnostics
    ), result.diagnostics

    if input_policy != "best-effort":
        assert result.outcome == "aborted" and result.ontology is None
        return

    assert result.outcome == "completed-with-errors"
    assert not any(d.kind == "ambiguous_language" or d.code == "AMBIGUOUS_PROJECT_LANGUAGE" for d in result.diagnostics)
    expected_untagged_lang = "nl" if use_override else None
    _assert_source_values(result.ontology, BASE.cPerson, RDFS.label, {Literal("Person", lang=expected_untagged_lang)})
    _assert_source_values(result.ontology, BASE.cOrg, RDFS.comment, {Literal("Unknown org description", lang=expected_untagged_lang)})
    _assert_source_values(result.ontology, BASE.cAddress, RDFS.comment, {Literal("Adresse", lang="nl" if use_override else "fr")})

