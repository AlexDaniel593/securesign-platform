"use client"

import { useForm } from "@conform-to/react"
import { parseWithZod } from "@conform-to/zod"
import { z } from "zod"
import { toast } from "sonner"
import { Loader2, CheckCircle, XCircle, SearchCheck } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { verify } from "@/features/certificates/services/cert-service"
import { useState } from "react"

const schema = z.object({
  certificate_pem: z.string().min(1, "El certificado PEM es requerido"),
})

export function VerifyCertificate() {
  const [result, setResult] = useState<{
    valid: boolean
    reason: string
    expires_in_days: number | null
  } | null>(null)
  const [isPending, setIsPending] = useState(false)

  const [form, fields] = useForm({
    onValidate({ formData }) {
      return parseWithZod(formData, { schema })
    },
    onSubmit(event, { formData }) {
      event.preventDefault()
      setIsPending(true)
      setResult(null)
      const data = Object.fromEntries(formData) as { certificate_pem: string }

      verify({ certificate_pem: data.certificate_pem })
        .then((res) => setResult({ valid: res.valid, reason: res.reason, expires_in_days: res.expires_in_days }))
        .catch((err) => toast.error(err.message))
        .finally(() => setIsPending(false))
    },
  })

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <SearchCheck className="size-5" /> Validar Certificado
        </CardTitle>
        <CardDescription>
          Verifica la validez de un certificado digital en formato PEM
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <form id={form.id} onSubmit={form.onSubmit} noValidate>
          <fieldset disabled={isPending} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor={fields.certificate_pem.id}>Certificado PEM</Label>
              <textarea
                id={fields.certificate_pem.id}
                name={fields.certificate_pem.name}
                placeholder="-----BEGIN CERTIFICATE-----&#10;..."
                defaultValue={fields.certificate_pem.initialValue}
                className="flex min-h-[120px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-xs transition-colors focus-visible:outline-hidden focus-visible:ring-1 focus-visible:ring-ring placeholder:text-muted-foreground disabled:cursor-not-allowed disabled:opacity-50 font-mono"
              />
              {fields.certificate_pem.errors && (
                <p className="text-sm text-destructive">{fields.certificate_pem.errors}</p>
              )}
            </div>

            <Button type="submit" disabled={isPending}>
              {isPending && <Loader2 className="size-4 animate-spin" />}
              {isPending ? "Validando..." : "Validar Certificado"}
            </Button>
          </fieldset>
        </form>

        {result && (
          <>
            <Separator />
            <div
              className={`flex items-start gap-3 rounded-md p-3 ${
                result.valid
                  ? "bg-green-50 text-green-700"
                  : "bg-red-50 text-red-700"
              }`}
            >
              {result.valid ? (
                <CheckCircle className="size-5 mt-0.5 shrink-0" />
              ) : (
                <XCircle className="size-5 mt-0.5 shrink-0" />
              )}
              <div>
                <p className="text-sm font-medium">{result.reason}</p>
                {result.expires_in_days !== null && (
                  <p className="text-sm mt-1 opacity-80">
                    Expira en {result.expires_in_days} días
                  </p>
                )}
              </div>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}
