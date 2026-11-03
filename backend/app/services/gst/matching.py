import datetime
from decimal import Decimal
from typing import List, Dict, Any, Optional, Tuple, Set
from uuid import UUID

from app.models.domain import GSTMatchStage, GSTDocType
from app.services.gst.normalization import strip_all_separators


def levenshtein_ratio(s1: str, s2: str) -> float:
    """Calculate similarity ratio between two strings [0.0 to 1.0]."""
    if not s1 and not s2:
        return 1.0
    if not s1 or not s2:
        return 0.0
    s1, s2 = s1.upper(), s2.upper()
    if s1 == s2:
        return 1.0

    len1, len2 = len(s1), len(s2)
    matrix = [[0] * (len2 + 1) for _ in range(len1 + 1)]

    for i in range(len1 + 1):
        matrix[i][0] = i
    for j in range(len2 + 1):
        matrix[0][j] = j

    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            matrix[i][j] = min(
                matrix[i - 1][j] + 1,        # deletion
                matrix[i][j - 1] + 1,        # insertion
                matrix[i - 1][j - 1] + cost  # substitution
            )

    dist = matrix[len1][len2]
    max_len = max(len1, len2)
    return round(1.0 - (dist / max_len), 4)


class MatchCandidate:
    def __init__(self, record: Dict[str, Any], record_id: Any):
        self.record = record
        self.id = record_id
        self.gstin = record.get("supplier_gstin")
        self.inv_raw = record.get("invoice_number_raw")
        self.inv_norm = record.get("invoice_number_norm")
        self.inv_stripped = strip_all_separators(self.inv_norm or "")
        self.date = record.get("invoice_date")
        self.doc_type = record.get("doc_type", GSTDocType.INV)
        self.taxable_value = record.get("taxable_value", Decimal("0.00"))
        self.igst = record.get("igst", Decimal("0.00"))
        self.cgst = record.get("cgst", Decimal("0.00"))
        self.sgst = record.get("sgst", Decimal("0.00"))
        self.cess = record.get("cess", Decimal("0.00"))
        self.invoice_total = record.get("invoice_total", Decimal("0.00"))
        self.is_valid = record.get("is_valid", True)


def identify_internal_duplicates(candidates: List[MatchCandidate]) -> Set[Any]:
    """
    Find internal duplicate invoices within the same dataset.
    Duplicate defined as: same supplier GSTIN + same normalized invoice number + same doc type.
    """
    seen: Dict[Tuple[str, str, str], List[Any]] = {}
    duplicates = set()

    for c in candidates:
        if not c.gstin or not c.inv_norm:
            continue
        key = (c.gstin, c.inv_norm, str(c.doc_type))
        if key not in seen:
            seen[key] = []
        seen[key].append(c.id)

    for key, ids in seen.items():
        if len(ids) > 1:
            for item_id in ids:
                duplicates.add(item_id)

    return duplicates


