from typing import List, Dict, Any
from app.models.domain import DiscrepancyType, Severity

def compare_documents(invoice_data: Dict[str, Any], reference_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Compare an invoice against a reference document (e.g. PO) deterministically.
    """
    findings = []
    
    # 1. Supplier Mismatch
    inv_supplier = str(invoice_data.get("supplier_name", "")).strip().lower()
    ref_supplier = str(reference_data.get("supplier_name", "")).strip().lower()
    
    if inv_supplier and ref_supplier and inv_supplier != ref_supplier:
        findings.append({
            "type": DiscrepancyType.SUPPLIER_MISMATCH,
            "severity": Severity.HIGH,
            "field": "supplier_name",
            "invoice_value": invoice_data.get("supplier_name"),
            "reference_value": reference_data.get("supplier_name"),
            "explanation": "Supplier name on invoice does not match the reference document."
        })
        
    # 2. PO Number Mismatch
    inv_po = str(invoice_data.get("po_number", "")).strip().lower()
    ref_po = str(reference_data.get("po_number", "")).strip().lower()
    if inv_po and ref_po and inv_po != ref_po:
        findings.append({
            "type": DiscrepancyType.PO_MISMATCH,
            "severity": Severity.HIGH,
            "field": "po_number",
            "invoice_value": invoice_data.get("po_number"),
            "reference_value": reference_data.get("po_number"),
            "explanation": "Purchase Order number on invoice does not match the reference document."
        })
        
    # 3. Total amount comparison
    try:
        inv_val = invoice_data.get("total_amount")
        ref_val = reference_data.get("total_amount")
        inv_total = float(str(inv_val).replace(',', '')) if inv_val is not None else 0.0
        ref_total = float(str(ref_val).replace(',', '')) if ref_val is not None else 0.0
        if inv_total > 0 and ref_total > 0 and abs(inv_total - ref_total) > 0.05:
            findings.append({
                "type": DiscrepancyType.TOTAL_MISMATCH,
                "severity": Severity.MEDIUM,
                "field": "total_amount",
                "invoice_value": str(inv_total),
                "reference_value": str(ref_total),
                "explanation": f"Total amount on invoice ({inv_total}) differs from reference document ({ref_total})."
            })
    except (ValueError, TypeError):
        pass

    return findings
