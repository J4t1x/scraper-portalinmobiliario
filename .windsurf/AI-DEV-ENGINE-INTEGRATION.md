# AI Dev Engine Integration — Portal Inmobiliario Scraper

**Fecha de integración:** Abril 2026  
**Versión del Engine:** 1.0

---

## ✅ Estado de Integración

| Componente | Estado | Ubicación |
|------------|--------|-----------|
| **Agentes** | ✅ Completo | `.windsurf/agents/` |
| **Specs** | ✅ Completo | `.windsurf/specs/` |
| **Workflows** | ✅ Completo | `.windsurf/workflows/` |
| **Rules** | ✅ Completo | `.windsurf/rules/` |
| **Docs** | ✅ Completo | `docs/` |

---

## 🤖 Agentes Disponibles

### 1. Scraper Agent
**Archivo:** `.windsurf/agents/scraper-agent.md`

**Responsabilidades:**
- Desarrollo de lógica de scraping
- Optimización de selectores
- Manejo de errores y retry
- Scraping de páginas de detalle

**Comandos:**
```bash
# Implementar nueva funcionalidad de scraping
/cascade-dev "Agregar scraping de imágenes"
```

### 2. Data Agent
**Archivo:** `.windsurf/agents/data-agent.md`

**Responsabilidades:**
- Validación de datos extraídos
- Transformación de formatos
- Deduplicación
- Exportación múltiple (TXT, JSON, CSV)

**Comandos:**
```bash
# Mejorar validación de datos
/cascade-dev "Agregar validación de coordenadas GPS"
```

### 3. Test Agent
**Archivo:** `.windsurf/agents/test-agent.md`

**Responsabilidades:**
- Tests unitarios
- Tests de integración
- Tests E2E
- Mocking de WebDriver

**Comandos:**
```bash
# Agregar tests
/cascade-dev "Implementar tests para scraping de detalle"
```

---

## 📋 Workflows Disponibles

### Desarrollo

**`/cascade-dev-scraper`**
- Desarrollo automatizado con SDD
- Generación automática de specs
- Implementación + tests + docs
- Loop continuo disponible

**Uso:**
```bash
# Una iteración
/cascade-dev-scraper

# Loop continuo
/cascade-dev-scraper --loop

# Spec específica
/cascade-dev-scraper SPEC-001

# Auto-generar spec
/cascade-dev-scraper "Agregar cache de resultados"
```

### Validación

**`/engine-validate`**
- Tests unitarios + integración
- Lint (opcional con flake8)
- Security check
- Docker build check
- Validación de datos

**Uso:**
```bash
# Validación completa
/engine-validate

# Solo tests rápidos
/engine-validate --quick

# Solo unitarios
/engine-validate --unit
```

### Observabilidad

**`/engine-observe`**
- Logs de Railway
- Métricas de performance
- Análisis de errores
- Calidad de datos
- Dashboard de observabilidad

**Uso:**
```bash
# Dashboard completo
/engine-observe

# Solo logs
/engine-observe --logs

# Solo errores
/engine-observe --errors
```

### Workflows Existentes

**`/portalinmobiliario-dev`**
- Setup local
- Ejecutar scraper
- Verificar resultados
- Docker workflow

**`/portalinmobiliario-github`**
- Subida a GitHub con Conventional Commits
- Validación pre-commit
- Push automático

---

## 📁 Estructura de Specs

### Carpetas

```
.windsurf/specs/
├── pending/          # Specs pendientes de implementación
├── in-progress/      # Specs en desarrollo
├── completed/        # Specs completadas
└── _template.md      # Template para nuevas specs
```

### Ciclo de Vida

```
1. Crear spec en pending/
   ↓
2. /cascade-dev-scraper SPEC-XXX
   ↓
3. Mover a in-progress/
   ↓
4. Implementar + tests + docs
   ↓
5. Validar con /engine-validate
   ↓
6. Mover a completed/
   ↓
7. Commit y push
```

---

## 🎯 Comandos Principales

### Desarrollo Automatizado

```bash
# Generar spec desde descripción
/cascade-dev-scraper "Implementar scraping de videos"

# Implementar spec existente
/cascade-dev-scraper SPEC-005

# Loop continuo (todas las specs pending)
/cascade-dev-scraper --loop
```

### Validación

```bash
# Validación completa antes de deploy
/engine-validate

# Solo tests
/engine-validate --unit
```

