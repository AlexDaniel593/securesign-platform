export interface HashRequest {
  content_base64: string
  filename?: string
}

export interface HashResponse {
  sha256_hash: string
  filename: string | null
  size: number
}

export interface KeyStatusResponse {
  has_keys: boolean
  fingerprint: string | null
}

export interface KeyGenerateResponse {
  fingerprint: string
  public_key: string
  message: string
}

export interface SignRequest {
  document_hash: string
  certificate_id?: number
}

export interface SignResponse {
  signature: string
  signed_at: string
  certificate_id?: number | null
}

export interface VerifyRequest {
  document_hash: string
  signature: string
  public_key: string
}

export interface VerifyResponse {
  valid: boolean
  message: string
}

export interface EncryptRequest {
  content_base64: string
}

export interface EncryptResponse {
  encrypted_base64: string
  iv: string
}

export interface DecryptRequest {
  encrypted_base64: string
  iv: string
}

export interface DecryptResponse {
  decrypted_base64: string
}
