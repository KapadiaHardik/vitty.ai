"use client";

import { useState, useEffect, use } from "react";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  CheckCircle,
  FileText,
  Printer,
  ShieldCheck,
  Clock,
  Check,
  XCircle,
  AlertTriangle,
} from "lucide-react";
import Link from "next/link";
import { getWorkflowReport } from "@/lib/api";

export default function WorkflowReport({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const { id } = resolvedParams;
  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchReport = async () => {
      try {
        const data = await getWorkflowReport(id);
        setReport(data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchReport();
  }, [id]);

  if (loading && !report) {
    return <div className="text-center text-slate-600 mt-20">Loading audit report...</div>;
  }

  if (!report) {
    return (
      <div className="text-center text-slate-700 mt-20">
        <p className="mb-4">Report not found.</p>
        <Link href="/workflows" className="text-primary-600 hover:text-primary-700 underline font-medium">
          Back to Workflows
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-6 md:p-12 max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between no-print">
        <Link
          href={`/workflows/${id}`}
          className="inline-flex items-center gap-2 text-slate-500 hover:text-slate-800 transition-colors text-sm font-medium"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Findings Review</span>
        </Link>

        <button
          onClick={() => window.print()}
          className="inline-flex items-center gap-2 bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-lg text-sm font-semibold transition-colors cursor-pointer shadow-sm shadow-primary-500/20"
        >
          <Printer className="w-4 h-4" />
          <span>Print / Save as PDF</span>
        </button>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-card p-8 sm:p-10 relative overflow-hidden space-y-10 border border-slate-200/90 shadow-sm"
      >
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-slate-200 pb-6">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 mb-2">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
              <span>Certified Audit Verification</span>
            </div>
            <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight flex items-center gap-3">
              <FileText className="text-primary-600" />
              Final Verification Report
            </h1>
            <p className="text-slate-500 font-mono text-xs mt-1">Workflow ID: {report.workflow_id}</p>
          </div>

          <div className="text-left sm:text-right text-xs text-slate-500">
            <p>Generated: {new Date().toLocaleDateString()}</p>
            <p className="mt-1">
              Status:{" "}
              <span className="font-semibold text-emerald-700 uppercase">{report.status}</span>
            </p>
          </div>
        </div>

        {/* Reviewed Documents */}
        <div>
          <h2 className="text-base font-semibold text-slate-900 mb-3">Reviewed Documents</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="bg-slate-50 rounded-xl p-4 border border-slate-200/80 space-y-1">
              <p className="text-slate-500 text-xs font-medium">Primary Invoice Document</p>
              <p className="text-slate-800 font-medium text-sm break-all">
                {report.invoice_filename || report.invoice_id}
              </p>
            </div>
            <div className="bg-slate-50 rounded-xl p-4 border border-slate-200/80 space-y-1">
              <p className="text-slate-500 text-xs font-medium">Supporting Reference Document (PO)</p>
              <p className="text-slate-800 font-medium text-sm break-all">
                {report.reference_filename || (report.reference_id ? report.reference_id : "None (Invoice Only)")}
              </p>
            </div>
          </div>
        </div>

        {/* Verification Summary Metrics */}
        <div>
          <h2 className="text-base font-semibold text-slate-900 mb-3">Audit Summary</h2>
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-slate-50 rounded-xl p-5 text-center border border-slate-200">
              <p className="text-2xl sm:text-3xl font-bold text-slate-900 mb-1">{report.summary.total_findings}</p>
              <p className="text-slate-500 text-xs font-medium">Total Findings</p>
            </div>
            <div className="bg-amber-50/70 rounded-xl p-5 text-center border border-amber-200">
              <p className="text-2xl sm:text-3xl font-bold text-amber-700 mb-1">{report.summary.pending_review}</p>
              <p className="text-amber-800 text-xs font-medium">Pending Review</p>
            </div>
            <div className="bg-emerald-50/70 rounded-xl p-5 text-center border border-emerald-200">
              <p className="text-2xl sm:text-3xl font-bold text-emerald-700 mb-1">{report.summary.reviewed}</p>
              <p className="text-emerald-800 text-xs font-medium">Reviewed & Closed</p>
            </div>
          </div>
        </div>

        {/* Findings Judgements */}
        <div>
          <h2 className="text-base font-semibold text-slate-900 mb-3">Verification Findings & Actions</h2>
          <div className="space-y-3">
            {report.findings.map((f: any) => (
              <div
                key={f.id}
                className="bg-white border border-slate-200 p-4 rounded-xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-2xs"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-slate-800 text-sm">{f.rule_id}</span>
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase ${
                        f.severity === "HIGH"
                          ? "bg-rose-50 text-rose-700 border border-rose-200"
                          : f.severity === "MEDIUM"
                          ? "bg-amber-50 text-amber-700 border border-amber-200"
                          : "bg-blue-50 text-blue-700 border border-blue-200"
                      }`}
                    >
                      {f.severity}
                    </span>
                  </div>
                  <p className="text-xs text-slate-600">{f.description}</p>
                  {f.source_evidence && (f.source_evidence.invoice_value || f.source_evidence.reference_value) && (
                    <div className="text-[11px] font-mono text-slate-500 mt-1">
                      {f.source_evidence.invoice_value && `Inv: ${f.source_evidence.invoice_value} `}
                      {f.source_evidence.reference_value && `| Ref: ${f.source_evidence.reference_value}`}
                    </div>
                  )}
                </div>

                <div className="shrink-0">
                  {f.decision === "ACCEPTED" ? (
                    <span className="inline-flex items-center gap-1.5 text-emerald-700 text-xs font-semibold bg-emerald-50 border border-emerald-200 px-3 py-1 rounded-full">
                      <Check className="w-3.5 h-3.5" /> Accepted by Auditor
                    </span>
                  ) : f.decision === "DISMISSED" ? (
                    <span className="inline-flex items-center gap-1.5 text-slate-500 text-xs font-semibold bg-slate-100 border border-slate-200 px-3 py-1 rounded-full">
                      Dismissed by Auditor
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1.5 text-amber-700 text-xs font-semibold bg-amber-50 border border-amber-200 px-3 py-1 rounded-full">
                      <AlertTriangle className="w-3.5 h-3.5" /> Pending Review
                    </span>
                  )}
                </div>
              </div>
            ))}

            {report.findings.length === 0 && (
              <div className="text-emerald-800 flex items-center gap-2 bg-emerald-50 p-4 rounded-xl border border-emerald-200 text-sm">
                <CheckCircle className="w-5 h-5 text-emerald-600" />
                <span>Clean record: 100% of mathematical validations passed with no variances.</span>
              </div>
            )}
          </div>
        </div>

        {/* Audit Trail */}
        {report.audit_trail && report.audit_trail.length > 0 && (
          <div>
            <h2 className="text-base font-semibold text-slate-900 mb-3 flex items-center gap-2">
              <Clock className="w-4 h-4 text-primary-600" />
              <span>Immutable Audit Trail</span>
            </h2>
            <div className="bg-slate-50 rounded-xl p-4 border border-slate-200 space-y-2">
              {report.audit_trail.map((item: any, idx: number) => (
                <div key={idx} className="flex items-center justify-between text-xs py-1.5 border-b border-slate-200/60 last:border-b-0">
                  <span className="text-slate-700 font-medium">{item.action}</span>
                  <span className="text-slate-500 font-mono">
                    {new Date(item.timestamp).toLocaleString([], { dateStyle: "short", timeStyle: "medium" })}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </motion.div>
    </div>
  );
}
