#!/usr/bin/env python3
"""
Test script for the Opportunities module.
Tests both database and JSON fallback functionality.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db_loader import DatabaseLoader
from data_loader import JSONDataLoader
from dashboard.routes import _get_opportunities_from_json
from logger_config import get_logger

logger = get_logger(__name__)


def test_database_opportunities():
    """Test getting opportunities from database"""
    print("\n" + "="*80)
    print("TEST 1: Database Opportunities")
    print("="*80)
    
    try:
        db_loader = DatabaseLoader()
        
        # Test connection
        if not db_loader.test_connection():
            print("❌ Database connection failed")
            return False
        
        print("✅ Database connection successful")
        
        # Get opportunities
        opportunities = db_loader.get_investment_opportunities()
        
        # Check structure
        required_keys = ['featured', 'top_5', 'highlighted', 'market_stats', 'communes', 'alerts']
        for key in required_keys:
            if key not in opportunities:
                print(f"❌ Missing key: {key}")
                return False
        
        print("✅ All required keys present")
        
        # Print summary
        print(f"\n📊 Summary:")
        print(f"  - Featured: {'Yes' if opportunities['featured'] else 'No'}")
        print(f"  - Top 5 opportunities: {len(opportunities.get('top_5', []))}")
        print(f"  - Highlighted: {len(opportunities.get('highlighted', []))}")
        print(f"  - Market avg price/m²: ${opportunities['market_stats'].get('avg_price_m2', 0):,}")
        print(f"  - Total market value: ${opportunities['market_stats'].get('total_value', 0):,}")
        print(f"  - Communes: {len(opportunities.get('communes', []))}")
        print(f"  - Alerts: {len(opportunities.get('alerts', []))}")
        
        # Check if we have data
        has_data = (
            opportunities.get('featured') is not None or 
            len(opportunities.get('top_5', [])) > 0
        )
        
        if has_data:
            print("\n✅ Database has opportunity data")
            
            # Print featured property if exists
            if opportunities['featured']:
                featured = opportunities['featured']
                prop = featured['property']
                print(f"\n🏆 Featured Opportunity:")
                print(f"  - Score: {featured['score']}")
                print(f"  - Title: {prop.get('titulo', 'N/A')}")
                print(f"  - Price: ${prop.get('precio', 0):,}")
                print(f"  - Comuna: {prop.get('comuna', 'N/A')}")
                print(f"  - Superficie: {prop.get('superficie_total', 0)} m²")
                print(f"  - Dormitorios: {prop.get('dormitorios', 'N/A')}")
                print(f"  - Baños: {prop.get('banos', 'N/A')}")
                print(f"  - Discount: {featured['discount_percentage']}%")
        else:
            print("\n⚠️  Database is empty, will need JSON fallback")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_json_fallback():
    """Test getting opportunities from JSON files"""
    print("\n" + "="*80)
    print("TEST 2: JSON Fallback")
    print("="*80)
    
    try:
        json_loader = JSONDataLoader()
        
        # Check if JSON files exist
        files = json_loader.list_json_files()
        print(f"📁 Found {len(files)} JSON files")
        
        if not files:
            print("⚠️  No JSON files found in output/ directory")
            return True  # Not an error, just no data
        
        # Get opportunities from JSON
        opportunities = _get_opportunities_from_json(json_loader)
        
        # Print summary
        print(f"\n📊 Summary:")
        print(f"  - Featured: {'Yes' if opportunities['featured'] else 'No'}")
        print(f"  - Top 5 opportunities: {len(opportunities.get('top_5', []))}")
        print(f"  - Highlighted: {len(opportunities.get('highlighted', []))}")
        print(f"  - Market avg price/m²: ${opportunities['market_stats'].get('avg_price_m2', 0):,}")
        print(f"  - Total market value: ${opportunities['market_stats'].get('total_value', 0):,}")
        print(f"  - Communes: {len(opportunities.get('communes', []))}")
        print(f"  - Alerts: {len(opportunities.get('alerts', []))}")
        
        if opportunities['featured']:
            featured = opportunities['featured']
            prop = featured['property']
            print(f"\n🏆 Featured Opportunity (from JSON):")
            print(f"  - Score: {featured['score']}")
            print(f"  - Title: {prop.get('titulo', 'N/A')}")
            print(f"  - Price: ${prop.get('precio', 0):,}")
            print(f"  - Comuna: {prop.get('comuna', 'N/A')}")
            print(f"  - Superficie: {prop.get('superficie_total', 0)} m²")
            print(f"  - Discount: {featured['discount_percentage']}%")
        
        print("\n✅ JSON fallback working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n🧪 Testing Opportunities Module")
    print("="*80)
    
    results = []
    
    # Test 1: Database
    results.append(("Database", test_database_opportunities()))
    
    # Test 2: JSON Fallback
    results.append(("JSON Fallback", test_json_fallback()))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n⚠️  Some tests failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
