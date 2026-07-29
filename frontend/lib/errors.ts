const errorMap: Record<string, string> = {
  "Invalid or expired token": "Sesión expirada. Inicia sesión nuevamente.",
  "Invalid token payload": "Token de sesión inválido.",
  "User not found or inactive": "Usuario no encontrado o desactivado.",
  "Admin privileges required": "Se requieren permisos de administrador.",
  "Invalid password": "Contraseña incorrecta.",
  "No RSA key pair found. Generate keys first.":
    "No tienes llaves RSA. Genera un par de llaves primero.",
  "File exceeds maximum upload size of 10 MB.":
    "El archivo excede el límite de 10 MB.",
  "Document not found": "Documento no encontrado.",
  "Signature not found for this document":
    "Firma no encontrada en este documento.",
  "Signer's public key not found":
    "No se encontró la llave pública del firmante.",
  "Only PDF files are accepted. Upload a file with .pdf extension.":
    "Solo se aceptan archivos PDF. Sube un archivo con extensión .pdf.",
  "Email already registered": "Este correo electrónico ya está registrado.",
  "Invalid email or password": "Correo o contraseña incorrectos.",
  "Account is deactivated": "Cuenta desactivada.",
  "Current password is incorrect": "La contraseña actual es incorrecta.",
  "You must generate a key pair before issuing a certificate. Use POST /crypto/keys/generate":
    "Debes generar un par de llaves RSA antes de emitir un certificado.",
  "Certificate not found": "Certificado no encontrado.",
  "Certificate is already revoked": "El certificado ya está revocado.",
  "Storage service unavailable":
    "Servicio de almacenamiento no disponible. Intenta más tarde.",
  "An unexpected error occurred": "Ocurrió un error inesperado.",
  "Request failed": "Error al conectar con el servidor.",
  "Value error, Password must be at least 8 characters long":
    "La contraseña debe tener al menos 8 caracteres.",
  "Value error, Password must be at most 20 characters long":
    "La contraseña debe tener máximo 20 caracteres.",
  "Value error, Password must contain at least one lowercase letter":
    "La contraseña debe contener al menos una letra minúscula.",
  "Value error, Password must contain at least one uppercase letter":
    "La contraseña debe contener al menos una letra mayúscula.",
  "Value error, Password must contain at least one number":
    "La contraseña debe contener al menos un número.",
  "Value error, Password must contain at least one special character":
    "La contraseña debe contener al menos un carácter especial.",
  "Password must be at least 8 characters long":
    "La contraseña debe tener al menos 8 caracteres.",
  "Password must be at most 20 characters long":
    "La contraseña debe tener máximo 20 caracteres.",
  "Password must contain at least one lowercase letter":
    "La contraseña debe contener al menos una letra minúscula.",
  "Password must contain at least one uppercase letter":
    "La contraseña debe contener al menos una letra mayúscula.",
  "Password must contain at least one number":
    "La contraseña debe contener al menos un número.",
  "Password must contain at least one special character":
    "La contraseña debe contener al menos un carácter especial.",
}

export function translateError(message: unknown): string {
  const str = typeof message === "string" ? message : String(message ?? "An unexpected error occurred")

  if (errorMap[str]) return errorMap[str]

  if (str.startsWith("Too many login attempts")) {
    const match = str.match(/Try again in (\d+) seconds/)
    const secs = match ? match[1] : "varios"
    return `Demasiados intentos. Intenta de nuevo en ${secs} segundos.`
  }

  const prefixes: [string, string][] = [
    ["Key generation failed: ", "Error al generar las llaves: "],
    ["Key export failed: ", "Error al exportar la llave: "],
    ["Signing failed: ", "Error al firmar: "],
    ["Encryption failed: ", "Error al cifrar: "],
    ["Decryption failed: ", "Error al descifrar: "],
    ["Invalid base64 content: ", "Contenido inválido: "],
    ["No RSA key pair found for user ", "No se encontraron llaves RSA. "],
  ]

  for (const [eng, sp] of prefixes) {
    if (str.startsWith(eng)) {
      return sp + str.slice(eng.length)
    }
  }

  return str
}