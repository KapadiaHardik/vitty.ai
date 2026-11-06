import re
import datetime
from decimal import Decimal, InvalidOperation
from typing import Dict, Any, List, Optional, Tuple
from app.models.domain import GSTDocType

GSTIN_REGEX = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$")


def normalize_gstin(val: Any) -> Tuple[Optional[str], Optional[str]]:
    """
    Returns (normalized_gstin, error_msg)
    """
    if val is None:
        return None, "GSTIN is missing"
    cleaned = str(val).strip().upper().replace(" ", "")
    if not cleaned:
        return None, "GSTIN is empty"
    if not GSTIN_REGEX.match(cleaned):
        return cleaned, f"Invalid GSTIN format: '{cleaned}'"
    return cleaned, None


def normalize_invoice_number(val: Any) -> Tuple[Optional[str], Optional[str]]:
    """
    Normalizes invoice number:
    - Uppercase
    - Strips leading/trailing spaces
    - Collapses multiple internal spaces
    - Normalizes leading zeros: e.g. 000123 -> 123, INV/0045 -> INV/45
    Returns (raw_value, normalized_value)
    """
    if val is None:
        return None, None
    raw = str(val).strip()
    if not raw:
        return None, None

    # Step 1: Uppercase & collapse spaces
    norm = re.sub(r"\s+", " ", raw.upper())

    # Step 2: Strip leading zeros from numeric components where appropriate
    # e.g., '00123' -> '123' or 'INV/0042' -> 'INV/42'
    def strip_zero(m):
        prefix = m.group(1)
        digits = m.group(2)
        stripped = digits.lstrip("0")
        return prefix + (stripped if stripped else "0")

    norm = re.sub(r"(^|[\/\-_#\s])0+([1-9][0-9]*)", r"\1\2", norm)
    return raw, norm


def strip_all_separators(norm_inv: str) -> str:
    """
    Removes common formatting separators (/, -, _, space, #) for flexible matching.
    """
    if not norm_inv:
        return ""
    return re.sub(r"[\/\-_#\s]+", "", norm_inv)


def parse_date(val: Any) -> Tuple[Optional[datetime.date], Optional[str]]:
    """
    Parses various date formats to datetime.date.
    Supports Excel serial dates, DD/MM/YYYY, YYYY-MM-DD, DD-MMM-YYYY, etc.
    """
    if val is None:
        return None, "Date is missing"
    if isinstance(val, datetime.date):
        if isinstance(val, datetime.datetime):
            return val.date(), None
        return val, None

    # Check for Excel serial number
    if isinstance(val, (int, float)):
        try:
            # Excel base date is 1899-12-30 (handling leap year bug)
            base = datetime.date(1899, 12, 30)
            return base + datetime.timedelta(days=int(val)), None
        except Exception:
            return None, f"Invalid Excel date number: {val}"

    val_str = str(val).strip()
    if not val_str:
        return None, "Date string is empty"

    # Known formats
    formats = [
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y-%m-%d",
        "%d-%b-%Y",
        "%d-%B-%Y",
        "%d/%m/%y",
        "%d-%m-%y",
        "%Y/%m/%d",
        "%d.%m.%Y",
    ]
    for fmt in formats:
        try:
            dt = datetime.datetime.strptime(val_str, fmt)
            return dt.date(), None
        except ValueError:
            continue

    return None, f"Could not parse date: '{val_str}'"


def parse_decimal(val: Any, default_val: str = "0.00") -> Tuple[Decimal, Optional[str]]:
    """
    Deterministic decimal parsing for monetary amounts.
    Prevents binary float inaccuracies.
    """
    if val is None:
        return Decimal(default_val), None
    if isinstance(val, (int, float, Decimal)):
        # Format via str to preserve exact representation
        try:
            d = Decimal(str(val)).quantize(Decimal("0.01"))
            return d, None
        except InvalidOperation:
            return Decimal(default_val), f"Invalid numeric amount: {val}"

    s = str(val).strip()
    if not s:
        return Decimal(default_val), None

    # Handle accounting brackets: e.g. (100.50) -> -100.50
    is_negative = False
    if s.startswith("(") and s.endswith(")"):
        is_negative = True
        s = s[1:-1].strip()

    # Clean currency symbols, commas, spaces
    clean_s = re.sub(r"[₹$,\s]", "", s)
    if clean_s.startswith("-"):
        is_negative = True
        clean_s = clean_s[1:]

    try:
        amt = Decimal(clean_s).quantize(Decimal("0.01"))
        if is_negative:
            amt = -amt
        return amt, None
    except InvalidOperation:
        return Decimal(default_val), f"Could not parse decimal currency: '{val}'"


