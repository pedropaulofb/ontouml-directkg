"""Public orchestration/result boundary for the approved baseline increments."""

from dataclasses import dataclass, field
from pathlib import Path

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, XSD

from .annotations import TextAnnotations
from .classifiers import allocate_resources, baseline_classes, emit_classes, emit_stereotype_disjointness
from .chains import emit_material_chains
from .diagnostics import Diagnostic, DiagnosticCollector, Outcome, _AbortConversion, export_report
from .enumerations import collect_enumerations, emit_enumerations
from .generalizations import emit_generalizations, emit_relation_generalizations
from .identity import ConfigurationError, is_absolute_iri, select_base
from .inverses import allocate_inverses
from .metadata import emit_metadata, read_metadata
from . import provenance as execution_provenance
from .provenance import ProvenanceRecord
from .properties import PropertyExpressions, collect_attributes, emit_attributes, emit_property_references, property_candidates
from .relation_axioms import emit_relation_axioms
from .relations import collect_relations, emit_relations, relation_names
from .source import apply_identifier_policy, check_stereotypes, index_project, read_project

DKGM_ONTOLOGY = URIRef("https://w3id.org/directkg/vocab/dkgm")


@dataclass
class ConversionResult:
    """A real conversion outcome, complete diagnostics and eligible ontology.

    Abortion always exposes ``ontology=None``. No accumulated aborted graph is
    returned. Diagnostic access/export remains available. Serialization and
    delivery are separate from transformation. Explicit delivery may append
    delivery diagnostics without changing an established transformation outcome.
    Required-provenance construction failure aborts before file delivery.
    ``completed`` is not a general conformance claim.
    """

    ontology: Graph | None
    outcome: Outcome
    diagnostics: tuple[Diagnostic, ...]
    provenance: Graph | None = None
    provenance_mode: str = "none"
    _provenance_record: ProvenanceRecord | None = field(default=None, repr=False)

    def to_turtle(self) -> str:
        """Serialize the actual eligible graph as Turtle, without writing files."""
        if self.ontology is None:
            raise ValueError("An aborted conversion has no deliverable ontology")
        return self.ontology.serialize(format="turtle")

    def to_provenance_turtle(self) -> str:
        """Serialize the separate provenance graph, without automatic file output."""
        if self.provenance is None:
            raise ValueError("No separate provenance graph is available")
        return self.provenance.serialize(format="turtle")

    def deliver(self, destination: str | Path):
        """Explicitly deliver Turtle and any sidecar; inspect the returned delivery result."""
        from .delivery import deliver
        return deliver(self, Path(destination))

    def _abort_provenance(self, cause: Exception) -> None:
        self.diagnostics += (Diagnostic(
            "ERROR", "REQUIRED_PROVENANCE", f"Cannot construct required transformation provenance: {cause}.",
            "Conversion aborted before ontology delivery; no incomplete provenance or substitute mode is delivered."),)
        self.outcome = "aborted"
        self.ontology = self.provenance = None
        self._provenance_record = None

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
            provenance: str = "embedded", metadata_file: str | Path | None = None,
            ontology_version_iri: str | None = None) -> ConversionResult:
    """Convert supported classifier/attribute/binary-relation VP-plugin 0.5.3 JSON.

    Embedded provenance is the default. Sidecar mode exposes a separate graph;
    only explicit ``result.deliver(path)`` writes ontology/provenance files.
    Unresolved naming/recovery branches raise NotImplementedError rather than
    returning an apparently completed partial conversion.

    ConfigurationError occurs before source reading and produces no conversion
    result/report. Policy-driven aborts return their actual produced diagnostics
    with outcome ``aborted`` and no ontology. Conversion writes no output files.
    """
    base, ontology_iri = select_base(base_iri)
    if ontology_version_iri is not None and (not isinstance(ontology_version_iri, str)
                                           or not is_absolute_iri(ontology_version_iri)):
        raise ConfigurationError("ontology_version_iri must be a syntactically valid absolute IRI")
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
    if metadata_file is not None:
        if not isinstance(metadata_file, (str, Path)) or Path(metadata_file).name != "metadata.yaml":
            raise ConfigurationError("metadata_file must explicitly identify a file named metadata.yaml")
        metadata_file = Path(metadata_file)
    diagnostics = DiagnosticCollector()
    if base_iri is None:
        diagnostics.add("WARNING", "PLACEHOLDER_BASE",
                        "No base IRI supplied: using a placeholder namespace, which is not recommended for publication.",
                        f"Effective entity base is {base}.")
    try:
        captured = [] if provenance != "none" else None
        project = read_project(Path(source), diagnostics, captured_bytes=captured)
        index = index_project(project, diagnostics, input_policy)
        check_stereotypes(index, diagnostics, stereotype_policy)
        index = apply_identifier_policy(index, diagnostics, input_policy)
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
        if ontology_version_iri is not None:
            graph.add((ontology, OWL.versionIRI, URIRef(ontology_version_iri)))
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
        emit_material_chains(graph, relations, groundings, attributes, expressions,
                             material_property_chains, diagnostics)
        emit_relation_axioms(graph, relations, expressions)
        metadata = read_metadata(metadata_file, diagnostics, input_policy)
        emit_metadata(graph, ontology, metadata)
        record = None
        if provenance != "none":
            configuration = {
                "base_iri": base_iri, "effective_base_iri": base,
                "ontology_version_iri": str(ontology_version_iri) if ontology_version_iri is not None else None,
                "iri_strategy": iri_strategy, "input_policy": input_policy,
                "stereotype_policy": stereotype_policy, "inverse_properties": inverse_properties,
                "stereotype_relation_naming": not no_stereotype_relation_naming,
                "relation_labels": relation_labels, "material_property_chains": material_property_chains,
                "language": language, "omit_identifiers": omit_identifiers,
                "metadata_file": str(metadata_file) if metadata_file is not None else None,
                "provenance": provenance,
            }
            try:
                record = execution_provenance.construct_provenance(
                    ontology, Path(source), captured[0], metadata, configuration, base)
                if provenance == "embedded":
                    for prefix, namespace in record.graph.namespaces():
                        graph.bind(prefix, namespace)
                    graph += record.graph
            except Exception as exc:
                diagnostics.add("ERROR", "REQUIRED_PROVENANCE",
                                f"Cannot construct required transformation provenance: {exc}.",
                                "Conversion aborted; no ontology, incomplete provenance or substitute mode is delivered.")
                raise _AbortConversion from exc
    except _AbortConversion:
        return ConversionResult(None, "aborted", tuple(diagnostics.events), provenance_mode=provenance)
    outcome: Outcome = "completed-with-errors" if any(d.severity == "ERROR" for d in diagnostics.events) else "completed"
    return ConversionResult(graph, outcome, tuple(diagnostics.events),
                            record.graph if provenance == "sidecar" else None, provenance, record)
