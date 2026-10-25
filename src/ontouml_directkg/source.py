"""Bounded VP-plugin 0.5.3 ingestion, declaration identity and reference lookup.

Fields/stereotypes are grounded in the 0.5.3 serializers and enums at exporter
commit 9fc02b8162db9910f21b8713549cafce2627dad0. Only Project.languages and the
accepted localized text carriers extend that exporter baseline. This is not an
implementation of the standalone OntoUML schema or an OntoUML semantic validator.
"""

from dataclasses import dataclass
import json
from pathlib import Path

from .diagnostics import DiagnosticCollector, SourceLocation, _AbortConversion

_BASE_FIELDS = {"id", "name", "description", "type"}
_MODEL_FIELDS = _BASE_FIELDS | {"propertyAssignments"}
_CLASSIFIER_FIELDS = _MODEL_FIELDS | {"stereotype", "isAbstract", "isDerived", "properties"}
_FIELDS = {
    "Project": _BASE_FIELDS | {"model", "diagrams", "languages"},
    "Package": _MODEL_FIELDS | {"contents"},
    "Class": _CLASSIFIER_FIELDS | {"isExtensional", "isPowertype", "order", "literals", "restrictedTo"},
    "Relation": _CLASSIFIER_FIELDS,
    "Property": _MODEL_FIELDS | {"stereotype", "isDerived", "isReadOnly", "isOrdered", "cardinality",
                                "propertyType", "subsettedProperties", "redefinedProperties", "aggregationKind"},
    "Generalization": _MODEL_FIELDS | {"general", "specific"},
    "GeneralizationSet": _MODEL_FIELDS | {"isDisjoint", "isComplete", "categorizer", "generalizations"},
    "Literal": _MODEL_FIELDS,
}
CLASS_STEREOTYPES = frozenset({
    "type", "historicalRole", "historicalRoleMixin", "event", "situation", "category", "mixin",
    "roleMixin", "phaseMixin", "kind", "collective", "quantity", "relator", "quality", "mode",
    "subkind", "role", "phase", "enumeration", "datatype", "abstract",
})
_RELATION_STEREOTYPES = frozenset({
    "material", "derivation", "comparative", "mediation", "characterization", "externalDependence",
    "componentOf", "memberOf", "subCollectionOf", "subQuantityOf", "instantiation", "termination",
    "participational", "participation", "historicalDependence", "creation", "manifestation",
    "bringsAbout", "triggers",
})
_STEREOTYPES = {"Class": CLASS_STEREOTYPES, "Relation": _RELATION_STEREOTYPES,
                "Property": frozenset({"begin", "end"})}


@dataclass(frozen=True)
class SourceElement:
    """A declaration/container with its actual source location and optional owner."""

    data: dict
    path: str
    owner: str | None = None

    @property
    def location(self) -> SourceLocation:
        identifier = self.data.get("id")
        return SourceLocation(self.path, identifier if isinstance(identifier, str) else None,
                              self.data.get("type"))


@dataclass(frozen=True)
class SourceIndex:
    """Only declarations are indexed; reference objects never declare identities."""

    project: dict
    elements: tuple[SourceElement, ...]
    declarations: dict[str, SourceElement]

    def resolve(self, reference: dict) -> SourceElement:
        """Resolve an exact decoded ID and declared type, without guessing a target.

        Mapping callers handle KeyError under their applicable recovery rules.
        This lookup itself neither generates RDF nor selects an input policy.
        """
        if not isinstance(reference, dict) or set(reference) != {"id", "type"}:
            raise KeyError("Malformed source reference")
        identifier = reference["id"]
        if not isinstance(identifier, str) or identifier not in self.declarations:
            raise KeyError("Unresolved source reference")
        element = self.declarations[identifier]
        if reference["type"] != element.data["type"]:
            raise KeyError("Reference type does not match its declaration")
        return element


def _non_json_constant(value: str) -> None:
    raise ValueError(f"{value} is not a JSON value")


