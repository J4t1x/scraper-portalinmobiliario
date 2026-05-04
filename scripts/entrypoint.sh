#!/bin/bash
set -e

echo "================================================"
echo "Portal Inmobiliario Scraper - Docker Container"
echo "================================================"

# Detectar Chrome o Chromium
CHROME_CMD=""
if command -v chromium &> /dev/null; then
    CHROME_CMD="chromium"
elif command -v chromium-browser &> /dev/null; then
    CHROME_CMD="chromium-browser"
elif command -v google-chrome &> /dev/null; then
    CHROME_CMD="google-chrome"
elif command -v google-chrome-stable &> /dev/null; then
    CHROME_CMD="google-chrome-stable"
fi

if [ -z "$CHROME_CMD" ]; then
    echo "⚠️  ADVERTENCIA: No se encontró Chrome/Chromium instalado (scraping no disponible)"
else
    echo "✅ Browser: $($CHROME_CMD --version 2>/dev/null || echo 'N/A')"
fi

# Verificar que ChromeDriver está instalado
if command -v chromedriver &> /dev/null; then
    echo "✅ ChromeDriver: $(chromedriver --version 2>/dev/null | head -n 1 || echo 'N/A')"
else
    echo "⚠️  ADVERTENCIA: ChromeDriver no está instalado"
fi

echo "✅ Python: $(python --version)"
echo "================================================"

# Activar virtual environment si existe
if [ -d "venv" ]; then
    echo "Activando virtual environment..."
    source venv/bin/activate
    echo "Virtual environment activado: $(which python)"
fi

# ============================================================================
# WAIT FOR POSTGRESQL (with retries)
# ============================================================================
if [ -n "$DATABASE_URL" ]; then
    echo "⏳ Esperando PostgreSQL..."
    RETRIES=30
    COUNT=0
    
    while [ $COUNT -lt $RETRIES ]; do
        if python -c "
import os, sys
try:
    from sqlalchemy import create_engine, text
    engine = create_engine(os.environ['DATABASE_URL'])
    with engine.connect() as conn:
        conn.execute(text('SELECT 1'))
    sys.exit(0)
except:
    sys.exit(1)
" 2>/dev/null; then
            echo "✅ PostgreSQL conectado"
            break
        fi
        
        COUNT=$((COUNT + 1))
        echo "  Intento $COUNT/$RETRIES..."
        sleep 2
    done
    
    if [ $COUNT -eq $RETRIES ]; then
        echo "❌ No se pudo conectar a PostgreSQL después de $RETRIES intentos"
        echo "   DATABASE_URL: $(echo $DATABASE_URL | sed 's/:[^@]*@/:***@/')"
    fi
fi

# ============================================================================
# CREATE TABLES IF NEEDED
# ============================================================================
if [ -n "$DATABASE_URL" ]; then
    echo "📦 Verificando tablas de base de datos..."
    python -c "
try:
    from database import setup_database, create_tables
    setup_database()
    create_tables()
    print('✅ Tablas verificadas/creadas')
except Exception as e:
    print(f'⚠️  Error verificando tablas: {e}')
" 2>/dev/null || true
fi

# Crear directorio output si no existe
mkdir -p /app/output /app/logs

echo "================================================"
echo "Ejecutando comando: $@"
echo "================================================"

# Ejecutar el comando pasado como argumento
exec "$@"
