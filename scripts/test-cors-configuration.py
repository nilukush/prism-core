#!/usr/bin/env python3
"""
Test CORS Configuration for PRISM Backend
Tests CORS from multiple origins to ensure proper configuration
"""

import requests
import sys
from typing import List, Dict
from colorama import init, Fore, Style

# Initialize colorama for cross-platform colored output
init(autoreset=True)

# Configuration
BACKEND_URL = "https://prism-backend-bwfx.onrender.com"
HEALTH_ENDPOINT = f"{BACKEND_URL}/health"
API_ENDPOINT = f"{BACKEND_URL}/api/v1/health"

# Origins to test
TEST_ORIGINS = [
    "https://prism-9z5biinym-nilukushs-projects.vercel.app",  # New production
    "https://prism-frontend-kappa.vercel.app",                 # Old domain
    "http://localhost:3000",                                    # Local development
    "http://localhost:3100",                                    # Alternative local
    "https://malicious-site.com"                               # Should be rejected
]

def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{Fore.CYAN}{'=' * 60}")
    print(f"{Fore.CYAN}{text}")
    print(f"{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}")

def print_test_result(origin: str, test_type: str, success: bool, details: str = ""):
    """Print test result with color coding"""
    status = f"{Fore.GREEN}✅ PASS" if success else f"{Fore.RED}❌ FAIL"
    print(f"\n{status}{Style.RESET_ALL} {test_type} from {Fore.YELLOW}{origin}{Style.RESET_ALL}")
    if details:
        print(f"   {Fore.GRAY}{details}{Style.RESET_ALL}")

def test_preflight_request(origin: str) -> Dict[str, any]:
    """Test CORS preflight (OPTIONS) request"""
    headers = {
        'Origin': origin,
        'Access-Control-Request-Method': 'GET',
        'Access-Control-Request-Headers': 'Content-Type, Authorization'
    }
    
    try:
        response = requests.options(HEALTH_ENDPOINT, headers=headers, timeout=10)
        
        cors_headers = {
            'allow_origin': response.headers.get('Access-Control-Allow-Origin', 'Not Set'),
            'allow_methods': response.headers.get('Access-Control-Allow-Methods', 'Not Set'),
            'allow_headers': response.headers.get('Access-Control-Allow-Headers', 'Not Set'),
            'allow_credentials': response.headers.get('Access-Control-Allow-Credentials', 'Not Set'),
            'max_age': response.headers.get('Access-Control-Max-Age', 'Not Set')
        }
        
        return {
            'success': response.status_code == 200 and cors_headers['allow_origin'] == origin,
            'status_code': response.status_code,
            'cors_headers': cors_headers
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def test_actual_request(origin: str) -> Dict[str, any]:
    """Test actual GET request with origin header"""
    headers = {
        'Origin': origin,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(HEALTH_ENDPOINT, headers=headers, timeout=10)
        
        cors_origin = response.headers.get('Access-Control-Allow-Origin', 'Not Set')
        cors_credentials = response.headers.get('Access-Control-Allow-Credentials', 'Not Set')
        
        return {
            'success': response.status_code == 200 and cors_origin == origin,
            'status_code': response.status_code,
            'cors_origin': cors_origin,
            'cors_credentials': cors_credentials,
            'body': response.json() if response.status_code == 200 else None
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def test_api_endpoint(origin: str) -> Dict[str, any]:
    """Test API v1 endpoint"""
    headers = {
        'Origin': origin,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(API_ENDPOINT, headers=headers, timeout=10)
        
        cors_origin = response.headers.get('Access-Control-Allow-Origin', 'Not Set')
        
        return {
            'success': response.status_code in [200, 401] and cors_origin == origin,
            'status_code': response.status_code,
            'cors_origin': cors_origin
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def main():
    """Run all CORS tests"""
    print_header("PRISM Backend CORS Configuration Test")
    print(f"Backend URL: {Fore.YELLOW}{BACKEND_URL}{Style.RESET_ALL}")
    
    # Test results summary
    all_passed = True
    allowed_origins = []
    rejected_origins = []
    
    for origin in TEST_ORIGINS:
        print_header(f"Testing Origin: {origin}")
        
        # Test 1: Preflight request
        preflight_result = test_preflight_request(origin)
        is_allowed = preflight_result['success']
        
        if 'error' in preflight_result:
            print_test_result(origin, "Preflight Request", False, f"Error: {preflight_result['error']}")
            all_passed = False
        else:
            details = f"Status: {preflight_result['status_code']}, "
            details += f"Allow-Origin: {preflight_result['cors_headers']['allow_origin']}"
            print_test_result(origin, "Preflight Request", is_allowed, details)
            
            if is_allowed:
                print(f"   {Fore.GRAY}Allow-Methods: {preflight_result['cors_headers']['allow_methods']}")
                print(f"   {Fore.GRAY}Allow-Headers: {preflight_result['cors_headers']['allow_headers']}")
                print(f"   {Fore.GRAY}Allow-Credentials: {preflight_result['cors_headers']['allow_credentials']}")
        
        # Test 2: Actual request
        actual_result = test_actual_request(origin)
        
        if 'error' in actual_result:
            print_test_result(origin, "GET Request", False, f"Error: {actual_result['error']}")
            all_passed = False
        else:
            details = f"Status: {actual_result['status_code']}, "
            details += f"CORS-Origin: {actual_result['cors_origin']}"
            print_test_result(origin, "GET Request", actual_result['success'], details)
            
            if actual_result['success'] and actual_result['body']:
                print(f"   {Fore.GRAY}Response: {actual_result['body']}")
        
        # Test 3: API endpoint
        api_result = test_api_endpoint(origin)
        
        if 'error' in api_result:
            print_test_result(origin, "API Request", False, f"Error: {api_result['error']}")
            all_passed = False
        else:
            details = f"Status: {api_result['status_code']}, "
            details += f"CORS-Origin: {api_result['cors_origin']}"
            print_test_result(origin, "API Request", api_result['success'], details)
        
        # Track allowed/rejected origins
        if is_allowed and origin != "https://malicious-site.com":
            allowed_origins.append(origin)
        elif not is_allowed and origin == "https://malicious-site.com":
            rejected_origins.append(origin)
        else:
            all_passed = False
    
    # Summary
    print_header("Test Summary")
    
    print(f"\n{Fore.GREEN}Allowed Origins:{Style.RESET_ALL}")
    for origin in allowed_origins:
        print(f"  ✅ {origin}")
    
    print(f"\n{Fore.RED}Rejected Origins:{Style.RESET_ALL}")
    for origin in rejected_origins:
        print(f"  ❌ {origin}")
    
    if all_passed and len(allowed_origins) == 4:
        print(f"\n{Fore.GREEN}🎉 All CORS tests passed! The configuration is correct.{Style.RESET_ALL}")
        return 0
    else:
        print(f"\n{Fore.RED}⚠️  Some CORS tests failed. Please check the configuration.{Style.RESET_ALL}")
        print(f"\nExpected to allow: {TEST_ORIGINS[:-1]}")
        print(f"Expected to reject: {TEST_ORIGINS[-1:]}")
        return 1

if __name__ == "__main__":
    sys.exit(main())