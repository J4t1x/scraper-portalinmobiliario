# MVP Analytics - Quick Start Guide

## 🚀 Inicio Rápido

### Prerequisitos
- Docker instalado
- **Nota:** Ollama está incluido en el contenedor MVP (no requiere instalación local)

### Opción 1: Deployment Automatizado (Recomendado)

```bash
# Deployment completo con verificación de servicios
./scripts/deploy-mvp.sh
```

Este script:
- ✅ Limpia contenedores anteriores
- ✅ Construye la imagen (10-15 min)
- ✅ Crea volúmenes necesarios
- ✅ Inicia el contenedor
- ✅ Verifica todos los servicios
- ✅ Muestra URLs y comandos útiles

### Opción 2: Deployment en Background

```bash
# Inicia build en background (no bloquea terminal)
./scripts/quick-deploy.sh

# Monitorear progreso
tail -f /tmp/mvp-build.log

# Cuando termine, iniciar contenedor
./scripts/start-container.sh
```

### Opción 3: Manual

```bash
# Build
docker build -f Dockerfile.mvp -t portalinmobiliario:mvp .

# Run
docker run -d \
  --name scraper-mvp \
  -p 5000:5000 \
  -p 11434:11434 \
  -v $(pwd)/output:/app/output \
  -v ollama-models:/app/.ollama/models \
  portalinmobiliario:mvp
```

**Nota:** El contenedor incluye:
- PostgreSQL en puerto interno 5432
- Flask en puerto 5000 (expuesto)
- Ollama en puerto 11434 (expuesto)
- Modelo pre-descargado: `qwen2.5-coder:1.5b`

### 3. Verificar Estado

```bash
# Verificar todos los servicios (script automático)
./scripts/check-services.sh

# O manualmente:

# Health check Flask
curl http://localhost:5000/health

# Verificar Ollama
curl http://localhost:11434/api/tags

# Estado de todos los servicios
docker exec scraper-mvp supervisorctl status

# Ver logs
docker logs -f scraper-mvp
```

## 📊 Ejecutar Pipeline de Analítica

### Opción 1: Desde el contenedor

```bash
docker exec scraper-mvp python analytics.py
```

### Opción 2: Vía API

```bash
curl -X POST http://localhost:5000/api/v2/opportunities/run-analytics \
  -H "X-API-KEY: your-api-key"
```

## 🔍 Consultar Oportunidades

### Ver top 20 oportunidades

```bash
curl http://localhost:5000/api/v2/opportunities/ \
  -H "X-API-KEY: your-api-key"
```

### Filtrar por comuna

```bash
curl "http://localhost:5000/api/v2/opportunities/?comuna=Las%20Condes" \
  -H "X-API-KEY: your-api-key"
```

### Ver estadísticas

```bash
curl http://localhost:5000/api/v2/opportunities/stats \
  -H "X-API-KEY: your-api-key"
```

## 🤖 Chat con Agente IA

```bash
curl -X POST http://localhost:5000/api/v2/agent/chat \
  -H "X-API-KEY: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"question": "¿Cuáles son las mejores oportunidades de inversión?"}'
```

## 🗄️ Ejecutar Scraping

```bash
docker exec scraper-mvp python main.py \
  --operacion venta \
  --tipo departamento \
  --max-pages 2
```

## 📈 Métricas y Monitoreo

### Ver uso de recursos

```bash
docker stats scraper-mvp
```

### Ver logs de PostgreSQL

```bash
docker exec scraper-mvp tail -f /var/log/postgresql.log
```

### Ver logs de Flask

```bash
docker exec scraper-mvp tail -f /var/log/flask.log
```

## 🛠️ Troubleshooting

### PostgreSQL no inicia

```bash
docker exec -it scraper-mvp bash
su - postgres
/etc/init.d/postgresql start
```

### Flask no responde

```bash
docker exec scraper-mvp supervisorctl status
docker exec scraper-mvp supervisorctl restart flask
```

### Ollama no responde

Verifica que Ollama esté corriendo dentro del contenedor:

```bash
# Ver logs de Ollama
docker exec scraper-mvp tail -f /var/log/ollama.log

# Reiniciar Ollama
docker exec scraper-mvp supervisorctl restart ollama

# Verificar modelos disponibles
docker exec scraper-mvp ollama list
```

## 📚 Endpoints Disponibles

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/v2/opportunities/` | GET | Listar oportunidades |
| `/api/v2/opportunities/stats` | GET | Estadísticas de oportunidades |
| `/api/v2/opportunities/run-analytics` | POST | Ejecutar pipeline de analítica |
| `/api/v2/agent/chat` | POST | Chat con agente IA |
| `/api/v2/properties/` | GET | Listar propiedades |
| `/api/v2/analytics/stats` | GET | Estadísticas generales |

## 🔐 Configuración de API Key

Edita el archivo `.env` en el contenedor:

```bash
docker exec -it scraper-mvp bash
echo "API_KEY=mi-clave-secreta" >> .env
supervisorctl restart flask
```

## 🎯 Próximos Pasos

1. Ejecutar scraping inicial
2. Ejecutar pipeline de analítica
3. Consultar oportunidades vía API
4. Probar chat con agente IA
5. Configurar scraping automático con scheduler
