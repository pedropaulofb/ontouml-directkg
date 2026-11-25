# DirectKG agent workflow

These are independent initial prompts for separate AI conversations. The project owner selects assignments, accepts design decisions and relays review handoffs. Each role retrieves repository files directly from GitHub; handoffs supply decisions, scope, revisions and review findings, not manually uploaded repository files.

## Active prompts

| Role | Prompt |
| --- | --- |
| Adviser | [adviser/adviser.md](adviser/adviser.md) |
| Audit Coordinator | [audit-coordinator/audit-coordinator.md](audit-coordinator/audit-coordinator.md) |
| Architect | [architect/architect.md](architect/architect.md) |
| Architect Reviewer | [architect/architect-reviewer.md](architect/architect-reviewer.md) |
| Documentation Engineer | [documentation/documentation-engineer.md](documentation/documentation-engineer.md) |
| Documentation Reviewer | [documentation/documentation-reviewer.md](documentation/documentation-reviewer.md) |
| Test Engineer | [test/test-engineer.md](test/test-engineer.md) |
| Test Reviewer | [test/test-reviewer.md](test/test-reviewer.md) |
| Implementation Engineer | [implementation/implementation-engineer.md](implementation/implementation-engineer.md) |
| Implementation Reviewer | [implementation/implementation-reviewer.md](implementation/implementation-reviewer.md) |

## Periodic auditors

These four independent roles run only when manually invoked. Each audits the complete current state of its area and relevant cross-artifact relationships across development iterations, independently of earlier agent reports. Invocation starts the audit; no creator handoff, upstream reviewer OK or other active agent is required.

| Role | Prompt |
| --- | --- |
| Architecture Auditor | [architect/architect-auditor.md](architect/architect-auditor.md) |
| Implementation Auditor | [implementation/implementation-auditor.md](implementation/implementation-auditor.md) |
| Test Auditor | [test/test-auditor.md](test/test-auditor.md) |
| Documentation Auditor | [documentation/documentation-auditor.md](documentation/documentation-auditor.md) |

Auditors retrieve the requested branch/ref (default main), identify its full SHA, inspect actual repository evidence and report coverage and limitations. They remain read-only, distinguish confirmed defects, investigation needs and architectural/owner decisions, and route findings to the responsible existing role through the owner.

Independent audits are outside the architectural decision execution and acceptance workflow. They do not issue workflow OK/NOT OK verdicts, close or waive gates, accept new semantics, launch other agents or authorize repairs. Prior review does not prevent a substantiated audit finding. The owner selects follow-up; corrections retain role ownership and independent review under the distinctions below. The four reports may be evaluated together through the audit execution pipeline. No additional persistent audit ledger or approval stage is required.

## Audit execution pipeline

The [Audit Coordinator](audit-coordinator/audit-coordinator.md) is an independent, read-only role between the four periodic auditors and the existing remediation and review workflows. It evaluates and reconciles reports, identifies decision and investigation needs, consolidates findings and prepares forwardable assignments. It does not modify repository artifacts, accept design decisions, authorize work, issue review verdicts, launch other agents or introduce an additional review gate. The owner retains authority over decisions, assignments, message forwarding, sequencing and closure. The Adviser and Improvement Auditor are not part of this pipeline; optional improvements may be considered separately.

