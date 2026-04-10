---
description: Ejecutar validación completa del código (tests, lint, security, build)
---

# engine-validate (scraper-portalinmobiliario)

Workflow de validación completa del scraper antes de deploy.

---

## Uso

```bash
/engine-validate                    # Validación completa
/engine-validate --quick            # Solo tests rápidos
/engine-validate --unit             # Solo tests unitarios
/engine-validate --integration      # Solo tests de integración
```

---

## Pasos

### 1. Verificar Entorno

```bash
# Verificar Python version
python --version  # Debe ser 3.11+

# Verificar venv activo
which python  # Debe apuntar a venv/

# Verificar dependencias instaladas
pip list | grep -E "(selenium|beautifulsoup4|pytest)"
```

---

### 2. Lint (Opcional)

**Python no tiene lint por defecto, pero se puede agregar:**

```bash
# Instalar flake8 si no está
pip install flake8

# Ejecutar lint
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

# Verificar PEP 8 (warnings, no errores)
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
```

**Criterios:**
- [ ] Sin errores de sintaxis (E9, F63, F7, F82)
- [ ] Warnings de PEP 8 aceptables

---

### 3. Tests Unitarios

```bash
# Ejecutar todos los tests unitarios
pytest tests/unit/ -v

# Con coverage
pytest tests/unit/ --cov=. --cov-report=term-missing
```

**Criterios:**
- [ ] Todos los tests pasan
- [ ] Coverage > 70%

---

### 4. Tests de Integración

```bash
# Ejecutar tests de integración
pytest tests/integration/ -v

# Con timeout (evitar tests colgados)
pytest tests/integration/ -v --timeout=60
```

**Criterios:**
- [ ] Todos los tests pasan
- [ ] No hay timeouts

---

### 5. Tests E2E (Limitado)

```bash
# Solo tests rápidos (no slow)
pytest tests/e2e/ -v -m "not slow"

# O ejecutar manualmente scraping limitado
python main.py --operacion venta --tipo departamento --max-pages 1 --verbose
```

**Criterios:**
- [ ] Scraping funciona
- [ ] Datos extraídos son válidos
- [ ] Exportación genera archivos

---

### 6. Security Check (Básico)

```bash
# Verificar que no hay credenciales hardcodeadas
grep -r "password\|api_key\|secret" --include="*.py" --exclude-dir=venv .

# Verificar .env no está en git
git ls-files | grep "^\.env$"  # No debe retornar nada

# Verificar dependencias sin vulnerabilidades conocidas
pip install safety
safety check
```

**Criterios:**
- [ ] Sin credenciales hardcodeadas
- [ ] `.env` no está en git
- [ ] Sin vulnerabilidades críticas

---

### 7. Build Check (Docker)

```bash
# Verificar que Dockerfile es válido
docker build -t scraper-test:latest . --no-cache

# Ejecutar contenedor de prueba
docker run --rm scraper-test:latest python main.py --help

# Limpiar
docker rmi scraper-test:latest
```

**Criterios:**
- [ ] Build exitoso
- [ ] Contenedor ejecuta correctamente

---

### 8. Validación de Datos

```bash
# Ejecutar scraping de prueba
python main.py --operacion venta --tipo departamento --max-pages 1 --formato json

# Validar datos generados
python validator.py output/*.json

# Verificar estructura de archivos
ls -lh output/
```

**Criterios:**
- [ ] Archivos generados correctamente
- [ ] Datos válidos según validator
- [ ] Formatos correctos (JSON, CSV)

---

## Resumen de Validación

Al final, mostrar resumen:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ VALIDACIÓN COMPLETA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Lint: Sin errores críticos
✅ Tests Unitarios: 45/45 passed (coverage: 82%)
✅ Tests Integración: 12/12 passed
✅ Tests E2E: 3/3 passed
✅ Security: Sin vulnerabilidades críticas
✅ Build: Docker build exitoso
✅ Datos: Validación exitosa

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 LISTO PARA DEPLOY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

O si hay errores:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ VALIDACIÓN FALLIDA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Lint: OK
❌ Tests Unitarios: 43/45 passed (2 failed)
✅ Tests Integración: 12/12 passed
⚠️  Tests E2E: Skipped
✅ Security: OK
✅ Build: OK
❌ Datos: Validación falló (3 errores)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⛔ NO LISTO PARA DEPLOY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Errores a corregir:
1. test_extract_price: AssertionError
2. test_validate_coordinates: ValueError
3. Datos: 3 propiedades con campos faltantes
```

---

## Modo Rápido

**Si se ejecuta con `--quick`:**

```bash
# Solo tests unitarios rápidos
pytest tests/unit/ -v -m "not slow"

# Skip Docker build
# Skip E2E tests
# Skip security check completo
```

---

## CI/CD Integration

**Para GitHub Actions:**

```yaml
name: Validate

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest tests/unit/ -v
      - run: pytest tests/integration/ -v
      - run: docker build -t scraper:test .
```

---

## Troubleshooting

### Tests fallan en CI pero pasan en local
- Verificar versiones de dependencias
- Verificar variables de entorno
- Usar mocks para tests E2E en CI

### Docker build falla
- Verificar Dockerfile
- Verificar requirements.txt actualizado
- Limpiar cache: `docker build --no-cache`

### Coverage bajo
- Agregar tests para funciones sin cobertura
- Verificar que tests realmente ejecuten código

---

**Última actualización:** Abril 2026
