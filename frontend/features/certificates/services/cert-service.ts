import type {
  IssueRequest,
  IssueResponse,
  CertificateListResponse,
  CertificateDetail,
  RevokeRequest,
  RevokeResponse,
  VerifyRequest,
  VerifyResponse,
  CheckResponse,
} from "@/features/certificates/types"

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1"

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: "Request failed" }))
    throw new Error(error.detail ?? error.message ?? "An unexpected error occurred")
  }
  return response.json()
}

function authHeaders(): Record<string, string> {
  const token = document.cookie
    .split("; ")
    .find((row) => row.startsWith("token="))
    ?.split("=")[1]
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export async function issue(data: IssueRequest): Promise<IssueResponse> {
  const response = await fetch(`${API_URL}/certificates/issue`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(data),
  })
  return handleResponse<IssueResponse>(response)
}

export async function list(revoked?: boolean): Promise<CertificateListResponse> {
  const params = revoked !== undefined ? `?revoked=${revoked}` : ""
  const response = await fetch(`${API_URL}/certificates${params}`, {
    headers: { ...authHeaders() },
  })
  return handleResponse<CertificateListResponse>(response)
}

export async function getById(id: number): Promise<CertificateDetail> {
  const response = await fetch(`${API_URL}/certificates/${id}`, {
    headers: { ...authHeaders() },
  })
  return handleResponse<CertificateDetail>(response)
}

export async function revoke(id: number, data?: RevokeRequest): Promise<RevokeResponse> {
  const response = await fetch(`${API_URL}/certificates/${id}/revoke`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(data ?? {}),
  })
  return handleResponse<RevokeResponse>(response)
}

export async function verify(data: VerifyRequest): Promise<VerifyResponse> {
  const response = await fetch(`${API_URL}/certificates/verify`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  })
  return handleResponse<VerifyResponse>(response)
}

export async function check(id: number): Promise<CheckResponse> {
  const response = await fetch(`${API_URL}/certificates/check/${id}`, {
    headers: { ...authHeaders() },
  })
  return handleResponse<CheckResponse>(response)
}
