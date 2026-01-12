#!/usr/bin/env python3
"""
Simple test to validate the Azure Function locally
"""

import azure.functions as func
from mcp_server import main
import asyncio
import json
import sys
import os

# Add shared_code to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'shared_code'))

# Import the function

# Mock Azure Functions HttpRequest and HttpResponse


class MockHttpRequest:
    def __init__(self, method="GET", body=None):
        self.method = method
        self._body = body

    def get_json(self):
        if self._body:
            return json.loads(self._body)
        return None


class MockHttpResponse:
    def __init__(self, body, status_code=200, mimetype="text/plain"):
        self.body = body
        self.status_code = status_code
        self.mimetype = mimetype
        print(f"HTTP {status_code} ({mimetype})")
        print(body)


# Replace func.HttpResponse with our mock
func.HttpResponse = MockHttpResponse


async def test_get_request():
    """Test GET request to see available tools"""
    print("=== Testing GET request ===")
    req = MockHttpRequest("GET")
    # Note: We need to import from the actual function file, not shared_code
    sys.path.append(os.path.join(os.path.dirname(__file__), 'mcp_server'))
    from __init__ import main as mcp_main

    response = await mcp_main(req)
    return response


async def test_bmi_calculation():
    """Test BMI calculation tool"""
    print("\n=== Testing BMI calculation ===")
    req = MockHttpRequest("POST", json.dumps({
        "tool": "calculate_bmi",
        "arguments": {
            "weight_kg": 70,
            "height_m": 1.75
        }
    }))

    sys.path.append(os.path.join(os.path.dirname(__file__), 'mcp_server'))
    from __init__ import main as mcp_main

    response = await mcp_main(req)
    return response


async def test_resources():
    """Test getting BMI resources"""
    print("\n=== Testing BMI resources ===")
    req = MockHttpRequest("POST", json.dumps({
        "tool": "get_bmi_resources",
        "arguments": {
            "resource_type": "categories"
        }
    }))

    sys.path.append(os.path.join(os.path.dirname(__file__), 'mcp_server'))
    from __init__ import main as mcp_main

    response = await mcp_main(req)
    return response


async def main():
    """Run all tests"""
    print("Testing Azure Function locally...")

    try:
        await test_get_request()
        await test_bmi_calculation()
        await test_resources()
        print("\n✅ All tests completed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
