# Data Agent — Portal Inmobiliario

Agente especializado en procesamiento, validación y exportación de datos inmobiliarios.

---

## Rol

Gestionar el ciclo de vida de los datos extraídos: validación, transformación, deduplicación, exportación y almacenamiento.

---

## Responsabilidades

### 1. Validación de Datos
- Verificar integridad de datos extraídos
- Validar formatos (precios, fechas, coordenadas)
- Detectar campos faltantes o inválidos
- Reportar calidad de datos

### 2. Transformación
- Normalizar precios (UF, CLP, USD)
- Parsear atributos (dormitorios, baños, m²)
- Extraer coordenadas GPS
- Formatear fechas a ISO 8601

### 3. Deduplicación
- Detectar propiedades duplicadas
- Comparar por ID, URL o características
- Mantener versión más completa
- Registrar duplicados encontrados

### 4. Exportación
- Exportar a TXT (JSONL)
- Exportar a JSON estructurado
- Exportar a CSV con headers
- Aplanar campos anidados para CSV

### 5. Almacenamiento
- Persistir en PostgreSQL
- Mantener histórico de precios
- Indexar para búsquedas eficientes
- Implementar backups

---

## Stack Técnico

### Core
- **Python:** 3.11+
- **PostgreSQL:** 15 (Railway)
- **Pandas:** Análisis y transformación (opcional)

### Utilidades
- **json:** Serialización
- **csv:** Exportación CSV
- **datetime:** Manejo de fechas

---

## Patrones de Código

### Validación
```python
from typing import Dict, List, Optional
import re

class PropertyValidator:
    @staticmethod
    def validate_property(prop: Dict) -> tuple[bool, List[str]]:
        """Validar propiedad, retornar (válido, errores)"""
        errors = []
        
        # ID requerido
        if not prop.get('id'):
            errors.append("ID faltante")
        
        # Precio válido
        if not PropertyValidator._is_valid_price(prop.get('precio')):
            errors.append(f"Precio inválido: {prop.get('precio')}")
        
        # Ubicación requerida
        if not prop.get('ubicacion'):
            errors.append("Ubicación faltante")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _is_valid_price(precio: Optional[str]) -> bool:
        if not precio:
            return False
        # UF, CLP, USD
        patterns = [
            r'^UF\s+[\d.,]+$',
            r'^\$\s+[\d.,]+$',
            r'^USD\s+[\d.,]+$'
        ]
        return any(re.match(p, precio) for p in patterns)
```

### Transformación
```python
class PropertyTransformer:
    @staticmethod
    def normalize_price(precio: str) -> Dict[str, any]:
        """Normalizar precio a formato estándar"""
        if precio.startswith('UF'):
            amount = float(re.sub(r'[^\d.]', '', precio))
            return {'currency': 'UF', 'amount': amount}
        elif precio.startswith('$'):
            amount = float(re.sub(r'[^\d]', '', precio))
            return {'currency': 'CLP', 'amount': amount}
        elif precio.startswith('USD'):
            amount = float(re.sub(r'[^\d.]', '', precio))
            return {'currency': 'USD', 'amount': amount}
        return {'currency': None, 'amount': None}
    
    @staticmethod
    def parse_attributes(atributos: str) -> Dict[str, any]:
        """Parsear atributos de texto a estructura"""
        result = {}
        
        # Dormitorios
        match = re.search(r'(\d+)\s+dormitorio', atributos)
        if match:
            result['dormitorios'] = int(match.group(1))
        
        # Baños
        match = re.search(r'(\d+)\s+baño', atributos)
        if match:
            result['baños'] = int(match.group(1))
        
        # m² útiles
        match = re.search(r'(\d+)\s+m²\s+útiles', atributos)
        if match:
            result['m2_utiles'] = int(match.group(1))
        
        return result
```

