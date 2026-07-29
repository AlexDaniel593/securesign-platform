"use client"

import { useForm } from "@conform-to/react"
import { parseWithZod } from "@conform-to/zod"
import { z } from "zod"
import { useRouter } from "next/navigation"
import { toast } from "sonner"
import { Check, Eye, EyeOff, Loader2, Lock, Mail, User, X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { register } from "@/features/auth/services/auth-service"
import { setToken } from "@/lib/auth"
import { useMemo, useState } from "react"

const PASSWORD_RULES = [
  { label: "Al menos 8 caracteres", test: (v: string) => v.length >= 8 },
  { label: "Máximo 20 caracteres", test: (v: string) => v.length <= 20 },
  { label: "Una letra minúscula", test: (v: string) => /[a-z]/.test(v) },
  { label: "Una letra mayúscula", test: (v: string) => /[A-Z]/.test(v) },
  { label: "Un número", test: (v: string) => /\d/.test(v) },
  { label: "Un carácter especial", test: (v: string) => /[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/`~;' ]/.test(v) },
] as const

const schema = z
  .object({
    name: z.string().min(2, "El nombre debe tener al menos 2 caracteres"),
    email: z.string().email("Ingresa un correo válido"),
    password: z.string()
      .min(8, "La contraseña debe tener al menos 8 caracteres")
      .max(20, "La contraseña debe tener máximo 20 caracteres")
      .regex(/[a-z]/, "Debe contener una minúscula")
      .regex(/[A-Z]/, "Debe contener una mayúscula")
      .regex(/\d/, "Debe contener un número")
      .regex(/[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/`~;' ]/, "Debe contener un carácter especial"),
    confirmPassword: z.string().min(1, "Confirma tu contraseña"),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Las contraseñas no coinciden",
    path: ["confirmPassword"],
  })

export function RegisterForm() {
  const router = useRouter()
  const [isPending, setIsPending] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)

  const [password, setPassword] = useState("")
  const passwordRules = useMemo(
    () => PASSWORD_RULES.map((r) => ({ ...r, met: r.test(password) })),
    [password],
  )

  const [form, fields] = useForm({
    onValidate({ formData }) {
      return parseWithZod(formData, { schema })
    },
    onSubmit(event, { formData }) {
      event.preventDefault()
      setIsPending(true)
      const data = Object.fromEntries(formData) as {
        name: string
        email: string
        password: string
        confirmPassword: string
      }

      register(data)
        .then((res) => {
          setToken(res.access_token)
          toast.success("Cuenta creada correctamente")
          router.push("/dashboard")
        })
        .catch((err) => {
          toast.error(err.message)
        })
        .finally(() => setIsPending(false))
    },
  })

  return (
    <form id={form.id} onSubmit={form.onSubmit} noValidate className="space-y-4">
      <fieldset disabled={isPending} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor={fields.name.id}>Nombre completo</Label>
          <div className="relative">
            <User className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
            <Input
              id={fields.name.id}
              name={fields.name.name}
              type="text"
              placeholder="Juan Pérez"
              className="pl-10"
              defaultValue={fields.name.initialValue}
            />
          </div>
          {fields.name.errors && (
            <p className="text-sm text-destructive">{fields.name.errors}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor={fields.email.id}>Email</Label>
          <div className="relative">
            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
            <Input
              id={fields.email.id}
              name={fields.email.name}
              type="email"
              placeholder="tu@correo.com"
              className="pl-10"
              defaultValue={fields.email.initialValue}
            />
          </div>
          {fields.email.errors && (
            <p className="text-sm text-destructive">{fields.email.errors}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor={fields.password.id}>Password</Label>
          <div className="relative">
            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
            <Input
              id={fields.password.id}
              name={fields.password.name}
              type={showPassword ? "text" : "password"}
              placeholder="••••••••"
              className="pl-10 pr-10"
              defaultValue={fields.password.initialValue}
              onChange={(e) => setPassword(e.target.value)}
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
          {fields.password.errors && (
            <p className="text-sm text-destructive">{fields.password.errors}</p>
          )}
          {password.length > 0 && (
            <ul className="space-y-1 text-sm">
              {passwordRules.map((rule) => (
                <li key={rule.label} className="flex items-center gap-2">
                  {rule.met ? (
                    <Check className="size-3.5 text-green-500 shrink-0" />
                  ) : (
                    <X className="size-3.5 text-muted-foreground shrink-0" />
                  )}
                  <span className={rule.met ? "text-green-600" : "text-muted-foreground"}>
                    {rule.label}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor={fields.confirmPassword.id}>Confirm password</Label>
          <div className="relative">
            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
            <Input
              id={fields.confirmPassword.id}
              name={fields.confirmPassword.name}
              type={showConfirmPassword ? "text" : "password"}
              placeholder="••••••••"
              className="pl-10 pr-10"
              defaultValue={fields.confirmPassword.initialValue}
            />
            <button
              type="button"
              onClick={() => setShowConfirmPassword(!showConfirmPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              tabIndex={-1}
            >
              {showConfirmPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
            </button>
          </div>
          {fields.confirmPassword.errors && (
            <p className="text-sm text-destructive">
              {fields.confirmPassword.errors}
            </p>
          )}
        </div>

        <Button type="submit" className="w-full" disabled={isPending}>
          {isPending && <Loader2 className="size-4 animate-spin" />}
          {isPending ? "Creating account..." : "Create account"}
        </Button>
      </fieldset>
    </form>
  )
}
