import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { FileText, KeyRound, Shield, Fingerprint } from "lucide-react"

const stats = [
  { label: "Documentos firmados", value: "0", icon: FileText },
  { label: "Certificados activos", value: "0", icon: Shield },
  { label: "Pares de llaves", value: "0", icon: KeyRound },
  { label: "Firmas realizadas", value: "0", icon: Fingerprint },
]

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          Resumen de tu actividad en SecureSign
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map(({ label, value, icon: Icon }) => (
          <Card key={label}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">{label}</CardTitle>
              <Icon className="size-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold">{value}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Actividad reciente</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              No hay actividad reciente. Comienza firmando un documento o generando un par de llaves.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Accesos rápidos</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <p className="text-sm text-muted-foreground">
              Usa las herramientas de la barra lateral para firmar documentos,
              administrar certificados y realizar operaciones criptográficas.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
