import type { LoginRequest, RegisterRequest, AuthResponse } from "@/features/auth/types"

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1"

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: "Request failed" }))
    throw new Error(error.detail ?? error.message ?? "An unexpected error occurred")
  }
  return response.json()
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
