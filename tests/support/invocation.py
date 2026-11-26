"""Replaceable binding to REAL DirectKG interfaces.

The dataclasses below are a test-side observation format, not a proposed public
API. The binding covers actual file conversion, public result reads, diagnostic
codes, CLI reports and the explicitly implemented fault boundaries. Other
capabilities remain explicitly unbound.
Never populate observations from expected fixtures or implement mappings here.
"""

from ast import literal_eval
from dataclasses import dataclass, field
from collections import Counter
from contextlib import contextmanager, nullcontext
import errno
import json
import inspect
import os
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
from typing import Any, Mapping, Protocol
from unittest.mock import patch

from rdflib import Graph, Literal, URIRef
from rdflib.term import Node


class ImplementationUnavailable(RuntimeError):
    """There is no verified production invocation to execute."""


@dataclass
class SourceInputAttempt:
    """Actual public-call result or native rejection; no rejection type is prescribed."""

    observation: "Observation | None" = None
    rejection: Exception | None = None


@dataclass
class SourceInputSurface:
    """Observed fileless/checksum extensions and the inspected interface evidence."""

    extensions: tuple[Any, ...]
    raw: Any


@dataclass(frozen=True)
class Diagnostic:
    """One observed event, retaining multiplicity and its original payload.

    ``kind`` and ``facts`` normalize the MEANING of actually produced fields or
    messages; they are not required production codes or JSON keys. A real
    binding must document each mapping and retain ``raw`` for reviewer audit.
    It must never infer an event, source locator or fact from the test request.

    ``source_ids`` retains IDs actually reported by the diagnostic. In contrast,
    ``identified_sources`` uses canonical source IDs to represent declarations
    unambiguously identified by any actually reported locator (for example a
    name, source path, native element reference, or ID). Resolve such locators
    against the actual source only when unambiguous; never fill this field from
    the expected affected element or the condition being tested.
    """

    severity: str
    kind: str
    message: str
    source_ids: tuple[str, ...] = ()
    source_types: tuple[str, ...] = ()
    generated_iris: tuple[str, ...] = ()
    facts: frozenset[str] = frozenset()
    raw: Any = None
    identified_sources: tuple[str, ...] = ()
    # The actual native/report identifier, distinct from normalized meaning.
    # None on console records whose inspected presentation displays no code.
    code: str | None = None


@dataclass
class CommentMeaning:
    """Meaning actually expressed by one produced RDF comment.

    Generated flag-comment wording is not standardized. A real binding may
    normalize its observed wording into field/value pairs, retaining the exact
    subject and literal as evidence. Never derive these meanings from input
    declarations or expected fixtures. Several meanings may share one comment.
    ``field`` uses the source field name, or ``stereotype`` for ``abstract``
    and the RD-18 property stereotypes ``begin`` / ``end``.
    This is a test-side reading of RDF, not a production metadata interface.
    """

    subject: URIRef
    literal: Literal
    field: str
    value: bool | str
    # Context actually expressed by the comment: attribute, relation,
    # source_end, target_end, or class. Resolve observed role wording, not the
    # source flag under test. Needed to distinguish end occurrences sharing a
    # primary-property target; older tests need not demand a context.
    context: str | None = None
    # RD-18: English meaning actually observed in the comment wording, not
    # inferred from an option, expected source stereotype or language tag alone.
    english: bool | None = None


@dataclass
class Observation:
    """Snapshot of actual public results, including policy-driven aborts.

    A binding must not hide a publicly delivered partial graph on abort,
    fabricate an outcome by counting severities, or discard diagnostic events.
    ``configuration_error`` carries the actual programmatic rejection signal;
    its production representation and exception class are deliberately open.
    """

    ontology: Graph | None
    outcome: str | None
    diagnostics: tuple[Diagnostic, ...]
    configuration_error: Any = None
    native: Any = field(default=None, repr=False)
    # Optional real-call input-processing trace, independent of returned status.
    conversion_started: bool | None = None
    execution_trace: Any = None
    comments: tuple[CommentMeaning, ...] = ()
    # Actual RDF statements expressing restrictedTo/nature information, read
    # from the produced graph regardless of predicate or comment wording. This
    # is a test-side semantic reading, not a production field. The binding must
    # report every such statement (including erroneous output), never derive
    # this evidence or an empty result from source inputs/expected omissions.
    restricted_to_output: tuple[tuple[Node, Node, Node], ...] = ()
    # Actual source-project description annotations, including erroneous empty
    # or fabricated replacement text. Read from output/interface evidence;
    # independent generated metadata is excluded. Never assume absence from
    # missing source text. Positive description tests require actual evidence.
    # This is a test-side reading, not a proposed production attribute.
    project_description_output: tuple[tuple[Node, Node, Node], ...] = ()
    # Actual prohibited logical/sequence output induced solely by the source
    # characteristics in GEN-05/CLS-01/PROP-04/05: extra logical axioms, dependence,
    # direction changes, value-order lists/sequences, or properties created
    # solely to represent a flag. Exclude independently required mappings and
    # permitted independent metadata. Read actual output/interface evidence;
    # never infer an empty result from the request or expected behavior.
    flag_semantic_output: tuple[tuple[Node, Node, Node], ...] = ()
    # Actual statements/auxiliary resources serving solely as RDF origin
    # markers for primary fallback labels. Exclude independent provenance and
    # metadata. Read output meaning; never infer absence from requested modes.
    relation_label_origin_output: tuple[tuple[Node, Node, Node], ...] = ()
    # Actual multi-member relation-set completeness/validation substitutes.
    # Exclude independently required hierarchy, disjointness and annotations.
    # This is output evidence, not an expected-input classification.
    relation_completeness_output: tuple[tuple[Node, Node, Node], ...] = ()
    # Actual element-level report entries about intentional inverse omissions,
    # including non-diagnostic native entries. Retain raw report evidence;
    # independently required structural/mapping diagnostics are not omissions.
    inverse_omission_reports: tuple[Any, ...] = ()
    # The actually imported core mereology URI, identified from the real
    # interface/publication evidence. Never fill from an expected constant or
    # assume that an arbitrary import is the required vocabulary.
    mereology_import: URIRef | None = None
    # Actual separately exposed provenance graph, when supplied by the public
    # Python result. Embedded statements remain in ontology. No reconstruction.
    provenance: Graph | None = None
    # Effective mode read from the live delivery result independently of YAML.
    provenance_mode: str | None = None
    # Actual output representing intentionally unrepresented relation-valued
    # connectors, including anonymous representations and grounding annotations.
    # Exclude independent endpoint mappings and reliable descriptive metadata
    # that does not represent the omitted connector.
    unrepresented_connector_output: tuple[Any, ...] | None = None
    # Actual additional semantics induced solely by a comparative-quality
    # derivation: comparison rules, chains/equivalence, counts or characteristics.
    comparative_semantic_output: tuple[Any, ...] | None = None
    # Actual leaks of discarded instantiation values in RDF/provenance/native
    # diagnostics. Includes booleans/characteristics whose meaning cannot be
    # identified by string searching; excludes category names and diagnostic
    # source-ID locators. Read actual evidence, never expected absence.
    discarded_instantiation_output: tuple[Any, ...] | None = None
    # Actual provenance resources grouped by observed role:
    # source, configuration, metadata, output, activity, software (DirectKG itself).
    # Metadata means input CLAIMED AS USED, including erroneous use claims.
    # A merely requested/failed-read entity without such a claim is not use.
    # Do not misclassify other software agents as DirectKG itself.
    # Never classify an input as used merely because it was requested.
    provenance_roles: Mapping[str, tuple[Node, ...]] | None = None
    # Normalize ONLY settings actually represented in the prov:value YAML.
    # Keys are semantic test terms, not proposed production configuration keys.
    configuration_controls: Mapping[str, Any] | None = None
    configuration_format: str | None = None  # actual prov configuration format: yaml
    configuration_literal: Literal | None = None  # actual designated prov:value, not synthesized YAML
    software_version: str | None = None  # read the actual softwareVersion meaning, not package defaults
    directkg_metadata_predicates: tuple[URIRef, ...] | None = None
    # Actual annotations attributable to external selected fields, including
    # erroneous fallback output. Independent generated metadata is excluded.
    external_metadata_output: tuple[tuple[Node, Node, Node], ...] | None = None
    # Actual evidence of provenance/output-artifact information, including
    # erroneous statements in ontology and configuration. Independent reliable
    # descriptive metadata is excluded; never presume these readers empty.
    transformation_provenance_output: tuple[Any, ...] | None = None
    output_artifact_output: tuple[Any, ...] | None = None
    embedded_output_configuration: tuple[Any, ...] | None = None
    # Actual filename/format evidence, each retained as RDF triples. These terms
    # have no prescribed predicate spelling beyond the normative vocabulary.
    output_filename: str | None = None
    output_format: str | None = None  # normalized actual format: turtle
    output_artifact_evidence: tuple[tuple[Node, Node, Node], ...] | None = None
    delivery_failures: tuple["DeliveryFailure", ...] = ()
    operations: tuple["Operation", ...] | None = None
    # Actual advertised valid deliveries and actual diagnostics-report writes,
    # identified from public results/console and instrumented I/O respectively.
    # Do not classify every JSON file as a report or infer validity from existence.
    valid_artifacts: tuple[Path, ...] | None = None
    diagnostics_exports: tuple[Path, ...] | None = None
    sidecar_writes: tuple[Path, ...] | None = None  # actual sidecars, regardless of filename spelling
    # Actual graph snapshot after successful ontology serialization/provenance
    # construction and immediately before file I/O. Obtain from the real I/O
    # interception, not from fixtures or an earlier conversion-only snapshot.
    # This permits independent metadata generated during normal output work.
    pre_delivery_ontology: Graph | None = None


@dataclass(frozen=True)
class Fault:
    """Test-only instruction to fail a REAL boundary, never a public option.

    kind: metadata, provenance, optional_enrichment, ontology, sidecar, diagnostics, transformation,
    stdout, stderr, runtime.
    operation: read, construct, output_construct, serialize, encode, create, write, flush,
    write_unexpected, flush_unexpected, unexpected, pre_conversion, parser_setup, post_delivery,
    enrich, emit_relations, result_construction, allocate_resources, allocate_inverses,
    allocate_name_fallbacks. Bind to an observed implementation operation or standard I/O,
    including child-process I/O for CLI cases. Do not implement a replacement transformation,
    pre-return expected outcomes, or add production fault hooks to satisfy this protocol.
    """

    kind: str
    operation: str
    path: Path | None = None


@dataclass(frozen=True)
class Operation:
    """Actual intercepted operation and raw trace/error evidence."""

    kind: str
    operation: str
    path: Path | None = None
    failed: bool = False
    raw: Any = None


@dataclass(frozen=True)
class DeliveryFailure:
    kind: str
    destination: Path | None
    reason: str
    raw: Any
    old_file_not_updated: bool | None = None


@dataclass
class ReportObservation:
    raw: Any
    diagnostics: tuple[Diagnostic, ...]
    outcomes: tuple[str, ...]
    # Actual shared report-schema evidence: published/native schema or inspected
    # common report-format definition, validated against these raw file bytes.
    # Never invent a schema identifier, infer equality from normalized events,
    # or require identical optional member presence in two JSON instances.
    schema: Any = None


@dataclass(frozen=True)
class ReportContent:
    """Actual outcome and native events, independent of JSON serialization.

    Each test-side record is (severity, code, message, effect, source triples,
    generated IRI); a source triple is (path, identifier, element type). These
    tuple representations are not a required Python production interface.
    """

    outcome: str
    events: tuple[tuple[Any, ...], ...]
    raw: Any


@dataclass
class SerializationObservation:
    data: bytes | None
    failure: Any = None


@dataclass
class DeliveryObservation:
    observation: Observation
    failure: Any = None


@dataclass
class CLIObservation:
    command: tuple[str, ...]
    returncode: int
    stdout: bytes
    stderr: bytes
    observation: Observation | None  # no conversion result for an actual invalid invocation
    console: tuple[Diagnostic, ...]
    # Observed conversion entry, from real instrumentation when needed; never
    # derive this solely from the expected exit code or configuration error.
    conversion_started: bool | None = None
    # Raw child-process instrumentation: actual input-processing entry and
    # native parser.error calls. This is not a production API or report.
    execution_trace: Any = None


@dataclass(frozen=True)
class Control:
    parameter: str
    choices: tuple[Any, ...] | None
    default: Any
    raw: Any  # actual help/signature/public-interface evidence
    arity: int | None = None


@dataclass
class ControlSurface:
    cli: Mapping[str, Control]
    python: Mapping[str, Control]  # indexed by semantic test-control name
    prohibited_features: Mapping[str, bool]  # actual observed feature presence
    software_version: str | None = None
    raw: Any = None
    # Conditional stream assertions must not invent entry-point support.
    stdout_supported: bool | None = None


def diagnostic_signatures(events):
    """Compare event meaning/multiplicity without imposing order or raw schema.

    The binding's semantic categories/facts must cover the actual event's
    meaning. Human wording and native object identity are not standardized.
    """
    return Counter((event.severity, event.kind, tuple(sorted(event.source_ids)),
                    tuple(sorted(event.source_types, key=lambda item: (type(item).__name__, repr(item)))),
                    tuple(sorted(event.generated_iris)),
                    tuple(sorted(event.facts)), tuple(sorted(event.identified_sources))) for event in events)


class Invocation(Protocol):
    def has_relation_cardinality_control(self, feature: str) -> bool:
        """Inspect actual public Python controls for the semantic feature
        omit_without_named_inverse or qualified. These test-side terms impose
        no production method/parameter spelling. CLI inspection is Wave 6.
        """
        ...

    def has_local_value_restriction_control(self) -> bool:
        """Inspect actual public Python controls for an optional allValuesFrom
        feature. No production parameter spelling is prescribed. Do not answer
        from the specification or tests; bind to the real interface evidence.
        The CLI surface is covered separately in its approved later wave.
        """
        ...

    def convert(
        self, source: Path, *, options: Mapping[str, Any], workdir: Path, faults: tuple[Fault, ...] = ()
    ) -> Observation:
        """Execute the public library; options are TEST-side semantic controls.

        Omitted controls must stay omitted so tests can examine real defaults.
        Do not auto-export diagnostics or repair the source. Use workdir for
        temporary execution artifacts; never write in fixture directories.
        """
        ...

    def attempt_source_input(self, source: Any, *, options: Mapping[str, Any], workdir: Path) -> SourceInputAttempt:
        """Submit the original object to the real public source argument.

        Retain native rejection or actual conversion result. Do not serialize,
        coerce, save, or pre-reject the object in this boundary.
        """
        ...

    def inspect_source_input_surface(self) -> SourceInputSurface:
        """Audit actual public entries/controls for fileless or checksum extensions."""
        ...

    def read_source_artifacts(self, graph: Graph) -> tuple[Node, ...]:
        """Identify source roles from actual provenance, retaining its RDF evidence."""
        ...

    def cli(self, source: Path | None, *, options: Mapping[str, Any], workdir: Path,
            output_path: Path | None = None, diagnostics_path: Path | None = None,
            extra_args: tuple[str, ...] = (), faults: tuple[Fault, ...] = ()) -> CLIObservation:
        """Run the REAL CLI subprocess; retain argv, both streams and native status.

        Omitted options stay omitted. Test semantic options map to inspected
        public flags; extra_args are literal CLI arguments. Never derive an
        outcome from severity/exit status, or rerun Python to fabricate CLI data.
        """
        ...

    def serialize(self, observation: Observation, *, target: str, faults: tuple[Fault, ...] = ()) -> SerializationObservation:
        """Explicit actual public ontology/provenance serialization to bytes."""
        ...

    def deliver(self, observation: Observation, *, output_path: Path, faults: tuple[Fault, ...] = ()) -> DeliveryObservation:
        """Actual public explicit file-delivery operation, including its failures.

        Do not implement delivery eligibility, failure precedence or sidecar
        sequencing in this test binding. Those are production assertions.
        """
        ...

    def export_diagnostics(self, observation: Observation, path: Path, *, faults: tuple[Fault, ...] = ()) -> DeliveryObservation:
        """Separate real Python export; normalize an actual return or exception."""
        ...

    def read_report(self, path: Path) -> ReportObservation:
        """Read the actual JSON using its real shared format; retain all events."""
        ...

    def report_content(self, observation: Observation) -> ReportContent:
        """Read actual public Python result fields without calling its writer."""
        ...

    def cli_report_content(self, process: CLIObservation) -> tuple[ReportContent, ReportContent]:
        """Read native conversion-return and post-delivery snapshots, independent of JSON."""
        ...

    def diagnostic_mirror_records(
        self, process: CLIObservation, report: ReportObservation
    ) -> tuple[Counter[bytes], Counter[bytes]]:
        """Read independent unfiltered console and JSON events as comparable records.

        Console rendering is binding knowledge, not required diagnostic wording.
        Preserve event content and multiplicity without requiring event order.
        """
        ...

    def inspect_controls(self) -> ControlSurface:
        """Inspect actual public help/signatures, defaults and feature availability."""
        ...

    def read_diagnostics(self, observation: Observation) -> tuple[Diagnostic, ...]:
        """Read actual public diagnostic access again, rather than this snapshot."""
        ...

    def read_outcome(self, observation: Observation) -> str:
        """Read the actual public conversion outcome again."""
        ...

    def read_ontology(self, observation: Observation) -> Graph | None:
        """Read the actual delivered graph again; do not reconstruct one."""
        ...

    def read_provenance(self, observation: Observation) -> Graph | None:
        """Read the current separate provenance graph from the public result."""
        ...

    def read_property_stereotype_comments(self, observation: Observation) -> tuple[CommentMeaning, ...]:
        """Read actual begin/end declaration meanings and their raw RDF literals.

        Association-end contexts must come from the actual comment, not the
        requested occurrence. Multiple meanings may share one combined literal.
        ``english`` records actual wording; no exact prose or mandatory @en
        spelling is prescribed. Unknown wording must remain unavailable.
        This test-side reader is not a production Python API.
        """
        ...

    def read_relation_limitation_source_ids(self, observation: Observation, source: Path) -> frozenset[str]:
        """Read the affected relation IDs identified by actual limitation warnings.

        Consolidated events may identify several relations. Uninterpreted
        reported locators remain unbound; no event is inferred from input.
        This reader is not a production API or prescribed locator format.
        """
        ...

    def read_relation_stereotype_annotations(self, observation: Observation, source: Path) -> tuple[tuple[Node, Node, Node], ...]:
        """Audit actual relation-declaration output; unknown forms are unbound.

        Source text and independently required annotations are retained.
        This is a replaceable test-side reader, not a production API.
        """
        ...

    def read_historical_dependence_annotations(self, observation: Observation, source: Path) -> tuple[tuple[Node, Node, Node], ...]:
        """Read additional stereotype-declaration annotations in actual RDF.

        Source-authored text and independent flag comments are not stereotype
        preservation. Retain raw triples for any interpreted output; unknown
        annotations require a verified interpretation, never assumed absence.
        This scoped test-side reader is not a production Python interface.
        """
        ...

    def read_relation_aggregation_comments(self, observation: Observation, source: Path) -> tuple[CommentMeaning, ...]:
        """Read aggregation value and end context from actual emitted comments.

        Retain each RDF subject/literal. Unknown native annotation forms must
        remain unavailable rather than establish absence. Test-side API only.
        """
        ...


class _UnboundInvocation:
    def has_relation_cardinality_control(self, feature):
        self._unavailable()

    def has_local_value_restriction_control(self):
        self._unavailable()

    def _unavailable(self) -> None:
        raise ImplementationUnavailable(
            "This adapter operation is not yet bound to the real DirectKG interface. "
            "RD-02 binds basic file conversion, result reads and fresh-file CLI reports; "
            "do not substitute a transformer, skip, or xfail other operations."
        )

    def convert(self, source, *, options, workdir, faults=()):
        self._unavailable()

    def attempt_source_input(self, source, *, options, workdir):
        self._unavailable()

    def inspect_source_input_surface(self):
        self._unavailable()

    def read_source_artifacts(self, graph):
        self._unavailable()

    def cli(self, source, *, options, workdir, output_path=None, diagnostics_path=None, extra_args=(), faults=()):
        self._unavailable()

    def serialize(self, observation, *, target, faults=()):
        self._unavailable()

    def deliver(self, observation, *, output_path, faults=()):
        self._unavailable()

    def export_diagnostics(self, observation, path, *, faults=()):
        self._unavailable()

    def read_report(self, path):
        self._unavailable()

    def report_content(self, observation):
        self._unavailable()

    def cli_report_content(self, process):
        self._unavailable()

    def diagnostic_mirror_records(self, process, report):
        self._unavailable()

    def inspect_controls(self):
        self._unavailable()

    def read_diagnostics(self, observation):
        self._unavailable()

    def read_outcome(self, observation):
        self._unavailable()

    def read_ontology(self, observation):
        self._unavailable()

    def read_provenance(self, observation):
        self._unavailable()

    def read_property_stereotype_comments(self, observation):
        self._unavailable()

    def read_relation_limitation_source_ids(self, observation, source):
        self._unavailable()

    def read_relation_stereotype_annotations(self, observation, source):
        self._unavailable()

    def read_historical_dependence_annotations(self, observation, source):
        self._unavailable()

    def read_relation_aggregation_comments(self, observation, source):
        self._unavailable()


class _BoundFieldsOnly:
    """Partial bindings must not turn unread evidence into empty/false results."""

    def __getattribute__(self, name):
        if name in type(self).__dataclass_fields__ and name not in type(self)._available_fields:
            raise ImplementationUnavailable(f"Observation reader {name!r} is not bound in RD-02")
        return object.__getattribute__(self, name)

    def __repr__(self):
        return f"{type(self).__name__}(available={sorted(type(self)._available_fields)!r})"


class _BasicObservation(_BoundFieldsOnly, Observation):
    _available_fields = frozenset({"ontology", "outcome", "diagnostics", "configuration_error", "native"})


class _PythonObservation(_BasicObservation):
    _available_fields = _BasicObservation._available_fields | {"provenance"}


class _InputObservedPython(_PythonObservation):
    _available_fields = _PythonObservation._available_fields | {
        "conversion_started", "execution_trace", "diagnostics_exports"}


class _MetadataPythonObservation(_PythonObservation):
    _available_fields = _PythonObservation._available_fields | {"external_metadata_output"}


class _InputObservedMetadataPython(_InputObservedPython):
    _available_fields = _InputObservedPython._available_fields | {"external_metadata_output"}


class _ProvenanceObservedPython(_InputObservedMetadataPython):
    _available_fields = _InputObservedMetadataPython._available_fields | {"operations"}


class _MetadataCLIObservation(_BasicObservation):
    _available_fields = _BasicObservation._available_fields | {"external_metadata_output"}


class _InspectedControlSurface(_BoundFieldsOnly, ControlSurface):
    _available_fields = frozenset({"cli", "python", "prohibited_features", "software_version", "raw", "stdout_supported"})


class _NoReportCLIObservation(_BasicObservation):
    _available_fields = _BasicObservation._available_fields | {"diagnostics_exports"}


class _SerializationFaultCLIObservation(_BoundFieldsOnly, Observation):
    _available_fields = frozenset({"outcome", "native"})


class _PythonDeliveryObservation(_InputObservedMetadataPython):
    _available_fields = _InputObservedMetadataPython._available_fields | {
        "delivery_failures", "operations", "valid_artifacts", "pre_delivery_ontology",
        "provenance_roles", "configuration_controls", "configuration_literal",
        "output_artifact_output", "output_artifact_evidence", "output_filename",
        "output_format", "embedded_output_configuration", "provenance_mode",
    }


class _ReportProcess(_BoundFieldsOnly, CLIObservation):
    _available_fields = frozenset({"command", "returncode", "stdout", "stderr", "observation", "console",
                                   "conversion_started", "execution_trace"})


class _ConsoleDiagnostic(_BoundFieldsOnly, Diagnostic):
    _available_fields = frozenset({"severity", "message", "raw", "code"})


def _observed_console(stdout, stderr):
    """Read severity from actual console records on either captured stream.

    Renderer spellings belong here, not in behavioral assertions. Retain each
    raw byte record and its stream; do not obtain events from JSON or exit codes.
    Source/category/fact interpretation remains explicitly unbound.
    """
    header = re.compile(rb"^[ \t]*(?:\[(INFO|WARNING|ERROR)\]|(INFO|WARNING|ERROR):)[ \t]*",
                        re.MULTILINE | re.IGNORECASE)
    events = []
    for stream, data in (("stdout", stdout), ("stderr", stderr)):
        matches = list(header.finditer(data))
        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(data)
            raw = data[match.start():end]
            # The inspected bracket-header renderer displays CODE: immediately
            # after severity. A bare severity header does not establish a code.
            displayed = re.match(rb"([^:\s]*):", data[match.end():end]) if match.group(1) else None
            events.append(_ConsoleDiagnostic(
                (match.group(1) or match.group(2)).decode("ascii").upper(),
                "console", raw.decode("utf-8", errors="replace"),
                raw={"stream": stream, "data": raw},
                code=displayed.group(1).decode("utf-8", errors="replace") if displayed else None,
            ))
    return tuple(events)


class _MetadataCapture:
    """Observe actual RDF additions inside the inspected external-metadata writer.

    The current writer emits the selected external values only. Observing its
    real Graph.add calls distinguishes those contributions from independently
    generated metadata, including duplicate additions of an existing triple.
    This class is also copied into the temporary CLI observer, never production.
    """

    def __init__(self):
        from ontouml_directkg.conversion import emit_metadata
        from rdflib import Graph
        self.writer_code = emit_metadata.__code__
        self.add_code = Graph.add.__code__
        self.frames = {}
        self.entries = self.returns = 0
        self.triples = []

    def observe(self, frame, event, argument):
        if frame.f_code is self.writer_code:
            if event == "call":
                self.entries += 1
                self.frames[frame] = frame.f_locals["graph"]
            elif event == "return":
                self.returns += 1
                self.frames.pop(frame, None)
        elif event == "call" and frame.f_code is self.add_code:
            if any(frame.f_locals["self"] is graph for graph in self.frames.values()):
                self.triples.append(tuple(frame.f_locals["triple"]))


@contextmanager
def _observe_metadata_output():
    capture = _MetadataCapture()
    previous = sys.getprofile()

    def observe(frame, event, argument):
        capture.observe(frame, event, argument)
        if previous is not None:
            previous(frame, event, argument)

    sys.setprofile(observe)
    try:
        yield capture
    finally:
        active = sys.getprofile() is observe
        sys.setprofile(previous)
        if not active or capture.frames or capture.entries != capture.returns:
            raise ImplementationUnavailable("Incomplete native metadata-emission evidence")


def _captured_metadata(capture, ontology):
    if ontology is None:
        return ()  # actual public result has no eligible ontology
    if not capture.entries or capture.entries != capture.returns:
        raise ImplementationUnavailable("Interpret the current external-metadata emission boundary")
    return tuple(capture.triples)


class _OntologySerializationProbe:
    """Fault only the main ontology's native Turtle or encoding operation."""

    def __init__(self, operation):
        from ontouml_directkg.conversion import ConversionResult

        self.operation = operation
        self.to_turtle = ConversionResult.to_turtle
        self.before = None
        self.calls = []

    def capture(self, result):
        from rdflib import Graph

        if result.ontology is not None:
            self.before = Graph() + result.ontology

    def serialize(self, result):
        from unittest.mock import patch

        if self.operation == "serialize":
            def fail(*args, **kwargs):
                error = ValueError("Cyclic RDF list")
                self.calls.append(error)
                raise error

            with patch.object(result.ontology, "serialize", fail):
                return self.to_turtle(result)

        class UnencodableTurtle(str):
            def encode(text, *args, **kwargs):
                try:
                    return super().encode(*args, **kwargs)
                except UnicodeEncodeError as error:
                    self.calls.append(error)
                    raise

        return UnencodableTurtle(self.to_turtle(result) + "\ud800")

    def snapshot(self, result):
        from rdflib.compare import isomorphic

        return {
            "faults": [{"operation": self.operation, "error_type": type(error).__name__,
                        "reason": str(error)} for error in self.calls],
            "graph_preserved": (self.before is not None and result.ontology is not None
                                and isomorphic(self.before, result.ontology)),
            "provenance_mode": result.provenance_mode,
        }


def _native_diagnostic_fields(events):
    return [(event.severity, event.code, event.message, event.effect,
             tuple((source.path, source.identifier, source.element_type) for source in event.sources),
             event.generated_iri) for event in events]


def diagnostic_record_counts(events):
    """Count native and traced diagnostic records without imposing source order."""
    return Counter((severity, code, message, effect, tuple(sorted(map(tuple, sources), key=repr)), iri)
                   for severity, code, message, effect, sources, iri in events)


def _fail_relation_emission(trace):
    """Raise at the actual stage, after collecting the native graph and diagnostic evidence."""
    import inspect
    from unittest.mock import patch
    from ontouml_directkg import conversion

    emit = conversion.emit_relations
    signature = inspect.signature(emit)

    def fail(*args, **kwargs):
        arguments = signature.bind(*args, **kwargs).arguments
        emit(*args, **kwargs)
        error = RuntimeError("RD04-TRANSFORM-417")
        trace["transformation_failure"] = {
            "graph_size": len(arguments["graph"]),
            "earlier_events": _native_diagnostic_fields(arguments["diagnostics"].events),
            "cause": str(error),
        }
        raise error

    return patch.object(conversion, "emit_relations", fail)


def _fail_result_construction(trace):
    """Raise once when constructing a non-aborted result, allowing aborted-result construction."""
    import inspect
    from unittest.mock import patch
    from ontouml_directkg import conversion

    real_result = conversion.ConversionResult
    real_init = real_result.__init__
    signature = inspect.signature(real_init)
    state = {"triggered": False}

    def fail_on_success(self, *args, **kwargs):
        bound = signature.bind(self, *args, **kwargs)
        bound.apply_defaults()
        arguments = bound.arguments
        ontology = arguments["ontology"]
        outcome = arguments["outcome"]
        if not state["triggered"] and ontology is not None and outcome != "aborted":
            state["triggered"] = True
            error = RuntimeError("RD04-RESULT-CONSTRUCTION-509")
            trace["transformation_failure"] = {
                "stage": "result_construction",
                "graph_size": len(ontology),
                "attempted_outcome": outcome,
                "earlier_events": _native_diagnostic_fields(arguments["diagnostics"]),
                "cause": str(error),
            }
            raise error
        return real_init(self, *args, **kwargs)

    return patch.object(real_result, "__init__", fail_on_success)


def _transformation_fault(faults):
    for operation in ("emit_relations", "result_construction",
                      "allocate_resources", "allocate_inverses", "allocate_name_fallbacks"):
        if faults == (Fault("transformation", operation),):
            return operation
    return None


