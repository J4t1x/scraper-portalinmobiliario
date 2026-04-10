#!/usr/bin/env python3
"""
Módulo de deduplicación de propiedades
Detecta y marca propiedades duplicadas entre ejecuciones usando ID como clave única.
"""

import json
import os
import shutil
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Any, Optional
from logger_config import get_logger

logger = get_logger(__name__)


@dataclass
class DeduplicationRegistry:
    """Registro de deduplicación con metadatos de ejecución"""
    ids: Set[str] = field(default_factory=set)
    first_seen: Dict[str, str] = field(default_factory=dict)
    last_seen: Dict[str, str] = field(default_factory=dict)
    execution_count: int = 0
    total_unique: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario serializable"""
        return {
            "ids": list(self.ids),
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "execution_count": self.execution_count,
            "total_unique": len(self.ids)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DeduplicationRegistry":
        """Crea instancia desde diccionario"""
        registry = cls()
        registry.ids = set(data.get("ids", []))
        registry.first_seen = data.get("first_seen", {})
        registry.last_seen = data.get("last_seen", {})
        registry.execution_count = data.get("execution_count", 0)
        registry.total_unique = data.get("total_unique", 0)
        return registry


class Deduplicator:
    """
    Sistema de detección de duplicados para propiedades inmobiliarias.
    
    Usa O(1) lookup con Set para máxima performance.
    Persiste en JSON preparado para migración a PostgreSQL en Fase 3.
    """
    
    def __init__(self, registry_path: str = "data/scraped_ids.json"):
        """
        Inicializa el deduplicador.
        
        Args:
            registry_path: Ruta al archivo JSON de registro
        """
        self.registry_path = Path(registry_path)
        self.registry = DeduplicationRegistry()
        self._load_registry()
    
    def _load_registry(self) -> None:
        """Carga el registro desde disco o crea uno nuevo"""
        try:
            if self.registry_path.exists():
                with open(self.registry_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.registry = DeduplicationRegistry.from_dict(data)
                    logger.info(f"📚 Registro cargado: {len(self.registry.ids)} IDs únicos")
            else:
                logger.info("📚 Nuevo registro de deduplicación creado")
                self._ensure_directory()
        except json.JSONDecodeError as e:
            logger.error(f"❌ Error decodificando JSON: {e}")
            self._handle_corrupt_registry()
        except Exception as e:
            logger.error(f"❌ Error cargando registro: {e}")
            self.registry = DeduplicationRegistry()
    
    def _ensure_directory(self) -> None:
        """Asegura que el directorio data/ exista"""
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _handle_corrupt_registry(self) -> None:
        """Maneja registro corrupto haciendo backup y creando nuevo"""
        if self.registry_path.exists():
            backup_path = self.registry_path.with_suffix('.json.corrupt')
            shutil.move(str(self.registry_path), str(backup_path))
            logger.warning(f"⚠️  Registro corrupto. Backup: {backup_path}")
        self.registry = DeduplicationRegistry()
    
    def save_registry(self) -> None:
        """Guarda el registro en disco"""
        try:
            self._ensure_directory()
            # Backup del registro anterior si existe
            if self.registry_path.exists():
                backup_path = self.registry_path.with_suffix('.json.backup')
                shutil.copy2(str(self.registry_path), str(backup_path))
            
            with open(self.registry_path, 'w', encoding='utf-8') as f:
                json.dump(self.registry.to_dict(), f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 Registro guardado: {len(self.registry.ids)} IDs")
        except Exception as e:
            logger.error(f"❌ Error guardando registro: {e}")
            raise
    
    def is_duplicate(self, property_id: str) -> bool:
        """
        Verifica si un ID es duplicado en O(1) time.
        
        Args:
            property_id: ID de la propiedad (ej: "MLC-12345678")
            
        Returns:
            True si el ID ya existe en el registro
        """
        return property_id in self.registry.ids
    
    def mark_property(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Marca una propiedad con flag is_duplicate.
        
        Args:
            data: Diccionario de propiedad con 'id' o 'url'
            
        Returns:
            Propiedad con campo 'is_duplicate' agregado
        """
        property_id = self._extract_property_id(data)
        
        if property_id:
            data['is_duplicate'] = self.is_duplicate(property_id)
        else:
            data['is_duplicate'] = False
            logger.warning(f"⚠️  Propiedad sin ID: {data.get('titulo', 'N/A')}")
        
        return data
    
    def _extract_property_id(self, data: Dict[str, Any]) -> Optional[str]:
        """
        Extrae el ID de una propiedad desde el diccionario.
        
        Soporta múltiples fuentes de ID:
        - Campo 'id' directo
        - Extraído de URL de portalinmobiliario
        """
        # ID directo
        if 'id' in data and data['id']:
            return str(data['id'])
        
        # Extraer de URL
        url = data.get('url', '')
        if url and 'portalinmobiliario.com' in url:
            # URLs típicas: .../MLC-12345678-...html
            import re
            match = re.search(r'(MLC-\d+)', url)
            if match:
                return match.group(1)
        
        return None
    
    def add_to_registry(self, property_id: str) -> None:
        """
        Agrega un ID al registro de deduplicación.
        
        Args:
            property_id: ID único de la propiedad
        """
        if not property_id:
            return
        
        now = datetime.now().isoformat()
        
        if property_id not in self.registry.ids:
            self.registry.ids.add(property_id)
            self.registry.first_seen[property_id] = now
            self.registry.total_unique = len(self.registry.ids)
        
        self.registry.last_seen[property_id] = now
    
    def process_properties(self, properties: List[Dict[str, Any]], 
                          add_to_registry: bool = True) -> List[Dict[str, Any]]:
        """
        Procesa una lista de propiedades marcando duplicados.
        
        Args:
            properties: Lista de diccionarios de propiedades
            add_to_registry: Si True, agrega IDs nuevos al registro
            
        Returns:
            Lista de propiedades con flag is_duplicate
        """
        processed = []
        duplicates_count = 0
        new_count = 0
        
        for prop in properties:
            marked = self.mark_property(prop.copy())
            property_id = self._extract_property_id(prop)
            
            if marked['is_duplicate']:
                duplicates_count += 1
            else:
                new_count += 1
            
            if add_to_registry and property_id:
                self.add_to_registry(property_id)
            
            processed.append(marked)
        
        # Actualizar contador de ejecuciones
        self.registry.execution_count += 1
        
        logger.info(f"🔍 Procesadas: {len(processed)} propiedades")
        logger.info(f"   - Nuevas: {new_count}")
        logger.info(f"   - Duplicadas: {duplicates_count}")
        
        return processed
    
    def filter_duplicates(self, properties: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filtra propiedades duplicadas de la lista.
        
        Args:
            properties: Lista con propiedades marcadas
            
        Returns:
            Lista solo con propiedades no duplicadas
        """
        filtered = [p for p in properties if not p.get('is_duplicate', False)]
        logger.info(f"🚫 Filtradas: {len(properties) - len(filtered)} duplicadas")
        return filtered
    
    def reset_registry(self) -> None:
        """Limpia completamente el registro de duplicados"""
        self.registry = DeduplicationRegistry()
        if self.registry_path.exists():
            backup_path = self.registry_path.with_suffix('.json.reset')
            shutil.move(str(self.registry_path), str(backup_path))
            logger.info(f"🗑️  Registro reseteado. Backup: {backup_path}")
        else:
            logger.info("🗑️  Registro vacío (no existía archivo)")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estadísticas del registro de deduplicación.
        
        Returns:
            Diccionario con estadísticas
        """
        return {
            "total_ids": len(self.registry.ids),
            "execution_count": self.registry.execution_count,
            "registry_file": str(self.registry_path),
            "file_exists": self.registry_path.exists(),
            "first_seen_count": len(self.registry.first_seen),
            "last_seen_count": len(self.registry.last_seen)
        }
    
    def print_stats(self) -> None:
        """Imprime estadísticas formateadas"""
        stats = self.get_stats()
        print("\n" + "=" * 60)
        print("📊 ESTADÍSTICAS DE DEDUPLICACIÓN")
        print("=" * 60)
        print(f"Total IDs únicos: {stats['total_ids']:,}")
        print(f"Ejecuciones: {stats['execution_count']}")
        print(f"Archivo: {stats['registry_file']}")
        print(f"Existe: {'Sí' if stats['file_exists'] else 'No'}")
        print("=" * 60 + "\n")


def create_deduplicator(registry_path: Optional[str] = None) -> Deduplicator:
    """
    Factory para crear instancia de Deduplicator.
    
    Args:
        registry_path: Ruta opcional al registro
        
    Returns:
        Instancia de Deduplicator
    """
    path = registry_path or os.getenv("DEDUP_REGISTRY_PATH", "data/scraped_ids.json")
    return Deduplicator(path)
