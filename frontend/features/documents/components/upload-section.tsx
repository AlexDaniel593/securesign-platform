"use client"

import { useState, useCallback, useRef } from "react"
import { DndContext, useDroppable } from "@dnd-kit/core"
import { toast } from "sonner"
import { Loader2, Upload, FileText } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { uploadDocument } from "@/features/documents/services/documents-service"
import { cn } from "@/lib/utils"

const MAX_FILE_SIZE = 10 * 1024 * 1024 // 10 MB

interface UploadSectionProps {
  onUploadSuccess: () => void
}

function DropZone({ onFile }: { onFile: (file: File) => void }) {
  const [isDragOver, setIsDragOver] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const { setNodeRef, isOver } = useDroppable({ id: "upload-drop" })

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(false)
  }, [])

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      e.stopPropagation()
      setIsDragOver(false)

      const file = e.dataTransfer.files?.[0]
      if (file) onFile(file)
    },
    [onFile]
  )

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0]
      if (file) onFile(file)
    },
    [onFile]
  )

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
        <Upload className={cn("mb-2 size-8", active ? "text-primary" : "text-muted-foreground")} />
        <p className="text-sm font-medium">
          {active ? "Suelta el archivo aquí" : "Arrastra tu PDF aquí"}
        </p>
        <p className="mt-1 text-xs text-muted-foreground">o haz clic para seleccionar (máx. 10 MB)</p>
      </div>
    </>
  )
}

export function UploadSection({ onUploadSuccess }: UploadSectionProps) {
  const [isPending, setIsPending] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)

  const handleFile = useCallback((file: File) => {
    if (file.type !== "application/pdf") {
      toast.error("Solo se permiten archivos PDF")
      return
    }
    if (file.size > MAX_FILE_SIZE) {
      toast.error("El archivo excede el límite de 10 MB")
      return
    }
    setSelectedFile(file)
  }, [])

  const handleUpload = async () => {
    if (!selectedFile) return
    setIsPending(true)
    try {
      await uploadDocument(selectedFile)
      toast.success("Documento subido correctamente")
      setSelectedFile(null)
      onUploadSuccess()
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
          <Upload className="size-5" /> Subir Documento
        </CardTitle>
        <CardDescription>
          Arrastra un archivo PDF o haz clic para seleccionarlo (máx. 10 MB)
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <DndContext>
          <DropZone onFile={handleFile} />
        </DndContext>

        {selectedFile && (
          <div className="flex items-center gap-3 rounded-md bg-muted p-3">
            <FileText className="size-5 text-muted-foreground shrink-0" />
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium">{selectedFile.name}</p>
              <p className="text-xs text-muted-foreground">
                {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
              </p>
            </div>
            <Button onClick={handleUpload} disabled={isPending} size="sm">
              {isPending && <Loader2 className="size-4 mr-1 animate-spin" />}
              {isPending ? "Subiendo..." : "Subir"}
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}