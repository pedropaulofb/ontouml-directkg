"""Separate IRI syntax, lexical names and source-ID identity (DK-IRI)."""

from collections import defaultdict
from collections.abc import Iterable
from ipaddress import IPv6Address
import re
import string
import unicodedata

DEFAULT_BASE = "https://example.org/directkg#"
_LANGUAGE_TAG_RE = re.compile(r"[a-zA-Z]+(?:-[a-zA-Z0-9]+)*")

# RFC 3987 section 2.2: private characters are permitted only in queries.
# Validate original characters; never trim, normalize, resolve or repair a base.
_UCS = (
    "\u00a0-\ud7ff\uf900-\ufdcf\ufdf0-\uffef"
    + "".join(chr(start) + "-" + chr(start + 0xFFFD)
              for start in range(0x10000, 0xE0000, 0x10000))
    + "\U000e1000-\U000efffd"
)
_PRIVATE = "\ue000-\uf8ff\U000f0000-\U000ffffd\U00100000-\U0010fffd"
_UNRESERVED = rf"[A-Za-z0-9_.~{_UCS}-]"
_SUBDELIMS = r"[!$&'()*+,;=]"
_TOKEN = rf"(?:{_UNRESERVED}|%[0-9A-Fa-f]{{2}}|{_SUBDELIMS})"
_PCHAR = rf"(?:{_TOKEN}|[:@])"
_REG_NAME = re.compile(rf"{_TOKEN}*")
_USERINFO = re.compile(rf"(?:{_TOKEN}|:)*")
_PATH = re.compile(rf"(?:{_PCHAR}|/)*")
_QUERY = re.compile(rf"(?:{_PCHAR}|[/?{_PRIVATE}])*")
_FRAGMENT = re.compile(rf"(?:{_PCHAR}|[/?])*")
_FUTURE_IP = re.compile(r"[vV][A-Fa-f0-9]+\.[A-Za-z0-9_.~!$&'()*+,;=:-]+")


class ConfigurationError(ValueError):
    """Rejected configuration before conversion, with no conversion result."""


def _valid_authority(value: str) -> bool:
    if "@" in value:
        userinfo, value = value.rsplit("@", 1)
        if _USERINFO.fullmatch(userinfo) is None:
            return False
    if value.startswith("["):
        end = value.find("]")
        if end == -1:
            return False
        host, suffix = value[1:end], value[end + 1:]
        if _FUTURE_IP.fullmatch(host) is None:
            try:
                # Scoped addresses are outside RFC 3987's IP-literal grammar.
                if "%" in host:
                    return False
                IPv6Address(host)
            except ValueError:
                return False
    else:
        host, separator, port = value.partition(":")
        suffix = separator + port
        if _REG_NAME.fullmatch(host) is None:
            return False
    return suffix == "" or re.fullmatch(r":[0-9]*", suffix) is not None


def is_absolute_iri(value: str) -> bool:
    """Check RFC 3987 IRI syntax with a scheme, without network or rewriting.

    RDF IRIs may have fragments. This uses the scheme-bearing ``IRI`` grammar,
    not the RFC's narrower ``absolute-IRI`` production that excludes fragments.
    """
    match = re.match(r"[A-Za-z][A-Za-z0-9+.-]*:", value)
    if match is None:
        return False
    hierarchical, mark, fragment = value[match.end():].partition("#")
    if mark and _FRAGMENT.fullmatch(fragment) is None:
        return False
    hierarchical, mark, query = hierarchical.partition("?")
    if mark and _QUERY.fullmatch(query) is None:
        return False
    if hierarchical.startswith("//"):
        authority, slash, path = hierarchical[2:].partition("/")
        return _valid_authority(authority) and _PATH.fullmatch(slash + path) is not None
    return _PATH.fullmatch(hierarchical) is not None


def select_base(supplied: str | None) -> tuple[str, str]:
    """Validate supplied, effective and ontology IRIs before any input is read."""
    if supplied is not None and (not isinstance(supplied, str) or not is_absolute_iri(supplied)):
        raise ConfigurationError("base_iri must be a syntactically valid absolute RDF IRI")
    base = DEFAULT_BASE if supplied is None else supplied
    if not base.endswith(("#", "/")):
        base += "#"
    ontology = base[:-1] if base.endswith("#") else base
    if not is_absolute_iri(base) or not is_absolute_iri(ontology):
        raise ConfigurationError("The effective entity base and derived ontology IRI must both be valid")
    return base, ontology