```mermaid
flowchart TB
    Start([Start]) --> Invoke["Owner initiates the four audits"]

    subgraph Audits["1. Independent parallel audits"]
        AA["Architecture Auditor"]
        DA["Documentation Auditor"]
        TA["Test Auditor"]
        IA["Implementation Auditor"]
    end

    Invoke --> AA & DA & TA & IA
    AA & DA & TA & IA --> Collect["Wait for all four completed reports"]
    Collect --> Forward["Owner forwards all reports to Audit Coordinator"]

    subgraph Coordination["2. Collective evaluation and clarification"]
        Forward --> Evaluate["Coordinator verifies, reconciles and classifies findings"]
        Evaluate --> Questions{"Decisions, investigations or material limitations requiring owner input?"}
        Questions -->|Yes| Clarify["Owner provides decisions, obtains evidence, authorizes investigation referrals or explicitly defers affected work"]
        Clarify --> Evaluate
        Questions -->|No unresolved questions for current remediation scope| Consolidate["Coordinator produces consolidated report and eligible issue-recipient messages"]
    end

    subgraph Distribution["3. Owner authorization and scheduling"]
        Consolidate --> Authorize["Owner authorizes eligible assignments and records deferrals and limitations"]
        Authorize --> Pending{"Unfinished authorized assignments?"}
        Pending -->|Yes| Ready{"Eligible unblocked assignments with satisfied prerequisites?"}
        Ready -->|No| Resolve["Owner resolves blockers or dependencies, or explicitly defers affected work"]
        Resolve --> Pending
        Ready -->|Yes| Dispatch["Owner forwards eligible assignments to the Architect or responsible engineers"]
    end

    subgraph Remediation["4. Remediation and independent review for each active assignment"]
        Dispatch --> Work["Recipient addresses assigned issue or prepares justified no-change disposition"]
        Work --> Blocked{"Assignment blocked?"}
        Blocked -->|Yes| Requeue["Return unfinished assignment to pending work; retain blocker"]
        Blocked -->|No| Submit["Owner forwards recipient handoff to corresponding Reviewer"]
        Submit --> Review{"Independent review disposition?"}
        Review -->|NOT OK| Feedback["Owner forwards review findings"]
        Feedback --> Work
        Review -->|Blocked| Requeue
        Review -->|OK| Architecture{"Architectural registration requiring unified downstream handoff?"}
        Architecture -->|Yes| Handoff["Architect prepares unified handoff; owner forwards it unchanged to all three engineers"]
        Handoff --> Queue["Queue applicable downstream work without duplicating assignments"]
        Queue --> Complete["Close reviewed assignment"]
        Architecture -->|No| Complete
    end

    Complete & Requeue --> Wait["Wait for all active assignments to conclude or return to pending work"]
    Wait --> Pending

    Pending -->|No| Check{"All applicable remediation and review obligations complete and no unresolved material audit matters?"}
    Check -->|Yes| Success([Audit workflow completed])
    Check -->|No| Closure{"Owner explicitly directs closure with deferred findings or acknowledged limitations?"}
    Closure -->|Yes| Qualified([Owner-directed closure])
    Closure -->|No| Followup["Owner resolves remaining material follow-up through applicable workflows"]
    Followup --> Check
```

**Intake and evaluation.** The owner initiates the four auditors independently in parallel, preferably against the same full commit SHA, waits for all four completed reports and forwards them to the Coordinator. A completed report may have partial coverage. The Coordinator verifies material findings against the intended remediation target (default main), reconciles differing audited revisions and intervening changes, preserves evidence and distinguishes confirmed defects, investigation and decision needs, legitimate pending work, already addressed or unsupported findings, and optional improvements. It does not repeat the comprehensive audits.

**Decision and clarification loop.** The Coordinator identifies unresolved questions and material coverage or verification limitations for owner input. The owner may forward a pre-decision investigation referral to the Architect or explicitly authorize another bounded investigation within an existing role's scope. The Coordinator incorporates the resulting evidence and owner decisions until the decisions necessary for the current remediation scope have been resolved or explicitly deferred. No final remediation assignments are generated before that loop concludes. A referral is not acceptance of a design decision or authorization to implement it. Deferred findings and unresolved dependencies remain visible and affected work is excluded from the executable scope.

**Consolidation and routing.** The Coordinator retains one local issue reference for each underlying problem and prepares one forwardable Markdown message per eligible issue–recipient pair, preserving contributing findings, evidence, governing requirements, assignment scope, target revision, dependencies, completion conditions and review requirements. The owner explicitly authorizes and forwards each eligible assignment; a proposal or forwarding for discussion alone is not authorization. Route by artifact ownership and the substance of the work, not by the reporting auditor. Work outside established ownership requires explicit owner scope assignment.

| Recipient | Independent reviewer |
| --- | --- |
| Architect | Architect Reviewer |
| Documentation Engineer | Documentation Reviewer |
| Test Engineer | Test Reviewer |
| Implementation Engineer | Implementation Reviewer |

