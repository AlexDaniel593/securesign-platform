"use client"

import { useEffect, useState } from "react"
import { toast } from "sonner"
import { Eye, EyeOff, Loader2, Settings, Lock, User, X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { getMe, changePassword, type UserProfile } from "@/features/auth/services/auth-service"
import { cn } from "@/lib/utils"

export function ProfileDropdown() {
  const [open, setOpen] = useState(false)
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [loading, setLoading] = useState(false)

  const [showPasswordForm, setShowPasswordForm] = useState(false)
  const [currentPassword, setCurrentPassword] = useState("")
  const [newPassword, setNewPassword] = useState("")
  const [showCurrentPw, setShowCurrentPw] = useState(false)
  const [showNewPw, setShowNewPw] = useState(false)
  const [changing, setChanging] = useState(false)

  useEffect(() => {
    if (!open) return
    setLoading(true)
    getMe()
      .then(setProfile)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [open])

  function handleClose() {
    setOpen(false)
    setShowPasswordForm(false)
    setCurrentPassword("")
    setNewPassword("")
  }

  async function handleChangePassword(e: React.FormEvent) {
    e.preventDefault()
    setChanging(true)
    try {
      await changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      })
      toast.success("Contrasena actualizada")
      handleClose()
    } catch (err) {
      toast.error((err as Error).message)
    } finally {
      setChanging(false)
    }
  }

  function formatDate(dateStr: string): string {
    return new Date(dateStr).toLocaleDateString("es-MX", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    })
  }

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className={cn(
          "flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
          "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
        )}
        title="Mi perfil"
      >
        <Settings className="size-4" />
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={handleClose} />
          <div className="absolute right-0 top-full z-50 mt-2 w-80 rounded-lg border bg-background p-4 shadow-lg text-foreground">
            {loading ? (
              <div className="flex items-center justify-center py-6">
                <Loader2 className="size-4 animate-spin text-muted-foreground" />
              </div>
            ) : !showPasswordForm ? (
              <div className="space-y-4">
                <div className="space-y-3">
                  <div className="flex items-center gap-3">
                    <div className="flex size-10 items-center justify-center rounded-full bg-primary/10">
                      <User className="size-5 text-primary" />
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-medium truncate">{profile?.name ?? "Cargando..."}</p>
                      <p className="text-xs text-muted-foreground truncate">{profile?.email ?? ""}</p>
                    </div>
                  </div>

                  {profile && (
                    <div className="space-y-1 rounded-md bg-muted p-3 text-xs">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Rol</span>
                        <span className="font-medium">{profile.is_admin ? "Administrador" : "Usuario"}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Estado</span>
                        <span className="font-medium">{profile.is_active ? "Activo" : "Inactivo"}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Registro</span>
                        <span className="font-medium">{formatDate(profile.created_at)}</span>
                      </div>
                    </div>
                  )}
                </div>

                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() => setShowPasswordForm(true)}
                >
                  <Lock className="mr-1 size-4" />
                  Cambiar contrasena
                </Button>
              </div>
            ) : (
              <form onSubmit={handleChangePassword} className="space-y-3">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium">Cambiar contrasena</p>
                  <button
                    type="button"
                    onClick={() => setShowPasswordForm(false)}
                    className="text-muted-foreground hover:text-foreground"
                  >
                    <X className="size-4" />
                  </button>
                </div>

                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
                  <Input
                    type={showCurrentPw ? "text" : "password"}
                    placeholder="Contrasena actual"
                    className="pl-10 pr-10 text-foreground"
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowCurrentPw(!showCurrentPw)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    tabIndex={-1}
                  >
                    {showCurrentPw ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                  </button>
                </div>

                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
                  <Input
                    type={showNewPw ? "text" : "password"}
                    placeholder="Nueva contrasena"
                    className="pl-10 pr-10 text-foreground"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    required
                    minLength={8}
                  />
                  <button
                    type="button"
                    onClick={() => setShowNewPw(!showNewPw)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    tabIndex={-1}
                  >
                    {showNewPw ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                  </button>
                </div>

                <Button
                  type="submit"
                  className="w-full"
                  disabled={changing || !currentPassword || !newPassword}
                >
                  {changing && <Loader2 className="mr-1 size-4 animate-spin" />}
                  {changing ? "Guardando..." : "Guardar"}
                </Button>
              </form>
            )}
          </div>
        </>
      )}
    </div>
  )
}
