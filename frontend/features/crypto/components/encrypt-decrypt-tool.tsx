"use client"

import { useForm } from "@conform-to/react"
import { parseWithZod } from "@conform-to/zod"
import { z } from "zod"
import { toast } from "sonner"
import { Loader2, Shield } from "lucide-react"
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
import { encrypt, decrypt } from "@/features/crypto/services/crypto-service"
import { useState } from "react"

const encryptSchema = z.object({
  plaintext: z.string().min(1, "El texto plano es requerido"),
})

const decryptSchema = z.object({
  encrypted_base64: z.string().min(1, "El texto cifrado es requerido"),
  iv: z.string().min(1, "El IV es requerido"),
})

export function EncryptDecryptTool() {
  const [mode, setMode] = useState<"encrypt" | "decrypt">("encrypt")
  const [encryptResult, setEncryptResult] = useState<{ encrypted_base64: string; iv: string } | null>(null)
  const [decryptResult, setDecryptResult] = useState<string | null>(null)
  const [isPending, setIsPending] = useState(false)

  const [encryptForm, encryptFields] = useForm({
    onValidate({ formData }) {
      return parseWithZod(formData, { schema: encryptSchema })
    },
    onSubmit(event, { formData }) {
      event.preventDefault()
      setIsPending(true)
      setEncryptResult(null)
      const data = Object.fromEntries(formData) as { plaintext: string }
      const content_base64 = btoa(data.plaintext)
      encrypt({ content_base64 })
        .then((res) => setEncryptResult({ encrypted_base64: res.encrypted_base64, iv: res.iv }))
        .catch((err) => toast.error(err.message))
        .finally(() => setIsPending(false))
    },
  })

  const [decryptForm, decryptFields] = useForm({
    onValidate({ formData }) {
      return parseWithZod(formData, { schema: decryptSchema })
    },
    onSubmit(event, { formData }) {
      event.preventDefault()
      setIsPending(true)
      setDecryptResult(null)
      const data = Object.fromEntries(formData) as { encrypted_base64: string; iv: string }
      decrypt(data)
        .then((res) => {
          const plaintext = atob(res.decrypted_base64)
          setDecryptResult(plaintext)
        })
        .catch((err) => toast.error(err.message))
        .finally(() => setIsPending(false))
    },
  })

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Shield className="size-5" /> Cifrar / Descifrar
        </CardTitle>
        <CardDescription>
          Cifra texto con AES o descifra usando la llave almacenada
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="flex gap-2">
          <Button
            variant={mode === "encrypt" ? "default" : "outline"}
            size="sm"
            onClick={() => setMode("encrypt")}
          >
            Cifrar
          </Button>
          <Button
            variant={mode === "decrypt" ? "default" : "outline"}
            size="sm"
            onClick={() => setMode("decrypt")}
          >
            Descifrar
          </Button>
        </div>

        {mode === "encrypt" ? (
          <form id={encryptForm.id} onSubmit={encryptForm.onSubmit} noValidate>
            <fieldset disabled={isPending} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor={encryptFields.plaintext.id}>Texto plano</Label>
                <Input
                  id={encryptFields.plaintext.id}
                  name={encryptFields.plaintext.name}
                  placeholder="Ingresa el texto a cifrar..."
                  defaultValue={encryptFields.plaintext.initialValue}
                />
                {encryptFields.plaintext.errors && (
                  <p className="text-sm text-destructive">{encryptFields.plaintext.errors}</p>
                )}
              </div>

              <Button type="submit" disabled={isPending}>
                {isPending && <Loader2 className="size-4 animate-spin" />}
                {isPending ? "Cifrando..." : "Cifrar con AES"}
              </Button>
            </fieldset>
          </form>
        ) : (
          <form id={decryptForm.id} onSubmit={decryptForm.onSubmit} noValidate>
            <fieldset disabled={isPending} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor={decryptFields.encrypted_base64.id}>Texto cifrado (base64)</Label>
                <textarea
                  id={decryptFields.encrypted_base64.id}
                  name={decryptFields.encrypted_base64.name}
                  placeholder="Pega el texto cifrado en base64..."
                  defaultValue={decryptFields.encrypted_base64.initialValue}
                  className="flex min-h-[80px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-xs transition-colors focus-visible:outline-hidden focus-visible:ring-1 focus-visible:ring-ring placeholder:text-muted-foreground disabled:cursor-not-allowed disabled:opacity-50"
                />
                {decryptFields.encrypted_base64.errors && (
                  <p className="text-sm text-destructive">{decryptFields.encrypted_base64.errors}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor={decryptFields.iv.id}>IV (base64)</Label>
                <Input
                  id={decryptFields.iv.id}
                  name={decryptFields.iv.name}
                  placeholder="Pega el IV en base64..."
                  defaultValue={decryptFields.iv.initialValue}
                />
                {decryptFields.iv.errors && (
                  <p className="text-sm text-destructive">{decryptFields.iv.errors}</p>
                )}
              </div>

              <Button type="submit" disabled={isPending}>
                {isPending && <Loader2 className="size-4 animate-spin" />}
                {isPending ? "Descifrando..." : "Descifrar con AES"}
              </Button>
            </fieldset>
          </form>
        )}

        {mode === "encrypt" && encryptResult && (
          <>
            <Separator />
            <div className="space-y-2 rounded-md bg-muted p-3">
              <div>
                <Label className="text-xs text-muted-foreground">Texto cifrado (base64)</Label>
                <p className="mt-1 break-all font-mono text-sm">{encryptResult.encrypted_base64}</p>
              </div>
              <div>
                <Label className="text-xs text-muted-foreground">IV (base64)</Label>
                <p className="mt-1 break-all font-mono text-sm">{encryptResult.iv}</p>
              </div>
            </div>
          </>
        )}

        {mode === "decrypt" && decryptResult !== null && (
          <>
            <Separator />
            <div className="rounded-md bg-muted p-3">
              <Label className="text-xs text-muted-foreground">Texto descifrado</Label>
              <p className="mt-1 break-all font-mono text-sm">{decryptResult}</p>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}
