"use client"

import { useEffect, useState } from "react"
import { Loader2 } from "lucide-react"
import type { SignatureItem } from "@/features/documents/types"
import { getSignatures } from "@/features/documents/services/documents-service"

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
        {signatures.map((sig) => (
          <li
            key={sig.id}
            className="rounded border bg-card p-3 text-sm"
          >
            <div className="flex flex-col gap-1">
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
              {sig.is_valid !== undefined && (
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
        ))}
      </ul>
    </div>
  )
}
