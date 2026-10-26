"""Required execution provenance, exact-byte checksums and configuration YAML."""

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

import yaml
from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, PROV, RDF, XSD

from .metadata import MetadataInput

SCHEMA = Namespace("https://schema.org/")
SPDX = Namespace("http://spdx.org/rdf/terms#")
SOFTWARE_VERSION = "0.0.0.dev1"


@dataclass(frozen=True)
class ProvenanceRecord:
    graph: Graph
    activity: URIRef
    ontology: URIRef


def _artifact_location(path: Path, replace_final: bool) -> URIRef:
    resolved = path.parent.resolve() / path.name if replace_final else path.resolve()
    return URIRef(resolved.as_uri())


def _optional_location(graph: Graph, artifact: BNode, path: Path, *, replace_final: bool = False) -> None:
    """Unavailable optional location metadata cannot invalidate required provenance."""
    try:
        graph.add((artifact, PROV.atLocation, _artifact_location(path, replace_final)))
    except Exception:
        return


def _checksum(graph: Graph, artifact: BNode, content: bytes) -> None:
    node = BNode()
    graph.add((artifact, SPDX.checksum, node))
    graph.add((node, RDF.type, SPDX.Checksum))
    graph.add((node, SPDX.algorithm, SPDX.checksumAlgorithm_sha256))
    graph.add((node, SPDX.checksumValue, Literal(sha256(content).hexdigest(), datatype=XSD.hexBinary)))


def _input(graph: Graph, activity: URIRef, path: Path, content: bytes, format_: str) -> None:
    artifact = BNode()
    graph.add((artifact, RDF.type, PROV.Entity))
    _optional_location(graph, artifact, path)
    graph.add((artifact, DCTERMS.format, Literal(format_)))
    graph.add((activity, PROV.used, artifact))
    _checksum(graph, artifact, content)


def construct_provenance(ontology: URIRef, source: Path, content: bytes,
                         metadata: MetadataInput, configuration: dict,
                         base: str) -> ProvenanceRecord:
    """Construct required records without reading input files again or writing output."""
    graph = Graph(bind_namespaces="none")
    for prefix, namespace in (("", base), ("rdf", RDF), ("xsd", XSD), ("dcterms", DCTERMS),
                              ("prov", PROV), ("schema", SCHEMA), ("spdx", SPDX)):
        graph.bind(prefix, namespace)
    activity = URIRef("urn:uuid:" + str(uuid4()))
    software = URIRef("https://github.com/pedropaulofb/ontouml-directkg")
    graph.add((activity, RDF.type, PROV.Activity))
    graph.add((activity, PROV.wasAssociatedWith, software))
    graph.add((software, RDF.type, PROV.SoftwareAgent))
    graph.add((software, RDF.type, SCHEMA.SoftwareApplication))
    graph.add((software, SCHEMA.name, Literal("OntoUML DirectKG")))
    graph.add((software, SCHEMA.softwareVersion, Literal(SOFTWARE_VERSION)))
    graph.add((ontology, PROV.wasGeneratedBy, activity))
    _input(graph, activity, source, content, "application/json")
    if metadata.content is not None:
        _input(graph, activity, metadata.path, metadata.content, "application/yaml")
    settings = BNode()
    graph.add((settings, RDF.type, PROV.Entity))
    graph.add((activity, PROV.used, settings))
    graph.add((settings, DCTERMS.format, Literal("application/yaml")))
    graph.add((settings, PROV.value, Literal(yaml.safe_dump(
        configuration, allow_unicode=True, sort_keys=True, default_flow_style=False))))
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    graph.add((activity, PROV.endedAtTime, Literal(timestamp, datatype=XSD.dateTime)))
    return ProvenanceRecord(graph, activity, ontology)


def output_provenance(record: ProvenanceRecord, destination: Path, content: bytes) -> Graph:
    """Add concrete output information only to a separate sidecar graph."""
    graph = Graph(bind_namespaces="none")
    for prefix, namespace in record.graph.namespaces():
        graph.bind(prefix, namespace)
    graph += record.graph
    artifact = BNode()
    graph.add((artifact, RDF.type, PROV.Entity))
    graph.add((artifact, DCTERMS.isFormatOf, record.ontology))
    graph.add((artifact, PROV.wasGeneratedBy, record.activity))
    _optional_location(graph, artifact, destination, replace_final=True)
    graph.add((artifact, SCHEMA.name, Literal(destination.name)))
    graph.add((artifact, DCTERMS.format, Literal("text/turtle")))
    _checksum(graph, artifact, content)
    return graph
