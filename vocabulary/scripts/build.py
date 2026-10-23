"""Validate and publish versioned DirectKG mereology vocabulary representations."""
from __future__ import annotations

import argparse
import calendar
import re
import shutil
import subprocess
from decimal import Decimal, localcontext
from pathlib import Path

from bs4 import BeautifulSoup
from rdflib import BNode, Graph, Literal, Namespace, RDF, RDFS, URIRef
from rdflib.namespace import DCTERMS, OWL, SKOS, XSD
from rdflib.plugins.parsers.notation3 import RDFSink, SinkParser

ROOT = Path(__file__).resolve().parents[2]
BASE = "https://w3id.org/directkg/vocab"
STEM = "dkgm-vocabulary"
RELEASE_RE = re.compile(r"dkgm-vocabulary-v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)\.ttl")
LATEST_NAME = "dkgm-vocabulary.ttl"
DKGM = Namespace(BASE + "#")
VANN = Namespace("http://purl.org/vocab/vann/")
ONTOLOGY = URIRef(BASE)
LICENSE = URIRef("https://creativecommons.org/licenses/by/4.0/")

# DK-GEN-04 in the 2026-10-21 specification and the released 0.1.0 graph.
# One table supplies both the property inventory and ordered chain expectations.
# Register a separately reviewed contract for a future release; never silently
# apply changed rules to historical sources or derive expectations from the input.
SOURCE_CONTRACTS = {
    "0.1.0": {
        DKGM.memberOf: (DKGM.memberOf, DKGM.subCollectionOf),
        DKGM.subCollectionOf: (DKGM.subCollectionOf, DKGM.subCollectionOf),
        DKGM.subQuantityOf: (DKGM.subQuantityOf, DKGM.subQuantityOf),
        DKGM.componentOf: None,
    },
}

# RFC 5646 syntax, without a network-dependent language registry lookup.
LANGUAGE_RE = re.compile(r"""
    (?:[A-Za-z]{2,3}(?:-[A-Za-z]{3}){0,3}|[A-Za-z]{4}|[A-Za-z]{5,8})
    (?:-[A-Za-z]{4})?(?:-(?:[A-Za-z]{2}|[0-9]{3}))?
    (?P<variants>(?:-(?:[A-Za-z0-9]{5,8}|[0-9][A-Za-z0-9]{3}))*)
    (?P<extensions>(?:-[0-9A-WY-Za-wy-z](?:-[A-Za-z0-9]{2,8})+)*)
    (?:-x(?:-[A-Za-z0-9]{1,8})+)?
""", re.VERBOSE)
GRANDFATHERED_LANGUAGES = frozenset("""
    en-gb-oed i-ami i-bnn i-default i-enochian i-hak i-klingon i-lux
    i-mingo i-navajo i-pwn i-tao i-tay i-tsu sgn-be-fr sgn-be-nl
    sgn-ch-de art-lojban cel-gaulish no-bok no-nyn zh-guoyu zh-hakka
    zh-min zh-min-nan zh-xiang
""".split())
DATE_TIME_RE = re.compile(
    r"(?P<year>-?(?:[0-9]{4}|[1-9][0-9]{4,}))-"
    r"(?P<month>[0-9]{2})-(?P<day>[0-9]{2})T"
    r"(?P<hour>[0-9]{2}):(?P<minute>[0-9]{2}):(?P<second>[0-9]{2})"
    r"(?P<fraction>\.[0-9]+)?(?P<zone>Z|[+-][0-9]{2}:[0-9]{2})?"
)


class _LexicalSink(RDFSink):
    """Keep lexical forms: RDFLib normalization can hide invalid date syntax.

    Use the same Turtle parser as Graph.parse, with a narrow literal-construction
    adapter for the pinned RDFLib version, without changing global RDFLib flags.
    """

    def newLiteral(self, text, datatype, language):
        return Literal(text, datatype=datatype, lang=language, normalize=False)


def _source_graph(file: Path) -> Graph:
    graph = Graph()
    parser = SinkParser(_LexicalSink(graph), baseURI=file.resolve().as_uri(), turtle=True)
    try:
        with file.open("rb") as stream:
            parser.loadStream(stream)
    except Exception as error:
        raise ValueError(f"{file}: expected valid Turtle; observed {error}") from error
    return graph


