# AI Analytics Studio - Guía de Usuario

## 🎯 Descripción

**AI Analytics Studio** es una experiencia premium de analítica inmobiliaria potenciada por IA local (Ollama). Proporciona una interfaz moderna tipo ChatGPT/Claude con control completo sobre el servidor Ollama y métricas de ejecución en tiempo real.

## ✨ Características Principales

### 1. Chat Inteligente con IA
- **Interfaz moderna** tipo ChatGPT con mensajes animados
- **Renderizado Markdown** para respuestas formateadas
- **Preguntas rápidas** predefinidas para análisis comunes
- **Historial de conversación** persistente durante la sesión

### 2. Panel de Control de Ollama
- **Estado en tiempo real** del servidor Ollama
- **Verificación automática** cada 30 segundos
- **Gestión de modelos** disponibles
- **Cambio de modelo** en tiempo real (próximamente)
- **Información de puerto** y conectividad

### 3. Métricas de Ejecución
Cada respuesta del agente incluye:
- ⏱️ **Latencia** - Tiempo de respuesta en milisegundos
- 🔢 **Tokens** - Cantidad de tokens procesados
- 🖥️ **Modelo** - Modelo utilizado para la respuesta

### 4. Métricas de Sesión
Panel lateral con estadísticas acumuladas:
- **Consultas totales** - Número de preguntas realizadas
- **Tokens totales** - Suma de todos los tokens procesados
- **Latencia promedio** - Tiempo promedio de respuesta
- **Barras de progreso** visuales para cada métrica

### 5. Gestión de Modelos
- **Lista de modelos** instalados en Ollama
- **Tamaño de cada modelo** en MB/GB
- **Modelo activo** destacado visualmente
- **Cambio de modelo** con un clic

## 🚀 Cómo Usar

### Acceso
1. Iniciar sesión en el dashboard
2. Navegar a **AI Analytics** en el menú lateral
3. El icono tiene un gradiente azul-púrpura distintivo

### Realizar Consultas

#### Opción 1: Escribir pregunta personalizada
```
Escribe tu pregunta en el campo de texto y presiona "Analizar"
```

#### Opción 2: Usar preguntas rápidas
Haz clic en uno de los botones predefinidos:
- 💎 **Mejores oportunidades** - Detecta propiedades con mejor relación precio/valor
- 📊 **Precio por m²** - Análisis de precios por metro cuadrado
- 🔄 **Comparar zonas** - Comparativa entre diferentes comunas

### Ejemplos de Preguntas

**Análisis de Oportunidades:**
```
¿Cuáles son las mejores oportunidades de inversión actualmente?
```

**Análisis por Zona:**
```
¿Cuál es el precio promedio por m² en Las Condes?
Compara precios entre Providencia y Ñuñoa
```

**Tendencias:**
```
¿Qué tipo de propiedad tiene mejor relación precio/calidad?
Muéstrame las propiedades más baratas en Santiago Centro
```

**Estadísticas:**
```
¿Cuántas propiedades tenemos por comuna?
¿Cuál es el rango de precios en Vitacura?
```

## 📊 Panel de Control

### Estado de Ollama

**Indicadores:**
- 🟢 **Online** - Servidor funcionando correctamente
- 🔴 **Offline** - Servidor no disponible
- 🟡 **Checking** - Verificando estado

**Acciones:**
- Botón **Verificar Estado** para actualización manual
- Actualización automática cada 30 segundos

### Métricas en Tiempo Real

**Durante cada consulta:**
1. Indicador de carga con barra de progreso animada
2. Mensaje "Analizando datos..."
3. Al completar: métricas debajo de la respuesta

**Métricas mostradas:**
- ⏱️ Duración en milisegundos
- 🔢 Tokens procesados
- 🖥️ Modelo utilizado

### Panel Lateral (Settings)

**Toggle con botón de configuración** en la esquina superior derecha

**Secciones:**
1. **Ollama Server** - Estado y configuración
2. **Métricas de Sesión** - Estadísticas acumuladas
3. **Modelos Disponibles** - Lista de modelos instalados

## 🎨 Diseño Visual

### Paleta de Colores
- **Gradientes azul-púrpura** para elementos principales
- **Slate** para texto y fondos neutros
- **Verde** para indicadores positivos
- **Rojo** para errores

### Animaciones
- **Fade-in** para mensajes nuevos
- **Pulse** para indicador de estado online
- **Bounce** para indicador de carga
- **Progress bar** animada durante procesamiento

### Tipografía
- **Font-mono** para datos técnicos (modelo, puerto)
- **Font-semibold** para títulos
- **Prose** para contenido de mensajes

## 🔧 Configuración Técnica

### Endpoints Utilizados

**Chat con IA:**
```
POST /api/v2/agent/chat
Headers: X-API-KEY, Content-Type: application/json
Body: { "question": "..." }
```

**Estado de Ollama:**
```
GET http://localhost:11434/api/tags
```

### Variables de Entorno
```bash
OLLAMA_HOST=0.0.0.0:11434
OLLAMA_MODELS=/app/.ollama/models
```

### Modelo por Defecto
```
qwen2.5-coder:1.5b (~900MB)
```

## 📈 Métricas y Rendimiento

### Latencia Esperada
- **Consultas simples:** 500-1500ms
- **Consultas complejas:** 1500-3000ms
- **Consultas con datos extensos:** 3000-5000ms

### Uso de Tokens
- **Pregunta corta:** ~50-100 tokens
- **Pregunta media:** ~100-200 tokens
- **Pregunta compleja:** ~200-400 tokens
- **Respuesta promedio:** ~200-500 tokens

### Optimización
- **Cache de contexto** para preguntas similares
- **Límite de caracteres** en input (500)
- **Timeout de 30 segundos** en requests

## 🐛 Troubleshooting

### Ollama muestra "Offline"

**Verificar:**
```bash
# Dentro del contenedor
docker exec scraper-mvp supervisorctl status ollama

# Ver logs
docker exec scraper-mvp tail -f /var/log/ollama.log

# Reiniciar servicio
docker exec scraper-mvp supervisorctl restart ollama
```

### Respuestas lentas

**Causas comunes:**
1. Modelo muy grande para el hardware
2. Múltiples consultas simultáneas
3. Dataset muy extenso

**Soluciones:**
- Usar modelo más pequeño (1.5b en lugar de 3b)
- Esperar a que termine consulta anterior
- Limitar contexto de datos enviados

### Error de conexión

**Verificar:**
1. Puerto 11434 expuesto en Docker
2. Ollama corriendo en contenedor
3. API key correcta en headers

## 🚀 Próximas Mejoras

- [ ] **Exportar conversación** a PDF/Markdown
- [ ] **Historial persistente** en base de datos
- [ ] **Gráficos generados por IA** en respuestas
- [ ] **Modo oscuro** para la interfaz
- [ ] **Voz a texto** para consultas
- [ ] **Sugerencias automáticas** basadas en historial
- [ ] **Compartir conversaciones** con equipo
- [ ] **Integración con dashboard** principal

## 📚 Referencias

- [Ollama API Documentation](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [Marked.js Documentation](https://marked.js.org/)
- [Alpine.js Documentation](https://alpinejs.dev/)
- [Tailwind CSS](https://tailwindcss.com/)

---

**Versión:** 1.0.0  
**Última actualización:** 10 de Abril, 2026  
**Autor:** AI Dev Engine (Cascade)
