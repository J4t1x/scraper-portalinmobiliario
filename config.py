import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuración del scraper"""
    
    BASE_URL = "https://www.portalinmobiliario.com"
    
    DELAY_BETWEEN_REQUESTS = float(os.getenv("DELAY_BETWEEN_REQUESTS", "2"))
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
    TIMEOUT = int(os.getenv("TIMEOUT", "30"))
    USER_AGENT = os.getenv(
        "USER_AGENT",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    
    ITEMS_PER_PAGE = 50
    
    OPERACIONES = ["venta", "arriendo", "arriendo-de-temporada"]
    TIPOS_PROPIEDAD = [
        "departamento",
        "casa",
        "oficina",
        "terreno",
        "local-comercial",
        "bodega",
        "estacionamiento",
        "parcela"
    ]
    
    OUTPUT_DIR = "output"
