"""Publication gates with isolated Git history and real source/staged artifacts."""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from bs4 import BeautifulSoup
from rdflib.namespace import OWL

from test_publication import BUILD_PATH, build


REPOSITORY = build.ROOT


class PublicationIntegrationTests(unittest.TestCase):
    def git(self, *arguments):
        return subprocess.check_output(["git", *arguments], cwd=self.root, stderr=subprocess.PIPE).decode().strip()

    def commit(self, message):
        self.git("add", "vocabulary", "branding")
        self.git("commit", "--allow-empty", "-qm", message)
        return self.git("rev-parse", "HEAD")

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.versioned = self.root / "vocabulary/versioned"
        self.versioned.mkdir(parents=True)
        self.latest = self.root / "vocabulary/latest"
        self.latest.mkdir()
        for suffix, latest_name in (("ttl", build.LATEST_NAME), ("html", "index.html")):
            original = REPOSITORY / f"vocabulary/versioned/dkgm-vocabulary-v0.1.0.{suffix}"
            shutil.copyfile(original, self.versioned / original.name)
            shutil.copyfile(original, self.latest / latest_name)
        for name in (build.LOGO, build.FAVICON):
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPOSITORY / name, target)
        self.git("init", "-q", "--initial-branch=main")
        self.git("config", "user.name", "Publication test fixture")
        self.git("config", "user.email", "fixture@example.org")
        self.git("remote", "add", "origin", "https://github.com/pedropaulofb/ontouml-directkg")
        self.anchor = self.commit("Reviewed historical floor")
        self.git("update-ref", build.TRUSTED_MAIN, self.anchor)
        for suffix, latest_name in (("ttl", build.LATEST_NAME), ("html", "index.html")):
            original = REPOSITORY / f"vocabulary/versioned/dkgm-vocabulary-v0.1.1.{suffix}"
            shutil.copyfile(original, self.versioned / original.name)
            shutil.copyfile(original, self.latest / latest_name)
        script = self.root / "vocabulary/scripts/build.py"
        script.parent.mkdir()
        # Only the pinned Git object is substituted for an isolated repository;
        # all production validation and CLI code is used unchanged.
        script.write_text(BUILD_PATH.read_text().replace(build.PUBLICATION_ANCHOR, self.anchor), encoding="utf-8")
        self.candidate = self.commit("Add a compatible release")
        for name, value in (("ROOT", self.root), ("PUBLICATION_ANCHOR", self.anchor)):
            patcher = patch.object(build, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.site = self.root / "site"
        shutil.copytree(self.root / "vocabulary/versioned", self.site / "vocabulary/versioned")
        shutil.copytree(self.latest, self.site / "vocabulary/latest")
        self.page = self.site / "vocabulary/versioned/dkgm-vocabulary-v0.1.1.html"

    def snapshot(self):
        return {str(p.relative_to(self.root)): (p.read_bytes() if p.is_file() else None,
                                              p.stat().st_mtime_ns, p.stat().st_mode)
                for p in self.root.rglob("*") if ".git" not in p.relative_to(self.root).parts}

    def reject(self, message):
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, message):
            build.check_publication(self.site)
        self.assertEqual(self.snapshot(), before)

    def mutate_html(self, action):
        soup = BeautifulSoup(self.page.read_text(), "html.parser")
        action(soup)
        self.page.write_text(str(soup), encoding="utf-8")

    def test_valid_bundle_and_manual_run_are_read_only(self):
        build.build(publication=True)
        before = self.snapshot()
        build.check_publication(self.site)
        self.assertEqual(self.snapshot(), before)
        # A manual run on the fetched main tip has no push-event predecessor.
        self.git("update-ref", build.TRUSTED_MAIN, self.candidate)
        before = self.snapshot()
        build.check_publication(self.site)
        self.assertEqual(self.snapshot(), before)

    def test_read_only_cli_and_workflow_fail_fast(self):
        script = self.root / "vocabulary/scripts/build.py"
        command = [sys.executable, "-B", str(script), "--check-only", "--publication", "--site", str(self.site)]
        before = self.snapshot()
        result = subprocess.run(command, capture_output=True, text=True, cwd=self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.snapshot(), before)
        self.page.unlink()
        # A failing gate stops the shell before a simulated Pages upload. This
        # executes the production CLI and the workflow's fail-fast shell behavior.
        import shlex
        upload = self.root / "uploaded"
        shell = shlex.join(command) + "\n" + shlex.join([sys.executable, "-c", f"from pathlib import Path; Path({str(upload)!r}).touch()"])
        result = subprocess.run(["bash", "-e", "-c", shell], capture_output=True, text=True, cwd=self.root)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(upload.exists())

    def test_missing_staged_directories_and_versioned_files(self):
        for path in (self.site / "vocabulary/latest/index.html",
                     self.site / "vocabulary/versioned/dkgm-vocabulary-v0.1.0.html", self.page):
            with self.subTest(path=path):
                data = path.read_bytes()
                path.unlink()
                self.reject("complete Turtle/HTML pairs|latest representation differs")
                path.write_bytes(data)
        shutil.rmtree(self.site / "vocabulary")
        self.reject("artifact directory")

    def test_incorrect_latest_copies(self):
        for name in (build.LATEST_NAME, "index.html"):
            with self.subTest(name=name):
                path = self.site / "vocabulary/latest" / name
                original = path.read_bytes()
                path.write_text("stale copy")
                self.reject("latest representation differs")
                path.write_bytes(original)

    def test_historical_changes_removals_and_self_comparison_are_rejected(self):
        self.git("update-ref", build.TRUSTED_MAIN, self.candidate)
        for version in ("0.1.0", "0.1.1"):
            for suffix in ("ttl", "html"):
                with self.subTest(version=version, suffix=suffix):
                    path = self.versioned / f"dkgm-vocabulary-v{version}.{suffix}"
                    original = path.read_bytes()
                    path.write_bytes(original + b"\nchanged\n")
                    bad = self.commit("Unauthorized historical edit")
                    self.git("update-ref", build.TRUSTED_MAIN, bad)
                    self.reject("immutable bytes from trusted main history")
                    if version == "0.1.0" and suffix == "ttl":
                        result = subprocess.run([sys.executable, "-B", str(self.root / "vocabulary/scripts/build.py"),
                                                 "--check-only", "--publication", "--base", "HEAD"],
                                                capture_output=True, text=True, cwd=self.root)
                        self.assertNotEqual(result.returncode, 0)
                        self.assertIn("trusted main history", result.stderr)
                    path.write_bytes(original)
                    restored = self.commit("Restore original fixture bytes")
                    self.git("update-ref", build.TRUSTED_MAIN, restored)
        path = self.versioned / "dkgm-vocabulary-v0.1.0.html"
        path.unlink()
        bad = self.commit("Remove historical snapshot")
        self.git("update-ref", build.TRUSTED_MAIN, bad)
        self.reject("immutable bytes from trusted main history")

    def test_main_merge_accepts_new_files_then_protects_them(self):
        self.git("branch", "release-feature", self.candidate)
        self.git("checkout", "-q", "-B", "main", self.anchor)
        self.commit("Independent main maintenance")
        self.git("merge", "--no-ff", "-m", "Accept compatible release", "release-feature")
        merged = self.git("rev-parse", "HEAD")
        self.git("update-ref", build.TRUSTED_MAIN, merged)
        build.check_publication(self.site)
        path = self.versioned / "dkgm-vocabulary-v0.1.1.html"
        path.write_bytes(path.read_bytes() + b"\nchanged\n")
        bad = self.commit("Alter the accepted release")
        self.git("update-ref", build.TRUSTED_MAIN, bad)
        self.reject("immutable bytes from trusted main history")

    def test_missing_untrusted_shallow_or_stale_integrity_evidence(self):
        self.git("update-ref", "-d", build.TRUSTED_MAIN)
        self.reject("integrity evidence unavailable")
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "integrity evidence unavailable"):
            build.build(publication=True)
        self.assertEqual(self.snapshot(), before)
        self.git("update-ref", build.TRUSTED_MAIN, self.anchor)
        self.git("config", "remote.origin.url", "https://example.org/untrusted")
        self.reject("canonical DirectKG origin")
        self.git("config", "remote.origin.url", "https://github.com/pedropaulofb/ontouml-directkg")
        with patch.object(build, "PUBLICATION_ANCHOR", "0" * 40):
            self.reject("reviewed anchor")
        shallow = self.root / ".git/shallow"
        shallow.write_text(self.candidate + "\n")
        self.reject("complete Git history")
        shallow.unlink()
        later = self.commit("Advance trusted main without artifact changes")
        self.git("update-ref", build.TRUSTED_MAIN, later)
        self.git("checkout", "-q", self.candidate)
        self.reject("stale or unrelated source")

    def test_uncommitted_artifact_changes_and_self_staging_are_rejected(self):
        path = self.versioned / "dkgm-vocabulary-v0.1.1.html"
        original = path.read_bytes()
        path.write_bytes(original + b"\n")
        (self.latest / "index.html").write_bytes(path.read_bytes())
        self.reject("uncommitted publication changes")
        path.write_bytes(original)
        (self.latest / "index.html").write_bytes(original)
        with self.assertRaisesRegex(ValueError, "separate assembled site"):
            build.check_publication(self.root)

    def test_source_to_staged_mismatch_is_rejected(self):
        historical = self.site / "vocabulary/versioned/dkgm-vocabulary-v0.1.0.html"
        historical.write_bytes(historical.read_bytes() + b"\n")
        self.reject("source-to-staged content mismatch")

    def test_broken_local_resources_fragments_and_embedded_assets(self):
        original = self.page.read_bytes()
        for change in ("resource", "fragment", "logo", "favicon"):
            with self.subTest(change=change):
                self.page.write_bytes(original)
                def mutate(soup):
                    if change == "resource":
                        soup.body.append(soup.new_tag("img", src="missing.png"))
                    elif change == "fragment":
                        soup.select_one('a[href="#componentOf"]')["href"] = "#missing"
                    elif change == "logo":
                        soup.select_one("#dkgm-brand img").decompose()
                    else:
                        soup.select_one('link[rel="icon"]').decompose()
                self.mutate_html(mutate)
                self.reject("broken local resource|broken HTML anchor|logo|favicon")

    def test_invalid_staged_rdf_and_incomplete_or_incorrect_html(self):
        turtle = self.page.with_suffix(".ttl")
        original_turtle = turtle.read_bytes()
        turtle.write_text("invalid Turtle")
        self.reject("valid Turtle")
        turtle.write_bytes(original_turtle)
        original = self.page.read_bytes()
        for change in ("term", "chain", "version"):
            with self.subTest(change=change):
                self.page.write_bytes(original)
                def mutate(soup):
                    if change == "term":
                        soup.select_one("#componentOf").decompose()
                    elif change == "chain":
                        soup.select_one(f'#memberOf th a[href="{OWL.propertyChainAxiom}"]').find_parent("tr").find("td").clear()
                    else:
                        soup.select_one(f'dt a[href="{OWL.versionIRI}"]').find_parent("dt").find_next_sibling("dd").string = "wrong version"
                self.mutate_html(mutate)
                self.reject("property sections|property.chain|version metadata")


if __name__ == "__main__":
    unittest.main()
