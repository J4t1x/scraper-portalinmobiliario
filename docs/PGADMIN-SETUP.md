# pgAdmin - Configuración

## Acceso a pgAdmin

**URL**: http://localhost:4425

**Credenciales de Login**:
- Email: `admin@admin.com`
- Password: `admin123`

## Configurar Conexión a PostgreSQL

Una vez dentro de pgAdmin, sigue estos pasos para conectar a la base de datos:

### 1. Agregar Nuevo Servidor

1. Click derecho en "Servers" → "Register" → "Server..."

### 2. Pestaña "General"

- **Name**: `Portal Inmobiliario Local`

### 3. Pestaña "Connection"

- **Host name/address**: `postgres` (nombre del contenedor en la red Docker)
  - **Alternativa desde host**: `host.docker.internal` (si no funciona `postgres`)
- **Port**: `5432`
- **Maintenance database**: `portalinmobiliario`
- **Username**: `scraper`
- **Password**: `scraper123`
- ✅ **Save password**: Marcar esta opción

### 4. Guardar

Click en "Save" y deberías ver la base de datos conectada.

## Conexión desde Host (fuera de Docker)

Si quieres conectar desde una herramienta externa (DBeaver, DataGrip, etc.):

```
Host: localhost
Port: 4420
Database: portalinmobiliario
Username: scraper
Password: scraper123
```

## Comandos Docker

```bash
# Iniciar pgAdmin
docker-compose -f docker-compose.v2.yml --profile admin up -d pgadmin

# Detener pgAdmin
docker-compose -f docker-compose.v2.yml --profile admin stop pgadmin

# Ver logs
docker logs portalinmobiliario-pgadmin

# Reiniciar pgAdmin
docker-compose -f docker-compose.v2.yml --profile admin restart pgadmin
```

## Puertos del Proyecto

- **PostgreSQL**: localhost:4420
- **Dashboard**: localhost:4421
- **Redis**: localhost:4422
- **Ollama**: localhost:4423
- **Adminer**: localhost:4424
- **pgAdmin**: localhost:4425

## Notas

- pgAdmin se ejecuta con el profile `admin`
- Los datos de pgAdmin se persisten en el volumen `pgadmin-data`
- La configuración está en modo desktop (no requiere master password)