def _force_escaped_id_collision(operation, trace):
    """Change one escape result in the real allocator, then observe its response."""
    import sys
    from unittest.mock import patch
    from ontouml_directkg import classifiers, conversion, inverses

    module, allocator_name, existing_id, changed_id = {
        "allocate_resources": (classifiers, "allocate_resources", "cA", "cB"),
        "allocate_inverses": (inverses, "allocate_inverses", "cA", "sFocus"),
        "allocate_name_fallbacks": (classifiers, "allocate_resources", "vPending", "vApproved"),
    }[operation]
    allocate = getattr(conversion, allocator_name)
    escape = module.escape_id

    def collision(identifier, *, whole_local_name=True):
        original = escape(identifier, whole_local_name=whole_local_name)
        evidence = trace["allocation_collision"]
        if identifier == existing_id:
            evidence["existing_candidate"] = original
            evidence["existing_whole_local_name"] = whole_local_name
        if identifier != changed_id:
            return original
        existing = escape(existing_id, whole_local_name=whole_local_name)
        evidence.update(
            original_candidates={existing_id: existing, identifier: original},
            forced_candidate=existing,
            forced_whole_local_name=whole_local_name,
        )
        return existing

    def observed_allocation(*args, **kwargs):
        native = sys._getframe(1).f_locals
        evidence = {
            "stage": native["stage"],
            "earlier_events": _native_diagnostic_fields(native["diagnostics"].events),
        }
        if operation == "allocate_inverses":
            evidence["existing_candidate"] = str(native["resources"][existing_id]).removeprefix(native["base"])
        trace["allocation_collision"] = evidence
        with patch.object(module, "escape_id", collision):
            try:
                return allocate(*args, **kwargs)
            except Exception as error:
                evidence["cause"] = str(error)
                raise

    return patch.object(conversion, allocator_name, observed_allocation)


def escaped_id_collision_diagnostic(record, evidence):
    """Tie the reported error to the observed allocator and its native cause."""
    severity, code, message, _, _, _ = record
    stage = (evidence.get("stage") or "").strip()
    cause = " ".join((evidence.get("cause") or "").split())
    return (severity == "ERROR" and code == "INTERNAL_TRANSFORMATION_FAILURE"
            and bool(stage) and stage in message
            and bool(cause) and cause in " ".join(message.split()))


def _fail_required_provenance(trace):
    """Inject a failure at the real required-provenance construction boundary."""
    import inspect
    from unittest.mock import patch
    from ontouml_directkg import provenance

    construct = provenance.construct_provenance
    signature = inspect.signature(construct)
    trace["provenance_probe"] = {"module": construct.__module__,
                                  "name": construct.__qualname__, "calls": []}

    def fail(*args, **kwargs):
        signature.bind(*args, **kwargs)
        error = RuntimeError("RD04-PROVENANCE-271")
        trace["provenance_probe"]["calls"].append({"cause": str(error), "operation": "construct"})
        raise error

    return patch.object(provenance, "construct_provenance", fail)


_CLI_OBSERVER = '''\
import argparse
import atexit
import errno
import json
import os
import sys
from pathlib import Path
from ontouml_directkg.conversion import ConversionResult, read_project, convert
from ontouml_directkg.diagnostics import export_report

reader_code = read_project.__code__
conversion_code = convert.__code__
parser_error_code = argparse.ArgumentParser.error.__code__
trace = {"input_reader": {"module": read_project.__module__, "name": read_project.__qualname__},
         "conversion_started": False, "parser_errors": [],
         "conversion_calls": 0, "conversion_returns": 0, "diagnostics_exports": [],
         "console_io_errors": [], "report_export_errors": [], "runtime_faults": [],
         "delivery_faults": []}
metadata = _MetadataCapture()
native_result = None
ontology_fault = os.environ.get("DIRECTKG_TEST_ONTOLOGY_FAULT")
probe = _OntologySerializationProbe(ontology_fault) if ontology_fault is not None else None
transformation_fault = os.environ.get("DIRECTKG_TEST_TRANSFORMATION_FAULT")
provenance_fault = os.environ.get("DIRECTKG_TEST_PROVENANCE_FAULT") == "construct"
cli_faults = json.loads(os.environ.get("DIRECTKG_TEST_CLI_FAULTS", "[]"))
if transformation_fault == "emit_relations":
    _fail_relation_emission(trace).start()
elif transformation_fault == "result_construction":
    _fail_result_construction(trace).start()
elif transformation_fault:
    _force_escaped_id_collision(transformation_fault, trace).start()
if provenance_fault:
    _fail_required_provenance(trace).start()
if probe is not None:
    def observed_turtle(result):
        return probe.serialize(result)

    ConversionResult.to_turtle = observed_turtle

_wrapped_streams = []

class _FailingConsoleStream:
    def __init__(self, wrapped, stream_name, operation):
        self._wrapped = wrapped
        self._stream_name = stream_name
        self._operation = operation
        self.active = True

    def write(self, data):
        if self.active and self._operation in {"write", "encode", "write_unexpected"}:
            if self._operation == "encode":
                err = UnicodeEncodeError("ascii", "\\u2603", 0, 1, "ordinal not in range(128)")
            elif self._operation == "write_unexpected":
                err = RuntimeError(f"Unexpected {self._stream_name} write failure")
            else:
                err = OSError(errno.EIO, f"Injected {self._stream_name} write failure")
            trace["console_io_errors"].append({
                "stream": self._stream_name,
                "operation": self._operation,
                "error_type": type(err).__name__,
                "reason": str(err),
            })
            raise err
        return self._wrapped.write(data)

    def flush(self):
        if self.active and self._operation in {"flush", "flush_unexpected"}:
            if self._operation == "flush_unexpected":
                err = RuntimeError(f"Unexpected {self._stream_name} flush failure")
            else:
                err = OSError(errno.EIO, f"Injected {self._stream_name} flush failure")
            trace["console_io_errors"].append({
                "stream": self._stream_name,
                "operation": self._operation,
                "error_type": type(err).__name__,
                "reason": str(err),
            })
            raise err
        return self._wrapped.flush()

    def __getattr__(self, name):
        return getattr(self._wrapped, name)

for _fault in cli_faults:
    _kind, _op, _fpath = _fault["kind"], _fault["operation"], _fault.get("path")
    if _kind == "provenance" and _op == "output_construct":
        import ontouml_directkg.delivery as _delivery_mod
        _prov_mod = _delivery_mod.execution_provenance
        trace.setdefault("provenance_probe", {"module": _prov_mod.output_provenance.__module__,
                                              "name": _prov_mod.output_provenance.__qualname__, "calls": []})
        def _fail_output_provenance(*args, **kwargs):
            err = RuntimeError("RD04-OUTPUT-PROVENANCE-272")
            trace["provenance_probe"]["calls"].append({"cause": str(err), "operation": "output_construct"})
            raise err
        _prov_mod.output_provenance = _fail_output_provenance
    elif _kind == "sidecar" and _op == "encode":
        _orig_prov_turtle = ConversionResult.to_provenance_turtle
        def _unencodable_prov(result, _orig=_orig_prov_turtle):
            class _BadStr(str):
                def encode(text, *args, **kwargs):
                    try:
                        return super().encode(*args, **kwargs)
                    except UnicodeEncodeError as err:
                        trace["delivery_faults"].append({"kind": "sidecar", "operation": "encode", "reason": str(err)})
                        raise
            return _BadStr(_orig(result) + "\\ud800")
        ConversionResult.to_provenance_turtle = _unencodable_prov
    elif _kind in {"ontology", "sidecar"} and _op == "unexpected":
        import ontouml_directkg.delivery as _delivery_mod
        _orig_write_artifact = _delivery_mod._write_artifact
        def _failing_write_artifact(path, content, _k=_kind, _fp=_fpath, _orig=_orig_write_artifact):
            target_match = (_fp is not None and Path(path) == Path(_fp)) or (
                _fp is None and ((_k == "sidecar") == str(path).endswith(".provenance.ttl"))
            )
            if target_match:
                err = RuntimeError(f"Unexpected runtime error during {_k} delivery")
                trace["delivery_faults"].append({"kind": _k, "operation": "unexpected", "path": str(path), "reason": str(err)})
                raise err
            return _orig(path, content)
        _delivery_mod._write_artifact = _failing_write_artifact
    elif _kind == "diagnostics" and _op in {"serialize", "unexpected"}:
        import ontouml_directkg.diagnostics as _diag_mod
        def _failing_json_dumps(*args, _op_name=_op, **kwargs):
            err = (TypeError("Injected diagnostics JSON serialization failure")
                   if _op_name == "serialize" else RuntimeError("Unexpected diagnostics export error"))
            trace["report_export_errors"].append({"operation": _op_name, "error_type": type(err).__name__, "reason": str(err)})
            raise err
        _diag_mod.json.dumps = _failing_json_dumps
    elif _kind in {"stdout", "stderr"} and _op in {"write", "encode", "flush", "write_unexpected", "flush_unexpected"}:
        _proxy = _FailingConsoleStream(getattr(sys, _kind), _kind, _op)
        setattr(sys, _kind, _proxy)
        _wrapped_streams.append(_proxy)
    elif _kind == "runtime" and _op == "pre_conversion":
        import ontouml_directkg.conversion as _conv_mod
        def _failing_select_base(*args, **kwargs):
            err = RuntimeError("Unexpected pre-conversion runtime failure")
            trace["runtime_faults"].append({"stage": "pre_conversion", "reason": str(err)})
            raise err
        _conv_mod.select_base = _failing_select_base
    elif _kind == "runtime" and _op == "parser_setup":
        import ontouml_directkg.cli as _cli_mod
        def _failing_build_parser(*args, **kwargs):
            err = RuntimeError("Unexpected parser setup runtime failure")
            trace["runtime_faults"].append({"stage": "parser_setup", "reason": str(err)})
            raise err
        _cli_mod.build_parser = _failing_build_parser
    elif _kind == "runtime" and _op == "post_delivery":
        import ontouml_directkg.delivery as _delivery_mod
        _orig_deliver = _delivery_mod.deliver
        def _post_delivery_runtime_fail(result, destination, _orig=_orig_deliver):
            real_delivered = _orig(result, destination)
            class _FailingFailuresDeliveryResult:
                def __init__(self, wrapped):
                    self._wrapped = wrapped
                @property
                def failures(self):
                    err = RuntimeError("Unexpected post-delivery runtime failure")
                    trace["runtime_faults"].append({"stage": "post_delivery", "reason": str(err)})
                    raise err
                def __getattr__(self, name):
                    return getattr(self._wrapped, name)
            return _FailingFailuresDeliveryResult(real_delivered)
        _delivery_mod.deliver = _post_delivery_runtime_fail

_diag_write_fault = any(f["kind"] == "diagnostics" and f["operation"] in {"create", "write"} for f in cli_faults)
write_bytes = Path.write_bytes

def observed_write_bytes(path, data):
    is_report = sys._getframe(1).f_code is export_report.__code__
    if is_report and _diag_write_fault:
        error = OSError(errno.EACCES, "Permission denied", str(path))
        trace["report_io_errors"].append({"destination": str(path), "errno": error.errno, "reason": str(error)})
        raise error
    try:
        return write_bytes(path, data)
    except OSError as error:
        if is_report:
            trace["report_io_errors"].append({"destination": str(path), "errno": error.errno,
                                              "reason": str(error)})
        raise

Path.write_bytes = observed_write_bytes
trace["report_at_export"] = []
trace["report_io_errors"] = []

def report_fields(outcome, events):
    return {"outcome": outcome, "events": _native_diagnostic_fields(events)}

def report_snapshot(result):
    # Copy public field values immediately, without calling the report writer.
    return report_fields(result.outcome, result.diagnostics)

def observe(frame, event, argument):
    global native_result
    metadata.observe(frame, event, argument)
    if frame.f_code is conversion_code:
        if event == "call":
            trace["conversion_calls"] += 1
        elif event == "return":
            trace["conversion_returns"] += 1
            native_result = argument
            if argument is not None:
                trace["conversion_report"] = report_snapshot(argument)
                if probe is not None:
                    probe.capture(argument)
    if event == "call":
        if frame.f_code is reader_code:
            trace["conversion_started"] = True
        elif frame.f_code is parser_error_code:
            trace["parser_errors"].append(frame.f_locals["message"])
        elif frame.f_code is export_report.__code__:
            trace["diagnostics_exports"].append(str(frame.f_locals["destination"]))
            if probe is not None or transformation_fault or provenance_fault or cli_faults:
                trace["report_at_export"].append(report_fields(
                    frame.f_locals["outcome"], frame.f_locals["events"]))

def finish():
    for _stream in _wrapped_streams:
        _stream.active = False
    trace["profile_active_at_exit"] = sys.getprofile() is observe
    sys.setprofile(None)
    trace["observation_completed"] = True
    trace["metadata"] = {"entries": metadata.entries, "returns": metadata.returns,
                         "active_frames": len(metadata.frames),
                         "triples": [[term.n3() for term in triple] for triple in metadata.triples]}
    if native_result is not None:
        # Copy the actual public result after CLI delivery has finished. Do not
        # call export_report/asdict or read its report to obtain these records.
        trace["native_report"] = report_snapshot(native_result)
        if probe is not None:
            trace["ontology_serialization"] = probe.snapshot(native_result)
    with open(os.environ["DIRECTKG_TEST_CLI_TRACE"], "w", encoding="utf-8") as output:
        json.dump(trace, output)

sys.setprofile(observe)
atexit.register(finish)
'''


@contextmanager
def _observe_python_input():
    """Observe the actual reader and shared report writer during one Python call.

    Like the CLI observer, this uses inspected native code objects and standard
    profiling. No function is replaced and no rejection is inferred from input
    options. Preserve any existing profile hook and refuse incomplete evidence.
    """
    from ontouml_directkg.conversion import read_project
    from ontouml_directkg.diagnostics import export_report

    reader_code, writer_code = read_project.__code__, export_report.__code__
    trace = {"input_reader": read_project, "report_writer": export_report,
             "conversion_started": False, "diagnostics_exports": []}
    previous = sys.getprofile()

    def observe(frame, event, argument):
        if event == "call":
            if frame.f_code is reader_code:
                trace["conversion_started"] = True
            elif frame.f_code is writer_code:
                trace["diagnostics_exports"].append(Path(frame.f_locals["destination"]))
        if previous is not None:
            previous(frame, event, argument)

    sys.setprofile(observe)
    try:
        yield trace
    finally:
        active = sys.getprofile() is observe
        sys.setprofile(previous)
        trace["observation_completed"] = active
        if not active:
            raise ImplementationUnavailable("Incomplete Python input-processing evidence")


def _run_observed_cli(command, workdir, *, ontology_fault=None, transformation_fault=None, provenance_fault=False, cli_faults=()):
    """Observe the real -m CLI without replacing conversion or parser behavior.

    The inspected converter finishes configuration validation before calling
    its actual input reader. A standard Python profile hook observes that entry
    and native argparse rejection calls inside the same CLI execution. Startup
    and completion evidence are mandatory; no missing trace means 'not started'.
    Reader/renderer implementation knowledge stays in this replaceable binding.
    """
    with TemporaryDirectory(prefix="directkg-cli-observer-", dir=workdir) as directory:
        directory = Path(directory)
        observers = tuple(map(inspect.getsource, (_MetadataCapture, _OntologySerializationProbe,
                                                   _native_diagnostic_fields, _fail_relation_emission,
                                                   _fail_result_construction, _force_escaped_id_collision,
                                                   _fail_required_provenance)))
        (directory / "sitecustomize.py").write_text("\n".join((*observers, _CLI_OBSERVER)), encoding="utf-8")
        trace_path = directory / "execution.json"
        environment = dict(os.environ)
        environment["DIRECTKG_TEST_CLI_TRACE"] = str(trace_path)
        environment.pop("DIRECTKG_TEST_ONTOLOGY_FAULT", None)
        environment.pop("DIRECTKG_TEST_TRANSFORMATION_FAULT", None)
        environment.pop("DIRECTKG_TEST_PROVENANCE_FAULT", None)
        environment.pop("DIRECTKG_TEST_CLI_FAULTS", None)
        if ontology_fault is not None:
            environment["DIRECTKG_TEST_ONTOLOGY_FAULT"] = ontology_fault
        if transformation_fault:
            environment["DIRECTKG_TEST_TRANSFORMATION_FAULT"] = transformation_fault
        if provenance_fault:
            environment["DIRECTKG_TEST_PROVENANCE_FAULT"] = "construct"
        if cli_faults:
            environment["DIRECTKG_TEST_CLI_FAULTS"] = json.dumps([
                {"kind": f.kind, "operation": f.operation, "path": str(f.path) if f.path is not None else None}
                for f in cli_faults
            ])
        environment["PYTHONPATH"] = str(directory) + (
            os.pathsep + environment["PYTHONPATH"] if environment.get("PYTHONPATH") else ""
        )
        completed = subprocess.run(command, cwd=workdir, capture_output=True, check=False, env=environment)
        try:
            trace = json.loads(trace_path.read_bytes())
        except (OSError, ValueError) as exc:
            raise ImplementationUnavailable("The real CLI input-processing observer did not complete") from exc
        if (trace.get("profile_active_at_exit") is not True
                or trace.get("observation_completed") is not True
                or type(trace.get("conversion_started")) is not bool
                or not isinstance(trace.get("parser_errors"), list)):
            raise ImplementationUnavailable("Incomplete CLI input-processing evidence")
        return completed, trace


_DIAGNOSTIC_KINDS = {
    "REQUIRED_PROVENANCE": "required_provenance",
    "INTERNAL_TRANSFORMATION_FAILURE": "internal_transformation_failure",
    "ONTOLOGY_DELIVERY": "ontology_delivery", "SIDECAR_DELIVERY": "sidecar_delivery",
    "MISSING_SOURCE_ID": "missing_id", "INVALID_SOURCE_ID": "invalid_id",
    "FAILED_RELATION": "failed_relation", "DUPLICATE_SOURCE_ID": "duplicate_id",
    "UNTRANSFORMABLE_ENUMERATION_VALUE": "invalid_enumeration_value",
    "ABSTRACTNESS_ANNOTATION": "abstractness", "MISSING_CLASS_NAME": "missing_name",
    "MISSING_NAME": "missing_name", "GENERIC_ID_FALLBACK": "generic_id_fallback",
    "MISSING_STEREOTYPE": "missing_stereotype", "UNRECOGNIZED_STEREOTYPE": "unrecognized_stereotype",
    "UNKNOWN_INFORMATION": "unknown_information", "UNPROCESSABLE_DOCUMENT": "unprocessable_document",
    "MATERIAL_CHAIN_COMPATIBILITY": "chain_compatibility", "MATERIAL_CHAIN_AMBIGUITY": "chain_ambiguity",
    "EXTENSIONALITY_ANNOTATION": "extensionality",
    "VOID_DATATYPE": "void_datatype", "ORDERING_ANNOTATION": "ordering",
    "RELATION_NAMING": "relation_naming", "MISSING_RELATION_NAME": "missing_name",
    "UNAVAILABLE_GROUNDING_RELATOR": "unavailable_grounding_relator",
    "METADATA_FIELD": "metadata_field", "METADATA_INPUT": "metadata_input",
    "UNMAPPED_RELATION_STEREOTYPE": "unmapped_relation_stereotype",
    "MISSING_CARDINALITY": "missing_cardinality",
    "INVALID_CARDINALITY": "invalid_cardinality",
    "SINGLETON_COMPLETENESS": "singleton_completeness",
    "RELATION_SET_COMPLETENESS": "relation_set_completeness",
    "EMPTY_GENERALIZATION_SET": "empty_generalization_set",
    "FAILED_CLASS_GENERALIZATION": "failed_class_generalization",
    "FAILED_RELATION_GENERALIZATION": "failed_relation_generalization",
    "UNRESOLVED_GENERALIZATION_SET_MEMBER": "unresolved_generalization_set_member",
    "PLACEHOLDER_BASE": "placeholder_base",
    "DERIVED_STATUS_ANNOTATION": "derived_status",
    "DISCARDED_INSTANTIATION_INFORMATION": "discarded_instantiation_data",
    "UNRESOLVED_ATTRIBUTE_TYPE": "unresolved_attribute_type",
    "UNRESOLVED_PROPERTY_REFERENCE": "unresolved_property_reference",
    "INVALID_PROPERTY_REFERENCES": "invalid_property_references",
    "AMBIGUOUS_PROJECT_LANGUAGE": "ambiguous_language",
    "UNSUPPORTED_RELATION_CONNECTOR": "unsupported_connector",
}


DKGM_CHAIN_WARNING_FACTS = frozenset({"dkgm_chains_absent", "dkgm_chains_consumer_supply"})


def read_dkgm_mode_setting(settings):
    """Read the effective setting from observed YAML, independent of CLI spelling."""
    keys = {"dkgm_vocabulary", "dkgm_vocabulary_mode"}
    values = [value for key, value in settings.items()
              if isinstance(key, str) and key.casefold().replace("-", "_") in keys]
    if len(values) > 1 and any(value != values[0] for value in values[1:]):
        raise ImplementationUnavailable("Conflicting native DKGM vocabulary settings in provenance")
    return values[0] if values else None


def relation_end_comment_meanings(graph, subject):
    """Interpret affirmative association-end facts from actual RDF comments.

    Known native wording and equivalent affirmative phrases are bound. The
    returned evidence retains the literal, its role, and the reported value.
    """
    from rdflib.namespace import RDFS

    pattern = (r"(?:ontouml source metadata:\s*)?(?:the )?(source|target) (?:association )?end\b"
               r"\s*:?\s*(?:(?:is )?(read[- ]only)|(?:has |uses |is marked with )?(shared|composite) aggregation)")
    for literal in graph.objects(subject, RDFS.comment):
        if not isinstance(literal, Literal):
            continue
        clauses = re.split(r"[.;!\n]|\s+and\s+(?=(?:the )?(?:source|target)\b)", str(literal).casefold())
        for clause in clauses:
            match = re.fullmatch(pattern, clause.strip())
            if match is None:
                continue
            end, read_only, aggregation = match.groups()
            context = end + "_end"
            if read_only is not None:
                yield CommentMeaning(subject, literal, "isReadOnly", True, context=context)
            else:
                yield CommentMeaning(subject, literal, "aggregationKind", aggregation.upper(), context=context)


def dkgm_chain_facts(message, effect):
    """Read the omission and affirmative supply guidance in a native event."""
    # Either field can contain a complete clause without terminal punctuation.
    clauses = [
        " ".join(clause.split())
        for field in (message, effect)
        for clause in re.split(r"[.!?;]+", field.casefold().replace("`", "").replace("’", "'"))
    ]
    chain = (r"(?:dkgm|generic)(?:[ -]+(?:dkgm|generic|mereological|mereology|property|inference))*"
             r"[ -]+chains?(?:[ -]+axioms?)?")
    count = r"(?:one|two|three|\d+)"
    chain_reference = (rf"(?:(?:all(?: {count})?|each|{count})(?: of)? )?"
                       rf"(?:the |these |those |every |some )?(?:{count} )?{chain}")
    whole_core = (rf"(?:(?:all(?: (?:three|3))?(?: of)?|each of) )?"
                  rf"(?:the |these |those |every )?(?:(?:three|3) )?{chain}")
    output = (r"(?:(?:the |this )?(?:(?:generated|delivered) (?:ontology|graph)"
              r"|(?:generated |delivered )?output(?: (?:graph|ontology))?)|(?:the|this) (?:ontology|graph))")
    recipient = r"(?:to (?:the )?(?:consumers?|readers?|users?|reasoners?) )?"
    location = rf"(?:in|within|from|as part of) {output}"
    # Availability describes output membership only when it names the output.
    absent = rf"absent|omitted|missing|unavailable {recipient}{location}"
    present = (rf"present|included|provided|emitted|generated|(?:in|within|part of) {output}"
               rf"|available {recipient}{location}")
    state = (r"(?:(?:is|are|was|were|remains?|will be|(?:has|have) been) )?"
             r"(?:(?:actually|already|currently|still|all) )?")
    negated_state = rf"(?:{state}not |(?:will not|won't) be |(?:has|have) not been )"
    negative_subject = r"no|none of|neither(?: of)?|not (?:one|a single)"
    # Read subject and predicate polarity together. A claim about the
    # separately supplied vocabulary can coexist with omission in the output.
    external_modifier = r"(?:separate|external|published|reference|dkgm)"
    outside_output = (rf"(?:the |a |an )?(?:(?:{external_modifier} )*(?:vocabulary|imports?)"
                      rf"|(?:{external_modifier} )+(?:ontology|graph))")
    chain_state = (
        rf"\b(?:(?P<negative_subject>{negative_subject}) )?"
        rf"(?P<chains>{chain_reference})(?: (?:in|from) {output})? "
        rf"(?:(?P<absent>{state}(?:{absent})|{negated_state}(?:{present}))"
        rf"|{state}(?:{present})|{negated_state}(?:{absent}))\b"
        rf"(?! {recipient}(?:separately|(?:in|within|from|by|via|through) {outside_output})\b)"
    )
    active_omission = (
        rf"\b(?:omits|without|(?:contains|includes) no|does not (?:include|emit|provide|contain)) "
        rf"(?:any )?{whole_core}\b(?![ -]+(?:omission|absence|loss|warning)\b)"
        rf"|\bno {whole_core}(?:$|[,:])"
    )
    include = r"include|contain|emit|provide|retain"
    inclusion = (
        rf"\b{output}(?: itself)? (?:(?:still|already|also|explicitly) )?"
        rf"(?:(?:will|does) (?:{include}|have)|(?:{include})s|has) "
        rf"(?:exactly |only )?{chain_reference}\b"
        rf"|\b{output} (?:(?:does not|doesn't|will not|won't) (?:omit|exclude) (?:any )?"
        rf"|(?:omits?|excludes?) no ){chain_reference}\b"
    )
    omission_claims = set()
    for clause in clauses:
        for claim in re.finditer(chain_state, clause):
            omitted = bool(claim["absent"]) != bool(claim["negative_subject"])
            if not omitted or re.fullmatch(whole_core, claim["chains"]):
                omission_claims.add(omitted)
        if re.search(active_omission, clause):
            omission_claims.add(True)
        if re.search(inclusion, clause):
            omission_claims.add(False)
    facts = set()
    if omission_claims == {True}:
        facts.add("dkgm_chains_absent")

    # An unqualified reference to the chains is meaningful after an omission
    # statement in the same event. Keep the directive and its objects together.
    target = rf"{chain}|dkgm axioms?|dkgm (?:ontology|vocabulary)"
    if "dkgm_chains_absent" in facts:
        target += r"|(?:omitted |missing )?(?:property[ -])?chains?(?:[ -]+axioms?)?"
    axioms = rf"(?:the |these |those )?(?:{target})\b"
    rules = r"(?:an? )?(?:equivalent|corresponding) (?:(?:inference|reasoning) )?rule(?:s| set|set)?\b"
    supply = r"(?:supply|provide|load|include|add|enable|assert|use|apply|import)"
    alternate = rf"(?:,?\s+or\s+|[, ]*\(or\s+)(?:{supply} )?"
    alternatives = rf"(?:either )?(?:{axioms}{alternate}{rules}|{rules}{alternate}{axioms})(?:\s*\))?"

    # Match affirmative verbs without skipping intervening negation. Recognize
    # both a consumer's obligation and a requirement stated in passive voice.
    audience = (r"\b(?:consumers?|you|users?|reasoners?|anyone)"
                r"(?: (?:who|requiring|needing|seeking|wanting) [^,;]+?)?\b")
    obligation = r"(?:must|needs? to|have to|has to|(?:are|is) required to|should)"
    action = rf"(?:{supply} {alternatives}|make {alternatives} available)"
    active = rf"(?:{audience} {obligation} |(?:^|[,:]\s+)){action}"
    need = rf"{audience} needs? {alternatives}"
    passive_guidance = (rf"\b{alternatives} {obligation} be "
                        r"(?:(?:made )?available|supplied|provided|loaded|included|added|asserted|used|applied|imported)\b")
    entailment = (rf"\b(?:recovering|preserving|deriving|inferring|obtaining) "
                  rf"(?:the |these |those )?(?:same |generic |dkgm )?(?:entailments|inferences) "
                  rf"(?:needs|requires) {alternatives}")
    conditional = (rf"\b(?:to |if you (?:need|want) to )"
                   rf"(?:recover|preserve|derive|infer|obtain) "
                   rf"(?:the |these |those )?(?:same |generic |dkgm )?(?:entailments|inferences), "
                   rf"(?:you )?(?:{obligation} )?{action}")
    guidance = rf"{active}|{need}|{passive_guidance}|{entailment}|{conditional}"
    negation = (r"\b(?:do|does|did) not (?:need|have to|require)\b"
                r"|\b(?:need|needs|must|should) not\b|\bnot (?:necessary|required)\b"
                r"|\b(?:don't|doesn't|didn't) (?:need|have to|require)\b|\bneedn't\b"
                r"|\bno (?:need|requirement) to\b")
    unrelated = (r"\b(?:for|to (?:derive|infer|enforce)) (?:the )?(?:material|cardinalit)\w*"
                 r"|\b(?:for (?:display|viewing|visuali[sz]ation|presentation|inspection|editing)|"
                 r"to (?:display|view|visuali[sz]e|document|inspect|edit))\b"
                 r"|\b(?:only|solely|just) (?:into|in|to) (?:an? |the )?(?:editor|viewer)\b")
    reasoning = r"\b(?:reason(?:er|ers|ing)|infer(?:ence|ences|ring|red)?|entail(?:ments?)?|deduc(?:e|tion))\b"
    for clause in clauses:
        if not re.search(guidance, clause) or re.search(rf"{negation}|{unrelated}", clause):
            continue
        # Guidance about explicit reasoning rules can identify the purpose
        # implicitly. For editor/viewer instructions require actual reasoning
        # context beyond the name of the rules.
        context = re.sub(rules, "", clause) if re.search(r"\b(?:editor|viewer)\b", clause) else clause
        if re.search(reasoning, context):
            facts.add("dkgm_chains_consumer_supply")
            break
    return facts


