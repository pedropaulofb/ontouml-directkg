"""CWD-independent fixture loading and bounded fixture-authoring checks.

These checks audit our fixtures, not DirectKG's input acceptance or recovery.
They reflect the inspected VP-plugin 0.5.3 serializers plus RD-27 text carriers.
They do not validate OntoUML semantics, guess exporter versions, fix data, or
apply a newer standalone schema to the whole document.
"""

import json
from pathlib import Path, PurePosixPath

import yaml


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
TOPICS = frozenset({"ontology", "iris", "properties", "input_diagnostics", "attributes_datatypes",
                    "classes", "higher_order", "labels", "relations", "inverses"})


def fixture_path(key: str, filename: str = "input.json") -> Path:
    parts = PurePosixPath(key).parts
    if len(parts) != 2 or any(p in {"", ".", ".."} for p in parts):
        raise ValueError("Expected <topic>/<case_slug> or shared/<fixture_slug>")
    if parts[0] in {"shared", "cli"}:
        path = FIXTURES.joinpath(*parts, filename).resolve()
    elif parts[0] in TOPICS:
        path = FIXTURES.joinpath("transformation", *parts, filename).resolve()
    else:
        raise ValueError("Unrecognized fixture topic: " + parts[0])
    if not path.is_relative_to(FIXTURES):
        raise ValueError("Fixture path escapes the fixture directory")
    if not path.is_file():
        raise FileNotFoundError(path)
    return path


def load_json(key: str, filename: str = "input.json") -> dict:
    """Load a new independent object; never repair invalid data."""
    return json.loads(fixture_path(key, filename).read_bytes())


def load_yaml(key: str, filename: str = "metadata.yaml"):
    """Read stored YAML without repairing, selecting fields or applying defaults."""
    return yaml.safe_load(fixture_path(key, filename).read_bytes())


def write_input(tmp_path: Path, document, filename: str = "input.json", *, ensure_ascii: bool = False) -> Path:
    """Materialize a reviewed test's small mutation in its pytest temp directory."""
    destination = tmp_path / filename
    destination.write_text(json.dumps(document, ensure_ascii=ensure_ascii, indent=2) + "\n", encoding="utf-8")
    return destination


def source_elements(document):
    """Walk actual declarations in the used exporter containers, not references.

    This is only data traversal. It assigns no transformation meaning and does
    not reinterpret arbitrary dictionaries or custom metadata as declarations.
    """
    if not isinstance(document, dict):
        return
    yield document
    kind = document.get("type")
    if kind == "Project":
        yield from source_elements(document.get("model"))
    for field in {"Package": ("contents",), "Class": ("properties", "literals"),
                  "Relation": ("properties",)}.get(kind, ()):
        children = document.get(field)
        if isinstance(children, list):
            for child in children:
                yield from source_elements(child)


def source_element(document, identifier):
    """Select one declaration by its exact ID; fail on missing/duplicate IDs."""
    matches = [item for item in source_elements(document) if item.get("id") == identifier]
    assert len(matches) == 1, (identifier, matches)
    return matches[0]


def _valid_identifier(value):
    """Fixture-authoring check for RD-02's opaque strings; never repair data."""
    if not isinstance(value, str) or value == "":
        return False
    try:
        value.encode("utf-8")
    except UnicodeError:
        return False
    return True


