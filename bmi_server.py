from mcp.server.fastmcp import FastMCP
import math
import pyodbc
import asyncio
import os
from typing import Dict, List, Union, Optional
import json

mcp = FastMCP("BMI & SQL Server")

print(f"Starting server {mcp.name}")

# SQL Server Configuration - Using Docker config for local testing
CURRENT_SQL_CONFIG = "docker_test"  # Changed from azure_relaxed to docker_test

# Import SQL configurations
try:
    from sql_config import SQL_CONFIGURATIONS, get_connection_string_for_config
    SQL_CONFIG = SQL_CONFIGURATIONS[CURRENT_SQL_CONFIG]
except ImportError:
    # Fallback configuration if sql_config.py is not available
    SQL_CONFIG = {
        'server': 'upskilling-dbserver.database.windows.net',
        'database': 'TestDB',
        'username': os.environ.get('SQL_USERNAME', ''),
        'driver': 'ODBC Driver 18 for SQL Server',
        'authentication': 'ActiveDirectoryInteractive',
        'timeout': 60,
        'encrypt': 'yes',
        'trust_server_certificate': 'yes'  # More permissive for connectivity
    }


def get_connection_string(config_name: str = None) -> str:
    """Generate SQL Server connection string using configuration system"""
    try:
        config_to_use = config_name or CURRENT_SQL_CONFIG
        return get_connection_string_for_config(config_to_use)
    except (NameError, ImportError):
        # Fallback to manual configuration
        connection_timeout = SQL_CONFIG['timeout']
        return (
            f"DRIVER={{{SQL_CONFIG['driver']}}};"
            f"SERVER={SQL_CONFIG['server']};"
            f"DATABASE={SQL_CONFIG['database']};"
            f"UID={SQL_CONFIG['username']};"
            f"Authentication={SQL_CONFIG['authentication']};"
            f"Encrypt={SQL_CONFIG['encrypt']};"
            f"TrustServerCertificate={SQL_CONFIG['trust_server_certificate']};"
            f"Connection Timeout={connection_timeout};"
        )


def get_alternative_connection_string() -> str:
    """Get alternative connection string for troubleshooting"""
    return (
        f"DRIVER={{{SQL_CONFIG['driver']}}};"
        f"SERVER={SQL_CONFIG['server']};"
        f"DATABASE={SQL_CONFIG['database']};"
        f"UID={SQL_CONFIG['username']};"
        f"Authentication=ActiveDirectoryPassword;"  # Alternative auth method
        f"Encrypt=yes;"
        f"TrustServerCertificate=yes;"  # Less secure but may help with connectivity
        f"Connection Timeout=60;"
    )


@mcp.tool()
def calculate_bmi(weight_kg: float, height_m: float) -> float:
    """
    Calculate BMI given weight in kg and height in meters.
    """
    if height_m <= 0:
        raise ValueError("Height must be greater than zero.")
    return weight_kg / (height_m ** 2)


@mcp.tool()
def test_network_connectivity() -> str:
    """
    Test network connectivity to the SQL Server
    """
    import socket
    import time

    server_host = SQL_CONFIG['server']
    port = 1433  # Default SQL Server port

    result = {
        "server": server_host,
        "port": port,
        "reachable": False,
        "response_time_ms": None,
        "error": None
    }

    try:
        # Test TCP connection
        start_time = time.time()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)  # 10 second timeout

        connection_result = sock.connect_ex((server_host, port))
        end_time = time.time()

        sock.close()

        if connection_result == 0:
            result["reachable"] = True
            result["response_time_ms"] = round(
                (end_time - start_time) * 1000, 2)
        else:
            result["error"] = f"Connection failed with code: {connection_result}"

    except Exception as e:
        result["error"] = str(e)

    return json.dumps(result, indent=2)


