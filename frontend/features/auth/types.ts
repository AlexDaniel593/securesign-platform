export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  name: string
  email: string
  password: string
  confirmPassword: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: {
    id: number
    name: string
    email: string
  }
}

export interface ApiError {
  message: string
  status: number
  errors?: Record<string, string[]>
}
