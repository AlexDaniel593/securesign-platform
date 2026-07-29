"use client"

import { useEffect, useState } from "react"
import { toast } from "sonner"
import { Loader2, Trash2, Shield, ShieldOff } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { listUsers, deleteUser, type UserItem } from "@/features/admin/services/admin-service"

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("es-MX", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  })
}

export default function AdminUsersPage() {
  const [users, setUsers] = useState<UserItem[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [deletingId, setDeletingId] = useState<number | null>(null)

  useEffect(() => {
    setLoading(true)
    listUsers(page)
      .then((res) => {
        setUsers(res.items)
        setTotal(res.total)
      })
      .catch((err) => toast.error(err.message))
      .finally(() => setLoading(false))
  }, [page])

  async function handleDelete(id: number, name: string) {
    if (!confirm(`Eliminar al usuario "${name}"?`)) return
    setDeletingId(id)
    try {
      await deleteUser(id)
      toast.success("Usuario eliminado")
      setUsers((prev) => prev.filter((u) => u.id !== id))
      setTotal((prev) => prev - 1)
    } catch (err) {
      toast.error((err as Error).message)
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Usuarios</h1>
        <p className="text-muted-foreground">Gestionar todos los usuarios del sistema ({total} total)</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Lista de usuarios</CardTitle>
          <CardDescription>Administra cuentas de usuario</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center gap-2 py-8 text-muted-foreground">
              <Loader2 className="size-4 animate-spin" />
              Cargando...
            </div>
          ) : users.length === 0 ? (
            <p className="py-8 text-center text-sm text-muted-foreground">No hay usuarios.</p>
          ) : (
            <div className="space-y-2">
              {users.map((user) => (
                <div
                  key={user.id}
                  className="flex items-center justify-between rounded border bg-card p-3"
                >
                  <div className="min-w-0 space-y-1">
                    <p className="text-sm font-medium">{user.name}</p>
                    <p className="text-xs text-muted-foreground">{user.email}</p>
                    <p className="text-xs text-muted-foreground">
                      Registrado: {formatDate(user.created_at)}
                    </p>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    {user.is_admin ? (
                      <span className="inline-flex items-center gap-1 rounded bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-800">
                        <Shield className="size-3" />
                        Admin
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 rounded bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground">
                        <ShieldOff className="size-3" />
                        Usuario
                      </span>
                    )}
                    <Button
                      variant="destructive"
                      size="sm"
                      className="h-7"
                      onClick={() => handleDelete(user.id, user.name)}
                      disabled={deletingId === user.id}
                    >
                      {deletingId === user.id ? (
                        <Loader2 className="size-3 animate-spin" />
                      ) : (
                        <Trash2 className="size-3" />
                      )}
                    </Button>
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
