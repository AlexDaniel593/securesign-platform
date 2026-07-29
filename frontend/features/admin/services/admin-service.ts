import { getToken } from "@/lib/auth"
import { translateError } from "@/lib/errors"

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1"

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: "Request failed" }))
    const detail = Array.isArray(error.detail) ? error.detail.map((d: { msg?: string }) => d.msg).join(", ") : error.detail
    throw new Error(translateError(detail ?? error.message ?? "An unexpected error occurred"))
  }
  return response.json()
}

function authHeaders(): Record<string, string> {
  const token = getToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export interface UserItem {
  id: number
  name: string
  email: string
  is_admin: boolean
  is_active: boolean
  created_at: string
}

export interface UserListResponse {
  items: UserItem[]
  total: number
  page: number
  limit: number
}

export async function listUsers(page = 1, limit = 20): Promise<UserListResponse> {
  const response = await fetch(`${API_URL}/admin?page=${page}&limit=${limit}`, {
    headers: { ...authHeaders() },
  })
  return handleResponse<UserListResponse>(response)
}

export async function getUser(id: number): Promise<UserItem> {
  const response = await fetch(`${API_URL}/admin/${id}`, {
    headers: { ...authHeaders() },
  })
  return handleResponse<UserItem>(response)
}

export async function deleteUser(id: number): Promise<{ message: string }> {
  const response = await fetch(`${API_URL}/admin/${id}`, {
    method: "DELETE",
    headers: { ...authHeaders() },
  })
  return handleResponse<{ message: string }>(response)
}
