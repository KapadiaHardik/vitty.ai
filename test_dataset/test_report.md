# Vitty.ai Phase 2 Verification Engine - Synthetic Test Suite Report
**Date:** 2026-10-18 17:08:36  
**Total Test Cases:** 60  
**Execution Time:** 0.17 seconds  
**Overall Accuracy:** **100.0%** (60/60 passed)  

## 1. Category Breakdown

| Category | Total | Passed | Failed | Success Rate |
|---|---|---|---|---|
| **A_CLEAN_COMPLIANT** | 12 | 12 | 0 | **100.0%** |
| **B_TAX_AND_ARITHMETIC** | 14 | 14 | 0 | **100.0%** |
| **C_MISSING_FIELDS** | 10 | 10 | 0 | **100.0%** |
| **D_2WAY_MISMATCHES** | 14 | 14 | 0 | **100.0%** |
| **E_DUPLICATES_BASE** | 3 | 3 | 0 | **100.0%** |
| **E_DUPLICATES** | 3 | 3 | 0 | **100.0%** |
| **F_MULTI_CURRENCY** | 3 | 3 | 0 | **100.0%** |
| **F_MULTI_LINE_COMPLEX** | 1 | 1 | 0 | **100.0%** |

## 2. Test Case Detail Log

| Case ID | Category | Status | Expected Findings | Actual Detected | Description |
|---|---|---|---|---|---|
| `TC_01` | `A_CLEAN_COMPLIANT` | 🟢 PASS | *None (Clean)* | *None (Clean)* | Clean 2-way match for Acme Industrial Supplies (zero findings expected). |
| `TC_02` | `A_CLEAN_COMPLIANT` | 🟢 PASS | *None (Clean)* | *None (Clean)* | Clean 2-way match for TechCore Solutions Ltd (zero findings expected). |
| `TC_03` | `A_CLEAN_COMPLIANT` | 🟢 PASS | *None (Clean)* | *None (Clean)* | Clean 2-way match for Apex Logistics LLP (zero findings expected). |
| `TC_04` | `A_CLEAN_COMPLIANT` | 🟢 PASS | *None (Clean)* | *None (Clean)* | Clean 2-way match for Zenith Office Systems (zero findings expected). |
| `TC_05` | `A_CLEAN_COMPLIANT` | 🟢 PASS | *None (Clean)* | *None (Clean)* | Clean 2-way match for BrightStar Electricals (zero findings expected). |
| `TC_06` | `A_CLEAN_COMPLIANT` | 🟢 PASS | *None (Clean)* | *None (Clean)* | Clean 2-way match for Precision Tools India (zero findings expected). |
| `TC_07` | `A_CLEAN_COMPLIANT` | 🟢 PASS | *None (Clean)* | *None (Clean)* | Clean standalone invoice for Global Horizon Consulting (zero findings expected). |
| `TC_08` | `A_CLEAN_COMPLIANT` | 🟢 PASS | *None (Clean)* | *None (Clean)* | Clean standalone invoice for Alpha Security Services (zero findings expected). |
| `TC_09` | `A_CLEAN_COMPLIANT` | 🟢 PASS | *None (Clean)* | *None (Clean)* | Clean standalone invoice for BlueWave Digital Media (zero findings expected). |
| `TC_10` | `A_CLEAN_COMPLIANT` | 🟢 PASS | *None (Clean)* | *None (Clean)* | Clean standalone invoice for Silverline Facility Management (zero findings expected). |
| `TC_11` | `A_CLEAN_COMPLIANT` | 🟢 PASS | *None (Clean)* | *None (Clean)* | Clean standalone invoice for CyberShield Infotech (zero findings expected). |
| `TC_12` | `A_CLEAN_COMPLIANT` | 🟢 PASS | *None (Clean)* | *None (Clean)* | Clean standalone invoice for Prime Packaging Corp (zero findings expected). |
| `TC_13` | `B_TAX_AND_ARITHMETIC` | 🟢 PASS | TOTAL_MISMATCH | TOTAL_MISMATCH | Arithmetic mismatch: Subtotal (10000.0) + Tax (1800.0) != Printed Total (12800.0). Total arithmetic overbilled by 1,000 |
| `TC_14` | `B_TAX_AND_ARITHMETIC` | 🟢 PASS | TOTAL_MISMATCH | TOTAL_MISMATCH | Arithmetic mismatch: Subtotal (45000.0) + Tax (8100.0) != Printed Total (45000.0). Tax omitted from printed grand total |
| `TC_15` | `B_TAX_AND_ARITHMETIC` | 🟢 PASS | TOTAL_MISMATCH | TOTAL_MISMATCH | Arithmetic mismatch: Subtotal (20000.0) + Tax (3600.0) != Printed Total (23000.0). Transposition error underbilled by 600 |
| `TC_16` | `B_TAX_AND_ARITHMETIC` | 🟢 PASS | TOTAL_MISMATCH | TOTAL_MISMATCH | Arithmetic mismatch: Subtotal (8500.0) + Tax (1530.0) != Printed Total (10500.0). Incorrect round-up by 470 |
| `TC_17` | `B_TAX_AND_ARITHMETIC` | 🟢 PASS | TOTAL_MISMATCH | TOTAL_MISMATCH | Arithmetic mismatch: Subtotal (64000.0) + Tax (11520.0) != Printed Total (72000.0). Subtotal addition mismatch by 3,520 |
| `TC_18` | `B_TAX_AND_ARITHMETIC` | 🟢 PASS | TOTAL_MISMATCH | TOTAL_MISMATCH | Arithmetic mismatch: Subtotal (50000.0) + Tax (5000.0) != Printed Total (59000.0). Tax computed at 10% but total printed as 59,000 |
| `TC_19` | `B_TAX_AND_ARITHMETIC` | 🟢 PASS | TOTAL_MISMATCH | TOTAL_MISMATCH | Arithmetic mismatch: Subtotal (12000.0) + Tax (0.0) != Printed Total (14160.0). Tax printed as 0 but added to grand total |
| `TC_20` | `B_TAX_AND_ARITHMETIC` | 🟢 PASS | TOTAL_MISMATCH | TOTAL_MISMATCH | Arithmetic mismatch: Subtotal (30000.0) + Tax (5400.0) != Printed Total (34400.0). Underbilled by 1,000 on total |
| `TC_21` | `B_TAX_AND_ARITHMETIC` | 🟢 PASS | TOTAL_MISMATCH | TOTAL_MISMATCH | Arithmetic mismatch: Subtotal (15000.0) + Tax (2700.0) != Printed Total (18200.0). Arithmetic error variance of 500 |
| `TC_22` | `B_TAX_AND_ARITHMETIC` | 🟢 PASS | TOTAL_MISMATCH | TOTAL_MISMATCH | Arithmetic mismatch: Subtotal (90000.0) + Tax (16200.0) != Printed Total (105000.0). Total under-sums tax by 1,200 |
| `TC_23` | `B_TAX_AND_ARITHMETIC` | 🟢 PASS | TOTAL_MISMATCH | TOTAL_MISMATCH | Arithmetic mismatch: Subtotal (28000.0) + Tax (5040.0) != Printed Total (33500.0). Arithmetic total mismatch of 460 |
| `TC_24` | `B_TAX_AND_ARITHMETIC` | 🟢 PASS | TOTAL_MISMATCH | TOTAL_MISMATCH | Arithmetic mismatch: Subtotal (7200.0) + Tax (1296.0) != Printed Total (8200.0). Arithmetic total under by 296 |
| `TC_25` | `B_TAX_AND_ARITHMETIC` | 🟢 PASS | TOTAL_MISMATCH | TOTAL_MISMATCH | Arithmetic mismatch: Subtotal (120000.0) + Tax (21600.0) != Printed Total (140000.0). Under-sums total by 1,600 |
| `TC_26` | `B_TAX_AND_ARITHMETIC` | 🟢 PASS | TOTAL_MISMATCH | TOTAL_MISMATCH | Arithmetic mismatch: Subtotal (35000.0) + Tax (6300.0) != Printed Total (42000.0). Overbilled arithmetic total by 700 |
| `TC_27` | `C_MISSING_FIELDS` | 🟢 PASS | MISSING_FIELD | MISSING_FIELD | Missing mandatory compliance fields: Missing invoice_number. |
| `TC_28` | `C_MISSING_FIELDS` | 🟢 PASS | MISSING_FIELD | MISSING_FIELD | Missing mandatory compliance fields: Missing invoice_date. |
| `TC_29` | `C_MISSING_FIELDS` | 🟢 PASS | MISSING_FIELD | MISSING_FIELD | Missing mandatory compliance fields: Missing supplier_name. |
| `TC_30` | `C_MISSING_FIELDS` | 🟢 PASS | MISSING_FIELD | MISSING_FIELD<br>TOTAL_MISMATCH | Missing mandatory compliance fields: Missing total_amount. |
| `TC_31` | `C_MISSING_FIELDS` | 🟢 PASS | MISSING_FIELD<br>MISSING_FIELD | MISSING_FIELD<br>MISSING_FIELD | Missing mandatory compliance fields: Missing invoice_number and invoice_date. |
| `TC_32` | `C_MISSING_FIELDS` | 🟢 PASS | MISSING_FIELD<br>MISSING_FIELD | MISSING_FIELD<br>MISSING_FIELD | Missing mandatory compliance fields: Missing supplier_name and invoice_number. |
| `TC_33` | `C_MISSING_FIELDS` | 🟢 PASS | MISSING_FIELD<br>MISSING_FIELD | MISSING_FIELD<br>MISSING_FIELD<br>TOTAL_MISMATCH | Missing mandatory compliance fields: Missing invoice_date and total_amount. |
| `TC_34` | `C_MISSING_FIELDS` | 🟢 PASS | MISSING_FIELD | MISSING_FIELD | Missing mandatory compliance fields: Quotation layout missing invoice_number. |
| `TC_35` | `C_MISSING_FIELDS` | 🟢 PASS | MISSING_FIELD | MISSING_FIELD | Missing mandatory compliance fields: Anonymous bill missing supplier_name. |
| `TC_36` | `C_MISSING_FIELDS` | 🟢 PASS | MISSING_FIELD | MISSING_FIELD<br>TOTAL_MISMATCH | Missing mandatory compliance fields: Incomplete receipt missing total_amount. |
| `TC_37` | `D_2WAY_MISMATCHES` | 🟢 PASS | TOTAL_MISMATCH | TOTAL_MISMATCH | 2-Way Mismatch: Invoice Total (55k) > PO Total (50k). |
| `TC_38` | `D_2WAY_MISMATCHES` | 🟢 PASS | TOTAL_MISMATCH | TOTAL_MISMATCH | 2-Way Mismatch: Invoice Total (118k) > PO Total (94.4k). |
| `TC_39` | `D_2WAY_MISMATCHES` | 🟢 PASS | TOTAL_MISMATCH | TOTAL_MISMATCH | 2-Way Mismatch: Invoice Total (32k) > PO Total (28k). |
| `TC_40` | `D_2WAY_MISMATCHES` | 🟢 PASS | TOTAL_MISMATCH | TOTAL_MISMATCH | 2-Way Mismatch: Invoice Total (88k) > PO Total (75k). |
| `TC_41` | `D_2WAY_MISMATCHES` | 🟢 PASS | SUPPLIER_MISMATCH | SUPPLIER_MISMATCH | 2-Way Mismatch: Supplier name mismatch between entities. |
| `TC_42` | `D_2WAY_MISMATCHES` | 🟢 PASS | SUPPLIER_MISMATCH | SUPPLIER_MISMATCH | 2-Way Mismatch: Sister company supplier mismatch. |
| `TC_43` | `D_2WAY_MISMATCHES` | 🟢 PASS | SUPPLIER_MISMATCH | SUPPLIER_MISMATCH | 2-Way Mismatch: Vendor legal name mismatch. |
| `TC_44` | `D_2WAY_MISMATCHES` | 🟢 PASS | PO_MISMATCH | PO_MISMATCH | 2-Way Mismatch: PO number digit transposition. |
| `TC_45` | `D_2WAY_MISMATCHES` | 🟢 PASS | PO_MISMATCH | PO_MISMATCH | 2-Way Mismatch: Wrong contract PO reference cited. |
| `TC_46` | `D_2WAY_MISMATCHES` | 🟢 PASS | PO_MISMATCH | PO_MISMATCH | 2-Way Mismatch: Suffix mismatch on PO number. |
| `TC_47` | `D_2WAY_MISMATCHES` | 🟢 PASS | SUPPLIER_MISMATCH<br>TOTAL_MISMATCH | SUPPLIER_MISMATCH<br>TOTAL_MISMATCH | 2-Way Mismatch: Compound: Supplier AND Total Mismatch. |
| `TC_48` | `D_2WAY_MISMATCHES` | 🟢 PASS | PO_MISMATCH<br>TOTAL_MISMATCH | PO_MISMATCH<br>TOTAL_MISMATCH | 2-Way Mismatch: Compound: PO number AND Total Mismatch. |
| `TC_49` | `D_2WAY_MISMATCHES` | 🟢 PASS | TOTAL_MISMATCH | TOTAL_MISMATCH | 2-Way Mismatch: Under-billing partial match. |
| `TC_50` | `D_2WAY_MISMATCHES` | 🟢 PASS | TOTAL_MISMATCH | TOTAL_MISMATCH | 2-Way Mismatch: Quantity variance leading to total mismatch. |
| `TC_51` | `E_DUPLICATES_BASE` | 🟢 PASS | *None (Clean)* | *None (Clean)* | Original submission for Vortex Technologies (#INV-VORTEX-901). Base run. |
| `TC_52` | `E_DUPLICATES` | 🟢 PASS | DUPLICATE_INVOICE | DUPLICATE_INVOICE | Duplicate invoice detection: Repeated submission of invoice #INV-VORTEX-901 by Vortex Technologies. |
| `TC_53` | `E_DUPLICATES_BASE` | 🟢 PASS | *None (Clean)* | *None (Clean)* | Original submission for Skyline Freight Carriers (#INV-SKY-4412). Base run. |
| `TC_54` | `E_DUPLICATES` | 🟢 PASS | DUPLICATE_INVOICE | DUPLICATE_INVOICE | Duplicate invoice detection: Repeated submission of invoice #INV-SKY-4412 by Skyline Freight Carriers. |
| `TC_55` | `E_DUPLICATES_BASE` | 🟢 PASS | *None (Clean)* | *None (Clean)* | Original submission for Omni Clean Logistics (#INV-OMNI-1008). Base run. |
| `TC_56` | `E_DUPLICATES` | 🟢 PASS | DUPLICATE_INVOICE | DUPLICATE_INVOICE | Duplicate invoice detection: Repeated submission of invoice #INV-OMNI-1008 by Omni Clean Logistics. |
| `TC_57` | `F_MULTI_CURRENCY` | 🟢 PASS | *None (Clean)* | *None (Clean)* | Multi-currency clean USD match vs PO (zero findings expected). |
| `TC_58` | `F_MULTI_CURRENCY` | 🟢 PASS | *None (Clean)* | *None (Clean)* | Multi-currency clean EUR match vs PO (zero findings expected). |
| `TC_59` | `F_MULTI_CURRENCY` | 🟢 PASS | TOTAL_MISMATCH | TOTAL_MISMATCH | USD invoice arithmetic error: Subtotal (3000) + Tax (300) != Printed Total (3500). |
| `TC_60` | `F_MULTI_LINE_COMPLEX` | 🟢 PASS | *None (Clean)* | *None (Clean)* | Multi-line complex infrastructure procurement (zero findings expected). |