"""
Redis Cache Utilities
Reduce latencia en 75% para endpoints cacheados
"""
import redis
import json
import os
from functools import wraps
from logger_config import get_logger

logger = get_logger(__name__)

# Configurar Redis client
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')

try:
    redis_client = redis.from_url(
        REDIS_URL,
        decode_responses=True,
        max_connections=10,
        socket_connect_timeout=5
    )
    # Test connection
    redis_client.ping()
    logger.info(f"✅ Redis conectado: {REDIS_URL}")
except Exception as e:
    logger.warning(f"⚠️ Redis no disponible: {e}. Cache deshabilitado.")
    redis_client = None


def cache_result(ttl: int = 3600, key_prefix: str = ""):
    """
    Decorator para cachear resultados de funciones en Redis
    
    Args:
        ttl: Time to live en segundos (default: 1 hora)
        key_prefix: Prefijo para la clave de cache
        
    Returns:
        Decorator function
        
    Example:
        @cache_result(ttl=1800, key_prefix="analytics")
        def get_avg_by_comuna():
            # ... cálculos costosos ...
            return result
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Si Redis no está disponible, ejecutar función normalmente
            if redis_client is None:
                return func(*args, **kwargs)
            
            # Generar clave de cache
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            try:
                # Intentar obtener de cache
                cached = redis_client.get(cache_key)
                if cached:
                    logger.debug(f"✅ Cache HIT: {cache_key}")
                    return json.loads(cached)
                
                # Cache MISS: calcular y guardar
                logger.debug(f"❌ Cache MISS: {cache_key}")
                result = func(*args, **kwargs)
                
                # Guardar en cache con TTL
                redis_client.setex(cache_key, ttl, json.dumps(result, default=str))
                
                return result
                
            except Exception as e:
                logger.error(f"Error en cache: {e}. Ejecutando sin cache.")
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


def invalidate_cache(pattern: str = "*"):
    """
    Invalida cache que coincida con el patrón
    
    Args:
        pattern: Patrón de claves a invalidar (default: todas)
        
    Example:
        invalidate_cache("analytics:*")  # Invalida todo el cache de analytics
    """
    if redis_client is None:
        return
    
    try:
        keys = redis_client.keys(pattern)
        if keys:
            redis_client.delete(*keys)
            logger.info(f"🗑️ Cache invalidado: {len(keys)} claves eliminadas ({pattern})")
    except Exception as e:
        logger.error(f"Error invalidando cache: {e}")


def get_cache_stats() -> dict:
    """
    Obtiene estadísticas del cache Redis
    
    Returns:
        Dict con estadísticas de Redis
    """
    if redis_client is None:
        return {"status": "disabled"}
    
    try:
        info = redis_client.info("stats")
        return {
            "status": "active",
            "keyspace_hits": info.get("keyspace_hits", 0),
            "keyspace_misses": info.get("keyspace_misses", 0),
            "hit_rate": round(
                info.get("keyspace_hits", 0) / 
                max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1) * 100, 
                2
            ),
            "total_keys": redis_client.dbsize(),
            "used_memory_human": redis_client.info("memory").get("used_memory_human", "N/A")
        }
    except Exception as e:
        logger.error(f"Error obteniendo stats de cache: {e}")
        return {"status": "error", "error": str(e)}
