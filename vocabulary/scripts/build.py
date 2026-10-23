"""Validate and publish versioned DirectKG mereology vocabulary representations."""
from __future__ import annotations

import argparse
import base64
import calendar
import json
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from decimal import Decimal, localcontext
from pathlib import Path
from urllib.parse import unquote, urlsplit

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
PROJECT_DOCS = URIRef("https://w3id.org/directkg/docs")
PROJECT_REPOSITORY = URIRef("https://w3id.org/directkg/git")
LOGO = "branding/ontouml-directkg-logo-transparent.png"
FAVICON = "branding/favicon/favicon.svg"
# Reviewed main before the feature waves: an independent Git object containing
# the established 0.1.0 snapshots. Later accepted main history extends this floor.
PUBLICATION_ANCHOR = "957a83454a3bcc9fcf73388fb2d2e2bb467a4561"
TRUSTED_MAIN = "refs/remotes/origin/main"


@dataclass(frozen=True)
class SourceContract:
    properties: dict
    documented: bool = False

# DK-GEN-04 in the 2026-10-21 specification and the released 0.1.0 graph.
# One table supplies both the property inventory and ordered chain expectations.
# Register a separately reviewed contract for a future release; never silently
# apply changed rules to historical sources or derive expectations from the input.
SOURCE_CONTRACTS = {
    "0.1.0": SourceContract({
        DKGM.memberOf: (DKGM.memberOf, DKGM.subCollectionOf),
        DKGM.subCollectionOf: (DKGM.subCollectionOf, DKGM.subCollectionOf),
        DKGM.subQuantityOf: (DKGM.subQuantityOf, DKGM.subQuantityOf),
        DKGM.componentOf: None,
    }),
}
# Descriptive additions and documentation requirements; the logical map is shared.
SOURCE_CONTRACTS["0.1.1"] = SourceContract(SOURCE_CONTRACTS["0.1.0"].properties, documented=True)

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


def version_key(version: str) -> tuple[int, ...]:
    return tuple(map(int, version.split(".")))


def next_version(previous: str, increment: str) -> str:
    """Calculate an explicitly selected patch/minor increment, not its policy."""
    version_of(Path(f"{STEM}-v{previous}.ttl"))
    require(increment in {"patch", "minor"}, "Choose a patch or minor increment")
    major, minor, patch = version_key(previous)
    return f"{major}.{minor}.{patch + 1}" if increment == "patch" else f"{major}.{minor + 1}.0"


def predecessor(file: Path, history: list[Path]) -> URIRef | None:
    """Derive history from actual release files, never from a maintained list."""
    version = version_of(file)
    versions = [version_of(path) for path in history]
    require(len(versions) == len(set(versions)), f"{file}: ambiguous duplicate release versions")
    earlier = [path for path in history if version_key(version_of(path)) < version_key(version)]
    if not earlier:
        return None
    previous = max(earlier, key=lambda path: version_key(version_of(path)))
    graph = _source_graph(previous)
    expected = URIRef(f"{BASE}/{version_of(previous)}")
    values = _values(previous, graph, ONTOLOGY, OWL.versionIRI, single=True)
    _check(previous, ONTOLOGY, OWL.versionIRI, values == {expected},
           f"the predecessor's filename-derived version IRI <{expected}>",
           sorted(value.n3() for value in values))
    return expected


def releases(directory: Path | None = None) -> list[Path]:
    directory = ROOT / "vocabulary/versioned" if directory is None else directory
    require(directory.is_dir(), f"Missing release directory: {directory}")
    require(not any(path.is_dir() for path in directory.iterdir()),
            "Versioned releases must be flat files, not version subdirectories")
    files = list(directory.glob("*.ttl"))
    require(bool(files), "No versioned Turtle releases found")
    for file in files:
        version_of(file)
    return sorted(files, key=lambda file: version_key(version_of(file)))