def reports_ontology_delivery_cause(diagnostic, failed_operation):
    """Compare observed cause wording with the operation recorded by the fault trace.

    A generic induced I/O failure is sufficient when the diagnostic does not
    specify a stage. Affirmed and excluded stages must agree with the trace,
    including when the message and effect express separate claims.
    """
    induced = r"(?:injected|forced|simulated|induced)"
    stage_forms = {
        "create": r"creat(?:e|ed|ing|ion)",
        "write": r"(?:writ(?:e|ing|ten)|wrote)",
        "serialize": r"seriali[sz](?:e[ds]?|ing|ation)",
    }
    stage = rf"(?:{'|'.join(stage_forms.values())})"
    target = r"(?:(?:ontology|output|destination) )?(?:(?:file|artifact) )?"
    failure = r"(?:failure|error|fault|exception)"
    named_failure = rf"{target}{stage} {failure}"
    io_failure = rf"(?:(?:i/o|io) {failure}|{named_failure})"
    cause = re.compile(
        rf"\b{induced}[- ](?:(?:a|an|the) )?{io_failure}\b"
        rf"|\b{io_failure} (?:was|had been) (?:(?:not|never|deliberately|intentionally) )*{induced}\b"
    )
    negation = r"(?:no|not|never|without)"
    denial_prefix = re.compile(
        rf"\b(?:{negation}(?: (?:(?:caused|triggered) by|(?:due|attributable) to|(?:result|stem) from))?|unrelated to)"
        r"(?: (?:a|an|the|any|actual|real))?(?: test[- ])? *$"
    )
    denying_predicate = (r" (?:was|had been) (?:not|never) (?:the (?:cause|reason)|responsible)\b"
                         r"| (?:did|could) (?:not|never) (?:cause|trigger)\b")
    denied_reference = re.compile(rf"\b(?:it|this|that)(?:{denying_predicate})")
    denial_suffix = re.compile(denying_predicate)
    denied_injection = re.compile(
        rf"\b(?:not|never) (?:inject|force|simulate|induce) (?:(?:a|an|the|any) )?{io_failure}\b"
    )
    stage_connector = r"(?:while|during|when|upon|on|at)"
    failure_reference = re.compile(
        rf"\b{named_failure}\b|\b(?P<generic>(?:(?:i/o|io) )?{failure})\b|\b(?:it|this|that) "
        r"(?:(?:did )?(?:not |never )?(?:happen(?:ed)?|occur(?:red)?|arise|arose|failed|took place)\b"
        rf"|(?:is|was) (?=(?:(?:not|never) )?{stage_connector}\b))"
    )
    operation_in_failure = re.compile(
        rf"\b(?:{target}(?P<nominal>{stage}) {failure}"
        rf"|(?:failed operation|failure stage) was (?:(?P<excluded>not|never) )?{target}(?P<stated>{stage}))\b"
    )
    stage_context = re.compile(
        rf"\b{stage_connector} "
        rf"(?:(?:the|it|was|being|attempting to|trying to) )*{target}({stage})\b"
    )
    stage_denial = re.compile(r"\b(?:not|never)(?: (?:happen|occur|arise|take place))? *$")

    observed_stage = re.compile(stage_forms[failed_operation.operation])

    confirmed = False
    for text in (diagnostic.raw.message, diagnostic.raw.effect):
        words = text.replace(str(failed_operation.path), "").casefold()
        words = " ".join(re.sub(r"n['’]t\b", " not", words).split())
        for statement in re.split(r"(?<=[.!?;]) ", words):
            if denied_reference.search(statement):
                return False
            references = list(failure_reference.finditer(statement))
            denials = set(denied_injection.finditer(statement))
            denials.update(reference for reference in references
                           if reference["generic"] and denial_prefix.search(statement[:reference.start()]))
            for match in cause.finditer(statement):
                if (denial_prefix.search(statement[:match.start()])
                        or re.search(rf"\b{negation}\b", match.group())
                        or denial_suffix.match(statement[match.end():])):
                    denials.add(match)
                else:
                    confirmed = True

            stage_claims = [
                (match, match["nominal"] or match["stated"], bool(match["excluded"]), match.start())
                for match in operation_in_failure.finditer(statement)
            ]
            if references:
                for match in stage_context.finditer(statement):
                    # A timing phrase inherits a denial of the failure it qualifies.
                    reference = next((ref for ref in reversed(references) if ref.end() <= match.start()),
                                     references[0])
                    stage_claims.append((match, match[1], False, reference.start()))
            scoped_denials = set()
            for match, stage_word, excluded, anchor in stage_claims:
                bound_denials = {denial for denial in denials if denial.start() <= anchor < denial.end()}
                scoped_denials.update(bound_denials)
                prefix = statement[:match.start()]
                excluded = excluded or bool(bound_denials or denial_prefix.search(prefix)
                                            or stage_denial.search(prefix) or denial_suffix.match(statement[match.end():]))
                if bool(observed_stage.fullmatch(stage_word)) == excluded:
                    return False
            if denials - scoped_denials:
                return False
    return confirmed


def _diagnostic_destination_pattern(destination):
    path = re.escape(str(destination))
    end = r"""(?=$|[\s'":,;)\]}]|\.(?=$|\s))"""
    return re.compile(rf"(?<![\w./\\]){path}" + end)


def _delivery_clauses(message, effect, destination):
    """Split diagnostic prose while preserving which statement names the destination."""
    clauses = []
    destination_pattern = _diagnostic_destination_pattern(destination)
    quoted_destination = repr(str(destination))
    quoted_marker = quoted_destination[0] + "<destination>" + quoted_destination[-1]
    for text in (message, effect):
        text = re.sub(r"^\s*\[ERROR\]\s+(?:[\w-]+:\s*)?", "", text)
        text = text.replace(quoted_destination, quoted_marker)
        text = destination_pattern.sub("<destination>", text)
        text = text.casefold().replace("’", "'")
        text = re.sub(r"\bcan't\b", "cannot", text)
        text = " ".join(re.sub(r"n't\b", " not", text).split())
        clauses.extend(re.split(r"(?<=[.!?;])\s+", text))
    return clauses


def _excluded_diagnostic_claim(clause, match):
    prefix, suffix = clause[:match.start()], clause[match.end():]
    return bool(
        re.search(r"\b(?:no|not|never|without|rule[ds]? out|unrelated to)"
                  r"(?: (?:be|left|caused by|due to|because of|attributed to|evidence of))?"
                  r"(?: (?:a|an|the|any|actual|real))? $", prefix)
        or re.match(r"(?:,? (?:but|yet))? (?:was |were |is |are |had been )?"
                    r"(?:ruled out|excluded|unrelated|did not cause|not (?:the cause|involved|responsible|present|detected|found))\b",
                    suffix)
    )


def _delivery_step_failure(step):
    """Recognize an explicit failure at the named operation."""
    issue = r"(?:error|failure|failed)"
    modifiers = r"(?:(?:the|main|ontology|file|turtle|utf-8|json) )*"
    action = r"(?:(?:write|deliver|save|create|export)(?: or (?:write|create))? )?"
    gerund = r"(?:(?:writing|delivering|saving|creating|exporting) )?"
    failed = (r"(?:(?:has |had |was )?(?:failed|failure|error|unsuccessful)"
              r"|(?:could|can) not be (?:completed|written|created|saved|delivered|exported|finished))")
    return (
        rf"\b(?:(?:cannot|could not|unable to|failed to) {action}{modifiers}{step}"
        rf"|{issue}(?:(?: (?:occurred|arose))? (?:while|during|in|at|when|to))? {gerund}{modifiers}{step}"
        rf"|{step}(?: (?:attempt|step|stage|delivery|writing|export))?"
        rf"(?: (?:of|for|to) (?:the )?(?:main )?ontology)? {failed})\b"
    )


def _delivery_claim_targets_destination(statement, bound_destination):
    """Allow additional destination evidence only if the failure names no competing path."""
    other_path = (r"(?:^|[\s'\"(])(?:/|[a-z]:[\\/]|\.\.?[\\/])\S"
                  r"|\b(?:to|for|at) ['\"]?(?:[\w.-]+[\\/])*[\w.-]+\.(?:ttl|json)\b")
    if re.search(other_path, statement):
        return False
    return "<destination>" in statement or bound_destination


def _delivery_failure_claims(clauses, failure, reason):
    """Yield each named failure with an explanation matching the observed cause.

    The bound forms are an inline causal detail and an immediately following
    reason statement. An inline explanation takes precedence over a later
    mention of an otherwise matching condition.
    """
    link = re.compile(r":|\s+(?:because(?: of)?|due to|caused by|owing to)\s+")
    boundary = r"\b(?:and|but|while|whereas)\b"
    heading = r"(?P<heading>(?:the )?(?:cause|reason)(?: is| was|:)?\s+)?"
    wrappers = (r"(?:(?:\[(?:errno|winerror) \d+\]|[\w.]*(?:error|exception):|"
                r"(?:utf-8 )?encoding (?:error|failure):)\s*)*"
                r"(?:['\"]utf-8['\"] codec cannot encode [^:]+:\s*)?")
    cause = re.compile(rf"^{heading}{wrappers}(?:(?:the|a|an|its) )?{reason}")
    if any(_excluded_diagnostic_claim(clause, mention)
           for clause in clauses for mention in re.finditer(reason, clause)):
        return

    for index, clause in enumerate(clauses):
        for claim in re.finditer(failure, clause):
            if _excluded_diagnostic_claim(clause, claim):
                continue
            tail = clause[claim.end():]
            connection = link.search(tail)
            if connection is not None:
                qualifier = tail[:connection.start()]
                # A connector belonging to another asserted failure is not this cause.
                if re.search(r"\b(?:failed|succeeded|unrelated)\b", qualifier):
                    continue
                detail = tail[connection.end():].strip()
            else:
                qualifier = tail
                detail = clauses[index + 1] if index + 1 < len(clauses) else ""
            match = cause.match(detail)
            if match is None or _excluded_diagnostic_claim(detail, match):
                continue
            # Without an inline link, read an explicit reason or a complete
            # explanation fragment. A related term in a new claim is insufficient.
            if connection is not None or match["heading"] or not detail[match.end():].strip(" .;!?"):
                prefix = re.split(boundary, clause[:claim.start()])[-1]
                suffix = re.split(boundary, qualifier, maxsplit=1)[0]
                yield prefix + claim.group() + suffix, match


def ontology_serialization_error(record, operation, destination):
    """Read affirmative stage and cause at the observed destination without fixing a code."""
    severity, _, message, effect, sources, _ = record
    if severity != "ERROR":
        return False
    structured_destination = any(source[0] == str(destination) for source in sources)
    if not sources:
        # The CLI appends the source locators to the rendered event.
        message, _, context = message.partition(" Sources: ")
        source_text = context.split(" Generated IRI: ", 1)[0]
        structured_destination = bool(_diagnostic_destination_pattern(destination).search(source_text))
    clauses = _delivery_clauses(message, effect, destination)
    serialize = r"seriali[sz](?:e[drs]?|ing|ation)"
    encode = r"encod(?:e[drs]?|ing)"
    serialization = rf"{serialize}(?: (?:and|or) (?:utf-8 )?{encode})?"
    if operation == "serialize":
        stage = serialization
        reason = (r"\b(?:(?:cyclic|circular) (?:rdf )?(?:list|collection)"
                  r"|cycle in (?:a |an |the )?(?:rdf )?(?:list|collection)"
                  r"|(?:rdf )?(?:list|collection) (?:(?:was|is) (?:cyclic|circular)|(?:contains|included) a cycle))\b")
    else:
        stage = rf"(?:{serialization}|{encode})"
        reason = r"\bsurrogate(?:s| (?:code points?|characters?))?\b"
    undelivered = (r"^(?:as a result,? |therefore,? )?"
                   r"(?:no (?:new )?ontology(?: file)? (?:was |is |could be )?"
                   r"|(?:the )?(?:new )?ontology(?: file)? (?:(?:was|is) not |could not be ))"
                   r"(?:delivered|written|created|saved) (?:to|at) <destination>")
    effect_names_destination = any(re.match(undelivered, clause) for clause in clauses)
    return any(_delivery_claim_targets_destination(statement, structured_destination or effect_names_destination)
               for statement, _ in _delivery_failure_claims(clauses, _delivery_step_failure(stage), reason))


def reports_older_ontology_retained(record, destination):
    """Read retention of the pre-existing ontology at the requested path."""
    older = r"\b(?:older|old|existing|previous|prior|pre-existing) (?:ontology(?: file)?|file|output|artifact|destination)\b"
    target = rf"(?:{older}|<destination>|\b(?:the|requested) destination(?: file)?\b)"
    state = (r"\b(?:not (?:updated|changed|modified|overwritten|replaced)"
             r"|unchanged|untouched|intact|preserved|retained|exactly as it was)\b")
    change = r"\b(?:updated|changed|modified|overwritten|replaced|deleted|truncated)\b"
    active_change = rf"\b(?:overwrote|overwrite|replaced|updated|modified|deleted|truncated) (?:the )?{target}"
    other_location = r"\b(?:backup|elsewhere|another (?:path|file|location))\b|\b(?:at|in|under|as|to) ['\"]?(?:/|[a-z]:[\\/])"
    claims = []
    for clause in _delivery_clauses(record[2], record[3], destination):
        if any(not _excluded_diagnostic_claim(clause, match) for match in re.finditer(active_change, clause)):
            return False
        for reference in re.finditer(target, clause):
            # A coordinated subject can share the ontology's retention predicate.
            following = re.sub(r"^ and (?:its|the) (?:provenance )?sidecar\b", "", clause[reference.end():])
            following = re.split(r"\b(?:sidecar|(?:generated|in-memory) (?:ontology|graph)|graph)\b",
                                 following, maxsplit=1)[0]
            if any(not _excluded_diagnostic_claim(following, match) for match in re.finditer(change, following)):
                return False
            if not re.search(other_location, following):
                claims.extend((following, match) for match in re.finditer(state, following))
    return bool(claims) and all(not _excluded_diagnostic_claim(clause, match) for clause, match in claims)


def transformation_failure_diagnostic(severity, message, effect, cause, *, stage="emit_relations"):
    """Read an affirmative failure at the observed stage and its observed cause."""
    if severity != "ERROR":
        return False
    operation = r"(?:mapping|emission|generation|transformation|creation|construction)"
    action = r"(?:mapping|emitting|generating|transforming|creating|constructing)"
    if stage == "emit_relations":
        relations = r"(?:relations?|relationships?)(?: (?:propert(?:y|ies)|axioms?))?"
        stage_pattern = re.compile(rf"\b(?:emit_relations|{relations} {operation}|{operation} of (?:the )?{relations}"
                                   rf"|{action} (?:the )?{relations})\b")
        other = r"(?:classes|provenance)"
        different_stage = re.compile(rf"\b(?:emit_classes|construct_provenance|(?:class(?:es)?|provenance) {operation}|"
                                     rf"(?:{operation} of|{action}) (?:the )?{other})\b")
    elif stage == "result_construction":
        result_noun = r"(?:conversion[- ])?result"
        stage_pattern = re.compile(
            rf"\b(?:result_construction|construct_result|build_result|conversionresult(?: construction)?|"
            rf"{result_noun} (?:construction|creation|building|assembly)|"
            rf"(?:construction|creation|building|assembly) of (?:the )?{result_noun}|"
            rf"(?:constructing|creating|building|assembling|construct|create|build|assemble) "
            rf"(?:the )?(?:{result_noun}|conversionresult))\b"
        )
        other = r"(?:classes|relations?|relationships?|metadata|provenance)"
        different_stage = re.compile(
            rf"\b(?:emit_classes|emit_relations|emit_metadata|read_metadata|construct_provenance|"
            rf"transformation[_ ]provenance|"
            rf"(?:class(?:es)?|relations?|relationships?|metadata|provenance) (?:{operation}|reading)|"
            rf"(?:{operation}|reading) of (?:the )?{other}|"
            rf"(?:{action}|reading) (?:the )?{other})\b"
        )
    else:
        raise ValueError(f"Unsupported transformation failure stage: {stage!r}")
    failure = re.compile(r"\b(?:(?:unexpected|internal|transformation) )*"
                         r"(?P<kind>failure|failed|error|exception|crashed)\b")
    cause_text = re.compile(rf"(?<![\w-]){re.escape(cause.casefold())}(?![\w-])")
    statements = []
    for field in (message, effect):
        field = re.sub(r"^\s*\[ERROR\]\s+(?:[\w-]+:\s*)?", "", field)
        words = " ".join(field.casefold().replace("’", "'").split())
        words = re.sub(r"n't\b", " not", words)
        # Sequence markers can start a new claim even without a full stop.
        statements.extend(re.split(r"(?<=[.!?;])\s+|, and |(?:, | (?:and )?)(?:then|afterwards?|subsequently|later) ",
                                   words))

    def stage_mentions(pattern, statement):
        for match in pattern.finditer(statement):
            if (not _excluded_diagnostic_claim(statement, match)
                    and not re.search(r"\b(?:after|following) (?:the )?$", statement[:match.start()])
                    and not re.match(r" (?:(?:was|had) )?(?:succeeded|completed|finished)\b",
                                     statement[match.end():])):
                yield match

    def describes_failure(location, claim, statement):
        if location.start() >= claim.end():
            between = statement[claim.end():location.start()]
            if claim.group("kind") == "failed" and between == " to " and re.match(
                r"(?:construct|create|build|assemble)\b", location.group(0)
            ):
                return True
            occurrence = r"(?:occurred|arose|happened|was(?: raised)?)"
            interruption = (r"(?:stopped|halted|interrupted|aborted|ended) (?:the )?"
                            r"(?:transformation|conversion|processing)")
            qualifier = r"(?:during|while|in|at|when) (?:(?:the )?stage:? )?(?:the )?['\"\x60]?"
            return bool(re.fullmatch(rf" (?:(?:{occurrence}|{interruption}) )?"
                                     rf"(?:{qualifier}|(?:interrupted|stopped|prevented) (?:the )?)", between))
        # In "relation transformation failed", the operation owns "transformation".
        claim_start = claim.start("kind") if claim.start() < location.end() else claim.start()
        between = statement[location.end():claim_start]
        subject_gap = (r"(?:: | )(?:(?:stage|has|had|raised|encountered) "
                       r"|(?:was )?(?:interrupted|stopped|aborted) by )?(?:an? )?")
        if re.fullmatch(subject_gap, between):
            return True
        # A leading stage qualifier may apply to a failure after its comma.
        return (bool(re.search(r"\b(?:during|while|in|at|when) (?:the )?$", statement[:location.start()]))
                and bool(re.fullmatch(r", (?:(?:the converter|directkg) (?:raised|encountered|reported) )?(?:an? )?",
                                      between)))

    for index, statement in enumerate(statements):
        claims = [
            match for match in failure.finditer(statement)
            if not re.search(r"\b(?:not true|denied) that\b", statement[:match.start()])
            and not _excluded_diagnostic_claim(statement, match)
            and not re.match(r"[^,;:]*\b(?:did not|never) (?:occur|arise|happen)\b", statement[match.end():])
        ]
        if not claims or any(describes_failure(location, claim, statement)
                             for location in stage_mentions(different_stage, statement) for claim in claims):
            continue
        # The next fields may explicitly describe the same failure's stage or reason.
        stage_reported = any(describes_failure(location, claim, statement)
                             for location in stage_mentions(stage_pattern, statement) for claim in claims)
        detail = cause_text.search(statement)
        cause_reported = bool(detail and not _excluded_diagnostic_claim(statement, detail))
        for following in statements[index + 1:]:
            if re.match(r"^(?:the )?(?:stage(?: was| is)?[: ]|during |while |when )", following):
                if any(stage_mentions(different_stage, following)):
                    stage_reported = False
                    break
                stage_reported |= any(stage_mentions(stage_pattern, following))
            elif re.match(r"^(?:the )?(?:cause|reason)(?: was| is|:)", following):
                detail = cause_text.search(following)
                if any(stage_mentions(different_stage, following)) or (
                        detail and _excluded_diagnostic_claim(following, detail)):
                    cause_reported = False
                    break
                cause_reported |= detail is not None
            elif following:
                break
        if stage_reported and cause_reported:
            return True
    return False


def console_covers_diagnostic_records(console, records):
    """Match captured events one-to-one with the records visible at the info threshold."""
    available = [(event.severity, " ".join(event.message.split()), event.code) for event in console]
    for severity, code, message, effect, sources, _ in records:
        text = (" ".join(message.split()), " ".join(effect.split()))
        for index, (display_severity, displayed, displayed_code) in enumerate(available):
            if display_severity != severity or not all(field in displayed for field in text):
                continue
            if displayed_code is not None and (not displayed_code or displayed_code != code):
                continue
            if not all(path in displayed or (identifier is not None and re.search(
                    rf"(?<!\w){re.escape(identifier)}(?!\w)", displayed)) for path, identifier, _ in sources):
                continue
            del available[index]
            break
        else:
            return False
    return True


def diagnostics_delivery_error(event, destination, *, reason=None, alias=False, artifact=None,
                               artifact_kind=None):
    """Read an affirmative report-delivery failure and its applicable cause.

    Interpret complete supported claims, not mentions of a cause. A renderer
    may use any provisional identifier (or no displayed identifier); the
    failure stage is established by the prose, not a particular code. The
    stable first-release core identifies other conditions, never report
    delivery itself. Explicit artifact descriptions must match the observed
    protected destination's role, as well as any named pathname.
    """
    code = getattr(event, "code", None)
    stable_core = {
        "PLACEHOLDER_BASE", "UNPROCESSABLE_DOCUMENT", "DUPLICATE_SOURCE_ID", "UNKNOWN_INFORMATION",
        "REQUIRED_PROVENANCE", "INTERNAL_TRANSFORMATION_FAILURE", "ONTOLOGY_DELIVERY", "SIDECAR_DELIVERY",
    }
    if event.severity != "ERROR" or code in stable_core:
        return False
    message = re.sub(r"^\s*(?:\[ERROR\]|ERROR:)\s*", "", event.message, flags=re.IGNORECASE)
    if code:
        message = re.sub(rf"^{re.escape(code)}:\s*", "", message)

    path = re.escape(str(destination))
    target = rf"(?-i:{path}|{re.escape(repr(str(destination)))}|\"{path}\")"
    report = r"(?:the )?(?:diagnostics?(?:[- ](?:report|file))?|(?:json )?report)"
    action = r"(?:write|create|save|deliver|export|serialize)"
    gerund = r"(?:writing|creating|saving|delivering|exporting|serializing)"
    failure = (
        rf"(?:cannot|could not|unable to|failed to) {action} {report} (?:to|at|for) {target}"
        rf"|(?:error|failure) (?:while )?{gerund} {report} (?:to|at|for) {target}"
        rf"|{report}(?: (?:delivery|export|writing|serialization))? (?:has )?failed (?:to|at|for) {target}"
        rf"|{report}(?: (?:delivery|export|writing|serialization))? (?:to|at|for) {target} (?:has )?failed"
        rf"|{report} (?:delivery|export|writing|serialization) (?:error|failure) (?:to|at|for) {target}"
    )
    claim = re.fullmatch(rf"(?:{failure})(?::\s*|\s+(?:because(?: of)?|due to)\s+)(?P<cause>.+)",
                         message.strip(), re.IGNORECASE | re.DOTALL)
    if claim is None:
        return False
    detail = claim["cause"].strip().removesuffix(".")
    detail = re.sub(r"^(?:(?:the )?(?:cause|reason)(?: is| was|:)\s*|[\w.]*(?:Error|Exception):\s*)",
                    "", detail, flags=re.IGNORECASE)
    if not alias:
        return bool(reason and " ".join(detail.split()).casefold() ==
                    " ".join(reason.strip().removesuffix(".").split()).casefold())

    # Accept affirmative alias descriptions, including the observed artifact
    # pathname when supplied. Do not credit negations, hedges, or unrelated
    # trailing claims merely containing an alias-related word.
    same = r"(?:the )?same (?:file|path|destination|artifact|object)"
    # Actual CLI cases supply the role explicitly: an ontology output can
    # itself have a sidecar-shaped filename. The conventional suffix retains
    # the reader's pathname-only binding for simple standalone probes.
    if artifact_kind is None and artifact is not None:
        artifact_kind = "sidecar" if str(artifact).endswith(".provenance.ttl") else "output"
    roles = {
        "output": r"(?:main )?(?:ontology(?: output)?|output)",
        "sidecar": r"(?:provenance )?sidecar",
        None: r"(?!)",  # no independently known specific role
    }
    if artifact_kind not in roles:
        return False
    peer = (rf"(?:the )?(?:protected )?(?:{roles[artifact_kind]}|artifact)"
            r"(?: (?:file|path|destination))?|(?:the )?protected (?:file|path|destination)")
    if artifact is not None:
        artifact_path = re.escape(str(artifact))
        named_path = rf"(?-i:{artifact_path}|{re.escape(repr(str(artifact)))}|\"{artifact_path}\")"
        peer = rf"(?:(?:{peer})(?: (?:at|named) {named_path})?|{named_path})"
    else:
        peer = rf"(?:{peer})"
    subject = r"(?:the )?(?:diagnostics? (?:report|file|destination|path)|report(?: (?:destination|path))?|destination|path)"
    alias_claim = (
        rf"{same}(?: as {peer})?"
        rf"|(?:{subject} )?(?:refers to|resolves to|identifies|is) {same}(?: as {peer})?"
        rf"|(?:{subject} )?aliases {peer}"
        rf"|(?:an? )?(?:filesystem |pathname |path )?alias(?:ing)?(?: (?:of|with|to) {peer})?"
    )
    return bool(re.fullmatch(alias_claim, detail, re.IGNORECASE))


def diagnostics_report_write_error(event, destination, observed_error):
    """Bind a distinct console report-delivery error to the actual failed filesystem call."""
    if (event.severity != "ERROR" or observed_error["destination"] != str(destination)
            or observed_error["errno"] != errno.ENOTDIR or not observed_error["reason"]):
        return False
    clauses = _delivery_clauses(event.message, "", destination)
    step = r"(?:diagnostics?(?:[- ](?:report|file))?|(?:json )?report)"
    reason = (r"\b(?:not (?:a )?(?:directory|folder)|non[- ]directory(?: (?:parent|component))?"
              r"|(?:parent(?: path)?|path component) (?:is|was|points to) (?:a )?(?:regular )?file"
              r"|(?:path component|component of (?:the )?path) (?:is|was) not (?:a )?(?:directory|folder))\b"
              r"""(?:\s*:\s*(?P<filename>'(?:\\.|[^'\\])*'|"(?:\\.|[^"\\])*"|<destination>))?""")
    write_to_path = r"\b(?:cannot|could not|unable to|failed to) (?:write|create|save|deliver|export)(?: to)? <destination>"
    failure = rf"(?:{_delivery_step_failure(step)}|{write_to_path})"
    for statement, cause in _delivery_failure_claims(clauses, failure, reason):
        filename = cause["filename"]
        if filename is not None and filename.strip("'\"") != "<destination>":
            continue
        if _delivery_claim_targets_destination(statement, filename is not None):
            return True
    return False


def _generalization_membership_facts(message):
    """Interpret a complete affirmative claim about the membership field."""
    # Keep the quoted field name, but treat quoted IDs and payloads as opaque.
    quoted = r"""(?:`[^`]*`|'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*")"""
    wording = re.sub(quoted, lambda match: (
        "generalizations" if match[0][1:-1].casefold() == "generalizations" else "<quoted>"
    ), message.casefold())
    wording = " ".join(wording.split()).removesuffix(".")
    field = r"(?:the )?(?:field )?(?:generalizations(?: field| container| value)?|membership (?:field|container|array|list))"
    locator = r"(?:<quoted>|[a-z0-9_.-]+)"
    declaration = rf"(?:the )?(?:generalization[- ]?set(?: {locator})?|element {locator})"
    prefix = rf"(?:{declaration}(?:[:,] ?| ))?"
    predicate = rf"{prefix}{field}(?: (?:is|was|has value|is set to) | *[:=] *)"
    actual = (
        rf"{prefix}{field}(?: *: *| )(?:(?:(?:is|was) )?expected (?:to be )?|(?:must|should) be )"
        r"(?:an? )?(?:json )?(?:array|list) *[,;:] *(?:but )?(?:got|found|received) "
    )
    field_description = rf"(?:{declaration} (?:has|contains|is|was) )?(?:an? |the )?"
    non_array = r"(?:non[- ](?:array|list)(?: value)?|object|dict(?:ionary)?|string|str|number|integer|int|float|boolean|bool)"
    claims = {
        "membership_absent": (
            rf"{predicate}(?:absent|missing|omitted|not (?:present|provided|supplied))"
            rf"|{field_description}(?:missing|absent|no) {field}"
        ),
        "membership_null": (
            rf"{predicate}(?:explicitly )?null(?:,? not (?:absent|missing))?"
            rf"|{field_description}(?:explicitly )?null {field}|{actual}null"
        ),
        "membership_non_array": (
            rf"{predicate}(?:an? )?(?:{non_array}|not (?:an? )?(?:json )?(?:array|list))"
            rf"|{field_description}non[- ](?:array|list) {field}"
            rf"|{actual}(?:an? )?{non_array}"
            rf"|{predicate}not null *[,;:] *(?:but )?it (?:is|was) (?:an? )?{non_array}"
        ),
    }
    # Full-claim matching rejects hedges, wider negation, and alternative
    # conditions even when one fragment resembles a supported assertion.
    return {fact for fact, pattern in claims.items() if re.fullmatch(pattern, wording)}


