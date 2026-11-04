# Usar imagen oficial de Python ligera
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Directorio de trabajo dentro del contenedor
WORKDIR /app

# Instalar dependencias del sistema necesarias si usas PostgreSQL o compilación
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar los requerimientos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el código del proyecto al contenedor
COPY biblioteca/ .

# Exponer el puerto 8000 para la app web
EXPOSE 8000

# Comando por defecto para ejecutar el servidor de Django
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py setup_roles && python manage.py collectstatic --noinput && exec gunicorn biblioteca.wsgi:application --bind 0.0.0.0:${PORT:-8000}"]