def normalize_name(value: str) -> str:
    """Apply lexical normalization without semantic rewriting (DK-IRI-03)."""
    text = unicodedata.normalize("NFD", value).strip()
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = "".join("_" if char.isspace() or char in string.punctuation
                   or unicodedata.category(char).startswith("P") else char for char in text)
    text = re.sub(r"_+", "_", text).strip("_")
    text = "".join(char for char in text if char in string.ascii_letters + string.digits + "_")
    return "_" + text if text[:1].isdigit() else text


def escape_id(identifier: str, *, whole_local_name: bool = True) -> str:
    """Injectively escape original UTF-8 bytes, including underscores (DK-IRI-05)."""
    result = "".join(chr(byte) if 65 <= byte <= 90 or 97 <= byte <= 122 or 48 <= byte <= 57
                     else f"_x{byte:02X}" for byte in identifier.encode("utf-8"))
    return "id_" + result if whole_local_name and result[:1].isdigit() else result


def check_id_candidate_collisions(candidates: Iterable[tuple[str, str]]) -> None:
    """Require unique candidates within one DK-IRI-05 construction."""
    claims: dict[str, str] = {}
    for identifier, candidate in candidates:
        if candidate in claims:
            raise RuntimeError(
                f"Distinct source IDs {claims[candidate]!r} and {identifier!r} "
                f"produced the same IRI candidate {str(candidate)!r} under DK-IRI-05"
            )
        claims[candidate] = identifier


def is_valid_language_tag(value: object) -> bool:
    """Validate nonempty tags against the simplified lexical rule (RD-02)."""
    return isinstance(value, str) and _LANGUAGE_TAG_RE.fullmatch(value) is not None


def valid_textual_value(value: object) -> str | dict[str, str] | None:
    """Retain only supported plain-string or valid languageString entries."""
    if value is None or isinstance(value, str):
        return value
    if isinstance(value, dict):
        return {
            key: text
            for key, text in value.items()
            if isinstance(key, str) and (key == "" or is_valid_language_tag(key)) and isinstance(text, str)
        }
    return None


def naming_text(value: object) -> str | None:
    """Select original localized text using DK-IRI-10's original-key ordering."""
    cleaned = valid_textual_value(value)
    if cleaned is None:
        return None
    if isinstance(cleaned, str):
        return cleaned if normalize_name(cleaned) else None
    lower_ascii = str.maketrans(string.ascii_uppercase, string.ascii_lowercase)
    candidates = [(key.translate(lower_ascii), text) for key, text in cleaned.items()
                  if normalize_name(text)]
    return min(candidates)[1] if candidates else None


def missing_name(value: object) -> bool:
    """Missing descriptive text is distinct from unusable ASCII naming text."""
    cleaned = valid_textual_value(value)
    if cleaned is None:
        return True
    if isinstance(cleaned, str):
        return not cleaned.strip()
    return not any(v.strip() for v in cleaned.values())


def class_name_candidate(identifier: str, name: object) -> str:
    """Return the class candidate before collision suffixes, also used as qualifier."""
    selected = naming_text(name)
    return normalize_name(selected) if selected is not None else "unnamedClass_" + escape_id(identifier, whole_local_name=False)


def resolve_name_collisions(candidates: dict[str, str]) -> dict[str, str]:
    """Suffix every colliding member deterministically, including new collisions.

    A generated suffix can itself meet another candidate. Reapplying the same
    group rule prevents merging in that case; no unsuffixed winner is selected.
    """
    resolved = candidates.copy()
    while True:
        groups: dict[str, list[str]] = defaultdict(list)
        for identifier, candidate in resolved.items():
            groups[candidate].append(identifier)
        collisions = {name: ids for name, ids in groups.items() if len(ids) > 1}
        if not collisions:
            return resolved
        for name, identifiers in collisions.items():
            for number, identifier in enumerate(sorted(identifiers), 1):
                resolved[identifier] = f"{name}_{number}"
