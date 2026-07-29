const TOKEN_KEY = "token"

export function setToken(token: string) {
  sessionStorage.setItem(TOKEN_KEY, token)
  document.cookie = `${TOKEN_KEY}=${token}; path=/; max-age=86400; samesite=lax`
}

export function getToken(): string | null {
  const fromSession = sessionStorage.getItem(TOKEN_KEY)
  if (fromSession) return fromSession

  const fromCookie = document.cookie
    .split("; ")
    .find((row) => row.startsWith(`${TOKEN_KEY}=`))
    ?.split("=")
    .slice(1)
    .join("=")
  return fromCookie ?? null
}

export function clearToken() {
  sessionStorage.removeItem(TOKEN_KEY)
  document.cookie = `${TOKEN_KEY}=; path=/; max-age=0`
}