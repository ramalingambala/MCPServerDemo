import mcp_server as shared_mcp_server
from mcp_server import mcp, logger
import azure.functions as func
import json
import logging
import sys
import os
import asyncio
from typing import Dict, Any, AsyncGenerator

# Add the shared_code directory to the path
sys.path.insert(0, os.path.join(
    os.path.dirname(__file__), '..', 'shared_code'))

# Import from shared_code - avoid naming conflict
mcp = shared_mcp_server.mcp
logger = shared_mcp_server.logger


async def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Function HTTP trigger for MCP Server with Server-Sent Events (SSE)

    This function provides SSE support for real-time MCP communication.
    """
    logger.info('MCP Server SSE HTTP trigger function processed a request.')

    try:
        method = req.method.upper()

        if method == 'GET':
            # Return SSE endpoint information
            response_data = {
                "status": "success",
                "message": "MCP Server SSE endpoint is available",
                "server_name": mcp.name,
                "endpoint_type": "Server-Sent Events (SSE)",
                "usage": {
                    "description": "Send POST requests to execute MCP tools with real-time responses",
                    "content_type": "text/event-stream",
                    "format": "SSE format with data: prefixed JSON"
                }
            }

            return func.HttpResponse(
                json.dumps(response_data, indent=2),
                mimetype="application/json",
                status_code=200
            )

        elif method == 'POST':
            # Handle SSE tool execution
            try:
                request_data = req.get_json()

                if not request_data:
                    error_event = f"data: {json.dumps({'error': 'Request body must be valid JSON'})}\\n\\n"
                    return func.HttpResponse(
                        error_event,
                        mimetype="text/event-stream",
                        status_code=400,
                        headers={"Cache-Control": "no-cache",
                                 "Connection": "keep-alive"}
                    )

                tool_name = request_data.get('tool')
                arguments = request_data.get('arguments', {})

                if not tool_name:
                    error_event = f"data: {json.dumps({'error': 'Missing tool parameter in request'})}\\n\\n"
                    return func.HttpResponse(
                        error_event,
                        mimetype="text/event-stream",
                        status_code=400,
                        headers={"Cache-Control": "no-cache",
                                 "Connection": "keep-alive"}
                    )

                # Check if tool exists
                if tool_name not in mcp._tools:
                    available_tools = list(mcp._tools.keys())
                    error_data = {
                        'error': f'Tool {tool_name} not found',
                        'available_tools': available_tools
                    }
                    error_event = f"data: {json.dumps(error_data)}\n\n"
                    return func.HttpResponse(
                        error_event,
                        mimetype="text/event-stream",
                        status_code=404,
                        headers={"Cache-Control": "no-cache",
                                 "Connection": "keep-alive"}
                    )

                # Create SSE response stream
                def generate_sse_response():
                    try:
                        # Send start event
                        start_event = {
                            "event": "start",
                            "tool": tool_name,
                            "arguments": arguments,
                            "timestamp": str(__import__('datetime').datetime.utcnow())
                        }
                        yield f"data: {json.dumps(start_event)}\\n\\n"

                        # Execute the tool
                        tool_func = mcp._tools[tool_name]

                        if arguments:
                            result = tool_func(**arguments)
                        else:
                            result = tool_func()

                        # Send result event
                        result_event = {
                            "event": "result",
                            "tool": tool_name,
                            "status": "success",
                            "result": result,
                            "timestamp": str(__import__('datetime').datetime.utcnow())
                        }
                        yield f"data: {json.dumps(result_event)}\\n\\n"

                        # Send end event
                        end_event = {
                            "event": "end",
                            "tool": tool_name,
                            "status": "completed",
                            "timestamp": str(__import__('datetime').datetime.utcnow())
                        }
                        yield f"data: {json.dumps(end_event)}\\n\\n"

                    except Exception as e:
                        # Send error event
                        error_event = {
                            "event": "error",
                            "tool": tool_name,
                            "error": str(e),
                            "timestamp": str(__import__('datetime').datetime.utcnow())
                        }
                        yield f"data: {json.dumps(error_event)}\\n\\n"

                # Generate the complete SSE response
                sse_response = ''.join(generate_sse_response())

                return func.HttpResponse(
                    sse_response,
                    mimetype="text/event-stream",
                    status_code=200,
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Headers": "Content-Type",
                        "Access-Control-Allow-Methods": "GET, POST, OPTIONS"
                    }
                )

            except ValueError as e:
                error_event = f"data: {json.dumps({'error': f'Invalid JSON in request body: {str(e)}'})}\\n\\n"
                return func.HttpResponse(
                    error_event,
                    mimetype="text/event-stream",
                    status_code=400,
                    headers={"Cache-Control": "no-cache",
                             "Connection": "keep-alive"}
                )

        else:
            error_event = f"data: {json.dumps({'error': f'Method {method} not supported'})}\\n\\n"
            return func.HttpResponse(
                error_event,
                mimetype="text/event-stream",
                status_code=405,
                headers={"Cache-Control": "no-cache",
                         "Connection": "keep-alive"}
            )

    except Exception as e:
        logger.error(f"Unexpected error in MCP SSE function: {str(e)}")
        error_event = f"data: {json.dumps({'error': 'Internal server error', 'details': str(e)})}\\n\\n"
        return func.HttpResponse(
            error_event,
            mimetype="text/event-stream",
            status_code=500,
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )
