# PRD - Fase 3: Versión Pro

**Versión:** 1.0  
**Fecha:** 8 de Abril, 2026  
**Estado:** Planificación  
**Owner:** Equipo de Desarrollo

---

## 1. Resumen Ejecutivo

### 1.1 Objetivo
Transformar el scraper en una solución profesional con almacenamiento persistente, automatización, monitoreo y dashboard analítico para análisis de mercado inmobiliario.

### 1.2 Alcance
- Almacenamiento en PostgreSQL con modelo relacional
- Scheduler para scraping automático (cron jobs)
- Dashboard de monitoreo con métricas en tiempo real
- Sistema de notificaciones de errores
- Cache de resultados para optimización
- API REST para acceso programático

### 1.3 Métricas de Éxito
- **Uptime:** ≥99% del scheduler
- **Latencia API:** <200ms p95
- **Cache hit rate:** ≥70%
- **Notificaciones:** 100% de errores críticos notificados
- **Datos históricos:** ≥6 meses de datos almacenados

---

## 2. Contexto y Motivación

### 2.1 Problema Actual
La Fase 2 mejoró la calidad de datos, pero el sistema sigue siendo:
- **Manual:** Requiere ejecución manual del scraper
- **Efímero:** Datos solo en archivos (sin persistencia estructurada)
- **No monitoreable:** Sin visibilidad del estado del sistema
- **Aislado:** No hay forma de acceder a datos programáticamente
- **Ineficiente:** Re-scraping completo en cada ejecución

### 2.2 Oportunidad
Convertir el scraper en una plataforma profesional que permita:
- Análisis de tendencias de mercado (precios, oferta, demanda)
- Detección automática de oportunidades de inversión
- Integración con otros sistemas (CRM, analytics)
- Monitoreo proactivo y alertas
- Optimización de recursos (cache, scraping incremental)

### 2.3 Stakeholders
- **Analistas de datos:** Acceso a datos históricos y tendencias
- **Inversores:** Alertas de oportunidades
- **Desarrolladores:** API para integración
- **DevOps:** Dashboard de monitoreo
- **Product Owner:** Métricas de negocio

---

## 3. Especificaciones Funcionales

### 3.1 Feature 1: Almacenamiento PostgreSQL

**Descripción:** Diseñar e implementar modelo de datos relacional para almacenar propiedades y metadatos.

**Modelo de Datos:**

```sql
-- Tabla principal de propiedades
properties (
  id VARCHAR(50) PRIMARY KEY,
  titulo TEXT NOT NULL,
  headline VARCHAR(200),
  precio_texto VARCHAR(100),
  precio_numerico DECIMAL(15,2),
  moneda VARCHAR(10),
  ubicacion TEXT,
  comuna VARCHAR(100),
  sector VARCHAR(100),
  operacion VARCHAR(50),
  tipo VARCHAR(50),
  dormitorios INT,
  banos INT,
  metros_utiles DECIMAL(10,2),
  descripcion TEXT,
  publicador_nombre VARCHAR(200),
  publicador_tipo VARCHAR(50),
  url TEXT,
  fecha_publicacion TIMESTAMP,
  fecha_scraping TIMESTAMP DEFAULT NOW(),
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
)

-- Tabla de imágenes
property_images (
  id SERIAL PRIMARY KEY,
  property_id VARCHAR(50) REFERENCES properties(id),
  url TEXT NOT NULL,
  orden INT,
  created_at TIMESTAMP DEFAULT NOW()
)

-- Tabla de historial de precios
price_history (
  id SERIAL PRIMARY KEY,
  property_id VARCHAR(50) REFERENCES properties(id),
  precio_numerico DECIMAL(15,2),
  moneda VARCHAR(10),
  fecha TIMESTAMP DEFAULT NOW()
)

-- Tabla de ejecuciones de scraping
scraping_runs (
  id SERIAL PRIMARY KEY,
  operacion VARCHAR(50),
  tipo VARCHAR(50),
  total_propiedades INT,
  nuevas INT,
  actualizadas INT,
  errores INT,
  duracion_segundos INT,
  status VARCHAR(50),
  started_at TIMESTAMP,
  finished_at TIMESTAMP
)
```

