"""Read-only HTTP verification after an authorized Pages deployment; never deploys."""
from __future__ import annotations

import hashlib
import time
from urllib.parse import urljoin, urlsplit

import requests

import build


# Registered targets in perma-id/w3id.org/ids/directkg/.htaccess, inspected for
# Wave 3. No GitHub releases, packages or additional W3ID routes are assumed.
SITE = "https://pedropaulofb.github.io/ontouml-directkg/"
TIMEOUT = (5, 15)
ATTEMPTS = 3
REDIRECTS = {301, 302, 303, 307, 308}


class VerificationFailure(ValueError):
    def __init__(self, kind, message):
        self.kind = kind
        super().__init__(message)


def route_specs():
    """Return registered PID, Accept, redirect status, target and expected file."""
    versions = build.releases()
    latest = build.ROOT / "vocabulary/latest"
    groups = [(build.BASE, latest / "index.html", latest / build.LATEST_NAME)]
    groups.extend((f"{build.BASE}/{build.version_of(source)}", source.with_suffix(".html"), source)
                  for source in versions)
    result = []
    for iri, html, turtle in groups:
        for suffix, accept, status, source in (
            ("", "text/html", 303, html), ("", "text/turtle", 303, turtle),
            ("/docs", "text/html", 302, html), ("/ttl", "text/turtle", 302, turtle),
        ):
            relative = source.relative_to(build.ROOT).as_posix()
            result.append((iri + suffix, accept, status, urljoin(SITE, relative), source))
    return result


class PublicVerifier:
    def __init__(self, session, *, sleep=time.sleep):
        self.session = session
        self.sleep = sleep
        self.validated = {}

    def get(self, url, accept):
        try:
            response = self.session.get(url, headers={"Accept": accept}, timeout=TIMEOUT,
                                        allow_redirects=False)
        except requests.RequestException as error:
            raise VerificationFailure("external", f"{url}: HTTP request unavailable: {error}") from error
        if response.status_code in {408, 429} or response.status_code >= 500:
            raise VerificationFailure("external", f"{url}: external HTTP {response.status_code}")
        if response.status_code >= 400:
            raise VerificationFailure("availability", f"{url}: representation unavailable (HTTP {response.status_code})")
        return response

    def follow(self, target, accept):
        seen = set()
        url = target
        for _ in range(6):
            parsed = urlsplit(url)
            if parsed.scheme != "https" or parsed.username or parsed.password or url in seen:
                raise VerificationFailure("redirect", f"{target}: unsafe or cyclic representation redirect to {url}")
            seen.add(url)
            response = self.get(url, accept)
            if response.status_code == 200:
                return response, url
            if response.status_code not in REDIRECTS or not response.headers.get("Location"):
                raise VerificationFailure("redirect", f"{url}: expected HTTP 200 or a valid redirect; observed HTTP {response.status_code}")
            # Ordinary HTTPS canonicalization may change the host or URL. The
            # registered W3ID hop is checked separately; final bytes must match.
            url = urljoin(url, response.headers["Location"])
        raise VerificationFailure("redirect", f"{target}: exceeded five representation redirects")

    def check_once(self, spec):
        uri, accept, status, target, source = spec
        response = self.get(uri, accept)
        location = urljoin(uri, response.headers.get("Location", ""))
        if response.status_code != status or location != target:
            raise VerificationFailure("redirect", f"{uri} [Accept: {accept}]: expected HTTP {status} to {target}; observed HTTP {response.status_code} to {location}")
        expected = source.read_bytes()
        digest = hashlib.sha256(expected).hexdigest()
        key = (target, accept, digest)
        if key not in self.validated:
            final, final_url = self.follow(target, accept)
            media_type = final.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            allowed = {"text/html"} if accept == "text/html" else {
                "text/turtle", "application/x-turtle", "text/plain", "application/octet-stream"}
            if media_type not in allowed:
                raise VerificationFailure("content", f"{final_url}: expected {accept} representation; observed Content-Type {media_type!r}")
            if final.content != expected:
                actual = hashlib.sha256(final.content).hexdigest()
                raise VerificationFailure("content", f"{final_url}: expected bytes from {source} (SHA-256 {digest}); observed SHA-256 {actual}")
            self.validated[key] = final_url
        return self.validated[key]

    def check(self, spec):
        for attempt in range(ATTEMPTS):
            try:
                return self.check_once(spec)
            except VerificationFailure as error:
                if error.kind == "redirect" or attempt == ATTEMPTS - 1:
                    raise
                # Covers network outages and short Pages/CDN propagation delays.
                # Failed content is never cached as a successful representation.
                self.sleep(attempt + 1)


def verify(session, *, sleep=time.sleep):
    # Validate the intended local artifacts through the existing contracts first.
    # An HTTP content mismatch is reported as such, not as an RDF semantic defect.
    build.check_artifacts(build.ROOT / "vocabulary")
    verifier = PublicVerifier(session, sleep=sleep)
    specs = route_specs()
    for spec in specs:
        final = verifier.check(spec)
        print(f"Verified {spec[0]} [Accept: {spec[1]}] -> {final}")
    print(f"Postdeployment verification passed for {len(specs)} registered PID/representation requests.")


def main():
    try:
        with requests.Session() as session:
            verify(session)
    except VerificationFailure as error:
        # Deployment already happened. Do not label external unavailability as a
        # deployment-action failure, local validation failure or semantic defect.
        label = "inconclusive due to external infrastructure" if error.kind == "external" else f"{error.kind} failure"
        print(f"Postdeployment verification {label}: {error}")
        return 2 if error.kind == "external" else 1
    except (ValueError, OSError) as error:
        print(f"Postdeployment verification input validation failed: {error}")
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
