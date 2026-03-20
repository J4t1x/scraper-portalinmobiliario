# Dockerfile para Portal Inmobiliario Scraper
# Imagen base con Python 3.11
FROM python:3.11-slim

# Metadata
LABEL maintainer="ja-viers"
LABEL description="Portal Inmobiliario Scraper with Selenium and Chrome"

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    DISPLAY=:99

# Instalar dependencias del sistema para Chrome y Selenium
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    apt-transport-https \
    unzip \
    curl \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Instalar Google Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Instalar ChromeDriver
RUN CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d '.' -f 1) \
    && CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}") \
    && wget -q "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip" \
    && unzip chromedriver_linux64.zip \
    && mv chromedriver /usr/local/bin/ \
    && chmod +x /usr/local/bin/chromedriver \
    && rm chromedriver_linux64.zip

# Crear usuario no-root
RUN useradd -m -u 1000 scraper && \
    mkdir -p /app /app/output && \
    chown -R scraper:scraper /app

# Establecer directorio de trabajo
WORKDIR /app

# Copiar requirements.txt primero (para cache de Docker)
COPY --chown=scraper:scraper requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar todo el código de la aplicación (incluyendo venv)
COPY --chown=scraper:scraper . .

# Asegurar que el directorio output existe y tiene permisos
RUN mkdir -p /app/output && chown -R scraper:scraper /app/output

# Cambiar a usuario no-root
USER scraper

# Copiar y dar permisos al entrypoint
COPY --chown=scraper:scraper entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Healthcheck (opcional)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Comando por defecto (puede ser sobrescrito)
CMD ["python", "main.py", "--help"]
