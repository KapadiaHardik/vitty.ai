import os
import csv
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "test_dataset", "gst_reconciliation")
os.makedirs(OUT_DIR, exist_ok=True)

# Standard styling for generated Excel files
def apply_styling(ws, headers, header_color="1E3A8A"):
    font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    fill = PatternFill(start_color=header_color, end_color=header_color, fill_type="solid")
    alignment = Alignment(horizontal="center", vertical="center")
    thin_border = Border(
        left=Side(style="thin", color="D1D5DB"),
        right=Side(style="thin", color="D1D5DB"),
        top=Side(style="thin", color="D1D5DB"),
        bottom=Side(style="thin", color="D1D5DB"),
    )

    ws.append(headers)
    ws.row_dimensions[1].height = 25

    for col_idx in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.font = font
        cell.fill = fill
        cell.alignment = alignment
        cell.border = thin_border

    # Auto-adjust column width
    for col in ws.columns:
        col_letter = get_column_letter(col[0].column)
        max_len = max(len(str(cell.value or "")) for cell in col)
        ws.column_dimensions[col_letter].width = max(max_len + 4, 12)


def generate_gstr2b_dataset():
    """
    Standard Indian Government GSTR-2B Portal Schema:
    GSTIN of supplier, Trade/Legal name, Invoice number, Invoice type, Invoice Date,
    Invoice Value, Place of supply, Supply Attract Reverse Charge, Rate (%),
    Taxable Value, Integrated Tax, Central Tax, State/UT Tax, Cess, GSTR-1/IFF Filing Date
    """
    headers = [
        "GSTIN of supplier",
        "Trade/Legal name",
        "Invoice number",
        "Invoice type",
        "Invoice Date",
        "Invoice Value",
        "Place of supply",
        "Taxable Value",
        "Integrated Tax",
        "Central Tax",
        "State/UT Tax",
        "Cess",
    ]

    rows = [
        # 1. Exact Match 1
        ["27AAACR1234A1Z1", "Reliance Infocomm Ltd", "INV-2024-001", "Regular", "05/04/2024", "118000.00", "27-Maharashtra", "100000.00", "0.00", "9000.00", "9000.00", "0.00"],
        # 2. Exact Match 2 (Interstate)
        ["29AABCT5678B1Z2", "Tata Consultancy Services", "TCS/0091", "Regular", "12/04/2024", "59000.00", "29-Karnataka", "50000.00", "9000.00", "0.00", "0.00", "0.00"],
        # 3. Strong Match (Small date difference in Books vs 2B)
        ["07AAAAA0000A1Z5", "Delhi Logistics Hub", "DLH-7781", "Regular", "15/04/2024", "23600.00", "07-Delhi", "20000.00", "3600.00", "0.00", "0.00", "0.00"],
        # 4. Flexible Match (Formatting difference: 'INV-2024-45' vs 'INV/2024/045')
        ["24AAACB9999C1Z3", "Gujarat Steel Traders", "INV-2024-45", "Regular", "18/04/2024", "354000.00", "24-Gujarat", "300000.00", "54000.00", "0.00", "0.00", "0.00"],
        # 5. Potential Match (Slightly altered invoice number for CA review)
        ["33AAACI4444D1Z4", "Chennai Auto Spares", "CAS/8892A", "Regular", "20/04/2024", "17700.00", "33-Tamil Nadu", "15000.00", "2700.00", "0.00", "0.00", "0.00"],
        # 6. Taxable Value Mismatch (Portal has 45000, Books has 50000)
        ["27AAACP8888E1Z9", "Pune Precision Tools", "PPT-1044", "Regular", "22/04/2024", "53100.00", "27-Maharashtra", "45000.00", "0.00", "4050.00", "4050.00", "0.00"],
        # 7. Tax Type Mismatch (Vendor filed as Intrastate CGST+SGST, but Books claimed Interstate IGST)
        ["27AABCM3333F1Z6", "Metro Packagers Mumbai", "MPM-302", "Regular", "24/04/2024", "29500.00", "27-Maharashtra", "25000.00", "0.00", "2250.00", "2250.00", "0.00"],
        # 8. GSTR-2B Only (Appears on portal, but accountant forgot to enter in Books)
        ["27AABCH1111G1Z8", "Horizon Cloud Solutions", "HCS-9910", "Regular", "26/04/2024", "14160.00", "27-Maharashtra", "12000.00", "0.00", "1080.00", "1080.00", "0.00"],
        # 9. Credit Note (CRN)
        ["27AAACR1234A1Z1", "Reliance Infocomm Ltd", "CRN-005", "Credit Note", "28/04/2024", "-11800.00", "27-Maharashtra", "-10000.00", "0.00", "-900.00", "-900.00", "0.00"],
    ]

    # Save Excel
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "GSTR-2B"
    apply_styling(ws, headers, header_color="1E3A8A")
    for r in rows:
        ws.append(r)
    excel_path = os.path.join(OUT_DIR, "GSTR2B_April_2024.xlsx")
    wb.save(excel_path)

    # Save CSV
    csv_path = os.path.join(OUT_DIR, "GSTR2B_April_2024.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)

    print(f"Created GSTR-2B files:\n - {excel_path}\n - {csv_path}")


def generate_purchase_register_dataset():
    """
    Standard Tally / ERP Purchase Register Schema:
    Party GSTIN, Party Name, Voucher No, Voucher Type, Date, Basic Amount,
    IGST Amount, CGST Amount, SGST Amount, Cess Amount, Grand Total
    """
    headers = [
        "Party GSTIN",
        "Party Name",
        "Voucher No",
        "Voucher Type",
        "Date",
        "Basic Amount",
        "IGST Amount",
        "CGST Amount",
        "SGST Amount",
        "Cess Amount",
        "Grand Total",
    ]

    rows = [
        # 1. Matches GSTR-2B Row 1 (Exact Match)
        ["27AAACR1234A1Z1", "Reliance Infocomm Ltd", "INV-2024-001", "Purchase", "05/04/2024", "100000.00", "0.00", "9000.00", "9000.00", "0.00", "118000.00"],
        # 2. Matches GSTR-2B Row 2 (Exact Match)
        ["29AABCT5678B1Z2", "Tata Consultancy Services", "TCS/0091", "Purchase", "12/04/2024", "50000.00", "9000.00", "0.00", "0.00", "0.00", "59000.00"],
        # 3. Matches GSTR-2B Row 3 (Strong Match: Date is 12/04/2024 in Books vs 15/04/2024 in 2B)
        ["07AAAAA0000A1Z5", "Delhi Logistics Hub", "DLH-7781", "Purchase", "12/04/2024", "20000.00", "3600.00", "0.00", "0.00", "0.00", "23600.00"],
        # 4. Matches GSTR-2B Row 4 (Flexible Match: 'INV/2024/045' vs 'INV-2024-45')
        ["24AAACB9999C1Z3", "Gujarat Steel Traders", "INV/2024/045", "Purchase", "18/04/2024", "300000.00", "54000.00", "0.00", "0.00", "0.00", "354000.00"],
        # 5. Matches GSTR-2B Row 5 (Potential Match: 'CAS/8892' vs 'CAS/8892A')
        ["33AAACI4444D1Z4", "Chennai Auto Spares", "CAS/8892", "Purchase", "20/04/2024", "15000.00", "2700.00", "0.00", "0.00", "0.00", "17700.00"],
        # 6. Matches GSTR-2B Row 6 (Taxable Value Mismatch: 50000 in Books vs 45000 in 2B)
        ["27AAACP8888E1Z9", "Pune Precision Tools", "PPT-1044", "Purchase", "22/04/2024", "50000.00", "0.00", "4500.00", "4500.00", "0.00", "59000.00"],
        # 7. Matches GSTR-2B Row 7 (Tax Type Mismatch: Books entered IGST instead of CGST+SGST)
        ["27AABCM3333F1Z6", "Metro Packagers Mumbai", "MPM-302", "Purchase", "24/04/2024", "25000.00", "4500.00", "0.00", "0.00", "0.00", "29500.00"],
        # 8. Books Only (In Books, but supplier never uploaded to GSTR-1, so missing in 2B!)
        ["27AAACK5555M1Z0", "Apex Office Supplies", "AOS-1102", "Purchase", "25/04/2024", "40000.00", "0.00", "3600.00", "3600.00", "0.00", "47200.00"],
        # 9. Duplicate Invoice in Books (Accountant entered invoice twice by mistake)
        ["27AAACK5555M1Z0", "Apex Office Supplies", "AOS-1102", "Purchase", "25/04/2024", "40000.00", "0.00", "3600.00", "3600.00", "0.00", "47200.00"],
        # 10. Credit Note matching GSTR-2B Row 9
        ["27AAACR1234A1Z1", "Reliance Infocomm Ltd", "CRN-005", "Credit Note", "28/04/2024", "-10000.00", "0.00", "-900.00", "-900.00", "0.00", "-11800.00"],
        # 11. Invalid Record: GSTIN is invalid format
        ["INVALID999", "Random Local Vendor", "RLV-001", "Purchase", "29/04/2024", "5000.00", "0.00", "450.00", "450.00", "0.00", "5900.00"],
    ]

    # Save Excel
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Purchase Register"
    apply_styling(ws, headers, header_color="047857")  # Emerald green header
    for r in rows:
        ws.append(r)
    excel_path = os.path.join(OUT_DIR, "Purchase_Register_April_2024.xlsx")
    wb.save(excel_path)

    # Save CSV
    csv_path = os.path.join(OUT_DIR, "Purchase_Register_April_2024.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)

    print(f"Created Purchase Register files:\n - {excel_path}\n - {csv_path}")


if __name__ == "__main__":
    generate_gstr2b_dataset()
    generate_purchase_register_dataset()
    print("\nSample datasets generated successfully!")
