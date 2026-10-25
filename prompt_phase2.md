## Mandatory Architecture Audit and Simplification — Phase 1 and Phase 2

Act as a pragmatic senior software engineer. Before implementing Phase 2, audit the entire existing Phase 1 codebase for unnecessary complexity, duplicated functionality, and premature architectural decisions.

**Do not assume that the existing Phase 1 architecture is correct simply because it already exists. Improve it where justified, without breaking working functionality.**

### 1. Audit for unnecessary complexity

Inspect and identify:

- Unnecessary abstractions, interfaces, base classes, factories, and dependency-injection layers.
- Multiple AI agent frameworks or overlapping orchestration libraries.
- Duplicate LLM clients, embedding providers, retrieval pipelines, or document-processing services.
- Unnecessary microservices, background workers, message queues, databases, vector stores, or infrastructure.
- Excessive wrappers around simple Python functions.
- Duplicate database models, utilities, API endpoints, and configuration.
- Complex implementations where a simple, readable solution would work.
- Dependencies that are unused, redundant, or introduced without a clear requirement.
- Premature implementations of Phase 2 or Phase 3 features that add maintenance overhead without providing current value.

### 2. Apply a simplify-before-extending approach

For every identified issue, determine whether to:

1. Keep it because it solves a real requirement.
2. Simplify it while preserving its behavior.
3. Consolidate duplicated functionality.
4. Remove it if it is unused and safe to delete.

Prefer the simplest implementation that satisfies the actual product requirements.

Examples:

- Use one LLM provider abstraction rather than multiple overlapping frameworks.
- Use ordinary Python functions for deterministic validation and comparison.
- Reuse the existing RAG pipeline instead of building another retrieval engine.
- Reuse PostgreSQL and pgvector instead of adding another database without a demonstrated need.
- Reuse existing background-job infrastructure rather than introducing a second job system.
- Avoid LangChain and LangGraph together unless each has a specific, justified role.
- Do not create generic agent frameworks when the product needs only one invoice-verification workflow.

These are guidelines, not automatic deletion rules. Inspect actual dependencies and usage before making changes.

### 3. Preserve working functionality

Before refactoring:

- Run the existing tests and record the baseline.
- Identify existing Phase 1 features and their dependencies.
- Preserve API contracts and database compatibility where practical.
- Use migrations for required schema changes.
- Add regression tests for behavior that could be affected.
- Avoid deleting code solely because it appears complex; verify whether it is used.
- Do not expose secrets or real client documents in logs or test fixtures.

Do not perform a complete rewrite. Make focused, incremental improvements.

### 4. Simplify infrastructure

Keep only the infrastructure needed to run and maintain the product.

Prefer the existing modular monolith and deployment setup. Do not add Kubernetes, microservices, Kafka, additional databases, separate orchestration services, or monitoring platforms unless a concrete requirement justifies them.

If a component is unnecessary, explain its removal and update the relevant configuration, dependencies, documentation, and tests.

### 5. Report findings before making broad changes

First provide a concise audit report with:

| Area | Required output |
|---|---|
| Existing architecture | What currently exists and why |
| Unnecessary complexity | Specific files, dependencies, or components |
| Recommended action | Keep, simplify, consolidate, or remove |
| Risk | Potential impact on Phase 1 functionality |
| Implementation | Minimal changes required |

Separate essential fixes from optional future improvements.

Do not refactor everything at once. Propose the smallest safe cleanup plan, then implement it incrementally after review.

### 6. Definition of architectural quality

The final codebase should have:

- One clear implementation for each responsibility.
- Minimal dependencies and infrastructure.
- Explicit, understandable data flow.
- Readable, testable functions.
- Clear module boundaries without excessive abstraction.
- Reliable document processing and evidence-backed answers.
- Secure workspace isolation and auditability.
- A straightforward path to extend workflows in Phase 2 and integrations in Phase 3.

**Final rule: Do not add a framework, abstraction, service, database, or dependency unless you can explain the concrete problem it solves and why a simpler existing solution is insufficient.**