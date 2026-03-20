#!/bin/bash
set -e

echo "================================================"
echo "Portal Inmobiliario Scraper - Docker Container"
echo "================================================"

# Verificar que Chrome está instalado
if ! command -v google-chrome &> /dev/null; then
    echo "ERROR: Google Chrome no está instalado"
    exit 1
fi

# Verificar que ChromeDriver está instalado
if ! command -v chromedriver &> /dev/null; then
    echo "ERROR: ChromeDriver no está instalado"
    exit 1
fi

# Mostrar versiones
echo "Chrome version: $(google-chrome --version)"
echo "ChromeDriver version: $(chromedriver --version | head -n 1)"
echo "Python version: $(python --version)"
echo "================================================"

# Activar virtual environment si existe
if [ -d "venv" ]; then
    echo "Activando virtual environment..."
    source venv/bin/activate
    echo "Virtual environment activado: $(which python)"
fi

# Verificar conexión a base de datos si DATABASE_URL está definida
if [ -n "$DATABASE_URL" ]; then
    echo "DATABASE_URL detectada, verificando conexión..."
    python -c "
import os
from urllib.parse import urlparse
try:
    url = urlparse(os.getenv('DATABASE_URL'))
    print(f'Base de datos configurada: {url.scheme}://{url.hostname}:{url.port}{url.path}')
except Exception as e:
    print(f'Error parseando DATABASE_URL: {e}')
"
fi

# Crear directorio output si no existe
mkdir -p /app/output

echo "================================================"
echo "Ejecutando comando: $@"
echo "================================================"

# Ejecutar el comando pasado como argumento
exec "$@"
