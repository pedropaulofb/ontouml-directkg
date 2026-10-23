"""Wave 2 source metadata, explicit release preparation and predecessor checks."""
import contextlib
import io
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from rdflib import BNode, Graph, Literal, URIRef
from rdflib.compare import isomorphic
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, SKOS

from test_publication import BUILD_PATH, build


ROOT = build.ROOT
OLD = ROOT / "vocabulary/versioned/dkgm-vocabulary-v0.1.0.ttl"
NEW = OLD.with_name("dkgm-vocabulary-v0.1.1.ttl")
MODERN = build.SOURCE_CONTRACTS["0.1.1"]


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.versioned = self.root / "vocabulary/versioned"
        self.versioned.mkdir(parents=True)
        for source in (OLD, OLD.with_suffix(".html")):
            shutil.copyfile(source, self.versioned / source.name)
        self.draft = self.root / "draft.ttl"
        self.graph = Graph().parse(NEW, format="turtle")
        self.source = self.versioned / NEW.name
        patcher = patch.object(build, "ROOT", self.root)
        patcher.start()
        self.addCleanup(patcher.stop)

    def write(self, file=None):
        self.graph.serialize(file or self.source, format="turtle", encoding="utf-8")

    def reject(self, predicate):
        self.write()
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaisesRegex(ValueError, str(predicate)) as error:
                build.validate_release(self.source)
        self.assertIn(str(self.source), str(error.exception))

    def test_patch_and_minor_increment_calculation(self):
        for previous, patch_version, minor in (("0.1.0", "0.1.1", "0.2.0"),
                                               ("0.9.9", "0.9.10", "0.10.0"),
                                               ("1.2.9", "1.2.10", "1.3.0")):
            self.assertEqual(build.next_version(previous, "patch"), patch_version)
            self.assertEqual(build.next_version(previous, "minor"), minor)
        with self.assertRaisesRegex(ValueError, "patch or minor"):
            build.next_version("0.1.0", "major")

    def test_automatic_assignment_preserves_draft_history_and_latest(self):
        self.graph.remove((build.ONTOLOGY, OWL.priorVersion, None))
        self.write(self.draft)
        latest = self.root / "vocabulary/latest"
        latest.mkdir()
        (latest / "sentinel").write_text("untouched")
        before = {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        result = build.prepare_release(self.draft, "patch")
        self.assertEqual(result, self.source)
        self.assertEqual(Graph().parse(result).value(build.ONTOLOGY, OWL.priorVersion),
                         Graph().parse(OLD).value(build.ONTOLOGY, OWL.versionIRI))
        build.validate_release(result)
        for path, contents in before.items():
            self.assertEqual((self.root / path).read_bytes(), contents)
        self.assertFalse(result.with_suffix(".html").exists())
        self.assertEqual(len(list(latest.iterdir())), 1)

    def test_explicit_preparation_cli(self):
        # Run the actual CLI against an isolated checkout; do not create releases
        # in the working repository during a test.
        scripts = self.root / "vocabulary/scripts"
        scripts.mkdir()
        shutil.copyfile(BUILD_PATH, scripts / "build.py")
        self.write(self.draft)
        result = subprocess.run([sys.executable, "-B", str(scripts / "build.py"),
                                 "--prepare-release", "patch", "--draft", str(self.draft)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.source.is_file())
        self.assertFalse(self.source.with_suffix(".html").exists())
        self.assertFalse((self.root / "vocabulary/latest").exists())

    def test_reviewed_minor_preparation_sets_both_version_fields(self):
        self.graph.set((build.ONTOLOGY, OWL.versionInfo, Literal("0.1.0")))
        self.graph.set((build.ONTOLOGY, OWL.versionIRI, URIRef(build.BASE + "/0.1.0")))
        self.write(self.draft)
        with patch.dict(build.SOURCE_CONTRACTS, {"0.2.0": MODERN}):
            source = build.prepare_release(self.draft, "minor")
            graph = Graph().parse(source)
            self.assertEqual(source.name, "dkgm-vocabulary-v0.2.0.ttl")
            self.assertEqual(str(graph.value(build.ONTOLOGY, OWL.versionInfo)), "0.2.0")
            self.assertEqual(graph.value(build.ONTOLOGY, OWL.versionIRI), URIRef(build.BASE + "/0.2.0"))
            build.validate_release(source)

    def test_invalid_draft_creates_no_release(self):
        self.graph.remove((build.DKGM.memberOf, RDFS.label, None))
        self.write(self.draft)
        before = {p: p.read_bytes() for p in self.versioned.iterdir()}
        with self.assertRaisesRegex(ValueError, "label"):
            build.prepare_release(self.draft, "patch")
        self.assertEqual({p: p.read_bytes() for p in self.versioned.iterdir()}, before)

    def test_missing_wrong_duplicated_and_incorrect_type_predecessors(self):
        valid = self.graph.value(build.ONTOLOGY, OWL.priorVersion)
        for values in ([], [URIRef(build.BASE + "/9.0.0")], [URIRef(build.BASE + "/0.1.1")],
                       [Literal(str(valid))], [BNode()], [valid, URIRef(build.BASE + "/0.0.9")]):
            with self.subTest(values=values):
                self.graph.remove((build.ONTOLOGY, OWL.priorVersion, None))
                for value in values:
                    self.graph.add((build.ONTOLOGY, OWL.priorVersion, value))
                self.reject(OWL.priorVersion)

    def test_repeated_identical_predecessor_statements_are_one_rdf_value(self):
        self.write()
        statement = f'<{build.ONTOLOGY}> <{OWL.priorVersion}> <{build.BASE}/0.1.0> .\n'
        with self.source.open("a", encoding="utf-8") as output:
            output.write(statement * 2)
        build.validate_release(self.source)

    def test_missing_and_wrong_new_discovery_metadata(self):
        original = set(self.graph)
        for subject, predicate in ((build.ONTOLOGY, RDFS.seeAlso),
                                   (build.ONTOLOGY, SKOS.scopeNote),
                                   (build.DKGM.memberOf, SKOS.scopeNote),
                                   (build.DKGM.memberOf, SKOS.example),
                                   (build.DKGM.componentOf, SKOS.scopeNote),
                                   *((term, RDFS.isDefinedBy) for term in MODERN.properties)):
            with self.subTest(subject=subject, predicate=predicate):
                self.graph.remove((subject, predicate, None))
                self.reject(predicate)
                self.graph = Graph()
                for triple in original:
                    self.graph.add(triple)
        for value in (Literal(str(build.ONTOLOGY)), URIRef(str(build.DKGM)), BNode()):
            self.graph.set((build.DKGM.memberOf, RDFS.isDefinedBy, value))
            self.reject(RDFS.isDefinedBy)

    def test_new_annotations_preserve_the_logical_graph(self):
        old = Graph().parse(OLD)
        new = Graph().parse(NEW)
        predicates = {RDF.type, OWL.propertyChainAxiom, RDF.first, RDF.rest}
        def logical(graph):
            result = Graph()
            for subject, predicate, value in graph:
                if predicate in predicates:
                    result.add((subject, predicate, value))
            return result
        self.assertTrue(isomorphic(logical(old), logical(new)))
        # The production contract, not just this projection, rejects extra axioms.
        self.graph.add((build.DKGM.componentOf, RDF.type, OWL.TransitiveProperty))
        self.reject(RDF.type)

    def test_conflicting_draft_predecessor_leaves_history_unchanged(self):
        for values in ([URIRef(build.BASE + "/9.0.0")],
                       [URIRef(build.BASE + "/0.1.0"), URIRef(build.BASE + "/0.1.1")]):
            self.graph.remove((build.ONTOLOGY, OWL.priorVersion, None))
            for value in values:
                self.graph.add((build.ONTOLOGY, OWL.priorVersion, value))
            self.write(self.draft)
            before = {p: p.read_bytes() for p in self.versioned.iterdir()}
            with self.assertRaisesRegex(ValueError, "priorVersion"):
                build.prepare_release(self.draft, "patch")
            self.assertEqual({p: p.read_bytes() for p in self.versioned.iterdir()}, before)

    def test_preparation_refuses_existing_target_or_unregistered_version(self):
        self.write(self.draft)
        target_html = self.source.with_suffix(".html")
        target_html.write_text("do not overwrite")
        with self.assertRaisesRegex(ValueError, "refusing to overwrite"):
            build.prepare_release(self.draft, "patch")
        self.assertEqual(target_html.read_text(), "do not overwrite")
        target_html.unlink()
        with self.assertRaisesRegex(ValueError, "reviewed source contract"):
            build.prepare_release(self.draft, "minor")
        self.assertFalse(self.versioned.joinpath("dkgm-vocabulary-v0.2.0.ttl").exists())

    def test_predecessor_updates_when_draft_is_copied_from_a_modern_release(self):
        self.write(self.draft)
        first = build.prepare_release(self.draft, "patch")
        before = first.read_bytes()
        shutil.copyfile(first, self.draft)
        with patch.dict(build.SOURCE_CONTRACTS, {"0.1.2": MODERN}):
            second = build.prepare_release(self.draft, "patch")
            self.assertEqual(Graph().parse(second).value(build.ONTOLOGY, OWL.priorVersion),
                             URIRef(build.BASE + "/0.1.1"))
            build.validate_release(second)
        self.assertEqual(first.read_bytes(), before)

    def test_numeric_predecessor_after_multiple_historical_releases(self):
        historical = build.SOURCE_CONTRACTS["0.1.0"]
        for version in ("0.1.9", "0.1.10"):
            graph = Graph().parse(OLD)
            graph.set((build.ONTOLOGY, OWL.versionInfo, Literal(version)))
            graph.set((build.ONTOLOGY, OWL.versionIRI, URIRef(build.BASE + "/" + version)))
            graph.serialize(self.versioned / f"dkgm-vocabulary-v{version}.ttl", format="turtle")
        self.graph.set((build.ONTOLOGY, OWL.versionInfo, Literal("0.1.10")))
        self.graph.set((build.ONTOLOGY, OWL.versionIRI, URIRef(build.BASE + "/0.1.10")))
        self.graph.remove((build.ONTOLOGY, OWL.priorVersion, None))
        self.write(self.draft)
        with patch.dict(build.SOURCE_CONTRACTS, {"0.1.9": historical, "0.1.10": historical, "0.1.11": MODERN}):
            target = build.prepare_release(self.draft, "patch")
            self.assertEqual(build.version_of(target), "0.1.11")
            graph = Graph().parse(target)
            self.assertEqual(graph.value(build.ONTOLOGY, OWL.priorVersion), URIRef(build.BASE + "/0.1.10"))
            graph.set((build.ONTOLOGY, OWL.priorVersion, URIRef(build.BASE + "/0.1.9")))
            graph.serialize(target, format="turtle")
            with self.assertRaisesRegex(ValueError, "immediately preceding release"):
                build.validate_release(target)

    def test_duplicate_history_versions_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "ambiguous duplicate"):
            build.predecessor(self.source, [OLD, OLD])

    def test_read_only_new_source_valid_and_invalid_leave_files_unchanged(self):
        self.write()
        for valid in (True, False):
            if not valid:
                self.graph.remove((build.ONTOLOGY, OWL.priorVersion, None))
                self.write()
            before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.versioned.iterdir()}
            if valid:
                build.check_sources(files=[self.source])
            else:
                with self.assertRaisesRegex(ValueError, "priorVersion"):
                    build.check_sources(files=[self.source])
            self.assertEqual({p: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.versioned.iterdir()}, before)


if __name__ == "__main__":
    unittest.main()