def validate_release(file: Path, history: list[Path] | None = None) -> None:
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
    policy = SOURCE_CONTRACTS[version]
    contract = policy.properties

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

    for term in contract:
        _check(file, term, RDF.type,
               (term, RDF.type, OWL.ObjectProperty) in graph,
               "an explicit owl:ObjectProperty declaration",
               sorted(node.n3() for node in graph.objects(term, RDF.type)))
        for predicate in (RDFS.label, SKOS.definition):
            _text(file, term, predicate, _values(file, graph, term, predicate), english=True)

    if policy.documented:
        previous = predecessor(file, releases() if history is None else history)
        values = set(graph.objects(ONTOLOGY, OWL.priorVersion))
        expected = {previous} if previous is not None else set()
        _check(file, ONTOLOGY, OWL.priorVersion, values == expected,
               f"the immediately preceding release {previous}" if previous else "no predecessor",
               sorted(value.n3() for value in values))
        _check(file, ONTOLOGY, RDFS.seeAlso,
               set(graph.objects(ONTOLOGY, RDFS.seeAlso)) == {PROJECT_DOCS, PROJECT_REPOSITORY},
               "the verified project documentation and repository IRIs",
               sorted(value.n3() for value in graph.objects(ONTOLOGY, RDFS.seeAlso)))
        for term in contract:
            values = _values(file, graph, term, RDFS.isDefinedBy, single=True)
            _check(file, term, RDFS.isDefinedBy, values == {ONTOLOGY},
                   f"the established ontology IRI <{ONTOLOGY}>",
                   sorted(value.n3() for value in values))
        for subject, predicate in ((ONTOLOGY, SKOS.scopeNote),
                                   (DKGM.memberOf, SKOS.scopeNote),
                                   (DKGM.memberOf, SKOS.example),
                                   (DKGM.componentOf, SKOS.scopeNote)):
            _text(file, subject, predicate, _values(file, graph, subject, predicate), english=True)

    for node in set(graph.all_nodes()) | set(graph.predicates()):
        if isinstance(node, URIRef) and str(node).startswith(str(DKGM)):
            _check(file, node, RDF.type, node in contract,
                   "one of the four approved DKGM property IRIs", node.n3())

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
    term_annotations = {RDFS.label, SKOS.definition, RDFS.comment, RDFS.seeAlso}
    if policy.documented:
        ontology_annotations.update({OWL.priorVersion, SKOS.scopeNote})
        term_annotations.update({RDFS.isDefinedBy, SKOS.scopeNote, SKOS.example})
    for subject, predicate, value in graph:
        if (subject, predicate, value) in approved:
            continue
        if subject in list_nodes | {RDF.nil} and predicate == RDF.type and value == RDF.List:
            continue
        allowed = (subject == ONTOLOGY and predicate in ontology_annotations
                   or subject in contract and predicate in term_annotations
                   or subject in creators and predicate == RDFS.label)
        _check(file, subject, predicate, allowed,
               "only the release contract's declarations, chains and descriptive metadata",
               value.n3())
        if predicate in {RDFS.label, SKOS.definition, RDFS.comment, SKOS.scopeNote, SKOS.example}:
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


