# SQL Server Connectivity Setup Guide

## Overview

Your MCP server now includes comprehensive SQL Server connectivity with multiple configuration options and robust error handling.

## 🔧 Available SQL Tools

### Connection Management
- `test_network_connectivity()` - Test network connectivity to SQL Server
- `test_sql_connection()` - Test SQL Server authentication and connection
- `list_sql_configurations()` - Show all available SQL configurations  
- `set_sql_configuration(config_name)` - Switch between configurations

### Database Operations
- `query_sql_server(query)` - Execute SELECT queries safely
- `get_table_list()` - List all tables in the database
- `get_table_schema(table_name, schema_name)` - Get table structure

### Other Tools
- `calculate_bmi(weight_kg, height_m)` - Calculate BMI
- `greet(name)` - Get a personalized greeting

## 🏗️ SQL Server Configurations

### 1. Azure Production (azure_production)
- **Server**: ie1misql00029.cb7cc8a016ea.database.windows.net
- **Database**: supplierwebsitedev
- **Auth**: Azure AD Interactive
- **Security**: High (certificate validation enabled)
- **Use**: Production environment

### 2. Azure Relaxed (azure_relaxed) - **DEFAULT**
- **Server**: ie1misql00029.cb7cc8a016ea.database.windows.net  
- **Database**: supplierwebsitedev
- **Auth**: Azure AD Interactive
- **Security**: Relaxed (certificate validation disabled)
- **Use**: When network/certificate issues occur

### 3. Docker Test (docker_test)
- **Server**: localhost:1433
- **Database**: master
- **Auth**: SQL Authentication (sa / set via environment variable `SA_PASSWORD`)
- **Use**: Local development and testing

### 4. Local Test (local_test)
- **Server**: localhost
- **Database**: TestDB
- **Auth**: SQL Authentication
- **Use**: Local SQL Server instance

## ✅ Current Status (Updated)

### Working Features
- ✅ **MCP Tool Validation**: All SQL tools now return proper JSON strings
- ✅ **Configuration Management**: Switch between 4 different SQL configurations
- ✅ **Network Connectivity**: Successfully test network connections to SQL servers
- ✅ **SQL Safety Features**: Dangerous queries (DROP, DELETE, INSERT, UPDATE, etc.) are blocked
- ✅ **Error Handling**: Comprehensive error messages and troubleshooting guidance
- ✅ **Testing Framework**: Complete test suite for all functionality

### Network Connectivity Status
- ✅ **Azure SQL Network**: Can reach ie1misql00029.cb7cc8a016ea.database.windows.net:1433
- ❌ **Azure SQL Authentication**: Login timeout (likely requires VPN/corporate network)
- 🔄 **Docker SQL**: Available for local testing (see Docker Setup below)

### Recent Fixes
- **Fixed MCP Tool Validation**: All SQL tools now return JSON strings instead of dict objects
- **Fixed SQL Safety Tests**: Dangerous query blocking now works correctly
- **Enhanced Error Handling**: Consistent JSON response format across all tools

## 🐳 Docker SQL Server Testing

For immediate testing without network/authentication issues, use the Docker setup:

### Quick Start
```bash
# Start Docker SQL Server and run tests
# Copy .env.example to .env and set SA_PASSWORD (or export SA_PASSWORD in your shell)
cp .env.example .env
export SA_PASSWORD="your_local_sa_password_here"
python test_docker_sql.py

# Manual Docker setup
docker-compose up -d                    # Start SQL Server
python test_config_tools.py           # Test configuration switching
python test_sql_server.py             # Test SQL connectivity
docker-compose down                    # Stop SQL Server
```

### Docker Configuration
- **Container**: mcr.microsoft.com/mssql/server:2022-latest
- **Port**: 1433
- **Username**: sa
- **Password**: set via environment variable `SA_PASSWORD` (do NOT commit secrets to source control)
- **Database**: master

