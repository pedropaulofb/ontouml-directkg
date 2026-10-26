"""OntoUML DirectKG's public Python conversion interface.

Conversion returns actual graphs, diagnostics and an explicit outcome. Embedded
provenance is the default; sidecar graphs and file delivery remain explicit.
Unresolved naming/recovery branches retain their development guards.
"""

from .conversion import ConversionResult, convert
from .diagnostics import Diagnostic, DiagnosticsExportError, SourceLocation
from .identity import ConfigurationError
from .delivery import DeliveryFailure, DeliveryResult
from .provenance import SOFTWARE_VERSION as __version__

__all__ = [
    "ConfigurationError", "ConversionResult", "Diagnostic",
    "DiagnosticsExportError", "SourceLocation", "convert",
    "DeliveryFailure", "DeliveryResult", "__version__",
]