def execute_matching_engine(
    books_records: List[Tuple[Any, Dict[str, Any]]],
    gstr2b_records: List[Tuple[Any, Dict[str, Any]]],
    tolerances: Optional[Dict[str, Any]] = None,
) -> Tuple[List[Dict[str, Any]], Set[Any], Set[Any]]:
    """
    4-Stage Deterministic GST Invoice Matching Engine.
    Enforces strict 1-to-1 matching.
    Returns:
    (matches_list, books_duplicate_ids, gstr2b_duplicate_ids)
    """
    if tolerances is None:
        tolerances = {}

    tax_tol = Decimal(str(tolerances.get("tax_diff_max", 1.0)))
    date_tol_days = int(tolerances.get("date_days_diff", 30))

    books = [MatchCandidate(rec, rec_id) for rec_id, rec in books_records]
    gstr2b = [MatchCandidate(rec, rec_id) for rec_id, rec in gstr2b_records]

    books_duplicates = identify_internal_duplicates(books)
    gstr2b_duplicates = identify_internal_duplicates(gstr2b)

    matched_books_ids = set()
    matched_gstr2b_ids = set()
    matches: List[Dict[str, Any]] = []

    # Helper to create match result
    def record_match(b: MatchCandidate, g: MatchCandidate, stage: GSTMatchStage, score: float, reason: str):
        matched_books_ids.add(b.id)
        matched_gstr2b_ids.add(g.id)
        matches.append({
            "books_candidate": b,
            "gstr2b_candidate": g,
            "stage": stage,
            "confidence_score": score,
            "reason": reason,
        })

    # ========================================================
    # STAGE 1: Exact Match
    # Same GSTIN, Same Normalized Invoice No, Same Date, Same Taxable Value (diff <= 0.01), Same DocType
    # ========================================================
    for b in books:
        if b.id in matched_books_ids or not b.gstin or not b.inv_norm:
            continue
        for g in gstr2b:
            if g.id in matched_gstr2b_ids or not g.gstin or not g.inv_norm:
                continue

            if b.doc_type != g.doc_type:
                continue

            if b.gstin == g.gstin and b.inv_norm == g.inv_norm:
                is_date_exact = (b.date is not None and g.date is not None and b.date == g.date)
                taxable_diff = abs(b.taxable_value - g.taxable_value)

                if is_date_exact and taxable_diff <= Decimal("0.01"):
                    record_match(
                        b, g,
                        GSTMatchStage.STAGE_1_EXACT,
                        1.0,
                        "Exact Match: GSTIN, Invoice Number, Date, and Taxable Value match completely."
                    )
                    break

    # ========================================================
    # STAGE 2: Strong Match
    # Same GSTIN, Same Normalized Invoice No, Same DocType, Minor Date difference (<= 30 days) or Tax diff <= ₹1.00
    # ========================================================
    for b in books:
        if b.id in matched_books_ids or not b.gstin or not b.inv_norm:
            continue
        for g in gstr2b:
            if g.id in matched_gstr2b_ids or not g.gstin or not g.inv_norm:
                continue

            if b.doc_type != g.doc_type:
                continue

            if b.gstin == g.gstin and b.inv_norm == g.inv_norm:
                taxable_diff = abs(b.taxable_value - g.taxable_value)
                days_diff = 0
                if b.date and g.date:
                    days_diff = abs((b.date - g.date).days)

                if taxable_diff <= tax_tol or days_diff <= date_tol_days:
                    score = 0.95 if (taxable_diff <= tax_tol and days_diff <= date_tol_days) else 0.90
                    reason = f"Strong Match: GSTIN and Invoice No match; Date diff: {days_diff}d, Taxable diff: ₹{taxable_diff}."
                    record_match(b, g, GSTMatchStage.STAGE_2_STRONG, score, reason)
                    break

    # ========================================================
    # STAGE 3: Flexible Match
    # Same GSTIN, Same Stripped Invoice No (ignoring '/', '-', '_', spaces), Same DocType, Taxable diff <= tax_tol
    # ========================================================
    for b in books:
        if b.id in matched_books_ids or not b.gstin or not b.inv_stripped:
            continue
        for g in gstr2b:
            if g.id in matched_gstr2b_ids or not g.gstin or not g.inv_stripped:
                continue

            if b.doc_type != g.doc_type:
                continue

            if b.gstin == g.gstin and b.inv_stripped == g.inv_stripped:
                taxable_diff = abs(b.taxable_value - g.taxable_value)
                days_diff = 0
                if b.date and g.date:
                    days_diff = abs((b.date - g.date).days)

                if taxable_diff <= (tax_tol * 2) and days_diff <= (date_tol_days * 2):
                    score = 0.85
                    reason = f"Flexible Match: Invoice formatting differences ('{b.inv_norm}' vs '{g.inv_norm}'), Taxable diff: ₹{taxable_diff}."
                    record_match(b, g, GSTMatchStage.STAGE_3_FLEXIBLE, score, reason)
                    break

    # ========================================================
    # STAGE 4: Potential Match (Candidate for CA Review)
    # Same GSTIN, Same DocType:
    # Either Levenshtein similarity on Inv No >= 0.75 OR Same Taxable Value with Partial Inv Match
    # ========================================================
    for b in books:
        if b.id in matched_books_ids or not b.gstin:
            continue

        best_g = None
        best_score = 0.0
        best_reason = ""

        for g in gstr2b:
            if g.id in matched_gstr2b_ids or not g.gstin:
                continue

            if b.doc_type != g.doc_type or b.gstin != g.gstin:
                continue

            inv_sim = levenshtein_ratio(b.inv_norm or "", g.inv_norm or "")
            taxable_diff = abs(b.taxable_value - g.taxable_value)

            # Case A: High invoice string similarity (>= 0.75)
            if inv_sim >= 0.75:
                score = round(0.5 + (inv_sim * 0.3), 2)
                if score > best_score:
                    best_score = score
                    best_g = g
                    best_reason = f"Potential Match: Similar invoice numbers ('{b.inv_norm}' ~ '{g.inv_norm}', sim={inv_sim:.2f})."

            # Case B: Taxable values match within ₹1.00 and invoice numbers share a common suffix/prefix
            elif taxable_diff <= tax_tol and b.inv_stripped and g.inv_stripped:
                if b.inv_stripped in g.inv_stripped or g.inv_stripped in b.inv_stripped:
                    score = 0.70
                    if score > best_score:
                        best_score = score
                        best_g = g
                        best_reason = f"Potential Match: Identical taxable value ₹{b.taxable_value} with overlapping invoice numbers ('{b.inv_norm}' vs '{g.inv_norm}')."

        if best_g and best_score >= 0.65:
            record_match(b, best_g, GSTMatchStage.STAGE_4_POTENTIAL, best_score, best_reason)

    # ========================================================
    # UNMATCHED RECORDS:
    # Books Only (missing in GSTR-2B)
    # ========================================================
    for b in books:
        if b.id not in matched_books_ids:
            matches.append({
                "books_candidate": b,
                "gstr2b_candidate": None,
                "stage": None,
                "confidence_score": 0.0,
                "reason": "Invoice exists in Purchase Register but is missing from GSTR-2B.",
            })

    # GSTR-2B Only (missing in Books)
    for g in gstr2b:
        if g.id not in matched_gstr2b_ids:
            matches.append({
                "books_candidate": None,
                "gstr2b_candidate": g,
                "stage": None,
                "confidence_score": 0.0,
                "reason": "Invoice appears on the GST Portal (GSTR-2B) but is not recorded in Purchase Register.",
            })

    return matches, books_duplicates, gstr2b_duplicates