def prepare_release(draft: Path, increment: str, base: str | None = None) -> Path:
    """Explicitly create one new source; ordinary builds never rewrite Turtle.

    A maintainer edits the draft's annotations and factual modified date first.
    Existing releases supply the next version and predecessor automatically.
    """
    check_immutable(base)
    history = releases()
    for source in history:
        validate_release(source, history)
    previous = history[-1]
    version = next_version(version_of(previous), increment)
    target = previous.with_name(f"{STEM}-v{version}.ttl")
    require(not target.exists() and not target.with_suffix(".html").exists(),
            f"{target}: refusing to overwrite an existing release artifact")
    require(version in SOURCE_CONTRACTS, f"{target}: register the reviewed source contract first")
    graph = _source_graph(draft)
    expected = predecessor(target, history)
    # A draft may start as a copy of the preceding release or already name the
    # new version. Conflicting version fields are not silently repaired.
    info = _values(draft, graph, ONTOLOGY, OWL.versionInfo, single=True).pop()
    iri = _values(draft, graph, ONTOLOGY, OWL.versionIRI, single=True).pop()
    _check(draft, ONTOLOGY, OWL.versionInfo,
           isinstance(info, Literal) and info.language is None
           and info.datatype in (None, XSD.string)
           and str(info) in {version_of(previous), version}
           and iri == URIRef(f"{BASE}/{info}"),
           "a consistent preceding or prepared version IRI/information pair", f"{iri.n3()}, {info.n3()}")
    values = set(graph.objects(ONTOLOGY, OWL.priorVersion))
    inherited = set(_source_graph(previous).objects(ONTOLOGY, OWL.priorVersion))
    _check(draft, ONTOLOGY, OWL.priorVersion,
           not values or values == {expected}
           or (str(info) == version_of(previous) and values == inherited),
           f"no predecessor, <{expected}>, or unchanged metadata inherited from the preceding release",
           sorted(value.n3() for value in values))
    graph.set((ONTOLOGY, OWL.versionInfo, Literal(version)))
    graph.set((ONTOLOGY, OWL.versionIRI, URIRef(f"{BASE}/{version}")))
    graph.set((ONTOLOGY, OWL.priorVersion, expected))
    graph.bind("dkgm", DKGM)
    with tempfile.TemporaryDirectory() as temporary:
        candidate = Path(temporary) / target.name
        graph.serialize(candidate, format="turtle", encoding="utf-8")
        candidate.write_bytes(candidate.read_bytes().rstrip(b"\n") + b"\n")
        validate_release(candidate, history)
        # Exclusive creation also protects against a concurrent preparer.
        with target.open("xb") as output:
            output.write(candidate.read_bytes())
    print(f"Prepared {target}; priorVersion={expected}; no HTML or latest files generated.")
    return target


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


def _link(soup, href, text):
    link = soup.new_tag("a", href=str(href))
    link.string = text
    return link


def _paragraphs(soup, container, values):
    container.clear()
    for value in sorted(set(values), key=lambda value: value.n3()):
        paragraph = soup.new_tag("p")
        if value.language:
            paragraph["lang"] = value.language
        paragraph.string = str(value)
        container.append(paragraph)


def _rows(table, predicate):
    return [link.find_parent("tr") for link in table.select("th a[href]")
            if link["href"] == str(predicate)]


def _term_row(soup, table, predicate, title):
    rows = _rows(table, predicate)
    require(len(rows) <= 1, f"Ambiguous generated property row: {predicate}")
    if rows:
        return rows[0].find("td")
    row = soup.new_tag("tr")
    header = soup.new_tag("th")
    header.append(_link(soup, predicate, title))
    row.append(header)
    cell = soup.new_tag("td")
    row.append(cell)
    table.append(row)
    return cell


def _sections(soup, graph, file):
    sections = {}
    for entity in soup.select(".property.entity"):
        iri = entity.select_one("table tr td code")
        require(iri is not None, f"{file}: property section has no IRI")
        term = URIRef(iri.get_text(strip=True))
        require(term not in sections and entity.get("id"),
                f"{file}: missing or duplicate property anchor for {term}")
        sections[term] = entity
    expected = set(graph.subjects(RDF.type, OWL.ObjectProperty))
    require(set(sections) == expected, f"{file}: property sections must match {sorted(map(str, expected))}")
    return sections


def _metadata_field(soup, predicate, file):
    links = soup.select(f'#metadata dt a[href="{predicate}"]')
    require(len(links) == 1, f"{file}: missing or ambiguous HTML metadata {predicate}")
    field = links[0].find_parent("dt").find_next_sibling("dd")
    require(field is not None, f"{file}: missing HTML metadata value for {predicate}")
    return field


def _asset_data(path, media_type):
    return f"data:{media_type};base64," + base64.b64encode((ROOT / path).read_bytes()).decode("ascii")


def _navigation(version):
    # These routes are registered in perma-id/w3id.org/ids/directkg/.htaccess.
    return {
        "Project documentation": str(PROJECT_DOCS),
        "Source repository": str(PROJECT_REPOSITORY),
        "Ontology IRI": BASE,
        "Current Turtle": f"{BASE}/ttl",
        "Version IRI": f"{BASE}/{version}",
        "Version Turtle": f"{BASE}/{version}/ttl",
    }


