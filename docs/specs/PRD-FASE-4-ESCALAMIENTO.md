# PRD - Fase 4: Escalamiento y Machine Learning

**Versión:** 1.0  
**Fecha:** 8 de Abril, 2026  
**Estado:** Planificación  
**Owner:** Equipo de Desarrollo

---

## 1. Resumen Ejecutivo

### 1.1 Objetivo
Escalar el sistema a nivel empresarial con scraping distribuido, machine learning para predicción de precios, dashboard analítico avanzado y integración multi-plataforma.

### 1.2 Alcance
- Scraping distribuido con Celery
- API REST profesional con FastAPI
- Dashboard analítico con BI avanzado
- Sistema de alertas inteligentes
- Machine Learning para predicción de precios
- Integración con múltiples plataformas inmobiliarias
- Mobile app (opcional)

### 1.3 Métricas de Éxito
- **Throughput:** 10,000+ propiedades/hora
- **Precisión ML:** ≥85% en predicción de precios
- **Usuarios activos:** 100+ usuarios concurrentes
- **Plataformas:** ≥3 portales inmobiliarios integrados
- **Alertas inteligentes:** ≥90% de precisión

---

## 2. Contexto y Motivación

### 2.1 Problema Actual
La Fase 3 creó una solución profesional, pero limitada en:
- **Escala:** Scraping secuencial (lento para grandes volúmenes)
- **Inteligencia:** Sin análisis predictivo ni insights automáticos
- **Alcance:** Solo Portal Inmobiliario (mercado fragmentado)
- **UX:** Dashboard básico sin analytics avanzado
- **Acceso:** Solo web (sin mobile app)

### 2.2 Oportunidad
Crear una plataforma empresarial que permita:
- Análisis de mercado inmobiliario a escala nacional
- Predicción de precios y tendencias con ML
- Detección automática de oportunidades de inversión
- Comparación multi-plataforma (Portal, Yapo, Toctoc, etc.)
- Insights accionables para inversores y analistas

### 2.3 Stakeholders
- **Inversores profesionales:** Análisis avanzado y alertas
- **Inmobiliarias:** Inteligencia de mercado
- **Analistas de datos:** Acceso a datos históricos y modelos ML
- **Desarrolladores:** API robusta para integraciones
- **Product Owner:** Métricas de negocio y crecimiento

---

## 3. Especificaciones Funcionales

### 3.1 Feature 1: Scraping Distribuido con Celery

**Descripción:** Sistema de scraping distribuido con workers paralelos para maximizar throughput.

**Arquitectura:**

```
┌─────────────────────────────────────────────────────────┐
│                   CELERY BEAT                            │
│              (Scheduler Maestro)                         │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                   REDIS BROKER                           │
│              (Cola de Tareas)                            │
└─────────────────────────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┬───────────────┐
          ▼               ▼               ▼               ▼
    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
    │ Worker 1│    │ Worker 2│    │ Worker 3│    │ Worker N│
    │(Selenium)│    │(Selenium)│    │(Selenium)│    │(Selenium)│
    └─────────┘    └─────────┘    └─────────┘    └─────────┘
          │               │               │               │
          └───────────────┴───────────────┴───────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │   POSTGRESQL DB       │
              └───────────────────────┘
```

**Tareas Distribuidas:**

1. **scrape_listing_page**
   - Input: URL de página de listado
   - Output: Lista de IDs de propiedades
   - Paralelización: Por página

2. **scrape_property_detail**
   - Input: ID de propiedad
   - Output: Datos completos de propiedad
   - Paralelización: Por propiedad

3. **process_property_data**
   - Input: Datos crudos de propiedad
   - Output: Datos validados y enriquecidos
   - Paralelización: Por propiedad

4. **update_database**
   - Input: Datos procesados
   - Output: Registro en DB
   - Batch inserts para eficiencia

**Configuración:**
- Workers: 4-8 (según recursos)
- Concurrency: 2 por worker
- Rate limiting: 10 req/s por worker
- Retry: 3 intentos con backoff exponencial
- Timeout: 30s por tarea

**Prioridad:** Crítica  
**Estimación:** 16 horas

---

### 3.2 Feature 2: API REST con FastAPI

**Descripción:** Migrar API de Flask a FastAPI para mejor performance, validación automática y documentación interactiva.

