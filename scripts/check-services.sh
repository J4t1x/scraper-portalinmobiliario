#!/bin/bash
# Script para verificar el estado de todos los servicios en el contenedor MVP

echo "🔍 Verificando servicios del contenedor MVP..."
echo ""

# Verificar que el contenedor esté corriendo
if ! docker ps | grep -q scraper-mvp; then
    echo "❌ El contenedor scraper-mvp no está corriendo"
    echo "   Ejecuta: docker run -d --name scraper-mvp -p 5000:5000 -p 11434:11434 portalinmobiliario:mvp"
    exit 1
fi

echo "✅ Contenedor scraper-mvp está corriendo"
echo ""

# Estado de Supervisor
echo "📋 Estado de servicios (Supervisor):"
docker exec scraper-mvp supervisorctl status
echo ""

# PostgreSQL
echo "🗄️  PostgreSQL:"
if docker exec scraper-mvp pg_isready -U scraper -d portalinmobiliario > /dev/null 2>&1; then
    echo "   ✅ PostgreSQL está listo"
else
    echo "   ❌ PostgreSQL no responde"
fi
echo ""

# Ollama
echo "🤖 Ollama:"
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "   ✅ Ollama está disponible en puerto 11434"
    echo "   📦 Modelos instalados:"
    docker exec scraper-mvp ollama list
else
    echo "   ❌ Ollama no responde"
fi
echo ""

# Flask
echo "🌐 Flask API:"
if curl -s http://localhost:5000/health > /dev/null 2>&1; then
    echo "   ✅ Flask está disponible en puerto 5000"
else
    echo "   ❌ Flask no responde"
fi
echo ""

# Uso de recursos
echo "💻 Uso de recursos:"
docker stats scraper-mvp --no-stream --format "   CPU: {{.CPUPerc}}\n   RAM: {{.MemUsage}}\n   NET: {{.NetIO}}"
echo ""

echo "✨ Verificación completada"