@mcp.tool()
def test_sql_connection() -> str:
    """
    Test the SQL Server connection and return connection status
    """
    try:
        connection_string = get_connection_string()
        cnxn = pyodbc.connect(connection_string)
        cursor = cnxn.cursor()

        # Test with a simple query
        cursor.execute(
            "SELECT @@VERSION as server_version, DB_NAME() as database_name")
        row = cursor.fetchone()

        result = {
            "status": "success",
            "connected": True,
            "server_version": str(row[0]) if row else "Unknown",
            "database_name": str(row[1]) if row else "Unknown",
            "server": SQL_CONFIG['server'],
            "database": SQL_CONFIG['database']
        }

        cursor.close()
        cnxn.close()
        return json.dumps(result, indent=2)

    except Exception as e:
        result = {
            "status": "error",
            "connected": False,
            "error": str(e),
            "server": SQL_CONFIG['server'],
            "database": SQL_CONFIG['database']
        }
        return json.dumps(result, indent=2)


@mcp.tool()
def query_sql_server(query: str) -> str:
    """
    Executes a read-only SQL SELECT query against a SQL Server database
    and returns the results as a list of dictionaries.

    Args:
        query: SQL SELECT query to execute (must be read-only)

    Returns:
        List of dictionaries with query results or error dict
    """
    # Basic safety check - only allow SELECT statements
    query_trimmed = query.strip().upper()
    if not query_trimmed.startswith('SELECT'):
        return json.dumps({"error": "Only SELECT queries are allowed for security reasons"}, indent=2)

    # Check for potentially dangerous keywords
    dangerous_keywords = ['DROP', 'DELETE', 'INSERT',
                          'UPDATE', 'ALTER', 'CREATE', 'TRUNCATE']
    if any(keyword in query_trimmed for keyword in dangerous_keywords):
        return json.dumps({"error": "Query contains potentially dangerous keywords. Only SELECT queries are allowed."}, indent=2)

    try:
        connection_string = get_connection_string()
        cnxn = pyodbc.connect(connection_string)
        cursor = cnxn.cursor()

        cursor.execute(query)

        # Get column names
        columns = [column[0]
                   for column in cursor.description] if cursor.description else []

        # Fetch results
        results = []
        rows = cursor.fetchall()

        for row in rows:
            # Convert row to dictionary
            row_dict = {}
            for i, value in enumerate(row):
                # Handle different data types
                if value is None:
                    row_dict[columns[i]] = None
                elif isinstance(value, (int, float, str, bool)):
                    row_dict[columns[i]] = value
                else:
                    # Convert other types to string
                    row_dict[columns[i]] = str(value)
            results.append(row_dict)

        cursor.close()
        cnxn.close()

        result = {
            "status": "success",
            "row_count": len(results),
            "columns": columns,
            "data": results
        }
        return json.dumps(result, indent=2)

    except Exception as e:
        result = {
            "status": "error",
            "error": str(e),
            "query": query
        }
        return json.dumps(result, indent=2)


@mcp.tool()
def get_table_list() -> str:
    """
    Get a list of all tables in the current database
    """
    query = """
    SELECT 
        TABLE_SCHEMA,
        TABLE_NAME,
        TABLE_TYPE
    FROM INFORMATION_SCHEMA.TABLES 
    WHERE TABLE_TYPE = 'BASE TABLE'
    ORDER BY TABLE_SCHEMA, TABLE_NAME
    """

    try:
        connection_string = get_connection_string()
        cnxn = pyodbc.connect(connection_string)
        cursor = cnxn.cursor()

        cursor.execute(query)
        results = []

        for row in cursor.fetchall():
            results.append({
                "schema": row.TABLE_SCHEMA,
                "table_name": row.TABLE_NAME,
                "table_type": row.TABLE_TYPE,
                "full_name": f"{row.TABLE_SCHEMA}.{row.TABLE_NAME}"
            })

        cursor.close()
        cnxn.close()

        result = {
            "status": "success",
            "table_count": len(results),
            "tables": results
        }
        return json.dumps(result, indent=2)

    except Exception as e:
        result = {
            "status": "error",
            "error": str(e)
        }
        return json.dumps(result, indent=2)


