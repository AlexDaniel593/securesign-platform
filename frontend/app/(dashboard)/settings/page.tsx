"use client"

import { useEffect, useState } from "react"
import { toast } from "sonner"
import { Eye, EyeOff, Loader2, Lock, User, Mail, Shield, Calendar } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { getMe, changePassword, type UserProfile } from "@/features/auth/services/auth-service"

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("es-MX", {
    day: "2-digit",
    month: "long",
    year: "numeric",
  })
}

export default function SettingsPage() {
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [loading, setLoading] = useState(true)

  const [currentPassword, setCurrentPassword] = useState("")
  const [newPassword, setNewPassword] = useState("")
  const [showCurrentPw, setShowCurrentPw] = useState(false)
  const [showNewPw, setShowNewPw] = useState(false)
  const [changing, setChanging] = useState(false)

  useEffect(() => {
    getMe()
      .then(setProfile)
      .catch((err) => toast.error(err.message))
      .finally(() => setLoading(false))
  }, [])

  async function handleChangePassword(e: React.FormEvent) {
    e.preventDefault()
    setChanging(true)
    try {
      await changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      })
      toast.success("Contrasena actualizada correctamente")
      setCurrentPassword("")
      setNewPassword("")
    } catch (err) {
      toast.error((err as Error).message)
    } finally {
      setChanging(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="size-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Mi Perfil</h1>
        <p className="text-muted-foreground">Gestiona tu informacion personal y contrasena</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="size-5" /> Informacion personal
            </CardTitle>
            <CardDescription>Datos de tu cuenta</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {profile && (
              <>
                <div className="flex items-center gap-3 rounded-md bg-muted p-3">
                  <User className="size-5 text-muted-foreground" />
                  <div>
                    <p className="text-xs text-muted-foreground">Nombre</p>
                    <p className="text-sm font-medium">{profile.name}</p>
                  </div>
                </div>

                <div className="flex items-center gap-3 rounded-md bg-muted p-3">
                  <Mail className="size-5 text-muted-foreground" />
                  <div>
                    <p className="text-xs text-muted-foreground">Correo electronico</p>
                    <p className="text-sm font-medium">{profile.email}</p>
                  </div>
                </div>

                <div className="flex items-center gap-3 rounded-md bg-muted p-3">
                  <Shield className="size-5 text-muted-foreground" />
                  <div>
                    <p className="text-xs text-muted-foreground">Rol</p>
                    <p className="text-sm font-medium">{profile.is_admin ? "Administrador" : "Usuario"}</p>
                  </div>
                </div>

                <div className="flex items-center gap-3 rounded-md bg-muted p-3">
                  <Calendar className="size-5 text-muted-foreground" />
                  <div>
                    <p className="text-xs text-muted-foreground">Fecha de registro</p>
                    <p className="text-sm font-medium">{formatDate(profile.created_at)}</p>
                  </div>
                </div>
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Lock className="size-5" /> Cambiar contrasena
            </CardTitle>
            <CardDescription>Actualiza tu contrasena de acceso</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleChangePassword} className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Contrasena actual</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
                  <Input
                    type={showCurrentPw ? "text" : "password"}
                    placeholder="Ingresa tu contrasena actual"
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
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Nueva contrasena</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
                  <Input
                    type={showNewPw ? "text" : "password"}
                    placeholder="Ingresa la nueva contrasena"
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
                <p className="text-xs text-muted-foreground">Minimo 8 caracteres</p>
              </div>

              <Button
                type="submit"
                className="w-full"
                disabled={changing || !currentPassword || !newPassword}
              >
                {changing && <Loader2 className="mr-1 size-4 animate-spin" />}
                {changing ? "Guardando..." : "Guardar contrasena"}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
