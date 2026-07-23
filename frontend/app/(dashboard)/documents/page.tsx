"use client"

import { useCallback, useState } from "react"
import { UploadSection } from "@/features/documents/components/upload-section"

export default function DocumentsPage() {
  const [refetchTrigger, setRefetchTrigger] = useState(0)
  const triggerRefetch = useCallback(() => setRefetchTrigger((n) => n + 1), [])

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Documentos</h1>
        <p className="text-muted-foreground">
          Sube, administra y firma tus documentos PDF
        </p>
      </div>

      <UploadSection onUploadSuccess={triggerRefetch} />

      <div className="rounded-md border bg-card p-6 text-center text-sm text-muted-foreground">
        Lista de documentos (próxima fase)
      </div>
    </div>
  )
}
