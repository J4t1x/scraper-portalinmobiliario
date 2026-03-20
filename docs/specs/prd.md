scrapper portalinmobiliario.com
---

# 📄 PRD — Sistema de Captura de Datos de Portalinmobiliario

---

## 1. 🧭 Resumen del Producto

Desarrollar un sistema automatizado en Python que permita:

* Capturar datos de propiedades desde Portalinmobiliario
* Navegar dinámicamente por:

  * Tipo de operación (venta, arriendo, etc.)
  * Tipo de propiedad
* Recorrer todas las páginas disponibles (paginación)
* Extraer datos estructurados
* Exportarlos a archivo `.txt` (y extensible a otros formatos)

---

## 2. 🎯 Objetivos

### Objetivo principal

Construir un scraper robusto que permita obtener información completa de propiedades para análisis, monitoreo o integración futura.

### Objetivos secundarios

* Automatizar la recolección de datos
* Permitir escalabilidad a múltiples categorías
* Preparar base para analítica inmobiliaria

---

## 3. 👤 Usuarios Objetivo

* Desarrolladores / Data Engineers
* Analistas inmobiliarios
* Plataformas PropTech
* Emprendimientos de agregación de propiedades

---

## 4. 🧩 Alcance

### ✔️ Incluye

* Scraping de listados
* Manejo de paginación
* Parametrización de URL
* Extracción de datos básicos
* Exportación a `.txt`

### ❌ No incluye (fase inicial)

* UI / frontend
* Base de datos
* Scraping distribuido
* Machine Learning

---

## 5. ⚙️ Funcionalidades

### 5.1 Configuración dinámica

El sistema debe permitir definir:

* Tipo de operación:

  * venta
  * arriendo
  * arriendo-de-temporada

* Tipo de propiedad:

  * departamento
  * casa
  * oficina
  * terreno
  * etc.

---

### 5.2 Construcción de URL

Formato base:

```
https://www.portalinmobiliario.com/{operacion}/{tipo}
```

Paginación:

```
_Desde_{offset}
```

Ejemplo:

```
https://www.portalinmobiliario.com/venta/departamento_Desde_50
```

---

### 5.3 Navegación con paginación

El sistema debe:

* Iterar automáticamente páginas
* Detectar fin de resultados
* Evitar loops infinitos

---

### 5.4 Extracción de datos

Por cada propiedad:

* Título
* Precio
* Ubicación
* URL detalle

### (Extensible — fase futura)

* Metros cuadrados
* Dormitorios
* Baños
* Coordenadas
* ID publicación

---

### 5.5 Exportación de datos

Formato inicial:

* `.txt` (una propiedad por línea, JSON-like)

Formato futuro:

* JSON
* CSV
* Base de datos (PostgreSQL)

---

### 5.6 Manejo de errores

El sistema debe:

* Ignorar items mal formateados
* Manejar errores HTTP
* Continuar ejecución ante fallos parciales

---

### 5.7 Control de velocidad

Para evitar bloqueos:

* Delay configurable entre requests
* User-Agent personalizado

---

## 6. 🏗️ Arquitectura

### Versión inicial (MVP)

```
Python Script
 ├── Configuración (operación/tipo)
 ├── Request HTTP
 ├── Parser (BeautifulSoup)
 ├── Paginador
 └── Exportador TXT
```

---

### Versión avanzada (recomendada)

```
Scraper Engine
 ├── URL Builder
 ├── Fetcher (requests / API interna)
 ├── Parser (HTML o JSON)
 ├── Queue (opcional)
 ├── Data Processor
 └── Storage Layer
```

---

## 7. 🔄 Flujo del sistema

1. Usuario define:

   * operación
   * tipo

2. Sistema construye URL

3. Ejecuta request

4. Parsea resultados

5. Guarda datos

6. Avanza paginación

7. Repite hasta terminar

---

## 8. ⚠️ Riesgos y Consideraciones

### Técnicos

* Cambios en estructura HTML
* Protección anti-bots
* Bloqueo por IP

### Legales

* Términos de uso del sitio
* Uso de datos recolectados

---

## 9. 🚀 Roadmap

### Fase 1 — MVP

* Scraper básico
* Exportación TXT
* Paginación funcional

---

### Fase 2 — Mejora

* Scraping de detalle
* Exportación JSON/CSV
* Logging

---

### Fase 3 — Pro

* Uso de endpoints internos (JSON)
* Base de datos
* Scheduler (cron)

---

### Fase 4 — Escalamiento

* Scraping distribuido
* API propia
* Dashboard analítico

---

## 10. 📊 Métricas de éxito

* % de páginas scrapeadas correctamente
* Cantidad de propiedades capturadas
* Tasa de errores
* Tiempo de ejecución

---

## 11. 🔮 Futuro (alto valor)

Esto puede evolucionar a:

* Comparador de precios inmobiliarios
* Sistema de alertas de oportunidades
* Modelo predictivo de precios
* API inmobiliaria propia

---

## 12. 🧠 Recomendación técnica clave

No te quedes solo en scraping HTML.

👉 Evoluciona a:

* Reverse engineering de API interna
* Pipeline de datos
* Persistencia estructurada

---