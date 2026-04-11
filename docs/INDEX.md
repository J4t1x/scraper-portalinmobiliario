# 📑 Índice Visual de Documentación

**Última actualización:** 11 Abril 2026  
**Proyecto:** Portal Inmobiliario Scraper v2.0.0-MVP Analytics

---

## 🗺️ Mapa de Navegación Rápida

```
┌─────────────────────────────────────────────────────────────┐
│                    DOCUMENTACIÓN                            │
│                Portal Inmobiliario Scraper                  │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
    🎯 CORE            🤖 AI & ANALYTICS    📖 GUIDES
        │                   │                   │
        ├─ ARCHITECTURE     ├─ AI-ANALYTICS     ├─ QUICKSTART
        ├─ MVP-ARCH         └─ OLLAMA-INT       └─ MVP-QUICKSTART
        ├─ STATUS
        ├─ CONVENTIONS
        ├─ LOGGING
        └─ ROADMAP
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
    🚀 DEPLOYMENT       📋 SPECS & PRDs    🔄 MIGRATION
        │                   │                   │
        ├─ DOCKER           ├─ prd.md           └─ MIGRATION-GUIDE
        ├─ QUICKSTART       ├─ SPEC-MVP-001
        └─ SUMMARY          ├─ PRD-OPTIMIZACION
                            ├─ PRD-FASE-2
                            ├─ PRD-FASE-3
                            ├─ PRD-FASE-4
                            └─ SPECS-RESUMEN
```

---

## 🎯 Documentación por Rol

### 👨‍💻 Para Desarrolladores

**Inicio rápido:**
1. [`QUICKSTART.md`](guides/QUICKSTART.md) - 5 minutos para ejecutar el scraper
2. [`ARCHITECTURE.md`](ARCHITECTURE.md) - Entender el sistema completo
3. [`CONVENTIONS.md`](CONVENTIONS.md) - Estándares de código

**Desarrollo:**
- [`MVP-ARCHITECTURE.md`](MVP-ARCHITECTURE.md) - Arquitectura del contenedor único
- [`LOGGING.md`](LOGGING.md) - Sistema de logging
- [`SPEC-MVP-001.md`](specs/SPEC-MVP-001.md) - Especificación completa del MVP

**Testing:**
- Coverage actual: 73%
- Ver `tests/` en el repositorio

---

### 🚀 Para DevOps

**Deployment:**
1. [`DOCKER.md`](deployment/DOCKER.md) - Guía completa de Docker
2. [`QUICKSTART-DOCKER.md`](deployment/QUICKSTART-DOCKER.md) - Docker en 5 minutos
3. [`DEPLOYMENT-SUMMARY.md`](deployment/DEPLOYMENT-SUMMARY.md) - Resumen de opciones

**Optimización:**
- [`PRD-OPTIMIZACION-CONTENEDOR.md`](specs/PRD-OPTIMIZACION-CONTENEDOR.md) - Plan de optimización (nuevo)
  - -45% tamaño imagen
  - -45% RAM
  - -50% costos

**Migración:**
- [`MIGRATION-GUIDE.md`](migration/MIGRATION-GUIDE.md) - Migración a PostgreSQL

---

### 📊 Para Product Managers

**Estado del proyecto:**
1. [`STATUS.md`](STATUS.md) - Estado actual y métricas
2. [`ROADMAP-COMPLETO.md`](ROADMAP-COMPLETO.md) - Roadmap detallado

**Especificaciones:**
- [`prd.md`](specs/prd.md) - PRD original
- [`SPECS-RESUMEN.md`](specs/SPECS-RESUMEN.md) - Resumen de todas las specs
- [`PRD-FASE-2-MEJORAS.md`](specs/PRD-FASE-2-MEJORAS.md) - Fase 2
- [`PRD-FASE-3-PRO.md`](specs/PRD-FASE-3-PRO.md) - Fase 3
- [`PRD-FASE-4-ESCALAMIENTO.md`](specs/PRD-FASE-4-ESCALAMIENTO.md) - Fase 4

---

### 🤖 Para Data Scientists / ML Engineers

