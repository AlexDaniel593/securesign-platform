"use client"

import { toast } from "sonner"
import { Copy, Loader2, KeyRound, CheckCircle2, XCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  generateKeys,
  getKeyStatus,
} from "@/features/crypto/services/crypto-service"
import { useEffect, useState } from "react"

export function KeyPairTool() {
  const [status, setStatus] = useState<{ has_keys: boolean; fingerprint: string | null } | null>(null)
  const [loadingStatus, setLoadingStatus] = useState(true)
  const [isPending, setIsPending] = useState(false)
  const [result, setResult] = useState<{ fingerprint: string; public_key: string; message: string } | null>(null)

  useEffect(() => {
    getKeyStatus()
      .then(setStatus)
      .catch(() => setStatus({ has_keys: false, fingerprint: null }))
      .finally(() => setLoadingStatus(false))
  }, [])

  async function handleGenerate() {
    setIsPending(true)
    setResult(null)
    try {
      const res = await generateKeys()
      setResult(res)
      setStatus({ has_keys: true, fingerprint: res.fingerprint })
      toast.success("Llaves generadas correctamente")
    } catch (err) {
      toast.error((err as Error).message)
    } finally {
      setIsPending(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <KeyRound className="size-5" /> Par de Llaves RSA
        </CardTitle>
        <CardDescription>
          Genera y administra tus llaves RSA para firma digital
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {loadingStatus ? (
          <p className="text-sm text-muted-foreground">Verificando estado de llaves...</p>
        ) : (
          <div className="flex items-center gap-2 rounded-md bg-muted p-3">
            {status?.has_keys ? (
              <CheckCircle2 className="size-5 text-green-500" />
            ) : (
              <XCircle className="size-5 text-destructive" />
            )}
            <span className="text-sm">
              {status?.has_keys
                ? `Tienes llaves generadas (Huella: ${status.fingerprint?.slice(0, 16)}...)`
                : "No tienes llaves generadas"}
            </span>
          </div>
        )}

        <Button onClick={handleGenerate} disabled={isPending || loadingStatus} className="w-full">
          {isPending && <Loader2 className="size-4 animate-spin" />}
          {isPending ? "Generando..." : "Generar Par de Llaves RSA"}
        </Button>

        {result && (
          <div className="rounded-md bg-muted p-3">
            <div className="flex items-center justify-between">
              <Label className="text-xs text-muted-foreground">Llave pública</Label>
              <button
                onClick={() => {
                  navigator.clipboard.writeText(result.public_key)
                  toast.success("Llave pública copiada al portapapeles")
                }}
                className="text-primary hover:text-foreground"
                title="Copiar llave pública"
              >
                <Copy className="size-4" />
              </button>
            </div>
            <p className="mt-1 break-all font-mono text-xs">{result.public_key.slice(0, 64)}...</p>
            <p className="mt-2 text-xs text-muted-foreground">{result.message}</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function Label({ className, children }: { className?: string; children: React.ReactNode }) {
  return <p className={`text-sm font-medium ${className ?? ""}`}>{children}</p>
}
