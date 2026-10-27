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


def _identifier_problem(data: dict) -> str | None:
    """Check opaque source IDs without changing their decoded strings (RD-02)."""
    if "id" not in data:
        return "Source identifier is missing: the id field is absent."
    identifier = data["id"]
    if not isinstance(identifier, str) or not identifier:
        return "Source identifier is invalid: expected a nonempty JSON string."
    try:
        identifier.encode("utf-8")
    except UnicodeError:
        return "Source identifier is invalid: the string cannot be encoded as UTF-8."
    return None


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
        problem = _identifier_problem(reference)
        if problem is not None:
            raise KeyError(problem)
        identifier = reference["id"]
        if identifier not in self.declarations:
            raise KeyError("Unresolved source reference")
        element = self.declarations[identifier]
        if reference["type"] != element.data["type"]:
            raise KeyError("Reference type does not match its declaration")
        return element


def input_error(diagnostics: DiagnosticCollector, policy: str, code: str,
                message: str, sources: tuple[SourceLocation, ...], recovery: str) -> None:
    """Apply the established structural-error policy, retaining ERROR severity."""
    abort = policy != "best-effort"
    diagnostics.add("ERROR", code, message,
                    "Conversion aborted; no ontology is delivered." if abort else recovery, sources)
    if abort:
        raise _AbortConversion


def _non_json_constant(value: str) -> None:
    raise ValueError(f"{value} is not a JSON value")


def read_project(path: Path, diagnostics: DiagnosticCollector, *,
                 captured_bytes: list[bytes] | None = None) -> dict:
    """Read the source once; inability to process a document always aborts."""
    try:
        content = path.read_bytes()
        if captured_bytes is not None:
            captured_bytes.append(content)
        document = json.loads(content, parse_constant=_non_json_constant)
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
        if kind not in {"Project", "Package"} and _identifier_problem(value) is None:
            declarations.setdefault(identifier, []).append(element)
        if kind == "Project":
            visit(value["model"], path + ".model", expected="Package")
        fields = {"Package": ("contents",), "Class": ("properties", "literals"),
                  "Relation": ("properties",)}.get(kind, ())
        for field in fields:
            children = value.get(field)
            if children is None:
                continue
            enumeration_values = (kind == "Class" and value.get("stereotype") == "enumeration"
                                  and field == "literals")
            # DK-DIAG-13 owns these malformed lists/values. Preserve the raw
            # collection for that mapping while indexing every Literal
            # declaration that can participate in fatal duplicate-ID checking.
            if enumeration_values and not isinstance(children, list):
                continue
            if not isinstance(children, list):
                raise NotImplementedError("Malformed declaration-container recovery is outside BI-W1")
            child_kind = "Property" if field == "properties" else "Literal" if field == "literals" else None
            for number, child in enumerate(children):
                if enumeration_values and (not isinstance(child, dict) or child.get("type") != "Literal"):
                    continue
                visit(child, f"{path}.{field}[{number}]", identifier if field != "contents" else None, child_kind)

    visit(project, "$")
    for identifier, competing in declarations.items():
        if len(competing) > 1:
            diagnostics.add("ERROR", "DUPLICATE_SOURCE_ID", f"Duplicate source declaration ID {identifier!r}.",
                            "Conversion aborted; competing declarations are not selected, merged or renamed.",
                            tuple(item.location for item in competing))
            raise _AbortConversion

    return SourceIndex(project, tuple(elements), {key: values[0] for key, values in declarations.items()})


def apply_identifier_policy(index: SourceIndex, diagnostics: DiagnosticCollector,
                            input_policy: str) -> SourceIndex:
    """Recover identifiers after the full source passes DK-DIAG-06's check.

    Filtering must not hide a rejected stereotype on an omitted declaration
    or its owned elements. Duplicate checking precedes this recovery as well.
    Literal and relation-end recovery remains in their mapping collectors.
    """
    relation_ids = {identifier for identifier, element in index.declarations.items()
                    if element.data["type"] == "Relation"}
    omitted: list[str] = []
    retained = []
    for element in index.elements:
        if any(element.path.startswith(path + ".") for path in omitted):
            continue
        kind = element.data["type"]
        relation_end = (kind == "Property" and isinstance(element.owner, str)
                        and element.owner in relation_ids)
        if kind not in {"Project", "Package", "Literal"} and not relation_end:
            problem = _identifier_problem(element.data)
            if problem is not None:
                input_error(diagnostics, input_policy,
                            "MISSING_SOURCE_ID" if "id" not in element.data else "INVALID_SOURCE_ID",
                            problem, (element.location,),
                            "Affected declaration and output requiring its ownership omitted; independent mappings retained.")
                omitted.append(element.path)
                continue
        retained.append(element)
    retained_paths = {element.path for element in retained}
    return SourceIndex(index.project, tuple(retained),
                       {key: element for key, element in index.declarations.items()
                        if element.path in retained_paths})


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
