import { getToken } from "@/lib/auth"
import { translateError } from "@/lib/errors"

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1"

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: "Request failed" }))
    throw new Error(translateError(error.detail ?? error.message ?? "An unexpected error occurred"))
  }
  return response.json()
}

function authHeaders(): Record<string, string> {
  const token = getToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export interface AuditLogItem {
  id: number
  user_id: number | null
  user_email: string | null
  action: string
  resource_type: string | null
  resource_id: string | null
  ip_address: string | null
  user_agent: string | null
  details: string | null
  created_at: string
}

export interface AuditLogsResponse {
  items: AuditLogItem[]
  total: number
  page: number
  limit: number
}

export interface AuditMetrics {
  total_users: number
  total_documents: number
  total_signatures: number
  failed_logins: number
}

export async function listOwnLogs(page = 1, limit = 20): Promise<AuditLogsResponse> {
  const response = await fetch(`${API_URL}/audit/logs?page=${page}&limit=${limit}`, {
    headers: { ...authHeaders() },
  })
  return handleResponse<AuditLogsResponse>(response)
}

export async function listAllLogs(page = 1, limit = 20): Promise<AuditLogsResponse> {
  const response = await fetch(`${API_URL}/audit/logs/all?page=${page}&limit=${limit}`, {
    headers: { ...authHeaders() },
  })
  return handleResponse<AuditLogsResponse>(response)
}

export async function getMetrics(): Promise<AuditMetrics> {
  const response = await fetch(`${API_URL}/audit/metrics`, {
    headers: { ...authHeaders() },
  })
  return handleResponse<AuditMetrics>(response)
}