**Mejoras sobre Flask:**
- Validación automática con Pydantic
- Async/await para mejor concurrencia
- Documentación automática (OpenAPI + Swagger)
- WebSocket nativo
- Mejor performance (2-3x más rápido)

**Endpoints Principales:**

```python
# Properties
GET    /api/v2/properties              # Listar con filtros avanzados
GET    /api/v2/properties/{id}         # Detalle
POST   /api/v2/properties/search       # Búsqueda avanzada
GET    /api/v2/properties/{id}/similar # Propiedades similares (ML)

# Analytics
GET    /api/v2/analytics/trends        # Tendencias de mercado
GET    /api/v2/analytics/heatmap       # Mapa de calor de precios
GET    /api/v2/analytics/forecast      # Predicción de precios (ML)
GET    /api/v2/analytics/insights      # Insights automáticos

# Alerts
GET    /api/v2/alerts                  # Listar alertas
POST   /api/v2/alerts                  # Crear alerta
PUT    /api/v2/alerts/{id}             # Actualizar
DELETE /api/v2/alerts/{id}             # Eliminar

# Admin
GET    /api/v2/admin/stats             # Estadísticas del sistema
GET    /api/v2/admin/jobs              # Estado de jobs de scraping
POST   /api/v2/admin/jobs/trigger      # Disparar scraping manual
```

**Características:**
- Autenticación JWT
- Rate limiting por usuario
- Paginación cursor-based
- Filtros avanzados (GraphQL-like)
- Compresión de responses (gzip)
- CORS configurado
- Versionado de API (v2)

**Prioridad:** Alta  
**Estimación:** 20 horas

---

### 3.3 Feature 3: Dashboard Analítico Avanzado

**Descripción:** Dashboard de Business Intelligence con visualizaciones avanzadas y análisis de mercado.

**Módulos:**

#### 3.3.1 Market Overview
- Mapa interactivo con heatmap de precios
- Distribución de propiedades por comuna
- Evolución de oferta/demanda
- Precio promedio por m² (tendencia)
- Tiempo promedio en el mercado

#### 3.3.2 Price Analysis
- Distribución de precios (histograma)
- Precio vs características (scatter plots)
- Comparación por tipo de propiedad
- Outliers y oportunidades
- Predicción de precios (ML)

#### 3.3.3 Trends & Forecasting
- Tendencias históricas (últimos 6-12 meses)
- Estacionalidad del mercado
- Predicción de precios futuros
- Análisis de correlaciones
- Indicadores de mercado (oferta/demanda)

#### 3.3.4 Investment Opportunities
- Propiedades subvaloradas (ML)
- ROI estimado por propiedad
- Zonas con mayor potencial
- Alertas de oportunidades
- Comparación con mercado

#### 3.3.5 Custom Reports
- Generador de reportes personalizados
- Export a PDF/Excel
- Programación de reportes
- Compartir con stakeholders

**Stack:**
- Frontend: React + TypeScript
- Charts: D3.js + Recharts
- Maps: Mapbox GL JS
- State: Redux Toolkit
- UI: Material-UI o Ant Design

**Prioridad:** Alta  
**Estimación:** 32 horas

---

### 3.4 Feature 4: Sistema de Alertas Inteligentes

**Descripción:** Alertas automáticas basadas en ML y reglas de negocio.

**Tipos de Alertas:**

#### 4.4.1 Price Alerts
- Nueva propiedad con precio bajo mercado (>15% bajo promedio)
- Reducción significativa de precio (>10%)
- Precio predicho vs precio real (oportunidad)

#### 4.4.2 Market Alerts
- Nueva oferta en zona de interés
- Cambio de tendencia en comuna
- Aumento/disminución de oferta (>20%)

#### 4.4.3 Custom Alerts
- Reglas personalizadas por usuario
- Filtros complejos (precio, ubicación, características)
- Frecuencia configurable (inmediata, diaria, semanal)

**Motor de Reglas:**
```python
# Ejemplo de regla
{
  "name": "Departamento Providencia Bajo Mercado",
  "conditions": {
    "tipo": "departamento",
    "comuna": "Providencia",
    "precio_max": 4000,  # UF
    "dormitorios_min": 2,
    "metros_min": 60
  },
  "trigger": "new_property",
  "notification": ["email", "slack"],
  "priority": "high"
}
```

