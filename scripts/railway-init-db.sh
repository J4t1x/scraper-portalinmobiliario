#!/bin/bash
# ============================================================================
# Script para inicializar la base de datos en Railway
# Uso: railway run bash railway-init-db.sh
# ============================================================================

set -e

echo "🗄️ Inicializando base de datos en Railway..."
echo ""

# Verificar que DATABASE_URL esté configurado
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL no está configurado"
    exit 1
fi

echo "✅ DATABASE_URL configurado"
echo ""

# Ejecutar script de inicialización
echo "📦 Creando tablas..."
python init_db.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Base de datos inicializada correctamente en Railway"
else
    echo ""
    echo "❌ Error al inicializar la base de datos"
    exit 1
fi
