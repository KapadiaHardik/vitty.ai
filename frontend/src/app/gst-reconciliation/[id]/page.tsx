"use client";

import { useState, useEffect, use } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  FileSpreadsheet,
  Download,
  Loader2,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Clock,
  ArrowLeft,
  Search,
  Filter,
  Check,
  RefreshCw,
  ExternalLink,
  HelpCircle,
  FileText,
  AlertCircle,
  Layers,
  ChevronRight,
  MessageSquare,
} from "lucide-react";
import Link from "next/link";
import {
  getGSTRun,
  fetchGSTDiscrepancies,
  reviewGSTDiscrepancy,
  getGSTExportDownloadUrl,
} from "@/lib/api";

interface NormalizedInvoice {
  id: string;
  source_type: "GSTR_2B" | "PURCHASE_REGISTER";
  supplier_gstin?: string;
  supplier_name?: string;
  invoice_number_raw?: string;
  invoice_number_norm?: string;
  invoice_date?: string;
  doc_type: "INV" | "CRN" | "DBN";
  taxable_value: string;
  igst: string;
  cgst: string;
  sgst: string;
  cess: string;
  invoice_total: string;
  pos?: string;
  source_file?: string;
  source_sheet?: string;
  source_row_index?: number;
  is_valid: boolean;
  validation_errors?: string[];
}

interface DiscrepancyDetail {
  id: string;
  match_id: string;
  category: string;
  books_value?: string;
  gstr2b_value?: string;
  difference?: string;
  explanation?: string;
  suggested_action?: string;
  review_status: "PENDING" | "RESOLVED" | "ACCEPTED_DIFF" | "REJECTED_MATCH" | "VENDOR_FOLLOW_UP";
  reviewer_notes?: string;
  reviewed_at?: string;
  match_stage?: string;
  confidence_score?: number;
  books_invoice?: NormalizedInvoice;
  gstr2b_invoice?: NormalizedInvoice;
}

interface RunDetail {
  id: string;
  company_gstin: string;
  tax_period: string;
  status: "PENDING" | "PARSING" | "MATCHING" | "COMPLETED" | "FAILED";
  error_message?: string;
  created_at: string;
  gstr2b_filename?: string;
  purchase_register_filename?: string;
  metrics: {
    total_books_records: number;
    total_gstr2b_records: number;
    matched_count: number;
    books_only_count: number;
    gstr2b_only_count: number;
    taxable_mismatch_count: number;
    tax_mismatch_count: number;
    date_mismatch_count: number;
    duplicate_count: number;
    potential_match_count: number;
    invalid_record_count: number;
    total_books_taxable: string;
    total_gstr2b_taxable: string;
    diff_taxable: string;
    total_books_igst: string;
    total_gstr2b_igst: string;
    diff_igst: string;
    total_books_cgst: string;
    total_gstr2b_cgst: string;
    diff_cgst: string;
    total_books_sgst: string;
    total_gstr2b_sgst: string;
    diff_sgst: string;
    total_books_cess: string;
    total_gstr2b_cess: string;
    diff_cess: string;
    pending_reviews: number;
    resolved_reviews: number;
  };
}

const CATEGORY_TABS = [
  { id: "ALL", label: "All Items" },
  { id: "MATCHED", label: "Matched" },
  { id: "BOOKS_ONLY", label: "Books Only" },
  { id: "GSTR2B_ONLY", label: "GSTR-2B Only" },
  { id: "TAXABLE_VALUE_MISMATCH", label: "Taxable Mismatch" },
  { id: "IGST_MISMATCH", label: "Tax Component Mismatch" },
  { id: "POTENTIAL_MATCH", label: "Potential Matches" },
  { id: "DUPLICATE_INVOICE", label: "Duplicates" },
  { id: "INVALID_OR_INCOMPLETE_RECORD", label: "Invalid Records" },
];