**Machine Learning:**
- Modelo de predicción de precios
- Detección de anomalías
- Scoring de oportunidades (0-100)

**Prioridad:** Alta  
**Estimación:** 16 horas

---

### 3.5 Feature 5: Machine Learning para Predicción de Precios

**Descripción:** Modelo de ML para predecir precio de propiedades basado en características.

**Pipeline de ML:**

```
┌─────────────────────────────────────────────────────────┐
│  1. DATA COLLECTION                                      │
│     - Propiedades históricas (6+ meses)                 │
│     - Features: tipo, ubicación, m², dormitorios, etc.  │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  2. FEATURE ENGINEERING                                  │
│     - Encoding de categorías (one-hot, target)          │
│     - Normalización de numéricos                        │
│     - Features derivados (precio/m², densidad)          │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  3. MODEL TRAINING                                       │
│     - Algoritmos: XGBoost, LightGBM, Random Forest      │
│     - Cross-validation (5-fold)                         │
│     - Hyperparameter tuning (Optuna)                    │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  4. MODEL EVALUATION                                     │
│     - Métricas: MAE, RMSE, R²                           │
│     - Feature importance                                │
│     - Error analysis                                    │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  5. MODEL DEPLOYMENT                                     │
│     - Serialización (joblib/pickle)                     │
│     - API endpoint (/api/v2/predict)                    │
│     - Monitoring de drift                               │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  6. RETRAINING                                           │
│     - Mensual (con nuevos datos)                        │
│     - A/B testing de modelos                            │
│     - Continuous improvement                            │
└─────────────────────────────────────────────────────────┘
```

**Features del Modelo:**
- **Numéricos:** metros_utiles, dormitorios, banos, precio_historico
- **Categóricos:** tipo, operacion, comuna, sector, publicador_tipo
- **Derivados:** precio_por_m2, densidad_zona, antiguedad_publicacion
- **Geográficos:** latitud, longitud, distancia_metro, distancia_centro

**Modelos a Evaluar:**
1. XGBoost (baseline)
2. LightGBM (rápido)
3. Random Forest (interpretable)
4. Neural Network (complejo)

**Métricas Objetivo:**
- MAE (Mean Absolute Error): <UF 200
- RMSE: <UF 300
- R²: >0.85

**Prioridad:** Alta  
**Estimación:** 24 horas

---

### 3.6 Feature 6: Integración Multi-Plataforma

**Descripción:** Scraping de múltiples portales inmobiliarios para comparación de mercado.

**Plataformas a Integrar:**

1. **Portal Inmobiliario** (ya implementado)
   - Cobertura: Nacional
   - Propiedades: ~200,000

2. **Yapo.cl**
   - Cobertura: Nacional
   - Propiedades: ~150,000
   - Características: Particulares + inmobiliarias

3. **Toctoc.com**
   - Cobertura: Nacional
   - Propiedades: ~100,000
   - Características: Enfoque en venta

4. **Mercado Libre**
   - Cobertura: Nacional
   - Propiedades: ~80,000
   - Características: Particulares

**Arquitectura:**

```python
# Scraper abstracto
class PropertyScraper(ABC):
    @abstractmethod
    def scrape_listings(self, filters):
        pass
    
    @abstractmethod
    def scrape_detail(self, property_id):
        pass
    
    @abstractmethod
    def normalize_data(self, raw_data):
        pass

# Implementaciones específicas
class PortalInmobiliarioScraper(PropertyScraper):
    ...

class YapoScraper(PropertyScraper):
    ...

class ToctocScraper(PropertyScraper):
    ...
```

**Normalización de Datos:**
- Schema unificado para todas las plataformas
- Mapeo de campos (titulo, precio, ubicacion, etc.)
- Detección de duplicados cross-platform
- Scoring de calidad de datos

**Prioridad:** Media  
**Estimación:** 40 horas (10h por plataforma)

---

### 3.7 Feature 7: Mobile App (Opcional)

**Descripción:** Aplicación móvil para acceso on-the-go a alertas y búsquedas.

**Funcionalidades:**
- Búsqueda de propiedades con filtros
- Alertas push en tiempo real
- Favoritos y listas personalizadas
- Mapa interactivo
- Comparación de propiedades
- Contacto directo con publicador

