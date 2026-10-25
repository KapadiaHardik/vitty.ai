# Vitty.ai Phase 2 — Senior Software Engineer Implementation Prompt

## Objective

Extend the existing Vitty.ai Phase 1 document intelligence product into Phase 2: an AI-assisted workflow engine for CA firms.

Build one reliable workflow: **Invoice Verification and Discrepancy Reporting**.

Users should be able to upload or select an invoice and supporting documents, extract relevant information, compare values, identify discrepancies, review evidence, approve or reject findings, and generate a final report.

**Engineering principle: Build the smallest maintainable solution that works end to end. Do not overengineer.**

---

## 1. Inspect the Existing Project First

Before writing code:

- Inspect the repository, architecture, database models, API routes, authentication, document ingestion, RAG, LLM integration, background jobs, frontend, and tests.
- Reuse existing components and dependencies wherever possible.
- Identify only the changes required for Phase 2.
- Present a short implementation plan and architecture diagram before coding.
- Do not rewrite Phase 1 or replace working libraries without a clear reason.

Do not generate duplicate services, utilities, models, or abstractions that already exist.

## 2. Target Architecture

Implement a modular monolith. Keep the existing frontend, backend, database, document storage, and LLM integrations.

### High-level architecture

```text
                  CA Firm User
                       |
                       v
                Next.js Frontend
                       |
                 FastAPI REST API
                       |
                       v
               Workflow Orchestrator
                       |
          +------------+------------+
          |            |            |
          v            v            v
     Extraction     Validation    Comparison
     (reuse P1)     (Python)      (Python)
          |            |            |
          +------------+------------+
                       |
                       v
              Discrepancy Analysis
              (Rules + optional LLM)
                       |
                       v
                Human Review
                       |
                       v
                 Final Report
                       |
          +------------+------------+
          |            |            |
          v            v            v
      PostgreSQL   Document Store   Audit Log
```

### Workflow execution sequence

```text
Start Workflow
      |
      v
Validate Inputs
      |
      v
Extract Invoice and Reference Data
      |
      v
Validate Extracted Fields and Totals
      |
      v
Compare Invoice with Available Documents
      |
      v
Identify Discrepancies
      |
      v
Save Findings and Evidence
      |
      v
Human Review and Approval
      |
      v
Generate Final Report
```

If required reference documents are missing, continue only with applicable checks and clearly mark the remaining checks as "Not verified." Do not treat missing evidence as a confirmed discrepancy.

### Architecture constraints

- Keep the existing modular monolith.
- Reuse the existing FastAPI application and database.
- Reuse Phase 1 document parsing, OCR, extraction, RAG, and LLM clients.
- Use ordinary Python functions for deterministic workflow steps.
- Use the existing background-job infrastructure if one already exists.
- Add a workflow framework such as LangGraph only if the repository genuinely needs persisted graph execution, conditional routing, and checkpoint recovery. Otherwise, start with a simple explicit workflow service.
- Do not add microservices, Kubernetes, Kafka, a second vector database, or a separate orchestration service.
- Do not introduce multiple agents. This phase needs one controlled workflow, not a multi-agent platform.

## 3. Minimal Workflow Implementation

Create one invoice-verification workflow with the following steps.

### Step 1: Input validation

Accept document IDs from the authenticated user's authorized workspace.

Support:
- Invoice
- Purchase order, if available
- Goods receipt or service completion record, if available

Verify document access and processing status before starting.

### Step 2: Structured extraction

Reuse the existing extraction pipeline.

Extract only the fields required for the first workflow:

- Supplier name and tax identifier, if present
- Invoice number and date
- Purchase-order reference, if present
- Line-item descriptions
- Quantities and unit prices
- Taxable amount and tax amounts
- Invoice total
- Currency

For reference documents, extract corresponding identifiers, quantities, prices, and amounts.

Use typed Pydantic schemas. Preserve source document IDs and page or cell references when available.

