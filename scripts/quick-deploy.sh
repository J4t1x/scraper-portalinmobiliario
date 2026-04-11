#!/bin/bash
# Quick deployment - Muestra output en tiempo real
# Uso: ./scripts/quick-deploy.sh

set -e

IMAGE_NAME="portalinmobiliario:mvp"
CONTAINER_NAME="scraper-mvp"

echo "🚀 Iniciando deployment..."
echo ""

# Limpiar contenedor anterior
echo "🧹 Limpiando contenedores anteriores..."
docker stop $CONTAINER_NAME 2>/dev/null || true
docker rm $CONTAINER_NAME 2>/dev/null || true
echo "✅ Limpieza completada"
echo ""

# Build con output en tiempo real
echo "📦 Building imagen Docker (10-15 minutos)..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

docker build -f Dockerfile.mvp -t $IMAGE_NAME . 2>&1 | while IFS= read -r line; do
    # Mostrar líneas importantes
    if echo "$line" | grep -qE "Step|RUN|COPY|FROM|DONE|ERROR|=>"; then
        echo "$line"
    fi
done

BUILD_EXIT_CODE=${PIPESTATUS[0]}

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $BUILD_EXIT_CODE -eq 0 ]; then
    echo "✅ Build completado exitosamente"
    echo ""
    echo "Ejecuta ahora:"
    echo "  ./scripts/start-container.sh"
else
    echo "❌ Error en el build (exit code: $BUILD_EXIT_CODE)"
    exit 1
fi
