# Guía de Migración a PostgreSQL

**Última actualización:** Abril 2026

---

## Resumen

Esta guía explica cómo migrar datos scrapeados desde archivos exportados (TXT/JSON/CSV) a PostgreSQL utilizando el script de migración incluido en el proyecto.

---

## Requisitos Previos

### 1. Base de Datos PostgreSQL

Necesitas una instancia de PostgreSQL ejecutándose. Puedes usar:

- **Local:** PostgreSQL instalado en tu máquina
- **Docker:** PostgreSQL en contenedor Docker
- **Railway:** PostgreSQL provisionado en Railway

### 2. Variables de Entorno

Configura la variable `DATABASE_URL` en tu archivo `.env`:

```env
DATABASE_URL=postgresql://usuario:password@localhost:5432/scraper_db
```

Para Railway, esta variable se configura automáticamente en el dashboard.

---

## Script de Migración

El script principal se encuentra en `scripts/migrate_to_postgres.py`.

### Componentes

- **`scripts/data_reader.py`**: Lee archivos TXT (JSONL), JSON y CSV
- **`scripts/data_validator.py`**: Valida datos antes de inserción
- **`scripts/migrate_to_postgres.py`**: Orquesta la migración completa

---

## Uso Básico

### Migrar un Archivo Específico

```bash
python scripts/migrate_to_postgres.py output/venta_departamento_20260407.txt
```

### Migrar Todo el Directorio `output/`

```bash
python scripts/migrate_to_postgres.py output/
```

Esto migrará todos los archivos TXT, JSON y CSV en el directorio.

---

## Opciones Avanzadas

### Modo Dry-Run (Simulación)

Simula la migración sin insertar datos en la base de datos:

```bash
python scripts/migrate_to_postgres.py output/ --dry-run
```

Útil para:
- Verificar que los datos son válidos
- Estimar tiempo de migración
- Identificar errores antes de la migración real

### Generar Reporte JSON

Guarda un reporte detallado de la migración:

```bash
python scripts/migrate_to_postgres.py output/ --report migration_report.json
```

El reporte incluye:
- Total de registros procesados
- Registros exitosos
- Registros fallidos
- Duplicados detectados
- Lista de errores con detalles

### Manejo de Duplicados

Por defecto, el script salta propiedades duplicadas (basado en URL):

```bash
# Por defecto: saltar duplicados
python scripts/migrate_to_postgres.py output/

# Incluir duplicados (sobrescribir)
python scripts/migrate_to_postgres.py output/ --include-duplicates
```

### Customizar Batch Size

El tamaño del batch afecta el rendimiento. Por defecto es 100:

```bash
python scripts/migrate_to_postgres.py output/ --batch-size 50
```

**Recomendaciones:**
- **Archivos pequeños (< 100 propiedades):** `--batch-size 50`
- **Archivos medianos (100-1000 propiedades):** `--batch-size 100` (default)
- **Archivos grandes (> 1000 propiedades):** `--batch-size 200`

### URL de Base de Datos Personalizada

Especifica una URL de base de datos diferente:

```bash
python scripts/migrate_to_postgres.py output/ --database-url postgresql://user:pass@host:port/db
```

---

## Formatos Soportados

### TXT (JSONL)

Formato de un objeto JSON por línea:

```json
{"id": "MLC-3705621748", "titulo": "Departamento", "precio": "UF 3.055", "ubicacion": "Santiago", "url": "https://...", "operacion": "venta", "tipo": "departamento"}
{"id": "MLC-3225188606", "titulo": "Casa", "precio": "$ 740.000", "ubicacion": "Santiago", "url": "https://...", "operacion": "venta", "tipo": "casa"}
```

### JSON Estructurado

Formato con metadata y array de propiedades:

```json
{
  "metadata": {
    "operacion": "venta",
    "tipo": "departamento",
    "total": 2,
    "fecha_scraping": "2026-04-09T20:32:22"
  },
  "propiedades": [
    {"id": "MLC-1", "titulo": "Prop 1", ...},
    {"id": "MLC-2", "titulo": "Prop 2", ...}
  ]
}
```

### CSV

Formato tabular con headers:

```csv
id,titulo,precio,ubicacion,url,operacion,tipo
MLC-1,Departamento,UF 3.055,Santiago,https://...,venta,departamento
MLC-2,Casa,$ 740.000,Santiago,https://...,venta,casa
```

---

## Validación de Datos

El script valida cada propiedad antes de insertarla:

### Campos Requeridos

- `id`: ID único de la propiedad
- `titulo`: Título de la propiedad
- `precio`: Precio (formato válido)
- `ubicacion`: Ubicación/dirección
- `url`: URL completa
- `operacion`: Tipo de operación (venta, arriendo, arriendo-de-temporada)
- `tipo`: Tipo de propiedad (departamento, casa, oficina, etc.)

### Validaciones Adicionales

- **Formato de precio:** Debe ser UF, CLP ($), o USD
- **URL:** Debe ser una URL válida (http/https)
- **Fecha:** Si está presente, debe ser formato ISO 8601
- **Coordenadas:** Si están presentes, deben ser valores GPS válidos

---

## Ejemplos de Uso

### Ejemplo 1: Migración Inicial

```bash
# 1. Verificar datos con dry-run
python scripts/migrate_to_postgres.py output/ --dry-run

# 2. Migrar con reporte
python scripts/migrate_to_postgres.py output/ --report migration_initial.json

# 3. Verificar reporte
cat migration_initial.json
```

### Ejemplo 2: Migración Incremental

