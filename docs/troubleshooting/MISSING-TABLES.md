# Error: Tabla `opportunities` no existe

## Problema

```
sqlalchemy.exc.ProgrammingError: (psycopg2.errors.UndefinedTable) relation "opportunities" does not exist
```

Este error ocurre cuando las tablas de la base de datos no han sido creadas.

## Causa

Las tablas no se crean automáticamente en Railway. Necesitas ejecutar el script de inicialización después del primer deploy.

## Solución

### Opción 1: Base de Datos Local (PostgreSQL en Docker)

```bash
# Con el contenedor portalinmobiliario-db corriendo
cd /Users/ja/Documents/GitHub/scraper-portalinmobiliario
./init-db-local.sh
```

### Opción 2: Usando Railway CLI (Producción)

```bash
# Desde tu máquina local
cd /Users/ja/Documents/GitHub/scraper-portalinmobiliario
railway run bash railway-init-db.sh
```

### Opción 3: Usando manage.sh

```bash
# Detecta automáticamente si usas contenedor único o PostgreSQL separado
./manage.sh init-db
```

### Opción 4: Ejecutar manualmente en Railway

```bash
# Conectarse a Railway y ejecutar
railway run python init_db.py
```

## Verificación

Después de ejecutar el script, verifica que las tablas se hayan creado:

```bash
# Conectarse a la base de datos
railway run psql $DATABASE_URL

# Listar tablas
\dt

# Deberías ver:
# - properties
# - features
# - images
# - publishers
# - opportunities
# - analytics_cache
# - scheduler_executions
# - scheduler_state
# - scraper_executions
# - scraper_logs
```

## Prevención

Este script solo necesita ejecutarse una vez después del primer deploy. Las tablas persistirán en la base de datos de Railway.

## Tablas Creadas

El script `init_db.py` crea las siguientes tablas:

1. **properties** - Propiedades scrapeadas
2. **features** - Características de las propiedades
3. **images** - Imágenes de las propiedades
4. **publishers** - Información de publicadores
5. **opportunities** - Oportunidades de inversión detectadas
6. **analytics_cache** - Cache de analítica
7. **scheduler_executions** - Historial de ejecuciones programadas
8. **scheduler_state** - Estado del scheduler
9. **scraper_executions** - Historial de ejecuciones del scraper
10. **scraper_logs** - Logs del scraper

## Archivos Relacionados

- `init_db.py` - Script de inicialización
- `railway-init-db.sh` - Script wrapper para Railway
- `manage.sh` - Script de gestión (comando `init-db`)
- `database.py` - Configuración de la base de datos
- `models/` - Definiciones de modelos SQLAlchemy
