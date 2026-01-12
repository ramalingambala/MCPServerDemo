#!/usr/bin/env python3
"""
Debug the MCP tool responses
"""
import asyncio
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

async def debug_tools():
    """Debug tool responses"""
    print("🔍 Debugging MCP Tool Responses...")
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Test each tool and print raw responses
            tools_to_test = [
                ("list_sql_configurations", {}),
                ("test_network_connectivity", {}),
                ("greet", {"name": "Test"})
            ]
            
            for tool_name, args in tools_to_test:
                print(f"\n🛠️  Testing tool: {tool_name}")
                print("-" * 40)
                
                try:
                    result = await session.call_tool(tool_name, arguments=args)
                    
                    print(f"Response type: {type(result)}")
                    print(f"Content length: {len(result.content)}")
                    
                    for i, content in enumerate(result.content):
                        print(f"Content {i}: {type(content)}")
                        print(f"Content {i} text (first 200 chars): {str(content.text)[:200]}")
                        
                        if hasattr(content, 'text') and content.text:
                            print(f"Full text: {content.text}")
                
                except Exception as e:
                    print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_tools())