```bash
# Migrar solo archivos nuevos
python scripts/migrate_to_postgres.py output/venta_departamento_20260409.txt --dry-run

# Si está correcto, migrar realmente
python scripts/migrate_to_postgres.py output/venta_departamento_20260409.txt
```

### Ejemplo 3: Migración con Duplicados

```bash
# Si quieres actualizar datos existentes (sobrescribir)
python scripts/migrate_to_postgres.py output/ --include-duplicates
```

---

## Solución de Problemas

### Error: "DATABASE_URL not configured"

**Causa:** Variable de entorno no configurada.

**Solución:**
```bash
# En .env
DATABASE_URL=postgresql://usuario:password@localhost:5432/scraper_db

# O especificar en línea de comandos
python scripts/migrate_to_postgres.py output/ --database-url postgresql://...
```

### Error: "File not found"

**Causa:** Archivo o directorio no existe.

**Solución:**
```bash
# Verificar que existe
ls output/

# Usar ruta absoluta si es necesario
python scripts/migrate_to_postgres.py /ruta/absoluta/output/
```

### Error: "Invalid JSON format"

**Causa:** Archivo JSON no tiene el formato esperado.

**Solución:**
- Verificar que el archivo JSON tenga la clave `propiedades`
- O que sea un array directo de propiedades
- Verificar que el JSON sea válido (sintaxis correcta)

### Muchos Registros Fallidos

**Causa:** Datos inválidos o formato incorrecto.

**Solución:**
```bash
# Ejecutar con dry-run para ver errores
python scripts/migrate_to_postgres.py output/ --dry-run

# Revisar reporte para ver errores específicos
python scripts/migrate_to_postgres.py output/ --report errors.json
```

### Performance Lenta

**Causa:** Batch size muy pequeño o base de datos remota.

**Solución:**
```bash
# Aumentar batch size
python scripts/migrate_to_postgres.py output/ --batch-size 200

# Para Railway, considerar usar conexión más cercana
```

---

## Modelo de Datos

El script migra datos al siguiente esquema de base de datos:

### Tabla `properties`

```sql
CREATE TABLE properties (
    id SERIAL PRIMARY KEY,
    url VARCHAR(500) UNIQUE NOT NULL,
    portal_id VARCHAR(100),
    titulo VARCHAR(500),
    precio INTEGER,
    precio_moneda VARCHAR(10),
    precio_original VARCHAR(100),
    operacion VARCHAR(50),
    tipo VARCHAR(50),
    comuna VARCHAR(100),
    region VARCHAR(100),
    direccion VARCHAR(500),
    headline VARCHAR(500),
    atributos TEXT,
    descripcion TEXT,
    publicado_en TIMESTAMP,
    scrapeado_en TIMESTAMP DEFAULT NOW(),
    actualizado_en TIMESTAMP
);
```

### Tablas Relacionadas

- **`features`**: Características individuales (dormitorios, baños, m², etc.)
- **`images`**: URLs de imágenes de la propiedad
- **`publishers`**: Información del publicador (inmobiliaria/particular)

---

## Testing

### Ejecutar Tests Unitarios

```bash
# Tests de data reader
pytest tests/unit/test_data_reader.py -v

# Tests de data validator
pytest tests/unit/test_data_validator.py -v
```

### Ejecutar Tests de Integración

```bash
# Tests de migración (usa SQLite en memoria)
pytest tests/integration/test_migration.py -v
```

### Ejecutar Todos los Tests

```bash
pytest tests/ -v
```

---

## Buenas Prácticas

### 1. Siempre Usar Dry-Run Primero

```bash
python scripts/migrate_to_postgres.py output/ --dry-run
```

### 2. Generar Reporte

```bash
python scripts/migrate_to_postgres.py output/ --report report.json
```

### 3. Hacer Backup Antes de Migración

```bash
# Backup de PostgreSQL
pg_dump scraper_db > backup_pre_migration.sql
```

### 4. Validar Datos Después de Migración

```bash
# Conectar a PostgreSQL
psql $DATABASE_URL

# Verificar conteo
SELECT COUNT(*) FROM properties;

# Verificar datos de muestra
SELECT * FROM properties LIMIT 5;
```

### 5. Migración Incremental para Datasets Grandes

Para datasets muy grandes (>10,000 propiedades), considera migrar en lotes:

```bash
# Migrar archivo por archivo
python scripts/migrate_to_postgres.py output/file1.txt
python scripts/migrate_to_postgres.py output/file2.txt
# ...
```

---

## Métricas de Performance

### Tiempos Esperados

- **100 propiedades:** ~5-10 segundos
- **1,000 propiedades:** ~30-60 segundos
- **10,000 propiedades:** ~5-10 minutos

### Factores que Afectan Performance

- Velocidad de conexión a base de datos
- Complejidad de datos (imágenes, características)
- Batch size configurado
- Latencia de red (para bases de datos remotas)

---

## Roadmap de Mejoras

### Próximas Características Planeadas

- [ ] Soporte para migración incremental automática
- [ ] Paralelización de migración para archivos grandes
- [ ] Interfaz web para monitoreo de migración
- [ ] Reintento automático de registros fallidos
- [ ] Validación avanzada con reglas personalizables

---

## Soporte

Si encuentras problemas o tienes preguntas:

1. Revisa esta guía
2. Ejecuta con `--dry-run` para diagnosticar
3. Genera reporte con `--report` para análisis
4. Abre un issue en el repositorio

---

**Última revisión:** Abril 2026
