# Historial de Ejecuciones - Dashboard Scraper

**Fecha:** 12 Abril 2026  
**Estado:** ✅ Completado

## Descripción

Implementación del historial completo de ejecuciones en el dashboard del scraper, mostrando todas las ejecuciones (manuales y programadas) con estado, resultado y métricas detalladas.

## Cambios Implementados

### 1. Template HTML (`templates/dashboard/scraper.html`)

**Sección "Historial de Ejecuciones" actualizada:**

- ✅ Nueva tabla con 7 columnas informativas:
  - **Tipo:** Tipo de propiedad (departamento, casa, etc.)
  - **Operación:** Venta, arriendo, arriendo-temporada
  - **Inicio:** Fecha/hora de inicio + tiempo relativo
  - **Duración:** Tiempo total de ejecución formateado
  - **Estado:** Badge con color según estado (running, completed, failed, cancelled)
  - **Trigger:** Badge indicando origen (Manual, Programado, API)
  - **Resultado:** Métricas detalladas (propiedades scrapeadas, nuevas, páginas procesadas, errores)

- ✅ Botón "Actualizar" para refrescar manualmente
- ✅ Descripción "Últimas 50 ejecuciones (manuales y programadas)"
- ✅ Filas clickeables para ver detalles (preparado para modal futuro)
- ✅ Estado vacío con icono y mensaje

### 2. JavaScript (`static/js/scraper-control.js`)

**Nuevas variables:**
- `executionHistory`: Array con las últimas 50 ejecuciones

**Nuevas funciones:**
- `refreshExecutionHistory()`: Carga historial desde `/api/scraper/executions?per_page=50`
- `showExecutionDetails(executionId)`: Placeholder para modal de detalles
- `formatTimeAgo(dateStr)`: Formatea tiempo relativo (Hace 5m, Hace 2h, Hace 3d, etc.)
- `formatDuration(seconds)`: Formatea duración (2h 30m, 45m 12s, 30s)
- `getStatusClass(status)`: Retorna clases CSS según estado
- `getStatusLabel(status)`: Traduce estado a español

**Auto-refresh:**
- Historial se actualiza cada 60 segundos automáticamente
- Se carga al inicializar el dashboard

### 3. CSS (`templates/dashboard/scraper.html`)

**Nuevos estilos:**
- `.cursor-pointer`: Cursor de mano para filas clickeables
- `.cursor-pointer:hover`: Efecto hover en filas

### 4. Backend (ya existente)

**Endpoint utilizado:**
- `GET /api/scraper/executions?per_page=50`
- Retorna datos de la tabla `scraper_executions`
- Incluye todos los campos necesarios: `execution_id`, `operacion`, `tipo`, `start_time`, `end_time`, `duration`, `status`, `triggered_by`, `properties_scraped`, `properties_new`, `properties_updated`, `pages_processed`, `error_message`

## Datos Mostrados

### Estados de Ejecución
- **running** (En ejecución) - Badge azul
- **completed** (Completado) - Badge verde
- **failed** (Fallido) - Badge rojo
- **cancelled** (Cancelado) - Badge amarillo

### Tipos de Trigger
- **manual** - Badge morado "Manual"
- **scheduled** - Badge verde "Programado"
- **api** - Badge azul "API"

### Métricas
- Propiedades scrapeadas totales
- Propiedades nuevas (entre paréntesis)
- Páginas procesadas
- Mensaje de error (si existe, truncado)

## Funcionalidad Futura

### Modal de Detalles (Pendiente)
Al hacer click en una fila, se abrirá un modal mostrando:
- Detalles completos de la ejecución
- Parámetros utilizados
- Logs en tiempo real
- Gráficos de progreso
- Botón para descargar logs

## Testing

### Casos de Prueba
1. ✅ Historial vacío muestra mensaje apropiado
2. ✅ Ejecuciones manuales se muestran con badge "Manual"
3. ✅ Ejecuciones programadas se muestran con badge "Programado"
4. ✅ Estados se muestran con colores correctos
5. ✅ Duración se formatea correctamente
6. ✅ Tiempo relativo se actualiza
7. ✅ Errores se muestran truncados
8. ✅ Auto-refresh funciona cada 60 segundos

### Para Verificar en Producción
```bash
# 1. Ejecutar scraping manual
# 2. Verificar que aparece en historial con badge "Manual"
# 3. Esperar a que complete
# 4. Verificar que estado cambia a "Completado"
# 5. Verificar métricas (props, páginas)
# 6. Ejecutar scraping programado
# 7. Verificar que aparece con badge "Programado"
```

## Archivos Modificados

1. `templates/dashboard/scraper.html` - Template HTML actualizado
2. `static/js/scraper-control.js` - Lógica JavaScript agregada

## Archivos Relacionados (sin cambios)

1. `dashboard/routes.py` - Endpoint `/api/scraper/executions` (ya existente)
2. `db_loader.py` - Método `get_scraper_executions()` (ya existente)
3. `models/scraper_execution.py` - Modelo `ScraperExecution` (ya existente)

## Notas Técnicas

- El historial se limita a 50 ejecuciones para optimizar rendimiento
- Se puede filtrar por `status`, `operacion`, `tipo` vía query params
- Paginación disponible con `page` y `per_page`
- Ordenamiento descendente por `start_time` (más recientes primero)

## Próximos Pasos

1. Implementar modal de detalles de ejecución
2. Agregar filtros en la UI (por estado, operación, tipo)
3. Agregar paginación en la UI
4. Agregar gráficos de tendencias
5. Exportar historial a CSV/Excel
