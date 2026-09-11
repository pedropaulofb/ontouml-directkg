# Role

Act as a senior researcher and software/knowledge-representation analyst with expertise in OntoUML, conceptual modeling, metamodeling, knowledge graphs, semantic transformations, and specification design.

# Context

I am developing a project called **OntoUML DirectKG**:

https://github.com/pedropaulofb/ontouml-directkg

The project is still in the **specification stage**, and that specification will need to be continued in later messages.

I will attach **two documents** to this conversation. Both concern the current specification of OntoUML DirectKG:

1. **Specification document** — contains decisions, requirements, definitions, constraints, design choices, and other aspects that have already been established.
2. **Open-items document** — contains questions, unresolved decisions, topics, alternatives, and other items that still need to be discussed or specified.

Both attached documents must be available to you at execution time.

# Relationship to previous context

This prompt is designed to work in either of two situations.

## If this conversation already contains prior OntoUML research

If, earlier in this same conversation, you were instructed to perform an in-depth study of OntoUML and repositories such as:

https://github.com/ontouml/ontouml-json2graph

https://github.com/OntoUML/ontouml-metamodel

https://github.com/OntoUML/ontouml-js

https://github.com/OntoUML/ontouml-vp-plugin

https://github.com/ontouml/ontouml-schema

then retain and use that previously acquired understanding as background knowledge when studying the DirectKG documents.

Do not repeat that research, summarize it, or report it now.

## If this is a new conversation

Do not assume that any previous OntoUML or DirectKG research is available.

Use the information contained in the two attached documents as the primary source for understanding the current DirectKG specification.

You may use your existing knowledge of OntoUML to interpret the material, but do not silently replace, reinterpret, or override explicit project decisions recorded in the documents.

The purpose of this prompt is **not** to conduct a new general OntoUML research project. The immediate task is to understand the two DirectKG specification documents in depth.

# Task

Study both attached documents **completely and in depth**.

Your objective at this stage is only to build a precise internal understanding of:

- what OntoUML DirectKG is intended to do;
- the project's goals and non-goals;
- its scope and boundaries;
- terminology and conceptual distinctions used by the project;
- requirements already established;
- architectural and design decisions already made;
- transformation principles and rules already established;
- expected inputs and outputs;
- constraints and invariants;
- examples and their intended meaning;
- implementation-related assumptions, where specified;
- decisions that are final or treated as established;
- decisions that are provisional or explicitly subject to reconsideration;
- questions and specification items that remain open;
- dependencies between open questions;
- alternatives already considered;
- arguments, rationale, trade-offs, or rejected alternatives recorded in the documents;
- inconsistencies, ambiguities, overlaps, or dependencies that may become relevant when specification work resumes.

Read the documents as parts of **one evolving specification**, not as independent texts.

# Source authority

For the purpose of understanding the current DirectKG specification:

- treat explicit decisions in the specification document as established project decisions unless the document itself marks them as provisional;
- treat items in the open-items document as unresolved unless there is clear evidence elsewhere in the supplied material that they have already been decided;
- distinguish carefully between requirements, examples, rationale, tentative ideas, open questions, and historical discussion;
- do not convert examples or exploratory notes into requirements unless the documents clearly do so;
- do not assume that an unresolved item has been decided merely because one alternative appears more technically plausible.

If the two documents appear to conflict, preserve awareness of the conflict rather than silently choosing one interpretation.

# Study discipline

Build a coherent internal model of the specification, including relationships between decisions and open questions.

Pay particular attention to:

- terminology that must remain consistent;
- dependencies between specification sections;
- assumptions that later decisions rely on;
- areas where one unresolved decision may affect several other parts of the specification;
- distinctions between OntoUML semantics and DirectKG transformation choices;
- distinctions between conceptual requirements and implementation decisions;
- anything involving temporal aspects of OntoUML, when present;
- interactions between the specification and the structure or semantics of OntoUML models.

Do not fabricate missing decisions or infer certainty where the documents remain intentionally open.

# What not to do yet

At this stage, **do not continue the specification**.

Specifically, do not:

- answer any of the open questions;
- recommend alternatives;
- resolve ambiguities;
- propose new requirements;
- identify a preferred architecture;
- write or modify code;
- modify the documents;
- produce a revised specification;
- create an implementation plan;
- create issues or tasks;
- evaluate which existing decisions are good or bad;
- provide a summary, review, critique, diagnosis, or report unless I explicitly request one later.

The goal is preparation for a subsequent discussion, not execution of that discussion now.

# Completion behavior

After you have fully studied both documents:

- do not present your findings;
- do not summarize either document;
- do not list the open questions;
- do not explain the project back to me;
- do not propose next steps;
- do not ask me to choose among the open questions.

Simply confirm briefly that:

1. you have studied both documents in depth;
2. you understand the current DirectKG specification and its unresolved items;
3. you are ready for my next instructions.

Then stop and wait for my next message.