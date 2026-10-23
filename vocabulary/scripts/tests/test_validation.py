"""Wave 1 source validation: real release fixtures, production checks, no HTML generation."""
import contextlib
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from rdflib import BNode, Graph, Literal, Namespace, RDF, RDFS, URIRef
from rdflib.collection import Collection
from rdflib.compare import isomorphic
from rdflib.namespace import DCTERMS, OWL, SKOS, XSD

from test_publication import BUILD_PATH, build


SOURCE = build.ROOT / "vocabulary/versioned/dkgm-vocabulary-v0.1.0.ttl"
EX = Namespace("https://example.org/")


class ValidationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.file = self.directory / SOURCE.name
        self.original = SOURCE.read_text(encoding="utf-8")
        self.graph = Graph().parse(data=self.original, format="turtle")

    def validate(self):
        # N-Triples is a Turtle subset and serializes malformed/cyclic list
        # fixtures without Turtle pretty-printer collection traversal.
        self.graph.serialize(self.file, format="nt", encoding="utf-8")
        build.validate_release(self.file)

    def rejected(self, expected):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaisesRegex(ValueError, expected) as error:
                self.validate()
        self.assertIn(str(self.file), str(error.exception))
        self.assertIn("expected", str(error.exception))
        self.assertIn("observed", str(error.exception))

    def test_historical_source_needs_no_future_metadata(self):
        before = SOURCE.read_bytes()
        build.validate_release(SOURCE)
        self.assertEqual(SOURCE.read_bytes(), before)
        self.assertFalse(list(self.graph.objects(build.DKGM.memberOf, RDFS.isDefinedBy)))

    def test_reordered_turtle_and_alternative_prefixes(self):
        # Valid N-Triples statements also form Turtle; reverse ordering and use
        # full IRIs rather than assuming particular serialization prefix aliases.
        lines = self.graph.serialize(format="nt").splitlines()
        self.file.write_text("\n".join(reversed(lines)) + "\n", encoding="utf-8")
        build.validate_release(self.file)
        self.file.write_text(self.original.replace("dkgm:", "mereology:"), encoding="utf-8")
        build.validate_release(self.file)

    def test_isomorphic_graph_with_renamed_blank_nodes(self):
        renamed = Graph()
        mapping = {node: BNode() for node in self.graph.all_nodes() if isinstance(node, BNode)}
        for triple in self.graph:
            renamed.add(tuple(mapping.get(node, node) for node in triple))
        self.assertTrue(isomorphic(self.graph, renamed))
        self.graph = renamed
        self.validate()

    def test_named_and_explicitly_typed_rdf_list_nodes(self):
        renamed = Graph()
        mapping = {node: URIRef(EX + "list-" + str(index))
                   for index, node in enumerate(self.graph.all_nodes()) if isinstance(node, BNode)}
        for triple in self.graph:
            renamed.add(tuple(mapping.get(node, node) for node in triple))
        for node in mapping.values():
            renamed.add((node, RDF.type, RDF.List))
        self.graph = renamed
        self.validate()

    def test_repeated_identical_statements_do_not_change_graph(self):
        statements = self.graph.serialize(format="nt")
        self.file.write_text(statements + "\n" + statements, encoding="utf-8")
        self.assertTrue(isomorphic(self.graph, Graph().parse(self.file, format="turtle")))
        build.validate_release(self.file)

    def test_redundant_identical_chain_lists_do_not_add_semantics(self):
        head = BNode()
        Collection(self.graph, head, [build.DKGM.memberOf, build.DKGM.subCollectionOf])
        self.graph.add((build.DKGM.memberOf, OWL.propertyChainAxiom, head))
        self.validate()

    def test_additional_languages_and_multiple_annotations(self):
        for tag in ("nl", "pt-BR", "zh-Hant", "en-GB", "de-CH-1901", "x-private", "i-klingon"):
            for predicate in (RDFS.label, SKOS.definition):
                self.graph.add((build.DKGM.memberOf, predicate, Literal("Additional text", lang=tag)))
        self.graph.add((build.DKGM.memberOf, RDFS.label, Literal("Another label", lang="en")))
        self.validate()

    def test_english_region_tag_satisfies_english_documentation(self):
        for predicate in (RDFS.label, SKOS.definition):
            self.graph.set((build.DKGM.memberOf, predicate, Literal("English text", lang="EN-gb")))
        self.validate()

    def test_multiple_creators(self):
        self.graph.add((build.ONTOLOGY, DCTERMS.creator, EX.creator))
        self.graph.add((EX.creator, RDFS.label, Literal("Another creator")))
        self.validate()

    def test_equivalent_string_literal_forms(self):
        for predicate in (OWL.versionInfo, build.VANN.preferredNamespacePrefix):
            value = self.graph.value(build.ONTOLOGY, predicate)
            self.graph.set((build.ONTOLOGY, predicate, Literal(str(value), datatype=XSD.string)))
        self.graph.set((build.ONTOLOGY, build.VANN.preferredNamespaceUri,
                        Literal(str(build.DKGM), datatype=XSD.anyURI)))
        self.validate()

    def test_invalid_turtle(self):
        self.file.write_text("@prefix broken", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "expected valid Turtle") as error:
            build.validate_release(self.file)
        self.assertIn(str(self.file), str(error.exception))

    def test_wrong_or_additional_ontology_identity(self):
        for identity in (EX.ontology, BNode()):
            with self.subTest(identity=identity):
                self.graph.remove((build.ONTOLOGY, RDF.type, OWL.Ontology))
                self.graph.add((identity, RDF.type, OWL.Ontology))
                self.rejected("canonical owl:Ontology")
                self.graph.remove((identity, RDF.type, OWL.Ontology))
                self.graph.add((build.ONTOLOGY, RDF.type, OWL.Ontology))
        self.graph.add((EX.second, RDF.type, OWL.Ontology))
        self.rejected("canonical owl:Ontology")

    def test_identity_namespace_and_license_values_and_node_kinds(self):
        cases = {
            OWL.versionIRI: (EX.wrong, Literal(BASE_VERSION), BNode()),
            OWL.versionInfo: (Literal("9.9.9"), EX.version, Literal("0.1.0", lang="en")),
            build.VANN.preferredNamespacePrefix: (Literal("wrong"), EX.prefix),
            build.VANN.preferredNamespaceUri: (Literal(str(EX)), URIRef(str(build.DKGM))),
            DCTERMS.license: (EX.license, Literal(str(build.LICENSE)), BNode()),
            DCTERMS.creator: (Literal("A person"), BNode()),
        }
        for predicate, values in cases.items():
            original = set(self.graph.objects(build.ONTOLOGY, predicate))
            for value in values:
                with self.subTest(predicate=predicate, value=value):
                    self.graph.set((build.ONTOLOGY, predicate, value))
                    self.rejected(str(predicate))
            self.graph.remove((build.ONTOLOGY, predicate, None))
            for value in original:
                self.graph.add((build.ONTOLOGY, predicate, value))

    def test_every_required_metadata_field_is_checked(self):
        for predicate in (OWL.versionIRI, OWL.versionInfo, build.VANN.preferredNamespacePrefix,
                          build.VANN.preferredNamespaceUri, DCTERMS.title, DCTERMS.description,
                          DCTERMS.creator, DCTERMS.license, DCTERMS.created, DCTERMS.modified):
            with self.subTest(predicate=predicate):
                values = set(self.graph.objects(build.ONTOLOGY, predicate))
                self.graph.remove((build.ONTOLOGY, predicate, None))
                self.rejected(str(predicate))
                for value in values:
                    self.graph.add((build.ONTOLOGY, predicate, value))

    def test_conflicting_single_valued_metadata(self):
        for predicate, value in ((OWL.versionIRI, EX.version),
                                 (OWL.versionInfo, Literal("0.2.0")),
                                 (build.VANN.preferredNamespacePrefix, Literal("other")),
                                 (build.VANN.preferredNamespaceUri, Literal(str(EX))),
                                 (DCTERMS.license, EX.license),
                                 (DCTERMS.created, Literal("2020-01-01T00:00:00Z", datatype=XSD.dateTime)),
                                 (DCTERMS.modified, Literal("2030-01-01T00:00:00Z", datatype=XSD.dateTime))):
            with self.subTest(predicate=predicate):
                self.graph.add((build.ONTOLOGY, predicate, value))
                self.rejected(str(predicate))
                self.graph.remove((build.ONTOLOGY, predicate, value))

    def test_required_text_metadata_is_nonempty_text(self):
        for predicate in (DCTERMS.title, DCTERMS.description):
            original = self.graph.value(build.ONTOLOGY, predicate)
            for value in (Literal(" \t"), EX.text, Literal(12)):
                with self.subTest(predicate=predicate, value=value):
                    self.graph.set((build.ONTOLOGY, predicate, value))
                    self.rejected(str(predicate))
            self.graph.set((build.ONTOLOGY, predicate, original))

    def test_invalid_date_syntax_values_datatypes_and_offsets(self):
        original = self.graph.value(build.ONTOLOGY, DCTERMS.modified)
        for lexical, datatype in (
            ("not-a-date", XSD.dateTime),
            ("2026-09-28 10:49:25Z", XSD.dateTime),
            ("2026-09-28", XSD.date),
            ("2026-09-28T10:49:25Z", None),
            ("2026-02-30T10:00:00Z", XSD.dateTime),
            ("2026-13-01T10:00:00Z", XSD.dateTime),
            ("2026-09-28T25:00:00Z", XSD.dateTime),
            ("2026-09-28T10:60:00Z", XSD.dateTime),
            ("2026-09-28T10:00:60Z", XSD.dateTime),
            ("2026-09-28T10:49:25+15:00", XSD.dateTime),
            ("2026-09-28T10:49:25+14:01", XSD.dateTime),
            ("2026-09-28T10:49:25+00:60", XSD.dateTime),
        ):
            with self.subTest(lexical=lexical, datatype=datatype):
                with contextlib.redirect_stderr(io.StringIO()):
                    value = Literal(lexical, datatype=datatype, normalize=False)
                self.graph.set((build.ONTOLOGY, DCTERMS.modified, value))
                self.rejected(str(DCTERMS.modified))
        self.graph.set((build.ONTOLOGY, DCTERMS.modified, EX.date))
        self.rejected(str(DCTERMS.modified))
        self.graph.set((build.ONTOLOGY, DCTERMS.modified, original))

    def dates(self, created, modified):
        for predicate, value in ((DCTERMS.created, created), (DCTERMS.modified, modified)):
            self.graph.set((build.ONTOLOGY, predicate,
                            Literal(value, datatype=XSD.dateTime, normalize=False)))

    def test_chronology_uses_offsets_not_wall_clock_order(self):
        self.dates("2026-09-28T12:00:00+02:00", "2026-09-28T11:00:00Z")
        self.validate()
        self.dates("2026-09-28T10:00:00Z", "2026-09-28T11:00:00+02:00")
        self.rejected("created <= modified")

    def test_equal_instants_fractional_precision_and_midnight(self):
        for created, modified in (
            ("2026-09-28T12:00:00+02:00", "2026-09-28T10:00:00Z"),
            ("2026-09-28T10:00:00.0000001Z", "2026-09-28T10:00:00.0000002Z"),
            ("2026-09-28T24:00:00Z", "2026-09-29T00:00:00Z"),
        ):
            with self.subTest(created=created, modified=modified):
                self.dates(created, modified)
                self.validate()
        self.dates("2026-09-28T10:00:00.0000002Z", "2026-09-28T10:00:00.0000001Z")
        self.rejected("created <= modified")
        # Decimal's default precision must not erase differences far below a microsecond.
        self.dates("2026-09-28T10:00:00." + "0" * 40 + "2Z",
                   "2026-09-28T10:00:00." + "0" * 40 + "1Z")
        self.rejected("created <= modified")

    def test_missing_timezones_are_not_assumed_to_be_local(self):
        self.dates("2026-09-28T10:00:00", "2026-09-28T11:00:00")
        self.validate()
        self.dates("2026-09-28T10:00:00", "2026-09-28T11:00:00Z")
        self.rejected("unambiguous timezone ordering")
        self.dates("2026-09-28T10:00:00", "2026-09-30T11:00:00Z")
        self.validate()

    def test_missing_and_incorrect_property_types(self):
        for term in build.SOURCE_CONTRACTS["0.1.0"].properties:
            with self.subTest(term=term):
                self.graph.remove((term, RDF.type, OWL.ObjectProperty))
                self.rejected("owl:ObjectProperty")
                self.graph.add((term, RDF.type, OWL.DatatypeProperty))
                self.rejected("owl:ObjectProperty")
                self.graph.remove((term, RDF.type, OWL.DatatypeProperty))
                self.graph.add((term, RDF.type, OWL.ObjectProperty))

    def test_unsupported_terms_and_foreign_source_properties(self):
        for term in (build.DKGM.unapproved, EX.sourceProperty):
            with self.subTest(term=term):
                self.graph.add((term, RDF.type, OWL.ObjectProperty))
                self.rejected(str(term))
                self.graph.remove((term, RDF.type, OWL.ObjectProperty))

    def test_missing_chains(self):
        for term in (build.DKGM.memberOf, build.DKGM.subCollectionOf, build.DKGM.subQuantityOf):
            with self.subTest(term=term):
                head = self.graph.value(term, OWL.propertyChainAxiom)
                self.graph.remove((term, OWL.propertyChainAxiom, head))
                self.rejected(str(OWL.propertyChainAxiom))
                self.graph.add((term, OWL.propertyChainAxiom, head))

    def test_reordered_or_incorrect_operands(self):
        head = self.graph.value(build.DKGM.memberOf, OWL.propertyChainAxiom)
        tail = self.graph.value(head, RDF.rest)
        self.graph.set((head, RDF.first, build.DKGM.subCollectionOf))
        self.graph.set((tail, RDF.first, build.DKGM.memberOf))
        self.rejected(str(OWL.propertyChainAxiom))
        self.graph.set((head, RDF.first, build.DKGM.memberOf))
        self.graph.set((tail, RDF.first, EX.wrongOperand))
        self.rejected(str(OWL.propertyChainAxiom))

    def test_incorrect_conclusion_and_additional_chains(self):
        for term in (build.DKGM.componentOf, EX.unapprovedConclusion):
            with self.subTest(term=term):
                head = self.graph.value(build.DKGM.memberOf, OWL.propertyChainAxiom)
                self.graph.add((term, OWL.propertyChainAxiom, head))
                self.rejected(str(OWL.propertyChainAxiom))
                self.graph.remove((term, OWL.propertyChainAxiom, head))
        head = BNode()
        Collection(self.graph, head, [build.DKGM.memberOf, build.DKGM.memberOf])
        self.graph.add((build.DKGM.memberOf, OWL.propertyChainAxiom, head))
        self.rejected(str(OWL.propertyChainAxiom))

    def test_empty_short_and_long_collections(self):
        original_head = self.graph.value(build.DKGM.memberOf, OWL.propertyChainAxiom)
        for operands in ([], [build.DKGM.memberOf], [build.DKGM.memberOf] * 3):
            with self.subTest(operands=operands):
                head = RDF.nil if not operands else BNode()
                if operands:
                    Collection(self.graph, head, operands)
                self.graph.set((build.DKGM.memberOf, OWL.propertyChainAxiom, head))
                self.rejected(str(OWL.propertyChainAxiom))
        self.graph.set((build.DKGM.memberOf, OWL.propertyChainAxiom, original_head))

    def test_missing_ambiguous_and_literal_list_links(self):
        for predicate in (RDF.first, RDF.rest):
            head = self.graph.value(build.DKGM.memberOf, OWL.propertyChainAxiom)
            original = self.graph.value(head, predicate)
            for value in (None, Literal("invalid")):
                with self.subTest(predicate=predicate, value=value):
                    self.graph.remove((head, predicate, None))
                    if value is not None:
                        self.graph.add((head, predicate, value))
                    self.rejected("first|rest|propertyChainAxiom")
            self.graph.set((head, predicate, original))
            self.graph.add((head, predicate, EX.ambiguous))
            self.rejected(str(predicate))
            self.graph.remove((head, predicate, EX.ambiguous))

    def test_cycles_and_incorrect_termination(self):
        head = self.graph.value(build.DKGM.memberOf, OWL.propertyChainAxiom)
        tail = self.graph.value(head, RDF.rest)
        for termination in (head, tail, EX.notNil, Literal("nil")):
            with self.subTest(termination=termination):
                self.graph.set((tail, RDF.rest, termination))
                self.rejected("first|rest|propertyChainAxiom")

    def test_detached_list_axioms_are_rejected(self):
        self.graph.add((BNode(), RDF.first, build.DKGM.memberOf))
        self.rejected(str(RDF.first))

    def test_unauthorized_characteristics_and_alignments(self):
        for characteristic in (OWL.AsymmetricProperty, OWL.IrreflexiveProperty,
                               OWL.TransitiveProperty, OWL.SymmetricProperty,
                               OWL.ReflexiveProperty, OWL.FunctionalProperty,
                               OWL.InverseFunctionalProperty, OWL.DatatypeProperty):
            with self.subTest(characteristic=characteristic):
                triple = (build.DKGM.componentOf, RDF.type, characteristic)
                self.graph.add(triple)
                self.rejected(str(RDF.type))
                self.graph.remove(triple)
        gufo = URIRef("http://purl.org/nemo/gufo#isComponentOf")
        for triple in (
            (build.DKGM.memberOf, RDFS.domain, EX.Collective),
            (build.DKGM.memberOf, RDFS.range, EX.Collective),
            (build.DKGM.memberOf, OWL.inverseOf, EX.hasMember),
            (EX.hasMember, OWL.inverseOf, build.DKGM.memberOf),
            (build.DKGM.componentOf, RDFS.subPropertyOf, gufo),
            (gufo, OWL.equivalentProperty, build.DKGM.componentOf),
            (EX.source, RDFS.subPropertyOf, build.DKGM.memberOf),
            (build.ONTOLOGY, OWL.imports, URIRef("http://purl.org/nemo/gufo")),
            (build.ONTOLOGY, OWL.imports, EX.otherOntology),
        ):
            with self.subTest(triple=triple):
                self.graph.add(triple)
                self.rejected(str(triple[1]))
                self.graph.remove(triple)

    def test_missing_invalid_or_nonenglish_term_annotations(self):
        for predicate in (RDFS.label, SKOS.definition):
            original = self.graph.value(build.DKGM.memberOf, predicate)
            self.graph.remove((build.DKGM.memberOf, predicate, None))
            self.rejected(str(predicate))
            for value in (Literal(""), Literal("Text"), Literal("Tekst", lang="nl"),
                          Literal("Invalid language", lang="e"),
                          Literal("Invalid region", lang="en-12"),
                          Literal("Repeated variant", lang="en-1901-1901"),
                          Literal("Repeated extension", lang="en-a-foo-a-bar"),
                          Literal("Missing language", datatype=RDF.langString),
                          Literal(12), EX.text):
                with self.subTest(predicate=predicate, value=value):
                    self.graph.set((build.DKGM.memberOf, predicate, value))
                    self.rejected(str(predicate))
            self.graph.set((build.DKGM.memberOf, predicate, original))

    def test_future_release_needs_its_own_reviewed_contract(self):
        self.file = self.directory / "dkgm-vocabulary-v0.2.0.ttl"
        self.graph.set((build.ONTOLOGY, OWL.versionInfo, Literal("0.2.0")))
        self.graph.set((build.ONTOLOGY, OWL.versionIRI, URIRef(build.BASE + "/0.2.0")))
        self.rejected("unregistered version 0.2.0")
        # A reviewed registration can reuse the unchanged contract without
        # altering the historical mapping. No real release is created here.
        with patch.dict(build.SOURCE_CONTRACTS, {"0.2.0": build.SOURCE_CONTRACTS["0.1.0"]}):
            self.validate()
            build.validate_release(SOURCE)

    def test_generation_and_read_only_use_the_same_validator(self):
        with patch.object(build, "releases", return_value=[SOURCE]), \
                patch.object(build, "validate_release", side_effect=ValueError("source rejected")), \
                patch.object(build.subprocess, "run") as generate, \
                patch.object(build.shutil, "copyfile") as copy:
            for action in (build.build, build.check_sources):
                with self.subTest(action=action):
                    with self.assertRaisesRegex(ValueError, "source rejected"):
                        action()
            generate.assert_not_called()
            copy.assert_not_called()

    def test_read_only_default_and_explicit_files_leave_tree_unchanged(self):
        root = self.directory / "checkout"
        shutil.copytree(build.ROOT / "vocabulary", root / "vocabulary",
                        ignore=shutil.ignore_patterns("__pycache__"))
        sentinel = root / "vocabulary/latest/sentinel.txt"
        sentinel.write_text("read-only does not inspect or repair generated artifacts")
        # Historical HTML limitations (or even missing HTML) do not affect source validation.
        (root / "vocabulary/versioned/dkgm-vocabulary-v0.1.0.html").unlink()
        script = root / "vocabulary/scripts/build.py"

        def snapshot():
            return {str(p.relative_to(root)): (
                        p.read_bytes() if p.is_file() else None,
                        p.stat().st_mtime_ns, p.stat().st_mode)
                    for p in root.rglob("*")}

        before = snapshot()
        for sources in ([], [str(root / "vocabulary/versioned" / SOURCE.name)]):
            result = subprocess.run([sys.executable, "-B", str(script), "--check-only", *sources],
                                    cwd=root, capture_output=True, text=True,
                                    env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("no files generated or modified", result.stdout)
            self.assertEqual(snapshot(), before)

        bad = root / "vocabulary/versioned" / SOURCE.name
        bad.write_text("invalid Turtle", encoding="utf-8")
        before = snapshot()
        result = subprocess.run([sys.executable, "-B", str(script), "--check-only"],
                                cwd=root, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(str(bad), result.stderr)
        self.assertEqual(snapshot(), before)

    def test_explicit_sources_require_read_only_flag(self):
        result = subprocess.run([sys.executable, "-B", str(BUILD_PATH), str(SOURCE)],
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("require --check-only", result.stderr)


BASE_VERSION = build.BASE + "/0.1.0"


if __name__ == "__main__":
    unittest.main()
