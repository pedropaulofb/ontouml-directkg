"""Preserve source-authored text independently of IRI lexical selection."""

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDFS

from .diagnostics import DiagnosticCollector, SourceLocation


def source_text(value: object) -> tuple[tuple[str | None, str], ...]:
    """Read only supported plain-string or bounded languageString carriers."""
    if value is None:
        return ()
    if isinstance(value, str):
        return ((None, value),) if value else ()
    if isinstance(value, dict) and all(isinstance(k, str) and isinstance(v, str) for k, v in value.items()):
        return tuple((key or None, text) for key, text in value.items() if text)
    raise NotImplementedError("Malformed textual-carrier recovery is outside BI-W1")


class TextAnnotations:
    """Resolve literal language with one consolidated ambiguity warning."""

    def __init__(self, project: dict, language: str | None, diagnostics: DiagnosticCollector) -> None:
        languages = project.get("languages", [])
        if not isinstance(languages, list) or not all(isinstance(v, str) and v for v in languages):
            raise NotImplementedError("Malformed project-language recovery is outside BI-W1")
        self.languages = languages
        self.override = language
        self.diagnostics = diagnostics
        self.project_location = SourceLocation("$", project.get("id"), "Project")
        self.warned = False

    def add(self, graph: Graph, subject: URIRef, predicate: URIRef, value: object) -> None:
        """Preserve every nonempty source value with its applicable language."""
        for local, text in source_text(value):
            language = self.override or local
            if language is None:
                if len(self.languages) == 1:
                    language = self.languages[0]
                elif len(self.languages) > 1 and not self.warned:
                    self.diagnostics.add(
                        "WARNING", "AMBIGUOUS_PROJECT_LANGUAGE",
                        "Language assignment is unresolved because multiple project languages are declared.",
                        "Source text without an explicit local language remains untagged.",
                        (self.project_location,),
                    )
                    self.warned = True
            try:
                literal = Literal(text, lang=language)
            except ValueError as exc:
                raise NotImplementedError("Malformed source-language-tag recovery is outside BI-W1") from exc
            graph.add((subject, predicate, literal))

    def describe(self, graph: Graph, subject: URIRef, source: dict) -> None:
        """Attach source names/descriptions without synthesizing replacements."""
        self.add(graph, subject, RDFS.label, source.get("name"))
        self.add(graph, subject, RDFS.comment, source.get("description"))