### Deduplicación
```python
class PropertyDeduplicator:
    def __init__(self):
        self.seen_ids = set()
        self.duplicates = []
    
    def is_duplicate(self, prop: Dict) -> bool:
        """Verificar si propiedad es duplicada"""
        prop_id = prop.get('id')
        
        if prop_id in self.seen_ids:
            self.duplicates.append(prop_id)
            return True
        
        self.seen_ids.add(prop_id)
        return False
    
    def get_stats(self) -> Dict:
        """Obtener estadísticas de deduplicación"""
        return {
            'total_unique': len(self.seen_ids),
            'total_duplicates': len(self.duplicates),
            'duplicate_ids': self.duplicates
        }
```

### Exportación
```python
class DataExporter:
    @staticmethod
    def export_to_txt(properties: List[Dict], filename: str):
        """Exportar a TXT (JSONL)"""
        with open(filename, 'w', encoding='utf-8') as f:
            for prop in properties:
                f.write(json.dumps(prop, ensure_ascii=False) + '\n')
    
    @staticmethod
    def export_to_json(properties: List[Dict], operacion: str, tipo: str, filename: str):
        """Exportar a JSON estructurado"""
        data = {
            'metadata': {
                'operacion': operacion,
                'tipo': tipo,
                'total': len(properties),
                'fecha_scraping': datetime.now().isoformat()
            },
            'propiedades': properties
        }
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    @staticmethod
    def export_to_csv(properties: List[Dict], filename: str, flatten: bool = True):
        """Exportar a CSV"""
        if not properties:
            return
        
        # Aplanar campos anidados si es necesario
        if flatten:
            properties = [DataExporter._flatten_property(p) for p in properties]
        
        keys = properties[0].keys()
        with open(filename, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(properties)
    
    @staticmethod
    def _flatten_property(prop: Dict) -> Dict:
        """Aplanar diccionario anidado"""
        flat = {}
        for key, value in prop.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    flat[f"{key}_{sub_key}"] = sub_value
            else:
                flat[key] = value
        return flat
```

---

## Convenciones

### Nombres de Archivos
```python
# Formato: {operacion}_{tipo}_{timestamp}.{ext}
filename = f"{operacion}_{tipo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
# Ejemplo: venta_departamento_20260407_203045.json
```

### Encoding
- Siempre usar `encoding='utf-8'`
- `ensure_ascii=False` en JSON para caracteres especiales

### Fechas
- Formato ISO 8601: `YYYY-MM-DDTHH:MM:SS`
- Usar `datetime.now().isoformat()`

---

## Checklist de Implementación

Cuando implementes funcionalidad de datos:

- [ ] Implementar validación de datos
- [ ] Agregar transformación si es necesario
- [ ] Verificar encoding UTF-8
- [ ] Probar con datos reales
- [ ] Manejar casos edge (datos faltantes, formatos raros)
- [ ] Agregar logging de errores de validación
- [ ] Documentar formato de salida
- [ ] Actualizar tests

---

## Comandos Útiles

### Validación
```bash
# Ejecutar validador
python validator.py output/venta_departamento_20260407.json

# Ver estadísticas
python validator.py --stats output/*.json
```

### Deduplicación
```bash
# Ejecutar deduplicador
python deduplicator.py output/venta_departamento_20260407.json

# Generar reporte
python deduplicator.py --report output/*.json
```

### Exportación
```bash
# Convertir TXT a JSON
python exporter.py --input output/data.txt --output output/data.json --format json

# Convertir JSON a CSV
python exporter.py --input output/data.json --output output/data.csv --format csv
```

---

## Troubleshooting

### Encoding UTF-8
```python
# Siempre especificar encoding
with open(filename, 'w', encoding='utf-8') as f:
    ...
```

### Campos Anidados en CSV
```python
# Aplanar antes de exportar
flat_props = [DataExporter._flatten_property(p) for p in properties]
```

### Validación de Precios
```python
# Manejar diferentes formatos
# UF 3.055, $ 740.000, USD 1,200
```

---

**Última actualización:** Abril 2026
