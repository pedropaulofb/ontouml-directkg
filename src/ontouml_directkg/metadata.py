"""Explicit Catalog metadata input, restricted to DK-GEN-09's seven fields."""

from dataclasses import dataclass
from pathlib import Path

import yaml
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCAT, DCTERMS

from .diagnostics import DiagnosticCollector, SourceLocation
from .identity import is_absolute_iri
from .source import input_error

MOD = Namespace("https://w3id.org/mod#")
_FIELDS = {"title": DCTERMS.title, "acronym": MOD.acronym,
           "contributor": DCTERMS.contributor, "keyword": DCAT.keyword,
           "source": DCTERMS.source, "landingPage": DCAT.landingPage,
           "license": DCTERMS.license}
_LISTS = {"contributor", "keyword", "source"}
_IRIS = {"contributor", "source", "landingPage", "license"}


@dataclass(frozen=True)
class MetadataInput:
    path: Path | None = None
    content: bytes | None = None
    values: tuple[tuple[URIRef, Literal | URIRef], ...] = ()


def read_metadata(path: Path | None, diagnostics: DiagnosticCollector,
                   policy: str) -> MetadataInput:
    """Preserve exact bytes only for an artifact actually read and parsed."""
    if path is None:
        return MetadataInput()
    location = SourceLocation(str(path), element_type="metadata file")
    try:
        content = path.read_bytes()
        data = yaml.safe_load(content)
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        input_error(diagnostics, policy, "METADATA_INPUT",
                    f"Cannot read or parse metadata file {path}: {exc}.", (location,),
                    "All external metadata omitted; source metadata and independent transformations retained.")
        return MetadataInput()
    if not isinstance(data, dict):
        input_error(diagnostics, policy, "METADATA_INPUT",
                    f"Metadata file {path} does not contain a top-level mapping.", (location,),
                    "All external metadata omitted; source metadata and independent transformations retained.")
        return MetadataInput(path, content)
    values = []
    for field, predicate in _FIELDS.items():
        value = data.get(field)
        if value is None or value == "" or value == []:
            continue
        if field in _LISTS:
            entries = value if isinstance(value, list) else None
        elif field == "landingPage" and isinstance(value, list):
            entries = value
        else:
            entries = [value]
        valid = ([] if entries is None else
                 [isinstance(entry, str) and bool(entry)
                  and (field not in _IRIS or is_absolute_iri(entry)) for entry in entries])
        if entries is None or not all(valid):
            input_error(diagnostics, policy, "METADATA_FIELD",
                        f"Selected metadata field {field!r} in {path} has an invalid value or value shape.",
                        (location,), "Affected external metadata omitted; independent selected fields and source mappings retained.")
            if valid and any(valid):
                raise NotImplementedError("Valid-sibling recovery in mixed metadata lists awaits the deferred Architect decision")
            continue
        for entry in entries:
            values.append((predicate, URIRef(entry) if field in _IRIS else Literal(entry)))
    return MetadataInput(path, content, tuple(values))


def emit_metadata(graph: Graph, ontology: URIRef, metadata: MetadataInput) -> None:
    if metadata.values:
        graph.bind("dcat", DCAT)
        graph.bind("mod", MOD)
    for predicate, value in metadata.values:
        graph.add((ontology, predicate, value))