- Direct engineering remediation of independent audit defects entirely under existing accepted specifications goes directly to the responsible engineer, without a new Architect registration, unified architectural handoff or Architect Reviewer OK as an entry prerequisite. The engineer and reviewer verify the accepted specification basis, explicit owner assignment and absence of new normative behavior.
- Architectural investigations and changes follow the existing architectural decision workflow: the owner accepts substantive decisions, the Architect registers the accepted decision or authorized correction, and the Architect Reviewer independently reviews the registration. When the established architectural handoff applies, the Architect prepares it after the applicable Reviewer OK and the owner forwards it unchanged to all three engineers. The Coordinator records dependent downstream responsibilities but does not release them prematurely or produce duplicate engineering messages for work covered by that handoff. Independent eligible engineering assignments need not wait for unrelated architectural work.

**Execution and review.** The owner schedules eligible assignments across different agents independently, preserving material dependencies and one-assignment-at-a-time limits within each agent. Each remediation or registration assignment, including a justified no-change disposition, retains its corresponding independent review. NOT OK returns the same assignment for correction or resolution of the blocker and a current disposition. Blocked work remains unfinished and cannot be redispatched until its blocker is resolved. An unresolved semantic question, normative gap or proposed change to accepted behavior discovered during remediation returns to the normal architectural workflow. No extra Coordinator approval is required.

**Completion.** The Coordinator's consolidated report distinguishes assessment and assignment status from actual remediation and review completion, and identifies pending decisions, investigations, deferrals and limitations. The owner checks that no remediation is necessary or all applicable assignments have been closed by their corresponding independent Reviewer OK, with no unresolved material findings requiring further action within the current audit scope, outstanding material decisions or investigations, blockers or unresolved material audit limitations, including material follow-up discovered during remediation. Legitimately pending development work requiring no additional action within the current audit scope does not by itself prevent completion. Explicit owner-directed closure with deferred material findings or acknowledged limitations is distinct from successful completion. Completing the current cycle does not claim repository-wide conformance or require the four auditors to run again; any subsequent audit is separately initiated by the owner.

## Execution and acceptance

For assignments introducing, modifying or implementing a registered architectural decision, preserve this logical workflow and each role's independent review; downstream execution has no cross-agent sign-off gates:

```mermaid
flowchart TB
    subgraph architecture["1. Architecture"]
        direction LR
        A["Architect"] -->|Submit| AR["Architect Reviewer"]
        AR -->|NOT OK: revise| A
    end

    subgraph preparation["2. Documentation and testing (parallel)"]
        direction TB
        subgraph documentation["Documentation"]
            direction LR
            D["Documentation Engineer"] -->|Submit| DR["Documentation Reviewer"]
            DR -->|NOT OK: revise| D
        end
        subgraph testing["Testing"]
            direction LR
            T["Test Engineer"] -->|Submit| TR["Test Reviewer"]
            TR -->|NOT OK: revise| T
        end
    end

    subgraph implementation["3. Implementation"]
        direction LR
        I["Implementation Engineer"] -->|Submit| IR["Implementation Reviewer"]
        IR -->|NOT OK: revise| I
    end

    architecture -->|Unified handoff after Architect review OK| preparation
    architecture -->|Same unified handoff| implementation
    preparation -.->|Available documentation and tests| implementation
```

For architectural decision implementation, Architect Reviewer OK remains required for the exact registered decision, scope and revision/disposition. The Architect then generates one self-contained handoff, copied unchanged to all three downstream engineers as their primary input. Documentation/testing logically prepare implementation, but each engineer proceeds independently without waiting for another downstream agent's completed work, disposition, reviewer OK or no-action confirmation. Each submission retains its own independent review: NOT OK returns it to its producing role for correction or resolution of the blocker and a current review disposition. An engineer's justified no-change result also retains its own review, without an artificial edit or empty commit or a separate OK/nothing-to-do message to unblock another engineer; eligible prior substantive review may be reused as below. BLOCKED is not completed work. An ordinary assignment does not waive architectural review. Other sequencing exceptions need an explicit task-specific owner instruction identifying the affected requirement and scope, carried in the handoff and checked by the reviewer; all unaffected gates remain required.