Do not duplicate the Phase 1 extraction engine.

### Step 3: Deterministic validation

Implement ordinary Python functions for:

- Missing required fields
- Invalid numeric values
- Line-item arithmetic
- Tax-total reconciliation
- Grand-total reconciliation
- Configurable rounding tolerance

Keep calculations and business rules outside the LLM.

### Step 4: Cross-document comparison

Compare invoice data with available reference data.

Check:
- Supplier mismatch
- Purchase-order reference mismatch
- Quantity mismatch
- Unit-price mismatch
- Tax or total mismatch
- Potential duplicate invoice number within the accessible dataset

Use deterministic comparison rules first.

If line-item matching is ambiguous, optionally ask the existing LLM to suggest matches, then validate the result. Record unresolved ambiguity for human review.

### Step 5: Discrepancy report

Store each finding with:

- Discrepancy type
- Severity
- Field or line item
- Invoice value
- Reference value, if available
- Rule applied
- Explanation
- Evidence references
- Recommended follow-up
- Review status

Use simple configurable severity rules. Do not label discrepancies as fraud or generate unsupported fraud probabilities.

### Step 6: Human review

Allow the user to:

- Inspect extracted fields
- Open supporting documents
- Review discrepancies and evidence
- Correct extracted values
- Accept or dismiss findings with a reason
- Approve or reject the final report

Record reviewer, timestamp, decision, and reason.

Approval applies only to the workflow report. Do not add automatic payment, filing, or external system actions.

### Step 7: Final report

Generate a report containing:

- Documents reviewed
- Extracted invoice summary
- Checks performed
- Discrepancies found
- Checks not performed and reasons
- Evidence references
- Human review decision
- Audit history

Use the existing reporting or export mechanism where possible. Do not build a new PDF generation framework unless necessary.

## 4. Minimal Backend Design

Follow the existing project conventions. Prefer extending existing files and models where appropriate rather than creating a new layer for every operation.

Add only the necessary modules, which may map to the following responsibilities:

```text
backend/
  workflows/
    invoice_verification.py   # Workflow orchestration
    schemas.py                # Input/output schemas
    validation.py             # Deterministic checks
    comparison.py             # Cross-document comparisons
    reporting.py              # Final report assembly
```

This is a logical example, not a requirement to duplicate existing modules.

Keep the main workflow readable:

1. Validate inputs.
2. Extract structured data using existing services.
3. Run deterministic checks.
4. Compare available reference documents.
5. Persist findings.
6. Pause for human review when necessary.
7. Generate the final report.

Use small, reusable functions with clear inputs and outputs. Avoid deeply nested logic, generic frameworks, excessive classes, and unnecessary design patterns.

## 5. Minimal Data Model

Inspect the existing schema before adding tables.

Reuse existing users, workspaces, documents, and audit logs.

Create only the additional persistent records needed for:

- Workflow execution and status
- Discrepancy findings
- Human review decisions

Store document references rather than copying full document contents.

Persist workflow state if required for background execution and resumption. Avoid storing duplicate representations of data already maintained by Phase 1.

Use migrations consistent with the existing project.

## 6. Minimal API

Follow the existing API versioning and naming conventions. Add only the endpoints needed for the workflow:

```text
POST /api/v1/workflows/invoice-verification
GET  /api/v1/workflows/{id}
GET  /api/v1/workflows/{id}/report
POST /api/v1/workflows/{id}/review
```

The start endpoint accepts authorized document IDs and optional structured inputs.

The status endpoint returns execution state and safe-to-display progress.

The report endpoint returns the current or final report.

The review endpoint records an authorized approval, rejection, or correction.

Add separate endpoints only when justified by the existing frontend or application design.

Use Pydantic validation, existing authentication, workspace authorization, and appropriate HTTP status codes. Do not expose internal exceptions to clients.

## 7. Frontend

