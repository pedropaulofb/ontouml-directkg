# Python API

These signatures, fields and available docstrings are generated from the public objects exported by `ontouml_directkg`. They describe the development implementation, not a certification that every accepted transformation rule is implemented. The inspected source revision is [`25bf7b2259331d0c439fe0f79f826bae0218b8f7`](https://github.com/pedropaulofb/ontouml-directkg/tree/25bf7b2259331d0c439fe0f79f826bae0218b8f7/src/ontouml_directkg).

Start with the [Python guide](../../guides/python.md) for a verified conversion and result handling. [Controls](../controls.md) owns accepted behavior and defaults; [Diagnostics and recovery](../diagnostics.md) owns outcomes and diagnostic policies. Conversion requires a concrete source file. Unresolved development branches can raise `NotImplementedError`.

## Conversion

::: ontouml_directkg.convert
    options:
      heading_level: 3
      show_root_heading: true
      show_source: false

## Result and explicit exports

Obtain the result from `convert`. Ontology serialization, file delivery and diagnostics export are explicit operations. Inspect the transformation outcome separately from delivery success.

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

Governing rules: DOC-FRAMEWORK, §§2.3 and 15; approved documentation structure P22 and §9.2; baseline consolidated: **2026-10-29**; repository commit: `25bf7b2259331d0c439fe0f79f826bae0218b8f7`; source: [`documentation/specification/transformation-specification.md`](https://github.com/pedropaulofb/ontouml-directkg/blob/25bf7b2259331d0c439fe0f79f826bae0218b8f7/documentation/specification/transformation-specification.md). Concrete API names and representations above come from source, not additional normative requirements.