def _check(file, subject, predicate, condition, expected, observed):
    require(condition,
            f"{file}: {subject} / {predicate}: expected {expected}; observed {observed}")


def _values(file, graph, subject, predicate, *, single=False):
    values = set(graph.objects(subject, predicate))
    _check(file, subject, predicate, len(values) == 1 if single else bool(values),
           "exactly one value" if single else "at least one value",
           sorted(value.n3() for value in values))
    return values


def _valid_language(tag):
    tag = tag.lower()
    if tag in GRANDFATHERED_LANGUAGES or re.fullmatch(r"x(?:-[a-z0-9]{1,8})+", tag):
        return True
    match = LANGUAGE_RE.fullmatch(tag)
    if match is None:
        return False
    variants = match["variants"].split("-")[1:]
    singletons = [part for part in match["extensions"].split("-") if len(part) == 1]
    return len(variants) == len(set(variants)) and len(singletons) == len(set(singletons))


def _text(file, subject, predicate, values, *, english=False):
    for value in values:
        valid = (isinstance(value, Literal) and bool(str(value).strip())
                 and value.datatype in (None, XSD.string, RDF.langString)
                 and (value.datatype != RDF.langString or value.language is not None)
                 and (value.language is None or _valid_language(value.language)))
        _check(file, subject, predicate, valid,
               "nonempty text with a valid language tag when supplied", value.n3())
    if english:
        _check(file, subject, predicate,
               any(value.language and value.language.lower().split("-")[0] == "en"
                   for value in values),
               "at least one English literal", sorted(value.n3() for value in values))


def _date_time(file, predicate, value):
    """Return exact Gregorian seconds and timezone presence, including fractions.

    Decimal avoids truncating valid sub-microsecond differences. Timezone-less
    values are not silently assigned the execution machine's local timezone.
    """
    match = DATE_TIME_RE.fullmatch(str(value).strip(" \t\r\n"))
    valid = isinstance(value, Literal) and value.datatype == XSD.dateTime and match
    _check(file, ONTOLOGY, predicate, valid, "an xsd:dateTime literal", value.n3())
    year, month, day, hour, minute, second = (
        int(match[key]) for key in ("year", "month", "day", "hour", "minute", "second"))
    fraction = Decimal(match["fraction"] or "0")
    zone = match["zone"]
    offset = 0
    if zone and zone != "Z":
        hours, minutes = int(zone[1:3]), int(zone[4:6])
        _check(file, ONTOLOGY, predicate,
               hours <= 14 and minutes <= 59 and (hours != 14 or minutes == 0),
               "a timezone offset within -14:00 to +14:00", value.n3())
        offset = (hours * 3600 + minutes * 60) * (1 if zone[0] == "+" else -1)
    valid = (1 <= month <= 12 and 1 <= day <= calendar.monthrange(year, month)[1]
             and 0 <= minute < 60 and 0 <= second < 60
             and (0 <= hour < 24 or (hour == 24 and minute == second == fraction == 0))
             and not (match["year"].startswith("-") and year == 0))
    _check(file, ONTOLOGY, predicate, valid, "a valid Gregorian date and time", value.n3())
    preceding_year = year - 1
    days = (365 * preceding_year + preceding_year // 4 - preceding_year // 100
            + preceding_year // 400
            + sum(calendar.monthrange(year, m)[1] for m in range(1, month)) + day - 1)
    whole_seconds = days * 86400 + hour * 3600 + minute * 60 + second - offset
    with localcontext() as context:
        context.prec = len(str(abs(whole_seconds))) + len(match["fraction"] or "") + 2
        seconds = Decimal(whole_seconds) + fraction
    return seconds, zone is not None


