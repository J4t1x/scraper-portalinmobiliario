#!/bin/bash
# ============================================================================
# Init Services Script - Portal Inmobiliario Scraper
# Verifica y prepara todos los servicios antes de iniciar la aplicación
# ============================================================================

set -e

echo "🚀 Iniciando verificación de servicios..."

# ============================================================================
# 1. WAIT FOR POSTGRESQL
# ============================================================================
wait_for_postgres() {
    echo "⏳ Esperando PostgreSQL..."
    local retries=30
    local count=0
    
    while [ $count -lt $retries ]; do
        if python3 -c "
import os, sys
try:
    from sqlalchemy import create_engine, text
    url = os.environ.get('DATABASE_URL', 'postgresql://scraper:scraper123@postgres:5432/portalinmobiliario')
    engine = create_engine(url)
    with engine.connect() as conn:
        conn.execute(text('SELECT 1'))
    print('OK')
    sys.exit(0)
except Exception as e:
    print(f'Waiting... ({e})')
    sys.exit(1)
" 2>/dev/null; then
            echo "✅ PostgreSQL está listo"
            return 0
        fi
        
        count=$((count + 1))
        echo "  Intento $count/$retries..."
        sleep 2
    done
    
    echo "❌ PostgreSQL no respondió después de $retries intentos"
    return 1
}

# ============================================================================
# 2. CREATE TABLES IF NEEDED
# ============================================================================
init_database() {
    echo "📦 Verificando tablas de base de datos..."
    python3 -c "
import os, sys
os.environ.setdefault('DATABASE_URL', 'postgresql://scraper:scraper123@postgres:5432/portalinmobiliario')

try:
    from database import setup_database, create_tables
    setup_database()
    create_tables()
    print('✅ Tablas verificadas/creadas')
except Exception as e:
    print(f'⚠️ Error creando tablas: {e}')
    sys.exit(1)
"
}

# ============================================================================
# 3. CHECK REDIS
# ============================================================================
check_redis() {
    echo "⏳ Verificando Redis..."
    local retries=10
    local count=0
    
    while [ $count -lt $retries ]; do
        if python3 -c "
import redis, os, sys
try:
    url = os.environ.get('REDIS_URL', 'redis://redis:6379')
    r = redis.from_url(url)
    r.ping()
    print('OK')
    sys.exit(0)
except Exception as e:
    print(f'Waiting... ({e})')
    sys.exit(1)
" 2>/dev/null; then
            echo "✅ Redis está listo"
            return 0
        fi
        
        count=$((count + 1))
        echo "  Intento $count/$retries..."
        sleep 2
    done
    
    echo "⚠️ Redis no está disponible (no crítico, continuando...)"
    return 0
}

# ============================================================================
# 4. CHECK OLLAMA
# ============================================================================
check_ollama() {
    echo "⏳ Verificando Ollama..."
    local retries=5
    local count=0
    
    OLLAMA_URL=${OLLAMA_URL:-http://ollama:11434}
    
    while [ $count -lt $retries ]; do
        if curl -sf "${OLLAMA_URL}/api/tags" > /dev/null 2>&1; then
            echo "✅ Ollama está listo en ${OLLAMA_URL}"
            return 0
        fi
        
        count=$((count + 1))
        echo "  Intento $count/$retries..."
        sleep 3
    done
    
    echo "⚠️ Ollama no está disponible (no crítico, el agente IA funcionará cuando se conecte)"
    return 0
}

# ============================================================================
# MAIN
# ============================================================================
echo "================================================"
echo "  Portal Inmobiliario Scraper - Init Services"
echo "================================================"

wait_for_postgres
init_database
check_redis
check_ollama

echo ""
echo "================================================"
echo "  ✅ Todos los servicios verificados"
echo "================================================"
echo ""