**Funcionalidades:**
- Inserción de nuevas propiedades
- Actualización de propiedades existentes
- Tracking de cambios de precio
- Soft delete (marcar como inactivas)
- Queries optimizadas con índices

**Prioridad:** Crítica  
**Estimación:** 12 horas

---

### 3.2 Feature 2: Scheduler Automático

**Descripción:** Sistema de cron jobs para scraping automático y mantenimiento.

**Jobs Programados:**

1. **Scraping Incremental** (cada 6 horas)
   - Scrapear solo primeras 5 páginas de cada tipo
   - Detectar propiedades nuevas
   - Actualizar propiedades existentes

2. **Scraping Completo** (diario, 3 AM)
   - Scrapear todas las páginas
   - Actualizar base de datos completa
   - Generar reporte de cambios

3. **Limpieza de Datos** (semanal, domingo 2 AM)
   - Marcar propiedades inactivas (no vistas en 7 días)
   - Comprimir logs antiguos
   - Limpiar cache expirado

4. **Health Check** (cada 15 minutos)
   - Verificar conectividad a DB
   - Verificar disponibilidad de Portal Inmobiliario
   - Enviar alerta si hay problemas

**Tecnología:**
- APScheduler (Python) o Celery Beat
- Configuración via YAML
- Logs de ejecución en DB

**Prioridad:** Alta  
**Estimación:** 8 horas

---

### 3.3 Feature 3: Dashboard de Monitoreo

**Descripción:** Dashboard web con métricas en tiempo real y visualizaciones.

**Secciones:**

1. **Overview**
   - Total de propiedades en DB
   - Propiedades activas vs inactivas
   - Última ejecución de scraping
   - Estado del sistema (healthy/degraded/down)

2. **Métricas de Scraping**
   - Propiedades scrapeadas (últimas 24h, 7d, 30d)
   - Tasa de éxito/error
   - Tiempo promedio de ejecución
   - Gráfico de tendencia

3. **Métricas de Datos**
   - Distribución por tipo de propiedad
   - Distribución por operación
   - Distribución por comuna
   - Rango de precios

4. **Performance**
   - Tiempo de respuesta de API
   - Cache hit rate
   - Uso de recursos (CPU, memoria, disco)

5. **Logs y Errores**
   - Últimos errores
   - Logs en tiempo real (WebSocket)
   - Filtros por nivel y módulo

**Stack:**
- Backend: Flask (ya existente)
- Frontend: Chart.js + TailwindCSS
- WebSocket: Flask-SocketIO (ya existente)

**Prioridad:** Alta  
**Estimación:** 16 horas

---

### 3.4 Feature 4: Sistema de Notificaciones

**Descripción:** Envío automático de notificaciones por email/Slack cuando ocurren eventos importantes.

**Eventos a Notificar:**

1. **Errores Críticos**
   - Scraping fallido (3 intentos)
   - Base de datos no disponible
   - Disco lleno (>90%)

2. **Alertas de Negocio**
   - Nueva propiedad con precio bajo mercado
   - Cambio significativo de precio (>10%)
   - Propiedad en ubicación de interés

3. **Reportes Programados**
   - Resumen diario de scraping
   - Reporte semanal de tendencias
   - Reporte mensual de mercado

**Canales:**
- Email (SMTP)
- Slack (Webhook)
- Telegram (Bot API)

**Configuración:**
- Reglas de alertas en YAML
- Templates de mensajes
- Rate limiting (evitar spam)

**Prioridad:** Media  
**Estimación:** 8 horas

---

### 3.5 Feature 5: Sistema de Cache

**Descripción:** Cache de resultados para optimizar performance y reducir carga en DB.

**Estrategia:**

1. **Cache de Queries**
   - Queries frecuentes (últimas propiedades, stats)
   - TTL: 5 minutos
   - Invalidación automática al insertar datos

2. **Cache de API Responses**
   - Endpoints de lectura
   - TTL: 1 minuto
   - Headers de cache (ETag, Last-Modified)

