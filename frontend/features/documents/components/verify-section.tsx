"use client"

import { useState, useCallback, useRef } from "react"
import { DndContext, useDroppable } from "@dnd-kit/core"
import { toast } from "sonner"
import {
  Loader2,
  CheckCircle,
  XCircle,
  ShieldAlert,
  FileText,
  ScrollText,
  Ban,
  RotateCcw,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { verifyFile } from "@/features/documents/services/documents-service"
import type { VerifyFileSignatureItem } from "@/features/documents/types"
import { cn } from "@/lib/utils"

const MAX_FILE_SIZE = 10 * 1024 * 1024

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

function DropZone({ onFile }: { onFile: (file: File) => void }) {
  const [isDragOver, setIsDragOver] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const { setNodeRef, isOver } = useDroppable({ id: "verify-drop" })

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(false)
    const file = e.dataTransfer.files?.[0]
    if (file) onFile(file)
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) onFile(file)
  }

  const active = isOver || isDragOver

  return (
    <>
      <input
        ref={inputRef}
        type="file"
        accept=".pdf"
        className="hidden"
        onChange={handleFileChange}
      />
      <div
        ref={setNodeRef}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={cn(
          "flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 transition-colors",
          active
            ? "border-primary bg-primary/5"
            : "border-muted-foreground/25 hover:border-muted-foreground/50"
        )}
      >
        <ScrollText className={cn("mb-2 size-8", active ? "text-primary" : "text-muted-foreground")} />
        <p className="text-sm font-medium">
          {active ? "Suelta el archivo aquí" : "Arrastra un PDF firmado"}
        </p>
        <p className="mt-1 text-xs text-muted-foreground">
          o haz clic para seleccionar (máx. 10 MB)
        </p>
      </div>
    </>
  )
}

function SignatureBadge({ is_valid }: { is_valid: boolean }) {
  if (is_valid) {
    return (
      <span className="inline-flex items-center gap-1 rounded bg-green-100 px-2 py-0.5 text-xs font-medium text-green-800">
        <CheckCircle className="size-3" />
        Válida
      </span>
    )
  }
  return (
    <span className="inline-flex items-center gap-1 rounded bg-red-100 px-2 py-0.5 text-xs font-medium text-red-800">
      <XCircle className="size-3" />
      Inválida
    </span>
  )
}

export function VerifySection() {
  const [file, setFile] = useState<File | null>(null)
  const [verifying, setVerifying] = useState(false)
  const [results, setResults] = useState<VerifyFileSignatureItem[] | null>(null)

  const handleFile = useCallback((f: File) => {
    if (f.type !== "application/pdf") {
      toast.error("Solo se permiten archivos PDF")
      return
    }
    if (f.size > MAX_FILE_SIZE) {
      toast.error("El archivo excede el límite de 10 MB")
      return
    }
    setFile(f)
    setResults(null)
  }, [])

  const handleVerify = async () => {
    if (!file) return
    setVerifying(true)
    try {
      const res = await verifyFile(file)
      setResults(res.signatures)
    } catch (err) {
      toast.error((err as Error).message)
    } finally {
      setVerifying(false)
    }
  }

  const handleReset = () => {
    setFile(null)
    setResults(null)
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span className="flex items-center gap-2">
            <ShieldAlert className="size-5" /> Verificar Firmas
          </span>
          {(file || results) && (
            <Button variant="ghost" size="icon" onClick={handleReset} title="Reiniciar">
              <RotateCcw className="size-4" />
            </Button>
          )}
        </CardTitle>
        <CardDescription>
          Sube un documento PDF firmado para verificar sus firmas digitales sin almacenarlo
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <DndContext>
          <DropZone onFile={handleFile} />
        </DndContext>

        {file && (
          <div className="flex items-center gap-3 rounded-md bg-muted p-3">
            <FileText className="size-5 shrink-0 text-muted-foreground" />
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium">{file.name}</p>
              <p className="text-xs text-muted-foreground">
                {(file.size / 1024 / 1024).toFixed(2)} MB
              </p>
            </div>
            <Button onClick={handleVerify} disabled={verifying} size="sm">
              {verifying && <Loader2 className="mr-1 size-4 animate-spin" />}
              {verifying ? "Verificando..." : "Verificar"}
            </Button>
          </div>
        )}

        {verifying && (
          <div className="flex items-center gap-2 py-4 text-sm text-muted-foreground">
            <Loader2 className="size-4 animate-spin" />
            Buscando firmas...
          </div>
        )}

        {results !== null && !verifying && (
          <div className="space-y-2">
            {results.length === 0 ? (
              <div className="rounded-md border bg-muted/30 p-4 text-center text-sm text-muted-foreground">
                <Ban className="mx-auto mb-1 size-5" />
                No se encontraron firmas asociadas a este documento.
              </div>
            ) : (
              <>
                <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  Firmas encontradas ({results.length})
                </p>
                <ul className="space-y-2">
                  {results.map((sig) => (
                    <li key={sig.id} className="rounded border bg-card p-3 text-sm">
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0 space-y-1">
                          {sig.signer_name && (
                            <p className="text-xs text-muted-foreground">
                              Firmado por: {sig.signer_name}{" "}
                              {sig.signer_email ? `(${sig.signer_email})` : ""}
                            </p>
                          )}
                          <p className="text-xs text-muted-foreground">
                            {formatDate(sig.signed_at)}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            Certificado:{" "}
                            {sig.certificate_status === "valid"
                              ? "Válido"
                              : sig.certificate_status === "revoked"
                                ? "Revocado"
                                : sig.certificate_status === "expired"
                                  ? "Expirado"
                                  : "No encontrado"}
                          </p>
                        </div>
                        <div className="flex shrink-0 items-center gap-2">
                          <SignatureBadge is_valid={sig.is_valid} />
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              </>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}