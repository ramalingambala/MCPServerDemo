#!/usr/bin/env python3
"""
Test the MCP server in SSE (web) mode
"""
import requests
import json
import time

def test_sse_server():
    """Test the server running in SSE mode"""
    server_url = "http://127.0.0.1:8000"
    
    print("🌐 Testing MCP Server in SSE (Web) Mode")
    print(f"Server URL: {server_url}")
    
    # Test if server is running
    try:
        response = requests.get(f"{server_url}/health", timeout=5)
        print(f"✅ Server health check: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Server not responding: {e}")
        print("💡 Make sure to start the server first:")
        print("   ./venv/bin/python bmi_server.py --sse")
        return
    
    # Test SSE endpoint
    try:
        response = requests.get(f"{server_url}/sse", timeout=5)
        print(f"✅ SSE endpoint accessible: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('content-type', 'Not set')}")
    except requests.exceptions.RequestException as e:
        print(f"❌ SSE endpoint error: {e}")

def manual_test_instructions():
    """Print manual testing instructions"""
    print("\n📋 Manual Testing Options:")
    print("=" * 50)
    
    print("\n1️⃣ Test with Python Client (Recommended):")
    print("   ./venv/bin/python test_bmi_server.py")
    
    print("\n2️⃣ Test with Web Browser (SSE Mode):")
    print("   # Terminal 1: Start server")
    print("   ./venv/bin/python bmi_server.py --sse")
    print("   # Terminal 2: Test endpoints")
    print("   curl http://127.0.0.1:8000/sse")
    
    print("\n3️⃣ Test individual functions:")
    print("   python3 -c \"from bmi_server import calculate_bmi; print(f'BMI: {calculate_bmi(70, 1.75):.2f}')\"")
    
    print("\n4️⃣ Test with custom values:")
    test_cases = [
        (65.0, 1.70, "Normal"),
        (90.0, 1.80, "Overweight"), 
        (55.0, 1.60, "Underweight")
    ]
    
    print("   # BMI Test Cases:")
    for weight, height, category in test_cases:
        bmi = weight / (height ** 2)
        print(f"   Weight: {weight}kg, Height: {height}m → BMI: {bmi:.2f} ({category})")

if __name__ == "__main__":
    test_sse_server()
    manual_test_instructions()