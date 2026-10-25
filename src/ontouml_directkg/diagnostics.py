"""Production diagnostics and explicit JSON export (DK-DIAG-04).

Code names and JSON keys are implementation representations, not additional
transformation requirements. The future CLI can use this same report writer.
"""

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Literal

Outcome = Literal["completed", "completed-with-errors", "aborted"]
Severity = Literal["INFO", "WARNING", "ERROR"]


@dataclass(frozen=True)
class SourceLocation:
    """An actual source declaration or container identified by its JSON path."""

    path: str
    identifier: str | None = None
    element_type: str | None = None


@dataclass(frozen=True)
class Diagnostic:
    """One produced diagnostic, including its reason, effect and source context."""

    severity: Severity
    code: str
    message: str
    effect: str
    sources: tuple[SourceLocation, ...] = ()
    generated_iri: str | None = None


class DiagnosticsExportError(OSError):
    """Explicit report-delivery failure; the conversion result remains usable."""

    def __init__(self, destination: Path, cause: OSError):
        self.destination = destination
        self.cause = cause
        super().__init__(f"Cannot write diagnostics to {destination}: {cause}")


class _AbortConversion(Exception):
    """Internal control flow after a diagnostic establishes an accepted abort."""


class DiagnosticCollector:
    """Retain every produced event; presentation never filters this collection."""

    def __init__(self) -> None:
        self.events: list[Diagnostic] = []

    def add(self, severity: Severity, code: str, message: str, effect: str,
            sources: tuple[SourceLocation, ...] = (),
            generated_iri: str | None = None) -> None:
        self.events.append(Diagnostic(severity, code, message, effect, sources, generated_iri))


def export_report(outcome: Outcome, events: tuple[Diagnostic, ...],
                  destination: str | Path) -> Path:
    """Write the actual outcome/events without changing them or conversion state.

    This operation is separate from conversion. OSError failures are exposed as
    DiagnosticsExportError, retaining the destination and original failure.
    """
    path = Path(destination)
    payload = {"outcome": outcome, "diagnostics": [asdict(event) for event in events]}
    data = (json.dumps(payload, ensure_ascii=True, indent=2) + "\n").encode("utf-8")
    try:
        path.write_bytes(data)
    except OSError as exc:
        raise DiagnosticsExportError(path, exc) from exc
    return path
