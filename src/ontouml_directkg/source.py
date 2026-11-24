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
    container_errors: tuple[tuple[tuple[SourceLocation, ...], str, str, str], ...] = ()
    omitted_paths: tuple[str, ...] = ()
    omitted_relations: frozenset[str] = frozenset()
    omitted_relation_ends: frozenset[str] = frozenset()

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


def validate_boolean_flags(element: SourceElement, flags: tuple[str, ...],
                           diagnostics: DiagnosticCollector, policy: str) -> None:
    """Validate defined Boolean flags on a surviving element (RD-02 Alternative 1)."""
    data = element.data
    elem_type = data.get("type") or "Element"
    identifier = data.get("id")
    id_str = identifier if isinstance(identifier, str) else None
    id_prefix = f"{id_str!r} " if id_str is not None else ""
    for flag in flags:
        value = data.get(flag)
        if value is None or type(value) is bool:
            continue
        input_error(
            diagnostics,
            policy,
            "MALFORMED_BOOLEAN_FLAG",
            f"{elem_type} {id_prefix}{flag} must be a boolean or null, got {type(value).__name__}.",
            (SourceLocation(f"{element.path}.{flag}", id_str, elem_type),),
            f"Malformed {flag} field omitted; owning {elem_type} and independent mappings retained.",
        )
        data.pop(flag, None)


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
    container_errors: list[tuple[tuple[SourceLocation, ...], str, str, str]] = []

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
            if kind == "Package" and field == "contents":
                if not isinstance(children, list):
                    id_text = f" {identifier!r}" if isinstance(identifier, str) else ""
                    if path == "$.model":
                        diagnostics.add(
                            "ERROR", "UNPROCESSABLE_DOCUMENT",
                            f"Root model Package{id_text} contents must be a JSON array or null (got {type(children).__name__}).",
                            "Conversion aborted; no ontology is delivered.",
                            (element.location,),
                        )
                        raise _AbortConversion
                    container_errors.append((
                        (element.location,),
                        "MALFORMED_PACKAGE_CONTENTS",
                        f"Package{id_text} contents at {path}.contents must be a JSON array or null (got {type(children).__name__}).",
                        "Affected nested package contents omitted; independently transformable elements retained.",
                    ))
                    continue
                for number, child in enumerate(children):
                    child_path = f"{path}.contents[{number}]"
                    if not isinstance(child, dict):
                        container_errors.append((
                            (SourceLocation(child_path, None, None),),
                            "INVALID_PACKAGE_CONTENTS_ENTRY",
                            f"Package.contents entry at {child_path} must be a JSON object, got {type(child).__name__}.",
                            "Affected Package.contents entry omitted; valid siblings and independent mappings retained.",
                        ))
                        continue
                    child_kind = child.get("type")
                    child_id = child.get("id")
                    child_loc = SourceLocation(
                        child_path,
                        child_id if isinstance(child_id, str) else None,
                        child_kind if isinstance(child_kind, str) else None,
                    )
                    if not isinstance(child_kind, str) or not child_kind.strip():
                        container_errors.append((
                            (child_loc,),
                            "INVALID_PACKAGE_CONTENTS_ENTRY",
                            f"Package.contents entry at {child_path} lacks a valid nonempty string 'type'.",
                            "Affected Package.contents entry omitted; valid siblings and independent mappings retained.",
                        ))
                        continue
                    if child_kind not in _FIELDS:
                        unknown(f"Unrecognized element type {child_kind!r} at {child_path}.",
                                SourceElement(child, child_path, None))
                        continue
                    if child_kind in {"Project", "Property", "Literal"}:
                        child_id_text = f" {child_id!r}" if isinstance(child_id, str) else ""
                        container_errors.append((
                            (child_loc,),
                            "MISPLACED_PACKAGE_DECLARATION",
                            f"Misplaced {child_kind} declaration{child_id_text} is not permitted in Package.contents.",
                            "Affected misplaced declaration omitted; valid siblings and independent mappings retained.",
                        ))
                        if child_kind != "Project":
                            child_element = SourceElement(child, child_path, None)
                            elements.append(child_element)
                            extra_child = sorted(set(child) - _FIELDS[child_kind])
                            if extra_child:
                                unknown(f"Unrecognized input fields on {child_kind}: {', '.join(extra_child)}.",
                                        child_element)
                            if _identifier_problem(child) is None:
                                declarations.setdefault(child_id, []).append(child_element)
                        continue
                    visit(child, child_path, None)
                continue

            if kind == "Class" and field == "properties":
                id_text = f" {identifier!r}" if isinstance(identifier, str) else ""
                if not isinstance(children, list):
                    container_errors.append((
                        (element.location,),
                        "MALFORMED_CLASS_PROPERTIES",
                        f"Class{id_text} properties container at {path}.properties must be a JSON array or null (got {type(children).__name__}).",
                        "Malformed Class.properties container omitted; owning Class and independent mappings retained.",
                    ))
                    continue
                for number, child in enumerate(children):
                    child_path = f"{path}.properties[{number}]"
                    if not isinstance(child, dict) or child.get("type") != "Property":
                        if isinstance(child, dict):
                            child_id = child.get("id")
                            child_kind = child.get("type")
                            child_loc = SourceLocation(
                                child_path,
                                child_id if isinstance(child_id, str) else None,
                                child_kind if isinstance(child_kind, str) else None,
                            )
                            sources = (child_loc, element.location)
                        else:
                            sources = (SourceLocation(child_path, None, None), element.location)
                        container_errors.append((
                            sources,
                            "INVALID_CLASS_PROPERTY_ENTRY",
                            f"Class{id_text} properties entry at {child_path} is not a Property object.",
                            "Invalid Class.properties entry omitted; owning Class, valid Property siblings, and independent mappings retained.",
                        ))
                        continue
                    visit(child, child_path, identifier, "Property")
                continue

            if kind == "Class" and field == "literals" and value.get("stereotype") != "enumeration":
                id_text = f" {identifier!r}" if isinstance(identifier, str) else ""
                if not isinstance(children, list):
                    container_errors.append((
                        (element.location,),
                        "MALFORMED_NON_ENUM_LITERALS",
                        f"Non-enumeration Class{id_text} literals container at {path}.literals must be a JSON array or null (got {type(children).__name__}).",
                        "Malformed Class.literals container omitted; owning Class and independent mappings retained.",
                    ))
                    continue
                for number, child in enumerate(children):
                    child_path = f"{path}.literals[{number}]"
                    if not isinstance(child, dict) or child.get("type") != "Literal":
                        if isinstance(child, dict):
                            child_id = child.get("id")
                            child_kind = child.get("type")
                            child_loc = SourceLocation(
                                child_path,
                                child_id if isinstance(child_id, str) else None,
                                child_kind if isinstance(child_kind, str) else None,
                            )
                            sources = (child_loc, element.location)
                        else:
                            sources = (SourceLocation(child_path, None, None), element.location)
                        container_errors.append((
                            sources,
                            "INVALID_NON_ENUM_LITERALS_ENTRY",
                            f"Non-enumeration Class{id_text} literals entry at {child_path} is not a Literal object.",
                            "Invalid Class.literals entry omitted; owning Class and independent mappings retained.",
                        ))
                        continue
                    child_id = child.get("id")
                    child_loc = SourceLocation(child_path, child_id if isinstance(child_id, str) else None, "Literal")
                    lit_text = f" {child_id!r}" if isinstance(child_id, str) else ""
                    container_errors.append((
                        (child_loc, element.location),
                        "DISALLOWED_NON_ENUM_LITERAL",
                        f"Literal declaration{lit_text} at {child_path} is not permitted on non-enumeration Class{id_text}.",
                        "Disallowed Class.literals entry omitted without generating owl:NamedIndividual; owning Class and independent mappings retained.",
                    ))
                    visit(child, child_path, identifier, "Literal")
                continue

            enumeration_values = (kind == "Class" and value.get("stereotype") == "enumeration"
                                  and field == "literals")
            relation_ends = (kind == "Relation" and field == "properties")
            # DK-DIAG-13 (enumerations) and DK-DIAG-03/DK-INS-02 (Relation.properties)
            # own these malformed lists/values. Preserve the raw collection for those
            # mappings while indexing every valid Literal/Property declaration that can
            # participate in fatal duplicate-ID and stereotype checks.
            if (enumeration_values or relation_ends) and not isinstance(children, list):
                continue
            if not isinstance(children, list):
                raise NotImplementedError("Malformed declaration-container recovery is outside BI-W1")
            child_kind = "Property" if field == "properties" else "Literal" if field == "literals" else None
            for number, child in enumerate(children):
                if enumeration_values and (not isinstance(child, dict) or child.get("type") != "Literal"):
                    continue
                if relation_ends and (not isinstance(child, dict) or child.get("type") != "Property"):
                    continue
                visit(child, f"{path}.{field}[{number}]", identifier if field != "contents" else None, child_kind)

    visit(project, "$")
    for identifier, competing in declarations.items():
        if len(competing) > 1:
            diagnostics.add("ERROR", "DUPLICATE_SOURCE_ID", f"Duplicate source declaration ID {identifier!r}.",
                            "Conversion aborted; competing declarations are not selected, merged or renamed.",
                            tuple(item.location for item in competing))
            raise _AbortConversion

    return SourceIndex(project, tuple(elements), {key: values[0] for key, values in declarations.items()},
                       tuple(container_errors))


