"use client"

import { useForm } from "@conform-to/react"
import { parseWithZod } from "@conform-to/zod"
import { z } from "zod"
import { toast } from "sonner"
import { Loader2, ShieldPlus } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { issue } from "@/features/certificates/services/cert-service"
import { useState } from "react"

const schema = z.object({
  subject_name: z.string().min(2, "El nombre del sujeto debe tener al menos 2 caracteres"),
  validity_days: z.string().optional(),
})

export function IssueCertificateForm({ onIssued }: { onIssued?: () => void }) {
  const [result, setResult] = useState<{
    id: number
    subject: string
    fingerprint: string
    valid_from: string
    valid_to: string
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
      const data = Object.fromEntries(formData) as { subject_name: string; validity_days?: string }

      issue({
        subject_name: data.subject_name,
        validity_days: data.validity_days ? Number(data.validity_days) : 365,
      })
        .then((res) => {
          setResult({
            id: res.id,
            subject: res.subject,
            fingerprint: res.fingerprint,
            valid_from: res.valid_from,
            valid_to: res.valid_to,
          })
          toast.success("Certificado emitido correctamente")
          onIssued?.()
        })
        .catch((err) => toast.error(err.message))
        .finally(() => setIsPending(false))
    },
  })

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <ShieldPlus className="size-5" /> Emitir Certificado
        </CardTitle>
        <CardDescription>
          Emite un nuevo certificado digital firmado por la CA
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <form id={form.id} onSubmit={form.onSubmit} noValidate>
          <fieldset disabled={isPending} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor={fields.subject_name.id}>Nombre del sujeto</Label>
              <Input
                id={fields.subject_name.id}
                name={fields.subject_name.name}
                placeholder="Ej: Juan Pérez"
                defaultValue={fields.subject_name.initialValue}
              />
              {fields.subject_name.errors && (
                <p className="text-sm text-destructive">{fields.subject_name.errors}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor={fields.validity_days.id}>Días de validez (opcional)</Label>
              <Input
                id={fields.validity_days.id}
                name={fields.validity_days.name}
                type="number"
                placeholder="365"
                defaultValue={fields.validity_days.initialValue ?? "365"}
              />
            </div>

            <Button type="submit" disabled={isPending}>
              {isPending && <Loader2 className="size-4 animate-spin" />}
              {isPending ? "Emitiendo..." : "Emitir Certificado"}
            </Button>
          </fieldset>
        </form>

        {result && (
          <div className="space-y-2 rounded-md bg-muted p-3">
            <div>
              <Label className="text-xs text-muted-foreground">Sujeto</Label>
              <p className="mt-1 font-mono text-sm">{result.subject}</p>
            </div>
            <div>
              <Label className="text-xs text-muted-foreground">Huella digital</Label>
              <p className="mt-1 break-all font-mono text-sm">{result.fingerprint}</p>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <Label className="text-xs text-muted-foreground">Válido desde</Label>
                <p className="mt-1 font-mono text-sm">{new Date(result.valid_from).toLocaleDateString()}</p>
              </div>
              <div>
                <Label className="text-xs text-muted-foreground">Válido hasta</Label>
                <p className="mt-1 font-mono text-sm">{new Date(result.valid_to).toLocaleDateString()}</p>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
