"""Local class identity, declarations, annotations and stereotype disjointness."""

from itertools import combinations

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS

from .annotations import TextAnnotations
from .datatypes import datatype_key
from .diagnostics import DiagnosticCollector
from .enumerations import Enumeration
from .identity import class_name_candidate, escape_id, missing_name, naming_text, normalize_name, resolve_name_collisions
from .source import SourceElement, SourceIndex

_ULTIMATE = frozenset({"collective", "kind", "mode", "quality", "quantity", "relator", "type"})
_GROUPS = (
    frozenset({"abstract", "datatype", "enumeration"}), frozenset({"event"}), frozenset({"situation"}),
    frozenset({"kind", "collective", "quantity", "relator", "mode", "quality", "subkind", "role", "phase",
               "category", "mixin", "roleMixin", "phaseMixin", "historicalRole", "historicalRoleMixin", "type"}),
)


def baseline_classes(index: SourceIndex) -> tuple[SourceElement, ...]:
    """Refuse later-wave constructs instead of silently omitting required output.

    NotImplementedError identifies unfinished implementation, not a new input
    policy, diagnostic, recovery mapping or claim that a valid model is invalid.
    """
    classes = []
    for element in index.elements:
        data = element.data
        kind = data["type"]
        if kind in {"Project", "Package", "Generalization", "GeneralizationSet", "Relation", "Property"}:
            continue
        if kind == "Literal":
            owner = index.declarations.get(element.owner)
            if owner is not None and owner.data.get("stereotype") == "enumeration":
                continue
            raise NotImplementedError("Literal declarations outside enumerations have no assigned baseline mapping")
        if kind != "Class":
            raise NotImplementedError(f"{kind} transformation belongs to a later baseline wave")
        identifier = data.get("id")
        if not isinstance(identifier, str) or not identifier:
            raise NotImplementedError("Missing/invalid class-ID recovery requires the deferred Architect decision")
        try:
            identifier.encode("utf-8")
        except UnicodeError as exc:
            raise NotImplementedError("Invalid source-ID recovery requires the deferred Architect decision") from exc
        for flag in ("isAbstract", "isDerived", "isExtensional", "isPowertype"):
            if data.get(flag) is not None and type(data[flag]) is not bool:
                raise NotImplementedError("Malformed class-flag recovery is outside the decided baseline")
        order = data.get("order")
        if order is not None and (isinstance(order, bool) or not isinstance(order, (str, int, float))):
            raise NotImplementedError("Malformed classifier-order recovery is outside the decided baseline")
        if data.get("stereotype") == "datatype" and datatype_key(data.get("name")) is not None:
            continue
        classes.append(element)
    return tuple(classes)


def allocate_resources(classes: tuple[SourceElement, ...], enumerations: tuple[Enumeration, ...],
                       base: str, strategy: str, property_candidates: dict[str, str] | None = None,
                       claimed_names: set[str] | None = None) -> dict[str, URIRef]:
    """Resolve classes first, then value prefixes and shared source collisions.

    A value can collide with a class. If that suffixes an enumeration class,
    rebuild its value candidates from the newly resolved class name before
    finishing. Names only acquire collision suffixes; source order is irrelevant.
    """
    candidates = {}
    for element in classes:
        identifier = element.data["id"]
        if strategy == "id":
            candidates[identifier] = escape_id(identifier)
        else:
            candidates[identifier] = class_name_candidate(identifier, element.data.get("name"))
    if strategy == "name":
        candidates.update(property_candidates or {})
        for enumeration in enumerations:
            for element in enumeration.values:
                if naming_text(element.data.get("name")) is None:
                    candidates[element.data["id"]] = escape_id(element.data["id"])
        if claimed_names is not None:
            claimed_names.update(candidates.values())
        candidates = resolve_name_collisions(candidates)
        for enumeration in enumerations:
            prefix = candidates[enumeration.source.data["id"]]
            for element in enumeration.values:
                selected = naming_text(element.data.get("name"))
                if selected is not None:
                    candidates[element.data["id"]] = prefix + "_" + normalize_name(selected)
        while True:
            if claimed_names is not None:
                claimed_names.update(candidates.values())
            resolved = resolve_name_collisions(candidates)
            changed = False
            for enumeration in enumerations:
                identifier = enumeration.source.data["id"]
                if resolved[identifier] == candidates[identifier]:
                    continue
                changed = True
                prefix = resolved[identifier]
                for element in enumeration.values:
                    selected = naming_text(element.data.get("name"))
                    if selected is not None:
                        resolved[element.data["id"]] = prefix + "_" + normalize_name(selected)
            candidates = resolved
            if not changed:
                break
    else:
        candidates.update(property_candidates or {})
        for enumeration in enumerations:
            for element in enumeration.values:
                candidates[element.data["id"]] = escape_id(element.data["id"])
    if len(set(candidates.values())) != len(candidates):
        raise NotImplementedError("Exceptional escaped-ID collision disposition requires an Architect decision")
    if claimed_names is not None:
        claimed_names.update(candidates.values())
    return {identifier: URIRef(base + candidate) for identifier, candidate in candidates.items()}


def emit_classes(graph: Graph, classes: tuple[SourceElement, ...], resources: dict[str, URIRef], strategy: str,
                 omit_identifiers: bool, text: TextAnnotations, diagnostics: DiagnosticCollector) -> None:
    """Emit actual OWL declarations/text only for classifiers with local targets."""
    if strategy == "name" and not omit_identifiers:
        for identifier, subject in resources.items():
            graph.add((subject, DCTERMS.identifier, Literal(identifier)))
    for element in classes:
        data = element.data
        identifier = data["id"]
        subject = resources[identifier]
        graph.add((subject, RDF.type, OWL.Class))
        text.describe(graph, subject, data)
        if ((strategy == "name" and naming_text(data.get("name")) is None)
                or (strategy == "id" and missing_name(data.get("name")))):
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
        extensional = data.get("isExtensional")
        if type(extensional) is bool:
            graph.add((subject, RDFS.comment, Literal(f"OntoUML class isExtensional: {str(extensional).lower()}.", lang="en")))
            if extensional:
                diagnostics.add("INFO", "EXTENSIONALITY_ANNOTATION",
                                "isExtensional=true is preserved as an annotation; its essential-parthood semantics are not enforced.",
                                "Class and annotation retained without additional logical axioms.", (element.location,))
        order = data.get("order")
        if order is not None:
            value = "orderless (*)" if order == "*" else str(order)
            graph.add((subject, RDFS.comment, Literal(f"OntoUML classifier order: {value}.", lang="en")))


def emit_stereotype_disjointness(graph: Graph, classes: tuple[SourceElement, ...],
                                 resources: dict[str, URIRef]) -> None:
    """Assert exactly the direct stereotype pairs, using one orientation each."""
    for left, right in combinations(sorted(classes, key=lambda element: element.data["id"]), 2):
        a, b = left.data.get("stereotype"), right.data.get("stereotype")
        ga = next((n for n, group in enumerate(_GROUPS) if a in group), None)
        gb = next((n for n, group in enumerate(_GROUPS) if b in group), None)
        if (a in _ULTIMATE and b in _ULTIMATE) or (ga is not None and gb is not None and ga != gb):
            graph.add((resources[left.data["id"]], OWL.disjointWith, resources[right.data["id"]]))