def _snapshot_versions(version, history):
    # Frozen HTML lists releases known at its preparation, never future versions.
    return sorted({version, *(version_of(path) for path in history
                              if version_key(version_of(path)) <= version_key(version))},
                  key=version_key)


def _chains(file, graph, term):
    return sorted({_chain(file, graph, term, head)[0]
                   for head in graph.objects(term, OWL.propertyChainAxiom)})


def _term_reference(term):
    return "dkgm:" + str(term).removeprefix(str(DKGM))


def _customize_current(soup, graph, source, history):
    """Small, source-derived additions to the existing PyLODE layout."""
    version = version_of(source)
    sections = _sections(soup, graph, source)
    for term, entity in sections.items():
        table = entity.find("table")
        # PyLODE combines definitions and comments in Description. Keep the
        # independent comments there; Definition already has its dedicated row.
        descriptions = _rows(table, DCTERMS.description)
        comments = set(graph.objects(term, RDFS.comment))
        if comments:
            _paragraphs(soup, _term_row(soup, table, DCTERMS.description, "Description"), comments)
        else:
            for row in descriptions:
                row.decompose()
        for predicate, title in ((SKOS.scopeNote, "Scope Note"), (SKOS.example, "Example")):
            values = set(graph.objects(term, predicate))
            if values:
                _paragraphs(soup, _term_row(soup, table, predicate, title), values)
        chains = _chains(source, graph, term)
        if chains:
            cell = _term_row(soup, table, OWL.propertyChainAxiom, "Property Chain Axiom")
            cell.clear()
            for operands in chains:
                paragraph = soup.new_tag("p")
                for index, prop in enumerate((*operands, term)):
                    if index:
                        paragraph.append(" ⊑ " if index == len(operands) else " ∘ ")
                    link = _link(soup, "#" + sections[prop]["id"], _term_reference(prop))
                    paragraph.append(link)
                cell.append(paragraph)

    metadata = soup.select_one("#metadata")
    field = _metadata_field(soup, DCTERMS.creator, source)
    field.clear()
    for creator in sorted(graph.objects(ONTOLOGY, DCTERMS.creator)):
        labels = sorted(str(value) for value in graph.objects(creator, RDFS.label))
        paragraph = soup.new_tag("p")
        paragraph.append(_link(soup, creator, "; ".join(labels) if labels else str(creator)))
        if labels:
            paragraph.append(f" ({creator})")
        field.append(paragraph)
    # PyLODE does not consistently include ontology scope notes in metadata.
    existing = metadata.select(f'dt a[href="{SKOS.scopeNote}"]')
    if existing:
        field = _metadata_field(soup, SKOS.scopeNote, source)
    else:
        wrapper = soup.new_tag("div")
        header = soup.new_tag("dt")
        header.append(_link(soup, SKOS.scopeNote, "Scope Notes"))
        wrapper.append(header)
        field = soup.new_tag("dd")
        wrapper.append(field)
        metadata.find("dl").append(wrapper)
    _paragraphs(soup, field, graph.objects(ONTOLOGY, SKOS.scopeNote))

    brand = _link(soup, PROJECT_DOCS, "")
    brand["id"] = "dkgm-brand"
    image = soup.new_tag("img", src=_asset_data(LOGO, "image/png"), alt="OntoUML DirectKG",
                         width="1308", height="887",
                         style="width:260px; max-width:100%; height:auto;")
    brand.append(image)
    metadata.insert(0, brand)
    for icon in soup.select('link[rel~="icon"]'):
        icon.decompose()
    soup.head.append(soup.new_tag("link", rel="icon", type="image/svg+xml",
                                 href=_asset_data(FAVICON, "image/svg+xml")))
    soup.head.append(soup.new_tag("link", rel="alternate", type="text/turtle",
                                 href=f"{BASE}/{version}/ttl", title=f"DKGM {version} Turtle"))
    navigation = soup.new_tag("nav", id="dkgm-navigation", attrs={"aria-label": "DirectKG resources"})
    links = soup.new_tag("ul")
    for title, href in _navigation(version).items():
        item = soup.new_tag("li")
        item.append(_link(soup, href, title))
        links.append(item)
    navigation.append(links)
    versions = soup.new_tag("p", id="dkgm-versions")
    versions.append("Versions in this snapshot: ")
    for index, available in enumerate(_snapshot_versions(version, history)):
        if index:
            versions.append(" · ")
        versions.append(_link(soup, f"{BASE}/{available}/docs", available))
    navigation.append(versions)
    metadata.find("h1").insert_after(navigation)


