#!/bin/bash
# Script para configurar jobs con intervalo de 10 minutos
# Sincronización continua de todas las fuentes de datos

API_URL="http://localhost:4421/api/scheduler/jobs"

echo "Configurando jobs con intervalo de 10 minutos..."
echo ""

# Array de combinaciones operación-tipo
declare -a JOBS=(
    "venta:departamento"
    "arriendo:departamento"
    "venta:casa"
    "arriendo:casa"
    "venta:oficina"
    "arriendo:oficina"
    "venta:terreno"
    "arriendo:terreno"
)

COUNTER=0

for job in "${JOBS[@]}"; do
    IFS=':' read -r operacion tipo <<< "$job"
    COUNTER=$((COUNTER + 1))
    
    echo "[$COUNTER/${#JOBS[@]}] Creando job: $operacion - $tipo"
    
    curl -s -X POST "$API_URL" \
        -H "Content-Type: application/json" \
        -d "{
            \"operacion\": \"$operacion\",
            \"tipo\": \"$tipo\",
            \"schedule_type\": \"interval\",
            \"schedule_args\": {
                \"minutes\": 10
            },
            \"max_pages\": 20,
            \"scrape_details\": true,
            \"max_detail_properties\": 50
        }" | jq -r '.status + ": " + .message'
    
    echo ""
done

echo "=========================================="
echo "Jobs configurados exitosamente"
echo "Total: ${#JOBS[@]} jobs"
echo "Intervalo: 10 minutos"
echo "=========================================="