def _unusable_categorizer_facts(message):
    """Read an affirmative unusable-categorizer condition from the native reason.

    Rejects internal-guard wording, bare expectations, negated or hedged claims,
    valid/absent/null categorizer statements, and unrelated subjects.
    """
    wording = message.casefold().replace("`", "").replace("’", "'")
    if re.search(
        r"\b(?:unexpected internal|not implemented|unimplemented|outside the decided baseline"
        r"|remains (?:unspecified|deferred|outside))\b",
        wording,
    ):
        return set()
    wording = re.sub(r"\bcan't\b", "cannot", wording)
    wording = re.sub(r"n't\b", " not", wording)
    # Mask literal container payloads so embedded punctuation or ID text cannot spoof prose.
    while re.search(r"\[[^\[\]]*\]", wording):
        wording = re.sub(r"\[[^\[\]]*\]", "<value>", wording)
    while re.search(r"\{[^{}]*\}", wording):
        wording = re.sub(r"\{[^{}]*\}", "<value>", wording)
    wording = re.sub(r"""(?<!\w)(['"])(categorizer|class|owl[:\s]+class|null)\1""", r"\2", wording)
    wording = re.sub(r"""(?<!\w)(?:'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*")(?=$|[\s.,;:)!?])""", "<quoted>", wording)
    wording = " ".join(wording.split())
    cat_noun = (
        r"\bcategorizer(?:\s+(?:reference|value|field|target|declaration|class))?\b"
        r"(?!\s+(?:recovery|handling|policy|rule|mapping|assertions?|expansion|extension)\b)"
    )
    val = r"(?:\s+(?:<value>|<quoted>|-?\d+(?:\.\d+)?|true|false))?"
    gs_scope = r"(?:\s+(?:of|for|on|in)\s+(?:the\s+)?(?:class\s+)?generalization[- ]?set(?:\s+(?:<quoted>|<value>))?)?"
    cat_subj = rf"{cat_noun}{val}{gs_scope}(?:\s+(?:that|which))?"
    owl_class = r"(?:generated\s+)?(?:local\s+)?(?:owl[:\s]+)?class(?:\s+(?:declaration|resource|element))?"
    ref_noun = r"(?:(?:valid\s+)?(?:class\s+)?reference(?:\s+object)?|(?:json\s+)?object)"
    unusable_adj = r"(?:unusable|invalid|malformed|unresolved|unresolvable|dangling|broken|non[- ]class)"
    absent_adj = r"(?:absent|missing|null|omitted)"
    valid_adj = r"(?:usable|valid|resolved|resolvable|preserved|present)"
    non_class_decl = r"(?:generalization|generalizationset|relation|property|package|literal)"
    non_class_type = rf"(?:string|str|number|integer|int|float|boolean|bool|array|list|{non_class_decl}|datatype|primitive)"
    disqualifiers = (
        rf"(?<!\bnot\s)(?<!\bno\s)\b(?:usable|valid|resolved|preserved)\s+{cat_noun}",
        rf"{cat_subj}\s+(?:is|was)\s+(?:usable|valid|resolved|preserved)\b",
        rf"{cat_subj}\s+(?:is|was)\s+(?:explicitly\s+)?(?<!non-)(?<!non )(?:null|absent|missing|omitted|not\s+(?:present|provided|supplied))\b",
        rf"(?<!non-)(?<!non )\b(?:no|without(?:\s+(?:a|an))?|absent|missing|null)\s+{cat_noun}",
        rf"\b{valid_adj}\s+or\s+(?:{unusable_adj}|{absent_adj})\b",
        rf"\b(?:{unusable_adj}|{absent_adj})\s+or\s+{valid_adj}\b",
        rf"(?:{cat_subj}\s+(?:is|was)\s+(?:(?:an?\s+)?{unusable_adj}\s+or\s+{absent_adj}|{absent_adj}\s+or\s+{unusable_adj})"
        rf"|\b(?:{unusable_adj}\s+or\s+{absent_adj}|{absent_adj}\s+or\s+{unusable_adj})\s+{cat_noun})",
        r"\b(?:may|might|could)\s+or\s+(?:may|might|could)\s+not\b|\busable\s+or\s+not\b",
        rf"{cat_subj}\s+(?:may|might|could)\s+(?:be|not\s+be|fail)\b",
        rf"\b(?:not|no|never|without|does\s+not\s+have|did\s+not\s+have|has\s+no)\s+"
        rf"(?:(?:a|an|the)\s+)?{unusable_adj}\s+{cat_noun}",
        rf"{cat_subj}\s+(?:is|was)\s+(?:not|neither)\s+(?:unusable|invalid|malformed|unresolved|unresolvable|dangling|broken|a\s+non[- ]class)\b",
    )
    guard_prefix = re.compile(
        r"\b(?:not|no|never|without|neither|cannot|may|might|could|must|should|if|whether|unless|when|whenever)\b[^.!?;]*$"
    )
    active_guard = re.compile(
        r"\b(?:did\s+not|does\s+not|not|never|if|whether|unless|when|whenever|may|might)\b[^.!?;]*$"
    )
    attributive = re.compile(
        rf"(?:^|[:,]\s*|\b(?:has|had|contains?|with|uses?|specifies?|declares?|found|encountered)\s+)"
        rf"(?:(?:a|an|the)\s+)?"
        rf"{unusable_adj}(?:\s+or\s+(?:{unusable_adj}|non[- ]local))?\s+{cat_noun}"
    )
    predicative = re.compile(
        rf"{cat_subj}\s*(?:"
        rf"\s+(?:is|was)\s+(?:(?:an?\s+)?(?:unusable|invalid|malformed|unresolved|unresolvable|dangling|broken"
        rf"|non[- ]class|non[- ]object|(?:supported\s+)?primitive\s+datatype|(?:visual\s+paradigm\s+)?void\b"
        rf"|(?:string|str|number|integer|int|float|boolean|bool|array|list|{non_class_decl})\b)"
        rf"|not\s+(?:usable|valid|resolved|resolvable|(?:a|an)\s+(?:usable\s+)?(?:{ref_noun}|{owl_class}))"
        rf"|(?:a|an)\s+{non_class_type}\b[^.!?;]*\b(?:not|instead\s+of|rather\s+than)\s+(?:a|an)\s+(?:{ref_noun}|{owl_class}))"
        rf"|\s+(?:is|was)\s+not\s+null\s*[,;:]\s*(?:but\s+)?it\s+(?:is|was)\s+(?:an?\s+)?{non_class_type}\b"
        rf"|\s+(?:cannot|could\s+not|does\s+not|did\s+not|fails?\s+to|failed\s+to)\s+"
        rf"(?:be\s+(?:resolved|used)|resolve(?:\s+to\s+(?:a|an)\s+{owl_class})?"
        rf"|(?:supply|provide|produce|yield|generate|map\s+to|identify)\s+(?:a|an)\s+(?:{ref_noun}|{owl_class})"
        rf"|(?:refer|point)\s+to\s+(?:a|an)\s+(?:{ref_noun}|{owl_class})|reference\s+(?:a|an)\s+(?:{ref_noun}|{owl_class}))"
        rf"|\s+(?:has|had)\s+(?:(?:a|an)\s+)?(?:(?:{unusable_adj}(?:\s+or\s+(?:{unusable_adj}|missing))?\s+"
        rf"(?:reference|id|identifier|value|target))|(?:missing(?:\s+or\s+{unusable_adj})?\s+(?:id|identifier))"
        rf"|(?:reference[- ])?type\s+mismatch)\b"
        rf"|\s+(?:reference\s+)?type\s+(?:does|did)\s+not\s+match(?:\s+(?:its|the)\s+(?:declaration|declared\s+type|class))?\b"
        rf"|:\s*reference\s+type\s+does\s+not\s+match\b"
        rf"|\s+(?:resolves?|resolved|points?|pointed|refers?|referred)\s+to\s+"
        rf"(?:(?:a|an)\s+(?:non[- ]class|(?:supported\s+)?primitive\s+datatype|(?:class|datatype)\s+(?:without|lacking)\s+(?:a\s+)?{owl_class}"
        rf"|{non_class_decl})\b|(?:visual\s+paradigm\s+)?void\b"
        rf"|<quoted>(?:,\s*|\s+)not\s+(?:a|an)\s+(?:{ref_noun}|{owl_class}))"
        rf"|\s+(?:has\s+no|lacks|is\s+without|without)\s+(?:a\s+)?{owl_class}"
        rf"|\s+(?:(?:(?:is|was)\s+)?expected\s+(?:to\s+(?:be|resolve\s+to)\s+)?|(?:must|should)\s+(?:be|resolve\s+to|supply)\s+)"
        rf"(?:a|an)\s+(?:{owl_class}|{ref_noun})\s*[,;:]\s*(?:but\s+)?(?:got|found|received|resolved\s+to|is|was)\s+"
        rf"(?!null\b|absent\b|missing\b|omitted\b)\S+"
        rf")"
    )
    active_failure = re.compile(
        rf"\b(?:cannot|could\s+not|unable\s+to|failed\s+to|fails\s+to)\s+(?:resolve|use)\s+(?:the\s+)?{cat_noun}"
    )
    matched = False
    for clause in re.split(r"[.!?;]+", wording):
        clause = clause.strip()
        if not clause:
            continue
        if any(re.search(pattern, clause) for pattern in disqualifiers):
            return set()
        for pattern in (attributive, predicative, active_failure):
            for match in pattern.finditer(clause):
                local_prefix = re.split(r"[:,]|\b(?:and|but|so|yet)\b", clause[:match.start()])[-1]
                guard = active_guard if pattern is active_failure else guard_prefix
                if guard.search(local_prefix):
                    continue
                matched = True
    return {"unusable_categorizer"} if matched else set()


def unusable_categorizer_diagnostic(message: str) -> bool:
    """Return whether a native ERROR reason asserts an unusable-categorizer condition."""
    return bool(_unusable_categorizer_facts(message))


def _inapplicable_relation_categorizer_facts(message):
    """Read an affirmative inapplicable non-null categorizer condition on a relation set.

    Rejects internal-guard wording, bare expectations, negated or hedged claims,
    absent/null/valid categorizer statements, and unrelated subjects.
    """
    wording = message.casefold().replace("`", "").replace("’", "'")
    if re.search(
        r"\b(?:unexpected internal|not implemented|unimplemented|outside the decided baseline"
        r"|remains (?:unspecified|deferred|outside))\b",
        wording,
    ):
        return set()
    wording = re.sub(r"\bcan't\b", "cannot", wording)
    wording = re.sub(r"n't\b", " not", wording)
    while re.search(r"\[[^\[\]]*\]", wording):
        wording = re.sub(r"\[[^\[\]]*\]", "<value>", wording)
    while re.search(r"\{[^{}]*\}", wording):
        wording = re.sub(r"\{[^{}]*\}", "<value>", wording)
    wording = re.sub(r"""(?<!\w)(['"])(categorizer|class|relation|null)\1""", r"\2", wording)
    wording = re.sub(r"""(?<!\w)(?:'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*")(?=$|[\s.,;:)!?])""", "<quoted>", wording)
    wording = " ".join(wording.split())
    cat_noun = (
        r"\bcategorizer(?:\s+(?:reference|value|field|target|declaration|class))?\b"
        r"(?!\s+(?:recovery|handling|policy|rule|mapping|assertions?|expansion|extension|treatment)\b)"
    )
    val = r"(?:\s+(?:<value>|<quoted>|-?\d+(?:\.\d+)?|true|false))?"
    rel_gs = r"(?:relation(?:\s+generalization)?[- ]?set(?:\s+(?:<quoted>|<value>))?)"
    any_gs = r"(?:(?:relation\s+)?generalization[- ]?set(?:\s+(?:<quoted>|<value>))?)"
    gs_scope = rf"(?:\s+(?:of|for|on|in)\s+(?:the\s+)?{any_gs})?"
    cat_subj = rf"{cat_noun}{val}{gs_scope}(?:\s+(?:that|which))?"
    inapplicable_adj = r"(?:inapplicable|disallowed|forbidden|prohibited|unsupported|unusable|invalid)"
    absent_adj = r"(?:absent|missing|null|omitted)"
    valid_adj = r"(?:usable|valid|applicable|allowed|permitted|supported)"
    global_disqualifiers = (
        rf"{cat_subj}\s+(?:is|was)\s+(?:explicitly\s+)?(?<!non-)(?<!non )(?:null|absent|missing|omitted|not\s+(?:present|provided|supplied))\b",
        rf"{cat_subj}\s+(?:is|was)\s+(?:not|neither)\s+(?:inapplicable|disallowed|forbidden|prohibited|unsupported|unusable|invalid|non[- ]null)\b",
        rf"\bnot\s+(?:a|an)\s+(?:{inapplicable_adj}(?:\s+non[- ]null)?|non[- ]null(?:\s+{inapplicable_adj})?)\s+{cat_noun}",
        rf"\b(?:was|were|is|are)\s+not\s+checked\b",
    )
    clause_disqualifiers = (
        rf"(?<!\bnot\s)(?<!\bno\s)(?<!\bin)\b(?:usable|valid|applicable|allowed|permitted|supported)\s+{cat_noun}",
        rf"{cat_subj}\s+(?:is|was)\s+(?:usable|valid|applicable|allowed|permitted|supported)\b",
        rf"(?<!non-)(?<!non )\b(?:no|without(?:\s+(?:a|an))?|absent|missing|null)\s+{cat_noun}",
        rf"\b{valid_adj}\s+or\s+(?:{inapplicable_adj}|{absent_adj})\b",
        rf"\b(?:{inapplicable_adj}|{absent_adj})\s+or\s+{valid_adj}\b",
        rf"(?:{cat_subj}\s+(?:is|was)\s+(?:(?:an?\s+)?{inapplicable_adj}\s+or\s+{absent_adj}|{absent_adj}\s+or\s+{inapplicable_adj})"
        rf"|\b(?:{inapplicable_adj}\s+or\s+{absent_adj}|{absent_adj}\s+or\s+{inapplicable_adj})\s+{cat_noun})",
        r"\b(?:may|might|could)\s+or\s+(?:may|might|could)\s+not\b|\b(?:applicable|inapplicable)\s+or\s+not\b",
        rf"{cat_subj}\s+(?:may|might|could)\s+(?:be|not\s+be|fail)\b",
        rf"\b(?:not|no|never|without|does\s+not\s+have|did\s+not\s+have|has\s+no)\s+"
        rf"(?:(?:a|an|the)\s+)?(?:{inapplicable_adj}(?:\s+non[- ]null)?|non[- ]null)\s+{cat_noun}",
    )
    guard_prefix = re.compile(
        r"\b(?:not|no|never|without|neither|cannot|may|might|could|must|should|if|whether|unless|when|whenever)\b[^.!?;]*$"
    )
    patterns = (
        re.compile(
            rf"\b{any_gs}\s+(?:has|had|contains?|with|uses?|specifies?|declares?|found|encountered)\s+"
            rf"(?:(?:a|an|the)\s+)?(?:present,?\s+)?(?:{inapplicable_adj}(?:\s+non[- ]null)?|non[- ]null\s+{inapplicable_adj})\s+{cat_noun}"
        ),
        re.compile(
            rf"(?:^|[:,]\s*)\s*(?:(?:a|an|the)\s+)?(?:present,?\s+)?(?:{inapplicable_adj}(?:\s+non[- ]null)?|non[- ]null\s+{inapplicable_adj})\s+{cat_noun}"
            rf"(?:\s+(?:<value>|<quoted>))?\s+(?:on|for|in)\s+(?:the\s+)?{any_gs}"
        ),
        re.compile(
            rf"\b{rel_gs}\s+(?:has|had|contains?|with|uses?|specifies?|declares?|found|encountered)\s+"
            rf"(?:(?:a|an|the)\s+)?(?:present,?\s+)?non[- ]null\s+{cat_noun}"
        ),
        re.compile(
            rf"(?:^|[:,]\s*)\s*(?:(?:a|an|the)\s+)?(?:present,?\s+)?non[- ]null\s+{cat_noun}"
            rf"(?:\s+(?:<value>|<quoted>))?\s+(?:on|for|in)\s+(?:the\s+)?{rel_gs}"
        ),
        re.compile(
            rf"{cat_noun}{val}\s+(?:of|for|on|in)\s+(?:the\s+)?{any_gs}(?:\s+(?:that|which))?\s+"
            rf"(?:is|was)\s+(?:(?:an?\s+)?{inapplicable_adj}|not\s+(?:applicable|allowed|permitted|supported))"
        ),
        re.compile(
            rf"\b{rel_gs}(?:\s+(?:that|which))?(?:\s+is\s+(?:a\s+)?{rel_gs})?\s+(?:and\s+)?(?:cannot|must\s+not|may\s+not|does\s+not|do\s+not)\s+"
            rf"(?:have|use|specify|declare|support|allow|accept)\s+(?:(?:a|an)\s+)?(?:non[- ]null\s+)?{cat_noun}"
        ),
    )
    if any(re.search(pattern, wording) for pattern in global_disqualifiers):
        return set()
    matched = False
    for clause in re.split(r"[.!?;]+", wording):
        clause = clause.strip()
        if not clause:
            continue
        if any(re.search(pattern, clause) for pattern in clause_disqualifiers):
            continue
        for pattern in patterns:
            for match in pattern.finditer(clause):
                local_prefix = re.split(r"[:,]|\b(?:and|but|so|yet)\b", clause[:match.start()])[-1]
                if guard_prefix.search(local_prefix):
                    continue
                matched = True
    return {"inapplicable_relation_categorizer"} if matched else set()


def inapplicable_relation_categorizer_diagnostic(message: str) -> bool:
    """Return whether a native ERROR reason asserts an inapplicable non-null categorizer on a relation set."""
    return bool(_inapplicable_relation_categorizer_facts(message))


def _unresolved_attribute_type_facts(message: str) -> set[str]:
    """Read affirmative unresolved/unavailable attribute value-type ERROR wording."""
    wording = message.casefold().replace("`", "").replace("’", "'")
    if re.search(
        r"\b(?:unexpected internal|not implemented|unimplemented|outside the decided baseline"
        r"|remains (?:unspecified|deferred|outside))\b",
        wording,
    ):
        return set()
    wording = re.sub(r"\bcan't\b", "cannot", wording)
    wording = re.sub(r"n't\b", " not", wording)
    while re.search(r"\{[^{}]*\}", wording):
        wording = re.sub(r"\{[^{}]*\}", "<value>", wording)
    wording = re.sub(r"""(?<!\w)(?:'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*")(?=$|[\s.,;:)!?])""", "<quoted>", wording)
    wording = " ".join(wording.split())
    disqualifiers = (
        r"\b(?:is|was|can be|could be|has been)\s+resolved\b",
        r"\bnot\s+(?:unresolved|missing|unavailable|invalid)\b",
        r"\b(?:if|whether|unless|when|whenever)\b[^.!?;]*\battribute\b",
        r"\b(?:may|might|could)\s+(?:be|fail)\b",
    )
    if any(re.search(pattern, wording) for pattern in disqualifiers):
        return set()
    attr_type = r"\battribute(?:\s+(?:<value>|<quoted>))?(?:\s+(?:value[- ]type|propertytype|target(?:\s+class)?))?(?:\s+reference)?(?:\s+(?:<value>|<quoted>))?"
    patterns = (
        re.compile(rf"{attr_type}\s+(?:cannot\s+be\s+resolved|could\s+not\s+be\s+resolved|is\s+unresolved|was\s+unresolved)\b"),
        re.compile(rf"{attr_type}\s+(?:resolves\s+to\s+no|has\s+no|lacks(?:\s+a)?)\s+(?:generated\s+)?(?:local\s+)?(?:owl:)?class\b"),
        re.compile(rf"\bunresolved\s+attribute\s+(?:value[- ]type|propertytype|target(?:\s+class)?)(?:\s+reference)?\b"),
    )
    for clause in re.split(r"[.!?;]+", wording):
        clause = clause.strip()
        if not clause:
            continue
        if any(pattern.search(clause) for pattern in patterns):
            return {"unresolved_attribute_type"}
    return set()


def unresolved_attribute_type_diagnostic(message: str) -> bool:
    """Return whether a native ERROR reason asserts an unresolved/unavailable attribute target type."""
    return bool(_unresolved_attribute_type_facts(message))


_DIAGNOSTIC_ID_TOKEN = r"""(?:'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*"|`[^`]+`|[\w-]+)"""


def _diagnostic_identifier(token: str) -> str:
    """Read a source ID without case folding or discarding quoted content."""
    if token.startswith(("'", '"')):
        try:
            return literal_eval(token)
        except (SyntaxError, ValueError):
            return token[1:-1]
    return token.removeprefix("`").removesuffix("`")


def _absent_attribute_property_type_claim(message: str):
    """Return an affirmative claim match, retaining its optional explicit subject."""
    wording = message.strip().removesuffix(".")
    attribute = rf"(?:class )?attribute(?: (?P<subject>{_DIAGNOSTIC_ID_TOKEN}))?"
    field = r"(?:the )?(?:propertytype|'propertytype'|\"propertytype\"|`propertytype`)(?: field| carrier)?"
    absent = r"(?:absent|missing|not (?:present|provided|supplied))"
    for pattern in (
        rf"{attribute} (?:has no {field}|lacks (?:a )?(?:required )?{field}|has (?:an? )?(?:absent|missing) {field}|(?:is missing|is lacking) (?:a |the )?(?:required )?{field}|{field} (?:is|was) {absent})",
        rf"(?:absent|missing) {field} (?:on|for|in) {attribute}",
        rf"{field} (?:is|was) {absent} (?:on|for|in) {attribute}",
    ):
        match = re.fullmatch(pattern, wording, re.IGNORECASE)
        if match:
            return match
    return None


def absent_attribute_property_type_diagnostic(message: str) -> bool:
    """Read an affirmative claim of an absent attribute propertyType field."""
    return _absent_attribute_property_type_claim(message) is not None


def absent_attribute_property_type_error(event, identifier):
    """Check the actual source locator, severity and provisional error meaning."""
    stable_codes = {
        "PLACEHOLDER_BASE", "UNPROCESSABLE_DOCUMENT", "DUPLICATE_SOURCE_ID", "UNKNOWN_INFORMATION",
        "REQUIRED_PROVENANCE", "INTERNAL_TRANSFORMATION_FAILURE", "ONTOLOGY_DELIVERY", "SIDECAR_DELIVERY",
    }
    # Observed display text combines native reason and effect; only the
    # native reason establishes the condition and its explicit subject.
    claim = _absent_attribute_property_type_claim(getattr(event.raw, "message", event.message))
    subject = claim.group("subject") if claim else None
    return (claim is not None and (subject is None or _diagnostic_identifier(subject) == identifier)
            and event.severity == "ERROR" and bool(event.code) and event.code not in stable_codes
            and identifier in event.identified_sources
            and "absent_attribute_property_type" in event.facts)


def unresolved_property_reference_between(event, referencing, field, referenced):
    """Read direction from the reported reference, not the order or count of locators.

    Native unresolved-reference reasons identify the field and reference value.
    The source locator identifies the referencing property; an explicit subject
    in the reason must agree with it. A target locator may also be present.
    """
    if (event.severity != "ERROR" or event.kind != "unresolved_property_reference"
            or referencing not in event.identified_sources):
        return False
    # IDs are opaque, not word tokens: punctuation can belong to the ID.
    # Consume the entire value up to the whitespace separating it from the
    # predicate. Native KeyError detail, when present, is a quoted string.
    quoted = r"""(?:'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*")"""
    token = rf"(?:{quoted}|`[^`]+`|[^\s'\"`]+)"
    unresolved = (r"(?:is|was) unresolved|(?:cannot|could not) be resolved|"
                  r"(?:cannot|could not) supply a property expression|"
                  r"does not resolve to a property expression")
    reason = getattr(event.raw, "message", event.message).strip().removesuffix(".")
    match = re.fullmatch(
        rf"(?:property|attribute)(?: (?P<subject>{token}))? "
        rf"{re.escape(field)} reference(?: (?:to|targeting))? "
        rf"(?P<target>\{{.*\}}|{token}) (?:{unresolved})(?:: {quoted})?",
        reason, re.IGNORECASE,
    )
    if not match:
        return False
    subject = match.group("subject")
    if subject is not None and _diagnostic_identifier(subject) != referencing:
        return False
    target = match.group("target")
    if target.startswith("{"):
        try:
            reference = literal_eval(target)
        except (SyntaxError, ValueError):
            return False
        return isinstance(reference, dict) and reference.get("id") == referenced
    return _diagnostic_identifier(target) == referenced


def _mixed_hierarchy_claim(message):
    """Read an affirmative mixed-declaration error, retaining its named subject."""
    token = r"""(?:'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*"|`[^`]+`|[^\s'\"`]+)"""
    subject = rf"(?P<construct>generalization(?:[ -]?set)?)(?: (?P<identifier>{token}))??"
    kinds = r"(?:(?:a )?class(?:es)? (?:and|to|with) (?:a )?relations?|(?:a )?relations? (?:and|to|with) (?:a )?class(?:es)?|class\s*/\s*relation|relation\s*/\s*class)"
    members = r"(?: endpoint(?:s| kinds)?| member(?:s| endpoints|ship)?| classifier(?:s| kinds| types)?| declaration(?:s| kinds| types)?| generalizations?)?"
    reason = message.strip().removesuffix(".")
    for pattern in (
        rf"{subject} (?:connects|mixes|combines|contains|has|groups) (?:both |mixed )?(?:resolved )?{kinds}{members}",
        rf"{subject} (?:has|contains|establishes) (?:a )?mixture of {kinds}{members}",
        rf"mixed {kinds} {subject}(?: membership| endpoints)?",
        rf"mixed {kinds} (?:membership|endpoints) (?:in|on|of) {subject}",
    ):
        match = re.fullmatch(pattern, reason, re.IGNORECASE)
        if match:
            return match
    return None


def _independent_hierarchy_claim(message):
    """Read an asserted arity error or unresolved general endpoint, not merely failed output."""
    token = r"""(?:'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*"|`[^`]+`|[^\s'\"`]+)"""
    relation = rf"(?:non[- ]?instantiation )?relation(?: (?P<identifier>{token}))??"
    generalization = rf"(?:relation )?generalization(?: (?P<identifier>{token}))??"
    reason = message.strip().removesuffix(".")
    patterns = (
        ("nonbinary_relation", rf"{relation} (?:has|contains) (?:a |an )?(?:non[- ]?binary properties(?: array| list| container)?(?: \(length 0, expected 2\))?|empty properties (?:array|list)|(?:0|zero) (?:association )?ends)"),
        ("nonbinary_relation", rf"{relation} (?:properties(?: array| list)? (?:is|was|are|were) (?:non[- ]?binary|empty))"),
        ("unresolved_general_reference", rf"{generalization} lacks both generated primary properties: general: ['\"]Unresolved source reference['\"]"),
        ("unresolved_general_reference", rf"{generalization} has (?:an? )?unresolved (?:general (?:endpoint )?|classifier |endpoint )?reference(?: (?:to )?(?P<target>{token}))?"),
        ("unresolved_general_reference", rf"{generalization} has (?:an? )?invalid or unresolved (?:general (?:endpoint )?|classifier |endpoint )?reference: ['\"]Unresolved source reference['\"]"),
        ("unresolved_general_reference", rf"{generalization} (?:general (?:endpoint )?reference|reference to (?:its )?general endpoint)(?: (?:to )?(?P<target>{token}))? (?:is unresolved|cannot be resolved|could not be resolved)"),
        ("unavailable_relation_expression", rf"{generalization} lacks both generated primary properties"),
    )
    for condition, pattern in patterns:
        match = re.fullmatch(pattern, reason, re.IGNORECASE)
        if match:
            return condition, match
    return None


def _hierarchy_condition_claims(message):
    """Read separate affirmative claims, including explicitly consolidated diagnostics.

    Try the complete reason first. A consolidated reason can contain separate
    sentence/semicolon-delimited claims; never split punctuation inside a
    quoted identifier or exception detail. Every clause must be recognized, so
    a conditional, negated or contradictory fragment cannot supply evidence.
    """
    def read(clause):
        mixed = _mixed_hierarchy_claim(clause)
        if mixed:
            return ("mixed_set" if mixed.group("construct").casefold().endswith("set") else "mixed_edge", mixed)
        return _independent_hierarchy_claim(clause)

    single = read(message)
    if single:
        return (single,)
    clauses = []
    start = 0
    for match in re.finditer(r"""'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*"|`[^`]+`|[.;](?=\s)""", message):
        if match.group() in {".", ";"}:
            clauses.append(message[start:match.start()].strip())
            start = match.end()
    clauses.append(message[start:].strip())
    claims = tuple(read(clause) for clause in clauses)
    return claims if all(claims) else ()


def hierarchy_condition_error(event, condition, identifier, *, reference=None):
    """Require affirmative condition and actual locator; permit a shared event for distinct claims."""
    if (event.severity != "ERROR" or identifier not in event.identified_sources
            or not event.code or event.code in {
                "PLACEHOLDER_BASE", "UNPROCESSABLE_DOCUMENT", "DUPLICATE_SOURCE_ID", "UNKNOWN_INFORMATION",
                "REQUIRED_PROVENANCE", "INTERNAL_TRANSFORMATION_FAILURE", "ONTOLOGY_DELIVERY", "SIDECAR_DELIVERY",
            }):
        return False
    for actual, claim in _hierarchy_condition_claims(getattr(event.raw, "message", event.message)):
        if actual != condition:
            continue
        subject = claim.group("identifier")
        target = claim.groupdict().get("target")
        if subject is None:
            # A subjectless clause may use the native source context, but
            # multiple candidate subjects of the same type are ambiguous.
            subject_type = {"mixed_set": "GeneralizationSet", "mixed_edge": "Generalization",
                            "nonbinary_relation": "Relation", "unresolved_general_reference": "Generalization",
                            "unavailable_relation_expression": "Generalization"}[actual]
            candidates = {source.identifier for source in getattr(event.raw, "sources", ())
                          if source.element_type in {None, subject_type}}
            if candidates != {identifier}:
                continue
        elif _diagnostic_identifier(subject) != identifier:
            continue
        if target is None or _diagnostic_identifier(target) == reference:
            return True
    return False


def mixed_hierarchy_error(event, identifier, *, is_set=False):
    """Require observed structural meaning and source identity, not a provisional code."""
    return hierarchy_condition_error(event, "mixed_set" if is_set else "mixed_edge", identifier)


def _nonclassifier_hierarchy_claim(message):
    """Read a structural endpoint-kind error independently of its provisional code."""
    subject = rf"generalization(?: (?P<identifier>{_DIAGNOSTIC_ID_TOKEN}))?"
    reason = message.strip().removesuffix(".")
    for pattern in (
        rf"{subject} (?:has|contains) (?:an? )?(?:non-classifier|nonclassifier) endpoint(?: type| kind)?",
        rf"{subject} (?:has|contains) (?:an? )?(?:invalid|unsupported) endpoint (?:type|kind)(?: (?:Property|'Property'|\"Property\"))?",
        rf"{subject} (?:has|contains) (?:an? )?endpoint (?:that is|which is|of type Property, which is) not (?:a )?Class or (?:a )?Relation",
        rf"{subject} connects (?:a )?(?:Class|Relation) (?:to|and|with) (?:a )?Property",
        rf"{subject} connects (?:a )?Property (?:to|and|with) (?:a )?(?:Class|Relation)",
    ):
        match = re.fullmatch(pattern, reason, re.IGNORECASE)
        if match:
            return match
    return None


def nonclassifier_hierarchy_error(event, identifier):
    claim = _nonclassifier_hierarchy_claim(getattr(event.raw, "message", event.message))
    if not claim or event.severity != "ERROR" or identifier not in event.identified_sources:
        return False
    subject = claim.group("identifier")
    return ((subject is None or _diagnostic_identifier(subject) == identifier)
            and bool(event.code) and event.code not in {
                "PLACEHOLDER_BASE", "UNPROCESSABLE_DOCUMENT", "DUPLICATE_SOURCE_ID", "UNKNOWN_INFORMATION",
                "REQUIRED_PROVENANCE", "INTERNAL_TRANSFORMATION_FAILURE", "ONTOLOGY_DELIVERY", "SIDECAR_DELIVERY",
            })


