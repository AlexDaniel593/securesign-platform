"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { LayoutDashboard, FileText, Shield, KeyRound, LogOut } from "lucide-react"
import { toast } from "sonner"
import { useRouter } from "next/navigation"

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/documents", label: "Documentos", icon: FileText },
  { href: "/certificates", label: "Certificados", icon: Shield },
  { href: "/crypto", label: "Herramientas Crypto", icon: KeyRound },
]

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const pathname = usePathname()
  const router = useRouter()

  function handleLogout() {
    document.cookie = "token=; path=/; max-age=0"
    toast.success("Sesión cerrada")
    router.push("/login")
  }

  return (
    <div className="flex h-screen">
      <aside className="flex w-64 flex-col bg-card border-r">
        <div className="flex  -center gap-2 p-6 border-b">
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
        </nav>

        <div className="p-4 border-t">
          <button
            onClick={handleLogout}
            className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
          >
            <LogOut className="size-4" />
            Cerrar sesión
          </button>
        </div>
      </aside>

      <main className="flex-1 overflow-auto p-6 bg-muted/30">
        {children}
      </main>
    </div>
  )
}
