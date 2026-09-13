# End the Documenter session: produce the consolidated specification

## Task and authoritative inputs

Produce the complete current OntoUML DirectKG specification that will serve as the normative baseline for future Architect and Documenter conversations. Follow the Documenter protocol established in this conversation.

Use the supplied baseline, the current working specification, and every explicitly accepted decision message, correction, and supersession supplied for integration during this session. No open-design-issues document is expected or required. Do not infer a backlog from its absence or import decisions from other conversations or external sources.

Inspect the actual available material. If the baseline or necessary accepted messages are unavailable or truncated, request the missing text before claiming a complete consolidation. An assistant summary is not a substitute for missing normative wording.

## Consolidation requirements

- Preserve all still-valid baseline content and incorporate all accepted decisions that can be faithfully integrated. Account for every accepted message as integrated, already integrated, explicitly superseded, or pending because of a stated integration problem.
- Organize by the software's scope, concepts, and behavior, not by conversation chronology. Maintain one coherent specification, not appended decision messages or a historical registry.
- Integrate additions and clarifications in the appropriate sections. Replace superseded wording only where replacement is explicitly accepted, and propagate changes through affected definitions, tables, examples, and cross-references.
- Preserve exact normative meaning, including scope, conditions, defaults, exceptions, unsupported cases, and requirement strength. Do not invent rules, rationale, version numbers, architecture, or answers to unspecified questions merely to make the document appear implementation-ready.
- Consolidate duplicate wording without losing unique requirements. Preserve consistent terminology and useful stable IDs; make each rule's primary location clear and cross-reference it where needed.
- Keep supported rationale and faithful examples clearly non-normative. Retain historical or rejected-alternative context only when relevant to understanding the current specification itself.
- Adapt the structure to the accepted content. Do not create empty feature sections or prescribed behavior to fill a template.

The specification must stand alone without needing the Architect's open issues, this conversation, or separate accepted decision messages to understand its integrated rules. Preserve accepted scope boundaries, including deliberately unsupported or deferred functionality. Do not include an unresolved-questions appendix or mix non-normative design questions into the accepted baseline.

## Integration problems: separate return to the Architect

Do not silently reconcile a genuine contradiction or choose an interpretation that requires a substantive design decision. Keep any affected unintegrated message separate from normative text and identify the exact issue to return to the Architect.

For each pending matter, provide a separately delimited note outside the specification containing the accepted message/reference and exact relevant wording, affected baseline passages, integration status, why faithful integration is blocked, and the clarification needed. Preserve the full accepted message when necessary to resume without this conversation. Do not generate a broad open-issues inventory or propose an architectural answer.

Uncontested, independent integrations may be consolidated while a matter is pending, but the result must then be labeled an incomplete consolidation, with pending matters explicitly disclosed outside it. Do not label it the fully updated replacement baseline. If the existing baseline itself contains an unresolved contradiction, do not arbitrarily delete or choose a rule to manufacture consistency; request an explicitly accepted resolution before issuing a baseline certified as coherent. A draft, if provided, must be clearly identified as such.

## Final verification and output

Before finalizing, compare the complete output with the baseline and accepted inputs. Verify coverage of still-valid requirements, authorized supersession, consistent terminology and references, preservation of modal strength and exceptions, and the separation of normative rules from explanations. Check that no accepted input was silently lost and no unresolved matter was silently resolved. Do not claim verification beyond the sources actually accessible.

When reconciliation succeeds, create the actual downloadable Markdown file `ontouml-directkg-current-specification.md` if file creation is available. Otherwise provide the complete Markdown in a clearly delimited copyable block. Deliver the full document, not a diff, excerpt, or summary; do not silently truncate it. If output limits prevent full delivery, explain the limitation and provide a complete multipart delivery with explicit assembly order.

Return a brief consolidation status and the download link or complete text. Add separate Architect-return notes only if needed. Confirm suitability as the next baseline only when the document is complete and internally consistent within the accepted scope; this does not mean all future design questions have been resolved. Do not continue architectural design.
