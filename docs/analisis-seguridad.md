# Informe de Analisis de Seguridad - SecureSign

## Datos del Analisis

| Campo | Valor |
|-------|-------|
| **Fecha** | Julio 2026 |
| **Plataforma** | SecureSign - Document Signing Platform |
| **Kali Linux IP** | 192.168.100.10 |
| **Ubuntu Server IP** | 192.168.56.101 |
| **Puertos Analizados** | 3000, 5432, 8000, 9000, 9001 |

---

## 1. Entorno de Despliegue

La plataforma SecureSign fue desplegada en un Ubuntu Server utilizando Docker Compose:

- **Frontend**: Next.js (puerto 3000)
- **Backend**: FastAPI (puerto 8000)
- **Base de datos**: PostgreSQL 16 (puerto 5432)
- **Almacenamiento**: MinIO (puertos 9000, 9001)

![Aplicacion ejecutandose en Ubuntu Server](img/aplicacion%20ejecutandose%20en%20ubuntu%20server.png)

---

## 2. Escaneo de Puertos

Se realizo un escaneo de puertos con Nmap para identificar servicios expuestos.

**Comando ejecutado:**
```bash
nmap -T4 -sV -p 3000,5432,8000,9000,9001 192.168.56.101
```

**Resultado:**
- Puerto 3000: Frontend Next.js
- Puerto 5432: PostgreSQL
- Puerto 8000: Backend API FastAPI
- Puerto 9000: MinIO API
- Puerto 9001: MinIO Console

**Hallazgos:**
- Todos los servicios estan activos y accesibles desde la red
- PostgreSQL (5432) y MinIO (9000, 9001) estan expuestos intencionalmente para demostrar el almacenamiento de datos en la presentacion

![Escaneo de Puertos](img/analisis%20de%20seguridad/1%20escaneo%20de%20puertos.png)

---

## 3. Analisis de Headers de Seguridad

Se verificaron los headers de seguridad HTTP en los puertos 3000 y 8000.

**Comando ejecutado:**
```bash
curl -sI http://192.168.56.101:3000 | grep -i "x-frame\|x-content\|strict-transport\|x-xss\|content-security\|server"
curl -sI http://192.168.56.101:8000 | grep -i "x-frame\|x-content\|strict-transport\|x-xss\|content-security\|server"
```

**Resultado:**
- Se identifico el servidor utilizado (Next.js/Uvicorn)
- Header `X-Content-Type-Options: nosniff` presente
- Header `X-Frame-Options` presente
- Headers de seguridad implementados correctamente

**Riesgo:** Bajo - Los headers de seguridad estan configurados correctamente

![Headers de Seguridad](img/analisis%20de%20seguridad/2%20headers%20de%20seguridad.png)

---

## 4. Verificacion de CORS

Se verifico la configuracion de Cross-Origin Resource Sharing.

**Comando ejecutado:**
```bash
curl -s -X OPTIONS -H "Origin: http://evil.com" -H "Access-Control-Request-Method: POST" -I http://192.168.56.101:8000/api/v1/auth/login
```

**Resultado:**
- El servidor rechaza solicitudes de origen no permitido
- CORS configurado correctamente para evitar accesos no autorizados

**Riesgo:** Bajo - La configuracion CORS es restrictiva

![Verificacion CORS](img/analisis%20de%20seguridad/3%20verifica%20cors.png)

---

## 5. Verificacion de HTTP Methods

Se verificaron los metodos HTTP permitidos en el endpoint de login.

**Comando ejecutado:**
```bash
for method in GET POST PUT DELETE OPTIONS TRACE; do
  echo -n "$method: "; curl -s -o /dev/null -w "%{http_code}" -X $method http://192.168.56.101:8000/api/v1/auth/login; echo
done
```

**Resultado:**
- POST: 422 (Metodo permitido, requiere datos)
- GET: 405 (Metodo no permitido)
- PUT/DELETE: 405 (Metodos no permitidos)
- OPTIONS: 200 (Permitido para CORS)
- TRACE: No permitido

**Riesgo:** Bajo - Solo se permiten metodos necesarios

![HTTP Methods](img/analisis%20de%20seguridad/4%20verificar%20http%20methods.png)

---

## 6. Verificacion de Archivos Sensibles

Se verifico el acceso a archivos y directorios sensibles.

**Comando ejecutado:**
```bash
for path in /.env /.git/config /docker-compose.yml /Dockerfile /package.json /wp-admin /phpmyadmin /.htaccess /server-status; do
  echo -n "$path: "; curl -s -o /dev/null -w "%{http_code}" http://192.168.56.101:3000$path; echo
done
```

**Resultado:**
- /.env: 403 (Acceso denegado)
- /.git/config: 404 (No encontrado)
- /docker-compose.yml: 404 (No encontrado)
- /Dockerfile: 404 (No encontrado)
- Todos los demas: 404 (No encontrados)

**Riesgo:** Bajo - Los archivos sensibles no estan expuestos

![Archivos Sensibles](img/analisis%20de%20seguridad/5%20verificar%20archivos%20sensibles.png)

---

## 7. Verificacion de Exposicion de Servicios

Se verifico la exposicion de servicios auxiliares.

**Comando ejecutado:**
```bash
curl -s http://192.168.56.101:9001 -o /dev/null -w "MinIO Console: %{http_code}\n"
curl -s http://192.168.56.101:8000/docs -o /dev/null -w "FastAPI Docs: %{http_code}\n"
curl -s http://192.168.56.101:8000/api/v1/openapi.json -o /dev/null -w "OpenAPI Spec: %{http_code}\n"
```

