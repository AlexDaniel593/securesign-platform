"use client"

import { useState, useRef, useEffect } from "react"
import { z } from "zod"
import { toast } from "sonner"
import { Loader2, Pencil, Download, Trash2, PenLine, ChevronDown, ChevronRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import type { DocumentItem } from "@/features/documents/types"
import {
  downloadDocument,
  signDocument,
} from "@/features/documents/services/documents-service"
import { SignaturesPanel } from "@/features/documents/components/signatures-panel"

const renameSchema = z.string().min(1, "El nombre no puede estar vacío")

interface DocumentRowProps {
  document: DocumentItem
  isEditing: boolean
  isExpanded: boolean
  onEdit: () => void
  onCancelEdit: () => void
  onRename: (id: number, filename: string) => void
  onDelete: (id: number) => void
  onToggleSignatures: () => void
  onRefetch: () => void
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleDateString("es-MX", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  })
}

export function DocumentRow({
  document,
  isEditing,
  isExpanded,
  onEdit,
  onCancelEdit,
  onRename,
  onDelete,
  onToggleSignatures,
  onRefetch,
}: DocumentRowProps) {
  const [renameValue, setRenameValue] = useState(document.filename)
  const [isDownloading, setIsDownloading] = useState(false)
  const [isSigning, setIsSigning] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const cancelledRef = useRef(false)

  // Focus the input when entering edit mode
  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus()
      inputRef.current.select()
    }
  }, [isEditing])

  // Reset rename value to current filename when entering edit mode
  useEffect(() => {
    if (isEditing) {
      cancelledRef.current = false
      setRenameValue(document.filename)
    }
  }, [isEditing, document.filename])

  const handleRenameSubmit = () => {
    if (cancelledRef.current) {
      cancelledRef.current = false
      return
    }
    const trimmed = renameValue.trim()
    const result = renameSchema.safeParse(trimmed)
    if (!result.success) {
      toast.error(result.error.errors[0].message)
      return
    }
    onRename(document.id, trimmed)
  }

  const handleRenameKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleRenameSubmit()
    } else if (e.key === "Escape") {
      cancelledRef.current = true
      onCancelEdit()
    }
  }

  const handleDownload = async () => {
    setIsDownloading(true)
    try {
      const blob = await downloadDocument(document.id)
      const url = URL.createObjectURL(blob)
      const anchor = window.document.createElement("a")
      anchor.href = url
      anchor.download = document.filename
      window.document.body.appendChild(anchor)
      anchor.click()
      window.document.body.removeChild(anchor)
      URL.revokeObjectURL(url)
    } catch (err: unknown) {
      toast.error((err as Error).message)
      // Stale row — refetch to reconcile
      onRefetch()
    } finally {
      setIsDownloading(false)
    }
  }

  const handleSign = async () => {
    setIsSigning(true)
    try {
      const result = await signDocument(document.id)
      toast.success(
        `Documento firmado correctamente. ID de firma: ${result.signature_id}`
      )
    } catch (err: unknown) {
      toast.error((err as Error).message)
    } finally {
      setIsSigning(false)
    }
  }

  return (
    <>
      <tr className="border-b transition-colors hover:bg-muted/30">
        <td className="px-4 py-3">
          {isEditing ? (
            <input
              ref={inputRef}
              type="text"
              value={renameValue}
              onChange={(e) => setRenameValue(e.target.value)}
              onBlur={handleRenameSubmit}
              onKeyDown={handleRenameKeyDown}
              className="w-full rounded border border-input bg-transparent px-2 py-1 text-sm
                focus:outline-none focus:ring-1 focus:ring-ring"
            />
          ) : (
            <span className="font-medium">{document.filename}</span>
          )}
        </td>
        <td className="px-4 py-3 text-muted-foreground hidden sm:table-cell">
          {formatFileSize(document.file_size)}
        </td>
        <td className="px-4 py-3 text-muted-foreground hidden md:table-cell">
          {formatDate(document.uploaded_at)}
        </td>
        <td className="px-4 py-3">
          <div className="flex items-center justify-end gap-1">
            {isEditing ? (
              <>
                <Button
                  variant="ghost"
                  size="icon"
                  className="size-8"
                  onClick={handleRenameSubmit}
                  title="Guardar nombre"
                >
                  <Pencil className="size-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  className="size-8"
                  onClick={onCancelEdit}
                  title="Cancelar"
                >
                  <span className="text-xs font-bold">✕</span>
                </Button>
              </>
            ) : (
              <>
                <Button
                  variant="ghost"
                  size="icon"
                  className="size-8"
                  onClick={onEdit}
                  disabled={isDownloading || isSigning}
                  title="Renombrar"
                >
                  <Pencil className="size-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  className="size-8"
                  onClick={handleDownload}
                  disabled={isDownloading}
                  title="Descargar"
                >
                  {isDownloading ? (
                    <Loader2 className="size-4 animate-spin" />
                  ) : (
                    <Download className="size-4" />
                  )}
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  className="size-8"
                  onClick={() => onDelete(document.id)}
                  disabled={isDownloading || isSigning}
                  title="Eliminar"
                >
                  <Trash2 className="size-4 text-destructive" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  className="size-8"
                  onClick={handleSign}
                  disabled={isSigning}
                  title="Firmar"
                >
                  {isSigning ? (
                    <Loader2 className="size-4 animate-spin" />
                  ) : (
                    <PenLine className="size-4" />
                  )}
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  className="size-8"
                  onClick={onToggleSignatures}
                  title="Ver firmas"
                >
                  {isExpanded ? (
                    <ChevronDown className="size-4" />
                  ) : (
                    <ChevronRight className="size-4" />
                  )}
                </Button>
              </>
            )}
          </div>
        </td>
      </tr>
      {isExpanded && (
        <tr>
          <td colSpan={4} className="px-4 py-3 bg-muted/20">
            <SignaturesPanel documentId={document.id} />
          </td>
        </tr>
      )}
    </>
  )
}
