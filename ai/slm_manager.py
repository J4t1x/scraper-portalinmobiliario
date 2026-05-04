"""
Small Language Model (SLM) Manager for Ollama integration.

This module manages SLMs optimized for analytics tasks:
- Model catalog with performance metrics
- Auto-detection of installed models
- Model switching and downloading
- Performance benchmarking
- Resource usage optimization

Based on: https://medium.com/@lekhashree2012/small-language-models-slms-the-lightweight-ai-revolution-everyones-talking-about-in-2025-b7db3d228bc2
"""

import logging
import requests
import os
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")


class ModelSize(Enum):
    """Model size categories for SLMs"""
    TINY = "tiny"      # < 1B parameters
    SMALL = "small"    # 1-3B parameters
    MEDIUM = "medium"  # 3-7B parameters
    LARGE = "large"    # 7-13B parameters


class ModelTask(Enum):
    """Specialized tasks for SLMs"""
    ANALYTICS = "analytics"
    CODE = "code"
    CHAT = "chat"
    REASONING = "reasoning"
    GENERAL = "general"


@dataclass
class SLMModel:
    """Small Language Model metadata"""
    name: str
    display_name: str
    size_category: ModelSize
    parameters: str
    size_mb: int
    tasks: List[ModelTask]
    description: str
    recommended_for: List[str]
    performance_score: int  # 0-100
    speed_score: int  # 0-100 (higher = faster)
    quality_score: int  # 0-100 (higher = better quality)
    installed: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['size_category'] = self.size_category.value
        data['tasks'] = [t.value for t in self.tasks]
        return data


