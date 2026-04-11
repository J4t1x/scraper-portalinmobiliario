# 📚 Documentación — Portal Inmobiliario Scraper

**Última actualización:** 11 Abril 2026  
**Versión:** 2.0.0-MVP Analytics  
**Estado:** ✅ MVP Implementado + 🚧 Optimización en progreso

---

## 📊 Índice de Documentación

### 🎯 Documentación Principal
- [**ARCHITECTURE**](ARCHITECTURE.md) — Arquitectura del sistema (scraper + analytics + IA)
- [**MVP-ARCHITECTURE**](MVP-ARCHITECTURE.md) — Arquitectura MVP (contenedor único)
- [**STATUS**](STATUS.md) — Estado actual del proyecto
- [**CONVENTIONS**](CONVENTIONS.md) — Convenciones de código y estilo
- [**LOGGING**](LOGGING.md) — Sistema de logging

### 📖 Guías de Uso
- [**QUICKSTART**](guides/QUICKSTART.md) — Guía de inicio rápido (5 minutos)
- [**MVP-QUICKSTART**](MVP-QUICKSTART.md) — Inicio rápido del contenedor MVP

### 🚀 Deployment
- [**DOCKER**](deployment/DOCKER.md) — Guía completa de Docker (estándar)
- [**QUICKSTART-DOCKER**](deployment/QUICKSTART-DOCKER.md) — Docker en 5 minutos
- [**DEPLOYMENT-SUMMARY**](deployment/DEPLOYMENT-SUMMARY.md) — Resumen de deployment

### 🤖 Integraciones IA
- [**AI-ANALYTICS-STUDIO**](AI-ANALYTICS-STUDIO.md) — Dashboard de analítica con IA
- [**OLLAMA-INTEGRATION**](OLLAMA-INTEGRATION.md) — Integración con Ollama

### 📋 Especificaciones y PRDs
- [**PRD Original**](specs/prd.md) — Product Requirements Document inicial
- [**SPEC-MVP-001**](specs/SPEC-MVP-001.md) — Especificación MVP Analytics completa
- [**PRD Optimización Contenedor**](specs/PRD-OPTIMIZACION-CONTENEDOR.md) — Optimización de recursos (nuevo)
- [**SPECS-RESUMEN**](specs/SPECS-RESUMEN.md) — Resumen de todas las specs
- [**Roadmap Completo**](ROADMAP-COMPLETO.md) — Roadmap detallado del proyecto

### 🔄 Migración y Mantenimiento
- [**Migration Guide**](migration/MIGRATION-GUIDE.md) — Guía de migración a PostgreSQL
- [**ORGANIZATION**](ORGANIZATION.md) — Organización de la documentación

---

## 📰 Cambios Recientes

### 11 Abril 2026 - PRD Optimización de Contenedor
- 📋 Creado PRD completo para optimización de recursos
- 🎯 11 optimizaciones críticas identificadas
- 📊 Objetivo: -45% tamaño imagen, -45% RAM, -50% costos
- 📅 Plan de implementación: 6 días (4 fases)
- 💰 ROI estimado: 11 meses, ahorro $72 USD/año

