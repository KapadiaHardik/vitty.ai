import json
import re
import logging
from typing import Dict, Any, Optional, List
from uuid import UUID
import pymupdf
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from app.models.domain import Document, DocumentChunk
from app.services.llm import generate_completion

logger = logging.getLogger(__name__)


class ExtractedLineItem(BaseModel):
    description: Optional[str] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    amount: Optional[float] = None


class ExtractedDocumentData(BaseModel):
    supplier_name: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    po_number: Optional[str] = None
    currency: Optional[str] = "USD"
    subtotal_amount: Optional[float] = None
    tax_amount: Optional[float] = None
    total_amount: Optional[float] = None
    line_items: List[ExtractedLineItem] = Field(default_factory=list)


def extract_text_from_file(file_path: str) -> str:
    """Extract raw text from a PDF or text file on disk."""
    text_content = ""
    try:
        if file_path.lower().endswith(".pdf"):
            with pymupdf.open(file_path) as doc:
                for page in doc:
                    text_content += page.get_text() + "\n"
        else:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text_content = f.read()
    except Exception as e:
        logger.warning(f"Failed to read file {file_path}: {e}")
    return text_content.strip()


async def get_document_full_text(document: Document, session: Optional[AsyncSession] = None) -> str:
    """Retrieve full document text from database chunks or original file."""
    # Try reading from DB chunks first if session is provided
    if session:
        try:
            stmt = select(DocumentChunk).where(DocumentChunk.document_id == document.id).order_by(DocumentChunk.chunk_index)
            res = await session.execute(stmt)
            chunks = res.scalars().all()
            if chunks:
                return "\n".join(c.text_content for c in chunks if c.text_content)
        except Exception as e:
            logger.warning(f"Could not load chunks for document {document.id}: {e}")

    # Fallback to reading disk file
    if document.original_path:
        return extract_text_from_file(document.original_path)

    return ""


def _heuristic_fallback_extraction(text: str, is_invoice: bool = True) -> Dict[str, Any]:
    """Deterministic regex extraction fallback if LLM is unavailable or fails."""
    data: Dict[str, Any] = {
        "supplier_name": None,
        "invoice_number": None,
        "invoice_date": None,
        "po_number": None,
        "currency": "INR",
        "subtotal_amount": None,
        "tax_amount": None,
        "total_amount": None,
        "line_items": []
    }

    # Currency detection
    curr_match = re.search(r"\b(INR|USD|EUR|GBP)\b|([₹$€£])", text)
    if curr_match:
        if curr_match.group(1):
            data["currency"] = curr_match.group(1).upper()
        elif curr_match.group(2) == "₹":
            data["currency"] = "INR"
        elif curr_match.group(2) == "$":
            data["currency"] = "USD"
        elif curr_match.group(2) == "€":
            data["currency"] = "EUR"
        elif curr_match.group(2) == "£":
            data["currency"] = "GBP"

    # Supplier name heuristic
    # 1. Look for explicit field: Supplier:, Vendor:, Seller:, Contracted Vendor:
    supp_field_match = re.search(r"(?:^|\n)\s*(?:supplier|vendor|contracted\s*vendor|seller)\s*:\s*([^\n\r]+)", text, re.IGNORECASE)
    if supp_field_match:
        cand = supp_field_match.group(1).strip()
        if len(cand) > 2 and not re.search(r"^(?:information|details|name)$", cand, re.IGNORECASE):
            data["supplier_name"] = cand

    if not data["supplier_name"]:
        # Fallback to top non-empty lines
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        for line in lines[:6]:
            if not re.search(r"invoice|tax|date|page|bill|receipt|purchase|order|original|recipient|details|vendor\s*information|buyer\s*order|payment\s*terms|authorized", line, re.IGNORECASE) and 3 < len(line) < 60:
                data["supplier_name"] = line
                break

    # Invoice Number (prefer explicit 'Invoice No:' or 'Invoice Number:')
    inv_explicit = re.search(r"(?:invoice\s*(?:number|no|num|#)|inv\s*(?:no|#|num)|bill\s*(?:no|#))[\s#:]*([A-Za-z0-9\-_/]+)", text, re.IGNORECASE)
    if inv_explicit:
        cand_inv = inv_explicit.group(1).strip()
        if cand_inv.upper() not in ["ORIGINAL", "DUPLICATE", "TAX", "RECIPIENT", "COMMERCIAL"]:
            data["invoice_number"] = cand_inv

    if not data["invoice_number"]:
        inv_match = re.search(r"\b(?:invoice|inv|bill)\b(?:\s*(?:number|no|num|#|reference|ref))?[\s#:]*([A-Za-z0-9\-_/]+)", text, re.IGNORECASE)
        if inv_match:
            cand_inv = inv_match.group(1).strip()
            if cand_inv.upper() not in ["ORIGINAL", "DUPLICATE", "TAX", "RECIPIENT", "COMMERCIAL", "DATE", "TERMS"]:
                data["invoice_number"] = cand_inv

    # PO Number (prefer explicit 'PO No:', 'PO Number:', 'PO Reference:')
    po_explicit = re.search(r"(?:p\.?o\.?\s*(?:number|no|num|#|ref(?:erence)?)|purchase\s*order\s*(?:number|no|num|#|ref(?:erence)?))[\s#:]*([A-Za-z0-9\-_/]+)", text, re.IGNORECASE)
    if po_explicit:
        cand_po = po_explicit.group(1).strip()
        if cand_po.upper() not in ["REFERENCE", "ORDER", "CONTRACT", "APPROVED", "TERMS", "ORIGINAL", "COMMERCIAL"]:
            data["po_number"] = cand_po

    if not data["po_number"]:
        po_match = re.search(r"(?:purchase\s*order|p\.?o\.?)[\s#:]*([A-Za-z0-9\-_/]+)", text, re.IGNORECASE)
        if po_match:
            cand_po = po_match.group(1).strip()
            if cand_po.upper() not in ["REFERENCE", "ORDER", "CONTRACT", "APPROVED", "TERMS", "ORIGINAL", "COMMERCIAL", "DATE"]:
                data["po_number"] = cand_po

    # Date
    date_match = re.search(r"(?:date)[\s#:]*([0-9]{1,4}[-/.][0-9]{1,2}[-/.][0-9]{1,4})", text, re.IGNORECASE)
    if date_match:
        data["invoice_date"] = date_match.group(1).strip()

    # Amounts: total, subtotal, tax with optional currency code/symbol and multiline handling
    curr_prefix = r"(?:INR|USD|EUR|GBP|Rs\.?|[₹$€£])?"

    total_match = re.search(r"\b(?:grand\s*total|total\s*amount|amount\s*due)\b[\s#:$]*" + curr_prefix + r"[\s#:$]*([0-9,]+\.[0-9]{2})", text, re.IGNORECASE)
    if not total_match:
        total_match = re.search(r"(?<!sub)\btotal\b[\s#:$]*" + curr_prefix + r"[\s#:$]*([0-9,]+\.[0-9]{2})", text, re.IGNORECASE)
    if total_match:
        try:
            data["total_amount"] = float(total_match.group(1).replace(",", ""))
        except ValueError:
            pass

    subtotal_match = re.search(r"\b(?:subtotal|sub-total|taxable\s*amount)\b[\s#:$]*" + curr_prefix + r"[\s#:$]*([0-9,]+\.[0-9]{2})", text, re.IGNORECASE)
    if subtotal_match:
        try:
            data["subtotal_amount"] = float(subtotal_match.group(1).replace(",", ""))
        except ValueError:
            pass

    tax_match = re.search(r"\b(?:gst\s*/\s*tax|tax|vat|gst|igst)\b[\s#:$]*" + curr_prefix + r"[\s#:$]*([0-9,]+\.[0-9]{2})", text, re.IGNORECASE)
    if tax_match:
        try:
            data["tax_amount"] = float(tax_match.group(1).replace(",", ""))
        except ValueError:
            pass

    return data


