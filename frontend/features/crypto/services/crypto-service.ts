import type {
  HashRequest,
  HashResponse,
  KeyStatusResponse,
  KeyGenerateResponse,
  SignRequest,
  SignResponse,
  VerifyRequest,
  VerifyResponse,
  EncryptRequest,
  EncryptResponse,
  DecryptRequest,
  DecryptResponse,
} from "@/features/crypto/types"

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

export async function hash(data: HashRequest): Promise<HashResponse> {
  const response = await fetch(`${API_URL}/crypto/hash`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(data),
  })
  return handleResponse<HashResponse>(response)
}

export async function getKeyStatus(): Promise<KeyStatusResponse> {
  const response = await fetch(`${API_URL}/crypto/keys/status`, {
    headers: { ...authHeaders() },
  })
  return handleResponse<KeyStatusResponse>(response)
}

export async function generateKeys(): Promise<KeyGenerateResponse> {
  const response = await fetch(`${API_URL}/crypto/keys/generate`, {
    method: "POST",
    headers: { ...authHeaders() },
  })
  return handleResponse<KeyGenerateResponse>(response)
}

export async function sign(data: SignRequest): Promise<SignResponse> {
  const response = await fetch(`${API_URL}/crypto/sign`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(data),
  })
  return handleResponse<SignResponse>(response)
}

export async function verify(data: VerifyRequest): Promise<VerifyResponse> {
  const response = await fetch(`${API_URL}/crypto/verify`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(data),
  })
  return handleResponse<VerifyResponse>(response)
}

export async function encrypt(data: EncryptRequest): Promise<EncryptResponse> {
  const response = await fetch(`${API_URL}/crypto/encrypt`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(data),
  })
  return handleResponse<EncryptResponse>(response)
}

export async function decrypt(data: DecryptRequest): Promise<DecryptResponse> {
  const response = await fetch(`${API_URL}/crypto/decrypt`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(data),
  })
  return handleResponse<DecryptResponse>(response)
}
