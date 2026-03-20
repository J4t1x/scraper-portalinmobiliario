---
description: Subida de cambios de portalinmobiliario a GitHub con Conventional Commits
---

Workflow para hacer commit y push del proyecto portalinmobiliario siguiendo las convenciones de commits del equipo.

## 1. Pre-checks

// turbo
1. Verificar estado del repo: `git status`
2. Revisar que no haya conflictos pendientes: `git diff --check`
3. Confirmar rama actual: `git branch --show-current`

## 2. Elegir tipo de commit

Usar **Conventional Commits** según el tipo de cambio realizado:

| Tipo | Cuándo usar |
|------|-------------|
| `feat` | Nueva funcionalidad para el usuario |
| `fix` | Corrección de un bug |
| `docs` | Cambios solo en documentación |
| `style` | Formato sin cambio de lógica (linting, espacios) |
| `refactor` | Reestructura sin cambiar comportamiento externo |
| `perf` | Mejora de rendimiento |
| `test` | Agrega o corrige pruebas |
| `build` | Cambios en build o dependencias (requirements.txt, Dockerfile) |
| `ci` | Cambios en CI/CD (GitHub Actions, workflows) |
| `chore` | Mantenimiento que no toca src ni tests |
| `revert` | Revierte un commit previo |
| `hotfix` | Corrección urgente en producción |
| `wip` | Trabajo en progreso (solo en ramas, nunca en main) |

**Formato:** `tipo(scope): descripción corta en minúsculas`

Ejemplos:
- `feat(docker): agregar Dockerfile con Chrome y Selenium`
- `fix(scraper): corregir timeout en paginación`
- `docs: actualizar DOCKER.md con guía Railway`
- `refactor(exporter): extraer lógica de formato a helper`

## 3. Preparar y hacer commit

1. Agregar archivos al staging:
   - Todo: `git add .`
   - Selectivo: `git add Dockerfile docker-compose.yml` (preferido para commits atómicos)
2. Revisar lo que se va a commitear: `git diff --staged --stat`
3. Hacer commit: `git commit -m "tipo(scope): descripción"`
4. Si el cambio toca múltiples áreas, hacer commits separados por tipo.

## 4. Push a GitHub

1. Push a la rama actual: `git push origin $(git branch --show-current)`
2. Si es la primera vez en esta rama: `git push -u origin $(git branch --show-current)`
3. Verificar en GitHub que el push llegó correctamente.

## 5. Post-push

1. Si se agregó Docker → Railway desplegará automáticamente (si está configurado)
2. Verificar GitHub Actions (workflows de Docker build)
3. Actualizar documentación si es necesario

## 6. Errores comunes

- **Push rechazado (non-fast-forward):** hacer `git pull --rebase origin main` antes de push.
- **Archivos sensibles (.env, tokens):** verificar `.gitignore` antes de `git add .`
- **Commit muy grande:** dividir en commits atómicos por tipo/scope.

## 7. Ejemplo de flujo completo para Docker

```bash
# 1. Verificar estado
git status

# 2. Agregar archivos Docker
git add Dockerfile docker-compose.yml .dockerignore entrypoint.sh

# 3. Commit
git commit -m "feat(docker): agregar configuración Docker con Chrome y Selenium"

# 4. Agregar documentación
git add DOCKER.md QUICKSTART-DOCKER.md README.md

# 5. Commit documentación
git commit -m "docs: agregar guías de Docker y Railway"

# 6. Agregar workflows
git add .github/workflows/ railway.json

# 7. Commit CI/CD
git commit -m "ci: agregar workflows GitHub y configuración Railway"

# 8. Push
git push origin main
```
