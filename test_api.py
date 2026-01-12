#!/usr/bin/env python3
"""
Test script for MCP BMI Calculator API endpoints
"""

import requests
import json
import time
import subprocess
import sys


def test_server():
    """Test the MCP server endpoints"""
    base_url = "http://localhost:7071"

    print("🧪 Testing MCP BMI Calculator API")
    print("=" * 50)

    try:
        # Test 1: GET endpoint - Server info
        print("1. Testing GET endpoint (server info)...")
        response = requests.get(base_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Server Status: {data.get('status', 'Unknown')}")
            print(f"   ✅ Available Tools: {data.get('tool_count', 0)}")
            print(f"   ✅ Server Name: {data.get('server_name', 'Unknown')}")

            # List available tools
            tools = data.get('available_tools', [])
            if tools:
                print("   📋 Available Tools:")
                for tool in tools[:5]:  # Show first 5 tools
                    print(
                        f"      - {tool.get('name', 'Unknown')}: {tool.get('description', 'No description')[:50]}...")
        else:
            print(f"   ❌ GET request failed: {response.status_code}")
            return False

        # Test 2: POST endpoint - BMI Calculation
        print("\n2. Testing POST endpoint (BMI calculation)...")
        bmi_request = {
            "tool": "calculate_bmi",
            "arguments": {
                "weight_kg": 70,
                "height_m": 1.75
            }
        }

        response = requests.post(
            base_url,
            json=bmi_request,
            headers={"Content-Type": "application/json"},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ BMI Calculation: {data.get('status', 'Unknown')}")

            # Parse the result
            result = data.get('result', '')
            if result:
                try:
                    bmi_data = json.loads(result)
                    print(f"   📊 BMI: {bmi_data.get('bmi', 'Unknown')}")
                    print(
                        f"   📊 Category: {bmi_data.get('category', 'Unknown')}")
                    print(
                        f"   📊 Health Risks: {len(bmi_data.get('health_information', {}).get('risks', []))} items")
                    print(
                        f"   📚 Resources: {len(bmi_data.get('resources', {}))} available")
                except json.JSONDecodeError:
                    print(f"   📄 Raw Result: {result[:100]}...")
        else:
            print(f"   ❌ BMI calculation failed: {response.status_code}")
            print(f"   📄 Response: {response.text}")
            return False

        # Test 3: POST endpoint - BMI Resources
        print("\n3. Testing POST endpoint (BMI resources)...")
        resource_request = {
            "tool": "get_bmi_resources",
            "arguments": {
                "resource_type": "categories"
            }
        }

        response = requests.post(
            base_url,
            json=resource_request,
            headers={"Content-Type": "application/json"},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ BMI Resources: {data.get('status', 'Unknown')}")
            print(f"   📚 Resource Tool: {data.get('tool', 'Unknown')}")
        else:
            print(f"   ❌ BMI resources failed: {response.status_code}")

        # Test 4: Error handling
        print("\n4. Testing error handling (invalid tool)...")
        error_request = {
            "tool": "invalid_tool",
            "arguments": {}
        }

        response = requests.post(
            base_url,
            json=error_request,
            headers={"Content-Type": "application/json"},
            timeout=10
        )

        if response.status_code >= 400:
            print(f"   ✅ Error handling working: {response.status_code}")
        else:
            print(f"   ⚠️  Expected error but got: {response.status_code}")

        print("\n🎯 API Testing Complete!")
        print("✅ Server is ready for Postman/curl testing")
        return True

    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Server not running on localhost:7071")
        return False
    except requests.exceptions.Timeout:
        print("❌ Timeout Error: Server not responding")
        return False
    except Exception as e:
        print(f"❌ Test Error: {e}")
        return False


def create_postman_collection():
    """Create a Postman collection for testing"""
    collection = {
        "info": {
            "name": "MCP BMI Calculator API",
            "description": "Test collection for MCP BMI Calculator with enhanced resources",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "item": [
            {
                "name": "Get Server Info",
                "request": {
                    "method": "GET",
                    "url": "http://localhost:7071/",
                    "description": "Get server information and available tools"
                }
            },
            {
                "name": "Calculate BMI - Normal Weight",
                "request": {
                    "method": "POST",
                    "url": "http://localhost:7071/",
                    "header": [
                        {
                            "key": "Content-Type",
                            "value": "application/json"
                        }
                    ],
                    "body": {
                        "mode": "raw",
                        "raw": json.dumps({
                            "tool": "calculate_bmi",
                            "arguments": {
                                "weight_kg": 70,
                                "height_m": 1.75
                            }
                        }, indent=2)
                    }
                }
            },
            {
                "name": "Calculate BMI - Underweight",
                "request": {
                    "method": "POST",
                    "url": "http://localhost:7071/",
                    "header": [
                        {
                            "key": "Content-Type",
                            "value": "application/json"
                        }
                    ],
                    "body": {
                        "mode": "raw",
                        "raw": json.dumps({
                            "tool": "calculate_bmi",
                            "arguments": {
                                "weight_kg": 45,
                                "height_m": 1.70
                            }
                        }, indent=2)
                    }
                }
            },
            {
                "name": "Calculate BMI - Obese",
                "request": {
                    "method": "POST",
                    "url": "http://localhost:7071/",
                    "header": [
                        {
                            "key": "Content-Type",
                            "value": "application/json"
                        }
                    ],
                    "body": {
                        "mode": "raw",
                        "raw": json.dumps({
                            "tool": "calculate_bmi",
                            "arguments": {
                                "weight_kg": 120,
                                "height_m": 1.70
                            }
                        }, indent=2)
                    }
                }
            },
            {
                "name": "Get BMI Resources - All",
                "request": {
                    "method": "POST",
                    "url": "http://localhost:7071/",
                    "header": [
                        {
                            "key": "Content-Type",
                            "value": "application/json"
                        }
                    ],
                    "body": {
                        "mode": "raw",
                        "raw": json.dumps({
                            "tool": "get_bmi_resources",
                            "arguments": {
                                "resource_type": "all"
                            }
                        }, indent=2)
                    }
                }
            },
            {
                "name": "Get BMI Resources - Categories",
                "request": {
                    "method": "POST",
                    "url": "http://localhost:7071/",
                    "header": [
                        {
                            "key": "Content-Type",
                            "value": "application/json"
                        }
                    ],
                    "body": {
                        "mode": "raw",
                        "raw": json.dumps({
                            "tool": "get_bmi_resources",
                            "arguments": {
                                "resource_type": "categories"
                            }
                        }, indent=2)
                    }
                }
            }
        ]
    }

    # Save collection to file
    with open('MCP_BMI_Calculator_Postman_Collection.json', 'w') as f:
        json.dump(collection, f, indent=2)

    print("📝 Postman collection saved to: MCP_BMI_Calculator_Postman_Collection.json")


if __name__ == "__main__":
    print("🚀 MCP BMI Calculator API Tester")
    print("=" * 50)

    # Check if server is running
    print("Checking if server is running on localhost:7071...")
    success = test_server()

    if success:
        print("\n📦 Creating Postman collection...")
        create_postman_collection()

        print("\n🎯 Next Steps:")
        print("1. Keep the server running: python local_test_server.py")
        print(
            "2. Import the Postman collection: MCP_BMI_Calculator_Postman_Collection.json")
        print("3. Test the endpoints in Postman")
        print("4. Or use the curl commands shown by the server")
    else:
        print("\n🔧 To start the server:")
        print("cd /path/to/project && source .venv/bin/activate && python local_test_server.py")
