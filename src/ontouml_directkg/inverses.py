"""Allocate named inverses after source-backed claims and final IRIs (DK-INV)."""

from collections import Counter, defaultdict

from rdflib import URIRef

from .annotations import source_text
from .identity import class_name_candidate, escape_id, naming_text, normalize_name
from .relations import Relation


def role_present(value: object) -> bool:
    return any(text.strip() for _, text in source_text(value))


def allocate_inverses(relations: tuple[Relation, ...], resources: dict[str, URIRef],
                       base: str, strategy: str, mode: str, claimed_names: set[str]) -> dict[str, URIRef]:
    selected = {}
    for relation in relations:
        end = relation.source_end
        present = role_present(end.data.get("name"))
        if (mode == "none" or (mode == "named" and not present)
                or (mode == "informed" and not present and end.data.get("cardinality") is None)):
            continue
        selected[end.data["id"]] = relation
    if strategy == "id":
        result = {identifier: URIRef(base + escape_id(identifier)) for identifier in selected}
        if len(set(result.values()) | set(resources.values())) != len(result) + len(resources):
            raise NotImplementedError("Exceptional escaped-ID collision disposition requires an Architect decision")
        return result

    claims = claimed_names | {str(resource).removeprefix(base) for resource in resources.values()}
    names, fallbacks, stages = {}, {}, {}
    for identifier, relation in selected.items():
        local = str(resources[relation.target_end.data["id"]]).removeprefix(base)
        fallbacks[identifier] = "inverseOf" + local[:1].upper() + local[1:]
        role = relation.source_end.data.get("name")
        selected_text = naming_text(role)
        if role_present(role) and selected_text is not None:
            names[identifier], stages[identifier] = normalize_name(selected_text), 0
        else:
            names[identifier], stages[identifier] = fallbacks[identifier], 1
    while True:
        counts = Counter(names.values())
        collisions = {identifier for identifier, name in names.items()
                      if name in claims or counts[name] > 1}
        if not collisions:
            return {identifier: URIRef(base + name) for identifier, name in names.items()}
        role_collisions = {identifier for identifier in collisions if stages[identifier] == 0}
        if role_collisions:
            for identifier in role_collisions:
                names[identifier], stages[identifier] = fallbacks[identifier], 1
            continue
        fallback_collisions = {identifier for identifier in collisions if stages[identifier] == 1}
        if fallback_collisions:
            for identifier in fallback_collisions:
                domain = selected[identifier].range.data
                qualifier = class_name_candidate(domain["id"], domain.get("name"))
                names[identifier] = fallbacks[identifier] + "_" + qualifier
                stages[identifier] = 2
            continue
        # Retained inverses reserve their names before any group is numbered.
        reserved = claims | {name for identifier, name in names.items() if identifier not in collisions}
        groups = defaultdict(list)
        for identifier in collisions:
            groups[names[identifier]].append(identifier)
        for name in sorted(groups):
            number = 1
            for identifier in sorted(groups[name]):
                # Keep the original qualified name, including source numeric text.
                while f"{name}_{number}" in reserved:
                    number += 1
                names[identifier] = f"{name}_{number}"
                reserved.add(names[identifier])
                number += 1
        return {identifier: URIRef(base + name) for identifier, name in names.items()}
