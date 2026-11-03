// Utility for making API requests to the backend

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export async function fetchDocuments() {
  const res = await fetch(`${API_BASE_URL}/documents/`);
  if (!res.ok) throw new Error('Failed to fetch documents');
  return res.json();
}

export async function uploadDocument(file: File) {
  const formData = new FormData();
  formData.append('file', file);
  
  const res = await fetch(`${API_BASE_URL}/documents/upload`, {
    method: 'POST',
    body: formData,
  });
  
  if (!res.ok) throw new Error('Failed to upload document');
  return res.json();
}

export async function askQuestion(question: string) {
  const res = await fetch(`${API_BASE_URL}/chat/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ question }),
  });
  
  if (!res.ok) {
    const errBody = await res.json().catch(() => null);
    throw new Error(errBody?.detail || `Error from backend (${res.status})`);
  }
  return res.json();
}

export async function startWorkflow(invoiceId: string, referenceId?: string) {
  const res = await fetch(`${API_BASE_URL}/workflows/invoice-verification`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ invoice_document_id: invoiceId, reference_document_id: referenceId }),
  });
  if (!res.ok) throw new Error('Failed to start workflow');
  return res.json();
}

export async function getWorkflow(workflowId: string) {
  const res = await fetch(`${API_BASE_URL}/workflows/${workflowId}`);
  if (!res.ok) throw new Error('Failed to get workflow');
  return res.json();
}

export async function reviewFinding(workflowId: string, findingId: string, decision: string, reason?: string) {
  const res = await fetch(`${API_BASE_URL}/workflows/${workflowId}/review`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ finding_id: findingId, decision, reason }),
  });
  if (!res.ok) throw new Error('Failed to submit review');
  return res.json();
}

export async function fetchWorkflows() {
  const res = await fetch(`${API_BASE_URL}/workflows/`);
  if (!res.ok) throw new Error('Failed to fetch workflows');
  return res.json();
}

export async function decideWorkflow(workflowId: string, status: "APPROVED" | "REJECTED", reason?: string) {
  const res = await fetch(`${API_BASE_URL}/workflows/${workflowId}/decision`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ status, reason }),
  });
  if (!res.ok) throw new Error('Failed to submit workflow decision');
  return res.json();
}

export async function getWorkflowReport(workflowId: string) {
  const res = await fetch(`${API_BASE_URL}/workflows/${workflowId}/report`);
  if (!res.ok) throw new Error('Failed to get report');
  return res.json();
}

// ==========================================
// GST Reconciliation API
// ==========================================

export async function uploadGSTFilePreview(file: File, sheetName?: string) {
  const formData = new FormData();
  formData.append('file', file);
  const url = new URL(`${API_BASE_URL}/gst-reconciliation/upload-preview`);
  if (sheetName) url.searchParams.append('sheet_name', sheetName);

  const res = await fetch(url.toString(), {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => null);
    throw new Error(err?.detail || 'Failed to upload and preview GST file');
  }
  return res.json();
}

export async function createGSTRun(payload: {
  company_gstin: string;
  tax_period: string;
  gstr2b_document_id: string;
  purchase_register_document_id: string;
  gstr2b_column_mapping?: Record<string, string>;
  purchase_register_column_mapping?: Record<string, string>;
  tolerances?: { tax_diff_max?: number; date_days_diff?: number };
}) {
  const res = await fetch(`${API_BASE_URL}/gst-reconciliation/runs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => null);
    throw new Error(err?.detail || 'Failed to create GST reconciliation run');
  }
  return res.json();
}

export async function fetchGSTRuns() {
  const res = await fetch(`${API_BASE_URL}/gst-reconciliation/runs`);
  if (!res.ok) throw new Error('Failed to fetch reconciliation runs');
  return res.json();
}

export async function getGSTRun(runId: string) {
  const res = await fetch(`${API_BASE_URL}/gst-reconciliation/runs/${runId}`);
  if (!res.ok) throw new Error('Failed to get reconciliation run details');
  return res.json();
}

export async function fetchGSTDiscrepancies(runId: string, params?: {
  category?: string;
  review_status?: string;
  search?: string;
}) {
  const url = new URL(`${API_BASE_URL}/gst-reconciliation/runs/${runId}/discrepancies`);
  if (params?.category && params.category !== 'ALL') url.searchParams.append('category', params.category);
  if (params?.review_status && params.review_status !== 'ALL') url.searchParams.append('review_status', params.review_status);
  if (params?.search) url.searchParams.append('search', params.search);

  const res = await fetch(url.toString());
  if (!res.ok) throw new Error('Failed to fetch discrepancies');
  return res.json();
}

export async function reviewGSTDiscrepancy(runId: string, payload: {
  discrepancy_id: string;
  review_status: string;
  reviewer_notes?: string;
}) {
  const res = await fetch(`${API_BASE_URL}/gst-reconciliation/runs/${runId}/review`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to submit review');
  return res.json();
}

export async function manualLinkGSTInvoices(runId: string, payload: {
  books_invoice_id: string;
  gstr2b_invoice_id: string;
  notes?: string;
}) {
  const res = await fetch(`${API_BASE_URL}/gst-reconciliation/runs/${runId}/manual-link`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to manually link records');
  return res.json();
}

export function getGSTExportDownloadUrl(runId: string): string {
  return `${API_BASE_URL}/gst-reconciliation/runs/${runId}/export`;
}

