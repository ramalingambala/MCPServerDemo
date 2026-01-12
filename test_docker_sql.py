#!/usr/bin/env python3
"""
Test Docker SQL Server setup and connectivity
"""

import asyncio
import json
import os
import subprocess
import time
from contextlib import asynccontextmanager

# MCP client imports
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def check_docker():
    """Check if Docker is running"""
    try:
        result = subprocess.run(
            ['docker', 'ps'], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False


def start_docker_sql():
    """Start the Docker SQL Server container"""
    print("🐳 Starting Docker SQL Server...")

    if not check_docker():
        print("❌ Docker is not running. Please start Docker Desktop.")
        return False

    try:
        # Start the container
        result = subprocess.run([
            'docker-compose', 'up', '-d'
        ], capture_output=True, text=True, cwd='/Users/balachandarramalingam/Projects/TestMCPServer-SSEinPython/TestMCPServer-SSEinPython')

        if result.returncode != 0:
            print(f"❌ Failed to start Docker container: {result.stderr}")
            return False

        print("✅ Docker SQL Server started successfully")

        # Wait for SQL Server to be ready
        print("⏳ Waiting for SQL Server to be ready...")
        for i in range(30):  # Wait up to 30 seconds
            result = subprocess.run([
                'docker', 'exec', 'test-sqlserver',
                '/opt/mssql-tools/bin/sqlcmd', '-S', 'localhost',
                '-U', 'sa', '-P', os.environ.get('SA_PASSWORD', ''),
                '-Q', 'SELECT 1'
            ], capture_output=True, text=True)

            if result.returncode == 0:
                print("✅ SQL Server is ready!")
                return True

            print(f"   Attempt {i+1}/30: Waiting for SQL Server...")
            time.sleep(2)

        print("❌ SQL Server failed to start within timeout")
        return False

    except Exception as e:
        print(f"❌ Error starting Docker SQL Server: {e}")
        return False


def stop_docker_sql():
    """Stop the Docker SQL Server container"""
    print("🛑 Stopping Docker SQL Server...")
    try:
        subprocess.run(['docker-compose', 'down'],
                       cwd='/Users/balachandarramalingam/Projects/TestMCPServer-SSEinPython/TestMCPServer-SSEinPython')
        print("✅ Docker SQL Server stopped")
    except Exception as e:
        print(f"❌ Error stopping Docker SQL Server: {e}")


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
            # Initialize the session
            await session.initialize()
            yield session


async def test_docker_sql_connectivity():
    """Test SQL connectivity with Docker"""
    print("🧪 Testing Docker SQL Server connectivity...\n")

    try:
        async with mcp_client() as session:
            print("✅ Connected to MCP server")

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
                print(
                    f"❌ Failed to switch configuration: {switch_data.get('error')}")
                return

            # Test network connectivity
            print("\n🌐 Testing network connectivity...")
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
            print("\n🔗 Testing SQL connection...")
            sql_result = await session.call_tool("test_sql_connection")
            sql_data = json.loads(sql_result.content[0].text)

            if sql_data.get("connected"):
                print(f"✅ SQL connection successful!")
                print(f"   Server: {sql_data.get('server')}")
                print(f"   Database: {sql_data.get('database_name')}")
                print(
                    f"   Version: {sql_data.get('server_version', '')[:50]}...")

                # Test a simple query
                print("\n📊 Testing SQL query...")
                query_result = await session.call_tool(
                    "query_sql_server",
                    arguments={
                        "query": "SELECT GETDATE() as current_time, @@VERSION as version"}
                )
                query_data = json.loads(query_result.content[0].text)

                if query_data.get("status") == "success":
                    print(f"✅ Query executed successfully!")
                    print(f"   Rows returned: {query_data.get('row_count')}")
                    if query_data.get('data'):
                        current_time = query_data['data'][0].get(
                            'current_time')
                        print(f"   Current time: {current_time}")
                else:
                    print(f"❌ Query failed: {query_data.get('error')}")

            else:
                print(f"❌ SQL connection failed: {sql_data.get('error')}")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main test function"""
    print("🚀 Docker SQL Server Test Suite\n")

    try:
        # Start Docker SQL Server
        if not start_docker_sql():
            return

        # Test connectivity
        await test_docker_sql_connectivity()

        print("\n✅ All Docker SQL Server tests completed!")

    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Ask if user wants to stop the container
        try:
            response = input(
                "\n🤔 Stop Docker SQL Server? (y/N): ").strip().lower()
            if response in ['y', 'yes']:
                stop_docker_sql()
            else:
                print(
                    "💡 Docker SQL Server is still running. Use 'docker-compose down' to stop it.")
        except KeyboardInterrupt:
            print("\n🛑 Stopping Docker SQL Server...")
            stop_docker_sql()


if __name__ == "__main__":
    asyncio.run(main())