export default function GSTReconciliationDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = use(params);
  const runId = resolvedParams.id;
  const router = useRouter();

  const [run, setRun] = useState<RunDetail | null>(null);
  const [discrepancies, setDiscrepancies] = useState<DiscrepancyDetail[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [activeCategory, setActiveCategory] = useState("ALL");
  const [reviewStatusFilter, setReviewStatusFilter] = useState("ALL");
  const [searchQuery, setSearchQuery] = useState("");

  // Side-by-Side Review Drawer
  const [selectedDiscrepancy, setSelectedDiscrepancy] = useState<DiscrepancyDetail | null>(null);
  const [reviewNotes, setReviewNotes] = useState("");
  const [submittingReview, setSubmittingReview] = useState(false);

  const loadRunData = async () => {
    try {
      const runData = await getGSTRun(runId);
      setRun(runData);

      if (runData.status === "COMPLETED" || runData.status === "FAILED") {
        const discs = await fetchGSTDiscrepancies(runId, {
          category: activeCategory !== "ALL" ? activeCategory : undefined,
          review_status: reviewStatusFilter !== "ALL" ? reviewStatusFilter : undefined,
          search: searchQuery.trim() || undefined,
        });
        setDiscrepancies(discs || []);
      }
    } catch (err) {
      console.error("Failed to load run details", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRunData();
  }, [activeCategory, reviewStatusFilter, searchQuery]);

  useEffect(() => {
    // Poll while processing
    if (run && (run.status === "PENDING" || run.status === "PARSING" || run.status === "MATCHING")) {
      const interval = setInterval(loadRunData, 3000);
      return () => clearInterval(interval);
    }
  }, [run?.status]);

  const handleReviewAction = async (decision: string) => {
    if (!selectedDiscrepancy) return;
    setSubmittingReview(true);
    try {
      await reviewGSTDiscrepancy(runId, {
        discrepancy_id: selectedDiscrepancy.id,
        review_status: decision,
        reviewer_notes: reviewNotes.trim() || undefined,
      });

      // Update locally
      setSelectedDiscrepancy((prev) => prev ? { ...prev, review_status: decision as any, reviewer_notes: reviewNotes } : null);
      setDiscrepancies((prev) =>
        prev.map((d) => (d.id === selectedDiscrepancy.id ? { ...d, review_status: decision as any, reviewer_notes: reviewNotes } : d))
      );
      loadRunData();
    } catch (err: any) {
      alert(err.message || "Failed to update review decision");
    } finally {
      setSubmittingReview(false);
    }
  };

  const getCategoryBadge = (category: string) => {
    switch (category) {
      case "MATCHED":
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">Matched</span>;
      case "BOOKS_ONLY":
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">Books Only</span>;
      case "GSTR2B_ONLY":
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">GSTR-2B Only</span>;
      case "TAXABLE_VALUE_MISMATCH":
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-orange-50 text-orange-700 border border-orange-200">Taxable Diff</span>;
      case "IGST_MISMATCH":
      case "CGST_MISMATCH":
      case "SGST_MISMATCH":
      case "CESS_MISMATCH":
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200">Tax Diff</span>;
      case "POTENTIAL_MATCH":
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-purple-50 text-purple-700 border border-purple-200">Potential Match</span>;
      case "DUPLICATE_INVOICE":
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-red-50 text-red-700 border border-red-200">Duplicate</span>;
      default:
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-700">{category}</span>;
    }
  };

  const getReviewBadge = (status: string) => {
    switch (status) {
      case "RESOLVED":
        return <span className="px-2 py-0.5 rounded-md text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">Resolved</span>;
      case "ACCEPTED_DIFF":
        return <span className="px-2 py-0.5 rounded-md text-[11px] font-semibold bg-blue-50 text-blue-700 border border-blue-200">Accepted Diff</span>;
      case "VENDOR_FOLLOW_UP":
        return <span className="px-2 py-0.5 rounded-md text-[11px] font-semibold bg-amber-50 text-amber-700 border border-amber-200">Vendor Follow-up</span>;
      case "REJECTED_MATCH":
        return <span className="px-2 py-0.5 rounded-md text-[11px] font-semibold bg-rose-50 text-rose-700 border border-rose-200">Match Rejected</span>;
      default:
        return <span className="px-2 py-0.5 rounded-md text-[11px] font-semibold bg-slate-100 text-slate-600">Pending Review</span>;
    }
  };

  if (loading && !run) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50/50">
        <div className="flex flex-col items-center gap-3 text-slate-400">
          <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
          <p className="text-sm font-medium">Loading reconciliation workspace...</p>
        </div>
      </div>
    );
  }

  if (!run) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50/50">
        <div className="text-center p-8 bg-white rounded-2xl border border-slate-200 shadow-xs max-w-md">
          <XCircle className="w-10 h-10 text-rose-500 mx-auto mb-3" />
          <h2 className="text-lg font-bold text-slate-900">Reconciliation Run Not Found</h2>
          <p className="text-sm text-slate-500 mt-1 mb-5">The requested reconciliation run does not exist or has been removed.</p>
          <Link href="/gst-reconciliation" className="px-4 py-2 bg-primary-600 text-white rounded-xl text-sm font-semibold">
            Back to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  const isProcessing = run.status === "PENDING" || run.status === "PARSING" || run.status === "MATCHING";

  return (
    <div className="min-h-screen bg-slate-50/50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
        {/* Navigation Breadcrumb & Actions */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Link
              href="/gst-reconciliation"
              className="p-2 rounded-xl border border-slate-200 bg-white text-slate-600 hover:bg-slate-50 transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl sm:text-2xl font-extrabold text-slate-900 font-mono">
                  {run.company_gstin}
                </h1>
                <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-200">
                  {run.tax_period}
                </span>
                {isProcessing ? (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200 animate-pulse">
                    <Loader2 className="w-3.5 h-3.5 animate-spin" /> {run.status}
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> Complete
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Files: {run.purchase_register_filename} (Books) ↔ {run.gstr2b_filename} (GSTR-2B)
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={loadRunData}
              className="p-2.5 rounded-xl border border-slate-200 bg-white text-slate-600 hover:bg-slate-50 transition-colors"
              title="Refresh"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
            <a
              href={getGSTExportDownloadUrl(runId)}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-4 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-xl text-sm shadow-xs transition-colors"
            >
              <Download className="w-4 h-4" /> Export Excel Report
            </a>
          </div>
        </div>

        {/* Processing Notification */}
        {isProcessing && (
          <div className="p-4 rounded-2xl bg-blue-50 border border-blue-200 text-blue-800 text-sm flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Loader2 className="w-5 h-5 animate-spin text-blue-600 shrink-0" />
              <div>
                <strong>Reconciliation engine is running...</strong>
                <p className="text-xs text-blue-700 mt-0.5">
                  Parsing records, applying deterministic 4-stage matching, and calculating tax variances. This screen auto-updates.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Top KPI Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 sm:gap-4">
          <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-xs">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Records</span>
            <div className="text-xl font-bold text-slate-900 mt-1">
              {run.metrics.total_books_records + run.metrics.total_gstr2b_records}
            </div>
            <div className="text-[11px] text-slate-400 mt-0.5">
              PR: {run.metrics.total_books_records} | 2B: {run.metrics.total_gstr2b_records}
            </div>
          </div>

          <div className="bg-white p-4 rounded-2xl border border-emerald-100 shadow-xs">
            <span className="text-xs font-semibold text-emerald-700 uppercase tracking-wider">Fully Matched</span>
            <div className="text-xl font-bold text-emerald-600 mt-1">
              {run.metrics.matched_count}
            </div>
            <div className="text-[11px] text-emerald-600/80 mt-0.5">Ready for ITC Claim</div>
          </div>

          <div className="bg-white p-4 rounded-2xl border border-rose-100 shadow-xs">
            <span className="text-xs font-semibold text-rose-700 uppercase tracking-wider">Books Only</span>
            <div className="text-xl font-bold text-rose-600 mt-1">
              {run.metrics.books_only_count}
            </div>
            <div className="text-[11px] text-rose-600/80 mt-0.5">Missing in GSTR-2B</div>
          </div>

          <div className="bg-white p-4 rounded-2xl border border-amber-100 shadow-xs">
            <span className="text-xs font-semibold text-amber-700 uppercase tracking-wider">GSTR-2B Only</span>
            <div className="text-xl font-bold text-amber-600 mt-1">
              {run.metrics.gstr2b_only_count}
            </div>
            <div className="text-[11px] text-amber-600/80 mt-0.5">Not Booked in ERP</div>
          </div>

          <div className="bg-white p-4 rounded-2xl border border-indigo-100 shadow-xs">
            <span className="text-xs font-semibold text-indigo-700 uppercase tracking-wider">Tax Mismatches</span>
            <div className="text-xl font-bold text-indigo-600 mt-1">
              {run.metrics.taxable_mismatch_count + run.metrics.tax_mismatch_count}
            </div>
            <div className="text-[11px] text-indigo-600/80 mt-0.5">Rate or Value Diff</div>
          </div>

          <div className="bg-white p-4 rounded-2xl border border-purple-100 shadow-xs">
            <span className="text-xs font-semibold text-purple-700 uppercase tracking-wider">Potential Match</span>
            <div className="text-xl font-bold text-purple-600 mt-1">
              {run.metrics.potential_match_count}
            </div>
            <div className="text-[11px] text-purple-600/80 mt-0.5">Needs CA Decision</div>
          </div>
        </div>

        {/* Financial Delta Bar */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs space-y-3">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Financial Summary & Variance
            </h3>
            <span className="text-xs text-slate-400 font-medium">All figures in INR (₹)</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-5 gap-4 text-xs">
            <div>
              <span className="text-slate-500">Taxable Value</span>
              <div className="font-semibold text-slate-800 mt-0.5">
                Books: ₹{parseFloat(run.metrics.total_books_taxable).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
              </div>
              <div className="text-slate-500">
                2B: ₹{parseFloat(run.metrics.total_gstr2b_taxable).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
              </div>
              <div className={`font-bold mt-1 ${parseFloat(run.metrics.diff_taxable) !== 0 ? "text-rose-600" : "text-emerald-600"}`}>
                Δ ₹{parseFloat(run.metrics.diff_taxable).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
              </div>
            </div>

            <div>
              <span className="text-slate-500">Integrated Tax (IGST)</span>
              <div className="font-semibold text-slate-800 mt-0.5">
                Books: ₹{parseFloat(run.metrics.total_books_igst).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
              </div>
              <div className="text-slate-500">
                2B: ₹{parseFloat(run.metrics.total_gstr2b_igst).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
              </div>
              <div className={`font-bold mt-1 ${parseFloat(run.metrics.diff_igst) !== 0 ? "text-rose-600" : "text-emerald-600"}`}>
                Δ ₹{parseFloat(run.metrics.diff_igst).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
              </div>
            </div>

            <div>
              <span className="text-slate-500">Central Tax (CGST)</span>
              <div className="font-semibold text-slate-800 mt-0.5">
                Books: ₹{parseFloat(run.metrics.total_books_cgst).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
              </div>
              <div className="text-slate-500">
                2B: ₹{parseFloat(run.metrics.total_gstr2b_cgst).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
              </div>
              <div className={`font-bold mt-1 ${parseFloat(run.metrics.diff_cgst) !== 0 ? "text-rose-600" : "text-emerald-600"}`}>
                Δ ₹{parseFloat(run.metrics.diff_cgst).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
              </div>
            </div>

            <div>
              <span className="text-slate-500">State Tax (SGST)</span>
              <div className="font-semibold text-slate-800 mt-0.5">
                Books: ₹{parseFloat(run.metrics.total_books_sgst).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
              </div>
              <div className="text-slate-500">
                2B: ₹{parseFloat(run.metrics.total_gstr2b_sgst).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
              </div>
              <div className={`font-bold mt-1 ${parseFloat(run.metrics.diff_sgst) !== 0 ? "text-rose-600" : "text-emerald-600"}`}>
                Δ ₹{parseFloat(run.metrics.diff_sgst).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
              </div>
            </div>

            <div>
              <span className="text-slate-500">Cess</span>
              <div className="font-semibold text-slate-800 mt-0.5">
                Books: ₹{parseFloat(run.metrics.total_books_cess).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
              </div>
              <div className="text-slate-500">
                2B: ₹{parseFloat(run.metrics.total_gstr2b_cess).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
              </div>
              <div className={`font-bold mt-1 ${parseFloat(run.metrics.diff_cess) !== 0 ? "text-rose-600" : "text-emerald-600"}`}>
                Δ ₹{parseFloat(run.metrics.diff_cess).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
              </div>
            </div>
          </div>
        </div>

        {/* Filter Toolbar & Tab Bar */}
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
          {/* Tab list */}
          <div className="border-b border-slate-100 px-4 flex items-center gap-1 overflow-x-auto scrollbar-none">
            {CATEGORY_TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveCategory(tab.id)}
                className={`px-4 py-3 text-xs font-semibold border-b-2 whitespace-nowrap transition-colors cursor-pointer ${
                  activeCategory === tab.id
                    ? "border-primary-600 text-primary-600"
                    : "border-transparent text-slate-500 hover:text-slate-800 hover:border-slate-300"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Search & Status Filter bar */}
          <div className="p-4 border-b border-slate-100 flex flex-col sm:flex-row items-center justify-between gap-3">
            <div className="relative w-full sm:w-80">
              <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search GSTIN, Inv #, Supplier..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-3 py-2 rounded-xl border border-slate-200 text-xs focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>

            <div className="flex items-center gap-2 w-full sm:w-auto">
              <span className="text-xs text-slate-500 font-medium">Review Status:</span>
              <select
                value={reviewStatusFilter}
                onChange={(e) => setReviewStatusFilter(e.target.value)}
                className="px-3 py-1.5 rounded-xl border border-slate-200 text-xs text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="ALL">All Statuses</option>
                <option value="PENDING">Pending Review</option>
                <option value="RESOLVED">Resolved</option>
                <option value="ACCEPTED_DIFF">Accepted Diff</option>
                <option value="VENDOR_FOLLOW_UP">Vendor Follow-up</option>
                <option value="REJECTED_MATCH">Rejected Match</option>
              </select>
            </div>
          </div>

          {/* Table */}
          {discrepancies.length === 0 ? (
            <div className="py-16 text-center text-slate-400 text-xs">
              <FileSpreadsheet className="w-8 h-8 mx-auto mb-2 opacity-50" />
              No records matching the selected filter.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-600 uppercase font-semibold border-b border-slate-100">
                  <tr>
                    <th className="px-5 py-3">Category</th>
                    <th className="px-5 py-3">Supplier GSTIN & Name</th>
                    <th className="px-5 py-3">Invoice No</th>
                    <th className="px-5 py-3">Books Value</th>
                    <th className="px-5 py-3">GSTR-2B Value</th>
                    <th className="px-5 py-3">Variance</th>
                    <th className="px-5 py-3">Review</th>
                    <th className="px-5 py-3 text-right">Inspect</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {discrepancies.map((d) => {
                    const b = d.books_invoice;
                    const g = d.gstr2b_invoice;
                    const gstin = b?.supplier_gstin || g?.supplier_gstin || "—";
                    const supplierName = b?.supplier_name || g?.supplier_name || "—";
                    const invNo = b?.invoice_number_norm || g?.invoice_number_norm || "—";

                    return (
                      <tr
                        key={d.id}
                        onClick={() => {
                          setSelectedDiscrepancy(d);
                          setReviewNotes(d.reviewer_notes || "");
                        }}
                        className="hover:bg-slate-50/80 transition-colors cursor-pointer"
                      >
                        <td className="px-5 py-3.5">{getCategoryBadge(d.category)}</td>
                        <td className="px-5 py-3.5 font-mono">
                          <div className="font-semibold text-slate-900">{gstin}</div>
                          <div className="text-[11px] font-sans text-slate-500 truncate max-w-[180px]">{supplierName}</div>
                        </td>
                        <td className="px-5 py-3.5 font-mono font-medium text-slate-800">
                          {invNo}
                        </td>
                        <td className="px-5 py-3.5 text-slate-700">
                          {b ? `₹${parseFloat(b.taxable_value).toLocaleString("en-IN")}` : <span className="text-slate-400">Missing</span>}
                        </td>
                        <td className="px-5 py-3.5 text-slate-700">
                          {g ? `₹${parseFloat(g.taxable_value).toLocaleString("en-IN")}` : <span className="text-slate-400">Missing</span>}
                        </td>
                        <td className="px-5 py-3.5">
                          {d.difference && parseFloat(d.difference) !== 0 ? (
                            <span className="font-bold text-rose-600 font-mono">
                              ₹{parseFloat(d.difference).toLocaleString("en-IN")}
                            </span>
                          ) : (
                            <span className="text-slate-400 font-mono">₹0.00</span>
                          )}
                        </td>
                        <td className="px-5 py-3.5">{getReviewBadge(d.review_status)}</td>
                        <td className="px-5 py-3.5 text-right">
                          <button className="p-1 rounded-lg hover:bg-slate-200 text-slate-500">
                            <ChevronRight className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Side-by-Side Review Drawer / Modal */}
      <AnimatePresence>
        {selectedDiscrepancy && (
          <div className="fixed inset-0 z-50 flex items-center justify-end bg-slate-900/40 backdrop-blur-xs">
            <motion.div
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{ type: "spring", damping: 25, stiffness: 200 }}
              className="bg-white w-full max-w-2xl h-full shadow-2xl border-l border-slate-200 flex flex-col justify-between overflow-hidden"
            >
              {/* Drawer Header */}
              <div className="px-6 py-5 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                      Discrepancy Details
                    </span>
                    {getCategoryBadge(selectedDiscrepancy.category)}
                  </div>
                  <h3 className="text-base font-extrabold text-slate-900 mt-1">
                    Invoice #{selectedDiscrepancy.books_invoice?.invoice_number_norm || selectedDiscrepancy.gstr2b_invoice?.invoice_number_norm || "—"}
                  </h3>
                </div>
                <button
                  onClick={() => setSelectedDiscrepancy(null)}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 cursor-pointer"
                >
                  <XCircle className="w-5 h-5" />
                </button>
              </div>

              {/* Drawer Body (Side-by-Side comparison) */}
              <div className="p-6 overflow-y-auto space-y-6 flex-1 text-xs">
                {/* Explanation Banner */}
                <div className="p-4 rounded-xl bg-amber-50/80 border border-amber-200 text-amber-900 space-y-1">
                  <div className="font-semibold flex items-center gap-1.5">
                    <AlertTriangle className="w-4 h-4 text-amber-600" />
                    {selectedDiscrepancy.explanation}
                  </div>
                  {selectedDiscrepancy.suggested_action && (
                    <div className="text-[11px] text-amber-700 pl-5.5">
                      <strong>Suggested Action:</strong> {selectedDiscrepancy.suggested_action}
                    </div>
                  )}
                </div>

                {/* Side-by-Side Comparison Grid */}
                <div className="grid grid-cols-2 gap-4">
                  {/* Left Column: Purchase Register */}
                  <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/40 space-y-3">
                    <div className="font-bold text-slate-900 border-b border-slate-200 pb-2 flex items-center justify-between">
                      <span>Purchase Register</span>
                      <span className="text-[10px] text-slate-400">Books of Accounts</span>
                    </div>

                    {selectedDiscrepancy.books_invoice ? (
                      <div className="space-y-2">
                        <div>
                          <span className="text-slate-400">Supplier GSTIN:</span>
                          <div className="font-mono font-semibold text-slate-900">{selectedDiscrepancy.books_invoice.supplier_gstin}</div>
                        </div>
                        <div>
                          <span className="text-slate-400">Supplier Name:</span>
                          <div className="font-medium text-slate-800">{selectedDiscrepancy.books_invoice.supplier_name || "—"}</div>
                        </div>
                        <div>
                          <span className="text-slate-400">Invoice Number:</span>
                          <div className="font-mono font-semibold text-slate-900">{selectedDiscrepancy.books_invoice.invoice_number_norm}</div>
                        </div>
                        <div>
                          <span className="text-slate-400">Invoice Date:</span>
                          <div className="font-medium text-slate-800">{selectedDiscrepancy.books_invoice.invoice_date || "—"}</div>
                        </div>
                        <div className="border-t border-slate-200 pt-2 space-y-1">
                          <div className="flex justify-between">
                            <span className="text-slate-500">Taxable Value:</span>
                            <span className="font-bold text-slate-900">₹{selectedDiscrepancy.books_invoice.taxable_value}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-500">IGST:</span>
                            <span>₹{selectedDiscrepancy.books_invoice.igst}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-500">CGST:</span>
                            <span>₹{selectedDiscrepancy.books_invoice.cgst}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-500">SGST:</span>
                            <span>₹{selectedDiscrepancy.books_invoice.sgst}</span>
                          </div>
                          <div className="flex justify-between font-bold border-t border-slate-100 pt-1 text-slate-900">
                            <span>Total Value:</span>
                            <span>₹{selectedDiscrepancy.books_invoice.invoice_total}</span>
                          </div>
                        </div>
                        <div className="text-[10px] text-slate-400 pt-2">
                          Source: {selectedDiscrepancy.books_invoice.source_file} (Row {selectedDiscrepancy.books_invoice.source_row_index})
                        </div>
                      </div>
                    ) : (
                      <div className="py-12 text-center text-slate-400">
                        <AlertCircle className="w-6 h-6 mx-auto mb-1 text-rose-400" />
                        Missing in Purchase Register
                      </div>
                    )}
                  </div>

                  {/* Right Column: GSTR-2B */}
                  <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/40 space-y-3">
                    <div className="font-bold text-slate-900 border-b border-slate-200 pb-2 flex items-center justify-between">
                      <span>GSTR-2B Statement</span>
                      <span className="text-[10px] text-slate-400">GST Portal Filing</span>
                    </div>

                    {selectedDiscrepancy.gstr2b_invoice ? (
                      <div className="space-y-2">
                        <div>
                          <span className="text-slate-400">Supplier GSTIN:</span>
                          <div className="font-mono font-semibold text-slate-900">{selectedDiscrepancy.gstr2b_invoice.supplier_gstin}</div>
                        </div>
                        <div>
                          <span className="text-slate-400">Supplier Name:</span>
                          <div className="font-medium text-slate-800">{selectedDiscrepancy.gstr2b_invoice.supplier_name || "—"}</div>
                        </div>
                        <div>
                          <span className="text-slate-400">Invoice Number:</span>
                          <div className="font-mono font-semibold text-slate-900">{selectedDiscrepancy.gstr2b_invoice.invoice_number_norm}</div>
                        </div>
                        <div>
                          <span className="text-slate-400">Invoice Date:</span>
                          <div className="font-medium text-slate-800">{selectedDiscrepancy.gstr2b_invoice.invoice_date || "—"}</div>
                        </div>
                        <div className="border-t border-slate-200 pt-2 space-y-1">
                          <div className="flex justify-between">
                            <span className="text-slate-500">Taxable Value:</span>
                            <span className="font-bold text-slate-900">₹{selectedDiscrepancy.gstr2b_invoice.taxable_value}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-500">IGST:</span>
                            <span>₹{selectedDiscrepancy.gstr2b_invoice.igst}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-500">CGST:</span>
                            <span>₹{selectedDiscrepancy.gstr2b_invoice.cgst}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-500">SGST:</span>
                            <span>₹{selectedDiscrepancy.gstr2b_invoice.sgst}</span>
                          </div>
                          <div className="flex justify-between font-bold border-t border-slate-100 pt-1 text-slate-900">
                            <span>Total Value:</span>
                            <span>₹{selectedDiscrepancy.gstr2b_invoice.invoice_total}</span>
                          </div>
                        </div>
                        <div className="text-[10px] text-slate-400 pt-2">
                          Source: {selectedDiscrepancy.gstr2b_invoice.source_file} (Row {selectedDiscrepancy.gstr2b_invoice.source_row_index})
                        </div>
                      </div>
                    ) : (
                      <div className="py-12 text-center text-slate-400">
                        <AlertCircle className="w-6 h-6 mx-auto mb-1 text-rose-400" />
                        Missing in GSTR-2B Portal
                      </div>
                    )}
                  </div>
                </div>

                {/* Review Notes Input */}
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                    CA Reviewer Notes / Justification:
                  </label>
                  <textarea
                    rows={2}
                    placeholder="e.g. Rounding difference accepted; contacted vendor for GSTR-1 amendment..."
                    value={reviewNotes}
                    onChange={(e) => setReviewNotes(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                </div>
              </div>

              {/* Drawer Footer Actions */}
              <div className="p-4 bg-slate-50 border-t border-slate-100 flex flex-wrap items-center justify-between gap-2">
                <button
                  type="button"
                  onClick={() => handleReviewAction("REJECTED_MATCH")}
                  disabled={submittingReview}
                  className="px-3 py-2 rounded-xl text-xs font-semibold bg-rose-50 text-rose-700 hover:bg-rose-100 transition-colors cursor-pointer"
                >
                  Reject Match
                </button>

                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => handleReviewAction("VENDOR_FOLLOW_UP")}
                    disabled={submittingReview}
                    className="px-3 py-2 rounded-xl text-xs font-semibold bg-amber-50 text-amber-800 hover:bg-amber-100 transition-colors cursor-pointer"
                  >
                    Mark for Vendor Follow-up
                  </button>

                  <button
                    type="button"
                    onClick={() => handleReviewAction("ACCEPTED_DIFF")}
                    disabled={submittingReview}
                    className="px-3 py-2 rounded-xl text-xs font-semibold bg-blue-50 text-blue-700 hover:bg-blue-100 transition-colors cursor-pointer"
                  >
                    Accept Difference
                  </button>

                  <button
                    type="button"
                    onClick={() => handleReviewAction("RESOLVED")}
                    disabled={submittingReview}
                    className="px-4 py-2 rounded-xl text-xs font-semibold bg-emerald-600 hover:bg-emerald-700 text-white transition-colors cursor-pointer flex items-center gap-1.5"
                  >
                    <Check className="w-3.5 h-3.5" /> Mark Resolved
                  </button>
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
