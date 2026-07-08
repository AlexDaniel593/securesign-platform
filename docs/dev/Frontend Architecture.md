# Arquitectura del Frontend - Plataforma de Firma Digital

## Stack Tecnológico

| Componente    | Tecnología      | Propósito                                         |
| ------------- | --------------- | ------------------------------------------------- |
| Framework     | Next.js         | Routing y renderizado                             |
| Lenguaje      | TypeScript      | Tipado estático                                   |
| Estilos       | Tailwind CSS    | Utilidades CSS rápidas                            |
| Estado global | Zustand         | Manejo de estado (auth, documentos, certificados) |
| Cliente HTTP  | Axios           | Peticiones API + interceptors JWT                 |
| Persistencia  | Zustand persist | localStorage para token y datos básicos           |

## Estructura de Carpetas

```text
frontend/
├── public/                      # Archivos estáticos (favicon, logos)
│
├── app/                         # Next.js App Router (routing)
│   ├── (auth)/                  # Grupo de rutas sin layout de dashboard
│   │   ├── login/
│   │   │   └── page.tsx         # Página de login
│   │   ├── register/
│   │   │   └── page.tsx         # Página de registro
│   │   └── layout.tsx           # Layout para auth (sin sidebar)
│   │
│   ├── (dashboard)/             # Grupo de rutas con layout protegido
│   │   ├── dashboard/
│   │   │   └── page.tsx         # Dashboard principal
│   │   ├── documents/
│   │   │   └── page.tsx         # Gestión de documentos
│   │   ├── certificates/
│   │   │   └── page.tsx         # Gestión de certificados
│   │   ├── crypto/
│   │   │   └── page.tsx         # Herramientas criptográficas
│   │   ├── audit/               # ⏳ Pendiente (logs)
│   │   │   └── page.tsx
│   │   └── layout.tsx           # Layout con sidebar + autenticación
│   │
│   ├── layout.tsx               # Layout raíz (providers, fuentes)
│   └── globals.css              # Estilos globales + Tailwind
│
├── components/                  # Componentes reutilizables
│   └── ui/                      # UI primitiva (sin lógica de negocio)
│       ├── Button.tsx           # Botón genérico
│       ├── Input.tsx            # Campo de texto
│       ├── Modal.tsx            # Modal genérico
│       ├── Toast.tsx            # Notificaciones
│       ├── Card.tsx             # Tarjeta contenedora
│       ├── Spinner.tsx          # Loader
│       └── Table.tsx            # Tabla genérica
│
├── features/                    # Módulos por dominio (FSD parcial)
│   │
│   ├── auth/                    # Autenticación
│   │   ├── components/
│   │   │   ├── LoginForm.tsx    # Formulario de login
│   │   │   └── RegisterForm.tsx # Formulario de registro
│   │   ├── hooks/
│   │   │   └── useAuth.ts       # Lógica de autenticación
│   │   ├── services/
│   │   │   └── authApi.ts       # Llamadas a /auth/*
│   │   └── types.ts             # Tipos: LoginRequest, RegisterRequest, User
│   │
│   ├── documents/               # Gestión de documentos
│   │   ├── components/
│   │   │   ├── DocumentUpload.tsx    # Subida de archivos
│   │   │   ├── DocumentList.tsx      # Lista paginada
│   │   │   ├── DocumentCard.tsx      │   │   │   ├── SignButton.tsx        # Botón para firmar
│   │   │   ├── VerifySignature.tsx   # Verificador de firma
│   │   │   └── DocumentDetail.tsx    # Vista detalle
│   │   ├── hooks/
│   │   │   └── useDocuments.ts  # CRUD + firma
│   │   ├── services/
│   │   │   └── documentApi.ts   # Llamadas a /documents/*, /crypto/*
│   │   └── types.ts             # Document, Signature, UploadResponse
│   │
│   ├── certificates/            # Certificados digitales
│   │   ├── components/
│   │   │   ├── CertificateList.tsx    # Lista de certificados
│   │   │   ├── CertificateCard.tsx    │   │   │   ├── IssueCertificateForm.tsx # Emitir nuevo certificado
│   │   │   ├── RevokeButton.tsx       # Revocar certificado
│   │   │   └── VerifyCertificate.tsx  # Validar certificado
│   │   ├── hooks/
│   │   │   └── useCertificates.ts # Lógica de certificados
│   │   ├── services/
│   │   │   └── certApi.ts        # Llamadas a /certificates/*
│   │   └── types.ts              # Certificate, IssueRequest
│   │
│   ├── crypto/                  # Herramientas criptográficas
│   │   ├── components/
│   │   │   ├── KeyGenerator.tsx     # Generar par RSA
│   │   │   ├── HashCalculator.tsx   # Calcular SHA-256
│   │   │   ├── EncryptDecrypt.tsx   # AES cifrado/descifrado
│   │   │   └── KeyStatus.tsx        # Mostrar estado de claves
│   │   ├── hooks/
│   │   │   └── useCrypto.ts     # Lógica criptográfica
│   │   ├── services/
│   │   │   └── cryptoApi.ts     # Llamadas a /crypto/*
│   │   └── types.ts             # KeyStatus, HashResponse, EncryptRequest
│   │
│   └── audit/                   # ⏳ Pendiente (logs)
│       ├── components/
│       │   └── LogViewer.tsx
│       ├── services/
│       │   └── auditApi.ts
│       └── types.ts
│
├── lib/                         # Infraestructura compartida
│   ├── api-client.ts            # Axios config + interceptors JWT
│   ├── utils.ts                 # Funciones helper (formateo fechas, bytes)
│   └── constants.ts             # Constantes (API_URL, TOKEN_KEY, PAGE_SIZE)
│
├── store/                       # Zustand stores
│   ├── authStore.ts             # user, token, login, logout, isAdmin
│   ├── documentStore.ts         # documents, currentDocument, list, upload, delete
│   ├── certStore.ts             # certificates, list, issue, revoke
│   └── uiStore.ts               # sidebarOpen, theme, loading, toast
│
├── hooks/                       # Hooks globales
│   ├── useToast.ts              # Sistema de notificaciones
│   ├── useDebounce.ts           # Debounce para búsquedas
│   └── useLocalStorage.ts       # Wrapper para localStorage
│
├── types/                       # Tipos globales
│   └── index.ts                 # ApiResponse, PaginatedResponse, UserRole
│
├── middleware.ts                # Next.js middleware (protección de rutas)
├── tailwind.config.js           # Configuración Tailwind
├── tsconfig.json                # Configuración TypeScript
├── .env.local                   # Variables locales (NEXT_PUBLIC_API_URL)
└── package.json                 # Dependencias