For independent audit defects in existing documentation, tests or implementation, the owner may explicitly assign remediation directly to the responsible engineer when it can be completed entirely under already accepted specifications. The engineer and reviewer must verify that no new normative behavior is introduced. No new Architect registration or Architect Reviewer OK is required as an entry prerequisite for that remediation. Audit findings alone authorize neither work nor acceptance. Ownership, one-assignment-at-a-time limits and the responsible independent review remain required; downstream execution remains independent. An unresolved semantic question, normative gap or proposed change to accepted behavior returns the affected decision to the Architect and normal architectural review before implementation of that decision. Classify by the substance of the work, not its audit label.

For a correction or no-change disposition, reuse earlier substantive review only when available, sufficient independent evidence covers the same artifacts, behavior and relevant scope; no substantive defects remain; the earlier blocker was exclusively procedural; the owner explicitly waived that exact prerequisite for this assignment; relevant artifacts and governing requirements are unchanged; and no new evidence invalidates the assessment. The responsible reviewer verifies identities, scope, relevant changes and the exact waiver, performs only the additional checks needed to resolve that blocker, and issues a current disposition referencing the prior verdict/revision, reused evidence, waiver and new checks. Changes elsewhere or advancement of main alone do not require complete re-review. Reuse does not retrospectively convert NOT OK to OK. If any condition fails, the required substantive review and unwaived gates remain necessary; a procedural waiver cannot excuse substantive defects or replace an independent review that never occurred.

The Adviser operates independently. The Architect investigates design decisions and registers owner-approved changes in the specification and open issues. Reviewers verify independently and never silently correct files or create design authority.

The owner accepts substantive design before registration; reviewer acceptance verifies the recorded result. A published commit alone is not a review verdict. Tests accepted by their reviewer can still fail against incomplete production; implementation uses their actual expectations and failures while the accepted specification remains normative.

## Repository context and ownership

Discover current non-archived documents in [documentation/specification/](../specification/), checking titles, authority and current history rather than sorting historical filenames. Current entry points are [transformation-specification.md](../specification/transformation-specification.md), [open-design-issues.md](../specification/open-design-issues.md), [documentation-structure.md](../specification/documentation-structure.md), and [test-suite-structure.md](../specification/test-suite-structure.md).

The Architect owns accepted specification/open-issue registration. Documentation, test and implementation engineers own their respective artifacts; each has a separate reviewer. The specification governs behavior, structure documents govern placement, tests provide executable evidence and code establishes observed functionality. Historical documents, examples and unresolved alternatives cannot create requirements.

Writers normally publish their authorized future work to main using non-force updates and concurrency checks, then submit for independent review. Explicit task-specific branch restrictions override that default. Reviewer roles are read-only. These prompts do not authorize an agent to start another role or send its handoff itself.

Handoffs identify exact approved scope, source and submitted/snapshot SHAs, changed paths or no-change evidence, requirement-to-artifact coverage, checks/results/limitations and prior findings for corrections. Identify architectural review evidence or the explicit owner remediation assignment and accepted specification basis, plus any task-specific procedural waiver. For review reuse, include the prior verdict/revision/scope and unchanged-artifact/requirement evidence; the reviewer records the reused assessment, new checks and current disposition in its verdict. Refer to each role's full protocol. No additional persistent approval ledger is required.

## Active and archived versions

Each role directory contains its current, unversioned prompts and an `archive/` subdirectory for superseded versions. Archived prompts provide historical context and do not govern current agents.

Archive filenames follow `<document-name>-YYYYMMDDTHHMMSSZ.md`: UTC to seconds from the outgoing revision's last content-changing commit, following pure moves or renames with unchanged content. This matches the specification archive convention.

When replacing a prompt, preserve its exact predecessor bytes and file mode, preferably by reusing the Git blob. Never overwrite different historical content; a verified identical archive can be reused. Publish preservation and replacement together in an atomic commit. The Architect applies the corresponding procedure separately to each modified authoritative document in `documentation/specification/archive/`.