def customize_documentation(output: Path, source: Path, history: list[Path] | None = None) -> None:
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
    if SOURCE_CONTRACTS[version_of(source)].documented:
        _customize_current(soup, graph, source, releases() if history is None else history)
    output.write_text(str(soup), encoding="utf-8")


def _check_text_display(file, subject, predicate, container, values):
    require(container is not None, f"{file}: missing HTML field {subject} / {predicate}")
    expected = sorted((str(value), (value.language or "").lower()) for value in set(values))
    actual = sorted((p.get_text(), p.get("lang", "").lower()) for p in container.find_all("p"))
    _check(file, subject, predicate, actual == expected,
           f"source-derived HTML text {expected}", actual)


def _check_current_documentation(file, soup, source, history):
    graph = _source_graph(source)
    version = version_of(source)
    sections = _sections(soup, graph, file)
    for term, entity in sections.items():
        table = entity.find("table")
        for predicate in (SKOS.definition, RDFS.comment, SKOS.scopeNote, SKOS.example):
            values = set(graph.objects(term, predicate))
            rows = _rows(table, DCTERMS.description if predicate == RDFS.comment else predicate)
            require(len(rows) == (1 if values else 0), f"{file}: missing or ambiguous {term} / {predicate}")
            if values:
                _check_text_display(file, term, predicate, rows[0].find("td"), values)
        defined_by = _rows(table, RDFS.isDefinedBy)
        require(len(defined_by) == 1 and
                [a.get("href") for a in defined_by[0].select("td a")] == [str(ONTOLOGY)],
                f"{file}: incorrect HTML isDefinedBy for {term}")
        chains = _chains(source, graph, term)
        rows = _rows(table, OWL.propertyChainAxiom)
        require(len(rows) == (1 if chains else 0), f"{file}: missing or unexpected property-chain display for {term}")
        if chains:
            cell = rows[0].find("td")
            paragraphs = cell.find_all("p") if cell else []
            require(len(paragraphs) == len(chains), f"{file}: empty or missing property-chain values for {term}")
            for paragraph, operands in zip(paragraphs, chains):
                references = (*operands, term)
                expected = [("#" + sections[prop]["id"], _term_reference(prop)) for prop in references]
                actual = [(a.get("href"), a.get_text()) for a in paragraph.find_all("a")]
                text = " ∘ ".join(_term_reference(prop) for prop in operands) + " ⊑ " + _term_reference(term)
                _check(file, term, OWL.propertyChainAxiom,
                       actual == expected and paragraph.get_text() == text,
                       f"{text}; references {expected}", f"{paragraph.get_text()}; references {actual}")
    for creator in graph.objects(ONTOLOGY, DCTERMS.creator):
        field = _metadata_field(soup, DCTERMS.creator, file)
        matches = field.find_all("a", href=str(creator))
        labels = sorted(str(value) for value in graph.objects(creator, RDFS.label))
        expected = "; ".join(labels) if labels else str(creator)
        require(len(matches) == 1 and matches[0].get_text() == expected
                and str(creator) in matches[0].parent.get_text(),
                f"{file}: creator name/identifier mismatch for {creator}")
    _check_text_display(file, ONTOLOGY, SKOS.scopeNote,
                        _metadata_field(soup, SKOS.scopeNote, file), graph.objects(ONTOLOGY, SKOS.scopeNote))
    for predicate in (OWL.priorVersion, RDFS.seeAlso):
        expected = set(map(str, graph.objects(ONTOLOGY, predicate)))
        field = _metadata_field(soup, predicate, file)
        require({a.get("href") for a in field.find_all("a")} == expected,
                f"{file}: incorrect HTML metadata links for {predicate}")
    brand = soup.select("#dkgm-brand")
    require(len(brand) == 1 and brand[0].get("href") == str(PROJECT_DOCS), f"{file}: missing project logo link")
    image = brand[0].find("img")
    require(image is not None and image.get("src") == _asset_data(LOGO, "image/png")
            and image.get("alt") == "OntoUML DirectKG"
            and image.get("width") == "1308" and image.get("height") == "887"
            and image.get("style") == "width:260px; max-width:100%; height:auto;",
            f"{file}: missing, incorrect or distorted DirectKG logo")
    icons = soup.select('link[rel~="icon"]')
    require(len(icons) == 1 and icons[0].get("href") == _asset_data(FAVICON, "image/svg+xml")
            and icons[0].get("type") == "image/svg+xml", f"{file}: incorrect DirectKG favicon")
    alternate = soup.select('link[rel~="alternate"][type="text/turtle"]')
    require(len(alternate) == 1 and alternate[0].get("href") == f"{BASE}/{version}/ttl",
            f"{file}: incorrect version-specific Turtle alternate link")
    navigation = soup.select_one("#dkgm-navigation")
    require(navigation is not None, f"{file}: missing project navigation")
    actual = [(a.get_text(), a.get("href")) for a in navigation.select("ul a")]
    require(actual == list(_navigation(version).items()), f"{file}: incorrect project/representation navigation")
    versions = soup.select_one("#dkgm-versions")
    expected = [(v, f"{BASE}/{v}/docs") for v in _snapshot_versions(version, history)]
    require(versions is not None and [(a.get_text(), a.get("href")) for a in versions.find_all("a")] == expected,
            f"{file}: incorrect available-version navigation")
    scripts = soup.select('script[type="application/ld+json"]')
    require(bool(scripts), f"{file}: missing PyLODE JSON-LD")
    for script in scripts:
        json.loads(script.string or "")
    ids = [tag["id"] for tag in soup.select("[id]")]
    require(len(ids) == len(set(ids)), f"{file}: duplicate HTML anchors")
    for element in soup.select("a[href], img[src], link[href]"):
        href = element.get("href", element.get("src", ""))
        url = urlsplit(href)
        require(url.scheme != "file", f"{file}: local file URL {href}")
        if url.scheme or url.netloc:
            continue
        target = (file.parent / unquote(url.path)).resolve() if url.path else file
        require(target.is_file(), f"{file}: broken local resource {href}")
        if url.fragment and target.suffix == ".html":
            target_soup = soup if target == file else BeautifulSoup(target.read_text(), "html.parser")
            require(target_soup.find(id=unquote(url.fragment)) is not None,
                    f"{file}: broken HTML anchor {href}")