def fixture_issues(document) -> frozenset[str]:
    """Return authoring issues for the structures used in this wave.

    Complete exported fields may be null. Missing names/stereotypes/cardinality
    are explicitly covered by accepted rules, so they are not authoring defects.
    Unknown fields/elements, invalid IDs, duplicate mapped declarations and
    dangling references are surfaced so intentional negatives can be verified.
    Diagram/custom-assignment internals do not enter mapped-ID uniqueness.
    """
    issues: set[str] = set()
    declarations: dict[str, str] = {}
    containers: dict[str, str] = {}
    references: list[dict] = []
    fields = {
        "Project": {"id", "name", "description", "type", "model", "diagrams", "languages"},
        "Package": {"id", "name", "description", "type", "propertyAssignments", "contents"},
        "Class": {"id", "name", "description", "type", "propertyAssignments", "stereotype",
                  "isAbstract", "isDerived", "properties", "isExtensional", "isPowertype",
                  "order", "literals", "restrictedTo"},
        "Relation": {"id", "name", "description", "type", "propertyAssignments", "stereotype",
                     "isAbstract", "isDerived", "properties"},
        "Property": {"id", "name", "description", "type", "propertyAssignments", "stereotype",
                     "isDerived", "isReadOnly", "isOrdered", "cardinality", "propertyType",
                     "subsettedProperties", "redefinedProperties", "aggregationKind"},
        "Generalization": {"id", "name", "description", "type", "propertyAssignments", "specific", "general"},
        "GeneralizationSet": {"id", "name", "description", "type", "propertyAssignments",
                              "isDisjoint", "isComplete", "categorizer", "generalizations"},
        "Literal": {"id", "name", "description", "type", "propertyAssignments"},
    }

    def reference(value):
        if not isinstance(value, dict) or set(value) != {"id", "type"}:
            issues.add("malformed_reference")
        else:
            references.append(value)

    def visit(value, expected=None):
        if not isinstance(value, dict):
            issues.add("malformed_declaration")
            return
        kind = value.get("type")
        if expected and kind != expected:
            issues.add("wrong_container_type")
        if kind not in fields:
            issues.add("unknown_element")
            return
        for key in set(value) - fields[kind]:
            issues.add("unknown_field:" + key)
        identifier = value.get("id")
        if not _valid_identifier(identifier):
            issues.add("invalid_id")
        elif kind not in {"Project", "Package"}:
            if identifier in declarations:
                issues.add("duplicate_id:" + identifier)
            else:
                declarations[identifier] = kind
        else:
            containers[identifier] = kind
        for key in ("name", "description"):
            text = value.get(key)
            if text is not None and not isinstance(text, str):
                if not (isinstance(text, dict) and all(isinstance(k, str) and isinstance(v, str) and v for k, v in text.items())):
                    issues.add("invalid_text:" + key)
        if kind == "Project":
            visit(value.get("model"), "Package")
            if "languages" in value and not (isinstance(value["languages"], list) and all(isinstance(v, str) and v for v in value["languages"])):
                issues.add("invalid_languages")
        if kind == "Package":
            for member in value.get("contents") or []:
                visit(member)
        if kind in {"Class", "Relation"}:
            properties = value.get("properties")
            if kind == "Relation" and not (isinstance(properties, list) and len(properties) == 2):
                issues.add("nonbinary_relation")
            if kind == "Relation" and isinstance(properties, list):
                if any(not isinstance(end, dict) or end.get("propertyType") is None for end in properties):
                    issues.add("unresolved_endpoint")
            for member in properties or []:
                visit(member, "Property")
        if kind == "Property":
            if value.get("propertyType") is not None:
                reference(value["propertyType"])
            for key in ("subsettedProperties", "redefinedProperties"):
                for target in value.get(key) or []:
                    reference(target)
            cardinality = value.get("cardinality")
            if cardinality is not None and not isinstance(cardinality, str):
                issues.add("invalid_cardinality_type")
        if kind == "Generalization":
            reference(value.get("specific"))
            reference(value.get("general"))
        if kind == "Class":
            literals = value.get("literals")
            if literals is not None and not isinstance(literals, list):
                issues.add("malformed_literals")
            elif isinstance(literals, list):
                for literal in literals:
                    visit(literal, "Literal")
            order = value.get("order")
            if order is not None and not isinstance(order, str):
                issues.add("invalid_order_type")
        if kind == "GeneralizationSet":
            if value.get("categorizer") is not None:
                reference(value["categorizer"])
            members = value.get("generalizations")
            if isinstance(members, list):
                for target in members:
                    reference(target)
            elif members is not None:
                issues.add("malformed_membership")

    visit(document, "Project")
    for target in references:
        identifier = target.get("id")
        if not _valid_identifier(identifier):
            issues.add("invalid_reference_id")
        elif identifier not in declarations:
            issues.add("unresolved_reference:" + identifier)
        elif declarations[identifier] != target.get("type"):
            issues.add("reference_type_mismatch:" + identifier)
    # Audit the concrete presentation variants actually used by our authored
    # fixtures against the 0.5.3 serializers. Their IDs never enter mapped-ID
    # uniqueness. Duplicate omitted views are intentional in one scoped case.
    if isinstance(document, dict):
        for diagram in document.get("diagrams") or []:
            if not isinstance(diagram, dict) or diagram.get("type") != "Diagram" or set(diagram) != {"id", "name", "description", "type", "owner", "contents"}:
                issues.add("malformed_diagram")
                continue
            owner = diagram.get("owner")
            if owner is not None and (not isinstance(owner, dict) or set(owner) != {"id", "type"} or containers.get(owner.get("id")) != owner.get("type")):
                issues.add("unresolved_diagram_owner")
            views = diagram.get("contents")
            if not isinstance(views, list):
                issues.add("malformed_view_collection")
                continue
            view_types = {v.get("id"): v.get("type") for v in views if isinstance(v, dict)}
            for view in views:
                if not isinstance(view, dict):
                    issues.add("malformed_view")
                    continue
                kind = view.get("type")
                expected_fields = {"id", "type", "modelElement", "shape"}
                if kind == "RelationView":
                    expected_fields |= {"source", "target"}
                if kind not in {"ClassView", "RelationView"} or set(view) != expected_fields:
                    issues.add("malformed_view")
                target = view.get("modelElement")
                if not isinstance(target, dict) or set(target) != {"id", "type"} or declarations.get(target.get("id")) != target.get("type"):
                    issues.add("unresolved_view_model_element")
                if kind == "RelationView":
                    for field in ("source", "target"):
                        end = view.get(field)
                        if not isinstance(end, dict) or set(end) != {"id", "type"} or view_types.get(end.get("id")) != end.get("type"):
                            issues.add("unresolved_view_endpoint")
                shape = view.get("shape")
                if not isinstance(shape, dict):
                    issues.add("malformed_shape")
                elif shape.get("type") == "Rectangle":
                    if set(shape) != {"id", "type", "x", "y", "width", "height"}:
                        issues.add("malformed_rectangle")
                elif shape.get("type") == "Path":
                    if set(shape) != {"id", "type", "points"} or not isinstance(shape.get("points"), list) or any(not isinstance(point, dict) or set(point) != {"x", "y"} for point in shape.get("points", [])):
                        issues.add("malformed_path")
                else:
                    issues.add("unknown_shape")
    return frozenset(issues)