**Resultado:**
- MinIO Console (9001): 200 (Accesible)
- FastAPI Docs (8000/docs): 200 (Accesible)
- OpenAPI Spec: 200 (Accesible)

**Nota:** MinIO Console y FastAPI Docs estan expuestos intencionalmente para fines de demostracion y documentacion de la arquitectura del sistema.

![Exposicion de Servicios](img/analisis%20de%20seguridad/6%20verificacion%20de%20exposicion%20de%20servicios.png)

---

## 8. Test de Autenticacion

Se verifico el comportamiento de autenticacion sin token y con token invalido.

**Comando ejecutado:**
```bash
# Sin token
curl -s http://192.168.56.101:8000/api/v1/documents/ -w "\nHTTP %{http_code}\n"

# Token invalido
curl -s -H "Authorization: Bearer invalidtoken123" http://192.168.56.101:8000/api/v1/documents/ -w "\nHTTP %{http_code}\n"
```

**Resultado:**
- Sin token: 401 (No autorizado)
- Token invalido: 401 (No autorizado)

**Riesgo:** Bajo - La autenticacion funciona correctamente, rechaza accesos no autorizados

![Test de Autenticacion](img/analisis%20de%20seguridad/7%20test%20de%20autenticacion.png)

---

## 9. Test de SQL Injection

Se verifico la resistencia a inyeccion SQL en el endpoint de login.

**Comando ejecutado:**
```bash
curl -s "http://192.168.56.101:8000/api/v1/auth/login" -X POST -H "Content-Type: application/json" -d '{"email":"admin@admin.com","password":"'"'"'||'"'"'1"}'
```

**Resultado:**
- La aplicacion rechaza el payload de inyeccion SQL
- No se produce error de base de datos ni acceso no autorizado

**Riesgo:** Bajo - La aplicacion es resistente a SQL Injection (usa ORM con consultas parametrizadas)

![SQL Injection](img/analisis%20de%20seguridad/8%20test%20SQL%20Injection.png)

---

## 10. Verificacion de Cookies Seguras

Se verifico la configuracion de cookies en la respuesta de autenticacion.

**Comando ejecutado:**
```bash
curl -s -v -X POST http://192.168.56.101:8000/api/v1/auth/login -H "Content-Type: application/json" -d '{"email":"admin@admin.com","password":"Admin123!"}' 2>&1 | grep -i "set-cookie"
```

**Resultado:**
- Cookie configurada con `HttpOnly`
- Cookie configurada con `Secure` (depende de HTTPS)
- Cookie configurada con `SameSite`

**Riesgo:** Bajo - Las cookies estan configuradas con las banderas de seguridad apropiadas

![Cookies Seguras](img/analisis%20de%20seguridad/9%20verificar%20cookies%20seguras.png)

---

## 11. Test de Fuerza Bruta en Login

Se realizo un prueba de fuerza bruta con credenciales comunes.

**Comando ejecutado:**
```bash
hydra -l admin@admin.com -P <(echo -e "admin\n123456\npassword\nAdmin123!\nadmin123") 192.168.56.101 http-post-form "/api/v1/auth/login:email=^USER^&password=^PASS^:detail"
```

**Resultado:**
- La prueba mostro que no hay proteccion contra fuerza bruta (rate limiting)
- Se puede intentar multiples veces sin bloqueo

**Riesgo:** Alto - No hay mecanismo de bloqueo por intentos fallidos

![Fuerza Bruta](img/analisis%20de%20seguridad/10%20fuerza%20bruta%20en%20el%20login.png)

---

## Resumen de Hallazgos

| # | Hallazgo | Riesgo | Estado |
|---|----------|--------|--------|
| 1 | PostgreSQL y MinIO expuestos (intencional para demostracion) | Bajo | Verificado |
| 2 | Headers de seguridad HTTP configurados | Bajo | Verificado |
| 3 | Documentacion API expuesta (intencional para demostracion) | Bajo | Verificado |
| 4 | MinIO Console expuesto (intencional para demostracion) | Bajo | Verificado |
| 5 | Sin rate limiting en login | Alto | Detectado |
| 6 | CORS configurado correctamente | Bajo | Verificado |
| 7 | HTTP Methods restringidos | Bajo | Verificado |
| 8 | Archivos sensibles protegidos | Bajo | Verificado |
| 9 | Autenticacion funcional | Bajo | Verificado |
| 10 | SQL Injection resistente | Bajo | Verificado |
| 11 | Cookies seguras | Bajo | Verificado |

---

## Recomendaciones

### Prioridad Alta
1. **Implementar rate limiting** en endpoints de autenticacion

### Prioridad Media
2. **Configurar logging** de intentos de autenticacion fallidos
3. **Implementar bloqueo temporal** de cuentas tras multiples intentos fallidos

### Nota
- PostgreSQL, MinIO y FastAPI Docs estan expuestos intencionalmente para fines de demostracion academica, permitiendo visualizar la arquitectura y el flujo de datos del sistema.

---

## Conclusion

El analisis de seguridad de la plataforma SecureSign identifico **1 hallazgo de riesgo alto** (falta de rate limiting) y **10 controles de seguridad verificados correctamente**. Los servicios de PostgreSQL, MinIO y FastAPI Docs estan expuestos intencionalmente para fines de demostracion academica, permitiendo visualizar la arquitectura del sistema. Se recomienda implementar rate limiting para mejorar la seguridad en entorno de produccion.
