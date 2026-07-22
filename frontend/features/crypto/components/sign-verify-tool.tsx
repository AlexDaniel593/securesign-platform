"use client"

import { useForm } from "@conform-to/react"
import { parseWithZod } from "@conform-to/zod"
import { z } from "zod"
import { toast } from "sonner"
import { Loader2, FileSignature, CheckCircle, XCircle } from "lucide-react"
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
import { Separator } from "@/components/ui/separator"
import { sign, verify } from "@/features/crypto/services/crypto-service"
import { useState } from "react"

const signSchema = z.object({
  document_hash: z.string().min(1, "El hash del documento es requerido"),
})

const verifySchema = z.object({
  document_hash: z.string().min(1, "El hash del documento es requerido"),
  signature: z.string().min(1, "La firma es requerida"),
  public_key: z.string().min(1, "La llave pública es requerida"),
})

export function SignVerifyTool() {
  const [mode, setMode] = useState<"sign" | "verify">("sign")
  const [signature, setSignature] = useState<string | null>(null)
  const [verificationResult, setVerificationResult] = useState<{ valid: boolean; message: string } | null>(null)
  const [isPending, setIsPending] = useState(false)

  const [signForm, signFields] = useForm({
    onValidate({ formData }) {
      return parseWithZod(formData, { schema: signSchema })
    },
    onSubmit(event, { formData }) {
      event.preventDefault()
      setIsPending(true)
      setSignature(null)
      const data = Object.fromEntries(formData) as { document_hash: string }
      sign(data)
        .then((res) => setSignature(res.signature))
        .catch((err) => toast.error(err.message))
        .finally(() => setIsPending(false))
    },
  })

  const [verifyForm, verifyFields] = useForm({
    onValidate({ formData }) {
      return parseWithZod(formData, { schema: verifySchema })
    },
    onSubmit(event, { formData }) {
      event.preventDefault()
      setIsPending(true)
      setVerificationResult(null)
      const data = Object.fromEntries(formData) as { document_hash: string; signature: string; public_key: string }
      verify(data)
        .then((res) => setVerificationResult({ valid: res.valid, message: res.message }))
        .catch((err) => toast.error(err.message))
        .finally(() => setIsPending(false))
    },
  })

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileSignature className="size-5" /> Firmar / Verificar
        </CardTitle>
        <CardDescription>
          Firma el hash de un documento o verifica una firma existente
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="flex gap-2">
          <Button
            variant={mode === "sign" ? "default" : "outline"}
            size="sm"
            onClick={() => setMode("sign")}
          >
            Firmar
          </Button>
          <Button
            variant={mode === "verify" ? "default" : "outline"}
            size="sm"
            onClick={() => setMode("verify")}
          >
            Verificar
          </Button>
        </div>

        {mode === "sign" ? (
          <form id={signForm.id} onSubmit={signForm.onSubmit} noValidate>
            <fieldset disabled={isPending} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor={signFields.document_hash.id}>Hash del documento (hex)</Label>
                <Input
                  id={signFields.document_hash.id}
                  name={signFields.document_hash.name}
                  placeholder="Ingresa el hash en hexadecimal..."
                  defaultValue={signFields.document_hash.initialValue}
                />
                {signFields.document_hash.errors && (
                  <p className="text-sm text-destructive">{signFields.document_hash.errors}</p>
                )}
              </div>

              <Button type="submit" disabled={isPending}>
                {isPending && <Loader2 className="size-4 animate-spin" />}
                {isPending ? "Firmando..." : "Firmar con RSA"}
              </Button>
            </fieldset>
          </form>
        ) : (
          <form id={verifyForm.id} onSubmit={verifyForm.onSubmit} noValidate>
            <fieldset disabled={isPending} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor={verifyFields.document_hash.id}>Hash del documento (hex)</Label>
                <Input
                  id={verifyFields.document_hash.id}
                  name={verifyFields.document_hash.name}
                  placeholder="Ingresa el hash en hexadecimal..."
                  defaultValue={verifyFields.document_hash.initialValue}
                />
                {verifyFields.document_hash.errors && (
                  <p className="text-sm text-destructive">{verifyFields.document_hash.errors}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor={verifyFields.signature.id}>Firma (base64)</Label>
                <textarea
                  id={verifyFields.signature.id}
                  name={verifyFields.signature.name}
                  placeholder="Pega la firma en base64..."
                  defaultValue={verifyFields.signature.initialValue}
                  className="flex min-h-[80px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-xs transition-colors focus-visible:outline-hidden focus-visible:ring-1 focus-visible:ring-ring placeholder:text-muted-foreground disabled:cursor-not-allowed disabled:opacity-50"
                />
                {verifyFields.signature.errors && (
                  <p className="text-sm text-destructive">{verifyFields.signature.errors}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor={verifyFields.public_key.id}>Llave pública</Label>
                <textarea
                  id={verifyFields.public_key.id}
                  name={verifyFields.public_key.name}
                  placeholder="Pega la llave pública..."
                  defaultValue={verifyFields.public_key.initialValue}
                  className="flex min-h-[80px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-xs transition-colors focus-visible:outline-hidden focus-visible:ring-1 focus-visible:ring-ring placeholder:text-muted-foreground disabled:cursor-not-allowed disabled:opacity-50"
                />
                {verifyFields.public_key.errors && (
                  <p className="text-sm text-destructive">{verifyFields.public_key.errors}</p>
                )}
              </div>

              <Button type="submit" disabled={isPending}>
                {isPending && <Loader2 className="size-4 animate-spin" />}
                {isPending ? "Verificando..." : "Verificar Firma"}
              </Button>
            </fieldset>
          </form>
        )}

        {mode === "sign" && signature && (
          <>
            <Separator />
            <div className="rounded-md bg-muted p-3">
              <Label className="text-xs text-muted-foreground">Firma (base64)</Label>
              <p className="mt-1 break-all font-mono text-sm">{signature}</p>
            </div>
          </>
        )}

        {mode === "verify" && verificationResult && (
          <>
            <Separator />
            <div
              className={`flex items-center gap-2 rounded-md p-3 ${
                verificationResult.valid
                  ? "bg-green-50 text-green-700"
                  : "bg-red-50 text-red-700"
              }`}
            >
              {verificationResult.valid ? (
                <CheckCircle className="size-5" />
              ) : (
                <XCircle className="size-5" />
              )}
              <span className="text-sm font-medium">{verificationResult.message}</span>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}
