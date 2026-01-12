#!/usr/bin/env python3
"""
SQL Server Configuration and Diagnostic Tool
"""
import os
import subprocess
import pyodbc


def test_odbc_drivers():
    """List available ODBC drivers"""
    print("🔍 Available ODBC Drivers:")
    print("-" * 40)

    try:
        drivers = pyodbc.drivers()
        for i, driver in enumerate(drivers, 1):
            print(f"  {i}. {driver}")
            if 'SQL Server' in driver:
                print(f"     ✅ This looks like a SQL Server driver!")

        if not any('SQL Server' in driver for driver in drivers):
            print("  ❌ No SQL Server drivers found!")
            print("  💡 Try installing: brew install msodbcsql18")

    except Exception as e:
        print(f"  ❌ Error listing drivers: {e}")


def test_network_connectivity():
    """Test network connectivity"""
    print("\n🌐 Testing Network Connectivity:")
    print("-" * 40)

    server = "ie1misql00029.cb7cc8a016ea.database.windows.net"

    # Test DNS resolution
    try:
        result = subprocess.run(
            ["nslookup", server],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print(f"  ✅ DNS resolution successful for {server}")
        else:
            print(f"  ❌ DNS resolution failed for {server}")
            print(f"     Error: {result.stderr}")
    except Exception as e:
        print(f"  ❌ DNS test error: {e}")

    # Test ping
    try:
        result = subprocess.run(
            ["ping", "-c", "3", server],
            capture_output=True,
            text=True,
            timeout=15
        )
        if result.returncode == 0:
            print(f"  ✅ Ping successful to {server}")
        else:
            print(f"  ❌ Ping failed to {server}")
    except Exception as e:
        print(f"  ❌ Ping test error: {e}")


def test_sql_connection_variations():
    """Test different connection string variations"""
    print("\n🔗 Testing SQL Connection Variations:")
    print("-" * 40)

    server = "ie1misql00029.cb7cc8a016ea.database.windows.net"
    database = "supplierwebsitedev"
    username = os.environ.get('SQL_USERNAME', '')

    # Connection string variations to try
    variations = [
        {
            "name": "Standard Azure AD Interactive",
            "conn_str": (
                f"DRIVER={{ODBC Driver 18 for SQL Server}};"
                f"SERVER={server};"
                f"DATABASE={database};"
                f"UID={username};"
                f"Authentication=ActiveDirectoryInteractive;"
                f"Encrypt=yes;"
                f"TrustServerCertificate=no;"
            )
        },
        {
            "name": "Azure AD Interactive with Trust Certificate",
            "conn_str": (
                f"DRIVER={{ODBC Driver 18 for SQL Server}};"
                f"SERVER={server};"
                f"DATABASE={database};"
                f"UID={username};"
                f"Authentication=ActiveDirectoryInteractive;"
                f"Encrypt=yes;"
                f"TrustServerCertificate=yes;"
            )
        },
        {
            "name": "Try ODBC Driver 17 (if available)",
            "conn_str": (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={server};"
                f"DATABASE={database};"
                f"UID={username};"
                f"Authentication=ActiveDirectoryInteractive;"
                f"Encrypt=yes;"
                f"TrustServerCertificate=yes;"
            )
        }
    ]

    for variation in variations:
        print(f"\n  📝 Trying: {variation['name']}")
        try:
            cnxn = pyodbc.connect(variation['conn_str'], timeout=30)
            cursor = cnxn.cursor()
            cursor.execute("SELECT @@VERSION")
            version = cursor.fetchone()[0]
            cursor.close()
            cnxn.close()

            print(f"  ✅ SUCCESS! Connection established.")
            print(f"     Server version: {version[:100]}...")
            return variation['conn_str']  # Return successful connection string

        except Exception as e:
            error_msg = str(e)
            if "Login timeout expired" in error_msg:
                print(f"  ⏱️  Timeout - Network or authentication issue")
            elif "Cannot open database" in error_msg:
                print(f"  🔐 Authentication issue - Check permissions")
            elif "file not found" in error_msg:
                print(f"  📁 Driver not found - Check ODBC driver installation")
            else:
                print(f"  ❌ Failed: {error_msg[:100]}...")

    return None


def create_environment_setup():
    """Create environment setup instructions"""
    print("\n⚙️  Environment Setup Instructions:")
    print("-" * 40)

    print("1. Install Microsoft ODBC Driver (if not already done):")
    print("   brew tap microsoft/mssql-release")
    print("   brew install msodbcsql18 mssql-tools18")

    print("\n2. Verify your Azure AD credentials:")
    print("   - Make sure you're logged into Azure CLI: az login")
    print("   - Check access: az account show")

    print("\n3. Network requirements:")
    print("   - Ensure port 1433 is not blocked by firewall")
    print("   - VPN connection may be required for corporate networks")

    print("\n4. Alternative authentication methods to try:")
    print("   - Azure AD Integrated (if domain joined)")
    print("   - SQL Server Authentication (if enabled)")
    print("   - Azure AD with MFA")


def main():
    """Run all diagnostic tests"""
    print("🏥 SQL Server Connectivity Diagnostic Tool")
    print("=" * 50)

    test_odbc_drivers()
    test_network_connectivity()

    successful_conn_str = test_sql_connection_variations()

    if successful_conn_str:
        print(f"\n✅ SOLUTION FOUND!")
        print(f"Use this connection string in your application:")
        print(f"'{successful_conn_str}'")
    else:
        print(f"\n❌ No successful connections found.")
        create_environment_setup()


if __name__ == "__main__":
    main()