**Stack:**
- React Native (iOS + Android)
- Expo (desarrollo rápido)
- Redux Toolkit (estado)
- React Navigation (navegación)

**Prioridad:** Baja  
**Estimación:** 80 horas

---

## 4. Especificaciones No Funcionales

### 4.1 Performance
- Scraping: 10,000+ propiedades/hora
- API latency: <100ms (p95)
- Dashboard load: <1s
- ML prediction: <200ms

### 4.2 Escalabilidad
- Horizontal scaling de workers
- DB sharding por fecha
- Cache distribuido (Redis Cluster)
- CDN para assets estáticos

### 4.3 Confiabilidad
- Uptime: ≥99.9%
- Backup automático (diario)
- Disaster recovery plan
- Monitoring 24/7

### 4.4 Seguridad
- Autenticación JWT
- Encriptación en tránsito (HTTPS)
- Encriptación en reposo (DB)
- Rate limiting agresivo
- Auditoría de accesos

---

## 5. Arquitectura

### 5.1 Diagrama de Alto Nivel

```
┌─────────────────────────────────────────────────────────┐
│                    USERS                                 │
│         Web App │ Mobile App │ API Clients              │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                   CDN (Cloudflare)                       │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              LOAD BALANCER (NGINX)                       │
└─────────────────────────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
    ┌─────────┐    ┌──────────┐    ┌──────────┐
    │FastAPI  │    │ React    │    │WebSocket │
    │ API     │    │Dashboard │    │ Server   │
    └─────────┘    └──────────┘    └──────────┘
          │               │               │
          └───────────────┼───────────────┘
                          ▼
              ┌───────────────────────┐
              │   REDIS CLUSTER       │
              │   - Cache             │
              │   - Celery Broker     │
              └───────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ PostgreSQL  │  │   Celery    │  │     ML      │
│   Master    │  │   Workers   │  │   Service   │
│             │  │  (Scraping) │  │  (FastAPI)  │
└─────────────┘  └─────────────┘  └─────────────┘
      │                  │                │
      ▼                  ▼                ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ PostgreSQL  │  │   Selenium  │  │   Model     │
│  Replicas   │  │   Grid      │  │   Storage   │
│  (Read)     │  │             │  │   (S3)      │
└─────────────┘  └─────────────┘  └─────────────┘
```

### 5.2 Stack Completo

| Capa | Tecnología | Versión |
|------|------------|---------|
| Frontend | React + TypeScript | 18+ |
| Mobile | React Native + Expo | Latest |
| API | FastAPI | 0.110+ |
| Workers | Celery | 5.3+ |
| Broker | Redis | 7+ |
| Database | PostgreSQL | 16+ |
| Cache | Redis Cluster | 7+ |
| ML | scikit-learn, XGBoost | Latest |
| Scraping | Selenium Grid | 4.18+ |
| Monitoring | Prometheus + Grafana | Latest |
| Logging | ELK Stack | Latest |
| Deploy | Docker + Kubernetes | Latest |

---

## 6. Plan de Implementación

### 6.1 Fases

#### Fase 4.1: Scraping Distribuido (Sprint 1-2)
- SPEC-020: Celery setup y configuración
- SPEC-021: Tareas distribuidas de scraping
- SPEC-022: Selenium Grid para paralelización

#### Fase 4.2: API FastAPI (Sprint 3)
- SPEC-023: Migración de Flask a FastAPI
- SPEC-024: Endpoints avanzados
- SPEC-025: Autenticación JWT

#### Fase 4.3: Machine Learning (Sprint 4-5)
- SPEC-026: Pipeline de datos para ML
- SPEC-027: Entrenamiento de modelos
- SPEC-028: Deployment de modelo
- SPEC-029: API de predicción

#### Fase 4.4: Dashboard Avanzado (Sprint 6-7)
- SPEC-030: Frontend React + TypeScript
- SPEC-031: Visualizaciones con D3.js
- SPEC-032: Mapa interactivo
- SPEC-033: Reportes personalizados

#### Fase 4.5: Alertas Inteligentes (Sprint 8)
- SPEC-034: Motor de reglas
- SPEC-035: Integración con ML
- SPEC-036: Notificaciones multi-canal

