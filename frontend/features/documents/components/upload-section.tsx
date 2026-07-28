"use client"

import { useForm } from "@conform-to/react"
import { parseWithZod } from "@conform-to/zod"
import { z } from "zod"
import { toast } from "sonner"
import { Loader2, Upload } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { uploadDocument } from "@/features/documents/services/documents-service"
import { useRef, useState } from "react"

const MAX_FILE_SIZE = 10 * 1024 * 1024 // 10 MB

const schema = z.object({
  file: z.instanceof(File, { message: "Selecciona un archivo PDF" }),
})

interface UploadSectionProps {
  onUploadSuccess: () => void
}

export function UploadSection({ onUploadSuccess }: UploadSectionProps) {
  const [isPending, setIsPending] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [form, fields] = useForm({
    onValidate({ formData }) {
      return parseWithZod(formData, { schema })
    },
    onSubmit(event, { formData }) {
      event.preventDefault()
      const file = formData.get("file") as File | null

      // Client-side 10 MB guard — checked before any network request
      if (file && file.size > MAX_FILE_SIZE) {
        toast.error("El archivo excede el límite de 10 MB")
        return
      }

      if (!file) return

      setIsPending(true)
      uploadDocument(file)
        .then(() => {
          toast.success("Documento subido correctamente")
          onUploadSuccess()
          // Reset the file input
          if (fileInputRef.current) {
            fileInputRef.current.value = ""
          }
        })
        .catch((err: Error) => {
          toast.error(err.message)
        })
        .finally(() => setIsPending(false))
    },
  })

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Upload className="size-5" /> Subir Documento
        </CardTitle>
        <CardDescription>
          Selecciona un archivo PDF (máx. 10 MB)
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form id={form.id} onSubmit={form.onSubmit} noValidate>
          <fieldset disabled={isPending} className="space-y-4">
            <div className="space-y-2">
              <input
                ref={fileInputRef}
                id={fields.file.id}
                name={fields.file.name}
                type="file"
                accept=".pdf"
                className="block w-full text-sm text-muted-foreground
                  file:mr-4 file:rounded-md file:border-0
                  file:bg-primary file:px-4 file:py-2
                  file:text-sm file:font-semibold file:text-primary-foreground
                  hover:file:bg-primary/90"
              />
              {fields.file.errors && (
                <p className="text-sm text-destructive">{fields.file.errors}</p>
              )}
            </div>

            <Button type="submit" disabled={isPending}>
              {isPending && <Loader2 className="size-4 mr-2 animate-spin" />}
              {isPending ? "Subiendo..." : "Subir Documento"}
            </Button>
          </fieldset>
        </form>
      </CardContent>
    </Card>
  )
}