def read_project(path: Path, diagnostics: DiagnosticCollector) -> dict:
    """Read the source once; inability to process a document always aborts."""
    try:
        document = json.loads(path.read_bytes(), parse_constant=_non_json_constant)
    except (OSError, ValueError, UnicodeError) as exc:
        diagnostics.add("ERROR", "UNPROCESSABLE_DOCUMENT", f"Cannot process source JSON {path}: {exc}",
                        "Conversion aborted; no ontology is delivered.")
        raise _AbortConversion from exc
    if (not isinstance(document, dict) or document.get("type") != "Project"
            or not isinstance(document.get("model"), dict)
            or document["model"].get("type") != "Package"):
        diagnostics.add("ERROR", "UNPROCESSABLE_DOCUMENT", "Source has no supported Project/Package model root.",
                        "Conversion aborted; no ontology is delivered.")
        raise _AbortConversion
    return document


def index_project(project: dict, diagnostics: DiagnosticCollector, input_policy: str) -> SourceIndex:
    """Traverse declared containers, retaining all competing IDs before lookup."""
    elements: list[SourceElement] = []
    declarations: dict[str, list[SourceElement]] = {}

    def unknown(message: str, source: SourceElement) -> None:
        fatal = input_policy == "strict"
        diagnostics.add("ERROR" if fatal else "WARNING", "UNKNOWN_INFORMATION", message,
                        "Conversion aborted; no ontology is delivered." if fatal else
                        "Unrecognized information omitted; recognized information is retained.",
                        (source.location,))
        if fatal:
            raise _AbortConversion

    def visit(value: object, path: str, owner: str | None = None, expected: str | None = None) -> None:
        if not isinstance(value, dict):
            raise NotImplementedError("Malformed declaration-container recovery is outside BI-W1")
        element = SourceElement(value, path, owner)
        kind = value.get("type")
        if not isinstance(kind, str) or kind not in _FIELDS:
            unknown(f"Unrecognized element type {kind!r} at {path}.", element)
            return
        if expected is not None and kind != expected:
            raise NotImplementedError("Recovery of misplaced declarations is outside BI-W1")
        elements.append(element)
        extra = sorted(set(value) - _FIELDS[kind])
        if extra:
            unknown(f"Unrecognized input fields on {kind}: {', '.join(extra)}.", element)
        identifier = value.get("id")
        if kind not in {"Project", "Package"} and isinstance(identifier, str) and identifier:
            declarations.setdefault(identifier, []).append(element)
        if kind == "Project":
            visit(value["model"], path + ".model", expected="Package")
        fields = {"Package": ("contents",), "Class": ("properties", "literals"),
                  "Relation": ("properties",)}.get(kind, ())
        for field in fields:
            children = value.get(field)
            if children is None:
                continue
            if not isinstance(children, list):
                raise NotImplementedError("Malformed declaration-container recovery is outside BI-W1")
            child_kind = "Property" if field == "properties" else "Literal" if field == "literals" else None
            for number, child in enumerate(children):
                visit(child, f"{path}.{field}[{number}]", identifier if field != "contents" else None, child_kind)

    visit(project, "$")
    for identifier, competing in declarations.items():
        if len(competing) > 1:
            diagnostics.add("ERROR", "DUPLICATE_SOURCE_ID", f"Duplicate source declaration ID {identifier!r}.",
                            "Conversion aborted; competing declarations are not selected, merged or renamed.",
                            tuple(item.location for item in competing))
            raise _AbortConversion
    return SourceIndex(project, tuple(elements), {key: values[0] for key, values in declarations.items()})


def check_stereotypes(index: SourceIndex, diagnostics: DiagnosticCollector, policy: str) -> None:
    """Apply DK-DIAG-06 independently of input policy; do not validate semantics."""
    for element in index.elements:
        kind = element.data["type"]
        if kind not in _STEREOTYPES:
            continue
        value = element.data.get("stereotype")
        if value is None:
            if kind == "Property" or policy != "require-known":
                continue
            diagnostics.add("ERROR", "MISSING_STEREOTYPE", f"Missing stereotype on {kind}.",
                            "Conversion aborted by the stereotype policy.", (element.location,))
            raise _AbortConversion
        if not isinstance(value, str):
            raise NotImplementedError("Malformed stereotype-value recovery is outside BI-W1")
        if value in _STEREOTYPES[kind]:
            continue
        accepted = policy == "allow-custom"
        diagnostics.add("WARNING" if accepted else "ERROR", "UNRECOGNIZED_STEREOTYPE",
                        f"Unrecognized stereotype {value!r} on {kind}.",
                        "Accepted without stereotype-specific semantics." if accepted else
                        "Conversion aborted by the stereotype policy.", (element.location,))
        if not accepted:
            raise _AbortConversion
