import type { LoginRequest, RegisterRequest, AuthResponse } from "@/features/auth/types"
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

export interface UserProfile {
  id: number
  name: string
  email: string
  is_admin: boolean
  is_active: boolean
  created_at: string
}

export async function login(data: LoginRequest): Promise<AuthResponse> {
  const response = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  })
  return handleResponse<AuthResponse>(response)
}

export async function register(data: RegisterRequest): Promise<AuthResponse> {
  const { password, email, name } = data
  const payload = { password, email, name }
  const response = await fetch(`${API_URL}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  return handleResponse<AuthResponse>(response)
}

export async function logout(token: string): Promise<void> {
  const response = await fetch(`${API_URL}/auth/logout`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: "Logout failed" }))
    throw new Error(error.detail ?? error.message)
  }
}

export async function getMe(): Promise<UserProfile> {
  const response = await fetch(`${API_URL}/auth/me`, {
    headers: { ...authHeaders() },
  })
  return handleResponse<UserProfile>(response)
}

export async function changePassword(data: {
  current_password: string
  new_password: string
}): Promise<{ message: string }> {
  const response = await fetch(`${API_URL}/auth/change-password`, {
    method: "PUT",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(data),
  })
  return handleResponse<{ message: string }>(response)
}
