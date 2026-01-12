#!/usr/bin/env python3
"""
Quick test for Docker SQL Server connectivity
"""

import asyncio
import json
from contextlib import asynccontextmanager

# MCP client imports
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@asynccontextmanager
async def mcp_client():
    """Create MCP client connection"""
    server_params = StdioServerParameters(
        command="python",
        args=["/Users/balachandarramalingam/Projects/TestMCPServer-SSEinPython/TestMCPServer-SSEinPython/bmi_server.py"],
        env=None
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


async def test_docker_connectivity():
    """Test Docker SQL Server connectivity"""
    print("🧪 Testing Docker SQL Server connectivity...\n")

    try:
        async with mcp_client() as session:
            # Switch to docker_test configuration
            print("🔄 Switching to docker_test configuration...")
            switch_result = await session.call_tool(
                "set_sql_configuration",
                arguments={"config_name": "docker_test"}
            )

            switch_data = json.loads(switch_result.content[0].text)
            if switch_data.get("status") == "success":
                print(f"✅ Switched to docker_test configuration")
            else:
                print(f"❌ Failed to switch: {switch_data.get('error')}")
                return

            # Test network connectivity to localhost:1433
            print("\n🌐 Testing network connectivity to localhost:1433...")
            network_result = await session.call_tool("test_network_connectivity")
            network_data = json.loads(network_result.content[0].text)

            if network_data.get("reachable"):
                print(
                    f"✅ Network connection successful ({network_data.get('response_time_ms')}ms)")
            else:
                print(
                    f"❌ Network connection failed: {network_data.get('error')}")
                return

            # Test SQL connection
            print("\n🔗 Testing SQL Server connection...")
            sql_result = await session.call_tool("test_sql_connection")
            sql_data = json.loads(sql_result.content[0].text)

            if sql_data.get("connected"):
                print(f"✅ SQL connection successful!")
                print(f"   Database: {sql_data.get('database_name')}")
                print(
                    f"   Server Version: {sql_data.get('server_version', '')[:80]}...")

                # Test a simple query
                print("\n📊 Testing SQL query...")
                query_result = await session.call_tool(
                    "query_sql_server",
                    arguments={
                        "query": "SELECT GETDATE() as current_time, @@SERVERNAME as server_name"}
                )
                query_data = json.loads(query_result.content[0].text)

                if query_data.get("status") == "success":
                    print(f"✅ Query executed successfully!")
                    if query_data.get('data'):
                        data = query_data['data'][0]
                        print(f"   Current time: {data.get('current_time')}")
                        print(f"   Server name: {data.get('server_name')}")
                else:
                    print(f"❌ Query failed: {query_data.get('error')}")

            else:
                print(f"❌ SQL connection failed: {sql_data.get('error')}")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_docker_connectivity())
