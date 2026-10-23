"""Wave 2 HTML regressions, using real pinned PyLODE output and production checks."""
import base64
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from bs4 import BeautifulSoup
from rdflib import Graph
from rdflib.collection import Collection
from rdflib.namespace import DCTERMS, OWL, RDFS, SKOS

from test_publication import build


SOURCE = build.ROOT / "vocabulary/versioned/dkgm-vocabulary-v0.1.1.ttl"
VERSION = build.version_of(SOURCE)


class DocumentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.raw = Path(cls.temporary.name) / "raw.html"
        # Use the same installed environment as the test runner, without
        # depending on a globally installed pylode executable.
        executable = Path(sys.executable).parent / "pylode"
        subprocess.run([str(executable), str(SOURCE), "-p", "ontpub", "-c", "true",
                        "-o", str(cls.raw)], check=True, capture_output=True, text=True)
        cls.raw_html = cls.raw.read_text(encoding="utf-8")
        build.customize_documentation(cls.raw, SOURCE)
        cls.processed = cls.raw.read_text(encoding="utf-8")
        cls.graph = Graph().parse(SOURCE, format="turtle")

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.page = Path(self.directory.name) / "vocabulary.html"
        self.soup = BeautifulSoup(self.processed, "html.parser")

    def check(self):
        self.page.write_text(str(self.soup), encoding="utf-8")
        build.check_documentation(self.page, VERSION, SOURCE)

    def reject(self, message):
        with self.assertRaisesRegex(ValueError, message):
            self.check()

    def row(self, predicate, term="memberOf"):
        return self.soup.select_one(f'#{term} th a[href="{predicate}"]').find_parent("tr")

    def test_real_generator_output_and_committed_artifact_pass(self):
        self.check()
        build.check_documentation(SOURCE.with_suffix(".html"), VERSION, SOURCE)

    def test_three_displayed_chains_match_rdf_lists_and_conclusions(self):
        for conclusion, head in self.graph.subject_objects(OWL.propertyChainAxiom):
            operands = list(Collection(self.graph, head))
            term = str(conclusion).split("#")[1]
            paragraph = self.row(OWL.propertyChainAxiom, term).find("td").find("p")
            expected = [str(prop).split("#")[1] for prop in [*operands, conclusion]]
            self.assertEqual([a["href"] for a in paragraph.find_all("a")],
                             ["#" + prop for prop in expected])
            self.assertEqual(paragraph.get_text(),
                             " ∘ ".join("dkgm:" + p for p in expected[:-1]) + " ⊑ dkgm:" + expected[-1])
        self.assertEqual(len(self.soup.select(f'th a[href="{OWL.propertyChainAxiom}"]')), 3)

    def test_definitions_once_and_independent_comments_preserved(self):
        for term in build.SOURCE_CONTRACTS[VERSION].properties:
            entity = self.soup.find(id=str(term).split("#")[1])
            for definition in self.graph.objects(term, SKOS.definition):
                texts = [p.get_text() for p in entity.find_all("p")]
                self.assertEqual(texts.count(str(definition)), 1)
            for comment in self.graph.objects(term, RDFS.comment):
                self.assertIn(str(comment), entity.get_text())
        self.check()

    def test_attribution_assets_and_json_ld_are_preserved(self):
        creator = self.graph.value(build.ONTOLOGY, DCTERMS.creator)
        attribution = self.soup.select_one(f'#metadata dd a[href="{creator}"]')
        self.assertEqual(attribution.get_text(), str(self.graph.value(creator, RDFS.label)))
        self.assertIn(str(creator), attribution.parent.get_text())
        for element, attribute, asset in (
            (self.soup.select_one("#dkgm-brand img"), "src", build.LOGO),
            (self.soup.select_one('link[rel="icon"]'), "href", build.FAVICON),
        ):
            data = base64.b64decode(element[attribute].split(",", 1)[1], validate=True)
            self.assertEqual(data, (build.ROOT / asset).read_bytes())
        raw_soup = BeautifulSoup(self.raw_html, "html.parser")
        self.assertEqual([json.loads(s.string) for s in raw_soup.select('script[type="application/ld+json"]')],
                         [json.loads(s.string) for s in self.soup.select('script[type="application/ld+json"]')])

    def test_empty_missing_and_reordered_chain_displays_fail(self):
        original = str(self.soup)
        for change in ("missing", "empty", "reordered", "wrong operand", "conclusion", "reference", "symbol"):
            with self.subTest(change=change):
                self.soup = BeautifulSoup(original, "html.parser")
                row = self.row(OWL.propertyChainAxiom)
                if change == "missing":
                    row.decompose()
                elif change == "empty":
                    row.find("td").clear()
                else:
                    links = row.select("td a")
                    if change == "reordered":
                        links[0]["href"], links[1]["href"] = links[1]["href"], links[0]["href"]
                        links[0].string, links[1].string = links[1].get_text(), links[0].get_text()
                    elif change == "wrong operand":
                        links[0]["href"] = "#subQuantityOf"
                        links[0].string = "dkgm:subQuantityOf"
                    elif change == "conclusion":
                        links[-1]["href"] = "#componentOf"
                        links[-1].string = "dkgm:componentOf"
                    elif change == "reference":
                        links[0]["href"] = "#componentOf"
                    else:
                        row.find("p").contents[1].replace_with(" + ")
                self.reject("property.chain|propertyChainAxiom")

    def test_unsupported_chain_display_fails(self):
        self.soup.select_one("#componentOf table").append(self.row(OWL.propertyChainAxiom).extract())
        self.reject("property.chain")

    def test_missing_term_or_broken_term_anchor_fails(self):
        original = str(self.soup)
        self.soup.select_one("#componentOf").decompose()
        self.reject("property sections")
        self.soup = BeautifulSoup(original, "html.parser")
        self.soup.select_one('a[href="#componentOf"]')["href"] = "#missing"
        self.reject("broken HTML anchor")

    def test_duplicate_definition_or_missing_comment_fails(self):
        original = str(self.soup)
        cell = self.row(DCTERMS.description).find("td")
        cell.append(self.row(SKOS.definition).find("p").__copy__())
        self.reject("source-derived HTML text")
        self.soup = BeautifulSoup(original, "html.parser")
        self.row(DCTERMS.description).find("td").clear()
        self.reject("source-derived HTML text")

    def test_incorrect_creator_assets_and_metadata_fail(self):
        original = str(self.soup)
        creator = self.graph.value(build.ONTOLOGY, DCTERMS.creator)
        for change in ("creator", "logo", "logo aspect", "favicon", "priorVersion", "scope note", "isDefinedBy", "JSON-LD"):
            with self.subTest(change=change):
                self.soup = BeautifulSoup(original, "html.parser")
                if change == "creator":
                    self.soup.select_one(f'#metadata dd a[href="{creator}"]').string = "Wrong name"
                elif change == "logo":
                    self.soup.select_one("#dkgm-brand img")["src"] = "missing.png"
                elif change == "logo aspect":
                    self.soup.select_one("#dkgm-brand img")["height"] = "10"
                elif change == "favicon":
                    self.soup.select_one('link[rel="icon"]')["href"] = "missing.ico"
                elif change == "priorVersion":
                    field = build._metadata_field(self.soup, OWL.priorVersion, self.page)
                    field.find("a")["href"] = build.BASE + "/9.0.0"
                elif change == "scope note":
                    self.row(SKOS.scopeNote).find("p").string = "Wrong scope"
                elif change == "isDefinedBy":
                    self.row(RDFS.isDefinedBy).select_one("td a")["href"] = str(build.DKGM)
                else:
                    for script in self.soup.select('script[type="application/ld+json"]'):
                        script.decompose()
                self.reject("creator|logo|favicon|metadata links|HTML text|isDefinedBy|JSON-LD")

    def test_wrong_representation_and_version_navigation_fail(self):
        original = str(self.soup)
        for selector in ('link[rel="alternate"]', "#dkgm-navigation ul a:last-child", "#dkgm-versions a"):
            with self.subTest(selector=selector):
                self.soup = BeautifulSoup(original, "html.parser")
                self.soup.select_one(selector)["href"] = build.BASE + "/ttl"
                self.reject("alternate|navigation")

    def test_historical_html_keeps_its_original_contract(self):
        historical = SOURCE.with_name("dkgm-vocabulary-v0.1.0.html")
        before = historical.read_bytes()
        build.check_documentation(historical, "0.1.0")
        self.assertEqual(historical.read_bytes(), before)
        self.assertNotIn("dkgm-brand", before.decode())

    def test_stale_latest_representations_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            latest = root / "vocabulary/latest"
            latest.mkdir(parents=True)
            for name, source in ((build.LATEST_NAME, SOURCE), ("index.html", SOURCE.with_suffix(".html"))):
                shutil.copyfile(source, latest / name)
            from unittest.mock import patch
            with patch.object(build, "ROOT", root):
                build.check_latest(SOURCE)
                for name in (build.LATEST_NAME, "index.html"):
                    original = (latest / name).read_bytes()
                    (latest / name).write_text("stale")
                    with self.assertRaisesRegex(ValueError, "differs from highest release"):
                        build.check_latest(SOURCE)
                    (latest / name).write_bytes(original)


if __name__ == "__main__":
    unittest.main()
