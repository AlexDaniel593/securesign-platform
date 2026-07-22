"use client"

import { useForm } from "@conform-to/react"
import { parseWithZod } from "@conform-to/zod"
import { z } from "zod"
import { toast } from "sonner"
import { Loader2, Hash } from "lucide-react"
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
import { hash } from "@/features/crypto/services/crypto-service"
import { useState } from "react"

const schema = z.object({
  content: z.string().min(1, "El contenido es requerido"),
})

export function HashTool() {
  const [result, setResult] = useState<{ sha256_hash: string; size: number } | null>(null)
  const [isPending, setIsPending] = useState(false)

  const [form, fields] = useForm({
    onValidate({ formData }) {
      return parseWithZod(formData, { schema })
    },
    onSubmit(event, { formData }) {
      event.preventDefault()
      setIsPending(true)
      setResult(null)
      const data = Object.fromEntries(formData) as { content: string }

      const content_base64 = btoa(data.content)
      hash({ content_base64 })
        .then((res) => setResult({ sha256_hash: res.sha256_hash, size: res.size }))
        .catch((err) => toast.error(err.message))
        .finally(() => setIsPending(false))
    },
  })

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Hash className="size-5" /> Generador de Hash
        </CardTitle>
        <CardDescription>
          Genera hash SHA-256 del contenido ingresado
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <form id={form.id} onSubmit={form.onSubmit} noValidate>
          <fieldset disabled={isPending} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor={fields.content.id}>Contenido</Label>
              <Input
                id={fields.content.id}
                name={fields.content.name}
                placeholder="Ingresa el texto a hashear..."
                defaultValue={fields.content.initialValue}
              />
              {fields.content.errors && (
                <p className="text-sm text-destructive">{fields.content.errors}</p>
              )}
            </div>

            <Button type="submit" disabled={isPending}>
              {isPending && <Loader2 className="size-4 animate-spin" />}
              {isPending ? "Generando..." : "Generar Hash SHA-256"}
            </Button>
          </fieldset>
        </form>

        {result && (
          <div className="space-y-2 rounded-md bg-muted p-3">
            <div>
              <Label className="text-xs text-muted-foreground">Hash SHA-256</Label>
              <p className="mt-1 break-all font-mono text-sm">{result.sha256_hash}</p>
            </div>
            <div>
              <Label className="text-xs text-muted-foreground">Tamaño</Label>
              <p className="mt-1 font-mono text-sm">{result.size} bytes</p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
