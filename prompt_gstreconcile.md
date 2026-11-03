# Vitty.ai — GST Reconciliation Engine Development

## Objective

Build a production-ready GST Reconciliation Engine for Indian CA firms.

The first supported workflow is:

**GSTR-2B vs Purchase Register reconciliation.**

The system must accept two financial datasets, normalize their records, match invoices, identify discrepancies, provide a review interface and generate downloadable reconciliation reports.

This feature must integrate into the existing Vitty.ai application.

---

## 1. IMPORTANT: Inspect the existing codebase first

Before writing code:

1. Inspect the existing frontend and backend architecture.
2. Understand the existing Phase 1 document intelligence and RAG implementation.
3. Inspect the Phase 2 invoice verification workflow, if implemented.
4. Identify existing:
   - Authentication and tenant isolation
   - Document upload and storage
   - Excel/CSV parsing
   - OCR and extraction services
   - Database models
   - Background processing
   - API structure
   - Frontend components
   - Audit logs and permissions
5. Identify reusable services and components.

Do not create duplicate implementations of existing functionality.

Prepare a short implementation plan identifying:
- Components to reuse
- Components to extend
- New components required
- Existing code that should be simplified, if necessary

Do not rewrite the existing application.

## 2. Functional architecture

Implement the following pipeline:

File Upload
→ Data Extraction
→ Column Mapping
→ Data Validation
→ Data Normalization
→ Invoice Matching
→ Discrepancy Classification
→ Reconciliation Results
→ Human Review
→ Report Generation

Keep the implementation modular but avoid unnecessary abstractions.

Use the existing backend architecture and database wherever possible.

## 3. File upload and ingestion

Support:
- GSTR-2B Excel and CSV
- Purchase Register Excel and CSV

PDF support should be added only where the existing extraction pipeline can reliably process it.

Requirements:
- Allow selection of company GSTIN and tax period.
- Allow users to upload both datasets.
- Auto-detect column names.
- Provide manual column mapping when automatic mapping fails.
- Validate mandatory columns.
- Show upload and processing status.
- Identify duplicate uploads.
- Preserve original uploaded files.
- Store source filename, sheet name and row number for every imported record.

Do not silently discard invalid records.

Display invalid records with their validation errors.

## 4. Standardized invoice data model

Create a common normalized invoice representation.

Fields:

- Tenant ID
- Company GSTIN
- Supplier GSTIN
- Supplier name
- Invoice number
- Normalized invoice number
- Invoice date
- Document type
- Taxable value
- IGST
- CGST
- SGST
- Cess
- Invoice total
- Place of supply
- Tax period
- Source type (GSTR-2B or Purchase Register)
- Source document ID
- Source filename
- Source sheet
- Source row number
- Validation status

Preserve original extracted values alongside normalized values.

Support invoices, debit notes and credit notes.

Use decimal arithmetic for all financial calculations. Avoid floating-point errors.

## 5. Data normalization

Implement reusable normalization functions for:

- GSTIN validation and formatting
- Invoice number normalization
- Date standardization
- Numeric and currency parsing
- Tax component standardization
- Document type standardization
- Missing and invalid values

Invoice number normalization should handle:
- Uppercase/lowercase differences
- Leading/trailing spaces
- Special characters
- Slashes and hyphens
- Extra spaces

Do not remove meaningful invoice number characters indiscriminately.

Keep both original and normalized values.

## 6. Invoice matching engine

Build a deterministic Python matching engine.

Implement matching in stages:

### Stage 1: Exact match
Match using:
- Supplier GSTIN
- Normalized invoice number
- Invoice date

### Stage 2: Strong match
Match using:
- Supplier GSTIN
- Normalized invoice number
- Small date or amount differences

### Stage 3: Flexible match
Handle:
- Invoice number formatting differences
- Minor date differences
- Taxable value or tax differences

### Stage 4: Potential match
Use a weighted similarity score based on:
- Supplier GSTIN
- Invoice number similarity
- Invoice date
- Taxable value
- Tax amounts

Return potential matches for human review rather than automatically treating uncertain records as matched.

Important:
- Prevent one invoice from being matched to multiple records unintentionally.
- Handle duplicate invoices.
- Handle credit notes and debit notes separately.
- Support configurable tolerances.
- Record the matching rule and confidence/reason for every match.
- Make matching deterministic and reproducible.

Do not use an LLM for invoice matching.

## 7. Discrepancy classification

Classify every record into one of the following categories:

1. Matched
2. Books only
3. GSTR-2B only
4. Taxable value mismatch
5. IGST mismatch
6. CGST mismatch
7. SGST mismatch
8. Cess mismatch
9. Invoice date mismatch
10. Duplicate invoice
11. Credit/debit note mismatch
12. Potential match
13. Invalid or incomplete record

For each discrepancy, calculate:

- Books value
- GSTR-2B value
- Difference
- Tax component differences
- Matching status
- Discrepancy reason

Allow multiple discrepancy flags where appropriate.

Avoid hiding a tax mismatch just because the invoice number matches.

## 8. Reconciliation dashboard

Build a dashboard for each GSTIN and tax period.

Display:

### Summary metrics
- Total Purchase Register invoices
- Total GSTR-2B invoices
- Matched invoices
- Books-only invoices
- GSTR-2B-only invoices
- Mismatched invoices
- Duplicate invoices
- Invalid records

