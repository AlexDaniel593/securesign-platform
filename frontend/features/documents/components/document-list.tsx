"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { FileText, ChevronLeft, ChevronRight, Loader2 } from "lucide-react"
import type { DocumentItem } from "@/features/documents/types"
import {
  listDocuments,
  deleteDocument,
  renameDocument,
} from "@/features/documents/services/documents-service"
import { DocumentRow } from "@/features/documents/components/document-row"
import { toast } from "sonner"

const LIMIT = 20

interface DocumentListProps {
  refetchTrigger: number
}

export function DocumentList({ refetchTrigger }: DocumentListProps) {
  const [documents, setDocuments] = useState<DocumentItem[]>([])
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [expandedId, setExpandedId] = useState<number | null>(null)

  const fetchDocuments = () => {
    setIsLoading(true)
    listDocuments(page, LIMIT)
      .then((res) => {
        setDocuments(res.items)
        setTotal(res.total)
      })
      .catch((err: Error) => toast.error(err.message))
      .finally(() => setIsLoading(false))
  }

  // Initial load + refetch on page change or external trigger
  useEffect(() => {
    fetchDocuments()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, refetchTrigger])

  const hasPrev = page > 1
  const hasNext = page * LIMIT < total

  const handleRename = async (id: number, filename: string) => {
    try {
      const updated = await renameDocument(id, { filename })
      setDocuments((prev) =>
        prev.map((doc) =>
          doc.id === id ? { ...doc, filename: updated.filename } : doc
        )
      )
      setEditingId(null)
      toast.success("Documento renombrado correctamente")
    } catch (err: unknown) {
      toast.error((err as Error).message)
      // Stale row — refetch to reconcile
      fetchDocuments()
    }
  }

  const handleDelete = async (id: number) => {
    if (!window.confirm("¿Estás seguro de eliminar este documento?")) return

    try {
      await deleteDocument(id)
      toast.success("Documento eliminado correctamente")
      fetchDocuments()
    } catch (err: unknown) {
      toast.error((err as Error).message)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText className="size-5" /> Mis Documentos
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="size-6 animate-spin text-muted-foreground" />
          </div>
        ) : documents.length === 0 ? (
          <div className="rounded-md border bg-muted/30 p-8 text-center">
            <p className="text-sm text-muted-foreground">
              No hay documentos aún. Sube tu primer archivo PDF.
            </p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto rounded-md border">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-muted/50">
                    <th className="px-4 py-3 text-left font-medium">Nombre</th>
                    <th className="px-4 py-3 text-left font-medium hidden sm:table-cell">
                      Tamaño
                    </th>
                    <th className="px-4 py-3 text-left font-medium hidden md:table-cell">
                      Subido
                    </th>
                    <th className="px-4 py-3 text-right font-medium">
                      Acciones
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {documents.map((doc) => (
                    <DocumentRow
                      key={doc.id}
                      document={doc}
                      isEditing={editingId === doc.id}
                      isExpanded={expandedId === doc.id}
                      onEdit={() => setEditingId(doc.id)}
                      onCancelEdit={() => setEditingId(null)}
                      onRename={handleRename}
                      onDelete={handleDelete}
                      onToggleSignatures={() =>
                        setExpandedId(
                          expandedId === doc.id ? null : doc.id
                        )
                      }
                      onRefetch={fetchDocuments}
                    />
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-between">
              <p className="text-xs text-muted-foreground">
                {total > 0
                  ? `Mostrando ${(page - 1) * LIMIT + 1}–${Math.min(page * LIMIT, total)} de ${total}`
                  : "Sin resultados"}
              </p>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={!hasPrev}
                  onClick={() => setPage((p) => p - 1)}
                >
                  <ChevronLeft className="size-4" />
                  Anterior
                </Button>
                <span className="text-xs text-muted-foreground tabular-nums">
                  Pág. {page}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={!hasNext}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Siguiente
                  <ChevronRight className="size-4" />
                </Button>
              </div>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}
