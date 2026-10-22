"""Shared source-text placement, language carriers, and multilingual selection."""

import copy

import pytest
from rdflib import Literal, Namespace
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, XSD

from tests.support.data import fixture_issues, source_element, source_elements, write_input
from tests.support.invocation import diagnostic_signatures
from tests.support.rdf import assert_selected_equal


BASE = Namespace("https://example.test/model#")
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
    """Rules: DK-IRI-10, DK-IRI-03, DK-IRI-08, DK-LBL-01, DK-LBL-02.

    Expected local names are explicit case data, not a test-side transformer.
    Check JSON order, user override and project languages independently of
    naming, retaining every original label in each observation.
    """
    for context, options in [("default", {}), ("override", {"language": "nl"}), ("project", {})]:
        for reverse in (False, True):
            document = source_json("shared/source_text")
            _localize_other_text(document)
            if identifier == "aAge":
                # Keep the selector case free of an unrelated class/property
                # collision when the chosen attribute text is "Person".
                source_element(document, "cPerson")["name"] = {"en": "AttributeOwner"}
            source_element(document, identifier)["name"] = dict(reversed(list(text.items()))) if reverse else copy.deepcopy(text)
            if context == "project":
                document["languages"] = ["pt-BR", "en"]
            result = run(path=write_input(tmp_path, document, context + str(reverse) + ".json"), **options)
            assert result.outcome == "completed"
            target = BASE[prefix + selected]
            assert (target, RDF.type, OWL.NamedIndividual if identifier == "vPending" else OWL.DatatypeProperty if identifier == "aAge" else OWL.Class) in result.ontology
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
    """Rules: DK-IRI-02, DK-IRI-08, DK-IRI-10, DK-LBL-01, DK-LBL-02."""
    document = source_json("shared/source_text")
    _localize_other_text(document)
    source_element(document, identifier)["name"] = {"pt-BR": "Pessoa", "en": "Person"}
    result = run(path=write_input(tmp_path, document), iri_strategy="id", language="nl")
    assert result.outcome == "completed"
    target = BASE[identifier]
    _assert_source_values(result.ontology, target, RDFS.label, {Literal("Pessoa", lang="nl"), Literal("Person", lang="nl")}, exclusive=False)
    assert set(result.ontology.subjects(DCTERMS.identifier, Literal(identifier))) == {target}


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
