# DirectKG mereology vocabulary publication

The **normative** source for each release is the immutable Turtle file
`vocabulary/versioned/dkgm-vocabulary-vX.Y.Z.ttl`. Versioned PyLODE HTML
snapshots are stored beside their sources. No version directories are used.

The highest numeric `X.Y.Z` release (not the most recently edited filename)
is promoted automatically to:

- `vocabulary/latest/dkgm-vocabulary.ttl` — exact copy of that release's Turtle.
- `vocabulary/latest/index.html` — exact copy of that release's PyLODE documentation.

The project-owner decision of **2026-10-24** authorizes a one-time pre-release
identity correction of the existing `0.1.0` and `0.1.1` Turtle/HTML files in place.
Their version numbers, metadata and logical axioms are retained; no new release
is created. The canonical ontology and converter import IRI is `https://w3id.org/directkg/vocab/dkgm`,
with term namespace `https://w3id.org/directkg/vocab/dkgm#` and preferred prefix `dkgm`.
Version IRIs are `https://w3id.org/directkg/vocab/dkgm/0.1.0` and `https://w3id.org/directkg/vocab/dkgm/0.1.1`.
`latest/` remains an exact copy of the highest release, `0.1.1`. No legacy
vocabulary or term aliases are retained. Source changes do not deploy them.

The existing `0.1.1` patch increment corrected the documentation and added descriptive discovery
metadata, scope notes and examples. No terms, definitions or logical axioms
change. Although SemVer permits flexibility below 1.0.0, a minor increment is
unnecessary for this correction of the existing vocabulary's presentation.

## Read-only source validation

Use the same production source validator without generating HTML, synchronizing
`latest/`, committing files, or publishing anything:

```bash
python vocabulary/scripts/build.py --check-only
```

By default this validates every versioned Turtle source, using the existing
numeric release discovery. To check selected versioned source files instead:

```bash
python vocabulary/scripts/build.py --check-only vocabulary/versioned/dkgm-vocabulary-v0.1.0.ttl
```

Validation failures return a nonzero status and identify the file, resource,
predicate, expected condition, and observed problem. `--base SHA` retains the
existing optional immutability comparison; source validation does not establish
a new comparison baseline or change publication workflows.

The source contract checks ontology/version identity, the hash namespace and
preferred prefix, the four object properties, and the three ordered binary
chains required by DK-GEN-04. RDF lists are checked structurally, including
branching, cycles and termination. Other logical axioms, including incoming
alignments and source-specific properties, are rejected by the current contract.
Equivalent serialization order, prefix aliases, list-node identifiers, repeated
identical statements and redundant identical chains do not change the contract.
This is source validation, not a general OWL equivalence or consistency reasoner.

Required ontology metadata is title, description, one or more creator IRIs, the
existing CC BY 4.0 license IRI, creation/modification date-times, namespace hints
and version fields. Identity fields, namespace hints, license and date-times are
single-valued; textual metadata may have multiple values. Each property needs a
nonempty English label and definition. Additional textual annotations and
languages are allowed under the existing descriptive predicates; language tags
are checked against RFC 5646 syntax without a network registry lookup.

Date-time checks preserve original literal spelling rather than allowing parser
normalization to hide invalid syntax. Chronology accounts for timezone offsets
and fractional seconds. Two timezone-less values are compared as local values;
mixed timezone presence must establish an unambiguous order across the possible
14-hour offset range. No execution-machine timezone or build timestamp is added.

`SOURCE_CONTRACTS` in `scripts/build.py` explicitly registers releases `0.1.0`
and `0.1.1`, sharing the same property/chain inventory. The latter also requires
term `rdfs:isDefinedBy`, verified project links, focused English scope notes and
examples, and `owl:priorVersion` derived from the actual preceding release.
An unregistered release fails with a request for a reviewed contract, rather
than silently inheriting rules that might be wrong for it. Future accepted
evolution must preserve the historical registration and deliberately add the
applicable contract. The historical release does not acquire new metadata
requirements. Source validation does not inspect HTML presentation or repair
generated representations; known 0.1.0 HTML limitations do not make it fail.

## Explicit source preparation

Edit a separate Turtle draft containing the approved annotations and an accurate
`dcterms:modified` date-time. Retain the original creation date and creator/license
metadata. Register the reviewed release contract, then explicitly select its
patch or minor increment:

```bash
python vocabulary/scripts/build.py --prepare-release patch --draft /path/to/edited-draft.ttl
```