def check_documentation(file: Path, version: str, source: Path | None = None,
                        history: list[Path] | None = None) -> None:
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
    if SOURCE_CONTRACTS[version].documented:
        _check_current_documentation(file, soup, source or file.with_suffix(".ttl"),
                                     releases() if history is None else history)


def check_latest(current: Path, latest: Path | None = None) -> None:
    latest = ROOT / "vocabulary/latest" if latest is None else latest
    for name, original in ((LATEST_NAME, current), ("index.html", current.with_suffix(".html"))):
        copy = latest / name
        require(copy.is_file() and copy.read_bytes() == original.read_bytes(),
                f"{copy}: latest representation differs from highest release {original.name}")
    require({p.name for p in latest.iterdir()} == {LATEST_NAME, "index.html"},
            "Unexpected files in latest publication directory")


def check_artifacts(directory: Path) -> list[Path]:
    """Validate actual RDF/HTML bytes at either source or staged locations."""
    for path in (directory, directory / "versioned", directory / "latest"):
        require(path.is_dir() and not path.is_symlink(),
                f"{path}: expected an ordinary artifact directory; observed missing directory or symlink")
    versions = releases(directory / "versioned")
    expected = {p.name for source in versions for p in (source, source.with_suffix(".html"))}
    observed = {p.name for p in (directory / "versioned").iterdir()}
    require(observed == expected,
            f"{directory / 'versioned'}: expected complete Turtle/HTML pairs {sorted(expected)}; observed {sorted(observed)}")
    for source in versions:
        html = source.with_suffix(".html")
        for path in (source, html):
            require(path.is_file() and not path.is_symlink(),
                    f"{path}: expected an ordinary artifact file; observed missing file or symlink")
        validate_release(source, versions)
        check_documentation(html, version_of(source), source, versions)
    current = versions[-1]
    for path in (directory / "latest").iterdir():
        require(path.is_file() and not path.is_symlink(), f"{path}: expected an ordinary latest file")
    check_latest(current, directory / "latest")
    # Also validate links relative to the actual latest/ location, not only the
    # identical bytes in versioned/. Historical HTML keeps its earlier contract.
    check_documentation(directory / "latest/index.html", version_of(current), current, versions)
    return versions