def normalize_document_type(val: Any, total_amt: Decimal) -> GSTDocType:
    """
    Standardize document type to INV, CRN, or DBN.
    """
    if val is not None:
        s = str(val).strip().upper()
        if any(keyword in s for keyword in ["CREDIT", "CRN", "C/N", "C.N"]):
            return GSTDocType.CRN
        if any(keyword in s for keyword in ["DEBIT", "DBN", "D/N", "D.N"]):
            return GSTDocType.DBN
        if "INV" in s or "BILL" in s:
            return GSTDocType.INV

    # If amount is strictly negative, it's typically a Credit Note
    if total_amt < 0:
        return GSTDocType.CRN

    return GSTDocType.INV


def normalize_record(raw_record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize extracted record into clean GST format and collect validation issues.
    """
    errors: List[str] = []

    # 1. Supplier GSTIN
    gstin, gstin_err = normalize_gstin(raw_record.get("supplier_gstin"))
    if gstin_err:
        errors.append(gstin_err)

    # 2. Supplier Name
    raw_name = raw_record.get("supplier_name")
    supplier_name = str(raw_name).strip()[:255] if raw_name else None

    # 3. Invoice Number
    inv_raw, inv_norm = normalize_invoice_number(raw_record.get("invoice_number"))
    if not inv_norm:
        errors.append("Invoice number is missing or empty")

    inv_raw = inv_raw[:100] if inv_raw else None
    inv_norm = inv_norm[:100] if inv_norm else None

    # 4. Invoice Date
    inv_date, date_err = parse_date(raw_record.get("invoice_date"))
    if date_err:
        errors.append(date_err)

    # 5. Financial Amounts (Decimal)
    taxable_val, tax_err = parse_decimal(raw_record.get("taxable_value"))
    if tax_err:
        errors.append(tax_err)

    igst, igst_err = parse_decimal(raw_record.get("igst"))
    if igst_err:
        errors.append(igst_err)

    cgst, cgst_err = parse_decimal(raw_record.get("cgst"))
    if cgst_err:
        errors.append(cgst_err)

    sgst, sgst_err = parse_decimal(raw_record.get("sgst"))
    if sgst_err:
        errors.append(sgst_err)

    cess, cess_err = parse_decimal(raw_record.get("cess"))
    if cess_err:
        errors.append(cess_err)

    # Invoice Total: if provided use it, else calculate from components
    raw_total = raw_record.get("invoice_total")
    if raw_total is not None and str(raw_total).strip():
        inv_total, tot_err = parse_decimal(raw_total)
        if tot_err:
            errors.append(tot_err)
    else:
        inv_total = taxable_val + igst + cgst + sgst + cess

    # 6. Doc Type
    doc_type = normalize_document_type(raw_record.get("doc_type"), inv_total)

    # 7. POS
    pos_val = raw_record.get("pos")
    pos = str(pos_val).strip()[:100] if pos_val else None

    is_valid = len(errors) == 0

    return {
        "supplier_gstin": gstin,
        "supplier_name": supplier_name,
        "invoice_number_raw": inv_raw,
        "invoice_number_norm": inv_norm,
        "invoice_date": inv_date,
        "doc_type": doc_type,
        "taxable_value": taxable_val,
        "igst": igst,
        "cgst": cgst,
        "sgst": sgst,
        "cess": cess,
        "invoice_total": inv_total,
        "pos": pos,
        "source_file": raw_record.get("_source_file"),
        "source_sheet": raw_record.get("_source_sheet"),
        "source_row_index": raw_record.get("_source_row_index"),
        "raw_record_data": raw_record.get("_raw_record"),
        "is_valid": is_valid,
        "validation_errors": errors if errors else None,
    }
