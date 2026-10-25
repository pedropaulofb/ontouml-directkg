"""Classifier-side primitive recognition (DK-DAT-01–02/04–05).

Only this registry can suppress a datatype's local class. Attribute/range
mapping remains a separate increment; recognition does not invent aliases.
"""

import re
import unicodedata

from rdflib import URIRef
from rdflib.namespace import XSD

from .identity import naming_text

PRIMITIVES: dict[str, URIRef] = {
    "boolean": XSD.boolean, "byte": XSD.byte, "char": XSD.string,
    "double": XSD.double, "float": XSD.float, "int": XSD.int,
    "long": XSD.long, "short": XSD.short, "string": XSD.string,
}


def datatype_key(name: object) -> str | None:
    """Return a registered key, recognized unsupported void, or custom (None).

    Localized names use the same original-text selector under both strategies.
    Plain strings go directly through primitive normalization, independently
    of whether their text can supply an ASCII IRI candidate.
    """
    selected = name if isinstance(name, str) else naming_text(name)
    if selected is None:
        return None
    key = unicodedata.normalize("NFKC", selected).strip().casefold()
    for prefix in ("xsd:", str(XSD).casefold()):
        if key.startswith(prefix):
            key = key[len(prefix):]
            break
    key = re.sub(r"[\s_-]+", "", key)
    return key if key in PRIMITIVES or key == "void" else None
