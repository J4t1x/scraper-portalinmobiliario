# 🚀 Quick Start - Docker

Guía rápida para ejecutar el scraper con Docker.

## ⚡ Testing Local (5 minutos)

### 1. Iniciar Docker Desktop
```bash
# Asegúrate de que Docker Desktop está corriendo
docker info
```

### 2. Build de la imagen
```bash
cd /ruta/a/portalinmobiliario
docker build -t portalinmobiliario:latest .
```

### 3. Ejecutar test automatizado
```bash
./test-docker.sh
```

### 4. Ejecutar scraper de prueba
```bash
docker run --rm \
  -v $(pwd)/output:/app/output \
  portalinmobiliario:latest \
  python main.py --operacion venta --tipo departamento --max-pages 1
```

## 🐙 Con Docker Compose (incluye PostgreSQL)

### 1. Iniciar servicios
```bash
docker-compose up -d
```

### 2. Ejecutar scraper
```bash
docker-compose run --rm scraper \
  python main.py --operacion venta --tipo departamento --max-pages 2
```

### 3. Ver base de datos (Adminer)
Abrir en navegador: http://localhost:8080
- Sistema: PostgreSQL
- Servidor: postgres
- Usuario: scraper
- Contraseña: scraper123
- BD: portalinmobiliario

### 4. Detener servicios
```bash
docker-compose down
```

## 🚂 Deploy a Railway (10 minutos)

### 1. Subir a GitHub
```bash
git add .
git commit -m "feat(docker): configuración Docker y Railway"
git push origin main
```

### 2. Crear proyecto en Railway
1. Ir a https://railway.app/new
2. Seleccionar "Deploy from GitHub repo"
3. Autorizar y seleccionar `portalinmobiliario`
4. Railway detectará el Dockerfile automáticamente

### 3. Agregar PostgreSQL
1. En el dashboard, click "New" → "Database" → "PostgreSQL"
2. Copiar la variable `DATABASE_URL`

### 4. Configurar variables de entorno
En el servicio scraper, agregar:
- `DATABASE_URL` (copiar de PostgreSQL)
- `DELAY_BETWEEN_REQUESTS=2`
- `MAX_RETRIES=3`

### 5. Deploy
Railway desplegará automáticamente. Ver logs en tiempo real desde el dashboard.

## 📖 Documentación Completa

- **[DOCKER.md](DOCKER.md)** - Guía completa de Docker y Railway
- **[README.md](README.md)** - Documentación general del proyecto

## 🆘 Troubleshooting Rápido

**Docker no inicia:**
```bash
# Verificar que Docker Desktop está corriendo
docker info
```

**Error de permisos:**
```bash
chmod +x entrypoint.sh test-docker.sh
```

**Rebuild sin cache:**
```bash
docker build --no-cache -t portalinmobiliario:latest .
```

**Ver logs del contenedor:**
```bash
docker logs <container_id>
```
