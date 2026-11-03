from decimal import Decimal
from typing import List, Dict, Any, Set
from app.models.domain import GSTDiscrepancyCategory, GSTMatchStage, GSTDocType


def classify_match_discrepancies(
    match_dict: Dict[str, Any],
    books_duplicates: Set[Any],
    gstr2b_duplicates: Set[Any],
    tolerances: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Evaluates a matched (or unmatched) pair and generates all applicable discrepancy items.
    Returns list of discrepancy dictionaries ready for DB persistence.
    """
    b = match_dict.get("books_candidate")
    g = match_dict.get("gstr2b_candidate")
    stage = match_dict.get("stage")
    tax_tol = Decimal(str(tolerances.get("tax_diff_max", 1.0)))
    date_tol_days = int(tolerances.get("date_days_diff", 30))

    discrepancies: List[Dict[str, Any]] = []

    # ----------------------------------------------------
    # Case 1: Invalid or Incomplete Record
    # ----------------------------------------------------
    if b and not b.is_valid:
        discrepancies.append({
            "category": GSTDiscrepancyCategory.INVALID_OR_INCOMPLETE_RECORD,
            "books_value": f"{b.inv_raw} ({b.gstin})",
            "gstr2b_value": None,
            "difference": Decimal("0.00"),
            "explanation": f"Purchase Register record contains validation errors: {', '.join(b.record.get('validation_errors') or [])}",
            "suggested_action": "Correct invoice details in ERP/Purchase Register.",
        })

    if g and not g.is_valid:
        discrepancies.append({
            "category": GSTDiscrepancyCategory.INVALID_OR_INCOMPLETE_RECORD,
            "books_value": None,
            "gstr2b_value": f"{g.inv_raw} ({g.gstin})",
            "difference": Decimal("0.00"),
            "explanation": f"GSTR-2B record contains formatting/validation errors: {', '.join(g.record.get('validation_errors') or [])}",
            "suggested_action": "Verify GST portal data or contact supplier.",
        })

    # ----------------------------------------------------
    # Case 2: Books Only
    # ----------------------------------------------------
    if b and not g:
        discrepancies.append({
            "category": GSTDiscrepancyCategory.BOOKS_ONLY,
            "books_value": f"Inv #{b.inv_norm} | Taxable: ₹{b.taxable_value}",
            "gstr2b_value": "Missing in GSTR-2B",
            "difference": b.taxable_value,
            "explanation": f"Invoice #{b.inv_norm} from supplier {b.gstin} is present in Books but missing from GSTR-2B.",
            "suggested_action": "Follow up with vendor to upload invoice in their GSTR-1.",
        })

    # ----------------------------------------------------
    # Case 3: GSTR-2B Only
    # ----------------------------------------------------
    if g and not b:
        discrepancies.append({
            "category": GSTDiscrepancyCategory.GSTR2B_ONLY,
            "books_value": "Missing in Books",
            "gstr2b_value": f"Inv #{g.inv_norm} | Taxable: ₹{g.taxable_value}",
            "difference": g.taxable_value,
            "explanation": f"Invoice #{g.inv_norm} from supplier {g.gstin} appears in GSTR-2B but was not recorded in Purchase Register.",
            "suggested_action": "Verify physical bill / delivery and book purchase in accounting software.",
        })

    # ----------------------------------------------------
    # Case 4: Duplicate Invoices
    # ----------------------------------------------------
    if b and b.id in books_duplicates:
        discrepancies.append({
            "category": GSTDiscrepancyCategory.DUPLICATE_INVOICE,
            "books_value": f"Inv #{b.inv_norm} (Duplicate in Books)",
            "gstr2b_value": None,
            "difference": Decimal("0.00"),
            "explanation": f"Invoice #{b.inv_norm} from supplier {b.gstin} appears more than once in the Purchase Register.",
            "suggested_action": "Check for double booking or review voucher entries.",
        })

    if g and g.id in gstr2b_duplicates:
        discrepancies.append({
            "category": GSTDiscrepancyCategory.DUPLICATE_INVOICE,
            "books_value": None,
            "gstr2b_value": f"Inv #{g.inv_norm} (Duplicate in GSTR-2B)",
            "difference": Decimal("0.00"),
            "explanation": f"Invoice #{g.inv_norm} from supplier {g.gstin} was filed multiple times on the GST portal.",
            "suggested_action": "Vendor may have filed duplicate invoice or amended incorrectly.",
        })

    # ----------------------------------------------------
    # Paired Invoices (b and g both exist)
    # ----------------------------------------------------
    if b and g:
        # Check Document Type Mismatch
        if b.doc_type != g.doc_type:
            discrepancies.append({
                "category": GSTDiscrepancyCategory.CREDIT_DEBIT_NOTE_MISMATCH,
                "books_value": str(b.doc_type.value),
                "gstr2b_value": str(g.doc_type.value),
                "difference": Decimal("0.00"),
                "explanation": f"Document type mismatch: Books has '{b.doc_type.value}' while GSTR-2B has '{g.doc_type.value}'.",
                "suggested_action": "Confirm whether transaction is an Invoice, Credit Note, or Debit Note.",
            })

        # Check Taxable Value Difference
        taxable_diff = b.taxable_value - g.taxable_value
        if abs(taxable_diff) > tax_tol:
            discrepancies.append({
                "category": GSTDiscrepancyCategory.TAXABLE_VALUE_MISMATCH,
                "books_value": f"₹{b.taxable_value}",
                "gstr2b_value": f"₹{g.taxable_value}",
                "difference": taxable_diff,
                "explanation": f"Taxable value mismatch: Books is ₹{b.taxable_value}, GSTR-2B is ₹{g.taxable_value} (Diff: ₹{taxable_diff}).",
                "suggested_action": "Verify bill basic value vs vendor portal filing.",
            })

        # Check IGST Difference
        igst_diff = b.igst - g.igst
        if abs(igst_diff) > tax_tol:
            discrepancies.append({
                "category": GSTDiscrepancyCategory.IGST_MISMATCH,
                "books_value": f"₹{b.igst}",
                "gstr2b_value": f"₹{g.igst}",
                "difference": igst_diff,
                "explanation": f"IGST mismatch: Books has ₹{b.igst}, GSTR-2B has ₹{g.igst} (Diff: ₹{igst_diff}).",
                "suggested_action": "Check place of supply and interstate tax classification.",
            })

        # Check CGST Difference
        cgst_diff = b.cgst - g.cgst
        if abs(cgst_diff) > tax_tol:
            discrepancies.append({
                "category": GSTDiscrepancyCategory.CGST_MISMATCH,
                "books_value": f"₹{b.cgst}",
                "gstr2b_value": f"₹{g.cgst}",
                "difference": cgst_diff,
                "explanation": f"CGST mismatch: Books has ₹{b.cgst}, GSTR-2B has ₹{g.cgst} (Diff: ₹{cgst_diff}).",
                "suggested_action": "Check intrastate tax rate calculation.",
            })

        # Check SGST Difference
        sgst_diff = b.sgst - g.sgst
        if abs(sgst_diff) > tax_tol:
            discrepancies.append({
                "category": GSTDiscrepancyCategory.SGST_MISMATCH,
                "books_value": f"₹{b.sgst}",
                "gstr2b_value": f"₹{g.sgst}",
                "difference": sgst_diff,
                "explanation": f"SGST mismatch: Books has ₹{b.sgst}, GSTR-2B has ₹{g.sgst} (Diff: ₹{sgst_diff}).",
                "suggested_action": "Check intrastate tax rate calculation.",
            })

        # Check Cess Difference
        cess_diff = b.cess - g.cess
        if abs(cess_diff) > tax_tol:
            discrepancies.append({
                "category": GSTDiscrepancyCategory.CESS_MISMATCH,
                "books_value": f"₹{b.cess}",
                "gstr2b_value": f"₹{g.cess}",
                "difference": cess_diff,
                "explanation": f"Cess mismatch: Books has ₹{b.cess}, GSTR-2B has ₹{g.cess} (Diff: ₹{cess_diff}).",
                "suggested_action": "Verify applicable cess rate.",
            })

        # Check Invoice Date Mismatch
        if b.date and g.date:
            days_diff = abs((b.date - g.date).days)
            if days_diff > date_tol_days:
                discrepancies.append({
                    "category": GSTDiscrepancyCategory.INVOICE_DATE_MISMATCH,
                    "books_value": str(b.date),
                    "gstr2b_value": str(g.date),
                    "difference": Decimal(str(days_diff)),
                    "explanation": f"Date mismatch: Books has {b.date}, GSTR-2B has {g.date} ({days_diff} days difference).",
                    "suggested_action": "Verify bill date and relevant tax period.",
                })

        # Check Potential Match Category
        if stage == GSTMatchStage.STAGE_4_POTENTIAL:
            discrepancies.append({
                "category": GSTDiscrepancyCategory.POTENTIAL_MATCH,
                "books_value": f"Inv #{b.inv_norm} ({b.date})",
                "gstr2b_value": f"Inv #{g.inv_norm} ({g.date})",
                "difference": abs(taxable_diff),
                "explanation": match_dict.get("reason", "Potential match identified; please confirm or reject."),
                "suggested_action": "Review source documents and confirm if these invoices represent the same transaction.",
            })

        # If paired and zero discrepancies, it is a clean MATCHED
        if not discrepancies:
            discrepancies.append({
                "category": GSTDiscrepancyCategory.MATCHED,
                "books_value": f"Inv #{b.inv_norm} | ₹{b.taxable_value}",
                "gstr2b_value": f"Inv #{g.inv_norm} | ₹{g.taxable_value}",
                "difference": Decimal("0.00"),
                "explanation": "Matched: Invoice number, date, and tax amounts match within acceptable tolerances.",
                "suggested_action": "No action needed. Ready for ITC claim.",
            })

    return discrepancies