Preparation validates existing sources, calculates the next version numerically,
and derives the immediate predecessor's version IRI from discovered release files.
It sets the draft's version fields and `owl:priorVersion` in a **new** versioned
Turtle file. A draft may identify either the preceding or prepared version. An
unchanged predecessor inherited from a copy of the preceding release is advanced
automatically; conflicting or ambiguous values are rejected. Existing Turtle or
HTML targets are never overwritten, and failed source validation creates no
release. The input draft, historical files, HTML and `latest/` stay unchanged.
Ordinary builds and `--check-only` never maintain or repair Turtle metadata.

This is a local preparation operation, not a GitHub release or deployment.
For `0.1.1`, it derives `https://w3id.org/directkg/vocab/dkgm/0.1.0` as predecessor.

## Generated documentation

The existing PyLODE `ontpub` profile is retained. Focused postprocessing reads
definitions, independent comments, scope notes, examples and ordered property
chains from the source graph. Chain expressions link both operands and their
conclusion to term anchors. Creator names are read from the existing creator
labels and shown beside their identifiers. PyLODE's JSON-LD remains intact.

The existing transparent PNG logo and SVG favicon under `branding/` are embedded
unchanged as data URLs, making the standalone HTML independent of asset paths.
Only the logo's proportional size is styled; the PyLODE layout is retained.
Navigation uses the `/vocab/dkgm` routes prepared in the W3ID migration branch
(`pedropaulofb/w3id.org`, `feat/directkg-dkgm-pid`), pending upstream integration:
project docs, repository, ontology, current Turtle, and this version's IRI/Turtle.
The Turtle alternate link always identifies the snapshot's own version, including
when the same HTML is copied to `latest/`. Version navigation is generated from
discovered releases up to that snapshot's version; immutable pages do not acquire
future entries.

The resource links use locally styled text pills with wrapping and a visible
keyboard-focus outline. The release links are labeled **Available versions**.
Postprocessing removes only PyLODE's orphaned comma-only separator spans directly
under the content container, preserving actual cardinality annotations and
separators inside property tables.

New-contract HTML is checked against its source graph for term sections, exact
annotation text, chains and references, creator attribution, branding, navigation,
Turtle alternate links, JSON-LD presence, unique anchors and local resources.
Historical `0.1.0` HTML retains its earlier presentation contract; all releases
check the exact ontology/property identities and embedded JSON-LD ontology IRI. Builds check that
`latest/` representations equal the highest versioned artifacts byte for byte.

## Building representations locally

Run with Python 3.12:

```bash
python -m pip install -r vocabulary/scripts/requirements.txt
python vocabulary/scripts/build.py
python -m unittest discover -s vocabulary/scripts/tests -v
```

The build validates metadata and release immutability (with `--base SHA`),
generates missing HTML snapshots with PyLODE's `ontpub` profile, then
synchronizes `latest/`. It does not overwrite previously generated
versioned HTML. The GitHub Actions workflow validates on pull requests and
automatically commits generated representations on pushes to `main` or
manual runs on `main`, after a read-only publication gate. It then calls `.github/workflows/docs.yml` with the prepared
commit SHA. That workflow builds the Zensical documentation and includes
both `vocabulary/latest/` and `vocabulary/versioned/` under the site's
`vocabulary/` path in a single GitHub Pages artifact. The documentation
homepage and vocabulary pages therefore share one publisher rather than
replacing each other's site. To serve the site, configure **Settings →
Pages → Build and deployment → GitHub Actions**. Workflow configuration
alone is not evidence of successful deployment.

## Publication gates and historical integrity

Generation and publication use the same source and HTML contracts. Publication
adds a required Git integrity gate; the ordinary `--check-only` source interface
remains available without Git history or HTML checks.

```bash
git fetch --no-tags origin refs/heads/main:refs/remotes/origin/main
python vocabulary/scripts/build.py --check-only --publication
```

The gate requires a complete checkout and the canonical DirectKG origin. Its
independent historical floor is reviewed main commit
`957a83454a3bcc9fcf73388fb2d2e2bb467a4561`, which contains the established 0.1.0
Turtle and HTML. Fetched main must retain that commit on its first-parent history,
and the candidate must contain fetched main. Later main snapshots extend the
protected inventory: each versioned path is compared with its earliest bytes in
that accepted history, including paths subsequently removed. The approved exceptions
are narrowly pinned in `scripts/build.py`. `IDENTIFIER_CORRECTION` contains four
path-specific SHA-256 before/after pairs for the authorized 0.1.0/0.1.1 identity correction.
`PRESENTATION_CORRECTION` adds one exact 0.1.1 HTML before/after pair for the
owner-approved 2026-10-25 navigation and stray-comma fix. These corrections are
applied in order, so older baselines require the final approved bytes; obsolete
intermediate HTML cannot be restored. All other comparisons require exact
equality. No runtime flag or caller-selected ref grants a general overwrite
permission. Other paths and later changes retain the existing byte protections,
even if a particular deployment failed.

