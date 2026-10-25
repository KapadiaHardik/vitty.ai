"""
Batch Verification Test Runner for Vitty.ai Phase 2 Synthetic Test Suite.
Executes automated audit verification across all 60 synthetic invoice & PO cases,
evaluates discrepancy detection against expected ground truth, and outputs
a detailed markdown report and audit metrics.
"""

import os
import sys
import json
import time

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add backend directory to sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.workflows.extraction import extract_text_from_file, _heuristic_fallback_extraction
from app.workflows.validation import validate_invoice
from app.workflows.comparison import compare_documents
from app.models.domain import DiscrepancyType

MANIFEST_PATH = os.path.join(BASE_DIR, "test_dataset", "manifest.json")
INVOICE_DIR = os.path.join(BASE_DIR, "test_dataset", "invoices")
PO_DIR = os.path.join(BASE_DIR, "test_dataset", "purchase_orders")
REPORT_PATH = os.path.join(BASE_DIR, "test_dataset", "test_report.md")


def run_all_synthetic_tests():
    if not os.path.exists(MANIFEST_PATH):
        print(f"Error: Manifest not found at {MANIFEST_PATH}. Run generate_synthetic_cases.py first.")
        return

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    test_cases = manifest["cases"]
    print(f"\n=================================================================")
    print(f"  Vitty.ai Phase 2 Engine - Automated Test Suite ({len(test_cases)} Cases)")
    print(f"=================================================================\n")

    seen_invoice_numbers = set()
    results = []
    category_stats = {}

    start_time = time.time()

    for tc in test_cases:
        case_id = tc["case_id"]
        category = tc["category"]
        inv_fn = tc["invoice_file"]
        po_fn = tc.get("po_file")
        has_po = tc.get("has_po", False)
        expected_types = [t.upper() for t in tc.get("expected_findings", [])]

        if category not in category_stats:
            category_stats[category] = {"total": 0, "passed": 0, "failed": 0}
        category_stats[category]["total"] += 1

        # Step 1: Read Invoice Text & Extract
        inv_path = os.path.join(INVOICE_DIR, inv_fn)
        inv_text = extract_text_from_file(inv_path)
        inv_data = _heuristic_fallback_extraction(inv_text, is_invoice=True)

        # Step 2: Read PO Text & Extract if present
        po_data = None
        if has_po and po_fn:
            po_path = os.path.join(PO_DIR, po_fn)
            po_text = extract_text_from_file(po_path)
            po_data = _heuristic_fallback_extraction(po_text, is_invoice=False)

        # Step 3: Run Validation and Comparison
        findings = []

        # 3a: Invoice internal validation (missing fields + arithmetic)
        val_findings = validate_invoice(inv_data)
        findings.extend(val_findings)

        # 3b: 2-way comparison with PO
        if po_data:
            comp_findings = compare_documents(inv_data, po_data)
            findings.extend(comp_findings)

        # 3c: Duplicate invoice check
        inv_num = inv_data.get("invoice_number")
        if inv_num:
            if inv_num in seen_invoice_numbers:
                findings.append({
                    "type": DiscrepancyType.DUPLICATE_INVOICE,
                    "field": "invoice_number",
                    "explanation": f"Duplicate invoice: #{inv_num} was processed previously."
                })
            else:
                seen_invoice_numbers.add(inv_num)

        actual_types = [f["type"].value.upper() if hasattr(f["type"], "value") else str(f["type"]).upper() for f in findings]

        # Evaluate correctness
        # For clean cases, expected_types is empty and actual_types must be empty
        # For discrepancy cases, all expected discrepancy types must be detected
        if len(expected_types) == 0:
            is_pass = len(actual_types) == 0
        else:
            # Check if all expected findings are in actual findings
            is_pass = all(exp in actual_types for exp in expected_types)

        if is_pass:
            category_stats[category]["passed"] += 1
            status_icon = "PASS"
        else:
            category_stats[category]["failed"] += 1
            status_icon = "FAIL"

        results.append({
            "case_id": case_id,
            "category": category,
            "status": "PASS" if is_pass else "FAIL",
            "invoice_file": inv_fn,
            "po_file": po_fn,
            "expected_findings": expected_types,
            "actual_findings": actual_types,
            "findings_details": [f.get("explanation") for f in findings],
            "description": tc["description"]
        })

        exp_str = ", ".join(expected_types) if expected_types else "NONE (CLEAN)"
        act_str = ", ".join(actual_types) if actual_types else "NONE (CLEAN)"
        print(f"[{status_icon}] {case_id} ({category:<20}) | Exp: {exp_str:<25} | Act: {act_str}")

    elapsed_time = round(time.time() - start_time, 2)
    total_cases = len(results)
    total_passed = sum(1 for r in results if r["status"] == "PASS")
    total_failed = total_cases - total_passed
    accuracy = round((total_passed / total_cases) * 100, 1)

    print(f"\n=================================================================")
    print(f"  TEST EXECUTION SUMMARY: {total_passed}/{total_cases} Passed ({accuracy}%) in {elapsed_time}s")
    print(f"=================================================================\n")

    # Generate Markdown Report
    report_lines = [
        "# Vitty.ai Phase 2 Verification Engine - Synthetic Test Suite Report",
        f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}  ",
        f"**Total Test Cases:** {total_cases}  ",
        f"**Execution Time:** {elapsed_time} seconds  ",
        f"**Overall Accuracy:** **{accuracy}%** ({total_passed}/{total_cases} passed)  \n",
        "## 1. Category Breakdown\n",
        "| Category | Total | Passed | Failed | Success Rate |",
        "|---|---|---|---|---|",
    ]

    for cat, stats in category_stats.items():
        rate = round((stats["passed"] / stats["total"]) * 100, 1) if stats["total"] > 0 else 0
        report_lines.append(f"| **{cat}** | {stats['total']} | {stats['passed']} | {stats['failed']} | **{rate}%** |")

    report_lines.extend([
        "\n## 2. Test Case Detail Log\n",
        "| Case ID | Category | Status | Expected Findings | Actual Detected | Description |",
        "|---|---|---|---|---|---|",
    ])

    for r in results:
        status_badge = "🟢 PASS" if r["status"] == "PASS" else "🔴 FAIL"
        exp_disp = "<br>".join(r["expected_findings"]) if r["expected_findings"] else "*None (Clean)*"
        act_disp = "<br>".join(r["actual_findings"]) if r["actual_findings"] else "*None (Clean)*"
        report_lines.append(f"| `{r['case_id']}` | `{r['category']}` | {status_badge} | {exp_disp} | {act_disp} | {r['description']} |")

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    print(f"Detailed Markdown report generated at: {REPORT_PATH}\n")
    return accuracy


if __name__ == "__main__":
    run_all_synthetic_tests()
