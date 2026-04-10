# 📚 Documentación — Portal Inmobiliario Scraper

**Última actualización:** Abril 2026

---

## � Índice de Documentación

### 🎯 Documentación Principal
- [**ARCHITECTURE**](ARCHITECTURE.md) — Arquitectura del sistema
- [**STATUS**](STATUS.md) — Estado actual del proyecto
- [**CONVENTIONS**](CONVENTIONS.md) — Convenciones de código
- [**ORGANIZATION**](ORGANIZATION.md) — Organización de la documentación

### 📖 Guías
- [**QUICKSTART**](guides/QUICKSTART.md) — Guía de inicio rápido (5 minutos)

### � Deployment
- [**Docker**](deployment/DOCKER.md) — Guía completa de Docker y Railway
- [**Docker Quickstart**](deployment/QUICKSTART-DOCKER.md) — Docker en 5 minutos
- [**Railway**](deployment/RAILWAY.md) — Deployment en Railway

### � Especificaciones
- [**PRD**](specs/prd.md) — Product Requirements Document
- [**Roadmap Completo**](ROADMAP-COMPLETO.md) — Roadmap detallado del proyecto

---

## 🎯 Propósito

Esta carpeta contiene toda la documentación del proyecto **Portal Inmobiliario Scraper**, organizada por categorías para facilitar el acceso y mantenimiento.

---

## 📂 Estructura

```
docs/
├── README.md                      # Este archivo (índice maestro)
├── ARCHITECTURE.md                # Arquitectura del sistema
├── STATUS.md                      # Estado actual del proyecto
├── CONVENTIONS.md                 # Convenciones de código
├── ORGANIZATION.md                # Organización de la documentación
├── ROADMAP-COMPLETO.md            # Roadmap detallado
├── guides/                        # Guías de uso
│   └── QUICKSTART.md              # Inicio rápido
├── deployment/                    # Guías de deployment
│   ├── DOCKER.md                  # Docker completo
│   ├── QUICKSTART-DOCKER.md       # Docker rápido
│   └── RAILWAY.md                 # Railway
└── specs/                         # Especificaciones
    ├── prd.md                     # Product Requirements
    ├── scraping-detail.md         # Spec de scraping de detalle
    ├── dashboard-web.md           # Spec de dashboard web
    ├── postgresql-integration.md  # Spec de PostgreSQL
    └── api-rest.md                # Spec de API REST
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

## 🤖 AI Dev Engine

Este proyecto está integrado con el **AI Dev Engine** para desarrollo automatizado:

### Workflows Disponibles
- `/cascade-dev-scraper` — Desarrollo automatizado con SDD
- `/engine-validate` — Validación completa (tests, lint, security)
- `/engine-observe` — Monitoreo de producción
- `/portalinmobiliario-dev` — Workflow de desarrollo local
- `/portalinmobiliario-github` — Subida a GitHub

### Agentes Especializados
- **Scraper Agent** — Desarrollo de scrapers
- **Data Agent** — Validación y exportación de datos
- **Test Agent** — Testing automatizado

Ver `.windsurf/` para más detalles.

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

**Última revisión:** Abril 2026

- **Repositorio:** GitHub (configurar URL)
- **Deployment:** Railway (configurar URL)
- **Documentación API:** Pendiente

## 📝 Convenciones

### Commits
Seguir **Conventional Commits**:
- `feat(scope): descripción`
- `fix(scope): descripción`
- `docs: descripción`

Ver: [.windsurf/workflows/portalinmobiliario-github.md](../.windsurf/workflows/portalinmobiliario-github.md)

### Estructura de Código
- Python 3.11+
- PEP 8 style guide
- Type hints recomendados

---

## 🆘 Soporte

Para problemas o preguntas:
1. Revisar documentación relevante
2. Verificar logs: `docker logs <container>`
3. Abrir issue en GitHub
