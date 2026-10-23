# Persistent identifiers and redirects

## Overview

OntoUML DirectKG registers persistent URLs (PIDs) with [W3ID](https://w3id.org/) under the namespace `https://w3id.org/directkg/`. These URLs identify project resources and the DirectKG Mereology Vocabulary (DKGM). A **persistent identifier** is the URL to reference; a **redirect destination** is the current place an HTTP request is sent. Hosting locations can change while the PID remains stable. Prefer W3ID URLs when linking to the registered resources or using their RDF identities.

W3ID provides HTTP redirects, not the hosted documents or ontology content. Registration does not guarantee that a destination has been published or is reachable.

## Which identifier should I use?

| Purpose | Persistent identifier |
| --- | --- |
| Project entry point | `https://w3id.org/directkg/` |
| Documentation website | `https://w3id.org/directkg/docs` |
| Git repository | `https://w3id.org/directkg/git` |
| PyPI distribution page (when available) | `https://w3id.org/directkg/pypi` |
| Latest GitHub release (when available) | `https://w3id.org/directkg/releases/latest` |
| Current DKGM ontology identity | `https://w3id.org/directkg/vocab` |
| Explicit current Turtle document | `https://w3id.org/directkg/vocab/ttl` |
| Version 0.1.0 DKGM ontology identity | `https://w3id.org/directkg/vocab/0.1.0` |

These are registered **project and vocabulary PIDs**. They are different from the ontology and entity IRIs a future DirectKG converter would generate for a particular OntoUML model. For the latter, consult [Identifiers and naming](identifiers.md#base-and-ontology-iris).

## Registered identifiers

The [registered W3ID configuration](https://github.com/perma-id/w3id.org/blob/master/ids/directkg/.htaccess) has **14 redirect-rule families**. The tables document configured mappings; they are not evidence of live HTTP responses or of the existence of every target.

PID paths in these tables are relative to `https://w3id.org/directkg`. Destination abbreviations expand to:

- **SITE**: `https://pedropaulofb.github.io/ontouml-directkg`
- **REPO**: `https://github.com/pedropaulofb/ontouml-directkg`

`X.Y.Z` describes a numeric version **pattern**, not a literal published identifier. The expansions below represent the full absolute destinations in the rewrite rules.

### Project and distribution identifiers

| PID path / pattern | Resource or purpose | Configured redirect destination | HTTP | Qualification |
| --- | --- | --- | --- | --- |
| `/` | Project homepage | `SITE/` | 302 | Same destination as `/docs` |
| `/docs` | Documentation website | `SITE/` | 302 | Documentation entry point |
| `/git` | Source repository | `REPO` | 302 | Project source |
| `/pypi` | Python distribution page | `https://pypi.org/project/ontouml-directkg/` | 302 | Package availability not guaranteed |
| `/releases/latest` | Latest GitHub release | `REPO/releases/latest` | 302 | Requires a published release |
| `/releases/vX.Y.Z` | Specific GitHub release | `REPO/releases/tag/vX.Y.Z` | 302 | Matching tag may not exist |

### Vocabulary and representation identifiers

| PID path / pattern | Resource or purpose | Configured redirect destination | HTTP | Qualification |
| --- | --- | --- | --- | --- |
| `/vocab` | Current DKGM ontology IRI | `SITE/vocabulary/latest/index.html` or `SITE/vocabulary/latest/dkgm-vocabulary.ttl` | 303 | HTML by default; Turtle when `Accept` contains `text/turtle` |
| `/vocab/ttl` | Current Turtle representation | `SITE/vocabulary/latest/dkgm-vocabulary.ttl` | 302 | Explicit Turtle route |
| `/vocab/docs` | Current HTML documentation | `SITE/vocabulary/latest/index.html` | 302 | Explicit HTML route |
| `/vocab/spec` | Alternative HTML documentation alias | `SITE/vocabulary/latest/index.html` | 302 | Not a separate transformation specification |
| `/vocab/X.Y.Z` | Version-specific DKGM ontology IRI | `SITE/vocabulary/versioned/dkgm-vocabulary-vX.Y.Z.html` or `SITE/vocabulary/versioned/dkgm-vocabulary-vX.Y.Z.ttl` | 303 | HTML by default; Turtle when `Accept` contains `text/turtle` |
| `/vocab/X.Y.Z/ttl` | Version-specific Turtle representation | `SITE/vocabulary/versioned/dkgm-vocabulary-vX.Y.Z.ttl` | 302 | Versioned document |
| `/vocab/X.Y.Z/docs` | Version-specific HTML documentation | `SITE/vocabulary/versioned/dkgm-vocabulary-vX.Y.Z.html` | 302 | Versioned document |
| `/vocab/X.Y.Z/spec` | Alternative version-specific HTML alias | `SITE/vocabulary/versioned/dkgm-vocabulary-vX.Y.Z.html` | 302 | Same document as `/docs` |

The registered paths for GitHub releases include `vX.Y.Z`; vocabulary version paths use `X.Y.Z` **without** the `v`. The existing vocabulary artifact is version **0.1.0**; the patterns do not establish that other releases or packages have been published.

## Vocabulary ontology and term IRIs

The [published DKGM Turtle artifact](https://github.com/pedropaulofb/ontouml-directkg/blob/main/vocabulary/latest/dkgm-vocabulary.ttl) declares the following:

| Kind | IRI | Meaning |
| --- | --- | --- |
| Ontology identity | `https://w3id.org/directkg/vocab` | Current DKGM ontology |
| `owl:versionIRI` | `https://w3id.org/directkg/vocab/0.1.0` | Published version 0.1.0 |
| RDF term namespace | `https://w3id.org/directkg/vocab#` | Prefix for the generic property IRIs |

| Term | Full RDF term IRI |
| --- | --- |
| `dkgm:memberOf` | `https://w3id.org/directkg/vocab#memberOf` |
| `dkgm:subCollectionOf` | `https://w3id.org/directkg/vocab#subCollectionOf` |
| `dkgm:subQuantityOf` | `https://w3id.org/directkg/vocab#subQuantityOf` |
| `dkgm:componentOf` | `https://w3id.org/directkg/vocab#componentOf` |

The term IRIs are **not additional path rewrite rules**: their `#` fragments identify RDF properties. The versioned ontology IRI is not a versioned term namespace. The HTML and Turtle redirect targets are **documents describing or representing** the ontology, not alternative IRIs to substitute for the ontology or its terms in RDF.

**Unresolved converter-import decision:** The vocabulary artifact declares the concrete W3ID ontology IRI, but the [accepted mereology mapping](../mapping/mereology.md#import-and-vocabulary-identity) still denotes the converter's mandatory stable import target by symbolic `U`. The normative specification has **not selected its concrete value**. This page documents the published artifact and registered routes; it does not select the IRI to be emitted by a future converter.

## HTTP resolution and content negotiation

The W3ID service applies the registered Apache rewrite rules in order. Matching rules marked `[L]` stop further processing for that pass.

- **302 Found** is used for project navigation and direct representation redirects (such as `/vocab/ttl`).
- **303 See Other** is used for ontology IRIs, pointing the requester to an HTML or Turtle document while leaving the ontology's identity distinct from the document URL.

For the current ontology IRI, the configured resolution is:

```text
https://w3id.org/directkg/vocab
               |
               v
         W3ID .htaccess
               |
     Does Accept contain "text/turtle"?
          /              \
        yes               no
         |                 |
       303               303
         |                 |
         v                 v
SITE/vocabulary/latest/   SITE/vocabulary/latest/
dkgm-vocabulary.ttl       index.html
```

`SITE` is the destination base defined above. Versioned ontology IRIs use equivalent rules pointing to the corresponding versioned files. This diagram illustrates **configured behavior**, not observed HTTP responses.

| `Accept` header | Configured `/vocab` redirect |
| --- | --- |
| `text/turtle` | Turtle, HTTP 303 |
| `text/html` | HTML, HTTP 303 |
| Absent, `*/*`, or `application/ld+json` | HTML, HTTP 303 |
| `text/turtle;q=0` | Turtle, HTTP 303 (literal substring still matches) |

The actual condition checks whether the `Accept` header **contains `text/turtle`**, case-insensitively; it does not rank HTTP quality factors. No JSON-LD or RDF/XML target is configured. Explicit `/vocab/ttl` and `/vocab/X.Y.Z/ttl` routes select Turtle regardless of `Accept`.

## URL patterns and edge cases

- **Numeric versions:** The patterns accept three dot-separated nonnegative integer components, without leading zeroes in multi-digit components. They do not cover prerelease labels or extra components.
- **Trailing slash:** Named paths accept one optional terminal `/`. The namespace root rule matches `/`; a slashless namespace directory request may undergo separate server-level directory normalization.
- **Paths and subpaths:** Rules are anchored to their defined paths, with no catch-all for arbitrary suffixes (such as `/vocab/0.1.0/other`).
- **Query strings:** No DirectKG rule examines query parameters. Apache would normally carry an incoming query string into these destinations because no substitution specifies a new query string. This is a configuration interpretation, not a verified runtime claim.
- **Fragments:** HTTP requests do not transmit fragments such as `#memberOf`; the redirect rules cannot match them. A corresponding HTML anchor is not guaranteed by the URL rule.
- **Unusual `Accept` values:** The substring match also selects Turtle for `text/turtle;q=0` and mixed headers containing `text/turtle`, regardless of preference weights.
- **Publication:** Registered routes may point to unpublished package distributions, GitHub releases, or vocabulary versions. A matching rule does not establish destination availability.

## Practical examples

These commands illustrate how to **inspect or follow** the registered routes. They do not represent tested responses; actual `Location`, `Content-Type`, and final status depend on the running services.

Inspect the configured current Turtle negotiation:

```bash
curl -I -H "Accept: text/turtle" https://w3id.org/directkg/vocab
```

Inspect the default HTML choice:

```bash
curl -I -H "Accept: text/html" https://w3id.org/directkg/vocab
```

Follow the explicit Turtle representation endpoint:

```bash
curl -L https://w3id.org/directkg/vocab/ttl
```

Inspect the published 0.1.0 version ontology's Turtle negotiation:

```bash
curl -I -H "Accept: text/turtle" https://w3id.org/directkg/vocab/0.1.0
```

Reference vocabulary terms using their persistent namespace, **not** a redirected Turtle or HTML document URL:

```turtle
@prefix dkgm: <https://w3id.org/directkg/vocab#> .
# dkgm:memberOf expands to https://w3id.org/directkg/vocab#memberOf
```

The ontology IRI `https://w3id.org/directkg/vocab`, version IRI `https://w3id.org/directkg/vocab/0.1.0`, and representation route `https://w3id.org/directkg/vocab/ttl` are distinct. This is an illustration of the **published vocabulary**, not a finalized converter import example.

## Authority and maintenance

The registered rules are maintained in [`perma-id/w3id.org/ids/directkg/.htaccess`](https://github.com/perma-id/w3id.org/blob/master/ids/directkg/.htaccess) ([raw source](https://raw.githubusercontent.com/perma-id/w3id.org/refs/heads/master/ids/directkg/.htaccess)). The [upstream namespace README](https://github.com/perma-id/w3id.org/blob/master/ids/directkg/README.md) describes administration.

The external `.htaccess` is the **technical authority** for mappings, conditions, status codes, and destination URLs; this page is their user-facing explanation. Destination URLs can change without changing the registered PIDs. Recheck the upstream file when updating the table, and distinguish registered behavior from verified live HTTP availability.

The [vocabulary publication process](https://github.com/pedropaulofb/ontouml-directkg/blob/main/vocabulary/README.md) governs creation of versioned Turtle and HTML artifacts. Pattern-based redirects do not publish those artifacts by themselves.
