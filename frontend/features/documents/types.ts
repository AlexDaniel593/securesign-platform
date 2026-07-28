export interface DocumentItem {
  id: number
  filename: string
  sha256_hash: string
  file_size: number
  uploaded_at: string
  signature_count: number
}

export interface DocumentListResponse {
  items: DocumentItem[]
  total: number
  page: number
  limit: number
}

 
export interface UploadResponse extends DocumentItem {}

export interface RenameRequest {
  filename: string
}

export interface RenameResponse {
  id: number
  filename: string
}

export interface SignRequest {
  certificate_id?: number
}

export interface SignResponse {
  signature_id: number
  signature: string
  signed_at: string
  certificate_id?: number
}

export interface SignatureItem {
  id: number
  certificate_id?: number
  signature_blob: string
  signed_at: string
  is_valid?: boolean | null
  verified_at?: string | null
  signer_name: string
  signer_email: string
}

export interface SignaturesResponse {
  signatures: SignatureItem[]
}

export interface VerificationResult {
  is_valid: boolean
  verified_at: string
  signer_name: string
  signer_email: string
  certificate_status: "valid" | "revoked" | "expired" | "not_found"
}

export interface ApiError {
  detail?: string
  message?: string
}
