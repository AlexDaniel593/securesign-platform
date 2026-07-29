"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { Settings } from "lucide-react"
import { Button } from "@/components/ui/button"
import { getToken } from "@/lib/auth"
import { AuthDropdown } from "@/features/auth/components/auth-dropdown"

export function HeaderActions() {
  const [logged, setLogged] = useState(false)

  useEffect(() => {
    setLogged(!!getToken())
  }, [])

  if (logged) {
    return (
      <Link href="/dashboard">
        <Button variant="ghost" className="gap-2 text-foreground">
          <Settings className="size-4" />
          Mi perfil
        </Button>
      </Link>
    )
  }

  return <AuthDropdown />
}