def _git(*arguments: str) -> bytes:
    result = subprocess.run(["git", *arguments], cwd=ROOT, capture_output=True)
    require(result.returncode == 0,
            f"Publication integrity evidence unavailable: git {' '.join(arguments)}: {result.stderr.decode(errors='replace').strip()}")
    return result.stdout


def _artifact_tree(ref: str, *directories: str) -> dict[str, str]:
    result = {}
    for record in _git("ls-tree", "-r", "-z", ref, "--", *directories).split(b"\0"):
        if record:
            metadata, path = record.decode().split("\t", 1)
            mode, kind, sha = metadata.split()
            require(kind == "blob" and mode == "100644",
                    f"{path}: expected an ordinary committed artifact; observed {mode} {kind}")
            result[path] = sha
    return result


def check_publication_history() -> None:
    """Protect the reviewed floor and snapshots previously accepted on main.

    Workflows must fetch canonical origin/main with complete history first.
    The candidate tip's new additions are allowed, while strict prior history
    protects existing files even during a manual run on that same main tip.
    No push-event SHA, caller-provided comparison ref, or deployment ledger is
    needed, and a candidate's own bytes never establish historical integrity.
    """
    require(_git("rev-parse", "--is-shallow-repository").strip() == b"false",
            "Publication integrity requires complete Git history; observed a shallow checkout")
    origin = _git("config", "--get", "remote.origin.url").decode().strip().removesuffix(".git")
    require(origin in {"https://github.com/pedropaulofb/ontouml-directkg",
                       "git@github.com:pedropaulofb/ontouml-directkg"},
            "Publication integrity requires the canonical DirectKG origin; observed an untrusted remote")
    tip = _git("rev-parse", "--verify", TRUSTED_MAIN + "^{commit}").decode().strip()
    head = _git("rev-parse", "--verify", "HEAD^{commit}").decode().strip()
    lineage = _git("rev-list", "--first-parent", tip).decode().splitlines()
    require(PUBLICATION_ANCHOR in lineage,
            f"Publication integrity requires reviewed anchor {PUBLICATION_ANCHOR} on trusted main's first-parent history")
    require(_git("merge-base", tip, head).decode().strip() == tip,
            "Publication integrity requires a candidate containing fetched main; observed stale or unrelated source")
    limit = _git("rev-parse", tip + "^1").decode().strip() if tip == head and tip != PUBLICATION_ANCHOR else tip
    references = [PUBLICATION_ANCHOR, *_git("rev-list", "--first-parent", "--reverse",
                                           f"{PUBLICATION_ANCHOR}..{limit}").decode().splitlines()]
    protected = {}
    for ref in references:
        for path, sha in _artifact_tree(ref, "vocabulary/versioned").items():
            protected.setdefault(path, sha)
    require(bool(protected), "Publication integrity baseline contains no historical artifacts")
    for path, sha in protected.items():
        current = ROOT / path
        require(current.is_file() and not current.is_symlink()
                and current.read_bytes() == _git("cat-file", "blob", sha),
                f"{path}: expected immutable bytes from trusted main history; observed modified or missing historical artifact")


