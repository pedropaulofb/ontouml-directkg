# Python API

These signatures, fields and available docstrings are generated from the public objects exported by `ontouml_directkg`. They describe the development implementation, not a certification that every accepted transformation rule is implemented. The inspected source revision is [`8dcd8741b5bc9ec142a66b5803a4a9dd7eee8504`](https://github.com/pedropaulofb/ontouml-directkg/tree/8dcd8741b5bc9ec142a66b5803a4a9dd7eee8504/src/ontouml_directkg).

Start with the [Python guide](../../guides/python.md) for verified usage and failure handling. [Controls](../controls.md) owns accepted behavior and defaults; [Diagnostics and recovery](../diagnostics.md) owns outcomes and diagnostic policies. Conversion requires a concrete source file. Unresolved implementation branches may raise exceptions internally (such as `NotImplementedError` development guards). Within `convert()`'s protected transformation boundary—from source reading through `ConversionResult` construction—policy-driven aborts and reportable unexpected internal failures (including caught internal guards) return an `aborted` `ConversionResult` with `INTERNAL_TRANSFORMATION_FAILURE` where an unexpected internal failure occurs, rather than propagating those internal exceptions to callers. Pre-conversion configuration rejection and explicit serialization, artifact delivery, and diagnostics export follow their [separate failure contracts](#exceptions); the specification prescribes no particular Python exception or result classes.

## Conversion

::: ontouml_directkg.convert
    options:
      heading_level: 3
      show_root_heading: true
      show_source: false

## Result and explicit exports

Obtain the result from `convert`. Ontology serialization, file delivery and diagnostics export are explicit operations. Inspect the transformation outcome separately from delivery success; see [Exceptions](#exceptions) and the [Python guide](../../guides/python.md#diagnostics-and-aborts) for the implemented failure boundaries.

::: ontouml_directkg.ConversionResult
    options:
      heading_level: 3
      show_root_heading: true
      show_source: false
      show_if_no_docstring: true
      members:
        - ontology
        - outcome
        - diagnostics
        - provenance
        - provenance_mode
        - to_turtle
        - to_provenance_turtle
        - deliver
        - export_diagnostics

## Diagnostics and source locations

::: ontouml_directkg.Diagnostic
    options:
      heading_level: 3
      show_root_heading: true
      show_source: false
      show_if_no_docstring: true
      members:
        - severity
        - code
        - message
        - effect
        - sources
        - generated_iri

::: ontouml_directkg.SourceLocation
    options:
      heading_level: 3
      show_root_heading: true
      show_source: false
      show_if_no_docstring: true
      members:
        - path
        - identifier
        - element_type

## Delivery results

::: ontouml_directkg.DeliveryResult
    options:
      heading_level: 3
      show_root_heading: true
      show_source: false
      show_if_no_docstring: true
      members:
        - conversion
        - ontology_path
        - provenance_path
        - failures
        - successful

::: ontouml_directkg.DeliveryFailure
    options:
      heading_level: 3
      show_root_heading: true
      show_source: false
      show_if_no_docstring: true
      members:
        - kind
        - destination
        - cause
        - old_file_not_updated
        - reason

## Exceptions

The accepted specification (`§15`, `DK-DIAG-04–05`, `DK-GEN-10`) requires programmatic signaling for pre-conversion rejection, direct serialization errors, and diagnostics-export failures without prescribing particular Python exception or result classes. At the inspected source revision (`8dcd8741b5bc9ec142a66b5803a4a9dd7eee8504`), the public API separates four failure boundaries:

- **Pre-conversion configuration rejection (`convert()`):** Before conversion starts, validation of transformation controls and `source` (`str | os.PathLike` via `os.fspath`) raises `ConfigurationError` (a `ValueError` subclass), producing no `ConversionResult`, transformation outcome, diagnostics report, or output files.
- **Transformation aborts (`convert()`):** Once conversion starts through `ConversionResult` construction, policy-driven aborts (including `UNPROCESSABLE_DOCUMENT`, `DUPLICATE_SOURCE_ID`, input- or stereotype-policy rejections, and conversion-time `REQUIRED_PROVENANCE`) and reportable unexpected internal failures (including internal `NotImplementedError` development guards and `RuntimeError` guards for `DK-IRI-07` ID-candidate collisions) are caught inside `convert()` and returned as `ConversionResult` with `outcome="aborted"`, `ontology=None`, `provenance=None`, and all produced diagnostics (adding `INTERNAL_TRANSFORMATION_FAILURE` for unexpected internal failures). Internal transformation exceptions are not propagated out of `convert()`.
- **Direct programmatic serialization (`to_turtle()`, `to_provenance_turtle()`):** Writes no files; raises `ValueError` when no eligible ontology or separate provenance graph is available, and propagates serialization exceptions without mutating `diagnostics`, `outcome`, or `ontology`.
- **Explicit artifact delivery (`deliver()`) and diagnostics export (`export_diagnostics()`):** For valid path destinations, `deliver()` returns `DeliveryResult` rather than raising delivery failures as exceptions: already-`aborted` results write no files and add no diagnostics; post-conversion `sidecar` output-provenance construction failures before writing abort the result (`REQUIRED_PROVENANCE`, `outcome="aborted"`, `ontology=None`, `provenance=None`) with no files written; and post-conversion ontology-file or post-ontology sidecar delivery failures record `ONTOLOGY_DELIVERY` or `SIDECAR_DELIVERY` in `result.diagnostics` and `DeliveryFailure` in `DeliveryResult.failures` while preserving the established transformation outcome. `export_diagnostics()` raises `DiagnosticsExportError` (an `OSError` subclass) on `OSError` write failures and propagates invalid-report `ValueError` or JSON-serialization errors directly, leaving `result`, `diagnostics`, `outcome`, and `ontology` unchanged.

::: ontouml_directkg.ConfigurationError
    options:
      heading_level: 3
      show_root_heading: true
      show_source: false
      members: []

::: ontouml_directkg.DiagnosticsExportError
    options:
      heading_level: 3
      show_root_heading: true
      show_source: false
      members: []

---

Governing rules: DOC-FRAMEWORK, §§2.3, 3.2–3.3, and 15; DK-GEN-10; DK-DIAG-04–05; approved documentation structure P22 and §9.2; baseline consolidated: **2026-11-26**; repository commit: `3156ff81731a7ee5b4720245380bc2ccb72dcaf1`; source: [`documentation/specification/transformation-specification.md`](https://github.com/pedropaulofb/ontouml-directkg/blob/3156ff81731a7ee5b4720245380bc2ccb72dcaf1/documentation/specification/transformation-specification.md). Concrete API names and representations above come from inspected source revision `8dcd8741b5bc9ec142a66b5803a4a9dd7eee8504`, not additional normative requirements.
