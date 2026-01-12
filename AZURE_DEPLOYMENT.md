# Azure Functions Deployment Configuration

## Project Structure
This project is configured for Azure Functions deployment with Python runtime on Linux.

### Files Created:
- `requirements.txt` - Python dependencies for Azure Functions
- `host.json` - Azure Functions host configuration
- `local.settings.json` - Local development settings
- `shared_code/mcp_server.py` - Core MCP server functionality
- `mcp_server/` - HTTP trigger function for MCP tools
- `mcp_sse/` - Server-Sent Events endpoint for real-time communication

### Azure Functions:

#### 1. mcp_server (HTTP Trigger)
- **Endpoint**: `https://your-function-app.azurewebsites.net/api/mcp_server`
- **Methods**: GET, POST
- **GET**: Returns server info and available tools
- **POST**: Executes MCP tools with JSON request/response

#### 2. mcp_sse (SSE Trigger)
- **Endpoint**: `https://your-function-app.azurewebsites.net/api/mcp_sse`
- **Methods**: GET, POST
- **GET**: Returns SSE endpoint information
- **POST**: Executes MCP tools with Server-Sent Events streaming

### Environment Variables:
Configure these in Azure Portal -> Function App -> Configuration -> Application Settings:

**SQL Server Configuration:**
- `SQL_SERVER` - SQL Server hostname
- `SQL_DATABASE` - Database name
- `SQL_USERNAME` - Username (for SQL auth)
- `SQL_PASSWORD` - Password (for SQL auth)
- `SQL_AUTH_TYPE` - Authentication type (SqlPassword/ActiveDirectoryInteractive)
- `SQL_ENCRYPT` - Enable encryption (yes/no)
- `SQL_TRUST_CERT` - Trust server certificate (yes/no)
- `SQL_TIMEOUT` - Connection timeout in seconds

**Function App Configuration:**
- `FUNCTIONS_WORKER_RUNTIME` - python
- `FUNCTIONS_EXTENSION_VERSION` - ~4

### Available MCP Tools:
1. `calculate_bmi` - Calculate BMI from weight and height
2. `test_network_connectivity` - Test network connectivity to SQL Server
3. `test_sql_connection` - Test SQL Server authentication
4. `query_sql_server` - Execute read-only SQL SELECT queries
5. `get_server_info` - Get Azure Functions environment information
6. `greet` - Simple greeting tool for testing

### Usage Examples:

#### HTTP API:
```bash
# Get server info
curl -X GET https://your-function-app.azurewebsites.net/api/mcp_server

# Execute BMI calculation
curl -X POST https://your-function-app.azurewebsites.net/api/mcp_server \\
  -H "Content-Type: application/json" \\
  -d '{"tool": "calculate_bmi", "arguments": {"weight_kg": 70, "height_m": 1.75}}'

# Execute SQL query
curl -X POST https://your-function-app.azurewebsites.net/api/mcp_server \\
  -H "Content-Type: application/json" \\
  -d '{"tool": "query_sql_server", "arguments": {"query": "SELECT @@VERSION"}}'
```

#### SSE API:
```bash
# Execute tool with real-time streaming
curl -X POST https://your-function-app.azurewebsites.net/api/mcp_sse \\
  -H "Content-Type: application/json" \\
  -H "Accept: text/event-stream" \\
  -d '{"tool": "get_server_info", "arguments": {}}'
```

### Deployment Steps:

1. **Install Azure Functions Core Tools:**
   ```bash
   npm install -g azure-functions-core-tools@4 --unsafe-perm true
   ```

2. **Login to Azure:**
   ```bash
   az login
   ```

3. **Create Function App (using Azure CLI):**
   ```bash
   # Create resource group
   az group create --name myResourceGroup --location "East US"
   
   # Create storage account
   az storage account create --name mystorageaccount --resource-group myResourceGroup --location "East US" --sku Standard_LRS
   
   # Create Function App with Flex Consumption plan (recommended)
   az functionapp create --resource-group myResourceGroup --name myMCPFunctionApp \\
     --storage-account mystorageaccount --runtime python --runtime-version 3.11 \\
     --os-type Linux --consumption-plan-location "East US"
   ```

4. **Deploy Function:**
   ```bash
   func azure functionapp publish myMCPFunctionApp
   ```

5. **Configure Application Settings:**
   ```bash
   # Set SQL Server configuration
   az functionapp config appsettings set --name myMCPFunctionApp --resource-group myResourceGroup \\
     --settings SQL_SERVER="your-sql-server.database.windows.net" \\
                SQL_DATABASE="your-database" \\
                SQL_AUTH_TYPE="ActiveDirectoryInteractive" \\
                SQL_ENCRYPT="yes" \\
                SQL_TRUST_CERT="no"
   ```

### Security Considerations:
- Use Azure Key Vault for sensitive configuration like SQL passwords
- Enable Application Insights for monitoring and logging
- Configure CORS settings appropriately for your use case
- Use Azure AD authentication for the Function App if needed
- Consider using Managed Identity for SQL Server authentication

Note: For local development, copy `.env.example` to `.env` and populate environment variables. For production, use Azure Key Vault or Function App application settings instead of `.env`.

### Monitoring:
- Enable Application Insights for comprehensive monitoring
- Use Azure Monitor for alerts and dashboards
- Check Function App logs in Azure Portal
- Monitor performance metrics and error rates