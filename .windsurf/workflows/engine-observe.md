---
description: Monitorear producción, ver logs, errores y métricas
---

# engine-observe (scraper-portalinmobiliario)

Workflow de observabilidad para monitorear el scraper en producción (Railway).

---

## Uso

```bash
/engine-observe                  # Dashboard completo
/engine-observe --logs           # Solo logs
/engine-observe --errors         # Solo errores
/engine-observe --metrics        # Solo métricas
```

---

## Pasos

### 1. Verificar Estado del Servicio

**Railway:**
```bash
# Verificar que el servicio está corriendo
railway status

# Ver información del deployment
railway logs --tail 50
```

**Local:**
```bash
# Verificar procesos Python
ps aux | grep python

# Verificar uso de recursos
top -p $(pgrep -f "python main.py")
```

---

### 2. Ver Logs

**Railway:**
```bash
# Logs en tiempo real
railway logs --follow

# Últimos 100 logs
railway logs --tail 100

# Filtrar por nivel
railway logs | grep "ERROR"
railway logs | grep "WARNING"
```

**Local:**
```bash
# Si se implementa logging a archivo
tail -f logs/scraper.log

# Filtrar errores
tail -f logs/scraper.log | grep "ERROR"
```

**Análisis de logs:**
```bash
# Contar errores
railway logs --tail 1000 | grep "ERROR" | wc -l

# Errores más comunes
railway logs --tail 1000 | grep "ERROR" | sort | uniq -c | sort -rn | head -10

# Timeouts
railway logs --tail 1000 | grep "TimeoutException" | wc -l
```

---

### 3. Monitorear Errores

**Tipos de errores a monitorear:**

1. **Errores de Scraping:**
   - TimeoutException
   - Selectores no encontrados
   - Rate limiting

2. **Errores de Datos:**
   - Validación fallida
   - Campos faltantes
   - Formatos inválidos

3. **Errores de Sistema:**
   - Out of memory
   - Disk full
   - Network errors

**Comandos:**
```bash
# Ver últimos errores
railway logs | grep "ERROR" | tail -20

# Agrupar por tipo
railway logs | grep "ERROR" | awk '{print $5}' | sort | uniq -c | sort -rn

# Ver stack traces
railway logs | grep -A 10 "Traceback"
```

---

### 4. Métricas de Performance

**Métricas clave:**

1. **Throughput:**
   - Propiedades scrapeadas por minuto
   - Páginas procesadas por hora

2. **Latencia:**
   - Tiempo promedio por página
   - Tiempo promedio por propiedad

3. **Tasa de éxito:**
   - % de páginas exitosas
   - % de propiedades válidas

**Análisis:**
```bash
# Contar propiedades scrapeadas
railway logs | grep "Propiedad extraída" | wc -l

# Calcular tiempo promedio
railway logs | grep "Página scrapeada en" | awk '{sum+=$NF; count++} END {print sum/count}'

# Tasa de éxito
railway logs | grep -E "(exitoso|fallido)" | sort | uniq -c
```

---

### 5. Monitorear Recursos

**Railway:**
```bash
# Ver uso de recursos en Railway dashboard
# CPU, Memory, Network

# O usar Railway CLI (si está disponible)
railway metrics
```

**Local:**
```bash
# CPU y memoria
top -p $(pgrep -f "python main.py")

# Uso de disco
df -h output/

# Network
netstat -an | grep ESTABLISHED | grep portalinmobiliario
```

---

### 6. Verificar Calidad de Datos

**Análisis de archivos generados:**
```bash
# Listar archivos recientes
ls -lht output/ | head -10

# Contar propiedades en archivo JSON
cat output/venta_departamento_*.json | jq '.propiedades | length'

# Verificar campos faltantes
python validator.py output/*.json --report

# Estadísticas de precios
cat output/*.json | jq '.propiedades[].precio' | sort | uniq -c
```

---

### 7. Alertas y Notificaciones

**Configurar alertas para:**

1. **Errores críticos:**
   - Tasa de error > 10%
   - Servicio caído
   - Out of memory

2. **Performance:**
   - Throughput < umbral
   - Latencia > umbral

3. **Datos:**
   - Propiedades con campos faltantes > 5%
   - Duplicados > 10%

**Implementación básica:**
```bash
# Script de monitoreo (ejecutar en cron)
#!/bin/bash

ERROR_COUNT=$(railway logs --tail 100 | grep "ERROR" | wc -l)

if [ $ERROR_COUNT -gt 10 ]; then
    echo "⚠️ ALERTA: $ERROR_COUNT errores en últimos 100 logs"
    # Enviar notificación (email, Slack, etc.)
fi
```

---

## Dashboard de Observabilidad

**Resumen visual:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 SCRAPER OBSERVABILITY DASHBOARD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🟢 Estado: Running
⏱️  Uptime: 24h 35m

📈 Métricas (últimas 24h):
  • Propiedades scrapeadas: 1,234
  • Páginas procesadas: 45
  • Throughput: 51 props/hora
  • Tiempo promedio/página: 12.3s

✅ Calidad de Datos:
  • Propiedades válidas: 98.5%
  • Campos completos: 95.2%
  • Duplicados: 1.2%

⚠️  Errores (últimas 24h):
  • TimeoutException: 3
  • Selectores no encontrados: 1
  • Rate limiting: 0

💾 Recursos:
  • CPU: 45%
  • Memoria: 512MB / 1GB
  • Disco: 2.3GB / 10GB

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Troubleshooting

### No hay logs en Railway
```bash
# Verificar que el servicio está corriendo
railway status

# Re-deploy si es necesario
railway up
```

### Logs locales no se generan
```bash
# Verificar configuración de logging
cat config.py | grep LOG

# Crear directorio de logs
mkdir -p logs
```

### Métricas inconsistentes
```bash
# Limpiar cache
rm -rf __pycache__

# Verificar timestamps en logs
railway logs | grep "timestamp"
```

---

## Integración con Herramientas

### Sentry (Error Tracking)
```python
import sentry_sdk

sentry_sdk.init(
    dsn="YOUR_DSN",
    traces_sample_rate=1.0
)
```

### Prometheus (Métricas)
```python
from prometheus_client import Counter, Histogram

properties_scraped = Counter('properties_scraped_total', 'Total properties scraped')
scraping_duration = Histogram('scraping_duration_seconds', 'Time spent scraping')
```

---

**Última actualización:** Abril 2026
