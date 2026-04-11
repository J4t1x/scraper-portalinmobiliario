#!/bin/bash
# Script de deployment automatizado para contenedor MVP
# Autor: AI Dev Engine (Cascade)
# Fecha: 2026-04-11

set -e  # Salir si hay error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Variables
IMAGE_NAME="portalinmobiliario:mvp"
CONTAINER_NAME="scraper-mvp"
FLASK_PORT=5000
OLLAMA_PORT=11434

echo -e "${PURPLE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${PURPLE}║                                                            ║${NC}"
echo -e "${PURPLE}║         🚀 Portal Inmobiliario MVP Deployment 🚀          ║${NC}"
echo -e "${PURPLE}║                                                            ║${NC}"
echo -e "${PURPLE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Función para mostrar spinner
spinner() {
    local pid=$1
    local delay=0.1
    local spinstr='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
    while [ "$(ps a | awk '{print $1}' | grep $pid)" ]; do
        local temp=${spinstr#?}
        printf " [%c]  " "$spinstr"
        local spinstr=$temp${spinstr%"$temp"}
        sleep $delay
        printf "\b\b\b\b\b\b"
    done
    printf "    \b\b\b\b"
}

# Paso 1: Detener y eliminar contenedor existente
echo -e "${YELLOW}📦 Paso 1/5: Limpiando contenedores anteriores...${NC}"
if docker ps -a | grep -q $CONTAINER_NAME; then
    echo "   → Deteniendo contenedor existente..."
    docker stop $CONTAINER_NAME 2>/dev/null || true
    echo "   → Eliminando contenedor existente..."
    docker rm $CONTAINER_NAME 2>/dev/null || true
    echo -e "${GREEN}   ✓ Contenedor anterior eliminado${NC}"
else
    echo -e "${GREEN}   ✓ No hay contenedores anteriores${NC}"
fi
echo ""

# Paso 2: Build de la imagen
echo -e "${YELLOW}🔨 Paso 2/5: Construyendo imagen Docker...${NC}"
echo "   → Esto puede tomar 10-15 minutos en el primer build"
echo "   → Descargando: PostgreSQL + Chrome + Ollama + Python deps"
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Build con output filtrado en tiempo real
docker build -f Dockerfile.mvp -t $IMAGE_NAME . 2>&1 | while IFS= read -r line; do
    # Mostrar pasos importantes
    if echo "$line" | grep -qE "^\[|Step |=> \[|DONE|ERROR|CACHED"; then
        # Colorear según tipo de línea
        if echo "$line" | grep -q "ERROR"; then
            echo -e "${RED}$line${NC}"
        elif echo "$line" | grep -q "DONE"; then
            echo -e "${GREEN}$line${NC}"
        elif echo "$line" | grep -q "CACHED"; then
            echo -e "${BLUE}$line${NC}"
        elif echo "$line" | grep -q "Step "; then
            echo -e "${YELLOW}$line${NC}"
        else
            echo "$line"
        fi
    fi
done

BUILD_EXIT_CODE=${PIPESTATUS[0]}

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if [ $BUILD_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}   ✓ Imagen construida exitosamente${NC}"
else
    echo -e "${RED}   ✗ Error en el build (exit code: $BUILD_EXIT_CODE)${NC}"
    exit 1
fi
echo ""

# Paso 3: Crear volumen para modelos de Ollama
echo -e "${YELLOW}💾 Paso 3/5: Creando volumen para modelos Ollama...${NC}"
if ! docker volume ls | grep -q ollama-models; then
    docker volume create ollama-models
    echo -e "${GREEN}   ✓ Volumen creado${NC}"
else
    echo -e "${GREEN}   ✓ Volumen ya existe${NC}"
fi
echo ""

# Paso 4: Ejecutar contenedor
echo -e "${YELLOW}🚀 Paso 4/5: Iniciando contenedor MVP...${NC}"
docker run -d \
  --name $CONTAINER_NAME \
  -p $FLASK_PORT:5000 \
  -p $OLLAMA_PORT:11434 \
  -v $(pwd)/output:/app/output \
  -v ollama-models:/app/.ollama/models \
  $IMAGE_NAME

if [ $? -eq 0 ]; then
    echo -e "${GREEN}   ✓ Contenedor iniciado${NC}"
else
    echo -e "${RED}   ✗ Error al iniciar contenedor${NC}"
    exit 1
fi
echo ""

# Paso 5: Verificar servicios
echo -e "${YELLOW}🔍 Paso 5/5: Verificando servicios...${NC}"
echo "   → Esperando 15 segundos para que los servicios inicien..."
sleep 15

# Verificar Supervisor
echo -n "   → Supervisor: "
if docker exec $CONTAINER_NAME supervisorctl status > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
fi

# Verificar PostgreSQL
echo -n "   → PostgreSQL: "
if docker exec $CONTAINER_NAME pg_isready -U scraper -d portalinmobiliario > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${YELLOW}⏳ (iniciando...)${NC}"
fi

# Verificar Ollama
echo -n "   → Ollama: "
sleep 5  # Dar más tiempo a Ollama
if curl -s http://localhost:$OLLAMA_PORT/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${YELLOW}⏳ (iniciando...)${NC}"
fi

# Verificar Flask
echo -n "   → Flask: "
if curl -s http://localhost:$FLASK_PORT/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${YELLOW}⏳ (iniciando...)${NC}"
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                            ║${NC}"
echo -e "${GREEN}║              ✅ Deployment Completado ✅                   ║${NC}"
echo -e "${GREEN}║                                                            ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Información de acceso
echo -e "${BLUE}📍 URLs de Acceso:${NC}"
echo -e "   • Dashboard: ${GREEN}http://localhost:$FLASK_PORT${NC}"
echo -e "   • Ollama API: ${GREEN}http://localhost:$OLLAMA_PORT${NC}"
echo -e "   • Health Check: ${GREEN}http://localhost:$FLASK_PORT/health${NC}"
echo ""

echo -e "${BLUE}🔧 Comandos Útiles:${NC}"
echo -e "   • Ver logs:           ${YELLOW}docker logs -f $CONTAINER_NAME${NC}"
echo -e "   • Estado servicios:   ${YELLOW}docker exec $CONTAINER_NAME supervisorctl status${NC}"
echo -e "   • Verificar servicios: ${YELLOW}./scripts/check-services.sh${NC}"
echo -e "   • Detener contenedor: ${YELLOW}docker stop $CONTAINER_NAME${NC}"
echo -e "   • Eliminar contenedor: ${YELLOW}docker rm $CONTAINER_NAME${NC}"
echo ""

echo -e "${BLUE}📊 Próximos Pasos:${NC}"
echo -e "   1. Acceder al dashboard en http://localhost:$FLASK_PORT"
echo -e "   2. Login con credenciales de admin"
echo -e "   3. Navegar a ${PURPLE}AI Analytics${NC} para probar el agente IA"
echo -e "   4. Ejecutar scraping desde el panel de Scraper"
echo -e "   5. Ver métricas en tiempo real"
echo ""

echo -e "${PURPLE}🎉 ¡Listo para usar! 🎉${NC}"
echo ""

# Mostrar logs en tiempo real (opcional)
read -p "¿Deseas ver los logs en tiempo real? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}Mostrando logs (Ctrl+C para salir)...${NC}"
    echo ""
    docker logs -f $CONTAINER_NAME
fi
