"""Explicit artifact delivery and failures, separate from transformation outcomes."""

from dataclasses import dataclass
import os
from pathlib import Path
import tempfile
from typing import TYPE_CHECKING

from .diagnostics import Diagnostic, SourceLocation
from . import provenance as execution_provenance

if TYPE_CHECKING:
    from .conversion import ConversionResult


@dataclass(frozen=True)
class DeliveryFailure:
    kind: str
    destination: Path
    cause: Exception
    old_file_not_updated: bool | None

    @property
    def reason(self) -> str:
        return str(self.cause)


@dataclass(frozen=True)
class DeliveryResult:
    conversion: "ConversionResult"
    ontology_path: Path | None = None
    provenance_path: Path | None = None
    failures: tuple[DeliveryFailure, ...] = ()

    @property
    def successful(self) -> bool:
        return self.conversion.outcome != "aborted" and not self.failures


def _write_artifact(destination: Path, content: bytes) -> None:
    """Replace the destination only after a complete temporary write beside it."""
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="wb", dir=destination.parent,
                                         prefix=".directkg-", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(content)
        os.replace(temporary, destination)
    finally:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass


def _failure(result: "ConversionResult", kind: str, destination: Path,
              cause: Exception, old: bool | None) -> DeliveryFailure:
    retained = (" An older file remains at the destination and was not updated for this execution." if old
                else " Any existing file was not updated for this execution." if old is None else "")
    result.diagnostics += (Diagnostic(
        "ERROR", kind.upper() + "_DELIVERY", f"Cannot deliver {kind} to {destination}: {cause}.",
        "Requested artifact delivery failed; the transformation outcome and generated ontology graph are unchanged."
        + retained, (SourceLocation(str(destination), element_type=kind + " destination"),)),)
    return DeliveryFailure(kind, destination, cause, old)


def deliver(result: "ConversionResult", destination: Path) -> DeliveryResult:
    if result.outcome == "aborted":
        return DeliveryResult(result)
    content = result.to_turtle().encode("utf-8")
    sidecar_graph = None
    if result.provenance_mode == "sidecar":
        try:
            sidecar_graph = execution_provenance.output_provenance(result._provenance_record, destination, content)
        except Exception as exc:
            result._abort_provenance(exc)
            return DeliveryResult(result)
    old = None
    try:
        old = destination.is_file()
        _write_artifact(destination, content)
    except Exception as exc:
        return DeliveryResult(result, failures=(_failure(result, "ontology", destination, exc, old),))
    if sidecar_graph is None:
        return DeliveryResult(result, ontology_path=destination)
    result.provenance = sidecar_graph
    sidecar = destination.with_name(destination.stem + ".provenance.ttl")
    old = None
    try:
        old = sidecar.is_file()
        content = result.to_provenance_turtle().encode("utf-8")
        _write_artifact(sidecar, content)
    except Exception as exc:
        return DeliveryResult(result, ontology_path=destination,
                              failures=(_failure(result, "sidecar", sidecar, exc, old),))
    return DeliveryResult(result, ontology_path=destination, provenance_path=sidecar)
