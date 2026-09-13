# End the Architect session: update the open-design-issues state

## Task and evidence

Produce the updated open-design-issues document for the next OntoUML DirectKG Architect conversation. Use the current specification loaded in this session, the prior open-issues document, and accessible discussion and explicit decisions from this session. Follow the Architect operating protocol already established here.

Read and reconcile the actual sources; do not rely solely on a summary or memory. If essential source material or acceptance evidence is inaccessible, request it or clearly identify the output as incomplete. Do not claim a complete handoff by reconstructing missing state.

## Reconcile unresolved state

- Account for every previously open issue. Remove fully resolved questions, narrow partially resolved ones to the remaining decision, and preserve unchanged issues that remain relevant even if not discussed this session.
- Incorporate genuine new in-scope specification gaps identified during the session. Do not invent optional features, ordinary implementation tasks, or speculative backlog items.
- Update dependencies, constraints, alternatives, and evidence to reflect explicit accepted decisions. Do not reopen a resolved question because its transfer or documentation is pending; that is a separate integration matter.
- Distinguish open, partially resolved, blocked, and explicitly deferred unresolved issues where useful. An accepted decision that something is outside project scope belongs in the specification, not in the unresolved backlog unless a separate in-scope question remains.
- Preserve existing issue IDs. Add unique IDs only when useful, and update cross-references without reusing an old ID for a different question.

## Required document content

Create a self-contained Markdown state document titled `OntoUML DirectKG — Open Design Issues`, organized by topic rather than chronology.

Briefly identify its non-normative purpose and the supplied baseline against which it was reconciled, using only known document identifiers or revision information. It must be used together with the current Documenter-maintained specification. It is not a specification and must not be supplied as required input to the Documenter.

For each unresolved issue, include only the fields necessary to resume accurately:

- issue identifier/title and exact decision still needed;
- current unresolved status and essential context, including any already-resolved boundary;
- why it matters and relevant in-scope constraints;
- minimal references to accepted baseline rules or accepted decision messages needed to understand it;
- dependencies on other unresolved issues;
- alternatives still under consideration and known trade-offs;
- any unaccepted recommendation, explicitly labeled as such;
- unanswered research questions, evidence gaps, and relevant source URLs, file paths, or versions already inspected;
- material edge cases or blockers and the next investigation/discussion needed.

Include a compact dependency order if useful. If no known issues remain, say that no unresolved issues are recorded in the available state; do not claim this proves the entire specification is complete.

Do not duplicate accepted decisions as project state, add an accepted-decisions section, or reproduce conversational history. Reference an accepted rule only as much as needed to explain an unresolved issue. Preserve useful evidence and reasoning, not the dialogue that produced them. Do not resolve issues while preparing this handoff.

## Prevent loss of accepted decisions between sessions

Check the accepted decision transfers produced during this session. Integration is confirmed only when I have supplied that confirmation or a current specification visibly contains the decision. Never assume a generated message was transferred.

Outside the open-issues document, identify any accepted decision references whose integration is pending or unconfirmed. Reissue any such message not yet provided in complete transferable form using the operating protocol's decision-message format. Keep it separate from the open-issues state. Do not create a third persistent project-state document or relabel accepted decisions as open issues.

State that the next Architect session must pair this handoff with the specification consolidated after those transfers. If integration reveals a substantive conflict, its unresolved clarification belongs back in the Architect workflow; do not solve it here without my decision.

## Output and check

Create the actual downloadable file `ontouml-directkg-open-design-issues.md` if file creation is available; otherwise provide the complete Markdown in a clearly delimited copyable block. Do not claim a file exists unless it was created.

Before delivery, verify that all known remaining issues and dependencies are preserved, resolved questions are removed or narrowed, alternatives remain non-normative, minimal accepted-rule references are accurate, and no unavailable information was invented. Provide the file/link or full text with a brief reconciliation status and any separate transfer/access limitations, then stop.
