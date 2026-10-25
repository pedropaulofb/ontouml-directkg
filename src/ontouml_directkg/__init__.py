"""OntoUML DirectKG's public Python conversion interface.

BI-W1 implements class declarations, their identity/text/flag annotations, input
policies and diagnostic access/export. Request ``provenance="none"`` explicitly
until BI-W6 implements the specified default embedded provenance. Later-wave
constructs raise NotImplementedError instead of returning silently partial output.
No CLI or ontology-file delivery interface is available in this increment.
"""

from .conversion import ConversionResult, convert
from .diagnostics import Diagnostic, DiagnosticsExportError, SourceLocation
from .identity import ConfigurationError

__all__ = [
    "ConfigurationError", "ConversionResult", "Diagnostic",
    "DiagnosticsExportError", "SourceLocation", "convert",
]
