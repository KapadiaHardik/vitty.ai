import os
import csv
import re
import logging
from typing import Dict, Any, List, Tuple, Optional
import openpyxl

from app.services.gst.constants import STANDARD_FIELDS, MANDATORY_FIELDS, COLUMN_ALIASES

logger = logging.getLogger(__name__)


def clean_header(header: Any) -> str:
    """Normalize header string for matching."""
    if header is None:
        return ""
    h = str(header).strip().lower()
    h = re.sub(r"[\r\n\t_]+", " ", h)
    h = re.sub(r"\s+", " ", h)
    return h.strip()


def detect_header_row_in_sheet(rows: List[List[Any]], max_scan: int = 15) -> int:
    """
    Find which row contains the table headers.
    GSTR-2B or ERP exports often have title metadata in the top 1-5 rows.
    """
    best_row_idx = 0
    max_matches = 0

    all_alias_keywords = set()
    for aliases in COLUMN_ALIASES.values():
        for a in aliases:
            all_alias_keywords.add(clean_header(a))

    for idx, row in enumerate(rows[:max_scan]):
        row_str_cells = [clean_header(cell) for cell in row if cell is not None and str(cell).strip()]
        matches = 0
        for cell in row_str_cells:
            if any(alias in cell or cell in alias for alias in all_alias_keywords):
                matches += 1
        if matches > max_matches and matches >= 2:
            max_matches = matches
            best_row_idx = idx

    return best_row_idx


def auto_map_columns(raw_headers: List[str]) -> Dict[str, str]:
    """
    Map standard GST fields to actual headers found in the file.
    Returns: { standard_field_name: raw_header_name }
    """
    cleaned_headers = [(raw, clean_header(raw)) for raw in raw_headers if raw]
    mapping: Dict[str, str] = {}
    used_raw_headers = set()

    for std_field, aliases in COLUMN_ALIASES.items():
        matched_raw = None
        # 1. Exact alias match
        for alias in aliases:
            clean_alias = clean_header(alias)
            for raw, cln in cleaned_headers:
                if cln == clean_alias and raw not in used_raw_headers:
                    matched_raw = raw
                    break
            if matched_raw:
                break

        # 2. Substring match if exact match wasn't found
        if not matched_raw:
            for alias in aliases:
                clean_alias = clean_header(alias)
                for raw, cln in cleaned_headers:
                    if (clean_alias in cln or cln in clean_alias) and raw not in used_raw_headers:
                        # Avoid matching 'taxable' to 'igst' or 'cgst'
                        if std_field == "taxable_value" and ("igst" in cln or "cgst" in cln or "sgst" in cln or "cess" in cln):
                            continue
                        matched_raw = raw
                        break
                if matched_raw:
                    break

        if matched_raw:
            mapping[std_field] = matched_raw
            used_raw_headers.add(matched_raw)

    return mapping


def read_excel_rows(file_path: str, sheet_name: Optional[str] = None) -> Tuple[List[str], str, List[List[Any]]]:
    """Read all rows from an Excel file using openpyxl."""
    wb = openpyxl.load_workbook(file_path, data_only=True, read_only=True)
    available_sheets = wb.sheetnames
    target_sheet = sheet_name if sheet_name and sheet_name in available_sheets else available_sheets[0]
    ws = wb[target_sheet]

    rows = []
    for row in ws.iter_rows(values_only=True):
        rows.append(list(row))
    wb.close()
    return available_sheets, target_sheet, rows


def read_csv_rows(file_path: str) -> Tuple[List[str], str, List[List[Any]]]:
    """Read all rows from a CSV file with automatic encoding detection."""
    encodings = ["utf-8-sig", "utf-8", "latin-1", "cp1252"]
    content = None
    for enc in encodings:
        try:
            with open(file_path, "r", encoding=enc) as f:
                reader = csv.reader(f)
                rows = [row for row in reader]
                content = rows
                break
        except Exception:
            continue

    if content is None:
        raise ValueError(f"Could not read CSV file {file_path} with supported encodings.")

    return ["Sheet1"], "Sheet1", content


