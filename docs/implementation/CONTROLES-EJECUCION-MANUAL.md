# Controles Adicionales de Ejecución Manual

**Fecha:** 12 Abril 2026  
**Estado:** ✅ Completado

## Descripción

Implementación de controles adicionales para la ejecución manual del scraper en el dashboard, permitiendo al usuario detener ejecuciones en curso y limitar la cantidad de registros a scrapear.

## Nuevas Funcionalidades

### 1. Selector de Cantidad Máxima de Registros

**Ubicación:** Sección "Ejecución Manual" del dashboard

**Opciones disponibles:**
- Sin límite (0)
- 50 propiedades
- 100 propiedades
- 200 propiedades
- 500 propiedades
- 1000 propiedades

**Comportamiento:**
- El scraper detendrá la ejecución automáticamente al alcanzar el límite de propiedades
- Útil para pruebas rápidas o scraping parcial
- Si se selecciona "Sin límite", el scraper procesará todas las páginas configuradas

### 2. Botón de Detener Ejecución

**Ubicación:** Junto al botón "Ejecutar Scraping"

**Características:**
- Solo se habilita cuando hay una ejecución activa
- Requiere confirmación del usuario antes de cancelar
- Actualiza el estado de la ejecución a "cancelled" en la base de datos
- Agrega log de cancelación
- Refresca automáticamente el historial de ejecuciones

**Flujo de cancelación:**
1. Usuario hace click en "Detener"
2. Sistema muestra confirmación
3. Si confirma, envía petición POST a `/api/scraper/executions/{execution_id}/cancel`
4. Backend actualiza estado a "cancelled" y registra duración
5. Frontend muestra mensaje de cancelación y refresca datos

## Cambios Implementados

### 1. Frontend - HTML (`templates/dashboard/scraper.html`)

**Grid de configuración actualizado:**
- Cambió de 4 a 5 columnas (lg:grid-cols-5)
- Nuevo selector "Registros Máx" entre "Páginas Máx" y "Formato"

**Botones de control mejorados:**
- Botón "Ejecutar Scraping" con iconos SVG (play/spinner)
- Nuevo botón "Detener" con icono de stop
- Ambos botones con estados disabled apropiados
- Layout responsive con flexbox

### 2. Frontend - JavaScript (`static/js/scraper-control.js`)

**Variable `manualConfig` actualizada:**
```javascript
manualConfig: {
    operacion: 'venta',
    tipo: 'departamento',
    max_pages: 10,
    max_properties: 0,  // NUEVO
    formato: 'json',
    scrape_details: true,
    verbose: false
}
```

**Nueva función `stopManualScraping()`:**
- Valida que exista `scrapingId` activo
- Solicita confirmación al usuario
- Envía petición POST a endpoint de cancelación
- Actualiza UI con mensaje de cancelación
- Refresca historial y ejecuciones activas

**Actualización de `runManualScraping()`:**
- Incluye `max_properties` en el request body
- Convierte a entero con `parseInt()`

### 3. Backend - Endpoint (`dashboard/routes.py`)

**Nuevo endpoint:**
```python
@bp.route('/api/scraper/executions/<execution_id>/cancel', methods=['POST'])
@login_required
def api_scraper_execution_cancel(execution_id):
```

**Funcionalidad:**
- Valida que la ejecución exista
- Solo cancela si el estado es "running"
- Registra usuario que canceló en logs
- Retorna success/error apropiado

### 4. Backend - Database (`db_loader.py`)

**Nuevo método `cancel_execution()`:**

**Validaciones:**
- Verifica que la ejecución exista
- Solo permite cancelar ejecuciones con status "running"

**Acciones:**
- Actualiza `status` a "cancelled"
- Establece `end_time` al momento actual
- Calcula `duration` en segundos
- Agrega log de nivel WARNING con mensaje de cancelación
- Commit de cambios en transacción

## API

### Endpoint de Cancelación

**URL:** `POST /api/scraper/executions/{execution_id}/cancel`

**Autenticación:** Requerida (login_required)

**Parámetros:**
- `execution_id` (path): ID de la ejecución a cancelar

**Respuesta exitosa (200):**
```json
{
  "success": true,
  "message": "Ejecución cancelada exitosamente"
}
```

**Respuesta error (400):**
```json
{
  "success": false,
  "error": "No se pudo cancelar la ejecución. Puede que ya haya finalizado."
}
```

