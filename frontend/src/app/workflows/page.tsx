"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  FileText,
  Play,
  Loader2,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Clock,
  ArrowRight,
  ShieldCheck,
  RefreshCw,
} from "lucide-react";
import Link from "next/link";
import { fetchDocuments, startWorkflow, fetchWorkflows } from "@/lib/api";

type DocumentStatus = "PENDING" | "PROCESSING" | "INDEXED" | "FAILED";

interface DocumentItem {
  id: string;
  filename: string;
  status: DocumentStatus;
}

interface WorkflowListItem {
  id: string;
  invoice_document_id: string;
  reference_document_id?: string;
  invoice_filename?: string;
  reference_filename?: string;
  status: "STARTED" | "IN_REVIEW" | "APPROVED" | "REJECTED" | "FAILED";
  created_at: string;
  total_findings: number;
  pending_reviews: number;
}

export default function WorkflowsPage() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [workflows, setWorkflows] = useState<WorkflowListItem[]>([]);
  const [invoiceId, setInvoiceId] = useState<string>("");
  const [referenceId, setReferenceId] = useState<string>("");
  const [isStarting, setIsStarting] = useState(false);
  const [loadingWorkflows, setLoadingWorkflows] = useState(true);
  const router = useRouter();

  const loadData = async () => {
    try {
      const [docsData, workflowsData] = await Promise.all([
        fetchDocuments().catch(() => ({ items: [] })),
        fetchWorkflows().catch(() => []),
      ]);
      setDocuments(docsData.items?.filter((d: DocumentItem) => d.status === "INDEXED") || []);
      setWorkflows(workflowsData || []);
    } catch (err) {
      console.error("Failed to load workflow data", err);
    } finally {
      setLoadingWorkflows(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleStart = async () => {
    if (!invoiceId) return;
    setIsStarting(true);
    try {
      const result = await startWorkflow(invoiceId, referenceId || undefined);
      const targetId = result.id || result.workflow_id;
      if (router && targetId) {
        router.push(`/workflows/${targetId}`);
      }
    } catch (err) {
      alert("Failed to start workflow");
      setIsStarting(false);
    }
  };

  const renderStatusBadge = (status: WorkflowListItem["status"]) => {
    switch (status) {
      case "STARTED":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200">
            <Loader2 className="w-3.5 h-3.5 animate-spin" /> In Progress
          </span>
        );
      case "IN_REVIEW":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-200">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-600" /> Needs Review
          </span>
        );
      case "APPROVED":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle className="w-3.5 h-3.5 text-emerald-600" /> Verified
          </span>
        );
      case "REJECTED":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
            <XCircle className="w-3.5 h-3.5 text-rose-600" /> Rejected
          </span>
        );
      case "FAILED":
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-red-50 text-red-700 border border-red-200">
            <XCircle className="w-3.5 h-3.5 text-red-600" /> Failed
          </span>
        );
    }
  };

  return (
    <div className="min-h-screen p-6 md:p-12 max-w-5xl mx-auto space-y-10">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-primary-50 text-primary-700 border border-primary-200 mb-2">
            <ShieldCheck className="w-3.5 h-3.5 text-primary-600" />
            <span>CA & Auditor Workflow Engine</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
            Invoice Verification & Audit
          </h1>
          <p className="text-slate-600 text-sm sm:text-base mt-1">
            Automate 2-way matching between Invoices and Purchase Orders with deterministic arithmetic validation.
          </p>
        </div>

        <button
          onClick={loadData}
          className="self-start sm:self-center inline-flex items-center gap-2 px-3.5 py-2 rounded-xl bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 shadow-2xs transition-colors text-sm font-semibold cursor-pointer"
        >
          <RefreshCw className="w-4 h-4 text-slate-500" />
          <span>Refresh</span>
        </button>
      </div>

      {/* Start Workflow Card */}
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full glass-card p-6 sm:p-8 flex flex-col gap-6 shadow-sm"
      >
        <div className="flex items-center gap-3 pb-4 border-b border-slate-100">
          <div className="w-10 h-10 rounded-xl bg-primary-50 border border-primary-200 flex items-center justify-center text-primary-600">
            <Play className="w-5 h-5 ml-0.5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-slate-900">Start New Verification</h2>
            <p className="text-xs text-slate-500">
              Select an invoice and optional supporting document to run automated checks.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
              Invoice Document <span className="text-rose-500">*</span>
            </label>
            <select
              value={invoiceId}
              onChange={(e) => setInvoiceId(e.target.value)}
              className="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 text-slate-800 text-sm outline-none focus:bg-white focus:border-primary-500 transition-colors shadow-2xs"
            >
              <option value="" className="text-slate-500">
                -- Choose Indexed Invoice --
              </option>
              {documents.map((doc) => (
                <option key={doc.id} value={doc.id} className="text-slate-800">
                  {doc.filename}
                </option>
              ))}
            </select>
            {documents.length === 0 && (
              <p className="text-xs text-amber-600 mt-2 font-medium">
                No indexed documents found. Please upload a PDF on the{" "}
                <Link href="/documents" className="underline hover:text-primary-700">
                  Documents
                </Link>{" "}
                page first.
              </p>
            )}
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
              Supporting Document (Purchase Order / GRN)
            </label>
            <select
              value={referenceId}
              onChange={(e) => setReferenceId(e.target.value)}
              className="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 text-slate-800 text-sm outline-none focus:bg-white focus:border-primary-500 transition-colors shadow-2xs"
            >
              <option value="" className="text-slate-500">
                -- None (Invoice Only) --
              </option>
              {documents
                .filter((doc) => doc.id !== invoiceId)
                .map((doc) => (
                  <option key={doc.id} value={doc.id} className="text-slate-800">
                    {doc.filename}
                  </option>
                ))}
            </select>
          </div>
        </div>

        <button
          onClick={handleStart}
          disabled={!invoiceId || isStarting}
          className="w-full flex items-center justify-center gap-2 bg-primary-600 hover:bg-primary-500 disabled:opacity-50 text-white py-3.5 rounded-xl font-semibold shadow-md shadow-primary-500/20 transition-all cursor-pointer disabled:cursor-not-allowed text-sm"
        >
          {isStarting ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Starting Verification...</span>
            </>
          ) : (
            <>
              <Play className="w-4 h-4" />
              <span>Run Automated Verification</span>
            </>
          )}
        </button>
      </motion.div>

      {/* Workflow History Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
            <Clock className="w-5 h-5 text-primary-600" />
            <span>Verification History ({workflows.length})</span>
          </h2>
        </div>

        {loadingWorkflows ? (
          <div className="glass-card p-12 text-center shadow-xs">
            <Loader2 className="w-8 h-8 text-primary-600 animate-spin mx-auto mb-3" />
            <p className="text-slate-500 text-sm">Loading verification runs...</p>
          </div>
        ) : workflows.length === 0 ? (
          <div className="glass-card p-12 text-center space-y-3 shadow-xs">
            <div className="w-12 h-12 rounded-2xl bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-400 mx-auto">
              <FileText className="w-6 h-6" />
            </div>
            <h3 className="text-base font-semibold text-slate-900">No Verification Runs Yet</h3>
            <p className="text-slate-500 text-xs max-w-md mx-auto">
              Select an invoice above to trigger your first automated arithmetic and discrepancy audit.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {workflows.map((wf) => (
              <motion.div
                key={wf.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className="glass-card p-5 hover:border-slate-300 transition-all flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-xs"
              >
                <div className="space-y-1.5 flex-1 min-w-0">
                  <div className="flex items-center gap-2.5 flex-wrap">
                    <span className="font-bold text-slate-900 text-sm truncate">
                      {wf.invoice_filename || "Invoice Document"}
                    </span>
                    {wf.reference_filename && (
                      <span className="text-xs px-2 py-0.5 rounded-md bg-slate-100 border border-slate-200 text-slate-600 font-medium">
                        vs. {wf.reference_filename}
                      </span>
                    )}
                    {renderStatusBadge(wf.status)}
                  </div>

                  <div className="flex items-center gap-4 text-xs text-slate-500">
                    <span>
                      ID: <span className="font-mono text-slate-600">{wf.id.substring(0, 8)}...</span>
                    </span>
                    <span>
                      Created: {new Date(wf.created_at).toLocaleString([], { dateStyle: "short", timeStyle: "short" })}
                    </span>
                    <span>
                      Findings:{" "}
                      <span
                        className={`font-semibold ${
                          wf.total_findings > 0 ? "text-amber-700" : "text-emerald-700"
                        }`}
                      >
                        {wf.total_findings}
                      </span>
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-2 self-end md:self-center shrink-0">
                  <Link
                    href={`/workflows/${wf.id}`}
                    className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-semibold transition-colors border border-slate-200"
                  >
                    <span>Inspect</span>
                    <ArrowRight className="w-3.5 h-3.5 text-slate-500" />
                  </Link>

                  {(wf.status === "APPROVED" || wf.status === "REJECTED") && (
                    <Link
                      href={`/workflows/${wf.id}/report`}
                      className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-primary-50 hover:bg-primary-100 text-primary-700 border border-primary-200 text-xs font-semibold transition-colors"
                    >
                      <FileText className="w-3.5 h-3.5" />
                      <span>Report</span>
                    </Link>
                  )}
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
