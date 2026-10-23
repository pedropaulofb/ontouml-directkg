# DirectKG mereology vocabulary publication

The **normative** source for each release is the immutable Turtle file
`vocabulary/versioned/dkgm-vocabulary-vX.Y.Z.ttl`. Versioned PyLODE HTML
snapshots are stored beside their sources. No version directories are used.

The highest numeric `X.Y.Z` release (not the most recently edited filename)
is promoted automatically to:

- `vocabulary/latest/dkgm-vocabulary.ttl` — exact copy of that release's Turtle.
- `vocabulary/latest/index.html` — exact copy of that release's PyLODE documentation.

The existing `0.1.0` Turtle and HTML are preserved without changes. This branch
prepares `0.1.1` and updates its local `latest/` copies; it does not deploy them.
The ontology IRI remains `https://w3id.org/directkg/vocab`, with term namespace
`https://w3id.org/directkg/vocab#` and new version IRI
`https://w3id.org/directkg/vocab/0.1.1`. This does not settle the separate
specification decision about the converter's stable import target.

The patch increment corrects the documentation and adds descriptive discovery
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
For `0.1.1`, it derives `https://w3id.org/directkg/vocab/0.1.0` as predecessor.

## Generated documentation

The existing PyLODE `ontpub` profile is retained. Focused postprocessing reads
definitions, independent comments, scope notes, examples and ordered property
chains from the source graph. Chain expressions link both operands and their
conclusion to term anchors. Creator names are read from the existing creator
labels and shown beside their identifiers. PyLODE's JSON-LD remains intact.

The existing transparent PNG logo and SVG favicon under `branding/` are embedded
unchanged as data URLs, making the standalone HTML independent of asset paths.
Only the logo's proportional size is styled; the PyLODE layout is retained.
Navigation uses routes verified against `perma-id/w3id.org/ids/directkg/.htaccess`:
project docs, repository, ontology, current Turtle, and this version's IRI/Turtle.
The Turtle alternate link always identifies the snapshot's own version, including
when the same HTML is copied to `latest/`. Version navigation is generated from
discovered releases up to that snapshot's version; immutable pages do not acquire
future entries.

New-contract HTML is checked against its source graph for term sections, exact
annotation text, chains and references, creator attribution, branding, navigation,
Turtle alternate links, JSON-LD presence, unique anchors and local resources.
Historical `0.1.0` HTML retains its earlier validation contract. Builds check that
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
manual runs. It then calls `.github/workflows/docs.yml` with the prepared
commit SHA. That workflow builds the Zensical documentation and includes
both `vocabulary/latest/` and `vocabulary/versioned/` under the site's
`vocabulary/` path in a single GitHub Pages artifact. The documentation
homepage and vocabulary pages therefore share one publisher rather than
replacing each other's site. To serve the site, configure **Settings →
Pages → Build and deployment → GitHub Actions**. Workflow configuration
alone is not evidence of successful deployment.

The converter itself is not implemented yet. The vocabulary's RDF license is
CC BY 4.0; the repository's overall software license is Apache 2.0.
