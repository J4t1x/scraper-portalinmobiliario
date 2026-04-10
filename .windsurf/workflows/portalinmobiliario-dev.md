---
description: Levantar y ejecutar el scraper de portalinmobiliario (setup, scraping, export)
---

# Workflow: Desarrollo del Scraper Portal Inmobiliario

## 1. Setup Inicial

### 1.1 Verificar entorno virtual
```bash
cd /Users/ja/Documents/GitHub/scraper-portalinmobiliario
```

### 1.2 Activar/Crear entorno virtual
```bash
# Si no existe venv, crearlo
python3 -m venv venv

# Activar venv
source venv/bin/activate
```

### 1.3 Instalar dependencias
```bash
pip install -r requirements.txt
```

### 1.4 Configurar variables de entorno
```bash
# Si no existe .env, copiarlo desde .env.example
cp .env.example .env

# Verificar configuración
cat .env
```

**Variables disponibles:**
- `DELAY_BETWEEN_REQUESTS=2` — Segundos entre requests
- `MAX_RETRIES=3` — Intentos máximos por página
- `TIMEOUT=30` — Timeout de requests (segundos)
- `USER_AGENT` — User agent personalizado

---

## 2. Ejecutar Scraper

### 2.1 Scraping básico (departamentos en venta)
```bash
python main.py --operacion venta --tipo departamento
```

### 2.2 Scraping con límite de páginas
```bash
python main.py --operacion venta --tipo departamento --max-pages 5
```

### 2.3 Scraping con formato JSON
```bash
python main.py --operacion venta --tipo departamento --formato json
```

### 2.4 Scraping con formato CSV
```bash
python main.py --operacion arriendo --tipo casa --formato csv
```

### 2.5 Modo verbose (debug)
```bash
python main.py --operacion venta --tipo terreno --verbose
```

**Tipos de operación disponibles:**
- `venta`
- `arriendo`
- `arriendo-de-temporada`

**Tipos de propiedad disponibles:**
- `departamento`
- `casa`
- `oficina`
- `terreno`
- `local-comercial`
- `bodega`
- `estacionamiento`
- `parcela`

---

## 3. Verificar Resultados

### 3.1 Listar archivos generados
```bash
ls -lh output/
```

### 3.2 Ver contenido de salida TXT
```bash
cat output/venta_departamento_*.txt
```

### 3.3 Ver contenido de salida JSON
```bash
cat output/venta_departamento_*.json | jq .
```

### 3.4 Ver contenido de salida CSV
```bash
cat output/arriendo_casa_*.csv
```

---

## 4. Desarrollo con Docker (Opcional)

### 4.1 Build de imagen Docker
```bash
docker build -t portalinmobiliario:latest .
```

### 4.2 Ejecutar con Docker
```bash
docker run --rm \
  -v $(pwd)/output:/app/output \
  portalinmobiliario:latest \
  python main.py --operacion venta --tipo departamento --max-pages 2
```

### 4.3 Ejecutar con Docker Compose
```bash
# Levantar servicios (incluye PostgreSQL)
docker-compose up -d

# Ejecutar scraper
docker-compose run --rm scraper python main.py --operacion venta --tipo departamento

# Ver logs
docker-compose logs -f scraper

# Detener servicios
docker-compose down
```

---

## 5. Testing y Debugging

### 5.1 Ejecutar script de ejemplo
```bash
python example.py
```

### 5.2 Test con Selenium (si es necesario)
```bash
python scraper_selenium.py
```

### 5.3 Verificar configuración
```bash
python -c "from config import Config; print(Config.DELAY_BETWEEN_REQUESTS)"
```

---

## 6. Limpieza

### 6.1 Limpiar archivos de salida
```bash
rm -rf output/*
```

### 6.2 Limpiar cache de Python
```bash
rm -rf __pycache__
find . -type d -name "__pycache__" -exec rm -rf {} +
```

### 6.3 Desactivar entorno virtual
```bash
deactivate
```

---

## 7. Comandos Útiles

### 7.1 Ver ayuda del scraper
```bash
python main.py --help
```

### 7.2 Actualizar dependencias
```bash
pip install --upgrade -r requirements.txt
```

### 7.3 Congelar dependencias actuales
```bash
pip freeze > requirements.txt
```

### 7.4 Ver logs en tiempo real (si se implementa logging a archivo)
```bash
tail -f logs/scraper.log
```

---

## 8. Troubleshooting

### 8.1 Error de módulos no encontrados
```bash
# Reinstalar dependencias
pip install -r requirements.txt --force-reinstall
```

### 8.2 Error de permisos en output/
```bash
mkdir -p output
chmod 755 output
```

### 8.3 Error de timeout
```bash
# Editar .env y aumentar TIMEOUT
echo "TIMEOUT=60" >> .env
```

### 8.4 Error de rate limiting
```bash
# Editar .env y aumentar DELAY_BETWEEN_REQUESTS
echo "DELAY_BETWEEN_REQUESTS=5" >> .env
```

---

## Notas

- **Stack:** Python 3.x + requests + BeautifulSoup4 + Selenium (opcional)
- **Output:** `output/` (se crea automáticamente)
- **Formatos:** TXT (JSONL), JSON, CSV
- **Docker:** Listo para Railway con PostgreSQL
- **Docs:** Ver `docs/README.md` para documentación completa
