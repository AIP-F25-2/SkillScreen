#!/usr/bin/env python3
"""
SkillScreen Backend Services Testing Script
This script tests all backend services for connectivity and functionality
"""

import requests
import json
import time
import sys
from typing import Dict, List, Tuple

# Service configurations
SERVICES = {
    'api-gateway': {'port': 5000, 'name': 'API Gateway'},
    'user-service': {'port': 5001, 'name': 'User Service'},
    'auth-service': {'port': 5002, 'name': 'Auth Service'},
    'interview-service': {'port': 5003, 'name': 'Interview Service'},
    'media-service': {'port': 5004, 'name': 'Media Service'},
    'video-ai-service': {'port': 5005, 'name': 'Video AI Service'},
    'audio-ai-service': {'port': 5006, 'name': 'Audio AI Service'},
    'text-ai-service': {'port': 5007, 'name': 'Text AI Service'},
    'assessment-service': {'port': 5008, 'name': 'Assessment Service'},
    'coding-service': {'port': 5009, 'name': 'Coding Service'},
    'logger-service': {'port': 5010, 'name': 'Logger Service'},
    'notification-service': {'port': 5011, 'name': 'Notification Service'}
}

class ServiceTester:
    def __init__(self):
        self.results = {}
        self.base_url = "http://localhost"
    
    def test_service_health(self, service_key: str, port: int) -> Tuple[bool, str]:
        """Test if a service is healthy"""
        try:
            url = f"{self.base_url}:{port}/health"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return True, f"Healthy - {data.get('status', 'unknown')}"
            else:
                return False, f"Unhealthy - Status: {response.status_code}"
        except requests.exceptions.RequestException as e:
            return False, f"Connection failed - {str(e)}"
    
    def test_service_info(self, service_key: str, port: int) -> Tuple[bool, str]:
        """Test service info endpoint"""
        try:
            url = f"{self.base_url}:{port}/info"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return True, f"Service: {data.get('service', 'Unknown')}"
            else:
                return False, f"Info endpoint failed - Status: {response.status_code}"
        except requests.exceptions.RequestException as e:
            return False, f"Info endpoint failed - {str(e)}"
    
    def test_api_gateway_routing(self) -> Tuple[bool, str]:
        """Test API Gateway routing to all services"""
        try:
            url = f"{self.base_url}:5000/route-test"
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                data = response.json()
                services = data.get('services', {})
                connected = sum(1 for s in services.values() if s.get('status') == 'connected')
                total = len(services)
                return True, f"Gateway routing - {connected}/{total} services connected"
            else:
                return False, f"Gateway routing test failed - Status: {response.status_code}"
        except requests.exceptions.RequestException as e:
            return False, f"Gateway routing test failed - {str(e)}"
    
    def test_auth_flow(self) -> Tuple[bool, str]:
        """Test authentication flow"""
        try:
            # Test registration
            register_url = f"{self.base_url}:5002/register"
            register_data = {
                "username": "testuser",
                "email": "test@example.com",
                "password": "testpassword"
            }
            response = requests.post(register_url, json=register_data, timeout=10)
            if response.status_code not in [201, 409]:  # 409 = user already exists
                return False, f"Registration failed - Status: {response.status_code}"
            
            # Test login
            login_url = f"{self.base_url}:5002/login"
            login_data = {
                "username": "testuser",
                "password": "testpassword"
            }
            response = requests.post(login_url, json=login_data, timeout=10)
            if response.status_code == 200:
                data = response.json()
                token = data.get('token')
                if token:
                    return True, f"Auth flow successful - Token generated"
                else:
                    return False, "Auth flow failed - No token received"
            else:
                return False, f"Login failed - Status: {response.status_code}"
        except requests.exceptions.RequestException as e:
            return False, f"Auth flow test failed - {str(e)}"
    
    def test_user_crud(self) -> Tuple[bool, str]:
        """Test user CRUD operations"""
        try:
            # Test get users
            url = f"{self.base_url}:5001/users"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return True, "User CRUD - GET users successful"
            else:
                return False, f"User CRUD failed - Status: {response.status_code}"
        except requests.exceptions.RequestException as e:
            return False, f"User CRUD test failed - {str(e)}"
    
    def test_ai_services(self) -> Tuple[bool, str]:
        """Test AI services with mock data"""
        try:
            # Test text analysis
            text_url = f"{self.base_url}:5007/analyze-text"
            text_data = {"text": "This is a test text for analysis"}
            response = requests.post(text_url, json=text_data, timeout=10)
            if response.status_code != 200:
                return False, f"Text AI service failed - Status: {response.status_code}"
            
            # Test video analysis
            video_url = f"{self.base_url}:5005/analyze-video"
            video_data = {"video_url": "http://example.com/test.mp4"}
            response = requests.post(video_url, json=video_data, timeout=10)
            if response.status_code != 200:
                return False, f"Video AI service failed - Status: {response.status_code}"
            
            # Test audio analysis
            audio_url = f"{self.base_url}:5006/analyze-audio"
            audio_data = {"audio_url": "http://example.com/test.mp3"}
            response = requests.post(audio_url, json=audio_data, timeout=10)
            if response.status_code != 200:
                return False, f"Audio AI service failed - Status: {response.status_code}"
            
            return True, "AI services - All AI services responding"
        except requests.exceptions.RequestException as e:
            return False, f"AI services test failed - {str(e)}"
    
    def test_logging(self) -> Tuple[bool, str]:
        """Test logging service"""
        try:
            # Test log creation
            log_url = f"{self.base_url}:5010/log"
            log_data = {
                "level": "INFO",
                "service": "test-service",
                "message": "Test log message"
            }
            response = requests.post(log_url, json=log_data, timeout=10)
            if response.status_code == 201:
                return True, "Logging service - Log creation successful"
            else:
                return False, f"Logging service failed - Status: {response.status_code}"
        except requests.exceptions.RequestException as e:
            return False, f"Logging service test failed - {str(e)}"
    
    def test_notifications(self) -> Tuple[bool, str]:
        """Test notification service"""
        try:
            # Test notification sending
            notif_url = f"{self.base_url}:5011/send-notification"
            notif_data = {
                "type": "email",
                "recipient": "test@example.com",
                "subject": "Test Notification",
                "message": "This is a test notification"
            }
            response = requests.post(notif_url, json=notif_data, timeout=10)
            if response.status_code == 201:
                return True, "Notification service - Notification sent successfully"
            else:
                return False, f"Notification service failed - Status: {response.status_code}"
        except requests.exceptions.RequestException as e:
            return False, f"Notification service test failed - {str(e)}"
    
    def run_all_tests(self):
        """Run all tests"""
        print("🧪 SkillScreen Backend Services Testing")
        print("=" * 50)
        
        # Test individual services
        print("\n📋 Testing Individual Services:")
        print("-" * 30)
        
        for service_key, config in SERVICES.items():
            port = config['port']
            name = config['name']
            
            print(f"\n🔍 Testing {name} (port {port})...")
            
            # Health check
            health_ok, health_msg = self.test_service_health(service_key, port)
            print(f"   Health: {'✅' if health_ok else '❌'} {health_msg}")
            
            # Info endpoint
            info_ok, info_msg = self.test_service_info(service_key, port)
            print(f"   Info:   {'✅' if info_ok else '❌'} {info_msg}")
            
            self.results[service_key] = {
                'health': health_ok,
                'info': info_ok,
                'name': name,
                'port': port
            }
        
        # Test specific functionality
        print("\n🔧 Testing Service Functionality:")
        print("-" * 35)
        
        # API Gateway routing
        gateway_ok, gateway_msg = self.test_api_gateway_routing()
        print(f"API Gateway Routing: {'✅' if gateway_ok else '❌'} {gateway_msg}")
        
        # Authentication flow
        auth_ok, auth_msg = self.test_auth_flow()
        print(f"Authentication Flow: {'✅' if auth_ok else '❌'} {auth_msg}")
        
        # User CRUD
        user_ok, user_msg = self.test_user_crud()
        print(f"User CRUD Operations: {'✅' if user_ok else '❌'} {user_msg}")
        
        # AI Services
        ai_ok, ai_msg = self.test_ai_services()
        print(f"AI Services: {'✅' if ai_ok else '❌'} {ai_msg}")
        
        # Logging
        log_ok, log_msg = self.test_logging()
        print(f"Logging Service: {'✅' if log_ok else '❌'} {log_msg}")
        
        # Notifications
        notif_ok, notif_msg = self.test_notifications()
        print(f"Notification Service: {'✅' if notif_ok else '❌'} {notif_msg}")
        
        # Summary
        print("\n📊 Test Summary:")
        print("=" * 50)
        
        healthy_services = sum(1 for r in self.results.values() if r['health'])
        total_services = len(self.results)
        
        print(f"Healthy Services: {healthy_services}/{total_services}")
        print(f"API Gateway Routing: {'✅' if gateway_ok else '❌'}")
        print(f"Authentication: {'✅' if auth_ok else '❌'}")
        print(f"User Operations: {'✅' if user_ok else '❌'}")
        print(f"AI Services: {'✅' if ai_ok else '❌'}")
        print(f"Logging: {'✅' if log_ok else '❌'}")
        print(f"Notifications: {'✅' if notif_ok else '❌'}")
        
        # Overall status
        all_basic_tests = healthy_services == total_services
        all_functional_tests = gateway_ok and auth_ok and user_ok and ai_ok and log_ok and notif_ok
        
        print(f"\n🎯 Overall Status:")
        if all_basic_tests and all_functional_tests:
            print("🎉 ALL TESTS PASSED! All services are working correctly.")
            return True
        else:
            print("⚠️  SOME TESTS FAILED! Check the details above.")
            return False

def main():
    """Main function"""
    print("Starting SkillScreen Backend Services Test...")
    print("Make sure all services are running with: docker-compose up -d")
    print("Waiting 5 seconds for services to be ready...")
    time.sleep(5)
    
    tester = ServiceTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ All services are working correctly!")
        sys.exit(0)
    else:
        print("\n❌ Some services have issues. Check the logs:")
        print("   docker-compose logs")
        sys.exit(1)

if __name__ == "__main__":
    main()
