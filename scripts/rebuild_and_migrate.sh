#!/bin/bash
# Script para reconstruir imagen y ejecutar migración
# Fecha: 12 Abril 2026

set -e

echo "=========================================="
echo "  Rebuild & Migrate"
echo "=========================================="
echo ""

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}📋 Paso 1: Detener contenedores${NC}"
docker-compose -f docker-compose.v2.yml down

echo ""
echo -e "${YELLOW}📋 Paso 2: Reconstruir imagen del scraper${NC}"
echo "Esto incluirá el nuevo alembic.ini y las migraciones..."
docker-compose -f docker-compose.v2.yml build scraper

echo ""
echo -e "${YELLOW}📋 Paso 3: Levantar PostgreSQL${NC}"
docker-compose -f docker-compose.v2.yml up -d postgres

echo ""
echo -e "${YELLOW}⏳ Esperando a que PostgreSQL esté listo...${NC}"
sleep 10

echo ""
echo -e "${YELLOW}📋 Paso 4: Ejecutar migración Alembic${NC}"
docker-compose -f docker-compose.v2.yml run --rm scraper alembic upgrade head

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Migración completada exitosamente${NC}"
else
    echo -e "${RED}❌ Error en la migración${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}📋 Paso 5: Verificar tablas creadas${NC}"
docker-compose -f docker-compose.v2.yml exec postgres psql -U scraper -d portalinmobiliario -c "\dt"

echo ""
echo -e "${GREEN}=========================================="
echo "  ✅ Rebuild & Migración Completada"
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
