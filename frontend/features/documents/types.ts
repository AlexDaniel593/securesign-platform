export interface DocumentItem {
  id: number
  filename: string
  sha256_hash: string
  file_size: number
  uploaded_at: string
}

export interface DocumentListResponse {
  items: DocumentItem[]
  total: number
  page: number
  limit: number
}

// eslint-disable-next-line @typescript-eslint/no-empty-interface
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
  is_valid?: boolean
}

export interface SignaturesResponse {
  signatures: SignatureItem[]
}

export interface ApiError {
  detail?: string
  message?: string
}
