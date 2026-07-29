"use client"

import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import { cn } from "@/lib/utils"
import { LayoutDashboard, FileText, Shield, KeyRound, LogOut, Users, ScrollText, Settings } from "lucide-react"
import { toast } from "sonner"
import { clearToken, getToken } from "@/lib/auth"
import { useEffect, useState } from "react"

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/documents", label: "Documentos", icon: FileText },
  { href: "/certificates", label: "Certificados", icon: Shield },
  { href: "/crypto", label: "Herramientas Crypto", icon: KeyRound },
]

const adminItems = [
  { href: "/admin/users", label: "Usuarios", icon: Users },
  { href: "/audit/logs", label: "Logs de Auditoria", icon: ScrollText },
]

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const pathname = usePathname()
  const router = useRouter()
  const [isAdmin, setIsAdmin] = useState(false)

  useEffect(() => {
    const token = getToken()
    if (!token) {
      router.push("/")
      return
    }
    fetch(`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1"}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => r.json())
      .then((data) => {
        if (data.is_admin) setIsAdmin(true)
      })
      .catch(() => {})
  }, [router])

  function handleLogout() {
    const token = getToken()
    if (token) {
      fetch(`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1"}/auth/logout`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      }).catch(() => {})
    }
    clearToken()
    toast.success("Sesion cerrada")
    router.push("/")
  }

  return (
    <div className="flex h-screen">
      <aside className="flex w-64 flex-col bg-card border-r">
        <div className="flex items-center gap-2 p-6 border-b">
          <KeyRound className="size-6 text-primary" />
          <h2 className="text-xl font-bold text-primary">SecureSign</h2>
        </div>

        <nav className="flex-1 space-y-1 p-4">
          {navItems.map(({ href, label, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                pathname === href || pathname.startsWith(href + "/")
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              )}
            >
              <Icon className="size-4" />
              {label}
            </Link>
          ))}

          {isAdmin && (
            <>
              <div className="my-3 border-t" />
              <p className="px-3 py-1 text-xs font-medium uppercase tracking-wider text-muted-foreground">
                Administracion
              </p>
              {adminItems.map(({ href, label, icon: Icon }) => (
                <Link
                  key={href}
                  href={href}
                  className={cn(
                    "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                    pathname === href || pathname.startsWith(href + "/")
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                  )}
                >
                  <Icon className="size-4" />
                  {label}
                </Link>
              ))}
            </>
          )}
        </nav>

        <div className="p-4 border-t space-y-1">
          <Link
            href="/settings"
            className={cn(
              "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
              pathname === "/settings"
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
            )}
          >
            <Settings className="size-4" />
            Mi perfil
          </Link>
          <button
            onClick={handleLogout}
            className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
          >
            <LogOut className="size-4" />
            Cerrar sesion
          </button>
        </div>
      </aside>

      <main className="flex-1 overflow-auto p-6 bg-muted/30">
        {children}
      </main>
    </div>
  )
}