def _attribute_owner_without_local_class_facts(message: str, effect: str = "") -> set[str]:
    """Read affirmative ERROR wording for an attribute owned by a Class without a local owl:Class."""
    combined = f"{message} {effect}".strip()
    wording = combined.casefold().replace("`", "").replace("’", "'")
    if re.search(
        r"\b(?:unexpected internal|not implemented|unimplemented|outside the decided baseline"
        r"|remains (?:unspecified|deferred|outside))\b",
        wording,
    ):
        return set()
    wording = re.sub(r"\bcan't\b", "cannot", wording)
    wording = re.sub(r"n't\b", " not", wording)
    while re.search(r"\{[^{}]*\}", wording):
        wording = re.sub(r"\{[^{}]*\}", "<value>", wording)
    wording = re.sub(r"""(?<!\w)(?:'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*")(?=$|[\s.,;:)!?])""", "<quoted>", wording)
    wording = " ".join(wording.split())
    disqualifiers = (
        r"\b(?:if|whether|unless|when|whenever)\b[^.!?;]*\b(?:attribute|owner|owning|class|primitive|void)\b",
        r"\b(?:may|might|could)\s+(?:be|have|lack|fail)\b",
    )
    if any(re.search(pattern, wording) for pattern in disqualifiers):
        return set()
    owl_class = r"(?:generated\s+)?(?:local\s+)?(?:owl[:\s]+)?class(?:\s+(?:declaration|resource|element|representation))?"
    owner_noun = r"(?:owning\s+(?:class|classifier|datatype)|owner(?:\s+(?:class|classifier|datatype))?)"
    clause_disqualifiers = (
        r"\b(?:value[- ]type|propertytype|target(?:\s+class)?|categorizer|generalization)\b",
        r"\brelation\b[^.!?;]*\b(?:source|target)\b",
        r"\b(?:is|was|can be|could be|has been)\s+(?:valid|usable|resolved|supported)\b",
        r"\bnot\s+(?:without|lacking|missing|invalid|unusable|incompatible)\b",
        r"\bdoes\s+not\s+lack\b",
        rf"(?<!not )(?<!cannot )\b(?:has|generates?|supplies?|provides?)\s+(?:a|an)\s+{owl_class}\b",
    )
    missing_class = rf"(?:has\s+no|lacks(?:\s+a)?|is\s+without|without|missing(?:\s+a)?|does\s+not\s+(?:have|generate)|cannot\s+(?:supply|provide|generate))\s+(?:a\s+)?{owl_class}"
    patterns = (
        re.compile(rf"\battribute\b[^.!?;]*\b{owner_noun}\b[^.!?;]*\b{missing_class}\b"),
        re.compile(rf"\b{owner_noun}\b[^.!?;]*\battribute\b[^.!?;]*\b{missing_class}\b"),
        re.compile(rf"\battribute\b[^.!?;]*\bowned\s+by\b[^.!?;]*\b{missing_class}\b"),
    )
    for clause in re.split(r"[.!?;]+", wording):
        clause = clause.strip()
        if not clause:
            continue
        if any(re.search(pattern, clause) for pattern in clause_disqualifiers):
            continue
        if any(pattern.search(clause) for pattern in patterns):
            return {"attribute_owner_without_local_class"}
    return set()


def attribute_owner_without_local_class_diagnostic(message: str, effect: str = "") -> bool:
    """Return whether a native ERROR asserts an attribute owner lacks a generated local owl:Class."""
    return bool(_attribute_owner_without_local_class_facts(message, effect))


def _normalize_diagnostic_clauses(message: str) -> tuple[str, list[str]]:
    """Normalize prose into lowercase clauses, rejecting internal/deferred guard wording."""
    wording = message.casefold().replace("`", "").replace("’", "'")
    if re.search(
        r"\b(?:unexpected internal|not implemented|unimplemented|outside the decided baseline"
        r"|remains (?:unspecified|deferred|outside))\b",
        wording,
    ):
        return "", []
    wording = re.sub(r"\bcan't\b", "cannot", wording)
    wording = re.sub(r"n't\b", " not", wording)
    while re.search(r"\{[^{}]*\}", wording):
        wording = re.sub(r"\{[^{}]*\}", "<value>", wording)
    wording = re.sub(r"""(?<!\w)(['"])(void)\1""", r"\2", wording)
    wording = re.sub(r"""(?<!\w)(?:'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*")(?=$|[\s.,;:)!?])""", "<quoted>", wording)
    wording = " ".join(wording.split())
    disqualifiers = (
        r"\b(?:if|whether|unless|when|whenever)\b[^.!?;]*\b(?:relation|property|generalization|source|target|void|stereotype)\b",
        r"\b(?:may|might|could)\s+(?:be|fail|conflict)\b",
    )
    if any(re.search(pattern, wording) for pattern in disqualifiers):
        return "", []
    clauses = [clause.strip() for clause in re.split(r"[.!?;]+", wording) if clause.strip()]
    return wording, clauses


def _rd02_datatype_relation_facts(severity: str, message: str, effect: str = "") -> tuple[str | None, set[str]]:
    """Read affirmative RD-02 datatype-valued relation compatibility/warning conditions."""
    combined = f"{message} {effect}".strip()
    _, clauses = _normalize_diagnostic_clauses(combined)
    if not clauses:
        return None, set()
    facts: set[str] = set()
    kind: str | None = None
    datatype_prop = r"(?:owl:)?datatype[- ]?propert(?:y|ies)|datatype[- ]valued(?: ordinary)?(?: binary)? relation"
    object_prop = r"(?:owl:)?object[- ]?propert(?:y|ies)"
    owl_class = r"(?:generated\s+)?(?:local\s+)?(?:owl[:\s]+)?class(?:\s+(?:declaration|resource|element|representation))?"

    if severity == "ERROR":
        void_patterns = (
            re.compile(r"\b(?:relation|target(?:s|ing|ed)?(?: end| endpoint)?)\b[^.!?;]*\bvoid\b[^.!?;]*\b(?:no (?:registered )?datatype|no mapping|unsupported|cannot (?:generate|map)|not mapped|lacks|has no)\b"),
            re.compile(r"\bvoid\b[^.!?;]*\b(?:target(?:s|ing|ed)?|endpoint|relation)\b[^.!?;]*\b(?:no (?:registered )?datatype|no mapping|unsupported|cannot|lacks|has no)\b"),
        )
        source_patterns = (
            re.compile(rf"\bsource\b[^.!?;]*\b(?:no|lacks|without)\s+{owl_class}"),
            re.compile(rf"\bsource\b[^.!?;]*\b(?:primitive|void)\b[^.!?;]*\b(?:no|lacks|without|cannot)\b"),
            re.compile(rf"\b(?:primitive|void)\s+(?:datatype\s+)?source\b[^.!?;]*\b(?:cannot|rejected|unsupported|no\s+{owl_class}|lacks)\b"),
        )
        stereotype_names = r"(?:componentof|memberof|subcollectionof|subquantityof|characterization|mediation|participational|externaldependence)"
        stereo_patterns = (
            re.compile(rf"\bstereotype\b[^.!?;]*(?:{stereotype_names})?[^.!?;]*\b(?:incompatible|requires\s+(?:an?\s+)?{object_prop}|not compatible|cannot be used|rejected)\b[^.!?;]*(?:{datatype_prop})?"),
            re.compile(rf"\b{stereotype_names}\b[^.!?;]*\b(?:{datatype_prop})\b[^.!?;]*\b(?:incompatible|requires\s+(?:an?\s+)?{object_prop}|not compatible|cannot|rejected)\b"),
            re.compile(rf"\b(?:{datatype_prop})\b[^.!?;]*\b(?:stereotype|{stereotype_names})\b[^.!?;]*\b(?:incompatible|requires\s+(?:an?\s+)?{object_prop}|not compatible|cannot|rejected)\b"),
        )
        chain_patterns = (
            re.compile(rf"\b(?:material[- ]property[- ]chain|material chain|property chain)\b[^.!?;]*\b(?:requires\s+(?:an?\s+)?{object_prop}|incompatible|conflicts?)\b[^.!?;]*(?:{datatype_prop})?"),
            re.compile(rf"\b(?:{datatype_prop})\b[^.!?;]*(?:\b(?:incompatible|conflicts?)\b[^.!?;]*\b(?:material[- ]property[- ]chain|material chain|property chain)\b|\b(?:material[- ]property[- ]chain|material chain|property chain)\b[^.!?;]*\b(?:incompatible|requires\s+(?:an?\s+)?{object_prop}|conflicts?|cannot)\b)"),
        )
        comparative_patterns = (
            re.compile(rf"\b(?:comparative(?:[-– ]quality)? derivation|comparative relation)\b[^.!?;]*\b(?:requires\s+(?:an?\s+)?{object_prop}|incompatible|conflicts?)\b[^.!?;]*(?:{datatype_prop})?"),
            re.compile(rf"\b(?:{datatype_prop})\b[^.!?;]*(?:\b(?:incompatible|conflicts?)\b[^.!?;]*\b(?:comparative(?:[-– ]quality)? derivation)\b|\b(?:comparative(?:[-– ]quality)? derivation)\b[^.!?;]*\b(?:incompatible|requires\s+(?:an?\s+)?{object_prop}|conflicts?|cannot)\b)"),
        )
        mult_patterns = (
            re.compile(rf"\bsource(?:[- ]end)?\s+(?:multiplicit(?:y|ies)|cardinalit(?:y|ies)|bounds?|constraints?)\b[^.!?;]*\b(?:inverse|cannot|incompatible|requires\s+an?\s+(?:unavailable\s+)?inverse|no inverse)\b"),
            re.compile(rf"\b(?:unavailable|no)\s+inverse(?:\s+datatype\s+property)?\b[^.!?;]*\bsource(?:[- ]end)?\s+(?:multiplicit(?:y|ies)|cardinalit(?:y|ies)|bounds?|constraints?)\b"),
            re.compile(rf"\b(?:{datatype_prop})\b[^.!?;]*\bsource(?:[- ]end)?\s+(?:multiplicit(?:y|ies)|cardinalit(?:y|ies)|bounds?)\b[^.!?;]*\b(?:no inverse|unavailable|cannot|incompatible)\b"),
        )
        for clause in clauses:
            if not re.search(r"\bnot\s+(?:incompatible|unsupported|rejected|missing)\b", clause):
                if any(p.search(clause) for p in void_patterns) and not re.search(r"^\s*attribute\b", clause):
                    facts.add("void_relation_target")
                    kind = kind or "datatype_relation_incompatibility"
                if any(p.search(clause) for p in source_patterns):
                    facts.add("non_class_relation_source")
                    kind = kind or "failed_relation"
                if any(p.search(clause) for p in stereo_patterns) and (
                        "stereotype" in clause or re.search(stereotype_names, clause)):
                    if "datatype" in clause or "primitive" in clause:
                        facts.add("incompatible_datatype_relation_stereotype")
                        kind = kind or "datatype_relation_incompatibility"
                if any(p.search(clause) for p in chain_patterns) and (
                        "datatype" in clause or "primitive" in clause):
                    facts.add("incompatible_material_chain")
                    kind = kind or "datatype_relation_incompatibility"
                if any(p.search(clause) for p in comparative_patterns) and (
                        "datatype" in clause or "primitive" in clause):
                    facts.add("incompatible_comparative_derivation")
                    kind = kind or "datatype_relation_incompatibility"
                if any(p.search(clause) for p in mult_patterns):
                    facts.add("incompatible_source_multiplicity")
                    kind = kind or "datatype_relation_incompatibility"
    elif severity == "WARNING":
        role_patterns = (
            re.compile(r"\bsource(?:[- ]end)?\s+role(?:\s+name)?\b[^.!?;]*\b(?:cannot be represented|not represented|unrepresentable|omitted|no inverse|without an inverse)\b"),
            re.compile(r"\b(?:cannot represent|omitted|unrepresentable)\b[^.!?;]*\bsource(?:[- ]end)?\s+role(?:\s+name)?\b"),
        )
        for clause in clauses:
            if not re.search(r"\b(?:is|was)\s+represented\b", clause) and any(p.search(clause) for p in role_patterns):
                facts.add("unrepresentable_source_role")
                kind = kind or "unrepresentable_source_role"
    return kind, facts


def _rd02_mixed_kind_facts(severity: str, message: str, effect: str = "") -> tuple[str | None, set[str]]:
    """Read affirmative RD-02 DK-PROP-03 and DK-REL-14/15 mixed-kind / unavailable-inverse ERRORs."""
    if severity != "ERROR":
        return None, set()
    combined = f"{message} {effect}".strip()
    _, clauses = _normalize_diagnostic_clauses(combined)
    if not clauses:
        return None, set()
    facts: set[str] = set()
    kind: str | None = None
    mixed_cue = (
        r"(?:mix(?:ed|es|ing)\s+(?:owl\s+)?(?:object(?:/|\s+and\s+|\s+or\s+)data(?:type)?|property[- ]kind)"
        r"|cross[- ]kind"
        r"|(?:owl:)?object[- ]?propert(?:y|ies)\b[^.!?;]*\b(?:and|with|to|from|cannot\s+(?:subset|redefine|specialize|be\s+disjoint\s+with))\b[^.!?;]*\b(?:owl:)?datatype[- ]?propert(?:y|ies)"
        r"|(?:owl:)?datatype[- ]?propert(?:y|ies)\b[^.!?;]*\b(?:and|with|to|from|cannot\s+(?:subset|redefine|specialize|be\s+disjoint\s+with))\b[^.!?;]*\b(?:owl:)?object[- ]?propert(?:y|ies)"
        r"|property[- ]kind\s+incompatibilit(?:y|ies)"
        r"|incompatible\s+property\s+kinds?)"
    )
    unavail_inv_patterns = (
        re.compile(r"\b(?:subsettedproperties|redefinedproperties|subsetting|redefinition|property (?:reference|inclusion))\b[^.!?;]*\b(?:no|unavailable|lacks|has no|without)\b[^.!?;]*\binverse\b[^.!?;]*\bdatatype\b"),
        re.compile(r"\b(?:subsettedproperties|redefinedproperties|subsetting|redefinition|property (?:reference|inclusion))\b[^.!?;]*\binverse\b[^.!?;]*\bdatatype\b[^.!?;]*\b(?:no|unavailable|lacks|has no|cannot)\b"),
        re.compile(r"\b(?:datatype[- ]?propert(?:y|ies)|datatype[- ]valued relation)\b[^.!?;]*\b(?:no|lacks|has no|without)\b[^.!?;]*\binverse\b[^.!?;]*(?:subset|redefin|reference|inclusion|source(?:[- ]association)? end)"),
        re.compile(r"\bsource(?:[- ]association)? end\b[^.!?;]*\bdatatype\b[^.!?;]*\b(?:no|unavailable|lacks|has no)\b[^.!?;]*\binverse\b"),
    )
    for clause in clauses:
        if re.search(r"\bnot\s+(?:mixed|incompatible|cross[- ]kind)\b", clause):
            continue
        if any(p.search(clause) for p in unavail_inv_patterns):
            facts.add("unavailable_datatype_inverse_reference")
            kind = kind or "property_inclusion_incompatibility"
        if re.search(mixed_cue, clause):
            if re.search(r"\b(?:subset(?:ting|tedproperties)?|redefin(?:ing|ition|edproperties)?|property (?:reference|inclusion)|inclusion)\b", clause):
                facts.add("mixed_property_kind_inclusion")
                kind = kind or "property_inclusion_incompatibility"
            if re.search(r"\b(?:disjoint|disjointness|generalization[- ]set)\b", clause):
                facts.add("mixed_property_kind_disjointness")
                kind = kind or "mixed_property_kind_disjointness"
            if re.search(r"\b(?:generalization|subproperty)\b", clause) and not re.search(
                    r"\b(?:generalization[- ]set|disjoint|disjointness)\b", clause):
                facts.add("mixed_property_kind_generalization")
                kind = kind or "failed_relation_generalization"
    return kind, facts


def rd02_relation_diagnostic(severity: str, message: str, effect: str = "") -> frozenset[str]:
    """Return recognized RD-02 datatype-relation / mixed-kind semantic facts for harness checks."""
    _, rel_facts = _rd02_datatype_relation_facts(severity, message, effect)
    _, mixed_facts = _rd02_mixed_kind_facts(severity, message, effect)
    return frozenset(rel_facts | mixed_facts)


def _relation_properties_container_facts(message: str) -> set[str]:
    """Read affirmative RD-02 Relation.properties container/arity ERROR wording."""
    wording = message.casefold().replace("`", "").replace("’", "'")
    if re.search(
        r"\b(?:unexpected internal|not implemented|unimplemented|outside the decided baseline"
        r"|outside this increment|remains (?:unspecified|deferred|outside))\b",
        wording,
    ):
        return set()
    wording = re.sub(r"\bcan't\b", "cannot", wording)
    wording = re.sub(r"n't\b", " not", wording)
    wording = re.sub(r"\bproperties\[\d+\]", "properties entry", wording)
    while re.search(r"\[[^\[\]]*\]", wording):
        wording = re.sub(r"\[[^\[\]]*\]", "<value>", wording)
    while re.search(r"\{[^{}]*\}", wording):
        wording = re.sub(r"\{[^{}]*\}", "<value>", wording)
    wording = re.sub(r"""(?<!\w)(['"])(properties|property|relation|null|instantiation)\1""", r"\2", wording)
    wording = re.sub(r"""(?<!\w)(?:'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*")(?=$|[\s.,;:)!?])""", "<quoted>", wording)
    wording = " ".join(wording.split())

    disqualifiers = (
        r"\b(?:if|whether|unless|when|whenever)\b[^.!?;]*\b(?:relation|association|properties|end|ends|arity)\b",
        r"\b(?:may|might|could)\s+(?:be|have|contain|fail)\b",
        r"\b(?:may|might|could)\s+or\s+(?:may|might|could)\s+not\b",
        r"\b(?:absent|missing)\s+or\s+null\b|\bnull\s+or\s+(?:absent|missing)\b",
        r"\b(?:missing|absent|null)\s+or\s+(?:not\s+(?:an?\s+)?(?:json\s+)?array|non[- ]?array|malformed|non[- ]?binary)\b",
        r"\b(?:non[- ]?binary|malformed)\s+or\s+(?:absent|missing|null|non[- ]?array)\b",
        r"\bbinary\s+or\s+non[- ]?binary\b|\bvalid\s+or\s+(?:invalid|malformed|non[- ]?binary)\b",
        r"\bnot\s+(?:absent|missing|malformed|non[- ]?binary|non[- ]?array|invalid)\b",
        r"\b(?:generalizations|generalization[- ]?set|literals|categorizer|package\.contents|class\.properties)\b",
        r"^\s*(?:class|package|attribute|enumeration)\b",
    )
    if any(re.search(pattern, wording) for pattern in disqualifiers):
        return set()
    if not re.search(r"\b(?:relation|association)\b", wording):
        return set()

    prop_noun = r"(?:properties(?:\s+(?:field|container|array|list|value|entry|entries))?)"
    rel_scope = r"(?:\s+(?:on|of|for|in)\s+(?:the\s+)?(?:(?:non[- ]?instantiation|instantiation)\s+)?(?:relation|association)(?:\s+(?:<quoted>|<value>))?)?"
    non_array_type = r"(?:non[- ]?array(?:\s+(?:value|type))?|object|dict(?:ionary)?|string|str|int(?:eger)?|number|float|bool(?:ean)?)"
    absent_patterns = (
        re.compile(rf"\b{prop_noun}{rel_scope}\s+(?:is|was)\s+(?:absent|missing|omitted|not\s+(?:present|supplied|provided))\b"),
        re.compile(rf"\b(?:missing|absent|omitted|no)\s+(?:(?:its|their|a|an|the|required)\s+)?{prop_noun}\b"),
        re.compile(rf"\b(?:does\s+not|did\s+not)\s+(?:have|contain|supply|provide)\s+(?:(?:a|an|the|its|their|required)\s+)?{prop_noun}\b"),
        re.compile(rf"\b(?:lacks|is\s+without)\s+(?:(?:a|an|the|its|their|required)\s+)?{prop_noun}\b"),
    )
    null_patterns = (
        re.compile(rf"(?<!\bnot\s)\b{prop_noun}{rel_scope}\s+(?:is|was)\s+(?:explicitly\s+)?(?:null|none)\b"),
        re.compile(rf"(?<!\bnot\s)\b(?:explicitly\s+)?null\s+{prop_noun}\b"),
        re.compile(rf"\b{prop_noun}{rel_scope}[^.!?;]*(?:expected|must\s+be|should\s+be)\s+(?:a\s+)?(?:json\s+)?(?:array|list)\s*[,;:]\s*(?:but\s+)?(?:got|found|received|not\b[^.!?;]*)\s+(?:null|none|nonetype)\b"),
    )
    non_array_patterns = (
        re.compile(rf"\b{prop_noun}{rel_scope}\s+(?:is|was)\s+(?:(?:a|an)\s+)?(?:{non_array_type}|not\s+(?:a|an)\s+(?:json\s+)?(?:array|list))\b"),
        re.compile(rf"\b(?:has|had|contains|with)\s+(?:(?:a|an)\s+)?non[- ]?array\s+{prop_noun}\b"),
        re.compile(rf"\bnon[- ]?array\s+{prop_noun}\b"),
        re.compile(rf"\b{prop_noun}{rel_scope}[^.!?;]*(?:expected|must\s+be|should\s+be)\s+(?:a|an)\s+(?:json\s+)?(?:array|list)\s*[,;:]\s*(?:(?:but\s+)?(?:got|found|received)|not)\s+(?:type\s+)?(?:(?:a|an)\s+)?(?:(?:{non_array_type}|-?\d+(?:\.\d+)?|true|false)\b|<quoted>|<value>)"),
        re.compile(rf"\b{prop_noun}{rel_scope}\s+(?:is|was)\s+not\s+null\s*[,;:]\s*(?:but\s+)?it\s+(?:is|was)\s+(?:(?:a|an)\s+)?{non_array_type}\b"),
    )
    malformed_entry_patterns = (
        re.compile(rf"\b(?:properties|association[- ]?ends?)\b[^.!?;]*\b(?:contains?|has|had|with|entry|entries|item|items|element|elements)\b[^.!?;]*\b(?:non[- ]?object|non[- ]?property|not\s+(?:a|an)\s+(?:json\s+)?object|not\s+(?:a|an)\s+property(?:\s+object)?|malformed\s+(?:entry|entries|item|element)|has\s+(?:invalid\s+)?type\s+(?!property\b)\S+)\b"),
        re.compile(rf"\b(?:non[- ]?object|non[- ]?property)\b[^.!?;]*\b(?:entry|entries|item|items|element|elements)\b[^.!?;]*\b(?:in|inside|of|at)\s+(?:the\s+)?(?:relation\s+(?:<quoted>\s+)?)?{prop_noun}\b"),
        re.compile(rf"\bproperties\s+entry\b[^.!?;]*\b(?:must\s+be|should\s+be|expected)\s+(?:a\s+)?(?:property\s+object|json\s+object)\s*[,;:]\s*(?:but\s+)?(?:got|found|received)\s+(?:(?:null|none|{non_array_type}|array|list)\b|<quoted>|<value>)"),
        re.compile(rf"\bproperties\s+entry\b[^.!?;]*\b(?:is\s+not\s+(?:a|an)\s+(?:json\s+)?object|not\s+(?:a|an)\s+property(?:\s+object)?|is\s+(?:null|none)|has\s+(?:invalid\s+)?type\s+(?!property\b)\S+)\b"),
    )
    end_or_entry = r"(?:(?:association\s+)?ends?|entries|items|elements)"
    non_binary_patterns = (
        re.compile(r"\b(?:non[- ]?binary|unary|n[- ]?ary)\s+(?:relation|association|properties(?:\s+array)?|arity)\b"),
        re.compile(rf"\b(?:relation|association)\b[^.!?;]*\b(?:is|has)\s+(?:(?:a|an)\s+)?(?:non[- ]?binary|unary|n[- ]?ary|arity\s+(?!2\b)\d+|(?:length|size)\s+(?!2\b)\d+|(?!2\b)\d+\s+{end_or_entry})\b"),
        re.compile(rf"\b{prop_noun}\b[^.!?;]*(?:\bis\s+(?:empty|non[- ]?binary|unary|n[- ]?ary)\b|\b(?:has\s+)?(?:length|size|arity)\s+(?!2\b)\d+\b|\bhas\s+(?!2\b)\d+\s+{end_or_entry}\b)"),
        re.compile(rf"\b(?:must|should|expected(?:\s+to)?)\s+(?:have|contain)\s+(?:exactly\s+)?2\s+{end_or_entry}\b[^.!?;]*\b(?:got|found|received|has|length|arity)\s+(?!2\b)\d+\b"),
        re.compile(rf"\b(?:expected|requires?)\s+(?:exactly\s+)?2\s+{end_or_entry}\b[^.!?;]*\b(?:got|found|received)\s+(?!2\b)\d+\b"),
    )

    facts: set[str] = set()
    for clause in re.split(r"[.!?]+", wording):
        clause = clause.strip()
        if not clause:
            continue
        if re.search(r"\b(?:is|was)\s+(?:binary|valid)\b", clause) and not re.search(r"\bnot\s+(?:binary|valid)\b", clause):
            continue
        if any(p.search(clause) for p in absent_patterns):
            facts.add("relation_properties_absent")
        if any(p.search(clause) for p in null_patterns):
            facts.add("relation_properties_null")
        if any(p.search(clause) for p in non_array_patterns):
            facts.add("relation_properties_non_array")
        if any(p.search(clause) for p in malformed_entry_patterns):
            facts.add("relation_properties_malformed_entry")
        if any(p.search(clause) for p in non_binary_patterns):
            facts.add("relation_properties_non_binary")
    return facts


def relation_properties_container_diagnostic(message: str) -> frozenset[str]:
    """Return recognized RD-02 Relation.properties container/arity facts for harness checks."""
    return frozenset(_relation_properties_container_facts(message))


def malformed_package_contents_diagnostic(event, package_id, package_path):
    """Identify the structural package-contents error using its native context."""
    stable_codes = {
        "PLACEHOLDER_BASE", "UNPROCESSABLE_DOCUMENT", "DUPLICATE_SOURCE_ID", "UNKNOWN_INFORMATION",
        "REQUIRED_PROVENANCE", "INTERNAL_TRANSFORMATION_FAILURE", "ONTOLOGY_DELIVERY", "SIDECAR_DELIVERY",
    }
    root = package_path == "$.model"
    if event.severity != "ERROR" or not event.code:
        return False
    if root and event.code != "UNPROCESSABLE_DOCUMENT":
        return False
    if not root and event.code in stable_codes:
        return False
    native = event.raw
    reason = " ".join(native.message.casefold().replace("`", "").split()).removesuffix(".")
    identifier = re.escape(package_id.casefold())
    path = re.escape(package_path.casefold())
    locator = rf"(?:{identifier}|'{identifier}'|\"{identifier}\")"
    path_locator = rf"{path}(?:\.contents)?(?![.\[\w])"
    located = (
        any(source.path in {package_path, package_path + ".contents"} or source.identifier == package_id
            for source in native.sources)
        or re.search(rf"(?<!\w){identifier}(?!\w)", reason)
        or re.search(path_locator, reason)
        or (root and reason.startswith(("root model ", "root package ")))
    )
    if not located:
        return False

    # Match the complete claim about the container, not unrelated adjectives
    # or an error about one of its entries. An expected type alone is not proof.
    prefix = r"(?:the )?(?:root model |root )?" if root else r"(?:the )?(?:nested )?"
    package = rf"package(?: {locator})?"
    field = rf"{prefix}{package}(?:\.|\s+)contents(?: (?:field|container|value))?(?: at {path_locator})?"
    array_type = r"(?:a |an )?(?:json )?(?:array|list)"
    actual = r"(?:an? )?(?:json )?(?:object|dict(?:ionary)?|string|str|number|int(?:eger)?|float|bool(?:ean)?|true|false|non[- ](?:array|list)(?: value)?)"
    condition = (
        rf"(?:is|are|was|were) (?:malformed|invalid|non[- ](?:array|list)|not {array_type}|{actual})"
        rf"|(?:must|should|(?:is |are )?expected to) be {array_type}(?: or null)?"
        rf"(?: \((?:got|found|received) {actual}\)|[,;:] (?:but )?(?:got|found|received) {actual})"
    )
    return bool(re.fullmatch(rf"{field} (?:{condition})|(?:malformed|invalid|non[- ](?:array|list)) {field}", reason))


def _normalize_container_message(message: str) -> str:
    wording = message.casefold().replace("`", "").replace("’", "'")
    if re.search(
        r"\b(?:unexpected internal|not implemented|unimplemented|outside the decided baseline"
        r"|outside this increment|remains (?:unspecified|deferred|outside)"
        r"|(?:has|have) no assigned (?:baseline )?mapping)\b",
        wording,
    ):
        return ""
    wording = re.sub(r"\bcan't\b", "cannot", wording)
    wording = re.sub(r"n't\b", " not", wording)
    wording = re.sub(r"\bcontents\[\d+\]", "contents entry", wording)
    wording = re.sub(r"\bproperties\[\d+\]", "properties entry", wording)
    wording = re.sub(r"\bliterals\[\d+\]", "literals entry", wording)
    while re.search(r"\[[^\[\]]*\]", wording):
        wording = re.sub(r"\[[^\[\]]*\]", "<value>", wording)
    while re.search(r"\{[^{}]*\}", wording):
        wording = re.sub(r"\{[^{}]*\}", "<value>", wording)
    wording = re.sub(
        r"""(?<!\w)(['"])(contents|properties|literals|package|class|property|literal|project|type|null|enumeration)\1""",
        r"\2",
        wording,
    )
    wording = re.sub(r"""(?<!\w)(?:'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*")(?=$|[\s.,;:)!?])""", "<quoted>", wording)
    return " ".join(wording.split())


