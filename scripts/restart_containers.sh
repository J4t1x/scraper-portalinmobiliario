#!/bin/bash
# Script para reiniciar contenedores con configuración corregida
# Fecha: 12 Abril 2026

set -e

echo "=========================================="
echo "  Reiniciar Contenedores"
echo "=========================================="
echo ""

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}📋 Paso 1: Detener contenedores actuales${NC}"
docker-compose -f docker-compose.v2.yml down

echo ""
echo -e "${YELLOW}📋 Paso 2: Levantar PostgreSQL${NC}"
docker-compose -f docker-compose.v2.yml up -d postgres

echo ""
echo -e "${YELLOW}⏳ Esperando a que PostgreSQL esté listo...${NC}"
sleep 10

echo ""
echo -e "${YELLOW}📋 Paso 3: Verificar estado de PostgreSQL${NC}"
docker-compose -f docker-compose.v2.yml ps postgres

echo ""
echo -e "${YELLOW}📋 Paso 4: Verificar healthcheck${NC}"
docker inspect portalinmobiliario-db --format='{{json .State.Health}}' | jq

echo ""
echo -e "${GREEN}=========================================="
echo "  ✅ PostgreSQL Reiniciado"
echo "==========================================${NC}"
echo ""
echo "Próximos pasos:"
echo "1. Ejecutar migración:"
echo "   ./scripts/migrate_to_postgresql.sh"
echo ""
echo "2. Levantar dashboard:"
echo "   docker-compose -f docker-compose.v2.yml --profile dashboard up"
echo ""
