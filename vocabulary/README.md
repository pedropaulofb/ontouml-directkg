# DirectKG mereology vocabulary publication

The **normative** source for each release is the immutable Turtle file
`vocabulary/versioned/dkgm-vocabulary-vX.Y.Z.ttl`. Versioned PyLODE HTML
snapshots are stored beside their sources. No version directories are used.

The highest numeric `X.Y.Z` release (not the most recently edited filename)
is promoted automatically to:

- `vocabulary/latest/dkgm-vocabulary.ttl` — exact copy of that release's Turtle.
- `vocabulary/latest/index.html` — exact copy of that release's PyLODE documentation.

The existing `0.1.0` source and ontology version identifiers are preserved
without changes. The current artifact uses
`https://w3id.org/directkg/vocab` and
`https://w3id.org/directkg/vocab/0.1.0`; relocation does not settle the
separate specification decision about the converter's stable import target.

## Publishing a subsequent version

Add a new `dkgm-vocabulary-vX.Y.Z.ttl` file to `vocabulary/versioned/`.
Update its version-related RDF metadata consistently; retain all earlier
Turtle and HTML snapshots unchanged. The existing graph's semantic evolution
requires its own accepted modeling decisions; this pipeline only publishes it.

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
