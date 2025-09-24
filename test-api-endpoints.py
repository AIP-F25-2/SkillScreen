#!/usr/bin/env python3
"""
Test script for all standardized /api endpoints
"""

import requests
import json
import time
from datetime import datetime

# Service configurations
SERVICES = [
    {"name": "API Gateway", "port": 5000, "url": "http://localhost:5000/api"},
    {"name": "User Service", "port": 5001, "url": "http://localhost:5001/api"},
    {"name": "Auth Service", "port": 5002, "url": "http://localhost:5002/api"},
    {"name": "Interview Service", "port": 5003, "url": "http://localhost:5003/api"},
    {"name": "Media Service", "port": 5004, "url": "http://localhost:5004/api"},
    {"name": "Video AI Service", "port": 5005, "url": "http://localhost:5005/api"},
    {"name": "Audio AI Service", "port": 5006, "url": "http://localhost:5006/api"},
    {"name": "Text AI Service", "port": 5007, "url": "http://localhost:5007/api"},
    {"name": "Assessment Service", "port": 5008, "url": "http://localhost:5008/api"},
    {"name": "Coding Service", "port": 5009, "url": "http://localhost:5009/api"},
    {"name": "Logger Service", "port": 5010, "url": "http://localhost:5010/api"},
    {"name": "Notification Service", "port": 5011, "url": "http://localhost:5011/api"}
]

def test_api_endpoint(service):
    """Test a single API endpoint"""
    try:
        print(f"Testing {service['name']} (port {service['port']})...")
        
        response = requests.get(service['url'], timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate response structure
            required_fields = ['success', 'data', 'meta']
            meta_required = ['pagination', 'timestamp', 'request_id']
            pagination_required = ['current_page', 'per_page', 'total_pages', 'total_count']
            
            # Check structure
            structure_valid = all(field in data for field in required_fields)
            meta_valid = all(field in data['meta'] for field in meta_required)
            pagination_valid = all(field in data['meta']['pagination'] for field in pagination_required)
            
            if structure_valid and meta_valid and pagination_valid:
                print(f"✅ {service['name']} - SUCCESS")
                print(f"   Status: {response.status_code}")
                print(f"   Success: {data['success']}")
                print(f"   Data count: {len(data['data'])}")
                print(f"   Total count: {data['meta']['pagination']['total_count']}")
                print(f"   Request ID: {data['meta']['request_id']}")
                print(f"   Timestamp: {data['meta']['timestamp']}")
                return True
            else:
                print(f"❌ {service['name']} - INVALID STRUCTURE")
                print(f"   Response: {json.dumps(data, indent=2)}")
                return False
        else:
            print(f"❌ {service['name']} - HTTP ERROR {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ {service['name']} - CONNECTION ERROR (Service not running)")
        return False
    except requests.exceptions.Timeout:
        print(f"❌ {service['name']} - TIMEOUT ERROR")
        return False
    except Exception as e:
        print(f"❌ {service['name']} - ERROR: {str(e)}")
        return False

def main():
    """Main testing function"""
    print("🚀 Testing Standardized /api Endpoints")
    print("=" * 60)
    print(f"Testing {len(SERVICES)} services...")
    print()
    
    successful_tests = 0
    total_tests = len(SERVICES)
    
    for service in SERVICES:
        if test_api_endpoint(service):
            successful_tests += 1
        print()
    
    print("=" * 60)
    print(f"📊 TEST RESULTS: {successful_tests}/{total_tests} services passed")
    
    if successful_tests == total_tests:
        print("🎉 ALL SERVICES ARE WORKING PERFECTLY!")
        print("\n✅ All /api endpoints are returning the correct structure:")
        print("   - success: boolean")
        print("   - data: array of resources")
        print("   - meta.pagination: pagination info")
        print("   - meta.timestamp: ISO timestamp")
        print("   - meta.request_id: unique request ID")
    else:
        print(f"⚠️  {total_tests - successful_tests} services failed")
        print("\nTroubleshooting:")
        print("1. Check if services are running: docker-compose ps")
        print("2. Check service logs: docker-compose logs [service-name]")
        print("3. Restart services: docker-compose restart")
    
    print("\n🔗 Quick Test Commands:")
    for service in SERVICES:
        print(f"   curl {service['url']}")
    
    return successful_tests == total_tests

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
