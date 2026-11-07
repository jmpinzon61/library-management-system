FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia los requirements desde el contexto actual
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo el contenido de la carpeta biblioteca al contenedor
COPY . .

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py setup_roles && python manage.py collectstatic --noinput && exec gunicorn biblioteca.wsgi:application --timeout 60 --bind 0.0.0.0:${PORT:-8000}"]