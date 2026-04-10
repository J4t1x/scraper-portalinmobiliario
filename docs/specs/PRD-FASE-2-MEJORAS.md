# PRD - Fase 2: Mejoras del Scraper

**Versión:** 1.0  
**Fecha:** 8 de Abril, 2026  
**Estado:** Planificación  
**Owner:** Equipo de Desarrollo

---

## 1. Resumen Ejecutivo

### 1.1 Objetivo
Mejorar la robustez, calidad de datos y mantenibilidad del scraper de Portal Inmobiliario mediante la implementación de funcionalidades avanzadas de extracción, validación y logging.

### 1.2 Alcance
- Extracción de datos de páginas de detalle
- Sistema de logging robusto con rotación
- Validación y sanitización de datos
- Detección de duplicados
- Tests unitarios completos

### 1.3 Métricas de Éxito
- **Calidad de datos:** 95% de propiedades con datos completos
- **Cobertura de tests:** ≥80%
- **Duplicados:** <1% de registros duplicados
- **Logging:** 100% de operaciones loggeadas
- **Tiempo de scraping:** Incremento <20% vs versión actual

---

## 2. Contexto y Motivación

### 2.1 Problema Actual
La Fase 1 (MVP) implementó scraping básico de listados, pero presenta limitaciones:
- Solo extrae datos de la página de listado (información limitada)
- No valida la calidad de los datos extraídos
- Logging básico sin rotación (archivos crecen indefinidamente)
- No detecta duplicados entre ejecuciones
- Sin tests unitarios (riesgo de regresiones)

### 2.2 Oportunidad
Mejorar la calidad y confiabilidad del scraper para:
- Obtener datos más completos (descripción, características detalladas, contacto)
- Garantizar consistencia de datos
- Facilitar debugging y monitoreo
- Prevenir duplicados en la base de datos
- Reducir riesgo de bugs en futuras modificaciones

### 2.3 Stakeholders
- **Usuarios finales:** Analistas de datos, inversores inmobiliarios
- **Desarrolladores:** Equipo de desarrollo y mantenimiento
- **DevOps:** Equipo de operaciones y monitoreo

---

## 3. Especificaciones Funcionales

### 3.1 Feature 1: Scraping de Página de Detalle

**Descripción:** Extraer información adicional de la página de detalle de cada propiedad.

**Datos adicionales a extraer:**
- Descripción completa del inmueble
- Características detalladas (orientación, año construcción, gastos comunes)
- Información del publicador (nombre, tipo: inmobiliaria/particular)
- Galería de imágenes (URLs)
- Coordenadas GPS (si disponibles)
- Fecha de publicación
- ID de publicador

**Prioridad:** Alta  
**Estimación:** 8 horas

---

### 3.2 Feature 2: Sistema de Logging Robusto

**Descripción:** Implementar logging estructurado con rotación automática de archivos.

**Requisitos:**
- Logs en formato JSON estructurado
- Rotación diaria con compresión de archivos antiguos
- Retención de logs: 30 días
- Niveles: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Contexto: timestamp, nivel, módulo, mensaje, metadata
- Logs separados por tipo: scraping, errores, performance

**Prioridad:** Media  
**Estimación:** 4 horas

---

### 3.3 Feature 3: Validación de Datos

**Descripción:** Validar y sanitizar datos extraídos antes de exportar.

**Validaciones:**
- **ID:** Formato válido (MLC-XXXXXXXX)
- **Precio:** Formato numérico válido (UF o $)
- **Ubicación:** No vacía, formato consistente
- **Atributos:** Valores numéricos válidos (dormitorios, baños, m²)
- **URL:** URL válida y accesible
- **Tipo/Operación:** Valores permitidos según config

**Sanitización:**
- Eliminar espacios en blanco extras
- Normalizar formatos de precio
- Estandarizar nombres de comunas
- Convertir tipos de datos (strings → números donde corresponda)

**Prioridad:** Alta  
**Estimación:** 6 horas

---

### 3.4 Feature 4: Detección de Duplicados

**Descripción:** Identificar y marcar propiedades duplicadas entre ejecuciones.

**Estrategia:**
- Usar ID de propiedad como clave primaria
- Mantener registro de IDs scrapeados en archivo JSON
- Comparar con ejecuciones anteriores
- Marcar duplicados con flag `is_duplicate: true`
- Opción CLI para incluir/excluir duplicados en export

**Prioridad:** Media  
**Estimación:** 4 horas

---

### 3.5 Feature 5: Tests Unitarios

**Descripción:** Implementar suite completa de tests con pytest.

