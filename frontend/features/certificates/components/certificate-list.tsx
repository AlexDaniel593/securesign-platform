"use client"

import { useEffect, useState } from "react"
import { toast } from "sonner"
import {
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Loader2,
  Shield,
  ShieldOff,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { list } from "@/features/certificates/services/cert-service"
import { RevokeButton } from "@/features/certificates/components/revoke-button"
import type { CertificateItem } from "@/features/certificates/types"

function certStatus(cert: CertificateItem): { label: string; icon: typeof CheckCircle2; class: string } {
  if (cert.revoked) {
    return { label: "Revocado", icon: ShieldOff, class: "text-red-500" }
  }
  const now = new Date()
  const validTo = new Date(cert.valid_to)
  if (validTo < now) {
    return { label: "Expirado", icon: AlertTriangle, class: "text-amber-500" }
  }
  return { label: "Activo", icon: CheckCircle2, class: "text-green-500" }
}

export function CertificateList() {
  const [certificates, setCertificates] = useState<CertificateItem[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<boolean | undefined>(undefined)
  const [refreshCounter, setRefreshCounter] = useState(0)

  useEffect(() => {
    setLoading(true)
    list(filter)
      .then((res) => {
        setCertificates(res.items)
        setTotal(res.total)
      })
      .catch((err) => toast.error(err.message))
      .finally(() => setLoading(false))
  }, [filter, refreshCounter])

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span className="flex items-center gap-2">
            <Shield className="size-5" /> Certificados
          </span>
          <Button variant="outline" size="sm" onClick={() => setRefreshCounter((c) => c + 1)} disabled={loading}>
            <RefreshCw className={`size-4 ${loading ? "animate-spin" : ""}`} />
          </Button>
        </CardTitle>
        <CardDescription>
          {total} certificado{total !== 1 ? "s" : ""} encontrado{total !== 1 ? "s" : ""}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex gap-2">
          <Button
            variant={filter === undefined ? "default" : "outline"}
            size="sm"
            onClick={() => setFilter(undefined)}
          >
            Todos
          </Button>
          <Button
            variant={filter === false ? "default" : "outline"}
            size="sm"
            onClick={() => setFilter(false)}
          >
            Activos
          </Button>
          <Button
            variant={filter === true ? "default" : "outline"}
            size="sm"
            onClick={() => setFilter(true)}
          >
            Revocados
          </Button>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="size-6 animate-spin text-muted-foreground" />
          </div>
        ) : certificates.length === 0 ? (
          <p className="py-8 text-center text-sm text-muted-foreground">
            No hay certificados. Emite uno nuevo para comenzar.
          </p>
        ) : (
          <div className="space-y-3">
            {certificates.map((cert) => {
              const status = certStatus(cert)
              const StatusIcon = status.icon
              return (
                <div
                  key={cert.id}
                  className="rounded-lg border p-4 space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <StatusIcon className={`size-5 ${status.class}`} />
                      <span className="font-medium">{cert.subject}</span>
                    </div>
                    {!cert.revoked && (
                      <RevokeButton certificateId={cert.id} onRevoked={() => setRefreshCounter((c) => c + 1)} />
                    )}
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <Label className="text-xs text-muted-foreground">Emisor</Label>
                      <p className="font-mono text-xs">{cert.issuer}</p>
                    </div>
                    <div>
                      <Label className="text-xs text-muted-foreground">Serial</Label>
                      <p className="font-mono text-xs truncate" title={cert.serial_number}>
                        {cert.serial_number.slice(0, 20)}...
                      </p>
                    </div>
                    <div>
                      <Label className="text-xs text-muted-foreground">Válido desde</Label>
                      <p className="text-xs">{new Date(cert.valid_from).toLocaleDateString()}</p>
                    </div>
                    <div>
                      <Label className="text-xs text-muted-foreground">Válido hasta</Label>
                      <p className="text-xs">{new Date(cert.valid_to).toLocaleDateString()}</p>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
