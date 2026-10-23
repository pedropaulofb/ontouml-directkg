"""HTTP verification-code tests with mocked responses, never a real deployment."""
import contextlib
import importlib.util
import io
import sys
import unittest
from unittest.mock import MagicMock, patch

import requests

from test_publication import build


SPEC = importlib.util.spec_from_file_location("dkgm_verification", build.ROOT / "vocabulary/scripts/verify_deployment.py")
verification = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = verification
with patch.dict(sys.modules, {"build": build}):
    SPEC.loader.exec_module(verification)


def response(status=200, body=b"", *, location=None, media="text/html"):
    result = requests.Response()
    result.status_code = status
    result._content = body
    result.headers["Content-Type"] = media
    if location is not None:
        result.headers["Location"] = location
    return result


class FakeSession:
    def __init__(self):
        self.calls = []
        self.responses = {}
        for uri, accept, status, target, source in verification.route_specs():
            self.responses[(uri, accept)] = response(status, location=target)
            self.responses[(target, accept)] = response(body=source.read_bytes(), media=accept)

    def get(self, url, *, headers, timeout, allow_redirects):
        self.calls.append((url, headers, timeout, allow_redirects))
        result = self.responses[(url, headers["Accept"])]
        if isinstance(result, list):
            result = result.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


class VerificationTests(unittest.TestCase):
    def setUp(self):
        self.session = FakeSession()
        self.sleeps = []
        self.verifier = verification.PublicVerifier(self.session, sleep=self.sleeps.append)
        self.spec = verification.route_specs()[0]

    def reject(self, kind):
        with self.assertRaises(verification.VerificationFailure) as error:
            self.verifier.check(self.spec)
        self.assertEqual(error.exception.kind, kind)
        return str(error.exception)

    def test_registered_current_and_versioned_routes(self):
        specs = verification.route_specs()
        current = specs[:4]
        self.assertEqual([(s[0], s[1], s[2]) for s in current], [
            (build.BASE, "text/html", 303), (build.BASE, "text/turtle", 303),
            (build.BASE + "/docs", "text/html", 302), (build.BASE + "/ttl", "text/turtle", 302)])
        for source in build.releases():
            version = build.version_of(source)
            rows = [s for s in specs if s[0] == build.BASE + "/" + version]
            self.assertEqual(len(rows), 2)
            self.assertTrue(all(s[2] == 303 and f"-v{version}." in s[3] for s in rows))

    def test_success_all_routes_bounded_requests_and_no_file_changes(self):
        before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in (build.ROOT / "vocabulary").rglob("*") if p.is_file()}
        with contextlib.redirect_stdout(io.StringIO()):
            verification.verify(self.session, sleep=self.sleeps.append)
        specs = verification.route_specs()
        targets = {(s[3], s[1]) for s in specs}
        self.assertEqual(len(self.session.calls), len(specs) + len(targets))
        self.assertTrue(all(call[2:] == (verification.TIMEOUT, False) for call in self.session.calls))
        self.assertEqual(self.sleeps, [])
        self.assertEqual({p: (p.read_bytes(), p.stat().st_mtime_ns) for p in before}, before)

    def test_wrong_pid_redirect_status_and_destination_are_not_retried(self):
        uri, accept, status, target, _ = self.spec
        for result in (response(301, location=target), response(status, location="https://example.org/wrong")):
            self.session.responses[(uri, accept)] = result
            self.reject("redirect")
        self.assertEqual(self.sleeps, [])
        self.assertEqual(len(self.session.calls), 2)

    def test_ordinary_https_canonicalization_is_accepted(self):
        _, accept, _, target, source = self.spec
        canonical = "https://example.org/canonical/vocabulary.html"
        self.session.responses[(target, accept)] = response(301, location=canonical)
        self.session.responses[(canonical, accept)] = response(body=source.read_bytes())
        self.assertEqual(self.verifier.check(self.spec), canonical)

    def test_cyclic_unsafe_and_excessive_redirects_fail(self):
        _, accept, _, target, _ = self.spec
        for destination in (target, "http://example.org/downgrade"):
            self.session.responses[(target, accept)] = response(302, location=destination)
            self.reject("redirect")
        for index in range(7):
            url = target if index == 0 else f"https://example.org/hop{index}"
            self.session.responses[(url, accept)] = response(302, location=f"https://example.org/hop{index + 1}")
        self.assertIn("five", self.reject("redirect"))

    def test_incorrect_html_or_turtle_bytes_fail_with_hash_diagnostics(self):
        for spec in verification.route_specs()[:2]:
            with self.subTest(accept=spec[1]):
                self.spec = spec
                self.session.responses[(spec[3], spec[1])] = response(body=b"wrong version", media=spec[1])
                message = self.reject("content")
                self.assertIn("SHA-256", message)
                self.assertIn(str(spec[4]), message)

    def test_bad_content_type_fails_and_turtle_static_fallback_is_allowed(self):
        _, accept, _, target, source = self.spec
        self.session.responses[(target, accept)] = response(body=source.read_bytes(), media="application/json")
        self.assertIn("Content-Type", self.reject("content"))
        self.spec = verification.route_specs()[1]
        self.session.responses[(self.spec[3], self.spec[1])] = response(body=self.spec[4].read_bytes(), media="text/plain")
        self.verifier.check(self.spec)

    def test_timeouts_and_external_statuses_are_bounded_and_distinct(self):
        uri, accept, *_ = self.spec
        for failure in (requests.Timeout("fixture timeout"), response(503), response(429)):
            with self.subTest(failure=failure):
                self.session.responses[(uri, accept)] = failure
                self.sleeps.clear()
                start = len(self.session.calls)
                self.reject("external")
                self.assertEqual(len(self.session.calls) - start, 3)
                self.assertEqual(self.sleeps, [1, 2])

    def test_transient_failure_and_propagating_content_can_recover(self):
        uri, accept, status, target, source = self.spec
        self.session.responses[(uri, accept)] = [response(503), response(status, location=target), response(status, location=target)]
        self.session.responses[(target, accept)] = [response(body=b"old cached content"), response(body=source.read_bytes())]
        self.verifier.check(self.spec)
        self.assertEqual(self.sleeps, [1, 2])

    def test_unavailable_representation_is_not_a_semantic_failure(self):
        self.session.responses[(self.spec[3], self.spec[1])] = response(404)
        message = self.reject("availability")
        self.assertIn("HTTP 404", message)
        self.assertNotIn("semantic", message)
        self.assertEqual(self.sleeps, [1, 2])

    def test_command_failure_classification(self):
        for kind, code in (("external", 2), ("availability", 1), ("content", 1), ("redirect", 1)):
            with self.subTest(kind=kind):
                failure = verification.VerificationFailure(kind, "fixture failure")
                output = io.StringIO()
                with patch.object(verification, "verify", side_effect=failure), \
                        patch.object(verification.requests, "Session", return_value=MagicMock()), \
                        contextlib.redirect_stdout(output):
                    self.assertEqual(verification.main(), code)
                self.assertIn("Postdeployment verification", output.getvalue())
                self.assertNotIn("RDF", output.getvalue())


if __name__ == "__main__":
    unittest.main()