def apply_identifier_policy(index: SourceIndex, diagnostics: DiagnosticCollector,
                            input_policy: str) -> SourceIndex:
    """Recover identifiers after the full source passes DK-DIAG-06's check.

    Filtering must not hide a rejected stereotype on an omitted declaration
    or its owned elements. Duplicate checking precedes this recovery as well.
    Literal and relation-end recovery remains in their mapping collectors.
    """
    relation_ids = {identifier for identifier, element in index.declarations.items()
                    if element.data["type"] == "Relation"}
    omitted: list[str] = list(index.omitted_paths)
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
                        if element.path in retained_paths},
                       index.container_errors, tuple(omitted),
                       index.omitted_relations, index.omitted_relation_ends)


def validate_containers(index: SourceIndex, diagnostics: DiagnosticCollector, input_policy: str) -> None:
    """Emit structural container/entry errors after duplicate, stereotype, and ID precedence."""
    for sources, code, message, recovery in index.container_errors:
        primary_path = sources[0].path
        if any(primary_path == path or primary_path.startswith(path + ".") for path in index.omitted_paths):
            continue
        input_error(diagnostics, input_policy, code, message, sources, recovery)


def check_stereotypes(index: SourceIndex, diagnostics: DiagnosticCollector, policy: str,
                      input_policy: str = "tolerant") -> SourceIndex:
    """Apply DK-DIAG-06 and RD-02 malformed-stereotype checks without validating semantics."""
    omitted_paths: list[str] = list(index.omitted_paths)
    omitted_relation_paths: list[str] = []
    omitted_relations = set(index.omitted_relations)
    omitted_relation_ends = set(index.omitted_relation_ends)
    retained: list[SourceElement] = []
    for element in index.elements:
        if any(element.path.startswith(path + ".") for path in omitted_paths):
            if (element.data.get("type") == "Property"
                    and any(element.path.startswith(path + ".") for path in omitted_relation_paths)
                    and _identifier_problem(element.data) is None):
                omitted_relation_ends.add(element.data["id"])
            continue
        kind = element.data["type"]
        if kind not in _STEREOTYPES:
            retained.append(element)
            continue
        value = element.data.get("stereotype")
        if value is None:
            if kind != "Property" and policy == "require-known":
                diagnostics.add("ERROR", "MISSING_STEREOTYPE", f"Missing stereotype on {kind}.",
                                "Conversion aborted by the stereotype policy.", (element.location,))
                raise _AbortConversion
            retained.append(element)
            continue
        if not isinstance(value, str) or not value.strip():
            identifier = element.data.get("id")
            id_text = f" {identifier!r}" if isinstance(identifier, str) else ""
            if not isinstance(value, str):
                message = f"{kind}{id_text} has a malformed stereotype (non-string {type(value).__name__})."
            else:
                message = f"{kind}{id_text} has an empty or whitespace-only stereotype."
            if kind == "Property":
                recovery = "Malformed Property.stereotype field omitted; valid property and independent mappings retained."
            elif kind == "Class":
                recovery = "Affected Class and its owned properties and literals omitted; independent mappings retained."
            else:
                recovery = "Affected Relation and dependent output omitted; independent mappings retained."
            input_error(diagnostics, input_policy, "MALFORMED_STEREOTYPE", message, (element.location,), recovery)
            if kind == "Property":
                element.data.pop("stereotype", None)
                retained.append(element)
            else:
                omitted_paths.append(element.path)
                if kind == "Relation":
                    omitted_relation_paths.append(element.path)
                    if _identifier_problem(element.data) is None:
                        omitted_relations.add(element.data["id"])
            continue
        if value not in _STEREOTYPES[kind]:
            accepted = policy == "allow-custom"
            diagnostics.add("WARNING" if accepted else "ERROR", "UNRECOGNIZED_STEREOTYPE",
                            f"Unrecognized stereotype {value!r} on {kind}.",
                            "Accepted without stereotype-specific semantics." if accepted else
                            "Conversion aborted by the stereotype policy.", (element.location,))
            if not accepted:
                raise _AbortConversion
        retained.append(element)
    retained_paths = {element.path for element in retained}
    return SourceIndex(
        index.project,
        tuple(retained),
        {key: element for key, element in index.declarations.items() if element.path in retained_paths},
        index.container_errors,
        tuple(omitted_paths),
        frozenset(omitted_relations),
        frozenset(omitted_relation_ends),
    )