@mcp.tool()
def get_table_schema(table_name: str, schema_name: str = "dbo") -> str:
    """
    Get the schema information for a specific table

    Args:
        table_name: Name of the table
        schema_name: Schema name (default: dbo)
    """
    query = """
    SELECT 
        COLUMN_NAME,
        DATA_TYPE,
        IS_NULLABLE,
        CHARACTER_MAXIMUM_LENGTH,
        NUMERIC_PRECISION,
        NUMERIC_SCALE,
        COLUMN_DEFAULT,
        ORDINAL_POSITION
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = ? AND TABLE_SCHEMA = ?
    ORDER BY ORDINAL_POSITION
    """

    try:
        connection_string = get_connection_string()
        cnxn = pyodbc.connect(connection_string)
        cursor = cnxn.cursor()

        cursor.execute(query, table_name, schema_name)
        results = []

        for row in cursor.fetchall():
            results.append({
                "column_name": row.COLUMN_NAME,
                "data_type": row.DATA_TYPE,
                "is_nullable": row.IS_NULLABLE,
                "max_length": row.CHARACTER_MAXIMUM_LENGTH,
                "numeric_precision": row.NUMERIC_PRECISION,
                "numeric_scale": row.NUMERIC_SCALE,
                "default_value": row.COLUMN_DEFAULT,
                "position": row.ORDINAL_POSITION
            })

        cursor.close()
        cnxn.close()

        if not results:
            result = {
                "status": "error",
                "error": f"Table '{schema_name}.{table_name}' not found"
            }
            return json.dumps(result, indent=2)

        result = {
            "status": "success",
            "table_name": f"{schema_name}.{table_name}",
            "column_count": len(results),
            "columns": results
        }
        return json.dumps(result, indent=2)

    except Exception as e:
        result = {
            "status": "error",
            "error": str(e),
            "table_name": f"{schema_name}.{table_name}"
        }
        return json.dumps(result, indent=2)


@mcp.tool()
def list_sql_configurations() -> str:
    """
    List all available SQL Server configurations
    """
    try:
        configs = []
        for key, config in SQL_CONFIGURATIONS.items():
            configs.append({
                "key": key,
                "name": config["name"],
                "server": config["server"],
                "database": config["database"],
                "authentication": config["authentication"],
                "description": config["description"],
                "is_current": key == CURRENT_SQL_CONFIG
            })

        result = {
            "status": "success",
            "current_config": CURRENT_SQL_CONFIG,
            "total_configs": len(configs),
            "configurations": configs
        }
        return json.dumps(result, indent=2)
    except (NameError, ImportError):
        result = {
            "status": "error",
            "error": "SQL configuration system not available"
        }
        return json.dumps(result, indent=2)


@mcp.tool()
def set_sql_configuration(config_name: str) -> str:
    """
    Switch to a different SQL Server configuration

    Args:
        config_name: Name of the configuration to switch to (e.g., 'azure_relaxed', 'docker_test')
    """
    global CURRENT_SQL_CONFIG

    try:
        if config_name not in SQL_CONFIGURATIONS:
            available = list(SQL_CONFIGURATIONS.keys())
            result = {
                "status": "error",
                "error": f"Configuration '{config_name}' not found. Available: {available}"
            }
            return json.dumps(result, indent=2)

        old_config = CURRENT_SQL_CONFIG
        CURRENT_SQL_CONFIG = config_name

        result = {
            "status": "success",
            "message": f"SQL configuration switched from '{old_config}' to '{config_name}'",
            "old_config": old_config,
            "new_config": config_name,
            "config_details": SQL_CONFIGURATIONS[config_name]["description"]
        }
        return json.dumps(result, indent=2)

    except (NameError, ImportError):
        result = {
            "status": "error",
            "error": "SQL configuration system not available"
        }
        return json.dumps(result, indent=2)


@mcp.tool()
def greet(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"


if __name__ == "__main__":
    # Check command line arguments for transport type
    import sys
    transport = "stdio"  # Default to stdio for testing
    for arg in sys.argv[1:]:
        if arg == "--sse":
            transport = "sse"
            break
        elif arg == "--stdio":
            transport = "stdio"
            break

    print(f"Running with transport: {transport}")
    mcp.run(transport=transport)
