#!/bin/bash
# ============================================================================
# Script para inicializar la base de datos local (portalinmobiliario-db)
# Uso: ./init-db-local.sh
# ============================================================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🗄️ Inicializando base de datos local...${NC}"
echo ""

# Verificar que el contenedor PostgreSQL esté corriendo
if ! docker ps | grep -q "portalinmobiliario-db"; then
    echo -e "${RED}❌ ERROR: Contenedor portalinmobiliario-db no está corriendo${NC}"
    echo ""
    echo "Inicia el contenedor con:"
    echo "  docker start portalinmobiliario-db"
    echo ""
    echo "O con docker-compose:"
    echo "  docker-compose up -d"
    exit 1
fi

echo -e "${GREEN}✅ Contenedor portalinmobiliario-db detectado${NC}"
echo ""

# Verificar que .env existe
if [ ! -f .env ]; then
    echo -e "${RED}❌ ERROR: Archivo .env no encontrado${NC}"
    exit 1
fi

echo -e "${BLUE}📦 Verificando configuración...${NC}"

# Verificar que DATABASE_URL esté en .env
if ! grep -q "^DATABASE_URL=" .env; then
    echo -e "${RED}❌ ERROR: DATABASE_URL no está configurado en .env${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Configuración encontrada en .env${NC}"
echo ""

# Activar entorno virtual si existe
if [ -d "venv" ]; then
    echo -e "${BLUE}📦 Activando entorno virtual...${NC}"
    source venv/bin/activate
fi

# Ejecutar script de inicialización (Python cargará el .env automáticamente)
echo -e "${BLUE}📦 Creando tablas en PostgreSQL...${NC}"
python init_db.py

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Base de datos inicializada correctamente${NC}"
    echo ""
    echo "Tablas creadas:"
    echo "  - properties"
    echo "  - features"
    echo "  - images"
    echo "  - publishers"
    echo "  - opportunities"
    echo "  - analytics_cache"
    echo "  - scheduler_executions"
    echo "  - scheduler_state"
    echo "  - scraper_executions"
    echo "  - scraper_logs"
else
    echo ""
    echo -e "${RED}❌ Error al inicializar la base de datos${NC}"
    exit 1
fi