def _package_contents_entry_facts(message: str, sources: tuple = ()) -> set[str]:
    """Read affirmative RD-02 Package.contents entry and misplaced-declaration ERROR wording."""
    wording = _normalize_container_message(message)
    if not wording:
        return set()
    disqualifiers = (
        r"\b(?:if|whether|unless|when|whenever)\b[^.!?;]*\b(?:package|contents|entry|entries|type|project|property|literal)\b",
        r"\b(?:may|might|could)\s+(?:be|have|contain|fail)\b",
        r"\b(?:may|might|could)\s+or\s+(?:may|might|could)\s+not\b",
        r"\bnot\s+(?:invalid|malformed|misplaced|disallowed|forbidden|prohibited|non[- ]?object|missing)\b",
        r"\b(?:class\.properties|relation\.properties|class\.literals|generalizations)\b",
        r"^\s*(?:relation|association|attribute|enumeration)\b",
    )
    if any(re.search(pattern, wording) for pattern in disqualifiers):
        return set()
    has_pkg_context = (
        ("package" in wording and "contents" in wording)
        or bool(re.search(r"\b(?:package\.contents|package[- ]contents|model\.contents)\b", wording))
        or any(".contents[" in (getattr(src, "path", "") or "") for src in sources)
    )
    if not has_pkg_context:
        return set()

    non_object_patterns = (
        re.compile(r"\b(?:non[- ]?object|not\s+(?:a|an)\s+(?:json\s+)?object)\b[^.!?;]*\b(?:entry|entries|item|items|element|elements)?[^.!?;]*\bcontents\b"),
        re.compile(r"\bcontents(?:\s+(?:entry|item|element))?\b[^.!?;]*\b(?:is\s+not\s+(?:a|an)\s+(?:json\s+)?object|is\s+(?:a|an)\s+non[- ]?object|(?:must|should|expected(?:\s+to)?)\s+be\s+(?:a|an)\s+(?:json\s+)?object)\b"),
    )
    invalid_type_patterns = (
        re.compile(r"\b(?:contents(?:\s+(?:entry|item|element))?|entry|item|element|object)\b[^.!?;]*\b(?:lacks?|missing|absent|without|has\s+(?:a|an)?\s*(?:invalid|missing|null|none|empty|blank|whitespace(?:-only)?|non[- ]?string))\s+(?:(?:a|an)\s+)?(?:valid\s+)?(?:non[- ]?empty\s+)?(?:string\s+)?type\b"),
        re.compile(r"\b(?:contents(?:\s+(?:entry|item|element))?|entry|item|element|object)\b[^.!?;]*\b(?:must|should|expected\s+to)\s+have\s+(?:a|an)\s+(?:valid\s+)?(?:non[- ]?empty\s+)?(?:string\s+)?type\b"),
        re.compile(r"\btype\b[^.!?;]*\b(?:is|was)\s+(?:absent|missing|null|none|empty|blank|whitespace(?:-only)?|non[- ]?string|not\s+(?:a|an)\s+(?:valid\s+)?(?:non[- ]?empty\s+)?(?:json\s+)?string)\b"),
        re.compile(r"\b(?:invalid|missing|empty|blank|non[- ]?string)\s+(?:element\s+)?type\b[^.!?;]*\bcontents\b"),
    )
    misplaced_patterns = (
        re.compile(r"\b(?:misplaced|disallowed|forbidden|prohibited|unsupported|not\s+(?:permitted|allowed))\b[^.!?;]*\b(?:project|property|literal)(?:\s+(?:declaration|entry|element|type))?\b"),
        re.compile(r"\b(?:project|property|literal)(?:\s+(?:declaration|entry|element|type))?\b[^.!?;]*\b(?:is|was|are)?\s*(?:misplaced|disallowed|forbidden|prohibited|not\s+(?:permitted|allowed)|cannot\s+(?:appear|be\s+(?:placed|declared|contained)))\b"),
        re.compile(r"\b(?:package\.contents|package\s+contents|contents)\b[^.!?;]*\b(?:cannot|must\s+not|does\s+not)\s+(?:contain|accept|allow|permit)\b[^.!?;]*\b(?:project|property|literal)\b"),
    )

    facts: set[str] = set()
    for clause in re.split(r"[.!?;]+", wording):
        clause = clause.strip()
        if not clause:
            continue
        if re.search(r"\b(?:is|was)\s+(?:valid|permitted|allowed)\b", clause) and not re.search(r"\bnot\s+(?:valid|permitted|allowed)\b", clause):
            continue
        if any(p.search(clause) for p in non_object_patterns):
            facts.add("package_contents_non_object_entry")
        if any(p.search(clause) for p in invalid_type_patterns):
            facts.add("package_contents_invalid_type")
        if any(p.search(clause) for p in misplaced_patterns):
            facts.add("package_contents_misplaced_declaration")
    return facts


def package_contents_entry_diagnostic(message: str, sources: tuple = ()) -> frozenset[str]:
    """Return recognized RD-02 Package.contents entry/misplaced-declaration facts for harness checks."""
    return frozenset(_package_contents_entry_facts(message, sources))


def _class_properties_container_facts(message: str) -> set[str]:
    """Read affirmative RD-02 Class.properties container/entry ERROR wording."""
    wording = _normalize_container_message(message)
    if not wording:
        return set()
    disqualifiers = (
        r"\b(?:if|whether|unless|when|whenever)\b[^.!?;]*\b(?:class|classifier|properties|entry|entries)\b",
        r"\b(?:may|might|could)\s+(?:be|have|contain|fail)\b",
        r"\b(?:may|might|could)\s+or\s+(?:may|might|could)\s+not\b",
        r"\bnot\s+(?:invalid|malformed|non[- ]?array|non[- ]?object|non[- ]?property)\b",
        r"\b(?:relation|association|package\.contents|class\.literals|literals|generalizations)\b",
        r"^\s*(?:relation|association|package|enumeration)\b",
    )
    if any(re.search(pattern, wording) for pattern in disqualifiers):
        return set()
    if not (re.search(r"\b(?:class|classifier|datatype|enumeration)\b", wording) and "properties" in wording):
        return set()

    non_array_type = r"(?:non[- ]?array(?:\s+(?:value|container|type))?|object|dict(?:ionary)?|string|str|int(?:eger)?|number|float|bool(?:ean)?)"
    non_array_patterns = (
        re.compile(rf"\bproperties(?:\s+(?:field|container|value))?\b[^.!?;]*\b(?:is|was)\s+(?:(?:a|an)\s+)?(?:{non_array_type}|not\s+(?:a|an)\s+(?:json\s+)?(?:array|list)|malformed|invalid)\b"),
        re.compile(rf"\b(?:malformed|invalid|non[- ]?array)\s+(?:class\s+)?properties\b"),
        re.compile(rf"\bproperties(?:\s+(?:field|container|value))?\b[^.!?;]*(?:expected|must\s+be|should\s+be)\s+(?:a|an)\s+(?:json\s+)?(?:array|list)\b"),
        re.compile(r"\b(?:has|had|with)\s+(?:a|an)?\s*non[- ]?array\s+properties\b"),
    )
    invalid_entry_patterns = (
        re.compile(r"\bproperties(?:\s+(?:entry|entries|item|items|element|elements))?\b[^.!?;]*\b(?:non[- ]?object|non[- ]?property|not\s+(?:a|an)\s+(?:json\s+)?object|not\s+(?:a|an)\s+property(?:\s+object)?|malformed|invalid\s+(?:entry|type)|lacks?\s+(?:a\s+)?(?:valid\s+)?(?:property\s+)?type|missing\s+(?:a\s+)?type)\b"),
        re.compile(r"\b(?:non[- ]?object|non[- ]?property|invalid|malformed)\s+(?:entry|entries|item|items|element|elements)\b[^.!?;]*\bproperties\b"),
        re.compile(r"\bproperties(?:\s+(?:entry|item|element))?\b[^.!?;]*(?:must|should|expected(?:\s+to)?)\s+be\s+(?:a|an)\s+(?:property(?:\s+object)?|json\s+object)\b"),
        re.compile(r"\bproperties(?:\s+(?:entry|item|element))?\b[^.!?;]*\bhas\s+(?:invalid\s+|unsupported\s+|unexpected\s+)?type\b"),
    )

    facts: set[str] = set()
    for clause in re.split(r"[.!?;]+", wording):
        clause = clause.strip()
        if not clause:
            continue
        if re.search(r"\b(?:is|was)\s+(?:valid|allowed|accepted)\b", clause) and not re.search(r"\bnot\s+(?:valid|allowed|accepted)\b", clause):
            continue
        if any(p.search(clause) for p in invalid_entry_patterns):
            facts.add("class_properties_invalid_entry")
        elif any(p.search(clause) for p in non_array_patterns):
            facts.add("class_properties_non_array")
    return facts


def class_properties_container_diagnostic(message: str) -> frozenset[str]:
    """Return recognized RD-02 Class.properties container/entry facts for harness checks."""
    return frozenset(_class_properties_container_facts(message))


def _non_enum_literals_facts(message: str) -> set[str]:
    """Read affirmative RD-02 non-enumeration Class.literals ERROR wording."""
    wording = _normalize_container_message(message)
    if not wording:
        return set()
    disqualifiers = (
        r"\b(?:if|whether|unless|when|whenever)\b[^.!?;]*\b(?:class|literals?|enumeration)\b",
        r"\b(?:may|might|could)\s+(?:be|have|contain|fail)\b",
        r"\b(?:may|might|could)\s+or\s+(?:may|might|could)\s+not\b",
        r"\bnot\s+(?:invalid|malformed|non[- ]?array|non[- ]?enumeration|disallowed|forbidden|prohibited)\b",
        r"\b(?:is|was)\s+(?:an\s+)?enumeration\b",
        r"^\s*enumeration\s+literals\b",
        r"\bno\s+enumeration\s+values\s+were\s+available\b",
        r"\b(?:relation|association|package\.contents|class\.properties|generalizations)\b",
        r"^\s*(?:relation|association|package)\b",
    )
    if any(re.search(pattern, wording) for pattern in disqualifiers):
        return set()
    has_non_enum_cue = bool(
        re.search(
            r"\bnon[- ]?enumeration\b|\bnot\s+(?:an?\s+)?enumeration\b"
            r"|\bwithout\s+(?:the\s+|stereotype\s+)?enumeration\b|\boutside\s+(?:an?\s+)?enumeration",
            wording,
        )
        or (
            re.search(r"\b(?:class|classifier|datatype)\b", wording)
            and not re.search(r"\benumeration\s+class\b|\bstereotype\s+enumeration\b", wording)
        )
    )
    if not (has_non_enum_cue and ("literal" in wording or "literals" in wording)):
        return set()

    non_array_type = r"(?:non[- ]?array(?:\s+(?:value|container|type))?|object|dict(?:ionary)?|string|str|int(?:eger)?|number|float|bool(?:ean)?)"
    non_array_patterns = (
        re.compile(rf"\bliterals(?:\s+(?:field|container|value))?\b[^.!?;]*\b(?:is|was)\s+(?:(?:a|an)\s+)?(?:{non_array_type}|not\s+(?:a|an)\s+(?:json\s+)?(?:array|list)|malformed|invalid)\b"),
        re.compile(r"\b(?:malformed|invalid|non[- ]?array)\s+(?:class\s+)?literals\b"),
        re.compile(r"\bliterals(?:\s+(?:field|container|value))?\b[^.!?;]*(?:expected|must\s+be|should\s+be)\s+(?:a|an)\s+(?:json\s+)?(?:array|list)\b"),
        re.compile(r"\b(?:has|had|with)\s+(?:a|an)?\s*non[- ]?array\s+literals\b"),
    )
    invalid_entry_patterns = (
        re.compile(r"\bliterals(?:\s+(?:entry|entries|item|items|element|elements))?\b[^.!?;]*\b(?:non[- ]?object|non[- ]?literal|not\s+(?:a|an)\s+(?:json\s+)?object|not\s+(?:a|an)\s+literal(?:\s+object)?|malformed|invalid\s+(?:entry|type)|missing\s+(?:a\s+)?type)\b"),
        re.compile(r"\b(?:non[- ]?object|non[- ]?literal|invalid|malformed)\s+(?:entry|entries|item|items|element|elements)\b[^.!?;]*\bliterals\b"),
        re.compile(r"\bliterals(?:\s+(?:entry|item|element))?\b[^.!?;]*(?:must|should|expected(?:\s+to)?)\s+be\s+(?:a|an)\s+(?:literal(?:\s+object)?|json\s+object)\b"),
    )
    disallowed_literal_patterns = (
        re.compile(r"\bliterals?\b[^.!?;]*\b(?:disallowed|forbidden|prohibited|unsupported|rejected|not\s+(?:permitted|allowed|supported)|cannot\s+(?:be\s+(?:declared|used|present)|appear))\b"),
        re.compile(r"\b(?:cannot|must\s+not|may\s+not)\s+(?:have|contain|declare|supply|provide)\s+(?:(?:a|an)\s+)?(?:non[- ]?empty\s+)?literals?\b"),
        re.compile(r"\bliteral\s+declarations?\b[^.!?;]*\b(?:outside\s+(?:an?\s+)?enumerations?|on\s+non[- ]?enumeration)\b"),
    )

    facts: set[str] = set()
    for clause in re.split(r"[.!?;]+", wording):
        clause = clause.strip()
        if not clause:
            continue
        if re.search(r"\b(?:is|was)\s+(?:valid|permitted|allowed)\b", clause) and not re.search(r"\bnot\s+(?:valid|permitted|allowed)\b", clause):
            continue
        if any(p.search(clause) for p in invalid_entry_patterns):
            facts.add("non_enum_literals_invalid_entry")
        elif any(p.search(clause) for p in non_array_patterns):
            facts.add("non_enum_literals_non_array")
        if any(p.search(clause) for p in disallowed_literal_patterns):
            facts.add("non_enum_literals_disallowed_literal")
    return facts


def non_enum_literals_diagnostic(message: str) -> frozenset[str]:
    """Return recognized RD-02 non-enumeration Class.literals facts for harness checks."""
    return frozenset(_non_enum_literals_facts(message))


def _normalize_textual_message(message: str) -> str:
    wording = message.casefold().replace("`", "").replace("’", "'")
    if re.search(
        r"\b(?:unexpected internal|not implemented|unimplemented|outside the decided baseline"
        r"|outside bi-w1|outside this increment|remains (?:unspecified|deferred|outside)"
        r"|(?:has|have) no assigned (?:baseline )?mapping)\b",
        wording,
    ):
        return ""
    wording = re.sub(r"\bcan't\b", "cannot", wording)
    wording = re.sub(r"n't\b", " not", wording)
    wording = re.sub(r"\bproject\.languages\b", "project languages", wording)
    wording = re.sub(r"\blanguages\[\d+\]", "languages entry", wording)
    while re.search(r"\[[^\[\]]*\]", wording):
        wording = re.sub(r"\[[^\[\]]*\]", "<value>", wording)
    while re.search(r"\{[^{}]*\}", wording):
        wording = re.sub(r"\{[^{}]*\}", "<value>", wording)
    wording = re.sub(
        r"""(?<!\w)(['"])(name|description|languagestring|languages|project languages|project|class|relation|property|literal|null|string|object|array|list)\1""",
        r"\2",
        wording,
    )
    wording = re.sub(r"""(?<!\w)(?:'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*")(?=$|[\s.,;:)!?])""", "<quoted>", wording)
    return " ".join(wording.split())


def _textual_carrier_facts(message: str, sources: tuple = ()) -> set[str]:
    """Read affirmative RD-02 malformed name/description/languageString ERROR wording."""
    wording = _normalize_textual_message(message)
    if not wording:
        return set()
    disqualifiers = (
        r"\b(?:if|whether|unless|when|whenever)\b[^.!?;]*\b(?:name|description|languagestring|language\s+tag|entry|carrier|field)\b",
        r"\b(?:may|might|could)\s+(?:be|have|contain|fail)\b",
        r"\b(?:may|might|could)\s+or\s+(?:may|might|could)\s+not\b",
        r"\bnot\s+(?:invalid|malformed|non[- ]?string|non[- ]?object|erroneous)\b",
        r"\b(?:project\s+languages|package\.contents|class\.properties|class\.literals|relation\.properties|generalizations|cardinality|stereotype)\b",
        r"\bmultiple\s+project\s+languages\b",
    )
    if any(re.search(pattern, wording) for pattern in disqualifiers):
        return set()
    has_text_context = (
        bool(re.search(r"\b(?:name|description|languagestring)\b", wording))
        or any(
            (getattr(src, "path", "") or "").endswith((".name", ".description"))
            or ".name[" in (getattr(src, "path", "") or "")
            or ".description[" in (getattr(src, "path", "") or "")
            for src in sources
        )
    )
    if not has_text_context:
        return set()

    field = r"(?:name|description)(?:\s+(?:field|carrier|value))?"
    whole_type = r"(?:non[- ]?(?:string|object|dict(?:ionary)?)|int(?:eger)?|float|number|bool(?:ean)?|array|list)"
    whole_field_patterns = (
        re.compile(rf"\b{field}\b[^.!?;]*\b(?:is|was)\s+(?:(?:a|an)\s+)?(?:{whole_type}|malformed|invalid(?:\s+type)?|not\s+(?:a|an)\s+(?:json\s+)?(?:string|object|languagestring))\b"),
        re.compile(rf"\b{field}\b[^.!?;]*(?:must|should|expected(?:\s+to)?)\s+be\s+(?:a|an)\s+(?:(?:json\s+)?string|languagestring|object)"),
        re.compile(rf"\b(?:malformed|invalid|wrong)\s+(?:whole[- ]?field\s+)?(?:type\s+(?:for|on|of)\s+)?{field}\b"),
        re.compile(rf"\b{field}\b[^.!?;]*\b(?:has|had)\s+(?:an?\s+)?(?:invalid|wrong|unsupported)\s+(?:whole[- ]?field\s+)?type\b"),
    )
    entry_patterns = (
        re.compile(r"\blanguagestring\b[^.!?;]*\b(?:invalid|malformed|non[- ]?string|empty|blank|whitespace)\b"),
        re.compile(r"\b(?:invalid|malformed|empty|blank|whitespace(?:-only)?)\s+(?:explicit\s+)?(?:language\s+tag|languagestring\s+(?:key|entry|value))\b"),
        re.compile(r"\b(?:language\s+tag|languagestring\s+key|localized\s+key)\b[^.!?;]*\b(?:is|was)?\s*(?:invalid|malformed|fails?|must\s+match|does\s+not\s+match)\b"),
        re.compile(r"\b(?:languagestring|localized)\s+(?:entry|value)\b[^.!?;]*\b(?:is|was|must\s+be|should\s+be|expected\s+to\s+be|got)\b[^.!?;]*\b(?:non[- ]?string|string|int(?:eger)?|float|number|bool(?:ean)?|null|array|list|object|dict)\b"),
        re.compile(r"\bnon[- ]?string\s+(?:localized\s+|languagestring\s+)?value\b"),
    )

    facts: set[str] = set()
    for clause in re.split(r"[.!?;]+", wording):
        clause = clause.strip()
        if not clause:
            continue
        if re.search(r"\b(?:is|was)\s+(?:valid|permitted|allowed|accepted)\b", clause) and not re.search(r"\bnot\s+(?:valid|permitted|allowed|accepted)\b", clause):
            continue
        if any(p.search(clause) for p in entry_patterns):
            facts.add("invalid_language_string_entry")
        elif any(p.search(clause) for p in whole_field_patterns):
            facts.add("malformed_textual_carrier")
    return facts


def textual_carrier_diagnostic(message: str, sources: tuple = ()) -> frozenset[str]:
    """Return recognized RD-02 malformed textual-carrier / languageString facts for harness checks."""
    return frozenset(_textual_carrier_facts(message, sources))


def _project_languages_facts(message: str) -> set[str]:
    """Read affirmative RD-02 malformed Project.languages ERROR wording."""
    wording = _normalize_textual_message(message)
    if not wording:
        return set()
    disqualifiers = (
        r"\b(?:if|whether|unless|when|whenever)\b[^.!?;]*\b(?:languages?|tag|entry|entries|array|list)\b",
        r"\b(?:may|might|could)\s+(?:be|have|contain|fail)\b",
        r"\b(?:may|might|could)\s+or\s+(?:may|might|could)\s+not\b",
        r"\bnot\s+(?:invalid|malformed|non[- ]?array|non[- ]?string|empty|blank)\b",
        r"\bmultiple\s+project\s+languages\b",
        r"\bassignment\s+is\s+unresolved\b",
        r"\b(?:languagestring|package\.contents|class\.properties|class\.literals|relation\.properties|generalizations)\b",
        r"\b(?:name|description)\b",
    )
    if any(re.search(pattern, wording) for pattern in disqualifiers):
        return set()
    if not ("project" in wording and "languages" in wording):
        return set()

    non_array_type = r"(?:non[- ]?array(?:\s+(?:value|container|type))?|object|dict(?:ionary)?|string|str|int(?:eger)?|number|float|bool(?:ean)?)"
    non_array_patterns = (
        re.compile(rf"\blanguages(?:\s+(?:field|container|value|carrier))?\b[^.!?;]*\b(?:is|was)\s+(?:(?:a|an)\s+)?(?:{non_array_type}|not\s+(?:a|an)\s+(?:json\s+)?(?:array|list))\b"),
        re.compile(r"\b(?:malformed|invalid|non[- ]?array)\s+project\s+languages\b"),
        re.compile(r"\blanguages(?:\s+(?:field|container|value|carrier))?\b[^.!?;]*(?:expected|must\s+be|should\s+be)\s+(?:a|an)\s+(?:json\s+)?(?:array|list)\b"),
        re.compile(r"\b(?:has|had|with)\s+(?:a|an)?\s*non[- ]?array\s+(?:project\s+)?languages\b"),
    )
    invalid_entry_patterns = (
        re.compile(r"\blanguages(?:\s+(?:entry|entries|element|elements|item|items))?\b[^.!?;]*\b(?:contains?|has|had)\b[^.!?;]*\b(?:non[- ]?string|empty|blank|whitespace(?:-only)?|invalid|malformed|null|int(?:eger)?|bool(?:ean)?|object|dict|array|list)\b"),
        re.compile(r"\b(?:project\s+)?languages\s+(?:entry|entries|element|elements|item|items)\b[^.!?;]*\b(?:must|should|expected(?:\s+to)?|is|was)\b[^.!?;]*\b(?:non[- ]?empty|string|valid|non[- ]?string|empty|blank|whitespace(?:-only)?|invalid|malformed|got)\b"),
        re.compile(r"\b(?:invalid|malformed|empty|blank|whitespace(?:-only)?|non[- ]?string)\s+(?:explicit\s+)?(?:language\s+tag|entry|entries|element|elements)\b[^.!?;]*\blanguages\b"),
        re.compile(r"\blanguage\s+tag\b[^.!?;]*\blanguages\b[^.!?;]*\b(?:is|was)?\s*(?:invalid|malformed|empty|blank|fails?|must\s+match)\b"),
    )

    facts: set[str] = set()
    for clause in re.split(r"[.!?;]+", wording):
        clause = clause.strip()
        if not clause:
            continue
        if re.search(r"\b(?:is|was)\s+(?:valid|permitted|allowed|accepted)\b", clause) and not re.search(r"\bnot\s+(?:valid|permitted|allowed|accepted)\b", clause):
            continue
        if any(p.search(clause) for p in invalid_entry_patterns):
            facts.add("project_languages_invalid_entry")
        elif any(p.search(clause) for p in non_array_patterns):
            facts.add("project_languages_non_array")
    return facts


def project_languages_diagnostic(message: str) -> frozenset[str]:
    """Return recognized RD-02 Project.languages ERROR facts for harness checks."""
    return frozenset(_project_languages_facts(message))


def _malformed_stereotype_facts(message: str, sources: tuple = ()) -> set[str]:
    """Read affirmative RD-02 malformed stereotype ERROR wording.

    Rejects internal/deferred guard wording, conditionals, hedges, negations,
    bare expectations, missing/null/unrecognized DK-DIAG-06 wording, datatype-
    relation incompatibility wording, and unrelated carrier/container subjects.
    """
    wording = message.casefold().replace("`", "").replace("’", "'")
    if re.search(
        r"\b(?:unexpected internal|not implemented|unimplemented|outside the decided baseline"
        r"|outside bi-w1|outside this increment|remains (?:unspecified|deferred|outside)"
        r"|(?:has|have) no assigned (?:baseline )?mapping)\b",
        wording,
    ):
        return set()
    wording = re.sub(r"\bcan't\b", "cannot", wording)
    wording = re.sub(r"n't\b", " not", wording)
    while re.search(r"\[[^\[\]]*\]", wording):
        wording = re.sub(r"\[[^\[\]]*\]", "<value>", wording)
    while re.search(r"\{[^{}]*\}", wording):
        wording = re.sub(r"\{[^{}]*\}", "<value>", wording)
    wording = re.sub(r"(?<!\w)(?:''|\"\"|'\s+'|\"\s+\")(?=$|[\s.,;:)!?])", "<blank_quoted>", wording)
    wording = re.sub(
        r"""(?<!\w)(['"])(stereotype|class|relation|property|null|string)\1""",
        r"\2",
        wording,
    )
    wording = re.sub(r"""(?<!\w)(?:'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*")(?=$|[\s.,;:)!?])""", "<quoted>", wording)
    wording = " ".join(wording.split())

    global_disqualifiers = (
        r"\b(?:if|whether|unless|when|whenever)\b[^.!?;]*\bstereotype\b",
        r"\b(?:may|might|could)\s+(?:be|have|contain|fail)\b",
        r"\b(?:may|might|could)\s+or\s+(?:may|might|could)\s+not\b",
        r"\bnot\s+(?:malformed|invalid|empty|blank|whitespace(?:-only)?|non[- ]?string)\b",
        r"\b(?:missing|absent|unrecognized)\s+stereotype\b",
        r"\bstereotype(?:\s+(?:field|value))?\s+(?:is|was)\s+(?:explicitly\s+)?(?<!non-)(?<!non )(?:null|none|absent|missing|omitted|unrecognized|recognized|valid|allowed|accepted)\b",
        r"\b(?:null|absent|missing)\s+or\s+(?:empty|blank|malformed|invalid|non[- ]?string)\b",
        r"\b(?:empty|blank|malformed|invalid|non[- ]?string)\s+or\s+(?:null|absent|missing)\b",
        r"\bdatatype[- ]valued\b|\brequires\s+(?:an?\s+)?(?:owl:)?object[- ]?propert(?:y|ies)\b",
        r"\b(?:name|description|languagestring|project\s+languages|generalizations|categorizer|cardinality|propertytype)\b",
    )
    if any(re.search(pattern, wording) for pattern in global_disqualifiers):
        return set()

    has_stereotype_context = (
        "stereotype" in wording
        or any((getattr(src, "path", "") or "").endswith(".stereotype") for src in sources)
    )
    if not has_stereotype_context:
        return set()

    bad_adj = r"(?:malformed|invalid(?:\s+type)?|non[- ]?string(?:\s+value)?|empty|blank|whitespace(?:-only)?)"
    bad_type = r"(?:int(?:eger)?|float|number|bool(?:ean)?|array|list|object|dict(?:ionary)?|<blank_quoted>)"
    patterns = (
        re.compile(rf"(?<!\bnot\s)(?<!\bno\s)(?<!\bnever\s)\b{bad_adj}\s+(?:or\s+{bad_adj}\s+)?stereotype\b"),
        re.compile(rf"\bstereotype(?:\s+(?:field|value))?(?:\s+(?:<quoted>|<value>))?\s+(?:is|was)\s+(?:(?:a|an)\s+)?(?:{bad_adj}|{bad_type}|not\s+(?:a|an)\s+(?:valid\s+|non[- ]?empty\s+|non[- ]?whitespace\s+)?(?:json\s+)?string)\b"),
        re.compile(rf"\b(?:has|had|with)\s+(?:a|an)?\s*{bad_adj}(?:\s+or\s+{bad_adj})?\s+stereotype\b"),
        re.compile(r"\bstereotype(?:\s+(?:field|value))?\b[^.!?;]*(?:must|should|expected(?:\s+to)?)\s+be\b[^.!?;]*(?:got|found|received)\b"),
        re.compile(rf"\bstereotype(?:\s+(?:field|value))?\b[^.!?;]*\b(?:cannot|must\s+not)\s+be\s+(?:{bad_adj}|{bad_type})\b"),
    )
    for clause in re.split(r"[.!?;]+", wording):
        clause = clause.strip()
        if not clause:
            continue
        if re.search(r"\b(?:is|was)\s+(?:valid|allowed|accepted|recognized)\b", clause) and not re.search(r"\bnot\s+(?:valid|allowed|accepted|recognized)\b", clause):
            continue
        if any(p.search(clause) for p in patterns):
            return {"malformed_stereotype"}
    return set()


def malformed_stereotype_diagnostic(message: str, sources: tuple = ()) -> frozenset[str]:
    """Return recognized RD-02 malformed-stereotype ERROR facts for harness checks."""
    return frozenset(_malformed_stereotype_facts(message, sources))


_BOOLEAN_FLAG_NAMES = (
    "isabstract", "isderived", "isextensional", "ispowertype",
    "isreadonly", "isordered", "iscomplete", "isdisjoint",
)


def _malformed_boolean_flag_facts(message: str, sources: tuple = ()) -> set[str]:
    """Read affirmative RD-02 malformed Boolean-flag ERROR wording.

    Rejects internal/deferred guard wording, conditionals, hedges, negations,
    bare expectations, valid/null/absent/true/false statements, UNKNOWN_INFORMATION
    unrecognized-field wording, and unrelated carrier/container subjects.
    """
    wording = message.casefold().replace("`", "").replace("’", "'")
    if re.search(
        r"\b(?:unexpected internal|not implemented|unimplemented|outside the decided baseline"
        r"|outside bi-w1|outside this increment|remains (?:unspecified|deferred|outside)"
        r"|(?:has|have) no assigned (?:baseline )?mapping)\b",
        wording,
    ):
        return set()
    wording = re.sub(r"\bcan't\b", "cannot", wording)
    wording = re.sub(r"n't\b", " not", wording)
    while re.search(r"\[[^\[\]]*\]", wording):
        wording = re.sub(r"\[[^\[\]]*\]", "<value>", wording)
    while re.search(r"\{[^{}]*\}", wording):
        wording = re.sub(r"\{[^{}]*\}", "<value>", wording)
    wording = re.sub(r"(?<!\w)(?:''|\"\"|'\s+'|\"\s+\")(?=$|[\s.,;:)!?])", "<blank_quoted>", wording)
    wording = re.sub(
        rf"""(?<!\w)(['"])({'|'.join(_BOOLEAN_FLAG_NAMES)}|class|relation|property|generalizationset|null|bool|boolean)\1""",
        r"\2",
        wording,
    )
    wording = re.sub(r"""(?<!\w)(?:'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*")(?=$|[\s.,;:)!?])""", "<quoted>", wording)
    wording = " ".join(wording.split())

    flag_alt = "|".join(_BOOLEAN_FLAG_NAMES)
    global_disqualifiers = (
        rf"\b(?:if|whether|unless|when|whenever)\b[^.!?;]*\b(?:{flag_alt}|boolean|flag)\b",
        r"\b(?:may|might|could)\s+(?:be|have|contain|fail)\b",
        r"\b(?:may|might|could)\s+or\s+(?:may|might|could)\s+not\b",
        r"\bnot\s+(?:malformed|invalid|non[- ]?bool(?:ean)?)\b",
        rf"\b(?:{flag_alt}|boolean\s+(?:flag|field)|flag)(?:\s+(?:field|value))?\s+(?:is|was)\s+(?:explicitly\s+)?(?<!non-)(?<!non )(?:null|none|absent|missing|omitted|true|false|valid|allowed|accepted|preserved)\b",
        r"\b(?:null|absent|missing|valid)\s+or\s+(?:malformed|invalid|non[- ]?bool(?:ean)?)\b",
        r"\b(?:malformed|invalid|non[- ]?bool(?:ean)?)\s+or\s+(?:null|absent|missing|valid)\b",
        r"\b(?:unrecognized|unknown|unexpected|undefined|unsupported)\s+(?:input\s+)?fields?\b",
        r"\bnot\s+(?:a\s+)?(?:defined|recognized|supported)\s+(?:boolean\s+)?(?:flag|field)\b",
        r"\bpreserved as an annotation\b",
        r"\b(?:stereotype|name|description|languagestring|project\s+languages|generalizations|categorizer|cardinality|propertytype|package\.contents|class\.properties|class\.literals|relation\.properties)\b",
    )
    if any(re.search(pattern, wording) for pattern in global_disqualifiers):
        return set()

    has_flag_context = (
        bool(re.search(rf"\b(?:{flag_alt})\b", wording))
        or bool(re.search(r"\bboolean\s+(?:flag|field)\b", wording))
        or any(
            (getattr(src, "path", "") or "").casefold().endswith(tuple("." + f for f in _BOOLEAN_FLAG_NAMES))
            for src in sources
        )
    )
    if not has_flag_context:
        return set()

    flag_subj = rf"(?:(?:{flag_alt})(?:\s+(?:boolean\s+)?(?:flag|field|value))?|boolean\s+(?:flag|field)(?:\s+value)?)"
    bad_adj = r"(?:malformed|invalid(?:\s+type)?|non[- ]?bool(?:ean)?(?:\s+value)?)"
    bad_type = r"(?:str(?:ing)?|int(?:eger)?|float|number|array|list|object|dict(?:ionary)?|<blank_quoted>|<quoted>|<value>)"
    patterns = (
        re.compile(rf"(?<!\bnot\s)(?<!\bno\s)(?<!\bnever\s)\b{bad_adj}\s+(?:or\s+{bad_adj}\s+)?{flag_subj}\b"),
        re.compile(rf"\b{flag_subj}(?:\s+(?:<quoted>|<value>))?\s+(?:is|was)\s+(?:(?:a|an)\s+)?(?:{bad_adj}|{bad_type}|not\s+(?:a|an)\s+(?:valid\s+)?(?:json\s+)?bool(?:ean)?)\b"),
        re.compile(rf"\b(?:has|had|with)\s+(?:a|an)?\s*{bad_adj}(?:\s+or\s+{bad_adj})?\s+{flag_subj}\b"),
        re.compile(rf"\b{flag_subj}\b[^.!?;]*(?:must|should|expected(?:\s+to)?)\s+be\b[^.!?;]*(?:got|found|received)\s+(?!null\b|none\b|bool(?:ean)?\b|true\b|false\b)\S+"),
        re.compile(rf"\b{flag_subj}\b[^.!?;]*\b(?:cannot|must\s+not)\s+be\s+(?:{bad_adj}|{bad_type})\b"),
    )
    for clause in re.split(r"[.!?;]+", wording):
        clause = clause.strip()
        if not clause:
            continue
        if re.search(r"\b(?:is|was)\s+(?:valid|allowed|accepted|preserved)\b", clause) and not re.search(r"\bnot\s+(?:valid|allowed|accepted|preserved)\b", clause):
            continue
        if any(p.search(clause) for p in patterns):
            return {"malformed_boolean_flag"}
    return set()


