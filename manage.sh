#!/bin/bash
# ============================================================================
# Script de Gestión - Portal Inmobiliario Scraper
# Versión: 2.0
# Uso: ./manage.sh [start|stop|restart|logs|stats|shell|status]
# ============================================================================

set -e

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

CONTAINER_NAME="scraper-optimized"

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

log_header() {
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# ============================================================================
# Comandos
# ============================================================================

cmd_start() {
    log_info "Iniciando contenedor..."
    ./start.sh "$@"
}

cmd_stop() {
    log_info "Deteniendo contenedor..."
    docker stop $CONTAINER_NAME 2>/dev/null || log_warning "Contenedor no está corriendo"
    log_success "Contenedor detenido"
}

cmd_restart() {
    log_info "Reiniciando contenedor..."
    cmd_stop
    sleep 2
    cmd_start "$@"
}

cmd_logs() {
    SERVICE=${1:-"all"}
    
    case $SERVICE in
        all)
            log_info "Mostrando todos los logs..."
            docker logs -f $CONTAINER_NAME
            ;;
        flask)
            log_info "Mostrando logs de Flask..."
            docker exec -it $CONTAINER_NAME tail -f /var/log/flask.log
            ;;
        postgres|postgresql|db)
            log_info "Mostrando logs de PostgreSQL..."
            docker exec -it $CONTAINER_NAME tail -f /var/log/postgresql.log
            ;;
        redis)
            log_info "Mostrando logs de Redis..."
            docker exec -it $CONTAINER_NAME tail -f /var/log/redis.log
            ;;
        ollama|ai)
            log_info "Mostrando logs de Ollama..."
            docker exec -it $CONTAINER_NAME tail -f /var/log/ollama.log
            ;;
        scheduler)
            log_info "Mostrando logs del Scheduler..."
            docker exec -it $CONTAINER_NAME tail -f /var/log/scheduler.log
            ;;
        *)
            log_error "Servicio desconocido: $SERVICE"
            log_info "Servicios disponibles: all, flask, postgres, redis, ollama, scheduler"
            exit 1
            ;;
    esac
}

cmd_stats() {
    log_header "📊 Estadísticas del Contenedor"
    docker stats $CONTAINER_NAME
}

cmd_shell() {
    log_info "Abriendo shell en el contenedor..."
    docker exec -it $CONTAINER_NAME /bin/bash
}

cmd_status() {
    log_header "📋 Estado del Contenedor"
    
    # Estado del contenedor
    if docker ps | grep -q $CONTAINER_NAME; then
        log_success "Contenedor: CORRIENDO"
        
        # Health status
        HEALTH=$(docker inspect --format='{{.State.Health.Status}}' $CONTAINER_NAME 2>/dev/null || echo "N/A")
        if [ "$HEALTH" = "healthy" ]; then
            log_success "Health: SALUDABLE"
        else
            log_warning "Health: $HEALTH"
        fi
        
        # Uptime
        UPTIME=$(docker inspect --format='{{.State.StartedAt}}' $CONTAINER_NAME)
        log_info "Iniciado: $UPTIME"
        
        echo ""
        log_header "🔧 Servicios Activos"
        docker exec -it $CONTAINER_NAME supervisorctl status
        
        echo ""
        log_header "💾 Uso de Recursos"
        docker stats $CONTAINER_NAME --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}\t{{.BlockIO}}"
        
        echo ""
        log_header "📦 Información de la Imagen"
        docker images | grep portalinmobiliario
        
    else
        log_warning "Contenedor: DETENIDO"
    fi
}

