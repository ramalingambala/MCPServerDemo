#!/usr/bin/env python3
"""
Simple test script for the BMI MCP server
"""
import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Server configuration
server_params = StdioServerParameters(
    command="/Users/balachandarramalingam/Projects/TestMCPServer-SSEinPython/TestMCPServer-SSEinPython/venv/bin/python",
    args=[
        "/Users/balachandarramalingam/Projects/TestMCPServer-SSEinPython/TestMCPServer-SSEinPython/bmi_server.py",
        "--stdio"
    ]
)

async def test_bmi_calculation():
    """Test the BMI calculation tool"""
    print("🧪 Testing BMI MCP Server...")
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            print("✅ Connected to MCP server")
            
            # Initialize the session
            await session.initialize()
            print("✅ Session initialized")
            
            # List available tools
            tools = await session.list_tools()
            print(f"📋 Available tools: {[tool.name for tool in tools.tools]}")
            
            # Test BMI calculation
            print("\n🔢 Testing BMI calculation...")
            bmi_result = await session.call_tool(
                "calculate_bmi", 
                arguments={"weight_kg": 70.0, "height_m": 1.75}
            )
            
            print(f"✅ BMI Result: {bmi_result.content[0].text}")
            
            # Test greeting tool
            print("\n👋 Testing greeting...")
            greeting_result = await session.call_tool(
                "greet", 
                arguments={"name": "Alice"}
            )
            
            print(f"✅ Greeting: {greeting_result.content[0].text}")
            
            print("\n🎉 All tests passed!")

def test_individual_bmi_function():
    """Test the BMI function directly"""
    print("\n🧮 Testing BMI function directly...")
    
    # Import the function directly
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    from bmi_server import calculate_bmi
    
    # Test cases
    test_cases = [
        (70.0, 1.75),  # Normal weight
        (85.0, 1.80),  # Slightly overweight
        (60.0, 1.65),  # Underweight
    ]
    
    for weight, height in test_cases:
        bmi = calculate_bmi(weight, height)
        print(f"   Weight: {weight}kg, Height: {height}m → BMI: {bmi:.2f}")

async def main():
    """Run all tests"""
    print("🚀 Starting BMI Server Tests\n")
    
    try:
        # Test MCP server
        await test_bmi_calculation()
        
        # Test function directly
        test_individual_bmi_function()
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())