def _chain(file, graph, conclusion, head):
    operands, triples, visited = [], set(), set()
    node = head
    while node != RDF.nil:
        _check(file, conclusion, OWL.propertyChainAxiom,
               isinstance(node, (BNode, URIRef)) and node not in visited,
               "an acyclic RDF collection terminating at rdf:nil", node.n3())
        visited.add(node)
        first = _values(file, graph, node, RDF.first, single=True).pop()
        rest = _values(file, graph, node, RDF.rest, single=True).pop()
        operands.append(first)
        triples.update(((node, RDF.first, first), (node, RDF.rest, rest)))
        # Only binary chains are approved; bound traversal even for hostile input.
        _check(file, conclusion, OWL.propertyChainAxiom, len(operands) <= 2,
               "a two-operand RDF collection", [value.n3() for value in operands])
        node = rest
    return tuple(operands), triples, visited


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def version_of(path: Path) -> str:
    match = RELEASE_RE.fullmatch(path.name)
    require(match is not None, f"Invalid release filename: {path.name}; use {STEM}-vX.Y.Z.ttl")
    return ".".join(match.groups())


def releases() -> list[Path]:
    directory = ROOT / "vocabulary/versioned"
    require(directory.is_dir(), f"Missing release directory: {directory}")
    require(not any(path.is_dir() for path in directory.iterdir()),
            "Versioned releases must be flat files, not version subdirectories")
    files = list(directory.glob("*.ttl"))
    require(bool(files), "No versioned Turtle releases found")
    for file in files:
        version_of(file)
    return sorted(files, key=lambda file: tuple(map(int, version_of(file).split("."))))


