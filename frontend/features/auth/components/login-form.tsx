"use client"

import { useForm } from "@conform-to/react"
import { parseWithZod } from "@conform-to/zod"
import { z } from "zod"
import { useRouter } from "next/navigation"
import { toast } from "sonner"
import { Loader2, Lock, Mail } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { login } from "@/features/auth/services/auth-service"
import { useState } from "react"

const schema = z.object({
  email: z.string().email("Ingresa un correo válido"),
  password: z.string().min(1, "La contraseña es requerida"),
})

export function LoginForm() {
  const router = useRouter()
  const [isPending, setIsPending] = useState(false)

  const [form, fields] = useForm({
    onValidate({ formData }) {
      return parseWithZod(formData, { schema })
    },
    onSubmit(event, { formData }) {
      event.preventDefault()
      setIsPending(true)
      const data = Object.fromEntries(formData) as { email: string; password: string }

      login(data)
        .then((res) => {
          document.cookie = `token=${res.access_token}; path=/; max-age=86400; samesite=lax`
          toast.success("Sesión iniciada correctamente")
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
          <Label htmlFor={fields.email.id}>Correo electrónico</Label>
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
          <Label htmlFor={fields.password.id}>Contraseña</Label>
          <div className="relative">
            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
            <Input
              id={fields.password.id}
              name={fields.password.name}
              type="password"
              placeholder="••••••••"
              className="pl-10"
              defaultValue={fields.password.initialValue}
            />
          </div>
          {fields.password.errors && (
            <p className="text-sm text-destructive">{fields.password.errors}</p>
          )}
        </div>

        <Button type="submit" className="w-full" disabled={isPending}>
          {isPending && <Loader2 className="size-4 animate-spin" />}
          {isPending ? "Iniciando sesión..." : "Iniciar sesión"}
        </Button>
      </fieldset>
    </form>
  )
}
