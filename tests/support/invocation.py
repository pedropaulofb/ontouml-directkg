"""Replaceable binding to REAL DirectKG interfaces.

The dataclasses below are a test-side observation format, not a proposed public
API. The RD-02 binding below covers actual file conversion, public result reads
and fresh-file CLI JSON reports. Other capabilities remain explicitly unbound.
Never populate observations from expected fixtures or implement mappings here.
"""

from ast import literal_eval
from dataclasses import dataclass, field
from collections import Counter
from contextlib import contextmanager, nullcontext
import json
import inspect
import os
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
from typing import Any, Mapping, Protocol

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

    kind: metadata, provenance, optional_enrichment, ontology, sidecar, diagnostics.
    operation: read, construct, serialize, create, write, enrich. Bind to an
    observed implementation operation or standard I/O, including child-process
    I/O for CLI cases. Do not implement a replacement transformation, pre-return
    expected outcomes, or add production fault hooks to satisfy this protocol.
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
                    tuple(sorted(event.source_types)), tuple(sorted(event.generated_iris)),
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

    def read_property_stereotype_comments(self, observation: Observation) -> tuple[CommentMeaning, ...]:
        """Read actual begin/end declaration meanings and their raw RDF literals.

        Association-end contexts must come from the actual comment, not the
        requested occurrence. Multiple meanings may share one combined literal.
        ``english`` records actual wording; no exact prose or mandatory @en
        spelling is prescribed. Unknown wording must remain unavailable.
        This test-side reader is not a production Python API.
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

    def read_property_stereotype_comments(self, observation):
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


class _MetadataCLIObservation(_BasicObservation):
    _available_fields = _BasicObservation._available_fields | {"external_metadata_output"}


class _VersionControlSurface(_BoundFieldsOnly, ControlSurface):
    _available_fields = frozenset({"cli", "python", "raw"})


class _ScopedControls(Mapping):
    """Bound lookups cannot imply a complete inventory or absent controls."""

    def __init__(self, controls):
        self._controls = controls

    def __getitem__(self, key):
        if key not in self._controls:
            raise ImplementationUnavailable(f"Control inspection {key!r} is not bound")
        return self._controls[key]

    def __iter__(self):
        raise ImplementationUnavailable("Complete control inventory is not bound")

    def __len__(self):
        raise ImplementationUnavailable("Complete control inventory is not bound")


class _ReportProcess(_BoundFieldsOnly, CLIObservation):
    _available_fields = frozenset({"command", "returncode", "stdout", "stderr", "observation", "console",
                                   "conversion_started", "execution_trace"})


class _ConsoleDiagnostic(_BoundFieldsOnly, Diagnostic):
    _available_fields = frozenset({"severity", "message", "raw"})


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
            events.append(_ConsoleDiagnostic(
                (match.group(1) or match.group(2)).decode("ascii").upper(),
                "console", raw.decode("utf-8", errors="replace"),
                raw={"stream": stream, "data": raw},
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


_CLI_OBSERVER = '''\
import argparse
import atexit
import json
import os
import sys
from ontouml_directkg.conversion import read_project

reader_code = read_project.__code__
parser_error_code = argparse.ArgumentParser.error.__code__
trace = {"input_reader": {"module": read_project.__module__, "name": read_project.__qualname__},
         "conversion_started": False, "parser_errors": []}
metadata = _MetadataCapture()

def observe(frame, event, argument):
    metadata.observe(frame, event, argument)
    if event == "call":
        if frame.f_code is reader_code:
            trace["conversion_started"] = True
        elif frame.f_code is parser_error_code:
            trace["parser_errors"].append(frame.f_locals["message"])

def finish():
    trace["profile_active_at_exit"] = sys.getprofile() is observe
    sys.setprofile(None)
    trace["observation_completed"] = True
    trace["metadata"] = {"entries": metadata.entries, "returns": metadata.returns,
                         "active_frames": len(metadata.frames),
                         "triples": [[term.n3() for term in triple] for triple in metadata.triples]}
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


def _run_observed_cli(command, workdir):
    """Observe the real -m CLI without replacing conversion or parser behavior.

    The inspected converter finishes configuration validation before calling
    its actual input reader. A standard Python profile hook observes that entry
    and native argparse rejection calls inside the same CLI execution. Startup
    and completion evidence are mandatory; no missing trace means 'not started'.
    Reader/renderer implementation knowledge stays in this replaceable binding.
    """
    with TemporaryDirectory(prefix="directkg-cli-observer-", dir=workdir) as directory:
        directory = Path(directory)
        (directory / "sitecustomize.py").write_text(inspect.getsource(_MetadataCapture) + "\n" + _CLI_OBSERVER,
                                                    encoding="utf-8")
        trace_path = directory / "execution.json"
        environment = dict(os.environ)
        environment["DIRECTKG_TEST_CLI_TRACE"] = str(trace_path)
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
}


def _observed_diagnostics(events):
    """Read inspected production fields; retain every event and its raw object.

    Unmapped diagnostic codes fail explicitly. Facts below come only from the
    actual message/effect and source locators, never from an input or request.
    """
    observed = []
    for event in events:
        if event.code not in _DIAGNOSTIC_KINDS:
            raise ImplementationUnavailable(f"Diagnostic interpretation not bound: {event.code}")
        wording = (event.message + " " + event.effect).casefold()
        facts = set()
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
        ids = tuple(source.identifier for source in event.sources if source.identifier is not None)
        observed.append(Diagnostic(
            event.severity, _DIAGNOSTIC_KINDS[event.code], event.message + " " + event.effect,
            source_ids=ids,
            source_types=tuple(source.element_type for source in event.sources if source.element_type is not None),
            generated_iris=() if event.generated_iri is None else (event.generated_iri,),
            facts=frozenset(facts), raw=event, identified_sources=ids,
        ))
    return tuple(observed)


class _DirectKGInvocation(_UnboundInvocation):
    """Minimal RD-02 wiring; no conversion, recovery or output rules live here."""

    def convert(self, source, *, options, workdir, faults=()):
        if faults:
            self._unavailable()
        try:
            from ontouml_directkg import ConfigurationError, convert
        except ImportError as exc:
            raise ImplementationUnavailable("Install the actual DirectKG package before conversion tests") from exc
        request = dict(options)
        if "stereotype_relation_naming" in request:
            request["no_stereotype_relation_naming"] = not request.pop("stereotype_relation_naming")
        # T5 verifies the real optional Python parameter, not an invented API.
        # Trace only this newly bound request; unrelated readers stay unbound.
        with _observe_metadata_output() as metadata, (
                _observe_python_input() if "ontology_version_iri" in request else nullcontext()) as trace:
            try:
                result = convert(source, **request)
            except ConfigurationError as exc:
                observed = _BasicObservation(None, None, (), configuration_error=exc)
            else:
                observed = _MetadataPythonObservation(
                    result.ontology, result.outcome, _observed_diagnostics(result.diagnostics),
                    native=result, provenance=result.provenance,
                    external_metadata_output=_captured_metadata(metadata, result.ontology))
        if trace is not None:
            extra = ({"external_metadata_output": observed.external_metadata_output}
                     if observed.native is not None else {})
            cls = _InputObservedMetadataPython if extra else _InputObservedPython
            return cls(observed.ontology, observed.outcome, observed.diagnostics,
                configuration_error=observed.configuration_error, native=observed.native,
                provenance=None if observed.native is None else observed.provenance,
                conversion_started=trace["conversion_started"], execution_trace=trace,
                diagnostics_exports=tuple(trace["diagnostics_exports"]), **extra)
        return observed

    def inspect_controls(self):
        """T5 binds only the version control; full-surface inspection stays open."""
        import inspect
        from ontouml_directkg import convert
        from ontouml_directkg.cli import build_parser

        signature = inspect.signature(convert)
        parameter = signature.parameters.get("ontology_version_iri")
        parser = build_parser()
        actions = [action for action in parser._actions if "--ontology-version-iri" in action.option_strings]
        if parameter is None or len(actions) != 1:
            raise ImplementationUnavailable("Interpret the current ontology-version-IRI public controls")
        action = actions[0]
        cli = Control("--ontology-version-iri", None if action.choices is None else tuple(action.choices),
                      action.default, action, arity=1 if action.nargs is None else action.nargs)
        python = Control(parameter.name, None, parameter.default, parameter)
        return _VersionControlSurface(
            _ScopedControls({cli.parameter: cli}), _ScopedControls({"ontology_version_iri": python}),
            {}, raw={"python_signature": signature, "cli_action": action, "cli_help": parser.format_help()})

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
                            "ontology_version_iri"}
        parser = build_parser()
        known_flags = {"-h", "--help", "-o", "--output", "--version", "--base-iri", "--iri-strategy",
                       "--input-policy", "--stereotype-policy", "--inverse-properties",
                       "--no-stereotype-relation-naming", "--relation-labels", "--material-property-chains",
                       "--language", "--omit-identifiers", "--metadata-file", "--provenance",
                       "--diagnostics-file", "--console-level", "--ontology-version-iri"}
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
        return _observed_diagnostics(observation.native.diagnostics)

    def read_outcome(self, observation):
        return observation.native.outcome

    def read_ontology(self, observation):
        return observation.native.ontology

    def read_property_stereotype_comments(self, observation):
        """Verified absence reader for the current, incomplete producer.

        Current production emits no boundary-stereotype comments. Audit actual
        RDF against its inspected non-boundary generated forms; never assume
        an empty result from source/request data. A new or unknown comment
        requires interpretation before it can earn positive/negative evidence.
        No proposed begin/end prose template is imposed here or by the tests.
        The existing all-comment meaning reader remains explicitly unbound.
        """
        from rdflib.namespace import RDFS
        non_boundary = (
            r"OntoUML (?:class|attribute|relation|source association end|target association end) "
            r"(?:isAbstract|isDerived): (?:true|false)\.",
            r"OntoUML source metadata: (?:this attribute|the (?:source|target) association end) "
            r"(?:is read-only|is ordered|has (?:shared|composite) aggregation)\.",
        )
        for subject, literal in self.read_ontology(observation).subject_objects(RDFS.comment):
            if not isinstance(literal, Literal) or not any(re.fullmatch(pattern, str(literal)) for pattern in non_boundary):
                raise ImplementationUnavailable(
                    "RD-18 comment meaning is not bound for this observed RDF statement; "
                    f"inspect and adapt its actual wording: {(subject, RDFS.comment, literal)!r}"
                )
        return ()

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

    def read_report(self, path):
        from ontouml_directkg.diagnostics import Diagnostic as NativeDiagnostic, SourceLocation, export_report
        payload = json.loads(Path(path).read_bytes())
        events = tuple(NativeDiagnostic(**{**entry, "sources": tuple(SourceLocation(**s) for s in entry["sources"])})
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
        if (faults or extra_args or output_path is None or diagnostics_path is None
                or Path(output_path).exists() or Path(diagnostics_path).exists()):
            self._unavailable()
        command = [sys.executable, "-m", "ontouml_directkg"]
        if source is not None:
            command.append(str(source))
        command.extend(["--output", str(output_path),
                        "--diagnostics-file", str(diagnostics_path)])
        for name, value in options.items():
            if name == "stereotype_relation_naming":
                if not value:
                    command.append("--no-stereotype-relation-naming")
            elif name in {"omit_identifiers", "no_stereotype_relation_naming"}:
                if value:
                    command.append("--" + name.replace("_", "-"))
            else:
                command.extend(("--" + name.replace("_", "-"), str(value)))
        completed, trace = _run_observed_cli(command, workdir)
        started = trace["conversion_started"]
        if completed.returncode == 2 and trace["parser_errors"] and not started:
            # Actual native rejection before input processing has no conversion
            # result. Do not require or manufacture a conversion-diagnostics file.
            return _ReportProcess(tuple(command), completed.returncode, completed.stdout, completed.stderr,
                                  None, _observed_console(completed.stdout, completed.stderr),
                                  conversion_started=started, execution_trace=trace)
        # Missing reports are a visible failure, never reconstructed by running
        # Python again, guessing an outcome or creating a hidden report.
        try:
            report = self.read_report(diagnostics_path)
        except FileNotFoundError as exc:
            exc.add_note(f"Real CLI status {completed.returncode}; processing started={started}; "
                         f"stderr={completed.stderr.decode('utf-8', errors='replace')}")
            raise
        graph = Graph().parse(output_path, format="turtle") if Path(output_path).is_file() else None
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