def validate_release(file: Path) -> None:
    """Validate source RDF only, using its explicitly registered release contract."""
    version = version_of(file)
    graph = _source_graph(file)
    ontologies = set(graph.subjects(RDF.type, OWL.Ontology))
    _check(file, ONTOLOGY, RDF.type, ontologies == {ONTOLOGY},
           "exactly the canonical owl:Ontology", sorted(node.n3() for node in ontologies))
    versions = _values(file, graph, ONTOLOGY, OWL.versionIRI, single=True)
    _check(file, ONTOLOGY, OWL.versionIRI, versions == {URIRef(f"{BASE}/{version}")},
           f"the release filename's version IRI <{BASE}/{version}>",
           sorted(node.n3() for node in versions))
    for predicate, expected, datatypes in (
        (OWL.versionInfo, version, (None, XSD.string)),
        (VANN.preferredNamespacePrefix, "dkgm", (None, XSD.string)),
        (VANN.preferredNamespaceUri, str(DKGM), (None, XSD.string, XSD.anyURI)),
    ):
        value = _values(file, graph, ONTOLOGY, predicate, single=True).pop()
        _check(file, ONTOLOGY, predicate,
               isinstance(value, Literal) and value.language is None
               and value.datatype in datatypes and str(value) == expected,
               f"the literal {expected!r}", value.n3())

    _check(file, ONTOLOGY, OWL.versionInfo, version in SOURCE_CONTRACTS,
           "an explicitly reviewed source-validation contract for this release",
           f"unregistered version {version}; register its approved contract before validation")
    contract = SOURCE_CONTRACTS[version]

    for predicate in (DCTERMS.title, DCTERMS.description):
        _text(file, ONTOLOGY, predicate, _values(file, graph, ONTOLOGY, predicate))
    creators = _values(file, graph, ONTOLOGY, DCTERMS.creator)
    for creator in creators:
        _check(file, ONTOLOGY, DCTERMS.creator, isinstance(creator, URIRef),
               "one or more creator IRIs", creator.n3())
    license_value = _values(file, graph, ONTOLOGY, DCTERMS.license, single=True).pop()
    _check(file, ONTOLOGY, DCTERMS.license, license_value == LICENSE,
           f"the established license IRI <{LICENSE}>", license_value.n3())
    date_predicates = (DCTERMS.created, DCTERMS.modified)
    date_values = [_values(file, graph, ONTOLOGY, predicate, single=True).pop()
                   for predicate in date_predicates]
    dates = [_date_time(file, predicate, value)
             for predicate, value in zip(date_predicates, date_values)]
    created, modified = dates
    # XML Schema comparison is partial when only one value has a timezone.
    # Require an established order across the possible +/-14-hour interval.
    uncertainty = Decimal(14 * 3600) if created[1] != modified[1] else Decimal(0)
    with localcontext() as context:
        context.prec = max(len(value[0].as_tuple().digits) for value in dates) + 10
        ordered = created[0] + uncertainty <= modified[0]
    _check(file, ONTOLOGY, DCTERMS.modified, ordered,
           "created <= modified with unambiguous timezone ordering",
           f"created={date_values[0].n3()}, modified={date_values[1].n3()}")

    for node in set(graph.all_nodes()) | set(graph.predicates()):
        if isinstance(node, URIRef) and str(node).startswith(str(DKGM)):
            _check(file, node, RDF.type, node in contract,
                   "one of the four approved DKGM property IRIs", node.n3())
    for term in contract:
        _check(file, term, RDF.type,
               (term, RDF.type, OWL.ObjectProperty) in graph,
               "an explicit owl:ObjectProperty declaration",
               sorted(node.n3() for node in graph.objects(term, RDF.type)))
        for predicate in (RDFS.label, SKOS.definition):
            _text(file, term, predicate, _values(file, graph, term, predicate), english=True)

    approved = {(ONTOLOGY, RDF.type, OWL.Ontology)}
    approved.update((term, RDF.type, OWL.ObjectProperty) for term in contract)
    list_nodes = set()
    for conclusion, head in graph.subject_objects(OWL.propertyChainAxiom):
        expected = contract.get(conclusion)
        _check(file, conclusion, OWL.propertyChainAxiom, expected is not None,
               "a chain on an approved chain-bearing property", head.n3())
        operands, list_triples, nodes = _chain(file, graph, conclusion, head)
        _check(file, conclusion, OWL.propertyChainAxiom, operands == expected,
               [str(term) for term in expected], [value.n3() for value in operands])
        approved.add((conclusion, OWL.propertyChainAxiom, head))
        approved.update(list_triples)
        list_nodes.update(nodes)
    for term, operands in contract.items():
        if operands is not None:
            _values(file, graph, term, OWL.propertyChainAxiom)

    # Closed logical contract, not a general ban on future approved evolution:
    # only declarations/chains above and existing descriptive predicates below.
    # This also catches incoming alignments and source-specific axioms whose
    # subjects are outside the DKGM namespace, not just axioms on local subjects.
    ontology_annotations = {
        DCTERMS.title, DCTERMS.description, DCTERMS.creator, DCTERMS.license,
        DCTERMS.created, DCTERMS.modified, VANN.preferredNamespacePrefix,
        VANN.preferredNamespaceUri, OWL.versionIRI, OWL.versionInfo,
        RDFS.label, RDFS.comment, RDFS.seeAlso,
    }
    for subject, predicate, value in graph:
        if (subject, predicate, value) in approved:
            continue
        if subject in list_nodes | {RDF.nil} and predicate == RDF.type and value == RDF.List:
            continue
        allowed = (subject == ONTOLOGY and predicate in ontology_annotations
                   or subject in contract and predicate in {
                       RDFS.label, SKOS.definition, RDFS.comment, RDFS.seeAlso}
                   or subject in creators and predicate == RDFS.label)
        _check(file, subject, predicate, allowed,
               "only the release contract's declarations, chains and descriptive metadata",
               value.n3())
        if predicate in {RDFS.label, SKOS.definition, RDFS.comment}:
            _text(file, subject, predicate, {value})
        elif predicate == RDFS.seeAlso:
            _check(file, subject, predicate, isinstance(value, URIRef),
                   "an IRI", value.n3())


def check_sources(base: str | None = None, files: list[Path] | None = None) -> None:
    """Read-only source validation; deliberately independent of HTML/latest checks."""
    check_immutable(base)
    sources = releases() if files is None else files
    require(bool(sources), "No vocabulary source files selected")
    for source in sources:
        validate_release(source)
    print(f"Validated {len(sources)} vocabulary source(s); no files generated or modified.")


def check_immutable(base: str | None) -> None:
    """Previously committed versioned artifacts must not be changed or removed."""
    if not base or set(base) == {"0"}:
        return
    paths = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", base, "--", "vocabulary/versioned"],
        cwd=ROOT, text=True).splitlines()
    for path in paths:
        original = subprocess.check_output(["git", "show", f"{base}:{path}"], cwd=ROOT)
        current = ROOT / path
        require(current.is_file() and current.read_bytes() == original,
                f"Immutable release file changed or removed: {path}; create a new release")


