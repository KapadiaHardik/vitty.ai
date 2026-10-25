# Development Prompt: Vitty.ai Financial Analytics Engine for CA and BFSI Firms

Act as a senior AI engineer, financial data analyst, and enterprise SaaS architect. Extend my existing Vitty.ai platform by developing a production-oriented **Financial Analytics Engine** for Indian CA firms, audit firms, wealth management companies, and BFSI businesses.

## 1. Existing Platform

Phase 2 is complete. The platform currently includes:

### A. Document Intelligence — `/documents`
- Upload financial and compliance documents.
- RAG-based question answering over uploaded documents.
- Extract relevant information from financial statements, GST returns, audit reports, contracts, and other PDFs.

### B. Invoice Verification — `/workflows`
- Invoice data extraction and required-field validation.
- Deterministic arithmetic checks using Python.
- Invoice-to-purchase-order matching.
- Duplicate invoice detection.
- Human review, accept/dismiss findings, audit notes, and report generation.

**Important:** Inspect the existing repository, architecture, database models, API endpoints, and dependencies before implementing anything. Reuse existing components and preserve working Phase 2 functionality. Do not rebuild the platform from scratch.

## 2. Objective

Build a modular financial analytics engine that transforms uploaded financial data into measurable insights, reconciliations, exceptions, and evidence-backed reports.

The engine must support different business configurations without hard-coding one firm's accounting rules into the core platform.

## 3. Core Analytics Modules

### Module 1: Financial Statement Analytics
Target: CA firms, auditors, SMEs, and corporate finance teams.

- Analyse Profit & Loss statements, balance sheets, and cash flow statements.
- Calculate liquidity, profitability, leverage, and efficiency ratios.
- Compare financial periods and identify significant changes.
- Detect unusual expense movements, margin deterioration, and working-capital changes.
- Explain the numerical drivers behind each finding.
- Flag missing or inconsistent financial statement figures.

### Module 2: Ledger and Bank Reconciliation
Target: CA firms, accounting teams, and finance departments.

- Ingest bank statements and ledger exports from CSV, Excel, and supported PDFs.
- Normalise dates, descriptions, debit/credit values, and transaction references.
- Match transactions using exact identifiers and configurable amount/date rules.
- Use fuzzy matching only for candidate generation, with transparent confidence scores.
- Identify unmatched entries, duplicate transactions, amount differences, and timing differences.
- Produce matched, unmatched, and manual-review reports.

### Module 3: GST Reconciliation Analytics
Target: Indian CA and tax-compliance firms.

- Import purchase registers and supported GSTR-2B data.
- Match supplier GSTIN, invoice number, invoice date, taxable value, and tax amounts.
- Identify missing invoices, potential ITC mismatches, duplicate records, and differences in tax values.
- Classify exceptions by severity and explain the reason.
- Export review-ready reconciliation reports.

Do not automatically conclude that ITC is eligible or ineligible from a data mismatch alone. Treat findings as review flags and allow for timing differences, amendments, credit notes, and applicable tax rules.

### Module 4: Audit Anomaly Analytics
Target: CA firms, internal audit teams, and BFSI finance operations.

- Flag duplicate payments, unusual journal entries, round-number transactions, unexpected vendor activity, and outlier amounts.
- Support configurable rules and statistical anomaly detection.
- Explain why each transaction was flagged and show the underlying data.
- Let reviewers mark findings as valid, dismissed, or requiring further investigation.
- Never label a transaction as fraud solely because it is anomalous.

### Module 5: Wealth and BFSI Analytics
Target: Wealth managers, financial advisory firms, and suitable BFSI teams.

Build this as a separate, configurable module rather than mixing it with CA workflows.

- Analyse portfolio holdings, asset allocation, concentration, returns, and benchmark comparisons where reliable data is available.
- Support portfolio drift and exposure analysis.
- Provide financial statement and borrower-data analytics for credit-risk review where relevant.
- Maintain source provenance and distinguish calculated metrics from AI-generated explanations.
- Do not provide unsupported investment recommendations or automated credit decisions.

## 4. Shared Analytics Architecture

Build reusable components for:

1. **Data ingestion:** CSV, Excel, structured JSON, and supported PDF tables.
2. **Data validation:** Schema checks, missing values, duplicate rows, invalid dates, and inconsistent totals.
3. **Normalisation:** Standardise financial periods, currency, transaction identifiers, and accounting fields.
4. **Calculation engine:** Use Python/Pandas or SQL for deterministic calculations.
5. **Reconciliation engine:** Configurable matching strategies, tolerances, and exception classifications.
6. **Analytics engine:** Ratios, period comparisons, aggregation, trend analysis, and anomaly detection.
7. **AI explanation layer:** Use the LLM to explain verified analytical results, not to invent financial calculations.
8. **Evidence and provenance:** Link each finding to its source file, row, page, period, and calculation where applicable.
9. **Reporting:** Export structured CSV/Excel and printable PDF reports.
10. **Human review:** Record reviewer decisions, comments, timestamps, and subsequent changes.

## 5. API and User Experience

First inspect the current API conventions. Extend the existing architecture with endpoints equivalent to:

- `POST /analytics/datasets` — upload and register datasets.
- `GET /analytics/datasets/{id}` — inspect dataset status and schema.
- `POST /analytics/financial-statements/analyze` — calculate financial metrics and trends.
- `POST /analytics/reconciliation/run` — run configurable reconciliation.
- `POST /analytics/gst-reconciliation/run` — compare purchase registers with GSTR-2B.
- `POST /analytics/anomalies/run` — identify and explain unusual records.
- `GET /analytics/jobs/{id}` — inspect processing status and results.
- `GET /analytics/reports/{id}` — retrieve a generated report.

These are proposed endpoints. Adapt them to existing routing, authentication, database models, and naming conventions rather than creating duplicate functionality.

The user experience should include:
- Dataset upload and validation summary.
- KPI cards and financial trend charts.
- Filterable transaction and exception tables.
- Finding details with source evidence.
- Review and dismissal controls.
- Report export.

Do not build an elaborate frontend if the existing project is currently API-first. Complete and test the backend first.

## 6. Security and Enterprise Requirements

- Enforce authentication and tenant-level data isolation.
- Validate file types, file sizes, schemas, and malformed input.
- Prevent one firm's users from accessing another firm's datasets or reports.
- Apply role-based permissions to sensitive operations.
- Record auditable processing and review events.
- Protect financial information in logs and error messages.
- Make processing idempotent where possible.
- Handle failures, retries, and partial processing safely.
- Avoid retaining uploaded financial data longer than configured policies allow.
- Do not execute payments, submit tax returns, or make consequential financial decisions autonomously.

## 7. Testing and Evaluation

Create synthetic test datasets with known expected outputs.

Test:
- Missing and malformed fields.
- Duplicate transactions.
- Exact and near matches.
- Different date formats.
- Debit/credit sign inconsistencies.
- Rounding differences.
- Missing periods and amended records.
- Large datasets and repeated uploads.
- Incorrect or incomplete financial statements.
- Tenant isolation and unauthorised access.

For every calculation and reconciliation, verify the result against deterministic expected values. Evaluate false positives, missed exceptions, processing time, and explanation accuracy.

Do not claim production readiness without test evidence.

## 8. Development Strategy

Implement incrementally:

**Step 1:** Inspect the repository and provide an architecture assessment.

**Step 2:** Identify reusable Phase 2 components, existing gaps, dependencies, and required schema changes.

**Step 3:** Recommend the smallest useful MVP. Prioritise financial statement analytics and ledger/bank reconciliation, unless the existing architecture or customer requirements justify another order.

**Step 4:** Implement one module end to end, including validation, calculation, APIs, tests, and report generation.

**Step 5:** Integrate it with existing authentication, document storage, audit logging, and review mechanisms.

**Step 6:** Run tests, document API usage, and provide sample requests, responses, and setup instructions.

Do not implement every module in a single unreviewed change. Work in small, testable increments.

## 9. Expected Deliverables

At the end of each increment, provide:
- Files created and modified.
- Architecture and design decisions.
- Database migrations, if required.
- API documentation and sample payloads.
- Unit and integration test results.
- Known limitations and security considerations.
- Instructions for running and validating the feature locally.

Begin by inspecting the existing codebase. Do not modify files until you have presented a concise implementation plan and identified the first module to build.