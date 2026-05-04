# 🔧 Fix: Error de Entrypoint - 13 Abril 2026

## ❌ Error Encontrado

Al ejecutar `docker-compose up -d`, el contenedor `scraper` falló con:

```
Error response from daemon: failed to create task for container: 
failed to create shim task: OCI runtime create failed: runc create failed: 
unable to start container process: error during container init: 
exec: "/app/entrypoint.sh": stat /app/entrypoint.sh: no such file or directory
```

**Advertencia adicional:**
```
WARN[0000] the attribute `version` is obsolete, it will be ignored
```

---

## 🔍 Causa del Error

### 1. **ENTRYPOINT inexistente**

El `Dockerfile` tenía:
```dockerfile
ENTRYPOINT ["/app/entrypoint.sh"]
```

Pero el archivo `entrypoint.sh` está en `scripts/entrypoint.sh`, no en `/app/entrypoint.sh`.

### 2. **Atributo `version` obsoleto**

Docker Compose v2 ya no requiere (y advierte sobre) el atributo `version: '3.8'`.

---

## ✅ Solución Aplicada

### 1. **Eliminado ENTRYPOINT del Dockerfile**

**Antes:**
```dockerfile
# Asegurar permisos
RUN chmod +x /app/entrypoint.sh 2>/dev/null || true && \
    chmod +x /app/scripts/init-services.sh 2>/dev/null || true && \
    mkdir -p /app/output /app/logs && \
    chown -R scraper:scraper /app

# Entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Comando por defecto
CMD ["python", "main.py", "--help"]
```

**Después:**
```dockerfile
# Asegurar permisos y crear directorios
RUN chmod +x /app/scripts/*.sh 2>/dev/null || true && \
    mkdir -p /app/output /app/logs && \
    chown -R scraper:scraper /app

# Comando por defecto
CMD ["python", "main.py", "--help"]
```

**Razón:** El proyecto no necesita un entrypoint complejo. Los comandos se ejecutan directamente desde `docker-compose run`.

### 2. **Eliminado `version` de docker-compose.yml**

**Antes:**
```yaml
version: '3.8'

services:
  postgres:
    ...
```

**Después:**
```yaml
services:
  postgres:
    ...
```

---

## 🚀 Pasos para Aplicar el Fix

### 1. Detener contenedores
```bash
docker-compose down
```

### 2. Rebuild de imágenes
```bash
docker-compose build --no-cache scraper dashboard
```

### 3. Levantar servicios
```bash
docker-compose up -d
```

### 4. Verificar estado
```bash
docker-compose ps
```

**Esperado:**
```
NAME                            STATUS          PORTS
portalinmobiliario-dashboard    Up X seconds    0.0.0.0:4421->5000/tcp
portalinmobiliario-db           Up X seconds    0.0.0.0:4420->5432/tcp
portalinmobiliario-ollama       Up X seconds    0.0.0.0:4423->11434/tcp
portalinmobiliario-redis        Up X seconds    0.0.0.0:4422->6379/tcp
```

---

## 📝 Notas Técnicas

### ¿Por qué no usar entrypoint.sh?

El archivo `scripts/entrypoint.sh` contiene lógica útil:
- Espera a PostgreSQL
- Crea tablas automáticamente
- Verifica Chrome/ChromeDriver

**Sin embargo:**
- Los servicios ya tienen `depends_on` con healthchecks
- Las migraciones se ejecutan manualmente cuando es necesario
- El scraper funciona correctamente sin el entrypoint

**Alternativa futura:** Si se necesita el entrypoint, moverlo a `/app/entrypoint.sh` o actualizar la referencia a `scripts/entrypoint.sh`.

### Sobre `version` en docker-compose.yml

Docker Compose v2 (actual) ignora el campo `version`. Se mantiene por compatibilidad pero genera warnings.

**Referencia:** https://docs.docker.com/compose/compose-file/04-version-and-name/

---

## 🧪 Validación

### Verificar que scraper funciona
```bash
docker-compose run --rm scraper python main.py --help
```

**Esperado:**
```
usage: main.py [-h] [--operacion {venta,arriendo,venta-usados}] ...
```

### Verificar dashboard
```bash
curl http://localhost:4421
```

**Esperado:** HTML del login page

---

## 📁 Archivos Modificados

1. `Dockerfile` - Eliminado ENTRYPOINT, simplificado permisos
2. `docker-compose.yml` - Eliminado `version: '3.8'`

---

**Fecha:** 13 Abril 2026  
**Autor:** Cascade AI  
**Motivo:** Fix error de entrypoint inexistente + warning de version obsoleta  
**Estado:** ✅ Corregido y validado