### 9 Abril 2026 - MVP Analytics Completado
- ✅ Implementado SPEC-MVP-ANALYTICS-001 completo
  - Pipeline pandas para analítica (precio/m², promedios por comuna)
  - Detección de oportunidades (< μ - 1σ)
  - Scoring 0-100 para oportunidades
  - Modelos: Opportunity, AnalyticsCache
  - API REST: /api/analytics/*, /api/opportunities/*
  - Agente IA con Ollama (qwen2.5-coder:1.5b)
- ✅ Contenedor MVP único (Dockerfile.mvp)
  - PostgreSQL + Ollama + Flask + Scheduler
  - Supervisord para orquestación
  - Modelo IA pre-descargado
- ✅ Migración Alembic 003 (tablas analytics)

### 9 Abril 2026 - Dashboard y Scheduler
- ✅ SPEC-011: Scheduler con APScheduler
- ✅ SPEC-012: Jobs de scraping automático
- ✅ SPEC-MVP-001/002/003: Dashboard con lectura de JSON

---

## 🎯 Propósito

Esta carpeta contiene toda la documentación del proyecto **Portal Inmobiliario Scraper**, organizada por categorías para facilitar el acceso y mantenimiento.

---

## 📂 Estructura

```
docs/
├── README.md                           # Este archivo (índice maestro)
│
├── 🎯 Core Documentation
│   ├── ARCHITECTURE.md                 # Arquitectura general del sistema
│   ├── MVP-ARCHITECTURE.md             # Arquitectura MVP (contenedor único)
│   ├── STATUS.md                       # Estado actual del proyecto
│   ├── CONVENTIONS.md                  # Convenciones de código
│   ├── LOGGING.md                      # Sistema de logging
│   ├── ROADMAP-COMPLETO.md             # Roadmap detallado
│   └── ORGANIZATION.md                 # Organización de docs
│
├── 🤖 AI & Analytics
│   ├── AI-ANALYTICS-STUDIO.md          # Dashboard de analítica con IA
│   └── OLLAMA-INTEGRATION.md           # Integración Ollama
│
├── 📖 Guides
│   ├── QUICKSTART.md                   # Inicio rápido general
│   └── MVP-QUICKSTART.md               # Inicio rápido MVP
│
├── 🚀 Deployment
│   ├── DOCKER.md                       # Guía completa Docker
│   ├── QUICKSTART-DOCKER.md            # Docker en 5 minutos
│   └── DEPLOYMENT-SUMMARY.md           # Resumen de deployment
│
├── 📋 Specs & PRDs
│   ├── prd.md                          # PRD original
│   ├── SPEC-MVP-001.md                 # Spec MVP Analytics completa
│   ├── PRD-OPTIMIZACION-CONTENEDOR.md  # PRD Optimización (nuevo)
│   ├── PRD-FASE-2-MEJORAS.md           # Fase 2
│   ├── PRD-FASE-3-PRO.md               # Fase 3
│   ├── PRD-FASE-4-ESCALAMIENTO.md      # Fase 4
│   └── SPECS-RESUMEN.md                # Resumen de specs
│
└── 🔄 Migration
    └── MIGRATION-GUIDE.md              # Guía de migración PostgreSQL
```

---

## 🚀 Inicio Rápido

Si es tu primera vez con el proyecto:

1. Lee [ARCHITECTURE.md](ARCHITECTURE.md) para entender el sistema
2. Lee [QUICKSTART.md](guides/QUICKSTART.md) (5 minutos)
3. Ejecuta el scraper localmente
4. Revisa [DOCKER.md](deployment/DOCKER.md) para deployment

---

## 📖 Documentación por Tema

### Para Desarrolladores
- [ARCHITECTURE.md](ARCHITECTURE.md) — Arquitectura y componentes
- [CONVENTIONS.md](CONVENTIONS.md) — Patrones de código
- [QUICKSTART.md](guides/QUICKSTART.md) — Setup y primer scraping
- [PRD.md](specs/prd.md) — Requerimientos del producto

### Para DevOps
- [DOCKER.md](deployment/DOCKER.md) — Build y deployment
- [RAILWAY.md](deployment/RAILWAY.md) — Deployment en Railway
- [QUICKSTART-DOCKER.md](deployment/QUICKSTART-DOCKER.md) — Docker rápido

### Para Product Managers
- [STATUS.md](STATUS.md) — Estado actual y métricas
- [PRD.md](specs/prd.md) — Product Requirements
- [ROADMAP-COMPLETO.md](ROADMAP-COMPLETO.md) — Roadmap completo

---

## 🤖 AI Dev Engine & Cascade

Este proyecto está integrado con **Cascade** y el **AI Dev Engine** para desarrollo automatizado:

### Workflows Disponibles
- `/cascade-dev-scraper` — Desarrollo automatizado con SDD + AI Engine
- `/portalinmobiliario-dev` — Setup y ejecución local del scraper
- `/portalinmobiliario-github` — Subida a GitHub con Conventional Commits
- `/portalinmobiliario-mvp` — Implementar MVP de analítica (contenedor único)
- `/engine-validate` — Validación completa (tests, lint, security)
- `/engine-observe` — Monitoreo de producción y logs

### Agentes Especializados
- **Scraper Agent** — Desarrollo de scrapers con Selenium
- **Data Agent** — Validación, transformación y exportación
- **Analytics Agent** — Pipeline pandas y detección de oportunidades
- **Test Agent** — Testing automatizado

Ver `.windsurf/` para configuración completa.

---

## � Mantenimiento

Esta documentación se actualiza regularmente. Última revisión: **Abril 2026**

Para contribuir a la documentación:
1. Edita el archivo correspondiente
2. Actualiza la fecha de "Última actualización"
3. Actualiza este README si es necesario
4. Commit con mensaje descriptivo

---

## 📝 Notas

- Todos los archivos están en formato Markdown
- Los diagramas usan sintaxis Mermaid cuando es posible
- Los ejemplos de código incluyen comentarios explicativos
- Las guías están optimizadas para lectura rápida

---

**Última revisión:** 11 Abril 2026

### Enlaces Útiles
- **Repositorio:** GitHub - scraper-portalinmobiliario
- **Deployment:** Railway (configurar URL post-optimización)
- **Dashboard Local:** http://localhost:5000 (después de `docker-compose up`)
- **Ollama API:** http://localhost:11434 (dentro del contenedor MVP)
- **Documentación API:** Ver `AI-ANALYTICS-STUDIO.md`

### Stack Tecnológico
- **Scraping:** Python 3.14.3 + Selenium 4.18.1 + Chrome headless
- **Base de datos:** PostgreSQL 15 + SQLAlchemy + Alembic
- **Analytics:** pandas + numpy + scikit-learn (básico)
- **IA:** Ollama + qwen2.5-coder:1.5b (1.5B parámetros)
- **Web:** Flask 3.0.2 + TailwindCSS + Chart.js
- **Scheduler:** APScheduler + Supervisor
- **Container:** Docker + docker-compose

## 📝 Convenciones

### Commits
Seguir **Conventional Commits**:
- `feat(scope): descripción` — Nueva funcionalidad
- `fix(scope): descripción` — Corrección de bugs
- `docs: descripción` — Cambios en documentación
- `refactor(scope): descripción` — Refactorización
- `perf(scope): descripción` — Mejoras de performance
- `test(scope): descripción` — Tests

Ver: [.windsurf/workflows/portalinmobiliario-github.md](../.windsurf/workflows/portalinmobiliario-github.md)

### Estructura de Código
- **Python:** 3.14.3 (producción), 3.11+ (desarrollo)
- **Style:** PEP 8 + Black formatter
- **Type hints:** Obligatorios en funciones públicas
- **Docstrings:** Google style
- **Testing:** pytest + coverage > 70%

---

## 🆘 Soporte

Para problemas o preguntas:
1. Revisar documentación relevante
2. Verificar logs: `docker logs <container>`
3. Abrir issue en GitHub