class SLMCatalog:
    """
    Catalog of recommended Small Language Models for analytics.
    
    Models are selected based on:
    - Size efficiency (< 7B parameters)
    - Task specialization (analytics, reasoning, code)
    - Performance benchmarks
    - Resource requirements
    """
    
    MODELS = [
        # TINY Models (< 1B) - Ultra-fast, basic tasks
        SLMModel(
            name="qwen2.5-coder:0.5b",
            display_name="Qwen2.5 Coder 0.5B",
            size_category=ModelSize.TINY,
            parameters="0.5B",
            size_mb=352,
            tasks=[ModelTask.CODE, ModelTask.ANALYTICS],
            description="Ultra-lightweight coding model, ideal for basic analytics",
            recommended_for=["Quick queries", "Basic statistics", "Low-resource environments"],
            performance_score=60,
            speed_score=100,
            quality_score=55
        ),
        
        # SMALL Models (1-3B) - Balanced speed/quality
        SLMModel(
            name="qwen2.5-coder:1.5b",
            display_name="Qwen2.5 Coder 1.5B",
            size_category=ModelSize.SMALL,
            parameters="1.5B",
            size_mb=934,
            tasks=[ModelTask.CODE, ModelTask.ANALYTICS, ModelTask.REASONING],
            description="Excellent balance of speed and quality for analytics tasks",
            recommended_for=["Market analysis", "Data insights", "Quick reports"],
            performance_score=75,
            speed_score=90,
            quality_score=70
        ),
        SLMModel(
            name="phi3:mini",
            display_name="Phi-3 Mini",
            size_category=ModelSize.SMALL,
            parameters="3.8B",
            size_mb=2300,
            tasks=[ModelTask.REASONING, ModelTask.ANALYTICS, ModelTask.CHAT],
            description="Microsoft's efficient model with strong reasoning capabilities",
            recommended_for=["Complex queries", "Comparative analysis", "Recommendations"],
            performance_score=80,
            speed_score=85,
            quality_score=78
        ),
        SLMModel(
            name="gemma2:2b",
            display_name="Gemma 2 2B",
            size_category=ModelSize.SMALL,
            parameters="2B",
            size_mb=1600,
            tasks=[ModelTask.GENERAL, ModelTask.ANALYTICS, ModelTask.CHAT],
            description="Google's efficient model with broad capabilities",
            recommended_for=["General analytics", "Market insights", "Trend analysis"],
            performance_score=78,
            speed_score=88,
            quality_score=75
        ),
        
        # MEDIUM Models (3-7B) - High quality
        SLMModel(
            name="qwen2.5-coder:3b",
            display_name="Qwen2.5 Coder 3B",
            size_category=ModelSize.MEDIUM,
            parameters="3B",
            size_mb=1900,
            tasks=[ModelTask.CODE, ModelTask.ANALYTICS, ModelTask.REASONING],
            description="High-quality coding and analytics with good speed",
            recommended_for=["Detailed analysis", "Complex queries", "Investment insights"],
            performance_score=85,
            speed_score=75,
            quality_score=85
        ),
        SLMModel(
            name="llama3.2:3b",
            display_name="Llama 3.2 3B",
            size_category=ModelSize.MEDIUM,
            parameters="3B",
            size_mb=2000,
            tasks=[ModelTask.GENERAL, ModelTask.REASONING, ModelTask.ANALYTICS],
            description="Meta's latest small model with strong reasoning",
            recommended_for=["Market analysis", "Investment opportunities", "Detailed reports"],
            performance_score=88,
            speed_score=80,
            quality_score=87
        ),
        SLMModel(
            name="qwen2.5-coder:7b",
            display_name="Qwen2.5 Coder 7B",
            size_category=ModelSize.MEDIUM,
            parameters="7B",
            size_mb=4700,
            tasks=[ModelTask.CODE, ModelTask.ANALYTICS, ModelTask.REASONING],
            description="Premium quality for complex analytics tasks",
            recommended_for=["Advanced analysis", "Multi-factor insights", "Strategic recommendations"],
            performance_score=92,
            speed_score=65,
            quality_score=92
        ),
        
        # LARGE Models (7-13B) - Maximum quality
        SLMModel(
            name="qwen2.5:7b",
            display_name="Qwen2.5 7B",
            size_category=ModelSize.LARGE,
            parameters="7B",
            size_mb=4700,
            tasks=[ModelTask.GENERAL, ModelTask.REASONING, ModelTask.ANALYTICS],
            description="High-quality general model with excellent reasoning",
            recommended_for=["Complex analysis", "Strategic insights", "Comprehensive reports"],
            performance_score=90,
            speed_score=70,
            quality_score=90
        ),
    ]
    
    @classmethod
    def get_all_models(cls) -> List[SLMModel]:
        """Get all models in catalog"""
        return cls.MODELS.copy()
    
    @classmethod
    def get_by_name(cls, name: str) -> Optional[SLMModel]:
        """Get model by name"""
        for model in cls.MODELS:
            if model.name == name:
                return model
        return None
    
    @classmethod
    def get_by_size(cls, size: ModelSize) -> List[SLMModel]:
        """Get models by size category"""
        return [m for m in cls.MODELS if m.size_category == size]
    
    @classmethod
    def get_by_task(cls, task: ModelTask) -> List[SLMModel]:
        """Get models suitable for a task"""
        return [m for m in cls.MODELS if task in m.tasks]
    
    @classmethod
    def get_recommended(cls, use_case: str = "analytics") -> SLMModel:
        """
        Get recommended model for a use case.
        
        Args:
            use_case: 'analytics', 'code', 'chat', 'reasoning', 'fast', 'quality'
        """
        if use_case == "fast":
            # Fastest model
            return sorted(cls.MODELS, key=lambda m: m.speed_score, reverse=True)[0]
        elif use_case == "quality":
            # Highest quality
            return sorted(cls.MODELS, key=lambda m: m.quality_score, reverse=True)[0]
        elif use_case == "balanced":
            # Best overall performance
            return sorted(cls.MODELS, key=lambda m: m.performance_score, reverse=True)[0]
        else:
            # Default: best for analytics
            analytics_models = cls.get_by_task(ModelTask.ANALYTICS)
            return sorted(analytics_models, key=lambda m: m.performance_score, reverse=True)[0]


