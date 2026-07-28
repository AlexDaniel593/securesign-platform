"use client"

import { useEffect, useState } from "react"
import { Loader2, CheckCircle, XCircle, ShieldAlert } from "lucide-react"
import type { SignatureItem, VerificationResult } from "@/features/documents/types"
import { getSignatures, verifySignature } from "@/features/documents/services/documents-service"
import { Button } from "@/components/ui/button"

interface SignaturesPanelProps {
  documentId: number
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleDateString("es-MX", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
}

export function SignaturesPanel({ documentId }: SignaturesPanelProps) {
  const [signatures, setSignatures] = useState<SignatureItem[] | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [verifyingSigId, setVerifyingSigId] = useState<number | null>(null)

  useEffect(() => {
    // Lazy fetch on first expand; cache in local state on re-expand
    if (signatures === null) {
      setIsLoading(true)
      getSignatures(documentId)
        .then((res) => {
          const sorted = [...res.signatures].sort(
            (a, b) =>
              new Date(b.signed_at).getTime() - new Date(a.signed_at).getTime()
          )
          setSignatures(sorted)
        })
        .catch(() => setSignatures([]))
        .finally(() => setIsLoading(false))
    }
  }, [documentId, signatures])

  const handleVerify = async (sigId: number) => {
    setVerifyingSigId(sigId)
    try {
      const result: VerificationResult = await verifySignature(documentId, sigId)
      setSignatures((prev) =>
        (prev ?? []).map((s) =>
          s.id === sigId
            ? {
                ...s,
                is_valid: result.is_valid,
                verified_at: result.verified_at,
                signer_name: result.signer_name,
                signer_email: result.signer_email,
              }
            : s
        )
      )
    } catch {
      // Verification failed silently — user can retry
    } finally {
      setVerifyingSigId(null)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 py-2 text-sm text-muted-foreground">
        <Loader2 className="size-4 animate-spin" />
        Cargando firmas...
      </div>
    )
  }

  if (!signatures || signatures.length === 0) {
    return (
      <div className="py-2 text-sm text-muted-foreground">
        Este documento aún no tiene firmas.
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
        Firmas ({signatures.length})
      </p>
      <ul className="space-y-2">
        {signatures.map((sig) => {
          const isVerified = sig.is_valid !== null && sig.is_valid !== undefined
          const isValid = sig.is_valid === true
          return (
            <li
              key={sig.id}
              className="rounded border bg-card p-3 text-sm"
            >
              <div className="flex flex-col gap-1">
                {/* Signer identity */}
                {(sig.signer_name || sig.signer_email) && (
                  <span className="text-xs text-muted-foreground">
                    Firmado por: {sig.signer_name || sig.signer_email}
                  </span>
                )}

                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">
                    ID: {sig.id}
                    {sig.certificate_id !== undefined &&
                      sig.certificate_id !== null &&
                      ` · Certificado: ${sig.certificate_id}`}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {formatDate(sig.signed_at)}
                  </span>
                </div>
                <code className="mt-1 block break-all rounded bg-muted px-2 py-1 font-mono text-xs">
                  {sig.signature_blob.length > 80
                    ? `${sig.signature_blob.slice(0, 80)}...`
                    : sig.signature_blob}
                </code>

                {/* Status badge + Verify button */}
                <div className="mt-1 flex items-center gap-2">
                  {isVerified ? (
                    <span
                      className={`inline-flex items-center gap-1 rounded px-2 py-0.5 text-xs font-medium ${
                        isValid
                          ? "bg-green-100 text-green-800"
                          : "bg-red-100 text-red-800"
                      }`}
                    >
                      {isValid ? (
                        <>
                          <CheckCircle className="size-3" />
                          Válida
                        </>
                      ) : (
                        <>
                          <XCircle className="size-3" />
                          Inválida
                        </>
                      )}
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 rounded bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground">
                      <ShieldAlert className="size-3" />
                      No verificada
                    </span>
                  )}

                  <Button
                    variant="outline"
                    size="sm"
                    className="h-7 text-xs"
                    onClick={() => handleVerify(sig.id)}
                    disabled={verifyingSigId === sig.id}
                  >
                    {verifyingSigId === sig.id ? (
                      <Loader2 className="mr-1 size-3 animate-spin" />
                    ) : null}
                    {verifyingSigId === sig.id ? "Verificando..." : "Verificar"}
                  </Button>
                </div>

                {/* Old status line (fallback) */}
                {sig.is_valid !== undefined && !isVerified && (
                  <span
                    className={`mt-1 text-xs font-medium ${
                      sig.is_valid ? "text-green-600" : "text-red-600"
                    }`}
                  >
                    {sig.is_valid ? "✓ Válida" : "✗ Inválida"}
                  </span>
                )}
              </div>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
