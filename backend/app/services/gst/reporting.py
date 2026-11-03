import io
from decimal import Decimal
from typing import List, Dict, Any, Optional
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from app.models.domain import (
    GSTReconciliationRun,
    GSTInvoiceMatch,
    GSTDiscrepancyCategory,
    GSTReviewAudit,
)


def create_header_style():
    font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")  # Navy blue
    alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    thin_border = Border(
        left=Side(style="thin", color="D1D5DB"),
        right=Side(style="thin", color="D1D5DB"),
        top=Side(style="thin", color="D1D5DB"),
        bottom=Side(style="thin", color="D1D5DB"),
    )
    return font, fill, alignment, thin_border


def style_worksheet(ws, headers: List[str]):
    font, fill, alignment, border = create_header_style()
    ws.append(headers)
    ws.row_dimensions[1].height = 28

    for col_idx in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.font = font
        cell.fill = fill
        cell.alignment = alignment
        cell.border = border

    # Auto-adjust column widths
    for col in ws.columns:
        col_letter = get_column_letter(col[0].column)
        max_len = 0
        for cell in col:
            val_str = str(cell.value or "")
            if len(val_str) > max_len:
                max_len = len(val_str)
        ws.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 40)


def generate_reconciliation_excel_report(
    run: GSTReconciliationRun,
    matches: List[GSTInvoiceMatch],
    audit_logs: List[GSTReviewAudit],
    metrics: Dict[str, Any],
) -> io.BytesIO:
    """
    Build 9-tab downloadable Excel report using openpyxl.
    """
    wb = openpyxl.Workbook()
    # Remove default sheet
    wb.remove(wb.active)

    # ----------------------------------------------------
    # Sheet 1: Summary
    # ----------------------------------------------------
    ws_sum = wb.create_sheet(title="Summary")
    ws_sum.column_dimensions["A"].width = 30
    ws_sum.column_dimensions["B"].width = 25
    ws_sum.column_dimensions["C"].width = 25

    title_font = Font(name="Calibri", size=16, bold=True, color="1E3A8A")
    sec_font = Font(name="Calibri", size=12, bold=True, color="111827")
    bold_font = Font(name="Calibri", size=11, bold=True)

    ws_sum.append(["Vitty.ai — GST Reconciliation Report"])
    ws_sum.cell(row=1, column=1).font = title_font
    ws_sum.append([f"Company GSTIN: {run.company_gstin} | Tax Period: {run.tax_period}"])
    ws_sum.append([])

    ws_sum.append(["Metric", "Count", "Notes"])
    ws_sum.cell(row=4, column=1).font = sec_font
    ws_sum.cell(row=4, column=2).font = sec_font
    ws_sum.cell(row=4, column=3).font = sec_font

    ws_sum.append(["Total Books Records", metrics.get("total_books_records", 0), "Invoices in Purchase Register"])
    ws_sum.append(["Total GSTR-2B Records", metrics.get("total_gstr2b_records", 0), "Invoices on GST Portal"])
    ws_sum.append(["Fully Matched", metrics.get("matched_count", 0), "Clean 1-to-1 matches"])
    ws_sum.append(["Books Only (Missing in 2B)", metrics.get("books_only_count", 0), "Risk of ITC Disallowance"])
    ws_sum.append(["GSTR-2B Only (Missing in Books)", metrics.get("gstr2b_only_count", 0), "Unclaimed ITC / Unbooked"])
    ws_sum.append(["Taxable Value Mismatches", metrics.get("taxable_mismatch_count", 0), "Rate or basic amount variances"])
    ws_sum.append(["Tax Component Mismatches", metrics.get("tax_mismatch_count", 0), "IGST / CGST / SGST / Cess variances"])
    ws_sum.append(["Duplicate Invoices", metrics.get("duplicate_count", 0), "Internal duplicates identified"])
    ws_sum.append(["Potential Matches", metrics.get("potential_match_count", 0), "Pending CA confirmation"])
    ws_sum.append(["Invalid / Incomplete", metrics.get("invalid_record_count", 0), "Format / missing field errors"])
    ws_sum.append([])

    ws_sum.append(["Financial Summary", "Books Total (₹)", "GSTR-2B Total (₹)", "Variance (₹)"])
    r_fin = ws_sum.max_row
    for c in range(1, 5):
        ws_sum.cell(row=r_fin, column=c).font = sec_font

    ws_sum.append(["Taxable Value", metrics.get("total_books_taxable", 0.0), metrics.get("total_gstr2b_taxable", 0.0), metrics.get("diff_taxable", 0.0)])
    ws_sum.append(["Integrated Tax (IGST)", metrics.get("total_books_igst", 0.0), metrics.get("total_gstr2b_igst", 0.0), metrics.get("diff_igst", 0.0)])
    ws_sum.append(["Central Tax (CGST)", metrics.get("total_books_cgst", 0.0), metrics.get("total_gstr2b_cgst", 0.0), metrics.get("diff_cgst", 0.0)])
    ws_sum.append(["State Tax (SGST)", metrics.get("total_books_sgst", 0.0), metrics.get("total_gstr2b_sgst", 0.0), metrics.get("diff_sgst", 0.0)])
    ws_sum.append(["Cess", metrics.get("total_books_cess", 0.0), metrics.get("total_gstr2b_cess", 0.0), metrics.get("diff_cess", 0.0)])

    # ----------------------------------------------------
    # Sheet 2: Matched Invoices
    # ----------------------------------------------------
    ws_matched = wb.create_sheet(title="Matched Invoices")
    headers_matched = [
        "Supplier GSTIN", "Supplier Name", "Invoice No (Books)", "Invoice No (2B)",
        "Date (Books)", "Date (2B)", "Taxable Value (₹)", "IGST (₹)", "CGST (₹)", "SGST (₹)", "Total (₹)",
        "Match Stage", "Confidence", "Source (Books)", "Source (2B)"
    ]
    style_worksheet(ws_matched, headers_matched)

    # ----------------------------------------------------
    # Sheet 3: Books Only
    # ----------------------------------------------------
    ws_books = wb.create_sheet(title="Books Only")
    headers_books = [
        "Supplier GSTIN", "Supplier Name", "Invoice No", "Date", "Doc Type",
        "Taxable Value (₹)", "IGST (₹)", "CGST (₹)", "SGST (₹)", "Total (₹)",
        "Source File", "Sheet", "Row", "Explanation", "Suggested Action"
    ]
    style_worksheet(ws_books, headers_books)

    # ----------------------------------------------------
    # Sheet 4: GSTR-2B Only
    # ----------------------------------------------------
    ws_2b = wb.create_sheet(title="GSTR-2B Only")
    headers_2b = [
        "Supplier GSTIN", "Supplier Name", "Invoice No", "Date", "Doc Type",
        "Taxable Value (₹)", "IGST (₹)", "CGST (₹)", "SGST (₹)", "Total (₹)",
        "Source File", "Sheet", "Row", "Explanation", "Suggested Action"
    ]
    style_worksheet(ws_2b, headers_2b)

    # ----------------------------------------------------
    # Sheet 5: Tax Mismatches
    # ----------------------------------------------------
    ws_tax = wb.create_sheet(title="Tax Mismatches")
    headers_tax = [
        "Supplier GSTIN", "Invoice No", "Category", "Books Value", "GSTR-2B Value",
        "Difference (₹)", "Explanation", "Suggested Action", "Review Status", "Reviewer Notes"
    ]
    style_worksheet(ws_tax, headers_tax)

    # ----------------------------------------------------
    # Sheet 6: Duplicate Invoices
    # ----------------------------------------------------
    ws_dup = wb.create_sheet(title="Duplicate Invoices")
    headers_dup = [
        "Dataset", "Supplier GSTIN", "Invoice No", "Date", "Taxable Value (₹)",
        "Source File", "Row", "Explanation"
    ]
    style_worksheet(ws_dup, headers_dup)

    # ----------------------------------------------------
    # Sheet 7: Potential Matches
    # ----------------------------------------------------
    ws_pot = wb.create_sheet(title="Potential Matches")
    headers_pot = [
        "Supplier GSTIN", "Books Inv No", "2B Inv No", "Books Date", "2B Date",
        "Books Taxable", "2B Taxable", "Confidence Score", "Reason", "Review Status"
    ]
    style_worksheet(ws_pot, headers_pot)

    # ----------------------------------------------------
    # Sheet 8: Invalid Records
    # ----------------------------------------------------
    ws_inv = wb.create_sheet(title="Invalid Records")
    headers_inv = [
        "Dataset", "Supplier GSTIN", "Invoice No", "Source File", "Sheet", "Row", "Validation Errors"
    ]
    style_worksheet(ws_inv, headers_inv)

    # ----------------------------------------------------
    # Sheet 9: Review History
    # ----------------------------------------------------
    ws_rev = wb.create_sheet(title="Review History")
    headers_rev = [
        "Timestamp", "User ID", "Action", "Previous Status", "New Status", "Comments"
    ]
    style_worksheet(ws_rev, headers_rev)

    # Populate data into the respective sheets
    for m in matches:
        b = m.books_invoice
        g = m.gstr2b_invoice
        discs = m.discrepancies or []

        # Sheet 2: Matched
        if any(d.category == GSTDiscrepancyCategory.MATCHED for d in discs):
            ws_matched.append([
                b.supplier_gstin if b else (g.supplier_gstin if g else ""),
                b.supplier_name if b else (g.supplier_name if g else ""),
                b.invoice_number_norm if b else "",
                g.invoice_number_norm if g else "",
                str(b.invoice_date) if b and b.invoice_date else "",
                str(g.invoice_date) if g and g.invoice_date else "",
                float(b.taxable_value) if b else (float(g.taxable_value) if g else 0.0),
                float(b.igst) if b else (float(g.igst) if g else 0.0),
                float(b.cgst) if b else (float(g.cgst) if g else 0.0),
                float(b.sgst) if b else (float(g.sgst) if g else 0.0),
                float(b.invoice_total) if b else (float(g.invoice_total) if g else 0.0),
                m.match_stage.value if m.match_stage else "",
                m.confidence_score,
                f"{b.source_file} (R:{b.source_row_index})" if b else "",
                f"{g.source_file} (R:{g.source_row_index})" if g else "",
            ])

        # Sheet 3: Books Only
        if b and not g:
            d_item = next((d for d in discs if d.category == GSTDiscrepancyCategory.BOOKS_ONLY), None)
            ws_books.append([
                b.supplier_gstin, b.supplier_name, b.invoice_number_norm, str(b.invoice_date or ""),
                b.doc_type.value, float(b.taxable_value), float(b.igst), float(b.cgst), float(b.sgst),
                float(b.invoice_total), b.source_file, b.source_sheet, b.source_row_index,
                d_item.explanation if d_item else "", d_item.suggested_action if d_item else ""
            ])

        # Sheet 4: GSTR-2B Only
        if g and not b:
            d_item = next((d for d in discs if d.category == GSTDiscrepancyCategory.GSTR2B_ONLY), None)
            ws_2b.append([
                g.supplier_gstin, g.supplier_name, g.invoice_number_norm, str(g.invoice_date or ""),
                g.doc_type.value, float(g.taxable_value), float(g.igst), float(g.cgst), float(g.sgst),
                float(g.invoice_total), g.source_file, g.source_sheet, g.source_row_index,
                d_item.explanation if d_item else "", d_item.suggested_action if d_item else ""
            ])

        # Sheet 5: Tax Mismatches & Date Mismatches
        tax_discs = [d for d in discs if d.category in [
            GSTDiscrepancyCategory.TAXABLE_VALUE_MISMATCH,
            GSTDiscrepancyCategory.IGST_MISMATCH,
            GSTDiscrepancyCategory.CGST_MISMATCH,
            GSTDiscrepancyCategory.SGST_MISMATCH,
            GSTDiscrepancyCategory.CESS_MISMATCH,
            GSTDiscrepancyCategory.INVOICE_DATE_MISMATCH,
        ]]
        for td in tax_discs:
            ws_tax.append([
                b.supplier_gstin if b else (g.supplier_gstin if g else ""),
                b.invoice_number_norm if b else (g.invoice_number_norm if g else ""),
                td.category.value,
                td.books_value,
                td.gstr2b_value,
                float(td.difference) if td.difference else 0.0,
                td.explanation,
                td.suggested_action,
                td.review_status.value,
                td.reviewer_notes or "",
            ])

        # Sheet 6: Duplicate Invoices
        dup_discs = [d for d in discs if d.category == GSTDiscrepancyCategory.DUPLICATE_INVOICE]
        for dd in dup_discs:
            dataset_name = "Purchase Register" if "Books" in (dd.books_value or "") else "GSTR-2B"
            inv_obj = b if dataset_name == "Purchase Register" else g
            ws_dup.append([
                dataset_name,
                inv_obj.supplier_gstin if inv_obj else "",
                inv_obj.invoice_number_norm if inv_obj else "",
                str(inv_obj.invoice_date or "") if inv_obj else "",
                float(inv_obj.taxable_value) if inv_obj else 0.0,
                inv_obj.source_file if inv_obj else "",
                inv_obj.source_row_index if inv_obj else "",
                dd.explanation,
            ])

        # Sheet 7: Potential Matches
        pot_discs = [d for d in discs if d.category == GSTDiscrepancyCategory.POTENTIAL_MATCH]
        for pd in pot_discs:
            ws_pot.append([
                b.supplier_gstin if b else (g.supplier_gstin if g else ""),
                b.invoice_number_norm if b else "",
                g.invoice_number_norm if g else "",
                str(b.invoice_date or "") if b else "",
                str(g.invoice_date or "") if g else "",
                float(b.taxable_value) if b else 0.0,
                float(g.taxable_value) if g else 0.0,
                m.confidence_score,
                pd.explanation,
                pd.review_status.value,
            ])

        # Sheet 8: Invalid Records
        inv_discs = [d for d in discs if d.category == GSTDiscrepancyCategory.INVALID_OR_INCOMPLETE_RECORD]
        for idisc in inv_discs:
            is_b = idisc.books_value is not None
            inv_obj = b if is_b else g
            ws_inv.append([
                "Purchase Register" if is_b else "GSTR-2B",
                inv_obj.supplier_gstin if inv_obj else "",
                inv_obj.invoice_number_raw if inv_obj else "",
                inv_obj.source_file if inv_obj else "",
                inv_obj.source_sheet if inv_obj else "",
                inv_obj.source_row_index if inv_obj else "",
                "; ".join(inv_obj.validation_errors or []) if inv_obj and inv_obj.validation_errors else idisc.explanation,
            ])

    # Sheet 9: Review History
    for log in audit_logs:
        ws_rev.append([
            str(log.timestamp),
            str(log.user_id),
            log.action,
            log.previous_state or "",
            log.new_state or "",
            log.comment or "",
        ])

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output
