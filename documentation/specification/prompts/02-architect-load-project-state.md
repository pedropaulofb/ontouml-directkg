# Load the current OntoUML DirectKG project state

## Inputs and prerequisites

Use this prompt in the same Architect conversation after the prerequisite ecosystem study. I am supplying both documents in this message:

- [ATTACH CURRENT SPECIFICATION]
- [ATTACH CURRENT OPEN ISSUES]

The actual documents must be accessible here; these placeholders are not their contents. Identify which attachment serves each role and read both completely, including tables, examples, appendices, and qualifications. If an input is missing, unreadable, truncated, or its role is materially unclear, request the necessary material rather than reconstructing it. If the prerequisite study is unavailable in this conversation, say so instead of assuming it happened.

## Source authority

OntoUML DirectKG converts OntoUML models represented as JSON into knowledge graphs and is currently being specified before implementation.

The current specification is the normative baseline for accepted project decisions. The open-design-issues document is a separate, non-normative state document describing unresolved work. Its alternatives, recommendations, assumptions, and examples do not establish requirements.

Interpret each statement according to its stated role: preserve the distinction between requirements, rationale, examples, and explicitly provisional material. Do not promote explanatory or provisional wording into an accepted rule. External technical sources inform reasoning about feasibility and meaning; they do not override accepted DirectKG choices. Do not import project decisions from other conversations, memory, or a repository unless I explicitly supply them as authoritative state.

If an open issue is clearly resolved by an explicit baseline rule, identify the issue as stale and cite that rule. The open-issues document cannot reopen it. If resolution is uncertain or the baseline itself is contradictory, identify the conflict without choosing an unstated interpretation. A document's later date alone does not authorize it to supersede the baseline.

## Study task

Understand the project's accepted scope, goals and non-goals, terminology, inputs and outputs, transformation rules, constraints, exceptions, interfaces, and architecture-related choices to the extent specified. Read these in relation to the unresolved questions, their dependencies, candidate alternatives, known evidence, and partial resolutions.

Use the earlier ecosystem study to interpret technical references while keeping OntoUML facts separate from DirectKG design choices. Inspect referenced passages rather than guessing at missing definitions. Preserve existing section and issue identifiers for later traceability.

Do not answer open questions, recommend designs, modify either document, reopen settled decisions, implement software, or produce a new specification at this stage. Do not create a backlog merely from topics the specification does not mention.

## Response

Briefly identify the two documents and any supplied version/revision information, confirm the extent of your study, and wait for the operating protocol. Surface only genuine contradictions, ambiguities, stale issue entries, or missing evidence that materially affect subsequent work, with precise document references and their implications. Do not hide a material limitation behind an unconditional readiness statement or produce a general project summary.
