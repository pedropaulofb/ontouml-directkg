"""Public orchestration/result boundary for the approved baseline increments."""

from dataclasses import dataclass, field
import os
from pathlib import Path

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, XSD

from .annotations import TextAnnotations, validate_project_languages, validate_textual_carriers
from .classifiers import allocate_resources, baseline_classes, emit_classes, emit_stereotype_disjointness
from .chains import emit_material_chains
from .diagnostics import Diagnostic, DiagnosticCollector, Outcome, _AbortConversion, export_report
from .dkgm import DKGM, DKGM_MODES, emit_dkgm
from .enumerations import collect_enumerations, emit_enumerations
from .generalizations import emit_generalizations, emit_relation_generalizations
from .identity import ConfigurationError, is_absolute_iri, is_valid_language_tag, select_base
from .inverses import allocate_inverses
from .metadata import emit_metadata, read_metadata
from . import provenance as execution_provenance
from .provenance import ProvenanceRecord
from .properties import PropertyExpressions, collect_attributes, emit_attributes, emit_property_references, property_candidates
from .relation_axioms import emit_relation_axioms
from .relations import collect_relations, emit_relations, relation_names
from .source import SourceElement, apply_identifier_policy, check_stereotypes, index_project, read_project, validate_containers


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

    def deliver(self, destination: str | os.PathLike):
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

    def export_diagnostics(self, destination: str | os.PathLike) -> Path:
        """Explicitly export the produced outcome/events, including after abort.

        Raises DiagnosticsExportError for an unwritable destination. The result,
        diagnostics, graph and outcome are unchanged by export or its failure.
        """
        return export_report(self.outcome, self.diagnostics, destination)


