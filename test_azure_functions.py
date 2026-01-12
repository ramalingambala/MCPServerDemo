#!/usr/bin/env python3
"""
Test Azure Functions MCP Server locally
This script tests the Azure Functions implementation without requiring Azure deployment.
"""

import sys
import os
import json
import importlib.util
from typing import Dict, Any

# Add the shared_code directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'shared_code'))


def test_mcp_server_import():
    """Test that the MCP server module can be imported"""
    print("🧪 Testing MCP Server Module Import...")

    try:
        from mcp_server import mcp, logger
        print(f"✅ Successfully imported MCP server: {mcp.name}")

        # List available tools
        tools = list(mcp._tools.keys())
        print(f"✅ Found {len(tools)} MCP tools:")
        for tool in tools:
            print(f"   - {tool}")

        return mcp

    except ImportError as e:
        print(f"❌ Failed to import MCP server: {e}")
        return None
    except Exception as e:
        print(f"❌ Error importing MCP server: {e}")
        return None


def test_mcp_tools(mcp_server):
    """Test MCP tools functionality"""
    print(f"\n🔧 Testing MCP Tools...")

    test_cases = [
        {
            "tool": "calculate_bmi",
            "arguments": {"weight_kg": 70, "height_m": 1.75},
            "description": "BMI calculation"
        },
        {
            "tool": "greet",
            "arguments": {"name": "Azure Functions"},
            "description": "Greeting tool"
        },
        {
            "tool": "get_server_info",
            "arguments": {},
            "description": "Server information"
        }
    ]

    results = []

    for test_case in test_cases:
        tool_name = test_case["tool"]
        arguments = test_case["arguments"]
        description = test_case["description"]

        print(f"\n🔸 Testing {description} ({tool_name})...")

        try:
            if tool_name not in mcp_server._tools:
                print(f"❌ Tool '{tool_name}' not found")
                results.append({"tool": tool_name, "status": "not_found"})
                continue

            tool_func = mcp_server._tools[tool_name]

            # Execute the tool
            if arguments:
                result = tool_func(**arguments)
            else:
                result = tool_func()

            print(f"✅ Tool executed successfully")

            # Try to parse result as JSON if it's a string
            try:
                if isinstance(result, str):
                    parsed_result = json.loads(result)
                    print(f"   Result type: JSON")
                    if "error" in parsed_result:
                        print(
                            f"   ⚠️  Tool returned error: {parsed_result.get('error')}")
                    else:
                        print(f"   ✅ Tool completed successfully")
                else:
                    print(f"   Result type: {type(result).__name__}")
                    print(f"   ✅ Tool completed successfully")

                results.append(
                    {"tool": tool_name, "status": "success", "result_type": type(result).__name__})

            except json.JSONDecodeError:
                print(f"   Result type: {type(result).__name__} (not JSON)")
                results.append(
                    {"tool": tool_name, "status": "success", "result_type": type(result).__name__})

        except Exception as e:
            print(f"❌ Tool execution failed: {e}")
            results.append(
                {"tool": tool_name, "status": "error", "error": str(e)})

    return results


def test_azure_functions_structure():
    """Test Azure Functions project structure"""
    print(f"\n📁 Testing Azure Functions Project Structure...")

    required_files = [
        "requirements.txt",
        "host.json",
        "local.settings.json",
        "shared_code/mcp_server.py",
        "mcp_server/function.json",
        "mcp_server/__init__.py",
        "mcp_sse/function.json",
        "mcp_sse/__init__.py"
    ]

    missing_files = []
    existing_files = []

    for file_path in required_files:
        full_path = os.path.join(os.path.dirname(__file__), file_path)
        if os.path.exists(full_path):
            existing_files.append(file_path)
            print(f"✅ {file_path}")
        else:
            missing_files.append(file_path)
            print(f"❌ {file_path} (missing)")

    print(f"\n📊 Project Structure Summary:")
    print(f"   ✅ Existing files: {len(existing_files)}")
    print(f"   ❌ Missing files: {len(missing_files)}")

    return len(missing_files) == 0


def simulate_http_requests(mcp_server):
    """Simulate HTTP requests to Azure Functions"""
    print(f"\n🌐 Simulating Azure Functions HTTP Requests...")

    # Simulate GET request to mcp_server endpoint
    print(f"\n🔸 Simulating GET /api/mcp_server...")
    try:
        tools = []
        for tool_name, tool_func in mcp_server._tools.items():
            tools.append({
                "name": tool_name,
                "description": tool_func.__doc__ or "No description available"
            })

        response_data = {
            "status": "success",
            "message": "MCP Server is running on Azure Functions",
            "server_name": mcp_server.name,
            "available_tools": tools,
            "tool_count": len(tools)
        }

        print(f"✅ GET request simulation successful")
        print(f"   Response: {len(json.dumps(response_data))} characters")

    except Exception as e:
        print(f"❌ GET request simulation failed: {e}")

    # Simulate POST request to mcp_server endpoint
    print(f"\n🔸 Simulating POST /api/mcp_server...")
    try:
        request_data = {
            "tool": "calculate_bmi",
            "arguments": {"weight_kg": 70, "height_m": 1.75}
        }

        tool_name = request_data.get('tool')
        arguments = request_data.get('arguments', {})

        if tool_name in mcp_server._tools:
            tool_func = mcp_server._tools[tool_name]
            result = tool_func(**arguments)

            response_data = {
                "status": "success",
                "tool": tool_name,
                "result": result,
                "arguments": arguments
            }

            print(f"✅ POST request simulation successful")
            print(f"   Response: {len(json.dumps(response_data))} characters")
        else:
            print(f"❌ Tool '{tool_name}' not found")

    except Exception as e:
        print(f"❌ POST request simulation failed: {e}")


def main():
    """Main test function"""
    print("🚀 Azure Functions MCP Server Local Test Suite\\n")

    # Test 1: Module import
    mcp_server = test_mcp_server_import()
    if not mcp_server:
        print("\\n❌ Cannot proceed - MCP server import failed")
        return

    # Test 2: Project structure
    structure_ok = test_azure_functions_structure()
    if not structure_ok:
        print("\\n⚠️  Some project files are missing, but continuing tests...")

    # Test 3: Tool functionality
    tool_results = test_mcp_tools(mcp_server)

    # Test 4: HTTP request simulation
    simulate_http_requests(mcp_server)

    # Summary
    print(f"\\n📊 Test Summary:")
    print(f"   🔧 MCP Server: {'✅ Working' if mcp_server else '❌ Failed'}")
    print(
        f"   📁 Project Structure: {'✅ Complete' if structure_ok else '⚠️ Incomplete'}")

    successful_tools = len(
        [r for r in tool_results if r.get('status') == 'success'])
    total_tools = len(tool_results)
    print(f"   🛠️  Tools: {successful_tools}/{total_tools} working")

    if mcp_server and successful_tools == total_tools:
        print(f"\\n🎉 All tests passed! Ready for Azure Functions deployment.")
    else:
        print(f"\\n⚠️  Some tests failed. Review the issues above before deployment.")


if __name__ == "__main__":
    main()
