"use client"

import { useState } from "react"
import { toast } from "sonner"
import { Loader2, ShieldX } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { revoke } from "@/features/certificates/services/cert-service"

export function RevokeButton({
  certificateId,
  onRevoked,
}: {
  certificateId: number
  onRevoked?: () => void
}) {
  const [isPending, setIsPending] = useState(false)
  const [showReason, setShowReason] = useState(false)
  const [reason, setReason] = useState("")

  async function handleRevoke() {
    setIsPending(true)
    try {
      await revoke(certificateId, reason ? { reason } : undefined)
      toast.success("Certificado revocado correctamente")
      onRevoked?.()
    } catch (err) {
      toast.error((err as Error).message)
    } finally {
      setIsPending(false)
      setShowReason(false)
      setReason("")
    }
  }

  return (
    <div className="space-y-2">
      {showReason ? (
        <div className="space-y-2">
          <Label className="text-xs text-muted-foreground">Motivo de revocación (opcional)</Label>
          <Input
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Ej: Compromiso de llave privada"
            disabled={isPending}
          />
          <div className="flex gap-2">
            <Button
              variant="destructive"
              size="sm"
              onClick={handleRevoke}
              disabled={isPending}
            >
              {isPending && <Loader2 className="size-4 animate-spin" />}
              {isPending ? "Revocando..." : "Confirmar Revocación"}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowReason(false)}
              disabled={isPending}
            >
              Cancelar
            </Button>
          </div>
        </div>
      ) : (
        <Button
          variant="destructive"
          size="sm"
          onClick={() => setShowReason(true)}
        >
          <ShieldX className="size-4" />
          Revocar
        </Button>
      )}
    </div>
  )
}
