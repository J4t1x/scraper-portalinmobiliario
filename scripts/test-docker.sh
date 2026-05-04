#!/bin/bash
# Script de testing para validar el contenedor Docker

set -e

echo "================================================"
echo "Testing Portal Inmobiliario Docker Container"
echo "================================================"

# Colores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para imprimir con color
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# 1. Verificar que Docker está corriendo
echo ""
print_info "1. Verificando Docker..."
if ! docker info > /dev/null 2>&1; then
    print_error "Docker no está corriendo. Inicia Docker Desktop primero."
    exit 1
fi
print_success "Docker está corriendo"

# 2. Build de la imagen
echo ""
print_info "2. Construyendo imagen Docker..."
if docker build -t portalinmobiliario:latest .; then
    print_success "Imagen construida exitosamente"
else
    print_error "Error al construir la imagen"
    exit 1
fi

# 3. Verificar que la imagen existe
echo ""
print_info "3. Verificando imagen..."
if docker images | grep -q portalinmobiliario; then
    print_success "Imagen portalinmobiliario encontrada"
    docker images | grep portalinmobiliario
else
    print_error "Imagen no encontrada"
    exit 1
fi

# 4. Test: Verificar Python
echo ""
print_info "4. Verificando Python en el contenedor..."
if docker run --rm portalinmobiliario:latest python --version; then
    print_success "Python funciona correctamente"
else
    print_error "Error con Python"
    exit 1
fi

# 5. Test: Verificar Chrome
echo ""
print_info "5. Verificando Chrome en el contenedor..."
if docker run --rm portalinmobiliario:latest google-chrome --version; then
    print_success "Chrome funciona correctamente"
else
    print_error "Error con Chrome"
    exit 1
fi

# 6. Test: Verificar ChromeDriver
echo ""
print_info "6. Verificando ChromeDriver en el contenedor..."
if docker run --rm portalinmobiliario:latest chromedriver --version; then
    print_success "ChromeDriver funciona correctamente"
else
    print_error "Error con ChromeDriver"
    exit 1
fi

# 7. Test: Ejecutar help del scraper
echo ""
print_info "7. Verificando script principal..."
if docker run --rm portalinmobiliario:latest python main.py --help; then
    print_success "Script principal funciona correctamente"
else
    print_error "Error con script principal"
    exit 1
fi

# 8. Test: Verificar entrypoint
echo ""
print_info "8. Verificando entrypoint..."
if docker run --rm portalinmobiliario:latest echo "Entrypoint OK"; then
    print_success "Entrypoint funciona correctamente"
else
    print_error "Error con entrypoint"
    exit 1
fi

# 9. Test opcional: Ejecutar scraper de prueba (comentado por defecto)
echo ""
print_info "9. Test de scraping (opcional - comentado)"
echo "Para ejecutar un test real de scraping, descomenta la siguiente línea:"
echo "# docker run --rm -v \$(pwd)/output:/app/output portalinmobiliario:latest python main.py --operacion venta --tipo departamento --max-pages 1"

# Resumen
echo ""
echo "================================================"
print_success "TODOS LOS TESTS PASARON EXITOSAMENTE"
echo "================================================"
echo ""
echo "Próximos pasos:"
echo "1. Ejecutar scraper de prueba:"
echo "   docker run --rm -v \$(pwd)/output:/app/output portalinmobiliario:latest python main.py --operacion venta --tipo departamento --max-pages 1"
echo ""
echo "2. Probar con docker-compose:"
echo "   docker-compose up -d"
echo "   docker-compose run --rm scraper python main.py --operacion venta --tipo departamento"
echo ""
echo "3. Subir a GitHub:"
echo "   git add ."
echo "   git commit -m \"feat(docker): configuración Docker y Railway\""
echo "   git push origin main"
echo ""
echo "4. Desplegar en Railway:"
echo "   Ver DOCKER.md para instrucciones completas"
echo ""