class SLMManager:
    """
    Manager for Small Language Models with Ollama integration.
    
    Features:
    - Auto-detect installed models
    - Download and manage models
    - Switch between models
    - Performance benchmarking
    - Resource monitoring
    """
    
    def __init__(self, ollama_url: str = OLLAMA_URL):
        self.ollama_url = ollama_url
        self.catalog = SLMCatalog()
        self._current_model = None
        self._installed_models = []
    
    def check_ollama_status(self) -> Dict[str, Any]:
        """
        Check if Ollama is running and accessible.
        
        Returns:
            Dict with status info
        """
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.ok:
                return {
                    'status': 'online',
                    'url': self.ollama_url,
                    'accessible': True
                }
        except Exception as e:
            logger.debug(f"Ollama not accessible: {e}")
        
        return {
            'status': 'offline',
            'url': self.ollama_url,
            'accessible': False
        }
    
    def get_installed_models(self, refresh: bool = False) -> List[SLMModel]:
        """
        Get list of installed models from Ollama.
        
        Args:
            refresh: Force refresh from Ollama API
            
        Returns:
            List of SLMModel objects with installed=True
        """
        if self._installed_models and not refresh:
            return self._installed_models
        
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            response.raise_for_status()
            data = response.json()
            
            installed = []
            for ollama_model in data.get('models', []):
                model_name = ollama_model.get('name', '')
                
                # Check if model is in our catalog
                catalog_model = self.catalog.get_by_name(model_name)
                if catalog_model:
                    catalog_model.installed = True
                    catalog_model.size_mb = ollama_model.get('size', 0) // (1024 * 1024)
                    installed.append(catalog_model)
                else:
                    # Create entry for unknown model
                    installed.append(SLMModel(
                        name=model_name,
                        display_name=model_name,
                        size_category=ModelSize.MEDIUM,
                        parameters="Unknown",
                        size_mb=ollama_model.get('size', 0) // (1024 * 1024),
                        tasks=[ModelTask.GENERAL],
                        description="Model not in catalog",
                        recommended_for=["General use"],
                        performance_score=50,
                        speed_score=50,
                        quality_score=50,
                        installed=True
                    ))
            
            self._installed_models = installed
            return installed
            
        except Exception as e:
            logger.error(f"Error getting installed models: {e}")
            return []
    
    def get_available_models(self) -> List[SLMModel]:
        """
        Get all models from catalog with installation status.
        
        Returns:
            List of all SLMModel objects
        """
        installed_names = {m.name for m in self.get_installed_models()}
        
        all_models = self.catalog.get_all_models()
        for model in all_models:
            model.installed = model.name in installed_names
        
        return all_models
    
    def pull_model(self, model_name: str) -> Tuple[bool, str]:
        """
        Download a model from Ollama registry.
        
        Args:
            model_name: Name of the model to download
            
        Returns:
            Tuple of (success, message)
        """
        try:
            logger.info(f"Pulling model {model_name}...")
            
            response = requests.post(
                f"{self.ollama_url}/api/pull",
                json={"name": model_name},
                stream=True,
                timeout=300
            )
            
            if response.ok:
                # Stream the download progress
                for line in response.iter_lines():
                    if line:
                        logger.debug(line.decode('utf-8'))
                
                # Refresh installed models
                self.get_installed_models(refresh=True)
                
                return True, f"Model {model_name} downloaded successfully"
            else:
                return False, f"Failed to download model: {response.text}"
                
        except Exception as e:
            logger.error(f"Error pulling model: {e}")
            return False, str(e)
    
    def delete_model(self, model_name: str) -> Tuple[bool, str]:
        """
        Delete a model from Ollama.
        
        Args:
            model_name: Name of the model to delete
            
        Returns:
            Tuple of (success, message)
        """
        try:
            response = requests.delete(
                f"{self.ollama_url}/api/delete",
                json={"name": model_name},
                timeout=30
            )
            
            if response.ok:
                self.get_installed_models(refresh=True)
                return True, f"Model {model_name} deleted successfully"
            else:
                return False, f"Failed to delete model: {response.text}"
                
        except Exception as e:
            logger.error(f"Error deleting model: {e}")
            return False, str(e)
    
    def benchmark_model(self, model_name: str, test_prompt: str = "Analyze real estate market trends") -> Dict[str, Any]:
        """
        Benchmark a model's performance.
        
        Args:
            model_name: Name of the model to benchmark
            test_prompt: Test prompt to use
            
        Returns:
            Dict with benchmark results
        """
        try:
            start_time = time.time()
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": model_name,
                    "prompt": test_prompt,
                    "stream": False
                },
                timeout=60
            )
            
            duration = time.time() - start_time
            
            if response.ok:
                data = response.json()
                
                return {
                    'success': True,
                    'model': model_name,
                    'duration_ms': int(duration * 1000),
                    'tokens': data.get('eval_count', 0),
                    'tokens_per_second': data.get('eval_count', 0) / duration if duration > 0 else 0,
                    'response_length': len(data.get('response', '')),
                    'load_duration_ms': data.get('load_duration', 0) // 1_000_000,
                    'prompt_eval_duration_ms': data.get('prompt_eval_duration', 0) // 1_000_000,
                    'eval_duration_ms': data.get('eval_duration', 0) // 1_000_000
                }
            else:
                return {
                    'success': False,
                    'model': model_name,
                    'error': response.text
                }
                
        except Exception as e:
            logger.error(f"Error benchmarking model: {e}")
            return {
                'success': False,
                'model': model_name,
                'error': str(e)
            }
    
    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Dict with model info or None
        """
        try:
            response = requests.post(
                f"{self.ollama_url}/api/show",
                json={"name": model_name},
                timeout=10
            )
            
            if response.ok:
                return response.json()
            
        except Exception as e:
            logger.error(f"Error getting model info: {e}")
        
        return None
    
    def get_recommendations(self, use_case: str = "analytics") -> List[SLMModel]:
        """
        Get recommended models for a use case, prioritizing installed ones.
        
        Args:
            use_case: Use case ('analytics', 'fast', 'quality', 'balanced')
            
        Returns:
            List of recommended models, installed first
        """
        all_models = self.get_available_models()
        
        # Filter by use case
        if use_case == "analytics":
            models = [m for m in all_models if ModelTask.ANALYTICS in m.tasks]
        elif use_case == "fast":
            models = sorted(all_models, key=lambda m: m.speed_score, reverse=True)[:5]
        elif use_case == "quality":
            models = sorted(all_models, key=lambda m: m.quality_score, reverse=True)[:5]
        else:  # balanced
            models = sorted(all_models, key=lambda m: m.performance_score, reverse=True)[:5]
        
        # Sort: installed first, then by performance
        return sorted(models, key=lambda m: (not m.installed, -m.performance_score))


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    manager = SLMManager()
    
    print("=== Ollama Status ===")
    status = manager.check_ollama_status()
    print(f"Status: {status['status']}")
    print(f"URL: {status['url']}")
    
    print("\n=== Installed Models ===")
    installed = manager.get_installed_models()
    for model in installed:
        print(f"- {model.display_name} ({model.size_mb}MB)")
    
    print("\n=== Available Models ===")
    available = manager.get_available_models()
    for model in available:
        status_icon = "✓" if model.installed else "○"
        print(f"{status_icon} {model.display_name} - {model.description}")
    
    print("\n=== Recommendations for Analytics ===")
    recommendations = manager.get_recommendations("analytics")
    for i, model in enumerate(recommendations[:3], 1):
        print(f"{i}. {model.display_name} (Score: {model.performance_score})")