### Financial summary
- Total taxable value in books
- Total taxable value in GSTR-2B
- Taxable value difference
- IGST difference
- CGST difference
- SGST difference
- Cess difference

### Reconciliation status
Show the number of records in each discrepancy category.

Allow users to filter by:
- GSTIN
- Tax period
- Supplier
- Reconciliation status
- Discrepancy type
- Review status

## 9. Exception review interface

Build a detailed reconciliation table.

For each record, display:

- Supplier name and GSTIN
- Invoice number
- Invoice date
- Books taxable value
- GSTR-2B taxable value
- Tax differences
- Matching status
- Discrepancy reason
- Source references
- Suggested next action

When a user opens a record, show the two source records side by side.

Allow the reviewer to:

- Mark as resolved
- Mark as pending
- Accept a difference with a reason
- Reject a suggested match
- Manually link two records
- Add comments
- Mark for client/vendor follow-up

Record reviewer identity, timestamp, decision and comments.

Do not automatically modify the original uploaded records.

## 10. GST validation and business rules

Implement deterministic validation for:

- GSTIN format
- Required invoice fields
- Tax amount calculations
- Taxable value and invoice total consistency
- Tax component differences
- Duplicate invoice identification
- Document type consistency

Keep tax rules and matching tolerances configurable and versioned.

Do not hardcode assumptions about every GST scenario.

Separate reconciliation results from legal ITC eligibility decisions.

The application must not automatically declare ITC eligible or ineligible. Present discrepancies and supporting information for CA review.

## 11. Report generation

Generate downloadable Excel reports containing:

1. Summary
2. Matched invoices
3. Books-only invoices
4. GSTR-2B-only invoices
5. Tax mismatches
6. Duplicate invoices
7. Potential matches
8. Invalid records
9. Review history

Each row should include source references and discrepancy explanations.

Use the existing report-generation infrastructure if available.

## 12. Database and APIs

Inspect existing database models before creating new ones.

Create or extend models for:

- Reconciliation runs
- Uploaded source documents
- Normalized invoice records
- Invoice matches
- Discrepancies
- Review decisions
- Reconciliation reports

Use existing tenant and user relationships.

Suggested API capabilities:

- Create reconciliation run
- Upload source files
- Map columns
- Validate uploaded data
- Start reconciliation
- Get reconciliation summary
- Get invoice-level results
- Get discrepancy details
- Update review status
- Manually link invoice records
- Add reviewer comments
- Download reconciliation report

Follow the existing API naming and response conventions.

## 13. Security and reliability

Ensure:

- Strict tenant-level data isolation
- GSTIN-level access controls where applicable
- File validation and secure storage
- No cross-tenant record matching
- Audit logging for important actions
- Safe handling of malformed Excel/CSV files
- Idempotent processing where appropriate
- Proper error handling and processing status
- Large-file processing without blocking API requests

Do not introduce Kafka, microservices or Kubernetes for this feature.

Reuse the existing background processing infrastructure.

## 14. Testing

Create tests for:

- Exact invoice matches
- Invoice number formatting differences
- Date differences
- Taxable value differences
- Individual tax component mismatches
- Missing invoices
- Duplicate invoices
- Credit/debit notes
- Invalid GSTINs
- Invalid input files
- Multiple GSTINs
- Multiple tax periods
- Potential matches
- One-to-one matching constraints
- Cross-tenant isolation
- Report generation
- Manual review and resolution

Use synthetic test data. Do not use real customer financial information in tests.

## 15. Implementation milestones

Implement incrementally.

**Milestone 1 — Codebase audit and design**
Inspect existing architecture and provide the implementation plan.

**Milestone 2 — File ingestion**
Implement upload, column mapping, parsing and validation.

**Milestone 3 — Normalization**
Build and test the normalized invoice representation.

**Milestone 4 — Matching engine**
Implement deterministic matching and duplicate handling.

**Milestone 5 — Discrepancy engine**
Calculate differences and classify exceptions.

**Milestone 6 — Dashboard and review**
Build summary metrics, filters and human review interface.

**Milestone 7 — Reports and testing**
Generate Excel reports and run the complete test suite.

After each milestone:
- Run relevant tests.
- Fix regressions.
- Summarize files changed.
- Explain what is working.
- Identify remaining work.

Do not implement all milestones in one uncontrolled change.

## 16. Architecture constraints

- Reuse Vitty.ai Phase 1 document infrastructure.
- Reuse Phase 2 workflow components where suitable.
- Keep the existing modular monolith.
- Use Python for deterministic reconciliation logic.
- Use LLMs only where useful for interpreting ambiguous information or generating explanations.
- Do not use LLMs for financial calculations or final invoice matching.
- Avoid multiple agent frameworks.
- Avoid duplicate OCR, RAG or LLM pipelines.
- Avoid unnecessary dependencies and infrastructure.
- Keep the code readable, testable and maintainable.

## Expected outcome

A CA firm should be able to:

1. Select a client GSTIN and tax period.
2. Upload GSTR-2B and Purchase Register.
3. Review automatically mapped and validated data.
4. Run reconciliation.
5. See matched, missing and mismatched invoices.
6. Investigate individual discrepancies with source evidence.
7. Resolve exceptions with reviewer comments.
8. Export a complete reconciliation report.

**Start with Milestone 1. Inspect the existing repository and report your findings and implementation plan before modifying code.**