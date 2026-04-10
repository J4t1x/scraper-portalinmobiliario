"""
Sistema de Logging Robusto - Portal Inmobiliario Scraper

Configuración de logging estructurado JSON con rotación automática.
"""

import os
import sys
import json
import gzip
import shutil
import logging
import logging.handlers
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional
from pythonjsonlogger import jsonlogger


class CustomJSONFormatter(jsonlogger.JsonFormatter):
    """Formatter JSON personalizado con campos adicionales."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        super().add_fields(log_record, record, message_dict)
        
        # Timestamp ISO8601
        if not log_record.get('timestamp'):
            log_record['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        
        # Nivel
        if log_record.get('level'):
            log_record['level'] = log_record['level'].upper()
        else:
            log_record['level'] = record.levelname
        
        # Logger name
        log_record['logger'] = record.name
        
        # Ubicación
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line'] = record.lineno
        
        # Thread/Process info
        log_record['thread'] = record.threadName
        log_record['process'] = record.process
        
        # Extra context (si existe)
        if hasattr(record, 'context'):
            log_record['context'] = record.context
        
        # Remove standard fields that are duplicated
        for field in ['name', 'levelno', 'levelname', 'pathname', 'filename', 'module', 'lineno', 'funcName', 'created', 'msecs', 'relativeCreated', 'thread', 'threadName', 'processName', 'process']:
            if field in log_record and field not in ['timestamp', 'level', 'logger', 'module', 'function', 'line', 'thread', 'process']:
                log_record.pop(field, None)


class GzipRotator:
    """Rotador que comprime archivos de log en gzip."""
    
    def __call__(self, source: str, dest: str) -> None:
        """Comprime el archivo de log en gzip."""
        try:
            with open(source, 'rb') as f_in:
                with gzip.open(dest + '.gz', 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            os.remove(source)
        except Exception as e:
            # Si falla la compresión, solo renombrar
            shutil.move(source, dest)
            logging.error(f"Error comprimiendo log: {e}", exc_info=True)


class LoggerConfig:
    """Configuración centralizada del sistema de logging."""
    
    DEFAULT_LOG_LEVEL = "INFO"
    DEFAULT_LOG_DIR = "logs"
    DEFAULT_RETENTION_DAYS = 30
    
    def __init__(self, log_level: Optional[str] = None, log_dir: Optional[str] = None):
        """
        Inicializa la configuración de logging.
        
        Args:
            log_level: Nivel de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_dir: Directorio donde guardar los logs
        """
        self.log_level = (log_level or os.getenv("LOG_LEVEL", self.DEFAULT_LOG_LEVEL)).upper()
        self.log_dir = Path(log_dir or os.getenv("LOG_DIR", self.DEFAULT_LOG_DIR))
        self.retention_days = int(os.getenv("LOG_RETENTION_DAYS", self.DEFAULT_RETENTION_DAYS))
        
        # Crear directorios de logs
        self._setup_directories()
        
        # Configurar logging
        self._setup_logging()
        
        # Limpiar logs antiguos
        self.clean_old_logs()
    
    def _setup_directories(self) -> None:
        """Crea los directorios necesarios para los logs."""
        self.scraping_dir = self.log_dir / "scraping"
        self.errors_dir = self.log_dir / "errors"
        self.performance_dir = self.log_dir / "performance"
        
        for dir_path in [self.scraping_dir, self.errors_dir, self.performance_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def _setup_logging(self) -> None:
        """Configura los handlers y formatters."""
        # Nivel de log
        level = getattr(logging, self.log_level, logging.INFO)
        
        # Root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        
        # Limpiar handlers existentes
        root_logger.handlers = []
        
        # Formatter JSON
        json_formatter = CustomJSONFormatter(
            '%(timestamp)s %(level)s %(logger)s %(module)s %(function)s %(line)s %(message)s'
        )
        
        # Console handler (solo INFO y superior, sin JSON para legibilidad)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(name)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
        
        # Handler de scraping (rotación diaria)
        scraping_handler = logging.handlers.TimedRotatingFileHandler(
            filename=self.scraping_dir / "scraping.json",
            when='midnight',
            interval=1,
            backupCount=self.retention_days,
            encoding='utf-8'
        )
        scraping_handler.setLevel(logging.DEBUG)
        scraping_handler.setFormatter(json_formatter)
        scraping_handler.rotator = GzipRotator()
        scraping_handler.namer = lambda name: name.replace(".json.", ".json.") + "."
        scraping_handler.suffix = "%Y-%m-%d"
        root_logger.addHandler(scraping_handler)
        
        # Handler de errores (rotación diaria, solo ERROR y CRITICAL)
        errors_handler = logging.handlers.TimedRotatingFileHandler(
            filename=self.errors_dir / "errors.json",
            when='midnight',
            interval=1,
            backupCount=self.retention_days,
            encoding='utf-8'
        )
        errors_handler.setLevel(logging.ERROR)
        errors_handler.setFormatter(json_formatter)
        errors_handler.rotator = GzipRotator()
        errors_handler.namer = lambda name: name.replace(".json.", ".json.") + "."
        errors_handler.suffix = "%Y-%m-%d"
        root_logger.addHandler(errors_handler)
        
        # Handler de performance (rotación diaria)
        perf_handler = logging.handlers.TimedRotatingFileHandler(
            filename=self.performance_dir / "performance.json",
            when='midnight',
            interval=1,
            backupCount=self.retention_days,
            encoding='utf-8'
        )
        perf_handler.setLevel(logging.INFO)
        perf_handler.setFormatter(json_formatter)
        perf_handler.rotator = GzipRotator()
        perf_handler.namer = lambda name: name.replace(".json.", ".json.") + "."
        perf_handler.suffix = "%Y-%m-%d"
        root_logger.addHandler(perf_handler)
        
        # Logger específico para performance
        self.perf_logger = logging.getLogger("performance")
        self.perf_logger.addHandler(perf_handler)
        self.perf_logger.propagate = False  # No duplicar en consola
    
    def clean_old_logs(self) -> None:
        """Elimina archivos de log más antiguos que retention_days."""
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        
        for log_subdir in [self.scraping_dir, self.errors_dir, self.performance_dir]:
            if not log_subdir.exists():
                continue
                
            for log_file in log_subdir.iterdir():
                if not log_file.is_file():
                    continue
                    
                try:
                    # Obtener fecha de modificación
                    mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                    if mtime < cutoff_date:
                        log_file.unlink()
                        logging.info(f"Eliminado log antiguo: {log_file.name}")
                except Exception as e:
                    logging.error(f"Error eliminando {log_file}: {e}", exc_info=True)
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        Obtiene un logger configurado.
        
        Args:
            name: Nombre del logger
            
        Returns:
            Logger configurado
        """
        return logging.getLogger(name)
    
    def log_performance(self, operation: str, duration_ms: float, context: Optional[Dict] = None) -> None:
        """
        Log específico para métricas de performance.
        
        Args:
            operation: Nombre de la operación
            duration_ms: Duración en milisegundos
            context: Contexto adicional
        """
        extra = {
            'context': {
                'operation': operation,
                'duration_ms': duration_ms,
                **(context or {})
            }
        }
        self.perf_logger.info(f"Performance: {operation} took {duration_ms:.2f}ms", extra=extra)


# Instancia global
_logger_config: Optional[LoggerConfig] = None


def setup_logging(log_level: Optional[str] = None, log_dir: Optional[str] = None) -> LoggerConfig:
    """
    Configura el sistema de logging.
    
    Args:
        log_level: Nivel de log
        log_dir: Directorio de logs
        
    Returns:
        Instancia de LoggerConfig
    """
    global _logger_config
    _logger_config = LoggerConfig(log_level, log_dir)
    return _logger_config


def get_logger(name: str) -> logging.Logger:
    """
    Obtiene un logger. Si no está configurado, configura con defaults.
    
    Args:
        name: Nombre del logger
        
    Returns:
        Logger configurado
    """
    global _logger_config
    if _logger_config is None:
        _logger_config = setup_logging()
    return _logger_config.get_logger(name)


def log_performance(operation: str, duration_ms: float, context: Optional[Dict] = None) -> None:
    """
    Log de métricas de performance.
    
    Args:
        operation: Nombre de la operación
        duration_ms: Duración en milisegundos
        context: Contexto adicional
    """
    global _logger_config
    if _logger_config is None:
        _logger_config = setup_logging()
    _logger_config.log_performance(operation, duration_ms, context)
