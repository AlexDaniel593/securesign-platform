import Link from "next/link"
import { Button } from "@/components/ui/button"
import { KeyRound, FileSignature, Shield, ArrowRight } from "lucide-react"

const features = [
  {
    icon: KeyRound,
    title: "Cifrado y Hash",
    description: "Genera hashes SHA-256/512, cifra y descifra texto con RSA y AES.",
  },
  {
    icon: FileSignature,
    title: "Firma Digital",
    description: "Firma documentos electrónicos y verifica firmas con certificados digitales.",
  },
  {
    icon: Shield,
    title: "Certificados",
    description: "Administra certificados digitales X.509 con validez jurídica.",
  },
]

export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b bg-card">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4">
          <div className="flex items-center gap-2">
            <KeyRound className="size-6 text-primary" />
            <span className="text-xl font-bold text-primary">SecureSign</span>
          </div>
          <nav className="flex items-center gap-4">
            <Link href="/login">
              <Button variant="ghost">Iniciar sesión</Button>
            </Link>
            <Link href="/register">
              <Button>Crear cuenta</Button>
            </Link>
          </nav>
        </div>
      </header>

      <main className="flex-1">
        <section className="mx-auto max-w-6xl px-4 py-24 text-center">
          <h1 className="text-5xl font-bold tracking-tight">
            Plataforma de Firma Digital
          </h1>
          <p className="mx-auto mt-4 max-w-2xl text-lg text-muted-foreground">
            SecureSign te permite firmar documentos electrónicos, gestionar
            certificados digitales y realizar operaciones criptográficas de
            forma segura y con validez legal.
          </p>
          <div className="mt-8 flex items-center justify-center gap-4">
            <Link href="/register">
              <Button size="lg">
                Comenzar ahora
                <ArrowRight className="ml-2 size-4" />
              </Button>
            </Link>
            <Link href="/login">
              <Button variant="outline" size="lg">
                <span className="text-black">Ya tengo cuenta</span>
              </Button>
            </Link>
          </div>
        </section>

        <section className="border-t bg-muted/30 py-20">
          <div className="mx-auto max-w-6xl px-4">
            <h2 className="text-center text-3xl font-bold">Funcionalidades</h2>
            <div className="mt-12 grid gap-8 md:grid-cols-3">
              {features.map(({ icon: Icon, title, description }) => (
                <div
                  key={title}
                  className="rounded-xl border bg-card p-6 shadow-sm"
                >
                  <div className="flex size-12 items-center justify-center rounded-lg bg-primary/10">
                    <Icon className="size-6 text-primary" />
                  </div>
                  <h3 className="mt-4 text-lg font-semibold text-primary">{title}</h3>
                  <p className="mt-2 text-sm text-muted-foreground">
                    {description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t py-6 text-center text-sm text-muted-foreground">
        &copy; {new Date().getFullYear()} SecureSign &mdash; Proyecto de Seguridad - ESPE
      </footer>
    </div>
  )
}
