#!/usr/bin/env python3
"""
Test script for SQL Server connectivity in the BMI MCP server
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


async def test_sql_connectivity():
    """Test SQL Server connectivity and functionality"""
    print("🗄️  Testing SQL Server Connectivity...")

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            print("✅ Connected to MCP server")

            # Initialize the session
            await session.initialize()
            print("✅ Session initialized")

            # List available tools
            tools = await session.list_tools()
            sql_tools = [tool.name for tool in tools.tools if 'sql' in tool.name.lower(
            ) or 'table' in tool.name.lower()]
            print(f"📋 Available SQL tools: {sql_tools}")

            print("\n🔗 Testing SQL connection...")
            try:
                # Test SQL connection
                connection_result = await session.call_tool("test_sql_connection", arguments={})
                connection_data = json.loads(connection_result.content[0].text)

                if connection_data.get("connected"):
                    print("✅ SQL Connection successful!")
                    print(f"   Server: {connection_data.get('server')}")
                    print(
                        f"   Database: {connection_data.get('database_name')}")
                    print(
                        f"   Version: {connection_data.get('server_version', 'Unknown')[:100]}...")

                    # Test getting table list
                    print("\n📊 Getting table list...")
                    tables_result = await session.call_tool("get_table_list", arguments={})
                    tables_data = json.loads(tables_result.content[0].text)

                    if tables_data.get("status") == "success":
                        table_count = tables_data.get("table_count", 0)
                        print(f"✅ Found {table_count} tables")

                        if table_count > 0:
                            # Show first few tables
                            tables = tables_data.get("tables", [])[:5]
                            print("   First 5 tables:")
                            for table in tables:
                                print(
                                    f"     - {table.get('full_name')} ({table.get('table_type')})")

                            # Test getting schema for first table if available
                            if tables:
                                first_table = tables[0]
                                print(
                                    f"\n📋 Getting schema for table: {first_table.get('full_name')}")

                                schema_result = await session.call_tool(
                                    "get_table_schema",
                                    arguments={
                                        "table_name": first_table.get('table_name'),
                                        "schema_name": first_table.get('schema')
                                    }
                                )
                                schema_data = json.loads(
                                    schema_result.content[0].text)

                                if schema_data.get("status") == "success":
                                    columns = schema_data.get("columns", [])
                                    print(
                                        f"✅ Table has {len(columns)} columns:")
                                    for col in columns[:3]:  # Show first 3 columns
                                        print(
                                            f"     - {col.get('column_name')} ({col.get('data_type')})")
                                else:
                                    print(
                                        f"❌ Schema error: {schema_data.get('error')}")
                    else:
                        print(
                            f"❌ Table list error: {tables_data.get('error')}")

                    # Test a simple query
                    print("\n🔍 Testing simple query...")
                    simple_query = "SELECT TOP 1 @@VERSION as version, GETDATE() as current_datetime"

                    query_result = await session.call_tool(
                        "query_sql_server",
                        arguments={"query": simple_query}
                    )
                    query_data = json.loads(query_result.content[0].text)

                    if query_data.get("status") == "success":
                        print("✅ Query executed successfully!")
                        print(
                            f"   Returned {query_data.get('row_count')} rows")
                        if query_data.get('data'):
                            data = query_data['data'][0]
                            print(
                                f"   Current time: {data.get('current_datetime')}")
                    else:
                        print(f"❌ Query error: {query_data.get('error')}")

                else:
                    print(
                        f"❌ SQL Connection failed: {connection_data.get('error')}")
                    print("\n🔧 Troubleshooting tips:")
                    print("   - Make sure you have network access to the SQL Server")
                    print("   - Verify your Azure AD credentials are valid")
                    print(
                        "   - Check if the ODBC Driver 18 for SQL Server is installed")
                    print("   - Try running: brew install msodbcsql18 (if on macOS)")

            except Exception as e:
                print(f"❌ Test failed with exception: {e}")
                import traceback
                traceback.print_exc()


def test_sql_safety():
    """Test SQL query safety features"""
    print("\n🛡️  Testing SQL Safety Features...")

    dangerous_queries = [
        "DROP TABLE test",
        "DELETE FROM users",
        "INSERT INTO test VALUES (1)",
        "UPDATE users SET name='hacker'",
        "CREATE TABLE malicious (id int)"
    ]

    print("Testing that dangerous queries are blocked:")

    # We'll test this by importing the function directly
    import sys
    import os
    sys.path.append(
        '/Users/balachandarramalingam/Projects/TestMCPServer-SSEinPython/TestMCPServer-SSEinPython')

    try:
        from bmi_server import query_sql_server
        import json

        for query in dangerous_queries:
            result_str = query_sql_server(query)
            try:
                result = json.loads(result_str)
                if isinstance(result, dict) and "error" in result:
                    print(f"   ✅ Blocked: {query[:30]}...")
                else:
                    print(f"   ❌ NOT BLOCKED: {query[:30]}...")
            except json.JSONDecodeError:
                print(f"   ❌ Invalid JSON response: {query[:30]}...")
    except Exception as e:
        print(f"   ❌ Error testing safety: {e}")


async def main():
    """Run all SQL tests"""
    print("🚀 Starting SQL Server Tests\n")

    try:
        await test_sql_connectivity()
        test_sql_safety()

        print("\n✅ SQL Server tests completed!")

    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