async def extract_document_data(
    document: Document,
    is_invoice: bool = True,
    session: Optional[AsyncSession] = None
) -> Dict[str, Any]:
    """
    Extract structured data from a document using LLM completion,
    falling back to deterministic heuristics if LLM fails or is unavailable.
    """
    full_text = await get_document_full_text(document, session)
    if not full_text:
        logger.warning(f"Empty text for document {document.id}")
        return _heuristic_fallback_extraction("", is_invoice)

    # Truncate text to avoid exceeding LLM context window (first ~6000 chars is plenty for invoices/POs)
    prompt_text = full_text[:6000]

    doc_type_str = "an Invoice" if is_invoice else "a Purchase Order / Reference Document"
    prompt = f"""You are a specialized financial document data extraction engine.
Analyze the following document text representing {doc_type_str} and extract the structured fields.

Return ONLY a valid JSON object with the following keys and data types:
{{
  "supplier_name": string or null,
  "invoice_number": string or null,
  "invoice_date": string or null (YYYY-MM-DD or as written),
  "po_number": string or null,
  "currency": string (e.g. "USD", "INR", "EUR"),
  "subtotal_amount": float or null (numeric subtotal before tax),
  "tax_amount": float or null (total tax/VAT/GST amount),
  "total_amount": float or null (grand total amount payable),
  "line_items": [
    {{
      "description": string,
      "quantity": float or null,
      "unit_price": float or null,
      "amount": float or null
    }}
  ]
}}

DOCUMENT TEXT:
---
{prompt_text}
---

Remember: Output ONLY valid JSON. No conversational text, no markdown outside the JSON block.
"""

    try:
        response_text = await generate_completion(prompt, max_tokens=500, temperature=0.1, json_mode=True, think=False)
        # Clean markdown codeblocks if LLM returned them
        cleaned = re.sub(r"^```(?:json)?", "", response_text.strip(), flags=re.MULTILINE)
        cleaned = re.sub(r"```$", "", cleaned.strip(), flags=re.MULTILINE).strip()

        # Find first { and last }
        start_idx = cleaned.find("{")
        end_idx = cleaned.rfind("}")
        if start_idx != -1 and end_idx != -1:
            json_str = cleaned[start_idx:end_idx + 1]
            parsed = json.loads(json_str)
            # Validate with Pydantic
            validated = ExtractedDocumentData(**parsed)
            result_dict = validated.model_dump()
            logger.info(f"Successfully extracted structured data via LLM for document {document.id}")
            return result_dict
    except Exception as e:
        logger.warning(f"LLM extraction failed or returned malformed JSON for doc {document.id}: {e}. Using deterministic fallback.")

    # Fallback to regex heuristic
    return _heuristic_fallback_extraction(full_text, is_invoice)
