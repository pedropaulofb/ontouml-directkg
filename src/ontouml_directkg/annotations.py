"""Preserve source-authored text independently of IRI lexical selection."""

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDFS

from .diagnostics import DiagnosticCollector, SourceLocation
from .identity import is_valid_language_tag, valid_textual_value
from .source import SourceElement, input_error


def source_text(value: object) -> tuple[tuple[str | None, str], ...]:
    """Read only supported plain-string or valid languageString entries."""
    cleaned = valid_textual_value(value)
    if cleaned is None:
        return ()
    if isinstance(cleaned, str):
        return ((None, cleaned),) if cleaned else ()
    return tuple((key or None, text) for key, text in cleaned.items() if text)


def validate_project_languages(project: dict, diagnostics: DiagnosticCollector, policy: str) -> list[str]:
    """Validate Project.languages; under best-effort omit the array as a whole on error."""
    languages = project.get("languages")
    if languages is None:
        return []
    project_id = project.get("id") if isinstance(project.get("id"), str) else None
    if not isinstance(languages, list):
        input_error(
            diagnostics,
            policy,
            "MALFORMED_PROJECT_LANGUAGES",
            f"Project.languages must be a JSON array or null, got {type(languages).__name__}.",
            (SourceLocation("$.languages", project_id, "Project"),),
            "Project.languages omitted as a whole; conversion continues with untagged fallback unless --language is supplied.",
        )
        return []
    invalid = False
    for index, entry in enumerate(languages):
        location = SourceLocation(f"$.languages[{index}]", project_id, "Project")
        if not isinstance(entry, str):
            invalid = True
            input_error(
                diagnostics,
                policy,
                "MALFORMED_PROJECT_LANGUAGES",
                f"Project.languages entry at $.languages[{index}] must be a nonempty string language tag, got {type(entry).__name__}.",
                (location,),
                "Project.languages omitted as a whole; conversion continues with untagged fallback unless --language is supplied.",
            )
        elif not is_valid_language_tag(entry):
            invalid = True
            input_error(
                diagnostics,
                policy,
                "MALFORMED_PROJECT_LANGUAGES",
                f"Invalid language tag {entry!r} in Project.languages at $.languages[{index}].",
                (location,),
                "Project.languages omitted as a whole; conversion continues with untagged fallback unless --language is supplied.",
            )
    return [] if invalid else list(languages)


def validate_textual_carriers(element: SourceElement, diagnostics: DiagnosticCollector, policy: str) -> None:
    """Validate name and description carriers on a covered surviving element."""
    data = element.data
    elem_type = data.get("type") or "Element"
    identifier = data.get("id")
    id_str = identifier if isinstance(identifier, str) else None
    id_prefix = f"{id_str!r} " if id_str is not None else ""
    for field in ("name", "description"):
        value = data.get(field)
        if value is None or isinstance(value, str):
            continue
        if not isinstance(value, dict):
            input_error(
                diagnostics,
                policy,
                "MALFORMED_TEXTUAL_CARRIER",
                f"{elem_type} {id_prefix}{field} must be a string, languageString object, or null, got {type(value).__name__}.",
                (SourceLocation(f"{element.path}.{field}", id_str, elem_type),),
                f"Malformed {field} field omitted; owning element and independent mappings retained.",
            )
            continue
        for key, entry in value.items():
            entry_loc = SourceLocation(f"{element.path}.{field}[{key!r}]", id_str, elem_type)
            if not isinstance(key, str) or (key != "" and not is_valid_language_tag(key)):
                input_error(
                    diagnostics,
                    policy,
                    "INVALID_LANGUAGE_STRING_ENTRY",
                    f"Invalid language tag {key!r} in {elem_type} {id_prefix}{field} languageString.",
                    (entry_loc,),
                    "Invalid languageString entry omitted; valid localized siblings and independent mappings retained.",
                )
            elif not isinstance(entry, str):
                input_error(
                    diagnostics,
                    policy,
                    "INVALID_LANGUAGE_STRING_ENTRY",
                    f"{elem_type} {id_prefix}{field} languageString entry {key!r} must be a string, got {type(entry).__name__}.",
                    (entry_loc,),
                    "Invalid languageString entry omitted; valid localized siblings and independent mappings retained.",
                )


class TextAnnotations:
    """Resolve literal language with one consolidated ambiguity warning."""

    def __init__(self, project: dict, language: str | None, diagnostics: DiagnosticCollector,
                 languages: list[str] | None = None) -> None:
        self.languages = (list(languages) if languages is not None
                          else validate_project_languages(project, diagnostics, "tolerant"))
        self.override = language
        self.diagnostics = diagnostics
        project_id = project.get("id")
        self.project_location = SourceLocation("$", project_id if isinstance(project_id, str) else None, "Project")
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
            graph.add((subject, predicate, Literal(text, lang=language)))

    def describe(self, graph: Graph, subject: URIRef, source: dict) -> None:
        """Attach source names/descriptions without synthesizing replacements."""
        self.add(graph, subject, RDFS.label, source.get("name"))
        self.add(graph, subject, RDFS.comment, source.get("description"))
