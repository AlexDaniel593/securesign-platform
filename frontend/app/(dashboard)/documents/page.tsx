"use client"

import { useCallback, useState } from "react"
import { UploadSection } from "@/features/documents/components/upload-section"
import { DocumentList } from "@/features/documents/components/document-list"
import { VerifySection } from "@/features/documents/components/verify-section"

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
      <DocumentList refetchTrigger={refetchTrigger} />
      <VerifySection />
    </div>
  )
}