When the candidate is itself main's tip, its strict prior history supplies the
comparison, allowing genuinely new artifacts at the tip. The pinned historical
floor remains protected, with only the exact corrections described above. The gate also compares the complete source
artifact inventory and bytes with the candidate's committed Git objects; this
separate cleanliness check does not serve as historical evidence. Missing refs,
shallow history, an untrusted origin, a missing anchor, stale candidates, changed
historical bytes and removed historical files all fail rather than skipping the
integrity check. No push-event predecessor, new state branch, publication ledger,
release list or additional write permission is required. Workflows fetch main
immediately before using this evidence; the read-only gate itself does not fetch
or write Git state.

For generation in publication workflows, `build.py --publication` applies the
same historical gate before generating missing representations. Preparation then
commits generated files locally, runs `--check-only --publication`, and only
pushes the prepared commit if that check succeeds. Existing branch protections
and the main-only promotion condition remain in place.

Both reusable and manual documentation runs fetch full trusted history, build
the Zensical site, copy the vocabulary artifacts, then run:

```bash
python vocabulary/scripts/build.py --check-only --publication --site site
```

This validates the actual staged RDF, HTML, version references, chains, internal
links, fragments and embedded assets, including links relative to `latest/`.
It checks required artifact pairs and inventories, latest/versioned equality,
and exact source-to-site bytes. It neither repairs stale copies nor regenerates
HTML. Historical 0.1.0 keeps its earlier presentation contract plus the shared
identity checks. Any required
failure stops Pages artifact upload. No external-link availability test is part
of this deterministic gate. GitHub Pages remains the single combined publisher.

## Coordinated W3ID validation

The W3ID source changes are in the existing fork, on `feat/directkg-dkgm-pid`,
based on upstream `master`. Only `ids/directkg/.htaccess` changes. The former
`/vocab` routes are withdrawn under the explicit pre-release decision; no aliases
or replacement resource are introduced. Upstream acceptance remains a separate
review step. Project navigation routes and representation targets are unchanged.

Validate all required paths, optional slashes, negotiation defaults, release
patterns, retired paths and unrelated project rules against that actual file:

```bash
python vocabulary/scripts/tests/check_w3id_routes.py ../w3id.org/ids/directkg/.htaccess
# Add --baseline /path/to/upstream.htaccess to compare unchanged project rules.
```

This is a static rule check, not a live HTTP test. Run the W3ID repository checker
and Apache checks separately using its contribution instructions.

## Verification after an authorized deployment

The documentation workflow's read-only `verify-publication` job runs only when
the existing main-only Pages deployment step actually succeeded. It checks out
the exact deployed source SHA and invokes:

```bash
python vocabulary/scripts/verify_deployment.py
```

Do not use this command to imply that a feature-branch version has been deployed.
It performs no deployment, commits or artifact changes. The verifier first uses
the shared local artifact contracts, then checks W3ID current/version
IRIs with HTML and Turtle Accept headers, plus their explicit `/docs` and `/ttl`
routes. Expected 303/302 locations follow the coordinated `/vocab/dkgm` W3ID rules;
available versions come from release files. Ordinary subsequent HTTPS redirects
are followed with cycle/redirect bounds, and final decoded HTTP bytes must equal
the intended artifacts. HTML media types are checked; Turtle also permits normal
static-file fallback media types because byte equality and validated source RDF
already establish representation identity.

HTTP requests have 5-second connect and 15-second read timeouts. Each failed check
gets at most three attempts with 1- and 2-second delays, except deterministic
redirect errors, which fail immediately. Successfully verified target responses
are reused for equivalent routes. Network errors, HTTP 408/429 and server errors
are reported as external-infrastructure uncertainty (exit 2). Unavailable
representations, incorrect redirects or content mismatches fail postdeployment
verification (exit 1); invalid local expected artifacts fail input validation
(exit 3). These are separate from deployment-action failures and do not label a
temporary W3ID or Pages outage as an RDF/OWL semantic error. Verification does not
roll back a completed deployment. Unit tests use mocked HTTP responses and do
not establish that any real deployment has passed verification.

The converter itself is not implemented yet. The vocabulary's RDF license is
CC BY 4.0; the repository's overall software license is Apache 2.0.