#### Fase 4.6: Multi-Plataforma (Sprint 9-10)
- SPEC-037: Scraper de Yapo
- SPEC-038: Scraper de Toctoc
- SPEC-039: Normalización cross-platform
- SPEC-040: Detección de duplicados

#### Fase 4.7: Mobile App (Sprint 11-12) - Opcional
- SPEC-041: Setup React Native
- SPEC-042: Pantallas principales
- SPEC-043: Integración con API
- SPEC-044: Push notifications

### 6.2 Timeline
- **Sprint 1-2:** 4 semanas (Scraping distribuido)
- **Sprint 3:** 2 semanas (FastAPI)
- **Sprint 4-5:** 4 semanas (Machine Learning)
- **Sprint 6-7:** 4 semanas (Dashboard)
- **Sprint 8:** 2 semanas (Alertas)
- **Sprint 9-10:** 4 semanas (Multi-plataforma)
- **Sprint 11-12:** 4 semanas (Mobile - opcional)
- **Total:** 20-24 semanas (5-6 meses)

---

## 7. Dependencias

### 7.1 Python
```
fastapi>=0.110.0
uvicorn[standard]>=0.29.0
celery[redis]>=5.3.0
scikit-learn>=1.4.0
xgboost>=2.0.0
lightgbm>=4.3.0
optuna>=3.6.0
pandas>=2.2.0
numpy>=1.26.0
matplotlib>=3.8.0
seaborn>=0.13.0
```

### 7.2 JavaScript
```
react@18
typescript@5
d3@7
recharts@2
mapbox-gl@3
redux-toolkit@2
react-native@0.73 (mobile)
```

### 7.3 Infraestructura
- Kubernetes cluster (o Railway Pro)
- PostgreSQL 16+ con replicas
- Redis Cluster
- S3-compatible storage (modelos ML)
- Selenium Grid

---

## 8. Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Complejidad de ML | Alta | Alto | Empezar con modelo simple, iterar |
| Costos de infraestructura | Alta | Alto | Optimización agresiva, auto-scaling |
| Scraping bloqueado | Media | Alto | Proxies rotativos, rate limiting |
| Modelo ML inexacto | Media | Medio | Validación continua, A/B testing |
| Integración multi-plataforma | Alta | Medio | Priorizar plataformas por ROI |

---

## 9. Criterios de Aceptación

### 9.1 Feature Completo
- [ ] Celery scraping 10,000+ props/hora
- [ ] FastAPI con latencia <100ms
- [ ] Modelo ML con R² >0.85
- [ ] Dashboard React funcionando
- [ ] Alertas inteligentes operativas
- [ ] ≥3 plataformas integradas

### 9.2 Calidad
- [ ] Tests E2E completos
- [ ] Load testing (1000 usuarios concurrentes)
- [ ] Security audit aprobado
- [ ] Documentación completa
- [ ] Code review aprobado

### 9.3 Deployment
- [ ] Kubernetes deployment
- [ ] CI/CD pipeline completo
- [ ] Monitoring con Grafana
- [ ] Backup automático
- [ ] Disaster recovery plan

---

## 10. Métricas de Seguimiento

### 10.1 Técnicas
- Throughput de scraping (props/hora)
- Latencia de API (p50, p95, p99)
- Precisión de ML (MAE, RMSE, R²)
- Uptime del sistema
- Costo por propiedad scrapeada

### 10.2 Negocio
- Usuarios activos (DAU, MAU)
- Alertas enviadas
- Propiedades en DB
- Plataformas integradas
- Revenue (si se monetiza)

---

## 11. Referencias

- [PRD Fase 3](./PRD-FASE-3-PRO.md) - Versión Pro completada
- [README.md](../../README.md) - Documentación principal
- [SDD Methodology](../../../SDD-jard/docs/SDD-METHODOLOGY.md)
- [Celery Docs](https://docs.celeryq.dev/)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [XGBoost Docs](https://xgboost.readthedocs.io/)

---

## 12. Aprobaciones

| Rol | Nombre | Fecha | Estado |
|-----|--------|-------|--------|
| Product Owner | - | - | Pendiente |
| Tech Lead | - | - | Pendiente |
| ML Lead | - | - | Pendiente |
| DevOps Lead | - | - | Pendiente |
| CFO | - | - | Pendiente |

---

**Última actualización:** 8 de Abril, 2026  
**Próxima revisión:** Al completar Fase 3
