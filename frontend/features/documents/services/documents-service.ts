import type {
  DocumentItem,
  DocumentListResponse,
  UploadResponse,
  RenameRequest,
  RenameResponse,
  SignResponse,
  SignRequest,
  SignaturesResponse,
  VerificationResult,
} from "@/features/documents/types"

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1"

// NOTE: duplicated from crypto-service.ts. Out of scope to refactor shared helpers.
async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: "Request failed" }))
    throw new Error(error.detail ?? error.message ?? "An unexpected error occurred")
  }
  return response.json()
}

// NOTE: duplicated from crypto-service.ts. Out of scope to refactor shared helpers.
function authHeaders(): Record<string, string> {
  const token = document.cookie
    .split("; ")
    .find((row) => row.startsWith("token="))
    ?.split("=")[1]
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export async function uploadDocument(file: File): Promise<UploadResponse> {
  const formData = new FormData()
  formData.append("file", file)

  const response = await fetch(`${API_URL}/documents/upload`, {
    method: "POST",
    headers: { ...authHeaders() },
    body: formData,
  })
  return handleResponse<UploadResponse>(response)
}

export async function listDocuments(
  page?: number,
  limit?: number
): Promise<DocumentListResponse> {
  const params = new URLSearchParams()
  if (page !== undefined) params.set("page", String(page))
  if (limit !== undefined) params.set("limit", String(limit))

  const query = params.toString()
  const url = `${API_URL}/documents${query ? `?${query}` : ""}`

  const response = await fetch(url, {
    headers: { ...authHeaders() },
  })
  return handleResponse<DocumentListResponse>(response)
}

export async function getDocument(id: number): Promise<DocumentItem> {
  const response = await fetch(`${API_URL}/documents/${id}`, {
    headers: { ...authHeaders() },
  })
  return handleResponse<DocumentItem>(response)
}

export async function downloadDocument(id: number): Promise<Blob> {
  const response = await fetch(`${API_URL}/documents/${id}/download`, {
    headers: { ...authHeaders() },
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: "Download failed" }))
    throw new Error(error.detail ?? error.message ?? "An unexpected error occurred")
  }
  return response.blob()
}

export async function deleteDocument(id: number): Promise<{ message: string }> {
  const response = await fetch(`${API_URL}/documents/${id}`, {
    method: "DELETE",
    headers: { "Content-Type": "application/json", ...authHeaders() },
  })
  return handleResponse<{ message: string }>(response)
}

export async function renameDocument(
  id: number,
  data: RenameRequest
): Promise<RenameResponse> {
  const response = await fetch(`${API_URL}/documents/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(data),
  })
  return handleResponse<RenameResponse>(response)
}

export async function signDocument(
  id: number,
  data?: SignRequest
): Promise<SignResponse> {
  const response = await fetch(`${API_URL}/documents/${id}/sign`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(data ?? {}),
  })
  return handleResponse<SignResponse>(response)
}

export async function getSignatures(id: number): Promise<SignaturesResponse> {
  const response = await fetch(`${API_URL}/documents/${id}/signatures`, {
    headers: { ...authHeaders() },
  })
  return handleResponse<SignaturesResponse>(response)
}

export async function verifySignature(
  docId: number,
  sigId: number
): Promise<VerificationResult> {
  const response = await fetch(`${API_URL}/documents/${docId}/verify/${sigId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
  })
  return handleResponse<VerificationResult>(response)
}