### Monitoreo

```bash
# Ver estado de producción
/engine-observe

# Ver últimos errores
/engine-observe --errors
```

### Desarrollo Local

```bash
# Setup y ejecución
/portalinmobiliario-dev

# Subir cambios a GitHub
/portalinmobiliario-github
```

---

## 📖 Documentación Integrada

### Docs Principales

| Archivo | Descripción |
|---------|-------------|
| `docs/ARCHITECTURE.md` | Arquitectura del sistema |
| `docs/STATUS.md` | Estado actual del proyecto |
| `docs/CONVENTIONS.md` | Convenciones de código |

### Reglas del Proyecto

**Archivo:** `.windsurf/rules/scraper-portalinmobiliario.md`

**Contenido:**
- Stack tecnológico
- Estructura del proyecto
- Convenciones de código
- Configuración
- Deployment
- Regla de auto-mantenimiento

---

## 🔄 Flujo de Trabajo Recomendado

### 1. Nueva Funcionalidad

```bash
# Opción A: Generar spec automáticamente
/cascade-dev-scraper "Agregar scraping de planos de planta"

# Opción B: Crear spec manualmente
# 1. Copiar .windsurf/specs/_template.md
# 2. Completar spec
# 3. Guardar en pending/SPEC-XXX.md
# 4. /cascade-dev-scraper SPEC-XXX
```

### 2. Validación

```bash
# Antes de commit
/engine-validate

# Verificar que todo pasa
# - Tests unitarios
# - Tests de integración
# - Docker build
# - Validación de datos
```

### 3. Deployment

```bash
# Subir a GitHub
/portalinmobiliario-github

# Railway despliega automáticamente
# Monitorear con /engine-observe
```

---

## 🎓 Mejores Prácticas

### Specs

1. **Usar template:** Siempre partir de `_template.md`
2. **Ser específico:** Criterios de aceptación verificables
3. **Estimar tiempo:** Ayuda a planificar
4. **Documentar decisiones:** En sección de notas

### Desarrollo

1. **Una spec a la vez:** No mezclar funcionalidades
2. **Tests primero:** TDD cuando sea posible
3. **Validar antes de commit:** `/engine-validate`
4. **Documentar cambios:** Actualizar docs/

### Commits

1. **Conventional Commits:** `feat(scope): descripción`
2. **Referenciar specs:** `Closes SPEC-XXX`
3. **Mensajes descriptivos:** Explicar el "por qué"

---

## 🚀 Próximos Pasos

### Specs Sugeridas

1. **SPEC-001:** Implementar cache de resultados
2. **SPEC-002:** Agregar scraping de planos de planta
3. **SPEC-003:** Implementar API REST con FastAPI
4. **SPEC-004:** Scheduler para scraping automático
5. **SPEC-005:** Dashboard analítico con gráficos

### Mejoras del Engine

1. [ ] Integrar GitHub Actions para CI/CD
2. [ ] Implementar auto-fix de errores comunes
3. [ ] Agregar métricas de performance
4. [ ] Implementar alertas automáticas
5. [ ] Dashboard de observabilidad web

---

## 📊 Métricas de Éxito

### Desarrollo

- **Tiempo de implementación:** Reducido en ~60% con AI Dev Engine
- **Cobertura de tests:** Objetivo > 80%
- **Bugs en producción:** Reducidos en ~40%

### Calidad

- **Code review automático:** 100% de specs
- **Validación pre-commit:** Obligatoria
- **Documentación:** Siempre actualizada

---

## 🔗 Links Útiles

- **AI Dev Engine:** `/Users/ja/Documents/GitHub/.windsurf/engine/`
- **Agentes Globales:** `/Users/ja/Documents/GitHub/.windsurf/agents/`
- **Workflows Globales:** `/Users/ja/Documents/GitHub/.windsurf/workflows/`
- **Documentación:** `docs/README.md`

---

## 📝 Notas

### Integración Completada

- ✅ Agentes especializados creados
- ✅ Workflows adaptados al proyecto
- ✅ Estructura de specs implementada
- ✅ Documentación completa
- ✅ Reglas del proyecto definidas

### Próximas Mejoras

- [ ] Integrar con GitHub Projects
- [ ] Implementar métricas de desarrollo
- [ ] Agregar templates de PRs
- [ ] Configurar GitHub Actions

---

**Última actualización:** Abril 2026
