"""BI-W1 class declarations; richer classifier mappings remain explicit gaps."""

from itertools import combinations

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS

from .annotations import TextAnnotations
from .diagnostics import DiagnosticCollector
from .identity import escape_id, missing_name, naming_text, normalize_name, resolve_name_collisions
from .source import SourceElement, SourceIndex

_ULTIMATE = frozenset({"collective", "kind", "mode", "quality", "quantity", "relator", "type"})
_GROUPS = (
    frozenset({"abstract", "datatype", "enumeration"}), frozenset({"event"}), frozenset({"situation"}),
    frozenset({"kind", "collective", "quantity", "relator", "mode", "quality", "subkind", "role", "phase",
               "category", "mixin", "roleMixin", "phaseMixin", "historicalRole", "historicalRoleMixin", "type"}),
)


def wave1_classes(index: SourceIndex) -> tuple[SourceElement, ...]:
    """Refuse later-wave constructs instead of silently omitting required output.

    NotImplementedError identifies unfinished implementation, not a new input
    policy, diagnostic, recovery mapping or claim that a valid model is invalid.
    """
    classes = []
    for element in index.elements:
        data = element.data
        kind = data["type"]
        if kind in {"Project", "Package"}:
            continue
        if kind != "Class":
            raise NotImplementedError(f"{kind} transformation belongs to a later baseline wave")
        identifier = data.get("id")
        if not isinstance(identifier, str) or not identifier:
            raise NotImplementedError("Missing/invalid class-ID recovery requires the deferred Architect decision")
        try:
            identifier.encode("utf-8")
        except UnicodeError as exc:
            raise NotImplementedError("Invalid source-ID recovery requires the deferred Architect decision") from exc
        if data.get("stereotype") in {"datatype", "enumeration"}:
            raise NotImplementedError("Datatype/enumeration classification belongs to BI-W2")
        if data.get("order") is not None or data.get("isExtensional") is not None:
            raise NotImplementedError("Classifier order/extensionality annotations belong to BI-W2")
        for flag in ("isAbstract", "isDerived"):
            if data.get(flag) is not None and type(data[flag]) is not bool:
                raise NotImplementedError("Malformed class-flag recovery is outside BI-W1")
        classes.append(element)
    # Recognized class pairs requiring later disjointness must not be returned
    # as completed while their required axioms are still unimplemented.
    for left, right in combinations(classes, 2):
        a, b = left.data.get("stereotype"), right.data.get("stereotype")
        ga = next((n for n, group in enumerate(_GROUPS) if a in group), None)
        gb = next((n for n, group in enumerate(_GROUPS) if b in group), None)
        if (a in _ULTIMATE and b in _ULTIMATE) or (ga is not None and gb is not None and ga != gb):
            raise NotImplementedError("Stereotype-based class disjointness belongs to BI-W2")
    return tuple(classes)


def emit_classes(graph: Graph, classes: tuple[SourceElement, ...], base: str, strategy: str,
                 omit_identifiers: bool, text: TextAnnotations, diagnostics: DiagnosticCollector) -> None:
    """Allocate class identities before emitting actual OWL declarations/text."""
    candidates = {}
    fallbacks = set()
    for element in classes:
        identifier = element.data["id"]
        if strategy == "id":
            candidates[identifier] = escape_id(identifier)
        else:
            selected = naming_text(element.data.get("name"))
            if selected is None:
                candidates[identifier] = "unnamedClass_" + escape_id(identifier, whole_local_name=False)
                fallbacks.add(identifier)
            else:
                candidates[identifier] = normalize_name(selected)
    if strategy == "name":
        candidates = resolve_name_collisions(candidates)
    elif len(set(candidates.values())) != len(candidates):
        raise NotImplementedError("Exceptional escaped-ID collision disposition requires an Architect decision")
    for element in classes:
        data = element.data
        identifier = data["id"]
        subject = URIRef(base + candidates[identifier])
        graph.add((subject, RDF.type, OWL.Class))
        text.describe(graph, subject, data)
        if strategy == "name" and not omit_identifiers:
            graph.add((subject, DCTERMS.identifier, Literal(identifier)))
        if identifier in fallbacks or (strategy == "id" and missing_name(data.get("name"))):
            diagnostics.add("WARNING", "MISSING_CLASS_NAME",
                            f"Class {identifier!r}, stereotype {data.get('stereotype')!r}, has no usable "
                            + ("name-based IRI name." if strategy == "name" else "source name."),
                            "Class retained with the generated IRI.", (element.location,), str(subject))
        if data.get("stereotype") == "abstract":
            graph.add((subject, RDFS.comment, Literal("OntoUML class stereotype: abstract.", lang="en")))
            diagnostics.add("INFO", "ABSTRACTNESS_ANNOTATION",
                            "The abstract stereotype is preserved as an annotation; its meaning is not additionally "
                            "enforced through OWL logical constraints. Applicable stereotype disjointness is unchanged.",
                            "Class and annotation retained.", (element.location,))
        for flag in ("isAbstract", "isDerived"):
            value = data.get(flag)
            if type(value) is not bool:
                continue
            graph.add((subject, RDFS.comment, Literal(f"OntoUML class {flag}: {str(value).lower()}.", lang="en")))
            if flag == "isAbstract":
                diagnostics.add("INFO", "ABSTRACTNESS_ANNOTATION",
                                f"Explicit isAbstract={str(value).lower()} is preserved as an annotation; its meaning "
                                "is not additionally enforced through OWL logical constraints.",
                                "Class and annotation retained.", (element.location,))
            elif value:
                diagnostics.add("INFO", "DERIVED_STATUS_ANNOTATION",
                                "isDerived=true is preserved as an annotation; the annotation itself supplies no derivation rule.",
                                "Class and annotation retained.", (element.location,))
