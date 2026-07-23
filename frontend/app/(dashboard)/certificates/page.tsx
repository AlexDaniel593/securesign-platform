"use client"

import { useState } from "react"
import { CertificateList } from "@/features/certificates/components/certificate-list"
import { IssueCertificateForm } from "@/features/certificates/components/issue-certificate-form"
import { VerifyCertificate } from "@/features/certificates/components/verify-certificate"

export default function CertificatesPage() {
  const [refreshKey, setRefreshKey] = useState(0)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Certificados</h1>
        <p className="text-muted-foreground">
          Emite, administra y valida tus certificados digitales
        </p>
      </div>
      <div className="grid gap-6 md:grid-cols-2">
        <IssueCertificateForm onIssued={() => setRefreshKey((k) => k + 1)} />
        <VerifyCertificate />
      </div>
      <div key={refreshKey}>
        <CertificateList />
      </div>
    </div>
  )
}
