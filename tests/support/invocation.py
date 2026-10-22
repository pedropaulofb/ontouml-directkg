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


def diagnostic_signatures(events):
    """Compare event meaning/multiplicity without imposing order or raw schema.

    The binding's semantic categories/facts must cover the actual event's
    meaning. Human wording and native object identity are not standardized.
    """
    return Counter((event.severity, event.kind, tuple(sorted(event.source_ids)),
                    tuple(sorted(event.source_types)), tuple(sorted(event.generated_iris)),
                    tuple(sorted(event.facts)), tuple(sorted(event.identified_sources))) for event in events)


class Invocation(Protocol):
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