def convert(source: str | os.PathLike, *, base_iri: str | None = None, iri_strategy: str = "name",
            input_policy: str = "tolerant", stereotype_policy: str = "allow-custom",
            language: str | None = None, omit_identifiers: bool = False,
            inverse_properties: str = "all", no_stereotype_relation_naming: bool = False,
            relation_labels: str = "source-only", material_property_chains: str = "none",
            provenance: str = "embedded", metadata_file: str | os.PathLike | None = None,
            ontology_version_iri: str | None = None, dkgm_vocabulary: str = "import") -> ConversionResult:
    """Convert supported classifier/attribute/binary-relation VP-plugin 0.5.3 JSON.

    Embedded provenance is the default. Sidecar mode exposes a separate graph;
    only explicit ``result.deliver(path)`` writes ontology/provenance files.
    Select the vocabulary delivery with ``dkgm_vocabulary``: the stable import
    (default), the fixed local core (``embed``), or bridge-target typing (``none``).
    Unresolved naming/recovery branches remain unimplemented; their failures
    abort conversion rather than return an apparently completed partial result.

    ConfigurationError occurs before source reading and produces no conversion
    result/report. Policy-driven aborts and reportable internal failures return
    all produced diagnostics with outcome ``aborted`` and no ontology or
    provenance graph. Conversion writes no output files.
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
               "dkgm_vocabulary": (dkgm_vocabulary, DKGM_MODES),
               "provenance": (provenance, {"none", "embedded", "sidecar"})}
    for name, (value, allowed) in choices.items():
        if not isinstance(value, str) or value not in allowed:
            raise ConfigurationError(f"Invalid {name}: expected one of {', '.join(sorted(allowed))}")
    if type(omit_identifiers) is not bool:
        raise ConfigurationError("omit_identifiers must be a boolean")
    if type(no_stereotype_relation_naming) is not bool:
        raise ConfigurationError("no_stereotype_relation_naming must be a boolean")
    if language is not None and not is_valid_language_tag(language):
        raise ConfigurationError("language must be one valid language tag")
    if metadata_file is not None:
        if not isinstance(metadata_file, (str, os.PathLike)):
            raise ConfigurationError("metadata_file must explicitly identify a file named metadata.yaml")
        try:
            metadata_fspath = os.fspath(metadata_file)
        except TypeError as exc:
            raise ConfigurationError("metadata_file must explicitly identify a file named metadata.yaml") from exc
        if not isinstance(metadata_fspath, str) or Path(metadata_fspath).name != "metadata.yaml":
            raise ConfigurationError("metadata_file must explicitly identify a file named metadata.yaml")
        metadata_file = Path(metadata_fspath)
    if not isinstance(source, (str, os.PathLike)):
        raise ConfigurationError("source must be a file path (str or os.PathLike)")
    try:
        source_fspath = os.fspath(source)
    except TypeError as exc:
        raise ConfigurationError("source must be a file path (str or os.PathLike)") from exc
    if not isinstance(source_fspath, str):
        raise ConfigurationError("source must be a file path (str or os.PathLike)")
    source_path = Path(source_fspath)
    diagnostics = DiagnosticCollector()
    if base_iri is None:
        diagnostics.add("WARNING", "PLACEHOLDER_BASE",
                        "No base IRI supplied: using a placeholder namespace, which is not recommended for publication.",
                        f"Effective entity base is {base}.")
    stage = "read_project"
    try:
        captured = [] if provenance != "none" else None
        project = read_project(source_path, diagnostics, captured_bytes=captured)
        stage = "index_project"
        index = index_project(project, diagnostics, input_policy)
        # DK-GEN-12 detects mixed hierarchies from resolved source declarations,
        # including classifiers whose later input-policy recovery omits output.
        source_index = index
        stage = "check_stereotypes"
        index = check_stereotypes(index, diagnostics, stereotype_policy, input_policy)
        stage = "apply_identifier_policy"
        index = apply_identifier_policy(index, diagnostics, input_policy)
        stage = "validate_containers"
        validate_containers(index, diagnostics, input_policy)
        stage = "baseline_classes"
        classes = baseline_classes(index, diagnostics, input_policy)
        stage = "collect_enumerations"
        enumerations = collect_enumerations(classes, diagnostics, input_policy)
        stage = "collect_relations"
        relations, groundings, omitted = collect_relations(index, classes, diagnostics, input_policy)
        stage = "collect_attributes"
        attributes, omitted_attributes = collect_attributes(index, classes, diagnostics, input_policy)
        stage = "validate_textual_carriers"
        project_languages = validate_project_languages(project, diagnostics, input_policy)
        validate_textual_carriers(SourceElement(project, "$"), diagnostics, input_policy)
        for element in index.elements:
            if element.data["type"] == "Class":
                validate_textual_carriers(element, diagnostics, input_policy)
        for enumeration in enumerations:
            for literal in enumeration.values:
                validate_textual_carriers(literal, diagnostics, input_policy)
        for relation in relations:
            validate_textual_carriers(relation.source, diagnostics, input_policy)
            validate_textual_carriers(relation.source_end, diagnostics, input_policy)
            validate_textual_carriers(relation.target_end, diagnostics, input_policy)
        for attribute in attributes:
            validate_textual_carriers(attribute.source, diagnostics, input_policy)
        stage = "relation_names"
        names, lexical = relation_names(relations, groundings, iri_strategy, relation_labels,
                                       no_stereotype_relation_naming, diagnostics)
        claims: set[str] = set()
        property_id_fallbacks: dict[str, str] = {}
        stage = "property_candidates"
        candidates = property_candidates(attributes, iri_strategy,
            {relation.target_end.data["id"]: (names[relation.target_end.data["id"]], relation.domain)
             for relation in relations}, claims, id_fallbacks=property_id_fallbacks)
        stage = "allocate_resources"
        resources = allocate_resources(classes, enumerations, base, iri_strategy,
                                       candidates, claims, property_id_fallbacks=property_id_fallbacks)
        stage = "allocate_inverses"
        inverses = allocate_inverses(relations, resources, base, iri_strategy, inverse_properties, claims)
        resources.update(inverses)
        stage = "TextAnnotations"
        text = TextAnnotations(project, language, diagnostics, project_languages)
        stage = "ontology initialization"
        graph = Graph(bind_namespaces="none")
        for prefix, namespace in (("", base), ("rdf", RDF), ("rdfs", RDFS), ("owl", OWL),
                                  ("xsd", XSD), ("dcterms", DCTERMS), ("dkgm", DKGM)):
            graph.bind(prefix, namespace)
        ontology = URIRef(ontology_iri)
        graph.add((ontology, RDF.type, OWL.Ontology))
        if ontology_version_iri is not None:
            graph.add((ontology, OWL.versionIRI, URIRef(ontology_version_iri)))
        stage = "project annotations"
        text.describe(graph, ontology, project)
        stage = "emit_classes"
        emit_classes(graph, classes, resources, iri_strategy, omit_identifiers, text, diagnostics)
        stage = "emit_stereotype_disjointness"
        emit_stereotype_disjointness(graph, classes, resources)
        stage = "emit_enumerations"
        emit_enumerations(graph, enumerations, resources, iri_strategy, text, diagnostics)
        stage = "emit_generalizations"
        emit_generalizations(graph, index, resources, diagnostics, input_policy, source_index=source_index)
        stage = "emit_attributes"
        emit_attributes(graph, attributes, resources, iri_strategy, text, diagnostics, input_policy)
        stage = "PropertyExpressions"
        ends = {end.data["id"]: (relation.target_end.data["id"], reverse)
                for relation in relations for end, reverse in ((relation.source_end, True), (relation.target_end, False))}
        end_kinds = {end.data["id"]: relation.kind
                     for relation in relations for end in (relation.source_end, relation.target_end)}
        expressions = PropertyExpressions(graph, attributes, resources, ends, inverses, omitted, end_kinds, omitted_attributes)
        stage = "emit_relations"
        bridges = emit_relations(graph, relations, resources, inverses, lexical, relation_labels, text,
                                 diagnostics, input_policy, expressions)
        stage = "emit_relation_generalizations"
        emit_relation_generalizations(graph, index,
            {relation.source.data["id"]: resources[relation.target_end.data["id"]] for relation in relations},
            {relation.source.data["id"]: inverses[relation.source_end.data["id"]]
             for relation in relations if relation.source_end.data["id"] in inverses}, diagnostics, input_policy,
            {relation.source.data["id"]: relation.kind for relation in relations}, source_index=source_index)
        stage = "emit_property_references"
        emit_property_references(graph, index, expressions, diagnostics, input_policy)
        stage = "emit_material_chains"
        emit_material_chains(graph, relations, groundings, attributes, expressions,
                             material_property_chains, diagnostics)
        stage = "emit_dkgm"
        emit_dkgm(graph, ontology, dkgm_vocabulary, bridges, diagnostics)
        stage = "emit_relation_axioms"
        emit_relation_axioms(graph, relations, expressions)
        stage = "read_metadata"
        metadata = read_metadata(metadata_file, diagnostics, input_policy)
        stage = "emit_metadata"
        emit_metadata(graph, ontology, metadata)
        record = None
        if provenance != "none":
            stage = "transformation provenance"
            configuration = {
                "base_iri": base_iri, "effective_base_iri": base,
                "ontology_version_iri": str(ontology_version_iri) if ontology_version_iri is not None else None,
                "iri_strategy": iri_strategy, "input_policy": input_policy,
                "stereotype_policy": stereotype_policy, "inverse_properties": inverse_properties,
                "stereotype_relation_naming": not no_stereotype_relation_naming,
                "relation_labels": relation_labels, "material_property_chains": material_property_chains,
                "dkgm_vocabulary": dkgm_vocabulary,
                "language": language, "omit_identifiers": omit_identifiers,
                "metadata_file": str(metadata_file) if metadata_file is not None else None,
                "provenance": provenance,
            }
            try:
                record = execution_provenance.construct_provenance(
                    ontology, source_path, captured[0], metadata, configuration, base)
                if provenance == "embedded":
                    for prefix, namespace in record.graph.namespaces():
                        graph.bind(prefix, namespace)
                    graph += record.graph
            except Exception as exc:
                diagnostics.add("ERROR", "REQUIRED_PROVENANCE",
                                f"Cannot construct required transformation provenance: {exc}.",
                                "Conversion aborted; no ontology, incomplete provenance or substitute mode is delivered.")
                raise _AbortConversion from exc
        stage = "result construction"
        outcome: Outcome = "completed-with-errors" if any(d.severity == "ERROR" for d in diagnostics.events) else "completed"
        return ConversionResult(graph, outcome, tuple(diagnostics.events),
                                record.graph if provenance == "sidecar" else None, provenance, record)
    except _AbortConversion:
        return ConversionResult(None, "aborted", tuple(diagnostics.events), provenance_mode=provenance)
    except Exception as exc:
        diagnostics.add("ERROR", "INTERNAL_TRANSFORMATION_FAILURE",
                        f"Unexpected internal failure in stage '{stage}': {type(exc).__name__}: {exc}.",
                        "Conversion aborted; no ontology or provenance sidecar is delivered.")
        return ConversionResult(None, "aborted", tuple(diagnostics.events), provenance_mode=provenance)
