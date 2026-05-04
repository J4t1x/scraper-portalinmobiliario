#!/bin/bash
# Script para migrar el dashboard a PostgreSQL
# Fecha: 12 Abril 2026

set -e

echo "=========================================="
echo "  Migración Dashboard a PostgreSQL"
echo "=========================================="
echo ""

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Verificar que docker-compose esté disponible
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ docker-compose no está instalado${NC}"
    exit 1
fi

echo -e "${YELLOW}📋 Paso 1: Verificar servicios${NC}"
echo "Levantando PostgreSQL..."
docker-compose -f docker-compose.v2.yml up -d postgres

echo ""
echo -e "${YELLOW}⏳ Esperando a que PostgreSQL esté listo...${NC}"
sleep 5

echo ""
echo -e "${YELLOW}📋 Paso 2: Verificar alembic.ini${NC}"
if [ ! -f "alembic.ini" ]; then
    echo -e "${RED}❌ alembic.ini no encontrado${NC}"
    exit 1
fi
echo -e "${GREEN}✅ alembic.ini encontrado${NC}"

echo ""
echo -e "${YELLOW}📋 Paso 3: Ejecutar migración Alembic${NC}"
docker-compose -f docker-compose.v2.yml run --rm scraper alembic upgrade head

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Migración completada exitosamente${NC}"
else
    echo -e "${RED}❌ Error en la migración${NC}"
    echo ""
    echo "Intentando mostrar el estado actual de Alembic:"
    docker-compose -f docker-compose.v2.yml run --rm scraper alembic current
    exit 1
fi

echo ""
echo -e "${YELLOW}📋 Paso 4: Verificar tablas creadas${NC}"
docker-compose -f docker-compose.v2.yml exec postgres psql -U scraper -d portalinmobiliario -c "\dt"

echo ""
echo -e "${GREEN}=========================================="
echo "  ✅ Migración Completada"
echo "==========================================${NC}"
echo ""
echo "Próximos pasos:"
echo "1. Levantar dashboard:"
echo "   docker-compose -f docker-compose.v2.yml --profile dashboard up"
echo ""
echo "2. Ejecutar scraping con tracking:"
echo "   docker-compose -f docker-compose.v2.yml run --rm scraper \\"
echo "     python main.py --operacion venta --tipo departamento \\"
echo "     --max-pages 5 --persist-to-db"
echo ""
echo "3. Ver historial de ejecuciones:"
echo "   curl http://localhost:4421/api/scraper/executions"
echo ""
