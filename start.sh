#!/bin/bash
# ============================================================================
# Script de Inicio Rápido - Portal Inmobiliario Scraper
# Versión: 2.0 Optimizado
# Uso: ./start.sh [core|dashboard|ai]
# ============================================================================

set -e

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuración
IMAGE_NAME="portalinmobiliario:optimized"
CONTAINER_NAME="scraper-optimized"
DOCKERFILE="Dockerfile.optimized"

# ============================================================================
# Funciones
# ============================================================================

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

show_menu() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  🚀 Portal Inmobiliario Scraper - Optimizado v2.0"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Selecciona el modo de ejecución:"
    echo ""
    echo "  1) CORE      - Solo scraping (1.2 GB RAM)"
    echo "  2) DASHBOARD - Scraping + Web UI (2.0 GB RAM)"
    echo "  3) AI        - Scraping + Dashboard + IA (3.5 GB RAM)"
    echo "  4) Salir"
    echo ""
    echo -n "Opción [1-4]: "
}

# ============================================================================
# Verificaciones
# ============================================================================

check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker no está instalado"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker daemon no está corriendo"
        exit 1
    fi
}

# ============================================================================
# Limpieza
# ============================================================================

cleanup() {
    log_info "Deteniendo contenedor anterior si existe..."
    docker stop $CONTAINER_NAME 2>/dev/null || true
    docker rm $CONTAINER_NAME 2>/dev/null || true
}

# ============================================================================
# Build
# ============================================================================

build_if_needed() {
    if ! docker images | grep -q "$IMAGE_NAME"; then
        log_info "Imagen no encontrada. Building..."
        echo ""
        
        export DOCKER_BUILDKIT=1
        
        docker build \
            --file $DOCKERFILE \
            --tag $IMAGE_NAME \
            --progress=plain \
            . 2>&1 | grep -E "Step|RUN|COPY|FROM|DONE|ERROR|=>" || true
        
        if [ ${PIPESTATUS[0]} -eq 0 ]; then
            log_success "Build completado"
        else
            log_error "Error en el build"
            exit 1
        fi
    else
        log_success "Imagen ya existe"
    fi
}

# ============================================================================
# Start Container
# ============================================================================

start_core() {
    log_info "Iniciando modo CORE (solo scraping)..."
    
    docker run -d \
        --name $CONTAINER_NAME \
        --env ENABLE_AI=false \
        --env ENABLE_DASHBOARD=false \
        --memory=1.5g \
        --cpus=1.5 \
        --restart=unless-stopped \
        -v $(pwd)/output:/app/output \
        -v $(pwd)/logs:/var/log \
        $IMAGE_NAME
    
    log_success "Contenedor iniciado en modo CORE"
    log_info "RAM asignada: 1.5 GB"
}

start_dashboard() {
    log_info "Iniciando modo DASHBOARD (scraping + web UI)..."
    
    docker run -d \
        --name $CONTAINER_NAME \
        --env ENABLE_AI=false \
        --env ENABLE_DASHBOARD=true \
        --memory=2g \
        --cpus=2 \
        --restart=unless-stopped \
        -p 5000:5000 \
        -v $(pwd)/output:/app/output \
        -v $(pwd)/logs:/var/log \
        $IMAGE_NAME
    
    log_success "Contenedor iniciado en modo DASHBOARD"
    log_info "RAM asignada: 2.0 GB"
    log_info "Dashboard: http://localhost:5000"
}

start_ai() {
    log_info "Iniciando modo AI (scraping + dashboard + IA)..."
    
    docker run -d \
        --name $CONTAINER_NAME \
        --env ENABLE_AI=true \
        --env ENABLE_DASHBOARD=true \
        --memory=3.5g \
        --cpus=3 \
        --restart=unless-stopped \
        -p 5000:5000 \
        -p 11434:11434 \
        -v $(pwd)/output:/app/output \
        -v $(pwd)/logs:/var/log \
        $IMAGE_NAME
    
    log_success "Contenedor iniciado en modo AI"
    log_info "RAM asignada: 3.5 GB"
    log_info "Dashboard: http://localhost:5000"
    log_info "Ollama API: http://localhost:11434"
}

# ============================================================================
# Wait for Health
# ============================================================================

wait_healthy() {
    log_info "Esperando que el contenedor esté saludable..."
    
    for i in {1..30}; do
        if docker inspect --format='{{.State.Health.Status}}' $CONTAINER_NAME 2>/dev/null | grep -q "healthy"; then
            log_success "Contenedor saludable"
            return 0
        fi
        echo -n "."
        sleep 2
    done
    
    echo ""
    log_warning "Timeout esperando health check"
}

# ============================================================================
# Show Info
# ============================================================================

show_info() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  ✨ Contenedor iniciado exitosamente"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    # Mostrar estadísticas
    docker stats $CONTAINER_NAME --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"
    
    echo ""
    log_info "Comandos útiles:"
    echo ""
    echo "  Ver logs en tiempo real:"
    echo "    docker logs -f $CONTAINER_NAME"
    echo ""
    echo "  Ver estadísticas:"
    echo "    docker stats $CONTAINER_NAME"
    echo ""
    echo "  Entrar al contenedor:"
    echo "    docker exec -it $CONTAINER_NAME /bin/bash"
    echo ""
    echo "  Ver servicios activos:"
    echo "    docker exec -it $CONTAINER_NAME supervisorctl status"
    echo ""
    echo "  Detener contenedor:"
    echo "    docker stop $CONTAINER_NAME"
    echo ""
    echo "  Ver logs de servicios:"
    echo "    docker exec -it $CONTAINER_NAME tail -f /var/log/flask.log"
    echo "    docker exec -it $CONTAINER_NAME tail -f /var/log/postgresql.log"
    echo ""
}

# ============================================================================
# Main
# ============================================================================

main() {
    # Verificar Docker
    check_docker
    
    # Limpiar contenedor anterior
    cleanup
    
    # Build si es necesario
    build_if_needed
    
    # Determinar modo
    MODE=${1:-""}
    
    if [ -z "$MODE" ]; then
        # Modo interactivo
        show_menu
        read -r choice
        
        case $choice in
            1)
                MODE="core"
                ;;
            2)
                MODE="dashboard"
                ;;
            3)
                MODE="ai"
                ;;
            4)
                log_info "Saliendo..."
                exit 0
                ;;
            *)
                log_error "Opción inválida"
                exit 1
                ;;
        esac
    fi
    
    # Iniciar según modo
    echo ""
    case $MODE in
        core)
            start_core
            ;;
        dashboard)
            start_dashboard
            ;;
        ai)
            start_ai
            ;;
        *)
            log_error "Modo inválido: $MODE"
            log_info "Uso: ./start.sh [core|dashboard|ai]"
            exit 1
            ;;
    esac
    
    # Esperar health check
    wait_healthy
    
    # Mostrar información
    show_info
}

# Ejecutar
main "$@"
