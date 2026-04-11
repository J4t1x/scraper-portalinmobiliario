#!/bin/bash
# Iniciar contenedor después del build
# Uso: ./scripts/start-container.sh

set -e

IMAGE_NAME="portalinmobiliario:mvp"
CONTAINER_NAME="scraper-mvp"
FLASK_PORT=5000
OLLAMA_PORT=11434

echo "🚀 Iniciando contenedor MVP..."

# Crear volumen si no existe
docker volume create ollama-models 2>/dev/null || true

# Iniciar contenedor
docker run -d \
  --name $CONTAINER_NAME \
  -p $FLASK_PORT:5000 \
  -p $OLLAMA_PORT:11434 \
  -v $(pwd)/output:/app/output \
  -v ollama-models:/app/.ollama/models \
  $IMAGE_NAME

echo "✅ Contenedor iniciado"
echo ""
echo "📍 URLs:"
echo "  • Dashboard: http://localhost:$FLASK_PORT"
echo "  • Ollama: http://localhost:$OLLAMA_PORT"
echo ""
echo "🔍 Verificar estado:"
echo "  ./scripts/check-services.sh"
echo ""
echo "📋 Ver logs:"
echo "  docker logs -f $CONTAINER_NAME"
