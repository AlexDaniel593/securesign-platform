"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { toast } from "sonner"
import { Eye, EyeOff, Loader2, Lock, Mail, User, ChevronDown } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { login, register } from "@/features/auth/services/auth-service"
import { setToken } from "@/lib/auth"
import { cn } from "@/lib/utils"

type Tab = "login" | "register"

export function AuthDropdown() {
  const router = useRouter()
  const [open, setOpen] = useState(false)
  const [tab, setTab] = useState<Tab>("login")
  const [isPending, setIsPending] = useState(false)
  const [showPassword, setShowPassword] = useState(false)

  const [name, setName] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")

  function reset() {
    setTab("login")
    setName("")
    setEmail("")
    setPassword("")
    setShowPassword(false)
    setIsPending(false)
  }

  function handleClose() {
    setOpen(false)
    reset()
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setIsPending(true)

    const action =
      tab === "login"
        ? login({ email, password })
        : register({ name, email, password, confirmPassword: password })

    action
      .then((res) => {
        setToken(res.access_token)
        toast.success(tab === "login" ? "Sesion iniciada" : "Cuenta creada")
        handleClose()
        router.push("/dashboard")
      })
      .catch((err) => {
        toast.error(err.message)
      })
      .finally(() => setIsPending(false))
  }

  return (
    <div className="relative">
      <Button variant="ghost" onClick={() => setOpen(!open)} className="gap-1 text-foreground">
        <User className="size-4" />
        <ChevronDown className={cn("size-3 transition-transform", open && "rotate-180")} />
      </Button>

      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={handleClose} />
          <div className="absolute right-0 top-full z-50 mt-2 w-80 rounded-lg border bg-background p-4 shadow-lg text-foreground">
            <div className="mb-4 flex gap-1 rounded-md bg-muted p-1">
              <button
                onClick={() => setTab("login")}
                className={cn(
                  "flex-1 rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
                  tab === "login"
                    ? "bg-background text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                Iniciar sesion
              </button>
              <button
                onClick={() => setTab("register")}
                className={cn(
                  "flex-1 rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
                  tab === "register"
                    ? "bg-background text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                Crear cuenta
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-3">
              {tab === "register" && (
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
                  <Input
                    type="text"
                    placeholder="Nombre completo"
                    className="pl-10 text-foreground"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required
                    minLength={2}
                  />
                </div>
              )}

              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
                <Input
                  type="email"
                  placeholder="Correo electronico"
                  className="pl-10 text-foreground"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>

              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
                <Input
                  type={showPassword ? "text" : "password"}
                  placeholder="Contrasena"
                  className="pl-10 pr-10 text-foreground"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  minLength={8}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                  tabIndex={-1}
                >
                  {showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                </button>
              </div>

              <Button type="submit" className="w-full" disabled={isPending}>
                {isPending && <Loader2 className="mr-1 size-4 animate-spin" />}
                {isPending
                  ? tab === "login"
                    ? "Iniciando..."
                    : "Creando..."
                  : tab === "login"
                    ? "Iniciar sesion"
                    : "Crear cuenta"}
              </Button>
            </form>
          </div>
        </>
      )}
    </div>
  )
}
