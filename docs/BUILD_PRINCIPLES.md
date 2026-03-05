# GLCS Build Principles

Welcome to the Global Logic Context Store project. This document outlines the principles and guidelines every contributor — human or AI — must follow. Please read this thoroughly before making any contributions.

---

## 1. Engineering Excellence

GLCS is designed to be released as a production-grade PyPI package. Every line of code must reflect that ambition.

- **Sound architecture.** All designs must be scalable, modular, and compatible with the broader Python ecosystem. Think long-term — write code that future contributors can extend without rewriting.
- **World-class standards.** Follow established Python conventions (PEP 8, type hints, clear naming). The bar is not "it works" — it is "it works well, reads well, and scales well."
- **Verifiable correctness.** Every new component must ship with proper tests. No pull request is complete without test coverage that demonstrates the code works as intended and does not break existing functionality.

## 2. Clarity and Auditability

Every part of GLCS must justify its existence.

- **No mystery components.** If a module, class, or function exists, its purpose should be immediately understandable. No contributor should ever look at a component and wonder *"why was this built?"*
- **Traceable design decisions.** Architectural choices should be documented where they are made. When a non-obvious decision is taken, leave a brief rationale — either inline, in a design doc, or in the PR description.
- **Readable code over clever code.** Favour straightforward implementations. If something requires a complex approach, document why the complexity is necessary.

## 3. Documentation

Good documentation is not optional — it is a core deliverable.

- **Clean and concise.** Write documentation that is easy to read and easy to navigate. Avoid walls of text; use structure, examples, and clear language.
- **Accurate and up to date.** Stale documentation is worse than no documentation. When you change behaviour, update the corresponding docs in the same PR.
- **Audience-aware.** API references should be precise. Guides should be approachable. Know who you are writing for.

## 4. Responsible Use of AI Coding Assistants

AI coding tools are welcome in this project under a **trust but verify** framework.

- **Developer ownership.** The developer who submits the code owns it — regardless of whether an AI generated it. You are responsible for understanding, reviewing, and testing every line.
- **Mandatory testing.** All AI-generated components must be tested by the developer before submission. Do not assume correctness — verify it.
- **Critical review.** Treat AI-generated code with the same scrutiny you would apply to a junior developer's pull request. Check for edge cases, security issues, and alignment with project conventions.

## 5. Guidelines for AI Coding Agents

When an AI agent is used as a contributor on this project, it must operate under the following constraints:

- **No shortcuts.** The agent must not take sub-optimal engineering shortcuts to save time or tokens. Quality is non-negotiable.
- **Present options, don't assume.** When the agent encounters ambiguity or multiple valid approaches, it must lay out all options clearly and let the developer decide. Autonomous decisions on architectural or design matters are not permitted.
- **Testability is mandatory.** The agent must not build components that cannot be independently tested and verified. If a component cannot be tested, it should not be built.
- **Align with engineering excellence.** Every output from the agent must meet the standards defined in Section 1. Code that does not meet these standards should be flagged and revised — not shipped.

---

*These guidelines apply to all contributors. When in doubt, ask. When uncertain, discuss. When building, build it right.*
