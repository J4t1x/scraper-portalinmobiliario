# 🚀 Guía Rápida de Inicio

## Instalación en 3 pasos

### 1️⃣ Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2️⃣ Configurar entorno (opcional)

```bash
cp .env.example .env
```

### 3️⃣ Ejecutar

```bash
python main.py --operacion venta --tipo departamento
```

---

## 📝 Comandos más usados

### Scrapear departamentos en venta

```bash
python main.py --operacion venta --tipo departamento
```

### Scrapear casas en arriendo (máximo 5 páginas)

```bash
python main.py --operacion arriendo --tipo casa --max-pages 5
```

### Exportar a JSON

```bash
python main.py --operacion venta --tipo oficina --formato json
```

### Exportar a CSV

```bash
python main.py --operacion arriendo --tipo departamento --formato csv
```

---

## 🎯 Operaciones disponibles

- `venta`
- `arriendo`
- `arriendo-de-temporada`

## 🏘️ Tipos de propiedad disponibles

- `departamento`
- `casa`
- `oficina`
- `terreno`
- `local-comercial`
- `bodega`
- `estacionamiento`
- `parcela`

---

## 📊 Formatos de exportación

- `txt` - Una propiedad por línea (JSON-like)
- `json` - Archivo JSON estructurado con metadata
- `csv` - Archivo CSV para Excel/Google Sheets

---

## 🔍 Ver resultados

Los archivos se guardan en la carpeta `output/` con el formato:

```
output/venta_departamento_20260318_103000.txt
```

---

## 💡 Ejemplos de uso programático

Ver archivo `example.py` para ejemplos de cómo usar el scraper en tu propio código Python.

```bash
python example.py
```

---

## ⚠️ Solución de problemas

### Error: ModuleNotFoundError

```bash
pip install -r requirements.txt
```

### Error: Connection timeout

Aumenta el timeout en `.env`:

```env
TIMEOUT=60
```

### Muy lento

Reduce el delay en `.env`:

```env
DELAY_BETWEEN_REQUESTS=1
```

---

## 📚 Más información

Ver `README.md` para documentación completa.