Extend the existing Next.js UI. Do not redesign the entire product.

Build only:

1. **Start workflow:** Select documents and start verification.
2. **Workflow status:** Show progress, failures, and completion.
3. **Review findings:** Display extracted values, discrepancies, and source evidence.
4. **Final report:** Show findings and human review status.

Reuse existing components, styles, document viewers, and upload screens.

Include loading, empty, failure, and retry states. Reflect approval only after backend confirmation.

## 8. Reliability and Security

Implement only the essential safeguards:

- Enforce workspace isolation on every request.
- Never trust client-supplied document IDs without authorization checks.
- Treat uploaded document text as untrusted input.
- Keep business rules and access control outside the LLM.
- Validate model outputs against typed schemas.
- Handle parsing errors, LLM failures, and missing evidence explicitly.
- Apply bounded retries and timeouts if background execution is used.
- Make workflow initiation idempotent where practical.
- Record workflow starts, failures, corrections, approvals, and rejections.
- Avoid logging document contents, credentials, or unnecessary sensitive data.

Do not create a separate security framework when existing middleware and authorization services can handle these requirements.

## 9. Testing

Reuse the Phase 1 evaluation dataset and add a small, focused set of synthetic invoice and purchase-order fixtures.

Cover at least:

1. Invoice matches the purchase order.
2. Invoice total is incorrect.
3. Quantity or unit price differs.
4. Required fields are missing.
5. Purchase order is unavailable.
6. Extraction returns invalid data.
7. LLM call fails.
8. Reviewer corrects or rejects a finding.
9. Workflow resumes after review.
10. A user attempts cross-workspace access.

Use deterministic tests for calculations and comparisons. Mock the LLM in unit tests. Test actual API and database integration for the main happy path and important failure paths.

Verify that each finding references the right source evidence.

Do not build a complex evaluation platform in Phase 2. Extend the existing test and evaluation framework.

## 10. Implementation Milestones

Implement in this order:

**Milestone 1:** Inspect repository, produce architecture diagram, and identify minimal changes.

**Milestone 2:** Implement workflow execution and persistence.

**Milestone 3:** Reuse extraction and add deterministic validation and comparison.

**Milestone 4:** Add discrepancy findings and evidence references.

**Milestone 5:** Add human review, audit events, and report generation.

**Milestone 6:** Integrate the workflow into the existing frontend.

**Milestone 7:** Run tests, fix regressions, and document the implementation.

After each milestone, run relevant tests and keep the application runnable. Do not implement all milestones in one enormous code-generation pass.

## 11. Explicit Non-Goals

Do not build:

- Multiple collaborating agents
- A general-purpose no-code workflow builder
- A new document intelligence or RAG engine
- New accounting software integrations
- Automatic email sending
- Automatic payments or accounting entries
- Automatic tax-return filing
- Complex risk-scoring systems
- A new monitoring platform
- Unnecessary database tables or abstraction layers
- A broad frontend redesign
- Any infrastructure that is not needed to ship this workflow

These capabilities can be considered later based on pilot feedback.

## 12. Definition of Done

Phase 2 is ready for pilot testing when a user can:

1. Select an invoice and available supporting documents.
2. Start invoice verification.
3. See the workflow's progress and status.
4. Review extracted values and evidence.
5. See arithmetic errors and cross-document discrepancies.
6. Correct values and review findings.
7. Approve or reject the report.
8. Access the final report and audit history.

All of this must work through the real application, API, and database.

No external financial action should occur automatically.

## Final instruction

Act as a pragmatic senior software engineer. Prefer existing code over new code, deterministic rules over unnecessary AI calls, and simple functions over elaborate abstractions.

First inspect the repository and return:
1. A concise description of the current architecture.
2. The target architecture diagram.
3. The exact files and database changes required.
4. A short, ordered implementation plan.

Wait for review of that plan before making broad changes. Then implement one milestone at a time and report test results after each milestone.