---
description: Desarrollo automatizado del scraper con Cascade + AI Dev Engine
---

# cascade-dev (scraper-portalinmobiliario)

Workflow de desarrollo automatizado que combina SDD + AI Dev Engine para el proyecto scraper-portalinmobiliario.

---

## Uso

```bash
# Modo clásico
/cascade-dev                              # Una iteración
/cascade-dev --loop                       # Loop continuo
/cascade-dev SPEC-001                     # Spec específica
/cascade-dev scraper-portalinmobiliario   # Solo specs de este proyecto

# Modo auto-spec
/cascade-dev "Agregar scraping de imágenes"
/cascade-dev "Implementar cache de resultados"
```

---

## Flujo de Ejecución

### 1. Seleccionar Spec

**Si no se especifica spec:**
```bash
# Listar specs pendientes
ls .windsurf/specs/pending/

# Seleccionar la de mayor prioridad
# O preguntar al usuario
```

**Si se proporciona descripción:**
1. Generar spec automáticamente
2. Guardar en `specs/pending/SPEC-XXX.md`
3. Continuar con implementación

---

### 2. Cargar Contexto

**Archivos a leer:**
- `.windsurf/rules/scraper-portalinmobiliario.md` — Reglas del proyecto
- `.windsurf/agents/scraper-agent.md` — Agente de scraping
- `.windsurf/agents/data-agent.md` — Agente de datos
- `.windsurf/agents/test-agent.md` — Agente de testing
- `docs/ARCHITECTURE.md` — Arquitectura actual
- `docs/STATUS.md` — Estado del proyecto
- `README.md` — Documentación principal

**Contexto clave:**
- Stack: Python 3.11+ + Selenium 4.18.1 + PostgreSQL
- Estructura: `main.py`, `scraper_selenium.py`, `exporter.py`, `validator.py`
- Convenciones: PEP 8, type hints, logging
- Deploy: Railway (Docker + PostgreSQL)

---

### 3. Planificar Implementación

**Usar Planner Agent:**
1. Leer spec completa
2. Descomponer en tareas
3. Identificar dependencias
4. Estimar tiempo
5. Crear plan de ejecución

**Ejemplo de plan:**
```
SPEC-001: Scraping de Imágenes
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Tareas:
1. [2h] Implementar extracción de URLs de imágenes
2. [1h] Agregar campo 'imagenes' a data model
3. [1h] Actualizar exportación (JSON, CSV)
4. [2h] Implementar tests
5. [1h] Actualizar documentación

Total: 7 horas
```

---

### 4. Ejecutar Implementación

**Fase 1: Core Implementation**

**Usar Scraper Agent:**
```python
# Modificar scraper_selenium.py
def scrape_property_detail(self, property_id: str, url: str) -> Dict:
    # Agregar extracción de imágenes
    imagenes = self._extract_images(driver)
    return {
        ...
        'imagenes': imagenes
    }

def _extract_images(self, driver: WebDriver) -> List[str]:
    # Implementar lógica
    pass
```

**Usar Data Agent:**
```python
# Modificar exporter.py
# Asegurar que campo 'imagenes' se exporte correctamente
```

**Fase 2: Testing**

**Usar Test Agent:**
```python
# tests/unit/test_scraper.py
def test_extract_images():
    # Test unitario
    pass

# tests/integration/test_scraping_with_images.py
def test_scrape_with_images():
    # Test de integración
    pass
```

**Fase 3: Documentation**
```bash
# Actualizar README.md
# Actualizar docs/ARCHITECTURE.md
# Actualizar docs/STATUS.md
```

---

### 5. Validar Implementación

**Ejecutar validaciones:**

```bash
# 1. Lint
# (Python no tiene lint por defecto, pero se puede agregar)
# flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

# 2. Tests unitarios
pytest tests/unit/ -v

# 3. Tests de integración
pytest tests/integration/ -v

# 4. Tests E2E (limitado)
pytest tests/e2e/ -v -m "not slow"

# 5. Verificar que no se rompió nada
python main.py --operacion venta --tipo departamento --max-pages 1 --verbose
```

**Criterios de éxito:**
- [ ] Todos los tests pasan
- [ ] No hay errores de sintaxis
- [ ] Scraping funciona correctamente
- [ ] Exportación genera archivos válidos
- [ ] Documentación actualizada

---

### 6. Completar Spec

**Mover spec:**
```bash
# De pending/ a completed/
mv .windsurf/specs/pending/SPEC-XXX.md .windsurf/specs/completed/SPEC-XXX.md
```

**Actualizar spec:**
```markdown
**Estado:** completed  
**Fecha completado:** YYYY-MM-DD

## Changelog
| Fecha | Cambio | Autor |
|-------|--------|-------|
| YYYY-MM-DD | Spec creada | Cascade |
| YYYY-MM-DD | Implementación completada | Cascade |
```

**Commit:**
```bash
git add .
git commit -m "feat(scraper): SPEC-XXX - [título]

- Implementación completa
- Tests agregados
- Documentación actualizada

Closes #XXX"
```

---

### 7. Deploy (Opcional)

**Si está configurado Railway:**
```bash
# Push a GitHub
git push origin main

# Railway despliega automáticamente
# Monitorear logs en Railway dashboard
```

---

## Modo Loop

**Si se ejecuta con `--loop`:**

```bash
while [ specs en pending/ ]; do
    # 1. Seleccionar siguiente spec
    # 2. Cargar contexto
    # 3. Planificar
    # 4. Ejecutar
    # 5. Validar
    # 6. Completar
    # 7. Repetir
done

echo "✅ Todas las specs completadas"
```

---

## Agentes Involucrados

| Agente | Responsabilidad |
|--------|-----------------|
| **Planner Agent** | Descomponer spec en tareas |
| **Scraper Agent** | Implementar lógica de scraping |
| **Data Agent** | Validación, transformación, exportación |
| **Test Agent** | Implementar tests automatizados |
| **Review Agent** | Code review automático |

---

## Comandos Útiles

### Desarrollo Local
```bash
# Activar venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar scraper
python main.py --operacion venta --tipo departamento --max-pages 1 --verbose

# Ejecutar tests
pytest -v
```

### Docker
```bash
# Build
docker build -t scraper-portalinmobiliario:latest .

# Run
docker run --rm \
  -v $(pwd)/output:/app/output \
  scraper-portalinmobiliario:latest \
  python main.py --operacion venta --tipo departamento --max-pages 1
```

---

## Troubleshooting

### Spec no se encuentra
```bash
# Verificar que existe
ls .windsurf/specs/pending/SPEC-XXX.md

# Verificar formato de nombre
# Debe ser: SPEC-001.md, SPEC-002.md, etc.
```

### Tests fallan
```bash
# Ver detalles
pytest -v --tb=short

# Ejecutar test específico
pytest tests/unit/test_scraper.py::test_specific -v
```

### Validación falla
```bash
# Ver logs detallados
python main.py --verbose

# Verificar configuración
cat .env
```

---

## Notas

- **Stack:** Python 3.11+ + Selenium + PostgreSQL
- **Deploy:** Railway (automático en push a main)
- **Docs:** Mantener `docs/` actualizado
- **Tests:** Ejecutar antes de commit
- **Convenciones:** Seguir `.windsurf/rules/scraper-portalinmobiliario.md`

---

**Última actualización:** Abril 2026
