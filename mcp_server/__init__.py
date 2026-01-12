import azure.functions as func
import json
import logging
import sys
import os
from typing import Dict, Any

# Add the shared_code directory to the path
shared_code_path = os.path.join(os.path.dirname(__file__), '..', 'shared_code')
if shared_code_path not in sys.path:
    sys.path.insert(0, shared_code_path)

# Also try the absolute path approach
abs_shared_code_path = os.path.abspath(shared_code_path)
if abs_shared_code_path not in sys.path:
    sys.path.insert(0, abs_shared_code_path)

# Import from shared_code
try:
    import mcp_server as shared_mcp
    mcp = shared_mcp.mcp
    logger = shared_mcp.logger
    logger.info("Successfully imported MCP server from shared_code")
except ImportError as e:
    logging.error(f"Failed to import shared MCP server: {e}")
    logging.error(f"Current sys.path: {sys.path}")
    logging.error(f"Current working directory: {os.getcwd()}")
    logging.error(f"Contents of current directory: {os.listdir('.')}")

    # Check if shared_code directory exists
    logging.error(f"Shared code path: {shared_code_path}")
    logging.error(
        f"Shared code path exists: {os.path.exists(shared_code_path)}")
    if os.path.exists(shared_code_path):
        logging.error(
            f"Contents of shared_code: {os.listdir(shared_code_path)}")

    # Try alternative import approach
    try:
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        from shared_code import mcp_server as shared_mcp
        mcp = shared_mcp.mcp
        logger = shared_mcp.logger
        logging.info(
            "Successfully imported MCP server using alternative method")
    except ImportError as e2:
        logging.error(f"Alternative import also failed: {e2}")
        # Fallback logging
        logger = logging.getLogger(__name__)
        mcp = None


