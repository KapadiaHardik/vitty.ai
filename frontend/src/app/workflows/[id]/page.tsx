"use client";

import { useState, useEffect, use } from "react";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  Loader2,
  CheckCircle,
  AlertTriangle,
  XCircle,
  ChevronRight,
  FileText,
  ShieldCheck,
  Check,
  X,
  FileCheck,
} from "lucide-react";
import Link from "next/link";
import { getWorkflow, reviewFinding, decideWorkflow } from "@/lib/api";

export default function WorkflowDetails({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const { id } = resolvedParams;
  const [workflow, setWorkflow] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [reviewingId, setReviewingId] = useState<string | null>(null);
  const [isDeciding, setIsDeciding] = useState(false);

  const fetchWorkflowData = async () => {
    if (!id || id === "undefined") {
      setLoading(false);
      return;
    }
    try {
      const data = await getWorkflow(id);
      setWorkflow(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!id || id === "undefined") return;
    fetchWorkflowData();
    const interval = setInterval(() => {
      if (workflow?.status === "STARTED") {
        fetchWorkflowData();
      }
    }, 3000);
    return () => clearInterval(interval);
  }, [id, workflow?.status]);

  const handleReview = async (findingId: string, decision: "ACCEPTED" | "DISMISSED") => {
    setReviewingId(findingId);
    try {
      const reason = decision === "DISMISSED" ? "Dismissed by auditor" : "Accepted by auditor";
      await reviewFinding(id, findingId, decision, reason);
      await fetchWorkflowData();
    } catch (err) {
      alert("Failed to submit review");
    } finally {
      setReviewingId(null);
    }
  };

  const handleWorkflowDecision = async (decision: "APPROVED" | "REJECTED") => {
    setIsDeciding(true);
    try {
      await decideWorkflow(id, decision, `Auditor formally set status to ${decision}`);
      await fetchWorkflowData();
    } catch (err) {
      alert("Failed to update workflow status");
    } finally {
      setIsDeciding(false);
    }
  };

  if (loading && !workflow) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-10 h-10 text-primary-600 animate-spin" />
      </div>
    );
  }

  if (!workflow) {
    return (
      <div className="min-h-screen p-12 text-center text-slate-800">
        <p className="text-xl font-semibold mb-4">Workflow not found</p>
        <Link href="/workflows" className="text-primary-600 underline">
          Back to Workflows
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-6 md:p-12 max-w-5xl mx-auto space-y-8">
      {/* Navigation bar */}
      <div className="flex items-center justify-between">
        <Link
          href="/workflows"
          className="inline-flex items-center gap-2 text-slate-500 hover:text-slate-900 transition-colors text-sm font-semibold"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Workflows</span>
        </Link>

        <div className="flex items-center gap-3">
          <Link
            href={`/workflows/${id}/report`}
            className="inline-flex items-center gap-2 bg-primary-50 hover:bg-primary-100 text-primary-700 px-4 py-2 rounded-xl transition-colors text-sm font-semibold border border-primary-200 shadow-2xs"
          >
            <FileText className="w-4 h-4 text-primary-600" />
            <span>Audit Report</span>
            <ChevronRight className="w-4 h-4 text-primary-500" />
          </Link>
        </div>
      </div>

      {/* Main Workflow Details Card */}
      <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} className="glass-card p-6 sm:p-8 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 pb-6 mb-6">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h1 className="text-2xl font-extrabold text-slate-900">
                {workflow.invoice_filename || `Invoice ${workflow.id.substring(0, 8)}`}
              </h1>
            </div>
            <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-500 font-mono">
              <span>Workflow ID: {workflow.id}</span>
              {workflow.reference_filename && <span>Reference: {workflow.reference_filename}</span>}
            </div>
          </div>

          <div className="flex items-center gap-3">
            {workflow.status === "STARTED" ? (
              <span className="flex items-center gap-2 bg-blue-50 text-blue-700 px-4 py-2 rounded-full font-semibold border border-blue-200 text-xs">
                <Loader2 className="w-3.5 h-3.5 animate-spin" /> In Progress
              </span>
            ) : workflow.status === "IN_REVIEW" ? (
              <span className="flex items-center gap-2 bg-amber-50 text-amber-800 px-4 py-2 rounded-full font-semibold border border-amber-200 text-xs">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-600" /> Needs Review
              </span>
            ) : workflow.status === "APPROVED" ? (
              <span className="flex items-center gap-2 bg-emerald-50 text-emerald-700 px-4 py-2 rounded-full font-semibold border border-emerald-200 text-xs">
                <CheckCircle className="w-3.5 h-3.5 text-emerald-600" /> Verified & Approved
              </span>
            ) : workflow.status === "REJECTED" ? (
              <span className="flex items-center gap-2 bg-rose-50 text-rose-700 px-4 py-2 rounded-full font-semibold border border-rose-200 text-xs">
                <XCircle className="w-3.5 h-3.5 text-rose-600" /> Rejected
              </span>
            ) : (
              <span className="flex items-center gap-2 bg-red-50 text-red-700 px-4 py-2 rounded-full font-semibold border border-red-200 text-xs">
                <XCircle className="w-3.5 h-3.5 text-red-600" /> Failed
              </span>
            )}
          </div>
        </div>

        {/* Findings Section */}
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-primary-600" />
              <span>Discrepancy Findings ({workflow.findings?.length || 0})</span>
            </h2>

            {/* Quick action to approve / reject entire workflow */}
            {workflow.status === "IN_REVIEW" && (
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleWorkflowDecision("APPROVED")}
                  disabled={isDeciding}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border border-emerald-300 text-xs font-semibold transition-colors cursor-pointer"
                >
                  <Check className="w-3.5 h-3.5" />
                  <span>Approve All</span>
                </button>
                <button
                  onClick={() => handleWorkflowDecision("REJECTED")}
                  disabled={isDeciding}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-300 text-xs font-semibold transition-colors cursor-pointer"
                >
                  <X className="w-3.5 h-3.5" />
                  <span>Reject</span>
                </button>
              </div>
            )}
          </div>

          {workflow.findings?.length === 0 ? (
            <div className="p-8 rounded-2xl bg-emerald-50 border border-emerald-200 text-center space-y-2">
              <FileCheck className="w-8 h-8 text-emerald-600 mx-auto" />
              <h3 className="text-base font-bold text-emerald-800">Clean Invoice - No Discrepancies Found</h3>
              <p className="text-xs text-emerald-700/80">
                All deterministic arithmetic checks passed and values match supporting documents.
              </p>
            </div>
          ) : (
            <div className="space-y-3.5">
              {workflow.findings?.map((finding: any) => (
                <div
                  key={finding.id}
                  className="bg-slate-50/70 border border-slate-200/90 p-5 rounded-2xl flex flex-col md:flex-row gap-4 justify-between shadow-2xs"
                >
                  <div className="flex-1 space-y-2">
                    <div className="flex items-center gap-2">
                      <span
                        className={`text-[10px] px-2.5 py-0.5 rounded-full font-bold uppercase tracking-wide ${
                          finding.severity === "HIGH"
                            ? "bg-rose-50 text-rose-700 border border-rose-200"
                            : finding.severity === "MEDIUM"
                            ? "bg-amber-50 text-amber-800 border border-amber-200"
                            : "bg-blue-50 text-blue-700 border border-blue-200"
                        }`}
                      >
                        {finding.severity}
                      </span>
                      <span className="text-slate-800 font-bold text-sm">
                        {finding.type || finding.rule_id}
                      </span>
                    </div>

                    <p className="text-slate-700 text-sm leading-relaxed">{finding.explanation || finding.description}</p>

                    {(finding.field || finding.invoice_value || finding.reference_value) && (
                      <div className="text-xs font-mono text-slate-700 bg-white p-2.5 rounded-xl border border-slate-200/80 flex flex-wrap gap-4 shadow-2xs">
                        {finding.field && (
                          <span>
                            Field: <strong className="text-slate-900">{finding.field}</strong>
                          </span>
                        )}
                        {finding.invoice_value && (
                          <span>
                            Invoice: <strong className="text-rose-600">{finding.invoice_value}</strong>
                          </span>
                        )}
                        {finding.reference_value && (
                          <span>
                            Reference: <strong className="text-emerald-700">{finding.reference_value}</strong>
                          </span>
                        )}
                      </div>
                    )}
                  </div>

                  <div className="flex flex-col justify-center min-w-[150px] shrink-0">
                    {!finding.review_status ? (
                      <div className="flex flex-col gap-2">
                        <button
                          onClick={() => handleReview(finding.id, "ACCEPTED")}
                          disabled={reviewingId === finding.id}
                          className="bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border border-emerald-300 px-3.5 py-2 rounded-xl transition-colors text-xs font-bold flex items-center justify-center gap-1.5 shadow-2xs cursor-pointer"
                        >
                          <Check className="w-3.5 h-3.5" />
                          <span>Accept Finding</span>
                        </button>
                        <button
                          onClick={() => handleReview(finding.id, "DISMISSED")}
                          disabled={reviewingId === finding.id}
                          className="bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-300 px-3.5 py-2 rounded-xl transition-colors text-xs font-bold flex items-center justify-center gap-1.5 shadow-2xs cursor-pointer"
                        >
                          <X className="w-3.5 h-3.5" />
                          <span>Dismiss</span>
                        </button>
                      </div>
                    ) : (
                      <div className="text-center p-2.5 rounded-xl bg-white border border-slate-200 shadow-2xs">
                        <span
                          className={`inline-flex items-center gap-1.5 text-xs font-bold uppercase ${
                            finding.review_status === "ACCEPTED" ? "text-emerald-700" : "text-slate-500"
                          }`}
                        >
                          {finding.review_status === "ACCEPTED" ? (
                            <CheckCircle className="w-3.5 h-3.5 text-emerald-600" />
                          ) : (
                            <XCircle className="w-3.5 h-3.5 text-slate-400" />
                          )}
                          <span>{finding.review_status}</span>
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </motion.div>
    </div>
  );
}