def check_publication(site: Path | None = None) -> None:
    """Read-only publication gate, including the assembled site when supplied."""
    check_publication_history()
    vocabulary = ROOT / "vocabulary"
    check_artifacts(vocabulary)
    committed = _artifact_tree("HEAD", "vocabulary/latest", "vocabulary/versioned")
    actual = {p.relative_to(ROOT).as_posix() for folder in ("latest", "versioned")
              for p in (vocabulary / folder).iterdir()}
    require(actual == set(committed),
            f"{vocabulary}: expected the committed publication file inventory; observed uncommitted additions or removals")
    for path, sha in committed.items():
        require((ROOT / path).read_bytes() == _git("cat-file", "blob", sha),
                f"{path}: expected exact committed source bytes; observed uncommitted publication changes")
    if site is not None:
        staged = site.resolve() / "vocabulary"
        require(staged.resolve() != vocabulary.resolve(),
                f"{staged}: expected a separate assembled site, not the authoritative source directory")
        check_artifacts(staged)
        staged_files = {p.relative_to(site.resolve()).as_posix()
                        for folder in ("latest", "versioned") for p in (staged / folder).iterdir()}
        require(staged_files == set(committed),
                f"{staged}: expected committed vocabulary files {sorted(committed)}; observed {sorted(staged_files)}")
        for path in committed:
            require((site / path).read_bytes() == (ROOT / path).read_bytes(),
                    f"{site / path}: expected authoritative source bytes; observed source-to-staged content mismatch")
    print("Validated publication artifacts and trusted historical integrity; no files modified.")


def build(base: str | None = None, *, publication: bool = False) -> None:
    if publication:
        check_publication_history()
    check_immutable(base)
    versions = releases()
    for source in versions:
        validate_release(source, versions)
    for source in versions:
        html = source.with_suffix(".html")
        if not html.exists():
            temporary = source.with_suffix(".tmp.html")
            try:
                subprocess.run(["pylode", str(source), "-p", "ontpub",
                                "-c", "true", "-o", str(temporary)], check=True)
                customize_documentation(temporary, source, versions)
                check_documentation(temporary, version_of(source), source, versions)
                temporary.replace(html)
            finally:
                temporary.unlink(missing_ok=True)
        check_documentation(html, version_of(source), source, versions)
    current = versions[-1]
    latest = ROOT / "vocabulary/latest"
    latest.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(current, latest / LATEST_NAME)
    shutil.copyfile(current.with_suffix(".html"), latest / "index.html")
    check_latest(current)
    print(f"Validated {len(versions)} release(s); latest={version_of(current)}; "
          "Pages artifact: vocabulary/latest/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", help="Git commit for immutable release comparison")
    parser.add_argument("--check-only", action="store_true",
                        help="Validate existing Turtle sources without generating or publishing files")
    parser.add_argument("--publication", action="store_true",
                        help="Require trusted main history; with --check-only also check committed RDF/HTML/latest")
    parser.add_argument("--site", type=Path, help="Assembled site for --check-only --publication")
    parser.add_argument("--prepare-release", choices=("patch", "minor"),
                        help="Explicitly prepare a new Turtle release from --draft; no HTML/latest changes")
    parser.add_argument("--draft", type=Path, help="Edited Turtle draft used only with --prepare-release")
    parser.add_argument("sources", nargs="*", type=Path,
                        help="Versioned Turtle sources for --check-only (default: all releases)")
    args = parser.parse_args()
    if args.sources and not args.check_only:
        parser.error("Explicit source files require --check-only")
    if args.prepare_release and (args.check_only or not args.draft):
        parser.error("--prepare-release requires --draft and cannot be combined with --check-only")
    if args.draft and not args.prepare_release:
        parser.error("--draft requires --prepare-release")
    if args.site and not (args.check_only and args.publication):
        parser.error("--site requires --check-only --publication")
    if args.publication and (args.prepare_release or args.sources):
        parser.error("--publication checks the complete artifact set, not a draft or selected sources")
    try:
        if args.prepare_release:
            prepare_release(args.draft, args.prepare_release, args.base)
        elif args.check_only:
            if args.publication:
                check_immutable(args.base)
                check_publication(args.site)
            else:
                check_sources(args.base, args.sources or None)
        else:
            build(args.base, publication=args.publication)
    except Exception as error:
        operation = "preparation" if args.prepare_release else "validation" if args.check_only else "publication"
        raise SystemExit(f"Vocabulary {operation} failed: {error}") from error
