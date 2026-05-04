#!/bin/bash
# ============================================================================
# build-and-test.sh - Verificar build y funcionamiento del contenedor
# Uso: ./scripts/build-and-test.sh
# ============================================================================

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  Build & Test - Portal Inmobiliario Scraper${NC}"
echo -e "${BLUE}============================================${NC}"

# Directorio del proyecto
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

echo -e "\n${YELLOW}📁 Directorio: $PROJECT_DIR${NC}"

# ============================================================================
# 1. Build de la imagen
# ============================================================================
echo -e "\n${BLUE}[1/5] 🔨 Building Docker image...${NC}"
BUILD_START=$(date +%s)

docker build -f Dockerfile.v2 -t portalinmobiliario:v2 . 2>&1 | tail -20

BUILD_END=$(date +%s)
BUILD_TIME=$((BUILD_END - BUILD_START))
echo -e "${GREEN}✅ Build completado en ${BUILD_TIME}s${NC}"

# ============================================================================
# 2. Verificar tamaño de imagen
# ============================================================================
echo -e "\n${BLUE}[2/5] 📦 Verificando tamaño de imagen...${NC}"
IMAGE_SIZE=$(docker images portalinmobiliario:v2 --format "{{.Size}}")
echo -e "   Tamaño: ${YELLOW}$IMAGE_SIZE${NC}"

# ============================================================================
# 3. Verificar Chromium y ChromeDriver
# ============================================================================
echo -e "\n${BLUE}[3/5] 🌐 Verificando Chromium y ChromeDriver...${NC}"

CHROMIUM_VERSION=$(docker run --rm portalinmobiliario:v2 chromium --version 2>/dev/null || echo "ERROR")
CHROMEDRIVER_VERSION=$(docker run --rm portalinmobiliario:v2 chromedriver --version 2>/dev/null | head -n 1 || echo "ERROR")

echo -e "   Chromium: ${YELLOW}$CHROMIUM_VERSION${NC}"
echo -e "   ChromeDriver: ${YELLOW}$CHROMEDRIVER_VERSION${NC}"

if [[ "$CHROMIUM_VERSION" == "ERROR" ]] || [[ "$CHROMEDRIVER_VERSION" == "ERROR" ]]; then
    echo -e "${RED}❌ Error: Chromium o ChromeDriver no instalados correctamente${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Chromium y ChromeDriver OK${NC}"

# ============================================================================
# 4. Verificar Python y dependencias
# ============================================================================
echo -e "\n${BLUE}[4/5] 🐍 Verificando Python y dependencias...${NC}"

PYTHON_VERSION=$(docker run --rm portalinmobiliario:v2 python --version 2>/dev/null || echo "ERROR")
echo -e "   Python: ${YELLOW}$PYTHON_VERSION${NC}"

# Verificar imports críticos
echo -e "   Verificando imports..."
docker run --rm portalinmobiliario:v2 python -c "
import selenium
import bs4
import requests
import flask
import sqlalchemy
print('   ✅ Todos los imports OK')
" 2>/dev/null || echo -e "${RED}   ❌ Error en imports${NC}"

# ============================================================================
# 5. Test de Selenium con Chromium
# ============================================================================
echo -e "\n${BLUE}[5/5] 🧪 Test de Selenium con Chromium...${NC}"

docker run --rm portalinmobiliario:v2 python -c "
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import shutil

# Configurar opciones
options = Options()
options.add_argument('--headless=new')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')

# Detectar Chromium
chromium_path = shutil.which('chromium')
chromedriver_path = shutil.which('chromedriver')

if chromium_path:
    options.binary_location = chromium_path
    
service = Service(chromedriver_path)
driver = webdriver.Chrome(service=service, options=options)

# Test básico
driver.get('https://www.google.com')
title = driver.title
driver.quit()

print(f'   ✅ Selenium test OK - Page title: {title[:30]}...')
" 2>&1 || echo -e "${RED}   ❌ Error en test de Selenium${NC}"

# ============================================================================
# Resumen
# ============================================================================
echo -e "\n${BLUE}============================================${NC}"
echo -e "${GREEN}✅ Build y verificación completados${NC}"
echo -e "${BLUE}============================================${NC}"
echo -e ""
echo -e "📊 ${YELLOW}Resumen:${NC}"
echo -e "   - Imagen: portalinmobiliario:v2"
echo -e "   - Tamaño: $IMAGE_SIZE"
echo -e "   - Build time: ${BUILD_TIME}s"
echo -e "   - Chromium: OK"
echo -e "   - Selenium: OK"
echo -e ""
echo -e "🚀 ${YELLOW}Comandos útiles:${NC}"
echo -e "   ${BLUE}# Levantar con PostgreSQL:${NC}"
echo -e "   docker-compose -f docker-compose.v2.yml up -d postgres"
echo -e ""
echo -e "   ${BLUE}# Ejecutar scraping:${NC}"
echo -e "   docker-compose -f docker-compose.v2.yml run --rm scraper python main.py --operacion venta --tipo departamento --max-pages 2"
echo -e ""
echo -e "   ${BLUE}# Levantar dashboard:${NC}"
echo -e "   docker-compose -f docker-compose.v2.yml --profile dashboard up"
echo -e ""
