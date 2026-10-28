"""Replaceable binding to REAL DirectKG interfaces.

The dataclasses below are a test-side observation format, not a proposed public
API. The RD-02 binding below covers actual file conversion, public result reads
and fresh-file CLI JSON reports. Other capabilities remain explicitly unbound.
Never populate observations from expected fixtures or implement mappings here.
"""

from dataclasses import dataclass, field
from collections import Counter
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Mapping, Protocol

from rdflib import Graph, Literal, URIRef
from rdflib.term import Node


class ImplementationUnavailable(RuntimeError):
    """There is no verified production invocation to execute."""


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
    ``field`` uses the source field name, or ``stereotype`` for ``abstract``.
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
    observation: Observation
    console: tuple[Diagnostic, ...]
    # Observed conversion entry, from real instrumentation when needed; never
    # derive this solely from the expected exit code or configuration error.
    conversion_started: bool | None = None


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
    # Capabilities whose existence is not prescribed by a production signature.
    # Conditional input/stream assertions must not invent entry-point support.
    in_memory_input_supported: bool | None = None
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

    def convert_memory(self, source: Mapping[str, Any], *, options: Mapping[str, Any], workdir: Path, faults: tuple[Fault, ...] = ()) -> Observation:
        """Use an actual supported in-memory public entry, without inventing bytes."""
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

    def convert_memory(self, source, *, options, workdir, faults=()):
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

    def inspect_controls(self):
        self._unavailable()

    def read_diagnostics(self, observation):
        self._unavailable()

    def read_outcome(self, observation):
        self._unavailable()

    def read_ontology(self, observation):
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


class _ReportProcess(_BoundFieldsOnly, CLIObservation):
    _available_fields = frozenset({"command", "returncode", "stdout", "stderr", "observation", "console"})


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


_DIAGNOSTIC_KINDS = {
    "MISSING_SOURCE_ID": "missing_id", "INVALID_SOURCE_ID": "invalid_id",
    "FAILED_RELATION": "failed_relation", "DUPLICATE_SOURCE_ID": "duplicate_id",
    "UNTRANSFORMABLE_ENUMERATION_VALUE": "invalid_enumeration_value",
    "ABSTRACTNESS_ANNOTATION": "abstractness", "MISSING_CLASS_NAME": "missing_name",
    "MISSING_NAME": "missing_name", "GENERIC_ID_FALLBACK": "generic_id_fallback",
    "MISSING_STEREOTYPE": "missing_stereotype", "UNRECOGNIZED_STEREOTYPE": "unrecognized_stereotype",
    "UNKNOWN_INFORMATION": "unknown_information", "UNPROCESSABLE_DOCUMENT": "unprocessable_document",
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
        if "aborted" in event.effect.casefold():
            facts.add("conversion_aborted")
        if event.code == "DUPLICATE_SOURCE_ID" and len(event.sources) >= 2 and "competing declarations" in wording:
            facts.add("competing_declarations")
        if "preserved as an annotation" in wording:
            facts.add("preserved_as_annotation")
        if "not additionally enforced" in wording:
            facts.add("not_logically_enforced")
        if "missing descriptive name" in wording:
            facts.add("missing_name")
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
        try:
            result = convert(source, **request)
        except ConfigurationError as exc:
            return _BasicObservation(None, None, (), configuration_error=exc)
        return _BasicObservation(result.ontology, result.outcome, _observed_diagnostics(result.diagnostics), native=result)

    def read_diagnostics(self, observation):
        return _observed_diagnostics(observation.native.diagnostics)

    def read_outcome(self, observation):
        return observation.native.outcome

    def read_ontology(self, observation):
        return observation.native.ontology

    def read_report(self, path):
        from ontouml_directkg.diagnostics import Diagnostic as NativeDiagnostic, SourceLocation, export_report
        payload = json.loads(Path(path).read_bytes())
        events = tuple(NativeDiagnostic(**{**entry, "sources": tuple(SourceLocation(**s) for s in entry["sources"])})
                       for entry in payload["diagnostics"])
        # The actual shared writer and its actual dataclasses are the inspected
        # report-format definition, not an invented JSON schema identifier.
        return ReportObservation(payload, _observed_diagnostics(events), (payload["outcome"],),
                                 schema=(export_report, NativeDiagnostic, SourceLocation))

    def cli(self, source, *, options, workdir, output_path=None, diagnostics_path=None, extra_args=(), faults=()):
        if (faults or extra_args or source is None or output_path is None or diagnostics_path is None
                or Path(output_path).exists() or Path(diagnostics_path).exists()):
            self._unavailable()
        command = [sys.executable, "-m", "ontouml_directkg", str(source), "--output", str(output_path),
                   "--diagnostics-file", str(diagnostics_path)]
        for name, value in options.items():
            if name == "stereotype_relation_naming":
                if not value:
                    command.append("--no-stereotype-relation-naming")
            elif name in {"omit_identifiers", "no_stereotype_relation_naming"}:
                if value:
                    command.append("--" + name.replace("_", "-"))
            else:
                command.extend(("--" + name.replace("_", "-"), str(value)))
        completed = subprocess.run(command, cwd=workdir, capture_output=True, check=False)
        # Missing reports are a visible failure, never reconstructed by running
        # Python again, guessing an outcome or creating a hidden report.
        report = self.read_report(diagnostics_path)
        graph = Graph().parse(output_path, format="turtle") if Path(output_path).is_file() else None
        observed = _BasicObservation(graph, report.outcomes[0], report.diagnostics, native=report.raw)
        return _ReportProcess(tuple(command), completed.returncode, completed.stdout, completed.stderr,
                              observed, _observed_console(completed.stdout, completed.stderr))


def get_invocation() -> Invocation:
    """Use real public file conversion; unbound capabilities still fail clearly."""
    return _DirectKGInvocation()
