#!/usr/bin/env python3
"""
Test script for SLM (Small Language Model) integration.

Tests:
1. SLM Manager initialization
2. Model catalog loading
3. Ollama connection
4. Model listing and filtering
5. Agent integration with SLMs
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai.slm_manager import SLMManager, SLMCatalog, ModelSize, ModelTask
from ai.agent import AnalyticsAgent
from logger_config import get_logger

logger = get_logger(__name__)


def print_section(title: str):
    """Print a section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_catalog():
    """Test SLM catalog"""
    print_section("TEST 1: SLM Catalog")
    
    all_models = SLMCatalog.get_all_models()
    print(f"✓ Total models in catalog: {len(all_models)}")
    
    # Group by size
    for size in ModelSize:
        models = SLMCatalog.get_by_size(size)
        print(f"  - {size.value}: {len(models)} models")
    
    # Group by task
    print("\nModels by task:")
    for task in ModelTask:
        models = SLMCatalog.get_by_task(task)
        print(f"  - {task.value}: {len(models)} models")
    
    # Recommendations
    print("\nRecommendations:")
    for use_case in ['analytics', 'fast', 'quality', 'balanced']:
        model = SLMCatalog.get_recommended(use_case)
        print(f"  - {use_case}: {model.display_name} (score: {model.performance_score})")
    
    return True


def test_manager():
    """Test SLM Manager"""
    print_section("TEST 2: SLM Manager")
    
    manager = SLMManager()
    
    # Check Ollama status
    status = manager.check_ollama_status()
    print(f"Ollama Status: {status['status']}")
    print(f"URL: {status['url']}")
    
    if status['status'] != 'online':
        print("⚠️  Ollama is not running. Some tests will be skipped.")
        print("   To start Ollama: ollama serve")
        return False
    
    # Get installed models
    print("\nInstalled models:")
    installed = manager.get_installed_models(refresh=True)
    if installed:
        for model in installed:
            print(f"  ✓ {model.display_name} ({model.size_mb}MB)")
    else:
        print("  No models installed")
    
    # Get all available models
    print("\nAll available models:")
    available = manager.get_available_models()
    installed_count = sum(1 for m in available if m.installed)
    print(f"  Total: {len(available)} ({installed_count} installed)")
    
    # Show top 5 by performance
    print("\nTop 5 models by performance:")
    top_models = sorted(available, key=lambda m: m.performance_score, reverse=True)[:5]
    for i, model in enumerate(top_models, 1):
        status_icon = "✓" if model.installed else "○"
        print(f"  {i}. {status_icon} {model.display_name} - Score: {model.performance_score}")
    
    return True


def test_agent_integration():
    """Test Agent integration with SLMs"""
    print_section("TEST 3: Agent Integration")
    
    agent = AnalyticsAgent()
    
    # Check status
    status = agent.check_status()
    print(f"Agent Status: {status['status']}")
    print(f"Current Model: {status['model']}")
    print(f"SLM Support: {status.get('slm_support', False)}")
    
    if status['status'] != 'online':
        print("⚠️  Agent is offline. Skipping integration tests.")
        return False
    
    # Get model info
    print("\nCurrent model info:")
    info = agent.get_model_info()
    if info.get('display_name'):
        print(f"  Name: {info['display_name']}")
        print(f"  Parameters: {info.get('parameters', 'Unknown')}")
        print(f"  Performance: {info.get('performance_score', 'N/A')}")
        print(f"  Speed: {info.get('speed_score', 'N/A')}")
        print(f"  Quality: {info.get('quality_score', 'N/A')}")
    else:
        print(f"  Name: {info['name']}")
        print(f"  Loaded: {info['loaded']}")
    
    # Test query
    print("\nTesting query...")
    try:
        context = {
            'stats': {
                'total': 100,
                'by_operacion': {'venta': 80, 'arriendo': 20},
                'precio_promedio': 150000000
            }
        }
        response = agent.ask("¿Cuántas propiedades hay en total?", context)
        print(f"✓ Query successful")
        print(f"  Response preview: {response[:100]}...")
    except Exception as e:
        print(f"✗ Query failed: {e}")
        return False
    
    return True


def test_model_switching():
    """Test model switching"""
    print_section("TEST 4: Model Switching")
    
    manager = SLMManager()
    agent = AnalyticsAgent()
    
    # Get installed models
    installed = manager.get_installed_models()
    
    if len(installed) < 2:
        print("⚠️  Need at least 2 installed models to test switching")
        print(f"   Currently installed: {len(installed)}")
        return False
    
    # Try switching to second model
    original_model = agent.model
    target_model = installed[1].name
    
    print(f"Current model: {original_model}")
    print(f"Switching to: {target_model}")
    
    success = agent.switch_model(target_model)
    
    if success:
        print(f"✓ Successfully switched to {target_model}")
        # Switch back
        agent.switch_model(original_model)
        print(f"✓ Switched back to {original_model}")
        return True
    else:
        print(f"✗ Failed to switch models")
        return False


def test_benchmarking():
    """Test model benchmarking"""
    print_section("TEST 5: Model Benchmarking")
    
    manager = SLMManager()
    installed = manager.get_installed_models()
    
    if not installed:
        print("⚠️  No models installed for benchmarking")
        return False
    
    # Benchmark first installed model
    model = installed[0]
    print(f"Benchmarking: {model.display_name}")
    
    result = manager.benchmark_model(model.name)
    
    if result.get('success'):
        print(f"✓ Benchmark completed:")
        print(f"  Duration: {result['duration_ms']}ms")
        print(f"  Tokens: {result['tokens']}")
        print(f"  Tokens/sec: {result['tokens_per_second']:.2f}")
        print(f"  Load time: {result['load_duration_ms']}ms")
        print(f"  Eval time: {result['eval_duration_ms']}ms")
        return True
    else:
        print(f"✗ Benchmark failed: {result.get('error', 'Unknown error')}")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("  SLM INTEGRATION TEST SUITE")
    print("=" * 70)
    
    results = []
    
    # Test 1: Catalog
    try:
        results.append(("Catalog", test_catalog()))
    except Exception as e:
        logger.error(f"Catalog test failed: {e}", exc_info=True)
        results.append(("Catalog", False))
    
    # Test 2: Manager
    try:
        manager_ok = test_manager()
        results.append(("Manager", manager_ok))
    except Exception as e:
        logger.error(f"Manager test failed: {e}", exc_info=True)
        results.append(("Manager", False))
        manager_ok = False
    
    # Test 3: Agent Integration
    if manager_ok:
        try:
            results.append(("Agent Integration", test_agent_integration()))
        except Exception as e:
            logger.error(f"Agent integration test failed: {e}", exc_info=True)
            results.append(("Agent Integration", False))
    else:
        results.append(("Agent Integration", False))
    
    # Test 4: Model Switching
    if manager_ok:
        try:
            results.append(("Model Switching", test_model_switching()))
        except Exception as e:
            logger.error(f"Model switching test failed: {e}", exc_info=True)
            results.append(("Model Switching", False))
    else:
        results.append(("Model Switching", False))
    
    # Test 5: Benchmarking
    if manager_ok:
        try:
            results.append(("Benchmarking", test_benchmarking()))
        except Exception as e:
            logger.error(f"Benchmarking test failed: {e}", exc_info=True)
            results.append(("Benchmarking", False))
    else:
        results.append(("Benchmarking", False))
    
    # Summary
    print_section("TEST SUMMARY")
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:10} - {test_name}")
    
    total = len(results)
    passed = sum(1 for _, result in results if result)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n⚠️  Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
