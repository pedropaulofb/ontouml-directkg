"""Replaceable binding to REAL DirectKG interfaces.

The dataclasses below are a test-side observation format, not a proposed public
API. No production package, entry point or signature exists at the pinned
baseline. Replace ``get_invocation`` and implement this protocol when one exists.
Never populate observations from expected fixtures or implement mappings here.
"""

from dataclasses import dataclass, field
from collections import Counter
from pathlib import Path
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
        self, source: Path, *, options: Mapping[str, Any], workdir: Path
    ) -> Observation:
        """Execute the public library; options are TEST-side semantic controls.

        Omitted controls must stay omitted so tests can examine real defaults.
        Do not auto-export diagnostics or repair the source. Use workdir for
        temporary execution artifacts; never write in fixture directories.
        """
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
            "DirectKG integration unavailable: main at the inspected baseline "
            "contains no production Python implementation or verified public "
            "entry point. Bind tests/support/invocation.py to the real interface; "
            "do not substitute a transformer, skip, or xfail these assertions."
        )

    def convert(self, source, *, options, workdir):
        self._unavailable()

    def read_diagnostics(self, observation):
        self._unavailable()

    def read_outcome(self, observation):
        self._unavailable()

    def read_ontology(self, observation):
        self._unavailable()


def get_invocation() -> Invocation:
    """The only production-binding selection point; currently explicitly unbound."""
    return _UnboundInvocation()
