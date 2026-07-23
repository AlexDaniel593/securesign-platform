export interface IssueRequest {
  subject_name: string
  validity_days?: number
}

export interface IssueResponse {
  id: number
  subject: string
  issuer: string
  valid_from: string
  valid_to: string
  fingerprint: string
}

export interface CertificateItem {
  id: number
  subject: string
  issuer: string
  serial_number: string
  valid_from: string
  valid_to: string
  revoked: boolean
  created_at: string
}

export interface CertificateListResponse {
  items: CertificateItem[]
  total: number
}

export interface CertificateDetail {
  id: number
  subject: string
  public_key: string
  issuer: string
  valid_from: string
  valid_to: string
  revoked: boolean
}

export interface RevokeRequest {
  reason?: string
}

export interface RevokeResponse {
  message: string
  revoked_at: string
}

export interface VerifyRequest {
  certificate_pem: string
  document_hash?: string
  signature?: string
}

export interface VerifyResponse {
  valid: boolean
  reason: string
  expires_in_days: number | null
}

export interface CheckResponse {
  valid: boolean
  status: string
}
