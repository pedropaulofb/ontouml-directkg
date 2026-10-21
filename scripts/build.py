"""Validate and publish versioned DirectKG mereology vocabulary representations."""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
from pathlib import Path

from bs4 import BeautifulSoup
from rdflib import Graph, Literal, RDF, URIRef
from rdflib.namespace import OWL, SKOS

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://w3id.org/directkg/vocab"
STEM = "dkgm-vocabulary"
RELEASE_RE = re.compile(r"dkgm-vocabulary-v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)\.ttl")
LATEST_NAME = "dkgm-vocabulary.ttl"


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
    version = version_of(file)
    graph = Graph().parse(file, format="turtle")
    ontology = URIRef(BASE)
    require(set(graph.subjects(RDF.type, OWL.Ontology)) == {ontology},
            f"{file.name}: expected the existing DirectKG ontology IRI")
    require(set(graph.objects(ontology, OWL.versionIRI)) == {URIRef(f"{BASE}/{version}")},
            f"{file.name}: owl:versionIRI does not match the release filename")
    require(set(graph.objects(ontology, OWL.versionInfo)) == {Literal(version)},
            f"{file.name}: owl:versionInfo does not match the release filename")


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
    args = parser.parse_args()
    try:
        build(args.base)
    except Exception as error:
        raise SystemExit(f"Vocabulary publication failed: {error}") from error