3. **Cache de Scraping**
   - Páginas ya scrapeadas (mismo día)
   - Evitar re-scraping innecesario
   - TTL: 6 horas

**Tecnología:**
- Redis (producción)
- In-memory dict (desarrollo)

**Prioridad:** Media  
**Estimación:** 6 horas

---

### 3.6 Feature 6: API REST

**Descripción:** API REST para acceso programático a datos de propiedades.

**Endpoints:**

```
GET /api/v1/properties
  - Listar propiedades con paginación
  - Filtros: tipo, operacion, comuna, precio_min, precio_max
  - Ordenamiento: precio, fecha, relevancia
  - Response: JSON con metadata de paginación

GET /api/v1/properties/{id}
  - Detalle de propiedad específica
  - Incluye imágenes e historial de precios

GET /api/v1/stats
  - Estadísticas generales
  - Distribuciones, promedios, tendencias

GET /api/v1/trends
  - Tendencias de mercado
  - Evolución de precios por tipo/comuna
  - Oferta/demanda

GET /api/v1/health
  - Estado del sistema
  - Última ejecución de scraping
  - Métricas de performance
```

**Características:**
- Autenticación con API Key
- Rate limiting (100 req/min)
- Documentación con Swagger/OpenAPI
- CORS configurado
- Versionado de API

**Prioridad:** Alta  
**Estimación:** 12 horas

---

## 4. Especificaciones No Funcionales

### 4.1 Performance
- API response time: <200ms (p95)
- Dashboard load time: <2s
- Scraping completo: <30 minutos
- Cache hit rate: ≥70%

### 4.2 Confiabilidad
- Uptime del scheduler: ≥99%
- Retry automático en errores transitorios
- Fallback a cache en caso de DB down
- Backup diario de base de datos

### 4.3 Seguridad
- API Key para autenticación
- Rate limiting para prevenir abuso
- Sanitización de inputs
- Secrets en variables de entorno

### 4.4 Escalabilidad
- DB preparado para millones de registros
- Cache distribuido (Redis Cluster)
- API stateless (horizontal scaling)
- Scheduler con workers paralelos

---

## 5. Arquitectura

### 5.1 Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────┐
│                    USERS / CLIENTS                       │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                   NGINX / LOAD BALANCER                  │
└─────────────────────────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
    ┌─────────┐    ┌──────────┐    ┌──────────┐
    │   API   │    │ Dashboard│    │ WebSocket│
    │ (Flask) │    │ (Flask)  │    │  Server  │
    └─────────┘    └──────────┘    └──────────┘
          │               │               │
          └───────────────┼───────────────┘
                          ▼
              ┌───────────────────────┐
              │   REDIS CACHE         │
              └───────────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │   POSTGRESQL DB       │
              │   - properties        │
              │   - images            │
              │   - price_history     │
              │   - scraping_runs     │
              └───────────────────────┘
                          ▲
                          │
              ┌───────────────────────┐
              │   SCHEDULER           │
              │   (APScheduler)       │
              │   - Scraping jobs     │
              │   - Maintenance       │
              │   - Health checks     │
              └───────────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │   SCRAPER ENGINE      │
              │   (Selenium)          │
              └───────────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │   NOTIFICATION        │
              │   SERVICE             │
              │   - Email             │
              │   - Slack             │
              └───────────────────────┘
