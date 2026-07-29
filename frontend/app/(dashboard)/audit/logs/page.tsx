"use client"

import { useEffect, useState } from "react"
import { toast } from "sonner"
import { Loader2, ScrollText, CheckCircle, XCircle, LogIn, LogOut, UserPlus } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { listAllLogs, listOwnLogs, getMetrics, type AuditLogItem, type AuditMetrics } from "@/features/audit/services/audit-service"
import { getToken } from "@/lib/auth"
import { cn } from "@/lib/utils"

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("es-MX", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
}

function ActionBadge({ action }: { action: string }) {
  const config: Record<string, { icon: typeof CheckCircle; color: string; label: string }> = {
    LOGIN_SUCCESS: { icon: LogIn, color: "bg-green-100 text-green-800", label: "Login OK" },
    LOGIN_FAILED: { icon: XCircle, color: "bg-red-100 text-red-800", label: "Login fallido" },
    LOGOUT: { icon: LogOut, color: "bg-muted text-muted-foreground", label: "Logout" },
    REGISTER: { icon: UserPlus, color: "bg-blue-100 text-blue-800", label: "Registro" },
  }
  const cfg = config[action] ?? { icon: ScrollText, color: "bg-muted text-muted-foreground", label: action }
  const Icon = cfg.icon
  return (
    <span className={cn("inline-flex items-center gap-1 rounded px-2 py-0.5 text-xs font-medium", cfg.color)}>
      <Icon className="size-3" />
      {cfg.label}
    </span>
  )
}

export default function AuditLogsPage() {
  const [isAdmin, setIsAdmin] = useState(false)
  const [logs, setLogs] = useState<AuditLogItem[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [metrics, setMetrics] = useState<AuditMetrics | null>(null)

  useEffect(() => {
    const token = getToken()
    if (!token) return
    fetch(`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1"}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => r.json())
      .then((data) => {
        if (data.is_admin) {
          setIsAdmin(true)
          getMetrics().then(setMetrics).catch(() => {})
        }
      })
      .catch(() => {})
  }, [])

  useEffect(() => {
    setLoading(true)
    const fetchFn = isAdmin ? listAllLogs : listOwnLogs
    fetchFn(page)
      .then((res) => {
        setLogs(res.items)
        setTotal(res.total)
      })
      .catch((err) => toast.error(err.message))
      .finally(() => setLoading(false))
  }, [page, isAdmin])

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Logs de Auditoria</h1>
        <p className="text-muted-foreground">
          {isAdmin ? "Todas las acciones del sistema" : "Tus acciones registradas"}
        </p>
      </div>

      {isAdmin && metrics && (
        <div className="grid gap-4 md:grid-cols-4">
          {[
            { label: "Usuarios", value: metrics.total_users },
            { label: "Documentos", value: metrics.total_documents },
            { label: "Firmas", value: metrics.total_signatures },
            { label: "Logins fallidos", value: metrics.failed_logins },
          ].map(({ label, value }) => (
            <Card key={label}>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">{label}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">{value}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Actividad</CardTitle>
          <CardDescription>{total} registros en total</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center gap-2 py-8 text-muted-foreground">
              <Loader2 className="size-4 animate-spin" />
              Cargando...
            </div>
          ) : logs.length === 0 ? (
            <p className="py-8 text-center text-sm text-muted-foreground">No hay registros.</p>
          ) : (
            <div className="space-y-2">
              {logs.map((log) => (
                <div key={log.id} className="rounded border bg-card p-3 text-sm">
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0 space-y-1">
                      <div className="flex items-center gap-2">
                        <ActionBadge action={log.action} />
                        {log.resource_type && (
                          <span className="text-xs text-muted-foreground">
                            {log.resource_type}
                            {log.resource_id ? ` #${log.resource_id}` : ""}
                          </span>
                        )}
                      </div>
                      {log.user_email && (
                        <p className="text-xs text-muted-foreground">
                          Usuario: {log.user_email}
                        </p>
                      )}
                      {log.ip_address && (
                        <p className="text-xs text-muted-foreground">
                          IP: {log.ip_address}
                        </p>
                      )}
                      {log.details && (
                        <p className="text-xs text-muted-foreground">{log.details}</p>
                      )}
                    </div>
                    <span className="shrink-0 text-xs text-muted-foreground">
                      {formatDate(log.created_at)}
                    </span>
                  </div>
                </div>
              ))}

              {total > 20 && (
                <div className="flex justify-center gap-2 pt-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1}
                  >
                    Anterior
                  </Button>
                  <span className="flex items-center px-3 text-sm text-muted-foreground">
                    Pagina {page} de {Math.ceil(total / 20)}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage((p) => p + 1)}
                    disabled={page * 20 >= total}
                  >
                    Siguiente
                  </Button>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
