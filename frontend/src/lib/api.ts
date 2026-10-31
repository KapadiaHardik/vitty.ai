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

