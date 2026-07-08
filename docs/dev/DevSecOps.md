# DEVSECOPS PIPELINE - PLATAFORMA DE FIRMA DIGITAL

## Estructura del Pipeline

El pipeline DevSecOps se ejecuta en GitHub Actions y cubre todo el ciclo de vida: desarrollo, build, escaneo, pruebas y despliegue.

## Fases del Pipeline

### Fase 1: Seguridad en Desarrollo (Pre-commit)

Estas herramientas se ejecutan localmente antes de hacer commit.

| Herramienta | Que escanea                          | Como se ejecuta            |
| ----------- | ------------------------------------ | -------------------------- |
| ESLint      | Codigo frontend (Next.js/TypeScript) | npm run lint               |
| Bandit      | Codigo backend (Python)              | bandit -r backend/ -ll     |
| Gitleaks    | Secretos (passwords, keys, tokens)   | gitleaks detect --source . |

### Fase 2: Integracion Continua (CI - GitHub Actions)

Se ejecuta automaticamente en cada push y pull request.

| Paso | Herramienta | Que hace | Umbral de fallo |
|------|-------------|----------|-----------------|
| Checkout | actions/checkout | Clona el repositorio | - |
| Setup Node | actions/setup-node | Instala Node.js para frontend | - |
| Setup Python | actions/setup-python | Instala Python para backend | - |
| Instalar dependencias | npm ci + pip install | Instala dependencias | Si falla la instalacion |
| Lint frontend | ESLint | Verifica calidad de codigo frontend | Si hay errores |
| Lint backend | Bandit | Verifica vulnerabilidades en Python | Si hay severidad MEDIA o ALTA |
| Tipo frontend | TypeScript (tsc) | Verifica tipos TypeScript | Si hay errores de tipo |
| Pruebas unitarias | pytest (backend) + Jest (frontend) | Ejecuta pruebas | Si alguna prueba falla |
| Escaneo de contenedores | Trivy | Escanea la imagen Docker | Si hay vulnerabilidades CRITICAS o ALTAS |
| Escaneo de dependencias | OWASP Dependency Check | Verifica vulnerabilidades en librerias | Si hay CVSS > 7.0 |
### Fase 3: Despliegue (CD - Continuous Deployment)
Se ejecuta al hacer merge a la rama main.

| Paso                        | Descripcion                                         |
| --------------------------- | --------------------------------------------------- |
| Build imagen Docker         | Construye imagen del backend                        |
| Escaneo final con Trivy     | Verifica que no hay vulnerabilidades CRITICAS       |
| Push a registry             | Sube imagen a Docker Hub                            |
| Despliegue en Ubuntu Server | Ejecuta docker-compose pull && docker-compose up -d |
| Health check                | Verifica que el servicio responde en /health        |

## Archivo de Pipeline: .github/workflows/devsecops.yml

```yaml
name: DevSecOps Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  # Job 1: Seguridad en codigo frontend
  frontend-security:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout codigo
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Instalar dependencias
        working-directory: ./frontend
        run: npm ci

      - name: ESLint (analisis estatico)
        working-directory: ./frontend
        run: npm run lint

      - name: TypeScript (verificacion de tipos)
        working-directory: ./frontend
        run: npx tsc --noEmit

      - name: Verificar secretos en frontend
        run: |
          npx --yes secretlint "frontend/**/*.{ts,tsx,js,jsx}"

  # Job 2: Seguridad en codigo backend
  backend-security:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout codigo
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
          cache-dependency-path: backend/requirements.txt

      - name: Instalar dependencias
        working-directory: ./backend
        run: |
          pip install -r requirements.txt
          pip install bandit safety

      - name: Bandit (analisis estatico de seguridad)
        working-directory: ./backend
        run: bandit -r app/ -ll -f json -o bandit-report.json
        continue-on-error: false

      - name: Safety (escaneo de dependencias vulnerables)
        working-directory: ./backend
        run: safety check --full-report

      - name: Verificar secretos en backend
        run: |
          pip install trufflehog
          trufflehog filesystem --directory ./backend --no-verification

  # Job 3: Pruebas unitarias e integracion
  tests:
    runs-on: ubuntu-latest
    needs: [frontend-security, backend-security]
    steps:
      - name: Checkout codigo
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Instalar dependencias backend
        working-directory: ./backend
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio httpx

      - name: Ejecutar pruebas backend
        working-directory: ./backend
        run: |
          pytest tests/ -v --cov=app --cov-report=xml
        env:
          DATABASE_URL: sqlite+aiosqlite:///./test.db
          SECRET_KEY: test-secret-key
          AES_KEY: 32bytessecretkeyfortestingonly

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Instalar dependencias frontend
        working-directory: ./frontend
        run: npm ci

      - name: Ejecutar pruebas frontend
        working-directory: ./frontend
        run: npm test

  # Job 4: Escaneo de contenedores con Trivy
  container-scan:
    runs-on: ubuntu-latest
    needs: [tests]
    steps:
      - name: Checkout codigo
        uses: actions/checkout@v4

      - name: Construir imagen Docker del backend
        working-directory: ./backend
        run: docker build -t app-backend:test .

      - name: Construir imagen Docker del frontend
        working-directory: ./frontend
        run: docker build -t app-frontend:test .

      - name: Escanear backend con Trivy
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: app-backend:test
          format: 'sarif'
          output: 'trivy-backend.sarif'
          severity: 'CRITICAL,HIGH'

      - name: Escanear frontend con Trivy
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: app-frontend:test
          format: 'sarif'
          output: 'trivy-frontend.sarif'
          severity: 'CRITICAL,HIGH'

      - name: Subir reportes Trivy a GitHub
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: trivy-backend.sarif

