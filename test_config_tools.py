#!/usr/bin/env python3
"""
Test the new SQL configuration tools in the MCP server
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

async def test_configuration_tools():
    """Test the SQL configuration management tools"""
    print("⚙️  Testing SQL Configuration Tools...")
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            print("✅ Connected to MCP server")
            
            # Initialize the session
            await session.initialize()
            
            # List available tools
            tools = await session.list_tools()
            config_tools = [tool.name for tool in tools.tools if 'configuration' in tool.name.lower() or 'config' in tool.name.lower()]
            print(f"📋 Available configuration tools: {config_tools}")
            
            # Test listing configurations
            print("\n📋 Listing SQL configurations...")
            try:
                configs_result = await session.call_tool("list_sql_configurations", arguments={})
                configs_data = json.loads(configs_result.content[0].text)
                
                if configs_data.get("status") == "success":
                    print(f"✅ Found {configs_data.get('total_configs')} configurations")
                    print(f"Current config: {configs_data.get('current_config')}")
                    
                    print("\nAvailable configurations:")
                    for config in configs_data.get("configurations", []):
                        current_indicator = "👉 " if config.get("is_current") else "   "
                        print(f"{current_indicator}{config['key']}: {config['name']}")
                        print(f"      Server: {config['server']}")
                        print(f"      Auth: {config['authentication']}")
                else:
                    print(f"❌ Error listing configurations: {configs_data.get('error')}")
            
            except Exception as e:
                print(f"❌ Error testing configuration tools: {e}")
            
            # Test switching configuration
            print(f"\n🔄 Testing configuration switching...")
            try:
                switch_result = await session.call_tool(
                    "set_sql_configuration", 
                    arguments={"config_name": "docker_test"}
                )
                switch_data = json.loads(switch_result.content[0].text)
                
                if switch_data.get("status") == "success":
                    print("✅ Configuration switched successfully")
                    print(f"   From: {switch_data.get('old_config')}")
                    print(f"   To: {switch_data.get('new_config')}")
                    print(f"   Details: {switch_data.get('config_details')}")
                else:
                    print(f"❌ Switch failed: {switch_data.get('error')}")
                
            except Exception as e:
                print(f"❌ Error switching configuration: {e}")
            
            # Test network connectivity tool
            print(f"\n🌐 Testing network connectivity...")
            try:
                network_result = await session.call_tool("test_network_connectivity", arguments={})
                network_data = json.loads(network_result.content[0].text)
                
                if network_data.get("reachable"):
                    print(f"✅ Network is reachable")
                    print(f"   Server: {network_data.get('server')}")
                    print(f"   Port: {network_data.get('port')}")
                    print(f"   Response time: {network_data.get('response_time_ms')}ms")
                else:
                    print(f"❌ Network unreachable: {network_data.get('error')}")
                    
            except Exception as e:
                print(f"❌ Error testing network: {e}")

async def main():
    """Run configuration tool tests"""
    print("🚀 Starting SQL Configuration Tool Tests\n")
    
    try:
        await test_configuration_tools()
        print(f"\n✅ Configuration tool tests completed!")
        
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())