**Cobertura:**
- Tests de scraper (mocking de requests)
- Tests de exporter (validación de formatos)
- Tests de validación de datos
- Tests de detección de duplicados
- Tests de configuración
- Tests de utilidades

**Requisitos:**
- Cobertura ≥80%
- Tests aislados (sin dependencias externas)
- Fixtures reutilizables
- CI/CD integration ready

**Prioridad:** Alta  
**Estimación:** 8 horas

---

## 4. Especificaciones No Funcionales

### 4.1 Performance
- Scraping de detalle no debe incrementar tiempo total >20%
- Validación debe ejecutarse en <100ms por propiedad
- Detección de duplicados en <500ms para 10,000 registros

### 4.2 Confiabilidad
- Manejo de errores en scraping de detalle (fallback a datos básicos)
- Logs nunca deben causar falla del scraper
- Validación no debe bloquear export (warnings en lugar de errores)

### 4.3 Mantenibilidad
- Código modular y testeable
- Documentación inline (docstrings)
- Configuración centralizada
- Logs estructurados para análisis automatizado

### 4.4 Escalabilidad
- Sistema de logging preparado para alto volumen
- Detección de duplicados eficiente (O(1) lookup)
- Tests rápidos (<30s suite completa)

---

## 5. Dependencias

### 5.1 Técnicas
- **pytest:** Framework de testing
- **pytest-cov:** Cobertura de tests
- **logging.handlers:** Rotación de logs
- **jsonschema:** Validación de schemas

### 5.2 Externas
- Ninguna (todas las dependencias son Python estándar o ya instaladas)

---

## 6. Plan de Implementación

### 6.1 Fases

#### Fase 2.1: Scraping de Detalle (Sprint 1)
- SPEC-002: Implementar scraping de página de detalle
- SPEC-003: Integrar datos de detalle en exportación

#### Fase 2.2: Calidad de Datos (Sprint 2)
- SPEC-004: Sistema de validación de datos
- SPEC-005: Detección de duplicados

#### Fase 2.3: Infraestructura (Sprint 3)
- SPEC-006: Sistema de logging robusto
- SPEC-007: Suite de tests unitarios

### 6.2 Timeline
- **Sprint 1:** 2 semanas (Scraping de detalle)
- **Sprint 2:** 2 semanas (Calidad de datos)
- **Sprint 3:** 2 semanas (Infraestructura)
- **Total:** 6 semanas

---

## 7. Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Cambios en HTML de detalle | Media | Alto | Implementar fallback a datos básicos |
| Performance degradado | Baja | Medio | Paralelizar requests de detalle |
| Logs llenan disco | Baja | Alto | Rotación automática + monitoreo |
| Tests frágiles | Media | Medio | Usar mocks y fixtures estables |

---

## 8. Criterios de Aceptación

### 8.1 Feature Completo
- [ ] Todas las specs implementadas y validadas
- [ ] Tests pasando con cobertura ≥80%
- [ ] Documentación actualizada
- [ ] Logs rotando correctamente
- [ ] Validación funcionando sin bloquear export

### 8.2 Calidad
- [ ] Code review aprobado
- [ ] Sin errores de lint
- [ ] Performance dentro de límites
- [ ] Manejo de errores robusto

### 8.3 Deployment
- [ ] Docker image actualizado
- [ ] Variables de entorno documentadas
- [ ] Railway deployment exitoso
- [ ] Smoke tests en producción

---

## 9. Métricas de Seguimiento

### 9.1 Durante Desarrollo
- Velocidad de desarrollo (story points/sprint)
- Bugs encontrados en testing
- Cobertura de tests (objetivo: 80%)
- Tiempo de ejecución de tests

### 9.2 Post-Deployment
- Tasa de éxito de scraping de detalle
- Porcentaje de datos validados exitosamente
- Cantidad de duplicados detectados
- Tamaño promedio de logs generados
- Tiempo total de scraping (comparado con Fase 1)

---

## 10. Referencias

- [README.md](../../README.md) - Documentación principal
- [PRD Fase 1](./prd.md) - MVP completado
- [ARCHITECTURE.md](../ARCHITECTURE.md) - Arquitectura del sistema
- [SDD Methodology](../../../SDD-jard/docs/SDD-METHODOLOGY.md) - Metodología de desarrollo

---

## 11. Aprobaciones

| Rol | Nombre | Fecha | Estado |
|-----|--------|-------|--------|
| Product Owner | - | - | Pendiente |
| Tech Lead | - | - | Pendiente |
| DevOps Lead | - | - | Pendiente |

---

**Última actualización:** 8 de Abril, 2026  
**Próxima revisión:** Al completar Sprint 1