**Analytics:**
- [`AI-ANALYTICS-STUDIO.md`](AI-ANALYTICS-STUDIO.md) - Dashboard de analítica con IA
- [`OLLAMA-INTEGRATION.md`](OLLAMA-INTEGRATION.md) - Integración con Ollama
- [`SPEC-MVP-001.md`](specs/SPEC-MVP-001.md) - Pipeline pandas y detección de oportunidades

**Modelos:**
- Ollama: qwen2.5-coder:1.5b (1.5B parámetros)
- Analytics: pandas + numpy + scikit-learn

---

## 📚 Documentos por Categoría

### 🎯 Core Documentation (7 docs)

| Documento | Descripción | Última actualización |
|-----------|-------------|---------------------|
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | Arquitectura general del sistema | Abril 2026 |
| [`MVP-ARCHITECTURE.md`](MVP-ARCHITECTURE.md) | Arquitectura MVP (contenedor único) | Abril 2026 |
| [`STATUS.md`](STATUS.md) | Estado actual del proyecto | 11 Abril 2026 |
| [`CONVENTIONS.md`](CONVENTIONS.md) | Convenciones de código y estilo | Abril 2026 |
| [`LOGGING.md`](LOGGING.md) | Sistema de logging | Abril 2026 |
| [`ROADMAP-COMPLETO.md`](ROADMAP-COMPLETO.md) | Roadmap detallado | Abril 2026 |
| [`ORGANIZATION.md`](ORGANIZATION.md) | Organización de la documentación | Abril 2026 |

---

### 🤖 AI & Analytics (2 docs)

| Documento | Descripción | Última actualización |
|-----------|-------------|---------------------|
| [`AI-ANALYTICS-STUDIO.md`](AI-ANALYTICS-STUDIO.md) | Dashboard de analítica con IA | Abril 2026 |
| [`OLLAMA-INTEGRATION.md`](OLLAMA-INTEGRATION.md) | Integración con Ollama | Abril 2026 |

---

### 📖 Guides (2 docs)

| Documento | Descripción | Tiempo de lectura |
|-----------|-------------|-------------------|
| [`guides/QUICKSTART.md`](guides/QUICKSTART.md) | Inicio rápido general | 5 minutos |
| [`MVP-QUICKSTART.md`](MVP-QUICKSTART.md) | Inicio rápido del contenedor MVP | 5 minutos |

---

### 🚀 Deployment (3 docs)

| Documento | Descripción | Nivel |
|-----------|-------------|-------|
| [`deployment/DOCKER.md`](deployment/DOCKER.md) | Guía completa de Docker | Avanzado |
| [`deployment/QUICKSTART-DOCKER.md`](deployment/QUICKSTART-DOCKER.md) | Docker en 5 minutos | Básico |
| [`deployment/DEPLOYMENT-SUMMARY.md`](deployment/DEPLOYMENT-SUMMARY.md) | Resumen de deployment | Intermedio |

---

### 📋 Specs & PRDs (7 docs)

| Documento | Tipo | Estado | Prioridad |
|-----------|------|--------|-----------|
| [`specs/prd.md`](specs/prd.md) | PRD Original | ✅ Completado | - |
| [`specs/SPEC-MVP-001.md`](specs/SPEC-MVP-001.md) | Spec Técnica | ✅ Completado | Alta |
| [`specs/PRD-OPTIMIZACION-CONTENEDOR.md`](specs/PRD-OPTIMIZACION-CONTENEDOR.md) | PRD | 🚧 En progreso | 🔴 Crítica |
| [`specs/PRD-FASE-2-MEJORAS.md`](specs/PRD-FASE-2-MEJORAS.md) | PRD | ⏳ Pendiente | Media |
| [`specs/PRD-FASE-3-PRO.md`](specs/PRD-FASE-3-PRO.md) | PRD | ⏳ Pendiente | Media |
| [`specs/PRD-FASE-4-ESCALAMIENTO.md`](specs/PRD-FASE-4-ESCALAMIENTO.md) | PRD | ⏳ Pendiente | Baja |
| [`specs/SPECS-RESUMEN.md`](specs/SPECS-RESUMEN.md) | Resumen | ✅ Actualizado | - |

---

### 🔄 Migration (1 doc)

