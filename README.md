# Sistema de Gestión Bibliotecaria Inteligente 
**Institución:** Fundación Universitaria UNINPAHU (2026) 
**Docente:** Elfar Didier Morantes Sánchez

# Integrantes del Equipo
* Juan Manuel Pinzón Aunta
* Iván Jair Mendoza Solano


# Descripción del Proyecto
Solución web desarrollada para automatizar el control de inventario de libros y el seguimiento de préstamos (Inspirado en la Biblioteca Luis Ángel Arango). El proyecto evoluciona desde un núcleo transaccional en **Django** hacia una arquitectura empresarial que integra **Node.js**, **IA generativa**, contenedores **Docker** y documentación con **Swagger/OpenAPI**

# Stack Tecnológico
* **Backend:** Python, Django, Django REST Framework
* **Microservicios:** Node.js, Express
* **Base de Datos:** SQLite (Desarrollo) / PostgreSQL (Producción)
* **DevOps:** Docker, Docker Compose, Render / Railway
* **Documentación:** Swagger / OpenAPI, Estándar IEEE 830 (SRS)

## Construir y ejecutar con Docker

Ejecuta estos comandos desde la raíz del repositorio. El contexto de
construcción es la raíz porque ahí está `requirements.txt`; el Dockerfile está
dentro de `biblioteca/`:

```powershell
docker build -f biblioteca/Dockerfile -t biblioteca-app .
docker run --rm -p 8000:8000 `
  -e DEBUG=true `
  -e ALLOWED_HOSTS=localhost,127.0.0.1 `
  -e DB_PATH=/data/db.sqlite3 `
  -v biblioteca_data:/data `
  biblioteca-app
```

La aplicación queda disponible en `http://localhost:8000/`. El volumen
`biblioteca_data` conserva SQLite al recrear el contenedor. No uses SQLite
como base de datos de producción si la plataforma no ofrece almacenamiento
persistente.

## Variables para producción

La configuración [render.yaml](./render.yaml) define un Blueprint de Render
con servicio Docker y base PostgreSQL. Desde el dashboard, conecta este
repositorio, selecciona **Blueprint** y aplica `render.yaml`.

Render genera `DJANGO_SECRET_KEY` y proporciona `DATABASE_URL` desde la base
PostgreSQL. La configuración de Django interpreta esta URL directamente.
No guardes claves ni credenciales en Git.

- `DEBUG=false`
- `DJANGO_SECRET_KEY`: la genera Render desde el Blueprint.
- `DATABASE_URL`: URL PostgreSQL interna proporcionada por Render.
- `RENDER_EXTERNAL_HOSTNAME`: Render la define al crear el servicio.

En Render, `RENDER_EXTERNAL_HOSTNAME` se agrega automáticamente a
`ALLOWED_HOSTS` y `CSRF_TRUSTED_ORIGINS`. La configuración de producción
redirige a HTTPS; la plataforma debe terminar TLS y enviar
`X-Forwarded-Proto`.

El contenedor aplica migraciones, configura los roles, ejecuta `collectstatic`
y levanta Gunicorn al iniciar.

El Blueprint usa planes gratuitos para la demo. Render indica que su base
PostgreSQL gratuita vence a los 30 días y que el disco local de los servicios
gratuitos es efímero; no lo uses como almacenamiento permanente.
