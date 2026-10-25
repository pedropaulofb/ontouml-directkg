"""Public orchestration/result boundary for the approved baseline increments."""

from dataclasses import dataclass
from pathlib import Path

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, XSD

from .annotations import TextAnnotations
from .classifiers import allocate_resources, baseline_classes, emit_classes, emit_stereotype_disjointness
from .diagnostics import Diagnostic, DiagnosticCollector, Outcome, _AbortConversion, export_report
from .enumerations import collect_enumerations, emit_enumerations
from .generalizations import emit_generalizations, emit_relation_generalizations
from .identity import ConfigurationError, select_base
from .inverses import allocate_inverses
from .properties import PropertyExpressions, collect_attributes, emit_attributes, emit_property_references, property_candidates
from .relations import collect_relations, emit_relations, relation_names
from .source import check_stereotypes, index_project, read_project

DKGM_ONTOLOGY = URIRef("https://w3id.org/directkg/vocab/dkgm")


@dataclass(frozen=True)
class ConversionResult:
    """A real conversion outcome, complete diagnostics and eligible ontology.

    Abortion always exposes ``ontology=None``. No accumulated aborted graph is
    returned. Diagnostic access/export remains available. Serialization and
    delivery are separate from transformation; BI-W1 supplies Turtle text, not
    an ontology-file writer. ``completed`` is not a general conformance claim.
    """

    ontology: Graph | None
    outcome: Outcome
    diagnostics: tuple[Diagnostic, ...]

    def to_turtle(self) -> str:
        """Serialize the actual eligible graph as Turtle, without writing files."""
        if self.ontology is None:
            raise ValueError("An aborted conversion has no deliverable ontology")
        return self.ontology.serialize(format="turtle")

    def export_diagnostics(self, destination: str | Path) -> Path:
        """Explicitly export the produced outcome/events, including after abort.

        Raises DiagnosticsExportError for an unwritable destination. The result,
        diagnostics, graph and outcome are unchanged by export or its failure.
        """
        return export_report(self.outcome, self.diagnostics, destination)


