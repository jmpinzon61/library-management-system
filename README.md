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

## Ejecutar con Docker Compose

Desde la raíz, copia `.env.example` a `.env` y reemplaza los valores de
`DJANGO_SECRET_KEY` y `NODE_SERVICE_TOKEN` por valores largos de desarrollo.
Agrega una clave de Google AI Studio a `GEMINI_API_KEY` para probar las
funciones de IA. No subas `.env` a Git.

```powershell
docker compose up --build
```

Compose levanta PostgreSQL, Django y el microservicio Node.js. Django queda
disponible en `http://localhost:8000/`; Swagger UI público para la red local
queda en `http://localhost:3000/docs`. El volumen `biblioteca_db` conserva la
base local al detener los contenedores.

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

## Entrega 3: microservicio, Swagger y asistencia con IA

El microservicio Node.js está en `microservicios/alertas`. Su documentación
OpenAPI/Swagger se sirve públicamente en `/docs` y el esquema JSON en
`/openapi.json`. La API contiene endpoints para sincronizar/listar alertas
internas de préstamos vencidos y para generar recomendaciones y resúmenes con
Gemini. Los endpoints internos requieren `NODE_SERVICE_TOKEN`; no publiques
ese token ni la clave `GEMINI_API_KEY`.

Django configura la comunicación con `NODE_SERVICE_URL` y
`NODE_SERVICE_TOKEN`. El botón de procesamiento en la pantalla de préstamos
vencidos sincroniza las alertas; Bibliotecarios y Administradores pueden
consultarlas. La recomendación bibliográfica y el resumen del libro se
solicitan desde la aplicación autenticada.

### Despliegue en Render

El Blueprint agrega el servicio público `biblioteca-alertas-api`; Swagger
estará en `https://biblioteca-alertas-api.onrender.com/docs`. Al aplicar los
cambios de `render.yaml`, configura el mismo `NODE_SERVICE_TOKEN` en los
servicios Django y Node, y configura `GEMINI_API_KEY` solo en Node. Mantén
estas variables en el dashboard de Render, no en Git.

Genera un token aleatorio de al menos 32 caracteres y coloca exactamente el
mismo valor en ambos servicios. Las alertas internas se muestran a usuarios
con permisos de Bibliotecario o Administrador; no se envían por correo.
