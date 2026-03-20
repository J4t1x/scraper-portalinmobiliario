# 🐳 Docker - Portal Inmobiliario Scraper

Guía completa para ejecutar el scraper en contenedores Docker y desplegarlo en Railway.

## 📋 Tabla de Contenidos

- [Requisitos](#requisitos)
- [Construcción de la Imagen](#construcción-de-la-imagen)
- [Ejecución Local](#ejecución-local)
- [Docker Compose](#docker-compose)
- [Variables de Entorno](#variables-de-entorno)
- [Despliegue en Railway](#despliegue-en-railway)
- [Troubleshooting](#troubleshooting)

## 🔧 Requisitos

- Docker 20.10+
- Docker Compose 2.0+ (opcional, para testing local)
- 2GB RAM mínimo
- Conexión a internet

## 🏗️ Construcción de la Imagen

### Build básico

```bash
docker build -t portalinmobiliario:latest .
```

### Build con tag específico

```bash
docker build -t portalinmobiliario:v1.0.0 .
```

### Build sin cache (forzar rebuild completo)

```bash
docker build --no-cache -t portalinmobiliario:latest .
```

### Verificar la imagen creada

```bash
docker images | grep portalinmobiliario
```

## 🚀 Ejecución Local

### Ejecución básica (mostrar ayuda)

```bash
docker run --rm portalinmobiliario:latest
```

### Scrapear departamentos en venta

```bash
docker run --rm \
  -v $(pwd)/output:/app/output \
  portalinmobiliario:latest \
  python main.py --operacion venta --tipo departamento --max-pages 2
```

### Scrapear con formato JSON

```bash
docker run --rm \
  -v $(pwd)/output:/app/output \
  portalinmobiliario:latest \
  python main.py --operacion arriendo --tipo casa --formato json --max-pages 3
```

### Modo interactivo (para debugging)

```bash
docker run -it --rm \
  -v $(pwd)/output:/app/output \
  portalinmobiliario:latest \
  /bin/bash
```

### Con variables de entorno personalizadas

```bash
docker run --rm \
  -e DELAY_BETWEEN_REQUESTS=3 \
  -e MAX_RETRIES=5 \
  -v $(pwd)/output:/app/output \
  portalinmobiliario:latest \
  python main.py --operacion venta --tipo oficina
```

## 🐙 Docker Compose

Docker Compose incluye PostgreSQL para almacenamiento de datos.

### Iniciar servicios

```bash
docker-compose up -d
```

### Ver logs

```bash
# Todos los servicios
docker-compose logs -f

# Solo scraper
docker-compose logs -f scraper

# Solo PostgreSQL
docker-compose logs -f postgres
```

### Ejecutar scraper con docker-compose

```bash
docker-compose run --rm scraper \
  python main.py --operacion venta --tipo departamento --max-pages 2
```

### Acceder a la base de datos

**Usando Adminer (interfaz web):**
- URL: http://localhost:8080
- Sistema: PostgreSQL
- Servidor: postgres
- Usuario: scraper
- Contraseña: scraper123
- Base de datos: portalinmobiliario

**Usando psql:**

```bash
docker-compose exec postgres psql -U scraper -d portalinmobiliario
```

### Detener servicios

```bash
docker-compose down
```

### Detener y eliminar volúmenes

```bash
docker-compose down -v
```

## 🔐 Variables de Entorno

### Variables del Scraper

| Variable | Descripción | Default | Requerida |
|----------|-------------|---------|-----------|
| `DATABASE_URL` | URL de conexión PostgreSQL | - | No |
| `DELAY_BETWEEN_REQUESTS` | Segundos entre requests | `2` | No |
| `MAX_RETRIES` | Intentos máximos por página | `3` | No |
| `TIMEOUT` | Timeout de requests (segundos) | `30` | No |
| `USER_AGENT` | User agent personalizado | Mozilla/5.0... | No |

### Archivo .env (ejemplo)

Crear archivo `.env` en la raíz del proyecto:

```env
# Scraper Config
DELAY_BETWEEN_REQUESTS=2
MAX_RETRIES=3
TIMEOUT=30
USER_AGENT=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36

# Database (Railway)
DATABASE_URL=postgresql://user:password@host:5432/database
```

### Usar archivo .env con Docker

```bash
docker run --rm --env-file .env \
  -v $(pwd)/output:/app/output \
  portalinmobiliario:latest \
  python main.py --operacion venta --tipo departamento
```

## 🚂 Despliegue en Railway

### 1. Preparación

**a) Crear cuenta en Railway:**
- Ir a https://railway.app
- Crear cuenta con GitHub

**b) Instalar Railway CLI (opcional):**

```bash
npm install -g @railway/cli
railway login
```

### 2. Crear Proyecto en Railway

**Opción A: Desde la Web UI**

1. Ir a https://railway.app/new
2. Seleccionar "Deploy from GitHub repo"
3. Autorizar acceso a tu repositorio
4. Seleccionar el repositorio `portalinmobiliario`
5. Railway detectará automáticamente el Dockerfile

**Opción B: Desde CLI**

```bash
cd /ruta/a/portalinmobiliario
railway init
railway up
```

### 3. Configurar PostgreSQL en Railway

1. En el dashboard del proyecto, click en "New"
2. Seleccionar "Database" → "PostgreSQL"
3. Railway creará automáticamente la base de datos
4. Copiar la variable `DATABASE_URL` generada

### 4. Configurar Variables de Entorno

En el dashboard de Railway:

1. Ir a tu servicio (scraper)
2. Click en "Variables"
3. Agregar:
   - `DATABASE_URL` (copiar de la BD PostgreSQL)
   - `DELAY_BETWEEN_REQUESTS=2`
   - `MAX_RETRIES=3`
   - `TIMEOUT=30`

### 5. Configurar Comando de Inicio

Railway necesita saber cómo ejecutar el scraper.

**Opción 1: Crear archivo `railway.json`**

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "startCommand": "python main.py --operacion venta --tipo departamento --formato json --max-pages 5",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 3
  }
}
```

**Opción 2: Configurar en Railway UI**

1. Ir a Settings → Deploy
2. En "Custom Start Command" agregar:
   ```
   python main.py --operacion venta --tipo departamento --formato json
   ```

### 6. Deploy

**Desde GitHub (recomendado):**

1. Push a tu repositorio:
   ```bash
   git add .
   git commit -m "feat(docker): agregar configuración Docker y Railway"
   git push origin main
   ```

2. Railway desplegará automáticamente

**Desde CLI:**

```bash
railway up
```

### 7. Monitoreo

**Ver logs en tiempo real:**

```bash
railway logs
```

**Desde la UI:**
- Ir a tu proyecto en Railway
- Click en el servicio
- Ver pestaña "Deployments" y "Logs"

### 8. Ejecutar Scraper On-Demand

Como el scraper no es un servicio web continuo, puedes:

**Opción A: Usar Railway CLI**

```bash
railway run python main.py --operacion arriendo --tipo casa --max-pages 3
```

**Opción B: Configurar Cron Jobs**

Railway no tiene cron nativo, pero puedes:
1. Usar un servicio externo como cron-job.org
2. Crear un endpoint HTTP simple que ejecute el scraper
3. Usar GitHub Actions para trigger el scraper

### 9. Costos Estimados

Railway ofrece:
- **Plan Free:** $5 USD de crédito mensual
- **Plan Developer:** $5 USD/mes + uso
- PostgreSQL consume ~$0.50/mes en plan básico

**Estimación para este proyecto:**
- Scraper (ejecuciones esporádicas): ~$1-2/mes
- PostgreSQL: ~$0.50/mes
- **Total:** ~$1.50-2.50/mes

## 🐛 Troubleshooting

### Error: Chrome no se puede iniciar

**Síntoma:**
```
selenium.common.exceptions.WebDriverException: Message: unknown error: Chrome failed to start
```

**Solución:**
Asegurarse que el contenedor tiene suficiente memoria (mínimo 2GB):

```bash
docker run --rm -m 2g \
  portalinmobiliario:latest \
  python main.py --operacion venta --tipo departamento
```

### Error: ChromeDriver version mismatch

**Síntoma:**
```
SessionNotCreatedException: Message: session not created: This version of ChromeDriver only supports Chrome version XX
```

**Solución:**
Rebuild la imagen sin cache:

```bash
docker build --no-cache -t portalinmobiliario:latest .
```

### Error: Permission denied en /app/output

**Síntoma:**
```
PermissionError: [Errno 13] Permission denied: '/app/output/...'
```

**Solución:**
Dar permisos al directorio output:

```bash
chmod -R 777 output/
```

O ejecutar con usuario root (no recomendado):

```bash
docker run --rm --user root \
  -v $(pwd)/output:/app/output \
  portalinmobiliario:latest \
  python main.py --operacion venta --tipo departamento
```

### Error: Database connection failed

**Síntoma:**
```
psycopg2.OperationalError: could not connect to server
```

**Solución:**
Verificar que `DATABASE_URL` está correctamente configurada:

```bash
docker-compose exec scraper env | grep DATABASE_URL
```

### Contenedor se detiene inmediatamente

**Síntoma:**
El contenedor ejecuta y se detiene sin output.

**Solución:**
Ver logs del contenedor:

```bash
docker logs <container_id>
```

Ejecutar en modo interactivo para debugging:

```bash
docker run -it --rm portalinmobiliario:latest /bin/bash
```

### Build muy lento

**Causa:**
Instalación de Chrome y ChromeDriver toma tiempo.

**Solución:**
Usar cache de Docker layers. Solo rebuild cuando sea necesario.

### Railway: Out of Memory

**Síntoma:**
Contenedor se reinicia constantemente en Railway.

**Solución:**
1. Ir a Settings en Railway
2. Aumentar memoria asignada (mínimo 2GB)
3. Optimizar opciones de Chrome en `scraper_selenium.py`:

```python
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--no-sandbox')
options.add_argument('--disable-gpu')
```

## 📚 Recursos Adicionales

- [Docker Documentation](https://docs.docker.com/)
- [Railway Documentation](https://docs.railway.app/)
- [Selenium with Docker](https://www.selenium.dev/documentation/grid/getting_started/)
- [PostgreSQL Docker](https://hub.docker.com/_/postgres)

## 🤝 Soporte

Para problemas o preguntas:
1. Revisar esta documentación
2. Verificar logs: `docker logs <container>`
3. Abrir issue en el repositorio