def convert(source: str | Path, *, base_iri: str | None = None, iri_strategy: str = "name",
            input_policy: str = "tolerant", stereotype_policy: str = "allow-custom",
            language: str | None = None, omit_identifiers: bool = False,
            inverse_properties: str = "all", no_stereotype_relation_naming: bool = False,
            relation_labels: str = "source-only", material_property_chains: str = "none",
            provenance: str = "embedded") -> ConversionResult:
    """Convert supported classifier/attribute/binary-relation VP-plugin 0.5.3 JSON.

    Early baseline callers must explicitly select ``provenance="none"``. Embedded/sidecar
    provenance belongs to BI-W6; the normative embedded default is retained but
    raises NotImplementedError until implemented, without silently downgrading.
    Later-wave model constructs likewise raise NotImplementedError and return
    no apparently completed partial conversion. This is a development boundary,
    not an input-policy fallback or a rejection of valid OntoUML semantics.

    ConfigurationError occurs before source reading and produces no conversion
    result/report. Policy-driven aborts return their actual produced diagnostics
    with outcome ``aborted`` and no ontology. Conversion writes no output files.
    """
    base, ontology_iri = select_base(base_iri)
    choices = {"iri_strategy": (iri_strategy, {"name", "id"}),
               "input_policy": (input_policy, {"strict", "tolerant", "best-effort"}),
               "stereotype_policy": (stereotype_policy, {"require-known", "allow-missing", "allow-custom"}),
               "inverse_properties": (inverse_properties, {"all", "informed", "named", "none"}),
               "relation_labels": (relation_labels, {"source-only", "generated"}),
               "material_property_chains": (material_property_chains,
                                            {"none", "omit-conflicting-constraints", "preserve-conflicting-constraints"}),
               "provenance": (provenance, {"none", "embedded", "sidecar"})}
    for name, (value, allowed) in choices.items():
        if not isinstance(value, str) or value not in allowed:
            raise ConfigurationError(f"Invalid {name}: expected one of {', '.join(sorted(allowed))}")
    if type(omit_identifiers) is not bool:
        raise ConfigurationError("omit_identifiers must be a boolean")
    if type(no_stereotype_relation_naming) is not bool:
        raise ConfigurationError("no_stereotype_relation_naming must be a boolean")
    if language is not None:
        try:
            if not isinstance(language, str) or not language:
                raise ValueError("Expected one nonempty language tag")
            Literal("", lang=language)
        except ValueError as exc:
            raise ConfigurationError("language must be one valid language tag") from exc
    if provenance != "none":
        raise NotImplementedError("Provenance generation, including the embedded default, belongs to BI-W6; "
                                  "explicitly request provenance='none' for early baseline increments")
    if material_property_chains != "none":
        raise NotImplementedError("Material-property-chain generation belongs to BI-W5")
    diagnostics = DiagnosticCollector()
    if base_iri is None:
        diagnostics.add("WARNING", "PLACEHOLDER_BASE",
                        "No base IRI supplied: using a placeholder namespace, which is not recommended for publication.",
                        f"Effective entity base is {base}.")
    try:
        project = read_project(Path(source), diagnostics)
        index = index_project(project, diagnostics, input_policy)
        check_stereotypes(index, diagnostics, stereotype_policy)
        classes = baseline_classes(index)
        enumerations = collect_enumerations(classes, diagnostics, input_policy)
        relations, groundings, omitted = collect_relations(index, classes, diagnostics, input_policy)
        attributes = collect_attributes(index, classes, diagnostics, input_policy)
        names, lexical = relation_names(relations, groundings, iri_strategy, relation_labels,
                                       no_stereotype_relation_naming, diagnostics)
        claims: set[str] = set()
        candidates = property_candidates(attributes, iri_strategy,
            {relation.target_end.data["id"]: (names[relation.target_end.data["id"]], relation.domain)
             for relation in relations}, claims)
        resources = allocate_resources(classes, enumerations, base, iri_strategy,
                                       candidates, claims)
        inverses = allocate_inverses(relations, resources, base, iri_strategy, inverse_properties, claims)
        resources.update(inverses)
        text = TextAnnotations(project, language, diagnostics)
        graph = Graph(bind_namespaces="none")
        for prefix, namespace in (("", base), ("rdf", RDF), ("rdfs", RDFS), ("owl", OWL),
                                  ("xsd", XSD), ("dcterms", DCTERMS), ("dkgm", str(DKGM_ONTOLOGY) + "#")):
            graph.bind(prefix, namespace)
        ontology = URIRef(ontology_iri)
        graph.add((ontology, RDF.type, OWL.Ontology))
        graph.add((ontology, OWL.imports, DKGM_ONTOLOGY))
        text.describe(graph, ontology, project)
        emit_classes(graph, classes, resources, iri_strategy, omit_identifiers, text, diagnostics)
        emit_stereotype_disjointness(graph, classes, resources)
        emit_enumerations(graph, enumerations, resources, iri_strategy, text, diagnostics)
        emit_generalizations(graph, index, resources, diagnostics, input_policy)
        emit_attributes(graph, attributes, resources, iri_strategy, text, diagnostics, input_policy)
        ends = {end.data["id"]: (relation.target_end.data["id"], reverse)
                for relation in relations for end, reverse in ((relation.source_end, True), (relation.target_end, False))}
        expressions = PropertyExpressions(graph, attributes, resources, ends, inverses, omitted)
        emit_relations(graph, relations, resources, inverses, lexical, relation_labels, text,
                       diagnostics, input_policy, expressions)
        emit_relation_generalizations(graph, index,
            {relation.source.data["id"]: resources[relation.target_end.data["id"]] for relation in relations},
            {relation.source.data["id"]: inverses[relation.source_end.data["id"]]
             for relation in relations if relation.source_end.data["id"] in inverses}, diagnostics, input_policy)
        emit_property_references(graph, index, expressions, diagnostics, input_policy)
    except _AbortConversion:
        return ConversionResult(None, "aborted", tuple(diagnostics.events))
    outcome: Outcome = "completed-with-errors" if any(d.severity == "ERROR" for d in diagnostics.events) else "completed"
    return ConversionResult(graph, outcome, tuple(diagnostics.events))
