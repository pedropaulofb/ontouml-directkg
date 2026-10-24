"""DirectKG vocabulary publication regression tests (independent of converter code)."""
import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from bs4 import BeautifulSoup
from rdflib import Graph

BUILD_PATH = Path(__file__).resolve().parents[1] / "build.py"
SPEC = importlib.util.spec_from_file_location("vocabulary_builder", BUILD_PATH)
build = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = build
SPEC.loader.exec_module(build)


class PublicationTests(unittest.TestCase):
    def test_original_version_metadata_and_mereology(self):
        source = build.ROOT / "vocabulary/versioned/dkgm-vocabulary-v0.1.0.ttl"
        build.validate_release(source)
        graph = Graph().parse(source)
        self.assertGreater(len(graph), 0)
        self.assertEqual(build.releases()[-1].read_bytes(),
                         (build.ROOT / "vocabulary/latest/dkgm-vocabulary.ttl").read_bytes())

    def test_numeric_version_selection(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            directory = root / "vocabulary/versioned"
            directory.mkdir(parents=True)
            for version in ("0.2.0", "0.10.0", "0.9.0"):
                (directory / f"dkgm-vocabulary-v{version}.ttl").touch()
            with patch.object(build, "ROOT", root):
                self.assertEqual([build.version_of(p) for p in build.releases()],
                                 ["0.2.0", "0.9.0", "0.10.0"])

    def test_invalid_release_filenames_fail(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "vocabulary/versioned"
            directory.mkdir(parents=True)
            (directory / "dkgm-vocabulary-v0.1.0.ttl").touch()
            (directory / "dkgm-vocabulary-v0.2.ttl").touch()
            with patch.object(build, "ROOT", directory.parents[1]):
                with self.assertRaisesRegex(ValueError, "Invalid release filename"):
                    build.releases()

    def test_incorrect_version_metadata_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            original = build.ROOT / "vocabulary/versioned/dkgm-vocabulary-v0.1.0.ttl"
            wrong = Path(temporary) / "dkgm-vocabulary-v0.2.0.ttl"
            shutil.copyfile(original, wrong)
            with self.assertRaisesRegex(ValueError, "versionIRI"):
                build.validate_release(wrong)

    def test_definition_customization_preserves_turtle(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = build.ROOT / "vocabulary/versioned/dkgm-vocabulary-v0.1.0.ttl"
            before = source.read_bytes()
            page = Path(temporary) / "doc.html"
            page.write_text('''<html><head></head><body>
<div id="metadata"><h1>Vocabulary</h1></div>
<div class="property entity"><table><tr><th>IRI</th>
<td><code>https://w3id.org/directkg/vocab/dkgm#memberOf</code></td>
</tr></table></div></body></html>''')
            build.customize_documentation(page, source)
            soup = BeautifulSoup(page.read_text(), "html.parser")
            row = soup.select_one('.property.entity a[href="http://www.w3.org/2004/02/skos/core#definition"]')
            self.assertIsNotNone(row)
            self.assertIn("Relates a member to a collective", row.find_parent("tr").get_text())
            self.assertEqual(source.read_bytes(), before)

    def test_existing_html_is_never_regenerated(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            vdir = root / "vocabulary/versioned"
            vdir.mkdir(parents=True)
            source = build.ROOT / "vocabulary/versioned/dkgm-vocabulary-v0.1.0.ttl"
            shutil.copyfile(source, vdir / source.name)
            html = vdir / "dkgm-vocabulary-v0.1.0.html"
            shutil.copyfile(source.with_suffix('.html'), html)
            original = html.read_bytes()
            with patch.object(build, "ROOT", root), patch.object(build.subprocess, "run") as invoke:
                build.build()
                build.build()
            invoke.assert_not_called()
            self.assertEqual(html.read_bytes(), original)
            self.assertEqual((root / "vocabulary/latest/index.html").read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
