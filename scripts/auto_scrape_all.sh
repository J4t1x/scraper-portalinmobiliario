#!/bin/bash
# Script de scraping automático completo
# Ejecuta todas las combinaciones de operación × tipo de propiedad

set -e

OPERACIONES=("venta" "arriendo" "arriendo-de-temporada")
TIPOS=("departamento" "casa" "oficina" "terreno" "local-comercial" "bodega" "estacionamiento" "parcela")

TOTAL=$((${#OPERACIONES[@]} * ${#TIPOS[@]}))
CURRENT=0

echo "=========================================="
echo "SCRAPING AUTOMÁTICO - PORTAL INMOBILIARIO"
echo "=========================================="
echo "Total de combinaciones: $TOTAL"
echo "Inicio: $(date)"
echo "=========================================="
echo ""

for operacion in "${OPERACIONES[@]}"; do
  for tipo in "${TIPOS[@]}"; do
    CURRENT=$((CURRENT + 1))
    echo "[$CURRENT/$TOTAL] Scraping: $operacion - $tipo"
    echo "Inicio: $(date '+%Y-%m-%d %H:%M:%S')"
    
    docker compose -f docker-compose.v2.yml run --rm scraper \
      python main.py \
      --operacion "$operacion" \
      --tipo "$tipo" \
      --formato json \
      --persist-to-db \
      --scrape-details \
      --max-detail-properties 100 \
      --verbose
    
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 0 ]; then
      echo "✅ Completado: $operacion - $tipo"
    else
      echo "❌ Error en: $operacion - $tipo (exit code: $EXIT_CODE)"
    fi
    
    echo "Fin: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "---"
    echo ""
    
    # Delay entre ejecuciones para no saturar
    sleep 5
  done
done

echo "=========================================="
echo "SCRAPING COMPLETO FINALIZADO"
echo "Fin: $(date)"
echo "=========================================="
