"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  FileSpreadsheet,
  Upload,
  Play,
  Loader2,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Clock,
  ArrowRight,
  ShieldCheck,
  RefreshCw,
  Plus,
  Sliders,
  ChevronRight,
  FileCheck,
  Eye,
  Check,
} from "lucide-react";
import Link from "next/link";
import {
  fetchGSTRuns,
  createGSTRun,
  uploadGSTFilePreview,
} from "@/lib/api";

interface GSTRunItem {
  id: string;
  company_gstin: string;
  tax_period: string;
  status: "PENDING" | "PARSING" | "MATCHING" | "COMPLETED" | "FAILED";
  created_at: string;
  total_books_records: number;
  total_gstr2b_records: number;
  matched_count: number;
  mismatch_count: number;
  pending_reviews: number;
}

interface ColumnPreview {
  document_id: string;
  filename: string;
  sheets: string[];
  active_sheet: string;
  detected_headers: string[];
  suggested_mapping: Record<string, string>;
  preview_rows: Record<string, string>[];
  total_preview_rows: number;
}

export default function GSTReconciliationPage() {
  const [runs, setRuns] = useState<GSTRunItem[]>([]);
  const [loadingRuns, setLoadingRuns] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const router = useRouter();

  // Modal Form State
  const [companyGstin, setCompanyGstin] = useState("");
  const [taxPeriod, setTaxPeriod] = useState("04-2024");
  const [taxTol, setTaxTol] = useState("1.0");
  const [dateTol, setDateTol] = useState("30");

  const [gstr2bFile, setGstr2bFile] = useState<File | null>(null);
  const [prFile, setPrFile] = useState<File | null>(null);
  const [gstr2bPreview, setGstr2bPreview] = useState<ColumnPreview | null>(null);
  const [prPreview, setPrPreview] = useState<ColumnPreview | null>(null);
  const [uploadingGstr2b, setUploadingGstr2b] = useState(false);
  const [uploadingPr, setUploadingPr] = useState(false);

  const [gstr2bMapping, setGstr2bMapping] = useState<Record<string, string>>({});
  const [prMapping, setPrMapping] = useState<Record<string, string>>({});

  const [isStarting, setIsStarting] = useState(false);
  const [startError, setStartError] = useState<string | null>(null);

  const loadRuns = async () => {
    try {
      const data = await fetchGSTRuns();
      setRuns(data || []);
    } catch (err) {
      console.error("Failed to load GST reconciliation runs", err);
    } finally {
      setLoadingRuns(false);
    }
  };

  useEffect(() => {
    loadRuns();
    const interval = setInterval(loadRuns, 4000);
    return () => clearInterval(interval);
  }, []);

  const handleGstr2bUpload = async (file: File) => {
    setGstr2bFile(file);
    setUploadingGstr2b(true);
    try {
      const preview = await uploadGSTFilePreview(file);
      setGstr2bPreview(preview);
      setGstr2bMapping(preview.suggested_mapping || {});
    } catch (err: any) {
      alert(err.message || "Failed to inspect GSTR-2B file");
    } finally {
      setUploadingGstr2b(false);
    }
  };

  const handlePrUpload = async (file: File) => {
    setPrFile(file);
    setUploadingPr(true);
    try {
      const preview = await uploadGSTFilePreview(file);
      setPrPreview(preview);
      setPrMapping(preview.suggested_mapping || {});
    } catch (err: any) {
      alert(err.message || "Failed to inspect Purchase Register file");
    } finally {
      setUploadingPr(false);
    }
  };

  const handleStartReconciliation = async () => {
    if (!companyGstin.trim() || companyGstin.trim().length !== 15) {
      setStartError("Please provide a valid 15-character GSTIN.");
      return;
    }
    if (!gstr2bPreview?.document_id || !prPreview?.document_id) {
      setStartError("Both GSTR-2B and Purchase Register files must be uploaded.");
      return;
    }

    setStartError(null);
    setIsStarting(true);

    try {
      const run = await createGSTRun({
        company_gstin: companyGstin.trim().toUpperCase(),
        tax_period: taxPeriod.trim(),
        gstr2b_document_id: gstr2bPreview.document_id,
        purchase_register_document_id: prPreview.document_id,
        gstr2b_column_mapping: gstr2bMapping,
        purchase_register_column_mapping: prMapping,
        tolerances: {
          tax_diff_max: parseFloat(taxTol) || 1.0,
          date_days_diff: parseInt(dateTol) || 30,
        },
      });

      setShowModal(false);
      router.push(`/gst-reconciliation/${run.id}`);
    } catch (err: any) {
      setStartError(err.message || "Failed to start reconciliation");
      setIsStarting(false);
    }
  };

  const renderStatusBadge = (status: GSTRunItem["status"]) => {
    switch (status) {
      case "PENDING":
      case "PARSING":
      case "MATCHING":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200">
            <Loader2 className="w-3.5 h-3.5 animate-spin" /> {status}
          </span>
        );
      case "COMPLETED":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> Completed
          </span>
        );
      case "FAILED":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
            <XCircle className="w-3.5 h-3.5 text-rose-600" /> Failed
          </span>
        );
    }
  };

  return (
    <div className="min-h-screen bg-slate-50/50 py-10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
        {/* Header Banner */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-6 sm:p-8 rounded-2xl border border-slate-200/80 shadow-xs">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2.5 py-0.5 rounded-md text-xs font-bold tracking-wide uppercase bg-primary-100 text-primary-800 border border-primary-200">
                GST Engine
              </span>
              <span className="text-xs text-slate-400">•</span>
              <span className="text-xs font-medium text-slate-500">GSTR-2B vs. Purchase Register</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              GST Reconciliation Engine
            </h1>
            <p className="text-sm text-slate-600 mt-1 max-w-2xl">
              Deterministic 4-stage matching algorithm designed for Indian CA firms. Ingest raw Excel/CSV statements, auto-map columns, identify tax discrepancies, and export audit-ready reports.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowModal(true)}
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-primary-600 hover:bg-primary-700 text-white font-semibold rounded-xl shadow-sm shadow-primary-500/20 transition-all hover:scale-102 cursor-pointer"
            >
              <Plus className="w-4 h-4" />
              New Reconciliation
            </button>
            <button
              onClick={loadRuns}
              className="p-2.5 rounded-xl border border-slate-200 bg-white text-slate-600 hover:bg-slate-50 transition-colors cursor-pointer"
              title="Refresh"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Previous Runs List */}
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
          <div className="px-6 py-5 border-b border-slate-100 flex items-center justify-between">
            <h2 className="text-base font-bold text-slate-900">Reconciliation Runs</h2>
            <span className="text-xs font-medium text-slate-500">
              {runs.length} {runs.length === 1 ? "run" : "runs"} recorded
            </span>
          </div>

          {loadingRuns ? (
            <div className="py-20 flex flex-col items-center justify-center text-slate-400 gap-3">
              <Loader2 className="w-7 h-7 animate-spin text-primary-600" />
              <p className="text-sm font-medium">Loading reconciliation history...</p>
            </div>
          ) : runs.length === 0 ? (
            <div className="py-20 text-center px-4">
              <div className="w-14 h-14 rounded-2xl bg-primary-50 text-primary-600 flex items-center justify-center mx-auto mb-4 border border-primary-100">
                <FileSpreadsheet className="w-7 h-7" />
              </div>
              <h3 className="text-base font-bold text-slate-900">No reconciliation runs yet</h3>
              <p className="text-sm text-slate-500 mt-1 max-w-sm mx-auto">
                Start your first reconciliation by uploading a GSTR-2B file and your Purchase Register.
              </p>
              <button
                onClick={() => setShowModal(true)}
                className="mt-5 inline-flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white text-sm font-semibold rounded-xl cursor-pointer"
              >
                <Plus className="w-4 h-4" /> Start First Run
              </button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 text-slate-600 text-xs uppercase font-semibold border-b border-slate-100">
                  <tr>
                    <th className="px-6 py-3.5">Client GSTIN</th>
                    <th className="px-6 py-3.5">Tax Period</th>
                    <th className="px-6 py-3.5">Status</th>
                    <th className="px-6 py-3.5">Records</th>
                    <th className="px-6 py-3.5">Matched</th>
                    <th className="px-6 py-3.5">Mismatches</th>
                    <th className="px-6 py-3.5">Pending Review</th>
                    <th className="px-6 py-3.5 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {runs.map((r) => (
                    <tr key={r.id} className="hover:bg-slate-50/80 transition-colors">
                      <td className="px-6 py-4 font-mono font-semibold text-slate-900">
                        {r.company_gstin}
                      </td>
                      <td className="px-6 py-4 font-medium text-slate-700">
                        {r.tax_period}
                      </td>
                      <td className="px-6 py-4">{renderStatusBadge(r.status)}</td>
                      <td className="px-6 py-4 text-slate-600 text-xs">
                        <div>Books: <span className="font-semibold text-slate-800">{r.total_books_records}</span></div>
                        <div>GSTR-2B: <span className="font-semibold text-slate-800">{r.total_gstr2b_records}</span></div>
                      </td>
                      <td className="px-6 py-4 font-semibold text-emerald-600">
                        {r.matched_count}
                      </td>
                      <td className="px-6 py-4 font-semibold text-rose-600">
                        {r.mismatch_count}
                      </td>
                      <td className="px-6 py-4">
                        {r.pending_reviews > 0 ? (
                          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
                            {r.pending_reviews} pending
                          </span>
                        ) : (
                          <span className="text-xs text-slate-400 font-medium">None</span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <Link
                          href={`/gst-reconciliation/${r.id}`}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-100 hover:bg-primary-50 text-slate-700 hover:text-primary-700 transition-colors"
                        >
                          View Report <ArrowRight className="w-3.5 h-3.5" />
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* New Reconciliation Modal */}
      <AnimatePresence>
        {showModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs overflow-y-auto">
            <motion.div
              initial={{ opacity: 0, scale: 0.96 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.96 }}
              className="bg-white w-full max-w-4xl rounded-2xl shadow-xl border border-slate-200 overflow-hidden my-8"
            >
              {/* Modal Header */}
              <div className="px-6 py-5 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
                <div>
                  <h3 className="text-lg font-bold text-slate-900">New GST Reconciliation</h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Configure client GSTIN, upload statement files, and confirm column mappings.
                  </p>
                </div>
                <button
                  onClick={() => setShowModal(false)}
                  className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 cursor-pointer"
                >
                  <XCircle className="w-5 h-5" />
                </button>
              </div>

              {/* Modal Form Body */}
              <div className="p-6 space-y-6 max-h-[75vh] overflow-y-auto">
                {startError && (
                  <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 shrink-0" />
                    <span>{startError}</span>
                  </div>
                )}

                {/* Metadata Row */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1.5 uppercase">
                      Company GSTIN (15 Digits)
                    </label>
                    <input
                      type="text"
                      maxLength={15}
                      placeholder="e.g. 27ABCDE1234F1Z5"
                      value={companyGstin}
                      onChange={(e) => setCompanyGstin(e.target.value.toUpperCase())}
                      className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-sm font-mono tracking-wider focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent uppercase"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1.5 uppercase">
                      Tax Period
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. 04-2024 or 2024-04"
                      value={taxPeriod}
                      onChange={(e) => setTaxPeriod(e.target.value)}
                      className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    />
                  </div>
                </div>

                {/* Upload GSTR-2B Section */}
                <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-sm font-bold text-slate-900 flex items-center gap-1.5">
                        <FileSpreadsheet className="w-4 h-4 text-indigo-600" />
                        1. GSTR-2B Statement (Excel / CSV)
                      </h4>
                      <p className="text-xs text-slate-500">Government portal export of auto-drafted ITC statement.</p>
                    </div>
                    {gstr2bPreview && (
                      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                        <Check className="w-3.5 h-3.5" /> Auto-Mapped ({Object.keys(gstr2bMapping).length} cols)
                      </span>
                    )}
                  </div>

                  {!gstr2bPreview ? (
                    <label className="border-2 border-dashed border-slate-300 hover:border-primary-500 bg-white rounded-xl p-5 flex flex-col items-center justify-center cursor-pointer transition-colors group">
                      <input
                        type="file"
                        accept=".xlsx,.csv,.xls"
                        className="hidden"
                        onChange={(e) => e.target.files?.[0] && handleGstr2bUpload(e.target.files[0])}
                      />
                      {uploadingGstr2b ? (
                        <div className="flex items-center gap-2 text-sm text-primary-600 font-medium">
                          <Loader2 className="w-4 h-4 animate-spin" /> Inspecting & auto-mapping columns...
                        </div>
                      ) : (
                        <>
                          <Upload className="w-6 h-6 text-slate-400 group-hover:text-primary-600 mb-1.5 transition-colors" />
                          <span className="text-xs font-semibold text-slate-700">Click to upload GSTR-2B (.xlsx, .csv)</span>
                        </>
                      )}
                    </label>
                  ) : (
                    <div className="text-xs text-slate-600 bg-white p-3 rounded-lg border border-slate-200 space-y-2">
                      <div className="flex items-center justify-between font-medium">
                        <span>File: <strong className="text-slate-800">{gstr2bPreview.filename}</strong></span>
                        <span>Sheet: <strong className="text-slate-800">{gstr2bPreview.active_sheet}</strong></span>
                        <button
                          onClick={() => { setGstr2bPreview(null); setGstr2bFile(null); }}
                          className="text-rose-600 hover:underline cursor-pointer"
                        >
                          Change File
                        </button>
                      </div>
                      <div className="text-[11px] text-slate-500">
                        Mapped fields: {Object.keys(gstr2bMapping).join(", ")}
                      </div>
                    </div>
                  )}
                </div>

                {/* Upload Purchase Register Section */}
                <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-sm font-bold text-slate-900 flex items-center gap-1.5">
                        <FileSpreadsheet className="w-4 h-4 text-emerald-600" />
                        2. Purchase Register (Excel / CSV)
                      </h4>
                      <p className="text-xs text-slate-500">Books of accounts register from Tally, Busy, SAP, or Zoho.</p>
                    </div>
                    {prPreview && (
                      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                        <Check className="w-3.5 h-3.5" /> Auto-Mapped ({Object.keys(prMapping).length} cols)
                      </span>
                    )}
                  </div>

                  {!prPreview ? (
                    <label className="border-2 border-dashed border-slate-300 hover:border-primary-500 bg-white rounded-xl p-5 flex flex-col items-center justify-center cursor-pointer transition-colors group">
                      <input
                        type="file"
                        accept=".xlsx,.csv,.xls"
                        className="hidden"
                        onChange={(e) => e.target.files?.[0] && handlePrUpload(e.target.files[0])}
                      />
                      {uploadingPr ? (
                        <div className="flex items-center gap-2 text-sm text-primary-600 font-medium">
                          <Loader2 className="w-4 h-4 animate-spin" /> Inspecting & auto-mapping columns...
                        </div>
                      ) : (
                        <>
                          <Upload className="w-6 h-6 text-slate-400 group-hover:text-primary-600 mb-1.5 transition-colors" />
                          <span className="text-xs font-semibold text-slate-700">Click to upload Purchase Register (.xlsx, .csv)</span>
                        </>
                      )}
                    </label>
                  ) : (
                    <div className="text-xs text-slate-600 bg-white p-3 rounded-lg border border-slate-200 space-y-2">
                      <div className="flex items-center justify-between font-medium">
                        <span>File: <strong className="text-slate-800">{prPreview.filename}</strong></span>
                        <span>Sheet: <strong className="text-slate-800">{prPreview.active_sheet}</strong></span>
                        <button
                          onClick={() => { setPrPreview(null); setPrFile(null); }}
                          className="text-rose-600 hover:underline cursor-pointer"
                        >
                          Change File
                        </button>
                      </div>
                      <div className="text-[11px] text-slate-500">
                        Mapped fields: {Object.keys(prMapping).join(", ")}
                      </div>
                    </div>
                  )}
                </div>

                {/* Tolerances Config */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Taxable / Tax Tolerance (₹)
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      value={taxTol}
                      onChange={(e) => setTaxTol(e.target.value)}
                      className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs focus:outline-none focus:ring-2 focus:ring-primary-500"
                    />
                    <span className="text-[10px] text-slate-400">Differences within ₹{taxTol} are treated as rounding tolerance.</span>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Date Tolerance Window (Days)
                    </label>
                    <input
                      type="number"
                      value={dateTol}
                      onChange={(e) => setDateTol(e.target.value)}
                      className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs focus:outline-none focus:ring-2 focus:ring-primary-500"
                    />
                    <span className="text-[10px] text-slate-400">Matches invoices dated within ±{dateTol} days.</span>
                  </div>
                </div>
              </div>

              {/* Modal Footer */}
              <div className="px-6 py-4 bg-slate-50 border-t border-slate-100 flex items-center justify-between">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 text-sm font-medium text-slate-600 hover:text-slate-900 cursor-pointer"
                >
                  Cancel
                </button>

                <button
                  type="button"
                  onClick={handleStartReconciliation}
                  disabled={isStarting || !companyGstin || !gstr2bPreview || !prPreview}
                  className="inline-flex items-center gap-2 px-5 py-2.5 bg-primary-600 hover:bg-primary-700 disabled:opacity-50 text-white font-semibold rounded-xl shadow-xs transition-all cursor-pointer"
                >
                  {isStarting ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" /> Launching Reconciliation...
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4" /> Start Reconciliation Run
                    </>
                  )}
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