## 🚀 Quick Start

### Test Your Current Setup
```bash
cd /path/to/your/project
./venv/bin/python test_sql_server.py
```

### Test Different Configurations
```bash
# List all configurations
./venv/bin/python sql_config.py list

# Test a specific configuration
./venv/bin/python sql_config.py test azure_relaxed
./venv/bin/python sql_config.py test docker_test
```

### Run Diagnostics
```bash
./venv/bin/python sql_diagnostics.py
```

## 🐳 Local Docker Setup (Recommended for Testing)

If you're having connectivity issues with Azure SQL, set up a local test server:

```bash
# Start SQL Server in Docker (set `SA_PASSWORD` in your shell first)
# Set `SA_PASSWORD` in your shell or copy `.env.example` to `.env` and edit
export SA_PASSWORD="(set your local SA password here)"
docker run -e 'ACCEPT_EULA=Y' -e "SA_PASSWORD=${SA_PASSWORD}" \
   -p 1433:1433 --name sql-server-test \
   -d mcr.microsoft.com/mssql/server:2022-latest

# Wait 30 seconds for startup, then test
./venv/bin/python sql_config.py test docker_test
```

## 🔍 Troubleshooting Azure SQL Connection

### Common Issues

1. **Login Timeout Expired**
   - **Cause**: Network connectivity, VPN required, or IP not whitelisted
   - **Solution**: Connect to VPN, check firewall rules, try different network

2. **Driver Not Found** 
   - **Cause**: ODBC driver not installed
   - **Solution**: `brew install msodbcsql18 mssql-tools18`

3. **Authentication Failed**
   - **Cause**: Azure AD credentials or permissions
   - **Solution**: Run `az login`, verify database access permissions

4. **Certificate Validation Errors**
   - **Cause**: Corporate network certificate issues
   - **Solution**: Use `azure_relaxed` configuration

### Network Requirements
- Port 1433 must be accessible
- Corporate VPN may be required
- IP address may need to be whitelisted in Azure SQL firewall

## 📋 Using the MCP Server

### Test All SQL Tools
```bash
./venv/bin/python test_sql_server.py
```

### Switch Configurations in MCP
```python
# In your MCP client:
await session.call_tool("list_sql_configurations", {})
await session.call_tool("set_sql_configuration", {"config_name": "docker_test"})
await session.call_tool("test_sql_connection", {})
```

### Execute Safe Queries
```python
# Only SELECT queries are allowed
await session.call_tool("query_sql_server", {
    "query": "SELECT TOP 5 * FROM INFORMATION_SCHEMA.TABLES"
})
```

## 🛡️ Security Features

### SQL Injection Protection
- Only SELECT statements allowed
- Dangerous keywords (DROP, DELETE, INSERT, UPDATE) are blocked
- Input validation on all queries

### Connection Security
- Encrypted connections by default
- Certificate validation (configurable)
- Timeout protection
- Proper error handling without exposing sensitive information

## 📁 Project Files

- `bmi_server.py` - Main MCP server with SQL tools
- `test_sql_server.py` - Comprehensive SQL testing
- `sql_config.py` - Configuration management system
- `sql_diagnostics.py` - Network and driver diagnostics
- `test_bmi_server.py` - General MCP server testing
- `SQL_SERVER_SETUP.md` - This documentation

## 🎯 Next Steps

1. **Test Connection**: Run diagnostics to identify issues
2. **Use Docker**: Set up local SQL Server for development  
3. **Network Setup**: Contact IT team about Azure SQL access
4. **Production**: Switch to `azure_production` when connectivity works
5. **Development**: Use `docker_test` for local development

## 💡 Tips

- Start with Docker setup for immediate testing
- Use `azure_relaxed` config to troubleshoot Azure connectivity
- Run diagnostics when connection issues occur
- Check VPN/network settings for corporate Azure SQL access
- Use the configuration system to easily switch between environments