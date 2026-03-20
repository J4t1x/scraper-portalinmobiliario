# 📚 Documentación - Portal Inmobiliario Scraper

**Última actualización:** 20 de Marzo, 2026

## 📋 Índice de Documentación

### 🚀 Guías de Inicio Rápido
- **[QUICKSTART.md](guides/QUICKSTART.md)** - Inicio rápido (instalación local)
- **[QUICKSTART-DOCKER.md](deployment/QUICKSTART-DOCKER.md)** - Inicio rápido con Docker

### 🐳 Deployment
- **[DOCKER.md](deployment/DOCKER.md)** - Guía completa de Docker y Railway
- **[DEPLOYMENT-SUMMARY.md](deployment/DEPLOYMENT-SUMMARY.md)** - Resumen de dockerización

### 📐 Especificaciones
- **[prd.md](specs/prd.md)** - Product Requirements Document

### 📖 Documentación Principal
- **[README.md](../README.md)** - Documentación general del proyecto (raíz)

---

## 🗂️ Estructura de Documentación

```
docs/
├── README.md                    # Este archivo (índice maestro)
├── deployment/                  # Guías de deployment
│   ├── DOCKER.md               # Docker completo
│   ├── QUICKSTART-DOCKER.md    # Docker rápido
│   └── DEPLOYMENT-SUMMARY.md   # Resumen técnico
├── guides/                      # Guías de uso
│   └── QUICKSTART.md           # Inicio rápido local
└── specs/                       # Especificaciones
    └── prd.md                  # PRD original
```

---

## 🎯 Navegación Rápida

### Para Desarrolladores
1. **Primera vez:** [QUICKSTART.md](guides/QUICKSTART.md)
2. **Con Docker:** [QUICKSTART-DOCKER.md](deployment/QUICKSTART-DOCKER.md)
3. **Deployment:** [DOCKER.md](deployment/DOCKER.md)

### Para Product/Business
1. **Visión del producto:** [prd.md](specs/prd.md)
2. **Estado actual:** [README.md](../README.md)

### Para DevOps
1. **Dockerización:** [DOCKER.md](deployment/DOCKER.md)
2. **Railway:** [DEPLOYMENT-SUMMARY.md](deployment/DEPLOYMENT-SUMMARY.md)

---

## 📊 Estado del Proyecto

### ✅ Completado
- Scraper básico con Selenium
- Exportación TXT/JSON/CSV
- Paginación automática
- Dockerización completa
- Configuración Railway

### 🚧 En Progreso
- Testing automatizado
- CI/CD con GitHub Actions

### 📋 Próximos Pasos
- Scraping de página de detalle
- Almacenamiento en PostgreSQL
- Dashboard de monitoreo

---

## 🔗 Links Útiles

- **Repositorio:** GitHub (configurar URL)
- **Deployment:** Railway (configurar URL)
- **Documentación API:** Pendiente

---

## 📝 Convenciones

### Commits
Seguir **Conventional Commits**:
- `feat(scope): descripción`
- `fix(scope): descripción`
- `docs: descripción`

Ver: [.windsurf/workflows/portalinmobiliario-github.md](../.windsurf/workflows/portalinmobiliario-github.md)

### Estructura de Código
- Python 3.11+
- PEP 8 style guide
- Type hints recomendados

---

## 🆘 Soporte

Para problemas o preguntas:
1. Revisar documentación relevante
2. Verificar logs: `docker logs <container>`
3. Abrir issue en GitHub