cmd_services() {
    log_header "🔧 Gestión de Servicios"
    
    ACTION=${1:-"status"}
    SERVICE=${2:-"all"}
    
    case $ACTION in
        status)
            docker exec -it $CONTAINER_NAME supervisorctl status
            ;;
        start)
            if [ "$SERVICE" = "all" ]; then
                docker exec -it $CONTAINER_NAME supervisorctl start all
            else
                docker exec -it $CONTAINER_NAME supervisorctl start $SERVICE
            fi
            ;;
        stop)
            if [ "$SERVICE" = "all" ]; then
                docker exec -it $CONTAINER_NAME supervisorctl stop all
            else
                docker exec -it $CONTAINER_NAME supervisorctl stop $SERVICE
            fi
            ;;
        restart)
            if [ "$SERVICE" = "all" ]; then
                docker exec -it $CONTAINER_NAME supervisorctl restart all
            else
                docker exec -it $CONTAINER_NAME supervisorctl restart $SERVICE
            fi
            ;;
        *)
            log_error "Acción desconocida: $ACTION"
            log_info "Acciones disponibles: status, start, stop, restart"
            exit 1
            ;;
    esac
}

cmd_cache() {
    log_header "📊 Estadísticas de Cache Redis"
    
    docker exec -it $CONTAINER_NAME redis-cli INFO stats | grep -E "keyspace_hits|keyspace_misses"
    
    echo ""
    KEYS=$(docker exec -it $CONTAINER_NAME redis-cli DBSIZE)
    log_info "Total de claves en cache: $KEYS"
    
    echo ""
    log_info "Comandos útiles:"
    echo "  - Ver todas las claves: docker exec -it $CONTAINER_NAME redis-cli KEYS '*'"
    echo "  - Limpiar cache:        docker exec -it $CONTAINER_NAME redis-cli FLUSHALL"
}

cmd_db() {
    log_header "🗄️ PostgreSQL"
    
    log_info "Abriendo psql..."
    docker exec -it $CONTAINER_NAME psql -U scraper -d portalinmobiliario
}

cmd_help() {
    log_header "🚀 Portal Inmobiliario Scraper - Gestión"
    
    echo ""
    echo "Uso: ./manage.sh [comando] [opciones]"
    echo ""
    echo "Comandos principales:"
    echo "  start [mode]       - Iniciar contenedor (mode: core|dashboard|ai)"
    echo "  stop               - Detener contenedor"
    echo "  restart [mode]     - Reiniciar contenedor"
    echo "  status             - Ver estado completo"
    echo ""
    echo "Logs:"
    echo "  logs [service]     - Ver logs (service: all|flask|postgres|redis|ollama|scheduler)"
    echo ""
    echo "Monitoreo:"
    echo "  stats              - Ver estadísticas en tiempo real"
    echo "  cache              - Ver estadísticas de Redis cache"
    echo ""
    echo "Acceso:"
    echo "  shell              - Abrir bash en el contenedor"
    echo "  db                 - Abrir psql (PostgreSQL)"
    echo ""
    echo "Servicios:"
    echo "  services [action] [service]"
    echo "    action: status|start|stop|restart"
    echo "    service: all|flask|postgresql|redis|ollama|scheduler"
    echo ""
    echo "Ejemplos:"
    echo "  ./manage.sh start dashboard"
    echo "  ./manage.sh logs flask"
    echo "  ./manage.sh services restart flask"
    echo "  ./manage.sh stats"
    echo ""
}

# ============================================================================
# Main
# ============================================================================

main() {
    COMMAND=${1:-"help"}
    shift || true
    
    case $COMMAND in
        start)
            cmd_start "$@"
            ;;
        stop)
            cmd_stop
            ;;
        restart)
            cmd_restart "$@"
            ;;
        logs)
            cmd_logs "$@"
            ;;
        stats)
            cmd_stats
            ;;
        shell|bash)
            cmd_shell
            ;;
        status)
            cmd_status
            ;;
        services)
            cmd_services "$@"
            ;;
        cache)
            cmd_cache
            ;;
        db|psql)
            cmd_db
            ;;
        help|--help|-h)
            cmd_help
            ;;
        *)
            log_error "Comando desconocido: $COMMAND"
            cmd_help
            exit 1
            ;;
    esac
}

# Ejecutar
main "$@"
