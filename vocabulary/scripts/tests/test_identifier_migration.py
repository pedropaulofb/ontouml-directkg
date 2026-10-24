"""Exact pre-release identity correction and continued historical protection."""
import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from bs4 import BeautifulSoup
from rdflib import Graph, URIRef
from rdflib.compare import isomorphic
from rdflib.namespace import OWL, RDF

from test_publication import build


REPOSITORY = build.ROOT
BASELINE = 'cbcfa428356a7e2ee7d41521c18fcbb7a849dbc2'
CANONICAL = 'https://w3id.org/directkg/vocab/dkgm'
FORMER = CANONICAL.removesuffix('/dkgm')


def original_bytes(path):
    return subprocess.check_output(['git', 'show', f'{BASELINE}:{path}'], cwd=REPOSITORY)


class IdentifierMigrationTests(unittest.TestCase):
    def test_only_identifiers_change_in_both_retained_releases(self):
        self.assertEqual(build.BASE, CANONICAL)
        self.assertEqual(set(build.IDENTIFIER_CORRECTION), {
            f'vocabulary/versioned/dkgm-vocabulary-v{version}.{suffix}'
            for version in ('0.1.0', '0.1.1') for suffix in ('ttl', 'html')})
        for name, (before, after) in build.IDENTIFIER_CORRECTION.items():
            with self.subTest(path=name):
                original = original_bytes(name)
                current = (REPOSITORY / name).read_bytes()
                self.assertEqual(hashlib.sha256(original).hexdigest(), before)
                self.assertEqual(hashlib.sha256(current).hexdigest(), after)
                # Exact byte comparison protects all annotations, axioms, dates,
                # embedded assets, and historical presentation beyond identity.
                self.assertEqual(current, original.replace(FORMER.encode(), CANONICAL.encode()))
                if name.endswith('.ttl'):
                    expected = Graph().parse(data=original.decode().replace(FORMER, CANONICAL), format='turtle')
                    self.assertTrue(isomorphic(Graph().parse(data=current, format='turtle'), expected))
                else:
                    soup = BeautifulSoup(current, 'html.parser')
                    data = json.loads(soup.select_one('script[type="application/ld+json"]').string)
                    self.assertIn(CANONICAL, [item.get('@id') for item in data])
        build.check_artifacts(REPOSITORY / 'vocabulary')

    def test_correction_is_exact_path_specific_and_cannot_be_reapplied(self):
        for name in build.IDENTIFIER_CORRECTION:
            original = original_bytes(name)
            current = (REPOSITORY / name).read_bytes()
            with self.subTest(path=name):
                self.assertTrue(build.historical_bytes_match(name, original, current))
                self.assertTrue(build.historical_bytes_match(name, current, current))
                for baseline, candidate in ((original, original), (original, current + b'\n'),
                                            (current, original), (current, current + b'\n'),
                                            (original + b'\n', current)):
                    self.assertFalse(build.historical_bytes_match(name, baseline, candidate))
                self.assertFalse(build.historical_bytes_match('vocabulary/versioned/unlisted.ttl', original, current))

    def test_all_rdf_representations_declare_exact_ontology_version_and_terms(self):
        vocabulary = REPOSITORY / 'vocabulary'
        sources = [*sorted((vocabulary / 'versioned').glob('*.ttl')), vocabulary / 'latest/dkgm-vocabulary.ttl']
        for source in sources:
            with self.subTest(path=source):
                graph = Graph().parse(source)
                ontology = URIRef(CANONICAL)
                self.assertEqual(set(graph.subjects(RDF.type, OWL.Ontology)), {ontology})
                version = '0.1.0' if 'v0.1.0' in source.name else '0.1.1'
                self.assertEqual(set(graph.objects(ontology, OWL.versionIRI)), {URIRef(CANONICAL + '/' + version)})
                self.assertEqual(set(graph.subjects(RDF.type, OWL.ObjectProperty)), {
                    URIRef(CANONICAL + '#' + name)
                    for name in ('memberOf', 'subCollectionOf', 'subQuantityOf', 'componentOf')})
                self.assertFalse(list(graph.triples((None, OWL.equivalentProperty, None))))

    def test_legacy_identifiers_are_rejected_in_rdf_and_embedded_html(self):
        with tempfile.TemporaryDirectory() as temporary:
            for suffix in ('ttl', 'html'):
                name = f'dkgm-vocabulary-v0.1.0.{suffix}'
                source = REPOSITORY / 'vocabulary/versioned' / name
                target = Path(temporary) / name
                target.write_text(source.read_text().replace(CANONICAL, FORMER))
                with self.subTest(suffix=suffix), self.assertRaisesRegex(ValueError, 'obsolete DKGM identifier'):
                    if suffix == 'ttl':
                        build.validate_release(target)
                    else:
                        build.check_documentation(target, '0.1.0')
        for value in (FORMER, FORMER + '#memberOf', FORMER + '/0.1.0', f'<{FORMER}>',
                      f'"{FORMER}/0.1.1/docs"', FORMER + '/ttl'):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'obsolete DKGM identifier'):
                build.check_identifier_text(Path('artifact'), value)

    def test_trusted_history_accepts_correction_then_rejects_later_edits_and_removals(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            def git(*args):
                return subprocess.check_output(['git', *args], cwd=root, stderr=subprocess.PIPE).decode().strip()
            def commit(message):
                git('add', 'vocabulary', 'branding')
                git('commit', '-qm', message)
                return git('rev-parse', 'HEAD')
            for name in build.IDENTIFIER_CORRECTION:
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(original_bytes(name))
            for name in (build.LOGO, build.FAVICON):
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(REPOSITORY / name, target)
            git('init', '-q', '--initial-branch=migration-test')
            git('config', 'user.name', 'Identity correction fixture')
            git('config', 'user.email', 'fixture@example.org')
            git('remote', 'add', 'origin', 'https://github.com/pedropaulofb/ontouml-directkg')
            anchor = commit('Original published identities')
            git('update-ref', build.TRUSTED_MAIN, anchor)
            for name in build.IDENTIFIER_CORRECTION:
                shutil.copyfile(REPOSITORY / name, root / name)
            shutil.copytree(REPOSITORY / 'vocabulary/latest', root / 'vocabulary/latest')
            corrected = commit('Apply the exact approved identity correction')
            with patch.object(build, 'ROOT', root), patch.object(build, 'PUBLICATION_ANCHOR', anchor):
                build.check_immutable(anchor)
                build.check_publication()
                git('update-ref', build.TRUSTED_MAIN, corrected)
                build.check_publication()  # accepted main tip; strict prior history
                git('commit', '--allow-empty', '-qm', 'Later unrelated maintenance')
                git('update-ref', build.TRUSTED_MAIN, git('rev-parse', 'HEAD'))
                build.check_publication()  # protection survives later history
                for name in build.IDENTIFIER_CORRECTION:
                    path = root / name
                    current = path.read_bytes()
                    for mutation in ('edit', 'remove', 'revert'):
                        with self.subTest(path=name, mutation=mutation):
                            if mutation == 'remove':
                                path.unlink()
                            else:
                                path.write_bytes(current + b'\n' if mutation == 'edit' else original_bytes(name))
                            with self.assertRaisesRegex(ValueError, 'Immutable release file changed or removed'):
                                build.check_immutable(corrected)
                            bad = commit('Unauthorized later historical change')
                            git('update-ref', build.TRUSTED_MAIN, bad)
                            with self.assertRaisesRegex(ValueError, 'immutable bytes from trusted main history'):
                                build.check_publication_history()
                            path.write_bytes(current)
                            restored = commit('Restore corrected fixture')
                            git('update-ref', build.TRUSTED_MAIN, restored)


if __name__ == '__main__':
    unittest.main()
