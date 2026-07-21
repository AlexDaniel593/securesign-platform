export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="flex h-screen">
      <aside className="w-64 bg-gray-800 text-white p-4">
        <h2 className="text-xl font-bold mb-6">SecureSign</h2>
        <nav className="space-y-2">
          <a href="/dashboard" className="block py-2 px-4 rounded hover:bg-gray-700">
            Dashboard
          </a>
          <a href="/documents" className="block py-2 px-4 rounded hover:bg-gray-700">
            Documents
          </a>
          <a href="/certificates" className="block py-2 px-4 rounded hover:bg-gray-700">
            Certificates
          </a>
          <a href="/crypto" className="block py-2 px-4 rounded hover:bg-gray-700">
            Crypto Tools
          </a>
        </nav>
      </aside>
      <main className="flex-1 overflow-auto p-6 bg-gray-50">
        {children}
      </main>
    </div>
  )
}