| Documento | Descripción | Estado |
|-----------|-------------|--------|
| [`migration/MIGRATION-GUIDE.md`](migration/MIGRATION-GUIDE.md) | Guía de migración a PostgreSQL | ✅ Completado |

---

## 🔍 Búsqueda Rápida por Tema

### Scraping
- [`ARCHITECTURE.md`](ARCHITECTURE.md) - Sección "Scraper Module"
- [`CONVENTIONS.md`](CONVENTIONS.md) - Patrones de scraping
- [`guides/QUICKSTART.md`](guides/QUICKSTART.md) - Ejecutar scraper

### Analytics & IA
- [`AI-ANALYTICS-STUDIO.md`](AI-ANALYTICS-STUDIO.md) - Dashboard completo
- [`OLLAMA-INTEGRATION.md`](OLLAMA-INTEGRATION.md) - Configuración Ollama
- [`SPEC-MVP-001.md`](specs/SPEC-MVP-001.md) - Pipeline pandas

### Docker & Deployment
- [`deployment/DOCKER.md`](deployment/DOCKER.md) - Guía completa
- [`deployment/QUICKSTART-DOCKER.md`](deployment/QUICKSTART-DOCKER.md) - Inicio rápido
- [`PRD-OPTIMIZACION-CONTENEDOR.md`](specs/PRD-OPTIMIZACION-CONTENEDOR.md) - Optimización

### Base de Datos
- [`ARCHITECTURE.md`](ARCHITECTURE.md) - Sección "Database Layer"
- [`migration/MIGRATION-GUIDE.md`](migration/MIGRATION-GUIDE.md) - Migración PostgreSQL
- [`SPEC-MVP-001.md`](specs/SPEC-MVP-001.md) - Modelos de datos

### Testing
- [`CONVENTIONS.md`](CONVENTIONS.md) - Estándares de testing
- [`STATUS.md`](STATUS.md) - Coverage actual (73%)

---

## 📊 Estadísticas de Documentación

```
Total de documentos: 23
├── Core: 7 docs
├── AI & Analytics: 2 docs
├── Guides: 2 docs
├── Deployment: 3 docs
├── Specs & PRDs: 7 docs
└── Migration: 1 doc

Estado:
├── ✅ Completados: 18 (78%)
├── 🚧 En progreso: 1 (4%)
└── ⏳ Pendientes: 4 (17%)

Última actualización: 11 Abril 2026
```

---

## 🎯 Próximos Pasos Recomendados

### Si eres nuevo en el proyecto:
1. Lee [`QUICKSTART.md`](guides/QUICKSTART.md) (5 min)
2. Revisa [`ARCHITECTURE.md`](ARCHITECTURE.md) (15 min)
3. Explora [`STATUS.md`](STATUS.md) para ver el estado actual

### Si vas a hacer deployment:
1. Lee [`QUICKSTART-DOCKER.md`](deployment/QUICKSTART-DOCKER.md) (5 min)
2. Revisa [`DOCKER.md`](deployment/DOCKER.md) para detalles
3. Consulta [`PRD-OPTIMIZACION-CONTENEDOR.md`](specs/PRD-OPTIMIZACION-CONTENEDOR.md) para optimización

### Si vas a desarrollar:
1. Lee [`CONVENTIONS.md`](CONVENTIONS.md)
2. Revisa [`SPEC-MVP-001.md`](specs/SPEC-MVP-001.md)
3. Consulta [`ARCHITECTURE.md`](ARCHITECTURE.md) para entender el sistema

---

## 🔗 Enlaces Externos

- **Repositorio:** GitHub - scraper-portalinmobiliario
- **Dashboard Local:** http://localhost:5000
- **Ollama API:** http://localhost:11434 (dentro del contenedor)
- **Railway:** (configurar post-optimización)

---

## 📝 Convenciones de Nomenclatura

- **MAYÚSCULAS.md** - Documentación principal
- **kebab-case.md** - Guías y tutoriales
- **PRD-*.md** - Product Requirements Documents
- **SPEC-*.md** - Especificaciones técnicas

---

**Mantenido por:** Equipo de Desarrollo  
**Última revisión:** 11 Abril 2026  
**Versión:** 2.0.0-MVP Analytics
