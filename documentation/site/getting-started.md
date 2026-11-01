# Getting started

Install the development package and convert the small [classes-and-attributes example](examples/index.md#downloadable-pairs). This path was verified with Python **3.12.14** against repository commit [`25bf7b2259331d0c439fe0f79f826bae0218b8f7`](https://github.com/pedropaulofb/ontouml-directkg/tree/25bf7b2259331d0c439fe0f79f826bae0218b8f7).

## Installation status

The repository declares Python **3.12 or later** and development version **`0.0.0.dev1`**. Use a virtual environment, then run:

```bash
git clone https://github.com/pedropaulofb/ontouml-directkg.git
cd ontouml-directkg
python -m pip install .
ontouml-directkg --version
```

For the inspected revision, the version command prints `0.0.0.dev1`. The repository evolves; check your installed version when reproducing this example. These are source-installation instructions and do not assert that a distribution is published on PyPI. Verification on Python 3.12.14 does not establish execution coverage for every declared Python version.

The development implementation has unresolved branches and partial test bindings. A successful example does not establish complete conformance. See [Contributing](development/contributing.md#verified-development-checks) for the test boundary and [Semantics and limitations](concepts/semantics.md) for the accepted semantic boundaries.

## First conversion

Run this command from the repository root. It uses the complete downloadable JSON input and the illustration's documented configuration:

```bash
ontouml-directkg documentation/site/examples/files/classes-and-attributes.json --output example.ttl --base-iri https://example.org/directkg-example# --iri-strategy id --language pt-BR --provenance none --diagnostics-file example-diagnostics.json
```

The command requires the concrete input file. It writes the ontology as Turtle and explicitly requests a JSON diagnostic report. Provenance is disabled for this example; other conversions default to embedded provenance. The [input contract](reference/input.md) and [control catalog](reference/controls.md) describe the wider accepted scope and defaults.

## Inspecting the result

At the verified revision:

- The conversion completed with exit code `0` and outcome `completed`.
- `example.ttl` contained **20 triples**. All **10 triples** in the downloadable illustrative excerpt were present.
- Two INFO diagnostics reported preservation of explicit `isAbstract: false` declarations through comments. The requested JSON report retained both events.

Inspect `example.ttl` and `example-diagnostics.json` independently. The downloadable `.ttl` remains a **specification illustration**, not a captured complete output: the converter also emits the ontology header and applicable comments omitted from that excerpt. Turtle formatting, prefix spelling and statement order are not fixed.

Use the [CLI guide](guides/cli.md#exit-codes-and-delivery-failures) to interpret other outcomes and delivery failures. For a verified library call, continue with the [Python guide](guides/python.md#conversion-and-configuration); the [generated API reference](reference/api/index.md) describes the actual public objects.

---

Governing rules: §§2.2–2.3, 3.2–3.3, 15; DK-GEN-10; DK-DIAG-04–05; baseline consolidated: **2026-10-29**; repository commit: `25bf7b2259331d0c439fe0f79f826bae0218b8f7`; source: [`documentation/specification/transformation-specification.md`](https://github.com/pedropaulofb/ontouml-directkg/blob/25bf7b2259331d0c439fe0f79f826bae0218b8f7/documentation/specification/transformation-specification.md). Runtime evidence above concerns the same commit and the stated example only.
