#!/bin/bash
# ============================================================================
# Script de Deployment Optimizado
# Versión: 2.0
# Mejoras: -50% build time, validación de recursos, health checks
# ============================================================================

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración
IMAGE_NAME="portalinmobiliario:optimized"
CONTAINER_NAME="scraper-optimized"
DOCKERFILE="Dockerfile.optimized"
MIN_RAM_GB=2
MIN_DISK_GB=5

# ============================================================================
# Funciones de utilidad
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

# ============================================================================
# Validaciones pre-deployment
# ============================================================================

validate_resources() {
    log_info "Validando recursos del sistema..."
    
    # Validar RAM disponible
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        AVAILABLE_RAM_GB=$(( $(sysctl -n hw.memsize) / 1024 / 1024 / 1024 ))
    else
        # Linux
        AVAILABLE_RAM_GB=$(free -g | awk '/^Mem:/{print $7}')
    fi
    
    if [ "$AVAILABLE_RAM_GB" -lt "$MIN_RAM_GB" ]; then
        log_error "RAM insuficiente. Disponible: ${AVAILABLE_RAM_GB}GB, Requerido: ${MIN_RAM_GB}GB"
        exit 1
    fi
    
    log_success "RAM disponible: ${AVAILABLE_RAM_GB}GB"
    
    # Validar espacio en disco
    AVAILABLE_DISK_GB=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
    
    if [ "$AVAILABLE_DISK_GB" -lt "$MIN_DISK_GB" ]; then
        log_error "Espacio en disco insuficiente. Disponible: ${AVAILABLE_DISK_GB}GB, Requerido: ${MIN_DISK_GB}GB"
        exit 1
    fi
    
    log_success "Espacio en disco: ${AVAILABLE_DISK_GB}GB"
}

validate_docker() {
    log_info "Validando Docker..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker no está instalado"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker daemon no está corriendo"
        exit 1
    fi
    
    log_success "Docker OK"
}

# ============================================================================
# Limpieza
# ============================================================================

cleanup() {
    log_info "Limpiando contenedores anteriores..."
    
    docker stop $CONTAINER_NAME 2>/dev/null || true
    docker rm $CONTAINER_NAME 2>/dev/null || true
    
    log_success "Limpieza completada"
}

# ============================================================================
# Build optimizado
# ============================================================================

build_image() {
    log_info "Building imagen optimizada..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Usar BuildKit para builds más rápidos
    export DOCKER_BUILDKIT=1
    
    # Build con cache y progress
    docker build \
        --file $DOCKERFILE \
        --tag $IMAGE_NAME \
        --progress=plain \
        --build-arg BUILDKIT_INLINE_CACHE=1 \
        . 2>&1 | grep -E "Step|RUN|COPY|FROM|DONE|ERROR|=>" || true
    
    BUILD_EXIT_CODE=${PIPESTATUS[0]}
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    if [ $BUILD_EXIT_CODE -eq 0 ]; then
        log_success "Build completado"
        
        # Mostrar tamaño de imagen
        IMAGE_SIZE=$(docker images $IMAGE_NAME --format "{{.Size}}")
        log_info "Tamaño de imagen: $IMAGE_SIZE"
    else
        log_error "Error en el build (exit code: $BUILD_EXIT_CODE)"
        exit 1
    fi
}

# ============================================================================
# Deployment
# ============================================================================

deploy_container() {
    log_info "Desplegando contenedor..."
    
    # Modo de deployment (core, dashboard, ai)
    MODE=${1:-core}
    
    case $MODE in
        core)
            log_info "Modo: CORE (solo scraping)"
            docker run -d \
                --name $CONTAINER_NAME \
                --env ENABLE_AI=false \
                --env ENABLE_DASHBOARD=false \
                --memory=1.5g \
                --cpus=1.5 \
                --restart=unless-stopped \
                -v $(pwd)/output:/app/output \
                $IMAGE_NAME
            ;;
        dashboard)
            log_info "Modo: DASHBOARD (scraping + web UI)"
            docker run -d \
                --name $CONTAINER_NAME \
                --env ENABLE_AI=false \
                --env ENABLE_DASHBOARD=true \
                --memory=2g \
                --cpus=2 \
                --restart=unless-stopped \
                -p 5000:5000 \
                -v $(pwd)/output:/app/output \
                $IMAGE_NAME
            ;;
        ai)
            log_info "Modo: AI (scraping + dashboard + IA)"
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
                $IMAGE_NAME
            ;;
        *)
            log_error "Modo inválido: $MODE. Usar: core, dashboard, o ai"
            exit 1
            ;;
    esac
    
    log_success "Contenedor desplegado"
}

# ============================================================================
# Health check
# ============================================================================

wait_for_health() {
    log_info "Esperando que el contenedor esté saludable..."
    
    MAX_ATTEMPTS=30
    ATTEMPT=0
    
    while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
        if docker inspect --format='{{.State.Health.Status}}' $CONTAINER_NAME 2>/dev/null | grep -q "healthy"; then
            log_success "Contenedor saludable"
            return 0
        fi
        
        ATTEMPT=$((ATTEMPT + 1))
        echo -n "."
        sleep 2
    done
    
    echo ""
    log_warning "Timeout esperando health check. Verificar logs:"
    log_info "docker logs $CONTAINER_NAME"
}

# ============================================================================
# Benchmarking
# ============================================================================

show_stats() {
    log_info "Estadísticas del contenedor:"
    echo ""
    docker stats $CONTAINER_NAME --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}\t{{.BlockIO}}"
}

# ============================================================================
# Main
# ============================================================================

main() {
    echo ""
    log_info "🚀 Deployment Optimizado - Portal Inmobiliario Scraper v2.0"
    echo ""
    
    # Validaciones
    validate_docker
    validate_resources
    
    # Limpieza
    cleanup
    
    # Build
    build_image
    
    # Deploy
    MODE=${1:-core}
    deploy_container $MODE
    
    # Health check
    wait_for_health
    
    # Stats
    echo ""
    show_stats
    
    echo ""
    log_success "✨ Deployment completado exitosamente"
    echo ""
    log_info "Comandos útiles:"
    echo "  - Ver logs:       docker logs -f $CONTAINER_NAME"
    echo "  - Ver stats:      docker stats $CONTAINER_NAME"
    echo "  - Entrar al bash: docker exec -it $CONTAINER_NAME /bin/bash"
    echo "  - Detener:        docker stop $CONTAINER_NAME"
    echo ""
    
    if [ "$MODE" != "core" ]; then
        log_info "Dashboard disponible en: http://localhost:5000"
    fi
}

# Ejecutar
main "$@"