**Respuesta error (500):**
```json
{
  "success": false,
  "error": "Mensaje de error técnico"
}
```

## Modelo de Datos

### Estado "cancelled"

Nuevo estado agregado a `ScraperExecution`:
- **running** → En ejecución
- **completed** → Completado exitosamente
- **failed** → Fallido con error
- **cancelled** → Cancelado por usuario ✨ NUEVO

### Campos actualizados al cancelar:
- `status`: "cancelled"
- `end_time`: Timestamp actual
- `duration`: Segundos desde start_time hasta end_time

### Log de cancelación:
- `level`: "WARNING"
- `message`: "Ejecución cancelada por el usuario"
- `source`: "dashboard"

## UI/UX

### Iconos SVG

**Botón Ejecutar:**
- Play icon (cuando no está ejecutando)
- Spinner animado (cuando está ejecutando)

**Botón Detener:**
- Stop icon (círculo con cuadrado)
- Color rojo (#dc2626)
- Disabled cuando no hay ejecución activa

### Estados de Botones

| Estado | Ejecutar | Detener |
|--------|----------|---------|
| Sin ejecución | Habilitado | Disabled |
| Ejecutando | Disabled | Habilitado |
| Completado | Habilitado | Disabled |

### Confirmaciones

**Al detener:**
```
¿Estás seguro de detener esta ejecución?
[Cancelar] [Aceptar]
```

## Testing

### Casos de Prueba

1. ✅ Selector de registros máximos se muestra correctamente
2. ✅ Valor por defecto es "Sin límite" (0)
3. ✅ Botón "Detener" está disabled al inicio
4. ✅ Botón "Detener" se habilita al iniciar scraping
5. ✅ Confirmación se muestra al hacer click en "Detener"
6. ✅ Cancelar confirmación no detiene la ejecución
7. ✅ Aceptar confirmación envía petición al backend
8. ✅ Estado se actualiza a "cancelled" en BD
9. ✅ Log de cancelación se registra
10. ✅ UI se actualiza mostrando mensaje de cancelación
11. ✅ Historial se refresca automáticamente
12. ✅ No se puede cancelar ejecución ya completada
13. ✅ max_properties se envía correctamente al backend

### Para Verificar en Producción

```bash
# 1. Iniciar scraping manual con límite de 100 registros
# 2. Verificar que botón "Detener" se habilita
# 3. Hacer click en "Detener" antes de completar
# 4. Confirmar cancelación
# 5. Verificar mensaje "Ejecución cancelada por el usuario"
# 6. Verificar en historial que estado es "Cancelado"
# 7. Verificar que duración se calculó correctamente
# 8. Verificar log de cancelación en BD
```

## Archivos Modificados

1. `templates/dashboard/scraper.html` - UI actualizada con nuevos controles
2. `static/js/scraper-control.js` - Lógica de cancelación agregada
3. `dashboard/routes.py` - Endpoint de cancelación agregado
4. `db_loader.py` - Método cancel_execution agregado

## Archivos Sin Cambios

1. `models/scraper_execution.py` - Modelo ya soporta status "cancelled"
2. `database.py` - Sin cambios necesarios
3. `scraper_selenium.py` - Sin cambios (respeta max_properties existente)

## Notas Técnicas

### Limitación Actual

El botón "Detener" actualiza el estado en la base de datos, pero **no detiene el proceso Python en ejecución**. El scraper continuará ejecutándose hasta completar la página actual.

### Mejora Futura

Para detener el proceso Python en tiempo real, se requiere:
1. Implementar verificación periódica del estado en `scraper_selenium.py`
2. Agregar flag de cancelación en memoria compartida o Redis
3. Verificar flag en cada iteración del loop de scraping
4. Salir gracefully si se detecta cancelación

### Workaround Actual

El estado "cancelled" en BD sirve para:
- Indicar al usuario que la ejecución fue cancelada
- Prevenir que se procesen los resultados
- Registrar en logs la acción del usuario
- Mostrar correctamente en historial

## Próximos Pasos

1. Implementar detención real del proceso Python
2. Agregar indicador de progreso con porcentaje
3. Agregar estimación de tiempo restante
4. Permitir pausar/reanudar ejecuciones
5. Agregar límite de tiempo máximo de ejecución
6. Implementar cola de ejecuciones