def get_file_preview(file_path: str, sheet_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract sheets, auto-detect header, generate suggested mapping and preview top rows.
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext in [".xlsx", ".xlsm", ".xltx", ".xltm"]:
        sheets, active_sheet, all_rows = read_excel_rows(file_path, sheet_name)
    elif ext in [".csv", ".txt"]:
        sheets, active_sheet, all_rows = read_csv_rows(file_path)
    else:
        raise ValueError(f"Unsupported file format: {ext}. Please provide Excel (.xlsx) or CSV.")

    if not all_rows:
        return {
            "sheets": sheets,
            "active_sheet": active_sheet,
            "detected_headers": [],
            "suggested_mapping": {},
            "preview_rows": [],
            "total_preview_rows": 0,
        }

    header_idx = detect_header_row_in_sheet(all_rows)
    raw_headers = [str(c).strip() if c is not None else f"Column_{i+1}" for i, c in enumerate(all_rows[header_idx])]
    suggested_map = auto_map_columns(raw_headers)

    preview_rows = []
    data_rows = all_rows[header_idx + 1 :]
    for r_idx, r in enumerate(data_rows[:10]):
        row_dict = {}
        # Ensure row list is padded to header length
        padded_row = r + [None] * max(0, len(raw_headers) - len(r))
        for col_idx, h in enumerate(raw_headers):
            val = padded_row[col_idx]
            row_dict[h] = str(val) if val is not None else ""
        row_dict["_source_row_index"] = header_idx + 2 + r_idx
        preview_rows.append(row_dict)

    return {
        "sheets": sheets,
        "active_sheet": active_sheet,
        "detected_headers": raw_headers,
        "suggested_mapping": suggested_map,
        "preview_rows": preview_rows,
        "total_preview_rows": len(preview_rows),
    }


def parse_file_records(
    file_path: str,
    column_mapping: Dict[str, str],
    sheet_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Parse entire file and map to standard fields.
    Each item contains:
    - standard fields
    - _source_file, _source_sheet, _source_row_index, _raw_record
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext in [".xlsx", ".xlsm", ".xltx", ".xltm"]:
        _, active_sheet, all_rows = read_excel_rows(file_path, sheet_name)
    elif ext in [".csv", ".txt"]:
        _, active_sheet, all_rows = read_csv_rows(file_path)
    else:
        raise ValueError(f"Unsupported file format: {ext}")

    if not all_rows:
        return []

    header_idx = detect_header_row_in_sheet(all_rows)
    raw_headers = [str(c).strip() if c is not None else f"Column_{i+1}" for i, c in enumerate(all_rows[header_idx])]

    # Invert mapping: raw_header -> standard_field
    inverted_map = {raw_col: std_field for std_field, raw_col in column_mapping.items()}

    records = []
    data_rows = all_rows[header_idx + 1 :]
    filename = os.path.basename(file_path)

    for r_idx, row in enumerate(data_rows):
        # Skip completely empty rows
        if not row or all(c is None or str(c).strip() == "" for c in row):
            continue

        padded_row = row + [None] * max(0, len(raw_headers) - len(row))
        raw_dict = {}
        standard_record = {field: None for field in STANDARD_FIELDS}

        for c_idx, h in enumerate(raw_headers):
            val = padded_row[c_idx]
            raw_dict[h] = val
            if h in inverted_map:
                std_f = inverted_map[h]
                standard_record[std_f] = val

        standard_record["_source_file"] = filename
        standard_record["_source_sheet"] = active_sheet
        standard_record["_source_row_index"] = header_idx + 2 + r_idx
        standard_record["_raw_record"] = {k: str(v) if v is not None else "" for k, v in raw_dict.items()}

        records.append(standard_record)

    return records