def customize_documentation(output: Path, source: Path) -> None:
    """Reuse the reference repository's source-derived SKOS definitions in PyLODE."""
    graph = Graph().parse(source, format="turtle")
    soup = BeautifulSoup(output.read_text(encoding="utf-8"), "html.parser")
    require(soup.head is not None and soup.select_one("#metadata") is not None,
            "Unexpected PyLODE output structure")
    for entity in soup.select(".property.entity"):
        table = entity.find("table")
        iri = table.select_one("tr td code") if table else None
        require(iri is not None, "PyLODE property block is missing its IRI")
        term = URIRef(iri.get_text(strip=True))
        definitions = sorted(graph.objects(term, SKOS.definition), key=lambda value: value.n3())
        if not definitions:
            continue
        require(table.find("a", href=str(SKOS.definition)) is None,
                "PyLODE already contains a Definition row; review generator compatibility")
        row = soup.new_tag("tr")
        header = soup.new_tag("th")
        label = soup.new_tag("a", href=str(SKOS.definition))
        label["class"] = ["hover_property"]
        label.string = "Definition"
        header.append(label)
        row.append(header)
        cell = soup.new_tag("td")
        for definition in definitions:
            paragraph = soup.new_tag("p")
            if definition.language:
                paragraph["lang"] = definition.language
            paragraph.string = str(definition)
            cell.append(paragraph)
        row.append(cell)
        defined_by = table.find("a", href="http://www.w3.org/2000/01/rdf-schema#isDefinedBy")
        anchor = defined_by.find_parent("tr") if defined_by else table.find("tr")
        require(anchor is not None, "PyLODE property block has no table rows")
        anchor.insert_after(row)
    output.write_text(str(soup), encoding="utf-8")


def check_documentation(file: Path, version: str) -> None:
    soup = BeautifulSoup(file.read_text(encoding="utf-8"), "html.parser")
    for predicate, expected in (
        (OWL.versionIRI, f"{BASE}/{version}"),
        (OWL.versionInfo, version),
    ):
        labels = soup.select(f'dt a[href="{predicate}"]')
        require(len(labels) == 1, f"{file.name}: missing or ambiguous {predicate}")
        field = labels[0].find_parent("dt").find_next_sibling("dd")
        require(field is not None and field.get_text(strip=True) == expected,
                f"{file.name}: PyLODE version metadata does not match {version}")


def build(base: str | None = None) -> None:
    check_immutable(base)
    versions = releases()
    for source in versions:
        validate_release(source)
        html = source.with_suffix(".html")
        if not html.exists():
            temporary = source.with_suffix(".tmp.html")
            try:
                subprocess.run(["pylode", str(source), "-p", "ontpub",
                                "-c", "true", "-o", str(temporary)], check=True)
                customize_documentation(temporary, source)
                check_documentation(temporary, version_of(source))
                temporary.replace(html)
            finally:
                temporary.unlink(missing_ok=True)
        check_documentation(html, version_of(source))
    current = versions[-1]
    latest = ROOT / "vocabulary/latest"
    latest.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(current, latest / LATEST_NAME)
    shutil.copyfile(current.with_suffix(".html"), latest / "index.html")
    require((latest / LATEST_NAME).read_bytes() == current.read_bytes(),
            "Latest Turtle differs from highest release")
    require((latest / "index.html").read_bytes() == current.with_suffix(".html").read_bytes(),
            "Latest HTML differs from highest release")
    require({p.name for p in latest.iterdir()} == {LATEST_NAME, "index.html"},
            "Unexpected files in latest publication directory")
    print(f"Validated {len(versions)} release(s); latest={version_of(current)}; "
          "Pages artifact: vocabulary/latest/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", help="Git commit for immutable release comparison")
    parser.add_argument("--check-only", action="store_true",
                        help="Validate existing Turtle sources without generating or publishing files")
    parser.add_argument("sources", nargs="*", type=Path,
                        help="Versioned Turtle sources for --check-only (default: all releases)")
    args = parser.parse_args()
    if args.sources and not args.check_only:
        parser.error("Explicit source files require --check-only")
    try:
        if args.check_only:
            check_sources(args.base, args.sources or None)
        else:
            build(args.base)
    except Exception as error:
        operation = "validation" if args.check_only else "publication"
        raise SystemExit(f"Vocabulary {operation} failed: {error}") from error
