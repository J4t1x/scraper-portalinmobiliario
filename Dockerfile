# ============================================================================
# Dockerfile.v2 - Portal Inmobiliario Scraper (Optimizado y Estable)
# Versión: 2.1 - Soluciona problemas de Chrome/ChromeDriver
# 
# Mejoras aplicadas del PRD:
# - Multi-stage build (-30% tamaño)
# - Chromium del sistema (sin dependencia de APIs externas)
# - Optimizaciones de memoria (-45% RAM)
# - Usuario no-root (seguridad)
# ============================================================================

# ============================================================================
# STAGE 1: Builder (temporal - solo para compilar dependencias Python)
# ============================================================================
FROM python:3.11-slim AS builder

# Instalar dependencias de compilación
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Crear virtualenv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copiar requirements y compilar
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# ============================================================================
# STAGE 2: Runtime (imagen final optimizada)
# ============================================================================
FROM python:3.11-slim

# Metadata
LABEL maintainer="ja-viers"
LABEL description="Portal Inmobiliario Scraper - Optimized v2.1"
LABEL version="2.1"

# Variables de entorno optimizadas
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DISPLAY=:99 \
    PATH="/opt/venv/bin:$PATH" \
    # Chromium paths
    CHROME_BIN=/usr/bin/chromium \
    CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Instalar dependencias de runtime (sin compiladores)
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Chromium y ChromeDriver del sistema (ESTABLE - no depende de APIs externas)
    chromium \
    chromium-driver \
    # Xvfb para headless (fallback)
    xvfb \
    # Utilidades mínimas
    curl \
    procps \
    # Runtime libraries para psycopg2
    libpq5 \
    # Fonts para renderizado correcto
    fonts-liberation \
    libnss3 \
    libxss1 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Crear usuario no-root (seguridad)
RUN useradd -m -u 1000 scraper && \
    mkdir -p /app /app/output /app/logs && \
    chown -R scraper:scraper /app

# Copiar virtualenv desde builder (multi-stage)
COPY --from=builder /opt/venv /opt/venv

# Establecer directorio de trabajo
WORKDIR /app

# Copiar código de la aplicación
COPY --chown=scraper:scraper . .

# Asegurar permisos y crear directorios
RUN chmod +x /app/scripts/*.sh 2>/dev/null || true && \
    mkdir -p /app/output /app/logs && \
    chown -R scraper:scraper /app

# Cambiar a usuario no-root
USER scraper

# Verificar instalación de Chromium (build-time check)
RUN chromium --version && chromedriver --version

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Comando por defecto
CMD ["python", "main.py", "--help"]
