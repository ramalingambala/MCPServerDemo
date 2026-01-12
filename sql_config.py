#!/usr/bin/env python3
"""
SQL Server Configuration Manager
Allows easy switching between different SQL Server configurations
"""
import json
import os

# Different SQL Server configurations for various scenarios
SQL_CONFIGURATIONS = {
    "azure_production": {
        "name": "Azure Production",
        "server": "upskilling-dbserver.database.windows.net",
        "database": "TestDB",
        "username": os.environ.get('SQL_USERNAME', ''),
        "driver": "ODBC Driver 18 for SQL Server",
        "authentication": "ActiveDirectoryInteractive",
        "encrypt": "yes",
        "trust_server_certificate": "no",
        "timeout": 30,
        "description": "Production Azure SQL Database with AD Authentication"
    },

    "azure_relaxed": {
        "name": "Azure Production (Relaxed Security)",
        "server": "upskilling-dbserver.database.windows.net",
        "database": "TestDB",
        "username": os.environ.get('SQL_USERNAME', ''),
        "driver": "ODBC Driver 18 for SQL Server",
        "authentication": "ActiveDirectoryInteractive",
        "encrypt": "yes",
        "trust_server_certificate": "yes",  # More permissive
        "timeout": 60,  # Longer timeout
        "description": "Same as production but with relaxed certificate validation"
    },

    "local_test": {
        "name": "Local Test Server",
        "server": "localhost",
        "database": "TestDB",
        "username": "sa",
        "password": os.environ.get('SQL_PASSWORD', ''),
        "driver": "ODBC Driver 18 for SQL Server",
        "authentication": "SqlPassword",
        "encrypt": "yes",
        "trust_server_certificate": "yes",
        "timeout": 30,
        "description": "Local SQL Server instance for testing"
    },

    "docker_test": {
        "name": "Docker SQL Server",
        "server": "127.0.0.1,1433",  # Using IP instead of localhost
        "database": "master",
        "username": "sa",
        "password": os.environ.get('SQL_PASSWORD', ''),
        "driver": "ODBC Driver 18 for SQL Server",
        "authentication": "SqlPassword",
        "encrypt": "yes",
        "trust_server_certificate": "yes",
        "timeout": 60,
        "description": "SQL Server running in Docker container"
    }
}


def get_connection_string_for_config(config_name: str) -> str:
    """Generate connection string for a specific configuration"""
    if config_name not in SQL_CONFIGURATIONS:
        raise ValueError(
            f"Configuration '{config_name}' not found. Available: {list(SQL_CONFIGURATIONS.keys())}")

    config = SQL_CONFIGURATIONS[config_name]

    # Build connection string based on authentication method
    if config["authentication"] == "ActiveDirectoryInteractive":
        conn_str = (
            f"DRIVER={{{config['driver']}}};"
            f"SERVER={config['server']};"
            f"DATABASE={config['database']};"
            f"UID={config['username']};"
            f"Authentication={config['authentication']};"
            f"Encrypt={config['encrypt']};"
            f"TrustServerCertificate={config['trust_server_certificate']};"
            f"Connection Timeout={config['timeout']};"
        )
    elif config["authentication"] == "SqlPassword":
        conn_str = (
            f"DRIVER={{{config['driver']}}};"
            f"SERVER={config['server']};"
            f"DATABASE={config['database']};"
            f"UID={config['username']};"
            f"PWD={config['password']};"
            f"Encrypt={config['encrypt']};"
            f"TrustServerCertificate={config['trust_server_certificate']};"
            f"Connection Timeout={config['timeout']};"
        )
    else:
        raise ValueError(
            f"Unsupported authentication method: {config['authentication']}")

    return conn_str


def list_configurations():
    """List all available configurations"""
    print("📋 Available SQL Server Configurations:")
    print("=" * 50)

    for key, config in SQL_CONFIGURATIONS.items():
        print(f"\n🔧 {key}")
        print(f"   Name: {config['name']}")
        print(f"   Server: {config['server']}")
        print(f"   Database: {config['database']}")
        print(f"   Auth: {config['authentication']}")
        # Don't print sensitive fields like password
        desc = config.get('description')
        print(f"   Description: {desc}")


def test_configuration(config_name: str):
    """Test a specific configuration"""
    import pyodbc

    print(f"\n🧪 Testing configuration: {config_name}")
    print("-" * 40)

    try:
        config = SQL_CONFIGURATIONS[config_name]
        print(f"Configuration: {config['name']}")
        print(f"Server: {config['server']}")
        print(f"Database: {config['database']}")

        conn_str = get_connection_string_for_config(config_name)
        print(f"Connection String: {conn_str}")

        print("\nAttempting connection...")
        cnxn = pyodbc.connect(conn_str)
        cursor = cnxn.cursor()

        # Test query
        cursor.execute(
            "SELECT @@VERSION as version, DB_NAME() as db_name, GETDATE() as current_time")
        row = cursor.fetchone()

        print("✅ SUCCESS! Connection established.")
        print(f"Database: {row.db_name}")
        print(f"Server Version: {row.version[:100]}...")
        print(f"Current Time: {row.current_time}")

        cursor.close()
        cnxn.close()

        return True

    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False


def create_local_docker_setup():
    """Provide instructions for setting up a local SQL Server for testing"""
    print("\n🐳 Local SQL Server Docker Setup:")
    print("=" * 40)
    print("If you want to test locally, run this Docker command:")
    print()
    print("docker run -e 'ACCEPT_EULA=Y' -e 'SA_PASSWORD=${SA_PASSWORD}' \\")
    print("   -p 1433:1433 --name sql-server-test \\")
    print("   -d mcr.microsoft.com/mssql/server:2022-latest")
    print()
    print("Then use the 'docker_test' configuration to connect.")


def main():
    """Main function for interactive configuration management"""
    list_configurations()

    print(f"\n🎯 Current Issue Analysis:")
    print("-" * 30)
    print("Based on the diagnostics, your Azure SQL connection is timing out.")
    print("This usually indicates one of these issues:")
    print("1. 🏢 Corporate network blocking the connection")
    print("2. 🔐 Azure AD authentication requires browser interaction")
    print("3. 🌐 VPN required to access the Azure SQL server")
    print("4. 🚪 IP address not whitelisted in Azure SQL firewall")

    print(f"\n💡 Recommendations:")
    print("1. Try connecting from a different network")
    print("2. Check if VPN is required")
    print("3. Contact your IT team about Azure SQL access")
    print("4. Test with a local SQL Server using Docker")

    create_local_docker_setup()

    # Test the relaxed configuration
    print(f"\n🔬 Testing relaxed Azure configuration...")
    success = test_configuration("azure_relaxed")

    if not success:
        print(f"\n🏠 Consider testing locally with Docker first:")
        print("1. Run the Docker command above")
        print("2. Wait for SQL Server to start (about 30 seconds)")
        print("3. Test with: python sql_config.py test docker_test")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "list":
            list_configurations()
        elif sys.argv[1] == "test" and len(sys.argv) > 2:
            test_configuration(sys.argv[2])
        else:
            print("Usage: python sql_config.py [list|test <config_name>]")
    else:
        main()
