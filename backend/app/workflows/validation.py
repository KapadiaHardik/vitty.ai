from typing import List, Dict, Any
from app.models.domain import DiscrepancyType, Severity

def validate_invoice(invoice_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Deterministically validate invoice data for missing fields and basic arithmetic.
    """
    findings = []
    
    # 1. Missing Required Fields
    required_fields = ["supplier_name", "invoice_number", "invoice_date", "total_amount"]
    for field in required_fields:
        if not invoice_data.get(field):
            findings.append({
                "type": DiscrepancyType.MISSING_FIELD,
                "severity": Severity.HIGH,
                "field": field,
                "invoice_value": None,
                "reference_value": None,
                "explanation": f"Required field '{field}' is missing from the invoice."
            })
            
    # 2. Total Arithmetic Check
    try:
        total_val = invoice_data.get("total_amount")
        tax_val = invoice_data.get("tax_amount")
        subtotal_val = invoice_data.get("subtotal_amount")

        total = float(str(total_val).replace(',', '')) if total_val is not None else 0.0
        tax = float(str(tax_val).replace(',', '')) if tax_val is not None else 0.0
        subtotal = float(str(subtotal_val).replace(',', '')) if subtotal_val is not None else 0.0
        
        if subtotal > 0 and abs((subtotal + tax) - total) > 0.05:
            findings.append({
                "type": DiscrepancyType.TOTAL_MISMATCH,
                "severity": Severity.HIGH,
                "field": "total_amount",
                "invoice_value": str(total),
                "reference_value": str(round(subtotal + tax, 2)),
                "explanation": f"Subtotal ({subtotal}) plus tax ({tax}) does not equal the grand total ({total})."
            })
    except (ValueError, TypeError):
        pass # Ignore malformed numbers here, handle gracefully
        
    return findings