def malformed_boolean_flag_diagnostic(message: str, sources: tuple = ()) -> frozenset[str]:
    """Return recognized RD-02 malformed-boolean-flag ERROR facts for harness checks."""
    return frozenset(_malformed_boolean_flag_facts(message, sources))


def _malformed_class_order_facts(message: str, sources: tuple = ()) -> set[str]:
    """Read affirmative RD-02 malformed Class.order ERROR wording.

    Rejects internal/deferred guard wording, conditionals, hedges, negations,
    bare expectations, valid/null/absent/string statements, UNKNOWN_INFORMATION
    unrecognized-field wording, ORDERING_ANNOTATION property-ordering wording,
    and unrelated carrier/container/flag subjects.
    """
    wording = message.casefold().replace("`", "").replace("’", "'")
    if re.search(
        r"\b(?:unexpected internal|not implemented|unimplemented|outside the decided baseline"
        r"|outside bi-w1|outside this increment|remains (?:unspecified|deferred|outside)"
        r"|(?:has|have) no assigned (?:baseline )?mapping)\b",
        wording,
    ):
        return set()
    wording = re.sub(r"\bcan't\b", "cannot", wording)
    wording = re.sub(r"n't\b", " not", wording)
    wording = re.sub(r"\bclass\.order\b", "class order", wording)
    while re.search(r"\[[^\[\]]*\]", wording):
        wording = re.sub(r"\[[^\[\]]*\]", "<value>", wording)
    while re.search(r"\{[^{}]*\}", wording):
        wording = re.sub(r"\{[^{}]*\}", "<value>", wording)
    wording = re.sub(r"(?<!\w)(?:''|\"\"|'\s+'|\"\s+\")(?=$|[\s.,;:)!?])", "<blank_quoted>", wording)
    wording = re.sub(
        r"""(?<!\w)(['"])(class order|classifier order|order|class|null|str|string)\1""",
        r"\2",
        wording,
    )
    wording = re.sub(r"""(?<!\w)(?:'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*")(?=$|[\s.,;:)!?])""", "<quoted>", wording)
    wording = " ".join(wording.split())

    global_disqualifiers = (
        r"\b(?:if|whether|unless|when|whenever)\b[^.!?;]*\border\b",
        r"\b(?:may|might|could)\s+(?:be|have|contain|fail)\b",
        r"\b(?:may|might|could)\s+or\s+(?:may|might|could)\s+not\b",
        r"\bnot\s+(?:malformed|invalid|non[- ]?string)\b",
        r"\border(?:\s+(?:field|value))?\s+(?:is|was)\s+(?:explicitly\s+)?(?<!non-)(?<!non )(?:null|none|absent|missing|omitted|a\s+(?:json\s+)?str(?:ing)?|valid|allowed|accepted|preserved)\b",
        r"\b(?:null|absent|missing|valid)\s+or\s+(?:malformed|invalid|non[- ]?string)\b",
        r"\b(?:malformed|invalid|non[- ]?string)\s+or\s+(?:null|absent|missing|valid)\b",
        r"\b(?:unrecognized|unknown|unexpected|undefined|unsupported)\s+(?:input\s+)?fields?\b",
        r"\bnot\s+(?:a\s+)?(?:defined|recognized|supported)\s+(?:class\s+)?field\b",
        r"\bvalue\s+order\s+is\s+not\s+represented\b",
        r"\bpreserved\s+as\s+an\s+annotation\b",
        rf"\b(?:stereotype|name|description|languagestring|project\s+languages|generalizations|categorizer|cardinality|propertytype|package\.contents|class\.properties|class\.literals|relation\.properties|{'|'.join(_BOOLEAN_FLAG_NAMES)})\b",
    )
    if any(re.search(pattern, wording) for pattern in global_disqualifiers):
        return set()

    has_order_locator = any(
        (getattr(src, "path", "") or "").casefold().endswith(".order") for src in sources
    )
    has_order_context = bool(re.search(r"\b(?:(?:class|classifier)\s+)?order\b", wording)) or has_order_locator
    if not has_order_context:
        return set()

    order_subj = r"(?:(?:(?:class|classifier)\s+)?order(?:\s+(?:field|value))?)"
    bad_adj = r"(?:malformed|invalid(?:\s+type)?|non[- ]?string(?:\s+value)?)"
    bad_type = r"(?:int(?:eger)?|float|number|bool(?:ean)?|array|list|object|dict(?:ionary)?|<blank_quoted>|<quoted>|<value>)"
    patterns = (
        re.compile(rf"(?<!\bnot\s)(?<!\bno\s)(?<!\bnever\s)\b{bad_adj}\s+(?:or\s+{bad_adj}\s+)?{order_subj}\b"),
        re.compile(rf"\b{order_subj}(?:\s+(?:<quoted>|<value>))?\s+(?:is|was)\s+(?:(?:a|an)\s+)?(?:{bad_adj}|{bad_type}|not\s+(?:a|an)\s+(?:valid\s+)?(?:json\s+)?str(?:ing)?)\b"),
        re.compile(rf"\b(?:has|had|with)\s+(?:a|an)?\s*{bad_adj}(?:\s+or\s+{bad_adj})?\s+{order_subj}\b"),
        re.compile(rf"\b{order_subj}\b[^.!?;]*\b(?:has|had)\s+(?:a|an)?\s*(?:{bad_adj}|wrong\s+type)\b"),
        re.compile(rf"\b{order_subj}\b[^.!?;]*(?:must|should|expected(?:\s+to)?)\s+be\b[^.!?;]*(?:got|found|received)\s+(?!null\b|none\b|str(?:ing)?\b)\S+"),
        re.compile(rf"\b{order_subj}\b[^.!?;]*\b(?:cannot|must\s+not)\s+be\s+(?:{bad_adj}|{bad_type})\b"),
    )
    locator_pattern = re.compile(rf"(?<!\bnot\s)(?<!\bno\s)(?<!\bnever\s)\b{bad_adj}\b")
    for clause in re.split(r"[.!?;]+", wording):
        clause = clause.strip()
        if not clause:
            continue
        if re.search(r"\b(?:is|was)\s+(?:valid|allowed|accepted|preserved)\b", clause) and not re.search(r"\bnot\s+(?:valid|allowed|accepted|preserved)\b", clause):
            continue
        if any(p.search(clause) for p in patterns) or (has_order_locator and locator_pattern.search(clause)):
            return {"malformed_class_order"}
    return set()


def malformed_class_order_diagnostic(message: str, sources: tuple = ()) -> frozenset[str]:
    """Return recognized RD-02 malformed Class.order ERROR facts for harness checks."""
    return frozenset(_malformed_class_order_facts(message, sources))


def _observed_diagnostics(events, *, retain_unclassified=False):
    """Read inspected production fields; retain every event and its raw object.

    Uninterpreted events fail explicitly. Facts below come only from the
    actual message/effect and source locators, never from an input or request.
    """
    observed = []
    for event in events:
        wording = (event.message + " " + event.effect).casefold()
        facts = dkgm_chain_facts(event.message, event.effect)
        kind = _DIAGNOSTIC_KINDS.get(event.code)
        if event.severity == "ERROR":
            hierarchy_conditions = {condition for condition, _ in _hierarchy_condition_claims(event.message)}
            if hierarchy_conditions & {"mixed_set", "mixed_edge"}:
                facts.add("mixed_class_relation_hierarchy")
                if kind is None:
                    kind = "mixed_class_relation_hierarchy"
            if "nonbinary_relation" in hierarchy_conditions:
                facts.add("relation_properties_non_binary")
                if kind is None:
                    kind = "failed_relation"
            if "unresolved_general_reference" in hierarchy_conditions:
                facts.add("unresolved_general_reference")
                if kind is None:
                    kind = "failed_relation_generalization"
        if event.severity == "ERROR" and _nonclassifier_hierarchy_claim(event.message):
            facts.add("nonclassifier_hierarchy_endpoint")
            if kind is None:
                kind = "nonclassifier_hierarchy_endpoint"
        membership_facts = _generalization_membership_facts(event.message) if event.severity == "ERROR" else set()
        if membership_facts:
            facts.update(membership_facts)
            if kind is None:
                kind = "unusable_generalization_membership"
        categorizer_facts = (_unusable_categorizer_facts(event.message)
                             if event.severity == "ERROR" and event.code != "INTERNAL_TRANSFORMATION_FAILURE"
                             else set())
        if categorizer_facts:
            facts.update(categorizer_facts)
            if kind is None:
                kind = "unusable_categorizer"
        rel_categorizer_facts = (_inapplicable_relation_categorizer_facts(event.message)
                                 if event.severity == "ERROR" and event.code != "INTERNAL_TRANSFORMATION_FAILURE"
                                 else set())
        if rel_categorizer_facts:
            facts.update(rel_categorizer_facts)
            if kind is None:
                kind = "inapplicable_relation_categorizer"
        attr_type_facts = (_unresolved_attribute_type_facts(event.message)
                           if event.severity == "ERROR" and event.code != "INTERNAL_TRANSFORMATION_FAILURE"
                           else set())
        if attr_type_facts:
            facts.update(attr_type_facts)
            if kind is None:
                kind = "unresolved_attribute_type"
        elif kind == "unresolved_attribute_type":
            facts.add("unresolved_attribute_type")
        if (event.severity == "ERROR" and event.code != "INTERNAL_TRANSFORMATION_FAILURE"
                and absent_attribute_property_type_diagnostic(event.message)):
            facts.add("absent_attribute_property_type")
            if kind is None:
                kind = "absent_attribute_property_type"
        owner_missing_facts = (_attribute_owner_without_local_class_facts(event.message, event.effect)
                               if event.severity == "ERROR" and event.code != "INTERNAL_TRANSFORMATION_FAILURE"
                               else set())
        if owner_missing_facts:
            facts.update(owner_missing_facts)
            if kind is None:
                kind = "attribute_owner_without_local_class"
        if event.code != "INTERNAL_TRANSFORMATION_FAILURE":
            rel_kind, rel_facts = _rd02_datatype_relation_facts(event.severity, event.message, event.effect)
            if rel_facts:
                facts.update(rel_facts)
                if kind is None:
                    kind = rel_kind
            mixed_kind, mixed_facts = _rd02_mixed_kind_facts(event.severity, event.message, event.effect)
            if mixed_facts:
                facts.update(mixed_facts)
                if kind is None:
                    kind = mixed_kind
            if event.severity == "ERROR":
                rel_prop_facts = _relation_properties_container_facts(event.message)
                if rel_prop_facts:
                    facts.update(rel_prop_facts)
                    if kind is None:
                        kind = "failed_relation"
        _structural_skip = {
            "INTERNAL_TRANSFORMATION_FAILURE", "UNKNOWN_INFORMATION", "DUPLICATE_SOURCE_ID",
            "MISSING_STEREOTYPE", "UNRECOGNIZED_STEREOTYPE", "MISSING_SOURCE_ID",
            "INVALID_SOURCE_ID", "UNPROCESSABLE_DOCUMENT", "AMBIGUOUS_PROJECT_LANGUAGE",
        }
        if event.severity == "ERROR" and event.code not in _structural_skip:
            cls_prop_facts = _class_properties_container_facts(event.message)
            if cls_prop_facts:
                facts.update(cls_prop_facts)
                if kind is None:
                    kind = "malformed_class_properties"
            non_enum_facts = _non_enum_literals_facts(event.message)
            if non_enum_facts:
                facts.update(non_enum_facts)
                if kind is None:
                    kind = "invalid_non_enumeration_literals"
            pkg_entry_facts = _package_contents_entry_facts(event.message, event.sources)
            if pkg_entry_facts:
                facts.update(pkg_entry_facts)
                if kind is None:
                    kind = "invalid_package_contents_entry"
            proj_lang_facts = _project_languages_facts(event.message)
            if proj_lang_facts:
                facts.update(proj_lang_facts)
                if kind is None:
                    kind = "malformed_project_languages"
            textual_facts = _textual_carrier_facts(event.message, event.sources)
            if textual_facts:
                facts.update(textual_facts)
                if kind is None:
                    kind = "malformed_textual_carrier"
            stereo_facts = _malformed_stereotype_facts(event.message, event.sources)
            if stereo_facts:
                facts.update(stereo_facts)
                if kind is None:
                    kind = "malformed_stereotype"
            flag_facts = _malformed_boolean_flag_facts(event.message, event.sources)
            if flag_facts:
                facts.update(flag_facts)
                if kind is None:
                    kind = "malformed_boolean_flag"
            order_facts = _malformed_class_order_facts(event.message, event.sources)
            if order_facts:
                facts.update(order_facts)
                if kind is None:
                    kind = "malformed_class_order"
        if kind is None:
            if (event.severity == "ERROR" and
                    (re.search(r"\bpackage\b", event.message, re.I)
                     or any(source.element_type == "Package" for source in event.sources)) and
                    re.search(r"\bcontents\b", event.message, re.I)):
                kind = "malformed_package_contents"
        if kind is None:
            if not facts and not retain_unclassified:
                raise ImplementationUnavailable(f"Diagnostic interpretation not bound: {event.code}")
            kind = "dkgm_chain_omission" if facts else "unclassified"
        if event.code in {"RELATION_NAMING", "UNMAPPED_RELATION_STEREOTYPE"}:
            # Interpret each meaning in the bound native rendering. One
            # message/effect can report both, regardless of its primary code.
            if re.search(r"\bsource-target (?:naming|fallback) (?:is |was )?used\b", wording):
                facts.add("source_target_naming")
            if re.search(r"\bsemantics are (?:only )?partially (?:translated|represented)\b", wording):
                facts.add("residual_relation_semantics")
            if not facts and "target-end role supplies its lexical name" not in wording:
                raise ImplementationUnavailable(
                    f"Relation warning meaning needs interpretation: {event.message!r}"
                )
        if event.code == "MISSING_CLASS_NAME":
            # The inspected producer uses repr() for both the opaque ID and
            # supplied stereotype. Read the reported literal, never the source
            # fixture or a presumed default; quoted delimiters may occur in IDs.
            quoted = r"""(?:'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*")"""
            match = re.fullmatch(
                rf"Class {quoted}, stereotype (?P<stereotype>{quoted}|None), "
                r"has no usable (?:name-based IRI name|source name)\.",
                event.message,
            )
            if match is None:
                raise ImplementationUnavailable(
                    f"Class naming diagnostic wording needs interpretation: {event.message!r}"
                )
            stereotype = literal_eval(match.group("stereotype"))
            if stereotype is not None:
                facts.add("stereotype:" + stereotype)
        if "aborted" in event.effect.casefold():
            facts.add("conversion_aborted")
        if event.code == "METADATA_INPUT" and "all external metadata omitted" in event.effect.casefold():
            facts.add("external_metadata_omitted")
        if event.code == "DUPLICATE_SOURCE_ID" and len(event.sources) >= 2 and "competing declarations" in wording:
            facts.add("competing_declarations")
        if "preserved as an annotation" in wording:
            facts.add("preserved_as_annotation")
        if "not additionally enforced" in wording:
            facts.add("not_logically_enforced")
        if "missing descriptive name" in wording:
            facts.add("missing_name")
        if event.code == "PLACEHOLDER_BASE":
            if "placeholder namespace" in wording:
                facts.add("placeholder_namespace")
            if "not recommended for publication" in wording:
                facts.add("not_recommended_for_publication")
        if event.code == "SINGLETON_COMPLETENESS":
            if "extensionally equivalent" in wording or "extensions equivalent" in wording:
                facts.add("extensional_equivalence")
            if "identifiers remain distinct" in wording:
                facts.add("distinct_identifiers")
        if event.code == "RELATION_SET_COMPLETENESS" and "coverage is not represented" in wording:
            facts.add("coverage_not_represented")
        if event.code == "ORDERING_ANNOTATION" and "value order is not represented" in wording:
            facts.add("ordering_not_represented")
        if event.code == "VOID_DATATYPE":
            if "void" in wording: facts.add("void")
            if "without a range" in wording: facts.add("range_omitted")
        if event.code == "MATERIAL_CHAIN_COMPATIBILITY":
            effect = event.effect.casefold()
            if "does not guarantee owl 2 dl" in wording or "owl 2 dl conformance is not guaranteed" in wording:
                facts.add("not_dl_guarantee")
            if "omission policy applied" in effect:
                facts.add("omission_policy_applied")
            if "omitted affected" in effect:
                if "cardinality restrictions" in effect: facts.add("cardinalities_omitted")
                if "property-disjointness axioms" in effect: facts.add("property_disjointness_omitted")
            if "constraints preserved" in effect:
                facts.add("constraints_preserved")
            if "may place the output outside owl 2 dl" in wording:
                facts.add("possible_owl_dl_incompatibility")
        if event.code == "MATERIAL_CHAIN_AMBIGUITY":
            if "multiple matching" in wording:
                facts.add("ambiguous_correspondence")
            if "same-class material endpoints cannot be assigned uniquely" in wording:
                facts.add("same_class_occurrences_unassigned")
        if event.code == "DISCARDED_INSTANTIATION_INFORMATION":
            msg = event.message.casefold()
            eff = event.effect.casefold()
            if "association identifier" in msg:
                facts.add("discarded_identifier")
            if "association name" in msg:
                facts.add("discarded_association_name")
            if "role names" in msg:
                facts.add("discarded_role_names")
            if "multiplicities" in msg:
                facts.add("discarded_multiplicities")
            if "association-level characteristics" in msg or "association description" in msg:
                facts.add("discarded_characteristics")
            if "no association or property resource" in eff or "not materialized" in eff:
                facts.add("association_data_not_materialized")
        if event.code == "AMBIGUOUS_PROJECT_LANGUAGE":
            if "multiple project languages" in wording:
                facts.add("multiple_project_languages")
            if "unresolved" in wording:
                facts.add("language_unresolved")
        if event.code == "UNSUPPORTED_RELATION_CONNECTOR":
            if "no accepted mapping" in wording:
                facts.add("no_accepted_endpoint_mapping")
        ids = tuple(source.identifier for source in event.sources if source.identifier is not None)
        observed.append(Diagnostic(
            event.severity, kind, event.message + " " + event.effect,
            source_ids=ids,
            source_types=tuple(source.element_type for source in event.sources if source.element_type is not None),
            generated_iris=() if event.generated_iri is None else (event.generated_iri,),
            facts=frozenset(facts), raw=event, identified_sources=ids,
            code=event.code,
        ))
    return tuple(observed)


def _delivery_provenance(result):
    """Read deliverable metadata from the native ontology or separate graph."""
    import yaml
    from rdflib.namespace import DCTERMS, OWL, PROV, RDF

    graph = result.provenance if result.provenance is not None else result.ontology
    if graph is None:
        return {}
    roots = set(result.ontology.subjects(RDF.type, OWL.Ontology))
    activities = {activity for root in roots for activity in graph.objects(root, PROV.wasGeneratedBy)}
    configurations = {entity for activity in activities for entity in graph.objects(activity, PROV.used)
                      if list(graph.objects(entity, PROV.value))}
    outputs = {entity for root in roots for entity in graph.subjects(DCTERMS.isFormatOf, root)}
    values = {literal for entity in configurations for literal in graph.objects(entity, PROV.value)}
    if len(values) > 1:
        raise ImplementationUnavailable("Interpret multiple native output configuration literals")
    literal = next(iter(values), None)
    settings = {} if literal is None else yaml.safe_load(str(literal))
    if not isinstance(settings, dict):
        raise ImplementationUnavailable("Read the actual native configuration YAML mapping")
    triples = tuple(triple for entity in outputs for triple in graph.triples((entity, None, None)))
    schema_name = URIRef("https://schema.org/name")
    filenames = {str(value) for _, predicate, value in triples if predicate == schema_name}
    formats = {str(value) for _, predicate, value in triples if predicate == DCTERMS.format}
    if len(filenames) > 1 or len(formats) > 1:
        raise ImplementationUnavailable("Interpret multiple native output artifact names or formats")
    media_type = next(iter(formats), None)
    return dict(provenance_roles={"configuration": tuple(configurations), "output": tuple(outputs)},
                configuration_controls=settings, configuration_literal=literal,
                output_artifact_output=triples, output_artifact_evidence=triples,
                output_filename=next(iter(filenames), None),
                output_format="turtle" if media_type == "text/turtle" else media_type,
                embedded_output_configuration=tuple(
                    (key, value) for key, value in settings.items()
                    if key == "output" or key.startswith(("output_", "destination", "ontology_file"))
                ) if result.provenance_mode == "embedded" else ())