```

### 5.2 Stack Tecnológico

| Componente | Tecnología | Versión |
|------------|------------|---------|
| Base de Datos | PostgreSQL | 16+ |
| Cache | Redis | 7+ |
| Backend | Flask | 3.0+ |
| Scheduler | APScheduler | 3.10+ |
| ORM | SQLAlchemy | 2.0+ |
| API Docs | Flask-RESTX | 1.3+ |
| WebSocket | Flask-SocketIO | 5.3+ |
| Scraper | Selenium | 4.18+ |
| Charts | Chart.js | 4.4+ |
| Notifications | smtplib, requests | - |

---

## 6. Plan de Implementación

### 6.1 Fases

#### Fase 3.1: Persistencia (Sprint 1-2)
- SPEC-008: Modelo de datos PostgreSQL
- SPEC-009: Migración de datos existentes
- SPEC-010: ORM con SQLAlchemy

#### Fase 3.2: Automatización (Sprint 3)
- SPEC-011: Scheduler con APScheduler
- SPEC-012: Jobs de scraping automático
- SPEC-013: Jobs de mantenimiento

#### Fase 3.3: API y Cache (Sprint 4)
- SPEC-014: API REST con Flask-RESTX
- SPEC-015: Sistema de cache con Redis
- SPEC-016: Documentación de API

#### Fase 3.4: Monitoreo (Sprint 5)
- SPEC-017: Dashboard de monitoreo
- SPEC-018: Sistema de notificaciones
- SPEC-019: Health checks

### 6.2 Timeline
- **Sprint 1-2:** 4 semanas (Persistencia)
- **Sprint 3:** 2 semanas (Automatización)
- **Sprint 4:** 2 semanas (API y Cache)
- **Sprint 5:** 2 semanas (Monitoreo)
- **Total:** 10 semanas

---

## 7. Dependencias

### 7.1 Nuevas Dependencias Python
```
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.0
redis>=5.0.0
apscheduler>=3.10.0
flask-restx>=1.3.0
flask-sqlalchemy>=3.1.0
flask-migrate>=4.0.0
```

### 7.2 Infraestructura
- PostgreSQL 16+ (Railway o local)
- Redis 7+ (Railway o local)
- SMTP server (Gmail, SendGrid)
- Slack Workspace (para notificaciones)

---

## 8. Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Migración de datos falla | Baja | Alto | Backup completo antes de migrar |
| Redis no disponible | Media | Medio | Fallback a in-memory cache |
| Scheduler se cae | Baja | Alto | Monitoreo con health checks |
| API sobrecargada | Media | Medio | Rate limiting + cache agresivo |
| Costos de infraestructura | Alta | Medio | Optimizar queries, usar cache |

---

## 9. Criterios de Aceptación

### 9.1 Feature Completo
- [ ] PostgreSQL con modelo completo implementado
- [ ] Scheduler ejecutando jobs automáticamente
- [ ] API REST funcionando con documentación
- [ ] Dashboard mostrando métricas en tiempo real
- [ ] Notificaciones enviándose correctamente
- [ ] Cache funcionando con hit rate ≥70%

### 9.2 Calidad
- [ ] Tests de integración con DB
- [ ] Tests de API (endpoints)
- [ ] Load testing de API (100 req/s)
- [ ] Documentación completa
- [ ] Code review aprobado

### 9.3 Deployment
- [ ] Docker Compose con todos los servicios
- [ ] Railway deployment con PostgreSQL + Redis
- [ ] Variables de entorno documentadas
- [ ] Backup automático configurado
- [ ] Monitoreo en producción

---

## 10. Métricas de Seguimiento

### 10.1 Técnicas
- Uptime del scheduler
- Latencia de API (p50, p95, p99)
- Cache hit rate
- Tamaño de base de datos
- Tiempo de ejecución de scraping

### 10.2 Negocio
- Total de propiedades en DB
- Propiedades nuevas por día
- Cambios de precio detectados
- Alertas enviadas
- Usuarios de API (si se implementa registro)

---

## 11. Referencias

- [PRD Fase 2](./PRD-FASE-2-MEJORAS.md) - Mejoras completadas
- [README.md](../../README.md) - Documentación principal
- [Docker Compose](../../docker-compose.yml) - Configuración actual
- [SDD Methodology](../../../SDD-jard/docs/SDD-METHODOLOGY.md)

---

## 12. Aprobaciones

| Rol | Nombre | Fecha | Estado |
|-----|--------|-------|--------|
| Product Owner | - | - | Pendiente |
| Tech Lead | - | - | Pendiente |
| DevOps Lead | - | - | Pendiente |
| Data Lead | - | - | Pendiente |

---

**Última actualización:** 8 de Abril, 2026  
**Próxima revisión:** Al completar Fase 2