async def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Function HTTP trigger for MCP Server

    This function handles HTTP requests and routes them to the appropriate MCP tools.
    """
    try:
        logger.info('MCP Server HTTP trigger function processed a request.')

        # Log function startup details for debugging
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Function runtime environment initialized")

    except Exception as startup_error:
        logger.error(
            f"Error during function startup: {str(startup_error)}", exc_info=True)
        return func.HttpResponse(
            json.dumps({
                "status": "error",
                "message": f"Function startup failed: {str(startup_error)}"
            }),
            mimetype="application/json",
            status_code=500
        )

    try:
        # Helper to await coroutines or return sync results
        async def _maybe_await(value):
            import inspect
            if inspect.isawaitable(value):
                return await value
            return value

        # Simple input schemas for known tools (used to populate MCP Tool metadata)
        TOOL_INPUT_SCHEMAS = {
            "calculate_bmi": {
                "type": "object",
                "properties": {
                    "weight_kg": {"type": "number", "description": "Weight in kilograms"},
                    "height_m": {"type": "number", "description": "Height in meters"}
                },
                "required": ["weight_kg", "height_m"]
            },
            "get_bmi_resources": {
                "type": "object",
                "properties": {
                    "resource_type": {"type": "string", "description": "Resource type to fetch (e.g., all, categories)"}
                }
            },
            "test_network_connectivity": {"type": "object", "properties": {}},
            "test_sql_connection": {"type": "object", "properties": {}},
            "query_sql_server": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "SELECT query to run"}},
                "required": ["query"]
            },
            "get_sql_config_debug": {"type": "object", "properties": {}},
            "get_server_info": {"type": "object", "properties": {}},
            "greet": {
                "type": "object",
                "properties": {"name": {"type": "string", "description": "Name to greet"}},
                "required": ["name"]
            }
        }

        # Check if MCP is available. Do not abort here — we have a
        # fallback metadata generator in `_get_tools()` that can
        # populate capabilities for clients (useful for local testing
        # when the MCP runtime isn't importable).
        if mcp is None:
            try:
                logger.warning(
                    "MCP runtime not available; using fallback tool metadata")
            except Exception:
                # If logger isn't set for some reason, fallback to python logging
                logging.warning(
                    "MCP runtime not available; using fallback tool metadata")

        # Get request method and body
        method = req.method.upper()

        # Add a health check endpoint that doesn't depend on MCP
        if method == 'GET' and req.url.endswith('/health'):
            return func.HttpResponse(
                json.dumps({
                    "status": "healthy",
                    "message": "Azure Function is running",
                    "mcp_available": mcp is not None,
                    "python_version": sys.version,
                    "working_directory": os.getcwd(),
                    "sys_path": sys.path[:3]  # First few paths for debugging
                }),
                mimetype="application/json",
                status_code=200
            )

        import inspect

        async def _get_tools():
            """Return normalized list of tools as dicts with keys: name, title, description, inputSchema"""
            try:
                raw_tools = await _maybe_await(mcp.list_tools())
            except Exception:
                raw_tools = None

            tools = []
            if raw_tools:
                # raw_tools likely a list of tool objects from FastMCP
                for tool in raw_tools:
                    name = getattr(tool, 'name', None) or getattr(
                        tool, 'id', None)
                    description = getattr(tool, 'description', None)
                    title = getattr(tool, 'title', name)
                    input_schema = TOOL_INPUT_SCHEMAS.get(
                        name, {"type": "object"})
                    tools.append(
                        {"name": name, "title": title, "description": description, "inputSchema": input_schema})
            else:
                # Fallback: build tools from TOOL_INPUT_SCHEMAS and shared_mcp functions
                for name, schema in TOOL_INPUT_SCHEMAS.items():
                    title = name
                    description = None
                    try:
                        func_obj = getattr(shared_mcp, name, None)
                        if func_obj:
                            doc = inspect.getdoc(func_obj) or ""
                            # Title: first line of docstring if present
                            title = doc.splitlines()[0] if doc else name
                            # Description: full docstring
                            description = doc
                    except Exception:
                        description = None
                    tools.append(
                        {"name": name, "title": title, "description": description, "inputSchema": schema})

            return tools

        def _make_sse_response(tools):
            # Build a JSON-RPC envelope similar to GitHub MCP server so Postman's
            # MCP client recognizes capabilities.
            rpc_payload = {
                "jsonrpc": "2.0",
                "id": 0,
                "result": {
                    "capabilities": {
                        "tools": tools,
                        "nextCursor": None
                    }
                }
            }

            # Primary event uses 'event: message' then 'data: <json>'
            sse_body = 'event: message\n' + 'data: ' + \
                json.dumps(rpc_payload) + "\n\n"

            # Final marker event to signal completion (also JSON-RPC style)
            final_rpc = {"jsonrpc": "2.0", "id": 0, "result": {"done": True}}
            final_event = 'event: message\n' + \
                'data: ' + json.dumps(final_rpc) + "\n\n"

            full_body = sse_body + final_event

            # Return as text/event-stream without Content-Length to allow
            # chunked transfer encoding (GitHub uses chunked); Postman handles this.
            headers = {
                'Cache-Control': 'no-cache',
                # Signal the client that the server will close the connection
                # after the SSE events. Some clients (Postman MCP) rely on
                # Connection: close to detect the end of the stream.
                'Connection': 'close'
            }
            return func.HttpResponse(body=full_body, mimetype="text/event-stream", status_code=200, headers=headers)

        # If the client specifically asked for Server-Sent Events (SSE),
        # respond with a single SSE message containing the capabilities/tools.
        # This makes Postman "Load capabilities" work which expects
        # Content-Type: text/event-stream.
        accept_header = req.headers.get(
            'Accept') or req.headers.get('accept') or ''
        try:
            if isinstance(accept_header, str) and 'text/event-stream' in accept_header.lower():
                tools = await _get_tools()
                return _make_sse_response(tools)
        except Exception:
            # If SSE response fails for any reason, fall back to JSON responses below
            logger.exception(
                "Failed to produce SSE response; falling back to JSON")

        if method == 'GET':
            # Return server information and available tools
            try:
                # Get available tools (FastMCP or fallback)
                tools = await _get_tools()

                # If client requested SSE via Accept header, return SSE payload
                if isinstance(accept_header, str) and 'text/event-stream' in accept_header.lower():
                    return _make_sse_response(tools)

                response_data = {
                    "status": "success",
                    "message": "MCP Server is running on Azure Functions",
                    "server_name": getattr(mcp, 'name', 'BMI and SQL Server - Azure Functions'),
                    "available_tools": tools,
                    "tool_count": len(tools)
                }

                return func.HttpResponse(
                    json.dumps(response_data, indent=2),
                    mimetype="application/json",
                    status_code=200
                )
            except Exception as e:
                logger.error(
                    f"Error getting tools list: {str(e)}", exc_info=True)
                logger.error(f"MCP object type: {type(mcp)}")
                logger.error(f"MCP attributes: {dir(mcp)}")
                response_data = {
                    "status": "success",
                    "message": "MCP Server is running on Azure Functions",
                    "server_name": getattr(mcp, 'name', 'Unknown'),
                    "available_tools": [],
                    "tool_count": 0,
                    "error": f"Could not load tools: {str(e)}"
                }

                return func.HttpResponse(
                    json.dumps(response_data, indent=2),
                    mimetype="application/json",
                    status_code=200
                )

        elif method == 'POST':
            # Handle tool execution requests
            try:
                request_data = req.get_json()

                if not request_data:
                    return func.HttpResponse(
                        json.dumps(
                            {"error": "Request body must be valid JSON"}),
                        mimetype="application/json",
                        status_code=400
                    )

                tool_name = request_data.get('tool')
                arguments = request_data.get('arguments', {})

                # Support JSON-RPC style tools/list and tools/call requests per MCP spec
                # Also preserve the simpler {"action":"list_tools"} for convenience
                rpc_method = request_data.get('method')
                action = request_data.get('action')

                if action == 'list_tools' or rpc_method == 'tools/list':
                    try:
                        tools = await _get_tools()

                        # If JSON-RPC request, wrap in jsonrpc response
                        if rpc_method == 'tools/list':
                            rpc_response = {
                                "jsonrpc": "2.0",
                                "id": request_data.get('id'),
                                "result": {
                                    "tools": tools,
                                    "nextCursor": None
                                }
                            }
                            return func.HttpResponse(json.dumps(rpc_response, indent=2), mimetype="application/json", status_code=200)

                        response_data = {
                            "status": "success",
                            "message": "MCP Server is running on Azure Functions",
                            "server_name": getattr(mcp, 'name', 'BMI and SQL Server - Azure Functions'),
                            "available_tools": tools,
                            "tool_count": len(tools)
                        }

                        return func.HttpResponse(json.dumps(response_data, indent=2), mimetype="application/json", status_code=200)
                    except Exception as e:
                        logger.error(
                            f"Error getting tools list (POST action): {str(e)}", exc_info=True)
                        return func.HttpResponse(json.dumps({"status": "error", "message": f"Could not load tools: {str(e)}"}), mimetype="application/json", status_code=500)

                # Handle JSON-RPC tool call requests: {"jsonrpc":"2.0","method":"tools/call","params":{...}}
                if rpc_method == 'tools/call':
                    params = request_data.get('params', {})
                    name = params.get('name')
                    arguments = params.get('arguments', {})
                    if not name:
                        return func.HttpResponse(json.dumps({"jsonrpc": "2.0", "id": request_data.get('id'), "error": {"code": -32602, "message": "Missing 'name' in params"}}), mimetype="application/json", status_code=400)
                    try:
                        result = await _maybe_await(mcp.call_tool(name, arguments))
                        # Normalize into MCP result shape: {content: [...], isError: false}
                        content_items = []
                        try:
                            # If result is JSON string, include as text content
                            result_text = None
                            if isinstance(result, tuple) and len(result) >= 1:
                                result_text = result[0][0].text if (isinstance(result[0], list) and len(
                                    result[0]) > 0 and hasattr(result[0][0], 'text')) else str(result)
                            elif hasattr(result, 'text'):
                                result_text = result.text
                            elif isinstance(result, str):
                                result_text = result
                            else:
                                result_text = str(result)
                            content_items.append(
                                {"type": "text", "text": result_text})
                        except Exception:
                            content_items.append(
                                {"type": "text", "text": str(result)})

                        rpc_response = {"jsonrpc": "2.0", "id": request_data.get(
                            'id'), "result": {"content": content_items, "isError": False}}
                        return func.HttpResponse(json.dumps(rpc_response, indent=2), mimetype="application/json", status_code=200)
                    except Exception as e:
                        rpc_error = {"jsonrpc": "2.0", "id": request_data.get(
                            'id'), "error": {"code": -32000, "message": str(e)}}
                        return func.HttpResponse(json.dumps(rpc_error, indent=2), mimetype="application/json", status_code=500)

                if not tool_name:
                    return func.HttpResponse(
                        json.dumps(
                            {"error": "Missing 'tool' parameter in request"}),
                        mimetype="application/json",
                        status_code=400
                    )

                # Check if tool exists and execute it
                try:
                    # Use MCP's call_tool method
                    logger.info(
                        f"Executing tool: {tool_name} with arguments: {arguments}")
                    result = await _maybe_await(mcp.call_tool(tool_name, arguments))

                    # Handle the FastMCP result structure
                    # FastMCP returns a tuple: ([TextContent], metadata)
                    result_text = None

                    if isinstance(result, tuple) and len(result) >= 2:
                        content_list, metadata = result[0], result[1]

                        # Check metadata first for 'result' key
                        if isinstance(metadata, dict) and 'result' in metadata:
                            result_text = metadata['result']
                        # Otherwise extract from TextContent list
                        elif isinstance(content_list, list) and len(content_list) > 0:
                            text_content = content_list[0]
                            if hasattr(text_content, 'text'):
                                result_text = text_content.text
                            else:
                                result_text = str(text_content)
                        else:
                            result_text = str(result)

                    # Check for CallToolResult with content
                    elif hasattr(result, 'content') and result.content:
                        if isinstance(result.content, list) and len(result.content) > 0:
                            text_content = result.content[0]
                            if hasattr(text_content, 'text'):
                                result_text = text_content.text
                            else:
                                result_text = str(text_content)
                        else:
                            result_text = str(result.content)

                    # Check for direct text attribute
                    elif hasattr(result, 'text'):
                        result_text = result.text

                    # Check if it's already a string
                    elif isinstance(result, str):
                        result_text = result

                    # Fallback to string conversion
                    else:
                        result_text = str(result)

                    # Try to parse as JSON if it looks like JSON
                    try:
                        parsed_result = json.loads(result_text)
                    except (json.JSONDecodeError, TypeError):
                        parsed_result = result_text

                    response_data = {
                        "status": "success",
                        "tool": tool_name,
                        "result": parsed_result,
                        "arguments": arguments
                    }

                    return func.HttpResponse(
                        json.dumps(response_data, indent=2),
                        mimetype="application/json",
                        status_code=200
                    )

                except Exception as e:
                    # Handle various types of tool execution errors
                    error_msg = str(e)
                    if "not found" in error_msg.lower():
                        # Tool not found error
                        tools_list = await _maybe_await(mcp.list_tools())
                        available_tools = [tool.name for tool in tools_list]
                        return func.HttpResponse(
                            json.dumps({
                                "error": f"Tool '{tool_name}' not found",
                                "available_tools": available_tools
                            }),
                            mimetype="application/json",
                            status_code=404
                        )
                    elif "argument" in error_msg.lower():
                        # Invalid arguments error
                        return func.HttpResponse(
                            json.dumps({
                                "error": f"Invalid arguments for tool '{tool_name}': {error_msg}",
                                "tool": tool_name,
                                "provided_arguments": arguments
                            }),
                            mimetype="application/json",
                            status_code=400
                        )
                    else:
                        # General execution error
                        logger.error(
                            f"Error executing tool '{tool_name}': {error_msg}")
                        return func.HttpResponse(
                            json.dumps({
                                "error": f"Tool execution failed: {error_msg}",
                                "tool": tool_name,
                                "arguments": arguments
                            }),
                            mimetype="application/json",
                            status_code=500
                        )

            except ValueError as e:
                return func.HttpResponse(
                    json.dumps(
                        {"error": f"Invalid JSON in request body: {str(e)}"}),
                    mimetype="application/json",
                    status_code=400
                )

        else:
            return func.HttpResponse(
                json.dumps({"error": f"Method '{method}' not supported"}),
                mimetype="application/json",
                status_code=405
            )

    except Exception as e:
        logger.error(f"Unexpected error in MCP Server function: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                "error": "Internal server error",
                "details": str(e)
            }),
            mimetype="application/json",
            status_code=500
        )