class _DirectKGInvocation(_UnboundInvocation):
    """Bind native calls and observations; no transformation rules live here."""

    def convert(self, source, *, options, workdir, faults=()):
        transformation_fault = _transformation_fault(faults)
        provenance_fault = faults == (Fault("provenance", "construct"),)
        if faults and not (transformation_fault or provenance_fault):
            self._unavailable()
        try:
            from ontouml_directkg import ConfigurationError, convert
        except ImportError as exc:
            raise ImplementationUnavailable("Install the actual DirectKG package before conversion tests") from exc
        request = dict(options)
        if "stereotype_relation_naming" in request:
            value = request.pop("stereotype_relation_naming")
            request["no_stereotype_relation_naming"] = (not value) if type(value) is bool else value
        if "dkgm_vocabulary" in request:
            try:
                inspect.signature(convert).bind(source, **request)
            except TypeError as exc:
                raise ImplementationUnavailable("Bind the public Python DKGM vocabulary mode control") from exc
        # Observe real input/report-writer calls for explicit persistence checks;
        # no input option is used to infer that a report was or was not written.
        with _observe_metadata_output() as metadata, _observe_python_input() as trace:
            injection = (_fail_relation_emission(trace) if transformation_fault == "emit_relations" else
                         _fail_result_construction(trace) if transformation_fault == "result_construction" else
                         _force_escaped_id_collision(transformation_fault, trace) if transformation_fault else
                         _fail_required_provenance(trace) if provenance_fault else nullcontext())
            try:
                with injection:
                    result = convert(source, **request)
            except ConfigurationError as exc:
                observed = _BasicObservation(None, None, (), configuration_error=exc)
            else:
                observed = _MetadataPythonObservation(
                    result.ontology, result.outcome, _observed_diagnostics(
                        result.diagnostics, retain_unclassified=bool(transformation_fault)),
                    native=result, provenance=result.provenance,
                    external_metadata_output=_captured_metadata(metadata, result.ontology))
        if trace is not None:
            extra = ({"external_metadata_output": observed.external_metadata_output}
                     if observed.native is not None else {})
            cls = _InputObservedMetadataPython if extra else _InputObservedPython
            if provenance_fault and observed.native is not None:
                cls = _ProvenanceObservedPython
                extra["operations"] = tuple(Operation("provenance", "construct", None, True, call)
                                            for call in trace["provenance_probe"]["calls"])
            return cls(observed.ontology, observed.outcome, observed.diagnostics,
                configuration_error=observed.configuration_error, native=observed.native,
                provenance=None if observed.native is None else observed.provenance,
                conversion_started=trace["conversion_started"], execution_trace=trace,
                diagnostics_exports=tuple(trace["diagnostics_exports"]), **extra)
        return observed

    def inspect_controls(self):
        """Inspect actions and parameters, and ask the native enum validators."""
        from ontouml_directkg import ConfigurationError, __version__, convert
        from ontouml_directkg.cli import build_parser

        signature = inspect.signature(convert)
        parser = build_parser()
        actions = {flag: action for action in parser._actions for flag in action.option_strings}
        negated = "no_stereotype_relation_naming"

        def semantic_value(name, value):
            return not value if name == negated and isinstance(value, bool) else value

        cli = {}
        python = {}
        rejections = {}
        for flag, action in actions.items():
            choices = None if action.choices is None else tuple(action.choices)
            if action.nargs == 0 and type(action.const) is type(action.default) is bool:
                choices = (action.default, action.const)
            cli[flag] = Control(flag, choices, semantic_value(action.dest, action.default), action,
                                arity=1 if action.nargs is None else action.nargs)

        # These are the enumerated parameters of the inspected Python API.
        # Obtain accepted values from its own validator, independently of CLI choices.
        enumerated = {"iri_strategy", "input_policy", "stereotype_policy", "inverse_properties",
                      "relation_labels", "material_property_chains", "dkgm_vocabulary", "provenance"}
        with TemporaryDirectory() as directory:
            absent_source = Path(directory) / "absent.json"
            for parameter in signature.parameters.values():
                if parameter.name == "source":
                    continue
                name = "stereotype_relation_naming" if parameter.name == negated else parameter.name
                python_choices = None
                if parameter.annotation is bool:
                    python_choices = (False, True)
                elif parameter.name in enumerated:
                    # A wrong-type rejection would leave string validation unchecked.
                    try:
                        convert(absent_source, **{parameter.name: "unsupported"})
                    except ConfigurationError as exc:
                        match = re.fullmatch(rf"Invalid {parameter.name}: expected one of (.+)", str(exc))
                        if not match:
                            raise ImplementationUnavailable(f"Interpret Python choices for {name}") from exc
                        python_choices = tuple(match[1].split(", "))
                        rejections[name] = exc
                    else:
                        raise AssertionError(f"Python accepted an unsupported string for {name}")
                    for choice in python_choices:
                        convert(absent_source, **{parameter.name: choice})
                python[name] = Control(parameter.name, python_choices,
                                       semantic_value(parameter.name, parameter.default), parameter)
        prohibited = {
            "ontology_iri": {"ontology_iri"},
            "local_value_restrictions": {"local_value_restrictions", "all_values_from"},
            "omit_reverse_cardinalities": {"omit_reverse_cardinalities", "no_reverse_cardinalities"},
            "qualified_relation_cardinalities": {"qualified_relation_cardinalities"},
        }
        observed_names = {"cli": {f.lstrip("-").replace("-", "_") for f in actions}
                          | {action.dest for action in actions.values()}, "python": set(signature.parameters)}
        features = {f"{interface}:{feature}": bool(names & aliases)
                    for interface, names in observed_names.items() for feature, aliases in prohibited.items()}
        output_action = actions.get("--output")
        stdout_supported = not (
            output_action is not None
            and getattr(output_action, "required", False) is True
            and "-o" in output_action.option_strings
            and "--output" in output_action.option_strings
            and not any(flag in actions for flag in ("--stdout", "-"))
        )
        return _InspectedControlSurface(cli, python, features, software_version=__version__,
                                        stdout_supported=stdout_supported,
                                        raw={"python_signature": signature, "cli_help": parser.format_help(),
                                             "python_enum_rejections": rejections})

    def attempt_source_input(self, source, *, options, workdir):
        try:
            result = self.convert(source, options=options, workdir=workdir)
        except (TypeError, ValueError, OSError) as exc:
            return SourceInputAttempt(rejection=exc)
        return SourceInputAttempt(observation=result)

    def inspect_source_input_surface(self):
        """Closed interpretation of inspected native interfaces, not a feature guess.

        Every currently exported name, conversion parameter and CLI action has
        been inspected below. Unfamiliar additions require interpretation; they
        cannot earn absence credit through spelling heuristics. This is not an
        expected public API whitelist: unknown surfaces raise unavailability,
        rather than assert that an independently accepted control is forbidden.
        """
        import inspect
        import ontouml_directkg
        from ontouml_directkg.cli import build_parser
        exports = tuple(ontouml_directkg.__all__)
        known_exports = {"ConfigurationError", "ConversionResult", "Diagnostic", "DiagnosticsExportError",
                         "SourceLocation", "convert", "DeliveryFailure", "DeliveryResult", "__version__"}
        signature = inspect.signature(ontouml_directkg.convert)
        known_parameters = {"source", "base_iri", "iri_strategy", "input_policy", "stereotype_policy",
                            "language", "omit_identifiers", "inverse_properties", "no_stereotype_relation_naming",
                            "relation_labels", "material_property_chains", "provenance", "metadata_file",
                            "ontology_version_iri", "dkgm_vocabulary"}
        parser = build_parser()
        known_flags = {"-h", "--help", "-o", "--output", "--version", "--base-iri", "--iri-strategy",
                       "--input-policy", "--stereotype-policy", "--inverse-properties",
                       "--no-stereotype-relation-naming", "--relation-labels", "--material-property-chains",
                       "--language", "--omit-identifiers", "--metadata-file", "--provenance",
                       "--diagnostics-file", "--console-level", "--ontology-version-iri", "--dkgm-vocabulary"}
        actions = tuple(parser._actions)
        unknown = (set(exports) - known_exports) | (set(signature.parameters) - known_parameters)
        unknown.update(flag for action in actions for flag in action.option_strings if flag not in known_flags)
        unknown.update(action.dest for action in actions if not action.option_strings and action.dest != "input")
        unknown.update(name for name, parameter in signature.parameters.items()
                       if parameter.kind in {parameter.VAR_POSITIONAL, parameter.VAR_KEYWORD})
        if unknown:
            raise ImplementationUnavailable(f"Interpret new public source/checksum surface before absence credit: {sorted(unknown)!r}")
        return SourceInputSurface((), {"exports": exports, "python_signature": signature,
                                      "cli_actions": actions, "cli_help": parser.format_help()})

    def read_source_artifacts(self, graph):
        """Current producer marks actually used JSON artifacts by their MIME format.

        This role reading is implementation knowledge, not a required RDF
        template or a role inferred from requested paths/checksums.
        """
        from rdflib.namespace import DCTERMS, PROV, RDF
        return tuple({artifact for activity in graph.subjects(RDF.type, PROV.Activity)
                      for artifact in graph.objects(activity, PROV.used)
                      if (artifact, DCTERMS.format, Literal("application/json")) in graph})

    def read_diagnostics(self, observation):
        native_trace = vars(observation).get("execution_trace") or {}
        return _observed_diagnostics(observation.native.diagnostics,
                                     retain_unclassified="transformation_failure" in native_trace)

    def read_outcome(self, observation):
        return observation.native.outcome

    def read_ontology(self, observation):
        return observation.native.ontology

    def read_provenance(self, observation):
        return observation.native.provenance

    def serialize(self, observation, *, target, faults=()):
        """Read the native result's public Turtle serialization."""
        applicable = {
            ("ontology", "serialize"), ("ontology", "encode"),
            ("provenance", "serialize"), ("provenance", "encode"),
        }
        if any((fault.kind, fault.operation) not in applicable or fault.kind != target for fault in faults):
            self._unavailable()
        method = {"ontology": "to_turtle", "provenance": "to_provenance_turtle"}[target]
        serializer = getattr(observation.native, method, None)
        if not callable(serializer):
            raise ImplementationUnavailable(f"Bind the public Python {target} serializer")
        graph_attr = "ontology" if target == "ontology" else "provenance"
        graph_obj = getattr(observation.native, graph_attr, None)
        fault = faults[0] if faults else None
        patch_ctx = nullcontext()
        if fault is not None and graph_obj is not None:
            if fault.operation == "serialize":
                def fail_serialize(*args, **kwargs):
                    raise ValueError("Cyclic RDF list")
                patch_ctx = patch.object(graph_obj, "serialize", fail_serialize)
            elif fault.operation == "encode":
                def fail_encode(*args, **kwargs):
                    raise UnicodeEncodeError("utf-8", "\ud800", 0, 1, "surrogates not allowed")
                patch_ctx = patch.object(graph_obj, "serialize", fail_encode)
        try:
            with patch_ctx:
                turtle = serializer()
            data = turtle.encode("utf-8")
        except (ValueError, RuntimeError, UnicodeEncodeError) as exc:
            return SerializationObservation(data=None, failure=exc)
        return SerializationObservation(data=data)

    def deliver(self, observation, *, output_path, faults=()):
        """Call real delivery while observing its write and serialization boundaries."""
        from ontouml_directkg import delivery

        native = observation.native
        destination = Path(output_path)
        sidecar = destination.with_name(destination.stem + ".provenance.ttl")
        targets = {"ontology": destination, "sidecar": sidecar, "provenance": sidecar}
        applicable = {("ontology", "create"), ("ontology", "write"),
                      ("ontology", "serialize"), ("ontology", "encode"), ("ontology", "unexpected"),
                      ("sidecar", "create"), ("sidecar", "write"),
                      ("sidecar", "serialize"), ("sidecar", "encode"), ("sidecar", "unexpected"),
                      ("provenance", "output_construct")}
        if any((fault.kind, fault.operation) not in applicable or
               (fault.path is not None and fault.path != targets[fault.kind]) for fault in faults):
            self._unavailable()
        before_io = None
        operations = []
        real_write = delivery._write_artifact
        real_open = delivery.tempfile.NamedTemporaryFile
        real_serialize = native.to_provenance_turtle
        real_output_provenance = delivery.execution_provenance.output_provenance
        serialization_fault = next((fault for fault in faults if fault.kind == "ontology"
                                    and fault.operation in {"serialize", "encode"}), None)
        probe = _OntologySerializationProbe(serialization_fault.operation) if serialization_fault else None

        def observe_operation(kind, operation, path):
            for fault in faults:
                if (kind, operation) == (fault.kind, fault.operation):
                    error = (RuntimeError(f"Unexpected runtime error during {kind} delivery")
                             if operation == "unexpected"
                             else OSError(f"Injected {kind} {operation} failure"))
                    operations.append(Operation(kind, operation, path, True, error))
                    raise error

        @contextmanager
        def open_observed(kind, path, *args, **kwargs):
            observe_operation(kind, "create", path)
            with real_open(*args, **kwargs) as stream:
                real_stream_write = stream.write

                def write_observed(*args, **kwargs):
                    observe_operation(kind, "write", path)
                    return real_stream_write(*args, **kwargs)

                with patch.object(stream, "write", write_observed):
                    yield stream

        def write_artifact(path, content):
            nonlocal before_io
            if before_io is None and native.ontology is not None:
                before_io = Graph() + native.ontology
            kind = "ontology" if path == destination else "sidecar" if path == sidecar else None
            if kind is None:
                raise ImplementationUnavailable(f"Interpret the native artifact write to {path}")
            observe_operation(kind, "unexpected", path)
            with patch.object(delivery.tempfile, "NamedTemporaryFile",
                              lambda *args, **kwargs: open_observed(kind, path, *args, **kwargs)):
                return real_write(path, content)

        def serialize_sidecar():
            observe_operation("sidecar", "serialize", sidecar)
            result_str = real_serialize()
            if any((f.kind, f.operation) == ("sidecar", "encode") for f in faults):
                class UnencodableSidecar(str):
                    def encode(text, *args, **kwargs):
                        try:
                            return super().encode(*args, **kwargs)
                        except UnicodeEncodeError as error:
                            operations.append(Operation("sidecar", "encode", sidecar, True, error))
                            raise
                return UnencodableSidecar(result_str + "\ud800")
            return result_str

        def failing_output_provenance(*args, **kwargs):
            if any((f.kind, f.operation) == ("provenance", "output_construct") for f in faults):
                error = RuntimeError("RD04-OUTPUT-PROVENANCE-272")
                operations.append(Operation("provenance", "output_construct", sidecar, True, error))
                raise error
            return real_output_provenance(*args, **kwargs)

        with patch.object(delivery, "_write_artifact", write_artifact), \
             patch.object(native, "to_provenance_turtle", serialize_sidecar), \
             patch.object(delivery.execution_provenance, "output_provenance", failing_output_provenance):
            if probe is None:
                delivered = native.deliver(destination)
            else:
                probe.capture(native)
                with patch.object(native, "to_turtle", lambda: probe.serialize(native)):
                    delivered = native.deliver(destination)
                before_io = probe.before
                operations.extend(Operation("ontology", probe.operation, destination, True, error)
                                  for error in probe.calls)
        failures = tuple(DeliveryFailure(item.kind, item.destination, item.reason, item,
                                         item.old_file_not_updated) for item in delivered.failures)
        fields = {**vars(observation), **_delivery_provenance(delivered.conversion)}
        fields.setdefault("external_metadata_output", None)
        fields.update(ontology=delivered.conversion.ontology, provenance=delivered.conversion.provenance,
                      provenance_mode=delivered.conversion.provenance_mode,
                      outcome=delivered.conversion.outcome, native=delivered.conversion,
                      diagnostics=_observed_diagnostics(
                          delivered.conversion.diagnostics, retain_unclassified=probe is not None or
                          "transformation_failure" in (vars(observation).get("execution_trace") or {})),
                      delivery_failures=failures, operations=tuple(operations), pre_delivery_ontology=before_io,
                      valid_artifacts=tuple(path for path in (delivered.ontology_path, delivered.provenance_path)
                                            if path is not None))
        return DeliveryObservation(_PythonDeliveryObservation(**fields), failures[0] if failures else None)

    def read_property_stereotype_comments(self, observation):
        """Recognize the native English property-stereotype comment renderings."""
        from rdflib.namespace import RDFS
        non_boundary = (
            r"OntoUML (?:class|attribute|relation|source association end|target association end) "
            r"(?:isAbstract|isDerived): (?:true|false)\.",
            r"OntoUML source metadata: (?:this attribute|the (?:source|target) association end) "
            r"(?:is read-only|is ordered|has (?:shared|composite) aggregation)\.",
        )
        boundary = re.compile(
            r"Declared OntoUML property stereotype(?: on the (source|target) association end)?: (begin|end)\."
        )
        meanings = []
        for subject, literal in self.read_ontology(observation).subject_objects(RDFS.comment):
            if isinstance(literal, Literal):
                match = boundary.fullmatch(str(literal))
                if match:
                    end, stereotype = match.groups()
                    context = f"{end}_end" if end else "attribute"
                    meanings.append(CommentMeaning(subject, literal, "stereotype", stereotype,
                                                   context=context, english=True))
                    continue
                if any(re.fullmatch(pattern, str(literal)) for pattern in non_boundary):
                    continue
            raise ImplementationUnavailable(
                "RD-18 comment meaning is not bound for this observed RDF statement; "
                f"inspect and adapt its actual wording: {(subject, RDFS.comment, literal)!r}"
            )
        return tuple(meanings)

    def read_relation_limitation_source_ids(self, observation, source):
        """Interpret reported ID locators against the actual supplied document.

        The inspected native residual-warning renderer reports relation IDs.
        Resolve only those actually reported locators, never all declarations
        or an expected affected element. Preserve consolidation without an
        event count requirement. Other locator/rendering forms need binding
        when inspectable; their absence cannot earn invented condition coverage.
        """
        from tests.support.data import source_elements
        declarations = {}
        for element in source_elements(json.loads(Path(source).read_bytes())):
            identifier = element.get('id')
            if isinstance(identifier, str):
                declarations.setdefault(identifier, []).append(element)
        reported = set()
        for event in self.read_diagnostics(observation):
            if 'residual_relation_semantics' not in event.facts or event.severity != 'WARNING':
                continue
            identified = event.identified_sources or event.source_ids
            relation_ids = set()
            for identifier in identified:
                matches = declarations.get(identifier, ())
                if len(matches) != 1:
                    raise ImplementationUnavailable('Residual-warning source locator is not unambiguously bound')
                element = matches[0]
                if element.get('type') == 'Relation' and isinstance(element.get('stereotype'), str):
                    relation_ids.add(identifier)
            if not relation_ids:
                raise ImplementationUnavailable('This actual residual warning has no interpretable relation locator')
            reported.update(relation_ids)
        return frozenset(reported)

    def read_relation_stereotype_annotations(self, observation, source):
        """Reuse the inspected producer's RDF audit for RD-17's settled relations.

        The current writer emits no declaration annotations for these stereotypes.
        The existing audit reads every actual triple, source text and known flag
        form. Unknown output raises unavailability; no empty evidence is assumed.
        Positive declaration forms remain unbound until actually inspectable.
        """
        return self.read_historical_dependence_annotations(observation, source)

    def read_historical_dependence_annotations(self, observation, source):
        """Audit the current producer's actual annotation forms for absence.

        No historical-dependence annotation is currently produced. Recognize
        source descriptions from the actual input and inspected independent
        flag wording, not a search for the stereotype's spelling. Audit other
        RDF predicates as well, so an unfamiliar annotation/auxiliary structure
        cannot silently earn an empty result. Positive/unknown forms remain
        unavailable until their actual meanings can be inspected and bound.
        Property labels/identifiers are checked directly by the topical
        assertions. Class labels need actual source-name evidence; class typing
        alone never classifies a label as independent of the stereotype.
        Unfamiliar class/auxiliary labels remain explicitly unavailable.
        """
        from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, XSD

        descriptions, names, identifiers = set(), set(), set()
        def read_descriptions(value):
            if isinstance(value, dict):
                if isinstance(value.get("id"), str): identifiers.add(value["id"])
                name = value.get("name")
                if isinstance(name, str): names.add(name)
                elif isinstance(name, dict): names.update(name.values())
                description = value.get("description")
                if isinstance(description, str): descriptions.add(description)
                elif isinstance(description, dict): descriptions.update(description.values())
                for key, child in value.items():
                    if key != "propertyAssignments": read_descriptions(child)
            elif isinstance(value, list):
                for child in value: read_descriptions(child)
        read_descriptions(json.loads(Path(source).read_bytes()))
        flag_forms = (
            r"OntoUML (?:class|attribute|relation|source association end|target association end) "
            r"(?:isAbstract|isDerived): (?:true|false)\.",
            r"OntoUML source metadata: (?:this attribute|the (?:source|target) association end) "
            r"(?:is read-only|is ordered|has (?:shared|composite) aggregation)\.",
            r"Declared OntoUML property stereotype(?: on the (?:source|target) association end)?: (?:begin|end)\.",
        )
        logical = {RDFS.domain, RDFS.range, RDFS.subClassOf, RDFS.subPropertyOf,
                   OWL.inverseOf, OWL.equivalentClass, OWL.equivalentProperty,
                   OWL.disjointWith, OWL.propertyDisjointWith, OWL.onProperty,
                   OWL.cardinality, OWL.minCardinality, OWL.maxCardinality,
                   OWL.qualifiedCardinality, OWL.minQualifiedCardinality, OWL.maxQualifiedCardinality,
                   OWL.onClass, OWL.onDataRange, OWL.someValuesFrom, OWL.allValuesFrom,
                   OWL.hasValue, OWL.hasSelf, OWL.unionOf, OWL.intersectionOf, OWL.complementOf,
                   OWL.oneOf, OWL.members, OWL.distinctMembers, OWL.propertyChainAxiom,
                   RDF.first, RDF.rest, OWL.imports}
        types = {OWL.Ontology, OWL.Class, OWL.ObjectProperty, OWL.DatatypeProperty,
                 OWL.Restriction, OWL.AsymmetricProperty, OWL.IrreflexiveProperty,
                 OWL.ReflexiveProperty, OWL.SymmetricProperty, OWL.TransitiveProperty,
                 OWL.FunctionalProperty, OWL.InverseFunctionalProperty, OWL.NamedIndividual,
                 OWL.AllDifferent, OWL.AllDisjointClasses, OWL.AllDisjointProperties}
        graph = self.read_ontology(observation)
        for triple in graph:
            subject, predicate, obj = triple
            if predicate in logical:
                continue
            if predicate == DCTERMS.identifier and isinstance(obj, Literal) and str(obj) in identifiers:
                continue
            if predicate == RDFS.label and isinstance(obj, Literal):
                if str(obj) in names or any((subject, RDF.type, kind) in graph
                                           for kind in (OWL.ObjectProperty, OWL.DatatypeProperty)):
                    continue
            if predicate == RDF.type and obj in types:
                continue
            if (predicate in {DCTERMS.created, DCTERMS.modified}
                    and isinstance(obj, Literal) and obj.datatype == XSD.dateTime):
                continue
            if predicate == RDFS.comment and isinstance(obj, Literal):
                if str(obj) in descriptions or any(re.fullmatch(pattern, str(obj)) for pattern in flag_forms):
                    continue
            raise ImplementationUnavailable(
                "Historical-dependence annotation interpretation is not bound for this actual RDF statement: "
                f"{triple!r}"
            )
        return ()

    def read_relation_aggregation_comments(self, observation, source):
        # Reuse the inspected producer's annotation audit: unknown wording,
        # predicates and auxiliary structures cannot earn absence credit.
        # It excludes actual source descriptions, not expected fixture values.
        self.read_historical_dependence_annotations(observation, source)
        from rdflib.namespace import RDFS
        comments = []
        for subject, literal in self.read_ontology(observation).subject_objects(RDFS.comment):
            match = re.fullmatch(
                r"OntoUML source metadata: the (source|target) association end "
                r"has (shared|composite) aggregation\.", str(literal))
            if match:
                comments.append(CommentMeaning(subject, literal, "aggregationKind",
                    match[2].upper(), context=match[1] + "_end"))
        return tuple(comments)

    def export_diagnostics(self, observation, path, *, faults=()):
        applicable = {
            ("diagnostics", "create"), ("diagnostics", "write"),
            ("diagnostics", "serialize"), ("diagnostics", "unexpected"),
        }
        target = Path(path)
        if any((fault.kind, fault.operation) not in applicable or
               (fault.path is not None and fault.path != target) for fault in faults):
            self._unavailable()
        from ontouml_directkg import DiagnosticsExportError
        from ontouml_directkg import diagnostics as diag_mod
        operations = []
        patch_ctx = nullcontext()
        if faults:
            fault = faults[0]
            if fault.operation in {"create", "write"}:
                real_write_bytes = Path.write_bytes
                def failing_write_bytes(self_path, data):
                    if self_path == target:
                        err = OSError(errno.EACCES, "Injected diagnostics write failure", str(target))
                        operations.append(Operation("diagnostics", fault.operation, target, True, err))
                        raise err
                    return real_write_bytes(self_path, data)
                patch_ctx = patch.object(Path, "write_bytes", failing_write_bytes)
            else:
                def failing_json_dumps(*args, **kwargs):
                    err = (TypeError("Injected diagnostics JSON serialization failure")
                           if fault.operation == "serialize" else RuntimeError("Unexpected diagnostics export error"))
                    operations.append(Operation("diagnostics", fault.operation, target, True, err))
                    raise err
                patch_ctx = patch.object(diag_mod.json, "dumps", failing_json_dumps)
        try:
            with patch_ctx:
                observation.native.export_diagnostics(path)
        except (DiagnosticsExportError, OSError, TypeError, ValueError, RuntimeError) as exc:
            fields = dict(vars(observation))
            fields["operations"] = tuple(operations)
            fields.setdefault("external_metadata_output", None)
            fields.setdefault("delivery_failures", ())
            fields.setdefault("valid_artifacts", ())
            fields.setdefault("pre_delivery_ontology", None)
            fields.setdefault("provenance_roles", None)
            fields.setdefault("configuration_controls", None)
            fields.setdefault("configuration_literal", None)
            fields.setdefault("output_artifact_output", None)
            fields.setdefault("output_artifact_evidence", None)
            fields.setdefault("output_filename", None)
            fields.setdefault("output_format", None)
            fields.setdefault("embedded_output_configuration", None)
            fields.setdefault("provenance_mode", None)
            return DeliveryObservation(_PythonDeliveryObservation(**fields),
                                       DeliveryFailure("diagnostics", target, str(exc), exc))
        return DeliveryObservation(observation)

    def report_content(self, observation):
        result = observation.native
        return ReportContent(result.outcome, tuple(_native_diagnostic_fields(result.diagnostics)), result)

    def cli_report_content(self, process):
        trace = process.execution_trace
        if (not isinstance(trace, dict) or trace.get("conversion_calls") != 1
                or trace.get("conversion_returns") != 1
                or not {"conversion_report", "native_report"} <= trace.keys()):
            raise ImplementationUnavailable("Complete same-execution native CLI report evidence is unavailable")
        snapshots = []
        for key in ("conversion_report", "native_report"):
            actual = trace[key]
            events = tuple((event[0], event[1], event[2], event[3], tuple(tuple(source) for source in event[4]), event[5])
                           for event in actual["events"])
            snapshots.append(ReportContent(actual["outcome"], events, trace))
        return tuple(snapshots)

    def read_report(self, path):
        from ontouml_directkg.diagnostics import Diagnostic as NativeDiagnostic, SourceLocation, export_report
        payload = json.loads(Path(path).read_bytes())
        # Unknown members are compatible extensions. Retain the complete raw
        # payload while interpreting only the inspected native fields.
        events = tuple(NativeDiagnostic(
                           **{name: entry[name] for name in ("severity", "code", "message", "effect", "generated_iri")},
                           sources=tuple(SourceLocation(**{name: source[name] for name in ("path", "identifier", "element_type")})
                                         for source in entry["sources"]))
                       for entry in payload["diagnostics"])
        # The actual shared writer and its actual dataclasses are the inspected
        # report-format definition, not an invented JSON schema identifier.
        return ReportObservation(payload, _observed_diagnostics(events), (payload["outcome"],),
                                 schema=(export_report, NativeDiagnostic, SourceLocation))

    def diagnostic_mirror_records(self, process, report):
        """T1: compare real captured events with independently read report events.

        The inspected CLI's info threshold displays every produced diagnostic.
        Its current renderer prints the native code/message/effect, source
        locators and generated IRI. Reconstruct that presentation only for the
        reported events; the produced side reads captured bytes exclusively.
        A renderer change needs a binding update, not a new expected message.
        Filtered console output cannot establish complete production evidence.
        """
        from ontouml_directkg.cli import build_parser
        from ontouml_directkg.diagnostics import Diagnostic as NativeDiagnostic

        if process.command[1:3] != ("-m", "ontouml_directkg"):
            raise ImplementationUnavailable("Interpret this CLI command before diagnostic mirroring")
        threshold = build_parser().parse_args(process.command[3:]).console_level
        if threshold != "info":
            raise ImplementationUnavailable("Complete diagnostic mirroring requires unfiltered console evidence")
        produced = Counter(event.raw["data"] for event in process.console)
        reported = Counter()
        for event in report.diagnostics:
            native = event.raw
            if not isinstance(native, NativeDiagnostic):
                raise ImplementationUnavailable("Interpret this report event before diagnostic mirroring")
            context = "; ".join(
                f"{source.element_type or 'source'} {source.identifier or ''} at {source.path}"
                for source in native.sources
            )
            record = (
                f"[{native.severity}] {native.code}: {native.message} {native.effect}"
                + (" Sources: " + context if context else "")
                + (" Generated IRI: " + native.generated_iri if native.generated_iri else "")
                + "\n"
            )
            # The inspected Python CLI's stderr escapes unencodable source
            # identifiers; retain that observed presentation for invalid IDs.
            reported[record.encode("utf-8", errors="backslashreplace")] += 1
        return produced, reported

    def cli(self, source, *, options, workdir, output_path=None, diagnostics_path=None, extra_args=(), faults=()):
        serialization_fault = (faults[0] if len(faults) == 1 and faults[0].kind == "ontology"
                               and faults[0].operation in {"serialize", "encode"}
                               and (faults[0].path is None or faults[0].path == output_path) else None)
        transformation_fault = _transformation_fault(faults)
        provenance_fault = faults == (Fault("provenance", "construct"),)
        supported_cli_faults = {
            ("provenance", "output_construct"),
            ("ontology", "unexpected"),
            ("sidecar", "encode"), ("sidecar", "unexpected"),
            ("diagnostics", "create"), ("diagnostics", "write"),
            ("diagnostics", "serialize"), ("diagnostics", "unexpected"),
            ("stdout", "write"), ("stdout", "encode"), ("stdout", "flush"),
            ("stdout", "write_unexpected"), ("stdout", "flush_unexpected"),
            ("stderr", "write"), ("stderr", "encode"), ("stderr", "flush"),
            ("stderr", "write_unexpected"), ("stderr", "flush_unexpected"),
            ("runtime", "pre_conversion"), ("runtime", "parser_setup"), ("runtime", "post_delivery"),
        }
        new_cli_faults = tuple(
            f for f in faults
            if (f.kind, f.operation) in supported_cli_faults
        )
        all_new_handled = bool(faults) and len(new_cli_faults) == len(faults)
        # Also allow combined ontology/sidecar/diagnostics/console faults where ontology serialize/encode is combined
        if not all_new_handled and faults and not (serialization_fault or transformation_fault or provenance_fault):
            # Check if faults are a mix of ontology serialize/encode and supported_cli_faults
            ont_ser = [f for f in faults if f.kind == "ontology" and f.operation in {"serialize", "encode"}]
            rest = tuple(f for f in faults if f not in ont_ser)
            if len(ont_ser) <= 1 and rest and all((f.kind, f.operation) in supported_cli_faults for f in rest):
                serialization_fault = ont_ser[0] if ont_ser else None
                new_cli_faults = rest
                all_new_handled = True
        sidecar_path = (Path(output_path).with_name(Path(output_path).stem + ".provenance.ttl")
                        if output_path is not None else None)
        def shared_identity(artifact):
            if artifact is None or diagnostics_path is None:
                return False
            try:
                return Path(diagnostics_path).samefile(artifact)
            except OSError:
                return False

        shared_output = shared_identity(output_path)
        shared_sidecar = options.get("provenance") == "sidecar" and shared_identity(sidecar_path)
        allow_existing_output = bool(faults and any(f.kind in {"ontology", "sidecar", "provenance", "diagnostics"} for f in faults)) or (
            output_path is not None and Path(output_path).is_symlink()
        ) or shared_output
        allow_existing_diag = bool(faults and any(f.kind == "diagnostics" for f in faults)) or (
            diagnostics_path is not None and (
                Path(diagnostics_path).is_symlink()
                or (output_path is not None and Path(output_path).is_symlink())
                or (sidecar_path is not None and sidecar_path.is_symlink())
            )
        ) or shared_output or shared_sidecar
        if ((faults and not (serialization_fault or transformation_fault or provenance_fault or all_new_handled))
                or extra_args
                or (output_path is not None and not allow_existing_output and Path(output_path).exists())
                or (diagnostics_path is not None and not allow_existing_diag and Path(diagnostics_path).exists())):
            self._unavailable()
        command = [sys.executable, "-m", "ontouml_directkg"]
        if source is not None:
            command.append(str(source))
        if output_path is not None:
            command.extend(["--output", str(output_path)])
        if diagnostics_path is not None:
            command.extend(["--diagnostics-file", str(diagnostics_path)])
        for name, value in options.items():
            if name == "stereotype_relation_naming":
                if not value:
                    command.append("--no-stereotype-relation-naming")
            elif name in {"omit_identifiers", "no_stereotype_relation_naming"}:
                if value:
                    command.append("--" + name.replace("_", "-"))
            else:
                command.extend(("--" + name.replace("_", "-"), str(value)))
        completed, trace = _run_observed_cli(
            command, workdir, ontology_fault=serialization_fault.operation if serialization_fault else None,
            transformation_fault=transformation_fault, provenance_fault=provenance_fault,
            cli_faults=new_cli_faults)
        started = trace["conversion_started"]
        has_runtime_fault = any(f.kind == "runtime" for f in new_cli_faults)
        has_console_fault = any(f.kind in {"stdout", "stderr"} for f in new_cli_faults)
        has_diag_fault = any(f.kind == "diagnostics" for f in new_cli_faults)
        has_late_prov_fault = any((f.kind, f.operation) == ("provenance", "output_construct") for f in new_cli_faults)
        has_delivery_fault = any(f.kind in {"ontology", "sidecar"} for f in new_cli_faults)
        if (completed.returncode == 2 and trace["parser_errors"] and not started) or (
                not started and (has_runtime_fault or has_console_fault or output_path is None)):
            # Actual native rejection or pre-conversion runtime failure has no conversion result.
            return _ReportProcess(tuple(command), completed.returncode, completed.stdout, completed.stderr,
                                  None, _observed_console(completed.stdout, completed.stderr),
                                  conversion_started=started, execution_trace=trace)
        if serialization_fault is not None:
            native = trace.get("native_report")
            if native is None or "ontology_serialization" not in trace:
                raise ImplementationUnavailable("Complete CLI file-serialization fault evidence is unavailable")
            observed = _SerializationFaultCLIObservation(None, native["outcome"], (), native=native)
            return _ReportProcess(tuple(command), completed.returncode, completed.stdout, completed.stderr,
                                  observed, _observed_console(completed.stdout, completed.stderr),
                                  conversion_started=started, execution_trace=trace)
        if transformation_fault:
            # Preserve the real status/console/trace if conversion raises instead of returning.
            return _ReportProcess(tuple(command), completed.returncode, completed.stdout, completed.stderr,
                                  None, _observed_console(completed.stdout, completed.stderr),
                                  conversion_started=started, execution_trace=trace)
        if (diagnostics_path is None or provenance_fault or has_late_prov_fault or has_diag_fault
                or has_delivery_fault or trace.get("report_io_errors") or trace.get("report_export_errors")
                or has_runtime_fault or (has_console_fault and not Path(diagnostics_path).is_file())
                or completed.returncode == 4):
            from ontouml_directkg import Diagnostic as NativeDiagnostic, SourceLocation

            # Keep the native result if no report was requested or filesystem
            # evidence shows that report delivery failed.
            if trace.get("conversion_calls") != 1 or trace.get("conversion_returns") != 1 or "native_report" not in trace:
                raise ImplementationUnavailable("Complete native CLI result evidence is unavailable")
            native = trace["native_report"]
            events = tuple(NativeDiagnostic(severity, code, message, effect,
                                            tuple(SourceLocation(*item) for item in sources), iri)
                           for severity, code, message, effect, sources, iri in native["events"])
            graph = (
                Graph().parse(output_path, format="turtle")
                if output_path is not None and Path(output_path).is_file()
                and not Path(output_path).is_symlink()
                and native["outcome"] != "aborted"
                and not has_delivery_fault and not has_late_prov_fault
                else None
            )
            observed = _NoReportCLIObservation(
                graph, native["outcome"], _observed_diagnostics(
                    events, retain_unclassified=bool(has_delivery_fault or trace.get("delivery_faults"))),
                native=native,
                diagnostics_exports=tuple(Path(item) for item in trace["diagnostics_exports"]))
            return _ReportProcess(tuple(command), completed.returncode, completed.stdout, completed.stderr,
                                  observed, _observed_console(completed.stdout, completed.stderr),
                                  conversion_started=started, execution_trace=trace)
        # Missing reports are a visible failure, never reconstructed by running
        # Python again, guessing an outcome or creating a hidden report.
        try:
            report = self.read_report(diagnostics_path)
        except FileNotFoundError as exc:
            exc.add_note(f"Real CLI status {completed.returncode}; processing started={started}; "
                         f"stderr={completed.stderr.decode('utf-8', errors='replace')}")
            raise
        graph = Graph().parse(output_path, format="turtle") if output_path is not None and Path(output_path).is_file() else None
        evidence = trace.get("metadata")
        if (not isinstance(evidence, dict) or type(evidence.get("entries")) is not int
                or evidence.get("entries") != evidence.get("returns") or evidence.get("active_frames") != 0
                or not isinstance(evidence.get("triples"), list) or (graph is not None and not evidence["entries"])):
            raise ImplementationUnavailable("Incomplete native CLI metadata-emission evidence")
        from rdflib.util import from_n3
        triples = tuple(tuple(from_n3(term) for term in triple) for triple in evidence["triples"])
        observed = _MetadataCLIObservation(graph, report.outcomes[0], report.diagnostics, native=report.raw,
                                          external_metadata_output=triples if graph is not None else ())
        return _ReportProcess(tuple(command), completed.returncode, completed.stdout, completed.stderr,
                              observed, _observed_console(completed.stdout, completed.stderr),
                              conversion_started=started, execution_trace=trace)


def get_invocation() -> Invocation:
    """Use real public file conversion; unbound capabilities still fail clearly."""
    return _DirectKGInvocation()
